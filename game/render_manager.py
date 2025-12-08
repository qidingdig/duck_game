#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
渲染管理器 - 统一管理游戏渲染
"""

import pygame
from typing import Optional
from utils.config import Config
from game.characters import Duckling


class RenderManager:
    """统一管理游戏渲染"""
    
    def __init__(self, screen: pygame.Surface, config: Config, ducklings: list):
        """
        初始化渲染管理器
        
        Args:
            screen: Pygame屏幕表面
            config: 游戏配置
            ducklings: 小鸭对象列表
        """
        self.screen = screen
        self.config = config
        self.ducklings = ducklings
        
        # 字体设置
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        except:
            self.font = None
            self.small_font = None
    
    def render_all(
        self,
        donald_pos: tuple,
        red_packet_game: Optional[object] = None,
        red_packet_game_active: bool = False
    ):
        """
        渲染所有游戏元素
        
        Args:
            donald_pos: 唐老鸭位置 (x, y)
            red_packet_game: 红包游戏管理器（可选）
            red_packet_game_active: 红包游戏是否激活
        """
        # 清屏
        self.screen.fill(self.config.background_color)
        
        # 绘制背景装饰
        self.render_background()
        
        # 绘制角色
        self.render_characters(donald_pos)
        
        # 绘制红包游戏效果
        if red_packet_game_active and red_packet_game:
            self.render_red_packets(red_packet_game)
        
        # 绘制UI信息
        self.render_ui()
        
        # 更新显示
        pygame.display.flip()
    
    def render_background(self):
        """绘制背景装饰"""
        # 绘制云朵
        cloud_color = (255, 255, 255)
        for i in range(3):
            x = 100 + i * 300
            y = 50 + i * 20
            pygame.draw.ellipse(self.screen, cloud_color, (x, y, 80, 40))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 20, y - 10, 60, 30))
            pygame.draw.ellipse(self.screen, cloud_color, (x + 40, y, 60, 30))
        
        # 绘制地面
        ground_color = (34, 139, 34)
        pygame.draw.rect(
            self.screen,
            ground_color,
            (0, self.config.SCREEN_HEIGHT - 50, self.config.SCREEN_WIDTH, 50)
        )
    
    def render_characters(self, donald_pos: tuple):
        """绘制角色"""
        # 绘制唐老鸭
        donald_rect = pygame.Rect(
            donald_pos[0],
            donald_pos[1],
            self.config.CHARACTER_SIZE,
            self.config.CHARACTER_SIZE
        )
        pygame.draw.ellipse(self.screen, self.config.DONALD_COLOR, donald_rect)
        pygame.draw.ellipse(self.screen, (0, 0, 0), donald_rect, 3)
        
        # 绘制唐老鸭的眼睛
        eye_size = 10
        eye_y = donald_pos[1] + self.config.CHARACTER_SIZE // 3
        pygame.draw.circle(
            self.screen,
            (0, 0, 0),
            (donald_pos[0] + self.config.CHARACTER_SIZE // 3, eye_y),
            eye_size
        )
        pygame.draw.circle(
            self.screen,
            (0, 0, 0),
            (donald_pos[0] + 2 * self.config.CHARACTER_SIZE // 3, eye_y),
            eye_size
        )
        
        # 绘制唐老鸭的嘴巴
        mouth_y = donald_pos[1] + 2 * self.config.CHARACTER_SIZE // 3
        pygame.draw.ellipse(
            self.screen,
            (255, 165, 0),
            (
                donald_pos[0] + self.config.CHARACTER_SIZE // 4,
                mouth_y - 8,
                self.config.CHARACTER_SIZE // 2,
                16
            )
        )
        
        # 绘制小鸭（使用Duckling对象）
        for duckling in self.ducklings:
            duckling.render(self.screen)
    
    def render_red_packets(self, red_packet_game: object):
        """绘制红包"""
        if red_packet_game and hasattr(red_packet_game, 'is_active'):
            if red_packet_game.is_active():
                red_packet_game.render(self.screen)
    
    def render_ui(self):
        """绘制UI信息"""
        if not self.font or not self.small_font:
            return
        
        # 绘制标题
        title_text = self.font.render("Duck Game", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        hint_text = self.small_font.render("Click Donald Duck to start!", True, (0, 0, 0))
        self.screen.blit(hint_text, (10, 50))

