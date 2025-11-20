#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tk 对话框管理器：负责唐老鸭聊天窗口的创建、输入处理与文本更新。
"""

from __future__ import annotations

import traceback
from queue import Queue
from typing import Callable, Optional

import tkinter as tk


class ChatDialogManager:
    """集中管理 Tk 对话框，解耦 DuckGame 与具体 UI 实现。"""

    def __init__(
        self,
        tk_root: Optional[tk.Misc],
        ui_queue: Optional[Queue],
        on_command: Optional[Callable[[str], None]] = None,
        *,
        focus_delay_frames: int = 10,
    ) -> None:
        self._root = tk_root
        self._ui_queue = ui_queue
        self._on_command = on_command
        self._focus_delay_frames = max(focus_delay_frames, 1)

        # 运行时状态
        self.dialog_window: Optional[tk.Toplevel] = None
        self.input_entry: Optional[tk.Entry] = None
        self.text_display: Optional[tk.Text] = None

        self.dialog_active = False
        self._need_dialog = False
        self._need_set_focus = False
        self._focus_counter = 0

    # ------------------------------------------------------------------ 外部交互 --
    def request_dialog(self) -> None:
        """请求显示对话窗口；如果已存在则置顶。"""
        if not self._root:
            print("错误: Tkinter root 未初始化，无法显示对话框。")
            return
        if self.dialog_active and self.dialog_window and self.dialog_window.winfo_exists():
            try:
                self.dialog_window.lift()
            except tk.TclError:
                pass
            return
        self._need_dialog = True

    def update(self) -> None:
        """在游戏主循环中调用，用于延迟创建窗口与设置焦点。"""
        if self._need_dialog:
            self._need_dialog = False
            self._create_dialog()

        if self._need_set_focus and self.dialog_window and self.dialog_window.winfo_exists():
            self._focus_counter += 1
            if self._focus_counter >= self._focus_delay_frames:
                self._set_input_focus()

        # 未捕获的销毁情况兜底重置
        if self.dialog_active:
            if not self.dialog_window or not self.dialog_window.winfo_exists():
                self.dialog_active = False
                self.dialog_window = None
                self.input_entry = None
                self.text_display = None
                self._need_set_focus = False

    def is_active(self) -> bool:
        return bool(self.dialog_active and self.dialog_window and self.dialog_window.winfo_exists())

    def post_text(self, text: str) -> None:
        """线程安全地向对话框追加文本（通过 UI 队列）。"""
        if not text or not self._ui_queue:
            return
        try:
            self._ui_queue.put(("append_text", text), block=False)
        except Exception as exc:  # pragma: no cover - 仅记录
            print(f"提交文本到 UI 队列失败: {exc}")

    def insert_text(self, text: str) -> None:
        """在主线程中安全插入文本。"""
        if not text:
            return
        try:
            if not (self.text_display and self.dialog_window and self.dialog_window.winfo_exists()):
                return
            self.text_display.config(state=tk.NORMAL)
            self.text_display.insert(tk.END, text)
            self.text_display.see(tk.END)
            self.text_display.config(state=tk.DISABLED)
            self.dialog_window.update_idletasks()
        except tk.TclError as exc:
            # 组件已销毁或主循环不存在，忽略
            print(f"[ChatDialog] 插入文本失败: {exc}")
        except Exception as exc:  # pragma: no cover
            print(f"[ChatDialog] 插入文本异常: {exc}")
            traceback.print_exc()

    def close_dialog(self) -> None:
        """关闭对话框并重置状态。"""
        print("[ChatDialog] close_dialog 被调用")
        try:
            if self.dialog_window and self.dialog_window.winfo_exists():
                self.dialog_window.destroy()
        except tk.TclError:
            pass
        finally:
            self.dialog_active = False
            self.dialog_window = None
            self.input_entry = None
            self.text_display = None
            self._need_set_focus = False

    # ---------------------------------------------------------------- 内部实现 --
    def _create_dialog(self) -> None:
        if not self._root:
            print("错误: Tkinter root 未初始化，无法创建对话框。")
            return
        try:
            dialog_window = tk.Toplevel(self._root)
            dialog_window.title("与唐老鸭对话")
            dialog_window.geometry("600x500")
            dialog_window.minsize(400, 300)
            dialog_window.focus_set()
            dialog_window.deiconify()
            dialog_window.update_idletasks()

            input_frame = tk.Frame(dialog_window)
            input_frame.pack(pady=10, padx=10, fill=tk.X)
            tk.Label(input_frame, text="输入消息:", font=("Arial", 12)).pack(anchor=tk.W)
            input_entry = tk.Entry(input_frame, font=("Arial", 12), width=50)
            input_entry.pack(pady=5, fill=tk.X)
            input_entry.bind("<Return>", self._handle_submit)

            display_frame = tk.Frame(dialog_window)
            display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            tk.Label(display_frame, text="对话记录:", font=("Arial", 12)).pack(anchor=tk.W)
            scrollbar = tk.Scrollbar(display_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_display = tk.Text(
                display_frame,
                height=15,
                width=60,
                font=("Arial", 10),
                yscrollcommand=scrollbar.set,
                state=tk.DISABLED,
            )
            text_display.pack(pady=5, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_display.yview)

            button_frame = tk.Frame(dialog_window)
            button_frame.pack(pady=10)
            tk.Button(button_frame, text="发送", command=self._handle_submit, font=("Arial", 12), width=10).pack(
                side=tk.LEFT, padx=5
            )
            tk.Button(button_frame, text="关闭", command=self.close_dialog, font=("Arial", 12), width=10).pack(
                side=tk.LEFT, padx=5
            )

            dialog_window.protocol("WM_DELETE_WINDOW", self.close_dialog)

            self.dialog_window = dialog_window
            self.input_entry = input_entry
            self.text_display = text_display
            self.dialog_active = True
            self._need_set_focus = True
            self._focus_counter = 0

            welcome_msg = (
                "唐老鸭: 你好！我是唐老鸭，有什么可以帮助你的吗？\n\n"
                "提示：\n"
                "- 输入'我要抢红包'可以开始红包游戏\n"
                "- 输入'我要ai问答'可以开始AI对话\n"
                "- 输入'我要统计代码量'会弹出配置界面，可以选择目录、语言和统计选项\n"
                "- 输入'统计代码: <目录路径>'可以快速统计指定目录的代码（使用默认设置）\n\n"
            )
            self.insert_text(welcome_msg)
        except Exception as exc:
            print(f"创建对话框时出错: {exc}")
            traceback.print_exc()
            self.dialog_active = False

    def _handle_submit(self, event=None) -> None:
        if not self.input_entry:
            return
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        self.input_entry.delete(0, tk.END)
        self.insert_text(f"你: {user_input}\n")
        if callable(self._on_command):
            try:
                self._on_command(user_input)
            except Exception as exc:  # pragma: no cover
                print(f"处理用户输入时出错: {exc}")
                traceback.print_exc()
        # 重新请求焦点
        self._need_set_focus = True
        self._focus_counter = 0

    def _set_input_focus(self) -> None:
        try:
            if not (self.dialog_window and self.dialog_window.winfo_exists() and self.input_entry):
                self._need_set_focus = False
                return
            self.dialog_window.focus_set()
            self.input_entry.config(state=tk.NORMAL)
            self.input_entry.focus_set()
            self.dialog_window.update_idletasks()
        except Exception as exc:
            print(f"[ChatDialog] 设置输入焦点失败: {exc}")
        finally:
            self._need_set_focus = False
            self._focus_counter = 0


