import pygame
import json
import os
import sys

# 尺寸配置
BOARD_SIZE = 600
COORD_GUTTER_RIGHT = 28   # 棋盘右侧坐标专用区域
COORD_GUTTER_BOTTOM = 24  # 棋盘下方坐标专用区域
SIDE_PANEL_WIDTH = 180  # 右侧时钟面板宽度
BOTTOM_PANEL_HEIGHT = 120
WIDTH = BOARD_SIZE + COORD_GUTTER_RIGHT + SIDE_PANEL_WIDTH
HEIGHT = BOARD_SIZE + COORD_GUTTER_BOTTOM + BOTTOM_PANEL_HEIGHT
BOARD_HEIGHT = BOARD_SIZE  # 保持棋盘交互区高度，不包含坐标带
PANEL_TOP = BOARD_SIZE + COORD_GUTTER_BOTTOM
SIDE_PANEL_X = BOARD_SIZE + COORD_GUTTER_RIGHT
SQ_SIZE = BOARD_SIZE // 8

# 时间控制选项 (分钟, 秒增量)
TIME_CONTROLS = [
    ("5+2 闪电", 5, 2),
    ("10+0 快棋", 10, 0),
    ("15+10 慢棋", 15, 10),
    ("无限时", 0, 0),
]

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
THEME_CONFIG_PATH = _app_path("assets", "theme.json")


def _color_tuple(value, fallback):
    try:
        if isinstance(value, str):
            c = pygame.Color(value)
        elif isinstance(value, (list, tuple)) and len(value) >= 3:
            c = pygame.Color(int(value[0]), int(value[1]), int(value[2]))
        else:
            return fallback
        return (c.r, c.g, c.b)
    except Exception:
        return fallback


def _resolve_images_dir(value):
    if not value:
        return IMAGES_DIR

    try:
        if os.path.isabs(value):
            candidate = value
        else:
            candidate = _app_path("assets", value)

        # 只有当目录存在且包含核心棋子图片时才使用。
        required = os.path.join(candidate, "wK.png")
        if os.path.isdir(candidate) and os.path.exists(required):
            return candidate
    except Exception:
        pass

    return IMAGES_DIR


def _resolve_background_image(value):
    if not value:
        return None

    try:
        candidates = []
        if os.path.isabs(value):
            candidates.append(value)
        else:
            candidates.append(_app_path("assets", value))
            candidates.append(_app_path("assets", "images", value))

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
    except Exception:
        pass

    return None


def _clamp_alpha(value, fallback):
    try:
        return max(0, min(255, int(value)))
    except Exception:
        return fallback


def _as_bool(value, fallback):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    return fallback


def _load_theme_config():
    defaults = {
        "light_square": (234, 232, 241),
        "dark_square": (118, 150, 86),
        "bg_color": (49, 46, 43),
        "panel_color": (38, 37, 34),
        "images_dir": IMAGES_DIR,
        "menu_background_image": None,
        "board_background_image": None,
        "board_square_alpha": 140,
        "board_overlay_squares": True,
        "board_show_coordinates": True,
    }

    if not os.path.exists(THEME_CONFIG_PATH):
        return defaults

    try:
        with open(THEME_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "light_square": _color_tuple(data.get("light_square"), defaults["light_square"]),
            "dark_square": _color_tuple(data.get("dark_square"), defaults["dark_square"]),
            "bg_color": _color_tuple(data.get("bg_color"), defaults["bg_color"]),
            "panel_color": _color_tuple(data.get("panel_color"), defaults["panel_color"]),
            "images_dir": _resolve_images_dir(data.get("images_dir")),
            "menu_background_image": _resolve_background_image(data.get("menu_background_image")),
            "board_background_image": _resolve_background_image(data.get("board_background_image")),
            "board_square_alpha": _clamp_alpha(data.get("board_square_alpha"), defaults["board_square_alpha"]),
            "board_overlay_squares": _as_bool(data.get("board_overlay_squares"), defaults["board_overlay_squares"]),
            "board_show_coordinates": _as_bool(data.get("board_show_coordinates"), defaults["board_show_coordinates"]),
        }
    except Exception as e:
        print(f"加载主题配置失败: {e}")
        return defaults


_THEME = _load_theme_config()

# 颜色配置
COLORS = [pygame.Color(*_THEME["light_square"]), pygame.Color(*_THEME["dark_square"])]
BG_COLOR = _THEME["bg_color"]
PANEL_COLOR = _THEME["panel_color"]
PIECE_IMAGES_DIR = _THEME["images_dir"]
MENU_BACKGROUND_IMAGE = _THEME["menu_background_image"]
BOARD_BACKGROUND_IMAGE = _THEME["board_background_image"]
BOARD_SQUARE_ALPHA = _THEME["board_square_alpha"]
BOARD_OVERLAY_SQUARES = _THEME["board_overlay_squares"]
BOARD_SHOW_COORDINATES = _THEME["board_show_coordinates"]

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