#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐小鸭行为与语音策略管理

参考 Strategy2 项目的 DuckGame.java，将行为策略与语音策略解耦，
并在不同事件中触发对应的动画与提示。

新增：通过 pyttsx3 实现本地语音播报（若可用）。
"""

import gc
import threading
import time
from queue import Queue
from typing import Callable, Dict, Iterable, List, Optional

try:
    import pyttsx3  # 本地 TTS 引擎（离线）
except ImportError:
    pyttsx3 = None

# Windows 上需要 COM 支持
try:
    import pythoncom
    HAS_COM = True
except ImportError:
    HAS_COM = False
    pythoncom = None


class BehaviorStrategy:
    """行为策略基类"""

    name: str = ""
    description: str = ""

    def start(self, duckling) -> None:
        raise NotImplementedError

    def stop(self, duckling) -> None:
        raise NotImplementedError


class SoundStrategy:
    """语音策略基类"""

    description: str = ""

    def play(self, notifier: Optional[Callable[[str], None]], speech_engine: Optional["SpeechEngine"]) -> None:
        if notifier:
            notifier(f"唐小鸭语音：{self.description}\n")
        if speech_engine:
            speech_engine.speak(self.description)


class JumpBehavior(BehaviorStrategy):
    name = "jump"
    description = "蹦蹦跳跳"

    def start(self, duckling) -> None:
        duckling.start_bounce()

    def stop(self, duckling) -> None:
        duckling.stop_bounce()


class SpinBehavior(BehaviorStrategy):
    name = "spin"
    description = "转圈圈"

    def start(self, duckling) -> None:
        duckling.start_spin()

    def stop(self, duckling) -> None:
        duckling.stop_spin()


class FlyBehavior(BehaviorStrategy):
    name = "fly"
    description = "飞起来了"

    def start(self, duckling) -> None:
        duckling.start_fly()

    def stop(self, duckling) -> None:
        duckling.stop_fly()


class QuackSound(SoundStrategy):
    description = "嘎嘎嘎，好开心！"


class MeowSound(SoundStrategy):
    description = "喵喵喵，好漂亮！"


class BarkSound(SoundStrategy):
    description = "汪汪汪，太酷了！"


class DuckAction:
    """行为+语音组合"""

    def __init__(self, behavior: BehaviorStrategy, sound: SoundStrategy):
        self.behavior = behavior
        self.sound = sound

    def start(
        self,
        ducklings: Iterable,
        notifier: Optional[Callable[[str], None]],
        speech_engine: Optional["SpeechEngine"],
    ) -> None:
        for duckling in ducklings:
            self.behavior.start(duckling)
        if notifier:
            notifier(f"唐小鸭动作：{self.behavior.description}\n")
        self.sound.play(notifier, speech_engine)

    def stop(self, ducklings: Iterable) -> None:
        for duckling in ducklings:
            self.behavior.stop(duckling)


class DuckBehaviorManager:
    """负责在不同事件中触发对应的行为与语音"""

    def __init__(self, notifier: Optional[Callable[[str], None]] = None, duration: float = 5.0):
        self.notifier = notifier
        self.duration = duration
        self.speech_engine = SpeechEngine()
        self._actions: Dict[str, DuckAction] = {
            "red_packet": DuckAction(JumpBehavior(), QuackSound()),
            "ai_chat": DuckAction(SpinBehavior(), MeowSound()),
            "code_count": DuckAction(FlyBehavior(), BarkSound()),
        }
        self._active_entries: List[Dict] = []
        if self.notifier and not self.speech_engine.available:
            self.notifier("提示：未检测到语音引擎（pyttsx3）。小鸭语音将以文本形式显示。\n")

    def trigger(self, event_name: str, ducklings: Iterable) -> None:
        action = self._actions.get(event_name)
        if not action:
            return
        ducklings = list(ducklings)
        if not ducklings:
            return
        action.start(ducklings, self.notifier, self.speech_engine)
        self._active_entries.append(
            {
                "action": action,
                "ducklings": ducklings,
                "end_time": time.time() + self.duration,
            }
        )

    def update(self) -> None:
        """定期调用，用于在持续时间结束后恢复原状"""
        now = time.time()
        remaining: List[Dict] = []
        for entry in self._active_entries:
            if now >= entry["end_time"]:
                entry["action"].stop(entry["ducklings"])
            else:
                remaining.append(entry)
        self._active_entries = remaining

    def clear(self) -> None:
        """立即停止所有行为"""
        for entry in self._active_entries:
            entry["action"].stop(entry["ducklings"])
        self._active_entries.clear()


class SpeechEngine:
    """包装 pyttsx3，实现异步播报"""

    def __init__(self):
        self.available = bool(pyttsx3)
        self._queue: Optional[Queue] = Queue() if self.available else None
        self._thread: Optional[threading.Thread] = None
        if self.available:
            try:
                self._thread = threading.Thread(target=self._loop, daemon=True)
                self._thread.start()
            except Exception:
                self.available = False
                self._queue = None
                self._thread = None

    def _loop(self):
        if not pyttsx3 or not self._queue:
            return
        # 先测试一次初始化，确认引擎可用
        try:
            test_engine = pyttsx3.init()
            test_engine.stop()
            self.available = True
        except Exception:
            self.available = False
            return
        
        # 在 Windows 上，为当前线程初始化 COM
        # 注意：如果 COM 已经初始化，CoInitialize 会失败，这是正常的
        com_initialized = False
        if HAS_COM:
            try:
                pythoncom.CoInitialize()
                com_initialized = True
            except pythoncom.com_error:
                # COM 已经初始化，这是正常的（例如在主线程中）
                pass
            except Exception:
                pass
        
        try:
            while True:
                try:
                    # 使用阻塞的 get()，这样有消息时会立即返回
                    text = self._queue.get()
                    if text is None:
                        break
                    engine = None
                    try:
                        # 每次播报时重新初始化引擎，避免 runAndWait() 后的状态问题
                        # 这是最可靠的方法，确保每次都是全新的引擎实例
                        # 在 Windows 上，尝试使用不同的驱动名称来确保独立性
                        try:
                            # 尝试使用 sapi5 驱动（Windows 默认）
                            engine = pyttsx3.init('sapi5')
                        except Exception:
                            # 如果失败，使用默认初始化
                            engine = pyttsx3.init()
                        
                        # 在 Windows 上，确保使用正确的驱动
                        try:
                            voices = engine.getProperty('voices')
                            if voices and len(voices) > 0:
                                engine.setProperty('voice', voices[0].id)
                        except Exception:
                            pass
                        
                        # 播报文本
                        engine.say(text)
                        
                        # 直接使用 runAndWait()，这是最可靠的方法
                        # 关键是在每次使用后完全清理引擎，确保下次可以正常使用
                        try:
                            engine.runAndWait()
                            # 在 runAndWait() 完成后，等待一小段时间确保语音真正播放完成
                            # Windows SAPI 可能需要额外时间来完成音频输出
                            time.sleep(0.2)
                        except Exception as run_wait_error:
                            # 即使异常，也尝试清理
                            try:
                                engine.stop()
                            except Exception:
                                pass
                            raise
                        
                    except Exception:
                        # 忽略 TTS 播报中的异常
                        pass
                    finally:
                        # 确保引擎被完全清理
                        if engine is not None:
                            try:
                                # 注意：不要调用 stop()，因为这会中断可能还在播放的语音
                                # runAndWait() 已经确保语音播放完成，stop() 可能会导致问题
                                pass
                            except Exception:
                                pass
                            try:
                                # 尝试结束事件循环（如果还在运行）
                                if hasattr(engine, 'endLoop'):
                                    try:
                                        engine.endLoop()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                # 在 Windows 上，可能需要额外的清理
                                # 删除引擎引用，让 Python 的垃圾回收器处理 COM 对象
                                del engine
                            except Exception:
                                pass
                            # 强制垃圾回收，确保 COM 对象被释放（Windows 上很重要）
                            gc.collect()
                        # 等待一小段时间，确保资源完全释放（特别是 Windows COM 对象）
                        # 增加等待时间，确保 COM 对象和音频设备完全释放
                        time.sleep(0.3)  # 增加等待时间，确保音频完全播放完成
                except Exception:
                    # 捕获循环中的任何异常，确保循环继续
                    time.sleep(0.1)  # 短暂等待后继续
                    continue
        finally:
            # 在 Windows 上，清理 COM（只有我们初始化的才清理）
            if HAS_COM and com_initialized:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def speak(self, text: str) -> bool:
        if not self._queue or not self.available:
            return False
        try:
            self._queue.put_nowait(text)
            return True
        except Exception:
            return False

    def shutdown(self):
        if self._queue:
            try:
                self._queue.put_nowait(None)
            except Exception:
                pass

