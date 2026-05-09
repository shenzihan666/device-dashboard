"""Collect all API routers into a single list for app inclusion."""

from backend.api.routes.entities import router as entities_router
from backend.api.routes.events import router as events_router
from backend.api.routes.heartbeat_ws import router as heartbeat_ws_router
from backend.api.routes.langsmith import router as langsmith_router
from backend.api.routes.layout import router as layout_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.state import router as state_router
from backend.api.routes.status import router as status_router
from backend.api.routes.websocket import router as websocket_router

all_routers = [
    events_router,
    state_router,
    entities_router,
    layout_router,
    langsmith_router,
    settings_router,
    status_router,
    websocket_router,
    heartbeat_ws_router,
]
