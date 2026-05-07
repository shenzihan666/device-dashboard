import { X } from 'lucide-react';
import type { ConnectionEvent } from '../services/api';

interface DetailDrawerProps {
  event: ConnectionEvent;
  onClose: () => void;
}

function formatTime(tsNs: number | undefined | null): string {
  if (!tsNs) return '--';
  const d = new Date(tsNs / 1e6);
  return d.toLocaleString('zh-CN', { hour12: false });
}

export default function DetailDrawer({ event, onClose }: DetailDrawerProps) {
  return (
    <div className="fixed top-0 right-0 w-[420px] h-full bg-foundry-card border-l border-foundry-border z-50 flex flex-col shadow-2xl animate-slide-in">
      {/* Header */}
      <div className="px-4 py-3 border-b border-foundry-border flex justify-between items-center">
        <h3 className="text-sm font-semibold text-foundry-accent">Event Detail</h3>
        <button
          className="text-foundry-text-dim hover:text-foundry-text transition-colors"
          onClick={onClose}
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        <div className="space-y-1.5 text-foundry-text">
          <div><span className="text-foundry-text-dim">Kind:</span> {event.kind}</div>
          <div><span className="text-foundry-text-dim">Time:</span> {formatTime(event.ts_ns)}</div>
          {event.host && <div><span className="text-foundry-text-dim">Host:</span> <span className="text-foundry-accent">{event.host}</span></div>}
          {event.device_serial && <div><span className="text-foundry-text-dim">Device:</span> <span className="text-foundry-purple">{event.device_serial}</span></div>}
          {event.ai_url && <div><span className="text-foundry-text-dim">AI URL:</span> <span className="text-foundry-amber">{event.ai_url}</span></div>}
          {event.prev_ai_url && <div><span className="text-foundry-text-dim">Previous:</span> {event.prev_ai_url}</div>}
          {event.status && <div><span className="text-foundry-text-dim">Status:</span> {event.status}</div>}
          {event.latency_ms && <div><span className="text-foundry-text-dim">Latency:</span> {event.latency_ms}ms</div>}
          {event.session_id && <div><span className="text-foundry-text-dim">Session:</span> {event.session_id}</div>}
        </div>

        {event.raw_line && (
          <div className="mt-4">
            <div className="text-foundry-text-dim mb-1">--- Raw Log ---</div>
            <pre className="whitespace-pre-wrap break-all text-foundry-text/80">{event.raw_line}</pre>
          </div>
        )}

        {event.payload_json && typeof event.payload_json === 'object' && (
          <div className="mt-4">
            <div className="text-foundry-text-dim mb-1">--- Payload ---</div>
            <pre className="whitespace-pre-wrap break-all text-foundry-text/80">
              {JSON.stringify(event.payload_json, null, 2)}
            </pre>
          </div>
        )}

        {event.request_id && (
          <a
            className="inline-block mt-4 px-3 py-1.5 bg-foundry-accent/15 text-foundry-accent rounded text-xs no-underline hover:bg-foundry-accent/25 transition-colors"
            href={`/api/langsmith/trace?request_id=${encodeURIComponent(event.request_id)}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open in LangSmith
          </a>
        )}
      </div>
    </div>
  );
}
