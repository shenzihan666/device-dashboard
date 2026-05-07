"""FastAPI application: REST API + WebSocket + static file serving."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.api import init_api
from backend.api import router as api_router
from backend.langsmith_link import lookup_trace
from backend.poller import Poller
from backend.state import StateProjector
from backend.store import EventStore
from backend.ws import Broadcaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

_NANO = 1_000_000_000

store = EventStore(config.DB_PATH)
state = StateProjector(offline_grace_ns=config.OFFLINE_GRACE_S * _NANO)
broadcaster = Broadcaster()
poller = Poller(store, state, broadcaster)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_api(store, state)
    if config.API_TOKEN:
        await poller.start()
    else:
        logger.warning("API_TOKEN not set — poller disabled, running in offline/demo mode")
    yield
    await poller.stop()


app = FastAPI(
    title="WeCom AI Connection Dashboard",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/langsmith/trace")
async def langsmith_trace(request_id: str):
    result = await lookup_trace(request_id)
    if result is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return result


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.disconnect(ws)


@app.get("/api/status")
async def status():
    mn, mx = store.get_time_range()
    return {
        "poller_running": poller._running,
        "ws_clients": broadcaster.client_count,
        "time_range": {"min_ns": mn, "max_ns": mx},
        "config": {
            "poll_interval_s": config.POLL_INTERVAL_S,
            "backfill_hours": config.BACKFILL_HOURS,
            "offline_grace_s": config.OFFLINE_GRACE_S,
        },
    }


DIST_DIR = FRONTEND_DIR / "dist"

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        """SPA fallback: serve index.html for all non-API paths."""
        file_path = DIST_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_DIR / "index.html"))
elif FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
