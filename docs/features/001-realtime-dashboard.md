# FEAT-001: Real-time Connection Dashboard

| Field | Value |
|-------|-------|
| **ID** | FEAT-001 |
| **Author** | shenzihan666 |
| **Date** | 2025-01-15 |
| **Status** | Shipped |
| **Priority** | P0 |

## Summary

A real-time operations dashboard that visualizes WeCom (enterprise WeChat) client connections to AI chat backends. The system polls Grafana Loki for structured sidecar logs, parses them into connection events, and renders a live interactive graph with an event feed and timeline replay.

## Motivation

Operations teams need visibility into which WeCom desktop clients are connected to which AI servers, when connections switch, and when devices go offline. Without a dedicated dashboard, this information is buried in raw Loki log queries, making it slow and error-prone to diagnose connection issues or verify deployment changes.

## Detailed Design

### Backend (FastAPI + SQLite)

- **Poller** (`backend/poller.py`) queries Grafana Loki on a configurable interval (`POLL_INTERVAL_S`), with initial backfill (`BACKFILL_HOURS`).
- **Parser** (`backend/parser.py`) extracts structured fields (server URL, device serial, host name, event type) from log lines.
- **State engine** (`backend/state.py`) maintains in-memory snapshots of servers, devices, hosts, and edges; marks devices offline after `OFFLINE_GRACE_S`.
- **Store** (`backend/store.py`) persists events and node layout positions in SQLite.
- **API** (`backend/api.py`) exposes REST endpoints for state, events, time range, density, and layout CRUD.
- **WebSocket** (`backend/ws.py`) pushes live events to connected browsers.

### Frontend (React + Vite + React Flow)

- **Graph canvas** (`ConnectionCanvas.tsx`) renders three-tier node layout (server -> device -> host) using React Flow with Dagre auto-layout.
- **Node components** (`ServerNode.tsx`, `DeviceNode.tsx`, `HostNode.tsx`) display status, counts, and connection details.
- **View/Edit mode** (`CanvasToolbar.tsx`) toggles between read-only viewing and drag-to-reposition with layout persistence via REST API.
- **Event feed** shows chronological connection events with semantic color coding.
- **Timeline scrubber** enables replay of any past time window.
- **Theming** uses Vercel-inspired light chrome (Inter font, Geist tokens) around the graph canvas.

### Data Flow

```
Grafana Loki → Poller → Parser → State Engine → SQLite
                                       ↓
                              REST API + WebSocket
                                       ↓
                              React SPA (React Flow graph,
                              event feed, timeline)
```

## Alternatives Considered

| Alternative | Pros | Cons | Why rejected |
|-------------|------|------|--------------|
| Grafana dashboard only | Zero custom code; built-in Loki integration | No graph visualization; limited interactivity; no layout persistence | Core requirement is a topology graph, not time-series panels |
| Polling from browser directly | Simpler architecture; no backend | Exposes Grafana credentials to client; no persistent storage; no offline detection | Security and data integrity concerns |
| Server-Sent Events instead of WebSocket | Simpler protocol; auto-reconnect | One-directional; no future bidirectional needs (e.g., remote commands) | WebSocket chosen for flexibility |

## Acceptance Criteria

- [x] Backend polls Loki and parses logs into structured events
- [x] Events persist in SQLite with full history
- [x] React Flow graph displays server/device/host topology
- [x] Dagre auto-layout with manual override and persistence
- [x] Live event feed updates via WebSocket
- [x] Timeline scrubber enables historical replay
- [x] Offline detection marks devices after grace period
- [x] View/Edit mode toggle for graph interaction

## Out of Scope

- Authentication and multi-tenant isolation (see [Overview](../guide/overview.md#out-of-scope-v1))
- HTTPS termination (handled by reverse proxy)
- Mobile-responsive layout
- Alerting and paging on connection switches

## Related

- [Architecture guide](../guide/architecture.md)
- [Frontend guide](../guide/frontend.md)
- [API reference](../guide/api.md)
- [ADR-001: React Flow](../adr/001-react-flow-graph-engine.md)
