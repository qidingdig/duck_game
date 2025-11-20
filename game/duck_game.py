#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐老鸭小游戏整合项目
"""

import sys
import os
import pygame
import threading
import time
import warnings
from typing import Dict, Optional
from queue import Queue
import re

warnings.filterwarnings("ignore", category=SyntaxWarning)

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.config import Config
from services.advanced_code_counter import AdvancedCodeCounter
from services.ai_service import AIService
from ui.chat_dialog import ChatDialogManager
from ui.code_statistics import CodeStatisticsUI
from ui.tk_root_manager import TkRootManager
from ui.queue_processor import UIQueueProcessor
from ui.message_dialog import MessageDialogHelper
from services.duck_behavior_manager import DuckBehaviorManager
from game.characters import Duckling
from game.command_processor import CommandProcessor
from core.game_state import GameState, GameStateManager
from core.event_system import EventManager
from game.minigames.red_packet_game import RedPacketGameManager
import random

class DuckGame:
    """主游戏类 """
    
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化pygame
        pygame.init()
        # 启用窗口调整大小功能，允许最大最小化
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Duck Game - 唐老鸭小游戏")
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        self.state_manager = GameStateManager()
        self.event_manager = EventManager()
        
        # 角色位置
        self.donald_pos = self.config.DONALD_POSITION
        self.duckling_positions = self.config.DUCKLING_POSITIONS
        
        # 初始化小鸭对象列表（每个小鸭随机外观）
        self.ducklings = []
        for i, pos in enumerate(self.duckling_positions):
            duckling = Duckling(
                pos[0], pos[1],
                self.config.CHARACTER_SIZE - 20,
                self.config.CHARACTER_SIZE - 20,
                f"唐小鸭{i+1}"
            )
            self.ducklings.append(duckling)
        
        self.red_packet_game = None
        self._ui_queue = Queue()  # 线程安全UI消息队列
        
        # 红包游戏状态
        self.red_packet_game_active = False
        
        # 唐小鸭移动状态
        self.duckling_positions_original = self.duckling_positions.copy()
        
        # 初始化AI服务
        self.ai_service = AIService(
            backend="openai",
            ollama_url="http://localhost:11434",
            model="deepseek-r1:8b",
            system_prompt="你是唐老鸭，一个友善的卡通角色。请用中文回答用户的问题，保持幽默和友好的语调。"
        )
        
        # 初始化增强代码统计工具
        self.code_counter = AdvancedCodeCounter()
        # 初始化行为管理器
        self.behavior_manager = DuckBehaviorManager(self._update_text_display)
        # 初始化命令处理器
        self.command_processor = CommandProcessor()
        self._setup_commands()
        # 初始化红包游戏管理器
        self._init_red_packet_game_manager()
        
        # 初始化UI基础设施
        self._tk_root_manager = TkRootManager(update_interval=5)
        self._ui_queue_processor = UIQueueProcessor()
        self._message_dialog = MessageDialogHelper()
        self._need_config_dialog = False  # 标记是否需要创建配置对话框
        self.code_stats_ui: Optional[CodeStatisticsUI] = None
        self.chat_ui: Optional[ChatDialogManager] = None
        
        # 在主线程中初始化Tkinter root窗口（必须在主线程中创建）
        if self._tk_root_manager.initialize():
            tk_root = self._tk_root_manager.get_root()
            self._message_dialog = MessageDialogHelper(tk_root=tk_root)
            
            # 注册UI队列消息处理器
            self._setup_ui_queue_handlers()
            
            # 初始化UI组件
            self.chat_ui = ChatDialogManager(
                tk_root=tk_root,
                ui_queue=self._ui_queue,
                on_command=self.handle_user_command,
            )
            self.code_stats_ui = CodeStatisticsUI(
                tk_root=tk_root,
                code_counter=self.code_counter,
                ui_queue=self._ui_queue,
                update_text_callback=self._update_text_display,
                trigger_behavior_callback=self.trigger_duck_behavior,
                default_target_dir=os.path.dirname(os.path.abspath(__file__)),
            )
        
        # 字体设置
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        except:
            # 如果字体加载失败，使用默认字体
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        
        print("=== 唐老鸭小游戏启动 ===")
        print("点击唐老鸭开始对话！")
        print("可用命令:")
        print("- 我要抢红包")
        print("- 我要ai问答")
        print("- 我要统计代码量")
        print("========================")
    
    def _setup_ui_queue_handlers(self):
        """注册UI队列消息处理器。"""
        # append_text 消息处理
        def handle_append_text(item):
            text = item[1] if len(item) > 1 else ""
            if self.chat_ui:
                self.chat_ui.insert_text(text)
            else:
                print(text, end="" if text.endswith("\n") else "\n")
        
        # show_charts 消息处理
        def handle_show_charts(item):
            code_result = item[1] if len(item) > 1 else None
            function_stats = item[2] if len(item) > 2 else None
            c_function_stats = item[3] if len(item) > 3 else None
            detail_table = item[4] if len(item) > 4 else None
            if self.code_stats_ui:
                self.code_stats_ui.show_charts(code_result, function_stats, c_function_stats, detail_table)
        
        # change_duckling_theme 消息处理
        def handle_change_theme(item):
            theme = item[1] if len(item) > 1 else "original"
            if hasattr(self, 'ducklings') and self.ducklings:
                for duckling in self.ducklings:
                    if theme == "excited":
                        duckling.switch_to_excited_theme()
                    elif theme == "focused":
                        duckling.switch_to_focused_theme()
                    elif theme == "original":
                        duckling.restore_original_appearance()
        
        # duck_behavior 消息处理
        def handle_duck_behavior(item):
            event_name = item[1] if len(item) > 1 else ""
            if hasattr(self, 'behavior_manager'):
                self.behavior_manager.trigger(event_name, getattr(self, 'ducklings', []))
        
        # 注册所有处理器
        self._ui_queue_processor.register_handler("append_text", handle_append_text)
        self._ui_queue_processor.register_handler("show_charts", handle_show_charts)
        self._ui_queue_processor.register_handler("change_duckling_theme", handle_change_theme)
        self._ui_queue_processor.register_handler("duck_behavior", handle_duck_behavior)
    
    def _init_red_packet_game_manager(self):
        """初始化红包游戏管理器"""
        try:
            self.red_packet_game = RedPacketGameManager(
                screen=self.screen,
                screen_width=self.config.SCREEN_WIDTH,
                screen_height=self.config.SCREEN_HEIGHT,
                duckling_positions=self.duckling_positions,
                duckling_size=self.config.CHARACTER_SIZE - 20,
                donald_pos=self.donald_pos,
                donald_size=self.config.CHARACTER_SIZE,
                event_manager=self.event_manager,
                on_statistics_update=self._handle_red_packet_statistics
            )
        except Exception as init_error:
            print(f"初始化红包游戏管理器失败: {init_error}")
            self.red_packet_game = None
    
    def _handle_red_packet_statistics(self, report: str):
        """接收红包游戏统计并显示"""
        if not report:
            return
        self._update_text_display(f"唐老鸭: 红包游戏结束！\n{report}\n")
    
    def _sync_ducklings_from_positions(self):
        """同步Duckling对象位置以匹配位置列表"""
        if not hasattr(self, 'ducklings'):
            return
        for i, pos in enumerate(self.duckling_positions):
            if i < len(self.ducklings):
                self.ducklings[i].x = pos[0]
                self.ducklings[i].y = pos[1]
    
    def update_red_packet_game(self, dt: float = 1 / 60):
        """更新红包游戏逻辑"""
        if not self.red_packet_game or not self.red_packet_game.is_active():
            return
        self.red_packet_game.update(dt)
        self._sync_ducklings_from_positions()
    
    
    def handle_click(self, pos):
        """处理鼠标点击事件"""
        # 检查是否点击了唐老鸭
        donald_rect = pygame.Rect(self.donald_pos[0], self.donald_pos[1], 
                                 self.config.CHARACTER_SIZE, self.config.CHARACTER_SIZE)
        if donald_rect.collidepoint(pos):
            self.show_dialog()
    
    def show_dialog(self):
        """显示对话框"""
        if self.chat_ui:
            self.chat_ui.request_dialog()
        else:
            print("Tk 对话框不可用。")
    
    def _setup_commands(self):
        """注册所有命令处理器。"""
        context = {"game": self}
        
        # 注册"我要抢红包"命令
        def handle_red_packet(user_input: str, ctx: Dict):
            game = ctx["game"]
            game._update_text_display("唐老鸭: 好的！让我来发红包！\n\n")
            threading.Thread(target=game.start_red_packet_game, daemon=True).start()
        
        self.command_processor.register(
            name="red_packet",
            patterns=["我要抢红包"],
            handler=handle_red_packet,
            description="启动红包游戏"
        )
        
        # 注册"我要ai问答"命令
        def handle_ai_chat(user_input: str, ctx: Dict):
            game = ctx["game"]
            game._update_text_display("唐老鸭: 好的！让我来回答你的问题！\n\n")
            threading.Thread(target=game.start_ai_chat, args=(user_input,), daemon=True).start()
        
        self.command_processor.register(
            name="ai_chat",
            patterns=["我要ai问答", "^我要ai问答"],
            handler=handle_ai_chat,
            description="开始AI对话"
        )
        
        # 注册"我要统计代码量"命令
        def handle_code_stat_config(user_input: str, ctx: Dict):
            game = ctx["game"]
            game._need_config_dialog = True
        
        self.command_processor.register(
            name="code_stat_config",
            patterns=["我要统计代码量"],
            handler=handle_code_stat_config,
            description="打开代码统计配置界面"
        )
        
        # 注册"统计代码: <路径>"命令
        def handle_code_stat_quick(user_input: str, ctx: Dict):
            game = ctx["game"]
            m = re.match(r'^\s*统计代码[：:]\s*(.+)\s*$', user_input)
            if not m:
                game._update_text_display("唐老鸭: 请提供要统计的目录路径，格式：统计代码: <目录路径>\n\n")
                return
            path_part = m.group(1)
            if (path_part.startswith('"') and path_part.endswith('"')) or (path_part.startswith("'") and path_part.endswith("'")):
                path_part = path_part[1:-1]
            path_part = path_part.strip()
            if not os.path.exists(path_part):
                game._update_text_display(f"唐老鸭: 路径不存在: {path_part}\n请检查路径是否正确。\n\n")
                return
            game._update_text_display(f"唐老鸭: 好的！让我来统计这个目录的代码量！\n目录: {path_part}\n\n")
            threading.Thread(target=game.start_code_counting, args=(path_part,), daemon=True).start()
        
        self.command_processor.register(
            name="code_stat_quick",
            patterns=[r'^统计代码[：:]\s*.+'],
            handler=handle_code_stat_quick,
            description="快速统计指定目录的代码量"
        )
        
        # 设置默认处理器（普通AI对话）
        def handle_default_ai(user_input: str, ctx: Dict):
            game = ctx["game"]
            threading.Thread(target=game.get_ai_response, args=(user_input,), daemon=True).start()
        
        self.command_processor.set_default_handler(handle_default_ai)
    
    def handle_user_command(self, user_input: str) -> None:
        """处理来自对话框的用户命令（与具体 UI 解耦）。"""
        user_input = user_input.strip()
        if not user_input:
            return
        
        print(f"[DEBUG] handle_user_command: 用户输入 = '{user_input}'")
        
        # 使用命令处理器处理
        context = {"game": self}
        self.command_processor.process(user_input, context)
    
    def start_red_packet_game(self):
        """启动红包游戏"""
        try:
            # 显示游戏开始信息（使用线程安全的方式）
            self._update_text_display("唐老鸭: 红包游戏开始！唐小鸭们开始移动！\n")
            
            # 启动红包游戏逻辑（在主线程中直接设置状态，不需要后台线程）
            self.start_red_packet_game_logic()
            
        except Exception as e:
            print(f"红包游戏错误: {e}")
            import traceback
            traceback.print_exc()
            self._update_text_display(f"唐老鸭: 抱歉，红包游戏出现了问题: {str(e)}\n\n")
    
    def start_red_packet_game_logic(self):
        """启动红包游戏逻辑"""
        # 初始化游戏状态
        self.red_packet_game_active = True
        if not self.red_packet_game:
            self._init_red_packet_game_manager()
        if self.red_packet_game:
            self.red_packet_game.start(duration=30)
        self.state_manager.set_state(GameState.RED_PACKET_GAME)
        self.game_start_time = time.time()
        self.game_duration = 30
        
        # 切换小鸭外观为兴奋主题（红包主题）- 通过UI队列确保在主线程执行
        self._ui_queue.put(("change_duckling_theme", "excited"))
        # 触发红包行为
        self.trigger_duck_behavior("red_packet")
    
    
    
    def end_red_packet_game(self):
        """结束红包游戏"""
        self.red_packet_game_active = False
        self.state_manager.set_state(GameState.IDLE)
        
        if self.red_packet_game:
            self.red_packet_game.stop()
        
        # 恢复小鸭的原始外观 - 通过UI队列确保在主线程执行
        self._ui_queue.put(("change_duckling_theme", "original"))
        
        # 同步位
        self._sync_ducklings_from_positions()
    
    
    def start_ai_chat(self, user_input):
        """启动AI对话"""
        try:
            # 触发AI行为
            self.trigger_duck_behavior("ai_chat")
            # 显示正在思考（使用线程安全的方式）
            self._update_text_display("唐老鸭: 让我想想...\n")
            
            # 使用AI服务
            ai_response = self.ai_service.chat_completions(
                user_input=user_input,
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
            # 使用线程安全的方式显示结果
            self._update_text_display(f"唐老鸭: {ai_response}\n\n")
                
        except Exception as e:
            print(f"AI对话错误: {e}")
            import traceback
            traceback.print_exc()
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，AI服务出现了问题: {str(e)}\n\n")
    
    def start_code_counting(self, *args, **kwargs):
        """兼容旧调用，委托给 CodeStatisticsUI 执行实际统计逻辑。"""
        if not self.code_stats_ui:
            self._update_text_display("唐老鸭: Tk 界面未初始化，暂时无法统计代码。\n")
            return
        self.code_stats_ui.start_code_counting(*args, **kwargs)
    def show_code_statistics_charts(self, code_result, function_stats=None, c_function_stats=None, detail_table=None):
        """兼容旧调用，转由 CodeStatisticsUI 负责绘制。"""
        if self.code_stats_ui:
            self.code_stats_ui.show_charts(code_result, function_stats, c_function_stats, detail_table)
        else:
            self._message_dialog.show_warning("图表渲染组件未初始化。", "警告")

    def _create_code_stat_chart(self, code_result):
        """已废弃的遗留接口，保留占位。"""
        return
        """
        try:
            import matplotlib.pyplot as plt

            # 解析语言->代码行数
            labels = []
            values = []

            try:
                # code_result是一个字典，包含 "summary", "by_language", "elapsed_time"
                # 需要从 by_language 中提取数据
                if isinstance(code_result, dict) and "by_language" in code_result:
                    by_language = code_result["by_language"]
                    # by_language 是一个字典，键是语言名称，值是统计数据对象
                    for lang, stat in by_language.items():
                        code_lines = None
                        if hasattr(stat, 'code'):
                            code_lines = getattr(stat, 'code')
                        elif isinstance(stat, dict) and 'code' in stat:
                            code_lines = stat['code']
                        elif isinstance(stat, (int, float)):
                            code_lines = int(stat)
                        if code_lines is None or code_lines == 0:
                            continue
                        labels.append(str(lang))  # 语言名称
                        values.append(int(code_lines))
                elif hasattr(code_result, 'items'):
                    # 如果直接是字典格式
                    for lang, stat in code_result.items():
                        if lang == "summary" or lang == "elapsed_time":
                            continue  # 跳过summary和elapsed_time
                        code_lines = None
                        if hasattr(stat, 'code'):
                            code_lines = getattr(stat, 'code')
                        elif isinstance(stat, dict) and 'code' in stat:
                            code_lines = stat['code']
                        elif isinstance(stat, (int, float)):
                            code_lines = int(stat)
                        if code_lines is None or code_lines == 0:
                            continue
                        labels.append(str(lang))
                        values.append(int(code_lines))
            except Exception as e:
                print(f"[DEBUG] 解析代码统计数据错误: {e}")
                import traceback
                traceback.print_exc()
                return

            if not labels:
                print("[DEBUG] 没有找到有效的语言统计数据")
                return

            # 按代码行数排序（降序）
            sorted_data = sorted(zip(labels, values), key=lambda x: -x[1])
            labels = [lang for lang, _ in sorted_data]
            values = [val for _, val in sorted_data]

            # 创建独立的matplotlib窗口
            fig = plt.figure(figsize=(12, 6))
            fig.canvas.manager.set_window_title('代码统计图表')
            
            # 创建两个子图
            ax1 = fig.add_subplot(121)
            ax2 = fig.add_subplot(122)
            
            # 柱状图
            ax1.bar(labels, values, color="#4C9AFF")
            ax1.set_title("各语言代码行数（柱状图）", fontsize=12)
            ax1.set_ylabel("行数", fontsize=10)
            ax1.tick_params(axis='x', rotation=45, labelsize=9)
            ax1.tick_params(axis='y', labelsize=9)
            
            # 饼图
            ax2.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            ax2.set_title("各语言占比（饼图）", fontsize=12)
            
            plt.tight_layout()
            plt.show(block=False)  # 非阻塞显示
            
        except Exception as e:
            print(f"创建代码统计图表错误: {e}")
            import traceback
            traceback.print_exc()
        """

    def _create_function_stat_chart(self, function_stats, lang_name="Python"):
        """已废弃，保留兼容。"""
        return

    def switch_to_code_tab(self):
        """切换到代码统计标签页 - 已废弃，使用独立窗口"""
        pass

    def switch_to_function_tab(self):
        """切换到函数统计标签页 - 已废弃，使用独立窗口"""
        pass
    
    def _clear_container(self, container):
        try:
            for child in container.winfo_children():
                child.destroy()
        except Exception:
            pass

    def show_code_chart_tab(self, container, code_result):
        """已废弃 - 使用独立matplotlib窗口"""
        # 这个方法已废弃，保留以避免调用错误
        pass

    def show_function_chart_tab(self, container, function_stats):
        """已废弃 - 使用独立matplotlib窗口"""
        # 这个方法已废弃，保留以避免调用错误
        pass
    
    def _update_text_display(self, text):
        """将文本更新请求放入队列，由主线程消费后更新Tkinter组件。"""
        try:
            self._ui_queue.put(("append_text", text), block=False)
        except Exception as e:
            print(f"提交文本更新到队列失败: {e}")

    def _enqueue_show_charts(self, code_result, function_stats=None, c_function_stats=None, detail_table=None):
        """兼容旧逻辑，转由 UI 控制器调度。"""
        try:
            self._ui_queue.put(("show_charts", code_result, function_stats, c_function_stats, detail_table), block=False)
        except Exception as e:
            print(f"提交图表显示到队列失败: {e}")

    def trigger_duck_behavior(self, event_name: str):
        """将行为触发放入队列，确保在主线程中执行。"""
        try:
            self._ui_queue.put(("duck_behavior", event_name), block=False)
        except Exception as e:
            print(f"提交行为触发到队列失败: {e}")

    def _process_ui_queue(self, limit_per_frame: int = 20):
        """在主线程中调用：消费UI队列并执行对应Tk操作。"""
        self._ui_queue_processor.process_queue(self._ui_queue, limit_per_frame)
    
    def get_ai_response(self, user_input):
        """获取AI响应（在后台线程中运行）"""
        try:
            # 显示正在思考（使用线程安全的方式）
            self._update_text_display("唐老鸭: 让我想想...\n")
            
            # 使用AI服务
            ai_response = self.ai_service.chat_completions(
                user_input=user_input,
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
            # 使用线程安全的方式更新UI
            self._update_text_display(f"唐老鸭: {ai_response}\n\n")
                
        except Exception as e:
            print(f"AI响应错误: {e}")
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，我暂时无法回答这个问题: {str(e)}\n\n")
    
    def render(self):
        """渲染游戏画面"""
        # 清屏
        self.screen.fill(self.config.background_color)
        
        # 绘制背景装饰
        self.render_background()
        
        # 绘制角色
        self.render_characters()
        
        # 绘制红包游戏效果
        if hasattr(self, 'red_packet_game_active') and self.red_packet_game_active:
            self.render_red_packets()
        
        # 绘制UI信息
        self.render_ui()
        
        # 更新显示
        pygame.display.flip()
    
    def render_red_packets(self):
        """绘制红包"""
        if self.red_packet_game and self.red_packet_game.is_active():
            self.red_packet_game.render(self.screen)
    
    def render_background(self):
        """绘制背景装饰"""
        # 绘制云朵
        cloud_color = (255, 255, 255)
        for i in range(3):
            x = 100 + i * 300
            y = 50 + i * 20
            pygame.draw.ellipse(self.screen, cloud_color, (x, y, 80, 40))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 20, y - 10, 60, 30))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 40, y, 60, 30))
        # 绘制地面
        ground_color = (34, 139, 34)
        pygame.draw.rect(self.screen, ground_color, (0, self.config.SCREEN_HEIGHT - 50, self.config.SCREEN_WIDTH, 50))
    
    def render_characters(self):
        """绘制角色"""
        # 绘制唐老鸭
        donald_rect = pygame.Rect(self.donald_pos[0], self.donald_pos[1], 
                                 self.config.CHARACTER_SIZE, self.config.CHARACTER_SIZE)
        pygame.draw.ellipse(self.screen, self.config.DONALD_COLOR, donald_rect)
        pygame.draw.ellipse(self.screen, (0, 0, 0), donald_rect, 3)
        
        # 绘制唐老鸭的眼睛
        eye_size = 10
        eye_y = self.donald_pos[1] + self.config.CHARACTER_SIZE // 3
        pygame.draw.circle(self.screen, (0, 0, 0), 
                         (self.donald_pos[0] + self.config.CHARACTER_SIZE // 3, eye_y), eye_size)
        pygame.draw.circle(self.screen, (0, 0, 0), 
                         (self.donald_pos[0] + 2 * self.config.CHARACTER_SIZE // 3, eye_y), eye_size)
        
        # 绘制唐老鸭的嘴巴
        mouth_y = self.donald_pos[1] + 2 * self.config.CHARACTER_SIZE // 3
        pygame.draw.ellipse(self.screen, (255, 165, 0), 
                          (self.donald_pos[0] + self.config.CHARACTER_SIZE // 4, mouth_y - 8, 
                           self.config.CHARACTER_SIZE // 2, 16))
        
        # 绘制汤小鸭（使用Duckling对象）
        for duckling in self.ducklings:
            duckling.render(self.screen)
    
    def render_ui(self):
        """绘制UI信息"""
        # 绘制标题 - 使用英文避免中文字符问题
        title_text = self.font.render("Duck Game", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        hint_text = self.small_font.render("Click Donald Duck to start!", True, (0, 0, 0))
        self.screen.blit(hint_text, (10, 50))
    
    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # 处理窗口大小改变事件
                    # Pygame会自动更新屏幕大小，我们只需要更新配置
                    self.config.SCREEN_WIDTH = event.w
                    self.config.SCREEN_HEIGHT = event.h
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        self.handle_click(event.pos)
            
            # 更新游戏状态
            self.update()
            
            # 渲染画面
            self.render()
            
            # 定期更新Tkinter，确保输入和关闭事件能够被处理
            dialog_active = self.chat_ui.is_active() if self.chat_ui else False
            config_active = self.code_stats_ui.has_active_window() if self.code_stats_ui else False
            has_active_windows = dialog_active or config_active
            self._tk_root_manager.update_loop(has_active_windows)

            # 无论Tk窗口是否存在，都处理一次UI队列
            try:
                self._process_ui_queue()
            except Exception:
                pass
            
            # 控制帧率
            clock.tick(60)
        
        # 主循环结束后清理资源
        if hasattr(self, 'behavior_manager') and self.behavior_manager:
            try:
                self.behavior_manager.clear()
                if hasattr(self.behavior_manager, 'speech_engine'):
                    self.behavior_manager.speech_engine.shutdown()
            except Exception:
                pass
        
        # 关闭Tk根窗口
        if hasattr(self, '_tk_root_manager'):
            self._tk_root_manager.shutdown()
        
        pygame.quit()
    
    def update(self):
        """更新游戏状态"""
        # 更新小鸭行为状态
        if hasattr(self, 'ducklings'):
            allow_override = not getattr(self, 'red_packet_game_active', False)
            for duckling in self.ducklings:
                if hasattr(duckling, 'update_behavior_state'):
                    duckling.update_behavior_state(allow_position_override=allow_override)
        if hasattr(self, 'behavior_manager'):
            self.behavior_manager.update()
        
        # 更新红包游戏状态（如果有）
        if hasattr(self, 'red_packet_game_active') and self.red_packet_game_active:
            self.update_red_packet_game(1 / 60)
            
            # 检查游戏是否结束（30秒后）
            if hasattr(self, 'game_start_time'):
                elapsed = time.time() - self.game_start_time
                if elapsed >= self.game_duration:
                    self.end_red_packet_game()
        
        # 更新对话框UI状态
        if self.chat_ui:
            self.chat_ui.update()
        
        # 检查并创建配置对话框（如果需要）
        if hasattr(self, '_need_config_dialog') and self._need_config_dialog:
            self._need_config_dialog = False
            try:
                if self.code_stats_ui:
                    self.code_stats_ui.show_config_dialog()
                else:
                    self._message_dialog.show_error("Tk 窗口尚未初始化，无法打开配置界面。", "错误")
            except Exception as e:
                print(f"创建配置对话框时出错: {e}")
                import traceback
                traceback.print_exc()


