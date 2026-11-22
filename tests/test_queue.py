from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

from opspilot.investigations import InvestigationStore
from opspilot.replay import investigate

CAPTURES = Path(__file__).resolve().parents[1] / "testbed" / "scenarios"


def test_expired_worker_cannot_overwrite_reclaimed_job(tmp_path):
    store = InvestigationStore(tmp_path / "queue.db", CAPTURES)
    queued = store.create("ad-high-cpu", "Ad CPU", "Demo replay", queued=True)
    started, release = Event(), Event()
    report = investigate("ad-high-cpu", CAPTURES)

    def run_replay(scenario, captures, *, on_step, as_of, checkpoint):
        if not started.is_set():
            started.set()
            assert release.wait(5)
            on_step("stale")
            return {**report, "service": "stale"}
        on_step("current")
        return report

    with (
        patch("opspilot.investigations.investigate", side_effect=run_replay),
        patch("opspilot.investigations.time", return_value=100) as clock,
    ):
        worker = Thread(target=store.process_next)
        worker.start()
        try:
            assert started.wait(5)
            assert store.get(queued["investigation_id"])["status"] == "running"
            assert not store.process_next()
            clock.return_value = 161
            assert store.process_next()
        finally:
            release.set()
            worker.join(5)

    assert not worker.is_alive()
    assert store.get(queued["investigation_id"])["report"] == report
    assert not store.process_next()
    steps = [
        event["step"]
        for event in store.events_after(queued["investigation_id"], 0)
        if "step" in event
    ]
    assert steps == ["current"]


def test_enqueue_notifies_after_the_job_is_visible(tmp_path):
    database = tmp_path / "notify.db"
    worker = InvestigationStore(database, CAPTURES)
    notifications = []

    def notify():
        notifications.append(worker.process_next())

    api = InvestigationStore(database, CAPTURES, on_enqueue=notify)
    queued = api.create("payment-failure", "Payment", "Demo warning", queued=True)
    assert notifications == [True]
    assert api.get(queued["investigation_id"])["status"] == "completed"
