"""Pydantic schemas for file upload endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    upload_id: str | None = None
    filename: str
    stored_path: str | None = None
    size: int
    checksum: str | None = None
    message: str


class FileInfo(BaseModel):
    filename: str
    size: int
    uploaded_at: datetime
    source_system: str | None = None
    upload_kind: str | None = None
    device_id: str | None = None
    hostname: str | None = None
    person_name: str | None = None


class FilesListResponse(BaseModel):
    files: list[FileInfo]


class DeviceFileInfo(BaseModel):
    file_id: str
    filename: str
    size: int
    uploaded_at: datetime
    source_system: str
    upload_kind: str
    extension: str


class DeviceFilesListResponse(BaseModel):
    device_id: str
    total_files: int
    files: list[DeviceFileInfo]


class FileContentResponse(BaseModel):
    file_id: str
    filename: str
    offset: int
    limit: int
    total_lines: int
    lines: list[str]
    truncated: bool
