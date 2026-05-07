import { useRef, useEffect } from 'react';
import type { ConnectionEvent } from '../services/api';

const KIND_CONFIG: Record<string, { cls: string; label: string }> = {
  synth_switched: { cls: 'bg-foundry-purple', label: 'SWITCH' },
  synth_device_offline: { cls: 'bg-foundry-red', label: 'OFFLINE' },
  synth_device_online: { cls: 'bg-foundry-green', label: 'ONLINE' },
  synth_host_offline: { cls: 'bg-foundry-red', label: 'HOST OFF' },
  synth_host_online: { cls: 'bg-foundry-green', label: 'HOST ON' },
  ai_server_observed: { cls: 'bg-foundry-accent/20 text-foundry-accent', label: 'AI REQ' },
  ai_health_check: { cls: 'bg-foundry-green/20 text-foundry-green', label: 'HEALTH' },
  sidecar_error: { cls: 'bg-red-600', label: 'ERROR' },
  device_error: { cls: 'bg-red-600', label: 'DEV ERR' },
  metric_event: { cls: 'bg-foundry-amber/20 text-foundry-amber', label: 'METRIC' },
  host_device_map: { cls: 'bg-foundry-accent/20 text-foundry-accent', label: 'MAP' },
};

function formatTime(tsNs: number | undefined | null): string {
  if (!tsNs) return '--:--:--';
  const d = new Date(tsNs / 1e6);
  return d.toLocaleTimeString('zh-CN', { hour12: false });
}

function getBadge(kind: string) {
  const cfg = KIND_CONFIG[kind] || { cls: 'bg-foundry-accent/20 text-foundry-accent', label: kind.slice(0, 8).toUpperCase() };
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
      <div className="px-3.5 py-2.5 text-[11px] font-semibold uppercase tracking-widest text-foundry-text-dim border-b border-foundry-border flex justify-between items-center">
        <span>Events</span>
        <span className="text-foundry-accent font-mono">{events.length}</span>
      </div>
      <div ref={listRef} className="flex-1 overflow-y-auto">
        {events.map((ev, i) => {
          const badge = getBadge(ev.kind);
          return (
            <div
              key={ev.id || `${ev.ts_ns}-${i}`}
              className="px-3.5 py-1.5 text-xs font-mono border-b border-foundry-border/50 cursor-pointer hover:bg-gray-50 transition-colors leading-relaxed"
              onClick={() => onEventClick(ev)}
            >
              <span className="text-foundry-text-dim mr-1.5">{formatTime(ev.ts_ns)}</span>
              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold mr-1 text-white ${badge.cls}`}>
                {badge.label}
              </span>
              {ev.host && <span className="text-foundry-accent mr-1">{ev.host}</span>}
              {ev.device_serial && <span className="text-foundry-purple mr-1">{ev.device_serial.slice(-6)}</span>}
              {ev.kind === 'synth_switched' && ev.prev_ai_url && ev.ai_url && (
                <span className="text-foundry-amber">
                  {ev.prev_ai_url.replace('http://', '').replace('/chat', '')} → {ev.ai_url.replace('http://', '').replace('/chat', '')}
                </span>
              )}
              {ev.kind !== 'synth_switched' && ev.ai_url && (
                <span className="text-foundry-amber">{ev.ai_url.replace('http://', '').replace('/chat', '')}</span>
              )}
            </div>
          );
        })}
        {events.length === 0 && (
          <div className="px-3.5 py-8 text-center text-foundry-text-dim text-xs">
            No events yet
          </div>
        )}
      </div>
    </>
  );
}
