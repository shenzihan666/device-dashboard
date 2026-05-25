"""Background retention sweeper for uploaded files.

Periodically removes files older than ``upload_retention_days`` and runs
CAS blob garbage collection.  When disk usage exceeds the emergency
threshold, the oldest date-directories are deleted until usage drops below
the watermark.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import structlog

from backend.config import Settings
from backend.core.services.cas_storage import BLOBS_DIR_NAME, gc_orphan_blobs
from backend.core.services.upload_quota import get_disk_usage_pct

logger = structlog.get_logger(__name__)


class RetentionSweeper:
    """Async background task that enforces retention and disk limits."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._upload_dir = settings.upload_dir
        self._retention_days = settings.upload_retention_days
        self._watermark_pct = settings.upload_disk_watermark_pct
        self._emergency_pct = settings.upload_disk_emergency_pct
        self._interval_s = settings.upload_sweeper_interval_min * 60
        self._task: asyncio.Task[None] | None = None
        self._running = False

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "retention_sweeper_started",
            retention_days=self._retention_days,
            interval_min=self._settings.upload_sweeper_interval_min,
        )

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("retention_sweeper_stopped")

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------

    async def _loop(self) -> None:
        while self._running:
            try:
                await asyncio.to_thread(self._sweep_once)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("retention_sweep_error", error=str(exc))
            try:
                await asyncio.sleep(self._interval_s)
            except asyncio.CancelledError:
                raise

    # ------------------------------------------------------------------
    # sweep logic (runs in a thread via asyncio.to_thread)
    # ------------------------------------------------------------------

    def _sweep_once(self) -> dict[str, Any]:
        t0 = time.monotonic()
        files_deleted = 0
        bytes_freed = 0

        if not self._upload_dir.exists():
            return {"files_deleted": 0, "bytes_freed": 0}

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)

        # Walk real files (skip .blobs)
        for f in self._iter_upload_files():
            try:
                st = f.stat()
                mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    size = st.st_size
                    f.unlink()
                    files_deleted += 1
                    bytes_freed += size
            except OSError:
                pass

        # Remove empty directories left behind
        self._prune_empty_dirs()

        # CAS orphan GC
        gc_stats = gc_orphan_blobs(self._upload_dir)

        # Emergency sweep if disk still critical
        emergency_freed = 0
        if self._disk_above(self._emergency_pct):
            emergency_freed = self._emergency_sweep()

        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        logger.info(
            "retention_sweep_completed",
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            blobs_gc=gc_stats.get("blobs_removed", 0),
            emergency_freed=emergency_freed,
            elapsed_ms=elapsed_ms,
        )
        return {
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed + emergency_freed,
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _iter_upload_files(self):
        """Yield all real upload files, skipping ``.blobs``."""
        for source_dir in self._upload_dir.iterdir():
            if not source_dir.is_dir() or source_dir.name == BLOBS_DIR_NAME:
                continue
            yield from source_dir.rglob("*")

    def _prune_empty_dirs(self) -> None:
        """Bottom-up removal of empty directories under upload_dir."""
        for source_dir in self._upload_dir.iterdir():
            if not source_dir.is_dir() or source_dir.name == BLOBS_DIR_NAME:
                continue
            for d in sorted(source_dir.rglob("*"), reverse=True):
                if d.is_dir():
                    try:
                        d.rmdir()
                    except OSError:
                        pass

    def _disk_above(self, pct: int) -> bool:
        target = self._upload_dir if self._upload_dir.exists() else self._upload_dir.parent
        return get_disk_usage_pct(target) >= pct

    def _emergency_sweep(self) -> int:
        """Delete oldest date-directories until disk usage drops below watermark."""
        logger.warning("upload_emergency_sweep", emergency_pct=self._emergency_pct)
        freed = 0
        dated_dirs = self._collect_dated_dirs()
        for d in dated_dirs:
            if not self._disk_above(self._watermark_pct):
                break
            for f in d.rglob("*"):
                if f.is_file():
                    try:
                        freed += f.stat().st_size
                        f.unlink()
                    except OSError:
                        pass
            try:
                for sub in sorted(d.rglob("*"), reverse=True):
                    if sub.is_dir():
                        try:
                            sub.rmdir()
                        except OSError:
                            pass
                d.rmdir()
            except OSError:
                pass

        if freed:
            gc_orphan_blobs(self._upload_dir)
            logger.info("upload_emergency_sweep_done", bytes_freed=freed)
        return freed

    def _collect_dated_dirs(self) -> list[Path]:
        """Collect all YYYY-MM-DD directories under uploads, sorted oldest first."""
        import re

        date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        dirs: list[tuple[str, Path]] = []
        for source_dir in self._upload_dir.iterdir():
            if not source_dir.is_dir() or source_dir.name == BLOBS_DIR_NAME:
                continue
            for d in source_dir.rglob("*"):
                if d.is_dir() and date_re.match(d.name):
                    dirs.append((d.name, d))
        dirs.sort(key=lambda x: x[0])
        return [d for _, d in dirs]
