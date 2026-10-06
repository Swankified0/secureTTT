import socket
import threading
import json
import sys

PORT = 5000


def receive_messages(sock):
    buffer = ""

    while True:
        try:
            data = sock.recv(4096)

            if not data:
                print("\nDisconnected from server.")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message:
                    continue

                data = json.loads(message)

                if data["type"] == "assignment":
                    print(f"You are Player {data['player']}")

                elif data["type"] == "start":
                    print("Both players connected. Game can begin!")

                elif data["type"] == "move":
                    print(
                        f"\nPlayer {data['player']} moved to "
                        f"row {data['row']}, column {data['col']}"
                    )

        except ConnectionResetError:
            print("\nConnection lost.")
            break


def main():
    # Default to same computer
    server_ip = "127.0.0.1"

    # Allows:
    # python insecure/client.py 192.168.1.50
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Connecting to {server_ip}:{PORT}...")
    client.connect((server_ip, PORT))

    print("Connected!")

    receiver = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )

    receiver.start()

    while True:
        try:
            row = int(input("Row (1-3): "))
            col = int(input("Column (1-3): "))

            message = {
                "type": "move",
                "player": "UNKNOWN",
                "row": row,
                "col": col
            }

            data = json.dumps(message) + "\n"

            client.sendall(data.encode("utf-8"))

        except (ValueError, KeyboardInterrupt):
            print("\nClosing client.")
            break

    client.close()


if __name__ == "__main__":
    main()