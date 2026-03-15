import pygame
import chess
import math
import os
from constants import *

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = self._safe_ui_font(40)
        self.small_font = self._safe_ui_font(24)
        self.coord_font = self._safe_mono_font(14, bold=True)
        self.images = self._load_images()
        self.menu_bg_image = self._load_menu_background()
        self.board_bg_image = self._load_board_background()

    def _load_windows_font(self, filenames, size):
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        for filename in filenames:
            path = os.path.join(fonts_dir, filename)
            if os.path.exists(path):
                try:
                    return pygame.font.Font(path, size)
                except Exception:
                    continue
        return None

    def _safe_sys_font(self, name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            # 某些 Windows 环境的字体注册表异常会导致 SysFont 崩溃，回退默认字体避免打包版秒退。
            return pygame.font.Font(None, size)

    def _safe_ui_font(self, size):
        # 优先直接读取 Windows 字体文件，避免 SysFont 在个别系统注册表异常时崩溃。
        direct = self._load_windows_font(
            ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "Deng.ttf"],
            size,
        )
        if direct is not None:
            return direct
        return self._safe_sys_font("SimHei", size)

    def _safe_mono_font(self, size, bold=False):
        direct = self._load_windows_font(
            ["consolab.ttf", "consola.ttf", "CascadiaMono.ttf"],
            size,
        )
        if direct is not None:
            return direct
        return self._safe_sys_font("Consolas", size, bold=bold)

    def _load_images(self):
        imgs = {}
        pieces = ['P', 'R', 'N', 'B', 'Q', 'K']
        for p in pieces:
            imgs[p] = pygame.transform.scale(pygame.image.load(os.path.join(PIECE_IMAGES_DIR, f"w{p}.png")), (SQ_SIZE, SQ_SIZE))
            imgs[p.lower()] = pygame.transform.scale(pygame.image.load(os.path.join(PIECE_IMAGES_DIR, f"b{p}.png")), (SQ_SIZE, SQ_SIZE))
        return imgs

    def _load_menu_background(self):
        if not MENU_BACKGROUND_IMAGE:
            return None
        try:
            img = pygame.image.load(MENU_BACKGROUND_IMAGE)
            return pygame.transform.scale(img, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"菜单背景图加载失败: {e}")
            return None

    def _load_board_background(self):
        if not BOARD_BACKGROUND_IMAGE:
            return None
        try:
            img = pygame.image.load(BOARD_BACKGROUND_IMAGE)
            return pygame.transform.scale(img, (BOARD_SIZE, BOARD_SIZE))
        except Exception as e:
            print(f"棋盘背景图加载失败: {e}")
            return None
    
    def draw_menu_background(self):
        """绘制主菜单背景"""
        if self.menu_bg_image is not None:
            self.screen.blit(self.menu_bg_image, (0, 0))
        else:
            self.screen.fill(BG_COLOR)

    def draw_button(self, text, rect, color=(100, 100, 100), text_color=(255, 255, 255)):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        is_hovered = rect.collidepoint(mouse_pos)
        is_pressed = is_hovered and mouse_pressed
        
        # 根据状态调整颜色
        if is_pressed:
            # 点击状态：颜色变暗，下沉效果
            adjusted_color = tuple(max(0, c - 40) for c in color)
            shadow_offset = 1
            border_color = (150, 150, 150)
        elif is_hovered:
            # 悬停状态：颜色变亮，边框高亮
            adjusted_color = tuple(min(255, c + 30) for c in color)
            shadow_offset = 3
            border_color = (255, 220, 100)
        else:
            # 正常状态
            adjusted_color = color
            shadow_offset = 2
            border_color = (200, 200, 200)
        
        # 绘制阴影
        pygame.draw.rect(self.screen, (20, 20, 20), rect.move(shadow_offset, shadow_offset), border_radius=5)
        # 绘制按钮主体
        pygame.draw.rect(self.screen, adjusted_color, rect, border_radius=5)
        # 绘制边框
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
        # 绘制文字
        txt = self.small_font.render(text, True, text_color)
        text_offset = 1 if is_pressed else 0
        self.screen.blit(txt, (rect.centerx - txt.get_width() // 2 + text_offset, 
                               rect.centery - txt.get_height() // 2 + text_offset))
        return rect

    def draw_button_on_surface(self, surface, text, rect, color=(100, 100, 100), text_color=(255, 255, 255)):
        """在指定 Surface 上绘制按钮（用于滚动区域）"""
        # 计算鼠标相对于滚动区域的位置 (滚动区域从 y=80 开始)
        mouse_pos = pygame.mouse.get_pos()
        adjusted_mouse = (mouse_pos[0], mouse_pos[1] - 80)
        mouse_pressed = pygame.mouse.get_pressed()[0]
        is_hovered = rect.collidepoint(adjusted_mouse)
        is_pressed = is_hovered and mouse_pressed
        
        if is_pressed:
            adjusted_color = tuple(max(0, c - 40) for c in color)
            shadow_offset = 1
            border_color = (150, 150, 150)
        elif is_hovered:
            adjusted_color = tuple(min(255, c + 30) for c in color)
            shadow_offset = 3
            border_color = (255, 220, 100)
        else:
            adjusted_color = color
            shadow_offset = 2
            border_color = (200, 200, 200)
        
        pygame.draw.rect(surface, (20, 20, 20), rect.move(shadow_offset, shadow_offset), border_radius=5)
        pygame.draw.rect(surface, adjusted_color, rect, border_radius=5)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=5)
        txt = self.small_font.render(text, True, text_color)
        text_offset = 1 if is_pressed else 0
        surface.blit(txt, (rect.centerx - txt.get_width() // 2 + text_offset, 
                           rect.centery - txt.get_height() // 2 + text_offset))
        return rect

    def _draw_arrow(self, color, start_sq_coords, end_sq_coords, width=6):
        """绘制从一个格子中心指向另一个格子中心的箭头"""
        # 计算起始和结束点的像素中心坐标
        start_pos = (start_sq_coords[0] * SQ_SIZE + SQ_SIZE // 2, 
                     start_sq_coords[1] * SQ_SIZE + SQ_SIZE // 2)
        end_pos = (end_sq_coords[0] * SQ_SIZE + SQ_SIZE // 2, 
                   end_sq_coords[1] * SQ_SIZE + SQ_SIZE // 2)

        # 1. 绘制箭头的杆（直线）
        pygame.draw.line(self.screen, color, start_pos, end_pos, width)

        # 2. 计算箭头的头部（三角形）
        # 计算线段的角度
        angle = math.atan2(start_pos[1] - end_pos[1], start_pos[0] - end_pos[0])
        
        # 箭头两翼的长度和张开角度
        arrow_head_size = 20
        arrow_head_angle = math.pi / 6  # 30度

        # 计算三角形的三个顶点
        point1 = end_pos
        point2 = (end_pos[0] + arrow_head_size * math.cos(angle + arrow_head_angle),
                  end_pos[1] + arrow_head_size * math.sin(angle + arrow_head_angle))
        point3 = (end_pos[0] + arrow_head_size * math.cos(angle - arrow_head_angle),
                  end_pos[1] + arrow_head_size * math.sin(angle - arrow_head_angle))

        # 绘制三角形箭头
        pygame.draw.polygon(self.screen, color, [point1, point2, point3])

    def _draw_board_coordinates(self, logic):
        if logic.player_color == chess.WHITE:
            files = ["a", "b", "c", "d", "e", "f", "g", "h"]
            ranks = ["8", "7", "6", "5", "4", "3", "2", "1"]
        else:
            files = ["h", "g", "f", "e", "d", "c", "b", "a"]
            ranks = ["1", "2", "3", "4", "5", "6", "7", "8"]

        # 坐标绘制到棋盘外侧的专用留白区，避免与棋盘内容和底部文字冲突。
        bottom_y = BOARD_SIZE + (COORD_GUTTER_BOTTOM // 2)
        right_x = BOARD_SIZE + (COORD_GUTTER_RIGHT // 2)

        for c, file_label in enumerate(files):
            text_color = (230, 230, 230)
            txt = self.coord_font.render(file_label, True, text_color)
            x = c * SQ_SIZE + SQ_SIZE // 2 - txt.get_width() // 2
            y = bottom_y - txt.get_height() // 2
            self.screen.blit(txt, (x, y))

        for r, rank_label in enumerate(ranks):
            text_color = (230, 230, 230)
            txt = self.coord_font.render(rank_label, True, text_color)
            x = right_x - txt.get_width() // 2
            y = r * SQ_SIZE + SQ_SIZE // 2 - txt.get_height() // 2
            self.screen.blit(txt, (x, y))

    def draw_board_coordinates_overlay(self, logic):
        if BOARD_SHOW_COORDINATES:
            self._draw_board_coordinates(logic)

    def draw_board(self, logic, selected_sq, state, learning_step, learning_seq, show_hints=False):
        # 1. 绘制基础棋盘格
        if self.board_bg_image is not None:
            self.screen.blit(self.board_bg_image, (0, 0))
            if BOARD_OVERLAY_SQUARES:
                for r in range(8):
                    for c in range(8):
                        base = COLORS[(r + c) % 2]
                        square = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
                        square.fill((base.r, base.g, base.b, BOARD_SQUARE_ALPHA))
                        self.screen.blit(square, (c * SQ_SIZE, r * SQ_SIZE))
        else:
            for r in range(8):
                for c in range(8):
                    pygame.draw.rect(self.screen, COLORS[(r + c) % 2], (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
                # --- 核心修改：绘制开局书提示箭头 ---
        if show_hints:
            book_moves = logic.get_external_book_moves()
            for move in book_moves:
                # 获取起始和结束格的屏幕坐标
                start_coords = logic.get_coords_from_sq(move.from_square)
                end_coords = logic.get_coords_from_sq(move.to_square)
                
                # 绘制绿色半透明箭头
                # 注意：Pygame draw 默认不支持线段透明，我们使用带 Alpha 的颜色，
                # 如果效果不够透明，可以考虑绘制到单独的 Surface 上再 blit
                self._draw_arrow((34, 177, 76), start_coords, end_coords)


        # 3. 绘制百科固定线路高亮
        if state == 'LEARNING' and learning_seq and learning_step < len(learning_seq):
            mv = chess.Move.from_uci(learning_seq[learning_step])
            for sq, color in [(mv.from_square, (0, 255, 255, 120)), (mv.to_square, (0, 255, 0, 150))]:
                c, r = logic.get_coords_from_sq(sq)
                s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA); s.fill(color)
                self.screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

        # 4. 绘制玩家选中高亮
        if selected_sq is not None:
            c, r = logic.get_coords_from_sq(selected_sq)
            s = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA); s.fill((255, 255, 0, 150))
            self.screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

        # 5. 【核心修复】绘制所有棋子 (必须在格子和提示的上方)
        for sq in chess.SQUARES:
            p = logic.board.piece_at(sq)
            if p:
                c, r = logic.get_coords_from_sq(sq)
                self.screen.blit(self.images[p.symbol()], (c * SQ_SIZE, r * SQ_SIZE))

    def draw_panel(self, logic, state, learning_title, learning_step, learning_seq):
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, PANEL_TOP, WIDTH, HEIGHT - PANEL_TOP))
        pygame.draw.line(self.screen, (70, 70, 70), (0, PANEL_TOP), (WIDTH, PANEL_TOP), 2)
        
        if state == 'LEARNING':
            # 截断过长的开局名称
            max_title_len = 12
            display_title = learning_title if len(learning_title) <= max_title_len else learning_title[:max_title_len] + "..."
            txt = f"{display_title} ({learning_step}/{len(learning_seq)})"
            col = (150, 255, 150)
        elif logic.board.is_game_over(claim_draw=True):
            txt = f"结束 | {logic.board.result(claim_draw=True)}"; col = (255, 100, 100)
        else:
            turn = "白方" if logic.board.turn == chess.WHITE else "黑方"
            txt = f"等待{turn}走棋..."; col = (255, 255, 255)
        
        # 第一行：状态信息
        self.screen.blit(self.small_font.render(txt, True, col), (20, PANEL_TOP + 15))
        
        # 第二行：显示完整开局名称（如果被截断了）
        if state == 'LEARNING' and len(learning_title) > max_title_len:
            full_txt = self.small_font.render(learning_title, True, (120, 200, 120))
            self.screen.blit(full_txt, (20, PANEL_TOP + 50))
    
    def draw_promotion_menu(self, turn):
        # 遮罩层
        overlay = pygame.Surface((WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 棋子选项 (后、车、象、马)
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        symbols = ['Q', 'R', 'B', 'N'] if turn == chess.WHITE else ['q', 'r', 'b', 'n']
        
        menu_w = SQ_SIZE * 4
        start_x, y = (BOARD_SIZE - menu_w) // 2, BOARD_HEIGHT // 2 - SQ_SIZE // 2
        
        # 背景
        pygame.draw.rect(self.screen, (220, 220, 220), (start_x - 10, y - 10, menu_w + 20, SQ_SIZE + 20), border_radius=5)
        
        for i, s in enumerate(symbols):
            rect = pygame.Rect(start_x + i * SQ_SIZE, y, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=3)
            # 绘制对应的棋子图片
            self.screen.blit(self.images[s], rect)
    
    def draw_clock_panel(self, white_time, black_time, current_turn, player_color, time_enabled=True):
        """绘制右侧时钟面板"""
        panel_x = SIDE_PANEL_X
        panel_rect = pygame.Rect(panel_x, 0, SIDE_PANEL_WIDTH, BOARD_SIZE)
        pygame.draw.rect(self.screen, (30, 30, 35), panel_rect)
        pygame.draw.line(self.screen, (60, 60, 65), (panel_x, 0), (panel_x, BOARD_SIZE), 2)
        
        # 格式化时间
        def format_time(seconds):
            if seconds is None or seconds < 0:
                return "--:--"
            mins = int(seconds) // 60
            secs = int(seconds) % 60
            return f"{mins:02d}:{secs:02d}"
        
        # 时钟字体
        clock_font = self._safe_mono_font(36, bold=True)
        label_font = self._safe_ui_font(18)
        
        # 对手时钟 (顶部)
        opponent_color = chess.BLACK if player_color == chess.WHITE else chess.WHITE
        opponent_time = black_time if opponent_color == chess.BLACK else white_time
        opponent_active = (current_turn == opponent_color) and time_enabled
        
        # 对手区域
        opp_rect = pygame.Rect(panel_x + 10, 50, SIDE_PANEL_WIDTH - 20, 100)
        opp_bg = (80, 40, 40) if opponent_active else (45, 45, 50)
        pygame.draw.rect(self.screen, opp_bg, opp_rect, border_radius=8)
        
        opp_label = "黑方" if opponent_color == chess.BLACK else "白方"
        self.screen.blit(label_font.render(opp_label, True, (180, 180, 180)), (panel_x + 20, 55))
        
        opp_time_txt = clock_font.render(format_time(opponent_time), True, (255, 255, 255))
        self.screen.blit(opp_time_txt, (panel_x + SIDE_PANEL_WIDTH//2 - opp_time_txt.get_width()//2, 85))
        
        # 玩家时钟 (底部)
        player_time = white_time if player_color == chess.WHITE else black_time
        player_active = (current_turn == player_color) and time_enabled
        
        # 玩家区域
        player_rect = pygame.Rect(panel_x + 10, BOARD_SIZE - 150, SIDE_PANEL_WIDTH - 20, 100)
        player_bg = (40, 80, 40) if player_active else (45, 45, 50)
        pygame.draw.rect(self.screen, player_bg, player_rect, border_radius=8)
        
        player_label = "白方" if player_color == chess.WHITE else "黑方"
        self.screen.blit(label_font.render(player_label + " (你)", True, (180, 180, 180)), (panel_x + 20, BOARD_SIZE - 145))
        
        player_time_txt = clock_font.render(format_time(player_time), True, (255, 255, 255))
        self.screen.blit(player_time_txt, (panel_x + SIDE_PANEL_WIDTH//2 - player_time_txt.get_width()//2, BOARD_SIZE - 115))
        
        if not time_enabled:
            hint = label_font.render("无限时", True, (120, 120, 120))
            self.screen.blit(hint, (panel_x + SIDE_PANEL_WIDTH//2 - hint.get_width()//2, BOARD_SIZE//2 - 10))