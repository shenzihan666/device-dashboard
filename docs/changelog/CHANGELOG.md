# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

### Added

- Upload retention and disk governance: 30-day TTL sweeper (`RetentionSweeper`), per-identity quota (default 5 GB), disk watermark rejection (85% → HTTP 507), emergency sweep at 95%.
- Content-addressable upload storage (`.blobs/{sha[:2]}/{sha}`) with hardlink-based deduplication; server-side gzip for `.log` / `.jsonl` on ingest; `Content-Encoding: gzip` passthrough from clients.
- `GET /api/uploads/storage-stats` — disk usage %, per-identity quota usage, retention and sweeper configuration.
- File upload endpoints: `POST /api/upload` (manual) and `POST /api/android-logs/upload` (Android-compatible) with industrial-grade structured logging, no authentication required.
- File storage service: structured directory layout (`uploads/{source}/{identity}/{kind}/{date}/{time}-{file}`), SHA256 checksums, size/extension validation.
- WeCom client event processing: `/ws/heartbeat` accepts `event` type messages (not just `heartbeat`), persists to DB and broadcasts via WebSocket.
- WeCom device nodes: canvas nodes for individual WeCom devices (serial number last 6 chars as label), with running/idle status.
- WeCom event display: EventFeed renders `wecom_device_launched`, `wecom_device_stopped`, `wecom_ai_request`, `wecom_red_dot_update`, `wecom_followup_started`, `wecom_followup_progress`, `wecom_followup_result`, `wecom_followup_finished`.
- Unit tests for brain URL matching and heartbeat peer-IP enrichment (`tests/unit/test_heartbeat_matching.py`).

### Fixed

- Canvas **wecom_client → brain_server** edges when clients report `brain_url` with the brain's public IP but the brain heartbeat uses a cloud hostname and omits `ip`: `/ws/heartbeat` enriches payloads with the WebSocket peer IP (honours `X-Forwarded-For` / `X-Real-IP` behind a reverse proxy) so `heartbeat_edges` can match via `_match_brain_url`.
- Canvas page layout: `min-h-0 h-full` on the canvas grid so the React Flow graph area gets a bounded height and nodes render instead of collapsing to zero height.
- Dashboard device log viewer: "View log files" passes the WeCom client `instance_id` (not device serial) to the log API.
- Dashboard and Settings pages: the grid `1fr` content row uses `min-h-0` (and a clipping wrapper) so the inner `h-full overflow-y-auto` region gets a bounded height and long card lists scroll instead of growing past the viewport.
- WebSocket `/ws/live` handler uses `ws.app.state` for the broadcaster (avoids relying on `Request` injection on the websocket route).
- Graph canvas in **Edit** mode: wire `onNodesChange` / `onEdgesChange` with `useNodesState` / `useEdgesState` so nodes move smoothly while dragging instead of only after mouse-up.
- Event feed: render `device_processing` `priority_count` via `String(...)` for consistent React text children.

### Added

- Enterprise-grade documentation structure with categorized folders, templates, and seed documents.
- Backend Clean Architecture layout: `backend/core`, `backend/infrastructure`, `backend/api` with FastAPI `Depends()` wiring.
- SQLAlchemy 2.0 async repositories, Alembic migration scaffold (`alembic/`), and pydantic-settings-based configuration.
- Unified JSON `APIResponse` envelope, Pydantic request/response schemas, global exception handlers, and structlog-based logging with request correlation.
- API contract tests under `tests/api/`, unit tests under `tests/unit/`, and shared async fixtures in `tests/conftest.py`.

### Changed

- Dashboard **WeCom Clients** section: client cards use the same responsive two-column grid as **AI Brain** (`md:grid-cols-2`) instead of a vertical stack; nested device tiles cap at three columns (`lg:grid-cols-3`) so layout stays readable when client cards are half-width.
- **Breaking:** REST responses are wrapped in `{ success, data, error, error_code, meta }`; `PUT /api/layout` expects `{ "positions": [...] }` instead of a bare JSON array.
- Frontend `src/services/api.ts` unwraps the envelope for all dashboard API calls.
- Deployment runbook (`docs/runbooks/deployment.md`): optional Alembic step and curl checks updated for the response envelope.

### Removed

- **Breaking:** Removed Grafana Loki polling entirely. No more `grafana_client.py`, `poller_service.py`, `API_TOKEN`, `GRAFANA_URL`, `LOKI_DATASOURCE_UID`, `POLL_INTERVAL_S`, `BACKFILL_HOURS`.
- **Breaking:** Removed LangSmith integration entirely. No more `langsmith_client.py`, `langsmith.py` route, `LANGSMITH_API_KEY`, or trace lookup UI.
- Settings UI simplified to only `point_to_point_enabled` toggle (on by default).
- Flat modules `backend/api.py`, `backend/store.py`, `backend/poller.py`, `backend/state.py`, `backend/parser.py`, `backend/events.py`, `backend/ws.py`, `backend/grafana_client.py`, `backend/langsmith_link.py` (logic moved into the layered packages above).

## [0.1.0] - 2025-01-15

Initial release of the WeCom AI Connection Dashboard.

### Added

- FastAPI backend with Grafana Loki poller, log parser, state engine, and SQLite persistence (`ceac2e8`).
- REST API for state, events, time range, density, and layout CRUD (`ceac2e8`).
- WebSocket endpoint (`/ws/live`) for real-time event streaming (`ceac2e8`).
- React + Vite frontend with React Flow graph canvas (`682cffe`).
- Three-tier node layout: server -> device -> host with Dagre auto-layout (`682cffe`).
- View/Edit mode toggle with layout persistence via `/api/layout` (`682cffe`).
- Event feed with chronological display and semantic color coding (`682cffe`).
- Timeline scrubber for historical replay (`682cffe`).
- Pytest suite for backend state and parser modules (`1426e9f`).
- Documentation tree under `docs/` (`f2079a8`).

### Changed

- Hoisted from subdirectory to repository root (`0f3dc54`).
- Migrated to `uv` package manager (`6b08371`).
- Vercel-inspired shell theme with Geist tokens and Inter font (`e7c241c`).
- White theme with graph tiers and updated docs (`b73027f`).

### Fixed

- Pre-push test runner uses `python -m pytest` (`7a30d7d`).
- Canvas View/Edit toggle aligned with shell segmented style (`43ab82c`).

### Chores

- Pre-commit hooks for Ruff (Python) and TypeScript checking (`81195df`).
- Ruff lint and format autofixes applied (`790af43`).
