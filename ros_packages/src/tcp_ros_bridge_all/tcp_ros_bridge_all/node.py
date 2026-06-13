#!/usr/bin/env python3
import json
import socket
import time
from typing import Any, Dict, Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Bool, Float32, Float32MultiArray


BUTTON_FIELDS = (
    "trigger_button",
    "grip_button",
    "joystick_click",
    "joystick_touch",
)


class TcpRosBridgeAll(Node):
    def __init__(self) -> None:
        super().__init__("tcp_ros_bridge_all")

        self.declare_parameter("tcp_host", "0.0.0.0")
        self.declare_parameter("tcp_port", 5005)
        self.declare_parameter("topic_prefix", "quest")
        self.declare_parameter("frame_id", "quest_tracking")
        self.declare_parameter("detected_timeout_sec", 0.35)

        self.tcp_host = str(self.get_parameter("tcp_host").value)
        self.tcp_port = int(self.get_parameter("tcp_port").value)
        self.prefix = "/" + str(self.get_parameter("topic_prefix").value).strip("/")
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.detected_timeout_sec = float(self.get_parameter("detected_timeout_sec").value)
        self.detected_state = {
            "head": False,
            "left": False,
            "right": False,
        }
        self.detected_last_update = {
            "head": 0.0,
            "left": 0.0,
            "right": 0.0,
        }
        detected_qos = QoSProfile(depth=1)
        detected_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self.detected_pubs = {
            "head": self.create_publisher(Bool, f"{self.prefix}/head/detected", detected_qos),
            "left": self.create_publisher(Bool, f"{self.prefix}/left/detected", detected_qos),
            "right": self.create_publisher(Bool, f"{self.prefix}/right/detected", detected_qos),
        }
        self.ros_topic_enable_pub = self.create_publisher(Bool, f"{self.prefix}/ros_topic_enable", 10)
        self.detected_timer = self.create_timer(0.1, self._publish_detected_state)
        self.last_ros_enabled_payload: Optional[Dict[str, Any]] = None

        self.pose_pubs = {
            "head": self.create_publisher(PoseStamped, f"{self.prefix}/head/pose", 10),
            "left": self.create_publisher(PoseStamped, f"{self.prefix}/left/pose", 10),
            "right": self.create_publisher(PoseStamped, f"{self.prefix}/right/pose", 10),
        }

        self.trigger_pubs = {
            "left": self.create_publisher(Float32, f"{self.prefix}/left/trigger", 10),
            "right": self.create_publisher(Float32, f"{self.prefix}/right/trigger", 10),
        }
        self.grip_pubs = {
            "left": self.create_publisher(Float32, f"{self.prefix}/left/grip", 10),
            "right": self.create_publisher(Float32, f"{self.prefix}/right/grip", 10),
        }
        self.joystick_pubs = {
            "left": self.create_publisher(Float32MultiArray, f"{self.prefix}/left/joystick", 10),
            "right": self.create_publisher(Float32MultiArray, f"{self.prefix}/right/joystick", 10),
        }
        self.button_pubs = {
            "left": self._make_button_publishers("left"),
            "right": self._make_button_publishers("right"),
        }
        self.active_conn: Optional[socket.socket] = None
        self.haptic_subs = [
            self.create_subscription(Bool, "/haptic_click_left", lambda msg: self._handle_haptic("left", msg), 10),
            self.create_subscription(Bool, "/haptic_click_right", lambda msg: self._handle_haptic("right", msg), 10),
        ]

    def spin_tcp(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.tcp_host, self.tcp_port))
            server.listen(1)
            server.settimeout(0.5)
            self.get_logger().info(f"TCP listening on {self.tcp_host}:{self.tcp_port}")
            self.get_logger().info(f"ROS publishing under {self.prefix}")

            while rclpy.ok():
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    rclpy.spin_once(self, timeout_sec=0.0)
                    continue

                self.get_logger().info(f"Quest connected from {addr[0]}:{addr[1]}")
                with conn:
                    self.active_conn = conn
                    self._handle_connection(conn)
                    self.active_conn = None
                self._set_all_detected(False)
                self.get_logger().info("Quest connection closed")

    def _handle_connection(self, conn: socket.socket) -> None:
        buffer = ""
        conn.settimeout(0.5)

        while rclpy.ok():
            try:
                data = conn.recv(4096)
            except socket.timeout:
                rclpy.spin_once(self, timeout_sec=0.0)
                continue

            if not data:
                return

            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    self._handle_line(line)

            rclpy.spin_once(self, timeout_sec=0.0)

    def _handle_line(self, line: str) -> None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"Skipping invalid JSON: {exc}")
            return

        if not isinstance(payload, dict):
            self.get_logger().warn("Skipping payload because JSON root is not an object")
            return

        try:
            self._publish_payload(payload)
        except (TypeError, ValueError, IndexError) as exc:
            self.get_logger().warn(f"Skipping malformed payload: {exc}")

    def _publish_payload(self, payload: Dict[str, Any]) -> None:
        ros_topic_enable = self._to_bool(payload.get("ros_topic_enable", True))
        self.ros_topic_enable_pub.publish(Bool(data=ros_topic_enable))

        if ros_topic_enable:
            self.last_ros_enabled_payload = payload
            publish_payload = payload
        else:
            publish_payload = self.last_ros_enabled_payload or payload

        detected = {
            "head": self._detected_value(publish_payload, "head"),
            "left": self._detected_value(publish_payload, "left"),
            "right": self._detected_value(publish_payload, "right"),
        }
        now = time.monotonic()
        for device_name in detected:
            self.detected_last_update[device_name] = now
        self.detected_state.update(detected)
        self._publish_detected_state()

        for device_name in ("head", "left", "right"):
            self._publish_pose(device_name, publish_payload.get(device_name))

        for side in ("left", "right"):
            self._publish_controls(side, publish_payload.get(side))

    def _publish_pose(self, device_name: str, device: Any) -> None:
        if not isinstance(device, dict):
            return
        if not self._to_bool(device.get("detected", False)):
            return
        if not self._to_bool(device.get("has_pose", False)):
            return

        pos = device.get("pos")
        rot = device.get("rot")
        if not self._valid_vector(pos, 3) or not self._valid_vector(rot, 4):
            self.get_logger().warn(f"Invalid {device_name} pose payload")
            return

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.pose.position.x = float(pos[0])
        msg.pose.position.y = float(pos[1])
        msg.pose.position.z = float(pos[2])
        msg.pose.orientation.x = float(rot[0])
        msg.pose.orientation.y = float(rot[1])
        msg.pose.orientation.z = float(rot[2])
        msg.pose.orientation.w = float(rot[3])
        self.pose_pubs[device_name].publish(msg)

    def _publish_controls(self, side: str, device: Any) -> None:
        if not isinstance(device, dict):
            device = {}

        self.trigger_pubs[side].publish(Float32(data=float(device.get("trigger", 0.0))))
        self.grip_pubs[side].publish(Float32(data=float(device.get("grip", 0.0))))

        joystick = device.get("joystick", [0.0, 0.0])
        if not self._valid_vector(joystick, 2):
            joystick = [0.0, 0.0]
        joy_msg = Float32MultiArray()
        joy_msg.data = [float(joystick[0]), float(joystick[1])]
        self.joystick_pubs[side].publish(joy_msg)

        for button_name, publisher in self.button_pubs[side].items():
            publisher.publish(Bool(data=self._button_value(side, device, button_name)))

    def _handle_haptic(self, side: str, msg: Bool) -> None:
        if not self._to_bool(msg.data):
            return

        command = {
            "type": "haptic",
            "side": side,
            "duration_ms": 35,
            "amplitude": 0.25,
        }
        self._send_tcp_command(command)

    def _send_tcp_command(self, command: Dict[str, Any]) -> None:
        conn = self.active_conn
        if conn is None:
            return

        try:
            conn.sendall((json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8"))
        except OSError as exc:
            self.get_logger().warn(f"Failed to send TCP command to Quest: {exc}")

    def _make_button_publishers(self, side: str) -> Dict[str, Any]:
        pubs = {
            name: self.create_publisher(Bool, f"{self.prefix}/{side}/{name}", 10)
            for name in BUTTON_FIELDS
        }

        if side == "right":
            pubs["a_button"] = self.create_publisher(Bool, f"{self.prefix}/right/a_button", 10)
            pubs["b_button"] = self.create_publisher(Bool, f"{self.prefix}/right/b_button", 10)
        else:
            pubs["menu_button"] = self.create_publisher(Bool, f"{self.prefix}/left/menu_button", 10)
            pubs["x_button"] = self.create_publisher(Bool, f"{self.prefix}/left/x_button", 10)
            pubs["y_button"] = self.create_publisher(Bool, f"{self.prefix}/left/y_button", 10)

        return pubs

    def _set_all_detected(self, value: bool) -> None:
        for device_name in self.detected_state:
            self.detected_state[device_name] = value
        self._publish_detected_state()

    def _publish_detected_state(self) -> None:
        now = time.monotonic()
        for device_name, last_update in self.detected_last_update.items():
            if self.detected_state[device_name] and now - last_update > self.detected_timeout_sec:
                self.detected_state[device_name] = False

        for device_name, is_detected in self.detected_state.items():
            self.detected_pubs[device_name].publish(Bool(data=is_detected))

    @staticmethod
    def _button_value(side: str, device: Dict[str, Any], button_name: str) -> bool:
        if side == "right" and button_name == "a_button":
            return TcpRosBridgeAll._to_bool(device.get("primary_button", False))
        if side == "right" and button_name == "b_button":
            return TcpRosBridgeAll._to_bool(device.get("secondary_button", False))
        if side == "left" and button_name == "x_button":
            return TcpRosBridgeAll._to_bool(device.get("primary_button", False))
        if side == "left" and button_name == "y_button":
            return TcpRosBridgeAll._to_bool(device.get("secondary_button", False))
        return TcpRosBridgeAll._to_bool(device.get(button_name, False))

    @staticmethod
    def _detected_value(payload: Dict[str, Any], device_name: str) -> bool:
        top_level_key = f"{device_name}_detected"
        if top_level_key in payload:
            return TcpRosBridgeAll._to_bool(payload.get(top_level_key, False))
        device = payload.get(device_name)
        return isinstance(device, dict) and TcpRosBridgeAll._to_bool(device.get("detected", False))

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return False

    @staticmethod
    def _valid_vector(value: Any, length: int) -> bool:
        return isinstance(value, (list, tuple)) and len(value) == length


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = TcpRosBridgeAll()
    try:
        node.spin_tcp()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
