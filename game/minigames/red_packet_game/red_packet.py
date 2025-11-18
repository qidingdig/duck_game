#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包实体类
"""

import pygame
import random
from typing import Tuple


class RedPacket:
    """红包实体类"""
    
    # 红包类型配置
    PACKET_TYPES = {
        0: {  # 小红包
            'size': (30, 40),
            'color': (255, 0, 0),
            'amount_range': (1, 10)
        },
        1: {  # 中红包
            'size': (50, 60),
            'color': (255, 100, 100),
            'amount_range': (10, 50)
        },
        2: {  # 大红包
            'size': (70, 80),
            'color': (200, 0, 0),
            'amount_range': (50, 100)
        }
    }
    
    def __init__(self, x: float, y: float, packet_type: int = 0):
        """
        初始化红包
        
        Args:
            x, y: 初始位置
            packet_type: 红包类型 (0: 小红包, 1: 中红包, 2: 大红包)
        """
        self.x = x
        self.y = y
        self.packet_type = packet_type
        
        # 从配置获取属性
        config = self.PACKET_TYPES[packet_type]
        self.width, self.height = config['size']
        self.color = config['color']
        
        # 随机生成金额
        min_amount, max_amount = config['amount_range']
        self.amount = round(random.uniform(min_amount, max_amount), 2)
        
        # 移动相关
        self.dx = random.uniform(-3, 3)
        self.dy = random.uniform(-3, 3)
        
        # 状态
        self.active = True
        self.hit_wall = False
    
    def update(self, dt: float = 1.0):
        """
        更新红包位置
        
        Args:
            dt: 时间增量（用于平滑移动）
        """
        if not self.active:
            return
        
        step = dt * 60.0  # 将秒为单位的dt换算为帧步长，保持原有速度感
        self.x += self.dx * step
        self.y += self.dy * step
    
    def get_rect(self) -> pygame.Rect:
        """获取碰撞矩形"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_amount(self) -> float:
        """获取金额"""
        return self.amount
    
    def get_type(self) -> int:
        """获取红包类型"""
        return self.packet_type
    
    def is_active(self) -> bool:
        """是否激活"""
        return self.active
    
    def deactivate(self, reason: str = "unknown"):
        """
        停用红包
        
        Args:
            reason: 停用原因 ('wall', 'caught', 'other')
        """
        self.active = False
        if reason == 'wall':
            self.hit_wall = True
    
    def set_velocity(self, dx: float, dy: float):
        """设置速度"""
        self.dx = dx
        self.dy = dy
    
    def get_position(self) -> Tuple[float, float]:
        """获取位置"""
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        """设置位置"""
        self.x = x
        self.y = y

