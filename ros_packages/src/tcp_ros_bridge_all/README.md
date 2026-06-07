# tcp_ros_bridge_all

ROS 2 bridge for the Isaac Quest contract. The node listens for newline-delimited TCP JSON and publishes raw Unity tracking poses and controller inputs under `/quest`.

Published topics include head/left/right poses, detected flags, triggers, grips, joysticks, generic trigger/grip/joystick buttons, left menu, and Quest aliases `a_button`, `b_button`, `x_button`, and `y_button`.

Run:

```bash
source /opt/ros/humble/setup.bash
cd ~/quest2skill/ros_packages
colcon build --packages-select tcp_ros_bridge_all
source install/setup.bash
ros2 launch tcp_ros_bridge_all tcp_ros_bridge_all.launch.py
```

Default frame for all pose topics is `quest_tracking`.
