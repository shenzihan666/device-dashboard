"""Tests for the retention sweeper background service."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from backend.config import Settings
from backend.core.services.cas_storage import blob_path_for
from backend.core.services.retention_sweeper import RetentionSweeper


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def settings(upload_dir: Path) -> Settings:
    return Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        upload_dir=upload_dir,
        upload_retention_days=30,
        upload_disk_watermark_pct=85,
        upload_disk_emergency_pct=95,
        upload_sweeper_interval_min=60,
    )


def _write(path: Path, content: bytes = b"data") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _age_file(path: Path, days: int) -> None:
    """Set mtime to *days* ago."""
    old_ts = time.time() - (days * 86400)
    os.utime(path, (old_ts, old_ts))


class TestSweepOnce:
    def test_deletes_files_older_than_retention(self, settings: Settings, upload_dir: Path) -> None:
        old_file = upload_dir / "src" / "dev1" / "log" / "2026-04-01" / "020000-test.log"
        _write(old_file, b"old data")
        _age_file(old_file, days=31)

        new_file = upload_dir / "src" / "dev1" / "log" / "2026-05-20" / "020000-test.log"
        _write(new_file, b"new data")

        sweeper = RetentionSweeper(settings)
        result = sweeper._sweep_once()

        assert not old_file.exists()
        assert new_file.exists()
        assert result["files_deleted"] >= 1

    def test_prunes_empty_directories(self, settings: Settings, upload_dir: Path) -> None:
        f = upload_dir / "src" / "dev1" / "log" / "2026-04-01" / "020000-test.log"
        _write(f, b"x")
        _age_file(f, days=31)

        sweeper = RetentionSweeper(settings)
        sweeper._sweep_once()

        assert not f.parent.exists()

    def test_does_not_touch_blobs_directly(self, settings: Settings, upload_dir: Path) -> None:
        blob = blob_path_for(upload_dir, "aabbccdd")
        _write(blob, b"blob data")
        _age_file(blob, days=60)

        # Create a ref so GC doesn't remove it
        ref = upload_dir / "src" / "dev1" / "log" / "2026-05-24" / "ref.log"
        _write(ref)
        os.link(blob, upload_dir / "ref-link")

        sweeper = RetentionSweeper(settings)
        sweeper._sweep_once()

        assert blob.exists()

    def test_gc_removes_orphan_blobs_after_sweep(
        self, settings: Settings, upload_dir: Path
    ) -> None:
        blob = blob_path_for(upload_dir, "orphan123")
        _write(blob, b"orphan")

        sweeper = RetentionSweeper(settings)
        sweeper._sweep_once()

        assert not blob.exists()


class TestEmergencySweep:
    def test_deletes_oldest_dirs_when_disk_critical(
        self, settings: Settings, upload_dir: Path
    ) -> None:
        d1 = upload_dir / "src" / "dev1" / "log" / "2026-04-01"
        _write(d1 / "a.log", b"oldest")

        d2 = upload_dir / "src" / "dev1" / "log" / "2026-05-20"
        _write(d2 / "b.log", b"newer")

        sweeper = RetentionSweeper(settings)

        call_count = 0

        def fake_disk_above(pct):
            nonlocal call_count
            call_count += 1
            return call_count <= 1

        sweeper._disk_above = fake_disk_above
        freed = sweeper._emergency_sweep()

        assert freed > 0
