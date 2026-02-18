import pygame
import chess
import math
from constants import *

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("SimHei", 40)
        self.small_font = pygame.font.SysFont("SimHei", 24)
        self.images = self._load_images()

    def _load_images(self):
        imgs = {}
        pieces = ['P', 'R', 'N', 'B', 'Q', 'K']
        for p in pieces:
            imgs[p] = pygame.transform.scale(pygame.image.load(f"images/w{p}.png"), (SQ_SIZE, SQ_SIZE))
            imgs[p.lower()] = pygame.transform.scale(pygame.image.load(f"images/b{p}.png"), (SQ_SIZE, SQ_SIZE))
        return imgs

    def draw_button(self, text, rect, color=(100, 100, 100), text_color=(255, 255, 255)):
        pygame.draw.rect(self.screen, (20, 20, 20), rect.move(2, 2), border_radius=5)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2, border_radius=5)
        txt = self.small_font.render(text, True, text_color)
        self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
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

    def draw_board(self, logic, selected_sq, state, learning_step, learning_seq, show_hints=False):
        # 1. 绘制基础棋盘格
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
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, BOARD_HEIGHT, WIDTH, HEIGHT - BOARD_HEIGHT))
        pygame.draw.line(self.screen, (70, 70, 70), (0, BOARD_HEIGHT), (WIDTH, BOARD_HEIGHT), 2)
        
        if state == 'LEARNING':
            txt = f"百科: {learning_title} ({learning_step}/{len(learning_seq)})"
            col = (150, 255, 150)
        elif logic.board.is_game_over():
            txt = f"结束 | {logic.board.result()}"; col = (255, 100, 100)
        else:
            turn = "白方" if logic.board.turn == chess.WHITE else "黑方"
            txt = f"等待{turn}走棋..."; col = (255, 255, 255)
            
        self.screen.blit(self.small_font.render(txt, True, col), (25, BOARD_HEIGHT + 30))
    
    def draw_promotion_menu(self, turn):
        # 遮罩层
        overlay = pygame.Surface((WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 棋子选项 (后、车、象、马)
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        symbols = ['Q', 'R', 'B', 'N'] if turn == chess.WHITE else ['q', 'r', 'b', 'n']
        
        menu_w = SQ_SIZE * 4
        start_x, y = (WIDTH - menu_w) // 2, BOARD_HEIGHT // 2 - SQ_SIZE // 2
        
        # 背景
        pygame.draw.rect(self.screen, (220, 220, 220), (start_x - 10, y - 10, menu_w + 20, SQ_SIZE + 20), border_radius=5)
        
        for i, s in enumerate(symbols):
            rect = pygame.Rect(start_x + i * SQ_SIZE, y, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, border_radius=3)
            # 绘制对应的棋子图片
            self.screen.blit(self.images[s], rect)