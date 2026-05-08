"""Common API response envelope and shared schema utilities."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Unified API response envelope."""

    success: bool = True
    data: T | None = None
    error: str | None = None
    error_code: str | None = None
    meta: dict[str, Any] | None = None
