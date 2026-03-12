"""
Bear-Chess 私服联机客户端模块
通过 WebSocket 连接自建服务器进行对战
依赖: pip install websockets
"""

import threading
import queue
import json

try:
    import websockets
    import asyncio
    PRIVATE_NET_AVAILABLE = True
except ImportError:
    PRIVATE_NET_AVAILABLE = False
    print("请安装 websockets: pip install websockets")


class PrivateClient:
    def __init__(self):
        self.server_url = ""
        self.nickname = ""
        self.connected = False
        self.room_id = None
        self.my_color = None      # "white" / "black"
        self.opponent_name = None
        self.time_limit = 600
        self.increment = 0
        self.game_started = False

        # 匹配/等待状态
        self.matching = False
        self.connecting = False  # 正在连接中

        # 事件队列：主线程从这里取消息
        self.event_queue = queue.Queue()

        # 内部
        self._ws = None
        self._loop = None
        self._thread = None
        self._send_queue = None  # asyncio.Queue, 在事件循环内创建

    # ── 连接服务器 ──────────────────────────────────────────

    def connect(self, server_url, nickname):
        """连接到服务器（非阻塞，立刻返回，结果通过 event_queue 通知）"""
        if not PRIVATE_NET_AVAILABLE:
            return False, "请先安装 websockets: pip install websockets"

        nickname = nickname.strip()[:20]
        if not nickname:
            return False, "昵称不能为空"

        # 规范化 URL
        url = server_url.strip().rstrip("/")
        if not url.startswith("ws://") and not url.startswith("wss://"):
            url = "ws://" + url

        self.server_url = url
        self.nickname = nickname
        self.connected = False
        self.connecting = True

        # 启动后台事件循环线程
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        return True, "正在连接..."

    def _run_loop(self):
        """后台事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._ws_main())

    async def _ws_main(self):
        self._send_queue = asyncio.Queue()
        try:
            async with websockets.connect(self.server_url) as ws:
                self._ws = ws
                # 发送昵称
                await ws.send(json.dumps({"action": "set_name", "name": self.nickname}))

                # 启动接收和发送协程
                recv_task = asyncio.create_task(self._recv_loop(ws))
                send_task = asyncio.create_task(self._send_loop(ws))
                await asyncio.gather(recv_task, send_task)

        except Exception as e:
            self.event_queue.put({"type": "conn_error", "msg": f"连接失败: {str(e)[:40]}"})
        finally:
            self.connected = False
            self.connecting = False
            self._ws = None

    async def _recv_loop(self, ws):
        """接收服务器消息"""
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "name_ok":
                    self.connected = True
                    self.connecting = False

                elif msg_type == "game_start":
                    self.my_color = msg.get("your_color")
                    self.room_id = msg.get("room_id")
                    self.opponent_name = (msg.get("black") if self.my_color == "white"
                                           else msg.get("white"))
                    self.time_limit = msg.get("time_limit", 600)
                    self.increment = msg.get("increment", 0)
                    self.game_started = True
                    self.matching = False

                elif msg_type == "matching":
                    self.matching = True

                elif msg_type == "match_cancelled":
                    self.matching = False

                elif msg_type == "game_over":
                    self.game_started = False
                    self.matching = False

                elif msg_type == "room_created":
                    self.room_id = msg.get("room_id")
                    self.my_color = msg.get("color")

                # 所有消息都放入队列供主线程处理
                self.event_queue.put(msg)

        except websockets.ConnectionClosed:
            self.event_queue.put({"type": "disconnected", "msg": "连接已断开"})

    async def _send_loop(self, ws):
        """从发送队列取消息发给服务器"""
        while True:
            data = await self._send_queue.get()
            if data is None:
                break
            try:
                await ws.send(json.dumps(data))
            except websockets.ConnectionClosed:
                break

    # ── 发送动作（线程安全） ────────────────────────────────

    def _send(self, data):
        """线程安全地向服务器发送消息"""
        if self._loop and self._send_queue is not None:
            self._loop.call_soon_threadsafe(self._send_queue.put_nowait, data)

    # ── 公开 API ────────────────────────────────────────────

    def create_room(self, time_limit=600, increment=0):
        if not self.connected:
            return False, "未连接到服务器"
        self._send({"action": "create_room", "time_limit": time_limit, "increment": increment})
        return True, "正在创建房间..."

    def join_room(self, room_id):
        if not self.connected:
            return False, "未连接到服务器"
        self._send({"action": "join_room", "room_id": room_id.strip().upper()})
        return True, "正在加入房间..."

    def quick_match(self):
        if not self.connected:
            return False, "未连接到服务器"
        if self.matching:
            return False, "已在匹配中"
        self._send({"action": "quick_match"})
        return True, "正在匹配..."

    def cancel_match(self):
        self.matching = False
        self._send({"action": "cancel_match"})

    def make_move(self, uci_move):
        if not self.connected or not self.game_started:
            return False
        self._send({"action": "move", "uci": uci_move})
        return True

    def resign(self):
        if self.connected and self.game_started:
            self._send({"action": "resign"})
        self.game_started = False

    def leave_room(self):
        self._send({"action": "leave"})
        self.room_id = None
        self.my_color = None
        self.game_started = False
        self.matching = False

    def disconnect(self):
        if self.game_started:
            self.resign()
        if self._send_queue is not None and self._loop:
            self._loop.call_soon_threadsafe(self._send_queue.put_nowait, None)
        self.connected = False
        self.game_started = False

    def poll_event(self):
        """非阻塞取一条服务器事件，无事件返回 None"""
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None
