# Quest2Skill ROS Bridge Workspace

Version `1.2` is the ROS-side bridge workspace for the Quest2Skill VR-to-Isaac workflow.

This repository receives Quest tracking/control data from the Unity Quest app over TCP, publishes it as ROS 2 topics, and relays haptic click requests from Isaac back to the Quest.

## Why This Exists

The Unity app and Isaac extension should not need to know about each other's process details. This ROS bridge is the middle layer:

- Unity sends newline-delimited Quest JSON over TCP.
- The bridge publishes headset/controller poses and controls under `/quest`.
- Isaac subscribes to those topics and drives its headset/controller proxy prims.
- Isaac publishes haptic click requests.
- The bridge sends compact haptic JSON commands back to Unity.

## Release 1.2

- Active package: `tcp_ros_bridge_all`.
- Haptic relay amplitude is `0.70`.
- Haptic click duration is `35 ms`.
- Subscribes to `/haptic_click_left` and `/haptic_click_right`.
- Publishes Quest headset/controller pose, detection, trigger, grip, joystick, and button topics.

## Run

```bash
source /opt/ros/humble/setup.bash
cd ~/quest2skill/ros_packages
colcon build --packages-select tcp_ros_bridge_all
source install/setup.bash
ros2 launch tcp_ros_bridge_all tcp_ros_bridge_all.launch.py
```

The bridge listens for newline-delimited Quest JSON over TCP on port `5005` and publishes ROS 2 topics under `/quest`.

## Important Topics

- `/quest/head/pose`
- `/quest/left/pose`
- `/quest/right/pose`
- `/quest/head/detected`
- `/quest/left/detected`
- `/quest/right/detected`
- `/quest/left/trigger`
- `/quest/right/trigger`
- `/quest/left/grip`
- `/quest/right/grip`
- `/quest/left/joystick`
- `/quest/right/joystick`
- `/haptic_click_left`
- `/haptic_click_right`

For the full project summary, see:

`QUEST_TO_ISAAC_WORK_SUMMARY.md`

Related source locations on the development machine:

- Unity Quest TCP app: `/home/ubuntu/QuestTcpOnly`
- Isaac Sim extension: `/home/ubuntu/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64/extsUser/isaacsim.quest_2_skill_isaac`
