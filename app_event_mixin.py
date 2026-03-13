import pygame
import chess

from constants import *


class EventMixin:
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.input_active:
                    self.input_active = False
                elif self.state == 'PRIVATE_ONLINE':
                    self.private.resign()
                    self.private.leave_room()
                    self.private_status = ""
                    self.state = 'PRIVATE_MENU'
                else:
                    self.reset_game()
                    self.state = 'MENU'

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == 'OPENING_MENU':
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
                pos = pygame.mouse.get_pos()
                total_height = len(OPENINGS_DATA) * 50
                visible_height = HEIGHT - 200
                max_scroll = max(0, total_height - visible_height)
                if max_scroll > 0:
                    drag_delta = pos[1] - self.drag_start_y
                    scroll_ratio = drag_delta / (visible_height - max(30, visible_height * visible_height // total_height))
                    self.scroll_offset = max(0, min(max_scroll, self.drag_start_offset + scroll_ratio * max_scroll))

            if event.type == pygame.MOUSEWHEEL and self.state == 'OPENING_MENU':
                max_scroll = max(0, len(OPENINGS_DATA) * 50 - 400)
                self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - event.y * 40))

            if self.input_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._handle_input_submit()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                    try:
                        import tkinter as tk

                        root = tk.Tk()
                        root.withdraw()
                        clipboard_text = root.clipboard_get()
                        root.destroy()
                        if clipboard_text:
                            self.input_text += clipboard_text
                    except Exception:
                        pass
                elif event.unicode.isprintable() and event.key != pygame.K_ESCAPE:
                    self.input_text += event.unicode

    def _draw_input_box(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(50, HEIGHT // 2 - 60, WIDTH - 100, 120)
        pygame.draw.rect(self.screen, (50, 50, 60), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), box_rect, 2, border_radius=10)

        hint = "输入 Token:" if self.input_target == 'token' else "输入用户名:"
        self.screen.blit(self.ui.small_font.render(hint, True, (200, 200, 200)), (70, HEIGHT // 2 - 45))

        display_text = self.input_text + ("|" if pygame.time.get_ticks() % 1000 < 500 else "")
        self.screen.blit(self.ui.small_font.render(display_text, True, (255, 255, 255)), (70, HEIGHT // 2 - 5))
        self.screen.blit(self.ui.small_font.render("Enter确认 / ESC取消", True, (150, 150, 150)), (70, HEIGHT // 2 + 30))

    def on_click(self, pos):
        if self.state == 'MENU':
            if pygame.Rect(WIDTH // 4, 220, WIDTH // 2, 50).collidepoint(pos):
                self.game_mode = 'pvp'
                self.state = 'TIME_SELECT'
            elif pygame.Rect(WIDTH // 4, 290, WIDTH // 2, 50).collidepoint(pos):
                self.game_mode = 'ai'
                self.state = 'TIME_SELECT'
            elif pygame.Rect(WIDTH // 4, 360, WIDTH // 2, 50).collidepoint(pos):
                self.reset_game()
                self.state = 'OPENING_MENU'
            elif pygame.Rect(WIDTH // 4, 430, WIDTH // 2, 50).collidepoint(pos):
                self.state = 'ONLINE_MENU'
            elif pygame.Rect(WIDTH // 4, 500, WIDTH // 2, 50).collidepoint(pos):
                self.state = 'PRIVATE_MENU'
                if self.private_server_url and self.private_nickname and not self.private.connected:
                    success, msg = self.private.connect(self.private_server_url, self.private_nickname)
                    self.private_status = msg

        elif self.state == 'ONLINE_MENU':
            if pygame.Rect(WIDTH // 4, 200, WIDTH // 2, 50).collidepoint(pos):
                self.input_active = True
                self.input_text = self.lichess_token
                self.input_target = 'token'
            elif pygame.Rect(WIDTH // 4, 280, WIDTH // 2, 50).collidepoint(pos) and self.lichess.connected:
                if not self.lichess.matching:
                    success, msg = self.lichess.create_challenge()
                    self.lichess_status = msg
            elif pygame.Rect(WIDTH // 4, 360, WIDTH // 2, 50).collidepoint(pos) and self.lichess.connected:
                self.input_active = True
                self.input_text = self.lichess_opponent
                self.input_target = 'opponent'
            elif pygame.Rect(WIDTH // 4, 440, WIDTH // 2, 50).collidepoint(pos) and self.lichess.connected:
                self.state = 'CHALLENGES'
            elif pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45).collidepoint(pos):
                self.state = 'MENU'

        elif self.state == 'CHALLENGES':
            challenges = self.lichess.get_pending_challenges()
            y = 150
            for c in challenges[:5]:
                if pygame.Rect(50, y, WIDTH - 100, 40).collidepoint(pos):
                    success, msg = self.lichess.accept_challenge(c['id'])
                    self.lichess_status = msg
                    if success:
                        self._start_online_game()
                    return
                y += 50
            if pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45).collidepoint(pos):
                self.state = 'ONLINE_MENU'

        elif self.state == 'OPENING_MENU':
            scroll_area = pygame.Rect(0, 80, WIDTH, HEIGHT - 200)
            if scroll_area.collidepoint(pos):
                y = 100 - self.scroll_offset
                for name in OPENINGS_DATA:
                    btn_rect = pygame.Rect(50, y, WIDTH - 100, 40)
                    if btn_rect.collidepoint(pos) and 80 <= y <= HEIGHT - 200:
                        self.learning_data.update({"title": name, "seq": OPENINGS_DATA[name], "step": 0})
                        self.state, self.logic.player_color = 'LEARNING', chess.WHITE
                        return
                    y += 50
            if pygame.Rect(WIDTH // 4, HEIGHT - 140, WIDTH // 2, 50).collidepoint(pos):
                self.learning_data.update({"title": "外部谱探索", "seq": [], "step": 0})
                self.state, self.logic.player_color = 'LEARNING', chess.WHITE
                return
            if pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45).collidepoint(pos):
                self.state = 'MENU'

        elif self.state == 'TIME_SELECT':
            y = 200
            for i, (name, mins, inc) in enumerate(TIME_CONTROLS):
                if pygame.Rect(WIDTH // 4, y + i * 70, WIDTH // 2, 55).collidepoint(pos):
                    saved_mode = self.game_mode
                    self.reset_game()
                    self.game_mode = saved_mode
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
            if pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45).collidepoint(pos):
                self.state = 'MENU'

        elif self.state == 'SELECT_SIDE':
            if pygame.Rect(WIDTH // 4, 250, WIDTH // 2, 60).collidepoint(pos):
                self.logic.player_color = chess.WHITE
                self.logic.start_engine()
                self.state = 'PLAYING'
                self.last_tick = pygame.time.get_ticks()
            elif pygame.Rect(WIDTH // 4, 330, WIDTH // 2, 60).collidepoint(pos):
                self.logic.player_color = chess.BLACK
                self.logic.start_engine()
                self.state = 'PLAYING'
                self.last_tick = pygame.time.get_ticks()
                self.ai_timer = pygame.time.get_ticks()

        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            if pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 70, 220, 40).collidepoint(pos):
                self.reset_game()
                self.state = 'MENU'
                return
            elif self.state == 'PROMOTING':
                self.handle_promotion(pos)
            elif self.state == 'PLAYING' and self.game_mode == 'pvp' and self._handle_pvp_draw_click(pos):
                return
            elif pos[1] <= BOARD_HEIGHT and not self.pvp_game_ended:
                self.handle_move(pos)

        elif self.state == 'ONLINE':
            if pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 70, 220, 40).collidepoint(pos):
                self.lichess.resign()
                self.lichess.disconnect()
                self.state = 'MENU'
                return
            elif pos[1] <= BOARD_HEIGHT:
                self.handle_online_move(pos)

        elif self.state == 'PRIVATE_MENU':
            self._handle_private_menu_click(pos)

        elif self.state == 'PRIVATE_ONLINE':
            if self.private.incoming_draw_offer and not self.private_game_ended:
                if pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 20, 105, 40).collidepoint(pos):
                    success, msg = self.private.accept_draw()
                    self.private_status = msg
                    return
                if pygame.Rect(WIDTH - 125, BOARD_HEIGHT + 20, 105, 40).collidepoint(pos):
                    success, msg = self.private.decline_draw()
                    self.private_status = msg
                    return
            elif not self.private_game_ended and pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 20, 220, 40).collidepoint(pos):
                success, msg = self.private.offer_draw()
                self.private_status = msg
                return

            if pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 70, 220, 40).collidepoint(pos):
                self.private.resign()
                self.private.leave_room()
                self.private_status = ""
                self.state = 'PRIVATE_MENU'
                return
            elif pos[1] <= BOARD_HEIGHT and not self.private_game_ended:
                self.handle_private_move(pos)

    def _handle_pvp_draw_click(self, pos):
        if self.game_mode != 'pvp' or self.state != 'PLAYING':
            return False
        if self.pvp_game_ended:
            return False

        offer_btn = pygame.Rect(WIDTH - 240, BOARD_HEIGHT + 20, 220, 40)
        if offer_btn.collidepoint(pos):
            self.pvp_draw_offer_from = None
            self.pvp_game_ended = True
            self.pvp_status = "游戏结束: 双方和棋"
            return True

        return False