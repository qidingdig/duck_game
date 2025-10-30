#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏配置管理
"""

class Config:
    """游戏配置类"""
    
    def __init__(self):
        # 屏幕设置
        self.SCREEN_WIDTH = 1000
        self.SCREEN_HEIGHT = 700
        
        # 游戏设置
        self.FPS = 60
        self.GAME_TITLE = "唐老鸭小游戏"
        
        # 角色设置
        self.CHARACTER_SIZE = 80
        self.CHARACTER_SPEED = 2
        
        # 唐老鸭设置
        self.DONALD_POSITION = (100, 300)
        self.DONALD_COLOR = (255, 255, 0)  # 黄色
        
        # 汤小鸭设置
        self.DUCKLING_POSITIONS = [
            (300, 200),  # 汤小鸭1
            (500, 400),  # 汤小鸭2
            (700, 150)   # 汤小鸭3
        ]
        self.DUCKLING_COLOR = (255, 165, 0)  # 橙色
        
        # 红包设置
        self.RED_PACKET_SIZES = [
            (30, 40),   # 小红包
            (50, 60),   # 中红包
            (70, 80)    # 大红包
        ]
        self.RED_PACKET_COLORS = [
            (255, 0, 0),    # 红色
            (255, 100, 100), # 浅红色
            (200, 0, 0)     # 深红色
        ]
        
        # AI服务设置
        self.OLLAMA_URL = "http://localhost:11434"
        self.AI_MODEL = "deepseekr1:8b"
        
        # 文件路径
        self.ASSETS_PATH = "assets"
        self.IMAGES_PATH = "assets/images"
        self.SOUNDS_PATH = "assets/sounds"
        
        # 背景颜色
        self.background_color = (135, 206, 235)  # 天蓝色背景