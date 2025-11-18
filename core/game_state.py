#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏状态管理器 - 统一管理游戏状态（状态机模式）
"""

from enum import Enum
from typing import Callable, List, Optional


class GameState(Enum):
    """游戏状态枚举"""
    IDLE = "idle"  # 空闲状态
    RED_PACKET_GAME = "red_packet_game"  # 红包游戏
    CODE_COUNTING = "code_counting"  # 代码统计
    AI_CHAT = "ai_chat"  # AI对话
    DIALOG_OPEN = "dialog_open"  # 对话框打开


class GameStateManager:
    """游戏状态管理器"""
    
    def __init__(self):
        self._current_state = GameState.IDLE
        self._previous_state = None
        self._state_listeners: List[Callable[[GameState, GameState], None]] = []
    
    def set_state(self, new_state: GameState) -> bool:
        """
        切换游戏状态
        
        Args:
            new_state: 新状态
            
        Returns:
            bool: 是否成功切换
        """
        if new_state == self._current_state:
            return False
        
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state
        
        # 通知所有监听器
        for listener in self._state_listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                print(f"状态监听器错误: {e}")
        
        return True
    
    def get_state(self) -> GameState:
        """获取当前状态"""
        return self._current_state
    
    def get_previous_state(self) -> Optional[GameState]:
        """获取上一个状态"""
        return self._previous_state
    
    def is_state(self, state: GameState) -> bool:
        """检查是否为指定状态"""
        return self._current_state == state
    
    def add_state_listener(self, callback: Callable[[GameState, GameState], None]):
        """
        添加状态变化监听器
        
        Args:
            callback: 回调函数，参数为 (old_state, new_state)
        """
        if callback not in self._state_listeners:
            self._state_listeners.append(callback)
    
    def remove_state_listener(self, callback: Callable[[GameState, GameState], None]):
        """移除状态变化监听器"""
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)
    
    def clear_listeners(self):
        """清空所有监听器"""
        self._state_listeners.clear()

