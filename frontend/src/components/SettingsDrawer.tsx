import { useEffect } from 'react';
import { X } from 'lucide-react';
import type { AppSettingsState } from '../services/api';

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
  settings: AppSettingsState;
  onUpdate: (patch: Partial<AppSettingsState>) => void;
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-geist-accent focus-visible:ring-offset-2 ${
        checked ? 'bg-geist-accent' : 'bg-geist-border-strong'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm ring-0 transition-transform ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="pr-4">
        <div className="text-sm font-medium text-geist-fg">{label}</div>
        <div className="text-xs text-geist-fg-muted mt-0.5">{description}</div>
      </div>
      <Toggle checked={checked} onChange={onChange} />
    </div>
  );
}

export default function SettingsDrawer({
  open,
  onClose,
  settings,
  onUpdate,
}: SettingsDrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed top-0 left-0 w-[360px] h-full bg-white border-r border-geist-border z-50 flex flex-col shadow-[0_8px_30px_rgba(0,0,0,0.06)] animate-slide-in-left">
        {/* Header */}
        <div className="px-5 py-4 border-b border-geist-border flex justify-between items-center">
          <h2 className="text-sm font-semibold text-geist-fg">Settings</h2>
          <button
            className="p-1 rounded-md text-geist-fg-muted hover:text-geist-fg hover:bg-geist-bg-muted transition-colors"
            onClick={onClose}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {/* Section: Data Source */}
          <div>
            <h3 className="text-[11px] font-medium uppercase tracking-wider text-geist-fg-subtle mb-1">
              Data Source
            </h3>
            <div className="divide-y divide-geist-border">
              <ToggleRow
                label="Grafana"
                description="Loki polling for sidecar logs"
                checked={settings.grafana_enabled}
                onChange={(v) => onUpdate({ grafana_enabled: v })}
              />
              <ToggleRow
                label="LangSmith"
                description="Trace lookup for request IDs"
                checked={settings.langsmith_enabled}
                onChange={(v) => onUpdate({ langsmith_enabled: v })}
              />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
