from flask import Flask, request, jsonify, render_template, Response
import grpc
import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'client'))
import memory_pb2
import memory_pb2_grpc

app = Flask(__name__)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _stub(host: str, port: int):
    channel = grpc.insecure_channel(f'{host}:{port}')
    return memory_pb2_grpc.MemoryGameStub(channel)

def _validate_port(port) -> int:
    p = int(port)
    if not (1 <= p <= 65535):
        raise ValueError("Puerto fuera de rango")
    return p

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/join', methods=['POST'])
def join():
    data = request.get_json(silent=True) or {}
    host = str(data.get('host', 'localhost'))
    name = str(data.get('name', 'Jugador'))[:30]
    room_id = str(data.get('room_id', ''))[:40]
    try:
        port = _validate_port(data.get('port', 50054))
        stub = _stub(host, port)
        resp = stub.JoinGame(
            memory_pb2.PlayerRequest(name=name, room_id=room_id), timeout=5
        )
        return jsonify({
            'player_id': resp.player_id,
            'board_size': resp.board_size,
            'room_id': resp.room_id,
            'is_host': resp.is_host,
        })
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/configure', methods=['POST'])
def configure():
    data = request.get_json(silent=True) or {}
    host = str(data.get('host', 'localhost'))
    try:
        port        = _validate_port(data.get('port', 50054))
        player_id   = str(data['player_id'])
        board_size  = int(data.get('board_size', 4))
        max_players = int(data.get('max_players', 2))
        max_rounds  = int(data.get('max_rounds', 3))
        stub = _stub(host, port)
        resp = stub.ConfigureGame(
            memory_pb2.ConfigRequest(
                player_id=player_id,
                board_size=board_size,
                max_players=max_players,
                max_rounds=max_rounds,
            ), timeout=5
        )
        return jsonify({'valid': resp.valid, 'message': resp.message})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/select', methods=['POST'])
def select():
    data = request.get_json(silent=True) or {}
    host = str(data.get('host', 'localhost'))
    try:
        port = _validate_port(data.get('port', 50054))
        player_id = str(data['player_id'])
        r = int(data['r'])
        c = int(data['c'])
        stub = _stub(host, port)
        resp = stub.SelectCard(
            memory_pb2.SelectRequest(player_id=player_id, r=r, c=c), timeout=5
        )
        return jsonify({'valid': resp.valid, 'message': resp.message})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/play', methods=['POST'])
def play():
    data = request.get_json(silent=True) or {}
    host = str(data.get('host', 'localhost'))
    try:
        port = _validate_port(data.get('port', 50054))
        player_id = str(data['player_id'])
        r1, c1 = int(data['r1']), int(data['c1'])
        r2, c2 = int(data['r2']), int(data['c2'])
        client_ts  = data.get('client_ts')   # epoch ms enviado por el browser
        lat_red_ms = float(int(time.time() * 1000) - int(client_ts)) if client_ts else 0.0

        stub = _stub(host, port)
        resp = stub.PlayTurn(memory_pb2.MoveRequest(
            player_id=player_id, r1=r1, c1=c1, r2=r2, c2=c2, lat_red_ms=lat_red_ms
        ), timeout=10)
        return jsonify({'valid': resp.valid, 'message': resp.message, 'match': resp.match})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/stream')
def stream():
    host = str(request.args.get('host', 'localhost'))
    player_id = str(request.args.get('player_id', ''))
    room_id = str(request.args.get('room_id', ''))
    try:
        port = _validate_port(request.args.get('port', 50054))
    except ValueError:
        return jsonify({'error': 'Puerto inválido'}), 400

    def generate():
        try:
            stub = _stub(host, port)
            req = memory_pb2.SubscribeRequest(player_id=player_id, room_id=room_id)
            for game_state in stub.SubscribeToUpdates(req):
                board = [
                    {
                        'r': card.r, 'c': card.c,
                        'symbol': card.symbol,
                        'flipped': card.flipped,
                        'matched': card.matched
                    }
                    for card in game_state.board
                ]
                payload = {
                    'board': board,
                    'current_player_id': game_state.current_player_id,
                    'current_player_name': game_state.current_player_name,
                    'status': game_state.status,
                    'scores': dict(game_state.scores),
                    'room_id': game_state.room_id,
                    'round': game_state.round,
                    'max_rounds': game_state.max_rounds,
                    'host_id': game_state.host_id,
                    'max_players': game_state.max_players,
                    'board_size': game_state.board_size,
                }
                yield f"data: {json.dumps(payload)}\n\n"
        except grpc.RpcError as e:
            yield f"data: {json.dumps({'error': e.details()})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/stats')
def stats():
    host = str(request.args.get('host', 'localhost'))
    room_id = str(request.args.get('room_id', ''))
    try:
        port = _validate_port(request.args.get('port', 50054))
        stub = _stub(host, port)
        resp = stub.GetStatistics(memory_pb2.StatsRequest(room_id=room_id), timeout=5)
        rankings = [
            {
                'name': p.name,
                'score': p.score,
                'total_moves': p.total_moves,
                'avg_response_time': round(p.avg_response_time, 2)
            }
            for p in resp.rankings
        ]
        return jsonify({'rankings': rankings})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/ranking')
def ranking():
    host = str(request.args.get('host', 'localhost'))
    try:
        port = _validate_port(request.args.get('port', 50054))
        stub = _stub(host, port)
        resp = stub.GetRanking(memory_pb2.Empty(), timeout=5)
        entries = [
            {
                'player_name':       e.player_name,
                'total_score':       e.total_score,
                'rounds_played':     e.rounds_played,
                'total_moves':       e.total_moves,
                'avg_response_time': round(e.avg_response_time, 2),
            }
            for e in resp.entries
        ]
        return jsonify({'entries': entries})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/rooms')
def rooms():
    host = str(request.args.get('host', 'localhost'))
    try:
        port = _validate_port(request.args.get('port', 50054))
        stub = _stub(host, port)
        resp = stub.ListRooms(memory_pb2.Empty(), timeout=5)
        return jsonify({'rooms': [
            {'room_id': r.room_id, 'status': r.status,
             'player_count': r.player_count, 'max_players': r.max_players}
            for r in resp.rooms
        ]})
    except grpc.RpcError as e:
        return jsonify({'error': e.details()}), 502
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('WEB_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
