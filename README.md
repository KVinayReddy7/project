# Robotics Telemetry Dashboard

A desktop GUI built with PyQt5 that connects to a ROS2 node to send commands and visualise live robot telemetry.

## Stack

- Python 3
- PyQt5
- ROS2 Jazzy
- Ubuntu 24.04 LTS

## What it does

- **Start / Stop buttons** publish commands to `/cmd_start` and `/cmd_stop`
- **Status panel** shows connection state, battery %, and velocity in real time
- **Live plots** display velocity and battery level over time
- **CSV logger** saves every telemetry message to `data/telemetry.csv` with timestamps

## ROS2 Topics

| Topic | Type | Direction |
|---|---|---|
| `/telemetry` | `std_msgs/Float32MultiArray` | robot → GUI |
| `/cmd_start` | `std_msgs/Bool` | GUI → robot |
| `/cmd_stop` | `std_msgs/Bool` | GUI → robot |

## How to run

```bash
git clone https://github.com/KVinayReddy7/project.git
cd project
make run
```

`make run` installs all dependencies and launches everything in one shot. You need `sudo` access for the first run.

Once ROS2 is installed, open a second terminal and start the mock robot node:

```bash
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python -m ros_nodes.mock_robot_node
```

## How the threading works

ROS2 and PyQt5 each need their own thread. Mixing them directly causes the UI to freeze or crash.

The solution used here:

1. `RosWorker` is a `QThread` that owns the ROS2 node and runs `executor.spin_once()` in a loop
2. When a `/telemetry` message arrives, the ROS2 callback emits a **Qt signal** with the data values
3. Qt automatically delivers that signal to the main UI thread via a queued connection
4. The main thread updates labels, plots, and writes to CSV — widgets are never touched from the ROS2 thread

This keeps the GUI responsive regardless of how busy the ROS2 side is.