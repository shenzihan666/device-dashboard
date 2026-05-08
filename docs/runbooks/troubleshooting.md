# Troubleshooting

| Field | Value |
|-------|-------|
| **Author** | Team |
| **Last updated** | 2025-01-15 |
| **Audience** | Ops / Dev |
| **Frequency** | Ad-hoc |

## Purpose

Common issues encountered when running the connection dashboard, with diagnosis steps and resolutions.

## Common Issues

### No data appears in the graph

**Symptoms:** Graph canvas is empty; no server/device/host nodes render.

**Diagnosis:**

```bash
curl http://localhost:8090/api/state
```

If the response has empty arrays, the poller is not ingesting data.

**Likely causes and resolutions:**

| Cause | Resolution |
|-------|------------|
| `API_TOKEN` is missing or invalid | Check `.env`; token must be a valid Grafana service account token (`glsa_...`) |
| `GRAFANA_URL` is unreachable | Verify network connectivity: `curl -I $GRAFANA_URL` |
| `LOKI_DATASOURCE_UID` is wrong | Confirm the UID in Grafana UI → Data Sources → Loki |
| No matching logs in Loki | Check that `wecom-sidecar-logs` exist in the configured time range |

### WebSocket shows "DISCONNECTED"

**Symptoms:** The top bar shows a red "DISCONNECTED" status instead of green "LIVE".

**Diagnosis:** Open browser DevTools → Network → WS tab. Check if the `/ws/live` connection is established.

**Likely causes and resolutions:**

| Cause | Resolution |
|-------|------------|
| Backend is not running | Restart uvicorn; check process logs |
| Reverse proxy strips WebSocket upgrade | Configure proxy to pass `Upgrade` and `Connection` headers |
| Vite dev proxy misconfigured | Ensure `vite.config.ts` proxies `/ws` to `localhost:8090` with `ws: true` |

### Devices stuck in "online" status

**Symptoms:** Devices that should be offline remain shown as online.

**Diagnosis:** Check the `OFFLINE_GRACE_S` value in `.env`. Default is 90 seconds.

**Resolution:** If the grace period is too long, reduce `OFFLINE_GRACE_S`. If the poller is not running, the state engine cannot detect offline transitions -- verify the backend process is active and polling.

### Layout resets after page reload

**Symptoms:** Manually positioned nodes revert to Dagre auto-layout positions.

**Diagnosis:**

```bash
curl http://localhost:8090/api/layout
```

If `positions` is empty, layouts are not being saved.

**Resolution:** Ensure the canvas is in **Edit** mode (via the floating toolbar) before dragging nodes. Positions are only persisted when Edit mode is active. Check browser DevTools for failed `PUT /api/layout` requests.

### Frontend build fails

**Symptoms:** `npm run build` exits with TypeScript errors.

**Diagnosis:**

```bash
cd frontend
npm run typecheck
```

**Resolution:** Fix the reported TypeScript errors. Common causes include missing type imports or stale generated types after backend API changes.

### Pre-commit hooks fail

**Symptoms:** `git commit` is rejected by hooks.

**Diagnosis:** Read the hook output. Common failures:

| Hook | Likely cause | Resolution |
|------|-------------|------------|
| Ruff lint | Python style violation | Run `uv run ruff check . --fix` |
| Ruff format | Formatting mismatch | Run `uv run ruff format .` |
| TypeScript check | Type error in frontend | Run `cd frontend && npm run typecheck` |
| Conventional commit | Bad commit message format | Use format: `type(scope): description` |

See [Development guide](../guide/development.md) for the full hook reference.

## Related

- [Deployment runbook](./deployment.md)
- [Configuration guide](../guide/configuration.md)
- [Development guide](../guide/development.md)
