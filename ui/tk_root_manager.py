#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tkinter根窗口管理器：统一管理Tk根窗口的创建、事件循环、更新频率。
"""

from __future__ import annotations

from typing import Optional

import tkinter as tk


class TkRootManager:
    """统一管理Tkinter根窗口的生命周期和事件循环。"""

    def __init__(self, update_interval: int = 5):
        """
        初始化Tk根窗口管理器。

        Args:
            update_interval: 每N帧调用一次update()，默认5帧（约83ms）
        """
        self._root: Optional[tk.Tk] = None
        self._update_counter: int = 0
        self._update_interval: int = max(update_interval, 1)
        self._initialized: bool = False

    def initialize(self) -> bool:
        """
        初始化Tk根窗口。

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return self._root is not None

        try:
            self._root = tk.Tk()
            self._root.withdraw()  # 隐藏根窗口
            self._root.protocol("WM_DELETE_WINDOW", lambda: None)  # 防止关闭根窗口
            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化Tkinter root时出错: {e}")
            self._root = None
            self._initialized = False
            return False

    def get_root(self) -> Optional[tk.Tk]:
        """
        获取Tk根窗口引用。

        Returns:
            Tk根窗口对象，如果未初始化则返回None
        """
        return self._root

    def is_initialized(self) -> bool:
        """检查根窗口是否已初始化。"""
        return self._initialized and self._root is not None

    def update_loop(self, has_active_windows: bool) -> None:
        """
        在主循环中调用，更新Tkinter事件循环。

        Args:
            has_active_windows: 是否有活跃的Tk窗口需要更新
        """
        if not self.is_initialized() or not has_active_windows:
            return

        try:
            self._update_counter += 1
            # 每帧都调用update_idletasks()，确保UI更新
            self._root.update_idletasks()

            # 每N帧调用一次update()，处理键盘和关闭事件
            if self._update_counter % self._update_interval == 0:
                try:
                    self._root.update()
                except (tk.TclError, RuntimeError, Exception):
                    # 忽略所有错误，确保程序继续运行
                    pass
        except Exception:
            # 忽略所有异常，确保游戏主循环不受影响
            pass

    def reset_update_counter(self) -> None:
        """重置更新计数器（通常不需要手动调用）。"""
        self._update_counter = 0

    def shutdown(self) -> None:
        """关闭根窗口（通常在程序退出时调用）。"""
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
            finally:
                self._root = None
                self._initialized = False

