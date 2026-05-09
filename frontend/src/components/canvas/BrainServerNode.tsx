import { Handle, Position } from '@xyflow/react';
import { Brain, Activity } from 'lucide-react';
import type { BrainServerState } from '../../services/api';

interface BrainServerNodeData {
  label: string;
  state: BrainServerState;
  [key: string]: unknown;
}

interface BrainServerNodeProps {
  data: BrainServerNodeData;
  selected?: boolean;
}

function healthColor(status: string): string {
  if (status === 'healthy' || status === 'ok') return 'bg-emerald-500';
  if (status === 'warning' || status === 'degraded') return 'bg-amber-500';
  return 'bg-red-500';
}

export default function BrainServerNode({ data, selected }: BrainServerNodeProps) {
  const { state } = data;
  const isOffline = !state.online;

  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] max-w-[220px] transition-all
      ${isOffline ? 'bg-gray-100 border-gray-300 opacity-60' : 'bg-orange-50 border-orange-400'}
      ${selected ? 'shadow-lg ring-2 ring-orange-400/50' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-orange-400 !border-orange-400" />
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-orange-400 !border-orange-400" />

      <div className="flex items-center gap-2 mb-2">
        <div className="text-orange-600">
          <Brain className="w-5 h-5" />
        </div>
        <div className="font-semibold text-sm text-orange-800 truncate flex-1">
          {data.label}
        </div>
        <span className={`w-2 h-2 rounded-full ${isOffline ? 'bg-gray-400' : healthColor(state.health_status)}`} />
      </div>

      <div className="flex items-center gap-1 mb-1.5">
        <span className="text-[10px] font-mono px-1.5 py-0.5 bg-orange-200 text-orange-800 rounded">
          v{state.version}
        </span>
        {isOffline && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
            offline
          </span>
        )}
      </div>

      <div className="flex items-center gap-3 pt-2 border-t border-orange-200 text-xs">
        <div className="flex items-center gap-1 text-gray-600">
          <Activity className="w-3 h-3" />
          <span>Workers: <strong className="text-orange-700">{state.worker_count}</strong></span>
        </div>
        <div className="text-gray-500">
          Inflight: <strong className="text-orange-700">{state.avg_inflight.toFixed(1)}</strong>
        </div>
      </div>
    </div>
  );
}
