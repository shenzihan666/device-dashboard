"""Tests for brain-server / WeCom-client edge matching in HeartbeatRegistry.

These cover the regression where every WeCom client points at the brain's
public IP (`http://118.31.238.44:8000`) while the brain reports a cloud
hostname (`iZbp1ew197l6kdw5vqrjd9Z:8000`) and no IP, leaving the canvas
without any client -> brain edges.
"""

from __future__ import annotations

from backend.api.routes.heartbeat_ws import _enrich_with_peer_ip
from backend.core.services.heartbeat_registry import _match_brain_url


def test_match_brain_url_by_public_ip() -> None:
    assert _match_brain_url(
        brain_url="http://118.31.238.44:8000",
        bs_instance_id="iZbp1ew197l6kdw5vqrjd9Z:8000",
        bs_name="iZbp1ew197l6kdw5vqrjd9Z",
        bs_ip="118.31.238.44",
    )


def test_match_brain_url_fails_without_ip_when_hosts_differ() -> None:
    """Original bug: with no public IP recorded, no edge is produced."""
    assert not _match_brain_url(
        brain_url="http://118.31.238.44:8000",
        bs_instance_id="iZbp1ew197l6kdw5vqrjd9Z:8000",
        bs_name="iZbp1ew197l6kdw5vqrjd9Z",
        bs_ip="",
    )


def test_match_brain_url_port_mismatch() -> None:
    assert not _match_brain_url(
        brain_url="http://118.31.238.44:9000",
        bs_instance_id="iZbp1ew197l6kdw5vqrjd9Z:8000",
        bs_name="iZbp1ew197l6kdw5vqrjd9Z",
        bs_ip="118.31.238.44",
    )


def test_match_brain_url_exact_host_match() -> None:
    assert _match_brain_url(
        brain_url="http://brain-1.internal:8000",
        bs_instance_id="brain-1.internal:8000",
        bs_name="brain-1.internal",
        bs_ip="",
    )


def test_enrich_with_peer_ip_fills_missing() -> None:
    data: dict = {"instance_id": "x", "instance_type": "brain_server"}
    _enrich_with_peer_ip(data, "118.31.238.44")
    assert data["ip"] == "118.31.238.44"


def test_enrich_with_peer_ip_preserves_reported_ip() -> None:
    data: dict = {"instance_id": "x", "ip": "10.0.0.5"}
    _enrich_with_peer_ip(data, "118.31.238.44")
    assert data["ip"] == "10.0.0.5"


def test_enrich_with_peer_ip_noop_when_peer_unknown() -> None:
    data: dict = {"instance_id": "x"}
    _enrich_with_peer_ip(data, "")
    assert "ip" not in data
