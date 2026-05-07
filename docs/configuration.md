# Configuration

Copy `.env.example` to `.env` and adjust values. The backend reads these at startup.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKEN` | *(required)* | Grafana service account token (`glsa_...`) |
| `GRAFANA_URL` | `https://mynameisi.grafana.net` | Grafana instance base URL |
| `LOKI_DATASOURCE_UID` | `grafanacloud-logs` | Loki datasource UID |
| `LANGSMITH_API_KEY` | *(optional)* | Enables “Open in LangSmith” links in the event detail drawer |
| `POLL_INTERVAL_S` | `10` | Seconds between Loki polls |
| `BACKFILL_HOURS` | `24` | Hours of history to load on first start |
| `OFFLINE_GRACE_S` | `90` | Seconds without activity before a device is marked offline |

Secrets and local overrides should stay in `.env` (gitignored). See the repository `.env.example` for the canonical template.
