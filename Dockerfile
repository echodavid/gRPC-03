# Dockerfile común para servidor y cliente
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias
RUN pip install --no-cache-dir grpcio grpcio-tools flask

# Copiar el contenido del proyecto
COPY . .

# Comando por defecto (será sobrescrito en docker-compose)
CMD ["python", "server/memory_server.py"]
