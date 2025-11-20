#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
红包游戏服务 - 管理红包游戏逻辑
"""

import pygame
import time
import threading
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from game.red_packet import RedPacketManager

class RedPacketService:
    """红包游戏服务"""
    
    def __init__(self):
        self.game_active = False
        self.game_duration = 30  # 游戏时长30秒
        self.red_packet_manager = None
        self.game_thread = None
    
    def start_game(self):
        """启动红包游戏"""
        if self.game_active:
            return "红包游戏已经在进行中！"
        
        self.game_active = True
        
        # 创建红包管理器
        self.red_packet_manager = RedPacketManager(1000, 700)
        self.red_packet_manager.start_game()
        
        # 启动游戏线程
        self.game_thread = threading.Thread(target=self._run_game, daemon=True)
        self.game_thread.start()
        
        return "红包游戏开始！唐老鸭正在发红包，唐小鸭们开始移动！"
    
    def _run_game(self):
        """运行红包游戏"""
        start_time = time.time()
        
        # 初始化pygame（如果还没有初始化）
        if not pygame.get_init():
            pygame.init()
        
        # 创建临时屏幕用于游戏逻辑
        screen = pygame.display.set_mode((1000, 700))
        clock = pygame.time.Clock()
        
        while self.game_active and (time.time() - start_time) < self.game_duration:
            # 更新红包管理器
            self.red_packet_manager.update()
            
            # 控制帧率
            clock.tick(60)
        
        # 游戏结束
        self.game_active = False
        if self.red_packet_manager:
            self.red_packet_manager.stop_game()
    
    def stop_game(self):
        """停止红包游戏"""
        self.game_active = False
        if self.red_packet_manager:
            self.red_packet_manager.stop_game()
    
    def get_statistics(self):
        """获取游戏统计"""
        if self.red_packet_manager:
            return self.red_packet_manager.get_statistics_text()
        return "游戏尚未开始"
    
    def is_game_active(self):
        """检查游戏是否活跃"""
        return self.game_active
