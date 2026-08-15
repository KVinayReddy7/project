"""Main dashboard window."""

from collections import deque
from pathlib import Path

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logging_utils.csv_logger import TelemetryLogger
from gui.ros_worker import RosWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robotics Telemetry Dashboard")
        self.resize(1050, 900)
        self._time_values = deque(maxlen=240)
        self._velocity_values = deque(maxlen=240)
        self._battery_values = deque(maxlen=240)
        self._sample_number = 0
        self._logger = TelemetryLogger(Path(__file__).resolve().parents[1] / "data" / "telemetry.csv")
        self._build_ui()

        self._worker = RosWorker(self)
        self._worker.telemetry_received.connect(self._on_telemetry)
        self._worker.connection_changed.connect(self._on_connection_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f7f9; }
            QLabel#title { color: #123047; font-size: 25px; font-weight: 700; }
            QLabel#subtitle { color: #617481; font-size: 13px; }
            QFrame, QWidget#panel { background: white; border: 1px solid #dbe4e8; border-radius: 8px; }
            QLabel.metric { color: #123047; font-size: 24px; font-weight: 700; }
            QLabel.caption { color: #6c7d87; font-size: 12px; }
            QPushButton { border: 0; border-radius: 6px; padding: 11px 20px; font-weight: 700; }
            QPushButton#start { background: #168a69; color: white; }
            QPushButton#start:hover { background: #117457; }
            QPushButton#stop { background: #d75b52; color: white; }
            QPushButton#stop:hover { background: #b8473f; }
            """
        )

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Robotics Telemetry Dashboard")
        title.setObjectName("title")
        subtitle = QLabel("ROS2 command console and live simulated robot telemetry")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        controls = QWidget()
        controls.setObjectName("panel")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(18, 14, 18, 14)
        self.connection_label = QLabel("●  Connecting to ROS2")
        self.connection_label.setStyleSheet("color: #c58b18; font-weight: 700;")
        self.state_label = QLabel("State: stopped")
        self.state_label.setStyleSheet("color: #617481; font-weight: 700;")
        start_button = QPushButton("Start")
        start_button.setObjectName("start")
        stop_button = QPushButton("Stop")
        stop_button.setObjectName("stop")
        start_button.clicked.connect(self._worker_start)
        stop_button.clicked.connect(self._worker_stop)
        controls_layout.addWidget(self.connection_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.state_label)
        controls_layout.addSpacing(18)
        controls_layout.addWidget(start_button)
        controls_layout.addWidget(stop_button)
        layout.addWidget(controls)

        metrics = QHBoxLayout()
        self.battery_label = self._metric_card(metrics, "Battery", "-- %")
        self.velocity_label = self._metric_card(metrics, "Velocity", "-- m/s")
        self.samples_label = self._metric_card(metrics, "Samples logged", "0")
        layout.addLayout(metrics)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#ffffff")
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setLabel("left", "Velocity (m/s)")
        self.plot.setLabel("bottom", "Sample")
        self.plot.setTitle("Live velocity", color="#123047", size="13pt")
        self.plot.getAxis("left").setTextPen(pg.mkPen("#617481"))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen("#617481"))
        self.velocity_curve = self.plot.plot([], [], pen=pg.mkPen("#168a69", width=3))
        layout.addWidget(self.plot, stretch=1)

        self.battery_plot = pg.PlotWidget()
        self.battery_plot.setBackground("#ffffff")
        self.battery_plot.showGrid(x=True, y=True, alpha=0.18)
        self.battery_plot.setLabel("left", "Battery (%)")
        self.battery_plot.setLabel("bottom", "Sample")
        self.battery_plot.setTitle("Battery level", color="#123047", size="13pt")
        self.battery_plot.getAxis("left").setTextPen(pg.mkPen("#617481"))
        self.battery_plot.getAxis("bottom").setTextPen(pg.mkPen("#617481"))
        self.battery_plot.setYRange(0, 100, padding=0)
        self.battery_plot.enableAutoRange(axis="y", enable=False)  # prevent SI prefix rescaling
        self.battery_curve = self.battery_plot.plot([], [], pen=pg.mkPen("#c58b18", width=3))
        layout.addWidget(self.battery_plot, stretch=1)

        self.setCentralWidget(root)

    @staticmethod
    def _metric_card(parent_layout, caption: str, value: str) -> QLabel:
        panel = QWidget()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 14, 18, 14)
        caption_label = QLabel(caption.upper())
        caption_label.setProperty("class", "caption")
        caption_label.setStyleSheet("color: #6c7d87; font-size: 12px;")
        value_label = QLabel(value)
        value_label.setProperty("class", "metric")
        value_label.setStyleSheet("color: #123047; font-size: 24px; font-weight: 700;")
        panel_layout.addWidget(caption_label)
        panel_layout.addWidget(value_label)
        parent_layout.addWidget(panel)
        return value_label

    def _worker_start(self) -> None:
        self._worker.publish_start()

    def _worker_stop(self) -> None:
        self._worker.publish_stop()

    def _on_connection_changed(self, connected: bool, message: str) -> None:
        color = "#168a69" if connected else "#d75b52"
        self.connection_label.setText(f"●  {message}")
        self.connection_label.setStyleSheet(f"color: {color}; font-weight: 700;")

    def _on_telemetry(self, battery: float, velocity: float, running: bool) -> None:
        self._sample_number += 1
        self._time_values.append(self._sample_number)
        self._velocity_values.append(velocity)
        self._battery_values.append(battery)
        self.battery_label.setText(f"{battery:.1f} %")
        self.velocity_label.setText(f"{velocity:.2f} m/s")
        self.samples_label.setText(str(self._sample_number))
        self.state_label.setText(f"State: {'running' if running else 'stopped'}")
        xs = list(self._time_values)
        self.velocity_curve.setData(xs, list(self._velocity_values))
        self.battery_curve.setData(xs, list(self._battery_values))
        if len(xs) > 1:
            self.plot.setXRange(xs[0], xs[-1], padding=0.04)
            self.battery_plot.setXRange(xs[0], xs[-1], padding=0.04)
        self._logger.write(battery, velocity, running)

    def _on_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 8000)

    def closeEvent(self, event) -> None:
        self._logger.close()
        self._worker.stop()
        event.accept()
