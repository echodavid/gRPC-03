import grpc
import threading
import os
import sys
import time

# Añadir el directorio actual al path para importar los archivos generados
sys.path.append(os.path.dirname(__file__))
import memory_pb2
import memory_pb2_grpc

class MemoryClient:
    def __init__(self, name, host='localhost'):
        self.name = name
        self.p_id = None
        self.board_size = 0
        self.my_turn = False
        self.last_state = None
        self.lock = threading.Lock()
        
        # Conexión al servidor
        canal = grpc.insecure_channel(f'{host}:50054')
        self.stub = memory_pb2_grpc.MemoryGameStub(canal)

    def listen_updates(self):
        """Hilo para recibir actualizaciones periódicas del servidor"""
        try:
            for state in self.stub.SubscribeToUpdates(memory_pb2.Empty()):
                with self.lock:
                    self.last_state = state
                    self.my_turn = (state.current_player_id == self.p_id)
                self.render_board()
                if state.status == "FINISHED":
                    self.show_results()
                    break
        except grpc.RpcError:
            print("\n❌ Conexión con el servidor perdida.")

    def render_board(self):
        """Dibuja el tablero y el estado del juego en la consola"""
        state = self.last_state
        if not state:
            return
        
        # Limpiar consola
        print("\033c", end="")
        print("="*40)
        print(f" 🧠 JUEGO DE MEMORIA DISTRIBUIDO")
        print("="*40)
        print(f" JUGADOR: {self.name} (ID: {self.p_id})")
        print(f" ESTADO:  {state.status}")
        print(f" TURNO DE: {state.current_player_name}")
        print("-" * 40)
        
        # Reconstruir matriz
        matrix = [["" for _ in range(self.board_size)] for _ in range(self.board_size)]
        for c in state.board:
            matrix[c.r][c.c] = c.symbol
        
        # Dibujar tablero con coordenadas
        print("    " + "  ".join(str(i) for i in range(self.board_size)))
        print("   " + "---" * self.board_size)
        for i, row in enumerate(matrix):
            # Usar padding para que los emojis se alineen bien
            row_str = " | ".join(row)
            print(f"{i} | {row_str} |")
        print("   " + "---" * self.board_size)
        
        print("\n📊 PUNTUACIONES:")
        for player, score in state.scores.items():
            print(f"   • {player:15}: {score} pts")
        
        if self.my_turn and state.status == "PLAYING":
            print("\n👉 ¡ES TU TURNO!")
            print(" Indica coordenadas separadas por espacios (ej. '0 1 2 3'):")
        elif state.status == "WAITING":
            print("\n⏳ Esperando a más jugadores para iniciar...")
        elif state.status == "PLAYING":
            print(f"\n⏳ Esperando a que {state.current_player_name} juegue...")

    def run(self):
        """Punto de entrada del cliente"""
        try:
            # Unirse al juego
            resp = self.stub.JoinGame(memory_pb2.PlayerRequest(name=self.name))
            self.p_id = resp.player_id
            self.board_size = resp.board_size
            
            # Iniciar escucha de actualizaciones en segundo plano
            threading.Thread(target=self.listen_updates, daemon=True).start()
            
            # Bucle principal de entrada de usuario
            while True:
                if self.my_turn:
                    # Usar input bloqueante si es nuestro turno
                    try:
                        line = input("> ")
                        if not line: continue
                        parts = list(map(int, line.split()))
                        if len(parts) != 4:
                            print("❌ Formato inválido. Use: fila1 col1 fila2 col2")
                            continue
                        
                        move_resp = self.stub.PlayTurn(memory_pb2.MoveRequest(
                            player_id=self.p_id, 
                            r1=parts[0], c1=parts[1], 
                            r2=parts[2], c2=parts[3]
                        ))
                        
                        if not move_resp.valid:
                            print(f"❌ {move_resp.message}")
                        else:
                            print(f"✅ {move_resp.message}")
                            self.my_turn = False # Desactivar turno localmente hasta recibir notificación
                    except ValueError:
                        print("❌ Entrada no válida. Use números.")
                    except EOFError:
                        break
                else:
                    # Si no es nuestro turno, solo esperamos
                    time.sleep(0.5)
        except grpc.RpcError as e:
            print(f"❌ No se pudo conectar al servidor: {e.details()}")

    def show_results(self):
        """Muestra las estadísticas finales obtenidas del servidor"""
        print("\n" + "*"*45)
        print("      🏆 RESULTADOS FINALES 🏆")
        print("*"*45)
        
        try:
            stats = self.stub.GetStatistics(memory_pb2.Empty())
            print(f"{'Jugador':<15} | {'Parejas':<7} | {'Movs':<5} | {'Tiempo(s)':<8}")
            print("-" * 45)
            for p in stats.rankings:
                print(f"{p.name:<15} | {p.score:<7} | {p.total_moves:<5} | {p.avg_response_time:<8.2f}")
        except:
            print("No se pudieron recuperar las estadísticas.")
            
        print("*"*45)
        print(" Gracias por jugar. Presiona Ctrl+C para salir.")

if __name__ == '__main__':
    nombre = input("Ingresa tu nombre de jugador: ") or "Jugador-Anon"
    host = os.environ.get("SERVER_HOST", "localhost")
    client = MemoryClient(nombre, host)
    client.run()
