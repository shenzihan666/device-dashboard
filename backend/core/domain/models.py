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


@dataclass
class GraphSnapshot:
    servers: list[ServerState]
    hosts: list[HostState]
    devices: list[DeviceState]
    edges: list[Edge]
