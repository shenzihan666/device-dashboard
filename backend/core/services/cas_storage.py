"""Content-addressable blob storage with hardlink-based deduplication."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

BLOBS_DIR_NAME = ".blobs"


def _blobs_root(upload_dir: Path) -> Path:
    return upload_dir / BLOBS_DIR_NAME


def blob_path_for(upload_dir: Path, sha256: str) -> Path:
    """Return the canonical blob path for a given SHA-256 hex digest."""
    return _blobs_root(upload_dir) / sha256[:2] / sha256


def store_blob(source: Path, sha256: str, upload_dir: Path) -> Path:
    """Move *source* into the CAS blob store.

    If a blob with the same digest already exists the source is deleted and the
    existing path is returned (idempotent).
    """
    dst = blob_path_for(upload_dir, sha256)
    if dst.exists():
        logger.debug("cas_blob_exists", sha256=sha256)
        try:
            source.unlink()
        except OSError:
            pass
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dst))
    logger.info("cas_blob_stored", sha256=sha256, size=dst.stat().st_size)
    return dst


def link_blob(blob_path: Path, dst_path: Path) -> None:
    """Create a hardlink from *blob_path* to *dst_path*.

    Falls back to ``shutil.copy2`` when the two paths reside on different
    filesystems (cross-device link).
    """
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(blob_path, dst_path)
        logger.debug("cas_hardlink_created", dst=str(dst_path))
    except OSError:
        shutil.copy2(blob_path, dst_path)
        logger.debug("cas_copy_fallback", dst=str(dst_path))


def gc_orphan_blobs(upload_dir: Path) -> dict[str, int]:
    """Remove blobs whose link count has dropped to 1 (no references).

    Returns a summary dict with ``blobs_scanned`` and ``blobs_removed``.
    """
    blobs_root = _blobs_root(upload_dir)
    if not blobs_root.exists():
        return {"blobs_scanned": 0, "blobs_removed": 0, "bytes_freed": 0}

    scanned = 0
    removed = 0
    freed = 0

    for prefix_dir in sorted(blobs_root.iterdir()):
        if not prefix_dir.is_dir():
            continue
        for blob in sorted(prefix_dir.iterdir()):
            if not blob.is_file():
                continue
            scanned += 1
            try:
                st = blob.stat()
                if st.st_nlink <= 1:
                    freed += st.st_size
                    blob.unlink()
                    removed += 1
            except OSError:
                pass
        # Remove empty prefix dirs
        try:
            prefix_dir.rmdir()
        except OSError:
            pass

    logger.info(
        "cas_blob_gc",
        blobs_scanned=scanned,
        blobs_removed=removed,
        bytes_freed=freed,
    )
    return {"blobs_scanned": scanned, "blobs_removed": removed, "bytes_freed": freed}
