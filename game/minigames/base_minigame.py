#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小游戏基类 - 所有小游戏都应继承此类
"""

from abc import ABC, abstractmethod
import pygame


class BaseMinigame(ABC):
    """小游戏基类"""
    
    def __init__(self):
        self._active = False
    
    @abstractmethod
    def start(self, **kwargs):
        """开始游戏"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止游戏"""
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """
        更新游戏逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        pass
    
    @abstractmethod
    def render(self, screen: pygame.Surface):
        """
        渲染游戏
        
        Args:
            screen: Pygame屏幕表面
        """
        pass
    
    def is_active(self) -> bool:
        """是否激活"""
        return self._active
    
    def pause(self):
        """暂停游戏"""
        self._active = False
    
    def resume(self):
        """恢复游戏"""
        self._active = True

