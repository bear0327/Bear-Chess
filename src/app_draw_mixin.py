import pygame
import chess

from constants import *


class DrawMixin:
    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == 'MENU':
            self.ui.draw_menu_background()
            title = self.ui.font.render("Bear-Chess", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
            self.ui.draw_button("双人模式", pygame.Rect(WIDTH // 4, 220, WIDTH // 2, 50))
            self.ui.draw_button("人机对战", pygame.Rect(WIDTH // 4, 290, WIDTH // 2, 50))
            self.ui.draw_button("开局百科", pygame.Rect(WIDTH // 4, 360, WIDTH // 2, 50), (45, 90, 45))
            self.ui.draw_button("联机对战", pygame.Rect(WIDTH // 4, 430, WIDTH // 2, 50), (90, 45, 90))
            self.ui.draw_button("私服联机", pygame.Rect(WIDTH // 4, 500, WIDTH // 2, 50), (45, 70, 120))

        elif self.state == 'ONLINE_MENU':
            title = self.ui.font.render("Lichess 联机", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

            status_color = (100, 255, 100) if self.lichess.connected else (255, 150, 150)
            status_txt = f"状态: {self.lichess_status}" if self.lichess_status else ("已连接" if self.lichess.connected else "未连接")
            self.screen.blit(self.ui.small_font.render(status_txt, True, status_color), (20, 80))

            token_display = self.lichess_token[:20] + "..." if len(self.lichess_token) > 20 else (self.lichess_token or "点击输入Token")
            btn_color = (80, 80, 120) if self.input_active and self.input_target == 'token' else (70, 70, 70)
            self.ui.draw_button(f"Token: {token_display}", pygame.Rect(WIDTH // 4, 200, WIDTH // 2, 50), btn_color)

            if self.lichess.connected:
                if self.lichess.matching:
                    self.ui.draw_button("正在匹配...", pygame.Rect(WIDTH // 4, 280, WIDTH // 2, 50), (120, 120, 45))
                else:
                    self.ui.draw_button("快速匹配", pygame.Rect(WIDTH // 4, 280, WIDTH // 2, 50), (45, 90, 45))
                opp_text = self.lichess_opponent or "输入用户名"
                btn_color2 = (80, 80, 120) if self.input_active and self.input_target == 'opponent' else (70, 70, 70)
                self.ui.draw_button(f"挑战: {opp_text}", pygame.Rect(WIDTH // 4, 360, WIDTH // 2, 50), btn_color2)
                self.ui.draw_button("查看挑战", pygame.Rect(WIDTH // 4, 440, WIDTH // 2, 50), (70, 70, 70))
            else:
                hint = self.ui.small_font.render("请先在 lichess.org 获取 API Token", True, (180, 180, 180))
                self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 280))

            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45), (100, 50, 50))

            if self.input_active:
                self._draw_input_box()

        elif self.state == 'CHALLENGES':
            title = self.ui.font.render("待处理的挑战", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

            challenges = self.lichess.get_pending_challenges()
            if challenges:
                y = 150
                for c in challenges[:5]:
                    challenger = c.get('challenger', {}).get('name', '未知')
                    self.ui.draw_button(f"来自: {challenger}", pygame.Rect(50, y, WIDTH - 100, 40), (45, 90, 45))
                    y += 50
            else:
                hint = self.ui.small_font.render("暂无挑战", True, (180, 180, 180))
                self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 200))

            self.ui.draw_button("返回", pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45), (100, 50, 50))

        elif self.state == 'ONLINE':
            self.ui.draw_board(self.logic, self.selected_sq, 'PLAYING', 0, [], False)
            self.ui.draw_panel(self.logic, 'PLAYING', "", 0, [])
            if self.time_enabled:
                self.ui.draw_clock_panel(self.white_time, self.black_time, self.logic.board.turn, self.logic.player_color)
            if self.time_expired:
                loser = "白方" if self.white_time <= 0 else "黑方"
                winner = "黑方" if self.white_time <= 0 else "白方"
                timeout_txt = self.ui.font.render(f"{loser}超时 - {winner}胜!", True, (255, 80, 80))
                self.screen.blit(timeout_txt, (BOARD_SIZE // 2 - timeout_txt.get_width() // 2, BOARD_HEIGHT // 2 - 20))
            info = f"Lichess | 你执{'白' if self.logic.player_color == chess.WHITE else '黑'}"
            self.screen.blit(self.ui.small_font.render(info, True, (150, 200, 255)), (20, PANEL_TOP + 45))
            self.ui.draw_button("认输退出", pygame.Rect(WIDTH - 240, PANEL_TOP + 70, 220, 40), (120, 40, 40))
            self.ui.draw_board_coordinates_overlay(self.logic)

        elif self.state == 'PRIVATE_MENU':
            self._draw_private_menu()

        elif self.state == 'PRIVATE_ONLINE':
            self._draw_private_online()

        elif self.state == 'OPENING_MENU':
            title_txt = self.ui.font.render("开局百科", True, (255, 255, 255))
            self.screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, 30))

            scroll_surface = pygame.Surface((WIDTH, HEIGHT - 200), pygame.SRCALPHA)
            y = 20 - self.scroll_offset
            for name in OPENINGS_DATA:
                if -40 <= y <= HEIGHT - 160:
                    self.ui.draw_button_on_surface(scroll_surface, name, pygame.Rect(50, y, WIDTH - 100, 40), (70, 70, 70))
                y += 50

            self.screen.blit(scroll_surface, (0, 80))

            total_height = len(OPENINGS_DATA) * 50
            visible_height = HEIGHT - 200
            if total_height > visible_height:
                scrollbar_height = max(30, visible_height * visible_height // total_height)
                scrollbar_y = 80 + (self.scroll_offset / max(1, total_height - visible_height)) * (visible_height - scrollbar_height)
                pygame.draw.rect(self.screen, (60, 60, 60), (WIDTH - 14, 80, 12, visible_height), border_radius=6)
                mouse_pos = pygame.mouse.get_pos()
                scrollbar_rect = pygame.Rect(WIDTH - 14, scrollbar_y, 12, scrollbar_height)
                if self.dragging_scrollbar:
                    bar_color = (200, 180, 80)
                elif scrollbar_rect.collidepoint(mouse_pos):
                    bar_color = (180, 180, 180)
                else:
                    bar_color = (130, 130, 130)
                pygame.draw.rect(self.screen, bar_color, scrollbar_rect, border_radius=6)

            pygame.draw.rect(self.screen, BG_COLOR, (0, HEIGHT - 160, WIDTH, 160))
            self.ui.draw_button("★ 外部谱自由探索", pygame.Rect(WIDTH // 4, HEIGHT - 140, WIDTH // 2, 50), (45, 90, 45))
            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45), (100, 50, 50))

        elif self.state == 'TIME_SELECT':
            title = self.ui.font.render("选择时间限制", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
            btn_y = 200
            for label, minutes, inc in TIME_CONTROLS:
                self.ui.draw_button(label, pygame.Rect(WIDTH // 4, btn_y, WIDTH // 2, 50))
                btn_y += 70
            self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45), (100, 50, 50))

        elif self.state == 'SELECT_SIDE':
            self.ui.draw_button("执白", pygame.Rect(WIDTH // 4, 250, WIDTH // 2, 60), (220, 220, 220), (0, 0, 0))
            self.ui.draw_button("执黑", pygame.Rect(WIDTH // 4, 330, WIDTH // 2, 60), (40, 40, 40))

        elif self.state in ['PLAYING', 'LEARNING', 'PROMOTING']:
            hints = (self.state == 'LEARNING')
            self.ui.draw_board(self.logic, self.selected_sq, self.state, self.learning_data["step"], self.learning_data["seq"], hints)
            if self.state == 'PROMOTING':
                self.ui.draw_promotion_menu(self.logic.board.turn)
            self.ui.draw_panel(self.logic, self.state, self.learning_data["title"], self.learning_data["step"], self.learning_data["seq"])
            if self.time_enabled:
                self.ui.draw_clock_panel(self.white_time, self.black_time, self.logic.board.turn, self.logic.player_color)
            if self.time_expired:
                loser = "白方" if self.white_time <= 0 else "黑方"
                winner = "黑方" if self.white_time <= 0 else "白方"
                timeout_txt = self.ui.font.render(f"{loser}超时 - {winner}胜!", True, (255, 80, 80))
                self.screen.blit(timeout_txt, (BOARD_SIZE // 2 - timeout_txt.get_width() // 2, BOARD_HEIGHT // 2 - 20))

            if self.state == 'PLAYING' and self.game_mode == 'pvp':
                if self.pvp_status:
                    status_color = (255, 100, 100) if "游戏结束" in self.pvp_status else (200, 200, 120)
                    self.screen.blit(self.ui.small_font.render(self.pvp_status, True, status_color), (20, PANEL_TOP + 45))

                if not self.pvp_game_ended and not self.time_expired:
                    self.ui.draw_button("提和(直接判和)", pygame.Rect(WIDTH - 240, PANEL_TOP + 20, 220, 40), (60, 100, 120))

            self.ui.draw_button("返回主菜单 [ESC]", pygame.Rect(WIDTH - 240, PANEL_TOP + 70, 220, 40), (120, 40, 40))
            self.ui.draw_board_coordinates_overlay(self.logic)

        pygame.display.flip()

    def _draw_private_menu(self):
        title = self.ui.font.render("私服联机", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        if self.private.connected:
            status_color = (100, 255, 100)
        elif self.private.connecting:
            status_color = (255, 220, 100)
        else:
            status_color = (255, 150, 150)
        if self.private_status:
            status_txt = self.private_status
        elif self.private.connecting:
            status_txt = "正在连接..."
        else:
            status_txt = "已连接" if self.private.connected else "未连接"
        self.screen.blit(self.ui.small_font.render(f"状态: {status_txt}", True, status_color), (20, 80))

        if self.private.room_id and not self.private.game_started:
            room_txt = f"房间号: {self.private.room_id}"
            self.screen.blit(self.ui.small_font.render(room_txt, True, (255, 220, 100)), (20, 115))

        srv_display = self.private_server_url or "点击输入服务器地址"
        btn_c1 = (80, 80, 120) if self.input_active and self.input_target == 'private_server' else (70, 70, 70)
        self.ui.draw_button(f"服务器: {srv_display[:25]}", pygame.Rect(WIDTH // 4, 160, WIDTH // 2, 50), btn_c1)

        nick_display = self.private_nickname or "点击输入昵称并连接"
        btn_c2 = (80, 80, 120) if self.input_active and self.input_target == 'private_nick' else (70, 70, 70)
        self.ui.draw_button(f"昵称: {nick_display[:20]}", pygame.Rect(WIDTH // 4, 230, WIDTH // 2, 50), btn_c2)

        if self.private.connected:
            self.ui.draw_button("创建房间", pygame.Rect(WIDTH // 4, 320, WIDTH // 2, 50), (45, 90, 45))
            self.ui.draw_button("加入房间", pygame.Rect(WIDTH // 4, 390, WIDTH // 2, 50), (70, 70, 70))
            if self.private.matching:
                self.ui.draw_button("取消匹配", pygame.Rect(WIDTH // 4, 460, WIDTH // 2, 50), (120, 120, 45))
            else:
                self.ui.draw_button("快速匹配", pygame.Rect(WIDTH // 4, 460, WIDTH // 2, 50), (45, 70, 120))

        self.ui.draw_button("返回主菜单", pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45), (100, 50, 50))

        if self.input_active:
            self._draw_input_box()

    def _draw_private_online(self):
        self.ui.draw_board(self.logic, self.selected_sq, 'PLAYING', 0, [], False)
        self.ui.draw_panel(self.logic, 'PLAYING', "", 0, [])
        if self.time_enabled:
            self.ui.draw_clock_panel(self.white_time, self.black_time, self.logic.board.turn, self.logic.player_color)
        if self.time_expired:
            loser = "白方" if self.white_time <= 0 else "黑方"
            winner = "黑方" if self.white_time <= 0 else "白方"
            timeout_txt = self.ui.font.render(f"{loser}超时 - {winner}胜!", True, (255, 80, 80))
            self.screen.blit(timeout_txt, (BOARD_SIZE // 2 - timeout_txt.get_width() // 2, BOARD_HEIGHT // 2 - 20))

        opp = self.private.opponent_name or "?"
        info = f"对手: {opp} | 你执{'白' if self.logic.player_color == chess.WHITE else '黑'}"
        self.screen.blit(self.ui.small_font.render(info, True, (150, 200, 255)), (20, PANEL_TOP + 45))

        if self.private_status and "游戏结束" in self.private_status:
            self.screen.blit(self.ui.small_font.render(self.private_status, True, (255, 100, 100)), (20, PANEL_TOP + 75))

        if self.private.incoming_draw_offer and not self.private_game_ended:
            self.ui.draw_button("接受和棋", pygame.Rect(WIDTH - 240, PANEL_TOP + 20, 105, 40), (45, 90, 45))
            self.ui.draw_button("拒绝", pygame.Rect(WIDTH - 125, PANEL_TOP + 20, 105, 40), (120, 80, 45))
        elif not self.private_game_ended:
            self.ui.draw_button("提和", pygame.Rect(WIDTH - 240, PANEL_TOP + 20, 220, 40), (60, 100, 120))

        self.ui.draw_button("认输退出", pygame.Rect(WIDTH - 240, PANEL_TOP + 70, 220, 40), (120, 40, 40))
        self.ui.draw_board_coordinates_overlay(self.logic)