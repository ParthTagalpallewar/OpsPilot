import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from threading import Event
from time import monotonic, sleep

from opspilot.apps.worker import main as worker

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


class FlakyStore:
    def __init__(self, stop: Event):
        self.stop = stop
        self.calls = 0

    def process_next(self) -> bool:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("database is locked")
        self.stop.set()
        return True


class NoWakeup:
    def wait(self) -> None:
        raise AssertionError("the worker should not idle while jobs are processed")


def test_worker_keeps_serving_after_an_unexpected_error(monkeypatch, caplog):
    monkeypatch.setattr(worker, "ERROR_BACKOFF_SECONDS", 0)
    stop = Event()
    store = FlakyStore(stop)

    with caplog.at_level(logging.ERROR):
        worker.serve(store, NoWakeup(), stop)

    assert store.calls == 2
    assert "Replay job processing failed unexpectedly" in caplog.text
    assert "database is locked" in caplog.text


def test_sigterm_stops_an_idle_worker_cleanly(tmp_path):
    database = tmp_path / "worker.db"
    env = {key: value for key, value in os.environ.items() if "OPSPILOT" not in key}
    env.update(OPSPILOT_DB=str(database), OPSPILOT_CAPTURES=str(CAPTURES))
    process = subprocess.Popen(
        [sys.executable, "-m", "opspilot.apps.worker.main"], cwd=tmp_path, env=env
    )
    try:
        deadline = monotonic() + 30
        while not database.exists():
            assert process.poll() is None and monotonic() < deadline
            sleep(0.05)
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            process.kill()
