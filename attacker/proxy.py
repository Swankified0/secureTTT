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
        original_row = message.get("row")
        original_col = message.get("col")
        print(
            "\nRead move from plaintext: "
            f"row={format_coordinate(original_row)}, "
            f"column={format_coordinate(original_col)}"
            "\nEnter new coordinates to modify the move, or press Enter to keep the current values."
        )
        message["row"] = prompt_coordinate("row", original_row)
        message["col"] = prompt_coordinate("column", original_col)

        if (message["row"], message["col"]) != (original_row, original_col):
            print(
                "Modified move: "
                f"row {format_coordinate(original_row)} -> "
                f"{format_coordinate(message['row'])}, "
                f"column {format_coordinate(original_col)} -> "
                f"{format_coordinate(message['col'])}"
            )
        else:
            print("Move left unchanged.")

    return message


def format_coordinate(value):
    """Format an internal zero-based coordinate for display."""
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2:
        return str(value + 1)
    return repr(value)


def prompt_coordinate(name, current_value):
    """Prompt for a 1-based board coordinate, preserving the current value on Enter."""
    while True:
        value = input(
            f"Replacement {name}:"
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


def inspect_tls_records(data, buffer, direction):
    """Report one encrypted TLS record without changing the bytes being relayed."""
    buffer.extend(data)

    while len(buffer) >= 5:
        record_length = int.from_bytes(buffer[3:5], byteorder="big")
        record_size = 5 + record_length
        if len(buffer) < record_size:
            break

        content_type = buffer[0]
        payload = bytes(buffer[5:record_size])
        del buffer[:record_size]

        if content_type != 23:
            continue

        print(
            f"\nOpaque TLS application-data record observed "
            f"({direction}, {len(payload)} bytes)."
        )
        print(f"Ciphertext sample: {payload[:16].hex(' ')}")
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            print(
                f"Inspection attempt failed: {type(error).__name__}. "
                "Move contents are not readable or editable."
            )
        else:
            print(
                "Payload superficially parsed as JSON, but it remains "
                "TLS data and will not be modified."
            )


def relay(source, destination, transform, direction):
    buffer = b""
    is_tls = None
    tls_record_buffer = bytearray()

    try:
        while True:
            data = source.recv(4096)
            if not data:
                if is_tls is None:
                    is_tls = (
                        len(buffer) >= 3
                        and buffer[0] in (20, 21, 22, 23)
                        and buffer[1] == 3
                    )
                if buffer and not is_tls:
                    raise ValueError(f"Incomplete JSON packet from {direction}")
                break

            buffer += data
            if is_tls is None:
                if (
                    len(buffer) >= 3
                    and buffer[0] in (20, 21, 22, 23)
                    and buffer[1] == 3
                ):
                    is_tls = True
                    if direction == "client -> server":
                        print(
                            "TLS client detected. The proxy will attempt "
                            "to inspect records and will forward them unchanged."
                        )
                elif len(buffer) >= 3:
                    is_tls = False
                    if direction == "client -> server":
                        print(
                            "Plaintext client detected; move messages "
                            "can be read and modified."
                        )

            if is_tls:
                inspect_tls_records(
                    buffer,
                    tls_record_buffer,
                    direction,
                )
                destination.sendall(buffer)
                buffer = b""
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    inspect_tls_records(
                        data,
                        tls_record_buffer,
                        direction,
                    )
                    destination.sendall(data)
                break

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
    print(f"Client connected from {client_address}; awaiting protocol data.")
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

    print(f"Proxy listening on {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"Forwarding connections to {SERVER_HOST}:{SERVER_PORT}")

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