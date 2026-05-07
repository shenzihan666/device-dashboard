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

export interface StateSnapshot {
  servers: { url: string; device_count: number }[];
  hosts: { name: string; status: string; last_seen_ns?: number; device_count: number }[];
  devices: { serial: string; host?: string; ai_url: string; status: string; last_seen_ns?: number }[];
  edges: { from: string; to: string; type: string; status?: string }[];
}

export interface NodePosition {
  node_id: string;
  x: number;
  y: number;
}

export async function getState(atNs?: number): Promise<StateSnapshot> {
  const url = atNs != null ? `/api/state?at=${atNs}` : '/api/state';
  const res = await fetch(url);
  return res.json();
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
  return res.json();
}

export async function getTimeRange(): Promise<{ min_ns: number | null; max_ns: number | null }> {
  const res = await fetch('/api/time_range');
  return res.json();
}

export async function getDensity(fromNs: number, toNs: number, buckets = 200): Promise<{ ts_ns: number; count: number }[]> {
  const res = await fetch(`/api/density?from=${fromNs}&to=${toNs}&buckets=${buckets}`);
  return res.json();
}

export async function getLayout(): Promise<NodePosition[]> {
  const res = await fetch('/api/layout');
  const data = await res.json();
  return data.positions || [];
}

export async function saveLayout(items: NodePosition[]): Promise<void> {
  await fetch('/api/layout', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(items),
  });
}

export async function resetLayout(): Promise<void> {
  await fetch('/api/layout', { method: 'DELETE' });
}
