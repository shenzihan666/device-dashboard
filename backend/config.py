"""Typed application settings backed by pydantic-settings.

All values can be overridden via environment variables or a `.env` file.
Invalid values are caught at import time (fail-fast).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Grafana / Loki
    grafana_url: str = "https://mynameisi.grafana.net"
    api_token: str = ""
    loki_datasource_uid: str = "grafanacloud-logs"

    # LangSmith
    langsmith_api_key: str = ""

    # Polling
    poll_interval_s: int = 10
    backfill_hours: int = 24
    offline_grace_s: int = 90

    # Heartbeat monitoring
    heartbeat_grace_s: int = 30
    heartbeat_check_interval_s: int = 5

    # Database
    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'events.db'}"

    # Logging
    log_level: str = "INFO"
    log_format: str = "console"  # "json" for production, "console" for dev

    # CORS
    cors_origins: list[str] = ["*"]

    # File Upload
    upload_dir: Path = BASE_DIR / "uploads"
    upload_allowed_extensions: list[str] = [".db", ".jsonl", ".log", ".xlsx", ".xls"]
    upload_max_size_mb: int = 100  # 100 MB max file size


@lru_cache
def get_settings() -> Settings:
    return Settings()
