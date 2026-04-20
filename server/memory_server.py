import grpc
from concurrent import futures
import time
import random
import threading
import uuid
import sqlite3
import os
import sys

sys.path.append(os.path.dirname(__file__))
import memory_pb2
import memory_pb2_grpc

BOARD_SIZE  = int(os.environ.get("BOARD_SIZE",  4))
MAX_ROUNDS  = int(os.environ.get("MAX_ROUNDS",  3))

EMOJIS = [
    "🍓","🐶","🍇","⚽","🐱","🍎","🚗","🌟",
    "🍕","🎈","🚀","🎸","🦒","🍩","🌈","🏝️",
    "🦁","🐸","🌺","🍦","🎃","🦋","🐧","🍄",
    "🎯","🏆","🌙","⭐","🎀","🦄","🐢","🍭",
]


def _log(msg, room_id=None):
    prefix = f"[{room_id}]" if room_id else "[SERVER]"
    print(f"{prefix} {time.strftime('%H:%M:%S')} {msg}", flush=True)


# ══════════════════════════════════════════════════════════════════
#  SQLite – ranking persistente
# ══════════════════════════════════════════════════════════════════
_DB_CONN  = None
_DB_LOCK  = threading.Lock()

def _db() -> sqlite3.Connection:
    global _DB_CONN
    if _DB_CONN is not None:
        return _DB_CONN
    with _DB_LOCK:
        if _DB_CONN is not None:
            return _DB_CONN
        data_dir = os.environ.get(
            "DATA_DIR",
            os.path.join(os.path.dirname(__file__), "..", "data"),
        )
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, "ranking.db")
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id     TEXT    NOT NULL,
                round_num   INTEGER NOT NULL,
                board_size  INTEGER NOT NULL,
                ended_at    TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_results (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id            INTEGER NOT NULL REFERENCES rounds(id),
                player_name         TEXT    NOT NULL,
                score               INTEGER NOT NULL,
                total_moves         INTEGER NOT NULL,
                avg_response_time   REAL    NOT NULL
            )
        """)
        conn.commit()
        _DB_CONN = conn
        _log(f"SQLite abierto → {path}")
        return conn


def db_save_round(room_id: str, round_num: int, board_size: int, players: dict):
    conn = _db()
    ended_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _DB_LOCK:
        cur = conn.execute(
            "INSERT INTO rounds (room_id, round_num, board_size, ended_at) VALUES (?,?,?,?)",
            (room_id, round_num, board_size, ended_at),
        )
        round_id = cur.lastrowid
        for d in players.values():
            rt = d["response_times"]
            avg = round(sum(rt) / len(rt), 3) if rt else 0.0
            conn.execute(
                "INSERT INTO player_results "
                "(round_id, player_name, score, total_moves, avg_response_time) "
                "VALUES (?,?,?,?,?)",
                (round_id, d["name"], d["score_this_round"], d["total_moves"], avg),
            )
        conn.commit()
    _log(f"Ronda {round_num} guardada en SQLite (room={room_id})")


def db_get_ranking(limit: int = 20) -> list:
    conn = _db()
    rows = conn.execute("""
        SELECT player_name,
               SUM(score)                AS total_score,
               COUNT(*)                  AS rounds_played,
               SUM(total_moves)          AS total_moves,
               AVG(avg_response_time)    AS avg_rt
        FROM   player_results
        GROUP  BY player_name
        ORDER  BY total_score DESC
        LIMIT  ?
    """, (limit,)).fetchall()
    return rows


# ══════════════════════════════════════════════════════════════════
#  GameRoom – estado y lógica de UNA sala (múltiples rondas)
# ══════════════════════════════════════════════════════════════════
class GameRoom:
    def __init__(self, room_id: str, size: int = BOARD_SIZE, max_rounds: int = MAX_ROUNDS):
        self.room_id    = room_id
        self.size       = size
        self.max_rounds = max_rounds
        self.round      = 0          # ronda actual (0 = esperando inicio)
        self.board      = []
        self.players    = {}         # player_id -> dict
        self.turn_order = []
        self.current_turn_idx = 0
        self.status     = "WAITING"
        self.processing = False
        self.pending_first = {}    # player_id -> (r, c) first-card selection
        self.lock       = threading.Lock()
        self.cv         = threading.Condition(self.lock)
        self._init_board()
        _log(f"Sala creada. Tablero {size}x{size}, {max_rounds} rondas.", room_id)

    # ── Tablero ────────────────────────────────────────────────────
    def _init_board(self):
        num_pairs = (self.size * self.size) // 2
        pool = EMOJIS[:num_pairs] * 2
        random.shuffle(pool)
        self.board = []
        for r in range(self.size):
            self.board.append([
                {"symbol": pool.pop(), "matched": False, "flipped": False}
                for _ in range(self.size)
            ])

    # ── Snapshot (llamar CON lock) ─────────────────────────────────
    def get_state_msg(self) -> memory_pb2.GameState:
        cards = []
        for r in range(self.size):
            for c in range(self.size):
                card = self.board[r][c]
                sym  = card["symbol"] if (card["flipped"] or card["matched"]) else "?"
                cards.append(memory_pb2.Card(
                    r=r, c=c, symbol=sym,
                    flipped=card["flipped"], matched=card["matched"],
                ))
        curr_id   = self.turn_order[self.current_turn_idx] if self.turn_order else ""
        curr_name = self.players[curr_id]["name"] if curr_id else "—"
        scores    = {d["name"]: d["score"] for d in self.players.values()}
        return memory_pb2.GameState(
            board=cards,
            current_player_id=curr_id,
            current_player_name=curr_name,
            status=self.status,
            scores=scores,
            room_id=self.room_id,
            round=self.round,
            max_rounds=self.max_rounds,
        )

    # ── Agregar jugador (llamar CON cv) ────────────────────────────
    def add_player(self, name: str) -> str:
        p_id = f"P-{uuid.uuid4().hex[:4].upper()}"
        self.players[p_id] = {
            "name":            name,
            "score":           0,    # acumulado total (todas las rondas)
            "score_this_round": 0,   # solo ronda actual (para guardar en DB)
            "total_moves":     0,
            "response_times":  [],
            "turn_started_at": 0,
        }
        self.turn_order.append(p_id)
        _log(f"'{name}' ({p_id}) unido. Total: {len(self.players)}", self.room_id)
        if len(self.players) >= 2 and self.status == "WAITING":
            self._start_next_round()
        self.cv.notify_all()
        return p_id

    def _start_next_round(self):
        """Inicia la siguiente ronda (sin lock — llamar desde contexto ya protegido)."""
        self.round += 1
        self.status = "PLAYING"
        self._init_board()
        self.pending_first.clear()
        for d in self.players.values():
            d["score_this_round"] = 0
        self.current_turn_idx = (self.round - 1) % len(self.turn_order)  # rota quien empieza
        self.players[self.turn_order[self.current_turn_idx]]["turn_started_at"] = time.time()
        _log(f"Ronda {self.round}/{self.max_rounds} iniciada.", self.room_id)
    # ── Selección de primera carta (pre-volteo) ────────────────────────
    def select_card(self, p_id: str, r: int, c: int):
        """Voltea la primera carta del turno y difunde el símbolo a todos."""
        with self.lock:
            if self.status != "PLAYING":
                return False, "La partida no está en curso."
            if self.turn_order[self.current_turn_idx] != p_id:
                return False, "No es tu turno."
            if self.processing:
                return False, "Espera, procesando la jugada anterior."
            if not (0 <= r < self.size and 0 <= c < self.size):
                return False, "Coordenadas fuera de rango."
            card = self.board[r][c]
            if card["matched"]:
                return False, "Carta ya emparejada."
            if card["flipped"]:
                return False, "Carta ya está volteada."
            # Unflip a previous pending selection (if player changed mind)
            prev = self.pending_first.get(p_id)
            if prev:
                self.board[prev[0]][prev[1]]["flipped"] = False
            # Flip the new selection
            card["flipped"] = True
            self.pending_first[p_id] = (r, c)
            self.cv.notify_all()
            return True, "ok"
    # ── Jugada ─────────────────────────────────────────────────────
    def play_turn(self, p_id, r1, c1, r2, c2) -> memory_pb2.MoveReply:
        with self.lock:
            if self.status != "PLAYING":
                return memory_pb2.MoveReply(valid=False, message="La partida no está en curso.")
            if self.turn_order[self.current_turn_idx] != p_id:
                return memory_pb2.MoveReply(valid=False, message="No es tu turno.")
            if not (0 <= r1 < self.size and 0 <= c1 < self.size and
                    0 <= r2 < self.size and 0 <= c2 < self.size):
                return memory_pb2.MoveReply(valid=False, message="Coordenadas fuera de rango.")
            if r1 == r2 and c1 == c2:
                return memory_pb2.MoveReply(valid=False, message="Debes elegir dos cartas distintas.")
            if self.processing:
                return memory_pb2.MoveReply(valid=False, message="Espera, procesando la jugada anterior.")
            c1_obj = self.board[r1][c1]
            c2_obj = self.board[r2][c2]
            if c1_obj["matched"] or c2_obj["matched"]:
                return memory_pb2.MoveReply(valid=False, message="Una carta ya fue emparejada.")
            # Card 1 may already be flipped if selected via select_card
            pre_selected = self.pending_first.pop(p_id, None) == (r1, c1)
            if not pre_selected and c1_obj["flipped"]:
                return memory_pb2.MoveReply(valid=False, message="Una carta ya está volteada.")
            if c2_obj["flipped"]:
                return memory_pb2.MoveReply(valid=False, message="Una carta ya está volteada.")

            player = self.players[p_id]
            player["total_moves"] += 1
            if player["turn_started_at"] > 0:
                player["response_times"].append(time.time() - player["turn_started_at"])

            self.processing = True
            c1_obj["flipped"] = True
            c2_obj["flipped"] = True
            self.cv.notify_all()

            is_match = c1_obj["symbol"] == c2_obj["symbol"]
            threading.Thread(
                target=self._delayed_cleanup,
                args=(is_match, r1, c1, r2, c2, p_id),
                daemon=True,
            ).start()

            return memory_pb2.MoveReply(
                valid=True,
                message="¡Pareja encontrada!" if is_match else "No coinciden.",
                match=is_match,
            )

    def _delayed_cleanup(self, is_match, r1, c1, r2, c2, p_id):
        time.sleep(2.0)
        with self.lock:
            c1_obj = self.board[r1][c1]
            c2_obj = self.board[r2][c2]
            if is_match:
                c1_obj["matched"] = True
                c2_obj["matched"] = True
                p = self.players[p_id]
                p["score"] += 1
                p["score_this_round"] += 1
            c1_obj["flipped"] = False
            c2_obj["flipped"] = False
            self.processing = False

            total_matched = sum(1 for row in self.board for c in row if c["matched"])
            if total_matched == self.size * self.size:
                # Guardar ronda en SQLite (en hilo aparte para no bloquear)
                rnd = self.round
                players_snap = {pid: dict(d) for pid, d in self.players.items()}
                threading.Thread(
                    target=db_save_round,
                    args=(self.room_id, rnd, self.size, players_snap),
                    daemon=True,
                ).start()

                if self.round >= self.max_rounds:
                    self.status = "FINISHED"
                    _log(f"¡Todas las rondas completadas!", self.room_id)
                else:
                    _log(f"Ronda {rnd} completada. Siguiente en 3 s…", self.room_id)
                    # Pausar entre rondas
                    threading.Thread(target=self._next_round_delayed, daemon=True).start()
            else:
                if not is_match:
                    self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
                next_pid = self.turn_order[self.current_turn_idx]
                self.players[next_pid]["turn_started_at"] = time.time()
            self.cv.notify_all()

    def _next_round_delayed(self):
        """Espera 3 s mostrando ROUND_OVER, luego reinicia."""
        self.status = "ROUND_OVER"
        self.cv.acquire()
        self.cv.notify_all()
        self.cv.release()
        time.sleep(3.0)
        with self.lock:
            self._start_next_round()
            self.cv.notify_all()

    # ── Stats de la sala actual ────────────────────────────────────
    def get_stats(self) -> memory_pb2.StatsResponse:
        with self.lock:
            rankings = []
            for d in self.players.values():
                rt = d["response_times"]
                avg = round(sum(rt) / len(rt), 3) if rt else 0.0
                rankings.append(memory_pb2.PlayerStats(
                    name=d["name"],
                    score=d["score"],
                    total_moves=d["total_moves"],
                    avg_response_time=avg,
                ))
            rankings.sort(key=lambda x: x.score, reverse=True)
            return memory_pb2.StatsResponse(rankings=rankings)


# ══════════════════════════════════════════════════════════════════
#  MemoryGameServicer – gestiona múltiples salas
# ══════════════════════════════════════════════════════════════════
class MemoryGameServicer(memory_pb2_grpc.MemoryGameServicer):
    def __init__(self):
        self.rooms: dict       = {}
        self.player_room: dict = {}
        self._random_waiting   = None
        self.mgr_lock          = threading.Lock()

    # ── room helpers (llamar CON mgr_lock) ────────────────────────
    def _resolve_room_id(self, requested: str) -> str:
        r = requested.strip()
        return self._matchmaking_room() if r in ("", "random") else r

    def _matchmaking_room(self) -> str:
        if self._random_waiting:
            room = self.rooms.get(self._random_waiting)
            if room and room.status == "WAITING":
                return self._random_waiting
            self._random_waiting = None
        room_id = f"random-{uuid.uuid4().hex[:6]}"
        self._random_waiting = room_id
        return room_id

    def _ensure_room(self, room_id: str) -> GameRoom:
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom(room_id)
        return self.rooms[room_id]

    # ── gRPC: JoinGame ────────────────────────────────────────────
    def JoinGame(self, request, context):
        with self.mgr_lock:
            room_id = self._resolve_room_id(request.room_id)
            room    = self._ensure_room(room_id)

        with room.cv:
            if room.status == "FINISHED":
                context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                              f"Sala '{room_id}' ya finalizó.")
                return
            if room.status == "PLAYING":
                context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                              f"Sala '{room_id}' ya está en juego.")
                return
            p_id = room.add_player(request.name)

        with self.mgr_lock:
            self.player_room[p_id] = room_id
            if self._random_waiting == room_id and room.status != "WAITING":
                self._random_waiting = None

        _log(f"JoinGame OK → {p_id} en sala {room_id}")
        return memory_pb2.PlayerResponse(
            player_id=p_id,
            board_size=room.size,
            room_id=room_id,
        )

    # ── gRPC: SubscribeToUpdates ───────────────────────────────────
    def SubscribeToUpdates(self, request, context):
        room_id = request.room_id
        room    = None
        deadline = time.time() + 10
        while time.time() < deadline:
            with self.mgr_lock:
                room = self.rooms.get(room_id)
            if room:
                break
            time.sleep(0.1)
        if not room:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Sala '{room_id}' no encontrada.")
            return

        while context.is_active():
            with room.cv:
                room.cv.wait(timeout=1.0)
                state = room.get_state_msg()
            yield state

    # ── gRPC: SelectCard ─────────────────────────────────────────
    def SelectCard(self, request, context):
        with self.mgr_lock:
            room_id = self.player_room.get(request.player_id)
            room    = self.rooms.get(room_id) if room_id else None
        if not room:
            return memory_pb2.SelectReply(valid=False, message="Sala no encontrada.")
        ok, msg = room.select_card(request.player_id, request.r, request.c)
        return memory_pb2.SelectReply(valid=ok, message=msg)

    # ── gRPC: PlayTurn ────────────────────────────────────────────
    def PlayTurn(self, request, context):
        with self.mgr_lock:
            room_id = self.player_room.get(request.player_id)
            room    = self.rooms.get(room_id) if room_id else None
        if not room:
            return memory_pb2.MoveReply(valid=False, message="Sala no encontrada.")
        return room.play_turn(
            request.player_id,
            request.r1, request.c1,
            request.r2, request.c2,
        )

    # ── gRPC: GetStatistics ───────────────────────────────────────
    def GetStatistics(self, request, context):
        with self.mgr_lock:
            room = self.rooms.get(request.room_id)
        if not room:
            return memory_pb2.StatsResponse(rankings=[])
        return room.get_stats()

    # ── gRPC: GetRanking (SQLite global) ─────────────────────────
    def GetRanking(self, request, context):
        rows = db_get_ranking()
        entries = [
            memory_pb2.RankingEntry(
                player_name=r[0],
                total_score=int(r[1]),
                rounds_played=int(r[2]),
                total_moves=int(r[3]),
                avg_response_time=float(r[4]),
            )
            for r in rows
        ]
        return memory_pb2.RankingResponse(entries=entries)

    # ── gRPC: ListRooms ───────────────────────────────────────────
    def ListRooms(self, request, context):
        with self.mgr_lock:
            snapshot = list(self.rooms.items())
        rooms = [
            memory_pb2.RoomInfo(
                room_id=rid,
                status=r.status,
                player_count=len(r.players),
            )
            for rid, r in snapshot
            if r.status not in ("FINISHED",)
        ]
        return memory_pb2.RoomListResponse(rooms=rooms)


# ══════════════════════════════════════════════════════════════════
def serve():
    _db()   # inicializar SQLite al arrancar
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    memory_pb2_grpc.add_MemoryGameServicer_to_server(MemoryGameServicer(), server)
    port = int(os.environ.get("GRPC_PORT", 50054))
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    _log(f"Servidor escuchando en :{port} ({MAX_ROUNDS} rondas por sala)")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
