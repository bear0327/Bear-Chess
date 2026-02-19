import pygame, sys, os, chess
from constants import *
from logic import GameLogic
from renderer import Renderer
from network import LichessClient, BERSERK_AVAILABLE

class ChessApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("国际象棋 - 最终修复版")
        self.logic = GameLogic()
        self.ui = Renderer(self.screen)
        self.lichess = LichessClient()
        self.lichess_token = ""
        self.lichess_opponent = ""
        self.lichess_status = ""
        self.input_active = False
        self.input_text = ""
        self.input_target = None  # 'token' 或 'opponent'
        self.reset_game()
        self.state = 'MENU'

    def reset_game(self):
        self.logic.reset()
        self.logic.stop_engine()  # 停止AI引擎
        self.logic.engine = None  # 清除引擎引用
        self.selected_sq = None
        self.ai_timer = 0
        self.learning_data = {"step": 0, "seq": [], "title": ""}
        self.pending_move_sq = None
        self.scroll_offset = 0  # 开局菜单滚动偏移
        self.dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_offset = 0
        # 时钟相关
        self.white_time = None  # 白方剩余时间（秒）
        self.black_time = None  # 黑方剩余时间（秒）
        self.time_increment = 0  # 每步加秒
        self.time_enabled = False  # 是否启用计时
        self.last_tick = None  # 上次计时时间戳
        self.time_expired = False  # 是否超时
        self.game_mode = None  # 'pvp', 'ai', 'learning', 'online'

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
            
            # 文本输入处理
            if self.input_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._handle_input_submit()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                elif event.unicode.isprintable():
                    self.input_text += event.unicode
    
    def _handle_input_submit(self):
        """处理输入提交"""
        self.input_active = False
        if self.input_target == 'token':
            self.lichess_token = self.input_text
            success, msg = self.lichess.connect(self.lichess_token)
            self.lichess_status = msg
        elif self.input_target == 'opponent':
            self.lichess_opponent = self.input_text
            self.lichess_status = f"正在挑战 {self.lichess_opponent}..."
            success, msg = self.lichess.challenge_player(self.lichess_opponent)
            self.lichess_status = msg
            if success:
                self._start_online_game()
    
    def _start_online_game(self):
        """开始联机游戏"""
        self.reset_game()
        self.logic.player_color = chess.WHITE if self.lichess.my_color == 'white' else chess.BLACK
        self.state = 'ONLINE'
    
    def _draw_input_box(self):
        """绘制输入框"""
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 输入框背景
        box_rect = pygame.Rect(50, HEIGHT//2 - 50, WIDTH - 100, 100)
        pygame.draw.rect(self.screen, (50, 50, 60), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), box_rect, 2, border_radius=10)
        
        # 提示文字
        hint = "输入 Token:" if self.input_target == 'token' else "输入用户名:"
        self.screen.blit(self.ui.small_font.render(hint, True, (200, 200, 200)), (70, HEIGHT//2 - 40))
        
        # 输入内容
        display_text = self.input_text + ("|" if pygame.time.get_ticks() % 1000 < 500 else "")
        self.screen.blit(self.ui.small_font.render(display_text, True, (255, 255, 255)), (70, HEIGHT//2))
        
        # 提示
        self.screen.blit(self.ui.small_font.render("按 Enter 确认 | ESC 取消", True, (150, 150, 150)), (70, HEIGHT//2 + 30))

    def on_click(self, pos):
        if self.state == 'MENU':
            if pygame.Rect(WIDTH//4, 220, WIDTH//2, 50).collidepoint(pos): 
                self.game_mode = 'pvp'
                self.state = 'TIME_SELECT'
            elif pygame.Rect(WIDTH//4, 290, WIDTH//2, 50).collidepoint(pos): 
                self.game_mode = 'ai'
                self.state = 'TIME_SELECT'
            elif pygame.Rect(WIDTH//4, 360, WIDTH//2, 50).collidepoint(pos): 
                self.reset_game(); self.state = 'OPENING_MENU'
            elif pygame.Rect(WIDTH//4, 430, WIDTH//2, 50).collidepoint(pos):
                self.state = 'ONLINE_MENU'
        
        elif self.state == 'ONLINE_MENU':
            if pygame.Rect(WIDTH//4, 200, WIDTH//2, 50).collidepoint(pos):
                # 输入 Token
                self.input_active = True
                self.input_text = self.lichess_token
                self.input_target = 'token'
            elif pygame.Rect(WIDTH//4, 280, WIDTH//2, 50).collidepoint(pos) and self.lichess.connected:
                # 快速匹配
                self.lichess_status = "正在匹配..."
                success, msg = self.lichess.create_challenge()
                self.lichess_status = msg
                if success:
                    self._start_online_game()
            elif pygame.Rect(WIDTH//4, 360, WIDTH//2, 50).collidepoint(pos) and self.lichess.connected:
                # 挑战好友
                self.input_active = True
                self.input_text = self.lichess_opponent
                self.input_target = 'opponent'
            elif pygame.Rect(WIDTH//4, 440, WIDTH//2, 50).collidepoint(pos) and self.lichess.connected:
                # 查看挑战
                self.state = 'CHALLENGES'
            elif pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45).collidepoint(pos):
                self.state = 'MENU'
        
        elif self.state == 'CHALLENGES':
            challenges = self.lichess.get_pending_challenges()
            y = 150
            for c in challenges[:5]:
                if pygame.Rect(50, y, WIDTH-100, 40).collidepoint(pos):
                    success, msg = self.lichess.accept_challenge(c['id'])
                    self.lichess_status = msg
                    if success:
                        self._start_online_game()
                    return
                y += 50
            if pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45).collidepoint(pos):
                self.state = 'ONLINE_MENU'
        
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

        elif self.state == 'TIME_SELECT':
            # 选择时间控制
            y = 200
            for i, (name, mins, inc) in enumerate(TIME_CONTROLS):
                if pygame.Rect(WIDTH//4, y + i*70, WIDTH//2, 55).collidepoint(pos):
                    saved_mode = self.game_mode  # 保存模式
                    self.reset_game()
                    self.game_mode = saved_mode  # 恢复模式
                    if mins > 0:
                        self.white_time = mins * 60
                        self.black_time = mins * 60
                        self.time_increment = inc
                        self.time_enabled = True
                    else:
                        self.time_enabled = False
                    
                    if self.game_mode == 'pvp':
                        self.logic.player_color = chess.WHITE
                        self.state = 'PLAYING'
                        self.last_tick = pygame.time.get_ticks()
                    elif self.game_mode == 'ai':
                        self.state = 'SELECT_SIDE'
                    return
            if pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45).collidepoint(pos):
                self.state = 'MENU'

        elif self.state == 'SELECT_SIDE':
            if pygame.Rect(WIDTH//4, 250, WIDTH//2, 60).collidepoint(pos):
                self.logic.player_color = chess.WHITE
                self.logic.start_engine()
                self.state = 'PLAYING'
                self.last_tick = pygame.time.get_ticks()
            elif pygame.Rect(WIDTH//4, 330, WIDTH//2, 60).collidepoint(pos):
                self.logic.player_color = chess.BLACK
                self.logic.start_engine()
                self.state = 'PLAYING'
                self.last_tick = pygame.time.get_ticks()
                self.ai_timer = pygame.time.get_ticks()

        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            if pygame.Rect(WIDTH-240, BOARD_HEIGHT+70, 220, 40).collidepoint(pos): 
                self.reset_game(); self.state = 'MENU'; return
            elif self.state == 'PROMOTING': self.handle_promotion(pos)
            elif pos[1] <= BOARD_HEIGHT: self.handle_move(pos)
        
        elif self.state == 'ONLINE':
            if pygame.Rect(WIDTH-240, BOARD_HEIGHT+70, 220, 40).collidepoint(pos):
                # 认输退出
                self.lichess.resign()
                self.lichess.disconnect()
                self.state = 'MENU'
                return
            elif pos[1] <= BOARD_HEIGHT:
                self.handle_online_move(pos)

    def handle_move(self, pos):
        # 超时后不能走棋
        if self.time_expired:
            return
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
                
                self._do_move(move)
                self.ai_timer = pygame.time.get_ticks()
            
            # 无论移动是否成功，都重置选中状态以允许下次点击
            self.selected_sq = None

    def handle_promotion(self, pos):
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        start_x, y = (BOARD_SIZE - SQ_SIZE*4)//2, BOARD_HEIGHT//2 - SQ_SIZE//2
        for i, pt in enumerate(piece_types):
            if pygame.Rect(start_x + i*SQ_SIZE, y, SQ_SIZE, SQ_SIZE).collidepoint(pos):
                promo_move = chess.Move(self.pending_move_sq[0], self.pending_move_sq[1], promotion=pt)
                self._do_move(promo_move)
                self.state = 'PLAYING'; self.ai_timer = pygame.time.get_ticks(); break
    
    def handle_online_move(self, pos):
        """处理联机游戏中的走棋"""
        # 只有轮到自己时才能走
        if self.logic.board.turn != self.logic.player_color:
            return
        
        sq = self.logic.get_sq_from_coords(pos[0]//SQ_SIZE, pos[1]//SQ_SIZE)
        
        if self.selected_sq is None:
            if p := self.logic.board.piece_at(sq):
                if p.color == self.logic.board.turn:
                    self.selected_sq = sq
        else:
            from_sq = self.selected_sq
            to_sq = sq
            move = chess.Move(from_sq, to_sq)
            
            # 检查升变
            piece = self.logic.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    # 默认升变为皇后
                    move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
            
            if move in self.logic.board.legal_moves:
                # 发送走法到 Lichess
                if self.lichess.make_move(move.uci()):
                    self.logic.board.push(move)
            
            self.selected_sq = None

    def update(self):
        # AI逻辑（超时后不能走棋）
        if self.state == 'PLAYING' and self.logic.engine and self.logic.board.turn != self.logic.player_color and not self.time_expired:
            if self.ai_timer > 0 and pygame.time.get_ticks() - self.ai_timer >= 1000:
                if mv := self.logic.get_ai_move():
                    self._do_move(mv)
                self.ai_timer = 0
        
        # 时钟计时（超时后停止计时）
        if self.state == 'PLAYING' and self.time_enabled and not self.time_expired and not self.logic.board.is_game_over():
            current_tick = pygame.time.get_ticks()
            if self.last_tick:
                elapsed = (current_tick - self.last_tick) / 1000.0
                if self.logic.board.turn == chess.WHITE:
                    self.white_time -= elapsed
                    if self.white_time <= 0:
                        self.white_time = 0
                        self.time_expired = True
                else:
                    self.black_time -= elapsed
                    if self.black_time <= 0:
                        self.black_time = 0
                        self.time_expired = True
            self.last_tick = current_tick
        
        # 联机游戏更新
        if self.state == 'ONLINE':
            event = self.lichess.get_opponent_move()
            if event:
                event_type = event[0]
                if event_type in ('full', 'state'):
                    moves_str = event[1]
                    moves = moves_str.split() if moves_str else []
                    # 同步棋盘状态
                    self.logic.board = chess.Board()
                    for m in moves:
                        try:
                            self.logic.board.push_uci(m)
                        except:
                            pass
                    # 检查游戏是否结束
                    if len(event) > 2 and event[2] in ('mate', 'resign', 'stalemate', 'draw'):
                        self.lichess_status = f"游戏结束: {event[2]}"
    
    def _do_move(self, move):
        """执行走法并处理计时"""
        moving_color = self.logic.board.turn
        self.logic.board.push(move)
        # 走完后给刚走的一方加秒
        if self.time_enabled and self.time_increment > 0:
            if moving_color == chess.WHITE:
                self.white_time += self.time_increment
            else:
                self.black_time += self.time_increment

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'MENU':
            self.ui.draw_menu_background()
            # 标题
            title = self.ui.font.render("国际象棋", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))
            # 按钮
            self.ui.draw_button("双人模式", pygame.Rect(WIDTH//4, 220, WIDTH//2, 50))
            self.ui.draw_button("人机对战", pygame.Rect(WIDTH//4, 290, WIDTH//2, 50))
            self.ui.draw_button("开局百科", pygame.Rect(WIDTH//4, 360, WIDTH//2, 50), (45, 90, 45))
            self.ui.draw_button("联机对战", pygame.Rect(WIDTH//4, 430, WIDTH//2, 50), (90, 45, 90))
        
        elif self.state == 'ONLINE_MENU':
            title = self.ui.font.render("Lichess 联机", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
            
            # 状态显示
            status_color = (100, 255, 100) if self.lichess.connected else (255, 150, 150)
            status_txt = f"状态: {self.lichess_status}" if self.lichess_status else ("已连接" if self.lichess.connected else "未连接")
            self.screen.blit(self.ui.small_font.render(status_txt, True, status_color), (20, 80))
            
            # Token 输入
            token_display = self.lichess_token[:20] + "..." if len(self.lichess_token) > 20 else (self.lichess_token or "点击输入Token")
            btn_color = (80, 80, 120) if self.input_active and self.input_target == 'token' else (70, 70, 70)
            self.ui.draw_button(f"Token: {token_display}", pygame.Rect(WIDTH//4, 200, WIDTH//2, 50), btn_color)
            
            # 连接后的选项
            if self.lichess.connected:
                self.ui.draw_button("快速匹配", pygame.Rect(WIDTH//4, 280, WIDTH//2, 50), (45, 90, 45))
                opp_text = self.lichess_opponent or "输入用户名"
                btn_color2 = (80, 80, 120) if self.input_active and self.input_target == 'opponent' else (70, 70, 70)
                self.ui.draw_button(f"挑战: {opp_text}", pygame.Rect(WIDTH//4, 360, WIDTH//2, 50), btn_color2)
                self.ui.draw_button("查看挑战", pygame.Rect(WIDTH//4, 440, WIDTH//2, 50), (70, 70, 70))
            else:
                hint = self.ui.small_font.render("请先在 lichess.org 获取 API Token", True, (180, 180, 180))
                self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 280))
            
            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45), (100, 50, 50))
            
            # 输入框
            if self.input_active:
                self._draw_input_box()
        
        elif self.state == 'CHALLENGES':
            title = self.ui.font.render("待处理的挑战", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
            
            challenges = self.lichess.get_pending_challenges()
            if challenges:
                y = 150
                for c in challenges[:5]:
                    challenger = c.get('challenger', {}).get('name', '未知')
                    self.ui.draw_button(f"来自: {challenger}", pygame.Rect(50, y, WIDTH-100, 40), (45, 90, 45))
                    y += 50
            else:
                hint = self.ui.small_font.render("暂无挑战", True, (180, 180, 180))
                self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 200))
            
            self.ui.draw_button("返回", pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45), (100, 50, 50))
        
        elif self.state == 'ONLINE':
            # 联机游戏界面
            self.ui.draw_board(self.logic, self.selected_sq, 'PLAYING', 0, [], False)
            self.ui.draw_panel(self.logic, 'PLAYING', "", 0, [])
            # 显示对战信息
            info = f"Lichess | 你执{'白' if self.logic.player_color == chess.WHITE else '黑'}"
            self.screen.blit(self.ui.small_font.render(info, True, (150, 200, 255)), (20, BOARD_HEIGHT + 15))
            self.ui.draw_button("认输退出", pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 70, 220, 40), (120, 40, 40))
        
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
        elif self.state == 'TIME_SELECT':
            title = self.ui.font.render("选择时间限制", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))
            btn_y = 200
            for label, minutes, inc in TIME_CONTROLS:
                self.ui.draw_button(label, pygame.Rect(WIDTH//4, btn_y, WIDTH//2, 50))
                btn_y += 70
            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH//4, HEIGHT-70, WIDTH//2, 45), (100, 50, 50))
        elif self.state == 'SELECT_SIDE':
            self.ui.draw_button("执白", pygame.Rect(WIDTH//4, 250, WIDTH//2, 60), (220, 220, 220), (0,0,0))
            self.ui.draw_button("执黑", pygame.Rect(WIDTH//4, 330, WIDTH//2, 60), (40, 40, 40))
        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            hints = (self.state == 'LEARNING')
            self.ui.draw_board(self.logic, self.selected_sq, self.state, self.learning_data["step"], self.learning_data["seq"], hints)
            if self.state == 'PROMOTING': self.ui.draw_promotion_menu(self.logic.board.turn)
            self.ui.draw_panel(self.logic, self.state, self.learning_data["title"], self.learning_data["step"], self.learning_data["seq"])
            # 绘制时钟面板
            if self.time_enabled:
                self.ui.draw_clock_panel(self.white_time, self.black_time, self.logic.board.turn, self.logic.player_color)
            # 超时显示
            if self.time_expired:
                loser = "白方" if self.white_time <= 0 else "黑方"
                winner = "黑方" if self.white_time <= 0 else "白方"
                timeout_txt = self.ui.font.render(f"{loser}超时 - {winner}胜!", True, (255, 80, 80))
                self.screen.blit(timeout_txt, (BOARD_SIZE//2 - timeout_txt.get_width()//2, BOARD_HEIGHT//2 - 20))
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