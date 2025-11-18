#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移动控制器
"""

import pygame
import random
import math
from typing import List, Tuple, Optional
from .red_packet import RedPacket
from core.physics_system import MovementController as BaseMovementController


class DucklingMovementController:
    """小鸭移动控制器"""
    
    def __init__(
        self, duckling_positions: List[Tuple[float, float]],
        screen_width: int, screen_height: int, duckling_size: int
    ):
        """
        初始化小鸭移动控制器
        
        Args:
            duckling_positions: 小鸭位置列表（会被修改）
            screen_width, screen_height: 屏幕尺寸
            duckling_size: 小鸭尺寸
        """
        self.duckling_positions = duckling_positions
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.duckling_size = duckling_size
        self.movement_data: List[dict] = []
        self.moving = False
        self.movement_controller = BaseMovementController()
    
    def start_movement(self):
        """开始移动"""
        self.moving = True
        self._initialize_movement_data()
    
    def stop_movement(self):
        """停止移动"""
        self.moving = False
    
    def _initialize_movement_data(self):
        """初始化移动数据"""
        if not self.movement_data:
            for _ in range(len(self.duckling_positions)):
                speed = random.uniform(2.5, 4.0)  # 与红包接近的速度
                angle = random.uniform(0, 2 * math.pi)
                dx = math.cos(angle) * speed
                dy = math.sin(angle) * speed
                self.movement_data.append({
                    'dx': dx,
                    'dy': dy,
                })
    
    def update(self, dt: float = 1.0, donald_pos: Optional[Tuple[float, float]] = None, 
               donald_size: int = 80):
        """
        更新小鸭位置
        
        Args:
            dt: 时间增量
            donald_pos: 唐老鸭位置（用于避开）
            donald_size: 唐老鸭尺寸
        """
        if not self.moving:
            return
        
        self._initialize_movement_data()
        
        for i in range(len(self.duckling_positions)):
            movement = self.movement_data[i]
            current_x, current_y = self.duckling_positions[i]
            
            step = dt * 60.0  # 将秒为单位的dt换算为帧步长
            new_x = current_x + movement['dx'] * step
            new_y = current_y + movement['dy'] * step
            
            # 边界反弹
            new_x, new_y, new_dx, new_dy = self.movement_controller.apply_bounce(
                new_x, new_y, movement['dx'], movement['dy'],
                self.screen_width, self.screen_height,
                self.duckling_size, self.duckling_size
            )
            
            movement['dx'] = new_dx
            movement['dy'] = new_dy
            
            # 避开唐老鸭
            if donald_pos:
                donald_rect = pygame.Rect(donald_pos[0], donald_pos[1], donald_size, donald_size)
                duckling_rect = pygame.Rect(new_x, new_y, self.duckling_size, self.duckling_size)
                
                if duckling_rect.colliderect(donald_rect):
                    new_x, new_y, new_dx, new_dy = self.movement_controller.avoid_collision(
                        new_x, new_y, movement['dx'], movement['dy'],
                        donald_rect, self.duckling_size, self.duckling_size
                    )
                    movement['dx'] = new_dx
                    movement['dy'] = new_dy
            
            # 更新位置
            self.duckling_positions[i] = (new_x, new_y)
    
    def reset_positions(self, original_positions: List[Tuple[float, float]]):
        """重置位置到原始位置"""
        self.duckling_positions[:] = original_positions[:]
        self.movement_data.clear()


class RedPacketMovementController:
    """红包移动控制器"""
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        初始化红包移动控制器
        
        Args:
            screen_width, screen_height: 屏幕尺寸
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.movement_controller = BaseMovementController()
    
    def update(self, packet: RedPacket, dt: float = 1.0):
        """
        更新红包位置
        
        Args:
            packet: 红包对象
            dt: 时间增量
        """
        if not packet.is_active():
            return
        
        packet.update(dt)
        
        # 边界检查（但不限制，让碰撞检测器处理）
        x, y = packet.get_position()
        width, height = packet.width, packet.height
        
        # 可以在这里添加物理效果（重力、摩擦力等）
        # 目前保持简单的线性移动

