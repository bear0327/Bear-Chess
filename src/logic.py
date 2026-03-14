import chess
import chess.engine
from constants import STOCKFISH_PATH, BOOK_PATH
import os
import subprocess
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
                popen_kwargs = {}
                if os.name == "nt":
                    popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH, **popen_kwargs)
            except Exception as e:
                self.engine = None
                print(f"引擎启动失败: {e} | path={STOCKFISH_PATH}")

    def stop_engine(self):
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None

    def get_ai_move(self):
        if self.board.is_game_over():
            return None

        if not self.engine:
            self.start_engine()
            if not self.engine:
                return None

        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            return result.move
        except (chess.engine.EngineTerminatedError, chess.engine.EngineError) as e:
            # 引擎异常退出时尝试重启一次，避免程序直接崩溃。
            print(f"引擎异常，尝试重启: {e}")
            self.stop_engine()
            self.start_engine()
            if not self.engine:
                return None
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
                return result.move
            except Exception as retry_err:
                print(f"引擎重试失败: {retry_err}")
                self.stop_engine()
                return None
        return None

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