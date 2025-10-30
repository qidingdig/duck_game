#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏启动脚本
"""

import sys
import os
import subprocess
import platform

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'pygame',
        'requests',
        'numpy',
        'pandas',
        'matplotlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_ollama():
    """检查ollama服务"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama服务正在运行")
            return True
        else:
            print("✗ Ollama服务响应异常")
            return False
    except Exception as e:
        print("✗ 无法连接到Ollama服务")
        print("请确保ollama服务正在运行:")
        print("1. 安装ollama: https://ollama.ai/")
        print("2. 启动服务: ollama serve")
        print("3. 下载模型: ollama pull deepseekr1:8b")
        return False

def main():
    """主函数"""
    print("=== 唐老鸭小游戏启动检查 ===")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("✗ 需要Python 3.7或更高版本")
        return
    
    print(f"✓ Python版本: {sys.version}")
    
    # 检查依赖包
    if not check_dependencies():
        return
    
    print("✓ 依赖包检查通过")
    
    # 检查ollama服务
    if not check_ollama():
        print("\n注意: AI对话功能可能无法使用")
        print("但红包游戏和代码统计功能仍然可用")
    
    print("\n=== 启动游戏 ===")
    
    # 启动游戏
    try:
        from main import main as game_main
        game_main()
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
    except Exception as e:
        print(f"\n游戏启动失败: {e}")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()
