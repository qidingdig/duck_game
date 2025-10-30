#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试导入是否正常
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("测试导入...")

try:
    from utils.config import Config
    print("Config导入成功")
    
    config = Config()
    print(f"配置初始化成功: 屏幕大小 {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
    
except Exception as e:
    print(f"Config导入失败: {e}")

try:
    import pygame
    print("pygame导入成功")
except Exception as e:
    print(f"pygame导入失败: {e}")

try:
    import tkinter as tk
    print("tkinter导入成功")
except Exception as e:
    print(f"tkinter导入失败: {e}")

try:
    import requests
    print("requests导入成功")
except Exception as e:
    print(f"requests导入失败: {e}")

print("导入测试完成！")
