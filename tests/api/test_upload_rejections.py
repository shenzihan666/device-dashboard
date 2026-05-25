"""API-level tests for upload quota (413) and watermark (507) rejections."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.config import Settings, get_settings
from backend.main import create_app


@pytest.fixture
def test_upload_dir(tmp_path: Path) -> Path:
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def test_settings(test_upload_dir: Path) -> Settings:
    return Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        log_level="DEBUG",
        log_format="console",
        upload_dir=test_upload_dir,
        upload_retention_days=30,
        upload_quota_per_identity_gb=5,
        upload_disk_watermark_pct=85,
        upload_disk_emergency_pct=95,
        upload_dedup_enabled=True,
    )


@pytest_asyncio.fixture
async def upload_client(
    test_settings: Settings,
) -> AsyncClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

    from backend.core.services.state_projector import StateProjector
    from backend.infrastructure.websocket.broadcaster import Broadcaster

    app.state.projector = StateProjector(offline_grace_ns=90 * 1_000_000_000)
    app.state.broadcaster = Broadcaster()
    app.state.poller = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_upload_data(content: bytes = b"hello world log") -> dict:
    return {
        "upload_kind": "scanner-log",
        "device_id": "dev-001",
        "hostname": "host-001",
        "person_name": "",
        "uploaded_at": "2026-05-25T02:00:00+08:00",
        "checksum": "",
    }


class TestUploadQuotaRejection:
    @pytest.mark.asyncio
    async def test_returns_413_when_quota_exceeded(self, upload_client: AsyncClient) -> None:
        with patch(
            "backend.core.services.file_storage.check_identity_quota",
            side_effect=__import__(
                "backend.core.services.upload_quota", fromlist=["QuotaExceeded"]
            ).QuotaExceeded("over quota"),
        ):
            resp = await upload_client.post(
                "/api/android-logs/upload",
                data=_make_upload_data(),
                files={"file": ("test.log", io.BytesIO(b"data"), "application/octet-stream")},
            )
        assert resp.status_code == 413


class TestUploadWatermarkRejection:
    @pytest.mark.asyncio
    async def test_returns_507_when_disk_full(self, upload_client: AsyncClient) -> None:
        with patch(
            "backend.core.services.file_storage.check_disk_watermark",
            side_effect=__import__(
                "backend.core.services.upload_quota", fromlist=["DiskWatermarkExceeded"]
            ).DiskWatermarkExceeded("disk full"),
        ):
            resp = await upload_client.post(
                "/api/android-logs/upload",
                data=_make_upload_data(),
                files={"file": ("test.log", io.BytesIO(b"data"), "application/octet-stream")},
            )
        assert resp.status_code == 507


class TestStorageStatsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_stats(self, upload_client: AsyncClient) -> None:
        resp = await upload_client.get("/api/uploads/storage-stats")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "disk_usage_pct" in body
        assert "retention_days" in body
        assert body["dedup_enabled"] is True
