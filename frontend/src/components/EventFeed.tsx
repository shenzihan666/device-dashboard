import { useRef, useEffect } from 'react';
import type { ConnectionEvent } from '../services/api';

const KIND_CONFIG: Record<string, { cls: string; label: string }> = {
  synth_switched: { cls: 'bg-violet-50 text-violet-600', label: 'SWITCH' },
  synth_device_offline: { cls: 'bg-red-50 text-red-600', label: 'OFFLINE' },
  synth_device_online: { cls: 'bg-emerald-50 text-emerald-600', label: 'ONLINE' },
  synth_host_offline: { cls: 'bg-red-50 text-red-600', label: 'HOST OFF' },
  synth_host_online: { cls: 'bg-emerald-50 text-emerald-600', label: 'HOST ON' },
  ai_server_observed: { cls: 'bg-blue-50 text-blue-600', label: 'AI REQ' },
  ai_health_check: { cls: 'bg-emerald-50 text-emerald-600', label: 'HEALTH' },
  sidecar_error: { cls: 'bg-red-50 text-red-600', label: 'ERROR' },
  device_error: { cls: 'bg-red-50 text-red-600', label: 'DEV ERR' },
  metric_event: { cls: 'bg-amber-50 text-amber-700', label: 'METRIC' },
  host_device_map: { cls: 'bg-blue-50 text-blue-600', label: 'MAP' },
};

function formatTime(tsNs: number | undefined | null): string {
  if (!tsNs) return '--:--:--';
  const d = new Date(tsNs / 1e6);
  return d.toLocaleTimeString('zh-CN', { hour12: false });
}

function getBadge(kind: string) {
  const cfg = KIND_CONFIG[kind] || { cls: 'bg-blue-50 text-blue-600', label: kind.slice(0, 8).toUpperCase() };
  return cfg;
}

interface EventFeedProps {
  events: ConnectionEvent[];
  onEventClick: (ev: ConnectionEvent) => void;
}

export default function EventFeed({ events, onEventClick }: EventFeedProps) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [events.length]);

  return (
    <>
      <div className="px-3.5 py-2.5 text-[11px] font-medium uppercase tracking-wider text-geist-fg-subtle border-b border-geist-border flex justify-between items-center">
        <span>Events</span>
        <span className="text-geist-fg font-mono">{events.length}</span>
      </div>
      <div ref={listRef} className="flex-1 overflow-y-auto">
        {events.map((ev, i) => {
          const badge = getBadge(ev.kind);
          return (
            <div
              key={ev.id || `${ev.ts_ns}-${i}`}
              className="px-3.5 py-1.5 text-xs font-mono border-b border-geist-border/60 cursor-pointer hover:bg-geist-bg-muted transition-colors leading-relaxed"
              onClick={() => onEventClick(ev)}
            >
              <span className="text-geist-fg-subtle mr-1.5">{formatTime(ev.ts_ns)}</span>
              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold mr-1 ${badge.cls}`}>
                {badge.label}
              </span>
              {ev.host && <span className="text-blue-600 mr-1">{ev.host}</span>}
              {ev.device_serial && <span className="text-violet-600 mr-1">{ev.device_serial.slice(-6)}</span>}
              {ev.kind === 'synth_switched' && ev.prev_ai_url && ev.ai_url && (
                <span className="text-amber-700">
                  {ev.prev_ai_url.replace('http://', '').replace('/chat', '')} → {ev.ai_url.replace('http://', '').replace('/chat', '')}
                </span>
              )}
              {ev.kind !== 'synth_switched' && ev.ai_url && (
                <span className="text-amber-700">{ev.ai_url.replace('http://', '').replace('/chat', '')}</span>
              )}
            </div>
          );
        })}
        {events.length === 0 && (
          <div className="px-3.5 py-8 text-center text-geist-fg-subtle text-xs">
            No events yet
          </div>
        )}
      </div>
    </>
  );
}
