#!/usr/bin/env bash
# ── Servidor gRPC ─────────────────────────────────────────────────
# El tamaño del tablero, nº de jugadores y rondas los configura
# el HOST desde la interfaz web al crear la sala.
#
# Uso: ./start_server.sh [MAX_ROUNDS_DEFAULT] [GRPC_PORT]
#
# Ejemplos:
#   ./start_server.sh          # defaults: 3 rondas, :50054
#   ./start_server.sh 5        # 5 rondas por defecto
#   ./start_server.sh 3 50055  # puerto personalizado
set -e
cd "$(dirname "$0")"

MAX_ROUNDS=${1:-3}
GRPC_PORT=${2:-50054}

echo "╔══════════════════════════════════════╗"
echo "║   🧠  Memoria gRPC — Servidor        ║"
echo "╠══════════════════════════════════════╣"
echo "║  Rondas (default): ${MAX_ROUNDS}"
echo "║  Puerto           : ${GRPC_PORT}"
echo "║  Tablero          : lo configura el host"
echo "╚══════════════════════════════════════╝"
echo ""

# Compilar proto si los pb2 no existen o el proto es más reciente
if [ ! -f server/memory_pb2.py ] || [ proto/memory.proto -nt server/memory_pb2.py ]; then
  echo "→ Compilando proto..."
  python3 -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=server \
    --grpc_python_out=server \
    proto/memory.proto
  echo "→ pb2 generados."
fi

MAX_ROUNDS=$MAX_ROUNDS GRPC_PORT=$GRPC_PORT python3 server/memory_server.py
