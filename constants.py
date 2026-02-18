import pygame
import json
import os

# 尺寸配置
WIDTH, HEIGHT = 600, 720
BOARD_HEIGHT = 600
SQ_SIZE = WIDTH // 8

# 颜色配置
COLORS = [pygame.Color("#eae8f1"), pygame.Color("#769656")]
BG_COLOR = (49, 46, 43)
PANEL_COLOR = (38, 37, 34)

# 路径
STOCKFISH_PATH = "./engine/stockfish-windows-x86-64-avx2.exe"
BOOK_PATH = "./engine/human.bin"
OPENINGS_PATH = "./openings.json"

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