import socket
import ssl
import threading
import json
from pathlib import Path
from common import game
from common.board import print_board

# Local demos only. Potential future LAN support would change this bind address
# and require distributing the public certificate to the other computers.
HOST = "127.0.0.1"
PORT = 5555
CERT_DIR = Path(__file__).resolve().parent.parent / "certs"

players = {}
game_lock = threading.Lock()
current_turn = "X"
game_over = False


def send_json(sock, message):
    """Send one JSON message followed by a newline."""
    data = json.dumps(message) + "\n"
    sock.sendall(data.encode("utf-8"))


def broadcast(message):
    """Send a JSON message to both players."""
    for sock in list(players.values()):
        try:
            send_json(sock, message)
        except OSError:
            pass


def handle_move(player, message):
    global current_turn
    global game_over

    try:
        row = int(message["row"])
        col = int(message["col"])
    except (KeyError, TypeError, ValueError):
        send_json(players[player], {
            "type": "error",
            "message": "Invalid move format."
        })
        return

    with game_lock:
        if game_over:
            send_json(players[player], {
                "type": "error",
                "message": "The game is already over."
            })
            return

        if player != current_turn:
            send_json(players[player], {
                "type": "error",
                "message": "It is not your turn."
            })
            return

        if not game.move(player, row, col):
            send_json(players[player], {
                "type": "error",
                "message": "Invalid move position."
            })
            return

        print_board(game.board)

        # Tell both clients about the updated board.
        broadcast({
            "type": "board",
            "board": game.board
        })

        status = game.check_game_status()

        if status == "winner":
            game_over = True
            broadcast({
                "type": "game_over",
                "result": "winner",
                "winner": player,
                "board": game.board
            })
            return

        if status == "tie":
            game_over = True
            broadcast({
                "type": "game_over",
                "result": "tie",
                "board": game.board
            })
            return

        # Switch turns.
        current_turn = "O" if current_turn == "X" else "X"

        broadcast({
            "type": "turn",
            "player": current_turn
        })


def handle_client(sock, player):
    """Receive and process messages from one player."""
    buffer = ""

    try:
        while True:
            data = sock.recv(4096)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    send_json(sock, {
                        "type": "error",
                        "message": "Invalid JSON."
                    })
                    continue

                print(f"[{player}] {message}")

                if message.get("type") == "move":
                    handle_move(player, message)
                else:
                    send_json(sock, {
                        "type": "error",
                        "message": "Unknown message type."
                    })

    except OSError as error:
        print(f"Player {player} connection closed: {error}")

    finally:
        sock.close()

        with game_lock:
            if player in players:
                del players[player]

            if players and not game_over:
                broadcast({
                    "type": "error",
                    "message": f"Player {player} disconnected."
                })


def accept_secure_player(server, context):
    """Only accept a player after a successful TLS handshake."""
    while True:
        sock, address = server.accept()
        try:
            # Limit the handshake wait, then use normal blocking gameplay.
            sock.settimeout(10)
            sock = context.wrap_socket(sock, server_side=True)
            sock.settimeout(None)
            return sock, address
        except OSError as error:
            print(f"TLS connection from {address} rejected: {error}")
            sock.close()


def main():
    global current_turn
    global game_over

    game.reset_board()
    current_turn = "X"
    game_over = False

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        context.load_cert_chain(
            certfile=str(CERT_DIR / "server.crt"),
            keyfile=str(CERT_DIR / "server.key"),
        )
    except (OSError, ssl.SSLError) as error:
        print(f"Could not load the server certificate and key: {error}")
        print("Run python tools/generate_cert.py from the project root first.")
        return

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(2)

    print(f"TLS server listening on {HOST}:{PORT}...")
    print("Waiting for Player X...")

    player_x, address_x = accept_secure_player(server, context)
    players["X"] = player_x

    print(f"Player X connected from {address_x}")

    send_json(player_x, {
        "type": "assignment",
        "player": "X"
    })

    print("Waiting for Player O...")

    player_o, address_o = accept_secure_player(server, context)
    players["O"] = player_o

    print(f"Player O connected from {address_o}")

    send_json(player_o, {
        "type": "assignment",
        "player": "O"
    })

    print("\nBoth players connected! Starting game...\n")

    broadcast({
        "type": "start",
        "board": game.board,
        "turn": "X"
    })
    print_board(game.board)

    x_thread = threading.Thread(
        target=handle_client,
        args=(player_x, "X")
    )

    o_thread = threading.Thread(
        target=handle_client,
        args=(player_o, "O")
    )

    x_thread.start()
    o_thread.start()

    x_thread.join()
    o_thread.join()

    server.close()


if __name__ == "__main__":
    main()
