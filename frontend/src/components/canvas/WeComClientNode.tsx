import { Handle, Position } from '@xyflow/react';
import { Monitor, Smartphone, Wifi, WifiOff } from 'lucide-react';
import type { WeComClientState } from '../../services/api';

interface WeComClientNodeData {
  label: string;
  state: WeComClientState;
  [key: string]: unknown;
}

interface WeComClientNodeProps {
  data: WeComClientNodeData;
  selected?: boolean;
}

export default function WeComClientNode({ data, selected }: WeComClientNodeProps) {
  const { state } = data;
  const isOffline = !state.online;

  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] max-w-[230px] transition-all
      ${isOffline ? 'bg-gray-100 border-gray-300 opacity-60' : 'bg-blue-50 border-blue-400'}
      ${selected ? 'shadow-lg ring-2 ring-blue-400/50' : ''}
    `}>
      <Handle type="source" position={Position.Top} className="!w-3 !h-3 !bg-blue-400 !border-blue-400" />

      <div className="flex items-center gap-2 mb-2">
        <div className="text-blue-600">
          <Monitor className="w-5 h-5" />
        </div>
        <div className="font-semibold text-sm text-blue-800 truncate flex-1">
          {data.label}
        </div>
        <span className={`w-2 h-2 rounded-full ${isOffline ? 'bg-gray-400' : 'bg-emerald-500'}`} />
      </div>

      <div className="flex items-center gap-1 mb-1.5">
        <span className="text-[10px] font-mono px-1.5 py-0.5 bg-blue-200 text-blue-800 rounded">
          v{state.version}
        </span>
        {state.ai_reachable ? (
          <span className="text-[10px] flex items-center gap-0.5 px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded">
            <Wifi className="w-2.5 h-2.5" /> AI OK
          </span>
        ) : (
          <span className="text-[10px] flex items-center gap-0.5 px-1.5 py-0.5 bg-red-100 text-red-700 rounded">
            <WifiOff className="w-2.5 h-2.5" /> AI Down
          </span>
        )}
      </div>

      {state.brain_url && (
        <div className="text-[10px] text-gray-500 truncate mb-1.5" title={state.brain_url}>
          Brain: {state.brain_url.replace('http://', '').replace('https://', '')}
        </div>
      )}

      <div className="flex items-center gap-2 pt-2 border-t border-blue-200 text-xs">
        <div className="flex items-center gap-1 text-gray-600">
          <Smartphone className="w-3 h-3" />
          <span>Devices: <strong className="text-blue-700">{state.device_count}</strong></span>
        </div>
        {state.ai_response_ms != null && (
          <div className="text-gray-500">
            {state.ai_response_ms.toFixed(0)}ms
          </div>
        )}
      </div>

      {state.devices.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1 text-[9px]">
          {(() => {
            const runCount = state.devices.filter((d) => d.running).length;
            const idleCount = state.devices.length - runCount;
            return (
              <>
                {runCount > 0 && (
                  <span className="px-1 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
                    {runCount} running
                  </span>
                )}
                {idleCount > 0 && (
                  <span className="px-1 py-0.5 bg-gray-100 text-gray-500 rounded">
                    {idleCount} idle
                  </span>
                )}
              </>
            );
          })()}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-blue-400 !border-blue-400" />
    </div>
  );
}
