#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Roll call window: combined configuration + execution UI.
"""

from __future__ import annotations

import os
import tkinter as tk
from typing import Any, Callable, Dict, Optional

from ui.message_dialog import MessageDialogHelper


class RollCallWindow:
    """Tk window that hosts roll call configuration and execution."""

    def __init__(
        self,
        tk_root: tk.Misc,
        message_dialog: MessageDialogHelper,
        on_start_callback: Callable[[Dict[str, Any]], None],
        on_mark_callback: Callable[[str, Optional[str]], None],
        on_close_callback: Optional[Callable[[], None]] = None,
        on_view_records_callback: Optional[Callable[[], None]] = None,
    ):
        self._root = tk_root
        self._message_dialog = message_dialog
        self._on_start = on_start_callback
        self._on_mark = on_mark_callback
        self._on_close = on_close_callback
        self._on_view_records = on_view_records_callback

        self._window: Optional[tk.Toplevel] = None
        self._current_student: Optional[Dict[str, Any]] = None

        # Tk variables
        self._mode_var = tk.StringVar(value="all")
        self._strategy_var = tk.StringVar(value="random")
        self._count_choice = tk.StringVar(value="10")
        self._custom_count = tk.IntVar(value=10)

        # Widgets
        self._start_button: Optional[tk.Button] = None
        self._status_frame: Optional[tk.Frame] = None
        self._student_name_label: Optional[tk.Label] = None
        self._student_id_label: Optional[tk.Label] = None
        self._student_note_label: Optional[tk.Label] = None
        self._photo_label: Optional[tk.Label] = None
        self._button_present: Optional[tk.Button] = None
        self._button_leave: Optional[tk.Button] = None
        self._button_absent: Optional[tk.Button] = None
        self._button_late: Optional[tk.Button] = None

    # ------------------------------------------------------------------ UI --
    def show(self) -> None:
        print(f"[DEBUG] RollCallWindow.show() 被调用")
        print(f"[DEBUG] _root = {self._root}")
        if self._window and tk.Toplevel.winfo_exists(self._window):
            print(f"[DEBUG] 窗口已存在，提升到前台")
            self._window.lift()
            return

        print(f"[DEBUG] 创建新窗口")
        if not self._root:
            print(f"[DEBUG] 错误：_root 为 None，无法创建窗口")
            return
        
        self._window = tk.Toplevel(self._root)
        print(f"[DEBUG] Toplevel 窗口创建成功")
        self._window.title("唐老鸭点名")
        self._window.geometry("720x600")
        self._window.minsize(720, 600)
        self._window.protocol("WM_DELETE_WINDOW", self._handle_close)
        self._window.focus_set()  # 参考 CodeStatisticsUI 的写法
        print(f"[DEBUG] 窗口属性设置完成")

        container = tk.Frame(self._window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        config_frame = tk.LabelFrame(container, text="点名配置", padx=10, pady=10)
        config_frame.pack(fill=tk.X)
        self._build_config_frame(config_frame)

        self._status_frame = tk.LabelFrame(container, text="点名执行", padx=10, pady=10)
        self._status_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self._build_status_frame(self._status_frame)

        self._set_execution_controls(enabled=False)
        self._refresh_mode()
        
        print(f"[DEBUG] 窗口内容构建完成")

    def _build_config_frame(self, parent: tk.Frame) -> None:
        mode_frame = tk.Frame(parent)
        mode_frame.pack(fill=tk.X, pady=5)
        tk.Label(mode_frame, text="点名方式:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="全点", variable=self._mode_var, value="all", command=self._refresh_mode).pack(
            side=tk.LEFT, padx=5
        )
        tk.Radiobutton(
            mode_frame, text="抽点", variable=self._mode_var, value="partial", command=self._refresh_mode
        ).pack(side=tk.LEFT, padx=5)

        count_frame = tk.Frame(parent)
        count_frame.pack(fill=tk.X, pady=5)
        tk.Label(count_frame, text="抽点人数:", font=("Arial", 10)).pack(side=tk.LEFT)
        self._count_widgets = []
        for val in ["10", "15", "20", "custom"]:
            text = val if val != "custom" else "自定义"
            rb = tk.Radiobutton(
                count_frame,
                text=text,
                variable=self._count_choice,
                value=val,
                state=tk.DISABLED,
            )
            rb.pack(side=tk.LEFT, padx=3)
            self._count_widgets.append(rb)
        self._custom_entry = tk.Spinbox(
            count_frame,
            from_=1,
            to=100,
            textvariable=self._custom_count,
            width=5,
            state=tk.DISABLED,
        )
        self._custom_entry.pack(side=tk.LEFT, padx=5)

        strategy_frame = tk.Frame(parent)
        strategy_frame.pack(fill=tk.X, pady=5)
        tk.Label(strategy_frame, text="点名策略:", font=("Arial", 10)).pack(side=tk.LEFT)
        tk.Radiobutton(
            strategy_frame, text="随机选取", variable=self._strategy_var, value="random"
        ).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(
            strategy_frame, text="优先旷课最多", variable=self._strategy_var, value="most_absent"
        ).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(
            strategy_frame, text="优先点到最少", variable=self._strategy_var, value="least_called"
        ).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self._start_button = tk.Button(btn_frame, text="开始点名", command=self._handle_start, width=12, bg="#4CAF50", fg="white")
        self._start_button.pack(side=tk.LEFT)
        tk.Button(btn_frame, text="查看记录", command=self._handle_view_records, width=10, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=self._handle_close, width=10).pack(side=tk.LEFT, padx=8)

    def _build_status_frame(self, parent: tk.Frame) -> None:
        info_frame = tk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=5)

        self._photo_label = tk.Label(info_frame, text="照片预览", width=20, relief=tk.GROOVE)
        self._photo_label.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=40)

        text_frame = tk.Frame(info_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self._student_name_label = tk.Label(text_frame, text="姓名: -", font=("Arial", 14, "bold"))
        self._student_name_label.pack(anchor=tk.W, pady=2)
        self._student_id_label = tk.Label(text_frame, text="学号: -", font=("Arial", 12))
        self._student_id_label.pack(anchor=tk.W, pady=2)
        self._student_note_label = tk.Label(text_frame, text="状态提示: 等待开始", font=("Arial", 11), fg="#555555")
        self._student_note_label.pack(anchor=tk.W, pady=4)

        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=15)
        self._button_present = tk.Button(btn_frame, text="出勤", width=10, command=lambda: self._handle_mark("present"))
        self._button_leave = tk.Button(btn_frame, text="请假", width=10, command=lambda: self._handle_mark("leave"))
        self._button_absent = tk.Button(btn_frame, text="旷课", width=10, command=lambda: self._handle_mark("absent"))
        self._button_late = tk.Button(btn_frame, text="迟到", width=10, command=lambda: self._handle_mark("late"))

        self._button_present.pack(side=tk.LEFT, padx=5)
        self._button_leave.pack(side=tk.LEFT, padx=5)
        self._button_absent.pack(side=tk.LEFT, padx=5)
        self._button_late.pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------ Callbacks --
    def _handle_start(self) -> None:
        config = {
            "mode": self._mode_var.get(),
            "strategy": self._strategy_var.get(),
            "count_choice": self._count_choice.get(),
            "custom_count": self._custom_count.get(),
        }
        try:
            # 先启用执行控件，这样即使advance_student立即执行，按钮也是可用的
            self._set_execution_controls(enabled=True)
            self._on_start(config)
            self._set_config_controls(enabled=False)
        except Exception as exc:
            self._message_dialog.show_error(f"开始点名失败: {exc}")
            # 如果失败，恢复执行控件状态
            self._set_execution_controls(enabled=False)

    def _handle_mark(self, status: str) -> None:
        from tkinter import simpledialog

        # 调试信息
        print(f"[DEBUG] _handle_mark调用: status={status}, window._current_student={self._current_student is not None}")

        # 对于迟到补签，不需要检查_current_student，直接调用manager
        if status == "late":
            default_value = self._current_student.get("student_id") if self._current_student else ""
            target_id = simpledialog.askstring("迟到补签", "请输入要改为迟到的学号：", initialvalue=default_value, parent=self._window)
            if not target_id:
                return
            student_id = target_id.strip()
            try:
                self._on_mark(status, student_id)
            except Exception as exc:
                self._message_dialog.show_error(f"状态更新失败: {exc}")
            return

        # 对于其他状态，直接调用manager，让manager检查状态
        # manager会检查自己的_current_student，不依赖窗口的_current_student
        # 但如果窗口有_current_student，使用它的student_id
        student_id = None
        if self._current_student:
            student_id = self._current_student.get("student_id")
            print(f"[DEBUG] _handle_mark: 从窗口获取student_id={student_id}")
        else:
            print(f"[DEBUG] _handle_mark: 窗口_current_student为None，传递None给manager")
        
        try:
            self._on_mark(status, student_id)
        except Exception as exc:
            self._message_dialog.show_error(f"状态更新失败: {exc}")

    def _handle_view_records(self) -> None:
        """查看记录按钮处理"""
        if self._on_view_records:
            try:
                self._on_view_records()
            except Exception as e:
                if self._message_dialog:
                    self._message_dialog.show_error(f"打开记录窗口失败: {e}")
                print(f"[RollCallWindow] 打开记录窗口失败: {e}")
    
    def _handle_close(self) -> None:
        """关闭窗口处理"""
        try:
            if self._window and tk.Toplevel.winfo_exists(self._window):
                self._window.destroy()
        except Exception as e:
            print(f"[RollCallWindow] 关闭窗口时出错: {e}")
        finally:
            self._window = None
            if self._on_close:
                self._on_close()

    # ------------------------------------------------------------- Helpers --
    def _refresh_mode(self) -> None:
        is_partial = self._mode_var.get() == "partial"
        state = tk.NORMAL if is_partial else tk.DISABLED
        for widget in getattr(self, "_count_widgets", []):
            widget.config(state=state)
        self._custom_entry.config(state=state)

    def set_student(self, student_info: Dict[str, Any]) -> None:
        """设置当前学生信息（确保与manager同步）"""
        # 确保student_info不为None
        if not student_info:
            print(f"[DEBUG] set_student: student_info为None")
            return
        
        # 设置窗口的_current_student（重要：必须在更新UI之前设置）
        self._current_student = student_info
        
        if not self._student_name_label:
            print(f"[DEBUG] set_student: _student_name_label为None，但_current_student已设置")
            return
        
        name = student_info.get("name", "-")
        student_id = student_info.get("student_id", "-")
        note = student_info.get("note", "")
        self._student_name_label.config(text=f"姓名: {name}")
        self._student_id_label.config(text=f"学号: {student_id}")
        self._student_note_label.config(text=f"状态提示: {note}")

        photo_path = student_info.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            self._photo_label.config(text=f"照片：{os.path.basename(photo_path)}")
        else:
            self._photo_label.config(text="照片：暂无")
        
        # 调试信息
        print(f"[DEBUG] set_student完成: 学生 {student_id} - {name}, _current_student已设置: {self._current_student is not None}")

    def show_message(self, message: str) -> None:
        if self._student_note_label:
            self._student_note_label.config(text=f"状态提示: {message}")

    def _set_config_controls(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED

        def set_state(widget):
            if isinstance(widget, (tk.Button, tk.Radiobutton, tk.Spinbox)):
                widget.config(state=state)

        if self._window:
            for child in self._window.winfo_children():
                if isinstance(child, tk.LabelFrame) and child.cget("text") == "点名配置":
                    for widget in child.winfo_children():
                        set_state(widget)

        if self._start_button:
            self._start_button.config(state=state)

    def _set_execution_controls(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for btn in [self._button_present, self._button_leave, self._button_absent, self._button_late]:
            if btn:
                btn.config(state=state)


