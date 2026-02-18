import pygame, sys, os, chess
from constants import *
from logic import GameLogic
from renderer import Renderer

class ChessApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("国际象棋 - 最终修复版")
        self.logic = GameLogic()
        self.ui = Renderer(self.screen)
        self.reset_game()
        self.state = 'MENU'

    def reset_game(self):
        self.logic.reset()
        self.selected_sq = None
        self.ai_timer = 0
        self.learning_data = {"step": 0, "seq": [], "title": ""}
        self.pending_move_sq = None
        self.scroll_offset = 0  # 开局菜单滚动偏移
        self.dragging_scrollbar = False  # 是否正在拖拽滚动条
        self.drag_start_y = 0  # 拖拽起始位置
        self.drag_start_offset = 0  # 拖拽起始偏移量

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                self.reset_game(); self.state = 'MENU'
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 只响应左键点击
                if self.state == 'OPENING_MENU':
                    # 检查是否点击了滚动条
                    pos = pygame.mouse.get_pos()
                    scrollbar_rect = pygame.Rect(WIDTH - 16, 80, 16, HEIGHT - 200)
                    if scrollbar_rect.collidepoint(pos):
                        self.dragging_scrollbar = True
                        self.drag_start_y = pos[1]
                        self.drag_start_offset = self.scroll_offset
                        continue
                self.on_click(pygame.mouse.get_pos())
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_scrollbar = False
            
            if event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:
                # 拖拽滚动条
                pos = pygame.mouse.get_pos()
                total_height = len(OPENINGS_DATA) * 50
                visible_height = HEIGHT - 200
                max_scroll = max(0, total_height - visible_height)
                if max_scroll > 0:
                    # 计算拖拽比例
                    drag_delta = pos[1] - self.drag_start_y
                    scroll_ratio = drag_delta / (visible_height - max(30, visible_height * visible_height // total_height))
                    self.scroll_offset = max(0, min(max_scroll, self.drag_start_offset + scroll_ratio * max_scroll))
            
            if event.type == pygame.MOUSEWHEEL and self.state == 'OPENING_MENU':
                # 滚轮滚动开局列表
                max_scroll = max(0, len(OPENINGS_DATA) * 50 - 400)  # 可滚动的最大范围
                self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - event.y * 40))

    def on_click(self, pos):
        if self.state == 'MENU':
            if pygame.Rect(WIDTH//4, 250, WIDTH//2, 60).collidepoint(pos): 
                self.reset_game(); self.state, self.logic.player_color = 'PLAYING', chess.WHITE
            elif pygame.Rect(WIDTH//4, 330, WIDTH//2, 60).collidepoint(pos): 
                self.reset_game(); self.state = 'SELECT_SIDE'
            elif pygame.Rect(WIDTH//4, 410, WIDTH//2, 60).collidepoint(pos): 
                self.reset_game(); self.state = 'OPENING_MENU'
        
        elif self.state == 'OPENING_MENU':
            # 滚动区域内的开局按钮点击检测
            scroll_area = pygame.Rect(0, 80, WIDTH, HEIGHT - 200)
            if scroll_area.collidepoint(pos):
                y = 100 - self.scroll_offset
                for name in OPENINGS_DATA:
                    btn_rect = pygame.Rect(50, y, WIDTH-100, 40)
                    if btn_rect.collidepoint(pos) and 80 <= y <= HEIGHT - 200:
                        self.learning_data.update({"title": name, "seq": OPENINGS_DATA[name], "step": 0})
                        self.state, self.logic.player_color = 'LEARNING', chess.WHITE; return
                    y += 50
            # 底部固定按钮
            if pygame.Rect(WIDTH//4, HEIGHT - 140, WIDTH//2, 50).collidepoint(pos):
                self.learning_data.update({"title": "外部谱探索", "seq": [], "step": 0})
                self.state, self.logic.player_color = 'LEARNING', chess.WHITE; return
            if pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45).collidepoint(pos): self.state = 'MENU'

        elif self.state == 'SELECT_SIDE':
            if pygame.Rect(WIDTH//4, 250, WIDTH//2, 60).collidepoint(pos):
                self.logic.player_color = chess.WHITE; self.logic.start_engine(); self.state = 'PLAYING'
            elif pygame.Rect(WIDTH//4, 330, WIDTH//2, 60).collidepoint(pos):
                self.logic.player_color = chess.BLACK; self.logic.start_engine(); self.state = 'PLAYING'
                self.ai_timer = pygame.time.get_ticks()

        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            if pygame.Rect(WIDTH-240, BOARD_HEIGHT+70, 220, 40).collidepoint(pos): 
                self.reset_game(); self.state = 'MENU'; return
            elif self.state == 'PROMOTING': self.handle_promotion(pos)
            elif pos[1] <= BOARD_HEIGHT: self.handle_move(pos)

    def handle_move(self, pos):
        # 修复：获取格子坐标
        sq = self.logic.get_sq_from_coords(pos[0]//SQ_SIZE, pos[1]//SQ_SIZE)
        
        if self.selected_sq is None:
            # 第一次点击：选中棋子
            if p := self.logic.board.piece_at(sq):
                # 只能选中当前该走棋的一方的棋子
                if p.color == self.logic.board.turn:
                    self.selected_sq = sq
        else:
            # 第二次点击：尝试移动
            from_sq = self.selected_sq
            to_sq = sq
            
            # --- 核心修复：优先判定升变 ---
            piece = self.logic.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                # 检查是否走到对方底线
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    # 检查合法的升变移动列表中，是否包含从该点到该点的移动
                    # python-chess 的合法移动会包含 .promotion 属性
                    is_promo_move = any(
                        m.from_square == from_sq and 
                        m.to_square == to_sq and 
                        m.promotion is not None 
                        for m in self.logic.board.legal_moves
                    )
                    
                    if is_promo_move:
                        # 记录待处理的坐标，进入升变选择状态
                        self.pending_move_sq = (from_sq, to_sq)
                        self.state = 'PROMOTING'
                        self.selected_sq = None
                        return # 必须立即返回，不执行下面的 push
            # 第二次点击：执行移动
            move = chess.Move(self.selected_sq, sq)
            
            if self.state == 'LEARNING':
                if self.learning_data["seq"]:
                    if self.learning_data["step"] < len(self.learning_data["seq"]) and \
                       move.uci() == self.learning_data["seq"][self.learning_data["step"]]:
                        self.logic.board.push(move)
                        self.learning_data["step"] += 1
                else:
                    if move in self.logic.get_external_book_moves():
                        self.logic.board.push(move)
            
            elif move in self.logic.board.legal_moves:
                # 检查升变
                p = self.logic.board.piece_at(self.selected_sq)
                if p and p.piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                    self.pending_move_sq = (self.selected_sq, sq)
                    self.state = 'PROMOTING'; self.selected_sq = None; return
                
                self.logic.board.push(move)
                self.ai_timer = pygame.time.get_ticks()
            
            # 无论移动是否成功，都重置选中状态以允许下次点击
            self.selected_sq = None

    def handle_promotion(self, pos):
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        start_x, y = (WIDTH - SQ_SIZE*4)//2, BOARD_HEIGHT//2 - SQ_SIZE//2
        for i, pt in enumerate(piece_types):
            if pygame.Rect(start_x + i*SQ_SIZE, y, SQ_SIZE, SQ_SIZE).collidepoint(pos):
                self.logic.board.push(chess.Move(self.pending_move_sq[0], self.pending_move_sq[1], promotion=pt))
                self.state = 'PLAYING'; self.ai_timer = pygame.time.get_ticks(); break

    def update(self):
        # AI逻辑
        if self.state == 'PLAYING' and self.logic.engine and self.logic.board.turn != self.logic.player_color:
            if self.ai_timer > 0 and pygame.time.get_ticks() - self.ai_timer >= 1000:
                if mv := self.logic.get_ai_move():
                    self.logic.board.push(mv)
                self.ai_timer = 0

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'MENU':
            self.ui.draw_button("双人模式", pygame.Rect(WIDTH//4, 250, WIDTH//2, 60))
            self.ui.draw_button("人机对战", pygame.Rect(WIDTH//4, 330, WIDTH//2, 60))
            self.ui.draw_button("开局百科", pygame.Rect(WIDTH//4, 410, WIDTH//2, 60), (45, 90, 45))
        elif self.state == 'OPENING_MENU':
            # 标题
            title_txt = self.ui.font.render("开局百科", True, (255, 255, 255))
            self.screen.blit(title_txt, (WIDTH//2 - title_txt.get_width()//2, 30))
            
            # 创建滚动区域的裁剪表面
            scroll_area = pygame.Rect(0, 80, WIDTH, HEIGHT - 200)
            scroll_surface = pygame.Surface((WIDTH, HEIGHT - 200), pygame.SRCALPHA)
            
            # 在裁剪表面上绘制开局按钮
            y = 20 - self.scroll_offset  # 相对于滚动区域的 y 坐标
            for name in OPENINGS_DATA:
                if -40 <= y <= HEIGHT - 160:  # 只绘制可见的按钮
                    self.ui.draw_button_on_surface(scroll_surface, name, pygame.Rect(50, y, WIDTH-100, 40), (70, 70, 70))
                y += 50
            
            # 将滚动表面绘制到屏幕
            self.screen.blit(scroll_surface, (0, 80))
            
            # 绘制滚动条
            total_height = len(OPENINGS_DATA) * 50
            visible_height = HEIGHT - 200
            if total_height > visible_height:
                scrollbar_height = max(30, visible_height * visible_height // total_height)
                scrollbar_y = 80 + (self.scroll_offset / max(1, total_height - visible_height)) * (visible_height - scrollbar_height)
                # 滚动条轨道
                pygame.draw.rect(self.screen, (60, 60, 60), (WIDTH - 14, 80, 12, visible_height), border_radius=6)
                # 滚动条滑块（拖拽时高亮）
                mouse_pos = pygame.mouse.get_pos()
                scrollbar_rect = pygame.Rect(WIDTH - 14, scrollbar_y, 12, scrollbar_height)
                if self.dragging_scrollbar:
                    bar_color = (200, 180, 80)  # 拖拽时金黄色
                elif scrollbar_rect.collidepoint(mouse_pos):
                    bar_color = (180, 180, 180)  # 悬停时变亮
                else:
                    bar_color = (130, 130, 130)  # 正常状态
                pygame.draw.rect(self.screen, bar_color, scrollbar_rect, border_radius=6)
            
            # 底部固定按钮背景遮挡
            pygame.draw.rect(self.screen, BG_COLOR, (0, HEIGHT - 160, WIDTH, 160))
            self.ui.draw_button("★ 外部谱自由探索", pygame.Rect(WIDTH//4, HEIGHT - 140, WIDTH//2, 50), (45, 90, 45))
            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45), (100, 50, 50))
        elif self.state == 'SELECT_SIDE':
            self.ui.draw_button("执白", pygame.Rect(WIDTH//4, 250, WIDTH//2, 60), (220, 220, 220), (0,0,0))
            self.ui.draw_button("执黑", pygame.Rect(WIDTH//4, 330, WIDTH//2, 60), (40, 40, 40))
        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            hints = (self.state == 'LEARNING')
            self.ui.draw_board(self.logic, self.selected_sq, self.state, self.learning_data["step"], self.learning_data["seq"], hints)
            if self.state == 'PROMOTING': self.ui.draw_promotion_menu(self.logic.board.turn)
            self.ui.draw_panel(self.logic, self.state, self.learning_data["title"], self.learning_data["step"], self.learning_data["seq"])
            self.ui.draw_button("返回主菜单 [ESC]", pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 70, 220, 40), (120, 40, 40))
        pygame.display.flip()

    def quit(self):
        self.logic.stop_engine(); pygame.quit(); sys.exit()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events(); self.update(); self.draw(); clock.tick(60)

if __name__ == "__main__":
    if os.path.exists("images"): ChessApp().run()
    else: print("请确保 images 文件夹存在")