import os
import sys

import chess
import pygame

from app_draw_mixin import DrawMixin
from app_event_mixin import EventMixin
from app_network_mixin import NetworkMixin
from constants import *
from logic import GameLogic
from network import LichessClient
from private_network import PrivateClient
from renderer import Renderer


class ChessApp(EventMixin, NetworkMixin, DrawMixin):
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
        self.input_target = None
        self.private = PrivateClient()
        self.private_server_url = PRIVATE_SERVER_URL
        self.private_nickname = PRIVATE_NICKNAME
        self.private_room_id = ""
        self.private_status = ""
        self.reset_game()
        self.state = 'MENU'

    def reset_game(self):
        self.logic.reset()
        self.logic.stop_engine()
        self.logic.engine = None
        self.selected_sq = None
        self.ai_timer = 0
        self.learning_data = {"step": 0, "seq": [], "title": ""}
        self.pending_move_sq = None
        self.scroll_offset = 0
        self.dragging_scrollbar = False
        self.drag_start_y = 0
        self.drag_start_offset = 0
        self.white_time = None
        self.black_time = None
        self.time_increment = 0
        self.time_enabled = False
        self.last_tick = None
        self.time_expired = False
        self.game_mode = None
        self.pvp_draw_offer_from = None
        self.pvp_status = ""
        self.pvp_game_ended = False
        self.private_game_ended = False

    def handle_move(self, pos):
        if self.time_expired or (self.game_mode == 'pvp' and self.pvp_game_ended):
            return

        sq = self.logic.get_sq_from_coords(pos[0] // SQ_SIZE, pos[1] // SQ_SIZE)

        if self.selected_sq is None:
            if p := self.logic.board.piece_at(sq):
                if p.color == self.logic.board.turn:
                    self.selected_sq = sq
        else:
            from_sq = self.selected_sq
            to_sq = sq

            piece = self.logic.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    is_promo_move = any(
                        m.from_square == from_sq and
                        m.to_square == to_sq and
                        m.promotion is not None
                        for m in self.logic.board.legal_moves
                    )
                    if is_promo_move:
                        self.pending_move_sq = (from_sq, to_sq)
                        self.state = 'PROMOTING'
                        self.selected_sq = None
                        return

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
                p = self.logic.board.piece_at(self.selected_sq)
                if p and p.piece_type == chess.PAWN and chess.square_rank(sq) in [0, 7]:
                    self.pending_move_sq = (self.selected_sq, sq)
                    self.state = 'PROMOTING'
                    self.selected_sq = None
                    return

                self._do_move(move)
                self.ai_timer = pygame.time.get_ticks()

            self.selected_sq = None

    def handle_promotion(self, pos):
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        start_x, y = (BOARD_SIZE - SQ_SIZE * 4) // 2, BOARD_HEIGHT // 2 - SQ_SIZE // 2
        for i, pt in enumerate(piece_types):
            if pygame.Rect(start_x + i * SQ_SIZE, y, SQ_SIZE, SQ_SIZE).collidepoint(pos):
                promo_move = chess.Move(self.pending_move_sq[0], self.pending_move_sq[1], promotion=pt)
                self._do_move(promo_move)
                self.state = 'PLAYING'
                self.ai_timer = pygame.time.get_ticks()
                break

    def update(self):
        if self.state == 'PLAYING' and self.logic.engine and self.logic.board.turn != self.logic.player_color and not self.time_expired:
            if self.ai_timer > 0 and pygame.time.get_ticks() - self.ai_timer >= 1000:
                if mv := self.logic.get_ai_move():
                    self._do_move(mv)
                self.ai_timer = 0

        board_over_for_clock = self.logic.board.is_game_over(claim_draw=True) if (self.state == 'PLAYING' and self.game_mode == 'pvp') else self.logic.board.is_game_over()
        if self.state in ('PLAYING', 'ONLINE', 'PRIVATE_ONLINE') and self.time_enabled and not self.time_expired and not board_over_for_clock and not self.pvp_game_ended:
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

        if self.state == 'ONLINE_MENU':
            is_matching, result = self.lichess.check_match_status()
            if not is_matching and result:
                success, msg = result
                self.lichess_status = msg
                self.lichess.match_result = None
                if success:
                    self._start_online_game()

        if self.state == 'ONLINE':
            event = self.lichess.get_opponent_move()
            if event:
                event_type = event[0]
                if event_type in ('full', 'state'):
                    moves_str = event[1]
                    moves = moves_str.split() if moves_str else []
                    self.logic.board = chess.Board()
                    for m in moves:
                        try:
                            self.logic.board.push_uci(m)
                        except Exception:
                            pass
                    if len(event) > 2 and event[2] in ('mate', 'resign', 'stalemate', 'draw'):
                        self.lichess_status = f"游戏结束: {event[2]}"

        if self.state in ('PRIVATE_MENU', 'PRIVATE_ONLINE'):
            self._update_private_online()

    def _do_move(self, move):
        moving_color = self.logic.board.turn
        self.logic.board.push(move)

        if self.game_mode == 'pvp':
            end_text = self._build_pvp_result_text()
            if end_text:
                self.pvp_game_ended = True
                self.pvp_status = end_text

        if self.time_enabled and self.time_increment > 0:
            if moving_color == chess.WHITE:
                self.white_time += self.time_increment
            else:
                self.black_time += self.time_increment

    def quit(self):
        self.logic.stop_engine()
        pygame.quit()
        sys.exit()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)


if __name__ == "__main__":
    if os.path.exists(IMAGES_DIR):
        ChessApp().run()
    else:
        print("请确保 assets/images 文件夹存在")