import json
from typing import List

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from tcp_ros_bridge.handlers import BridgeContext, PayloadHandler, default_handlers
from tcp_ros_bridge.tcp_server import LineTcpServer


class TcpRosBridgeNode(Node):
    def __init__(self, handlers: List[PayloadHandler] | None = None) -> None:
        super().__init__("tcp_ros_bridge")

        self.declare_parameter("tcp_host", "0.0.0.0")
        self.declare_parameter("tcp_port", 5005)
        self.declare_parameter("topic_prefix", "quest")
        self.declare_parameter("frame_id", "quest_origin")
        self.declare_parameter("publish_raw", True)

        self._host = self.get_parameter("tcp_host").value
        self._port = int(self.get_parameter("tcp_port").value)
        self._publish_raw = bool(self.get_parameter("publish_raw").value)
        self._context = BridgeContext(
            node=self,
            topic_prefix=str(self.get_parameter("topic_prefix").value),
            frame_id=str(self.get_parameter("frame_id").value),
        )

        prefix = self._context.topic_prefix.rstrip("/")
        self._raw_pub = self.create_publisher(String, f"{prefix}/raw", 10)

        self._handlers = handlers or default_handlers()
        for handler in self._handlers:
            handler.create_publishers(self._context)

        self._server = LineTcpServer(
            host=str(self._host),
            port=self._port,
            on_line=self._handle_line,
            on_status=lambda msg: self.get_logger().info(f"TCP {msg}"),
            on_error=lambda exc: self.get_logger().error(f"TCP error: {exc}"),
        )
        self._server.start()

    def destroy_node(self) -> bool:
        self._server.stop()
        return super().destroy_node()

    def _handle_line(self, line: str) -> None:
        if self._publish_raw:
            self._raw_pub.publish(String(data=line))

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f"Skipping invalid JSON: {exc}")
            return

        if not isinstance(payload, dict):
            self.get_logger().warn("Skipping JSON payload because it is not an object")
            return

        handled = False
        for handler in self._handlers:
            handled = handler.handle(payload, self._context) or handled

        if not handled:
            self.get_logger().debug(f"No handler accepted payload keys: {sorted(payload.keys())}")


def main(args: List[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TcpRosBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
