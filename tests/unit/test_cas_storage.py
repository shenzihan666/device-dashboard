"""Tests for content-addressable blob storage."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.core.services.cas_storage import (
    BLOBS_DIR_NAME,
    blob_path_for,
    gc_orphan_blobs,
    link_blob,
    store_blob,
)


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    d = tmp_path / "uploads"
    d.mkdir()
    return d


def _write(path: Path, content: bytes = b"hello world") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class TestStoreBlob:
    def test_stores_new_blob(self, upload_dir: Path) -> None:
        src = upload_dir / "incoming.log"
        _write(src, b"log data")
        sha = "abc123"

        result = store_blob(src, sha, upload_dir)

        assert result == blob_path_for(upload_dir, sha)
        assert result.exists()
        assert result.read_bytes() == b"log data"
        assert not src.exists()

    def test_idempotent_on_duplicate(self, upload_dir: Path) -> None:
        sha = "deadbeef"
        blob = blob_path_for(upload_dir, sha)
        _write(blob, b"original")

        src = upload_dir / "dup.log"
        _write(src, b"duplicate")

        result = store_blob(src, sha, upload_dir)

        assert result == blob
        assert result.read_bytes() == b"original"
        assert not src.exists()


class TestLinkBlob:
    def test_creates_hardlink(self, upload_dir: Path) -> None:
        blob = upload_dir / BLOBS_DIR_NAME / "ab" / "abcdef"
        _write(blob, b"data")

        dst = upload_dir / "source" / "dev1" / "scanner-log" / "2026-05-25" / "020000-test.log.gz"
        link_blob(blob, dst)

        assert dst.exists()
        assert dst.read_bytes() == b"data"
        assert os.stat(blob).st_ino == os.stat(dst).st_ino

    def test_creates_parent_dirs(self, upload_dir: Path) -> None:
        blob = upload_dir / BLOBS_DIR_NAME / "ff" / "ff0011"
        _write(blob, b"x")

        dst = upload_dir / "a" / "b" / "c" / "file.db"
        link_blob(blob, dst)

        assert dst.exists()


class TestGcOrphanBlobs:
    def test_removes_orphan_blobs(self, upload_dir: Path) -> None:
        blob = blob_path_for(upload_dir, "deadbeef0000")
        _write(blob, b"orphan data")

        stats = gc_orphan_blobs(upload_dir)

        assert stats["blobs_scanned"] == 1
        assert stats["blobs_removed"] == 1
        assert stats["bytes_freed"] == len(b"orphan data")
        assert not blob.exists()

    def test_keeps_linked_blobs(self, upload_dir: Path) -> None:
        blob = blob_path_for(upload_dir, "aabbccdd")
        _write(blob, b"linked data")
        ref = upload_dir / "ref.log"
        os.link(blob, ref)

        stats = gc_orphan_blobs(upload_dir)

        assert stats["blobs_removed"] == 0
        assert blob.exists()
        assert ref.exists()

    def test_empty_blobs_dir(self, upload_dir: Path) -> None:
        stats = gc_orphan_blobs(upload_dir)
        assert stats == {"blobs_scanned": 0, "blobs_removed": 0, "bytes_freed": 0}
