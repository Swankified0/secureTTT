import socket
import ssl
import threading
import json
from pathlib import Path

HOST = "127.0.0.1"
PORT = 5556
SERVER_NAME = "localhost"
CERT_FILE = Path(__file__).resolve().parent.parent / "certs" / "server.crt"
# Potential future LAN support can make the connection address and certificate path
# configurable, while still verifying the identity in the server certificate.

my_player = None
game_over_event = threading.Event()
both_players_connected = threading.Event()
my_turn_event = threading.Event()

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
                both_players_connected.set()
                my_turn_event.set()
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

                    current_turn = data_json.get("turn", "X")
                    print(f"Current turn: Player {current_turn}")

                    if current_turn == my_player:
                        my_turn_event.set()
                    
                    both_players_connected.set()

                elif msg_type == "board":
                    print_board(data_json["board"])

                elif msg_type == "turn":
                    current_turn = data_json["player"]

                    if current_turn == my_player:
                        my_turn_event.set()
                        print("It is YOUR turn!")

                    else:
                        my_turn_event.clear()
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
                    my_turn_event.set()

                elif msg_type == "error":
                    print(f"\n[Server Error]: {data_json.get('message')}")

        except OSError as error:
            print(f"\nConnection lost: {error}")
            game_over_event.set()
            both_players_connected.set()
            my_turn_event.set()
            break


def main():
    # Trust our local demo certificate, with certificate and name checks enabled.
    try:
        context = ssl.create_default_context(cafile=str(CERT_FILE))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    except (OSError, ssl.SSLError) as error:
        print(f"Could not load the trusted server certificate: {error}")
        print("Run python tools/generate_cert.py from the project root first.")
        return

    print(f"Connecting securely to {HOST}:{PORT}...")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.settimeout(10)
        client.connect((HOST, PORT))
        client = context.wrap_socket(client, server_hostname=SERVER_NAME)
        client.settimeout(None)
    except ssl.SSLCertVerificationError as error:
        print(f"Server certificate verification failed: {error}")
        client.close()
        return
    except OSError as error:
        print(f"Could not establish a TLS connection: {error}")
        print("Make sure the secure server is running on this computer.")
        client.close()
        return

    print(f"TLS connected ({client.version()})! Waiting for another player...")

    receiver = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )
    receiver.start()
    both_players_connected.wait()

    while not (game_over_event.is_set()):
        my_turn_event.wait()

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
            my_turn_event.clear()
            client.sendall(data.encode("utf-8"))

        except (ValueError, KeyboardInterrupt):
            print("\nExiting client.")
            break
        except OSError as error:
            print(f"\nCould not send move: {error}")
            break

    client.close()


if __name__ == "__main__":
    main()
