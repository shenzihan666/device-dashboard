"""File storage service for handling uploaded files.

Provides secure file storage with detailed industrial-grade logging.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from backend.config import Settings, get_settings

logger = structlog.get_logger(__name__)

# Safe filename sanitization pattern
SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")
_NANO = 1_000_000_000


def _now_utc() -> datetime:
    """Get current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def _sanitize_segment(value: str, fallback: str = "unknown") -> str:
    """Sanitize a path segment to be safe for filesystem use.

    Args:
        value: The segment to sanitize
        fallback: Fallback value if sanitized result is empty

    Returns:
        Sanitized string safe for use in file paths
    """
    cleaned = SAFE_SEGMENT_RE.sub("-", value.strip()).strip("-.")
    result = cleaned or fallback
    logger.debug("segment_sanitized", original=value, sanitized=result)
    return result


def _safe_filename(filename: str) -> str:
    """Create a safe filename from potentially unsafe input.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    path = Path(filename)
    stem = _sanitize_segment(path.stem, "upload")
    ext = path.suffix.lower()
    result = f"{stem}{ext}"
    logger.debug("filename_sanitized", original=filename, safe=result)
    return result


def _checksum_file(file_path: Path) -> str:
    """Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal SHA256 checksum
    """
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
) -> Path:
    """Build a structured storage path for an uploaded file.

    Path structure:
        {upload_dir}/{source_system}/{identity}/{upload_kind}/{date}/{time}-{safe_filename}

    Args:
        upload_dir: Base upload directory
        source_system: Source system identifier
        identity: Device/host/person identifier
        upload_kind: Type of upload
        uploaded_at: Upload timestamp
        original_filename: Original filename

    Returns:
        Complete path where file should be stored
    """
    date_segment = uploaded_at.strftime("%Y-%m-%d")
    time_segment = uploaded_at.strftime("%H%M%S")
    safe_source = _sanitize_segment(source_system, "source")
    safe_kind = _sanitize_segment(upload_kind, "upload")
    safe_identity = _sanitize_segment(identity, "unknown")
    safe_filename = _safe_filename(original_filename)

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


class FileStorageService:
    """Service for handling file storage operations."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the file storage service.

        Args:
            settings: Application settings, uses get_settings() if None
        """
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
        """Validate file extension against allowed list.

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid, message)
        """
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
        """Validate file size against maximum limit.

        Args:
            size_bytes: File size in bytes

        Returns:
            Tuple of (is_valid, message)
        """
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
    ) -> dict[str, Any]:
        """Save an uploaded file to storage.

        Args:
            file: FastAPI UploadFile object
            source_system: Source system identifier
            upload_kind: Type of upload
            uploaded_at: Upload timestamp (defaults to now)
            device_id: Optional device identifier
            hostname: Optional hostname identifier
            person_name: Optional person identifier

        Returns:
            Dictionary with upload result metadata

        Raises:
            ValueError: If validation fails
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
        file.file.seek(0, 2)  # Seek to end
        size_bytes = file.file.tell()
        file.file.seek(0)  # Seek back to start

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

        # Build storage path
        storage_path = build_storage_path(
            upload_dir=self.upload_dir,
            source_system=source_system,
            identity=identity,
            upload_kind=upload_kind,
            uploaded_at=uploaded_at,
            original_filename=filename,
        )

        logger.debug(
            "upload_preparing_storage",
            upload_id=upload_id,
            storage_path=str(storage_path),
        )

        # Create directory structure
        try:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(
                "upload_directory_created",
                upload_id=upload_id,
                directory=str(storage_path.parent),
            )
        except Exception as e:
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.error(
                "upload_directory_create_failed",
                upload_id=upload_id,
                directory=str(storage_path.parent),
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise

        # Save file
        try:
            with storage_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(
                "file_saved",
                upload_id=upload_id,
                stored_path=str(storage_path),
                size_bytes=size_bytes,
            )
        except Exception as e:
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.error(
                "upload_file_save_failed",
                upload_id=upload_id,
                storage_path=str(storage_path),
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            # Clean up partial file if it exists
            if storage_path.exists():
                try:
                    storage_path.unlink()
                    logger.warning(
                        "upload_partial_file_deleted",
                        upload_id=upload_id,
                        path=str(storage_path),
                    )
                except Exception as cleanup_error:
                    logger.error(
                        "upload_cleanup_failed",
                        upload_id=upload_id,
                        path=str(storage_path),
                        error=str(cleanup_error),
                    )
            raise

        # Compute checksum
        try:
            checksum = _checksum_file(storage_path)
        except Exception as e:
            duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
            logger.warning(
                "upload_checksum_failed",
                upload_id=upload_id,
                storage_path=str(storage_path),
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            checksum = None

        duration_ms = (time.time_ns() - start_time_ns) / 1_000_000
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024

        logger.info(
            "upload_completed",
            upload_id=upload_id,
            filename=filename,
            stored_path=str(storage_path),
            size_bytes=size_bytes,
            size_kb=round(size_kb, 2),
            size_mb=round(size_mb, 2),
            checksum=checksum,
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
            "size": size_bytes,
            "checksum": checksum,
            "uploaded_at": uploaded_at,
            "source_system": source_system,
            "upload_kind": upload_kind,
            "device_id": device_id,
            "hostname": hostname,
            "person_name": person_name,
            "message": f"File '{filename}' uploaded successfully",
        }
