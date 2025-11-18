#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包生成器
"""

import random
from typing import Callable, Optional
from .red_packet import RedPacket
from core.event_system import EventManager, GameEvent


class RedPacketSpawner:
    """红包生成器"""
    
    def __init__(self, event_manager: Optional[EventManager] = None):
        """
        初始化生成器
        
        Args:
            event_manager: 事件管理器（可选）
        """
        self.event_manager = event_manager
        self.spawn_rate = 30  # 每30帧生成一个
        self.spawn_timer = 0
        self.paused = False
        self.spawn_position_strategy: Optional[Callable[[], tuple]] = None
    
    def set_spawn_rate(self, rate: int):
        """
        设置生成频率
        
        Args:
            rate: 每多少帧生成一个红包
        """
        self.spawn_rate = max(1, rate)
    
    def set_spawn_position_strategy(self, strategy: Callable[[], tuple]):
        """
        设置生成位置策略
        
        Args:
            strategy: 返回 (x, y) 的函数
        """
        self.spawn_position_strategy = strategy
    
    def spawn(self, default_x: float = 0, default_y: float = 0) -> RedPacket:
        """
        生成红包
        
        Args:
            default_x, default_y: 默认生成位置
            
        Returns:
            RedPacket: 生成的红包对象
        """
        # 确定生成位置
        if self.spawn_position_strategy:
            x, y = self.spawn_position_strategy()
        else:
            x, y = default_x, default_y
        
        # 随机选择红包类型
        packet_type = random.randint(0, 2)
        packet = RedPacket(x, y, packet_type)
        
        # 发布事件
        if self.event_manager:
            self.event_manager.emit(GameEvent.RED_PACKET_SPAWNED, packet)
        
        return packet
    
    def update(self, dt: float = 1.0) -> Optional[RedPacket]:
        """
        更新生成逻辑
        
        Args:
            dt: 时间增量
            
        Returns:
            Optional[RedPacket]: 如果生成了红包则返回，否则返回None
        """
        if self.paused:
            return None
        
        self.spawn_timer += dt
        
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            return self.spawn()
        
        return None
    
    def pause(self):
        """暂停生成"""
        self.paused = True
    
    def resume(self):
        """恢复生成"""
        self.paused = False
    
    def reset_timer(self):
        """重置计时器"""
        self.spawn_timer = 0

