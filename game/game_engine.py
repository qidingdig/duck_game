#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏引擎 - 管理游戏状态和渲染
"""

import pygame
import time
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.characters import DonaldDuck, Duckling
from game.red_packet import RedPacketManager

class GameEngine:
    """游戏引擎类"""
    
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        
        # 初始化角色
        self.donald = DonaldDuck(
            self.config.DONALD_POSITION[0],
            self.config.DONALD_POSITION[1],
            self.config.CHARACTER_SIZE,
            self.config.CHARACTER_SIZE
        )
        
        self.ducklings = []
        for i, pos in enumerate(self.config.DUCKLING_POSITIONS):
            duckling = Duckling(
                pos[0], pos[1],
                self.config.CHARACTER_SIZE - 20,
                self.config.CHARACTER_SIZE - 20,
                f"唐小鸭{i+1}"
            )
            self.ducklings.append(duckling)
        
        # 初始化红包管理器
        self.red_packet_manager = RedPacketManager(
            self.config.SCREEN_WIDTH,
            self.config.SCREEN_HEIGHT
        )
        
        # 游戏状态
        self.background_color = (135, 206, 235)  # 天蓝色背景
        self.character_animation_active = False
        self.animation_start_time = 0
        
        # 字体
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def update(self):
        """更新游戏状态"""
        # 更新唐老鸭
        self.donald.update()
        
        # 更新小鸭
        for duckling in self.ducklings:
            duckling.update()
        
        # 更新红包管理器
        self.red_packet_manager.update()
        
        # 检查角色动画状态
        if self.character_animation_active:
            current_time = time.time()
            if current_time - self.animation_start_time > 5:  # 5秒后停止动画
                self.stop_character_animation()
    
    def render(self):
        """渲染游戏画面"""
        # 清屏
        self.screen.fill(self.background_color)
        
        # 绘制背景装饰
        self.render_background()
        
        # 绘制角色
        self.donald.render(self.screen)
        for duckling in self.ducklings:
            duckling.render(self.screen)
        
        # 绘制红包
        self.red_packet_manager.render(self.screen)
        
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
        pygame.draw.rect(self.screen, ground_color, 
                        (0, self.config.SCREEN_HEIGHT - 50, 
                         self.config.SCREEN_WIDTH, 50))
    
    def render_ui(self):
        """绘制UI信息"""
        # 绘制标题
        title_text = self.font.render("唐老鸭小游戏", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        hint_text = self.small_font.render("点击唐老鸭开始对话！", True, (0, 0, 0))
        self.screen.blit(hint_text, (10, 50))
        
        # 绘制红包游戏统计
        if self.red_packet_manager.game_active:
            stats_text = self.red_packet_manager.get_statistics_text()
            lines = stats_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    text = self.small_font.render(line, True, (0, 0, 0))
                    self.screen.blit(text, (self.config.SCREEN_WIDTH - 200, 10 + i * 25))
    
    def is_donald_clicked(self, pos):
        """检查是否点击了唐老鸭"""
        return self.donald.is_clicked(pos)
    
    def start_character_animation(self):
        """开始角色动画"""
        self.character_animation_active = True
        self.animation_start_time = time.time()
        
        # 让汤小鸭开始随机移动
        for duckling in self.ducklings:
            duckling.start_random_movement()
        
        # 让唐老鸭开始弹跳
        self.donald.start_bounce()
    
    def stop_character_animation(self):
        """停止角色动画"""
        self.character_animation_active = False
        
        # 停止小鸭移动
        for duckling in self.ducklings:
            duckling.stop_random_movement()
        
        # 停止唐老鸭弹跳
        self.donald.stop_bounce()
    
    def start_red_packet_game(self):
        """开始红包游戏"""
        self.red_packet_manager.start_game()
        self.start_character_animation()
    
    def stop_red_packet_game(self):
        """停止红包游戏"""
        self.red_packet_manager.stop_game()
        self.stop_character_animation()
    
    def get_red_packet_statistics(self):
        """获取红包统计信息"""
        return self.red_packet_manager.get_statistics_text()
