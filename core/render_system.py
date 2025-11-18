#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
渲染系统 - 分层渲染管理
"""

from enum import IntEnum
from typing import Callable, Dict, List
import pygame


class RenderLayer(IntEnum):
    """渲染层枚举"""
    BACKGROUND = 0  # 背景层
    GAME_OBJECTS = 1  # 游戏对象层
    UI = 2  # UI层
    OVERLAY = 3  # 覆盖层（最上层）


class RenderSystem:
    """渲染系统"""
    
    def __init__(self, screen: pygame.Surface):
        """
        初始化渲染系统
        
        Args:
            screen: Pygame屏幕表面
        """
        self.screen = screen
        self._renderers: Dict[RenderLayer, List[Callable[[pygame.Surface], None]]] = {}
        
        # 初始化所有层
        for layer in RenderLayer:
            self._renderers[layer] = []
    
    def add_renderer(self, layer: RenderLayer, renderer: Callable[[pygame.Surface], None]):
        """
        添加渲染器
        
        Args:
            layer: 渲染层
            renderer: 渲染函数，参数为screen
        """
        if renderer not in self._renderers[layer]:
            self._renderers[layer].append(renderer)
    
    def remove_renderer(self, layer: RenderLayer, renderer: Callable[[pygame.Surface], None]):
        """移除渲染器"""
        if layer in self._renderers and renderer in self._renderers[layer]:
            self._renderers[layer].remove(renderer)
    
    def render(self):
        """按层渲染所有内容"""
        # 按层顺序渲染
        for layer in sorted(RenderLayer):
            if layer in self._renderers:
                for renderer in self._renderers[layer]:
                    try:
                        renderer(self.screen)
                    except Exception as e:
                        print(f"渲染器错误 [Layer {layer.name}]: {e}")
    
    def clear(self):
        """清空所有渲染器"""
        for layer in self._renderers:
            self._renderers[layer].clear()
    
    def clear_layer(self, layer: RenderLayer):
        """清空指定层的所有渲染器"""
        if layer in self._renderers:
            self._renderers[layer].clear()
    
    def get_renderer_count(self, layer: RenderLayer) -> int:
        """获取指定层的渲染器数量"""
        if layer in self._renderers:
            return len(self._renderers[layer])
        return 0

