# Dockerfile común para servidor y cliente
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Compilar el .proto dentro de la imagen
RUN python3 -m grpc_tools.protoc \
      --proto_path=proto \
      --python_out=server \
      --grpc_python_out=server \
      proto/memory.proto \
  && python3 -m grpc_tools.protoc \
      --proto_path=proto \
      --python_out=client \
      --grpc_python_out=client \
      proto/memory.proto

# Crear directorio de datos
RUN mkdir -p /app/data

# Comando por defecto (sobrescrito en docker-compose)
CMD ["python3", "server/memory_server.py"]
