"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from backend.api.schemas.common import APIResponse
from backend.api.schemas.events import EventQueryParams, EventResponse
from backend.api.schemas.layout import LayoutSaveRequest, NodePosition


class TestAPIResponse:
    def test_success_response(self):
        resp = APIResponse(data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.error is None

    def test_error_response(self):
        resp = APIResponse(success=False, error="something went wrong", error_code="BAD_REQUEST")
        assert resp.success is False
        assert resp.error == "something went wrong"
        assert resp.data is None


class TestEventQueryParams:
    def test_valid_params(self):
        params = EventQueryParams(limit=100)
        assert params.limit == 100
        assert params.from_ns is None

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            EventQueryParams(limit=0)
        with pytest.raises(ValidationError):
            EventQueryParams(limit=20000)

    def test_alias_population(self):
        params = EventQueryParams.model_validate({"from": 1000, "to": 2000, "limit": 50})
        assert params.from_ns == 1000
        assert params.to_ns == 2000


class TestEventResponse:
    def test_full_event(self):
        ev = EventResponse(
            id=1,
            ts_ns=1778150882084678300,
            kind="ai_server_observed",
            host="DESKTOP-TEST",
            device_serial="ABC123",
            ai_url="http://10.0.0.1:8000/chat",
        )
        assert ev.id == 1
        assert ev.kind == "ai_server_observed"

    def test_minimal_event(self):
        ev = EventResponse(id=2, ts_ns=100, kind="test")
        assert ev.host is None
        assert ev.payload_json is None


class TestLayoutSchemas:
    def test_valid_layout_request(self):
        req = LayoutSaveRequest(positions=[NodePosition(node_id="n1", x=1.0, y=2.0)])
        assert len(req.positions) == 1

    def test_empty_positions_rejected(self):
        with pytest.raises(ValidationError):
            LayoutSaveRequest(positions=[])
