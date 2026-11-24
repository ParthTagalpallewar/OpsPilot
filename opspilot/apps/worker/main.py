"""Run a worker against the local OpsPilot database."""

import argparse
import logging
import os
import signal
from pathlib import Path
from threading import Event

from opspilot.investigations import InvestigationStore
from opspilot.live_metrics import configured_live_metrics
from opspilot.live_traces import configured_live_traces
from opspilot.operational_metrics import configure_metrics
from opspilot.telemetry import configure_tracing
from opspilot.wakeup import WorkerWakeup, configured_wakeup

ERROR_BACKOFF_SECONDS = 5
logger = logging.getLogger(__name__)


def serve(store: InvestigationStore, wakeup: WorkerWakeup, stop: Event) -> None:
    while not stop.is_set():
        try:
            processed = store.process_next()
        except Exception:
            # The claimed job keeps its lease, so it is retried once the lease expires.
            logger.exception("Replay job processing failed unexpectedly")
            stop.wait(ERROR_BACKOFF_SECONDS)
            continue
        if not processed:
            wakeup.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process at most one job.")
    args = parser.parse_args()
    stop = Event()
    # Finish the current job, then exit. PID 1 in a container ignores SIGTERM otherwise.
    signal.signal(signal.SIGTERM, lambda signum, frame: stop.set())
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    configure_tracing()
    configure_metrics("worker")
    store = InvestigationStore(
        os.environ.get("OPSPILOT_DATABASE_DSN")
        or Path(os.environ.get("OPSPILOT_DB", "opspilot.sqlite3")),
        Path(os.environ.get("OPSPILOT_CAPTURES", "testbed/scenarios")),
        checkpoint_replay=True,
        live_metrics=configured_live_metrics(),
        live_traces=configured_live_traces(),
    )
    if args.once:
        store.process_next()
        return
    try:
        serve(store, configured_wakeup(), stop)
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
