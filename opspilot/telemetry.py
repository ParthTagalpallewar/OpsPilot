"""OpenTelemetry setup shared by the CLI, API, and worker."""

import base64
import os
from urllib.parse import urlsplit

from opentelemetry import trace

tracer = trace.get_tracer("opspilot")


def start_span(name: str, **options):
    # Exception messages can quote capture content, so spans never record them.
    return tracer.start_as_current_span(
        name, record_exception=False, set_status_on_exception=False, **options
    )


def langfuse_export_config() -> tuple[str, dict[str, str]]:
    host = os.environ.get("LANGFUSE_HOST", "").strip()
    public = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    url = urlsplit(host)
    loopback = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not public
        or not secret
        or not url.hostname
        or url.username is not None
        or url.query
        or url.fragment
        or not (url.scheme == "https" or (url.scheme == "http" and loopback))
    ):
        raise ValueError("Configure a Langfuse HTTPS host and both project keys")
    encoded = base64.b64encode(f"{public}:{secret}".encode()).decode()
    return f"{host.rstrip('/')}/api/public/otel/v1/traces", {
        "Authorization": f"Basic {encoded}",
        "x-langfuse-ingestion-version": "4",
    }


def configure_tracing() -> None:
    mode = os.environ.get("OPSPILOT_TRACING", "").strip().lower()
    if not mode:
        return
    if mode not in {"console", "otlp", "langfuse"}:
        raise ValueError("OPSPILOT_TRACING must be console, otlp, or langfuse")

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    provider = TracerProvider(resource=Resource.create({"service.name": "opspilot"}))
    if mode in {"otlp", "langfuse"}:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        if mode == "langfuse":
            endpoint, headers = langfuse_export_config()
            exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        else:
            exporter = OTLPSpanExporter()
    else:
        import sys

        exporter = ConsoleSpanExporter(out=sys.stderr)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
