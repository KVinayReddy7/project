"""Simulated robot using the in-process pub/sub bus (no ROS2 required)."""
import math
import time

from simulation.bus import publish, subscribe


class SimMockRobot:
    def __init__(self) -> None:
        self._running = False
        self._battery = 100.0
        self._phase = 0.0
        self._stopped = False
        subscribe("/cmd_start", self._on_start)
        subscribe("/cmd_stop", self._on_stop)

    def _on_start(self, data: bool) -> None:
        self._running = bool(data)

    def _on_stop(self, data: bool) -> None:
        if data:
            self._running = False

    def stop(self) -> None:
        self._stopped = True

    def run(self) -> None:
        last = time.monotonic()
        while not self._stopped:
            time.sleep(0.1)
            now = time.monotonic()
            elapsed = now - last
            last = now
            if self._running:
                self._battery = max(0.0, self._battery - elapsed * 0.08)
                if self._battery == 0.0:
                    self._running = False  # dead battery stops the robot
                self._phase += elapsed * 2.2
                velocity = 1.5 + 1.0 * math.sin(self._phase)
            else:
                velocity = 0.0
            publish("/telemetry", [float(self._battery), float(velocity), self._running])
