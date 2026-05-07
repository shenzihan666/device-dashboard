# Development

## Python toolchain

This project uses **uv** (`uv.lock` at repo root).

```bash
uv sync                    # install deps + dev group (pytest, ruff, pre-commit)
uv run pytest              # backend tests (see also pre-push hook)
uv run ruff check .        # optional manual lint
uv run ruff format .       # optional manual format
```

## Frontend

```bash
cd frontend
npm install
npm run dev          # Vite dev server
npm run build        # production build → dist/
npm run typecheck    # tsc --noEmit (also run via pre-commit)
```

## Pre-commit

Hooks are defined in `.pre-commit-config.yaml`.

One-time setup:

```bash
uv tool install pre-commit   # or install pre-commit another way
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

What runs:

- **pre-commit** — Ruff on Python under `backend/`, `tests/`, `scripts/`; TypeScript check via `scripts/typecheck_frontend.py`; general file hygiene.
- **commit-msg** — **Conventional Commits** (strict), allowed types include `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, etc.
- **pre-push** — `scripts/run_pytest.py` (backend pytest).

Run everything on all files (CI-style):

```bash
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```

Do not use `--no-verify` or `SKIP=…` unless project policy explicitly allows it for a given change.
