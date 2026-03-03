"""
packages/observability/src/tracer.py

OpenTelemetry setup for Continuum Agent Hub.
Provides traced spans for each LangGraph node and cost meters.
"""

import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "continuum-agent-hub")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

_resource = Resource.create({"service.name": SERVICE_NAME})

# ── Tracer ────────────────────────────────────────────────────────────────────

def init_tracer() -> trace.Tracer:
    """Initialise OTEL tracer and return a module tracer."""
    provider = TracerProvider(resource=_resource)
    exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(SERVICE_NAME)


# ── Meter ─────────────────────────────────────────────────────────────────────

def init_meter() -> metrics.Meter:
    """Initialise OTEL meter and return a module meter."""
    exporter = OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15_000)
    provider = MeterProvider(resource=_resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return metrics.get_meter(SERVICE_NAME)


# ── Singletons (initialised once at app startup) ──────────────────────────────

tracer: trace.Tracer = init_tracer()
meter: metrics.Meter = init_meter()

# Instruments
token_counter = meter.create_counter(
    "continuum.tokens_consumed",
    unit="tokens",
    description="Total LLM tokens consumed per agent and user",
)
iteration_histogram = meter.create_histogram(
    "continuum.agent_iterations",
    unit="iterations",
    description="Number of LangGraph iterations per harvest job",
)
tool_error_counter = meter.create_counter(
    "continuum.tool_errors",
    unit="errors",
    description="Count of tool-level errors caught by the Purification Node",
)
hitl_counter = meter.create_counter(
    "continuum.hitl_escalations",
    unit="escalations",
    description="Tasks sent to HITL queue due to low confidence",
)


def record_tokens(count: int, agent: str, user_id: str) -> None:
    token_counter.add(count, {"agent": agent, "user_id": user_id})


def record_iterations(count: int, agent: str) -> None:
    iteration_histogram.record(count, {"agent": agent})


def record_tool_error(tool: str, error_type: str) -> None:
    tool_error_counter.add(1, {"tool": tool, "error_type": error_type})


def record_hitl(agent: str, reason: str) -> None:
    hitl_counter.add(1, {"agent": agent, "reason": reason})
