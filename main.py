import pygame
import chess
import chess.engine
import sys
import os

# 配置常量
WIDTH, HEIGHT = 600, 600
SQ_SIZE = WIDTH // 8
COLORS = [pygame.Color("#eeeed2"), pygame.Color("#769656")]

# --- 请修改为你电脑上 stockfish 的实际路径 ---
STOCKFISH_PATH = "./engine/stockfish-windows-x86-64-avx2.exe" 

class ChessUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("国际象棋 - 模式选择")
        self.font = pygame.font.SysFont("SimHei", 40)
        self.small_font = pygame.font.SysFont("SimHei", 30)
        
        self.board = chess.Board()
        self.images = {}
        self.load_images()
        
        self.state = 'MENU'
        self.game_mode = None    
        self.player_color = None 
        self.selected_sq = None
        self.engine = None
        
        ### 修改点 1: 引入计时器和状态锁 ###
        self.ai_timer_start = 0  # 记录该 AI 走棋的时间点
        self.ai_thinking = False # 标记 AI 是否正在计算

    def load_images(self):
        pieces = ['P', 'R', 'N', 'B', 'Q', 'K']
        for piece in pieces:
            self.images[piece] = pygame.transform.scale(pygame.image.load(f"images/w{piece}.png"), (SQ_SIZE, SQ_SIZE))
            self.images[piece.lower()] = pygame.transform.scale(pygame.image.load(f"images/b{piece}.png"), (SQ_SIZE, SQ_SIZE))

    def draw_button(self, text, y_offset, color=(100, 100, 100)):
        rect = pygame.Rect(WIDTH // 4, y_offset, WIDTH // 2, 60)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
        text_surf = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))
        return rect

    def draw_menu(self):
        self.screen.fill((49, 46, 43))
        title = self.font.render("国际象棋", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        self.btn_pvp = self.draw_button("双人模式", 250)
        self.btn_pve = self.draw_button("人机对战", 350)

    def draw_side_selection(self):
        self.screen.fill((49, 46, 43))
        title = self.font.render("选择你的棋子", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        self.btn_white = self.draw_button("执白 (先手)", 250, (200, 200, 200))
        self.btn_black = self.draw_button("执黑 (后手)", 350, (50, 50, 50))

    def start_engine(self):
        if not self.engine:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            except Exception as e:
                print(f"引擎启动失败: {e}")

    def main_loop(self):
        clock = pygame.time.Clock()
        while True:
            ### 修改点 2: 获取当前时间戳 ###
            current_time = pygame.time.get_ticks()

            if self.state == 'MENU':
                self.draw_menu()
            elif self.state == 'SELECT_SIDE':
                self.draw_side_selection()
            elif self.state == 'PLAYING':
                self.draw_game()
                
                ### 修改点 3: 优化的 AI 触发逻辑 ###
                # 如果是人机模式 + 轮到 AI + 游戏没结束 + 计时器已启动
                if (self.game_mode == 'PVE' and 
                    self.board.turn != self.player_color and 
                    not self.board.is_game_over() and 
                    self.ai_timer_start > 0):
                    
                    # 检查是否已经等待了 1000 毫秒 (1秒)
                    if current_time - self.ai_timer_start >= 1000:
                        self.ai_thinking = True
                        self.ai_move()
                        self.ai_thinking = False
                        self.ai_timer_start = 0 # 重置计时器

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.engine: self.engine.quit()
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # AI 思考时禁止玩家点击，防止逻辑混乱
                    if not self.ai_thinking:
                        pos = pygame.mouse.get_pos()
                        self.handle_click(pos)

            pygame.display.flip()
            clock.tick(60) # 建议提到 60 帧，响应更快

    def handle_click(self, pos):
        if self.state == 'MENU':
            if self.btn_pvp.collidepoint(pos):
                self.game_mode = 'PVP'
                self.state = 'PLAYING'
            elif self.btn_pve.collidepoint(pos):
                self.game_mode = 'PVE'
                self.state = 'SELECT_SIDE'
                
        elif self.state == 'SELECT_SIDE':
            if self.btn_white.collidepoint(pos):
                self.player_color = chess.WHITE
                self.start_engine()
                self.state = 'PLAYING'
                self.ai_timer_start = 0 
            elif self.btn_black.collidepoint(pos):
                self.player_color = chess.BLACK
                self.start_engine()
                self.state = 'PLAYING'
                ### 修改点 4: 玩家选黑棋时，白棋 AI 立即开始 1 秒倒计时 ###
                self.ai_timer_start = pygame.time.get_ticks()
                
        elif self.state == 'PLAYING':
            if self.game_mode == 'PVP' or self.board.turn == self.player_color:
                self.handle_game_click(pos)

    def handle_game_click(self, pos):
        col = pos[0] // SQ_SIZE
        row = 7 - (pos[1] // SQ_SIZE)
        clicked_sq = chess.square(col, row)

        if self.selected_sq is None:
            piece = self.board.piece_at(clicked_sq)
            if piece and piece.color == self.board.turn:
                self.selected_sq = clicked_sq
        else:
            move = chess.Move(self.selected_sq, clicked_sq)
            if self.board.piece_at(self.selected_sq).piece_type == chess.PAWN and chess.square_rank(clicked_sq) in [0, 7]:
                move.promotion = chess.QUEEN
            
            if move in self.board.legal_moves:
                self.board.push(move)
                ### 修改点 5: 玩家落子成功后，记录时间戳，启动 AI 倒计时 ###
                self.ai_timer_start = pygame.time.get_ticks()
                
            self.selected_sq = None

    def ai_move(self):
        ### 修改点 6: 移除内部的 delay，确保 UI 线程不在此卡死 ###
        if self.engine:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            self.board.push(result.move)

    def draw_game(self):
        for r in range(8):
            for c in range(8):
                color = COLORS[(r + c) % 2]
                pygame.draw.rect(self.screen, color, (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
        if self.selected_sq is not None:
            c, r = chess.square_file(self.selected_sq), 7 - chess.square_rank(self.selected_sq)
            s = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(150); s.fill((255, 255, 0))
            self.screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                c, r = chess.square_file(sq), 7 - chess.square_rank(sq)
                self.screen.blit(self.images[piece.symbol()], (c * SQ_SIZE, r * SQ_SIZE))
        
        if self.board.is_game_over():
            text = f"游戏结束: {self.board.result()}"
            surf = self.small_font.render(text, True, (200, 0, 0))
            self.screen.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT - 30))

if __name__ == "__main__":
    if not os.path.exists("images"):
        print("请确保 images 文件夹中有棋子 PNG 文件")
    else:
        ui = ChessUI()
        ui.main_loop()