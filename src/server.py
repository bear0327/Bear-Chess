"""
Bear-Chess 私服联机服务端
部署到云服务器运行: python src/server.py
依赖: pip install websockets
"""

import asyncio
import json
import secrets
import time
import websockets

# ── 房间与玩家管理 ──────────────────────────────────────────

rooms = {}        # room_id -> Room
waiting_queue = [] # 快速匹配等待队列 [(ws, nickname)]

class Room:
    def __init__(self, room_id, time_limit=600, increment=0):
        self.room_id = room_id
        self.white = None       # (ws, nickname)
        self.black = None
        self.moves = []         # UCI 走法列表
        self.status = "waiting" # waiting / playing / ended
        self.time_limit = time_limit
        self.increment = increment
        self.created_at = time.time()
        self.draw_offer_from = None  # "white" / "black" / None

    def is_full(self):
        return self.white is not None and self.black is not None

    def get_opponent(self, ws):
        if self.white and self.white[0] is ws:
            return self.black
        if self.black and self.black[0] is ws:
            return self.white
        return None

    def get_color(self, ws):
        if self.white and self.white[0] is ws:
            return "white"
        if self.black and self.black[0] is ws:
            return "black"
        return None

    def to_info(self):
        return {
            "room_id": self.room_id,
            "white": self.white[1] if self.white else None,
            "black": self.black[1] if self.black else None,
            "status": self.status,
            "time_limit": self.time_limit,
            "increment": self.increment,
        }

# ── 生成房间号 ──────────────────────────────────────────────

def generate_room_id():
    return secrets.token_hex(3).upper()  # 6位十六进制

# ── 安全发送 ────────────────────────────────────────────────

async def safe_send(ws, data):
    try:
        await ws.send(json.dumps(data))
    except websockets.ConnectionClosed:
        pass

# ── 消息处理 ────────────────────────────────────────────────

async def handle_client(ws):
    nickname = None
    room = None

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await safe_send(ws, {"type": "error", "msg": "无效的消息格式"})
                continue

            action = msg.get("action")

            # ── 设置昵称 ─────────────────────────────────
            if action == "set_name":
                name = str(msg.get("name", ""))[:20].strip()
                if not name:
                    await safe_send(ws, {"type": "error", "msg": "昵称不能为空"})
                    continue
                nickname = name
                await safe_send(ws, {"type": "name_ok", "name": nickname})

            # ── 创建房间 ─────────────────────────────────
            elif action == "create_room":
                if not nickname:
                    await safe_send(ws, {"type": "error", "msg": "请先设置昵称"})
                    continue
                if room:
                    await safe_send(ws, {"type": "error", "msg": "你已在房间中"})
                    continue

                room_id = generate_room_id()
                time_limit = min(max(int(msg.get("time_limit", 600)), 60), 3600)
                increment = min(max(int(msg.get("increment", 0)), 0), 60)
                new_room = Room(room_id, time_limit, increment)
                new_room.white = (ws, nickname)
                rooms[room_id] = new_room
                room = new_room
                await safe_send(ws, {
                    "type": "room_created",
                    "room_id": room_id,
                    "color": "white",
                    "info": new_room.to_info(),
                })

            # ── 加入房间 ─────────────────────────────────
            elif action == "join_room":
                if not nickname:
                    await safe_send(ws, {"type": "error", "msg": "请先设置昵称"})
                    continue
                if room:
                    await safe_send(ws, {"type": "error", "msg": "你已在房间中"})
                    continue

                room_id = str(msg.get("room_id", "")).strip().upper()
                target = rooms.get(room_id)
                if not target:
                    await safe_send(ws, {"type": "error", "msg": "房间不存在"})
                    continue
                if target.is_full():
                    await safe_send(ws, {"type": "error", "msg": "房间已满"})
                    continue

                target.black = (ws, nickname)
                target.status = "playing"
                room = target

                # 通知双方游戏开始
                game_start_info = {
                    "type": "game_start",
                    "room_id": room_id,
                    "white": target.white[1],
                    "black": target.black[1],
                    "time_limit": target.time_limit,
                    "increment": target.increment,
                }
                await safe_send(target.white[0], {**game_start_info, "your_color": "white"})
                await safe_send(ws, {**game_start_info, "your_color": "black"})

            # ── 快速匹配 ─────────────────────────────────
            elif action == "quick_match":
                if not nickname:
                    await safe_send(ws, {"type": "error", "msg": "请先设置昵称"})
                    continue
                if room:
                    await safe_send(ws, {"type": "error", "msg": "你已在房间中"})
                    continue

                # 查找等待中的对手
                opponent = None
                while waiting_queue:
                    candidate_ws, candidate_name = waiting_queue.pop(0)
                    if candidate_ws.open:
                        opponent = (candidate_ws, candidate_name)
                        break

                if opponent:
                    # 配对成功，创建房间
                    room_id = generate_room_id()
                    new_room = Room(room_id, 600, 0)
                    new_room.white = opponent
                    new_room.black = (ws, nickname)
                    new_room.status = "playing"
                    rooms[room_id] = new_room
                    room = new_room

                    game_start_info = {
                        "type": "game_start",
                        "room_id": room_id,
                        "white": opponent[1],
                        "black": nickname,
                        "time_limit": 600,
                        "increment": 0,
                    }
                    await safe_send(opponent[0], {**game_start_info, "your_color": "white"})
                    await safe_send(ws, {**game_start_info, "your_color": "black"})
                else:
                    # 加入等待队列
                    waiting_queue.append((ws, nickname))
                    await safe_send(ws, {"type": "matching", "msg": "正在等待对手..."})

            # ── 取消匹配 ─────────────────────────────────
            elif action == "cancel_match":
                waiting_queue[:] = [(w, n) for w, n in waiting_queue if w is not ws]
                await safe_send(ws, {"type": "match_cancelled"})

            # ── 走棋 ─────────────────────────────────────
            elif action == "move":
                if not room or room.status != "playing":
                    await safe_send(ws, {"type": "error", "msg": "不在对局中"})
                    continue

                uci_move = str(msg.get("uci", "")).strip()
                if not uci_move:
                    continue

                room.moves.append(uci_move)
                room.draw_offer_from = None
                opponent = room.get_opponent(ws)
                if opponent:
                    await safe_send(opponent[0], {
                        "type": "opponent_move",
                        "uci": uci_move,
                        "moves": room.moves,
                    })
                # 回执确认
                await safe_send(ws, {"type": "move_ok", "uci": uci_move})

            # ── 提和 ─────────────────────────────────────
            elif action == "offer_draw":
                if not room or room.status != "playing":
                    await safe_send(ws, {"type": "error", "msg": "不在对局中"})
                    continue

                color = room.get_color(ws)
                opponent = room.get_opponent(ws)
                if not color or not opponent:
                    await safe_send(ws, {"type": "error", "msg": "对局状态异常"})
                    continue

                if room.draw_offer_from == color:
                    await safe_send(ws, {"type": "error", "msg": "你已发送提和，请等待对方回应"})
                    continue

                room.draw_offer_from = color
                await safe_send(ws, {"type": "draw_offer_sent"})
                await safe_send(opponent[0], {"type": "draw_offer", "from": color})

            # ── 接受提和 ─────────────────────────────────
            elif action == "accept_draw":
                if not room or room.status != "playing":
                    await safe_send(ws, {"type": "error", "msg": "不在对局中"})
                    continue

                color = room.get_color(ws)
                opponent = room.get_opponent(ws)
                if not color or not opponent:
                    await safe_send(ws, {"type": "error", "msg": "对局状态异常"})
                    continue

                if not room.draw_offer_from or room.draw_offer_from == color:
                    await safe_send(ws, {"type": "error", "msg": "当前没有可接受的提和"})
                    continue

                room.status = "ended"
                result = {"type": "game_over", "reason": "draw", "winner": None}
                await safe_send(ws, result)
                await safe_send(opponent[0], result)
                rooms.pop(room.room_id, None)
                room = None

            # ── 拒绝提和 ─────────────────────────────────
            elif action == "decline_draw":
                if not room or room.status != "playing":
                    await safe_send(ws, {"type": "error", "msg": "不在对局中"})
                    continue

                color = room.get_color(ws)
                opponent = room.get_opponent(ws)
                if not color or not opponent:
                    await safe_send(ws, {"type": "error", "msg": "对局状态异常"})
                    continue

                if not room.draw_offer_from or room.draw_offer_from == color:
                    await safe_send(ws, {"type": "error", "msg": "当前没有可拒绝的提和"})
                    continue

                room.draw_offer_from = None
                await safe_send(ws, {"type": "draw_declined"})
                await safe_send(opponent[0], {"type": "draw_declined"})

            # ── 认输 ─────────────────────────────────────
            elif action == "resign":
                if room and room.status == "playing":
                    room.status = "ended"
                    color = room.get_color(ws)
                    winner = "black" if color == "white" else "white"
                    result = {"type": "game_over", "reason": "resign", "winner": winner}
                    await safe_send(ws, result)
                    opponent = room.get_opponent(ws)
                    if opponent:
                        await safe_send(opponent[0], result)
                    rooms.pop(room.room_id, None)
                    room = None

            # ── 离开房间 ──────────────────────────────────
            elif action == "leave":
                if room:
                    opponent = room.get_opponent(ws)
                    if room.status == "playing":
                        color = room.get_color(ws)
                        winner = "black" if color == "white" else "white"
                        if opponent:
                            await safe_send(opponent[0], {
                                "type": "game_over",
                                "reason": "disconnect",
                                "winner": winner,
                            })
                    elif room.status == "waiting" and opponent:
                        await safe_send(opponent[0], {"type": "opponent_left"})
                    rooms.pop(room.room_id, None)
                    room = None
                    await safe_send(ws, {"type": "left"})

            else:
                await safe_send(ws, {"type": "error", "msg": f"未知操作: {action}"})

    except websockets.ConnectionClosed:
        pass
    finally:
        # 清理：玩家断连
        waiting_queue[:] = [(w, n) for w, n in waiting_queue if w is not ws]
        if room:
            opponent = room.get_opponent(ws)
            if room.status == "playing" and opponent:
                color = room.get_color(ws)
                winner = "black" if color == "white" else "white"
                await safe_send(opponent[0], {
                    "type": "game_over",
                    "reason": "disconnect",
                    "winner": winner,
                })
            rooms.pop(room.room_id, None)


# ── 定时清理超时房间 ─────────────────────────────────────────

async def cleanup_rooms():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        expired = [rid for rid, r in rooms.items()
                   if r.status == "waiting" and now - r.created_at > 600]
        for rid in expired:
            r = rooms.pop(rid, None)
            if r and r.white:
                await safe_send(r.white[0], {"type": "room_expired"})


# ── 启动服务器 ───────────────────────────────────────────────

async def main():
    port = 8765
    print(f"Bear-Chess 服务器启动于 ws://0.0.0.0:{port}")
    asyncio.create_task(cleanup_rooms())
    async with websockets.serve(handle_client, "0.0.0.0", port):
        await asyncio.Future()  # 永不结束

if __name__ == "__main__":
    asyncio.run(main())
