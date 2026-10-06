import socket
import threading
import json

HOST = "0.0.0.0"
PORT = 5000


def send_json(sock, message):
    data = json.dumps(message) + "\n"
    sock.sendall(data.encode("utf-8"))


def relay(source, destination, player):
    """
    Takes anything received from one client and forwards it
    directly to the other client.
    """
    try:
        while True:
            data = source.recv(4096)

            if not data:
                break

            # Intentionally print the raw plaintext traffic.
            # This is the insecure version.
            print(f"[{player} -> OTHER PLAYER] {data.decode('utf-8').strip()}")

            destination.sendall(data)

    except ConnectionResetError:
        print(f"Player {player} disconnected.")

    finally:
        source.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allows the server to restart without waiting for the port.
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(2)

    print(f"Server listening on port {PORT}...")
    print("Waiting for Player X...")

    player_x, address_x = server.accept()
    print(f"Player X connected from {address_x}")

    send_json(player_x, {
        "type": "assignment",
        "player": "X"
    })

    print("Waiting for Player O...")

    player_o, address_o = server.accept()
    print(f"Player O connected from {address_o}")

    send_json(player_o, {
        "type": "assignment",
        "player": "O"
    })

    print("\nBoth players connected!")
    print("Starting communication...\n")

    send_json(player_x, {"type": "start"})
    send_json(player_o, {"type": "start"})

    # X -> O
    x_thread = threading.Thread(
        target=relay,
        args=(player_x, player_o, "X")
    )

    # O -> X
    o_thread = threading.Thread(
        target=relay,
        args=(player_o, player_x, "O")
    )

    x_thread.start()
    o_thread.start()

    x_thread.join()
    o_thread.join()

    server.close()


if __name__ == "__main__":
    main()