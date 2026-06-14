# tcp_ros_bridge_all

ROS 2 bridge for the Isaac Quest contract.

Version `1.2` listens for newline-delimited TCP JSON from the Quest Unity app, publishes raw Unity tracking poses and controller inputs under `/quest`, and relays haptic click requests from Isaac back to the Quest.

## Why This Package Exists

`tcp_ros_bridge_all` is the active ROS 2 bridge for Quest2Skill. It keeps the Quest app simple by accepting one TCP connection, while exposing the data to Isaac through normal ROS topics.

Published topics include head/left/right poses, detected flags, triggers, grips, joysticks, generic trigger/grip/joystick buttons, left menu, and Quest aliases `a_button`, `b_button`, `x_button`, and `y_button`.

It also subscribes to:

- `/haptic_click_left`
- `/haptic_click_right`

When either topic receives `true`, it sends this haptic command back to Unity:

```json
{"type":"haptic","side":"left","duration_ms":35,"amplitude":0.70}
```

## Run

```bash
source /opt/ros/humble/setup.bash
cd ~/quest2skill/ros_packages
colcon build --packages-select tcp_ros_bridge_all
source install/setup.bash
ros2 launch tcp_ros_bridge_all tcp_ros_bridge_all.launch.py
```

Default frame for all pose topics is `quest_tracking`.

## Parameters

- `tcp_host`: default `0.0.0.0`
- `tcp_port`: default `5005`
- `topic_prefix`: default `quest`
- `frame_id`: default `quest_tracking`
- `detected_timeout_sec`: default `0.35`

## Expected TCP Input

The bridge expects one JSON object per line. The Unity app sends top-level state plus nested `head`, `left`, and `right` device objects containing pose and control values.

The bridge respects `ros_topic_enable=false` by keeping the last enabled pose/control payload active while still reporting the ROS topic enable state.
