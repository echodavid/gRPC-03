import grpc
from concurrent import futures
import time
import random
import threading
import uuid
import sqlite3
import json
import os
import sys

sys.path.append(os.path.dirname(__file__))
import memory_pb2
import memory_pb2_grpc

BOARD_SIZE  = int(os.environ.get("BOARD_SIZE",  8))
MAX_ROUNDS  = int(os.environ.get("MAX_ROUNDS",  3))

EMOJIS = [
    "🍓","🐶","🍇","⚽","🐱","🍎","🚗","🌟",
    "🍕","🎈","🚀","🎸","🦒","🍩","🌈","🏝️",
    "🦁","🐸","🌺","🍦","🎃","🦋","🐧","🍄",
    "🎯","🏆","🌙","⭐","🎀","🦄","🐢","🍭",
    "🏀","🎵","🌊","🦊","🍋","🎪","🚂","🏄",
    "🌸","🦕","🎭","🍜","🦅","🎨","🌵","🐬",
    "🎺","🍰","🌻","🚁",
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
        # ── rounds: una fila por ronda terminada ──────────────────────────
        conn.execute("""\n            CREATE TABLE IF NOT EXISTS rounds (\n                id          INTEGER PRIMARY KEY AUTOINCREMENT,\n                id_ses      TEXT    NOT NULL DEFAULT '',\n                room_id     TEXT    NOT NULL DEFAULT '',\n                round_num   INTEGER NOT NULL,\n                tam_tab     INTEGER NOT NULL DEFAULT 0,\n                board_size  INTEGER NOT NULL DEFAULT 0,\n                niv_dif     INTEGER NOT NULL DEFAULT 0,\n                started_at  TEXT    NOT NULL DEFAULT '',\n                ended_at    TEXT    NOT NULL DEFAULT '',\n                t_ron_ms    INTEGER NOT NULL DEFAULT 0\n            )\n        """)
        # ── player_results: una fila por jugador por ronda ────────────────
        # Nombres de columnas alineados con la guía de métricas (sección 10)
        conn.execute("""\n            CREATE TABLE IF NOT EXISTS player_results (\n                id          INTEGER PRIMARY KEY AUTOINCREMENT,\n                id_ron      INTEGER NOT NULL REFERENCES rounds(id),\n                id_ses      TEXT    NOT NULL DEFAULT '',\n                id_jug      TEXT    NOT NULL DEFAULT '',\n                player_name TEXT    NOT NULL DEFAULT '',\n                tot_aci     INTEGER NOT NULL DEFAULT 0,\n                total_moves INTEGER NOT NULL DEFAULT 0,\n                t_resp_ms   INTEGER NOT NULL DEFAULT 0,\n                tot_err     INTEGER NOT NULL DEFAULT 0,\n                tasa_aci    REAL    NOT NULL DEFAULT 0.0,\n                tasa_err    REAL    NOT NULL DEFAULT 0.0,\n                racha_aci   INTEGER NOT NULL DEFAULT 0,\n                racha_err   INTEGER NOT NULL DEFAULT 0,\n                rec_par     REAL    NOT NULL DEFAULT 0.0,\n                tot_ayu     INTEGER NOT NULL DEFAULT 0\n            )\n        """)
        # ── moves: un registro por jugada (nivel de evento) ───────────────
        conn.execute("""\n            CREATE TABLE IF NOT EXISTS moves (\n                id               INTEGER PRIMARY KEY AUTOINCREMENT,\n                id_ron           INTEGER NOT NULL REFERENCES rounds(id),\n                id_ses           TEXT    NOT NULL DEFAULT '',\n                id_jug           TEXT    NOT NULL DEFAULT '',\n                player_name      TEXT    NOT NULL DEFAULT '',\n                move_num         INTEGER NOT NULL DEFAULT 0,\n                r1               INTEGER NOT NULL DEFAULT 0,\n                c1               INTEGER NOT NULL DEFAULT 0,\n                sym1             TEXT    NOT NULL DEFAULT '',\n                r2               INTEGER NOT NULL DEFAULT 0,\n                c2               INTEGER NOT NULL DEFAULT 0,\n                sym2             TEXT    NOT NULL DEFAULT '',\n                is_match         INTEGER NOT NULL DEFAULT 0,\n                t_resp_ms        INTEGER NOT NULL DEFAULT 0,\n                matched_before   INTEGER NOT NULL DEFAULT 0,\n                racha_aci        INTEGER NOT NULL DEFAULT 0,\n                racha_err        INTEGER NOT NULL DEFAULT 0,\n                sym1_seen_before INTEGER NOT NULL DEFAULT 0,\n                sym2_seen_before INTEGER NOT NULL DEFAULT 0,\n                tam_tab          INTEGER NOT NULL DEFAULT 0,\n                niv_dif          INTEGER NOT NULL DEFAULT 0,\n                lat_red_ms       REAL    NOT NULL DEFAULT 0.0,\n                board_state_json TEXT    NOT NULL DEFAULT '[]',\n                scores_json      TEXT    NOT NULL DEFAULT '{}',\n                ts               TEXT    NOT NULL DEFAULT ''\n            )\n        """)
        # ── Migraciones: añadir columnas si no existen (DB preexistente) ──
        _migrations = [
            ("rounds",         "id_ses TEXT NOT NULL DEFAULT ''"),
            ("rounds",         "tam_tab INTEGER NOT NULL DEFAULT 0"),
            ("rounds",         "niv_dif INTEGER NOT NULL DEFAULT 0"),
            ("rounds",         "started_at TEXT NOT NULL DEFAULT ''"),
            ("rounds",         "t_ron_ms INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "id_ron INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "id_ses TEXT NOT NULL DEFAULT ''"),
            ("player_results", "id_jug TEXT NOT NULL DEFAULT ''"),
            ("player_results", "tot_aci INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "t_resp_ms INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "tot_err INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "tasa_aci REAL NOT NULL DEFAULT 0.0"),
            ("player_results", "tasa_err REAL NOT NULL DEFAULT 0.0"),
            ("player_results", "racha_aci INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "racha_err INTEGER NOT NULL DEFAULT 0"),
            ("player_results", "rec_par REAL NOT NULL DEFAULT 0.0"),
            ("player_results", "tot_ayu INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "id_jug TEXT NOT NULL DEFAULT ''"),
            ("moves",          "id_ses TEXT NOT NULL DEFAULT ''"),
            ("moves",          "id_ron INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "tam_tab INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "t_resp_ms INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "racha_aci INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "racha_err INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "sym1_seen_before INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "sym2_seen_before INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "niv_dif INTEGER NOT NULL DEFAULT 0"),
            ("moves",          "lat_red_ms REAL NOT NULL DEFAULT 0.0"),
        ]
        for _tbl, _col_def in _migrations:
            try:
                conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN {_col_def}")
            except sqlite3.OperationalError:
                pass  # columna ya existe
        conn.commit()
        _DB_CONN = conn
        _log(f"SQLite abierto → {path}")
        return conn


def db_save_round(room_id: str, round_num: int, board_size: int, players: dict,
                  move_log: list = None, started_at: float = 0.0):
    conn = _db()
    now            = time.time()
    ended_at       = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
    started_at_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started_at)) if started_at else ended_at
    t_ron_ms       = int((now - started_at) * 1000) if started_at else 0
    niv_dif        = board_size   # niv_dif ≡ tam_tab en esta implementación
    with _DB_LOCK:
        cur = conn.execute(
            "INSERT INTO rounds "
            "(id_ses, room_id, round_num, tam_tab, board_size, niv_dif, started_at, ended_at, t_ron_ms) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (room_id, room_id, round_num, board_size, board_size, niv_dif,
             started_at_str, ended_at, t_ron_ms),
        )
        round_id = cur.lastrowid
        for p_id, d in players.items():
            rt           = d["response_times"]
            avg_s        = sum(rt) / len(rt) if rt else 0.0
            t_resp_ms    = int(avg_s * 1000)          # t_resp_ms: milisegundos (guía)
            tot_aci      = d["score_this_round"]       # tot_aci (guía)
            tot_err      = max(0, d["total_moves"] - tot_aci)  # tot_err (guía)
            tasa_aci     = round(tot_aci / d["total_moves"], 4) if d["total_moves"] else 0.0
            tasa_err     = round(1.0 - tasa_aci, 4)   # tasa_err (guía)
            racha_aci    = d.get("racha_aci_max", 0)   # racha_aci: máx aciertos consec. (guía)
            racha_err    = d.get("racha_err_max", 0)   # racha_err: máx errores consec.  (guía)
            # rec_par: proporción de aciertos cuando ambos símbolos ya habían sido vistos
            p_moves      = [m for m in (move_log or []) if m.get("player_name") == d["name"]]
            both_seen    = [m for m in p_moves
                            if m.get("sym1_seen_before") and m.get("sym2_seen_before")]
            rec_par      = round(
                sum(1 for m in both_seen if m["is_match"]) / len(both_seen), 4
            ) if both_seen else 0.0
            conn.execute(
                "INSERT INTO player_results "
                "(id_ron, id_ses, id_jug, player_name, "
                " tot_aci, total_moves, t_resp_ms, tot_err, "
                " tasa_aci, tasa_err, racha_aci, racha_err, rec_par, tot_ayu) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (round_id, room_id, p_id, d["name"],
                 tot_aci, d["total_moves"], t_resp_ms, tot_err,
                 tasa_aci, tasa_err, racha_aci, racha_err, rec_par, 0),
            )
        if move_log:
            conn.executemany(
                "INSERT INTO moves "
                "(id_ron, id_ses, id_jug, player_name, move_num, "
                " r1, c1, sym1, r2, c2, sym2, is_match, "
                " t_resp_ms, matched_before, "
                " racha_aci, racha_err, sym1_seen_before, sym2_seen_before, "
                " tam_tab, niv_dif, lat_red_ms, board_state_json, scores_json, ts) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        round_id, room_id, m.get("id_jug", ""), m["player_name"],
                        m["move_num"],
                        m["r1"], m["c1"], m["sym1"],
                        m["r2"], m["c2"], m["sym2"],
                        1 if m["is_match"] else 0,
                        int(m.get("t_resp_ms", 0)),
                        m["matched_before"],
                        m.get("racha_aci", 0), m.get("racha_err", 0),
                        m.get("sym1_seen_before", 0), m.get("sym2_seen_before", 0),
                        m.get("tam_tab", board_size), m.get("niv_dif", board_size),
                        m.get("lat_red_ms", 0.0),
                        m["board_state_json"], m["scores_json"], m["ts"],
                    )
                    for m in move_log
                ],
            )
        conn.commit()
    _log(f"Ronda {round_num} guardada — {len(move_log or [])} movs, t_ron={t_ron_ms}ms (room={room_id})")


def db_get_ranking(limit: int = 20) -> list:
    conn = _db()
    rows = conn.execute("""
        SELECT player_name,
               SUM(tot_aci)                       AS total_score,
               COUNT(*)                           AS rounds_played,
               SUM(total_moves)                   AS total_moves,
               CAST(AVG(t_resp_ms) AS REAL)        AS avg_rt
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
        self.status     = "LOBBY"   # LOBBY hasta que el host configure
        self.processing = False
        self.host_id    = None      # primer jugador en unirse
        self.max_players = 2        # configurable por el host
        self.configured  = False
        self.pending_first = {}         # player_id -> (r, c) first-card selection
        self._move_log  = []            # list of move dicts for AI training
        self._move_num  = 0             # sequential move counter within round
        self.round_started_at = 0.0     # epoch time when current round started (t_ron_ms)
        self._seen_symbols_round = set()  # símbolos revelados en la ronda actual (rec_par)
        self.lock       = threading.Lock()
        self.cv         = threading.Condition(self.lock)
        self._init_board()
        _log(f"Sala creada. Tablero {size}x{size}, {max_rounds} rondas.", room_id)

    # ── Tablero ────────────────────────────────────────────────────
    def _init_board(self):
        total = self.size * self.size
        num_pairs = total // 2
        pairs = [EMOJIS[i % len(EMOJIS)] for i in range(num_pairs)]
        pool = pairs * 2
        if total % 2 == 1:          # tablero de tamaño impar → carta comodín extra
            pool.append("🃏")
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
            host_id=self.host_id or "",
            max_players=self.max_players,
            board_size=self.size,
        )

    # ── Agregar jugador (llamar CON cv) ────────────────────────────
    def add_player(self, name: str) -> str:
        p_id = f"P-{uuid.uuid4().hex[:4].upper()}"
        self.players[p_id] = {
            "id_jug":           p_id,  # id_jug: identificador anónimo del jugador (guía)
            "name":             name,
            "score":            0,     # acumulado total (todas las rondas)
            "score_this_round": 0,     # tot_aci de la ronda actual (para guardar en DB)
            "total_moves":      0,
            "response_times":   [],    # lista de t_resp_s por movimiento
            "turn_started_at":  0,
            "racha_aci_actual": 0,     # racha_aci corriente en este turno
            "racha_err_actual": 0,     # racha_err corriente en este turno
            "racha_aci_max":    0,     # racha_aci máxima de la ronda (→ DB racha_aci)
            "racha_err_max":    0,     # racha_err máxima de la ronda (→ DB racha_err)
        }
        self.turn_order.append(p_id)
        if not self.host_id:
            self.host_id = p_id   # primer jugador = host
        _log(f"'{name}' ({p_id}) unido. Total: {len(self.players)}", self.room_id)
        if self.configured and len(self.players) >= self.max_players and self.status == "WAITING":
            self._start_next_round()
        self.cv.notify_all()
        return p_id

    def _start_next_round(self):
        """Inicia la siguiente ronda (sin lock — llamar desde contexto ya protegido)."""
        self.round += 1
        self.status = "PLAYING"
        self._init_board()
        self.pending_first.clear()
        self._move_log = []
        self._move_num = 0
        self._seen_symbols_round = set()
        self.round_started_at = time.time()
        for d in self.players.values():
            d["score_this_round"]  = 0
            d["racha_aci_actual"]  = 0
            d["racha_err_actual"]  = 0
            d["racha_aci_max"]     = 0
            d["racha_err_max"]     = 0
        self.current_turn_idx = (self.round - 1) % len(self.turn_order)  # rota quien empieza
        self.players[self.turn_order[self.current_turn_idx]]["turn_started_at"] = time.time()
        _log(f"Ronda {self.round}/{self.max_rounds} iniciada.", self.room_id)

    # ── Configuración por el host ────────────────────────────────────
    def configure_game(self, p_id: str, board_size: int, max_players: int, max_rounds: int):
        with self.lock:
            if self.host_id != p_id:
                return False, "Solo el host puede configurar la partida."
            if self.status not in ("LOBBY",):
                return False, "La sala ya está en curso o ya fue configurada."
            if not (2 <= board_size <= 10):
                return False, "Tamaño de tablero debe ser entre 2 y 10."
            if not (2 <= max_players <= 8):
                return False, "Número de jugadores debe ser entre 2 y 8."
            if not (1 <= max_rounds <= 10):
                return False, "Rondas debe ser entre 1 y 10."
            self.size        = board_size
            self.max_players = max_players
            self.max_rounds  = max_rounds
            self.configured  = True
            self.status      = "WAITING"
            self._init_board()
            _log(f"Configurada: {board_size}x{board_size}, {max_players} jugadores, {max_rounds} rondas.", self.room_id)
            if len(self.players) >= self.max_players:
                self._start_next_round()
            self.cv.notify_all()
            return True, "ok"
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
    def play_turn(self, p_id, r1, c1, r2, c2, lat_red_ms: float = 0.0) -> memory_pb2.MoveReply:
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
            rt = time.time() - player["turn_started_at"] if player["turn_started_at"] > 0 else 0.0
            if player["turn_started_at"] > 0:
                player["response_times"].append(rt)

            # ── Snapshot para entrenamiento de IA (antes de voltear c2) ──
            matched_before   = sum(1 for row in self.board for cell in row if cell["matched"])
            sym1_seen_before = 1 if c1_obj["symbol"] in self._seen_symbols_round else 0
            sym2_seen_before = 1 if c2_obj["symbol"] in self._seen_symbols_round else 0
            board_snap = [
                self.board[rr][cc]["symbol"]
                if (self.board[rr][cc]["matched"] or self.board[rr][cc]["flipped"])
                else "?"
                for rr in range(self.size) for cc in range(self.size)
            ]

            self.processing = True
            c1_obj["flipped"] = True
            c2_obj["flipped"] = True
            self.cv.notify_all()

            is_match = c1_obj["symbol"] == c2_obj["symbol"]

            # ── Actualizar rachas y símbolos vistos ────────────────────
            if is_match:
                player["racha_aci_actual"] += 1
                player["racha_err_actual"]  = 0
            else:
                player["racha_err_actual"] += 1
                player["racha_aci_actual"]  = 0
            player["racha_aci_max"] = max(player["racha_aci_max"], player["racha_aci_actual"])
            player["racha_err_max"] = max(player["racha_err_max"], player["racha_err_actual"])
            self._seen_symbols_round.add(c1_obj["symbol"])
            self._seen_symbols_round.add(c2_obj["symbol"])

            # ── Registrar movimiento (nivel de evento — guía sección 5.1) ───
            self._move_log.append({
                "id_jug":           p_id,                      # id_jug (guía)
                "move_num":         self._move_num,
                "player_name":      player["name"],
                "id_ses":           self.room_id,              # id_ses (guía)
                "r1": r1, "c1": c1, "sym1": c1_obj["symbol"],
                "r2": r2, "c2": c2, "sym2": c2_obj["symbol"],
                "is_match":         is_match,
                "t_resp_ms":        int(rt * 1000),            # t_resp_ms en ms (guía)
                "matched_before":   matched_before,
                "racha_aci":        player["racha_aci_actual"], # racha_aci (guía)
                "racha_err":        player["racha_err_actual"], # racha_err (guía)
                "sym1_seen_before": sym1_seen_before,          # insumo para rec_par
                "sym2_seen_before": sym2_seen_before,
                "tam_tab":          self.size,                  # tam_tab (guía)
                "niv_dif":          self.size,                  # niv_dif (guía)
                "lat_red_ms":       round(lat_red_ms, 3),       # lat_red_ms (guía)
                "board_state_json": json.dumps(board_snap, ensure_ascii=False),
                "scores_json":      json.dumps(
                    {d["name"]: d["score"] for d in self.players.values()},
                    ensure_ascii=False,
                ),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            self._move_num += 1

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
                move_log_snap = list(self._move_log)
                threading.Thread(
                    target=db_save_round,
                    args=(self.room_id, rnd, self.size, players_snap, move_log_snap, self.round_started_at),
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
            is_host=(p_id == room.host_id),
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

    # ── gRPC: ConfigureGame ────────────────────────────────────
    def ConfigureGame(self, request, context):
        with self.mgr_lock:
            room_id = self.player_room.get(request.player_id)
            room    = self.rooms.get(room_id) if room_id else None
        if not room:
            return memory_pb2.ConfigReply(valid=False, message="Sala no encontrada.")
        ok, msg = room.configure_game(
            request.player_id, request.board_size,
            request.max_players, request.max_rounds,
        )
        return memory_pb2.ConfigReply(valid=ok, message=msg)

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
            request.lat_red_ms,
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
                max_players=r.max_players,
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
