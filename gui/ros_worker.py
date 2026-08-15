"""ROS2 worker that bridges asynchronous ROS traffic into the Qt UI thread.

When rclpy is not installed the worker falls back to an in-process simulation
that uses simulation.bus for pub/sub, keeping the same Qt-signal interface.
"""
import time

from PyQt5.QtCore import QThread, pyqtSignal


class RosWorker(QThread):
    """Run rclpy or a simulation in a background thread; emit Qt-safe signals."""

    telemetry_received = pyqtSignal(float, float, bool)
    connection_changed = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node = None
        self._context = None
        self._stop_requested = False
        self._sim_publish = None
        self._sim_robot = None

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        try:
            import rclpy  # noqa: F401 – only checking availability
            self._run_ros2()
        except ImportError:
            self._run_simulation()
        except Exception as exc:
            self.connection_changed.emit(False, "ROS2 unavailable")
            self.error_occurred.emit(str(exc))

    # ------------------------------------------------------------------
    # ROS2 mode
    # ------------------------------------------------------------------

    def _run_ros2(self) -> None:
        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from rclpy.node import Node
        from std_msgs.msg import Bool, Float32MultiArray

        self._context = rclpy.context.Context()
        rclpy.init(context=self._context)

        class DashboardBridge(Node):
            def __init__(bridge_self):
                super().__init__("telemetry_dashboard_bridge")
                bridge_self.create_subscription(
                    Float32MultiArray, "/telemetry", bridge_self._on_telemetry, 10
                )
                bridge_self.start_publisher = bridge_self.create_publisher(
                    Bool, "/cmd_start", 10
                )
                bridge_self.stop_publisher = bridge_self.create_publisher(
                    Bool, "/cmd_stop", 10
                )

            def _on_telemetry(bridge_self, message):
                if len(message.data) < 3:
                    return
                self.telemetry_received.emit(
                    float(message.data[0]),
                    float(message.data[1]),
                    bool(message.data[2]),
                )

        self._node = DashboardBridge()
        executor = SingleThreadedExecutor(context=self._context)
        executor.add_node(self._node)
        self.connection_changed.emit(True, "Connected to ROS2")

        while rclpy.ok(context=self._context) and not self._stop_requested:
            executor.spin_once(timeout_sec=0.1)

        executor.shutdown()
        self._node.destroy_node()
        rclpy.shutdown(context=self._context)

    # ------------------------------------------------------------------
    # Simulation mode (no ROS2)
    # ------------------------------------------------------------------

    def _run_simulation(self) -> None:
        import queue
        import threading
        from simulation.bus import publish, subscribe
        from simulation.mock_robot import SimMockRobot

        self._sim_publish = publish
        self._sim_robot = SimMockRobot()

        # Queue bridges the plain threading.Thread → QThread boundary safely
        _queue: queue.Queue = queue.Queue()
        subscribe("/telemetry", _queue.put)

        robot_thread = threading.Thread(target=self._sim_robot.run, daemon=True)
        robot_thread.start()

        self.connection_changed.emit(True, "Simulation Mode")

        # Emit signals from this QThread, never from the robot thread
        while not self._stop_requested:
            try:
                data = _queue.get(timeout=0.05)
                self.telemetry_received.emit(float(data[0]), float(data[1]), bool(data[2]))
            except queue.Empty:
                pass

        self._sim_robot.stop()
        robot_thread.join(timeout=2.0)

    # ------------------------------------------------------------------
    # Command publishing (works in both modes)
    # ------------------------------------------------------------------

    def publish_start(self) -> None:
        self._publish_command(True)

    def publish_stop(self) -> None:
        self._publish_command(False)

    def _publish_command(self, value: bool) -> None:
        # The topic name encodes the command; payload is always True so callbacks fire
        if self._node is not None:
            from std_msgs.msg import Bool

            message = Bool()
            message.data = True
            publisher = self._node.start_publisher if value else self._node.stop_publisher
            publisher.publish(message)
        elif self._sim_publish is not None:
            topic = "/cmd_start" if value else "/cmd_stop"
            self._sim_publish(topic, True)
        else:
            self.error_occurred.emit("Worker not ready yet.")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def stop(self) -> None:
        self._stop_requested = True
        if self._context is not None:
            try:
                import rclpy

                rclpy.shutdown(context=self._context)
            except Exception:
                pass
        self.wait(3000)
