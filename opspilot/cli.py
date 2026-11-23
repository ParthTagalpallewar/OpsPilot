import argparse
import json
from datetime import datetime
from pathlib import Path

from opspilot.evaluation import evaluate_replay
from opspilot.evidence.otlp_logs import import_payment_logs
from opspilot.evidence.prometheus import capture_comparison
from opspilot.evidence.rollouts import import_rollouts
from opspilot.evidence.traces import capture_payment_trace
from opspilot.operational_metrics import configure_metrics
from opspilot.replay import METRIC_SCENARIOS, SCENARIOS, investigate
from opspilot.telemetry import configure_tracing


def main():
    parser = argparse.ArgumentParser(description="Replay an OpsPilot investigation.")
    commands = parser.add_subparsers(dest="command")
    replay = commands.add_parser("replay", help="Analyze a captured demo incident.")
    replay.add_argument("scenario", choices=SCENARIOS)
    replay.add_argument(
        "--with-claude", action="store_true", help="Request a Claude explanation."
    )
    replay.add_argument(
        "--as-of", type=datetime.fromisoformat, help="Replay cutoff with UTC offset."
    )
    evaluate = commands.add_parser("eval", help="Score the frozen demo replays.")
    evaluate.add_argument(
        "--ground-truth", type=Path, default=Path("testbed/ground_truth/replay.json")
    )
    capture = commands.add_parser(
        "capture-metrics", help="Freeze two Prometheus percentage windows."
    )
    capture.add_argument("scenario", choices=METRIC_SCENARIOS)
    capture.add_argument("--url", required=True)
    capture.add_argument(
        "--query", required=True, help="PromQL returning one percent series."
    )
    capture.add_argument(
        "--windows",
        nargs=4,
        required=True,
        metavar=("BASE_START", "BASE_END", "FAULT_START", "FAULT_END"),
    )
    capture.add_argument("--step", type=int, default=30)
    capture.add_argument("--output", required=True, type=Path)
    capture_trace = commands.add_parser(
        "capture-payment-trace", help="Freeze a Payment error trace from Jaeger."
    )
    capture_trace.add_argument("--url", required=True)
    capture_trace.add_argument("--trace-id", required=True)
    capture_trace.add_argument("--output", required=True, type=Path)
    import_logs = commands.add_parser(
        "import-payment-logs", help="Freeze warnings and errors from an OTLP JSON file."
    )
    import_logs.add_argument("source", type=Path)
    import_logs.add_argument("--output", required=True, type=Path)
    rollout = commands.add_parser(
        "import-rollouts", help="Freeze Deployment-owned Kubernetes ReplicaSets."
    )
    rollout.add_argument("scenario", choices=METRIC_SCENARIOS)
    rollout.add_argument("source", type=Path)
    rollout.add_argument("--namespace", required=True)
    rollout.add_argument("--deployment", required=True)
    rollout.add_argument("--output", required=True, type=Path)
    for command in (replay, evaluate):
        command.add_argument(
            "--captures",
            type=Path,
            default=Path("testbed/scenarios"),
            help="Directory containing the captured telemetry files.",
        )
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    try:
        configure_tracing()
        configure_metrics("cli")
        if args.command == "capture-metrics":
            service, _, _ = METRIC_SCENARIOS[args.scenario]
            path = args.output / f"{service}-prometheus.json"
            capture_comparison(args.url, args.query, args.windows, args.step, path)
            report = {"capture": str(path), "scenario": args.scenario}
        elif args.command == "capture-payment-trace":
            path = capture_payment_trace(args.url, args.trace_id, args.output)
            report = {"capture": str(path), "scenario": "payment-failure"}
        elif args.command == "import-payment-logs":
            path = import_payment_logs(args.source, args.output)
            report = {"capture": str(path), "scenario": "payment-failure"}
        elif args.command == "import-rollouts":
            service, _, _ = METRIC_SCENARIOS[args.scenario]
            path = import_rollouts(
                args.source,
                args.output,
                namespace=args.namespace,
                deployment=args.deployment,
                service=service,
            )
            report = {"capture": str(path), "scenario": args.scenario}
        elif args.command == "eval":
            report = evaluate_replay(args.captures, args.ground_truth)
        else:
            if (
                args.with_claude
                and args.captures.resolve() != Path("testbed/scenarios").resolve()
            ):
                parser.error("--with-claude requires the repository demo captures")
            report = investigate(
                args.scenario,
                args.captures,
                with_claude=args.with_claude,
                as_of=args.as_of,
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    if args.command == "eval":
        return int(report["passed_scenarios"] != report["total_scenarios"])
