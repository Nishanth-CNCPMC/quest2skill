import json

import paho.mqtt.client as mqtt


MQTT_HOST = "localhost"
MQTT_PORT = 1883


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker")
    client.subscribe("quest/right/status")
    client.subscribe("quest/right/pose")
    client.subscribe("quest/right/trigger")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    if topic == "quest/right/status":
        print(f"[STATUS] {payload}")
    elif topic == "quest/right/trigger":
        print(f"[TRIGGER] {payload}")
    elif topic == "quest/right/pose":
        data = json.loads(payload)
        rel_pos = data["rel_pos"]
        rel_rot = data["rel_rot"]
        trigger = data["trigger"]

        print(
            "[POSE] "
            f"x={rel_pos[0]:.4f}, y={rel_pos[1]:.4f}, z={rel_pos[2]:.4f} | "
            f"qx={rel_rot[0]:.4f}, qy={rel_rot[1]:.4f}, qz={rel_rot[2]:.4f}, qw={rel_rot[3]:.4f} | "
            f"trigger={trigger:.4f}"
        )


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()
