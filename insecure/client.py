import socket
import threading
import json
import sys

PORT = 5555

my_player = None
game_over_event = threading.Event()


def print_board(board):
    """Render the 3x3 board in ASCII."""
    print("\n  1   2   3")
    for idx, row in enumerate(board):
        display_row = [cell if cell != "" else " " for cell in row]
        print(f"{idx + 1} " + " | ".join(display_row))
        if idx < 2:
            print(" ---+---+---")
    print()


def receive_messages(sock):
    global my_player
    buffer = ""

    while True:
        try:
            data = sock.recv(4096)

            if not data:
                print("\nDisconnected from server.")
                game_over_event.set()
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message.strip():
                    continue

                data_json = json.loads(message)
                msg_type = data_json.get("type")

                if msg_type == "assignment":
                    my_player = data_json["player"]
                    print(f"\nYou are Player {my_player}")

                elif msg_type == "start":
                    print("\nBoth players connected! Game started.")
                    if "board" in data_json:
                        print_board(data_json["board"])
                    print(f"Current turn: Player {data_json.get('turn', 'X')}")

                elif msg_type == "board":
                    print_board(data_json["board"])

                elif msg_type == "turn":
                    current_turn = data_json["player"]
                    if current_turn == my_player:
                        print("It is YOUR turn!")
                    else:
                        print(f"Waiting for Player {current_turn}...")

                elif msg_type == "game_over":
                    if "board" in data_json:
                        print_board(data_json["board"])

                    result = data_json.get("result")
                    if result == "winner":
                        winner = data_json.get("winner")
                        if winner == my_player:
                            print("=== YOU WIN! ===")
                        else:
                            print(f"=== Player {winner} Wins! ===")
                    elif result == "tie":
                        print("=== GAME OVER: TIE ===")

                    game_over_event.set()

                elif msg_type == "error":
                    print(f"\n[Server Error]: {data_json.get('message')}")

        except ConnectionResetError:
            print("\nConnection lost.")
            game_over_event.set()
            break


def main():
    server_ip = "127.0.0.1"

    if len(sys.argv) > 1:
        server_ip = sys.argv[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Connecting to {server_ip}:{PORT}...")
    try:
        client.connect((server_ip, PORT))
    except ConnectionRefusedError:
        print("Could not connect to the server. Make sure server.py is running.")
        return

    print("Connected! Waiting for another player...")

    receiver = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )
    receiver.start()

    while not game_over_event.is_set():
        try:
            row_str = input("Row (1-3): ")
            if game_over_event.is_set():
                break

            col_str = input("Column (1-3): ")
            if game_over_event.is_set():
                break

            row = int(row_str) - 1
            col = int(col_str) - 1

            if not (0 <= row <= 2 and 0 <= col <= 2):
                print("Coordinates must be between 1 and 3.")
                continue

            message = {
                "type": "move",
                "row": row,
                "col": col
            }

            data = json.dumps(message) + "\n"
            client.sendall(data.encode("utf-8"))

        except (ValueError, KeyboardInterrupt):
            print("\nExiting client.")
            break

    client.close()


if __name__ == "__main__":
    main()