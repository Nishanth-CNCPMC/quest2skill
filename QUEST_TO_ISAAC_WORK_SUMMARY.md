# Quest to Isaac Sim Work Summary

This document summarizes the current Quest 3 to Isaac Sim pipeline and the work completed so far.

## High-Level Pipeline

The current stack is:

1. Unity Quest app reads Meta Quest 3 tracking and controller input.
2. Unity sends newline-delimited JSON over TCP.
3. ROS 2 bridge receives TCP and publishes `/quest/...` topics.
4. Isaac Sim extension subscribes to ROS 2 topics and drives USD prims.

MQTT was used earlier, but the active path is now TCP to ROS 2 to Isaac Sim.

## Main Locations

Unity Quest app:

`/home/ubuntu/QuestTcpOnly`

ROS bridge:

`/home/ubuntu/quest2skill/mqtt_bridge/quest_tcp_to_ros.py`

Isaac Sim extension:

`/home/ubuntu/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64/extsUser/isaacsim.quest_2_skill_isaac`

Main Isaac extension module:

`/home/ubuntu/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64/extsUser/isaacsim.quest_2_skill_isaac/isaacsim/quest_2_skill_isaac`

USD file currently loaded by the extension:

`/home/ubuntu/Documents/cube_move_quest/cube.usd`

## Unity Quest TCP App

The Unity app currently reads:

- Head pose and detection state
- Left controller pose and detection state
- Right controller pose and detection state
- Trigger values
- Grip values
- Thumbstick axes
- Thumbstick click/touch
- Trigger button
- Grip button
- Left X/Y buttons
- Left menu button
- Right A/B buttons

Key Unity scripts:

- `QuestInputReader.cs`: reads XR input devices and controls.
- `QuestPosePublisher.cs`: builds the outgoing JSON message.
- `QuestTcpClient.cs`: connects to the TCP bridge and sends one JSON line per update.
- `QuestHud.cs`: in-headset debug HUD.

Important deployment note:

Before sideloading to Quest, `QuestTcpClient.host` must point to the PC LAN IP address. `127.0.0.1` points to the Quest itself after deployment.

## Unity TCP JSON Shape

Unity sends one newline-delimited JSON object. The current shape includes top-level tracking flags and nested device objects:

```json
{
  "app_active": true,
  "head_detected": true,
  "right_detected": true,
  "left_detected": true,
  "origin_set": true,
  "message": "quest tracking active",
  "rel_pos": [0.0, 0.0, 0.0],
  "rel_rot": [0.0, 0.0, 0.0, 1.0],
  "trigger": 0.0,
  "head": {
    "detected": true,
    "has_pose": true,
    "pos": [0.0, 0.0, 0.0],
    "rot": [0.0, 0.0, 0.0, 1.0],
    "has_rel_pose": true,
    "rel_pos": [0.0, 0.0, 0.0],
    "rel_rot": [0.0, 0.0, 0.0, 1.0]
  },
  "left": {
    "detected": true,
    "has_pose": true,
    "pos": [0.0, 0.0, 0.0],
    "rot": [0.0, 0.0, 0.0, 1.0],
    "trigger": 0.0,
    "grip": 0.0,
    "joystick": [0.0, 0.0],
    "primary_button": false,
    "secondary_button": false,
    "trigger_button": false,
    "grip_button": false,
    "menu_button": false,
    "joystick_click": false,
    "joystick_touch": false
  },
  "right": {
    "detected": true,
    "has_pose": true,
    "pos": [0.0, 0.0, 0.0],
    "rot": [0.0, 0.0, 0.0, 1.0],
    "trigger": 0.0,
    "grip": 0.0,
    "joystick": [0.0, 0.0],
    "primary_button": false,
    "secondary_button": false,
    "trigger_button": false,
    "grip_button": false,
    "menu_button": false,
    "joystick_click": false,
    "joystick_touch": false
  }
}
```

The top-level right-controller `rel_pos` and `rel_rot` are retained for backward compatibility, but the active ROS and Isaac path uses the nested `head`, `left`, and `right` device objects.

## ROS 2 Bridge

The active bridge is:

```bash
cd /home/ubuntu/quest2skill/mqtt_bridge
./quest_tcp_to_ros.py
```

It listens on:

```text
0.0.0.0:5005
```

It publishes under:

```text
/quest
```

Current important ROS topics:

```text
/quest/head/detected
/quest/head/pose
/quest/left/detected
/quest/left/grip
/quest/left/grip_button
/quest/left/joystick
/quest/left/joystick_click
/quest/left/joystick_touch
/quest/left/menu_button
/quest/left/pose
/quest/left/trigger
/quest/left/trigger_button
/quest/left/x_button
/quest/left/y_button
/quest/right/a_button
/quest/right/b_button
/quest/right/detected
/quest/right/grip
/quest/right/grip_button
/quest/right/joystick
/quest/right/joystick_click
/quest/right/joystick_touch
/quest/right/pose
/quest/right/trigger
/quest/right/trigger_button
```

Pose topics are `geometry_msgs/msg/PoseStamped`.

Joystick topics are `std_msgs/msg/Float32MultiArray` with two values.

Analog trigger and grip topics are `std_msgs/msg/Float32`.

Button and detected topics are `std_msgs/msg/Bool`.

## Isaac Sim Extension

The Isaac extension is shown in Isaac as:

```text
Quest2Skill Isaac
```

The Python module path remains:

```text
isaacsim.quest_2_skill_isaac
```

The extension is now modularized:

- `extension.py`: UI, ROS state handling, high-level update loop, calibration, locomotion.
- `ros_client.py`: generic ROS 2 subscriber wrapper.
- `constants.py`: topic names, prim paths, speed defaults.
- `transforms.py`: Unity-to-Isaac axis mapping, quaternion helpers, relative pose math.
- `cube_stage.py`: generic USD prim transform and visibility helpers.

## Isaac USD Prim Structure

The target headset rig structure is:

```text
/World/HeadsetRig
/World/HeadsetRig/Headset
/World/HeadsetRig/Headset/Camera
/World/HeadsetRig/Headset/QuestLeftControllerProxy
/World/HeadsetRig/Headset/QuestRightControllerProxy
```

Other active prim:

```text
/Environment
```

## Unity to Isaac Axis Mapping

Unity convention:

```text
+X = right
+Y = up
+Z = forward
```

Isaac convention used here:

```text
+Y = right
+Z = up
-X = forward
```

Position mapping:

```python
isaac = [-unity_z, unity_x, unity_y]
```

Rotation mapping is centralized in `transforms.py`; the axis conversion is not scattered in the extension loop.

## Visibility Behavior

The extension controls visibility this way:

- `/quest/head/detected == false`: hide `/Environment`
- `/quest/head/detected == true`: show `/Environment`
- `/quest/left/detected == false`: hide `/World/HeadsetRig/Headset/QuestLeftControllerProxy`
- `/quest/left/detected == true`: show `/World/HeadsetRig/Headset/QuestLeftControllerProxy`
- `/quest/right/detected == false`: hide `/World/HeadsetRig/Headset/QuestRightControllerProxy`
- `/quest/right/detected == true`: show `/World/HeadsetRig/Headset/QuestRightControllerProxy`

The extension writes only:

- visibility
- translate
- orient

It does not write scale, physics, collision, rigid body settings, or robot-control properties.

## Headset Rig Calibration

Calibration is triggered by:

```text
/quest/right/a_button == true
```

On the rising edge of A:

1. Save the current raw `/quest/head/pose` as `quest_head_origin`.
2. Reset `/World/HeadsetRig` to the authored USD transform stored from the live stage.
3. Reset accumulated joystick locomotion.
4. Set `calibrated = true`.
5. Reset `/World/HeadsetRig/Headset` to local identity.

Before calibration:

- Raw Quest head pose does not drive the headset or camera.
- This prevents the view from jumping unexpectedly.

After calibration:

```text
relative_head_pose = inverse(quest_head_origin) * current_head_pose
```

The relative head pose is converted through Unity-to-Isaac mapping and written locally to:

```text
/World/HeadsetRig/Headset
```

The camera is expected to be a child of `Headset`, so it follows physical head motion.

## Controller Pose Behavior

Controller proxy transforms are still computed relative to the current head pose:

```text
left_relative = inverse(current_head_pose) * current_left_pose
right_relative = inverse(current_head_pose) * current_right_pose
```

Those relative poses are converted through the same Unity-to-Isaac axis mapping and written to the controller proxy child prims under:

```text
/World/HeadsetRig/Headset
```

## Joystick Locomotion

Joystick input moves only:

```text
/World/HeadsetRig
```

It does not directly pitch the camera or overwrite the live headset child motion.

Joystick input is applied only while the matching joystick touch topic is true.

Left joystick:

- `/quest/left/joystick_touch == true` is required.
- Left joystick `X`: strafe left/right.
- Left joystick `Y`: move forward/reverse in the Isaac X-Y ground plane.
- Movement is relative to current rig yaw plus current head yaw.

Right joystick:

- `/quest/right/joystick_touch == true` is required.
- Right joystick `X`: yaw around Isaac Z, with the sign inverted per latest adjustment.
- Right joystick `Y`: move up/down along Isaac Z.

When joystick touch is false:

- Locomotion stops.
- Headset child motion continues after calibration.
- Controller proxy updates continue.

## Current Verification

Local Python compile checks pass:

```bash
python3 -m compileall -q extsUser/isaacsim.quest_2_skill_isaac/isaacsim/quest_2_skill_isaac
```

Full runtime validation must be done inside Isaac Sim because the local shell Python does not cleanly load Isaac's USD `pxr` bindings.

## Known Current GitHub Push Blockers

At the time of writing:

- `/home/ubuntu/QuestTcpOnly` is not a Git repository.
- `/home/ubuntu/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64` is not a Git repository.
- `/home/ubuntu/quest2skill` is a Git repository, but has no commits yet and no remote configured.
- GitHub CLI is installed, but authentication is invalid:

```text
gh auth status
github.com: authentication failed
```

Recommended repository split:

1. `quest-tcp-only`: Unity Quest TCP app.
2. `quest2skill-ros-bridge`: ROS TCP bridge and related ROS tooling.
3. `isaacsim-quest-ros-controller-mapper`: Isaac Sim extension source.

Before pushing, configure GitHub authentication and provide remote URLs or authenticated repository names for each target repository.
