import json
import math
import socket
import time


HOST = "127.0.0.1"
PORT = 5005


def main() -> None:
    sock = socket.create_connection((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")

    origin_sent = False
    t = 0.0

    with sock:
        while True:
            if not origin_sent:
                msg = {
                    "right_detected": True,
                    "origin_set": False,
                    "message": "controller detected, press A to set origin",
                }
                origin_sent = True
            else:
                msg = {
                    "right_detected": True,
                    "origin_set": True,
                    "rel_pos": [
                        0.1 * math.sin(t),
                        0.0,
                        0.1 * math.cos(t),
                    ],
                    "rel_rot": [0.0, 0.0, 0.0, 1.0],
                    "trigger": 0.8,
                }

            line = json.dumps(msg) + "\n"
            sock.sendall(line.encode("utf-8"))
            print(msg)

            t += 0.05
            time.sleep(1 / 60)


if __name__ == "__main__":
    main()
