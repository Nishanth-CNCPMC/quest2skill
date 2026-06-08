# Quest2Skill ROS Bridge Workspace

This repository contains the ROS-side tooling for the Quest 3 to Isaac Sim pipeline.

The current active bridge is:

```bash
cd mqtt_bridge
./quest_tcp_to_ros.py
```

It listens for newline-delimited Quest JSON over TCP on port `5005` and publishes ROS 2 topics under `/quest`.

For the full project summary, see:

`QUEST_TO_ISAAC_WORK_SUMMARY.md`

Related source locations on the development machine:

- Unity Quest TCP app: `/home/ubuntu/QuestTcpOnly`
- Isaac Sim extension: `/home/ubuntu/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64/extsUser/isaacsim.quest_2_skill_isaac`
