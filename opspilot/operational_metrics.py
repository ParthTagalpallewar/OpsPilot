"""Low-cardinality OpenTelemetry metrics for investigation operations."""

import os
from collections.abc import Callable
from uuid import uuid4

from opentelemetry import metrics

meter = metrics.get_meter("opspilot")
worker_duration = meter.create_histogram("opspilot.job.duration", unit="s")
worker_outcomes = meter.create_counter("opspilot.job.outcomes", unit="{job}")
review_wait = meter.create_histogram("opspilot.review.wait", unit="s")
model_tokens = meter.create_counter("opspilot.model.tokens", unit="{token}")


def configure_metrics(role: str, queue_depth: Callable[[], int] | None = None) -> None:
    mode = os.environ.get("OPSPILOT_METRICS", "").strip().lower()
    if not mode:
        return
    if mode not in {"console", "otlp"}:
        raise ValueError("OPSPILOT_METRICS must be console or otlp")

    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import Resource

    if mode == "otlp":
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )

        exporter = OTLPMetricExporter()
    else:
        import sys

        exporter = ConsoleMetricExporter(out=sys.stderr)

    provider = MeterProvider(
        resource=Resource.create(
            {
                "service.name": "opspilot",
                "service.instance.id": str(uuid4()),
                "opspilot.role": role,
            }
        ),
        metric_readers=[PeriodicExportingMetricReader(exporter)],
    )
    metrics.set_meter_provider(provider)
    if queue_depth is not None:

        def observe_queue(options):
            return [metrics.Observation(queue_depth())]

        meter.create_observable_gauge(
            "opspilot.queue.available", [observe_queue], unit="{job}"
        )
