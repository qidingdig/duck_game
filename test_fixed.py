#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复版本的游戏
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_imports():
    """测试导入"""
    print("测试导入...")
    
    try:
        from openai import OpenAI
        print("OpenAI导入成功")
    except Exception as e:
        print(f"OpenAI导入失败: {e}")
        return False
    
    try:
        import pygame
        print("pygame导入成功")
    except Exception as e:
        print(f"pygame导入失败: {e}")
        return False
    
    try:
        from utils.config import Config
        config = Config()
        print(f"Config导入成功: 屏幕大小 {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
    except Exception as e:
        print(f"Config导入失败: {e}")
        return False
    
    return True

def test_ai_connection():
    """测试AI连接"""
    print("\n测试AI连接...")
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        
        response = client.chat.completions.create(
            model="deepseek-r1:8b",
            messages=[
                {"role": "system", "content": "你是唐老鸭，请用中文回答。"},
                {"role": "user", "content": "你好"}
            ],
            temperature=0.7,
            max_tokens=100,
            timeout=10
        )
        
        ai_response = response.choices[0].message.content
        print(f"AI连接成功: {ai_response[:50]}...")
        return True
        
    except Exception as e:
        print(f"AI连接失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 唐老鸭小游戏修复版本测试 ===")
    
    # 测试导入
    if not test_imports():
        print("导入测试失败，请检查依赖包")
        return
    
    # 测试AI连接
    if not test_ai_connection():
        print("AI连接测试失败，请检查ollama服务")
        print("请确保:")
        print("1. ollama服务正在运行: ollama serve")
        print("2. 模型已下载: ollama pull deepseek-r1:8b")
        return
    
    print("\n所有测试通过！")
    print("现在可以运行游戏: python main_fixed.py")

if __name__ == "__main__":
    main()
