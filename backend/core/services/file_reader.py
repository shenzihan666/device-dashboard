"""Efficient line-based file reader for large log files.

Uses cached newline-offset indices for O(1) random access to any line range.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NamedTuple

import structlog

logger = structlog.get_logger(__name__)

DEFAULT_PAGE_SIZE = 500
MAX_PAGE_SIZE = 2000

TEXT_EXTENSIONS = frozenset({".log", ".jsonl"})


class LineIndex(NamedTuple):
    offsets: list[int]  # byte offset of each line start
    mtime: float
    size: int


_index_cache: dict[str, LineIndex] = {}
_MAX_CACHE = 64


def compute_file_id(file_path: Path, base_dir: Path) -> str:
    rel = str(file_path.relative_to(base_dir))
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()


def _evict_cache() -> None:
    if len(_index_cache) > _MAX_CACHE:
        oldest = list(_index_cache.keys())[: len(_index_cache) - _MAX_CACHE]
        for key in oldest:
            del _index_cache[key]


def build_line_index(file_path: Path) -> LineIndex:
    key = str(file_path)
    stat = file_path.stat()

    cached = _index_cache.get(key)
    if cached and cached.mtime == stat.st_mtime and cached.size == stat.st_size:
        return cached

    offsets: list[int] = [0]
    with file_path.open("rb") as f:
        while True:
            line = f.readline()
            if not line:
                break
            offsets.append(f.tell())

    # If the file does not end with a newline, the last entry is past-EOF
    if offsets and offsets[-1] == stat.st_size:
        offsets.pop()

    index = LineIndex(offsets=offsets, mtime=stat.st_mtime, size=stat.st_size)
    _index_cache[key] = index
    _evict_cache()
    logger.debug("line_index_built", file=str(file_path), lines=len(offsets))
    return index


def read_line_range(
    file_path: Path,
    offset: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[str], int]:
    """Read a range of lines from a file.

    Returns (lines, total_lines).
    """
    index = build_line_index(file_path)
    total_lines = len(index.offsets)

    start = max(0, offset)
    end = min(start + limit, total_lines)

    if start >= total_lines:
        return [], total_lines

    lines: list[str] = []
    with file_path.open("rb") as f:
        for line_num in range(start, end):
            f.seek(index.offsets[line_num])
            if line_num + 1 < len(index.offsets):
                raw = f.read(index.offsets[line_num + 1] - index.offsets[line_num])
            else:
                raw = f.read()
            lines.append(raw.decode("utf-8", errors="replace").rstrip("\n").rstrip("\r"))

    return lines, total_lines


def resolve_file_id(
    device_id: str,
    file_id: str,
    upload_dir: Path,
    sanitize_fn: object,
) -> Path | None:
    """Resolve a file_id back to a file path by scanning the device's upload tree.

    Args:
        device_id: Raw device identifier (serial number).
        file_id: SHA-256 hex digest of the file's relative path.
        upload_dir: Base upload directory.
        sanitize_fn: The _sanitize_segment function from file_storage.

    Returns:
        Resolved Path or None if not found.
    """
    from backend.core.services.file_storage import _sanitize_segment  # noqa: F811

    safe_identity = (
        sanitize_fn(device_id) if callable(sanitize_fn) else _sanitize_segment(device_id)
    )
    upload_dir = upload_dir.resolve()

    for source_dir in upload_dir.iterdir():
        if not source_dir.is_dir():
            continue
        identity_dir = source_dir / safe_identity
        if not identity_dir.is_dir():
            continue
        for f in identity_dir.rglob("*"):
            if not f.is_file():
                continue
            f_resolved = f.resolve()
            if not str(f_resolved).startswith(str(upload_dir)):
                continue
            if compute_file_id(f_resolved, upload_dir) == file_id:
                return f_resolved

    return None
