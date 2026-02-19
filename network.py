"""
Lichess 联机模块
需要先安装: pip install berserk
"""

import threading
import queue
import time

try:
    import berserk
    BERSERK_AVAILABLE = True
except ImportError:
    BERSERK_AVAILABLE = False
    print("请安装 berserk: pip install berserk")

class LichessClient:
    def __init__(self):
        self.client = None
        self.token = None
        self.game_id = None
        self.my_color = None
        self.connected = False
        self.game_stream = None
        self.move_queue = queue.Queue()  # 接收对手走法
        self.stream_thread = None
        self.username = None
        
    def connect(self, token):
        """连接到 Lichess"""
        if not BERSERK_AVAILABLE:
            return False, "请先安装 berserk: pip install berserk"
        
        try:
            session = berserk.TokenSession(token)
            self.client = berserk.Client(session)
            # 验证连接
            account = self.client.account.get()
            self.username = account['username']
            self.token = token
            self.connected = True
            return True, f"已连接: {self.username}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def create_challenge(self, time_limit=10, increment=0):
        """创建一个开放挑战（等待他人加入）"""
        if not self.connected:
            return False, "未连接到 Lichess"
        
        try:
            # 创建 seek（开放挑战）
            # 返回的是生成器，等待有人接受
            self.game_id = None
            self.my_color = None
            
            # 使用线程监听事件流
            def wait_for_game():
                try:
                    for event in self.client.board.stream_incoming_events():
                        if event['type'] == 'gameStart':
                            self.game_id = event['game']['gameId']
                            # 判断颜色
                            if event['game'].get('color') == 'white':
                                self.my_color = 'white'
                            else:
                                self.my_color = 'black'
                            break
                except Exception as e:
                    print(f"等待游戏错误: {e}")
            
            # 先开始监听
            event_thread = threading.Thread(target=wait_for_game, daemon=True)
            event_thread.start()
            
            # 创建 seek
            self.client.board.seek(time_limit, increment, rated=False)
            
            # 等待游戏开始（最多30秒）
            event_thread.join(timeout=30)
            
            if self.game_id:
                self._start_game_stream()
                return True, f"对局开始! ID: {self.game_id}"
            else:
                return False, "等待超时，无人应战"
                
        except Exception as e:
            return False, f"创建挑战失败: {str(e)}"
    
    def challenge_player(self, opponent_username, time_limit=10, increment=0):
        """挑战指定玩家"""
        if not self.connected:
            return False, "未连接到 Lichess"
        
        try:
            # 发送挑战
            challenge = self.client.challenges.create(
                opponent_username,
                rated=False,
                clock_limit=time_limit * 60,
                clock_increment=increment
            )
            
            challenge_id = challenge['challenge']['id']
            
            # 等待对方接受
            def wait_for_accept():
                try:
                    for event in self.client.board.stream_incoming_events():
                        if event['type'] == 'gameStart':
                            self.game_id = event['game']['gameId']
                            if event['game'].get('color') == 'white':
                                self.my_color = 'white'
                            else:
                                self.my_color = 'black'
                            break
                        elif event['type'] == 'challengeDeclined':
                            break
                except Exception as e:
                    print(f"等待接受错误: {e}")
            
            event_thread = threading.Thread(target=wait_for_accept, daemon=True)
            event_thread.start()
            event_thread.join(timeout=60)
            
            if self.game_id:
                self._start_game_stream()
                return True, f"对局开始! 你执{'白' if self.my_color == 'white' else '黑'}"
            else:
                return False, "挑战被拒绝或超时"
                
        except Exception as e:
            return False, f"挑战失败: {str(e)}"
    
    def accept_challenge(self, challenge_id):
        """接受挑战"""
        if not self.connected:
            return False, "未连接到 Lichess"
        
        try:
            self.client.challenges.accept(challenge_id)
            
            # 等待游戏开始
            for event in self.client.board.stream_incoming_events():
                if event['type'] == 'gameStart':
                    self.game_id = event['game']['gameId']
                    if event['game'].get('color') == 'white':
                        self.my_color = 'white'
                    else:
                        self.my_color = 'black'
                    break
            
            if self.game_id:
                self._start_game_stream()
                return True, f"对局开始! 你执{'白' if self.my_color == 'white' else '黑'}"
            return False, "游戏启动失败"
            
        except Exception as e:
            return False, f"接受挑战失败: {str(e)}"
    
    def get_pending_challenges(self):
        """获取待处理的挑战"""
        if not self.connected:
            return []
        
        try:
            challenges = list(self.client.challenges.get_mine())
            incoming = [c for c in challenges if c.get('direction') == 'in']
            return incoming
        except:
            return []
    
    def _start_game_stream(self):
        """开始监听游戏状态流"""
        def stream_game():
            try:
                for event in self.client.board.stream_game_state(self.game_id):
                    if event['type'] == 'gameFull':
                        # 游戏完整状态
                        state = event.get('state', {})
                        moves = state.get('moves', '')
                        self.move_queue.put(('full', moves))
                    elif event['type'] == 'gameState':
                        # 游戏状态更新
                        moves = event.get('moves', '')
                        status = event.get('status', '')
                        self.move_queue.put(('state', moves, status))
                    elif event['type'] == 'chatLine':
                        pass  # 忽略聊天
            except Exception as e:
                self.move_queue.put(('error', str(e)))
        
        self.stream_thread = threading.Thread(target=stream_game, daemon=True)
        self.stream_thread.start()
    
    def make_move(self, uci_move):
        """发送走法到 Lichess"""
        if not self.game_id:
            return False
        
        try:
            self.client.board.make_move(self.game_id, uci_move)
            return True
        except Exception as e:
            print(f"发送走法失败: {e}")
            return False
    
    def get_opponent_move(self):
        """获取对手的走法（非阻塞）"""
        try:
            return self.move_queue.get_nowait()
        except queue.Empty:
            return None
    
    def resign(self):
        """认输"""
        if self.game_id:
            try:
                self.client.board.resign_game(self.game_id)
            except:
                pass
    
    def disconnect(self):
        """断开连接"""
        self.resign()
        self.game_id = None
        self.my_color = None
        self.connected = False
        self.client = None
