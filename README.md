# Bear Chess

[English README](./README.en.md)

Bear Chess 是一个基于 Python + Pygame 的国际象棋项目，支持本地对弈、人机对战、开局学习与联机模式。

## 功能概览

- 本地双人对弈
- 人机对战（Stockfish UCI 引擎）
- 开局学习与外部开局书提示
- Lichess 联机（Token 连接）
- 多种时控（5+2、10+0、15+10、无限时）

## 运行环境

- Python 3.9+
- Windows（默认配置）

## 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动（源码方式）

```bash
python src/main.py
```

3. Windows 双击启动

- start_app.bat
- create_desktop_shortcut.bat

说明：

- 桌面 Bear Chess 图标使用隐藏启动器，不显示 cmd/shell 窗口。
- start_app.bat 默认只在缺依赖时安装，启动更快。
- 强制重装依赖可用：start_app.bat --install

## 打包为 Windows App

执行：

- build_app.bat

脚本会自动完成：

1. 安装打包依赖
2. 生成 dist/BearChess/BearChess.exe
3. 自动更新桌面启动图标
4. 自动启动 exe

分发说明：

- 当前是 onedir 打包，需保留整个 dist/BearChess 目录。

## 项目结构

```text
Bear-Chess/
	src/
		main.py
		logic.py
		renderer.py
		constants.py
		network.py
		private_network.py
		app_event_mixin.py
		app_network_mixin.py
		app_draw_mixin.py
		server.py
	assets/
		images/
		openings.json
		theme.json
	engine/
	start_app.bat
	build_app.bat
	create_desktop_shortcut.bat
	launch_bear_chess_hidden.vbs
```

## 联机模式（Lichess）

1. 进入联机页面
2. 输入 Lichess API Token
3. 可进行快速匹配、挑战用户、查看并接受挑战

## 自定义棋盘主题

你可以直接编辑 assets/theme.json 来自定义棋盘颜色：

- light_square: 浅色格
- dark_square: 深色格
- bg_color: 背景色
- panel_color: 底部面板色
- images_dir: 棋子图片目录（相对于 assets）
- board_background_image: 棋盘背景图（相对于 assets，例如 bd1.jpg）
- board_square_alpha: 棋盘格透明度（0-255，越小越能看到背景图）

支持两种写法：

- 十六进制字符串（如 #f0d9b5）
- RGB 数组（如 [240, 217, 181]）

修改后重启游戏即可生效。

自定义棋子图片示例：

1. 在 assets 下新建目录，例如 assets/images_blue
2. 放入 12 张棋子图片，文件名必须是：
	wP.png wR.png wN.png wB.png wQ.png wK.png
	bP.png bR.png bN.png bB.png bQ.png bK.png
3. 在 assets/theme.json 中设置：

```json
"images_dir": "images_blue"
```

自定义棋盘背景图示例：

```json
"board_background_image": "bd1.jpg",
"board_square_alpha": 140
```

## 常见问题

1. 启动后直接退出

- 先重新执行 build_app.bat
- 确认 dist/BearChess 下存在 BearChess.exe 与 _internal 目录

2. 人机模式报引擎错误

- 确认 engine/stockfish-windows-x86-64-avx2.exe 存在
- 若更换引擎路径，请在 src/constants.py 中调整

3. 联机连接失败

- 检查网络可访问 lichess.org
- 检查 Token 是否有效

## 致谢

- python-chess
- Pygame
- Lichess API
- Stockfish