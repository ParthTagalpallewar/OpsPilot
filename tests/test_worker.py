import logging
from threading import Event

from opspilot.apps.worker import main as worker


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
