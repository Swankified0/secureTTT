import json
import socket
import threading

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 5556
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555

console_input_lock = threading.Lock()


def modify_client_packet(message):
    """Edit a client-to-server JSON message before forwarding it."""
    if message.get("type") != "move":
        return message

    with console_input_lock:
        print("\nPlayer submitted a move. Enter replacement coordinates or press Enter to keep each value.")
        message["row"] = prompt_coordinate("row", message.get("row"))
        message["col"] = prompt_coordinate("column", message.get("col"))

    return message


def prompt_coordinate(name, current_value):
    """Prompt for a 1-based board coordinate, preserving the current value on Enter."""
    if isinstance(current_value, int) and not isinstance(current_value, bool) and 0 <= current_value <= 2:
        current_display = current_value + 1
    else:
        current_display = "unchanged"

    while True:
        value = input(
            f"Replacement {name}: "
        ).strip()
        if not value:
            return current_value

        try:
            coordinate = int(value)
        except ValueError:
            print("Enter a number from 1 to 3, or press Enter to keep the current value.")
            continue

        if 1 <= coordinate <= 3:
            return coordinate - 1

        print("Coordinate must be between 1 and 3.")


def modify_server_packet(message):
    """Edit a server-to-client JSON message before forwarding it."""
    return message


def relay(source, destination, transform, direction):
    buffer = b""

    try:
        while True:
            data = source.recv(4096)
            if not data:
                if buffer:
                    raise ValueError(f"Incomplete JSON packet from {direction}")
                break

            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue

                message = json.loads(line.decode("utf-8"))
                if not isinstance(message, dict):
                    raise ValueError(f"Expected a JSON object from {direction}")

                modified_message = transform(message)
                packet = json.dumps(modified_message) + "\n"
                destination.sendall(packet.encode("utf-8"))

    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, EOFError) as error:
        print(f"Proxy relay error ({direction}): {error}")
        try:
            destination.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
    finally:
        try:
            destination.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle_client(client_socket, client_address):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((SERVER_HOST, SERVER_PORT))
    except OSError as error:
        print(f"Could not connect to game server {SERVER_HOST}:{SERVER_PORT}: {error}")
        client_socket.close()
        server_socket.close()
        return

    print(f"Proxying client {client_address}")
    client_to_server = threading.Thread(
        target=relay,
        args=(client_socket, server_socket, modify_client_packet, "client -> server"),
    )
    server_to_client = threading.Thread(
        target=relay,
        args=(server_socket, client_socket, modify_server_packet, "server -> client"),
    )

    client_to_server.start()
    server_to_client.start()
    client_to_server.join()
    server_to_client.join()
    client_socket.close()
    server_socket.close()
    print(f"Client {client_address} disconnected")


def main():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy.bind((LISTEN_HOST, LISTEN_PORT))
    proxy.listen()

    print(f"Proxy listening on port {LISTEN_PORT}")
    print(f"Forwarding to game server at {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            client_socket, client_address = proxy.accept()
            threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\nStopping proxy.")
    finally:
        proxy.close()


if __name__ == "__main__":
    main()