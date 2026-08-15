# Robotics Telemetry Dashboard

A lightweight PyQt5 desktop dashboard for a simulated ROS2 robot. It sends start/stop commands, displays battery and velocity, plots velocity live, and logs every telemetry sample to CSV.

## Requirements

This project targets Ubuntu 24.04 LTS with ROS2 Jazzy. Install ROS2 Jazzy first and make sure `rclpy` and `std_msgs` are available in the sourced ROS environment.

The ROS2 topics are:

- `/telemetry`: `std_msgs/msg/Float32MultiArray`, data is `[battery_percent, velocity_mps, running_as_0_or_1]`
- `/cmd_start`: `std_msgs/msg/Bool`
- `/cmd_stop`: `std_msgs/msg/Bool`

## Install

```bash
cd ~/Desktop/project
sudo apt update
sudo apt install python3-venv python3-pyqt5
python3 -m venv --system-site-packages .venv
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`--system-site-packages` lets the virtual environment use Ubuntu's PyQt5 and ROS2 Python packages. If your ROS2 installation is in a different location, source that installation instead.

## Run

Open two terminals.

Terminal 1, start the mock robot:

```bash
cd ~/Desktop/project
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python -m ros_nodes.mock_robot_node
```

Terminal 2, start the GUI:

```bash
cd ~/Desktop/project
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python main.py
```

Click **Start** to publish a `True` message on `/cmd_start`; velocity will begin changing. Click **Stop** to publish on `/cmd_stop`; velocity returns to zero. The CSV file is written to `data/telemetry.csv`.

## Threading design

The GUI runs on Qt's main thread. `RosWorker` is a `QThread` that owns the ROS2 node and calls `executor.spin_once()` in its background loop. The ROS subscription callback emits Qt signals containing plain telemetry values. Qt delivers those signals to `MainWindow` in the main thread, where labels, the plot, and the CSV logger are updated. This prevents ROS callbacks from touching Qt widgets directly and keeps the interface responsive.

When the window closes, the logger is closed and the worker is asked to stop before the process exits.
