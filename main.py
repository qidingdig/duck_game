#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Duck Game 入口模块"""

import sys
import requests

from game.duck_game import DuckGame

REQUIRED_PACKAGES = [
    'pygame',
    'requests',
    'numpy',
    'pandas',
    'matplotlib',
]

    
def check_dependencies() -> bool:
    """检查依赖包是否齐全"""
    missing_packages = []
    for package in REQUIRED_PACKAGES:
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


def check_ollama() -> bool:
    """检查 Ollama 服务（可选）"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama 服务正在运行")
            return True
        print("✗ Ollama 服务响应异常")
        return False
    except Exception:
        print("✗ 无法连接到 Ollama 服务")
        print("请确保执行了以下步骤：")
        print("1. 安装 Ollama: https://ollama.ai/")
        print("2. 启动服务: ollama serve")
        print("3. 下载模型: ollama pull deepseekr1:8b")
        return False


def main():
    """程序入口"""
    print("=== 唐老鸭小游戏启动检查 ===")
    
    if sys.version_info < (3, 7):
        print("✗ 需要 Python 3.7 或更高版本")
        return
    print(f"✓ Python 版本: {sys.version.split()[0]}")
    
    if not check_dependencies():
        print("\n请先安装依赖包后再运行游戏")
        return
    print("✓ 依赖包检查通过")
    
    if not check_ollama():
        print("\n注意: AI 对话功能可能暂时不可用，")
        print("      但红包游戏和代码统计功能仍可正常使用。")
    
    print("\n=== 启动游戏 ===")
    try:
        game = DuckGame()
        game.run()
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
    except Exception as exc:
        print(f"\n游戏启动失败: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

