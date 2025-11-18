#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
唐老鸭小游戏整合项目
"""

import sys
import os
import pygame
import tkinter as tk
from tkinter import messagebox
import threading
import time
import warnings
from typing import Optional
from openai import OpenAI
from queue import Queue
import re

warnings.filterwarnings("ignore", category=SyntaxWarning)

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.config import Config
from services.advanced_code_counter import AdvancedCodeCounter
from ui.code_statistics import CodeStatisticsUI
from services.duck_behavior_manager import DuckBehaviorManager
from game.characters import Duckling
from core.game_state import GameState, GameStateManager
from core.event_system import EventManager
from game.minigames.red_packet_game import RedPacketGameManager
import random

class DuckGame:
    """主游戏类 """
    
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化pygame
        pygame.init()
        # 启用窗口调整大小功能，允许最大最小化
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Duck Game - 唐老鸭小游戏")
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        self.state_manager = GameStateManager()
        self.event_manager = EventManager()
        
        # 角色位置
        self.donald_pos = self.config.DONALD_POSITION
        self.duckling_positions = self.config.DUCKLING_POSITIONS
        
        # 初始化小鸭对象列表（每个小鸭随机外观）
        self.ducklings = []
        for i, pos in enumerate(self.duckling_positions):
            duckling = Duckling(
                pos[0], pos[1],
                self.config.CHARACTER_SIZE - 20,
                self.config.CHARACTER_SIZE - 20,
                f"唐小鸭{i+1}"
            )
            self.ducklings.append(duckling)
        
        self.red_packet_game = None
        
        # 对话框相关
        self.dialog_active = False
        
        # 红包游戏状态
        self.red_packet_game_active = False
        
        # 汤小鸭移动状态
        self.duckling_positions_original = self.duckling_positions.copy()
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        
        # 初始化增强代码统计工具
        self.code_counter = AdvancedCodeCounter()
        # 初始化行为管理器
        self.behavior_manager = DuckBehaviorManager(self._update_text_display)
        # 初始化红包游戏管理器
        self._init_red_packet_game_manager()
        
        # 初始化tkinter相关
        self._root = None
        self._need_dialog = False
        self._dialog_lock = threading.Lock()  # 用于保护对话框创建
        self._tk_running = False  # tkinter主循环是否在运行
        self._update_counter = 0  # 用于控制update()的调用频率
        self._ui_queue = Queue()  # 线程安全UI消息队列
        self._dialog_saved_geometry = None  # 保存的对话框geometry，用于恢复
        self._chart_window_created_time = None  # 图表窗口创建时间，用于临时保护
        self._tk_update_counter = 0  # 用于控制Tkinter更新频率
        self._need_set_focus = False  # 标记是否需要设置输入框焦点
        self._need_config_dialog = False  # 标记是否需要创建配置对话框
        self._last_window_pos = {}  # 记录窗口位置，用于检测拖动
        self._is_dragging = False  # 标记是否正在拖动窗口
        self._update_call_count = 0  # 计数器，限制update()调用频率
        self._drag_start_time = 0  # 拖动开始时间
        self._last_drag_check_time = 0  # 上次拖动检查时间
        self.code_stats_ui: Optional[CodeStatisticsUI] = None
        
        # 在主线程中初始化Tkinter root窗口（必须在主线程中创建）
        try:
            self._root = tk.Tk()
            self._root.withdraw()  # 隐藏根窗口
            self._root.protocol("WM_DELETE_WINDOW", lambda: None)  # 防止关闭根窗口
            # 启动after()事件处理循环，让Tkinter自己处理事件，避免在主循环中调用update()
            self._tk_event_loop_running = False
            self._start_tk_event_loop()
        except Exception as e:
            print(f"初始化Tkinter root时出错: {e}")
            self._root = None
        else:
            self.code_stats_ui = CodeStatisticsUI(
                tk_root=self._root,
                code_counter=self.code_counter,
                ui_queue=self._ui_queue,
                update_text_callback=self._update_text_display,
                trigger_behavior_callback=self.trigger_duck_behavior,
                default_target_dir=os.path.dirname(os.path.abspath(__file__)),
            )
        
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
    
    def _start_tk_event_loop(self):
        """启动Tkinter的after()事件循环（现在事件处理在主循环中完成，这里只标记）"""
        if not hasattr(self, '_root') or self._root is None:
            return
        
        # 标记事件循环已启动（虽然实际处理在主循环中）
        self._tk_event_loop_running = True
    
    def _init_red_packet_game_manager(self):
        """初始化红包游戏管理器"""
        try:
            self.red_packet_game = RedPacketGameManager(
                screen=self.screen,
                screen_width=self.config.SCREEN_WIDTH,
                screen_height=self.config.SCREEN_HEIGHT,
                duckling_positions=self.duckling_positions,
                duckling_size=self.config.CHARACTER_SIZE - 20,
                donald_pos=self.donald_pos,
                donald_size=self.config.CHARACTER_SIZE,
                event_manager=self.event_manager,
                on_statistics_update=self._handle_red_packet_statistics
            )
        except Exception as init_error:
            print(f"初始化红包游戏管理器失败: {init_error}")
            self.red_packet_game = None
    
    def _handle_red_packet_statistics(self, report: str):
        """接收红包游戏统计并显示"""
        if not report:
            return
        self._update_text_display(f"唐老鸭: 红包游戏结束！\n{report}\n")
    
    def _sync_ducklings_from_positions(self):
        """同步Duckling对象位置以匹配位置列表"""
        if not hasattr(self, 'ducklings'):
            return
        for i, pos in enumerate(self.duckling_positions):
            if i < len(self.ducklings):
                self.ducklings[i].x = pos[0]
                self.ducklings[i].y = pos[1]
    
    def update_red_packet_game(self, dt: float = 1 / 60):
        """更新红包游戏逻辑"""
        if not self.red_packet_game or not self.red_packet_game.is_active():
            return
        self.red_packet_game.update(dt)
        self._sync_ducklings_from_positions()
    
    
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
            except:
                pass
        
        # 标记需要创建对话框（在主循环中创建，确保在主线程）
        self._need_dialog = True
        print("已标记需要创建对话框")  # 调试信息
    
    def _show_code_counting_dialog(self):
        """打开代码统计配置对话框（委托给 UI 模块）"""
        if self.code_stats_ui:
            self.code_stats_ui.show_config_dialog()
        else:
            messagebox.showerror("错误", "Tk 窗口尚未初始化，无法打开配置界面。")
    
    def _check_and_create_dialog(self):
        """在主循环中调用，检查并创建对话框（非阻塞）"""
        if not self._need_dialog:
            return
        
        if self.dialog_active:
            self._need_dialog = False
            return
        
        self._need_dialog = False
        
        # 确保有Tk根窗口
        if not hasattr(self, '_root') or self._root is None:
            print("错误: Tkinter root窗口未初始化")
            self.dialog_active = False
            return
        
        # 直接创建对话框，不使用after延迟（避免事件循环问题）
        try:
            print("开始创建对话框窗口...")
            
            # 创建对话框窗口 - 确保可以拖动
            dialog_window = tk.Toplevel(self._root)
            dialog_window.title("与唐老鸭对话")
            dialog_window.geometry("600x500")
            dialog_window.minsize(400, 300)  # 设置最小大小，但允许拖动和缩放
            # 允许窗口拖动和缩放，通过智能事件处理避免GIL问题
            # 确保窗口可以拖动（Toplevel默认就可以拖动，不需要特殊设置）
            dialog_window.deiconify()
            # 确保窗口可以接收焦点和事件
            dialog_window.focus_set()
            
            # 确保after()事件循环正在运行
            if not hasattr(self, '_tk_event_loop_running') or not self._tk_event_loop_running:
                self._start_tk_event_loop()
            
            # 立即更新窗口，确保显示
            dialog_window.update_idletasks()
            
            # 创建输入框 - 确保可以正常输入中文
            input_frame = tk.Frame(dialog_window)
            input_frame.pack(pady=10, padx=10, fill=tk.X)
            tk.Label(input_frame, text="输入消息:", font=("Arial", 12)).pack(anchor=tk.W)
            self.input_entry = tk.Entry(input_frame, font=("Arial", 12), width=50)
            self.input_entry.pack(pady=5, fill=tk.X)
            # 绑定回车键事件
            self.input_entry.bind('<Return>', lambda e: self.process_input(dialog_window))
            # 确保输入框默认状态是可编辑的（Entry默认就是NORMAL，但显式设置更安全）
            self.input_entry.config(state=tk.NORMAL)
            # 不立即设置焦点，避免影响中文输入法
            # 延迟设置焦点，确保窗口完全显示后再设置
            self._need_set_focus = True
            
            # 创建显示区域
            display_frame = tk.Frame(dialog_window)
            display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            tk.Label(display_frame, text="对话记录:", font=("Arial", 12)).pack(anchor=tk.W)
            scrollbar = tk.Scrollbar(display_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.text_display = tk.Text(display_frame, height=15, width=60, font=("Arial", 10), yscrollcommand=scrollbar.set, state=tk.DISABLED)
            self.text_display.pack(pady=5, fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.text_display.yview)
            
            # 创建按钮
            button_frame = tk.Frame(dialog_window)
            button_frame.pack(pady=10)
            tk.Button(button_frame, text="发送", command=lambda: self.process_input(dialog_window), font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="关闭", command=lambda: self.close_dialog(dialog_window), font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
            
            # 保存对话框窗口引用
            self.dialog_window = dialog_window
            self.dialog_active = True
            
            # 添加欢迎消息（使用线程安全的方式，确保在主循环中执行）
            welcome_msg = "唐老鸭: 你好！我是唐老鸭，有什么可以帮助你的吗？\n\n"
            welcome_msg += "提示：\n"
            welcome_msg += "- 输入'我要抢红包'可以开始红包游戏\n"
            welcome_msg += "- 输入'我要ai问答'可以开始AI对话\n"
            welcome_msg += "- 输入'我要统计代码量'会弹出配置界面，可以选择目录、语言和统计选项\n"
            welcome_msg += "- 输入'统计代码: <目录路径>'可以快速统计指定目录的代码（使用默认设置）\n\n"
            # 使用线程安全的方式插入欢迎消息
            self._update_text_display(welcome_msg)
            # 设置关闭事件处理，确保可以点击×关闭
            def on_close():
                self.close_dialog(dialog_window)
            dialog_window.protocol("WM_DELETE_WINDOW", on_close)
            
            # 立即更新窗口，确保内容显示
            dialog_window.update_idletasks()
            # 立即调用一次update()，确保窗口和输入框可以接收事件
            try:
                dialog_window.update()
            except:
                pass
            
            # 确保窗口获得焦点
            dialog_window.focus_set()
            # 不立即设置输入框焦点，避免影响中文输入法
            # 标记需要设置焦点，将在主循环中延迟设置
            self._need_set_focus = True
            
            print(f"对话框已创建: {self.dialog_active}, 状态: {self.dialog_window.winfo_exists() if hasattr(self, 'dialog_window') else False}, 可见: {1 if hasattr(self, 'dialog_window') and self.dialog_window.winfo_viewable() else 0}")
            
        except Exception as e:
            print(f"创建对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            self.dialog_active = False
    
    
    def close_dialog(self, dialog_window=None):
        """关闭对话框（非阻塞）"""
        if dialog_window is None:
            dialog_window = getattr(self, 'dialog_window', None)
        
        print("[DEBUG] close_dialog被调用")
        try:
            if dialog_window:
                # 检查窗口是否还存在
                try:
                    if dialog_window.winfo_exists():
                        print("[DEBUG] 正在销毁窗口")
                        # 直接销毁窗口（不调用grab_release，避免阻塞）
                        dialog_window.destroy()
                        print("[DEBUG] 窗口已销毁")
                except (tk.TclError, AttributeError) as e:
                    # 窗口已经不存在
                    print(f"[DEBUG] 窗口已不存在: {e}")
                    pass
        except Exception as e:
            print(f"关闭对话框错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 重置状态
            self.dialog_active = False
            self.dialog_window = None
            self.input_entry = None
            self.text_display = None
            self._need_set_focus = False  # 重置焦点设置标志
            print("对话框已关闭")  # 调试信息
    
    def _restore_dialog_geometry(self, geometry):
        """恢复对话框窗口的geometry"""
        try:
            if hasattr(self, 'dialog_window') and self.dialog_window:
                if self.dialog_window.winfo_exists():
                    current_geometry = self.dialog_window.geometry()
                    current_width = self.dialog_window.winfo_width()
                    current_height = self.dialog_window.winfo_height()
                    
                    # 解析geometry获取期望的大小
                    import re
                    geo_match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geometry)
                    if geo_match:
                        saved_width = int(geo_match.group(1))
                        saved_height = int(geo_match.group(2))
                        saved_x = int(geo_match.group(3))
                        saved_y = int(geo_match.group(4))
                        
                        # 检查实际大小是否改变
                        if current_width != saved_width or current_height != saved_height:
                            print(f"[DEBUG] _restore_dialog_geometry: 恢复geometry")
                            print(f"[DEBUG] 当前实际大小: {current_width}x{current_height}, 目标: {saved_width}x{saved_height}")
                            # 锁定并恢复（不使用update()避免线程问题）
                            self.dialog_window.minsize(saved_width, saved_height)
                            self.dialog_window.maxsize(saved_width, saved_height)
                            self.dialog_window.resizable(False, False)
                            self.dialog_window.geometry(geometry)
                            self.dialog_window.update_idletasks()
                        elif current_geometry != geometry:
                            # geometry字符串不匹配但实际大小匹配，也需要恢复
                            self.dialog_window.geometry(geometry)
                            self.dialog_window.update_idletasks()
                    elif current_geometry != geometry:
                        # 如果解析失败，使用geometry字符串比较
                        print(f"[DEBUG] _restore_dialog_geometry: 恢复geometry")
                        print(f"[DEBUG] 当前: {current_geometry}, 目标: {geometry}")
                        self.dialog_window.geometry(geometry)
                        self.dialog_window.update_idletasks()
        except Exception as e:
            print(f"[DEBUG] _restore_dialog_geometry异常: {e}")
    
    def _set_input_focus(self):
        """设置输入框焦点（在主循环中调用，确保窗口完全显示，只设置一次）"""
        try:
            if hasattr(self, 'input_entry') and self.input_entry:
                if hasattr(self, 'dialog_window') and self.dialog_window:
                    if self.dialog_window.winfo_exists():
                        # 检查输入框是否已经有焦点，避免频繁设置
                        try:
                            focused_widget = self.dialog_window.focus_get()
                            if focused_widget == self.input_entry:
                                # 已经有焦点，不需要重复设置
                                self._need_set_focus = False
                                return
                        except:
                            pass
                        
                        # 确保窗口获得焦点
                        self.dialog_window.focus_set()
                        # 确保输入框可以使用（Entry默认就是NORMAL，但显式设置更安全）
                        self.input_entry.config(state=tk.NORMAL)
                        # 确保输入框获得焦点（只设置一次，避免影响中文输入法）
                        self.input_entry.focus_set()
                        # 只使用update_idletasks()，避免在主循环中调用update()
                        self.dialog_window.update_idletasks()
                        # 标记焦点已设置
                        self._need_set_focus = False
                        print("[DEBUG] 输入框焦点已设置")
        except Exception as e:
            print(f"[DEBUG] 设置输入框焦点失败: {e}")
            import traceback
            traceback.print_exc()
            self._need_set_focus = False
    
    def _safe_insert_text(self, text):
        """安全地插入文本到text_display（处理DISABLED状态）- 线程安全版本"""
        # 这个方法会被队列处理器调用，此时已经在主线程中，可以直接操作Tkinter组件
        try:
            if hasattr(self, 'text_display') and self.text_display:
                # 检查组件是否还存在且有效
                try:
                    if self.text_display.winfo_exists():
                        self.text_display.config(state=tk.NORMAL)
                        self.text_display.insert(tk.END, text)
                        self.text_display.see(tk.END)
                        self.text_display.config(state=tk.DISABLED)
                        # 立即更新显示（只使用update_idletasks，不使用update）
                        if hasattr(self, 'dialog_window') and self.dialog_window:
                            try:
                                if self.dialog_window.winfo_exists():
                                    self.dialog_window.update_idletasks()
                            except:
                                pass
                except tk.TclError as e:
                    # 组件已销毁或不在主循环中，忽略错误
                    # 如果还不在主循环中，将文本重新放入队列延迟处理
                    if "main thread is not in main loop" in str(e).lower() or "main loop" in str(e).lower():
                        print(f"[DEBUG] 不在主循环中，重新放入队列: {e}")
                        # 重新放入队列，稍后处理
                        try:
                            self._ui_queue.put(("append_text", text), block=False)
                        except:
                            pass
                    pass
        except RuntimeError as e:
            # 如果是不在主循环中的错误，重新放入队列
            if "main thread is not in main loop" in str(e).lower() or "main loop" in str(e).lower():
                print(f"[DEBUG] 不在主循环中，重新放入队列: {e}")
                try:
                    self._ui_queue.put(("append_text", text), block=False)
                except:
                    pass
            else:
                print(f"[DEBUG] 插入文本失败: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"[DEBUG] 插入文本失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _safe_insert_text_thread_safe(self, text):
        """线程安全版本：将文本插入请求放入队列"""
        # 始终使用线程安全的队列机制，确保可以在任何线程中调用
        self._update_text_display(text)
    
    def process_input(self, dialog_window, event=None):
        """处理用户输入"""
        if not hasattr(self, 'input_entry') or self.input_entry is None:
            print("[DEBUG] process_input: input_entry不存在")
            return
        
        try:
            user_input = self.input_entry.get().strip()
            print(f"[DEBUG] process_input: 用户输入 = '{user_input}'")
            
            if not user_input:
                return
            
            # 显示用户输入（使用线程安全的方式，确保在主循环中执行）
            self._update_text_display(f"你: {user_input}\n")
            
            # 清空输入框（在获取输入后）
            self.input_entry.delete(0, tk.END)
            
            # 确保输入框重新获得焦点，以便继续输入
            self.input_entry.focus_set()
            
            # 处理特殊命令
            if "我要抢红包" in user_input:
                self._update_text_display("唐老鸭: 好的！让我来发红包！\n\n")
                # 启动红包游戏
                threading.Thread(target=self.start_red_packet_game, daemon=True).start()
            
            elif "我要ai问答" in user_input or user_input.startswith("我要ai问答"):
                self._update_text_display("唐老鸭: 好的！让我来回答你的问题！\n\n")
                # 启动AI问答
                threading.Thread(target=self.start_ai_chat, args=(user_input,), daemon=True).start()
            
            elif "我要统计代码量" in user_input:
                # 标记需要创建配置对话框（在主循环中创建，避免GIL问题）
                self._need_config_dialog = True
            
            elif user_input.startswith("统计代码:") or user_input.startswith("统计代码："):
                # 解析目录路径（支持 Windows 盘符冒号）
                m = re.match(r'^\s*统计代码[：:]\s*(.+)\s*$', user_input)
                if not m:
                    self._update_text_display("唐老鸭: 请提供要统计的目录路径，格式：统计代码: <目录路径>\n\n")
                    return
                path_part = m.group(1)
                # 展开引号
                if (path_part.startswith('"') and path_part.endswith('"')) or (path_part.startswith("'") and path_part.endswith("'")):
                    path_part = path_part[1:-1]
                # 规范化路径（允许包含空格）
                path_part = path_part.strip()
                # 验证路径
                if not os.path.exists(path_part):
                    self._update_text_display(f"唐老鸭: 路径不存在: {path_part}\n请检查路径是否正确。\n\n")
                    return
                self._update_text_display(f"唐老鸭: 好的！让我来统计这个目录的代码量！\n目录: {path_part}\n\n")
                # 启动代码统计
                threading.Thread(target=self.start_code_counting, args=(path_part,), daemon=True).start()
            
            else:
                # 普通AI对话
                threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()
                
        except Exception as e:
            print(f"[DEBUG] process_input错误: {e}")
            import traceback
            traceback.print_exc()
    
    def start_red_packet_game(self):
        """启动红包游戏"""
        try:
            # 显示游戏开始信息（使用线程安全的方式）
            self._update_text_display("唐老鸭: 红包游戏开始！唐小鸭们开始移动！\n")
            
            # 启动红包游戏逻辑（在主线程中直接设置状态，不需要后台线程）
            self.start_red_packet_game_logic()
            
        except Exception as e:
            print(f"红包游戏错误: {e}")
            import traceback
            traceback.print_exc()
            self._update_text_display(f"唐老鸭: 抱歉，红包游戏出现了问题: {str(e)}\n\n")
    
    def start_red_packet_game_logic(self):
        """启动红包游戏逻辑"""
        # 初始化游戏状态
        self.red_packet_game_active = True
        if not self.red_packet_game:
            self._init_red_packet_game_manager()
        if self.red_packet_game:
            self.red_packet_game.start(duration=30)
        self.state_manager.set_state(GameState.RED_PACKET_GAME)
        self.game_start_time = time.time()
        self.game_duration = 30
        
        # 切换小鸭外观为兴奋主题（红包主题）- 通过UI队列确保在主线程执行
        self._ui_queue.put(("change_duckling_theme", "excited"))
        # 触发红包行为
        self.trigger_duck_behavior("red_packet")
    
    
    
    def end_red_packet_game(self):
        """结束红包游戏"""
        self.red_packet_game_active = False
        self.state_manager.set_state(GameState.IDLE)
        
        if self.red_packet_game:
            self.red_packet_game.stop()
        
        # 恢复小鸭的原始外观 - 通过UI队列确保在主线程执行
        self._ui_queue.put(("change_duckling_theme", "original"))
        
        # 同步位置
        self._sync_ducklings_from_positions()
    
    
    def start_ai_chat(self, user_input):
        """启动AI对话"""
        try:
            # 触发AI行为
            self.trigger_duck_behavior("ai_chat")
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
            
            # 使用线程安全的方式显示结果
            self._update_text_display(f"唐老鸭: {ai_response}\n\n")
                
        except Exception as e:
            print(f"AI对话错误: {e}")
            import traceback
            traceback.print_exc()
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，AI服务出现了问题: {str(e)}\n\n")
    
    def start_code_counting(self, *args, **kwargs):
        """兼容旧调用，委托给 CodeStatisticsUI 执行实际统计逻辑。"""
        if not self.code_stats_ui:
            self._update_text_display("唐老鸭: Tk 界面未初始化，暂时无法统计代码。\n")
            return
        self.code_stats_ui.start_code_counting(*args, **kwargs)
    def show_code_statistics_charts(self, code_result, function_stats=None, c_function_stats=None, detail_table=None):
        """兼容旧调用，转由 CodeStatisticsUI 负责绘制。"""
        if self.code_stats_ui:
            self.code_stats_ui.show_charts(code_result, function_stats, c_function_stats, detail_table)
        else:
            messagebox.showwarning("警告", "图表渲染组件未初始化。")

    def _create_code_stat_chart(self, code_result):
        """已废弃的遗留接口，保留占位。"""
        return
        """
        try:
            import matplotlib.pyplot as plt

            # 解析语言->代码行数
            labels = []
            values = []

            try:
                # code_result是一个字典，包含 "summary", "by_language", "elapsed_time"
                # 需要从 by_language 中提取数据
                if isinstance(code_result, dict) and "by_language" in code_result:
                    by_language = code_result["by_language"]
                    # by_language 是一个字典，键是语言名称，值是统计数据对象
                    for lang, stat in by_language.items():
                        code_lines = None
                        if hasattr(stat, 'code'):
                            code_lines = getattr(stat, 'code')
                        elif isinstance(stat, dict) and 'code' in stat:
                            code_lines = stat['code']
                        elif isinstance(stat, (int, float)):
                            code_lines = int(stat)
                        if code_lines is None or code_lines == 0:
                            continue
                        labels.append(str(lang))  # 语言名称
                        values.append(int(code_lines))
                elif hasattr(code_result, 'items'):
                    # 如果直接是字典格式
                    for lang, stat in code_result.items():
                        if lang == "summary" or lang == "elapsed_time":
                            continue  # 跳过summary和elapsed_time
                        code_lines = None
                        if hasattr(stat, 'code'):
                            code_lines = getattr(stat, 'code')
                        elif isinstance(stat, dict) and 'code' in stat:
                            code_lines = stat['code']
                        elif isinstance(stat, (int, float)):
                            code_lines = int(stat)
                        if code_lines is None or code_lines == 0:
                            continue
                        labels.append(str(lang))
                        values.append(int(code_lines))
            except Exception as e:
                print(f"[DEBUG] 解析代码统计数据错误: {e}")
                import traceback
                traceback.print_exc()
                return

            if not labels:
                print("[DEBUG] 没有找到有效的语言统计数据")
                return

            # 按代码行数排序（降序）
            sorted_data = sorted(zip(labels, values), key=lambda x: -x[1])
            labels = [lang for lang, _ in sorted_data]
            values = [val for _, val in sorted_data]

            # 创建独立的matplotlib窗口
            fig = plt.figure(figsize=(12, 6))
            fig.canvas.manager.set_window_title('代码统计图表')
            
            # 创建两个子图
            ax1 = fig.add_subplot(121)
            ax2 = fig.add_subplot(122)
            
            # 柱状图
            ax1.bar(labels, values, color="#4C9AFF")
            ax1.set_title("各语言代码行数（柱状图）", fontsize=12)
            ax1.set_ylabel("行数", fontsize=10)
            ax1.tick_params(axis='x', rotation=45, labelsize=9)
            ax1.tick_params(axis='y', labelsize=9)
            
            # 饼图
            ax2.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
            ax2.set_title("各语言占比（饼图）", fontsize=12)
            
            plt.tight_layout()
            plt.show(block=False)  # 非阻塞显示
            
        except Exception as e:
            print(f"创建代码统计图表错误: {e}")
            import traceback
            traceback.print_exc()
        """

    def _create_function_stat_chart(self, function_stats, lang_name="Python"):
        """已废弃，保留兼容。"""
        return

    def switch_to_code_tab(self):
        """切换到代码统计标签页 - 已废弃，使用独立窗口"""
        pass

    def switch_to_function_tab(self):
        """切换到函数统计标签页 - 已废弃，使用独立窗口"""
        pass
    
    def _clear_container(self, container):
        try:
            for child in container.winfo_children():
                child.destroy()
        except Exception:
            pass

    def show_code_chart_tab(self, container, code_result):
        """已废弃 - 使用独立matplotlib窗口"""
        # 这个方法已废弃，保留以避免调用错误
        pass

    def show_function_chart_tab(self, container, function_stats):
        """已废弃 - 使用独立matplotlib窗口"""
        # 这个方法已废弃，保留以避免调用错误
        pass
    
    def _update_text_display(self, text):
        """将文本更新请求放入队列，由主线程消费后更新Tkinter组件。"""
        try:
            self._ui_queue.put(("append_text", text), block=False)
        except Exception as e:
            print(f"提交文本更新到队列失败: {e}")

    def _enqueue_show_charts(self, code_result, function_stats=None, c_function_stats=None, detail_table=None):
        """兼容旧逻辑，转由 UI 控制器调度。"""
        try:
            self._ui_queue.put(("show_charts", code_result, function_stats, c_function_stats, detail_table), block=False)
        except Exception as e:
            print(f"提交图表显示到队列失败: {e}")

    def trigger_duck_behavior(self, event_name: str):
        """将行为触发放入队列，确保在主线程中执行。"""
        try:
            self._ui_queue.put(("duck_behavior", event_name), block=False)
        except Exception as e:
            print(f"提交行为触发到队列失败: {e}")

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
                    # 确保在Tkinter事件循环中执行
                    if hasattr(self, '_root') and self._root:
                        # 先更新idle任务，确保事件循环处于活动状态
                        try:
                            self._root.update_idletasks()
                            # 现在可以安全地调用_safe_insert_text
                            self._safe_insert_text(text)
                        except Exception as e:
                            print(f"[DEBUG] 处理文本更新时出错: {e}")
                            # 如果出错，尝试延迟处理
                            import traceback
                            traceback.print_exc()
                elif kind == "show_charts":
                    code_result = item[1]
                    function_stats = item[2] if len(item) > 2 else None
                    c_function_stats = item[3] if len(item) > 3 else None
                    detail_table = item[4] if len(item) > 4 else None
                    if self.code_stats_ui:
                        self.code_stats_ui.show_charts(code_result, function_stats, c_function_stats, detail_table)
                elif kind == "change_duckling_theme":
                    theme = item[1] if len(item) > 1 else "original"
                    # 在主线程中切换小鸭外观
                    if hasattr(self, 'ducklings') and self.ducklings:
                        for duckling in self.ducklings:
                            if theme == "excited":
                                duckling.switch_to_excited_theme()
                            elif theme == "focused":
                                duckling.switch_to_focused_theme()
                            elif theme == "original":
                                duckling.restore_original_appearance()
                elif kind == "duck_behavior":
                    event_name = item[1]
                    if hasattr(self, 'behavior_manager'):
                        self.behavior_manager.trigger(event_name, getattr(self, 'ducklings', []))
            except Exception as e:
                print(f"处理UI队列项出错: {e}")
                import traceback
                traceback.print_exc()
    
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
        if self.red_packet_game and self.red_packet_game.is_active():
            self.red_packet_game.render(self.screen)
    
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
        pygame.draw.rect(self.screen, ground_color, (0, self.config.SCREEN_HEIGHT - 50, self.config.SCREEN_WIDTH, 50))
    
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
        
        # 绘制汤小鸭（使用Duckling对象）
        for duckling in self.ducklings:
            duckling.render(self.screen)
    
    def render_ui(self):
        """绘制UI信息"""
        # 绘制标题 - 使用英文避免中文字符问题
        title_text = self.font.render("Duck Game", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # 绘制提示信息
        hint_text = self.small_font.render("Click Donald Duck to start!", True, (0, 0, 0))
        self.screen.blit(hint_text, (10, 50))
    
    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # 处理窗口大小改变事件
                    # Pygame会自动更新屏幕大小，我们只需要更新配置
                    self.config.SCREEN_WIDTH = event.w
                    self.config.SCREEN_HEIGHT = event.h
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        self.handle_click(event.pos)
            
            # 更新游戏状态
            self.update()
            
            # 渲染画面
            self.render()
            
            # 定期更新Tkinter，确保输入和关闭事件能够被处理
            # 直接在主循环中调用update()，但使用较低的频率和异常处理
            if hasattr(self, '_root') and self._root and (self.dialog_active or hasattr(self, '_config_window')):
                try:
                    # 更新计数器
                    if hasattr(self, '_tk_update_counter'):
                        self._tk_update_counter += 1
                    else:
                        self._tk_update_counter = 0
                    
                    # 每帧都调用update_idletasks()，确保UI更新
                    self._root.update_idletasks()
                    
                    # 每5帧（约83ms）调用一次update()，处理键盘和关闭事件
                    # 这是关键：必须调用update()才能处理键盘和关闭事件
                    # 频率适中，既能处理事件，又不会影响中文输入法的提示词框
                    if self._tk_update_counter % 5 == 0:
                        try:
                            # 直接调用update()处理事件
                            # 适中的频率，确保输入法提示词框正常显示
                            self._root.update()
                        except (tk.TclError, RuntimeError, Exception):
                            # 忽略所有错误，确保程序继续运行
                            pass
                    
                    # 处理UI队列中的更新请求
                    try:
                        self._process_ui_queue()
                    except Exception:
                        pass
                    
                    # 如果需要设置输入框焦点，在主循环中设置（延迟几帧确保窗口完全显示）
                    if hasattr(self, '_need_set_focus') and self._need_set_focus:
                        if self._tk_update_counter > 10:  # 延迟约10帧（约167ms）再设置焦点
                            self._set_input_focus()
                except Exception:
                    pass
            
            # 控制帧率
            clock.tick(60)
        
        # 主循环结束后清理资源
        if hasattr(self, 'behavior_manager') and self.behavior_manager:
            try:
                self.behavior_manager.clear()
                if hasattr(self.behavior_manager, 'speech_engine'):
                    self.behavior_manager.speech_engine.shutdown()
            except Exception:
                pass
        pygame.quit()
    
    def update(self):
        """更新游戏状态"""
        # 更新小鸭行为状态
        if hasattr(self, 'ducklings'):
            allow_override = not getattr(self, 'red_packet_game_active', False)
            for duckling in self.ducklings:
                if hasattr(duckling, 'update_behavior_state'):
                    duckling.update_behavior_state(allow_position_override=allow_override)
        if hasattr(self, 'behavior_manager'):
            self.behavior_manager.update()
        
        # 更新红包游戏状态（如果有）
        if hasattr(self, 'red_packet_game_active') and self.red_packet_game_active:
            self.update_red_packet_game(1 / 60)
            
            # 检查游戏是否结束（30秒后）
            if hasattr(self, 'game_start_time'):
                elapsed = time.time() - self.game_start_time
                if elapsed >= self.game_duration:
                    self.end_red_packet_game()
        
        # 检查并创建对话框（如果需要）
        self._check_and_create_dialog()
        
        # 检查并创建配置对话框（如果需要）
        if hasattr(self, '_need_config_dialog') and self._need_config_dialog:
            self._need_config_dialog = False
            try:
                self._show_code_counting_dialog()
            except Exception as e:
                print(f"创建配置对话框时出错: {e}")
                import traceback
                traceback.print_exc()


