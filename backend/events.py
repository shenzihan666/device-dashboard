"""Event dataclass hierarchy for all parsed and synthetic events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Event:
    ts_ns: int
    kind: str
    host: str | None = None
    device_serial: str | None = None
    ai_url: str | None = None
    prev_ai_url: str | None = None
    status: str | None = None
    latency_ms: int | None = None
    request_id: str | None = None
    session_id: str | None = None
    raw_line: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("payload", None)
        d["payload_json"] = self.payload if self.payload else None
        return d


# Event kind constants
AI_SERVER_OBSERVED = "ai_server_observed"
AI_HEALTH_CHECK = "ai_health_check"
SIDECAR_ERROR = "sidecar_error"
DEVICE_ERROR = "device_error"
METRIC_EVENT = "metric_event"
HOST_DEVICE_MAP = "host_device_map"

SYNTH_SWITCHED = "synth_switched"
SYNTH_DEVICE_OFFLINE = "synth_device_offline"
SYNTH_DEVICE_ONLINE = "synth_device_online"
SYNTH_HOST_OFFLINE = "synth_host_offline"
SYNTH_HOST_ONLINE = "synth_host_online"
