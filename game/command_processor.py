#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令处理器：统一处理用户命令，支持命令注册和扩展。
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple


class CommandHandler:
    """命令处理器基类"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化命令处理器。

        Args:
            name: 命令名称（用于注册和识别）
            description: 命令描述（用于帮助信息）
        """
        self.name = name
        self.description = description

    def match(self, user_input: str) -> bool:
        """
        检查用户输入是否匹配此命令。

        Args:
            user_input: 用户输入文本

        Returns:
            True if input matches this command, False otherwise
        """
        raise NotImplementedError

    def execute(self, user_input: str, context: Dict) -> bool:
        """
        执行命令。

        Args:
            user_input: 用户输入文本
            context: 执行上下文（包含DuckGame实例等）

        Returns:
            True if command was handled, False otherwise
        """
        raise NotImplementedError


class PatternCommandHandler(CommandHandler):
    """基于模式匹配的命令处理器"""

    def __init__(
        self,
        name: str,
        patterns: List[str],
        handler: Callable[[str, Dict], None],
        description: str = "",
    ):
        """
        初始化模式匹配命令处理器。

        Args:
            name: 命令名称
            patterns: 匹配模式列表（支持字符串包含和正则表达式）
            handler: 处理函数，接收(user_input, context)参数
            description: 命令描述
        """
        super().__init__(name, description)
        self.patterns = patterns
        self.handler = handler
        self._compiled_patterns: List[re.Pattern] = []

        # 编译正则表达式模式
        for pattern in patterns:
            if pattern.startswith("^") or pattern.startswith(".*"):
                # 正则表达式模式
                try:
                    self._compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    # 如果编译失败，作为普通字符串处理
                    self._compiled_patterns.append(None)
            else:
                # 普通字符串模式
                self._compiled_patterns.append(None)

    def match(self, user_input: str) -> bool:
        """检查用户输入是否匹配命令模式。"""
        user_input_lower = user_input.lower().strip()

        for i, pattern in enumerate(self.patterns):
            compiled = self._compiled_patterns[i]

            if compiled:
                # 使用正则表达式匹配
                if compiled.search(user_input):
                    return True
            else:
                # 使用字符串包含匹配
                if pattern.lower() in user_input_lower:
                    return True

        return False

    def execute(self, user_input: str, context: Dict) -> bool:
        """执行命令处理函数。"""
        try:
            self.handler(user_input, context)
            return True
        except Exception as e:
            print(f"[CommandProcessor] 执行命令 '{self.name}' 时出错: {e}")
            import traceback
            traceback.print_exc()
            return False


class CommandProcessor:
    """统一处理用户命令，支持命令注册和扩展。"""

    def __init__(self):
        """初始化命令处理器。"""
        self._handlers: List[Tuple[int, CommandHandler]] = []
        self._default_handler: Optional[Callable[[str, Dict], None]] = None

    def register(
        self,
        name: str,
        patterns: List[str],
        handler: Callable[[str, Dict], None],
        description: str = "",
        priority: int = 0,
    ) -> None:
        """
        注册命令处理器。

        Args:
            name: 命令名称
            patterns: 匹配模式列表
            handler: 处理函数，接收(user_input, context)参数
            description: 命令描述
            priority: 优先级（数字越大优先级越高，默认0）
        """
        command_handler = PatternCommandHandler(name, patterns, handler, description)
        self._handlers.append((priority, command_handler))
        # 按优先级排序（优先级高的在前）
        self._handlers.sort(key=lambda item: item[0])
        print(f"[CommandProcessor] 注册命令: {name} (模式: {patterns})")

    def register_handler(self, handler: CommandHandler, priority: int = 0) -> None:
        """
        注册命令处理器对象。

        Args:
            handler: 命令处理器对象
            priority: 优先级
        """
        self._handlers.append((priority, handler))
        self._handlers.sort(key=lambda item: item[0])
        print(f"[CommandProcessor] 注册命令处理器: {handler.name}")

    def set_default_handler(self, handler: Callable[[str, Dict], None]) -> None:
        """
        设置默认处理器（当没有命令匹配时调用）。

        Args:
            handler: 默认处理函数，接收(user_input, context)参数
        """
        self._default_handler = handler

    def process(self, user_input: str, context: Dict) -> bool:
        """
        处理用户输入，匹配并执行相应的命令。

        Args:
            user_input: 用户输入文本
            context: 执行上下文

        Returns:
            True if a command was matched and executed, False otherwise
        """
        user_input = user_input.strip()
        if not user_input:
            return False

        # 按注册顺序匹配命令（后注册的优先级更高）
        for priority, handler in sorted(self._handlers, key=lambda item: item[0], reverse=True):
            if handler.match(user_input):
                print(f"[CommandProcessor] 匹配命令: {handler.name}")
                if handler.execute(user_input, context):
                    return True

        # 如果没有匹配的命令，使用默认处理器
        if self._default_handler:
            try:
                self._default_handler(user_input, context)
                return True
            except Exception as e:
                print(f"[CommandProcessor] 默认处理器执行失败: {e}")
                return False

        return False

    def get_commands(self) -> List[Tuple[str, str]]:
        """
        获取所有已注册的命令列表。

        Returns:
            命令列表，每个元素为(name, description)元组
        """
        sorted_handlers = sorted(self._handlers, key=lambda item: item[0], reverse=True)
        return [(handler.name, handler.description) for _, handler in sorted_handlers]

    def get_help_text(self) -> str:
        """
        生成帮助文本。

        Returns:
            帮助文本字符串
        """
        lines = ["可用命令："]
        for _, handler in sorted(self._handlers, key=lambda item: item[0], reverse=True):
            if handler.description:
                lines.append(f"  - {handler.name}: {handler.description}")
            else:
                lines.append(f"  - {handler.name}")
        return "\n".join(lines)

    def clear(self) -> None:
        """清空所有已注册的命令处理器。"""
        self._handlers.clear()
        self._default_handler = None

