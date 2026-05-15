# Frontend

The UI lives in `frontend/` and is built with **Vite**, **React**, **Tailwind CSS**, and **React Flow** (`@xyflow/react`).

## Layout shell

The root layout (`App.tsx`) is a **two-column grid**: a fixed **sidebar** (`Sidebar.tsx`, ~200px) for switching pages, plus a **main** area that depends on the active route:

- **Dashboard** — Top bar (title + WebSocket status) and a **scrollable** body (`Dashboard.tsx`). The shell grid uses `min-h-0` on the `1fr` content row and wraps the page in `overflow-hidden` so the inner `h-full overflow-y-auto` layer gets a bounded height. (Without `min-h-0`, CSS Grid’s default `min-height: auto` on `1fr` tracks lets the row grow with content, which suppresses nested scrolling.)

- **Canvas** — Top bar with **LIVE / REPLAY** toggle and WebSocket status; **center** — React Flow graph with floating **View / Edit** toolbar (`CanvasToolbar.tsx`): same muted-track **segmented** pattern as LIVE/REPLAY (active segment is white on `geist-bg-muted`); **Edit** uses `useNodesState` + `onNodesChange` so the canvas repaints while dragging; positions persist via `/api/layout` on drag end. **Right column** — event feed. **Bottom** — timeline scrubber for replay.

- **Settings** — Top bar plus full-page **Settings** (`SettingsPage.tsx`) using the same scroll-friendly grid pattern as Dashboard (data-source toggles such as point-to-point live under `/api/settings`).

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

- **Chrome (shell)** — Top bar, event feed column, timeline strip, detail drawer, and floating **View / Edit** toolbar use a **Vercel-inspired** light treatment: **Inter** (loaded from Google Fonts in `index.html`), Tailwind **`geist`** tokens in `frontend/tailwind.config.js` (near-black text `#0a0a0a`, soft grays `#fafafa` / `#f5f5f5`, hairline borders `#ededed`, blue accents where needed), and CSS variables in `frontend/src/index.css` aligned to the same palette. Segmented controls use white-on-muted backgrounds; semantic chips in the event feed use soft tinted backgrounds (e.g. `bg-blue-50 text-blue-600`).
- **Canvas (graph)** — Server / host / device **node components** still use the legacy **`foundry`** color names in Tailwind so graph card borders and status colors stay stable and independent of shell restyles. The React Flow **dot** background, edges, minimap, and controls are unchanged in behavior; global CSS only tweaks control/minimap chrome (borders, light shadows) to match the shell.

## Key files

| Path | Role |
|------|------|
| `src/App.tsx` | Root grid: sidebar + Dashboard / Canvas / Settings shells |
| `src/components/Sidebar.tsx` | Page navigation (Dashboard, Canvas, Settings) |
| `src/components/dashboard/Dashboard.tsx` | Brain server and WeCom client cards (scrollable body) |
| `src/components/SettingsPage.tsx` | Settings form (scrollable body) |
| `src/components/canvas/CanvasToolbar.tsx` | Floating View / Edit mode toggle and reset layout |
| `src/components/canvas/ConnectionCanvas.tsx` | React Flow, edges, background |
| `src/utils/dagreLayout.ts` | Auto-layout for nodes without saved positions |
| `src/components/canvas/*Node.tsx` | Server / Device / Host card UI |
| `src/hooks/useAppSettings.ts` | Load and update `/api/settings` with optimistic UI |
| `src/services/api.ts` | Types and fetch helpers for backend APIs |
