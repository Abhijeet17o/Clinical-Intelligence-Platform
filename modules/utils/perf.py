"""Lightweight performance timing utilities for quick instrumentation.

Provides a Timer context manager that logs timings and records them for later
inspection with get_records(). Designed for development profiling and is
non-invasive in production (minimal overhead).
"""
import time
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)
_records: List[Tuple[str, float]] = []


class Timer:
    """Context manager to time a block and record the elapsed seconds.

    Usage:
        with Timer('upload_audio'):
            ...
    After the block exits a debug log will be emitted and the record stored.
    """

    def __init__(self, name: str):
        self.name = name
        self._start = None
        self.elapsed = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._start is None:
            return
        self.elapsed = time.perf_counter() - self._start
        _records.append((self.name, self.elapsed))
        logger.debug(f"[PERF] {self.name}: {self.elapsed:.3f}s")


def get_records(reset: bool = False):
    """Return recorded (name, elapsed_seconds) tuples.

    If reset=True, the internal buffer is cleared after returning.
    """
    global _records
    out = list(_records)
    if reset:
        _records = []
    return out


def clear_records():
    global _records
    _records = []
