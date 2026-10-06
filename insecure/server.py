import socket
import threading
import json

try:
    from common.game import move, check_game_status, board, reset_board
except ImportError:
    from common.game import move, check_game_status, board, reset_board

HOST = "0.0.0.0"
PORT = 5555

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
        except (BrokenPipeError, ConnectionResetError):
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

        if not move(player, row, col):
            send_json(players[player], {
                "type": "error",
                "message": "Invalid move position."
            })
            return

        # Tell both clients about the updated board.
        broadcast({
            "type": "board",
            "board": board
        })

        status = check_game_status()

        if status == "winner":
            game_over = True
            broadcast({
                "type": "game_over",
                "result": "winner",
                "winner": player,
                "board": board
            })
            return

        if status == "tie":
            game_over = True
            broadcast({
                "type": "game_over",
                "result": "tie",
                "board": board
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

    except ConnectionResetError:
        print(f"Player {player} disconnected.")

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


def main():
    global current_turn
    global game_over

    reset_board()
    current_turn = "X"
    game_over = False

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(2)

    print(f"Server listening on port {PORT}...")
    print("Waiting for Player X...")

    player_x, address_x = server.accept()
    players["X"] = player_x

    print(f"Player X connected from {address_x}")

    send_json(player_x, {
        "type": "assignment",
        "player": "X"
    })

    print("Waiting for Player O...")

    player_o, address_o = server.accept()
    players["O"] = player_o

    print(f"Player O connected from {address_o}")

    send_json(player_o, {
        "type": "assignment",
        "player": "O"
    })

    print("\nBoth players connected! Starting game...\n")

    broadcast({
        "type": "start",
        "board": board,
        "turn": "X"
    })

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