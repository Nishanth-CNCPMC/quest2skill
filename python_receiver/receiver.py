import json
import socket


HOST = "0.0.0.0"
PORT = 5005


def print_message(msg: dict) -> None:
    right_detected = msg.get("right_detected", False)
    origin_set = msg.get("origin_set", False)

    if not right_detected:
        print(f"Right controller: not detected | origin_set={origin_set} | {msg.get('message', '')}")
        return

    if not origin_set:
        print(f"Right controller: detected | origin_set=false | {msg.get('message', '')}")
        return

    rel_pos = msg["rel_pos"]
    rel_rot = msg["rel_rot"]
    trigger = msg.get("trigger", 0.0)

    print(
        "Right controller relative | "
        f"pos x={rel_pos[0]:.4f}, y={rel_pos[1]:.4f}, z={rel_pos[2]:.4f} | "
        f"rot x={rel_rot[0]:.4f}, y={rel_rot[1]:.4f}, z={rel_rot[2]:.4f}, w={rel_rot[3]:.4f} | "
        f"trigger={trigger:.4f}"
    )


def handle_connection(conn: socket.socket, addr) -> None:
    print(f"Connected by {addr}")
    buffer = ""

    while True:
        data = conn.recv(4096)
        if not data:
            print("Connection closed.")
            return

        buffer += data.decode("utf-8", errors="ignore")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            try:
                print_message(json.loads(line))
            except Exception as exc:
                print(f"Bad message: {line}")
                print(f"Error: {exc}")


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Listening on {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        with conn:
            handle_connection(conn, addr)


if __name__ == "__main__":
    main()
