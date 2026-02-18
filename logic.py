import chess
import chess.engine
from constants import STOCKFISH_PATH, BOOK_PATH
import os
import chess.polyglot

class GameLogic:
    def __init__(self):
        self.board = chess.Board()
        self.engine = None
        self.player_color = chess.WHITE

    def reset(self):
        self.board = chess.Board()

    def start_engine(self):
        if not self.engine:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            except:
                print("引擎启动失败")

    def stop_engine(self):
        if self.engine: self.engine.quit()

    def get_ai_move(self):
        if self.engine and not self.board.is_game_over():
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            return result.move
        return None

    def get_external_book_moves(self):
        moves = []
        if os.path.exists(BOOK_PATH):
            try:
                with chess.polyglot.open_reader(BOOK_PATH) as reader:
                    for entry in reader.find_all(self.board):
                        moves.append(entry.move) 
            except: pass
        return moves

    def get_sq_from_coords(self, col, row):
        """精准修复：坐标转换"""
        if self.player_color == chess.BLACK:
            # 黑方视角：底层是第0行(Rank 1)，顶层是第7行(Rank 8)
            # col 0 是 File H, col 7 是 File A
            return chess.square(7 - col, row)
        else:
            # 白方视角：底层是第7行(Rank 1)，顶层是第0行(Rank 8)
            # col 0 是 File A, col 7 是 File H
            return chess.square(col, 7 - row)

    def get_coords_from_sq(self, sq):
        """精准修复：棋盘格转屏幕位置"""
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        if self.player_color == chess.BLACK:
            return 7 - f, r
        else:
            return f, 7 - r
    
    def get_external_book_moves(self):
        """仅从外部 .bin 文件获取建议走法"""
        moves = []
        if os.path.exists(BOOK_PATH):
            try:
                with chess.polyglot.open_reader(BOOK_PATH) as reader:
                    for entry in reader.find_all(self.board):
                        moves.append(entry.move)
            except Exception as e:
                print(f"读取外部开局书失败: {e}")
        return moves