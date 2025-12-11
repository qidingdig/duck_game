# 唐老鸭小游戏 (Duck Game)

一个基于 Pygame 的交互式小游戏，集成了红包游戏、AI 对话和代码统计功能。

## 功能特性

- 🎮 **交互式游戏界面**：点击唐老鸭开始对话
- 🧧 **红包游戏**：唐小鸭移动抢红包，统计红包数量和金额
- 🤖 **AI 对话**：基于 Ollama 的智能对话功能
- 📊 **代码统计**：支持多语言代码量统计，包含可视化图表
- 🗒️ **唐老鸭点名**：支持全点/抽点、多种策略、假条校验与迟到补签

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
- **`我要点名` / `开始点名`** - 打开唐老鸭点名调度窗口

### 代码统计功能

代码统计支持以下特性：

- 支持多种编程语言（Python, Java, C/C++, JavaScript 等）
- 可选择特定语言进行统计
- 统计代码行数、注释行数、空行数
- 支持 Python 和 C/C++ 函数统计
- 生成可视化图表（柱状图、饼图、函数长度直方图）
- 支持导出为 CSV、JSON、XLSX 格式
- 支持语言明细表显示和导出

### 唐老鸭点名

1. 在对话框中输入 `我要点名` / `开始点名`。
2. 在同一窗口中配置点名方式（全点/抽点）、抽点人数、策略（随机 / 旷课最多 / 点到最少）。
3. 开始后窗口会依次展示学生信息并语音播报，提供“到 / 请假 / 旷课 / 迟到”按钮。
4. “请假”仅在该学生已提交本节课假条的情况下生效。
5. 若学生在 10 分钟内从旷课补到，可通过“迟到”按钮输入学号，将对应记录从“旷课”改为“迟到”。
6. 所有点名结果会自动写入数据库，可通过命令扩展或服务层接口做汇总。

## 项目结构

```
duck_game/
├── main.py                    # 主入口文件
├── setup.py                   # 安装脚本
├── requirements.txt           # Python 依赖包列表
├── README.md                  # 项目说明文档
├── .gitignore                 # Git忽略文件配置
├── core/                      # 核心系统层
│   ├── __init__.py
│   ├── game_state.py         # 游戏状态管理器（状态机）
│   ├── event_system.py        # 事件系统（观察者模式）
│   ├── physics_system.py     # 物理系统
│   └── render_system.py      # 渲染系统
├── game/                      # 游戏逻辑层
│   ├── __init__.py
│   ├── duck_game.py          # 游戏主类
│   ├── characters.py         # 角色类（唐老鸭、小鸭）
│   ├── command_processor.py  # 命令处理器
│   ├── game_loop.py          # 游戏循环
│   ├── render_manager.py     # 渲染管理器
│   ├── roll_call_manager.py  # 点名流程管理器
│   └── minigames/            # 小游戏模块
│       ├── __init__.py
│       ├── base_minigame.py  # 小游戏基类
│       └── red_packet_game/  # 红包游戏模块
│           ├── __init__.py
│           ├── game_manager.py
│           ├── red_packet.py
│           ├── collision_detector.py
│           ├── movement_controller.py
│           ├── renderer.py
│           ├── spawner.py
│           └── statistics.py
├── ui/                        # UI层
│   ├── __init__.py
│   ├── tk_root_manager.py      # Tk根窗口管理器
│   ├── queue_processor.py      # UI队列消息处理器
│   ├── message_dialog.py       # 统一消息对话框工具
│   ├── chat_dialog.py          # 唐老鸭聊天窗口
│   ├── code_statistics.py      # 代码统计配置窗口
│   ├── charts/                 # 图表模块（策略模式）
│   │   ├── __init__.py
│   │   ├── chart_renderer.py       # 图表渲染器
│   │   ├── chart_types.py          # 图表类型定义（柱状图、饼图等）
│   │   ├── chart_layout.py         # 图表布局策略
│   │   └── chart_data_extractor.py # 图表数据提取器
│   └── roll_call/              # 点名UI模块
│       ├── __init__.py
│       ├── roll_call_window.py     # 点名配置与执行窗口
│       └── roll_call_records_window.py  # 点名记录查看窗口
├── services/                  # 服务层
│   ├── __init__.py
│   ├── ai_service.py          # AI对话服务
│   ├── roll_call_service.py   # 点名服务（SQLite数据库）
│   ├── duck_behavior_manager.py  # 小鸭行为管理器
│   └── code_statistics/       # 代码统计模块
│       ├── __init__.py
│       ├── base.py            # 代码统计基类（公共功能）
│       ├── advanced_counter.py # 增强统计服务（继承基类）
│       ├── statistics_service.py  # 统计业务逻辑服务
│       ├── report_formatter.py # 报告格式化器
│       ├── result_exporter.py  # 结果导出管理器
│       └── exporters/          # 导出器模块（策略模式）
│           ├── __init__.py
│           ├── base_exporter.py  # 导出器基类
│           ├── csv_exporter.py    # CSV导出器
│           ├── json_exporter.py    # JSON导出器
│           └── xlsx_exporter.py   # XLSX导出器
├── models/                    # 数据模型层
│   ├── __init__.py
│   └── code_statistics.py     # 代码统计数据模型（统一dataclass）
├── data/                      # 数据访问层
│   ├── __init__.py
│   ├── database_interface.py  # 数据库接口抽象
│   ├── sqlite_database.py      # SQLite数据库实现
│   ├── models.py               # 数据模型（Student, RollCall等）
│   ├── repositories.py         # 数据仓库模式实现
│   └── database_migration.py  # 数据库迁移管理
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── logger.py              # 统一日志系统
│   └── exceptions.py          # 异常处理工具
├── samples/                   # 示例文件
│   ├── students_sample.csv    # 学生名单CSV示例
│   ├── students_sample.json   # 学生名单JSON示例
│   └── students_sample.xlsx   # 学生名单Excel示例
├── tools/                     # 工具脚本
│   ├── __init__.py
│   └── db_manager.py          # 数据库管理工具
└── assets/                    # 资源文件
    ├── images/                # 图片资源
    └── sounds/                # 音频资源
```

## 架构设计

### 核心系统层 (core/)

提供游戏的基础架构，采用模块化设计：

- **GameStateManager**: 统一管理游戏状态，使用状态机模式
- **EventManager**: 解耦模块间通信，使用观察者模式
- **RenderSystem**: 渲染系统，管理渲染层和渲染顺序
- **CollisionDetector**: 碰撞检测器
- **MovementController**: 运动控制器

### 游戏逻辑层 (game/)

包含游戏的核心逻辑：

- **DuckGame**: 游戏主类，管理游戏循环和整体流程
- **Characters**: 角色类（唐老鸭、小鸭）
  - `Character`: 角色基类
  - `DonaldDuck`: 唐老鸭角色
  - `Duckling`: 小鸭角色
- **CommandProcessor**: 命令处理器，支持命令注册和扩展
  - 可扩展的命令系统
  - 支持模式匹配（字符串和正则表达式）
  - 支持命令优先级和默认处理器
  - `CommandHandler`: 命令处理器接口
  - `PatternCommandHandler`: 模式匹配命令处理器
- **GameLoop**: 游戏循环管理器
- **RenderManager**: 渲染管理器
- **RollCallManager**: 点名流程管理器
  - 管理点名配置、学生名单与状态流转
  - 与 RollCallService / RollCallWindow 协同
- **Minigames**: 小游戏模块，采用基类设计，易于扩展
  - `BaseMinigame`: 小游戏基类
  - `red_packet_game/`: 红包游戏模块

### 服务层 (services/)

提供各种业务服务：

- **AIService**: AI对话服务（统一接口，支持OpenAI兼容API和Ollama原生API）
  - 支持OpenAI兼容格式（通过Ollama的/v1端点）
  - 支持Ollama原生格式（/api/generate端点）
  - 自动降级和错误处理
  - 对话历史管理
- **CodeStatistics模块**（模块化设计）:
  - `base.py`: 公共基类（`CodeCounterBase`），包含文件遍历、行分类等公共功能
  - `advanced_counter.py`: 增强统计服务（`AdvancedCodeCounter`），继承基类，提供语言统计、函数统计等功能
  - `statistics_service.py`: 统计业务逻辑服务（`CodeStatisticsService`），协调统计执行和报告格式化
  - `report_formatter.py`: 报告格式化器（`ReportFormatter`），负责文本报告格式化
  - `result_exporter.py`: 结果导出管理器（`ResultExporter`），使用策略模式管理多种导出格式
  - `exporters/`: 导出器子模块（策略模式）
    - `base_exporter.py`: 导出器基类
    - `csv_exporter.py`: CSV导出器
    - `json_exporter.py`: JSON导出器
    - `xlsx_exporter.py`: XLSX导出器
- **RollCallService**: 点名服务
  - SQLite 数据存储（Repository模式）
  - 学生/假条/点名记录管理
  - 支持学生导入（CSV、Excel、JSON格式）
  - 支持迟到补签的时间校验（可配置时间限制）
  - 历史记录数据完整性保护（学生姓名快照）
- **DuckBehaviorManager**: 小鸭行为管理器
  - 行为策略（跳跃、旋转、飞行等）
  - 语音策略（本地TTS播报）
  - 事件触发机制

### UI层 (ui/)

UI 层模块化，分为基础设施层和功能组件层：

**基础设施层**：
- `tk_root_manager.py`：统一管理 Tk 根窗口的创建、事件循环、更新频率
- `queue_processor.py`：统一处理 UI 队列消息，支持消息类型注册和批量处理
- `message_dialog.py`：统一的消息框接口，支持未来替换 UI 库

**功能组件层**：
- `chat_dialog.py`：管理唐老鸭聊天窗口、输入事件与线程安全文本更新（通过 UI 队列）
- `code_statistics.py`：代码统计配置窗口，协调统计服务和导出器
- `roll_call/`：点名UI模块
  - `roll_call_window.py`：点名配置与执行窗口，支持状态录入与迟到补签
  - `roll_call_records_window.py`：点名记录查看窗口，支持记录查看、导出和删除
- `charts/`：图表模块（策略模式）
  - `chart_renderer.py`：图表渲染器，使用策略模式管理图表类型和布局
  - `chart_types.py`：图表类型定义（柱状图、饼图、函数统计图等），易于扩展新图表类型
  - `chart_layout.py`：图表布局策略（默认布局、紧凑布局等），易于扩展新布局
  - `chart_data_extractor.py`：图表数据提取器，从统计结果中提取图表所需数据

**架构优势**：
- DuckGame 完全脱离 Tkinter 细节，只通过接口交互
- UI 组件可独立测试和替换
- 便于未来替换 UI 库（如 PyQt）
- 符合 SOLID 原则，职责清晰

### 数据访问层 (data/)

采用Repository模式和数据库抽象层设计：

- **DatabaseInterface**: 数据库接口抽象，定义统一的数据库操作接口
- **SQLiteDatabase**: SQLite数据库实现，提供事务支持和连接管理
- **Models** (`data/models.py`): 数据模型定义
  - `Student`: 学生模型（学号、姓名、昵称、照片路径、统计信息）
  - `StudentLeave`: 请假记录模型
  - `RollCall`: 点名会话模型
  - `RollCallRecord`: 点名记录模型（包含学生姓名快照，保证历史数据完整性）
- **Repository模式**: 数据访问层采用Repository模式，实现数据访问与业务逻辑分离
  - `StudentRepository` / `SQLiteStudentRepository`: 学生数据访问
  - `StudentLeaveRepository` / `SQLiteStudentLeaveRepository`: 请假记录数据访问
  - `RollCallRepository` / `SQLiteRollCallRepository`: 点名会话数据访问
  - `RollCallRecordRepository` / `SQLiteRollCallRecordRepository`: 点名记录数据访问
- **DatabaseMigration**: 数据库迁移管理
  - 支持版本升级
  - 自动执行迁移脚本
  - 保证数据迁移的安全性

### 数据模型层 (models/)

- **CodeStatistics模型** (`models/code_statistics.py`): 代码统计数据模型
  - 使用dataclass定义统一的数据结构
  - 包含文件统计、函数统计、汇总信息等

### 工具模块 (utils/)

提供通用工具和基础设施：

- **Config** (`utils/config.py`): 配置管理
  - 集中管理游戏配置、窗口大小、点名配置等
  - 支持业务常量配置（如状态映射、列名映射等）
- **Logger** (`utils/logger.py`): 统一日志系统
  - 支持控制台和文件输出
  - 统一的日志格式和级别管理
- **Exceptions** (`utils/exceptions.py`): 异常处理工具
  - 提供异常处理装饰器和工具函数

### 工具脚本 (tools/)

提供数据库管理和辅助工具：

- **DatabaseManager** (`tools/db_manager.py`): 数据库管理工具
  - 提供便捷的CRUD操作接口
  - 支持命令行和编程两种使用方式

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

### 扩展功能

项目采用模块化设计，可以轻松扩展：

- **添加新小游戏**：在 `game/minigames/` 目录创建新模块（继承 `BaseMinigame`）
- **添加新服务**：在 `services/` 目录添加新的业务服务
- **添加新图表类型**：
  1. 在 `ui/charts/chart_types.py` 中创建新图表类（继承 `ChartType`）
  2. 在 `ui/charts/chart_renderer.py` 中注册新图表类型
  3. 在 `ui/charts/chart_layout.py` 中添加新图表的布局配置
- **添加新统计指标**：
  1. 在 `services/code_statistics/advanced_counter.py` 中添加统计方法
  2. 在 `models/code_statistics.py` 中添加数据模型（如需要）
  3. 在 `services/code_statistics/statistics_service.py` 中集成新指标
  4. 在 `ui/code_statistics.py` 中展示新指标
  5. 在导出器中添加新指标的导出逻辑
- **添加新导出格式**：
  1. 在 `services/code_statistics/exporters/` 中创建新导出器（继承 `Exporter`）
  2. 在 `services/code_statistics/result_exporter.py` 中注册新导出器



### 语音播报

语音由 `pyttsx3` 提供（离线 TTS）。如需启用，请确保执行：

```bash
pip install pyttsx3
```

如果未安装或初始化失败，语音会自动降级为文本提示。

## 许可证

本项目仅供学习和研究使用。

---

**享受游戏！** 🦆🎮
