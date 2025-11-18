#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物理系统 - 碰撞检测和移动计算
"""

import pygame
from typing import Tuple, Optional, List


class CollisionDetector:
    """碰撞检测器"""
    
    @staticmethod
    def check_rect_collision(rect1: pygame.Rect, rect2: pygame.Rect) -> bool:
        """
        检查矩形碰撞
        
        Args:
            rect1: 矩形1
            rect2: 矩形2
            
        Returns:
            bool: 是否碰撞
        """
        return rect1.colliderect(rect2)
    
    @staticmethod
    def check_circle_collision(
        center1: Tuple[float, float], radius1: float,
        center2: Tuple[float, float], radius2: float
    ) -> bool:
        """
        检查圆形碰撞
        
        Args:
            center1: 圆心1坐标
            radius1: 半径1
            center2: 圆心2坐标
            radius2: 半径2
            
        Returns:
            bool: 是否碰撞
        """
        dx = center1[0] - center2[0]
        dy = center1[1] - center2[1]
        distance = (dx * dx + dy * dy) ** 0.5
        return distance < (radius1 + radius2)
    
    @staticmethod
    def check_point_in_rect(point: Tuple[float, float], rect: pygame.Rect) -> bool:
        """
        检查点是否在矩形内
        
        Args:
            point: 点坐标
            rect: 矩形
            
        Returns:
            bool: 点是否在矩形内
        """
        return rect.collidepoint(point)
    
    @staticmethod
    def get_collision_response(
        rect1: pygame.Rect, rect2: pygame.Rect
    ) -> Optional[Tuple[float, float]]:
        """
        获取碰撞响应向量（用于分离物体）
        
        Args:
            rect1: 矩形1
            rect2: 矩形2
            
        Returns:
            Optional[Tuple[float, float]]: 分离向量 (dx, dy)，如果未碰撞返回None
        """
        if not rect1.colliderect(rect2):
            return None
        
        # 计算重叠区域
        overlap_left = rect1.right - rect2.left
        overlap_right = rect2.right - rect1.left
        overlap_top = rect1.bottom - rect2.top
        overlap_bottom = rect2.bottom - rect1.top
        
        # 找到最小重叠方向
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
        
        if min_overlap == overlap_left:
            return (-overlap_left, 0)
        elif min_overlap == overlap_right:
            return (overlap_right, 0)
        elif min_overlap == overlap_top:
            return (0, -overlap_top)
        else:
            return (0, overlap_bottom)
    
    @staticmethod
    def check_multiple_collisions(
        target_rect: pygame.Rect, other_rects: List[pygame.Rect]
    ) -> List[pygame.Rect]:
        """
        检查与多个矩形的碰撞
        
        Args:
            target_rect: 目标矩形
            other_rects: 其他矩形列表
            
        Returns:
            List[pygame.Rect]: 碰撞的矩形列表
        """
        collisions = []
        for rect in other_rects:
            if target_rect.colliderect(rect):
                collisions.append(rect)
        return collisions


class MovementController:
    """移动控制器"""
    
    @staticmethod
    def apply_movement(
        x: float, y: float, dx: float, dy: float,
        screen_width: int, screen_height: int,
        obj_width: int = 0, obj_height: int = 0
    ) -> Tuple[float, float]:
        """
        应用移动并处理边界
        
        Args:
            x, y: 当前位置
            dx, dy: 移动增量
            screen_width, screen_height: 屏幕尺寸
            obj_width, obj_height: 对象尺寸
            
        Returns:
            Tuple[float, float]: 新位置 (x, y)
        """
        new_x = x + dx
        new_y = y + dy
        
        # 边界限制
        new_x = max(0, min(new_x, screen_width - obj_width))
        new_y = max(0, min(new_y, screen_height - obj_height))
        
        return new_x, new_y
    
    @staticmethod
    def check_boundary(
        x: float, y: float,
        screen_width: int, screen_height: int,
        obj_width: int, obj_height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        检查边界碰撞
        
        Args:
            x, y: 位置
            screen_width, screen_height: 屏幕尺寸
            obj_width, obj_height: 对象尺寸
            
        Returns:
            Tuple[bool, Optional[str]]: (是否碰撞, 碰撞边界: 'left'/'right'/'top'/'bottom')
        """
        if x <= 0:
            return True, 'left'
        if x >= screen_width - obj_width:
            return True, 'right'
        if y <= 0:
            return True, 'top'
        if y >= screen_height - obj_height:
            return True, 'bottom'
        return False, None
    
    @staticmethod
    def apply_bounce(
        x: float, y: float, dx: float, dy: float,
        screen_width: int, screen_height: int,
        obj_width: int, obj_height: int
    ) -> Tuple[float, float, float, float]:
        """
        应用边界反弹
        
        Args:
            x, y: 当前位置
            dx, dy: 当前速度
            screen_width, screen_height: 屏幕尺寸
            obj_width, obj_height: 对象尺寸
            
        Returns:
            Tuple[float, float, float, float]: (新x, 新y, 新dx, 新dy)
        """
        new_x, new_y = x, y
        new_dx, new_dy = dx, dy
        
        # 检查并处理边界
        if x <= 0:
            new_x = 0
            new_dx = abs(dx)  # 反弹
        elif x >= screen_width - obj_width:
            new_x = screen_width - obj_width
            new_dx = -abs(dx)  # 反弹
        
        if y <= 0:
            new_y = 0
            new_dy = abs(dy)  # 反弹
        elif y >= screen_height - obj_height:
            new_y = screen_height - obj_height
            new_dy = -abs(dy)  # 反弹
        
        return new_x, new_y, new_dx, new_dy
    
    @staticmethod
    def avoid_collision(
        x: float, y: float, dx: float, dy: float,
        avoid_rect: pygame.Rect,
        obj_width: int, obj_height: int
    ) -> Tuple[float, float, float, float]:
        """
        避免与指定矩形碰撞
        
        Args:
            x, y: 当前位置
            dx, dy: 当前速度
            avoid_rect: 要避开的矩形
            obj_width, obj_height: 对象尺寸
            
        Returns:
            Tuple[float, float, float, float]: (新x, 新y, 新dx, 新dy)
        """
        obj_rect = pygame.Rect(x, y, obj_width, obj_height)
        
        if obj_rect.colliderect(avoid_rect):
            # 反转方向
            new_dx = -dx
            new_dy = -dy
            new_x = x + new_dx
            new_y = y + new_dy
            
            # 如果还是碰撞，随机方向
            new_rect = pygame.Rect(new_x, new_y, obj_width, obj_height)
            if new_rect.colliderect(avoid_rect):
                import random
                new_dx = random.uniform(-2, 2)
                new_dy = random.uniform(-2, 2)
                new_x = x + new_dx
                new_y = y + new_dy
            
            return new_x, new_y, new_dx, new_dy
        
        return x, y, dx, dy

