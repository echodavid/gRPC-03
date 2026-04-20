# 🧠 Juego de Memoria Distribuido — gRPC

> **A10 · Sistemas en Red** | Práctica 3

Juego de memoria multiplayer en tiempo real, arquitectura cliente-servidor distribuida usando **gRPC** como protocolo de comunicación. Varias partidas pueden correr simultáneamente en salas independientes, con ranking persistente en SQLite y cliente web con interfaz gráfica.

---

## Características

- **Multisala** — múltiples partidas concurrentes; cada sala es independiente
- **Matchmaking** — unirse a una partida aleatoria o crear/unirse a una sala nombrada
- **Múltiples rondas** — cada sala corre N rondas (configurable); scores acumulados
- **Streaming en tiempo real** — SSE (Server-Sent Events) desde Flask hacia el browser; el estado del tablero se sincroniza en todos los clientes vía `SubscribeToUpdates`
- **Primera carta visible** — al seleccionar la primera carta, el servidor la revela a todos los jugadores (`SelectCard` RPC) antes de terminar el turno
- **Ranking global** — historial persistente en SQLite (`data/ranking.db`); consulta desde la UI
- **Cliente web** — interfaz dark con animaciones 3D, emojis SVG (Twemoji), responsive
- **Docker** — imagen única para servidor y cliente; `docker-compose` para despliegue completo

---

## Estructura

```
practica-03/
├── proto/
│   └── memory.proto          # Definición del servicio gRPC
├── server/
│   ├── memory_server.py      # Servidor gRPC (GameRoom + multi-sala + SQLite)
│   ├── memory_pb2.py         # Generado por protoc
│   └── memory_pb2_grpc.py    # Generado por protoc
├── client/
│   ├── memory_client.py      # Cliente de consola
│   ├── memory_pb2.py
│   └── memory_pb2_grpc.py
├── web_client/
│   ├── app.py                # Proxy Flask (browser ↔ gRPC) + SSE
│   └── templates/
│       └── index.html        # SPA del juego
├── data/                     # ranking.db (generado en ejecución, gitignored)
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## Servicios gRPC (`memory.proto`)

| RPC | Tipo | Descripción |
|-----|------|-------------|
| `JoinGame` | Unary | Une a un jugador a una sala (matchmaking o sala nombrada) |
| `SelectCard` | Unary | Pre-voltea la primera carta; el símbolo se difunde a todos |
| `PlayTurn` | Unary | Completa el turno enviando las coordenadas de ambas cartas |
| `SubscribeToUpdates` | Server-stream | Stream continuo del estado del tablero |
| `GetStatistics` | Unary | Estadísticas de la sala actual |
| `ListRooms` | Unary | Lista de salas activas |
| `GetRanking` | Unary | Ranking global histórico desde SQLite |

---

## Requisitos

- Python 3.9+
- pip3

---

## Instalación y ejecución local (paso a paso)

### 1. Clonar el repositorio

```bash
git clone https://github.com/echodavid/gRCP-03.git
cd gRCP-03
```

### 2. Instalar dependencias Python

```bash
pip3 install grpcio grpcio-tools flask
```

### 3. Compilar el archivo `.proto` (genera los archivos `_pb2.py`)

> Los archivos generados no se incluyen en el repositorio. **Este paso es obligatorio** antes de ejecutar cualquier cosa.

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

Esto genera en `server/` y `client/`:
- `memory_pb2.py` — clases de mensajes
- `memory_pb2_grpc.py` — stubs y servicers gRPC

### 4. Iniciar el servidor gRPC

```bash
python3 server/memory_server.py
```

Salida esperada:
```
[SERVER] HH:MM:SS SQLite abierto → …/data/ranking.db
[SERVER] HH:MM:SS Servidor escuchando en :50054 (3 rondas por sala)
```

Variables de entorno opcionales:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GRPC_PORT` | `50054` | Puerto del servidor gRPC |
| `BOARD_SIZE` | `4` | Tamaño del tablero (4 → 4×4) |
| `MAX_ROUNDS` | `3` | Rondas por sala |
| `DATA_DIR` | `../data` | Directorio para `ranking.db` |

### 5. Iniciar el cliente web

Abre otra terminal:

```bash
WEB_PORT=8081 python3 web_client/app.py
```

Luego abre **http://localhost:8081** en el navegador (una pestaña por jugador).

### 6. Cliente de consola (alternativo al web)

```bash
python3 client/memory_client.py
```

---

## Ejecución con Docker

```bash
cd practica-03
docker compose up --build
```

- Servidor gRPC → `localhost:50054`
- Cliente web → **http://localhost:8080**

Para lanzar clientes de consola interactivos:

```bash
docker compose run --rm player1
docker compose run --rm player2
```

---

## Cómo jugar (web)

1. Ingresa tu nombre y la IP del servidor gRPC
2. Elige **🎲 Aleatoria** (matchmaking) o **🏷️ Específica** (sala por nombre)
3. Espera a que se conecte otro jugador — la partida inicia automáticamente
4. En tu turno, haz clic en **dos cartas**:
   - La primera se voltea inmediatamente (visible para todos)
   - La segunda completa el turno
5. Si forman pareja → ganas 1 punto y juegas de nuevo
6. Al terminar todas las rondas, se muestran los resultados y el ranking global

---

## Concurrencia

- `threading.Condition` (`cv`) como semáforo para el estado de cada sala
- `threading.Lock` (`mgr_lock`) para el gestor de salas
- Flag `processing` para evitar doble-jugada durante el delay de 2 s entre rondas
- `yield state` fuera del bloque `with cv` para no bloquear el lock durante el stream gRPC
- `PRAGMA journal_mode=WAL` en SQLite para acceso concurrente sin bloqueos

---

## Persistencia

Al finalizar cada ronda, los resultados se guardan en `data/ranking.db` (SQLite):

```
rounds          → room_id, round_num, board_size, ended_at
player_results  → round_id, player_name, score, total_moves, avg_response_time
```

El ranking global agrega por nombre de jugador y ordena por `SUM(score)`.
