#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件系统 - 解耦模块间通信（观察者模式）
"""

from typing import Callable, Dict, List, Any, Optional
from enum import Enum


class GameEvent(Enum):
    """游戏事件枚举"""
    # 红包游戏事件
    RED_PACKET_SPAWNED = "red_packet_spawned"
    RED_PACKET_CAUGHT = "red_packet_caught"
    RED_PACKET_HIT_WALL = "red_packet_hit_wall"
    RED_PACKET_DEACTIVATED = "red_packet_deactivated"
    
    # 小鸭事件
    DUCKLING_MOVED = "duckling_moved"
    DUCKLING_CAUGHT_PACKET = "duckling_caught_packet"
    
    # 游戏事件
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    GAME_PAUSED = "game_paused"
    GAME_RESUMED = "game_resumed"
    
    # UI事件
    DIALOG_OPENED = "dialog_opened"
    DIALOG_CLOSED = "dialog_closed"
    
    # 代码统计事件
    CODE_COUNTING_STARTED = "code_counting_started"
    CODE_COUNTING_COMPLETED = "code_counting_completed"
    
    # AI对话事件
    AI_CHAT_STARTED = "ai_chat_started"
    AI_RESPONSE_RECEIVED = "ai_response_received"


class EventManager:
    """事件管理器"""
    
    def __init__(self):
        self._subscribers: Dict[GameEvent, List[Callable[[Any], None]]] = {}
    
    def subscribe(self, event_type: GameEvent, callback: Callable[[Any], None]):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，参数为事件数据
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: GameEvent, callback: Callable[[Any], None]):
        """取消订阅事件"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def emit(self, event_type: GameEvent, data: Any = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"事件回调错误 [{event_type.value}]: {e}")
    
    def clear(self):
        """清空所有订阅"""
        self._subscribers.clear()
    
    def get_subscriber_count(self, event_type: GameEvent) -> int:
        """获取指定事件的订阅者数量"""
        if event_type in self._subscribers:
            return len(self._subscribers[event_type])
        return 0

