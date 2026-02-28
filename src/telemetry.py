"""OpenTelemetry tracing configuration for agent-orchestrator.

Instruments agent pipeline calls with distributed tracing.
Exports spans to a Jaeger-compatible OTLP endpoint, configurable via:
    OTEL_EXPORTER_OTLP_ENDPOINT  (default: http://localhost:4317)
    OTEL_SERVICE_NAME            (default: agent-orchestrator)

Usage:
    from src.telemetry import setup_tracing, get_tracer
    setup_tracing()
    tracer = get_tracer()
    with tracer.start_as_current_span("my-operation") as span:
        span.set_attribute("query", "AI safety")
        ...
"""

from __future__ import annotations

import os
from typing import Any

# Import guards: OpenTelemetry is optional. If not installed, all calls are no-ops.
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    _OTLP_AVAILABLE = True
except ImportError:
    _OTLP_AVAILABLE = False


_tracer_provider: Any = None
_tracer: Any = None


class _NoopTracer:
    """Fallback no-op tracer when OpenTelemetry is not installed."""

    class _NoopSpan:
        def set_attribute(self, key: str, value: object) -> None:  # noqa: D102
            pass

        def record_exception(self, exc: BaseException) -> None:  # noqa: D102
            pass

        def set_status(self, status: object) -> None:  # noqa: D102
            pass

        def __enter__(self) -> "_NoopTracer._NoopSpan":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    def start_as_current_span(self, name: str, **kwargs: object) -> "_NoopTracer._NoopSpan":  # noqa: D102
        return self._NoopSpan()


def setup_tracing(
    service_name: str | None = None,
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> None:
    """Initialize OpenTelemetry tracing.

    Args:
        service_name: Service name for spans. Defaults to OTEL_SERVICE_NAME env var
                      or "agent-orchestrator".
        otlp_endpoint: OTLP gRPC endpoint (Jaeger-compatible). Defaults to
                       OTEL_EXPORTER_OTLP_ENDPOINT env var or
                       "http://localhost:4317".
        console_export: If True, also print spans to console (for debugging).
    """
    global _tracer_provider, _tracer

    if not _OTEL_AVAILABLE:
        return  # Silently skip if OpenTelemetry not installed

    resolved_service = (
        service_name
        or os.environ.get("OTEL_SERVICE_NAME", "agent-orchestrator")
    )
    resolved_endpoint = (
        otlp_endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )

    resource = Resource(attributes={SERVICE_NAME: resolved_service})
    provider = TracerProvider(resource=resource)

    if _OTLP_AVAILABLE:
        otlp_exporter = OTLPSpanExporter(endpoint=resolved_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    if console_export or not _OTLP_AVAILABLE:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    _tracer = trace.get_tracer(resolved_service)


def get_tracer() -> Any:
    """Return the configured tracer, or a no-op tracer if OTEL is unavailable."""
    if not _OTEL_AVAILABLE or _tracer is None:
        return _NoopTracer()
    return _tracer


def shutdown_tracing() -> None:
    """Flush and shut down the tracer provider."""
    if _tracer_provider is not None and _OTEL_AVAILABLE:
        _tracer_provider.shutdown()
