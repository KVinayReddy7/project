"""Thread-safe synchronous pub/sub bus used when rclpy is not available."""
import threading
from collections import defaultdict
from typing import Any, Callable

_lock = threading.Lock()
_subscribers: dict[str, list[Callable]] = defaultdict(list)


def subscribe(topic: str, callback: Callable[[Any], None]) -> None:
    with _lock:
        _subscribers[topic].append(callback)


def publish(topic: str, data: Any) -> None:
    with _lock:
        callbacks = list(_subscribers[topic])
    for callback in callbacks:
        callback(data)
