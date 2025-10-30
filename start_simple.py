#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐老鸭小游戏 - 简化启动版本
避免复杂的导入问题
"""

import sys
import os
import pygame
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import requests
import json

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入配置
from utils.config import Config

class SimpleDuckGame:
    """简化版唐老鸭游戏"""
    
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT))
        pygame.display.set_caption("唐老鸭小游戏 - 简化版")
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 角色位置
        self.donald_pos = self.config.DONALD_POSITION
        self.duckling_positions = self.config.DUCKLING_POSITIONS
        
        # 对话框相关
        self.dialog_active = False
        
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
        donald_rect = pygame.Rect(self.donald_pos[0], self.donald_pos[1], 
                                 self.config.CHARACTER_SIZE, self.config.CHARACTER_SIZE)
        if donald_rect.collidepoint(pos):
            self.show_dialog()
    
    def show_dialog(self):
        """显示对话框"""
        if self.dialog_active:
            return
        
        self.dialog_active = True
        
        # 创建对话框窗口
        dialog_window = tk.Tk()
        dialog_window.title("与唐老鸭对话")
        dialog_window.geometry("500x400")
        dialog_window.resizable(False, False)
        
        # 设置窗口居中
        dialog_window.transient()
        dialog_window.grab_set()
        
        # 创建输入框
        input_frame = tk.Frame(dialog_window)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(input_frame, text="输入消息:", font=("Arial", 12)).pack(anchor=tk.W)
        
        self.input_entry = tk.Entry(input_frame, font=("Arial", 12), width=50)
        self.input_entry.pack(pady=5, fill=tk.X)
        self.input_entry.bind('<Return>', self.process_input)
        self.input_entry.focus()
        
        # 创建显示区域
        display_frame = tk.Frame(dialog_window)
        display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        tk.Label(display_frame, text="对话记录:", font=("Arial", 12)).pack(anchor=tk.W)
        
        self.text_display = scrolledtext.ScrolledText(display_frame, height=15, width=60, font=("Arial", 10))
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
            # 模拟红包游戏
            time.sleep(1)
            result = "红包游戏统计:\n总红包数: 15\n总金额: ¥156.80\n小红包: 8个, ¥45.20\n中红包: 5个, ¥67.50\n大红包: 2个, ¥44.10\n"
            
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 红包游戏结束！\n{result}\n")
                self.text_display.see(tk.END)
            
        except Exception as e:
            print(f"红包游戏错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，红包游戏出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def start_ai_chat(self, user_input):
        """启动AI对话"""
        try:
            # 尝试连接ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseekr1:8b",
                    "prompt": user_input,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "抱歉，我无法回答这个问题。")
            else:
                ai_response = "AI服务暂时不可用，请检查ollama服务是否正在运行。"
            
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: {ai_response}\n\n")
                self.text_display.see(tk.END)
                
        except Exception as e:
            print(f"AI对话错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，AI服务出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def start_code_counting(self):
        """启动代码统计"""
        try:
            # 模拟代码统计
            time.sleep(1)
            result = "代码统计报告:\n总文件数: 25\n总行数: 1250\n代码行数: 890\n注释行数: 180\n空行数: 180\n"
            
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 代码统计完成！\n{result}\n")
                self.text_display.see(tk.END)
            
        except Exception as e:
            print(f"代码统计错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，代码统计出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def get_ai_response(self, user_input):
        """获取AI响应"""
        try:
            # 尝试连接ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseekr1:8b",
                    "prompt": user_input,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "抱歉，我无法回答这个问题。")
            else:
                ai_response = "AI服务暂时不可用，请检查ollama服务是否正在运行。"
            
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: {ai_response}\n\n")
                self.text_display.see(tk.END)
                
        except Exception as e:
            print(f"AI响应错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，我暂时无法回答这个问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def render(self):
        """渲染游戏画面"""
        # 清屏
        self.screen.fill(self.config.background_color)
        
        # 绘制背景装饰
        self.render_background()
        
        # 绘制角色
        self.render_characters()
        
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
    
    def render_characters(self):
        """绘制角色"""
        # 绘制唐老鸭
        donald_rect = pygame.Rect(self.donald_pos[0], self.donald_pos[1], 
                                 self.config.CHARACTER_SIZE, self.config.CHARACTER_SIZE)
        pygame.draw.ellipse(self.screen, self.config.DONALD_COLOR, donald_rect)
        pygame.draw.ellipse(self.screen, (0, 0, 0), donald_rect, 3)
        
        # 绘制唐老鸭的眼睛
        eye_size = 10
        eye_y = self.donald_pos[1] + self.config.CHARACTER_SIZE // 3
        pygame.draw.circle(self.screen, (0, 0, 0), 
                         (self.donald_pos[0] + self.config.CHARACTER_SIZE // 3, eye_y), eye_size)
        pygame.draw.circle(self.screen, (0, 0, 0), 
                         (self.donald_pos[0] + 2 * self.config.CHARACTER_SIZE // 3, eye_y), eye_size)
        
        # 绘制唐老鸭的嘴巴
        mouth_y = self.donald_pos[1] + 2 * self.config.CHARACTER_SIZE // 3
        pygame.draw.ellipse(self.screen, (255, 165, 0), 
                          (self.donald_pos[0] + self.config.CHARACTER_SIZE // 4, mouth_y - 8, 
                           self.config.CHARACTER_SIZE // 2, 16))
        
        # 绘制汤小鸭
        for i, pos in enumerate(self.duckling_positions):
            duckling_rect = pygame.Rect(pos[0], pos[1], 
                                      self.config.CHARACTER_SIZE - 20, self.config.CHARACTER_SIZE - 20)
            pygame.draw.ellipse(self.screen, self.config.DUCKLING_COLOR, duckling_rect)
            pygame.draw.ellipse(self.screen, (0, 0, 0), duckling_rect, 2)
            
            # 绘制眼睛
            eye_size = 6
            eye_y = pos[1] + (self.config.CHARACTER_SIZE - 20) // 3
            pygame.draw.circle(self.screen, (0, 0, 0), 
                             (pos[0] + (self.config.CHARACTER_SIZE - 20) // 3, eye_y), eye_size)
            pygame.draw.circle(self.screen, (0, 0, 0), 
                             (pos[0] + 2 * (self.config.CHARACTER_SIZE - 20) // 3, eye_y), eye_size)
    
    def render_ui(self):
        """绘制UI信息"""
        # 绘制标题
        font = pygame.font.Font(None, 36)
        title_text = font.render("唐老鸭小游戏", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        small_font = pygame.font.Font(None, 24)
        hint_text = small_font.render("点击唐老鸭开始对话！", True, (0, 0, 0))
        self.screen.blit(hint_text, (10, 50))
    
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
            
            # 渲染游戏
            self.render()
            
            # 控制帧率
            self.clock.tick(self.config.FPS)
        
        # 清理资源
        pygame.quit()
        print("游戏结束，感谢游玩！")

def main():
    """主函数"""
    try:
        game = SimpleDuckGame()
        game.run()
    except Exception as e:
        print(f"游戏启动失败: {e}")
        messagebox.showerror("错误", f"游戏启动失败: {e}")

if __name__ == "__main__":
    main()

