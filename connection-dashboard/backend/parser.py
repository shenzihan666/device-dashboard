"""Regex / JSON parsers for the five log-line shapes from wecom-sidecar-logs."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from backend.events import (
    AI_HEALTH_CHECK,
    AI_SERVER_OBSERVED,
    DEVICE_ERROR,
    HOST_DEVICE_MAP,
    METRIC_EVENT,
    SIDECAR_ERROR,
    Event,
)

# ── AI Server observed ──────────────────────────────────────────────────
# Example: [10AE9X304J0033Z] AI Server: http://118.31.238.44:8000/chat
_RE_AI_SERVER = re.compile(
    r"\[(?P<serial>[A-Z0-9]+)\]\s+AI Server:\s+(?P<url>https?://[^\s]+)"
)

# ── AI Health Check ─────────────────────────────────────────────────────
# Example: [AIHealthChecker] status=healthy network=reachable http=alive inference=None time=94ms
_RE_HEALTH = re.compile(
    r"\[AIHealthChecker\]\s+"
    r"status=(?P<status>\S+)\s+"
    r"network=(?P<network>\S+)\s+"
    r"http=(?P<http>\S+)\s+"
    r"inference=(?P<inference>\S+)\s+"
    r"time=(?P<time_ms>\d+)ms"
)

# ── Sidecar transient error ─────────────────────────────────────────────
# Example: Transient error (attempt 1/3): Server disconnected, reconnecting in 0.5s...
_RE_SIDECAR_ERR = re.compile(
    r"Transient error \(attempt (?P<attempt>\d+)/(?P<max_attempts>\d+)\):\s+(?P<message>.+)"
)

# ── Per-device error ────────────────────────────────────────────────────
# Example: [10AE9X304J0033Z] Error: Server disconnected
_RE_DEVICE_ERR = re.compile(
    r"\[(?P<serial>[A-Z0-9]+)\]\s+Error:\s+(?P<message>.+)"
)

# ── Host/device mapping from ADB traces ─────────────────────────────────
# Example: [ADB_TRACE] serial=10AEC61XMY00773 pid=7612 ...
_RE_SERIAL_IN_BODY = re.compile(r"serial=(?P<serial>[A-Z0-9]{6,})")

# ── Device serial from bracket prefix ───────────────────────────────────
_RE_BRACKET_SERIAL = re.compile(r"\[(?P<serial>[A-Z0-9]{8,})\]")

# ── Metrics logger JSON ────────────────────────────────────────────────
# The JSON blob starts after `metrics_logger:_emit:NNN | `
_RE_METRICS_JSON = re.compile(r"metrics_logger:_emit:\d+\s*\|\s*(?P<json>\{.+)")


def _extract_host_from_labels(labels: str | dict | None) -> str | None:
    """Pull 'host' from the Loki labels column (dict or stringified dict)."""
    if labels is None:
        return None
    if isinstance(labels, str):
        try:
            labels = ast.literal_eval(labels)
        except (ValueError, SyntaxError):
            return None
    if isinstance(labels, dict):
        return labels.get("host")
    return None


def parse_ai_server(line: str, ts_ns: int, host: str | None) -> Event | None:
    m = _RE_AI_SERVER.search(line)
    if not m:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=AI_SERVER_OBSERVED,
        host=host,
        device_serial=m.group("serial"),
        ai_url=m.group("url"),
        raw_line=line,
    )


def parse_health_check(line: str, ts_ns: int, host: str | None) -> Event | None:
    m = _RE_HEALTH.search(line)
    if not m:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=AI_HEALTH_CHECK,
        host=host,
        status=m.group("status"),
        latency_ms=int(m.group("time_ms")),
        raw_line=line,
        payload={
            "network": m.group("network"),
            "http": m.group("http"),
            "inference": m.group("inference"),
        },
    )


def parse_sidecar_error(line: str, ts_ns: int, host: str | None) -> Event | None:
    m = _RE_SIDECAR_ERR.search(line)
    if not m:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=SIDECAR_ERROR,
        host=host,
        status="error",
        raw_line=line,
        payload={
            "attempt": int(m.group("attempt")),
            "max_attempts": int(m.group("max_attempts")),
            "message": m.group("message").strip(),
        },
    )


def parse_device_error(line: str, ts_ns: int, host: str | None) -> Event | None:
    m = _RE_DEVICE_ERR.search(line)
    if not m:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=DEVICE_ERROR,
        host=host,
        device_serial=m.group("serial"),
        status="error",
        raw_line=line,
        payload={"message": m.group("message").strip()},
    )


def parse_metrics_event(line: str, ts_ns: int, host: str | None) -> Event | None:
    m = _RE_METRICS_JSON.search(line)
    if not m:
        return None
    try:
        data: dict[str, Any] = json.loads(m.group("json"))
    except json.JSONDecodeError:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=METRIC_EVENT,
        host=host,
        device_serial=data.get("device_serial"),
        session_id=data.get("session_id"),
        raw_line=line,
        payload=data,
    )


def parse_host_device_map(line: str, ts_ns: int, host: str | None) -> Event | None:
    """Extract host↔device serial mapping from ADB trace or bracket-prefix lines."""
    m = _RE_SERIAL_IN_BODY.search(line)
    if not m:
        m = _RE_BRACKET_SERIAL.search(line)
    if not m or not host:
        return None
    return Event(
        ts_ns=ts_ns,
        kind=HOST_DEVICE_MAP,
        host=host,
        device_serial=m.group("serial"),
    )


def parse_row(
    line: str,
    ts_ns: int,
    labels: str | dict | None,
    ref: str,
) -> Event | None:
    """Route a raw log row to the appropriate parser based on the query ref.

    ref is the Loki query refId ("A".."E") so we know which parser to try first.
    """
    host = _extract_host_from_labels(labels)

    if ref == "A":
        return parse_ai_server(line, ts_ns, host)
    if ref == "B":
        return parse_health_check(line, ts_ns, host)
    if ref == "C":
        return parse_sidecar_error(line, ts_ns, host) or parse_device_error(
            line, ts_ns, host
        )
    if ref == "D":
        return parse_metrics_event(line, ts_ns, host)
    if ref == "E":
        return parse_host_device_map(line, ts_ns, host)

    return None
