# 唐老鸭小游戏 (Duck Game)

一个基于 Pygame 的交互式小游戏，集成了红包游戏、AI 对话和代码统计功能。

## 功能特性

- 🎮 **交互式游戏界面**：点击唐老鸭开始对话
- 🧧 **红包游戏**：唐小鸭移动抢红包，统计红包数量和金额
- 🤖 **AI 对话**：基于 Ollama 的智能对话功能
- 📊 **代码统计**：支持多语言代码量统计，包含可视化图表

## 系统要求

- Python 3.7 或更高版本
- Windows / macOS / Linux

## 安装步骤

### 1. 克隆或下载项目

```bash
cd duck_game
```

### 2. 安装依赖

**方式一：使用安装脚本（推荐）**

```bash
python setup.py
```

**方式二：手动安装**

```bash
pip install -r requirements.txt
```

### 3. 配置 AI 功能

如果需要使用 AI 对话功能，需要安装并配置 Ollama：

1. 访问 [Ollama 官网](https://ollama.ai/) 下载并安装
2. 启动 Ollama 服务：
   ```bash
   ollama serve
   ```
3. 下载 AI 模型：
   ```bash
   ollama pull deepseekr1:8b
   ```

> **注意**：如果不配置 Ollama，AI 对话功能将不可用，但红包游戏和代码统计功能仍然可以正常使用。

## 运行游戏

```bash
python main.py
```

## 使用说明

### 启动游戏

运行 `python main.py` 后，游戏窗口会自动打开。

### 开始对话

点击游戏界面中的**唐老鸭**，会弹出对话窗口。

### 可用命令

在对话窗口中输入以下命令：

- **`我要抢红包`** - 启动红包游戏（30秒游戏时间）
- **`我要ai问答`** - 开始 AI 对话
- **`我要统计代码量`** - 打开代码统计配置界面
- **`统计代码: <目录路径>`** - 快速统计指定目录的代码（使用默认设置）

### 代码统计功能

代码统计支持以下特性：

- 支持多种编程语言（Python, Java, C/C++, JavaScript 等）
- 可选择特定语言进行统计
- 统计代码行数、注释行数、空行数
- 支持 Python 和 C/C++ 函数统计
- 生成可视化图表（柱状图、饼图、函数长度直方图）
- 支持导出为 CSV、JSON、XLSX 格式
- 支持语言明细表显示和导出

## 项目结构

```
duck_game/
├── main.py                    # 主入口文件
├── setup.py                   # 安装脚本
├── requirements.txt           # Python 依赖包列表
├── README.md                  # 项目说明文档
├── assets/                    # 资源文件目录
│   ├── images/               # 图片资源
│   └── sounds/               # 音频资源
├── core/                      # 核心系统层
│   ├── __init__.py
│   ├── game_state.py         # 游戏状态管理器（状态机）
│   ├── event_system.py        # 事件系统（观察者模式）
│   ├── render_system.py       # 渲染系统（分层渲染）
│   └── physics_system.py     # 物理系统（碰撞检测、移动）
├── game/                      # 游戏逻辑层
│   ├── __init__.py
│   ├── duck_game.py          # 游戏主类
│   ├── characters.py         # 角色类
│   ├── red_packet.py         # 红包游戏逻辑（旧版，保留兼容）
│   └── minigames/            # 小游戏模块（新）
│       ├── __init__.py
│       ├── base_minigame.py  # 小游戏基类
│       └── red_packet_game/  # 红包游戏模块（已细化）
│           ├── __init__.py
│           ├── game_manager.py      # 游戏管理器
│           ├── red_packet.py        # 红包实体
│           ├── spawner.py           # 红包生成器
│           ├── collision_detector.py  # 碰撞检测
│           ├── movement_controller.py  # 移动控制
│           ├── statistics.py        # 统计收集器
│           └── renderer.py          # 渲染器
├── ui/                        # UI层（已完全模块化）
│   ├── __init__.py
│   ├── tk_root_manager.py      # Tk根窗口管理器
│   ├── queue_processor.py      # UI队列消息处理器
│   ├── message_dialog.py       # 统一消息对话框工具
│   ├── chat_dialog.py          # 唐老鸭聊天窗口与输入处理
│   ├── code_statistics.py      # 代码统计配置面板 + 导出逻辑
│   └── chart_renderer.py       # Matplotlib 图表渲染与布局
├── services/                  # 服务模块
│   ├── __init__.py
│   ├── ai_service.py         # AI 服务
│   ├── advanced_code_counter.py  # 代码统计服务
│   └── duck_behavior_manager.py  # 小鸭行为管理器
└── utils/                     # 工具模块
    ├── __init__.py
    └── config.py             # 配置管理
```

## 架构设计

### 核心系统层 (core/)

提供游戏的基础架构，采用模块化设计：

- **GameStateManager**: 统一管理游戏状态，使用状态机模式
- **EventManager**: 解耦模块间通信，使用观察者模式
- **RenderSystem**: 分层渲染管理，支持多渲染器
- **PhysicsSystem**: 物理计算（碰撞检测、移动控制）

### 游戏逻辑层 (game/)

包含游戏的核心逻辑：

- **DuckGame**: 游戏主类，管理游戏循环和整体流程
- **Characters**: 角色类（唐老鸭、小鸭）
- **CommandProcessor**: 命令处理器，支持命令注册和扩展
  - 可扩展的命令系统
  - 支持模式匹配（字符串和正则表达式）
  - 支持命令优先级和默认处理器
- **Minigames**: 小游戏模块，采用基类设计，易于扩展

### 服务层 (services/)

提供各种业务服务：

- **AIService**: AI对话服务（统一接口，支持OpenAI兼容API和Ollama原生API）
  - 支持OpenAI兼容格式（通过Ollama的/v1端点）
  - 支持Ollama原生格式（/api/generate端点）
  - 自动降级和错误处理
  - 对话历史管理
- **AdvancedCodeCounter**: 代码统计服务
- **DuckBehaviorManager**: 小鸭行为管理

### UI层 (ui/)

UI 层已完全模块化，分为基础设施层和功能组件层：

**基础设施层**：
- `tk_root_manager.py`：统一管理 Tk 根窗口的创建、事件循环、更新频率
- `queue_processor.py`：统一处理 UI 队列消息，支持消息类型注册和批量处理
- `message_dialog.py`：统一的消息框接口，支持未来替换 UI 库

**功能组件层**：
- `chat_dialog.py`：管理唐老鸭聊天窗口、输入事件与线程安全文本更新（通过 UI 队列）
- `code_statistics.py`：封装 Tk 配置窗口、用户选项收集、后台统计线程、CSV/JSON/XLSX 导出、语言明细表构建
- `chart_renderer.py`：统一管理 Matplotlib 的窗口、图表布局、函数直方图和语言明细表渲染

**架构优势**：
- DuckGame 完全脱离 Tkinter 细节，只通过接口交互
- UI 组件可独立测试和替换
- 便于未来替换 UI 库（如 PyQt）
- 符合 SOLID 原则，职责清晰

## 依赖包

- `pygame >= 2.6.0` - 游戏引擎
- `requests >= 2.31.0` - HTTP 请求（用于检查 Ollama 服务状态）
- `numpy >= 1.24.3` - 数值计算
- `pandas >= 2.0.3` - 数据处理
- `matplotlib >= 3.7.2` - 数据可视化
- `openpyxl >= 3.1.0` - Excel文件处理
- `pyttsx3 >= 2.90` - 本地语音播报（可选，但启用"小鸭语音"功能需安装）

## 常见问题

### Q: 游戏启动失败？

A: 请检查：
1. Python 版本是否为 3.7 或更高
2. 是否已安装所有依赖包：`pip install -r requirements.txt`
3. 查看错误信息，根据提示解决问题

### Q: AI 对话功能不可用？

A: 请确保：
1. Ollama 服务正在运行：`ollama serve`
2. 已下载模型：`ollama pull deepseekr1:8b`
3. 检查防火墙是否阻止了 localhost:11434 端口

### Q: 代码统计功能报错？

A: 请检查：
1. 目标目录路径是否正确
2. 是否有读取权限
3. 是否选择了有效的编程语言

## 开发说明

### 重构进度

项目正在进行架构重构，采用更模块化、面向对象的设计：

- ✅ **阶段1完成**: 核心系统模块（GameStateManager, EventManager, RenderSystem, PhysicsSystem）
- ✅ **阶段2完成**: 红包游戏模块细化（RedPacket, Spawner, CollisionDetector, MovementController, Statistics, Renderer, GameManager）
- 🔄 **阶段3进行中**: UI层模块（代码统计配置/图表已独立至 `ui/`，其余 Tk 组件正在迁移）
- 🔄 **阶段4进行中**: 游戏主类重构
- ⏳ **阶段5待进行**: 完整测试和优化

### 扩展功能

项目采用模块化设计，可以轻松扩展：

- 在 `game/minigames/` 目录添加新的小游戏（继承 `BaseMinigame`）
- 在 `services/` 目录添加新的服务
- 在 `core/` 目录扩展核心系统功能
- 在 `ui/` 目录添加新的UI组件

### 添加新小游戏

1. 在 `game/minigames/` 创建新目录
2. 实现 `BaseMinigame` 接口
3. 在 `DuckGame` 中注册新游戏


### 语音播报

小鸭的语音由 `pyttsx3` 提供（离线 TTS）。如需启用，请确保执行：

```bash
pip install pyttsx3
```

如果未安装或初始化失败，语音会自动降级为文本提示。

## 许可证

本项目仅供学习和研究使用。

---

**享受游戏！** 🦆🎮
