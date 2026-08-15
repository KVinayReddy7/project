"""Timestamped telemetry CSV writer."""

import csv
from datetime import datetime, timezone
from pathlib import Path


class TelemetryLogger:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        if self.output_path.stat().st_size == 0:
            self._writer.writerow(("timestamp", "battery_percent", "velocity", "running"))
            self._file.flush()

    def write(self, battery: float, velocity: float, running: bool) -> None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        self._writer.writerow((timestamp, f"{battery:.2f}", f"{velocity:.3f}", running))
        self._file.flush()

    def close(self) -> None:
        self._file.close()
