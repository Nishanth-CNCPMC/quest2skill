#!/usr/bin/env python3
import json
import socket
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, Float32, Float32MultiArray, String


TCP_HOST = "0.0.0.0"
TCP_PORT = 5005
PREFIX = "/quest"
FRAME_ID = "quest_origin"


class QuestTcpToRos:
    def __init__(self):
        rclpy.init(args=None)
        self.node = rclpy.create_node("quest_tcp_to_ros")

        self.raw_pub = self.node.create_publisher(String, f"{PREFIX}/raw", 10)
        self.status_pub = self.node.create_publisher(String, f"{PREFIX}/right/status", 10)
        self.app_active_pub = self.node.create_publisher(Bool, f"{PREFIX}/app_active", 10)
        self.head_detected_pub = self.node.create_publisher(Bool, f"{PREFIX}/head/detected", 10)
        self.left_detected_pub = self.node.create_publisher(Bool, f"{PREFIX}/left/detected", 10)
        self.right_detected_pub = self.node.create_publisher(Bool, f"{PREFIX}/right/detected", 10)
        self.origin_set_pub = self.node.create_publisher(Bool, f"{PREFIX}/right/origin_set", 10)

        self.head_pose_pub = self.node.create_publisher(PoseStamped, f"{PREFIX}/head/pose", 10)
        self.left_pose_pub = self.node.create_publisher(PoseStamped, f"{PREFIX}/left/pose", 10)
        self.right_pose_pub = self.node.create_publisher(PoseStamped, f"{PREFIX}/right/pose", 10)

        self.left_joystick_pub = self.node.create_publisher(Float32MultiArray, f"{PREFIX}/left/joystick", 10)
        self.right_joystick_pub = self.node.create_publisher(Float32MultiArray, f"{PREFIX}/right/joystick", 10)
        self.left_trigger_pub = self.node.create_publisher(Float32, f"{PREFIX}/left/trigger", 10)
        self.right_trigger_pub = self.node.create_publisher(Float32, f"{PREFIX}/right/trigger", 10)
        self.left_grip_pub = self.node.create_publisher(Float32, f"{PREFIX}/left/grip", 10)
        self.right_grip_pub = self.node.create_publisher(Float32, f"{PREFIX}/right/grip", 10)
        self.left_button_pubs = self._button_publishers("left")
        self.right_button_pubs = self._button_publishers("right")

    def spin_tcp(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((TCP_HOST, TCP_PORT))
        server.listen(1)

        print(f"TCP listening on {TCP_HOST}:{TCP_PORT}")
        print(f"ROS publishing under {PREFIX}")

        try:
            while rclpy.ok():
                conn, addr = server.accept()
                print(f"Quest connected from {addr}")
                self._handle_connection(conn)
        finally:
            server.close()
            self.node.destroy_node()
            rclpy.shutdown()

    def _handle_connection(self, conn):
        buffer = ""
        with conn:
            while rclpy.ok():
                data = conn.recv(4096)
                if not data:
                    print("Quest connection closed.")
                    return

                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self._handle_line(line)
                rclpy.spin_once(self.node, timeout_sec=0.0)

    def _handle_line(self, line):
        self.raw_pub.publish(String(data=line))

        try:
            msg = json.loads(line)
            app_active = bool(msg.get("app_active", False))
            head_detected = bool(msg.get("head_detected", self._device_detected(msg.get("head"))))
            left_detected = bool(msg.get("left_detected", self._device_detected(msg.get("left"))))
            right_detected = bool(msg.get("right_detected", False))
            origin_set = bool(msg.get("origin_set", False))

            self.app_active_pub.publish(Bool(data=app_active))
            self.head_detected_pub.publish(Bool(data=head_detected))
            self.left_detected_pub.publish(Bool(data=left_detected))
            self.right_detected_pub.publish(Bool(data=right_detected))
            self.origin_set_pub.publish(Bool(data=origin_set))
            self._publish_status(msg, app_active, right_detected)

            self._publish_device_pose("head", msg.get("head"), self.head_pose_pub)
            self._publish_device_pose("left", msg.get("left"), self.left_pose_pub)
            self._publish_device_pose("right", msg.get("right"), self.right_pose_pub)

            self._publish_controls("left", msg.get("left"))
            self._publish_controls("right", msg.get("right"))
        except Exception as exc:
            self.status_pub.publish(String(data="invalid_pose_payload"))
            print(f"Bad message: {line}")
            print(f"Error: {exc}")

    def _button_publishers(self, side):
        pubs = {
            "primary_button": self.node.create_publisher(Bool, f"{PREFIX}/{side}/primary_button", 10),
            "secondary_button": self.node.create_publisher(Bool, f"{PREFIX}/{side}/secondary_button", 10),
            "trigger_button": self.node.create_publisher(Bool, f"{PREFIX}/{side}/trigger_button", 10),
            "grip_button": self.node.create_publisher(Bool, f"{PREFIX}/{side}/grip_button", 10),
            "menu_button": self.node.create_publisher(Bool, f"{PREFIX}/{side}/menu_button", 10),
            "joystick_click": self.node.create_publisher(Bool, f"{PREFIX}/{side}/joystick_click", 10),
            "joystick_touch": self.node.create_publisher(Bool, f"{PREFIX}/{side}/joystick_touch", 10),
        }
        if side == "left":
            pubs["x_button"] = self.node.create_publisher(Bool, f"{PREFIX}/left/x_button", 10)
            pubs["y_button"] = self.node.create_publisher(Bool, f"{PREFIX}/left/y_button", 10)
        else:
            pubs["a_button"] = self.node.create_publisher(Bool, f"{PREFIX}/right/a_button", 10)
            pubs["b_button"] = self.node.create_publisher(Bool, f"{PREFIX}/right/b_button", 10)
            pubs["meta_button"] = self.node.create_publisher(Bool, f"{PREFIX}/right/meta_button", 10)
        return pubs

    def _publish_status(self, msg, app_active, right_detected):
        if not app_active:
            status = msg.get("message", "head_pose_not_detected")
        elif not right_detected:
            status = "no_controller_detected"
        else:
            status = "detected_origin_set"
        self.status_pub.publish(String(data=str(status)))

    def _publish_device_pose(self, name, device, publisher):
        if not isinstance(device, dict):
            return

        pos = device.get("pos")
        rot = device.get("rot")
        if not self._valid_vector(pos, 3) or not self._valid_vector(rot, 4):
            return

        publisher.publish(self._pose_msg(pos, rot))

    def _publish_controls(self, side, device):
        if not isinstance(device, dict):
            return

        joystick = device.get("joystick", [0.0, 0.0])
        if self._valid_vector(joystick, 2):
            msg = Float32MultiArray()
            msg.data = [float(joystick[0]), float(joystick[1])]
            (self.left_joystick_pub if side == "left" else self.right_joystick_pub).publish(msg)

        trigger = Float32(data=float(device.get("trigger", 0.0)))
        grip = Float32(data=float(device.get("grip", 0.0)))
        if side == "left":
            self.left_trigger_pub.publish(trigger)
            self.left_grip_pub.publish(grip)
            button_pubs = self.left_button_pubs
        else:
            self.right_trigger_pub.publish(trigger)
            self.right_grip_pub.publish(grip)
            button_pubs = self.right_button_pubs

        for name, publisher in button_pubs.items():
            publisher.publish(Bool(data=self._button_value(side, device, name)))

    @staticmethod
    def _button_value(side, device, name):
        if name in ("a_button", "x_button"):
            return bool(device.get("primary_button", False))
        if name in ("b_button", "y_button"):
            return bool(device.get("secondary_button", False))
        if name == "meta_button":
            return bool(device.get("menu_button", False))
        return bool(device.get(name, False))

    def _pose_msg(self, pos, rot):
        msg = PoseStamped()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = FRAME_ID
        msg.pose.position.x = float(pos[0])
        msg.pose.position.y = float(pos[1])
        msg.pose.position.z = float(pos[2])
        msg.pose.orientation.x = float(rot[0])
        msg.pose.orientation.y = float(rot[1])
        msg.pose.orientation.z = float(rot[2])
        msg.pose.orientation.w = float(rot[3])
        return msg

    @staticmethod
    def _valid_vector(value, length):
        return isinstance(value, list) and len(value) == length

    @staticmethod
    def _device_detected(device):
        return isinstance(device, dict) and bool(device.get("detected", False))


def main():
    QuestTcpToRos().spin_tcp()


if __name__ == "__main__":
    main()
