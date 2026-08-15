#!/usr/bin/env python3
"""Publish simulated robot telemetry and respond to start/stop commands."""

import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32MultiArray


class MockRobot(Node):
    def __init__(self):
        super().__init__("mock_robot")
        self._running = False
        self._battery = 100.0
        self._phase = 0.0
        self._last_tick = time.monotonic()

        self._telemetry_publisher = self.create_publisher(
            Float32MultiArray, "/telemetry", 10
        )
        self.create_subscription(Bool, "/cmd_start", self._start_callback, 10)
        self.create_subscription(Bool, "/cmd_stop", self._stop_callback, 10)
        self.create_timer(0.1, self._publish_telemetry)

        self.get_logger().info("Mock robot publishing on /telemetry")

    def _start_callback(self, message: Bool) -> None:
        if message.data:
            self._running = True
            self.get_logger().info("Start command received")

    def _stop_callback(self, message: Bool) -> None:
        if message.data:
            self._running = False
            self.get_logger().info("Stop command received")

    def _publish_telemetry(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now

        if self._running:
            self._battery = max(0.0, self._battery - elapsed * 0.08)
            if self._battery == 0.0:
                self._running = False  # dead battery stops the robot
            self._phase += elapsed * 2.2
            velocity = 0.65 + 0.15 * math.sin(self._phase)
        else:
            velocity = 0.0

        message = Float32MultiArray()
        message.data = [float(self._battery), float(velocity), float(self._running)]
        self._telemetry_publisher.publish(message)


def main() -> None:
    rclpy.init()
    node = MockRobot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
