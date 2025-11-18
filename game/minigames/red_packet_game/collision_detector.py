#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包碰撞检测器
"""

import pygame
from typing import List, Tuple, Optional
from .red_packet import RedPacket
from core.physics_system import CollisionDetector as BaseCollisionDetector


class RedPacketCollisionDetector:
    """红包碰撞检测器"""
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        初始化碰撞检测器
        
        Args:
            screen_width, screen_height: 屏幕尺寸
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.collision_detector = BaseCollisionDetector()
    
    def check_duckling_collision(
        self, packet: RedPacket, duckling_positions: List[Tuple[float, float]], 
        duckling_size: int
    ) -> Optional[int]:
        """
        检查与小鸭的碰撞
        
        Args:
            packet: 红包对象
            duckling_positions: 小鸭位置列表 [(x, y), ...]
            duckling_size: 小鸭尺寸
            
        Returns:
            Optional[int]: 碰撞的小鸭索引，如果未碰撞返回None
        """
        packet_rect = packet.get_rect()
        
        for i, (duck_x, duck_y) in enumerate(duckling_positions):
            duckling_rect = pygame.Rect(duck_x, duck_y, duckling_size, duckling_size)
            
            if self.collision_detector.check_rect_collision(packet_rect, duckling_rect):
                return i
        
        return None
    
    def check_wall_collision(self, packet: RedPacket) -> bool:
        """
        检查墙壁碰撞
        
        Args:
            packet: 红包对象
            
        Returns:
            bool: 是否碰撞墙壁
        """
        x, y = packet.get_position()
        width, height = packet.width, packet.height
        
        return (x <= 0 or x >= self.screen_width - width or
                y <= 0 or y >= self.screen_height - height)
    
    def check_donald_collision(
        self, packet: RedPacket, donald_pos: Tuple[float, float], donald_size: int
    ) -> bool:
        """
        检查与唐老鸭的碰撞
        
        Args:
            packet: 红包对象
            donald_pos: 唐老鸭位置 (x, y)
            donald_size: 唐老鸭尺寸
            
        Returns:
            bool: 是否碰撞
        """
        packet_rect = packet.get_rect()
        donald_rect = pygame.Rect(donald_pos[0], donald_pos[1], donald_size, donald_size)
        
        return self.collision_detector.check_rect_collision(packet_rect, donald_rect)
    
    def handle_collision(
        self, packet: RedPacket, collision_type: str, data: dict = None
    ) -> bool:
        """
        处理碰撞
        
        Args:
            packet: 红包对象
            collision_type: 碰撞类型 ('duckling', 'wall', 'donald')
            data: 额外数据
            
        Returns:
            bool: 是否成功处理
        """
        if collision_type == 'wall':
            packet.deactivate('wall')
            return True
        elif collision_type == 'duckling':
            packet.deactivate('caught')
            return True
        elif collision_type == 'donald':
            # 可以添加特殊处理逻辑
            return False
        
        return False

