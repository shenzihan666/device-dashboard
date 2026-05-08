# ADR-001: React Flow as Graph Rendering Engine

| Field | Value |
|-------|-------|
| **ID** | ADR-001 |
| **Author** | shenzihan666 |
| **Date** | 2025-01-15 |
| **Status** | Accepted |

## Context

The connection dashboard needs to render a live, interactive graph showing relationships between AI servers, WeCom desktop devices, and host machines. Requirements include:

- Directed edges between three tiers of nodes (server -> device -> host).
- Drag-to-reposition with layout persistence.
- Auto-layout via Dagre when no saved positions exist.
- Real-time updates via WebSocket without full re-renders.
- Minimap, pan/zoom controls, and a dot-grid background.

The team evaluated several graph/diagram libraries for the React ecosystem.

## Decision

Use **React Flow** (`@xyflow/react`) as the graph rendering engine, paired with **Dagre** for automatic layout computation.

React Flow provides a declarative, React-native API for nodes and edges with built-in support for custom node components, edge types, controls, minimap, and background patterns. Dagre handles hierarchical layout (`rankdir: 'TB'`) to stack the three node tiers vertically.

## Consequences

### Positive

- First-class React integration: nodes are React components, enabling Tailwind styling and shared design tokens.
- Built-in pan, zoom, minimap, and controls reduce custom code.
- Dagre layout produces clean hierarchical graphs out of the box.
- Active maintenance and large community (`@xyflow/react` v12+).
- Supports both controlled and uncontrolled node positioning, making layout persistence straightforward.

### Negative

- Bundle size increase (~80 KB gzipped for React Flow + Dagre).
- Dagre is unmaintained upstream; the community fork (`@dagrejs/dagre`) is used instead.
- Complex custom edge routing (e.g., bundled edges for many devices) requires manual work.

### Neutral

- The three-tier layout (server/device/host) is an application concern built on top of Dagre, not a React Flow feature.

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **D3.js (force layout)** | Maximum flexibility but requires imperative DOM manipulation; no React component model for nodes; force layouts produce unstable positions for hierarchical data. |
| **Cytoscape.js** | Powerful graph library with layout plugins, but canvas-based rendering makes it hard to use React components as nodes; theming is CSS-adjacent, not Tailwind-native. |
| **vis-network** | Simple API for network graphs, but limited customization for node appearance; no React-native integration; project activity has slowed. |
| **Custom SVG/Canvas** | Full control, but building pan/zoom, minimap, drag, edge routing, and hit testing from scratch is a multi-week effort with ongoing maintenance. |

## Related

- [Frontend guide](../guide/frontend.md) -- graph semantics, edge direction, and theming details
- [Architecture guide](../guide/architecture.md) -- overall system data flow
