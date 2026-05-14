import { Handle, Position } from '@xyflow/react';
import { Smartphone, Brain, Crosshair } from 'lucide-react';
import type { WeComDevice } from '../../services/api';

interface WeComDeviceNodeData {
  label: string;
  device: WeComDevice;
  [key: string]: unknown;
}

interface WeComDeviceNodeProps {
  data: WeComDeviceNodeData;
  selected?: boolean;
}

export default function WeComDeviceNode({ data, selected }: WeComDeviceNodeProps) {
  const { device } = data;
  const isRunning = device.running === true;
  const redDots = device.red_dot_pending ?? 0;
  const currentTarget = device.current_target;
  const followup = device.followup;
  const ai = device.ai;

  const borderColor = isRunning ? 'border-blue-400' : 'border-gray-300';
  const bgColor = isRunning ? 'bg-white' : 'bg-gray-50 opacity-70';

  return (
    <div className={`
      px-3 py-2.5 rounded-lg border-2 shadow-md min-w-[170px] max-w-[200px] transition-all
      ${bgColor} ${borderColor}
      ${selected ? 'shadow-lg ring-2 ring-blue-400/50' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-blue-400 !border-blue-400" />

      {/* Header: serial + running indicator */}
      <div className="flex items-center gap-2 mb-1.5">
        <Smartphone className={`w-4 h-4 ${isRunning ? 'text-blue-500' : 'text-gray-400'}`} />
        <span className="font-semibold text-xs font-mono text-gray-800 truncate flex-1">
          {data.label}
        </span>
        {isRunning && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        )}
      </div>

      {/* Running status pill */}
      <div className="flex items-center gap-1 mb-1.5 flex-wrap">
        {isRunning ? (
          <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
            running
          </span>
        ) : (
          <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded font-medium">
            idle
          </span>
        )}
        {device.sync_running && (
          <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">sync</span>
        )}
        {device.followup_running && (
          <span className="text-[10px] px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded">followup</span>
        )}
      </div>

      {/* Red dot badge */}
      {(redDots > 0 || currentTarget) && (
        <div className="flex items-center gap-1 mb-1 text-[10px]">
          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
            {redDots}
          </span>
          {currentTarget && (
            <span className="text-red-600 truncate max-w-[100px]" title={currentTarget}>
              → {currentTarget}
            </span>
          )}
        </div>
      )}

      {/* Followup in progress */}
      {followup?.in_progress && (
        <div className="flex items-center gap-1 mb-1 text-[10px]">
          <Crosshair className="w-3 h-3 text-amber-600" />
          <span className="text-amber-700 truncate max-w-[120px]" title={followup.target ?? undefined}>
            Follow-up: {followup.target || '...'}
          </span>
        </div>
      )}

      {/* AI stats (compact) */}
      {ai && ai.requests_total > 0 && (
        <div className="flex items-center gap-1 pt-1 border-t border-gray-200 text-[10px] text-gray-500">
          <Brain className="w-3 h-3" />
          <span>AI: {ai.requests_total}</span>
          {ai.failures_total > 0 && (
            <span className="text-red-500">({ai.failures_total} err)</span>
          )}
        </div>
      )}
    </div>
  );
}
