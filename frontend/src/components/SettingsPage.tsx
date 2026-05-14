import type { AppSettingsState } from '../services/api';

interface SettingsPageProps {
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

export default function SettingsPage({ settings, onUpdate }: SettingsPageProps) {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-lg font-semibold text-geist-fg mb-6">Settings</h1>

        <div>
          <h3 className="text-[11px] font-medium uppercase tracking-wider text-geist-fg-subtle mb-1">
            Data Source
          </h3>
          <div className="divide-y divide-geist-border">
            <ToggleRow
              label="Point-to-point"
              description="Heartbeat from brain server & WeCom client"
              checked={settings.point_to_point_enabled}
              onChange={(v) => onUpdate({ point_to_point_enabled: v })}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
