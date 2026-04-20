# 🧠 Juego de Memoria Distribuido — gRPC

> **A10 · Sistemas en Red** | Práctica 3

Juego de memoria multiplayer en tiempo real con arquitectura cliente-servidor distribuida sobre **gRPC**. Múltiples partidas corren simultáneamente en salas independientes. El host de cada sala configura el tablero desde la UI. Los resultados se persisten en SQLite con datos de entrenamiento para IA.

---

## Características

| Característica | Detalle |
|---|---|
| **Multisala** | Múltiples partidas concurrentes; cada sala es totalmente independiente |
| **Host configura la sala** | El primer jugador elige tamaño de tablero, nº de jugadores y nº de rondas desde la UI antes de que empiece la partida |
| **Matchmaking** | Unirse a sala aleatoria o por nombre |
| **Múltiples rondas** | N rondas por sala (1–10); scores acumulados entre rondas |
| **Primera carta visible** | `SelectCard` RPC revela el símbolo de la primera carta a todos los jugadores en tiempo real |
| **Streaming en tiempo real** | `SubscribeToUpdates` server-stream + SSE desde Flask al browser |
| **Ranking global** | Historial all-time en SQLite; consulta desde la pestaña Ranking de la UI |
| **Datos de entrenamiento IA** | Cada movimiento se guarda con snapshot del tablero, tiempos de respuesta y contexto para ML |
| **Cliente web** | SPA dark con animaciones 3D, emojis SVG (Twemoji), responsive |
| **Docker** | Imagen única para server y web; `docker-compose` con healthcheck |

---

## Estructura del proyecto

```
practica-03/
├── proto/
│   └── memory.proto           # 8 RPCs del servicio gRPC
├── server/
│   ├── memory_server.py       # Servidor gRPC — GameRoom, multi-sala, SQLite
│   ├── memory_pb2.py          # (generado) clases de mensajes
│   └── memory_pb2_grpc.py     # (generado) servicer y stubs
├── client/
│   ├── memory_client.py       # Cliente de consola
│   ├── memory_pb2.py          # (generado)
│   └── memory_pb2_grpc.py     # (generado)
├── web_client/
│   ├── app.py                 # Proxy Flask (REST/SSE ↔ gRPC)
│   └── templates/
│       └── index.html         # SPA del juego
├── data/                      # ranking.db — gitignored, montado como volumen
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── start_server.sh            # Script de inicio del servidor (auto-compila proto)
├── start_web.sh               # Script de inicio del cliente web (auto-compila proto)
└── .gitignore
```

---

## Servicios gRPC (`memory.proto`)

| RPC | Tipo | Descripción |
|-----|------|-------------|
| `JoinGame` | Unary | Une un jugador a una sala; devuelve `is_host=true` si es el primero |
| `ConfigureGame` | Unary | El host fija `board_size`, `max_players` y `max_rounds`; cambia estado `LOBBY → WAITING` |
| `SelectCard` | Unary | Voltea la primera carta del turno; el símbolo se emite a todos por stream |
| `PlayTurn` | Unary | Completa el turno con coordenadas de la segunda carta |
| `SubscribeToUpdates` | Server-stream | Stream continuo del `GameState` (tablero, scores, turno, ronda) |
| `GetStatistics` | Unary | Estadísticas de la sala actual |
| `ListRooms` | Unary | Lista de salas activas con `status` y `player_count` |
| `GetRanking` | Unary | Ranking global histórico desde SQLite |

### Ciclo de estados de una sala

```
LOBBY → (host llama ConfigureGame) → WAITING → (se completan los jugadores) → PLAYING
  → (fin de ronda) → ROUND_OVER → PLAYING → … → FINISHED
```

---

## Requisitos

- Python 3.9+
- pip3 / pip

```bash
pip3 install -r requirements.txt
```

`requirements.txt`:
```
grpcio==1.80.0
grpcio-tools==1.80.0
flask==3.1.3
```

---

## Ejecución local

### Opción A — Scripts automáticos (recomendado)

Los scripts comprueban si los archivos `_pb2.py` están desactualizados y recompilan el `.proto` automáticamente.

```bash
# Terminal 1 — servidor gRPC
./start_server.sh                  # defaults: 3 rondas, puerto 50054
./start_server.sh 5                # 5 rondas por defecto
./start_server.sh 3 50055          # rondas y puerto personalizados

# Terminal 2 — cliente web
./start_web.sh                     # puerto 8081
./start_web.sh 8082                # puerto personalizado
```

Luego abre **http://localhost:8081** (una pestaña por jugador).

---

### Opción B — Manual paso a paso

**1. Compilar el `.proto`**

> Los archivos `_pb2.py` no están en el repositorio. Este paso es obligatorio.

```bash
python3 -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=server \
  --grpc_python_out=server \
  proto/memory.proto

python3 -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=client \
  --grpc_python_out=client \
  proto/memory.proto
```

**2. Iniciar el servidor gRPC**

```bash
MAX_ROUNDS=3 GRPC_PORT=50054 python3 server/memory_server.py
```

Salida esperada:
```
[SERVER] 12:00:00 SQLite abierto → …/data/ranking.db
[SERVER] 12:00:00 Servidor escuchando en :50054 (3 rondas por sala)
```

**Variables de entorno del servidor:**

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GRPC_PORT` | `50054` | Puerto gRPC |
| `MAX_ROUNDS` | `3` | Rondas por sala (fallback; el host puede sobrescribir desde la UI) |
| `DATA_DIR` | `../data` | Directorio donde se crea `ranking.db` |

**3. Iniciar el cliente web**

```bash
WEB_PORT=8081 python3 web_client/app.py
```

**4. Cliente de consola (alternativo)**

```bash
python3 client/memory_client.py
```

---

## Ejecución con Docker

```bash
cd practica-03
docker compose up --build
```

| Servicio | Endpoint |
|----------|----------|
| Servidor gRPC | `localhost:50054` |
| Cliente web | **http://localhost:8080** |

Para lanzar clientes de consola interactivos en el mismo stack:

```bash
docker compose run --rm player1
docker compose run --rm player2
```

El `Dockerfile` compila el `.proto` durante el build, por lo que no se necesita tener `grpcio-tools` instalado localmente.

---

## Cómo jugar (cliente web)

1. **Ingresa** tu nombre y la IP del servidor gRPC (default `localhost:50054`)
2. **Elige** sala — 🎲 Aleatoria (matchmaking) o 🏷️ Específica (nombre de sala)
3. **Si eres el host** — aparece el panel de configuración:
   - **Tablero**: tamaño NxN (2–10, paso 2) usando los botones `−` / `+`
   - **Jugadores**: cuántos jugadores se necesitan para empezar (2–8)
   - **Rondas**: número de rondas de la partida (1–10)
   - Presiona **Iniciar partida** — la sala pasa de `LOBBY` a `WAITING`
4. **Los demás jugadores** se unen y ven el tablero en gris mientras esperan al host
5. **Cuando hay suficientes jugadores** la partida comienza automáticamente
6. **Durante tu turno**:
   - Haz clic en la **primera carta** → se voltea y todos la ven (SelectCard)
   - Haz clic en la **segunda carta** → el servidor evalúa el par (PlayTurn)
   - Par correcto → +1 punto y juegas de nuevo
   - Par incorrecto → las cartas se ocultan y pasa el turno
7. **Al finalizar cada ronda** se muestra la puntuación; la siguiente ronda empieza automáticamente
8. **Al finalizar todas las rondas** aparece el resultado final y el **Ranking Global** (all-time desde SQLite)

---

## Concurrencia

- `threading.Condition` (`cv`) por sala — los streams bloquean hasta que hay cambio de estado
- `threading.Lock` (`mgr_lock`) — protege el gestor de salas compartido
- Flag `self.processing` — evita doble-jugada durante el delay de 2 s entre rondas
- El `yield` del stream gRPC ocurre **fuera** del bloque `with cv` para no bloquear el lock
- `PRAGMA journal_mode=WAL` — SQLite en modo WAL para acceso concurrente sin bloqueos

---

## Persistencia — SQLite (`data/ranking.db`)

### Esquema

```
rounds
  id, room_id, round_num, board_size, ended_at

player_results
  id, round_id, player_name, score, total_moves, avg_response_time_s

moves  ← datos de entrenamiento para IA
  id, round_id, move_num, player_name,
  r1, c1, sym1, r2, c2, sym2,
  is_match, response_time_s, matched_before,
  board_state_json,   ← snapshot NxN en el momento del movimiento
  scores_json,        ← scores de todos los jugadores en ese instante
  ts
```

### Consultas útiles

```bash
# Ranking global
sqlite3 data/ranking.db \
  "SELECT player_name, SUM(score) total FROM player_results GROUP BY player_name ORDER BY total DESC;"

# Exportar movimientos para ML
sqlite3 -csv -header data/ranking.db "SELECT * FROM moves;" > moves.csv

# Ver tablas
sqlite3 data/ranking.db ".tables"
```

---

## Arquitectura

```
Browser (tab A)         Browser (tab B)
     │                       │
     │  HTTP / SSE            │  HTTP / SSE
     ▼                       ▼
┌─────────────── Flask (web_client/app.py) :8081 ───────────────┐
│  POST /api/join      POST /api/configure   POST /api/select   │
│  POST /api/play      GET  /api/stream      GET  /api/ranking   │
│  GET  /api/rooms     GET  /api/stats                          │
└───────────────────────────┬───────────────────────────────────┘
                            │  gRPC (streaming + unary)
                            ▼
┌──────────── memory_server.py :50054 ──────────────────────────┐
│  MemoryGameServicer                                           │
│  GameRoomManager  ──► GameRoom × N (una por sala)            │
│  SQLite ──► data/ranking.db                                   │
└───────────────────────────────────────────────────────────────┘
```
