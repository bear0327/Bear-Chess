import pygame
import chess

from constants import *


class NetworkMixin:
    def _handle_input_submit(self):
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
        elif self.input_target == 'private_server':
            self.private_server_url = self.input_text
        elif self.input_target == 'private_nick':
            self.private_nickname = self.input_text
            if self.private_server_url and self.private_nickname:
                success, msg = self.private.connect(self.private_server_url, self.private_nickname)
                self.private_status = msg
        elif self.input_target == 'private_room_join':
            self.private_room_id = self.input_text
            success, msg = self.private.join_room(self.private_room_id)
            self.private_status = msg

    def _start_online_game(self):
        self.reset_game()
        self.logic.player_color = chess.WHITE if self.lichess.my_color == 'white' else chess.BLACK
        self.white_time = 10 * 60
        self.black_time = 10 * 60
        self.increment = 0
        self.time_enabled = True
        self.last_tick = pygame.time.get_ticks()
        self.state = 'ONLINE'

    def handle_online_move(self, pos):
        if self.logic.board.turn != self.logic.player_color:
            return

        sq = self.logic.get_sq_from_coords(pos[0] // SQ_SIZE, pos[1] // SQ_SIZE)

        if self.selected_sq is None:
            if p := self.logic.board.piece_at(sq):
                if p.color == self.logic.board.turn:
                    self.selected_sq = sq
        else:
            from_sq = self.selected_sq
            to_sq = sq
            move = chess.Move(from_sq, to_sq)

            piece = self.logic.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

            if move in self.logic.board.legal_moves:
                if self.lichess.make_move(move.uci()):
                    self.logic.board.push(move)

            self.selected_sq = None

    def _handle_private_menu_click(self, pos):
        if pygame.Rect(WIDTH // 4, 160, WIDTH // 2, 50).collidepoint(pos):
            self.input_active = True
            self.input_text = self.private_server_url
            self.input_target = 'private_server'
        elif pygame.Rect(WIDTH // 4, 230, WIDTH // 2, 50).collidepoint(pos):
            self.input_active = True
            self.input_text = self.private_nickname
            self.input_target = 'private_nick'
        elif self.private.connected:
            if pygame.Rect(WIDTH // 4, 320, WIDTH // 2, 50).collidepoint(pos):
                success, msg = self.private.create_room()
                self.private_status = msg
            elif pygame.Rect(WIDTH // 4, 390, WIDTH // 2, 50).collidepoint(pos):
                self.input_active = True
                self.input_text = self.private_room_id
                self.input_target = 'private_room_join'
            elif pygame.Rect(WIDTH // 4, 460, WIDTH // 2, 50).collidepoint(pos):
                if self.private.matching:
                    self.private.cancel_match()
                    self.private_status = "已取消匹配"
                else:
                    success, msg = self.private.quick_match()
                    self.private_status = msg
        if pygame.Rect(WIDTH // 4, HEIGHT - 70, WIDTH // 2, 45).collidepoint(pos):
            if self.private.matching:
                self.private.cancel_match()
            self.state = 'MENU'

    def _start_private_game(self):
        self.reset_game()
        self.game_mode = 'private_online'
        self.private_game_ended = False
        self.private_status = "对局开始"
        self.logic.player_color = chess.WHITE if self.private.my_color == 'white' else chess.BLACK
        self.white_time = self.private.time_limit
        self.black_time = self.private.time_limit
        self.time_increment = self.private.increment
        self.time_enabled = True
        self.last_tick = pygame.time.get_ticks()
        self.state = 'PRIVATE_ONLINE'

    def _build_board_result_text(self):
        if not self.logic.board.is_game_over(claim_draw=True):
            return None

        outcome = self.logic.board.outcome(claim_draw=True)
        if outcome is None:
            return "游戏结束"

        if outcome.winner is None:
            reason = str(outcome.termination).replace("Termination.", "")
            return f"游戏结束: 和棋 ({reason})"

        winner_color = chess.WHITE if outcome.winner else chess.BLACK
        if winner_color == self.logic.player_color:
            return "游戏结束: 你获胜"
        return "游戏结束: 你失败"

    def _build_pvp_result_text(self):
        if not self.logic.board.is_game_over(claim_draw=True):
            return None

        outcome = self.logic.board.outcome(claim_draw=True)
        if outcome is None:
            return "游戏结束"

        if outcome.winner is None:
            reason = str(outcome.termination).replace("Termination.", "")
            return f"游戏结束: 和棋 ({reason})"

        winner = "白方" if outcome.winner == chess.WHITE else "黑方"
        return f"游戏结束: {winner}胜"

    def handle_private_move(self, pos):
        if self.private_game_ended:
            return

        if self.logic.board.turn != self.logic.player_color:
            return

        sq = self.logic.get_sq_from_coords(pos[0] // SQ_SIZE, pos[1] // SQ_SIZE)

        if self.selected_sq is None:
            if p := self.logic.board.piece_at(sq):
                if p.color == self.logic.board.turn:
                    self.selected_sq = sq
        else:
            from_sq = self.selected_sq
            to_sq = sq
            move = chess.Move(from_sq, to_sq)

            piece = self.logic.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

            if move in self.logic.board.legal_moves:
                if self.private.make_move(move.uci()):
                    self.logic.board.push(move)
                    if self.time_enabled and self.time_increment > 0:
                        if self.logic.board.turn == chess.WHITE:
                            self.black_time += self.time_increment
                        else:
                            self.white_time += self.time_increment
                    end_text = self._build_board_result_text()
                    if end_text:
                        self.private_game_ended = True
                        self.private_status = end_text

            self.selected_sq = None

    def _update_private_online(self):
        event = self.private.poll_event()
        while event:
            etype = event.get("type")

            if etype == "name_ok":
                self.private_status = f"已连接: {self.private.nickname}"

            elif etype == "conn_error":
                self.private_status = event.get("msg", "连接失败")

            elif etype == "game_start":
                self._start_private_game()

            elif etype == "room_created":
                self.private_room_id = event.get("room_id", "")
                self.private_status = f"房间已创建: {self.private_room_id}（等待对手加入）"

            elif etype == "opponent_move":
                uci = event.get("uci", "")
                if uci:
                    try:
                        m = chess.Move.from_uci(uci)
                        if m in self.logic.board.legal_moves:
                            self.logic.board.push(m)
                            if self.time_enabled and self.time_increment > 0:
                                if self.logic.board.turn == chess.WHITE:
                                    self.black_time += self.time_increment
                                else:
                                    self.white_time += self.time_increment
                            end_text = self._build_board_result_text()
                            if end_text:
                                self.private_game_ended = True
                                self.private_status = end_text
                    except ValueError:
                        pass

            elif etype == "game_over":
                reason = event.get("reason", "")
                winner = event.get("winner", "")
                self.private_game_ended = True
                if reason == "draw":
                    self.private_status = "游戏结束: 双方和棋"
                elif reason == "resign":
                    self.private_status = f"游戏结束: 认输 ({winner}胜)"
                elif reason == "disconnect":
                    self.private_status = f"游戏结束: 对手断线 ({winner}胜)"
                else:
                    self.private_status = f"游戏结束: {reason} ({winner}胜)"

            elif etype == "draw_offer":
                self.private_status = "对手请求和棋"

            elif etype == "draw_offer_sent":
                self.private_status = "已发送提和，等待对方回应"

            elif etype == "draw_declined":
                self.private_status = "提和被拒绝"

            elif etype == "error":
                self.private_status = event.get("msg", "错误")

            elif etype == "matching":
                self.private_status = "正在等待对手..."

            elif etype == "disconnected":
                self.private_status = "连接已断开"
                if self.state == 'PRIVATE_ONLINE':
                    self.state = 'PRIVATE_MENU'

            event = self.private.poll_event()