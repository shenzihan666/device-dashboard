"""In-memory state projection: detects server switches, device/host offline/online.

The StateProjector maintains a rolling view of current connections and emits
synthetic events when transitions are detected.
"""

from __future__ import annotations

import time
from typing import Any

from backend.events import (
    AI_HEALTH_CHECK,
    AI_SERVER_OBSERVED,
    DEVICE_ERROR,
    HOST_DEVICE_MAP,
    METRIC_EVENT,
    SIDECAR_ERROR,
    SYNTH_DEVICE_OFFLINE,
    SYNTH_DEVICE_ONLINE,
    SYNTH_HOST_OFFLINE,
    SYNTH_HOST_ONLINE,
    SYNTH_SWITCHED,
    Event,
)

_NANO = 1_000_000_000


class StateProjector:
    """Pure-function projection from an event stream.

    Feed events via ``process(event)``; it returns a (possibly empty) list
    of synthetic events to persist.

    ``check_offline()`` should be called periodically (e.g. every 30s) to
    detect devices/hosts that have gone silent.
    """

    def __init__(self, offline_grace_ns: int | None = None) -> None:
        self.offline_grace_ns = offline_grace_ns or 90 * _NANO

        # device_serial -> current AI URL
        self.current_url: dict[str, str] = {}
        # device_serial -> last event ts_ns
        self.device_last_seen: dict[str, int] = {}
        # device_serial -> True if currently marked offline
        self.device_offline: dict[str, bool] = {}

        # host -> last health ts_ns
        self.host_last_seen: dict[str, int] = {}
        # host -> True if currently marked offline
        self.host_offline: dict[str, bool] = {}

        # host -> device_serial set
        self.host_devices: dict[str, set[str]] = {}
        # device_serial -> host
        self.device_host: dict[str, str] = {}

    def process(self, event: Event) -> list[Event]:
        """Process one event; return synthetic events (may be empty)."""
        synths: list[Event] = []

        serial = event.device_serial
        host = event.host

        # Update host ↔ device mapping
        if host and serial:
            self.host_devices.setdefault(host, set()).add(serial)
            self.device_host[serial] = host

        # Track device activity
        if serial:
            self.device_last_seen[serial] = event.ts_ns

            if self.device_offline.get(serial):
                self.device_offline[serial] = False
                synths.append(Event(
                    ts_ns=event.ts_ns,
                    kind=SYNTH_DEVICE_ONLINE,
                    host=host or self.device_host.get(serial),
                    device_serial=serial,
                ))

        # Track host activity for health-related events
        if host and event.kind in (AI_HEALTH_CHECK, SIDECAR_ERROR):
            self.host_last_seen[host] = event.ts_ns

            if self.host_offline.get(host):
                self.host_offline[host] = False
                synths.append(Event(
                    ts_ns=event.ts_ns,
                    kind=SYNTH_HOST_ONLINE,
                    host=host,
                ))

        # Detect server switch
        if event.kind == AI_SERVER_OBSERVED and serial and event.ai_url:
            prev = self.current_url.get(serial)
            if prev is not None and prev != event.ai_url:
                synths.append(Event(
                    ts_ns=event.ts_ns,
                    kind=SYNTH_SWITCHED,
                    host=host or self.device_host.get(serial),
                    device_serial=serial,
                    ai_url=event.ai_url,
                    prev_ai_url=prev,
                ))
            self.current_url[serial] = event.ai_url

        return synths

    def check_offline(self, now_ns: int | None = None) -> list[Event]:
        """Scan for devices/hosts that have gone silent. Call periodically."""
        if now_ns is None:
            now_ns = int(time.time() * _NANO)

        synths: list[Event] = []
        threshold = now_ns - self.offline_grace_ns

        for serial, last_ts in list(self.device_last_seen.items()):
            if last_ts < threshold and not self.device_offline.get(serial):
                self.device_offline[serial] = True
                synths.append(Event(
                    ts_ns=now_ns,
                    kind=SYNTH_DEVICE_OFFLINE,
                    host=self.device_host.get(serial),
                    device_serial=serial,
                ))

        for host, last_ts in list(self.host_last_seen.items()):
            if last_ts < threshold and not self.host_offline.get(host):
                self.host_offline[host] = True
                synths.append(Event(
                    ts_ns=now_ns,
                    kind=SYNTH_HOST_OFFLINE,
                    host=host,
                ))

        return synths

    def get_snapshot(self) -> dict[str, Any]:
        """Return the current state as a JSON-serialisable dict."""
        servers: dict[str, dict] = {}
        hosts: dict[str, dict] = {}
        devices: dict[str, dict] = {}
        edges: list[dict] = []

        for serial, url in self.current_url.items():
            host = self.device_host.get(serial)
            is_offline = self.device_offline.get(serial, False)
            status = "offline" if is_offline else "online"

            devices[serial] = {
                "serial": serial,
                "host": host,
                "ai_url": url,
                "status": status,
                "last_seen_ns": self.device_last_seen.get(serial),
            }

            # Server node
            if url not in servers:
                servers[url] = {"url": url, "device_count": 0}
            servers[url]["device_count"] += 1

            # Host node
            if host and host not in hosts:
                host_offline = self.host_offline.get(host, False)
                hosts[host] = {
                    "name": host,
                    "status": "offline" if host_offline else "online",
                    "last_seen_ns": self.host_last_seen.get(host),
                    "device_count": len(self.host_devices.get(host, set())),
                }

            # Edges
            if host:
                edges.append({"from": serial, "to": host, "type": "device_host"})
            edges.append({
                "from": serial,
                "to": url,
                "type": "device_server",
                "status": status,
            })

        return {
            "servers": list(servers.values()),
            "hosts": list(hosts.values()),
            "devices": list(devices.values()),
            "edges": edges,
        }

    def rebuild_from_events(self, events: list[dict]) -> None:
        """Replay a list of stored event dicts to rebuild in-memory state."""
        for ev_dict in events:
            kind = ev_dict.get("kind", "")
            if kind.startswith("synth_"):
                continue
            ev = Event(
                ts_ns=ev_dict["ts_ns"],
                kind=kind,
                host=ev_dict.get("host"),
                device_serial=ev_dict.get("device_serial"),
                ai_url=ev_dict.get("ai_url"),
                status=ev_dict.get("status"),
            )
            self.process(ev)
