import { useState } from 'react';
import { Monitor, Smartphone, Wifi, WifiOff, ChevronDown, ChevronRight } from 'lucide-react';
import type { WeComClientState } from '../../services/api';
import WeComDeviceItem from './WeComDeviceItem';

interface WeComClientCardProps {
  state: WeComClientState;
}

export default function WeComClientCard({ state }: WeComClientCardProps) {
  const [expanded, setExpanded] = useState(true);
  const isOffline = !state.online;

  const runCount = state.devices.filter((d) => d.running).length;
  const idleCount = state.devices.length - runCount;

  return (
    <div className={`
      p-4 rounded-xl border-2 shadow-sm transition-all
      ${isOffline
        ? 'bg-gray-50 border-gray-200 opacity-60'
        : 'bg-blue-50/50 border-blue-200'
      }
    `}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${isOffline ? 'bg-gray-200' : 'bg-blue-100'}`}>
          <Monitor className={`w-5 h-5 ${isOffline ? 'text-gray-500' : 'text-blue-600'}`} />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-sm text-gray-800">{state.name}</h3>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
              v{state.version}
            </span>
            {isOffline ? (
              <span className="text-[10px] font-medium text-gray-500">offline</span>
            ) : state.ai_reachable ? (
              <span className="text-[10px] flex items-center gap-0.5 px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded">
                <Wifi className="w-2.5 h-2.5" /> AI OK
              </span>
            ) : (
              <span className="text-[10px] flex items-center gap-0.5 px-1.5 py-0.5 bg-red-100 text-red-700 rounded">
                <WifiOff className="w-2.5 h-2.5" /> AI Down
              </span>
            )}
            {state.ai_response_ms != null && !isOffline && (
              <span className="text-[10px] text-gray-500">{state.ai_response_ms.toFixed(0)}ms</span>
            )}
          </div>
        </div>
      </div>

      {/* Brain URL */}
      {state.brain_url && !isOffline && (
        <div className="text-[10px] text-gray-500 mb-3 truncate" title={state.brain_url}>
          Brain: {state.brain_url.replace('http://', '').replace('https://', '')}
        </div>
      )}

      {/* Device Summary Bar */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-2 bg-white/60 rounded-lg mb-2 hover:bg-white/80 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Smartphone className="w-4 h-4 text-blue-500" />
          <span className="text-xs font-medium text-gray-700">
            {state.device_count} device{state.device_count !== 1 ? 's' : ''}
          </span>
          {!isOffline && (
            <div className="flex gap-1">
              {runCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
                  {runCount} running
                </span>
              )}
              {idleCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
                  {idleCount} idle
                </span>
              )}
            </div>
          )}
        </div>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Device List */}
      {expanded && state.devices.length > 0 && (
        <div className="space-y-2">
          {state.devices.map((device) => (
            <WeComDeviceItem
              key={device.serial}
              device={device}
              instanceId={state.instance_id}
              online={state.online}
            />
          ))}
        </div>
      )}

      {expanded && state.devices.length === 0 && (
        <div className="text-center py-4 text-xs text-gray-400">
          No devices
        </div>
      )}
    </div>
  );
}
