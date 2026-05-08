import { X } from 'lucide-react';
import { useState } from 'react';
import { fetchLangsmithTrace, type ConnectionEvent } from '../services/api';

interface DetailDrawerProps {
  event: ConnectionEvent;
  onClose: () => void;
  langsmithEnabled?: boolean;
}

function formatTime(tsNs: number | undefined | null): string {
  if (!tsNs) return '--';
  const d = new Date(tsNs / 1e6);
  return d.toLocaleString('zh-CN', { hour12: false });
}

export default function DetailDrawer({ event, onClose, langsmithEnabled = true }: DetailDrawerProps) {
  const [langsmithBusy, setLangsmithBusy] = useState(false);
  const [langsmithErr, setLangsmithErr] = useState<string | null>(null);

  const handleOpenLangsmith = async () => {
    if (!event.request_id) return;
    setLangsmithErr(null);
    setLangsmithBusy(true);
    try {
      const data = await fetchLangsmithTrace(event.request_id);
      if (data.trace_url) {
        window.open(data.trace_url, '_blank', 'noopener,noreferrer');
      } else {
        setLangsmithErr('No trace URL returned');
      }
    } catch (e) {
      setLangsmithErr(e instanceof Error ? e.message : 'Lookup failed');
    } finally {
      setLangsmithBusy(false);
    }
  };

  return (
    <div className="fixed top-0 right-0 w-[420px] h-full bg-white border-l border-geist-border z-50 flex flex-col shadow-[0_8px_30px_rgba(0,0,0,0.06)] animate-slide-in">
      {/* Header */}
      <div className="px-4 py-3 border-b border-geist-border flex justify-between items-center">
        <h3 className="text-sm font-semibold text-geist-fg">Event Detail</h3>
        <button
          className="p-1 rounded-md text-geist-fg-muted hover:text-geist-fg hover:bg-geist-bg-muted transition-colors"
          onClick={onClose}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        <div className="space-y-1.5 text-geist-fg">
          <div><span className="text-geist-fg-subtle">Kind:</span> {event.kind}</div>
          <div><span className="text-geist-fg-subtle">Time:</span> {formatTime(event.ts_ns)}</div>
          {event.host && <div><span className="text-geist-fg-subtle">Host:</span> <span className="text-blue-600">{event.host}</span></div>}
          {event.device_serial && <div><span className="text-geist-fg-subtle">Device:</span> <span className="text-violet-600">{event.device_serial}</span></div>}
          {event.ai_url && <div><span className="text-geist-fg-subtle">AI URL:</span> <span className="text-amber-700">{event.ai_url}</span></div>}
          {event.prev_ai_url && <div><span className="text-geist-fg-subtle">Previous:</span> {event.prev_ai_url}</div>}
          {event.status && <div><span className="text-geist-fg-subtle">Status:</span> {event.status}</div>}
          {event.latency_ms && <div><span className="text-geist-fg-subtle">Latency:</span> {event.latency_ms}ms</div>}
          {event.session_id && <div><span className="text-geist-fg-subtle">Session:</span> {event.session_id}</div>}
        </div>

        {event.raw_line && (
          <div className="mt-4">
            <div className="text-geist-fg-subtle mb-1.5 text-[11px] font-medium uppercase tracking-wider">Raw Log</div>
            <pre className="whitespace-pre-wrap break-all text-geist-fg-muted bg-geist-bg-muted rounded-md p-3 border border-geist-border">{event.raw_line}</pre>
          </div>
        )}

        {event.payload_json && typeof event.payload_json === 'object' && (
          <div className="mt-4">
            <div className="text-geist-fg-subtle mb-1.5 text-[11px] font-medium uppercase tracking-wider">Payload</div>
            <pre className="whitespace-pre-wrap break-all text-geist-fg-muted bg-geist-bg-muted rounded-md p-3 border border-geist-border">
              {JSON.stringify(event.payload_json, null, 2)}
            </pre>
          </div>
        )}

        {event.request_id && langsmithEnabled && (
          <div className="mt-4 space-y-1">
            <button
              type="button"
              className="inline-block px-3 py-1.5 bg-geist-fg text-white rounded-md text-xs font-medium hover:bg-black transition-colors disabled:opacity-50"
              disabled={langsmithBusy}
              onClick={() => void handleOpenLangsmith()}
            >
              {langsmithBusy ? 'Opening…' : 'Open in LangSmith'}
            </button>
            {langsmithErr && (
              <div className="text-xs text-red-600">{langsmithErr}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
