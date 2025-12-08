#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏循环管理器 - 管理游戏主循环和事件处理
"""

import pygame
from typing import Callable, Optional


class GameLoop:
    """游戏循环管理器"""
    
    def __init__(
        self,
        screen: pygame.Surface,
        update_callback: Callable[[], None],
        render_callback: Callable[[], None],
        handle_click_callback: Optional[Callable[[tuple], None]] = None,
        handle_resize_callback: Optional[Callable[[int, int], None]] = None,
        ui_update_callback: Optional[Callable[[], None]] = None,
        fps: int = 60
    ):
        """
        初始化游戏循环
        
        Args:
            screen: Pygame屏幕表面
            update_callback: 更新回调函数
            render_callback: 渲染回调函数
            handle_click_callback: 点击事件处理回调（可选）
            handle_resize_callback: 窗口大小改变回调（可选）
            ui_update_callback: UI更新回调（可选）
            fps: 目标帧率
        """
        self.screen = screen
        self.update_callback = update_callback
        self.render_callback = render_callback
        self.handle_click_callback = handle_click_callback
        self.handle_resize_callback = handle_resize_callback
        self.ui_update_callback = ui_update_callback
        self.fps = fps
        self.running = False
    
    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        self.running = True
        
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    # 处理窗口大小改变事件
                    if self.handle_resize_callback:
                        self.handle_resize_callback(event.w, event.h)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.handle_click_callback:  # 左键点击
                        self.handle_click_callback(event.pos)
            
            # 更新游戏状态
            self.update_callback()
            
            # 渲染画面
            self.render_callback()
            
            # UI更新（如果提供）
            if self.ui_update_callback:
                self.ui_update_callback()
            
            # 控制帧率
            clock.tick(self.fps)
    
    def stop(self):
        """停止游戏循环"""
        self.running = False

