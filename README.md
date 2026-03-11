# Bear Chess

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-UI%20Engine-1f6f8b)

[English README](./README.en.md)

一个基于 Python + Pygame 的本地国际象棋项目，支持：

- 本地双人对弈
- 人机对战（内置 Stockfish 引擎）
- 开局百科与外部开局书提示
- Lichess 联机对战（Token 连接）
- 多种时间控制与超时判负

项目适合作为学习图形界面、状态机、棋类规则处理（python-chess）和第三方平台 API（Lichess）的练习样例。

## 目录

- [功能特性](#功能特性)
- [运行环境](#运行环境)
- [快速开始](#快速开始)
- [Lichess 联机说明](#lichess-联机说明)
- [项目截图](#项目截图)
- [目录结构（核心）](#目录结构核心)
- [关键资源路径](#关键资源路径)
- [常见问题](#常见问题)
- [后续可改进方向](#后续可改进方向)
- [致谢](#致谢)

## 功能特性

- 棋盘与棋子渲染（支持白/黑视角转换）
- 合法走子校验（基于 `python-chess`）
- 兵升变选择（后 / 车 / 象 / 马）
- 人机模式（Stockfish UCI 引擎）
- 开局学习模式（`openings.json` 固定线路）
- 外部谱探索（`engine/human.bin`）
- 计时模式（如 `5+2`、`10+0`、`15+10`、无限时）
- Lichess：快速匹配、挑战用户、接受挑战、认输

## 运行环境

- Python 3.9+
- Windows（当前默认引擎路径为 Windows 可执行文件）

## 快速开始

### 1) 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

### 2) 启动项目

```bash
python main.py
```

启动后会进入主菜单，可选择：

- 双人模式
- 人机对战
- 开局百科
- 联机对战（Lichess）



## Lichess 联机说明

1. 进入“联机对战”页面。
2. 输入 Lichess API Token。
3. 成功连接后可：
	 - 快速匹配
	 - 挑战指定用户名
	 - 查看并接受收到的挑战

注意事项：

- Token 无效或过期会在界面状态栏提示。
- 联机模式默认按 10+0 时控启动。
- 网络异常、超时会在状态栏显示错误信息。

## 目录结构（核心）

```text
Bear-Chess/
	main.py          # 应用入口与状态机
	logic.py         # 棋局逻辑、引擎调用、坐标转换
	renderer.py      # UI 渲染（棋盘、面板、按钮、时钟）
	network.py       # Lichess API 连接与对局流处理
	constants.py     # 全局常量、路径、时间控制
	openings.json    # 开局百科数据
	images/          # 棋子与界面资源
	engine/          # Stockfish 可执行文件、开局书、引擎源码
```

## 关键资源路径

项目默认使用以下路径（定义在 `constants.py`）：

- 引擎：`./engine/stockfish-windows-x86-64-avx2.exe`
- 外部开局书：`./engine/human.bin`
- 开局 JSON：`./openings.json`

如果你更换了文件位置，请同步修改 `constants.py`。

## 常见问题

### 1) 启动时报“请确保 images 文件夹存在”

请确认项目根目录下存在 `images/`，且包含 `wK.png`、`bK.png` 等棋子贴图。

### 2) 人机模式无法走子/无 AI 响应

- 检查引擎文件是否存在：`engine/stockfish-windows-x86-64-avx2.exe`
- 若你在非 Windows 平台运行，需要改为对应平台的 Stockfish 可执行文件路径。

### 3) 联机无法连接

- 确认已安装 `requests`
- 确认网络可访问 `https://lichess.org`
- 确认 Token 正确且未过期

## 后续可改进方向

- 增加跨平台引擎路径自动检测（Windows / macOS / Linux）
- 增加音效、动画与主题皮肤
- 增加 PGN 导入导出与复盘
- 补充自动化测试与打包脚本

## 致谢

- [python-chess](https://python-chess.readthedocs.io/)
- [Pygame](https://www.pygame.org/)
- [Lichess API](https://lichess.org/api)
- [Stockfish](https://stockfishchess.org/)