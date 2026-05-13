import { Brain, Activity, Cpu, HardDrive } from 'lucide-react';
import type { BrainServerState } from '../../services/api';

interface BrainServerCardProps {
  state: BrainServerState;
}

function healthColor(status: string): string {
  if (status === 'healthy' || status === 'ok') return 'bg-emerald-500';
  if (status === 'warning' || status === 'degraded') return 'bg-amber-500';
  return 'bg-red-500';
}

function healthBorder(status: string): string {
  if (status === 'healthy' || status === 'ok') return 'border-emerald-200';
  if (status === 'warning' || status === 'degraded') return 'border-amber-200';
  return 'border-red-200';
}

export default function BrainServerCard({ state }: BrainServerCardProps) {
  const isOffline = !state.online;

  return (
    <div className={`
      p-4 rounded-xl border-2 shadow-sm transition-all
      ${isOffline
        ? 'bg-gray-50 border-gray-200 opacity-60'
        : `bg-orange-50/50 border-orange-200 ${healthBorder(state.health_status)}`
      }
    `}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${isOffline ? 'bg-gray-200' : 'bg-orange-100'}`}>
          <Brain className={`w-5 h-5 ${isOffline ? 'text-gray-500' : 'text-orange-600'}`} />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-sm text-gray-800">{state.name}</h3>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
              v{state.version}
            </span>
            {isOffline ? (
              <span className="text-[10px] font-medium text-gray-500">offline</span>
            ) : (
              <span className="flex items-center gap-1 text-[10px] font-medium text-gray-600">
                <span className={`w-2 h-2 rounded-full ${healthColor(state.health_status)}`} />
                {state.health_status}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg">
          <Activity className="w-4 h-4 text-orange-500" />
          <div>
            <div className="text-[10px] text-gray-500">Workers</div>
            <div className="text-sm font-semibold text-gray-800">{state.worker_count}</div>
          </div>
        </div>

        <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg">
          <div className="w-4 h-4 flex items-center justify-center text-orange-500 font-bold text-xs">Σ</div>
          <div>
            <div className="text-[10px] text-gray-500">Handled</div>
            <div className="text-sm font-semibold text-gray-800">{state.total_handled.toLocaleString()}</div>
          </div>
        </div>

        <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg">
          <div className="w-4 h-4 flex items-center justify-center text-orange-500 font-bold text-xs">~</div>
          <div>
            <div className="text-[10px] text-gray-500">Inflight</div>
            <div className="text-sm font-semibold text-gray-800">{state.avg_inflight.toFixed(1)}</div>
          </div>
        </div>

        {state.memory_mb != null && (
          <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg">
            <HardDrive className="w-4 h-4 text-orange-500" />
            <div>
              <div className="text-[10px] text-gray-500">Memory</div>
              <div className="text-sm font-semibold text-gray-800">{state.memory_mb} MB</div>
            </div>
          </div>
        )}

        {state.cpu_pct != null && (
          <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg">
            <Cpu className="w-4 h-4 text-orange-500" />
            <div>
              <div className="text-[10px] text-gray-500">CPU</div>
              <div className="text-sm font-semibold text-gray-800">{state.cpu_pct.toFixed(1)}%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
