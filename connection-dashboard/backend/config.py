from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GRAFANA_URL: str = os.getenv("GRAFANA_URL", "https://mynameisi.grafana.net")
API_TOKEN: str = os.getenv("API_TOKEN", "")
LOKI_UID: str = os.getenv("LOKI_DATASOURCE_UID", "grafanacloud-logs")
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

POLL_INTERVAL_S: int = int(os.getenv("POLL_INTERVAL_S", "10"))
BACKFILL_HOURS: int = int(os.getenv("BACKFILL_HOURS", "24"))
OFFLINE_GRACE_S: int = int(os.getenv("OFFLINE_GRACE_S", "90"))

DB_PATH: Path = BASE_DIR / "data" / "events.db"
