# Documentation

Enterprise documentation for **connection-dashboard** (WeCom AI Connection Dashboard).

Start here, then follow the links below. The root [README.md](../README.md) keeps a short introduction and quick commands; deeper detail lives under `docs/`.

---

## Guides

Product and developer guides covering setup, architecture, and usage.

| Document | Description |
|----------|-------------|
| [Overview](./guide/overview.md) | What the product does and main capabilities |
| [Getting started](./guide/getting-started.md) | Production run and local development with Vite |
| [Configuration](./guide/configuration.md) | Environment variables (`.env`) |
| [Architecture](./guide/architecture.md) | Backend, data flow, and how the UI connects |
| [Frontend](./guide/frontend.md) | React Flow graph, layout tiers, and UI conventions |
| [API reference](./guide/api.md) | REST endpoints and WebSocket |
| [Development](./guide/development.md) | Toolchain (`uv`), tests, and pre-commit hooks |

## Architecture Decision Records

Immutable records of significant technical decisions. See [ADR index](./adr/README.md).

| Record | Status | Summary |
|--------|--------|---------|
| [ADR-001](./adr/001-react-flow-graph-engine.md) | Accepted | React Flow as the graph rendering engine |

## Feature Specifications

Structured proposals for new functionality. See [features index](./features/README.md).

| Spec | Status | Summary |
|------|--------|---------|
| [FEAT-001](./features/001-realtime-dashboard.md) | Shipped | Real-time connection dashboard |

## Bug Reports

Known issues and structured bug tracking. See [bugs index](./bugs/README.md).

> No open bugs documented yet. Use the [bug report template](./templates/bug-report.md) to file one.

## Changelog

Release history following [Keep a Changelog](https://keepachangelog.com/) conventions.

- [CHANGELOG.md](./changelog/CHANGELOG.md)

## Runbooks

Operational procedures for deployment, monitoring, and troubleshooting.

| Runbook | Description |
|---------|-------------|
| [Deployment](./runbooks/deployment.md) | Deploy, rollback, and environment setup |
| [Troubleshooting](./runbooks/troubleshooting.md) | Common issues and resolution steps |

## Templates

Standardized templates for contributing documentation. See [templates index](./templates/README.md).

| Template | Use for |
|----------|---------|
| [Bug report](./templates/bug-report.md) | Filing a new bug in `bugs/` |
| [Feature spec](./templates/feature-spec.md) | Proposing a new feature in `features/` |
| [ADR](./templates/adr.md) | Recording an architecture decision in `adr/` |
| [Runbook](./templates/runbook.md) | Adding an operational procedure in `runbooks/` |

---

## Contributing Documentation

1. Pick the appropriate **template** from [`docs/templates/`](./templates/README.md).
2. Copy it into the correct category folder (`bugs/`, `features/`, `adr/`, or `runbooks/`).
3. Fill in all sections; remove placeholder text.
4. Add a row to the relevant index table in this file and the category `README.md`.
5. Commit using Conventional Commits: `docs(category): short description`.
