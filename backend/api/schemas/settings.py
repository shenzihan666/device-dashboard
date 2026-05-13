"""Pydantic schemas for the app-settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    point_to_point_enabled: bool


class AppSettingsUpdateRequest(BaseModel):
    point_to_point_enabled: bool | None = None
