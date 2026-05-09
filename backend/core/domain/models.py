"""Value objects for domain entities (Host, Device, Server, Edge)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceState:
    serial: str
    host: str | None
    ai_url: str
    status: str
    last_seen_ns: int | None


@dataclass(frozen=True)
class HostState:
    name: str
    status: str
    last_seen_ns: int | None
    device_count: int


@dataclass(frozen=True)
class ServerState:
    url: str
    device_count: int


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    edge_type: str
    status: str | None = None


@dataclass(frozen=True)
class WeComClientState:
    instance_id: str
    name: str
    version: str
    brain_url: str
    device_count: int
    devices: tuple  # tuple of dicts for hashability
    health_status: str
    ai_reachable: bool
    ai_response_ms: float | None
    last_heartbeat_ns: int
    online: bool


@dataclass(frozen=True)
class BrainServerState:
    instance_id: str
    name: str
    version: str
    worker_count: int
    total_handled: int
    avg_inflight: float
    health_status: str
    memory_mb: float | None
    cpu_pct: float | None
    last_heartbeat_ns: int
    online: bool


@dataclass
class GraphSnapshot:
    servers: list[ServerState]
    hosts: list[HostState]
    devices: list[DeviceState]
    edges: list[Edge]
    brain_servers: list[BrainServerState]
    wecom_clients: list[WeComClientState]
    heartbeat_edges: list[Edge]
