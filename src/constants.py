import pygame
import json
import os
import sys

# 尺寸配置
BOARD_SIZE = 600
SIDE_PANEL_WIDTH = 180  # 右侧时钟面板宽度
WIDTH = BOARD_SIZE + SIDE_PANEL_WIDTH  # 780
HEIGHT = 720
BOARD_HEIGHT = 600
SQ_SIZE = BOARD_SIZE // 8

# 时间控制选项 (分钟, 秒增量)
TIME_CONTROLS = [
    ("5+2 闪电", 5, 2),
    ("10+0 快棋", 10, 0),
    ("15+10 慢棋", 15, 10),
    ("无限时", 0, 0),
]

# 颜色配置
COLORS = [pygame.Color("#eae8f1"), pygame.Color("#769656")]
BG_COLOR = (49, 46, 43)
PANEL_COLOR = (38, 37, 34)

def _get_app_base_dir():
    # PyInstaller 打包后优先使用 _MEIPASS（onedir 下通常是 _internal）。
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS

    # 兜底：打包后使用 exe 所在目录，源码运行使用项目根目录。
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_BASE_DIR = _get_app_base_dir()


def _app_path(*parts):
    return os.path.join(APP_BASE_DIR, *parts)


# 路径
STOCKFISH_PATH = _app_path("engine", "stockfish-windows-x86-64-avx2.exe")
BOOK_PATH = _app_path("engine", "human.bin")
OPENINGS_PATH = _app_path("assets", "openings.json")
IMAGES_DIR = _app_path("assets", "images")

# ── 私服联机配置 ─────────────────────────────────────────────
# 将下面的地址改为你的云服务器IP和端口，就不用每次在游戏里输入了
PRIVATE_SERVER_URL = "ws://61.184.13.39:8765"   # 例如 "ws://123.45.67.89:8765"
PRIVATE_NICKNAME = ""     # 默认昵称，留空则需要在游戏中输入

# 从外部 JSON 文件加载开局数据
def _load_openings():
    if os.path.exists(OPENINGS_PATH):
        try:
            with open(OPENINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 展平嵌套结构：{分类: {名称: 走法}} -> {名称: 走法}
                openings = {}
                for category, items in data.items():
                    openings.update(items)
                return openings
        except Exception as e:
            print(f"加载开局文件失败: {e}")
    # 回退到默认开局
    return {
        "意大利开局": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
        "西班牙开局": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
    }

OPENINGS_DATA = _load_openings()