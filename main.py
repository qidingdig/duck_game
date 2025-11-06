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
from tkinter import messagebox, filedialog
import threading
import time
import requests
import json
from openai import OpenAI
from queue import Queue
import re

# Windows API用于获取窗口实际大小
try:
    import ctypes
    from ctypes import wintypes
    
    # 设置DPI感知（必须在导入user32之前）
    try:
        # Windows 10/11 推荐的DPI感知设置
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        try:
            # Windows 8.1 及更早版本
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    
    # Windows API函数
    user32 = ctypes.windll.user32
    
    # 定义RECT结构
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long),
                   ("top", ctypes.c_long),
                   ("right", ctypes.c_long),
                   ("bottom", ctypes.c_long)]
    
    # GetWindowRect函数签名
    # HWND在Windows上实际上是无符号整数指针
    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = ctypes.c_bool
    
    # SetWindowPos函数签名 - 用于锁定窗口大小
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_NOREDRAW = 0x0008
    SWP_NOACTIVATE = 0x0010
    SWP_FRAMECHANGED = 0x0020
    SWP_SHOWWINDOW = 0x0040
    SWP_HIDEWINDOW = 0x0080
    SWP_NOCOPYBITS = 0x0100
    SWP_NOOWNERZORDER = 0x0200
    SWP_NOSENDCHANGING = 0x0400
    
    user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos.restype = ctypes.c_bool
    
    def lock_window_size(hwnd, width, height, x, y):
        """使用Windows API锁定窗口大小和位置"""
        try:
            hwnd_int = int(hwnd)
            if hwnd_int == 0:
                return False
            # 使用SetWindowPos锁定窗口大小和位置
            # HWND_TOPMOST = -1, 但这里我们不需要改变Z顺序，所以用0
            # SWP_NOSIZE | SWP_NOMOVE = 只改变Z顺序，但我们要改变大小和位置
            # 实际上我们要设置大小和位置，所以不使用这些标志
            flags = SWP_NOZORDER | SWP_NOACTIVATE
            result = user32.SetWindowPos(hwnd_int, 0, x, y, width, height, flags)
            return bool(result)
        except Exception as e:
            print(f"[DEBUG] lock_window_size异常: {e}")
            return False
    
    def get_window_actual_size(hwnd):
        """使用Windows API获取窗口的实际大小（包括边框和标题栏）"""
        try:
            # 确保hwnd是正确的类型
            if hwnd is None:
                return None, None
            # Tkinter的winfo_id()返回的是整数，可以直接作为HWND使用
            hwnd_int = int(hwnd)
            if hwnd_int == 0:
                return None, None
            
            rect = RECT()
            # 直接使用整数作为HWND（在Windows上，HWND就是整数）
            if user32.GetWindowRect(hwnd_int, ctypes.byref(rect)):
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                return width, height
            # 不打印错误，避免日志刷屏（只在第一次失败时打印）
        except Exception as e:
            # 只在第一次失败时打印，避免日志刷屏
            if not hasattr(get_window_actual_size, '_error_printed'):
                print(f"[DEBUG] get_window_actual_size异常: {e}")
                get_window_actual_size._error_printed = True
        return None, None
    
    # GetClientRect函数签名 - 获取客户区域大小
    user32.GetClientRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = ctypes.c_bool
    
    # DPI相关API
    shcore = None
    try:
        shcore = ctypes.windll.shcore
        # GetDpiForWindow (Windows 10+)
        try:
            shcore.GetDpiForWindow.argtypes = [ctypes.c_void_p]
            shcore.GetDpiForWindow.restype = ctypes.c_uint
        except:
            pass
    except:
        pass
    
    # GetSystemMetrics用于获取窗口边框和标题栏的标准大小
    SM_CXFRAME = 32
    SM_CYFRAME = 33
    SM_CYCAPTION = 4
    
    def get_window_detailed_info(hwnd):
        """获取窗口的详细信息，包括DPI和客户区域大小"""
        try:
            hwnd_int = int(hwnd)
            if hwnd_int == 0:
                return None
            
            info = {}
            
            # 获取窗口矩形（包括边框和标题栏）
            window_rect = RECT()
            if user32.GetWindowRect(hwnd_int, ctypes.byref(window_rect)):
                info['window_width'] = window_rect.right - window_rect.left
                info['window_height'] = window_rect.bottom - window_rect.top
            
            # 获取客户区域矩形（不包括边框和标题栏）
            client_rect = RECT()
            if user32.GetClientRect(hwnd_int, ctypes.byref(client_rect)):
                info['client_width'] = client_rect.right - client_rect.left
                info['client_height'] = client_rect.bottom - client_rect.top
                
                # 计算边框大小
                if 'window_width' in info and 'window_height' in info:
                    border_width = info['window_width'] - info['client_width']
                    border_height = info['window_height'] - info['client_height']
                    info['border_width'] = border_width
                    info['border_height'] = border_height
                    
                    # 如果边框大小为0，尝试使用GetSystemMetrics获取标准边框大小
                    if border_width == 0 and border_height == 0:
                        try:
                            # 获取标准窗口边框和标题栏大小
                            frame_width = user32.GetSystemMetrics(SM_CXFRAME)
                            frame_height = user32.GetSystemMetrics(SM_CYFRAME)
                            caption_height = user32.GetSystemMetrics(SM_CYCAPTION)
                            info['standard_border_width'] = frame_width * 2  # 左右边框
                            info['standard_border_height'] = frame_height * 2 + caption_height  # 上下边框+标题栏
                            info['calculated_client_width'] = info['window_width'] - (frame_width * 2)
                            info['calculated_client_height'] = info['window_height'] - (frame_height * 2 + caption_height)
                        except:
                            pass
            
            # 获取DPI
            if shcore:
                try:
                    dpi = shcore.GetDpiForWindow(hwnd_int)
                    info['dpi'] = dpi
                    info['dpi_scale'] = dpi / 96.0  # 96是标准DPI
                except:
                    pass
            
            return info
        except Exception as e:
            if not hasattr(get_window_detailed_info, '_error_printed'):
                print(f"[DEBUG] get_window_detailed_info异常: {e}")
                get_window_detailed_info._error_printed = True
        return None
    
    WINDOWS_API_AVAILABLE = True
except:
    WINDOWS_API_AVAILABLE = False
    def get_window_actual_size(hwnd):
        return None, None

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
        # 启用窗口调整大小功能，允许最大最小化
        self.screen = pygame.display.set_mode((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.RESIZABLE)
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
        """显示代码统计配置对话框"""
        # 确保在主线程中创建对话框
        if not hasattr(self, '_root') or self._root is None:
            print("错误: Tkinter root窗口未初始化")
            return
        
        try:
            # 创建配置对话框窗口
            config_window = tk.Toplevel(self._root)
            config_window.title("代码统计配置")
            config_window.geometry("700x650")
            config_window.minsize(400, 400)  # 设置最小大小，但允许拖动和缩放
            # 允许窗口拖动和缩放，通过智能事件处理避免GIL问题
            config_window.focus_set()
            
            # 确保after()事件循环正在运行
            if not hasattr(self, '_tk_event_loop_running') or not self._tk_event_loop_running:
                self._start_tk_event_loop()
            
            # 保存配置窗口引用，以便清理
            self._config_window = config_window
            
            # 保存配置的变量（保存在实例变量中，避免被垃圾回收）
            self._code_counting_config = {
                'target_dir': os.path.dirname(os.path.abspath(__file__)),
                'selected_languages': set(),
                'include_blank': tk.BooleanVar(self._root, value=True),
                'include_comment': tk.BooleanVar(self._root, value=True),
                'include_function_stats': tk.BooleanVar(self._root, value=True),
                'include_c_function_stats': tk.BooleanVar(self._root, value=False)
            }
            
            # 创建主容器（不使用滚动框架，直接使用普通Frame）
            main_frame = tk.Frame(config_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 1. 目录选择区域
            dir_frame = tk.LabelFrame(main_frame, text="选择统计目录", font=("Arial", 11, "bold"), padx=10, pady=10)
            dir_frame.pack(fill=tk.X, padx=5, pady=5)
            
            dir_input_frame = tk.Frame(dir_frame)
            dir_input_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self._target_dir_var = tk.StringVar(self._root, value=self._code_counting_config['target_dir'])
            dir_entry = tk.Entry(dir_input_frame, textvariable=self._target_dir_var, font=("Arial", 10), width=50)
            dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            
            def browse_directory():
                directory = filedialog.askdirectory(title="选择要统计的目录", initialdir=self._target_dir_var.get())
                if directory:
                    self._target_dir_var.set(directory)
                    self._code_counting_config['target_dir'] = directory
            
            browse_btn = tk.Button(dir_input_frame, text="浏览...", command=browse_directory, font=("Arial", 10), width=10)
            browse_btn.pack(side=tk.RIGHT)
            
            # 2. 语言选择区域（不使用expand=True，避免挤压按钮区域）
            lang_frame = tk.LabelFrame(main_frame, text="选择要统计的语言（不选择则统计所有语言）", font=("Arial", 11, "bold"), padx=10, pady=10)
            lang_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
            
            # 语言列表（从AdvancedCodeCounter获取）
            all_languages = sorted(set(self.code_counter.EXT_TO_LANGUAGE.values()))
            self._language_vars = {}
            
            # 创建滚动框架用于语言选择（固定高度，避免占据所有空间）
            lang_canvas = tk.Canvas(lang_frame, height=180)
            lang_scrollbar = tk.Scrollbar(lang_frame, orient="vertical", command=lang_canvas.yview)
            lang_scrollable_frame = tk.Frame(lang_canvas)
            
            # 安全地更新滚动区域（使用装饰器避免重复调用）
            _last_update_time = [0]
            import time as time_module
            
            def update_scrollregion(event=None):
                try:
                    # 限制更新频率，避免频繁调用导致GIL问题
                    current_time = time_module.time()
                    if current_time - _last_update_time[0] < 0.1:  # 最多每100ms更新一次
                        return
                    _last_update_time[0] = current_time
                    
                    lang_canvas.configure(scrollregion=lang_canvas.bbox("all"))
                except Exception:
                    pass  # 忽略更新时的错误
            
            lang_scrollable_frame.bind("<Configure>", update_scrollregion)
            
            # 先创建窗口，再绑定事件
            lang_canvas_window_id = lang_canvas.create_window((0, 0), window=lang_scrollable_frame, anchor="nw")
            lang_canvas.configure(yscrollcommand=lang_scrollbar.set)
            
            # Canvas窗口大小改变时也更新滚动区域（限制频率）
            def on_canvas_configure(event):
                try:
                    # 更新Canvas窗口的宽度，使其与Canvas同宽
                    canvas_width = event.width
                    lang_canvas.itemconfig(lang_canvas_window_id, width=canvas_width)
                    # 延迟更新滚动区域，避免频繁调用
                    update_scrollregion()
                except Exception:
                    pass
            
            lang_canvas.bind('<Configure>', on_canvas_configure)
            
            # 不绑定窗口的Configure事件，避免窗口缩放时的GIL问题
            # Canvas的滚动区域更新将通过Canvas自己的Configure事件处理
            
            # 创建语言复选框（3列布局）
            cols = 3
            for idx, lang in enumerate(all_languages):
                var = tk.BooleanVar(self._root, value=False)
                self._language_vars[lang] = var
                row = idx // cols
                col = idx % cols
                cb = tk.Checkbutton(lang_scrollable_frame, text=lang, variable=var, font=("Arial", 9))
                cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            
            lang_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            lang_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 全选/全不选按钮 - 完全参考浏览按钮的布局方式
            # 注意：lang_btn_frame不使用fill=tk.X，避免影响按钮大小
            lang_btn_frame = tk.Frame(lang_frame)
            lang_btn_frame.pack(padx=5, pady=5)
            
            def select_all_languages():
                for var in self._language_vars.values():
                    var.set(True)
            
            def deselect_all_languages():
                for var in self._language_vars.values():
                    var.set(False)
            
            # 实现切换功能：点击一次全选，再点击一次取消全选
            def toggle_select_all(event=None):
                # 检查是否所有语言都已选中
                all_selected = all(var.get() for var in self._language_vars.values())
                if all_selected:
                    # 如果全部选中，则取消全选
                    deselect_all_languages()
                else:
                    # 否则全选
                    select_all_languages()
            
            # 全选按钮 - 完全参考浏览按钮的设置：font=("Arial", 10), width=10，pack时没有额外参数
            select_all_btn = tk.Button(lang_btn_frame, text="全选", command=toggle_select_all, 
                                      font=("Arial", 10), width=10)
            select_all_btn.pack(side=tk.LEFT)
            
            # 全不选按钮 - 同样参考浏览按钮的设置
            tk.Button(lang_btn_frame, text="全不选", command=deselect_all_languages, 
                     font=("Arial", 10), width=10).pack(side=tk.LEFT)
            
            # 3. 统计选项区域
            options_frame = tk.LabelFrame(main_frame, text="统计选项", font=("Arial", 11, "bold"), padx=10, pady=10)
            options_frame.pack(fill=tk.X, padx=5, pady=5)
            
            tk.Checkbutton(options_frame, text="统计空行数", variable=self._code_counting_config['include_blank'], 
                          font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
            tk.Checkbutton(options_frame, text="统计注释行数", variable=self._code_counting_config['include_comment'], 
                          font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
            tk.Checkbutton(options_frame, text="统计Python函数信息（仅对Python文件）", 
                          variable=self._code_counting_config['include_function_stats'], 
                          font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
            tk.Checkbutton(options_frame, text="统计C/C++函数信息（仅对C/C++文件）", 
                          variable=self._code_counting_config['include_c_function_stats'], 
                          font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
            
            # 4. 按钮区域（固定在底部）
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
            
            def start_counting():
                # 收集配置
                target_dir = self._target_dir_var.get().strip()
                if not target_dir or not os.path.exists(target_dir):
                    messagebox.showerror("错误", "请选择有效的目录路径！")
                    return
                
                # 收集选中的语言
                selected_languages = {lang for lang, var in self._language_vars.items() if var.get()}
                
                # 收集统计选项
                include_blank = self._code_counting_config['include_blank'].get()
                include_comment = self._code_counting_config['include_comment'].get()
                include_function_stats = self._code_counting_config['include_function_stats'].get()
                include_c_function_stats = self._code_counting_config['include_c_function_stats'].get()
                
                # 不关闭配置窗口，保持打开以便多次统计
                # 显示开始统计信息
                self._update_text_display(f"唐老鸭: 好的！开始统计代码量！\n目录: {target_dir}\n")
                if selected_languages:
                    lang_list = ", ".join(sorted(selected_languages))
                    self._update_text_display(f"统计语言: {lang_list}\n\n")
                
                # 启动代码统计（在后台线程）
                threading.Thread(
                    target=self.start_code_counting,
                    args=(target_dir, selected_languages, include_blank, include_comment, include_function_stats, include_c_function_stats),
                    daemon=True
                ).start()
            
            def cleanup_config_dialog():
                """清理配置对话框的Tkinter变量"""
                try:
                    # 清理所有变量引用
                    if hasattr(self, '_target_dir_var'):
                        self._target_dir_var = None
                    if hasattr(self, '_language_vars'):
                        self._language_vars.clear()
                    if hasattr(self, '_code_counting_config'):
                        # 清理 BooleanVar 引用
                        for key in list(self._code_counting_config.keys()):
                            if isinstance(self._code_counting_config[key], (tk.BooleanVar, tk.StringVar)):
                                self._code_counting_config[key] = None
                            else:
                                del self._code_counting_config[key]
                        self._code_counting_config = None
                    if hasattr(self, '_config_window'):
                        self._config_window = None
                except Exception:
                    pass  # 忽略清理时的错误
                config_window.destroy()
            
            # 按钮完全参考浏览按钮的样式，确保高度一致
            # 浏览按钮：font=("Arial", 10), width=10，pack时没有pady
            # 为了确保高度一致，我们也移除pack中的pady，只保留padx用于水平间距
            start_btn = tk.Button(button_frame, text="开始统计", command=start_counting, 
                                 font=("Arial", 10), width=10, bg="#4CAF50", fg="white")
            start_btn.pack(side=tk.LEFT, padx=5)
            
            cancel_btn = tk.Button(button_frame, text="取消", command=cleanup_config_dialog, 
                                   font=("Arial", 10), width=10)
            cancel_btn.pack(side=tk.LEFT, padx=5)
            
            # 添加一个空的框架来填充剩余空间，防止按钮被压缩
            tk.Frame(button_frame).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 绑定窗口关闭事件
            config_window.protocol("WM_DELETE_WINDOW", cleanup_config_dialog)
            
            # 更新窗口（只使用update_idletasks，避免GIL问题）
            config_window.update_idletasks()
            config_window.focus_set()
            
        except Exception as e:
            print(f"创建代码统计配置对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"创建配置对话框失败: {e}")
    
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
            self._update_text_display("唐老鸭: 红包游戏开始！汤小鸭们开始移动！\n")
            
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
        
        # 显示统计结果（确保statistics存在）
        if hasattr(self, 'statistics') and self.statistics:
            result = f"红包游戏统计:\n"
            result += f"总红包数: {self.statistics['total_count']}\n"
            result += f"总金额: ¥{self.statistics['total_amount']:.2f}\n"
            result += f"小红包: {self.statistics['type_counts'][0]}个, ¥{self.statistics['type_amounts'][0]:.2f}\n"
            result += f"中红包: {self.statistics['type_counts'][1]}个, ¥{self.statistics['type_amounts'][1]:.2f}\n"
            result += f"大红包: {self.statistics['type_counts'][2]}个, ¥{self.statistics['type_amounts'][2]:.2f}\n"
            
            # 使用线程安全的方式显示结果
            self._update_text_display(f"唐老鸭: 红包游戏结束！\n{result}\n")
        else:
            self._update_text_display("唐老鸭: 红包游戏结束！\n")
        
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
    
    def start_code_counting(self, target_dir=None, selected_languages=None, include_blank=True, include_comment=True, include_function_stats=True, include_c_function_stats=False):
        """启动代码统计（可能在后台线程中运行）
        
        Args:
            target_dir: 要统计的目录路径
            selected_languages: 选中的语言集合，如果为None或空则统计所有语言
            include_blank: 是否在报告中包含空行数
            include_comment: 是否在报告中包含注释行数
            include_function_stats: 是否统计Python函数信息
            include_c_function_stats: 是否统计C/C++函数信息
        """
        try:
            # 显示开始统计信息（使用线程安全的方式）
            self._update_text_display("唐老鸭: 正在统计代码量，请稍候...\n")        
            
            # 确定要统计的目录
            if target_dir is None:
                target_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 根据选择的语言构建include列表
            include_patterns = []
            if selected_languages and len(selected_languages) > 0:
                # 根据语言找到对应的扩展名
                ext_to_lang = self.code_counter.EXT_TO_LANGUAGE
                lang_to_exts = {}
                for ext, lang in ext_to_lang.items():
                    if lang not in lang_to_exts:
                        lang_to_exts[lang] = []
                    lang_to_exts[lang].append(ext)
                
                # 构建include模式
                for lang in selected_languages:
                    if lang in lang_to_exts:
                        for ext in lang_to_exts[lang]:
                            include_patterns.append(f"**/*{ext}")
            
            # 统计代码量
            result = self.code_counter.count_code_by_language(
                target_dir, 
                include=include_patterns if include_patterns else None
            )
            summary = result["summary"]
            by_language = result["by_language"]
            elapsed_time = result["elapsed_time"]
            
            # 过滤语言（如果指定了语言）
            if selected_languages and len(selected_languages) > 0:
                filtered_by_language = {lang: stat for lang, stat in by_language.items() if lang in selected_languages}
                by_language = filtered_by_language
            
            # 生成统计报告文本
            report_text = f"代码统计报告:\n"
            report_text += f"{'='*50}\n"
            report_text += f"统计目录: {target_dir}\n"
            report_text += f"总文件数: {summary.files}\n"
            report_text += f"总行数: {summary.total}\n"
            report_text += f"代码行数: {summary.code}\n"
            if include_comment:
                report_text += f"注释行数: {summary.comment}\n"
            if include_blank:
                report_text += f"空行数: {summary.blank}\n"
            report_text += f"耗时: {elapsed_time:.3f} 秒\n\n"
            
            if by_language:
                report_text += f"按语言统计:\n"
                report_text += f"{'语言':<20} {'文件数':<10} {'代码行数':<15}"
                if include_comment:
                    report_text += f" {'注释行数':<15}"
                if include_blank:
                    report_text += f" {'空行数':<15}"
                report_text += "\n"
                report_text += "-" * 80 + "\n"
                
                # 按代码行数排序
                sorted_langs = sorted(by_language.items(), key=lambda x: -x[1].code)
                for lang, stat in sorted_langs:  # 显示所有选中的语言
                    report_text += f"{lang:<20} {stat.files:<10} {stat.code:<15}"
                    if include_comment:
                        report_text += f" {stat.comment:<15}"
                    if include_blank:
                        report_text += f" {stat.blank:<15}"
                    report_text += "\n"
            else:
                report_text += "未找到匹配的代码文件。\n"
            
            # 统计Python函数（如果启用）
            function_stats = None
            if include_function_stats:
                function_stats = self.code_counter.count_python_functions(target_dir)
                
                if function_stats.total_functions > 0:
                    report_text += f"\nPython函数统计:\n"
                    report_text += f"总函数数: {function_stats.total_functions}\n"
                    report_text += f"平均长度: {function_stats.mean_length:.2f} 行\n"
                    report_text += f"中位数长度: {function_stats.median_length:.2f} 行\n"
                    report_text += f"最小长度: {function_stats.min_length} 行\n"
                    report_text += f"最大长度: {function_stats.max_length} 行\n"
            
            # 统计C/C++函数（如果启用）
            c_function_stats = None
            if include_c_function_stats:
                c_function_stats = self.code_counter.count_c_functions(target_dir)
                
                if c_function_stats.total_functions > 0:
                    report_text += f"\nC/C++函数统计:\n"
                    report_text += f"总函数数: {c_function_stats.total_functions}\n"
                    report_text += f"平均长度: {c_function_stats.mean_length:.2f} 行\n"
                    report_text += f"中位数长度: {c_function_stats.median_length:.2f} 行\n"
                    report_text += f"最小长度: {c_function_stats.min_length} 行\n"
                    report_text += f"最大长度: {c_function_stats.max_length} 行\n"
            
            # 显示文本结果（使用线程安全的方式）
            self._update_text_display(f"唐老鸭: 代码统计完成！\n{report_text}\n")
            
            # 打开图形化窗口（需要在主线程中调用）
            # 主线程显示图表（通过队列）
            self._enqueue_show_charts(result, function_stats, c_function_stats)
            
        except Exception as e:
            print(f"代码统计错误: {e}")
            import traceback
            traceback.print_exc()
            # 使用线程安全的方式显示错误
            self._update_text_display(f"唐老鸭: 抱歉，代码统计出现了问题: {str(e)}\n\n")
    
    def show_code_statistics_charts(self, code_result, function_stats=None, c_function_stats=None):
        """显示代码统计图表 - 使用matplotlib独立窗口"""
        try:
            import matplotlib
            matplotlib.use('TkAgg')  # 使用TkAgg后端
            try:
                matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
                matplotlib.rcParams['axes.unicode_minus'] = False
            except Exception:
                pass
            import matplotlib.pyplot as plt
            
            # 创建代码统计图表窗口
            self._create_code_stat_chart(code_result)
            
            # 创建函数统计图表窗口（Python）- 始终显示，即使没有数据也显示0
            self._create_function_stat_chart(function_stats, "Python")
            
            # 创建函数统计图表窗口（C/C++）- 始终显示，即使没有数据也显示0
            self._create_function_stat_chart(c_function_stats, "C/C++")
            
        except ImportError:
            messagebox.showwarning("警告", "需要安装matplotlib才能显示图表:\npip install matplotlib")
        except Exception as e:
            print(f"显示图表错误: {e}")
            messagebox.showerror("错误", f"显示图表时出错: {str(e)}")

    def _create_code_stat_chart(self, code_result):
        """创建代码统计图表 - matplotlib独立窗口"""
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

    def _create_function_stat_chart(self, function_stats, lang_name="Python"):
        """创建函数统计图表 - matplotlib独立窗口"""
        try:
            import matplotlib.pyplot as plt

            lengths = []
            summary_vals = {
                '均值': 0,
                '中位数': 0,
                '最小值': 0,
                '最大值': 0,
            }

            # 解析数据
            if function_stats:
                try:
                    if hasattr(function_stats, 'functions'):
                        funcs = getattr(function_stats, 'functions')
                        for f in funcs:
                            if hasattr(f, 'line_count'):
                                lengths.append(int(getattr(f, 'line_count')))
                            elif hasattr(f, 'length'):
                                lengths.append(int(getattr(f, 'length')))
                    elif isinstance(function_stats, dict) and 'functions' in function_stats:
                        for f in function_stats['functions']:
                            if isinstance(f, dict):
                                if 'line_count' in f:
                                    lengths.append(int(f['line_count']))
                                elif 'length' in f:
                                    lengths.append(int(f['length']))
                            elif hasattr(f, 'line_count'):
                                lengths.append(int(f.line_count))
                            elif hasattr(f, 'length'):
                                lengths.append(int(f.length))

                    # 解析汇总
                    if hasattr(function_stats, 'mean_length'):
                        summary_vals['均值'] = getattr(function_stats, 'mean_length', 0) or 0
                        summary_vals['中位数'] = getattr(function_stats, 'median_length', 0) or 0
                        summary_vals['最小值'] = getattr(function_stats, 'min_length', 0) or 0
                        summary_vals['最大值'] = getattr(function_stats, 'max_length', 0) or 0
                    elif isinstance(function_stats, dict) and 'summary' in function_stats:
                        s = function_stats['summary']
                        summary_vals['均值'] = s.get('mean', 0) or 0
                        summary_vals['中位数'] = s.get('median', 0) or 0
                        summary_vals['最小值'] = s.get('min', 0) or 0
                        summary_vals['最大值'] = s.get('max', 0) or 0
                except Exception:
                    pass

            # 创建独立的matplotlib窗口
            fig = plt.figure(figsize=(10, 6))
            fig.canvas.manager.set_window_title(f'{lang_name}函数统计图表')
            ax = fig.add_subplot(111)

            if lengths:
                # 直方图
                ax.hist(lengths, bins=min(50, max(5, len(set(lengths)))), color="#00C853", edgecolor='black')
                ax.set_title(f"{lang_name} 函数长度直方图", fontsize=12)
                ax.set_xlabel("行数", fontsize=10)
                ax.set_ylabel("函数个数", fontsize=10)
                ax.tick_params(labelsize=9)
                
                # 添加统计线（垂直参考线，不在图例中显示，因为右上角已有完整统计信息）
                if summary_vals['均值'] > 0:
                    ax.axvline(summary_vals['均值'], color='red', linestyle='--', linewidth=2, alpha=0.7)
                if summary_vals['中位数'] > 0:
                    ax.axvline(summary_vals['中位数'], color='green', linestyle='--', linewidth=2, alpha=0.7)
            else:
                # 如果没有数据，显示提示信息
                ax.text(0.5, 0.5, f"没有找到{lang_name}函数统计数据", 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title(f"{lang_name} 函数长度统计", fontsize=12)
            
            # 在右上角统一显示所有统计信息（格式统一）
            text_y = 0.95  # 距离顶部5%
            text_x = 0.98  # 距离右侧2%
            stats_text = (f"均值: {summary_vals['均值']:.1f}\n"
                         f"中位数: {summary_vals['中位数']:.1f}\n"
                         f"最小值: {summary_vals['最小值']}\n"
                         f"最大值: {summary_vals['最大值']}")
            ax.text(text_x, text_y, stats_text, 
                   transform=ax.transAxes,
                   fontsize=10,
                   verticalalignment='top',
                   horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            plt.show(block=False)  # 非阻塞显示

        except Exception as e:
            print(f"创建函数统计图表错误: {e}")
            import traceback
            traceback.print_exc()

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

    def _enqueue_show_charts(self, code_result, function_stats=None, c_function_stats=None):
        """将显示图表的请求放入队列，由主线程处理。"""
        try:
            self._ui_queue.put(("show_charts", code_result, function_stats, c_function_stats), block=False)
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
                    self.show_code_statistics_charts(code_result, function_stats, c_function_stats)
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
    
    def update(self):
        """更新游戏状态"""
        # 更新红包游戏状态（如果有）
        if hasattr(self, 'red_packet_game_active') and self.red_packet_game_active:
            # 更新红包位置
            if hasattr(self, 'red_packets') and self.red_packets:
                self.update_red_packets()
            
            # 更新汤小鸭位置
            if hasattr(self, 'duckling_moving') and self.duckling_moving:
                self.update_duckling_positions()
            
            # 生成红包（每30帧生成一个）
            if hasattr(self, 'red_packet_timer'):
                self.red_packet_timer += 1
                if self.red_packet_timer >= self.red_packet_spawn_interval:
                    self.spawn_red_packet()
                    self.red_packet_timer = 0
            
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
