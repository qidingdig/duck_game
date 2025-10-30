#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
游戏安装脚本
"""

import os
import sys
import subprocess
import platform

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    
    # 先尝试安装pygame的预编译版本
    try:
        print("正在安装pygame...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame", "--upgrade"])
        print("✓ pygame安装完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ pygame安装失败: {e}")
        print("尝试安装pygame的预编译版本...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame", "--only-binary=all"])
            print("✓ pygame预编译版本安装完成")
        except subprocess.CalledProcessError:
            print("✗ pygame安装失败，请手动安装")
            return False
    
    # 安装其他依赖包
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "numpy", "pandas", "matplotlib"])
        print("✓ 其他依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖包安装失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    directories = [
        "assets",
        "assets/images",
        "assets/sounds",
        "game",
        "services",
        "utils"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ 创建目录: {directory}")

def check_ollama():
    """检查ollama安装"""
    print("\n检查Ollama安装...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Ollama已安装")
            return True
        else:
            print("✗ Ollama未安装")
            return False
    except FileNotFoundError:
        print("✗ Ollama未安装")
        return False

def install_ollama():
    """安装ollama"""
    print("\n正在安装Ollama...")
    system = platform.system().lower()
    
    if system == "windows":
        print("请手动下载并安装Ollama:")
        print("1. 访问 https://ollama.ai/")
        print("2. 下载Windows版本")
        print("3. 运行安装程序")
    elif system == "darwin":  # macOS
        try:
            subprocess.run(["brew", "install", "ollama"], check=True)
            print("✓ Ollama安装完成")
        except subprocess.CalledProcessError:
            print("✗ 请手动安装Ollama")
    else:  # Linux
        try:
            subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh"], check=True)
            print("✓ Ollama安装完成")
        except subprocess.CalledProcessError:
            print("✗ 请手动安装Ollama")

def download_model():
    """下载AI模型"""
    print("\n正在下载AI模型...")
    try:
        subprocess.run(["ollama", "pull", "deepseekr1:8b"], check=True)
        print("✓ AI模型下载完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ AI模型下载失败")
        return False

def main():
    """主安装函数"""
    print("=== 唐老鸭小游戏安装程序 ===")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("✗ 需要Python 3.7或更高版本")
        return
    
    print(f"✓ Python版本: {sys.version}")
    
    # 创建目录
    create_directories()
    
    # 安装依赖包
    if not install_requirements():
        return
    
    # 检查ollama
    if not check_ollama():
        install_ollama()
        if not check_ollama():
            print("请手动安装Ollama后重新运行此脚本")
            return
    
    # 下载AI模型
    download_model()
    
    print("\n=== 安装完成 ===")
    print("运行游戏: python run_game.py")
    print("或直接运行: python main.py")

if __name__ == "__main__":
    main()
