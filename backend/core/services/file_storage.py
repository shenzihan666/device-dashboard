"""File storage service for handling uploaded files.

Provides secure file storage with CAS deduplication, gzip compression,
disk watermark enforcement, and per-identity quota checks.
"""

from __future__ import annotations

import gzip
import hashlib
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from backend.config import Settings, get_settings
from backend.core.services.cas_storage import link_blob, store_blob
from backend.core.services.upload_quota import (
    DiskWatermarkExceeded,
    QuotaExceeded,
    check_disk_watermark,
    check_identity_quota,
)

logger = structlog.get_logger(__name__)

SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
_NANO = 1_000_000_000


def _now_utc() -> datetime:
    """Get current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def _sanitize_segment(value: str, fallback: str = "unknown") -> str:
    """Sanitize a path segment to be safe for filesystem use."""
    cleaned = SAFE_SEGMENT_RE.sub("-", value.strip()).strip("-.")
    result = cleaned or fallback
    logger.debug("segment_sanitized", original=value, sanitized=result)
    return result


def _safe_filename(filename: str) -> str:
    """Create a safe filename from potentially unsafe input."""
    path = Path(filename)
    stem = _sanitize_segment(path.stem, "upload")
    ext = path.suffix.lower()
    result = f"{stem}{ext}"
    logger.debug("filename_sanitized", original=filename, safe=result)
    return result


def _checksum_file(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(1024 * 1024), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    logger.debug("checksum_computed", file_path=str(file_path), checksum=checksum)
    return checksum


def build_storage_path(
    *,
    upload_dir: Path,
    source_system: str,
    identity: str,
    upload_kind: str,
    uploaded_at: datetime,
    original_filename: str,
    is_compressed: bool = False,
) -> Path:
    """Build a structured storage path for an uploaded file.

    Path structure:
        {upload_dir}/{source_system}/{identity}/{upload_kind}/{date}/{time}-{safe_filename}
    """
    date_segment = uploaded_at.strftime("%Y-%m-%d")
    time_segment = uploaded_at.strftime("%H%M%S")
    safe_source = _sanitize_segment(source_system, "source")
    safe_kind = _sanitize_segment(upload_kind, "upload")
    safe_identity = _sanitize_segment(identity, "unknown")
    safe_filename = _safe_filename(original_filename)

    if is_compressed and not safe_filename.endswith(".gz"):
        safe_filename += ".gz"

    path = (
        upload_dir
        / safe_source
        / safe_identity
        / safe_kind
        / date_segment
        / f"{time_segment}-{safe_filename}"
    )

    logger.debug(
        "storage_path_built",
        original_filename=original_filename,
        storage_path=str(path),
        source_system=source_system,
        identity=identity,
        upload_kind=upload_kind,
        uploaded_at=uploaded_at.isoformat(),
    )

    return path


def _should_compress(filename: str, compress_kinds: list[str]) -> bool:
    """Check if the file extension is in the compress list."""
    ext = Path(filename).suffix.lower()
    return ext in compress_kinds


def _gzip_file(src: Path, dst: Path) -> None:
    """Gzip *src* into *dst*."""
    with src.open("rb") as f_in, gzip.open(dst, "wb", compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)


class FileStorageService:
    """Service for handling file storage operations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.upload_dir = self.settings.upload_dir
        self.allowed_extensions = set(self.settings.upload_allowed_extensions)
        self.max_size_bytes = self.settings.upload_max_size_mb * 1024 * 1024

        logger.info(
            "file_storage_initialized",
            upload_dir=str(self.upload_dir),
            allowed_extensions=list(self.allowed_extensions),
            max_size_mb=self.settings.upload_max_size_mb,
        )

    def validate_extension(self, filename: str) -> tuple[bool, str]:
        """Validate file extension against allowed list."""
        ext = Path(filename).suffix.lower()
        if not ext:
            logger.warning("upload_no_extension", filename=filename)
            return False, "No file extension provided"

        if ext not in self.allowed_extensions:
            allowed = ", ".join(sorted(self.allowed_extensions))
            logger.warning(
                "upload_invalid_extension",
                filename=filename,
                extension=ext,
                allowed=allowed,
            )
            return False, f"Unsupported file type: {ext}. Allowed: {allowed}"

        logger.debug("upload_extension_validated", filename=filename, extension=ext)
        return True, "OK"

    def validate_size(self, size_bytes: int) -> tuple[bool, str]:
        """Validate file size against maximum limit."""
        if size_bytes > self.max_size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            logger.warning(
                "upload_size_exceeded",
                size_bytes=size_bytes,
                size_mb=round(size_mb, 2),
                max_size_bytes=self.max_size_bytes,
                max_size_mb=self.settings.upload_max_size_mb,
            )
            return False, (
                f"File too large: {size_mb:.2f} MB. "
                f"Maximum allowed: {self.settings.upload_max_size_mb} MB"
            )

        logger.debug(
            "upload_size_validated", size_bytes=size_bytes, max_size_bytes=self.max_size_bytes
        )
        return True, "OK"

    async def save_upload(
        self,
        *,
        file: Any,  # FastAPI UploadFile
        source_system: str,
        upload_kind: str,
        uploaded_at: datetime | None = None,
        device_id: str | None = None,
        hostname: str | None = None,
        person_name: str | None = None,
        client_gzipped: bool = False,
    ) -> dict[str, Any]:
        """Save an uploaded file to storage with CAS dedup and optional gzip.

        Args:
            file: FastAPI UploadFile object
            source_system: Source system identifier
            upload_kind: Type of upload
            uploaded_at: Upload timestamp (defaults to now)
            device_id: Optional device identifier
            hostname: Optional hostname identifier
            person_name: Optional person identifier
            client_gzipped: True if the client already sent gzipped content

        Returns:
            Dictionary with upload result metadata

        Raises:
            ValueError: If validation fails
            DiskWatermarkExceeded: If disk usage is too high
            QuotaExceeded: If identity quota is exceeded
        """
        start_time_ns = time.time_ns()
        upload_id = str(uuid4())
        filename = file.filename or "unknown.bin"
        content_type = file.content_type or "application/octet-stream"

        identity = device_id or hostname or person_name or source_system

        logger.info(
            "upload_started",
            upload_id=upload_id,
            filename=filename,
            content_type=content_type,
            source_system=source_system,
            upload_kind=upload_kind,
            device_id=device_id,
            hostname=hostname,
            person_name=person_name,
            identity=identity,
        )

        # Validate extension
        valid_ext, ext_msg = self.validate_extension(filename)
        if not valid_ext:
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.error(
                "upload_failed_validation",
                upload_id=upload_id,
                filename=filename,
                reason=ext_msg,
                duration_ms=round(duration_ms, 2),
            )
            raise ValueError(ext_msg)

        # Get file size by reading
        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)

        # Validate size
        valid_size, size_msg = self.validate_size(size_bytes)
        if not valid_size:
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.error(
                "upload_failed_size_check",
                upload_id=upload_id,
                filename=filename,
                size_bytes=size_bytes,
                reason=size_msg,
                duration_ms=round(duration_ms, 2),
            )
            raise ValueError(size_msg)

        if uploaded_at is None:
            uploaded_at = _now_utc()

        # --- Step 1: stream to temp file + compute SHA-256 ---
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            dir=str(self.upload_dir) if self.upload_dir.exists() else None,
            prefix="upload-",
        )
        tmp_path = Path(tmp_path_str)
        try:
            sha256 = hashlib.sha256()
            with open(tmp_fd, "wb") as tmp_fh:
                while True:
                    chunk = file.file.read(1024 * 1024)
                    if not chunk:
                        break
                    sha256.update(chunk)
                    tmp_fh.write(chunk)

            checksum = sha256.hexdigest()
            stored_size = tmp_path.stat().st_size

            # --- Step 2: gzip if needed ---
            should_gz = _should_compress(filename, self.settings.upload_compress_kinds)
            is_compressed = False

            if client_gzipped:
                is_compressed = True
            elif should_gz:
                gz_path = tmp_path.with_suffix(tmp_path.suffix + ".gz")
                _gzip_file(tmp_path, gz_path)
                tmp_path.unlink()
                tmp_path = gz_path
                stored_size = tmp_path.stat().st_size
                is_compressed = True
                logger.info(
                    "upload_gzipped",
                    upload_id=upload_id,
                    original_size=size_bytes,
                    compressed_size=stored_size,
                )

            # --- Step 3: quota / watermark pre-checks ---
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            check_disk_watermark(self.upload_dir, self.settings.upload_disk_watermark_pct)
            quota_bytes = self.settings.upload_quota_per_identity_gb * 1024 * 1024 * 1024
            safe_identity = _sanitize_segment(identity, "unknown")
            check_identity_quota(self.upload_dir, safe_identity, quota_bytes)

            # --- Step 4: CAS store + hardlink ---
            if self.settings.upload_dedup_enabled:
                blob_path = store_blob(tmp_path, checksum, self.upload_dir)
                storage_path = build_storage_path(
                    upload_dir=self.upload_dir,
                    source_system=source_system,
                    identity=identity,
                    upload_kind=upload_kind,
                    uploaded_at=uploaded_at,
                    original_filename=filename,
                    is_compressed=is_compressed,
                )
                link_blob(blob_path, storage_path)
                stored_size = storage_path.stat().st_size
            else:
                storage_path = build_storage_path(
                    upload_dir=self.upload_dir,
                    source_system=source_system,
                    identity=identity,
                    upload_kind=upload_kind,
                    uploaded_at=uploaded_at,
                    original_filename=filename,
                    is_compressed=is_compressed,
                )
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(tmp_path), str(storage_path))

            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            size_kb = stored_size / 1024
            size_mb = size_kb / 1024

            logger.info(
                "upload_completed",
                upload_id=upload_id,
                filename=filename,
                stored_path=str(storage_path),
                size_bytes=stored_size,
                size_kb=round(size_kb, 2),
                size_mb=round(size_mb, 2),
                checksum=checksum,
                compressed=is_compressed,
                dedup=self.settings.upload_dedup_enabled,
                source_system=source_system,
                upload_kind=upload_kind,
                device_id=device_id,
                hostname=hostname,
                person_name=person_name,
                duration_ms=round(duration_ms, 2),
            )

            return {
                "upload_id": upload_id,
                "filename": filename,
                "stored_path": str(storage_path),
                "size": stored_size,
                "checksum": checksum,
                "uploaded_at": uploaded_at,
                "source_system": source_system,
                "upload_kind": upload_kind,
                "device_id": device_id,
                "hostname": hostname,
                "person_name": person_name,
                "message": f"File '{filename}' uploaded successfully",
            }

        except (DiskWatermarkExceeded, QuotaExceeded):
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.error(
                "upload_unexpected_error",
                upload_id=upload_id,
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise
