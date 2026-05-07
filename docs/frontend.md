# Frontend

The UI lives in `frontend/` and is built with **Vite**, **React**, **Tailwind CSS**, and **React Flow** (`@xyflow/react`).

## Layout shell

The main app grid (`App.tsx`):

- **Top bar** — title, LIVE/REPLAY toggle, WebSocket status.
- **Center** — React Flow canvas with floating **View / Edit** toolbar (Edit enables dragging; positions persist via `/api/layout`).
- **Right column** — event feed.
- **Bottom** — timeline scrubber for replay.

## Graph semantics

Snapshot data maps to three **node types**:

| Type | Represents | Typical data |
|------|------------|--------------|
| `server` | AI server URL | Label, URL, device count |
| `device` | Desktop / device (WeCom client) | Serial, host name, `ai_url`, status |
| `host` | PC host | Name, status, device count |

### Edge direction and vertical tiers

Edges are built in `ConnectionCanvas.tsx` so **Dagre** (`rankdir: 'TB'`) stacks tiers top-to-bottom:

1. **Top** — **Server** (source for device↔server edges).
2. **Middle** — **Device** (desktop).
3. **Bottom** — **Host** (device → host for `device_host` edges).

Server→device links are drawn as **server → device**; device→host links as **device → host**. Styling (color, dash, animation) reflects edge kind and offline status.

## Theming

- Tailwind **foundry** palette is defined in `frontend/tailwind.config.js` with CSS variables in `frontend/src/index.css`.
- The product targets a **light, white-first** shell: pale borders, white cards on the canvas, and a **dot** background via React Flow `Background` (dots variant).

## Key files

| Path | Role |
|------|------|
| `src/components/canvas/ConnectionCanvas.tsx` | React Flow, edges, background |
| `src/utils/dagreLayout.ts` | Auto-layout for nodes without saved positions |
| `src/components/canvas/*Node.tsx` | Server / Device / Host card UI |
| `src/services/api.ts` | Types and fetch helpers for backend APIs |
