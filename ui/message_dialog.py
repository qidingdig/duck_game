#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
消息对话框工具：统一的消息框接口，支持未来替换UI库。
"""

from __future__ import annotations

from typing import Optional

try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    tk = None
    messagebox = None


class MessageDialogHelper:
    """统一的消息框工具，提供线程安全的消息显示接口。"""

    def __init__(self, tk_root: Optional[tk.Misc] = None):
        """
        初始化消息对话框助手。

        Args:
            tk_root: Tkinter根窗口，如果为None则尝试自动获取
        """
        self._root = tk_root
        self._default_title = "Duck Game"

    def set_default_title(self, title: str) -> None:
        """设置默认对话框标题。"""
        self._default_title = title

    def _ensure_root(self) -> bool:
        """确保有可用的Tk根窗口。"""
        if self._root:
            return True

        if not HAS_TKINTER:
            print("[MessageDialog] Tkinter不可用，无法显示消息框")
            return False

        try:
            # 尝试获取默认根窗口
            self._root = tk._default_root
            if self._root:
                return True
        except Exception:
            pass

        print("[MessageDialog] 无法获取Tk根窗口，消息框将使用print输出")
        return False

    def show_error(self, message: str, title: Optional[str] = None) -> None:
        """
        显示错误消息框。

        Args:
            message: 错误消息内容
            title: 对话框标题，如果为None则使用默认标题
        """
        if not self._ensure_root():
            print(f"[错误] {title or self._default_title}: {message}")
            return

        try:
            messagebox.showerror(title or self._default_title, message)
        except Exception as e:
            print(f"[MessageDialog] 显示错误消息框失败: {e}")
            print(f"[错误] {title or self._default_title}: {message}")

    def show_warning(self, message: str, title: Optional[str] = None) -> None:
        """
        显示警告消息框。

        Args:
            message: 警告消息内容
            title: 对话框标题，如果为None则使用默认标题
        """
        if not self._ensure_root():
            print(f"[警告] {title or self._default_title}: {message}")
            return

        try:
            messagebox.showwarning(title or self._default_title, message)
        except Exception as e:
            print(f"[MessageDialog] 显示警告消息框失败: {e}")
            print(f"[警告] {title or self._default_title}: {message}")

    def show_info(self, message: str, title: Optional[str] = None) -> None:
        """
        显示信息消息框。

        Args:
            message: 信息消息内容
            title: 对话框标题，如果为None则使用默认标题
        """
        if not self._ensure_root():
            print(f"[信息] {title or self._default_title}: {message}")
            return

        try:
            messagebox.showinfo(title or self._default_title, message)
        except Exception as e:
            print(f"[MessageDialog] 显示信息消息框失败: {e}")
            print(f"[信息] {title or self._default_title}: {message}")

    def ask_yes_no(self, message: str, title: Optional[str] = None) -> bool:
        """
        显示是/否确认对话框。

        Args:
            message: 确认消息内容
            title: 对话框标题，如果为None则使用默认标题

        Returns:
            True if user clicked Yes, False otherwise
        """
        if not self._ensure_root():
            print(f"[确认] {title or self._default_title}: {message}")
            return False

        try:
            return messagebox.askyesno(title or self._default_title, message)
        except Exception as e:
            print(f"[MessageDialog] 显示确认对话框失败: {e}")
            print(f"[确认] {title or self._default_title}: {message}")
            return False

    def ask_ok_cancel(self, message: str, title: Optional[str] = None) -> bool:
        """
        显示确定/取消确认对话框。

        Args:
            message: 确认消息内容
            title: 对话框标题，如果为None则使用默认标题

        Returns:
            True if user clicked OK, False otherwise
        """
        if not self._ensure_root():
            print(f"[确认] {title or self._default_title}: {message}")
            return False

        try:
            return messagebox.askokcancel(title or self._default_title, message)
        except Exception as e:
            print(f"[MessageDialog] 显示确认对话框失败: {e}")
            print(f"[确认] {title or self._default_title}: {message}")
            return False

