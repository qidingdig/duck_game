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

## 项目结构

```
duck_game/
├── main.py                 # 主游戏文件（包含所有游戏逻辑）
├── setup.py                # 安装脚本
├── requirements.txt        # Python 依赖包列表
├── README.md               # 项目说明文档
├── assets/                 # 资源文件目录
│   ├── images/            # 图片资源
│   └── sounds/            # 音频资源
├── game/                   # 游戏核心模块
│   ├── __init__.py
│   ├── characters.py      # 角色类
│   ├── game_engine.py     # 游戏引擎
│   └── red_packet.py      # 红包游戏逻辑
├── services/               # 服务模块
│   ├── __init__.py
│   ├── ai_service.py      # AI 服务
│   ├── advanced_code_counter.py  # 代码统计服务（增强版）
│   └── red_packet_service.py     # 红包服务
└── utils/                  # 工具模块
    ├── __init__.py
    └── config.py          # 配置管理
```

## 依赖包

- `pygame >= 2.6.0` - 游戏引擎
- `requests >= 2.31.0` - HTTP 请求（用于检查 Ollama 服务状态）
- `numpy >= 1.24.3` - 数值计算
- `pandas >= 2.0.3` - 数据处理
- `matplotlib >= 3.7.2` - 数据可视化
- `pyttsx3 >= 2.90` - 本地语音播报（可选，但启用“小鸭语音”功能需安装）

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

### 主要文件

- **main.py**: 包含 `DuckGame` 类和游戏主循环，是项目的核心文件
- **setup.py**: 用于首次安装和配置，创建必要目录并安装依赖

### 扩展功能

项目采用模块化设计，可以轻松扩展：

- 在 `game/` 目录添加新的游戏功能
- 在 `services/` 目录添加新的服务
- 在 `utils/` 目录添加工具函数

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
