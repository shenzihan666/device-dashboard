"""File upload API routes.

Provides endpoints for uploading files from various sources including:
- General file upload endpoint
- Android-compatible endpoint
- Storage stats / health endpoint

All endpoints provide detailed industrial-grade logging.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile

from backend.api.dependencies import SettingsDep
from backend.api.schemas.common import APIResponse
from backend.api.schemas.upload import (
    DeviceFileInfo,
    DeviceFilesListResponse,
    FileContentResponse,
    IdentityUsage,
    StorageStatsResponse,
    UploadResponse,
)
from backend.core.services.file_reader import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    TEXT_EXTENSIONS,
    compute_file_id,
    read_line_range,
    resolve_file_id,
)
from backend.core.services.file_storage import FileStorageService, _sanitize_segment
from backend.core.services.upload_quota import (
    DiskWatermarkExceeded,
    QuotaExceeded,
    get_disk_usage_pct,
    get_identity_usage_bytes,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


def _now_utc() -> datetime:
    """Get current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def _parse_uploaded_at(uploaded_at_str: str | None) -> datetime:
    """Parse uploaded_at timestamp string."""
    if not uploaded_at_str:
        return _now_utc()

    try:
        normalized = uploaded_at_str.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except ValueError:
        logger.warning(
            "uploaded_at_parse_failed",
            timestamp=uploaded_at_str,
            reason="Using current time instead",
        )
        return _now_utc()


def _is_client_gzipped(content_encoding: str | None) -> bool:
    """Check if the client sent gzipped content."""
    if not content_encoding:
        return False
    return "gzip" in content_encoding.lower()


@router.post("/upload", response_model=APIResponse[UploadResponse])
async def upload_file(
    settings: SettingsDep,
    file: UploadFile = File(...),
    upload_kind: str = Form("manual-upload"),
    device_id: str = Form(""),
    hostname: str = Form(""),
    person_name: str = Form(""),
    uploaded_at: str = Form(""),
    content_encoding: str | None = Header(None),
) -> APIResponse[UploadResponse]:
    """Upload a file to the server."""
    request_logger = logger.bind(
        endpoint="/api/upload",
        client_provided_filename=file.filename,
        content_type=file.content_type,
    )
    request_logger.info("upload_request_received")

    try:
        storage_service = FileStorageService(settings)
        parsed_uploaded_at = _parse_uploaded_at(uploaded_at)

        result = await storage_service.save_upload(
            file=file,
            source_system="manual",
            upload_kind=upload_kind,
            uploaded_at=parsed_uploaded_at,
            device_id=device_id or None,
            hostname=hostname or None,
            person_name=person_name or None,
            client_gzipped=_is_client_gzipped(content_encoding),
        )

        return APIResponse(
            data=UploadResponse(
                success=True,
                upload_id=result["upload_id"],
                filename=result["filename"],
                stored_path=result["stored_path"],
                size=result["size"],
                checksum=result["checksum"],
                message=result["message"],
            )
        )

    except QuotaExceeded as e:
        request_logger.warning("upload_rejected_quota", error=str(e))
        raise HTTPException(status_code=413, detail=str(e)) from e
    except DiskWatermarkExceeded as e:
        request_logger.warning("upload_rejected_watermark", error=str(e))
        raise HTTPException(status_code=507, detail=str(e)) from e
    except ValueError as e:
        request_logger.error("upload_validation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        request_logger.error("upload_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process upload") from e


@router.post("/android-logs/upload", response_model=APIResponse[UploadResponse])
async def upload_android_logs(
    settings: SettingsDep,
    file: UploadFile = File(...),
    device_id: str = Form(...),
    hostname: str = Form(...),
    person_name: str = Form(""),
    upload_kind: str = Form(...),
    checksum: str = Form(""),
    uploaded_at: str = Form(...),
    content_encoding: str | None = Header(None),
) -> APIResponse[UploadResponse]:
    """Upload endpoint compatible with Android devices.

    Supports ``Content-Encoding: gzip`` — when set the server stores the
    payload as-is without double-compressing.
    """
    request_logger = logger.bind(
        endpoint="/api/android-logs/upload",
        client_provided_filename=file.filename,
        content_type=file.content_type,
        device_id=device_id,
        hostname=hostname,
        upload_kind=upload_kind,
    )
    request_logger.info("android_upload_request_received")

    try:
        storage_service = FileStorageService(settings)
        parsed_uploaded_at = _parse_uploaded_at(uploaded_at)

        result = await storage_service.save_upload(
            file=file,
            source_system="android-run-test",
            upload_kind=upload_kind,
            uploaded_at=parsed_uploaded_at,
            device_id=device_id,
            hostname=hostname,
            person_name=person_name or None,
            client_gzipped=_is_client_gzipped(content_encoding),
        )

        if checksum and checksum.strip():
            request_logger.info(
                "android_upload_checksum_received",
                client_checksum=checksum.strip(),
                server_checksum=result["checksum"],
                checksum_match=checksum.strip() == result["checksum"]
                if result["checksum"]
                else None,
            )

        return APIResponse(
            data=UploadResponse(
                success=True,
                upload_id=result["upload_id"],
                filename=result["filename"],
                stored_path=result["stored_path"],
                size=result["size"],
                checksum=result["checksum"],
                message=result["message"],
            )
        )

    except QuotaExceeded as e:
        request_logger.warning("upload_rejected_quota", error=str(e))
        raise HTTPException(status_code=413, detail=str(e)) from e
    except DiskWatermarkExceeded as e:
        request_logger.warning("upload_rejected_watermark", error=str(e))
        raise HTTPException(status_code=507, detail=str(e)) from e
    except ValueError as e:
        request_logger.error("android_upload_validation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        request_logger.error("android_upload_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process upload") from e


@router.get("/uploads-test")
async def uploads_test(settings: SettingsDep) -> dict[str, str]:
    """Simple test endpoint to verify upload configuration."""
    return {
        "upload_dir": str(settings.upload_dir),
        "upload_dir_exists": str(settings.upload_dir.exists()),
        "allowed_extensions": ", ".join(settings.upload_allowed_extensions),
        "max_size_mb": str(settings.upload_max_size_mb),
    }


@router.get("/uploads/storage-stats", response_model=APIResponse[StorageStatsResponse])
async def storage_stats(settings: SettingsDep) -> APIResponse[StorageStatsResponse]:
    """Return disk usage, per-identity quotas, and retention configuration."""
    upload_dir = settings.upload_dir
    target = upload_dir if upload_dir.exists() else upload_dir.parent
    disk_pct = get_disk_usage_pct(target)

    quota_bytes = settings.upload_quota_per_identity_gb * 1024 * 1024 * 1024
    quota_mb = round(quota_bytes / (1024 * 1024), 2)

    identities: list[IdentityUsage] = []
    if upload_dir.exists():
        seen: set[str] = set()
        for source_dir in upload_dir.iterdir():
            if not source_dir.is_dir() or source_dir.name.startswith("."):
                continue
            for identity_dir in source_dir.iterdir():
                if not identity_dir.is_dir():
                    continue
                ident = identity_dir.name
                if ident in seen:
                    continue
                seen.add(ident)
                used = get_identity_usage_bytes(upload_dir, ident)
                used_mb = round(used / (1024 * 1024), 2)
                identities.append(
                    IdentityUsage(
                        identity=ident,
                        used_bytes=used,
                        used_mb=used_mb,
                        quota_bytes=quota_bytes,
                        quota_mb=quota_mb,
                        usage_pct=round((used / quota_bytes) * 100, 2) if quota_bytes else 0,
                    )
                )

    identities.sort(key=lambda x: x.used_bytes, reverse=True)

    return APIResponse(
        data=StorageStatsResponse(
            disk_usage_pct=disk_pct,
            disk_watermark_pct=settings.upload_disk_watermark_pct,
            disk_emergency_pct=settings.upload_disk_emergency_pct,
            retention_days=settings.upload_retention_days,
            dedup_enabled=settings.upload_dedup_enabled,
            sweeper_interval_min=settings.upload_sweeper_interval_min,
            identities=identities,
        )
    )


@router.get("/uploads/{device_id}", response_model=APIResponse[DeviceFilesListResponse])
async def list_device_files(
    device_id: str,
    settings: SettingsDep,
) -> APIResponse[DeviceFilesListResponse]:
    """List all uploaded files for a device."""
    safe_identity = _sanitize_segment(device_id)
    upload_dir = settings.upload_dir.resolve()

    if not upload_dir.exists():
        return APIResponse(
            data=DeviceFilesListResponse(device_id=device_id, total_files=0, files=[])
        )

    files: list[DeviceFileInfo] = []
    for source_dir in upload_dir.iterdir():
        if not source_dir.is_dir():
            continue
        identity_dir = source_dir / safe_identity
        if not identity_dir.is_dir():
            continue
        source_system = source_dir.name
        for f in identity_dir.rglob("*"):
            if not f.is_file():
                continue
            f_resolved = f.resolve()
            if not str(f_resolved).startswith(str(upload_dir)):
                continue

            rel = f_resolved.relative_to(identity_dir)
            parts = rel.parts
            upload_kind = parts[0] if len(parts) >= 2 else ""
            date_segment = parts[1] if len(parts) >= 3 else ""
            name_part = parts[-1] if parts else f.name

            uploaded_at = _now_utc()
            try:
                from datetime import datetime as _dt

                time_prefix = name_part.split("-")[0] if "-" in name_part else ""
                if date_segment and time_prefix and len(time_prefix) == 6:
                    uploaded_at = _dt.strptime(
                        f"{date_segment}{time_prefix}", "%Y-%m-%d%H%M%S"
                    ).replace(tzinfo=timezone.utc)
            except (ValueError, IndexError):
                pass

            display_name = name_part
            if (
                "-" in name_part
                and name_part.split("-")[0].isdigit()
                and len(name_part.split("-")[0]) == 6
            ):
                display_name = name_part.split("-", 1)[1]

            stat = f_resolved.stat()
            files.append(
                DeviceFileInfo(
                    file_id=compute_file_id(f_resolved, upload_dir),
                    filename=display_name,
                    size=stat.st_size,
                    uploaded_at=uploaded_at,
                    source_system=source_system,
                    upload_kind=upload_kind,
                    extension=f_resolved.suffix.lower(),
                )
            )

    files.sort(key=lambda x: x.uploaded_at, reverse=True)
    return APIResponse(
        data=DeviceFilesListResponse(device_id=device_id, total_files=len(files), files=files)
    )


@router.get(
    "/uploads/{device_id}/{file_id}/content",
    response_model=APIResponse[FileContentResponse],
)
async def get_file_content(
    device_id: str,
    file_id: str,
    settings: SettingsDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> APIResponse[FileContentResponse]:
    """Read paginated content of an uploaded file."""
    upload_dir = settings.upload_dir.resolve()
    file_path = resolve_file_id(device_id, file_id, upload_dir, _sanitize_segment)

    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    ext = file_path.suffix.lower()
    if ext not in TEXT_EXTENSIONS:
        return APIResponse(
            data=FileContentResponse(
                file_id=file_id,
                filename=file_path.name,
                offset=0,
                limit=limit,
                total_lines=1,
                lines=[f"[Binary file: {file_path.name} — preview not available]"],
                truncated=False,
            )
        )

    lines, total_lines = read_line_range(file_path, offset=offset, limit=limit)

    display_name = file_path.name
    if (
        "-" in display_name
        and display_name.split("-")[0].isdigit()
        and len(display_name.split("-")[0]) == 6
    ):
        display_name = display_name.split("-", 1)[1]

    return APIResponse(
        data=FileContentResponse(
            file_id=file_id,
            filename=display_name,
            offset=offset,
            limit=limit,
            total_lines=total_lines,
            lines=lines,
            truncated=False,
        )
    )
