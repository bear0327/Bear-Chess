import pygame

# 尺寸配置
WIDTH, HEIGHT = 600, 680
BOARD_HEIGHT = 600
SQ_SIZE = WIDTH // 8

# 颜色配置
COLORS = [pygame.Color("#eeeed2"), pygame.Color("#769656")]
BG_COLOR = (49, 46, 43)
PANEL_COLOR = (38, 37, 34)

# 路径
STOCKFISH_PATH = "./engine/stockfish-windows-x86-64-avx2.exe"
BOOK_PATH = "./engine/human.bin"

# 开局数据
OPENINGS_DATA = {
    "意大利开局": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
    "西西里防御": ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4"],
    "西班牙开局": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
    "法兰西防御": ["e2e4", "e7e6", "d2d4", "d7d5"],
    "女王兵起手": ["d2d4", "d7d5", "c2c4"],
}