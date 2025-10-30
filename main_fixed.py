#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐老鸭小游戏整合项目 - 修复版本
解决中文字符显示、AI模型错误、红包功能等问题
"""

import sys
import os
import pygame
import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
import json
from openai import OpenAI
from queue import Queue
import re

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.config import Config
from services.advanced_code_counter import AdvancedCodeCounter

class DuckGame:
    """主游戏类 - 修复版本"""
    
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT))
        pygame.display.set_caption("Duck Game - 唐老鸭小游戏")
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 角色位置
        self.donald_pos = self.config.DONALD_POSITION
        self.duckling_positions = self.config.DUCKLING_POSITIONS
        
        # 对话框相关
        self.dialog_active = False
        
        # 红包游戏状态
        self.red_packet_game_active = False
        self.red_packets = []
        
        # 汤小鸭移动状态
        self.duckling_moving = False
        self.duckling_positions_original = self.duckling_positions.copy()
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        
        # 初始化增强代码统计工具
        self.code_counter = AdvancedCodeCounter()
        
        # 初始化tkinter相关
        self._root = None
        self._need_dialog = False
        self._dialog_lock = threading.Lock()  # 用于保护对话框创建
        self._tk_running = False  # tkinter主循环是否在运行
        self._update_counter = 0  # 用于控制update()的调用频率
        self._ui_queue = Queue()  # 线程安全UI消息队列
        
        # 字体设置
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        except:
            # 如果字体加载失败，使用默认字体
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        
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
        # 如果对话框已经打开，直接返回
        if self.dialog_active:
            try:
                if hasattr(self, 'dialog_window') and self.dialog_window:
                    if self.dialog_window.winfo_exists():
                        # 窗口已存在，将其置前
                        self.dialog_window.lift()
                        return
            except:
                pass
        
        # 标记需要创建对话框（在主循环中创建，确保在主线程）
        self._need_dialog = True
        print("已标记需要创建对话框")  # 调试信息
    
    def _check_and_create_dialog(self):
        """在主循环中调用，检查并创建对话框（非阻塞）"""
        if not self._need_dialog:
            return
        
        if self.dialog_active:
            self._need_dialog = False
            return
        
        self._need_dialog = False
        
        try:
            # 确保有Tk根窗口（必须在主线程中创建）
            if not hasattr(self, '_root') or self._root is None:
                self._root = tk.Tk()
                # 使用withdraw隐藏根窗口，避免overrideredirect影响输入法/最小化
                try:
                    self._root.withdraw()
                except Exception:
                    pass
                self._root.protocol("WM_DELETE_WINDOW", lambda: None)
                
            # 创建对话框窗口
            dialog_window = tk.Toplevel(self._root)
            dialog_window.title("与唐老鸭对话")
            dialog_window.geometry("600x500")
            dialog_window.minsize(600, 500)
            dialog_window.resizable(True, True)
            
            # 确保窗口可见并置前（必须在创建后立即调用)
            dialog_window.deiconify()  # 显示窗口
            # 不强制置前，避免与输入法焦点冲突
            # dialog_window.lift()
            # dialog_window.attributes('-topmost', True)
            # dialog_window.attributes('-topmost', False)
            
            # 不使用grab_set，避免阻塞
            try:
                # 不使用transient，因为这可能影响可见性
                pass
            except:
                pass
            
            self.dialog_window = dialog_window
            self.dialog_active = True
            
            # 创建输入框
            input_frame = tk.Frame(dialog_window)
            input_frame.pack(pady=10, padx=10, fill=tk.X)
            
            tk.Label(input_frame, text="输入消息:", font=("Arial", 12)).pack(anchor=tk.W)
            
            self.input_entry = tk.Entry(input_frame, font=("Arial", 12), width=50)
            self.input_entry.pack(pady=5, fill=tk.X)
            self.input_entry.bind('<Return>', lambda e: self.process_input(dialog_window))
            
            # 创建显示区域
            display_frame = tk.Frame(dialog_window)
            display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            
            tk.Label(display_frame, text="对话记录:", font=("Arial", 12)).pack(anchor=tk.W)
            
            scrollbar = tk.Scrollbar(display_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.text_display = tk.Text(display_frame, height=15, width=60, font=("Arial", 10),
                                       yscrollcommand=scrollbar.set)
            self.text_display.pack(pady=5, fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.text_display.yview)
            
            # 创建按钮
            button_frame = tk.Frame(dialog_window)
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="发送", 
                     command=lambda: self.process_input(dialog_window), 
                     font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="关闭", 
                     command=lambda: self.close_dialog(dialog_window), 
                     font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
            
            # 添加欢迎消息
            welcome_msg = "唐老鸭: 你好！我是唐老鸭，有什么可以帮助你的吗？\n\n"
            welcome_msg += "提示：\n"
            welcome_msg += "- 输入'我要抢红包'可以开始红包游戏\n"
            welcome_msg += "- 输入'我要ai问答'可以开始AI对话\n"
            welcome_msg += "- 输入'我要统计代码量'可以统计当前项目代码\n"
            welcome_msg += "- 输入'统计代码: <目录路径>'可以统计指定目录的代码\n\n"
            self.text_display.insert(tk.END, welcome_msg)
            self.text_display.see(tk.END)
            
            # 设置关闭事件
            dialog_window.protocol("WM_DELETE_WINDOW", lambda: self.close_dialog(dialog_window))
            
            # 强制更新窗口以确保显示
            dialog_window.update_idletasks()
            
            # 再次确保可见
            dialog_window.deiconify()
            dialog_window.lift()
            
            # 设置焦点到输入框（延迟一点，确保窗口已经显示）
            def set_focus():
                try:
                    if hasattr(self, 'input_entry') and self.input_entry:
                        self.input_entry.focus_set()
                        self.input_entry.icursor(0)  # 设置光标位置
                except:
                    pass
            dialog_window.after(100, set_focus)  # 延迟100ms后设置焦点
            
            # 也立即尝试设置焦点
            try:
                if hasattr(self, 'input_entry') and self.input_entry:
                    self.input_entry.focus_set()
            except:
                pass
            
            print(f"对话框已创建: {dialog_window.winfo_exists()}, 状态: {self.dialog_active}, 可见: {dialog_window.winfo_viewable()}")  # 调试信息
            
        except Exception as e:
            print(f"创建对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            self.dialog_active = False
            self._need_dialog = False
    
    
    def close_dialog(self, dialog_window=None):
        """关闭对话框（非阻塞）"""
        if dialog_window is None:
            dialog_window = getattr(self, 'dialog_window', None)
        
        try:
            if dialog_window:
                # 检查窗口是否还存在
                try:
                    if dialog_window.winfo_exists():
                        # 直接销毁窗口（不调用grab_release，避免阻塞）
                        dialog_window.destroy()
                except (tk.TclError, AttributeError):
                    # 窗口已经不存在
                    pass
        except Exception as e:
            print(f"关闭对话框错误: {e}")
        finally:
            # 重置状态
            self.dialog_active = False
            self.dialog_window = None
            self.input_entry = None
            self.text_display = None
            print("对话框已关闭")  # 调试信息
    
    def process_input(self, dialog_window, event=None):
        """处理用户输入"""
        if not hasattr(self, 'input_entry') or self.input_entry is None:
            return
        
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        # 显示用户输入
        if hasattr(self, 'text_display') and self.text_display:
            self.text_display.insert(tk.END, f"你: {user_input}\n")
            self.text_display.see(tk.END)
        
        self.input_entry.delete(0, tk.END)
        
        # 处理特殊命令
        if "我要抢红包" in user_input:
            if hasattr(self, 'text_display') and self.text_display:
                self.text_display.insert(tk.END, "唐老鸭: 好的！让我来发红包！\n\n")
                self.text_display.see(tk.END)
            # 启动红包游戏
            threading.Thread(target=self.start_red_packet_game, daemon=True).start()
        
        elif "我要ai问答" in user_input or user_input.startswith("我要ai问答"):
            if hasattr(self, 'text_display') and self.text_display:
                self.text_display.insert(tk.END, "唐老鸭: 好的！让我来回答你的问题！\n\n")
                self.text_display.see(tk.END)
            # 启动AI问答
            threading.Thread(target=self.start_ai_chat, args=(user_input,), daemon=True).start()
        
        elif "我要统计代码量" in user_input:
            # 统计当前项目目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if hasattr(self, 'text_display') and self.text_display:
                self.text_display.insert(tk.END, f"唐老鸭: 好的！让我来统计当前项目代码量！\n目录: {current_dir}\n\n")
                self.text_display.see(tk.END)
            # 启动代码统计
            threading.Thread(target=self.start_code_counting, args=(current_dir,), daemon=True).start()
        
        elif user_input.startswith("统计代码:") or user_input.startswith("统计代码："):
            # 解析目录路径（支持 Windows 盘符冒号）
            m = re.match(r'^\s*统计代码[：:]\s*(.+)\s*$', user_input)
            if not m:
                if hasattr(self, 'text_display') and self.text_display:
                    self.text_display.insert(tk.END, "唐老鸭: 请提供要统计的目录路径，格式：统计代码: <目录路径>\n\n")
                    self.text_display.see(tk.END)
                return
            path_part = m.group(1)
            
            # 展开引号
            if (path_part.startswith('"') and path_part.endswith('"')) or (path_part.startswith("'") and path_part.endswith("'")):
                path_part = path_part[1:-1]
            
            # 规范化路径（允许包含空格）
            path_part = path_part.strip()
            
            # 验证路径
            if not os.path.exists(path_part):
                if hasattr(self, 'text_display') and self.text_display:
                    self.text_display.insert(tk.END, f"唐老鸭: 路径不存在: {path_part}\n请检查路径是否正确。\n\n")
                    self.text_display.see(tk.END)
                return
            
            if hasattr(self, 'text_display') and self.text_display:
                self.text_display.insert(tk.END, f"唐老鸭: 好的！让我来统计这个目录的代码量！\n目录: {path_part}\n\n")
                self.text_display.see(tk.END)
            # 启动代码统计
            threading.Thread(target=self.start_code_counting, args=(path_part,), daemon=True).start()
        
        else:
            # 普通AI对话
            threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()
    
    def start_red_packet_game(self):
        """启动红包游戏"""
        try:
            # 显示游戏开始信息（使用线程安全的方式，因为可能被主线程调用）
            if hasattr(self, 'text_display') and self.text_display:
                # 如果在主线程中，直接调用；否则使用线程安全方式
                try:
                    self.text_display.insert(tk.END, "唐老鸭: 红包游戏开始！汤小鸭们开始移动！\n")
                    self.text_display.see(tk.END)
                except RuntimeError:
                    # 如果不在主线程，使用线程安全方式
                    self._update_text_display("唐老鸭: 红包游戏开始！汤小鸭们开始移动！\n")
            
            # 启动红包游戏逻辑（在后台线程）
            threading.Thread(target=self.start_red_packet_game_logic, daemon=True).start()
            
        except Exception as e:
            print(f"红包游戏错误: {e}")
            self._update_text_display(f"唐老鸭: 抱歉，红包游戏出现了问题: {str(e)}\n\n")
    
    def start_red_packet_game_logic(self):
        """启动红包游戏逻辑"""
        # 初始化游戏状态
        self.red_packet_game_active = True
        self.red_packets = []
        self.duckling_moving = True
        self.game_start_time = time.time()
        self.game_duration = 30  # 30秒游戏
        self.red_packet_timer = 0
        self.red_packet_spawn_interval = 30  # 每30帧生成一个红包
        self.statistics = {
            'total_count': 0,
            'total_amount': 0.0,
            'type_counts': [0, 0, 0],
            'type_amounts': [0.0, 0.0, 0.0]
        }
    
    def spawn_red_packet(self):
        """生成红包"""
        import random
        
        # 从唐老鸭位置发射红包
        start_x = self.donald_pos[0] + self.config.CHARACTER_SIZE // 2
        start_y = self.donald_pos[1] + self.config.CHARACTER_SIZE // 2
        
        # 随机选择红包类型
        packet_type = random.randint(0, 2)
        sizes = [(30, 40), (50, 60), (70, 80)]
        colors = [(255, 0, 0), (255, 100, 100), (200, 0, 0)]
        amounts = [(1, 10), (10, 50), (50, 100)]
        
        packet = {
            'x': start_x,
            'y': start_y,
            'size': sizes[packet_type],
            'color': colors[packet_type],
            'amount': round(random.uniform(amounts[packet_type][0], amounts[packet_type][1]), 2),
            'dx': random.uniform(-3, 3),
            'dy': random.uniform(-3, 3),
            'type': packet_type,
            'active': True
        }
        
        self.red_packets.append(packet)
    
    def update_red_packets(self):
        """更新红包位置"""
        for packet in self.red_packets[:]:
            if not packet['active']:
                continue
                
            # 更新位置
            packet['x'] += packet['dx']
            packet['y'] += packet['dy']
            
            # 检查边界碰撞
            if (packet['x'] <= 0 or packet['x'] >= self.config.SCREEN_WIDTH - packet['size'][0] or
                packet['y'] <= 0 or packet['y'] >= self.config.SCREEN_HEIGHT - packet['size'][1]):
                
                # 红包碰壁，统计金额
                self.statistics['total_count'] += 1
                self.statistics['total_amount'] += packet['amount']
                self.statistics['type_counts'][packet['type']] += 1
                self.statistics['type_amounts'][packet['type']] += packet['amount']
                
                # 标记为非激活
                packet['active'] = False
                self.red_packets.remove(packet)
    
    def update_duckling_positions(self):
        """更新汤小鸭位置 - 全图移动，避免与唐老鸭重合"""
        if not self.duckling_moving:
            return
        
        import random
        import math
        
        # 初始化汤小鸭移动状态（如果还没有）
        if not hasattr(self, 'duckling_movement_data'):
            self.duckling_movement_data = []
            for i in range(len(self.duckling_positions)):
                self.duckling_movement_data.append({
                    'dx': random.uniform(-2, 2),
                    'dy': random.uniform(-2, 2),
                    'direction': random.randint(1, 4)  # 1:右下, 2:左下, 3:左上, 4:右上
                })
        
        for i in range(len(self.duckling_positions)):
            movement = self.duckling_movement_data[i]
            current_x, current_y = self.duckling_positions[i]
            
            # 更新位置
            new_x = current_x + movement['dx']
            new_y = current_y + movement['dy']
            
            # 边界反弹逻辑（参考原始红包游戏）
            if new_x <= 0:
                new_x = 0
                if movement['direction'] == 2:  # 左下 -> 右下
                    movement['direction'] = 1
                elif movement['direction'] == 3:  # 左上 -> 右上
                    movement['direction'] = 4
                movement['dx'] = abs(movement['dx'])
            elif new_x >= self.config.SCREEN_WIDTH - (self.config.CHARACTER_SIZE - 20):
                new_x = self.config.SCREEN_WIDTH - (self.config.CHARACTER_SIZE - 20)
                if movement['direction'] == 1:  # 右下 -> 左下
                    movement['direction'] = 2
                elif movement['direction'] == 4:  # 右上 -> 左上
                    movement['direction'] = 3
                movement['dx'] = -abs(movement['dx'])
            
            if new_y <= 0:
                new_y = 0
                if movement['direction'] == 3:  # 左上 -> 左下
                    movement['direction'] = 2
                elif movement['direction'] == 4:  # 右上 -> 右下
                    movement['direction'] = 1
                movement['dy'] = abs(movement['dy'])
            elif new_y >= self.config.SCREEN_HEIGHT - (self.config.CHARACTER_SIZE - 20):
                new_y = self.config.SCREEN_HEIGHT - (self.config.CHARACTER_SIZE - 20)
                if movement['direction'] == 1:  # 右下 -> 右上
                    movement['direction'] = 4
                elif movement['direction'] == 2:  # 左下 -> 左上
                    movement['direction'] = 3
                movement['dy'] = -abs(movement['dy'])
            
            # 检查是否与唐老鸭重合
            donald_rect = pygame.Rect(self.donald_pos[0], self.donald_pos[1], 
                                     self.config.CHARACTER_SIZE, self.config.CHARACTER_SIZE)
            duckling_rect = pygame.Rect(new_x, new_y, 
                                      self.config.CHARACTER_SIZE - 20, self.config.CHARACTER_SIZE - 20)
            
            if donald_rect.colliderect(duckling_rect):
                # 如果重合，改变移动方向
                movement['dx'] = -movement['dx']
                movement['dy'] = -movement['dy']
                # 重新计算位置
                new_x = current_x + movement['dx']
                new_y = current_y + movement['dy']
                
                # 确保不重合
                if pygame.Rect(new_x, new_y, self.config.CHARACTER_SIZE - 20, self.config.CHARACTER_SIZE - 20).colliderect(donald_rect):
                    # 如果还是重合，随机选择新方向
                    movement['dx'] = random.uniform(-2, 2)
                    movement['dy'] = random.uniform(-2, 2)
                    new_x = current_x + movement['dx']
                    new_y = current_y + movement['dy']
            
            # 更新位置
            self.duckling_positions[i] = (new_x, new_y)
    
    def end_red_packet_game(self):
        """结束红包游戏"""
        self.red_packet_game_active = False
        self.duckling_moving = False
        
        # 重置汤小鸭位置到原始位置
        self.duckling_positions = self.duckling_positions_original.copy()
        
        # 清理移动数据
        if hasattr(self, 'duckling_movement_data'):
            delattr(self, 'duckling_movement_data')
        
        # 显示统计结果
        result = f"红包游戏统计:\n"
        result += f"总红包数: {self.statistics['total_count']}\n"
        result += f"总金额: ¥{self.statistics['total_amount']:.2f}\n"
        result += f"小红包: {self.statistics['type_counts'][0]}个, ¥{self.statistics['type_amounts'][0]:.2f}\n"
        result += f"中红包: {self.statistics['type_counts'][1]}个, ¥{self.statistics['type_amounts'][1]:.2f}\n"
        result += f"大红包: {self.statistics['type_counts'][2]}个, ¥{self.statistics['type_amounts'][2]:.2f}\n"
        
        # 使用线程安全的方式显示结果
        self._update_text_display(f"唐老鸭: 红包游戏结束！\n{result}\n")
        
        # 清理红包
        self.red_packets = []
    
    def start_red_packet_visual_effect(self):
        """启动红包游戏视觉效果"""
        # 在游戏主界面显示红包游戏状态
        self.red_packet_game_active = True
        self.red_packet_timer = 0
        self.red_packets = []  # 存储红包对象
        
        # 生成一些红包
        import random
        for i in range(10):
            packet = {
                'x': random.randint(0, self.config.SCREEN_WIDTH - 50),
                'y': random.randint(0, self.config.SCREEN_HEIGHT - 50),
                'size': random.choice([(30, 40), (50, 60), (70, 80)]),
                'color': random.choice([(255, 0, 0), (255, 100, 100), (200, 0, 0)]),
                'amount': round(random.uniform(1, 100), 2),
                'dx': random.uniform(-2, 2),  # 移动速度x
                'dy': random.uniform(-2, 2)   # 移动速度y
            }
            self.red_packets.append(packet)
    
    def start_ai_chat(self, user_input):
        """启动AI对话"""
        try:
            # 显示正在思考
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, "唐老鸭: 让我想想...\n")
                self.text_display.see(tk.END)
            
            # 使用OpenAI客户端
            response = self.openai_client.chat.completions.create(
                model="deepseek-r1:8b",
                messages=[
                    {"role": "system", "content": "你是唐老鸭，一个友善的卡通角色。请用中文回答用户的问题，保持幽默和友好的语调。"},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
            ai_response = response.choices[0].message.content
            if not ai_response.strip():
                ai_response = "抱歉，我没有理解你的问题，请重新提问。"
            
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: {ai_response}\n\n")
                self.text_display.see(tk.END)
                
        except Exception as e:
            print(f"AI对话错误: {e}")
            if hasattr(self, 'text_display'):
                self.text_display.insert(tk.END, f"唐老鸭: 抱歉，AI服务出现了问题: {str(e)}\n\n")
                self.text_display.see(tk.END)
    
    def start_code_counting(self, target_dir=None):
        """启动代码统计（可能在后台线程中运行）"""
        try:
            # 显示开始统计信息（使用线程安全的方式）
            self._update_text_display("唐老鸭: 正在统计代码量，请稍候...\n")        
            
            # 确定要统计的目录
            if target_dir is None:
                target_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 统计代码量
            result = self.code_counter.count_code_by_language(target_dir)
            summary = result["summary"]
            by_language = result["by_language"]
            elapsed_time = result["elapsed_time"]
            
            # 生成统计报告文本
            report_text = f"代码统计报告:\n"
            report_text += f"{'='*50}\n"
            report_text += f"统计目录: {target_dir}\n"
            report_text += f"总文件数: {summary.files}\n"
            report_text += f"总行数: {summary.total}\n"
            report_text += f"代码行数: {summary.code}\n"
            report_text += f"注释行数: {summary.comment}\n"
            report_text += f"空行数: {summary.blank}\n"
            report_text += f"耗时: {elapsed_time:.3f} 秒\n\n"
            report_text += f"按语言统计:\n"
            report_text += f"{'语言':<20} {'文件数':<10} {'代码行数':<15}\n"
            report_text += "-" * 50 + "\n"
            
            # 按代码行数排序
            sorted_langs = sorted(by_language.items(), key=lambda x: -x[1].code)
            for lang, stat in sorted_langs[:10]:  # 只显示前10个
                report_text += f"{lang:<20} {stat.files:<10} {stat.code:<15}\n"
            
            # 统计Python函数
            function_stats = self.code_counter.count_python_functions(target_dir)
            
            if function_stats.total_functions > 0:
                report_text += f"\nPython函数统计:\n"
                report_text += f"总函数数: {function_stats.total_functions}\n"
                report_text += f"平均长度: {function_stats.mean_length:.2f} 行\n"
                report_text += f"中位数长度: {function_stats.median_length:.2f} 行\n"
                report_text += f"最小长度: {function_stats.min_length} 行\n"
                report_text += f"最大长度: {function_stats.max_length} 行\n"
            
            # 显示文本结果（使用线程安全的方式）
            self._update_text_display(f"唐老鸭: 代码统计完成！\n{report_text}\n")
            
            # 打开图形化窗口（需要在主线程中调用）
            # 主线程显示图表（通过队列）
            self._enqueue_show_charts(result, function_stats)
            
        except Exception as e:
            print(f"代码统计错误: {e}")
            import traceback
            traceback.print_exc()
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，代码统计出现了问题: {str(e)}\n\n")
    
    def show_code_statistics_charts(self, code_result, function_stats):
        """显示代码统计图表"""
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            # 设置中文字体与负号显示
            try:
                matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
                matplotlib.rcParams['axes.unicode_minus'] = False
            except Exception:
                pass
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # 确保有Tk根窗口，且可见（某些系统在根窗口withdraw时Toplevel不可见）
            if not hasattr(self, '_root') or self._root is None:
                self._root = tk.Tk()
                try:
                    self._root.protocol("WM_DELETE_WINDOW", lambda: None)
                except Exception:
                    pass
            try:
                # 让root极小且不干扰：1x1，并尽量降低到后台
                self._root.deiconify()
                self._root.geometry("1x1+10+10")
                try:
                    self._root.lower()
                except Exception:
                    pass
            except Exception:
                pass
            
            # 创建新窗口
            chart_window = tk.Toplevel(self._root)
            chart_window.title("代码统计图表")
            chart_window.geometry("1200x700")
            try:
                chart_window.minsize(900, 560)
            except Exception:
                pass
            chart_window.resizable(True, True)
            
            # 保证可见并置前一次，随后交还焦点
            try:
                chart_window.deiconify()
                chart_window.attributes('-topmost', True)
                chart_window.lift()
                # 100ms后取消topmost，避免影响输入法/最小化
                chart_window.after(100, lambda: chart_window.attributes('-topmost', False))
            except Exception:
                pass
            
            # 按钮区放在上方，内容区在下方，按钮在两页都可见
            button_frame = tk.Frame(chart_window)
            button_frame.pack(fill=tk.X, padx=10, pady=8)
            
            tab_frame = tk.Frame(chart_window, bd=1, relief=tk.GROOVE)
            tab_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
            # 防止内容自适应压缩外层尺寸
            try:
                tab_frame.pack_propagate(False)
            except Exception:
                pass
            
            # 保存引用，便于切换
            self._chart_window = chart_window
            self._chart_tab_frame = tab_frame
            # 仅保存“按语言统计”部分，避免把summary/elapsed_time当作语言
            try:
                by_lang = code_result.get('by_language') if isinstance(code_result, dict) else None
            except Exception:
                by_lang = None
            self._chart_code_result = by_lang if by_lang is not None else code_result
            self._chart_function_stats = function_stats
            
            tk.Button(button_frame, text="代码统计", 
                     command=self.switch_to_code_tab).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="函数统计", 
                     command=self.switch_to_function_tab).pack(side=tk.LEFT, padx=5)
            
            # 默认显示代码统计
            self.show_code_chart_tab(tab_frame, self._chart_code_result)
            
        except ImportError:
            messagebox.showwarning("警告", "需要安装matplotlib才能显示图表:\npip install matplotlib")
        except Exception as e:
            print(f"显示图表错误: {e}")
            messagebox.showerror("错误", f"显示图表时出错: {str(e)}")

    def switch_to_code_tab(self):
        try:
            if hasattr(self, '_chart_tab_frame') and self._chart_tab_frame is not None and hasattr(self, '_chart_code_result'):
                self.show_code_chart_tab(self._chart_tab_frame, self._chart_code_result)
        except Exception as e:
            print(f"切换到代码统计错误: {e}")

    def switch_to_function_tab(self):
        try:
            if hasattr(self, '_chart_tab_frame') and self._chart_tab_frame is not None and hasattr(self, '_chart_function_stats'):
                self.show_function_chart_tab(self._chart_tab_frame, self._chart_function_stats)
        except Exception as e:
            print(f"切换到函数统计错误: {e}")
    
    def _clear_container(self, container):
        try:
            for child in container.winfo_children():
                child.destroy()
        except Exception:
            pass

    def show_code_chart_tab(self, container, code_result):
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            # 再保证中文
            try:
                matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
                matplotlib.rcParams['axes.unicode_minus'] = False
            except Exception:
                pass

            self._clear_container(container)

            # 解析语言->代码行数
            labels = []
            values = []

            # 尝试多种结构的兼容
            try:
                items_iter = code_result.items() if hasattr(code_result, 'items') else []
                for lang, stat in items_iter:
                    code_lines = None
                    if hasattr(stat, 'code'):
                        code_lines = getattr(stat, 'code')
                    elif isinstance(stat, dict) and 'code' in stat:
                        code_lines = stat['code']
                    elif isinstance(stat, (int, float)):
                        code_lines = int(stat)
                    if code_lines is None:
                        continue
                    labels.append(str(lang))
                    values.append(int(code_lines))
            except Exception:
                pass

            if not labels:
                # 兜底：无数据
                empty_label = tk.Label(container, text="没有可显示的代码统计数据", font=("Microsoft YaHei", 12))
                empty_label.pack(pady=20)
                return

            # 图表
            fig, axes = plt.subplots(1, 2, figsize=(10, 4))
            # 柱状图
            axes[0].bar(labels, values, color="#4C9AFF")
            axes[0].set_title("各语言代码行数（柱状图）")
            axes[0].set_ylabel("行数")
            axes[0].tick_params(axis='x', rotation=45)
            # 饼图
            axes[1].pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            axes[1].set_title("各语言占比（饼图）")
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            self._clear_container(container)
            err = tk.Label(container, text=f"显示代码统计出错: {e}")
            err.pack(pady=16)

    def show_function_chart_tab(self, container, function_stats):
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            # 再保证中文
            try:
                matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
                matplotlib.rcParams['axes.unicode_minus'] = False
            except Exception:
                pass

            self._clear_container(container)

            lengths = []
            summary_text = None
            summary_vals = None

            # 尝试解析多种结构
            try:
                if hasattr(function_stats, 'functions'):
                    funcs = getattr(function_stats, 'functions')
                    for f in funcs:
                        if hasattr(f, 'length'):
                            lengths.append(int(getattr(f, 'length')))
                elif isinstance(function_stats, dict) and 'functions' in function_stats:
                    for f in function_stats['functions']:
                        if isinstance(f, dict) and 'length' in f:
                            lengths.append(int(f['length']))

                # 解析汇总
                if hasattr(function_stats, 'mean_length'):
                    mean_v = getattr(function_stats, 'mean_length', None)
                    median_v = getattr(function_stats, 'median_length', None)
                    min_v = getattr(function_stats, 'min_length', None)
                    max_v = getattr(function_stats, 'max_length', None)
                    summary_vals = {
                        '均值': mean_v,
                        '中位数': median_v,
                        '最小': min_v,
                        '最大': max_v,
                    }
                    summary_text = f"均值: {mean_v}  最大: {max_v}  最小: {min_v}  中位数: {median_v}"
                elif isinstance(function_stats, dict) and 'summary' in function_stats:
                    s = function_stats['summary']
                    summary_vals = {
                        '均值': s.get('mean'),
                        '中位数': s.get('median'),
                        '最小': s.get('min'),
                        '最大': s.get('max'),
                    }
                    summary_text = f"均值: {s.get('mean')}  最大: {s.get('max')}  最小: {s.get('min')}  中位数: {s.get('median')}"
            except Exception:
                pass

            # 顶部统计文字
            top = tk.Frame(container)
            top.pack(fill=tk.X)
            if summary_text:
                tk.Label(top, text=summary_text, anchor='w').pack(side=tk.LEFT, padx=8, pady=8)

            if lengths:
                fig, ax = plt.subplots(1, 1, figsize=(8, 4))
                ax.hist(lengths, bins=min(50, max(5, len(set(lengths)))) , color="#00C853", edgecolor='black')
                ax.set_title("Python 函数长度直方图")
                ax.set_xlabel("行数")
                ax.set_ylabel("函数个数")
                plt.tight_layout()
            else:
                if not summary_vals:
                    empty_label = tk.Label(container, text="没有可显示的函数长度数据", font=("Microsoft YaHei", 12))
                    empty_label.pack(pady=20)
                    return
                # 使用汇总值画条形图
                labels = list(summary_vals.keys())
                values = [summary_vals[k] if summary_vals[k] is not None else 0 for k in labels]
                fig, ax = plt.subplots(1, 1, figsize=(8, 4))
                ax.bar(labels, values, color="#26A69A")
                ax.set_title("Python 函数长度统计")
                ax.set_ylabel("行数")
                plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            self._clear_container(container)
            err = tk.Label(container, text=f"显示函数统计出错: {e}")
            err.pack(pady=16)
    
    def _update_text_display(self, text):
        """将文本更新请求放入队列，由主线程消费后更新Tkinter组件。"""
        try:
            self._ui_queue.put(("append_text", text), block=False)
        except Exception as e:
            print(f"提交文本更新到队列失败: {e}")

    def _enqueue_show_charts(self, code_result, function_stats):
        """将显示图表的请求放入队列，由主线程处理。"""
        try:
            self._ui_queue.put(("show_charts", code_result, function_stats), block=False)
        except Exception as e:
            print(f"提交图表显示到队列失败: {e}")

    def _process_ui_queue(self, limit_per_frame: int = 20):
        """在主线程中调用：消费UI队列并执行对应Tk操作。"""
        processed = 0
        while not self._ui_queue.empty() and processed < limit_per_frame:
            try:
                item = self._ui_queue.get_nowait()
            except Exception:
                break
            processed += 1
            if not item:
                continue
            kind = item[0]
            try:
                if kind == "append_text":
                    text = item[1]
                    if hasattr(self, 'text_display') and self.text_display:
                        self.text_display.insert(tk.END, text)
                        self.text_display.see(tk.END)
                elif kind == "show_charts":
                    code_result, function_stats = item[1], item[2]
                    self.show_code_statistics_charts(code_result, function_stats)
            except Exception as e:
                print(f"处理UI队列项出错: {e}")
    
    def get_ai_response(self, user_input):
        """获取AI响应（在后台线程中运行）"""
        try:
            # 显示正在思考（使用线程安全的方式）
            self._update_text_display("唐老鸭: 让我想想...\n")
            
            # 使用OpenAI客户端
            response = self.openai_client.chat.completions.create(
                model="deepseek-r1:8b",
                messages=[
                    {"role": "system", "content": "你是唐老鸭，一个友善的卡通角色。请用中文回答用户的问题，保持幽默和友好的语调。"},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
            ai_response = response.choices[0].message.content
            if not ai_response.strip():
                ai_response = "抱歉，我没有理解你的问题，请重新提问。"
            
            # 使用线程安全的方式更新UI
            self._update_text_display(f"唐老鸭: {ai_response}\n\n")
                
        except Exception as e:
            print(f"AI响应错误: {e}")
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，我暂时无法回答这个问题: {str(e)}\n\n")
    
    def render(self):
        """渲染游戏画面"""
        # 清屏
        self.screen.fill(self.config.background_color)
        
        # 绘制背景装饰
        self.render_background()
        
        # 绘制角色
        self.render_characters()
        
        # 绘制红包游戏效果
        if hasattr(self, 'red_packet_game_active') and self.red_packet_game_active:
            self.render_red_packets()
        
        # 绘制UI信息
        self.render_ui()
        
        # 更新显示
        pygame.display.flip()
    
    def render_red_packets(self):
        """绘制红包"""
        if not hasattr(self, 'red_packets'):
            return
        
        for packet in self.red_packets:
            if not packet.get('active', True):
                continue
            
            # 绘制红包
            packet_rect = pygame.Rect(packet['x'], packet['y'], packet['size'][0], packet['size'][1])
            pygame.draw.rect(self.screen, packet['color'], packet_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), packet_rect, 2)
            
            # 绘制金额
            font = pygame.font.Font(None, 16)
            amount_text = font.render(f"¥{packet['amount']}", True, (255, 255, 255))
            text_rect = amount_text.get_rect(center=(packet['x'] + packet['size'][0]//2, 
                                                   packet['y'] + packet['size'][1]//2))
            self.screen.blit(amount_text, text_rect)
    
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
            # 使用当前位置
            current_x, current_y = pos
            
            duckling_rect = pygame.Rect(current_x, current_y, 
                                      self.config.CHARACTER_SIZE - 20, self.config.CHARACTER_SIZE - 20)
            pygame.draw.ellipse(self.screen, self.config.DUCKLING_COLOR, duckling_rect)
            pygame.draw.ellipse(self.screen, (0, 0, 0), duckling_rect, 2)
            
            # 绘制眼睛
            eye_size = 6
            eye_y = current_y + (self.config.CHARACTER_SIZE - 20) // 3
            pygame.draw.circle(self.screen, (0, 0, 0), 
                             (current_x + (self.config.CHARACTER_SIZE - 20) // 3, eye_y), eye_size)
            pygame.draw.circle(self.screen, (0, 0, 0), 
                             (current_x + 2 * (self.config.CHARACTER_SIZE - 20) // 3, eye_y), eye_size)
    
    def render_ui(self):
        """绘制UI信息"""
        # 绘制标题 - 使用英文避免中文字符问题
        title_text = self.font.render("Duck Game", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        hint_text = self.small_font.render("Click Donald Duck to start!", True, (0, 0, 0))
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
            
            # 更新红包游戏状态
            self.update_red_packet_game()
            
            # 检查并创建对话框（如果需要）
            self._check_and_create_dialog()
            
            # 统一更新Tk：无论对话框是否打开，只要_root存在就驱动事件循环与队列
            if hasattr(self, '_root') and self._root:
                try:
                    self._root.update_idletasks()
                    try:
                        self._root.update()
                    except Exception:
                        pass
                    # 消费UI队列（保证所有Tk调用在主线程执行）
                    self._process_ui_queue()
                except Exception as e:
                    print(f"更新Tk循环错误: {e}")
            
            # 如果对话框打开，检查其可见性与状态
            if self.dialog_active:
                try:
                    if hasattr(self, 'dialog_window') and self.dialog_window:
                        try:
                            if self.dialog_window.winfo_exists():
                                try:
                                    state = self.dialog_window.state()
                                except Exception:
                                    state = 'normal'
                                if state == 'withdrawn':
                                    self.dialog_window.deiconify()
                            else:
                                self.dialog_active = False
                                self.dialog_window = None
                                print("对话框窗口已销毁")
                        except (tk.TclError, AttributeError) as e:
                            self.dialog_active = False
                            self.dialog_window = None
                            print(f"对话框窗口检查错误: {e}")
                except Exception as e:
                    print(f"对话框状态更新错误: {e}")

            # 渲染游戏
            self.render()
            
            # 控制帧率
            self.clock.tick(self.config.FPS)
        
        # 清理资源
        print("正在清理资源...")
        try:
            # 关闭对话框
            if hasattr(self, 'dialog_window') and self.dialog_window:
                try:
                    self.dialog_window.destroy()
                except:
                    pass
            
            # 清理tkinter
            if hasattr(self, '_root') and self._root:
                try:
                    # 先销毁所有子窗口
                    for widget in self._root.winfo_children():
                        try:
                            widget.destroy()
                        except:
                            pass
                    # 然后清理根窗口
                    self._root.quit()
                    self._root.destroy()
                except Exception as e:
                    print(f"清理tkinter时出错: {e}")
                    # 强制清理
                    try:
                        import sys
                        if 'Tkinter' in sys.modules or 'tkinter' in sys.modules:
                            self._root = None
                    except:
                        pass
        except Exception as e:
            print(f"清理资源时出错: {e}")
        
        # 关闭pygame
        try:
            pygame.quit()
        except:
            pass
        
        print("游戏结束，感谢游玩！")
        
        # 强制退出（如果还有残留进程）
        import sys
        import os
        try:
            sys.exit(0)
        except:
            os._exit(0)
    
    def update_red_packet_game(self):
        """更新红包游戏状态"""
        if not self.red_packet_game_active:
            return
        
        current_time = time.time()
        elapsed_time = current_time - self.game_start_time
        
        # 检查游戏是否结束
        if elapsed_time >= self.game_duration:
            self.end_red_packet_game()
            return
        
        # 生成红包
        self.red_packet_timer += 1
        if self.red_packet_timer >= self.red_packet_spawn_interval:
            self.spawn_red_packet()
            self.red_packet_timer = 0
        
        # 更新红包位置
        self.update_red_packets()
        
        # 更新汤小鸭位置
        self.update_duckling_positions()

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
