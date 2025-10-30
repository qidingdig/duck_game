#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐老鸭小游戏整合项目 - 主入口
整合AI对话、红包游戏、代码统计等功能
"""

import sys
import os
import pygame
import tkinter as tk
from tkinter import messagebox
import threading
import time

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from game.game_engine import GameEngine
from services.ai_service import AIService
from services.code_counter import CodeCounter
from services.red_packet_service import RedPacketService
from utils.config import Config

class DuckGame:
    """主游戏类"""
    
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT))
        pygame.display.set_caption("唐老鸭小游戏 - Duck Game")
        
        # 初始化游戏引擎
        self.game_engine = GameEngine(self.screen, self.config)
        
        # 初始化服务
        self.ai_service = AIService()
        self.code_counter = CodeCounter()
        self.red_packet_service = RedPacketService()
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 对话框相关
        self.dialog_active = False
        self.dialog_text = ""
        self.dialog_response = ""
        
        print("=== 唐老鸭小游戏启动 ===")
        print("点击唐老鸭开始对话！")
        print("可用命令:")
        print("- 我要抢红包")
        print("- 我要ai问答")
        print("- 我要统计代码量")
        print("========================")
    
    def handle_click(self, pos):
        """处理鼠标点击事件"""
        # 检查是否点击了唐老鸭
        if self.game_engine.is_donald_clicked(pos):
            self.show_dialog()
    
    def show_dialog(self):
        """显示对话框"""
        if self.dialog_active:
            return
        
        self.dialog_active = True
        
        # 创建对话框窗口
        dialog_window = tk.Tk()
        dialog_window.title("与唐老鸭对话")
        dialog_window.geometry("400x300")
        dialog_window.resizable(False, False)
        
        # 设置窗口居中
        dialog_window.transient()
        dialog_window.grab_set()
        
        # 创建输入框
        input_frame = tk.Frame(dialog_window)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(input_frame, text="输入消息:", font=("Arial", 12)).pack(anchor=tk.W)
        
        self.input_entry = tk.Entry(input_frame, font=("Arial", 12), width=40)
        self.input_entry.pack(pady=5, fill=tk.X)
        self.input_entry.bind('<Return>', self.process_input)
        self.input_entry.focus()
        
        # 创建显示区域
        display_frame = tk.Frame(dialog_window)
        display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        tk.Label(display_frame, text="对话记录:", font=("Arial", 12)).pack(anchor=tk.W)
        
        self.text_display = tk.Text(display_frame, height=10, width=50, font=("Arial", 10))
        self.text_display.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # 创建按钮
        button_frame = tk.Frame(dialog_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="发送", command=self.process_input, 
                 font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="关闭", command=dialog_window.destroy, 
                 font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
        
        # 添加欢迎消息
        self.text_display.insert(tk.END, "唐老鸭: 你好！我是唐老鸭，有什么可以帮助你的吗？\n\n")
        self.text_display.see(tk.END)
        
        # 设置关闭事件
        def on_closing():
            self.dialog_active = False
            dialog_window.destroy()
        
        dialog_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 启动对话框
        dialog_window.mainloop()
    
    def process_input(self, event=None):
        """处理用户输入"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        # 显示用户输入
        self.text_display.insert(tk.END, f"你: {user_input}\n")
        self.input_entry.delete(0, tk.END)
        
        # 处理特殊命令
        if "我要抢红包" in user_input:
            self.text_display.insert(tk.END, "唐老鸭: 好的！让我来发红包！\n\n")
            self.text_display.see(tk.END)
            # 启动红包游戏
            threading.Thread(target=self.start_red_packet_game, daemon=True).start()
        
        elif "我要ai问答" in user_input:
            self.text_display.insert(tk.END, "唐老鸭: 好的！让我来回答你的问题！\n\n")
            self.text_display.see(tk.END)
            # 启动AI问答
            threading.Thread(target=self.start_ai_chat, args=(user_input,), daemon=True).start()
        
        elif "我要统计代码量" in user_input:
            self.text_display.insert(tk.END, "唐老鸭: 好的！让我来统计代码量！\n\n")
            self.text_display.see(tk.END)
            # 启动代码统计
            threading.Thread(target=self.start_code_counting, daemon=True).start()
        
        else:
            # 普通AI对话
            threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()
    
    def start_red_packet_game(self):
        """启动红包游戏"""
        try:
            # 让汤小鸭开始移动
            self.game_engine.start_character_animation()
            
            # 启动红包游戏
            result = self.red_packet_service.start_game()
            
            # 显示结果
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 红包游戏结束！\n{result}\n\n")
                self.text_display.see(tk.END)
            
            # 停止角色动画
            self.game_engine.stop_character_animation()
            
        except Exception as e:
            print(f"红包游戏错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，红包游戏出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def start_ai_chat(self, user_input):
        """启动AI对话"""
        try:
            response = self.ai_service.chat(user_input)
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: {response}\n\n")
                self.text_display.see(tk.END)
        except Exception as e:
            print(f"AI对话错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，AI服务出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def start_code_counting(self):
        """启动代码统计"""
        try:
            # 让汤小鸭开始移动
            self.game_engine.start_character_animation()
            
            # 统计代码量
            result = self.code_counter.count_code_lines(".")
            
            # 显示结果
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 代码统计完成！\n{result}\n\n")
                self.text_display.see(tk.END)
            
            # 停止角色动画
            self.game_engine.stop_character_animation()
            
        except Exception as e:
            print(f"代码统计错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，代码统计出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def get_ai_response(self, user_input):
        """获取AI响应"""
        try:
            response = self.ai_service.chat(user_input)
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: {response}\n\n")
                self.text_display.see(tk.END)
        except Exception as e:
            print(f"AI响应错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，我暂时无法回答这个问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def run(self):
        """主游戏循环"""
        while self.running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        self.handle_click(event.pos)
            
            # 更新游戏状态
            self.game_engine.update()
            
            # 渲染游戏
            self.game_engine.render()
            
            # 控制帧率
            self.clock.tick(self.config.FPS)
        
        # 清理资源
        pygame.quit()
        print("游戏结束，感谢游玩！")

def main():
    """主函数"""
    try:
        game = DuckGame()
        game.run()
    except Exception as e:
        print(f"游戏启动失败: {e}")
        messagebox.showerror("错误", f"游戏启动失败: {e}")

if __name__ == "__main__":
    main()
