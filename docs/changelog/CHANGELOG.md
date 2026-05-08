# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

### Added

- Enterprise-grade documentation structure with categorized folders, templates, and seed documents.
- Backend Clean Architecture layout: `backend/core`, `backend/infrastructure`, `backend/api` with FastAPI `Depends()` wiring.
- SQLAlchemy 2.0 async repositories, Alembic migration scaffold (`alembic/`), and pydantic-settings-based configuration.
- Unified JSON `APIResponse` envelope, Pydantic request/response schemas, global exception handlers, and structlog-based logging with request correlation.
- API contract tests under `tests/api/`, unit tests under `tests/unit/`, and shared async fixtures in `tests/conftest.py`.

### Changed

- **Breaking:** REST responses are wrapped in `{ success, data, error, error_code, meta }`; `PUT /api/layout` expects `{ "positions": [...] }` instead of a bare JSON array.
- Grafana client is async **httpx** (`backend/infrastructure/external/grafana_client.py`); pandas and sync `requests` usage removed from the backend path.
- Frontend `src/services/api.ts` unwraps the envelope for all dashboard API calls; LangSmith opens `trace_url` after a client-side fetch.

### Removed

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
