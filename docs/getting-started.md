# Getting started

## Prerequisites

- **Python** 3.11+ with [**uv**](https://docs.astral.sh/uv/) (this repo ships `uv.lock`).
- **Node.js** and **npm** for the frontend (`frontend/package.json`).

## Production-style run

Build the frontend, then start the API. When `frontend/dist` exists, the backend serves the built SPA.

```bash
cp .env.example .env   # set API_TOKEN (required); optional LANGSMITH_API_KEY
uv sync
cd frontend && npm install && npm run build && cd ..
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090
```

Open `http://localhost:8090/`.

## Development (hot reload)

Use two terminals: FastAPI on **8090**, Vite on **5173** (Vite proxies `/api` and `/ws` to the backend).

```bash
# Terminal A — repo root
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8090

# Terminal B
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Next steps

- [Configuration](./configuration.md) — environment variables
- [Development](./development.md) — lint, typecheck, tests, hooks
