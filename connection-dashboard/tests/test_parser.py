"""Golden-line tests for each log shape parser."""

from backend.events import (
    AI_HEALTH_CHECK,
    AI_SERVER_OBSERVED,
    DEVICE_ERROR,
    HOST_DEVICE_MAP,
    METRIC_EVENT,
    SIDECAR_ERROR,
)
from backend.parser import (
    parse_ai_server,
    parse_device_error,
    parse_health_check,
    parse_host_device_map,
    parse_metrics_event,
    parse_row,
    parse_sidecar_error,
)

TS = 1778150882084678300
HOST = "DESKTOP-8THEIVC"


class TestAIServerObserved:
    LINE = (
        "2026-05-07 18:48:07 | INFO     | "
        "services.followup.response_detector:_generate_reply:2587 | "
        "[10AE9X304J0033Z] AI Server: http://118.31.238.44:8000/chat"
    )

    def test_parse(self):
        ev = parse_ai_server(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == AI_SERVER_OBSERVED
        assert ev.device_serial == "10AE9X304J0033Z"
        assert ev.ai_url == "http://118.31.238.44:8000/chat"
        assert ev.host == HOST

    def test_no_match(self):
        assert parse_ai_server("random log line", TS, HOST) is None

    def test_via_parse_row(self):
        labels = f"{{'host': '{HOST}', 'job': 'wecom-sidecar-logs'}}"
        ev = parse_row(self.LINE, TS, labels, ref="A")
        assert ev is not None
        assert ev.kind == AI_SERVER_OBSERVED
        assert ev.host == HOST


class TestHealthCheck:
    LINE = (
        "2026-05-07 18:49:02 | INFO     | "
        "services.ai_health_checker:_loop:255 | "
        "[AIHealthChecker] status=healthy network=reachable http=alive "
        "inference=None time=94ms"
    )

    def test_parse(self):
        ev = parse_health_check(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == AI_HEALTH_CHECK
        assert ev.status == "healthy"
        assert ev.latency_ms == 94
        assert ev.payload["network"] == "reachable"

    def test_no_match(self):
        assert parse_health_check("something else", TS, HOST) is None


class TestSidecarError:
    LINE = (
        "2026-05-07 16:13:55 | WARNING  | "
        "wecom_automation.services.integration.sidecar:_request_with_retry:144 | "
        "Transient error (attempt 1/3): Server disconnected, reconnecting in 0.5s..."
    )

    def test_parse(self):
        ev = parse_sidecar_error(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == SIDECAR_ERROR
        assert ev.status == "error"
        assert ev.payload["attempt"] == 1
        assert ev.payload["max_attempts"] == 3
        assert "Server disconnected" in ev.payload["message"]


class TestDeviceError:
    LINE = (
        "2026-05-07 13:59:45 | ERROR    | "
        "services.followup.response_detector:_generate_reply:2745 | "
        "[10AE9X304J0033Z] Error: Server disconnected"
    )

    def test_parse(self):
        ev = parse_device_error(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == DEVICE_ERROR
        assert ev.device_serial == "10AE9X304J0033Z"
        assert ev.payload["message"] == "Server disconnected"

    def test_via_parse_row_ref_c(self):
        labels = {"host": HOST}
        ev = parse_row(self.LINE, TS, labels, ref="C")
        assert ev is not None
        assert ev.kind == DEVICE_ERROR


class TestMetricsEvent:
    LINE = (
        '2026-05-07 18:49:44 | INFO     | '
        'wecom_automation.core.metrics_logger:_emit:119 | '
        '{"timestamp": "2026-05-07T18:49:44.467965", "level": "METRIC", '
        '"event": "session_summary", "session_id": "9d83e495", '
        '"device_serial": "10AEC61XMY00773", "data": {"duration_seconds": 4998.27}}'
    )

    def test_parse(self):
        ev = parse_metrics_event(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == METRIC_EVENT
        assert ev.device_serial == "10AEC61XMY00773"
        assert ev.session_id == "9d83e495"
        assert ev.payload["event"] == "session_summary"

    def test_bad_json(self):
        bad = "metrics_logger:_emit:119 | {not json"
        assert parse_metrics_event(bad, TS, HOST) is None


class TestHostDeviceMap:
    LINE = (
        "2026-05-07 18:48:02 | INFO     | "
        "wecom_automation.services.adb_service:_trace_start:157 | "
        "[ADB_TRACE] serial=10AEC61XMY00773 pid=7612 step=get_state "
        "event=start caller=refresh_ui_state"
    )

    def test_parse(self):
        ev = parse_host_device_map(self.LINE, TS, HOST)
        assert ev is not None
        assert ev.kind == HOST_DEVICE_MAP
        assert ev.device_serial == "10AEC61XMY00773"
        assert ev.host == HOST

    def test_no_host_returns_none(self):
        assert parse_host_device_map(self.LINE, TS, None) is None

    def test_bracket_serial(self):
        line = "[15787989750086X] some other log"
        ev = parse_host_device_map(line, TS, HOST)
        assert ev is not None
        assert ev.device_serial == "15787989750086X"
