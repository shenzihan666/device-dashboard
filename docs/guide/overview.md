# Overview

The **WeCom AI Connection Dashboard** is a real-time operations view for WeCom (enterprise WeChat) clients connecting to AI chat backends.

## What it does

- Polls **Grafana Loki** (`wecom-sidecar-logs`) on a fixed interval, parses structured log lines into **connection events**, and persists them in **SQLite**.
- Exposes a **FastAPI** service with REST and WebSocket endpoints.
- Serves a **React + Vite** single-page app that shows:
  - A **live workflow-style graph** of servers, desktop/device nodes, and hosts (see [Frontend](./frontend.md)).
  - An **event feed** and **timeline** for replay and inspection.

## Out of scope (v1)

- Authentication / multi-tenant isolation
- HTTPS termination (use a reverse proxy)
- Mobile-first layout
- Alerting / paging on connection switches

For setup and run commands, see [Getting started](./getting-started.md).
