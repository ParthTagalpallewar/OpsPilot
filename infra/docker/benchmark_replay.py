"""Measure HTTP enqueue-to-completion latency on the local Compose demo."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from statistics import median
from time import monotonic
from urllib.request import urlopen

from smoke_replay import BASE_URL, post_json

SCENARIOS = ("ad-high-cpu", "email-memory-leak", "payment-failure")


def time_investigation(index: int) -> float:
    scenario = SCENARIOS[index % len(SCENARIOS)]
    start = monotonic()
    status, _, location = post_json(
        "/v1/incidents",
        {
            "scenario": scenario,
            "title": f"Replay benchmark {index + 1}",
            "description": "Measure the queued demo investigation.",
            "queued": True,
        },
    )
    if status != 202 or location is None:
        raise RuntimeError(f"Expected queued investigation, got HTTP {status}")
    with urlopen(BASE_URL + location + "/events", timeout=200) as stream:
        for line in stream:
            if monotonic() - start > 200:
                raise TimeoutError(f"Replay exceeded the benchmark timeout: {scenario}")
            if not line.startswith(b"data: "):
                continue
            state = json.loads(line[6:])["status"]
            if state == "completed":
                return monotonic() - start
            if state == "failed":
                raise RuntimeError(f"Replay failed: {scenario}")
    raise RuntimeError(f"Progress stream ended before completion: {scenario}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=30)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.concurrency <= min(args.jobs, 20) or args.jobs > 1000:
        parser.error("Use 1–1,000 jobs and concurrency between 1 and 20, at most jobs")

    time_investigation(0)
    start = monotonic()
    durations = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as workers:
        futures = [
            workers.submit(time_investigation, index) for index in range(args.jobs)
        ]
        for future in futures:
            try:
                durations.append(future.result())
            except (OSError, RuntimeError, ValueError) as exc:
                failures.append(str(exc))
    elapsed = monotonic() - start
    ordered = sorted(durations)
    result = {
        "jobs": args.jobs,
        "concurrency": args.concurrency,
        "completed": len(ordered),
        "failures": failures,
        "wall_seconds": round(elapsed, 3),
    }
    if ordered:
        p50 = median(ordered)
        p95 = ordered[ceil(0.95 * len(ordered)) - 1]
        result.update(
            p50_seconds=round(p50, 3),
            p95_seconds=round(p95, 3),
            max_seconds=round(ordered[-1], 3),
            meets_replay_latency_targets=not failures and p50 < 90 and p95 < 180,
        )

    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
