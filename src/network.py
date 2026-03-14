"""
Lichess 联机模块
依赖: pip install requests
"""

import threading
import queue
import time
import json
import requests

# 标记是否可用（检查 requests）
try:
    import requests
    BERSERK_AVAILABLE = True  # 保持变量名兼容
except ImportError:
    BERSERK_AVAILABLE = False
    print("请安装 requests: pip install requests")

class LichessClient:
    def __init__(self):
        self.token = None
        self.game_id = None
        self.my_color = None
        self.connected = False
        self.game_stream = None
        self.move_queue = queue.Queue()  # 接收对手走法
        self.stream_thread = None
        self.username = None
        # 匹配状态
        self.matching = False
        self.match_result = None  # (success, message)
        self.match_thread = None
        
    def connect(self, token):
        """连接到 Lichess"""
        if not BERSERK_AVAILABLE:
            return False, "请先安装 requests: pip install requests"
        
        # 清理token（去除空白字符）
        token = token.strip()
        if not token:
            return False, "Token不能为空"
        
        try:
            # 用 requests 验证 token
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get("https://lichess.org/api/account", headers=headers, timeout=10)
            
            if resp.status_code == 401:
                return False, "Token无效或已过期"
            elif resp.status_code != 200:
                return False, f"连接失败: HTTP {resp.status_code}"
            
            account = resp.json()
            self.username = account.get('username', 'Unknown')
            self.token = token
            self.connected = True
            return True, f"已连接: {self.username}"
        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 lichess.org"
        except Exception as e:
            error_msg = str(e)
            return False, f"连接失败: {error_msg[:40]}"
    
    def create_challenge(self, time_limit=10, increment=0):
        """创建一个开放挑战（非阻塞，后台运行）"""
        if not self.connected or not self.token:
            return False, "未连接到 Lichess"
        
        if self.matching:
            return False, "已在匹配中..."
        
        self.matching = True
        self.match_result = None
        self.game_id = None
        self.my_color = None
        
        def do_match():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                game_found = threading.Event()
                
                def wait_for_game():
                    try:
                        # 使用 requests 流式获取事件
                        event_resp = requests.get(
                            "https://lichess.org/api/stream/event",
                            headers=headers,
                            stream=True,
                            timeout=70
                        )
                        for line in event_resp.iter_lines():
                            if line:
                                try:
                                    event = json.loads(line.decode('utf-8'))
                                    if event.get('type') == 'gameStart':
                                        self.game_id = event['game']['gameId']
                                        if event['game'].get('color') == 'white':
                                            self.my_color = 'white'
                                        else:
                                            self.my_color = 'black'
                                        game_found.set()
                                        break
                                except json.JSONDecodeError:
                                    pass
                        event_resp.close()
                    except Exception as e:
                        print(f"等待游戏错误: {e}")
                
                # 先开始监听
                event_thread = threading.Thread(target=wait_for_game, daemon=True)
                event_thread.start()
                
                # 使用 requests 创建 seek
                data = {
                    "rated": "false",
                    "time": time_limit,
                    "increment": increment
                }
                seek_resp = requests.post(
                    "https://lichess.org/api/board/seek",
                    headers=headers,
                    data=data,
                    timeout=65
                )
                
                # 等待游戏开始（最多60秒）
                if game_found.wait(timeout=60):
                    self._start_game_stream()
                    self.match_result = (True, f"对局开始! 你执{'白' if self.my_color == 'white' else '黑'}")
                else:
                    self.match_result = (False, "等待超时，无人应战")
                    
            except Exception as e:
                self.match_result = (False, f"匹配失败: {str(e)[:30]}")
            finally:
                self.matching = False
        
        self.match_thread = threading.Thread(target=do_match, daemon=True)
        self.match_thread.start()
        return True, "正在匹配中..."
    
    def check_match_status(self):
        """检查匹配状态，返回 (is_matching, result)"""
        if self.matching:
            return True, None
        return False, self.match_result
    
    def cancel_match(self):
        """取消匹配"""
        self.matching = False
        self.match_result = None
    
    def challenge_player(self, opponent_username, time_limit=10, increment=0):
        """挑战指定玩家"""
        if not self.connected or not self.token:
            return False, "未连接到 Lichess"
        
        try:
            # 使用 requests 发送挑战
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "rated": "false",
                "clock.limit": time_limit * 60,
                "clock.increment": increment
            }
            resp = requests.post(
                f"https://lichess.org/api/challenge/{opponent_username}",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if resp.status_code != 200:
                return False, f"挑战失败: {resp.text[:30]}"
            
            challenge_info = resp.json()
            challenge_id = challenge_info.get('challenge', {}).get('id')
            
            if not challenge_id:
                return False, "创建挑战失败"
            
            # 等待对方接受（用 requests 流式获取事件）
            game_found = threading.Event()
            
            def wait_for_accept():
                try:
                    event_resp = requests.get(
                        "https://lichess.org/api/stream/event",
                        headers=headers,
                        stream=True,
                        timeout=60
                    )
                    for line in event_resp.iter_lines():
                        if line:
                            try:
                                event = json.loads(line.decode('utf-8'))
                                if event.get('type') == 'gameStart':
                                    self.game_id = event['game']['gameId']
                                    if event['game'].get('color') == 'white':
                                        self.my_color = 'white'
                                    else:
                                        self.my_color = 'black'
                                    game_found.set()
                                    break
                                elif event.get('type') == 'challengeDeclined':
                                    break
                            except json.JSONDecodeError:
                                pass
                    event_resp.close()
                except Exception as e:
                    print(f"等待接受错误: {e}")
            
            event_thread = threading.Thread(target=wait_for_accept, daemon=True)
            event_thread.start()
            
            if game_found.wait(timeout=60):
                self._start_game_stream()
                return True, f"对局开始! 你执{'白' if self.my_color == 'white' else '黑'}"
            else:
                return False, "挑战被拒绝或超时"
                
        except Exception as e:
            return False, f"挑战失败: {str(e)[:30]}"
    
    def accept_challenge(self, challenge_id):
        """接受挑战"""
        if not self.connected or not self.token:
            return False, "未连接到 Lichess"
        
        try:
            # 用 requests 接受挑战
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(
                f"https://lichess.org/api/challenge/{challenge_id}/accept",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code != 200:
                return False, "接受挑战失败"
            
            # 获取游戏信息
            game_info = resp.json()
            self.game_id = game_info.get('id') or game_info.get('game', {}).get('id')
            
            # 判断颜色（需要从游戏状态获取）
            if self.game_id:
                game_resp = requests.get(
                    f"https://lichess.org/api/board/game/stream/{self.game_id}",
                    headers=headers,
                    stream=True,
                    timeout=10
                )
                for line in game_resp.iter_lines():
                    if line:
                        event = json.loads(line.decode('utf-8'))
                        if event.get('type') == 'gameFull':
                            white_id = event.get('white', {}).get('id', '').lower()
                            if self.username and self.username.lower() == white_id:
                                self.my_color = 'white'
                            else:
                                self.my_color = 'black'
                            break
                game_resp.close()
                
                self._start_game_stream()
                return True, f"对局开始! 你执{'白' if self.my_color == 'white' else '黑'}"
            return False, "游戏启动失败"
            
        except Exception as e:
            return False, f"接受挑战失败: {str(e)[:30]}"
    
    def get_pending_challenges(self):
        """获取待处理的挑战"""
        if not self.connected or not self.token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(
                "https://lichess.org/api/challenge",
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                incoming = data.get('in', [])
                return incoming
            return []
        except:
            return []
    
    def _start_game_stream(self):
        """开始监听游戏状态流"""
        def stream_game():
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                resp = requests.get(
                    f"https://lichess.org/api/board/game/stream/{self.game_id}",
                    headers=headers,
                    stream=True,
                    timeout=None  # 长连接不设超时
                )
                for line in resp.iter_lines():
                    if line:
                        try:
                            event = json.loads(line.decode('utf-8'))
                            if event.get('type') == 'gameFull':
                                # 游戏完整状态
                                state = event.get('state', {})
                                moves = state.get('moves', '')
                                self.move_queue.put(('full', moves))
                            elif event.get('type') == 'gameState':
                                # 游戏状态更新
                                moves = event.get('moves', '')
                                status = event.get('status', '')
                                self.move_queue.put(('state', moves, status))
                            elif event.get('type') == 'chatLine':
                                pass  # 忽略聊天
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                self.move_queue.put(('error', str(e)))
        
        self.stream_thread = threading.Thread(target=stream_game, daemon=True)
        self.stream_thread.start()
    
    def make_move(self, uci_move):
        """发送走法到 Lichess"""
        if not self.game_id or not self.token:
            return False
        
        try:
            # 直接用 requests 发送走法，避免 ndjson 兼容性问题
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.post(
                f"https://lichess.org/api/board/game/{self.game_id}/move/{uci_move}",
                headers=headers,
                timeout=10
            )
            return resp.status_code == 200
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
        if self.game_id and self.token:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                requests.post(
                    f"https://lichess.org/api/board/game/{self.game_id}/resign",
                    headers=headers,
                    timeout=10
                )
            except:
                pass
    
    def disconnect(self):
        """断开连接"""
        self.resign()
        self.game_id = None
        self.my_color = None
        self.connected = False
        self.token = None
