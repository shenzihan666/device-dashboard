"""Pydantic schemas for the app-settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    grafana_enabled: bool
    langsmith_enabled: bool


class AppSettingsUpdateRequest(BaseModel):
    grafana_enabled: bool | None = None
    langsmith_enabled: bool | None = None
