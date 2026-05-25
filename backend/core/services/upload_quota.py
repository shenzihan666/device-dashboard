"""Disk watermark and per-identity quota enforcement for uploads."""

from __future__ import annotations

import shutil
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class QuotaExceeded(ValueError):
    """Raised when an identity's cumulative upload size exceeds its quota."""


class DiskWatermarkExceeded(Exception):
    """Raised when the partition holding upload_dir crosses the watermark."""


def get_disk_usage_pct(path: Path) -> float:
    """Return disk usage percentage for the partition containing *path*."""
    usage = shutil.disk_usage(path)
    pct = (usage.used / usage.total) * 100
    return round(pct, 2)


def check_disk_watermark(upload_dir: Path, watermark_pct: int) -> None:
    """Raise ``DiskWatermarkExceeded`` if disk usage >= *watermark_pct*."""
    target = upload_dir if upload_dir.exists() else upload_dir.parent
    pct = get_disk_usage_pct(target)
    if pct >= watermark_pct:
        logger.warning(
            "upload_rejected_watermark",
            disk_usage_pct=pct,
            watermark_pct=watermark_pct,
            path=str(target),
        )
        raise DiskWatermarkExceeded(f"Disk usage {pct}% exceeds watermark {watermark_pct}%")


def get_identity_usage_bytes(upload_dir: Path, identity: str) -> int:
    """Sum the on-disk size of all files stored for *identity* across source dirs."""
    total = 0
    if not upload_dir.exists():
        return 0
    for source_dir in upload_dir.iterdir():
        if not source_dir.is_dir() or source_dir.name.startswith("."):
            continue
        identity_dir = source_dir / identity
        if not identity_dir.is_dir():
            continue
        for f in identity_dir.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    return total


def check_identity_quota(upload_dir: Path, identity: str, quota_bytes: int) -> None:
    """Raise ``QuotaExceeded`` if *identity*'s total usage >= *quota_bytes*."""
    used = get_identity_usage_bytes(upload_dir, identity)
    if used >= quota_bytes:
        used_mb = round(used / (1024 * 1024), 2)
        quota_mb = round(quota_bytes / (1024 * 1024), 2)
        logger.warning(
            "upload_rejected_quota",
            identity=identity,
            used_mb=used_mb,
            quota_mb=quota_mb,
        )
        raise QuotaExceeded(f"Identity '{identity}' usage {used_mb} MB exceeds quota {quota_mb} MB")
