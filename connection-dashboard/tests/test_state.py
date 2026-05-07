"""Tests for switch detection, offline/online logic in StateProjector."""

from backend.events import (
    AI_HEALTH_CHECK,
    AI_SERVER_OBSERVED,
    SYNTH_DEVICE_OFFLINE,
    SYNTH_DEVICE_ONLINE,
    SYNTH_HOST_OFFLINE,
    SYNTH_HOST_ONLINE,
    SYNTH_SWITCHED,
    Event,
)
from backend.state import StateProjector

_NANO = 1_000_000_000
HOST = "DESKTOP-TEST"
SERIAL = "ABC123DEF456"
URL_A = "http://10.0.0.1:8000/chat"
URL_B = "http://10.0.0.2:8000/chat"


def _make_event(ts_s: int, url: str = URL_A, serial: str = SERIAL) -> Event:
    return Event(
        ts_ns=ts_s * _NANO,
        kind=AI_SERVER_OBSERVED,
        host=HOST,
        device_serial=serial,
        ai_url=url,
    )


class TestSwitchDetection:
    def test_no_switch_on_first_event(self):
        proj = StateProjector()
        synths = proj.process(_make_event(100, URL_A))
        assert not any(s.kind == SYNTH_SWITCHED for s in synths)

    def test_no_switch_same_url(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        synths = proj.process(_make_event(110, URL_A))
        assert not any(s.kind == SYNTH_SWITCHED for s in synths)

    def test_switch_detected(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        synths = proj.process(_make_event(110, URL_B))
        switches = [s for s in synths if s.kind == SYNTH_SWITCHED]
        assert len(switches) == 1
        assert switches[0].prev_ai_url == URL_A
        assert switches[0].ai_url == URL_B
        assert switches[0].device_serial == SERIAL

    def test_switch_back(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        proj.process(_make_event(110, URL_B))
        synths = proj.process(_make_event(120, URL_A))
        switches = [s for s in synths if s.kind == SYNTH_SWITCHED]
        assert len(switches) == 1
        assert switches[0].prev_ai_url == URL_B
        assert switches[0].ai_url == URL_A


class TestOfflineDetection:
    def test_device_goes_offline(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        proj.process(_make_event(100))
        synths = proj.check_offline(now_ns=200 * _NANO)
        offline_evs = [s for s in synths if s.kind == SYNTH_DEVICE_OFFLINE]
        assert len(offline_evs) == 1
        assert offline_evs[0].device_serial == SERIAL

    def test_device_not_offline_within_grace(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        proj.process(_make_event(100))
        synths = proj.check_offline(now_ns=105 * _NANO)
        assert not any(s.kind == SYNTH_DEVICE_OFFLINE for s in synths)

    def test_device_comes_back_online(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        proj.process(_make_event(100))
        proj.check_offline(now_ns=200 * _NANO)
        synths = proj.process(_make_event(210))
        online_evs = [s for s in synths if s.kind == SYNTH_DEVICE_ONLINE]
        assert len(online_evs) == 1
        assert online_evs[0].device_serial == SERIAL

    def test_no_duplicate_offline(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        proj.process(_make_event(100))
        synths1 = proj.check_offline(now_ns=200 * _NANO)
        synths2 = proj.check_offline(now_ns=300 * _NANO)
        assert len([s for s in synths1 if s.kind == SYNTH_DEVICE_OFFLINE]) == 1
        assert len([s for s in synths2 if s.kind == SYNTH_DEVICE_OFFLINE]) == 0


class TestHostOffline:
    def test_host_goes_offline(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        health = Event(
            ts_ns=100 * _NANO,
            kind=AI_HEALTH_CHECK,
            host=HOST,
            status="healthy",
            latency_ms=50,
        )
        proj.process(health)
        synths = proj.check_offline(now_ns=200 * _NANO)
        host_offline = [s for s in synths if s.kind == SYNTH_HOST_OFFLINE]
        assert len(host_offline) == 1
        assert host_offline[0].host == HOST

    def test_host_comes_back_online(self):
        proj = StateProjector(offline_grace_ns=10 * _NANO)
        health = Event(
            ts_ns=100 * _NANO,
            kind=AI_HEALTH_CHECK,
            host=HOST,
            status="healthy",
            latency_ms=50,
        )
        proj.process(health)
        proj.check_offline(now_ns=200 * _NANO)
        health2 = Event(
            ts_ns=210 * _NANO,
            kind=AI_HEALTH_CHECK,
            host=HOST,
            status="healthy",
            latency_ms=40,
        )
        synths = proj.process(health2)
        host_online = [s for s in synths if s.kind == SYNTH_HOST_ONLINE]
        assert len(host_online) == 1


class TestSnapshot:
    def test_snapshot_reflects_state(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        snap = proj.get_snapshot()
        assert len(snap["devices"]) == 1
        assert snap["devices"][0]["ai_url"] == URL_A
        assert len(snap["servers"]) == 1
        assert snap["servers"][0]["url"] == URL_A
        assert len(snap["hosts"]) == 1

    def test_snapshot_after_switch(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        proj.process(_make_event(110, URL_B))
        snap = proj.get_snapshot()
        assert snap["devices"][0]["ai_url"] == URL_B


class TestRebuild:
    def test_rebuild_from_events(self):
        proj = StateProjector()
        proj.process(_make_event(100, URL_A))
        proj.process(_make_event(110, URL_B))

        proj2 = StateProjector()
        proj2.rebuild_from_events(
            [
                {
                    "ts_ns": 100 * _NANO,
                    "kind": AI_SERVER_OBSERVED,
                    "host": HOST,
                    "device_serial": SERIAL,
                    "ai_url": URL_A,
                },
                {
                    "ts_ns": 110 * _NANO,
                    "kind": AI_SERVER_OBSERVED,
                    "host": HOST,
                    "device_serial": SERIAL,
                    "ai_url": URL_B,
                },
            ]
        )
        assert proj2.current_url[SERIAL] == URL_B
        assert proj2.get_snapshot() == proj.get_snapshot()
