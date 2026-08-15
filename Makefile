.PHONY: all setup ros2 run stop clean clean-all

SHELL := /bin/bash
VENV  := .venv

all: run

# ── Python environment ─────────────────────────────────────────────────────────
# Target file acts as a sentinel — setup only runs when venv is absent.

$(VENV)/bin/activate:
	@echo "==> Installing system packages (pyqt5, venv)..."
	@sudo apt-get install -y python3-venv python3-pyqt5 -q
	@echo "==> Creating Python virtual environment..."
	@python3 -m venv --system-site-packages $(VENV)
	@$(VENV)/bin/pip install --quiet --upgrade pip
	@$(VENV)/bin/pip install --quiet pyqtgraph
	@echo "==> Python environment ready."

setup: $(VENV)/bin/activate

# ── ROS2 installation ──────────────────────────────────────────────────────────

ros2:
	@ROS_FOUND=$$(find /opt/ros -maxdepth 2 -name "setup.bash" 2>/dev/null | head -1); \
	if [ -n "$$ROS_FOUND" ]; then \
		echo "==> ROS2 found: $$ROS_FOUND"; \
	else \
		. /etc/os-release; \
		case "$$UBUNTU_CODENAME" in \
			noble)   ROS_DISTRO=jazzy ;; \
			oracular) ROS_DISTRO=jazzy ;; \
			plucky|questing) ROS_DISTRO=kilted ;; \
			*)       ROS_DISTRO=kilted ;; \
		esac; \
		echo "==> Ubuntu $$UBUNTU_CODENAME detected — installing ROS2 $$ROS_DISTRO (~800 MB)..."; \
		sudo apt-get install -y software-properties-common curl -q; \
		sudo add-apt-repository universe -y; \
		sudo curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
			-o /usr/share/keyrings/ros-archive-keyring.gpg; \
		echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $$UBUNTU_CODENAME main" \
			| sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null; \
		sudo apt-get update -q; \
		sudo apt-get install -y ros-$$ROS_DISTRO-ros-base ros-dev-tools -q \
			|| echo "  WARNING: ROS2 install failed — app will run in simulation mode."; \
	fi

# ── Launch ─────────────────────────────────────────────────────────────────────
# With ROS2: starts mock robot node in background, then GUI; kills node on exit.
# Without ROS2: starts GUI only; built-in simulation mode activates automatically.

run: setup ros2
	@echo "==> Launching Robotics Telemetry Dashboard..."
	@bash -c '\
		MOCK_PID=""; \
		ROS_SETUP=$$(find /opt/ros -maxdepth 2 -name "setup.bash" 2>/dev/null | sort -r | head -1); \
		if [ -n "$$ROS_SETUP" ]; then \
			source "$$ROS_SETUP"; \
			source $(VENV)/bin/activate; \
			python -m ros_nodes.mock_robot_node & \
			MOCK_PID=$$!; \
			echo "  [ROS2 mode] $$ROS_SETUP — mock robot PID: $$MOCK_PID"; \
		else \
			source $(VENV)/bin/activate; \
			echo "  [Simulation mode] ROS2 unavailable — using built-in simulation."; \
		fi; \
		python main.py; \
		[ -n "$$MOCK_PID" ] && kill $$MOCK_PID 2>/dev/null; \
		echo "==> Dashboard closed."; \
	'

# ── Helpers ────────────────────────────────────────────────────────────────────

stop:
	@pkill -f mock_robot_node 2>/dev/null \
		&& echo "==> Mock robot stopped." \
		|| echo "==> No mock robot process found."

clean:
	@rm -rf $(VENV)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "==> Cleaned. (CSV log preserved — run 'make clean-all' to also remove it)"

clean-all: clean
	@rm -f data/telemetry.csv
	@echo "==> CSV log removed."
