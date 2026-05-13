export interface ConnectionEvent {
  id?: number;
  ts_ns: number;
  kind: string;
  host?: string | null;
  device_serial?: string | null;
  ai_url?: string | null;
  prev_ai_url?: string | null;
  status?: string | null;
  latency_ms?: number | null;
  request_id?: string | null;
  session_id?: string | null;
  raw_line?: string | null;
  payload_json?: Record<string, unknown> | null;
}

export interface WeComDeviceFollowup {
  in_progress: boolean;
  target: string | null;
  batch_id: string | null;
}

export interface WeComDeviceAI {
  last_request_at: string | null;
  requests_total: number;
  failures_total: number;
}

export interface WeComDevice {
  serial: string;
  name: string;
  status: string;
  running?: boolean;
  sync_running?: boolean;
  followup_running?: boolean;
  red_dot_pending?: number;
  current_target?: string | null;
  followup?: WeComDeviceFollowup;
  ai?: WeComDeviceAI;
}

export interface WeComClientState {
  instance_id: string;
  name: string;
  version: string;
  brain_url: string;
  device_count: number;
  devices: WeComDevice[];
  health_status: string;
  ai_reachable: boolean;
  ai_response_ms: number | null;
  last_heartbeat_ns: number;
  online: boolean;
}

export interface BrainServerState {
  instance_id: string;
  name: string;
  version: string;
  worker_count: number;
  total_handled: number;
  avg_inflight: number;
  health_status: string;
  memory_mb: number | null;
  cpu_pct: number | null;
  last_heartbeat_ns: number;
  online: boolean;
}

export interface DataSourcesState {
  grafana_enabled: boolean;
  point_to_point_enabled: boolean;
}

export interface StateSnapshot {
  servers: { url: string; device_count: number }[];
  hosts: { name: string; status: string; last_seen_ns?: number; device_count: number }[];
  devices: { serial: string; host?: string; ai_url: string; status: string; processing?: boolean; last_seen_ns?: number }[];
  edges: { from: string; to: string; type: string; status?: string }[];
  brain_servers: BrainServerState[];
  wecom_clients: WeComClientState[];
  heartbeat_edges: { from: string; to: string; type: string; status?: string }[];
  data_sources?: DataSourcesState;
}

export interface NodePosition {
  node_id: string;
  x: number;
  y: number;
}

interface ApiEnvelope<T> {
  success: boolean;
  data?: T;
  error?: string | null;
  error_code?: string | null;
  meta?: Record<string, unknown> | null;
}

async function readEnvelope<T>(res: Response): Promise<T> {
  const body = (await res.json()) as ApiEnvelope<T>;
  if (!res.ok || body.success === false) {
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  if (body.data === undefined || body.data === null) {
    throw new Error('Empty response data');
  }
  return body.data;
}

export async function getState(atNs?: number): Promise<StateSnapshot> {
  const url = atNs != null ? `/api/state?at=${atNs}` : '/api/state';
  const res = await fetch(url);
  return readEnvelope<StateSnapshot>(res);
}

export async function getEvents(params?: {
  limit?: number;
  from?: number;
  to?: number;
}): Promise<ConnectionEvent[]> {
  const search = new URLSearchParams();
  if (params?.limit) search.set('limit', String(params.limit));
  if (params?.from) search.set('from', String(params.from));
  if (params?.to) search.set('to', String(params.to));
  const res = await fetch(`/api/events?${search.toString()}`);
  return readEnvelope<ConnectionEvent[]>(res);
}

export async function getTimeRange(): Promise<{ min_ns: number | null; max_ns: number | null }> {
  const res = await fetch('/api/time_range');
  return readEnvelope<{ min_ns: number | null; max_ns: number | null }>(res);
}

export async function getDensity(
  fromNs: number,
  toNs: number,
  buckets = 200,
): Promise<{ ts_ns: number; count: number }[]> {
  const res = await fetch(`/api/density?from=${fromNs}&to=${toNs}&buckets=${buckets}`);
  return readEnvelope<{ ts_ns: number; count: number }[]>(res);
}

export async function getLayout(): Promise<NodePosition[]> {
  const res = await fetch('/api/layout');
  const data = await readEnvelope<{ positions: NodePosition[] }>(res);
  return data.positions || [];
}

export async function saveLayout(items: NodePosition[]): Promise<void> {
  const res = await fetch('/api/layout', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ positions: items }),
  });
  await readEnvelope<{ saved: number }>(res);
}

export async function resetLayout(): Promise<void> {
  const res = await fetch('/api/layout', { method: 'DELETE' });
  await readEnvelope<{ cleared: boolean }>(res);
}

/* ── App settings (data-source toggles) ── */

export interface AppSettingsState {
  grafana_enabled: boolean;
  point_to_point_enabled: boolean;
  langsmith_enabled: boolean;
}

export async function getAppSettings(): Promise<AppSettingsState> {
  const res = await fetch('/api/settings');
  return readEnvelope<AppSettingsState>(res);
}

export async function updateAppSettings(
  patch: Partial<AppSettingsState>,
): Promise<AppSettingsState> {
  const res = await fetch('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  return readEnvelope<AppSettingsState>(res);
}

/** LangSmith trace summary returned inside the API envelope `data`. */
export interface LangsmithTraceSummary {
  run_id: string;
  name?: string;
  status?: string;
  latency_s?: number | null;
  error?: string | null;
  trace_url?: string | null;
}

export async function fetchLangsmithTrace(requestId: string): Promise<LangsmithTraceSummary> {
  const res = await fetch(`/api/langsmith/trace?request_id=${encodeURIComponent(requestId)}`);
  return readEnvelope<LangsmithTraceSummary>(res);
}
