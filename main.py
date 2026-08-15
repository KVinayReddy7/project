#!/usr/bin/env python3
"""Start the PyQt5 robotics telemetry dashboard."""

import sys

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Robotics Telemetry Dashboard")

    window = MainWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
