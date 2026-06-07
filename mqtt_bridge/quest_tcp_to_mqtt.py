import socket
import json
import time
import paho.mqtt.client as mqtt

TCP_HOST = "0.0.0.0"
TCP_PORT = 5005

MQTT_HOST = "localhost"
MQTT_PORT = 1883

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((TCP_HOST, TCP_PORT))
server.listen(1)

print(f"TCP listening on {TCP_HOST}:{TCP_PORT}")
print(f"MQTT publishing to {MQTT_HOST}:{MQTT_PORT}")

conn, addr = server.accept()
print(f"Quest connected from {addr}")

buffer = ""

while True:
    data = conn.recv(4096)

    if not data:
        print("Quest connection closed.")
        break

    buffer += data.decode("utf-8", errors="ignore")

    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        line = line.strip()

        if not line:
            continue

        # Always publish raw line for debugging
        client.publish("quest/raw", line)

        try:
            msg = json.loads(line)

            right_detected = msg.get("right_detected", False)

            if not right_detected:
                client.publish("quest/right/status", "no_controller_detected")
                print("No right controller detected")
                continue

            origin_set = msg.get("origin_set", False)

            if not origin_set:
                client.publish("quest/right/status", "origin_not_set")
                print(msg.get("message", "Controller detected, origin not set"))
                continue

            rel_pos = msg.get("rel_pos", None)
            rel_rot = msg.get("rel_rot", None)
            trigger = msg.get("trigger", 0.0)

            pose_msg = {
                "timestamp": time.time(),
                "rel_pos": rel_pos,
                "rel_rot": rel_rot,
                "trigger": trigger,
            }

            client.publish("quest/right/status", "detected_origin_set")
            client.publish("quest/right/pose", json.dumps(pose_msg))
            client.publish("quest/right/trigger", str(trigger))

            print(
                f"Right controller | "
                f"rel_pos={rel_pos} | rel_rot={rel_rot} | trigger={trigger}"
            )

        except Exception as e:
            print(f"Bad message: {line}")
            print(f"Error: {e}")

client.loop_stop()
client.disconnect()
