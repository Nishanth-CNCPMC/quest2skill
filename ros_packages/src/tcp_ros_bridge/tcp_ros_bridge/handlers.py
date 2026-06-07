from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String


Payload = Dict[str, Any]


@dataclass
class BridgeContext:
    node: Node
    topic_prefix: str
    frame_id: str


class PayloadHandler(Protocol):
    def create_publishers(self, context: BridgeContext) -> None:
        ...

    def handle(self, payload: Payload, context: BridgeContext) -> bool:
        ...


class RightControllerHandler:
    """Publishes the current Quest right-controller payload schema."""

    def create_publishers(self, context: BridgeContext) -> None:
        prefix = context.topic_prefix.rstrip("/")
        node = context.node
        self._status_pub = node.create_publisher(String, f"{prefix}/right/status", 10)
        self._detected_pub = node.create_publisher(Bool, f"{prefix}/right/detected", 10)
        self._origin_set_pub = node.create_publisher(Bool, f"{prefix}/right/origin_set", 10)
        self._pose_pub = node.create_publisher(PoseStamped, f"{prefix}/right/pose", 10)
        self._trigger_pub = node.create_publisher(Float32, f"{prefix}/right/trigger", 10)

    def handle(self, payload: Payload, context: BridgeContext) -> bool:
        if not self._looks_like_right_controller(payload):
            return False

        right_detected = bool(payload.get("right_detected", False))
        origin_set = bool(payload.get("origin_set", False))
        trigger = float(payload.get("trigger", 0.0))

        self._detected_pub.publish(Bool(data=right_detected))
        self._origin_set_pub.publish(Bool(data=origin_set))
        self._trigger_pub.publish(Float32(data=trigger))

        if not right_detected:
            self._publish_status("no_controller_detected")
            return True

        if not origin_set:
            self._publish_status(payload.get("message") or "origin_not_set")
            return True

        rel_pos = payload.get("rel_pos")
        rel_rot = payload.get("rel_rot")
        if not self._valid_vector(rel_pos, 3) or not self._valid_vector(rel_rot, 4):
            context.node.get_logger().warn(
                "Skipping right-controller pose: expected rel_pos[3] and rel_rot[4]"
            )
            self._publish_status("invalid_pose_payload")
            return True

        pose = PoseStamped()
        pose.header.stamp = context.node.get_clock().now().to_msg()
        pose.header.frame_id = context.frame_id
        pose.pose.position.x = float(rel_pos[0])
        pose.pose.position.y = float(rel_pos[1])
        pose.pose.position.z = float(rel_pos[2])
        pose.pose.orientation.x = float(rel_rot[0])
        pose.pose.orientation.y = float(rel_rot[1])
        pose.pose.orientation.z = float(rel_rot[2])
        pose.pose.orientation.w = float(rel_rot[3])

        self._pose_pub.publish(pose)
        self._publish_status("detected_origin_set")
        return True

    @staticmethod
    def _looks_like_right_controller(payload: Payload) -> bool:
        return (
            "right_detected" in payload
            or "origin_set" in payload
            or "rel_pos" in payload
            or "rel_rot" in payload
            or "trigger" in payload
        )

    @staticmethod
    def _valid_vector(value: Any, size: int) -> bool:
        return isinstance(value, list) and len(value) == size

    def _publish_status(self, status: str) -> None:
        self._status_pub.publish(String(data=status))


def default_handlers() -> List[PayloadHandler]:
    return [
        RightControllerHandler(),
    ]
