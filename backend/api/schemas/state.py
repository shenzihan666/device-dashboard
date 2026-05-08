"""Pydantic schemas for state endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class DeviceStateResponse(BaseModel):
    serial: str
    host: str | None = None
    ai_url: str
    status: str
    last_seen_ns: int | None = None


class HostStateResponse(BaseModel):
    name: str
    status: str
    last_seen_ns: int | None = None
    device_count: int


class ServerStateResponse(BaseModel):
    url: str
    device_count: int


class EdgeResponse(BaseModel):
    source: str  # "from" in dict form
    target: str  # "to" in dict form
    type: str
    status: str | None = None


class StateSnapshotResponse(BaseModel):
    servers: list[ServerStateResponse]
    hosts: list[HostStateResponse]
    devices: list[DeviceStateResponse]
    edges: list[EdgeResponse]
