#!/usr/bin/env bash
# ── Cliente web Flask ─────────────────────────────────────────────
# Uso: ./start_web.sh [WEB_PORT]
#
# Ejemplos:
#   ./start_web.sh        # puerto 8081
#   ./start_web.sh 8080
set -e
cd "$(dirname "$0")"

WEB_PORT=${1:-8081}

echo "╔══════════════════════════════════════╗"
echo "║   🌐  Memoria gRPC — Web client      ║"
echo "╠══════════════════════════════════════╣"
echo "║  Puerto : ${WEB_PORT}"
echo "║  URL    : http://localhost:${WEB_PORT}"
echo "╚══════════════════════════════════════╝"
echo ""

# Compilar proto si los pb2 del client no existen o el proto es más reciente
if [ ! -f client/memory_pb2.py ] || [ proto/memory.proto -nt client/memory_pb2.py ]; then
  echo "→ Compilando proto (client/)..."
  python3 -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=client \
    --grpc_python_out=client \
    proto/memory.proto
  echo "→ pb2 generados."
fi

WEB_PORT=$WEB_PORT python3 web_client/app.py
