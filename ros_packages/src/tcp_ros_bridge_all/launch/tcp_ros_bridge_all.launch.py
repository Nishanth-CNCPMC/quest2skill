from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    tcp_host = LaunchConfiguration("tcp_host")
    tcp_port = LaunchConfiguration("tcp_port")
    topic_prefix = LaunchConfiguration("topic_prefix")
    frame_id = LaunchConfiguration("frame_id")
    detected_timeout_sec = LaunchConfiguration("detected_timeout_sec")

    return LaunchDescription(
        [
            DeclareLaunchArgument("tcp_host", default_value="0.0.0.0"),
            DeclareLaunchArgument("tcp_port", default_value="5005"),
            DeclareLaunchArgument("topic_prefix", default_value="quest"),
            DeclareLaunchArgument("frame_id", default_value="quest_tracking"),
            DeclareLaunchArgument("detected_timeout_sec", default_value="0.35"),
            Node(
                package="tcp_ros_bridge_all",
                executable="tcp_ros_bridge_all_node",
                name="tcp_ros_bridge_all",
                output="screen",
                parameters=[
                    {
                        "tcp_host": tcp_host,
                        "tcp_port": ParameterValue(tcp_port, value_type=int),
                        "topic_prefix": topic_prefix,
                        "frame_id": frame_id,
                        "detected_timeout_sec": ParameterValue(
                            detected_timeout_sec,
                            value_type=float,
                        ),
                    }
                ],
            ),
        ]
    )
