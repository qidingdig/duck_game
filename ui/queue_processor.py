#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI队列处理器：统一处理UI队列消息，解耦消息类型与处理逻辑。
"""

from __future__ import annotations

import traceback
from queue import Queue
from typing import Any, Callable, Dict, Optional


class UIQueueProcessor:
    """统一处理UI队列消息，支持消息类型注册和批量处理。"""

    def __init__(self):
        """初始化队列处理器。"""
        self._handlers: Dict[str, Callable[[tuple], None]] = {}

    def register_handler(self, message_type: str, handler: Callable[[tuple], None]) -> None:
        """
        注册消息处理器。

        Args:
            message_type: 消息类型（如 "append_text", "show_charts"）
            handler: 处理函数，接收消息元组作为参数
        """
        if not isinstance(message_type, str) or not message_type:
            raise ValueError("message_type must be a non-empty string")
        if not callable(handler):
            raise ValueError("handler must be callable")

        self._handlers[message_type] = handler

    def unregister_handler(self, message_type: str) -> None:
        """
        取消注册消息处理器。

        Args:
            message_type: 要取消的消息类型
        """
        self._handlers.pop(message_type, None)

    def process_queue(self, queue: Queue, limit_per_frame: int = 20) -> int:
        """
        处理队列中的消息。

        Args:
            queue: UI消息队列
            limit_per_frame: 每帧最多处理的消息数量

        Returns:
            实际处理的消息数量
        """
        if not queue:
            return 0

        processed = 0
        while not queue.empty() and processed < limit_per_frame:
            try:
                item = queue.get_nowait()
            except Exception:
                break

            processed += 1

            if not item:
                continue

            if not isinstance(item, (tuple, list)) or len(item) == 0:
                print(f"[UIQueueProcessor] 无效的消息格式: {item}")
                continue

            message_type = item[0]
            handler = self._handlers.get(message_type)

            if handler:
                try:
                    handler(item)
                except Exception as e:
                    print(f"[UIQueueProcessor] 处理消息 '{message_type}' 时出错: {e}")
                    traceback.print_exc()
            else:
                print(f"[UIQueueProcessor] 未注册的消息类型: {message_type}")

        return processed

    def has_handler(self, message_type: str) -> bool:
        """检查是否已注册指定类型的处理器。"""
        return message_type in self._handlers

    def get_registered_types(self) -> list[str]:
        """获取所有已注册的消息类型。"""
        return list(self._handlers.keys())

    def clear_handlers(self) -> None:
        """清空所有已注册的处理器。"""
        self._handlers.clear()

