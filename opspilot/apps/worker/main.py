"""Run a worker against the local OpsPilot database."""

import argparse
import os
from pathlib import Path

from opspilot.investigations import InvestigationStore
from opspilot.live_metrics import configured_live_metrics
from opspilot.live_traces import configured_live_traces
from opspilot.operational_metrics import configure_metrics
from opspilot.telemetry import configure_tracing
from opspilot.wakeup import configured_wakeup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process at most one job.")
    args = parser.parse_args()
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
    wakeup = configured_wakeup()
    try:
        while True:
            if not store.process_next():
                wakeup.wait()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
