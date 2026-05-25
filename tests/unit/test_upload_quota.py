"""Tests for disk watermark and per-identity quota enforcement."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.core.services.upload_quota import (
    DiskWatermarkExceeded,
    QuotaExceeded,
    check_disk_watermark,
    check_identity_quota,
    get_disk_usage_pct,
    get_identity_usage_bytes,
)


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    d = tmp_path / "uploads"
    d.mkdir()
    return d


def _write(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00" * size)


class TestGetDiskUsagePct:
    def test_returns_float(self, tmp_path: Path) -> None:
        pct = get_disk_usage_pct(tmp_path)
        assert isinstance(pct, float)
        assert 0 <= pct <= 100


class TestCheckDiskWatermark:
    def test_passes_when_below(self, upload_dir: Path) -> None:
        check_disk_watermark(upload_dir, watermark_pct=99)

    def test_raises_when_above(self, upload_dir: Path) -> None:
        with patch("backend.core.services.upload_quota.get_disk_usage_pct", return_value=90.0):
            with pytest.raises(DiskWatermarkExceeded, match="90.0%"):
                check_disk_watermark(upload_dir, watermark_pct=85)


class TestGetIdentityUsageBytes:
    def test_sums_all_sources(self, upload_dir: Path) -> None:
        _write(upload_dir / "src1" / "dev1" / "a.log", 100)
        _write(upload_dir / "src2" / "dev1" / "b.log", 200)

        total = get_identity_usage_bytes(upload_dir, "dev1")
        assert total == 300

    def test_ignores_other_identities(self, upload_dir: Path) -> None:
        _write(upload_dir / "src1" / "dev1" / "a.log", 100)
        _write(upload_dir / "src1" / "dev2" / "b.log", 999)

        total = get_identity_usage_bytes(upload_dir, "dev1")
        assert total == 100

    def test_skips_blobs_dir(self, upload_dir: Path) -> None:
        _write(upload_dir / ".blobs" / "aa" / "aabb", 5000)
        total = get_identity_usage_bytes(upload_dir, "aabb")
        assert total == 0

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        assert get_identity_usage_bytes(tmp_path / "nope", "dev1") == 0


class TestCheckIdentityQuota:
    def test_passes_when_under(self, upload_dir: Path) -> None:
        _write(upload_dir / "src" / "dev1" / "f.log", 100)
        check_identity_quota(upload_dir, "dev1", quota_bytes=1024)

    def test_raises_when_over(self, upload_dir: Path) -> None:
        _write(upload_dir / "src" / "dev1" / "f.log", 2000)
        with pytest.raises(QuotaExceeded, match="dev1"):
            check_identity_quota(upload_dir, "dev1", quota_bytes=1000)
