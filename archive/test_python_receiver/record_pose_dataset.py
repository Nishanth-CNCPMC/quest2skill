import json
import socket
import time
from pathlib import Path


HOST = "0.0.0.0"
PORT = 5005
DATASET_DIR = Path("/home/ubuntu/quest2skill/datasets")
OUTPUT_FILE = DATASET_DIR / "pose_log.jsonl"


def to_sample(msg: dict) -> dict:
    return {
        "timestamp": time.time(),
        "right_detected": msg.get("right_detected", False),
        "origin_set": msg.get("origin_set", False),
        "quest_controller_relative_pose": {
            "position": msg.get("rel_pos"),
            "rotation_xyzw": msg.get("rel_rot"),
        },
        "quest_trigger": msg.get("trigger", 0.0),
        "message": msg.get("message"),
        "robot_joint_positions": None,
        "robot_joint_velocities": None,
        "end_effector_pose": None,
        "object_pose": None,
        "target_pose": None,
        "action": None,
        "success": False,
    }


def main() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Recording to {OUTPUT_FILE}")
    print(f"Listening on {HOST}:{PORT}...")

    conn, addr = server.accept()
    print(f"Connected by {addr}")

    buffer = ""
    with conn, open(OUTPUT_FILE, "w", encoding="utf-8") as output:
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
                    sample = to_sample(json.loads(line))
                except Exception as exc:
                    print(f"Bad message: {line}")
                    print(f"Error: {exc}")
                    continue

                output.write(json.dumps(sample) + "\n")
                output.flush()
                print(sample)


if __name__ == "__main__":
    main()
