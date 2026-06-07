# tcp_ros_bridge

ROS 2 bridge for the Quest TCP streamer. It listens for newline-delimited JSON on TCP and maps each payload to ROS topics instead of MQTT.

## Current Payload

The current Unity sender is expected to send one JSON object per line:

```json
{
  "right_detected": true,
  "origin_set": true,
  "rel_pos": [0.1, 0.0, 0.2],
  "rel_rot": [0.0, 0.0, 0.0, 1.0],
  "trigger": 0.8
}
```

## Topics

With the default `topic_prefix: quest`, the node publishes:

- `/quest/raw` (`std_msgs/String`): original JSON line for debugging.
- `/quest/right/status` (`std_msgs/String`): controller/origin state.
- `/quest/right/detected` (`std_msgs/Bool`): right controller detected.
- `/quest/right/origin_set` (`std_msgs/Bool`): origin calibration state.
- `/quest/right/pose` (`geometry_msgs/PoseStamped`): relative controller pose.
- `/quest/right/trigger` (`std_msgs/Float32`): trigger value.

## Run

From a ROS 2 workspace that contains this package:

```bash
colcon build --packages-select tcp_ros_bridge
source install/setup.bash
ros2 launch tcp_ros_bridge tcp_ros_bridge.launch.py
```

For local testing with the existing fake sender:

```bash
python3 /home/ubuntu/quest2skill/python_receiver/fake_pose_sender.py
```

## Extend

Add new data types by creating another handler in `tcp_ros_bridge/handlers.py` that implements:

- `create_publishers(context)`
- `handle(payload, context) -> bool`

Then add it to `default_handlers()`. For example, a future `HeadPoseHandler` can publish `/quest/head/pose` without touching the TCP server or the node wiring.
