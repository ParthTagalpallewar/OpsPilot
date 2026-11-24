import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

import pytest

from opspilot.investigations import MAX_JOB_ATTEMPTS, InvestigationStore
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
            with store.database.session() as connection:
                (old_token,) = connection.execute(
                    "SELECT claim_token FROM replay_jobs WHERE investigation_id = ?",
                    (queued["investigation_id"],),
                ).fetchone()
            clock.return_value = 161
            assert not store._renew_lease(queued["investigation_id"], old_token)
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


def test_job_that_never_finishes_fails_after_its_attempts(tmp_path):
    store = InvestigationStore(tmp_path / "poison.db", CAPTURES)
    queued = store.create("ad-high-cpu", "Ad CPU", "Demo replay", queued=True)
    investigation_id = queued["investigation_id"]

    with (
        patch("opspilot.investigations.investigate", side_effect=RuntimeError("bug")),
        patch("opspilot.investigations.time") as clock,
    ):
        for attempt in range(MAX_JOB_ATTEMPTS):
            clock.return_value = 100 + attempt * 61
            with pytest.raises(RuntimeError):
                store.process_next()
        clock.return_value = 100 + MAX_JOB_ATTEMPTS * 61
        assert store.process_next()

    document = store.get(investigation_id)
    assert document["status"] == "failed"
    assert document["error"] == "Replay stopped after repeated worker failures"
    assert not store.process_next()
    assert [event["status"] for event in store.events_after(investigation_id, 0)] == [
        "queued",
        *["running"] * MAX_JOB_ATTEMPTS,
        "failed",
    ]


def test_queue_created_before_attempt_tracking_still_processes(tmp_path):
    database = tmp_path / "existing.db"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE replay_jobs (investigation_id TEXT PRIMARY KEY, "
            "scenario TEXT NOT NULL, claim_token TEXT, lease_until REAL)"
        )
        connection.execute(
            "CREATE TABLE investigation_events (sequence INTEGER PRIMARY KEY, "
            "investigation_id TEXT NOT NULL, status TEXT NOT NULL, "
            "recorded_at TEXT NOT NULL)"
        )

    store = InvestigationStore(database, CAPTURES)
    queued = store.create("ad-high-cpu", "Ad CPU", "Demo replay", queued=True)
    assert store.process_next()
    assert store.get(queued["investigation_id"])["status"] == "completed"


@pytest.mark.parametrize(
    ("scenario", "live", "error"),
    [
        ("ad-high-cpu", False, "Replay telemetry is unavailable"),
        ("ad-high-cpu", True, "Live Prometheus telemetry is unavailable"),
        ("payment-failure", True, "Live Jaeger telemetry is unavailable"),
    ],
)
def test_failed_job_names_the_unavailable_telemetry(tmp_path, scenario, live, error):
    store = InvestigationStore(tmp_path / "failed.db", tmp_path / "no-captures")
    alert_at = "2026-11-23T02:30:00+00:00" if live else None
    queued = store.create(
        scenario,
        "Alert",
        "Demo replay",
        queued=True,
        alert_occurrence=f"a1:{alert_at}" if live else None,
        live_alert_at=alert_at,
    )

    assert store.process_next()
    document = store.get(queued["investigation_id"])
    assert (document["status"], document["error"]) == ("failed", error)


def test_active_worker_renews_lease_past_original_expiry(tmp_path, monkeypatch):
    database = tmp_path / "queue.db"
    worker = InvestigationStore(database, CAPTURES)
    competitor = InvestigationStore(database, CAPTURES)
    queued = worker.create("ad-high-cpu", "Ad CPU", "Demo replay", queued=True)
    investigation_id = queued["investigation_id"]
    started, release, renewed = Event(), Event(), Event()
    report = investigate("ad-high-cpu", CAPTURES)
    renew = worker._renew_lease

    def run_replay(*args, **kwargs):
        started.set()
        assert release.wait(5)
        return report

    def record_renewal(job_id, token):
        result = renew(job_id, token)
        if result and clock.return_value == 145:
            renewed.set()
        return result

    monkeypatch.setattr("opspilot.investigations.LEASE_RENEWAL_SECONDS", 0.01)
    monkeypatch.setattr(worker, "_renew_lease", record_renewal)
    with (
        patch("opspilot.investigations.investigate", side_effect=run_replay),
        patch("opspilot.investigations.time", return_value=100) as clock,
    ):
        running = Thread(target=worker.process_next)
        running.start()
        try:
            assert started.wait(5)
            clock.return_value = 145
            assert renewed.wait(5)
            clock.return_value = 161
            assert competitor.queue_depth() == 0
            assert not competitor.process_next()
        finally:
            release.set()
            running.join(5)

    assert not running.is_alive()
    assert worker.get(investigation_id)["report"] == report
    assert [event["status"] for event in worker.events_after(investigation_id, 0)] == [
        "queued",
        "running",
        "completed",
    ]
