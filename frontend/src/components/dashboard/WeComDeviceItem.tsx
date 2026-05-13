import { Smartphone, Brain, Crosshair, Circle } from 'lucide-react';
import type { WeComDevice } from '../../services/api';

interface WeComDeviceItemProps {
  device: WeComDevice;
}

export default function WeComDeviceItem({ device }: WeComDeviceItemProps) {
  const isRunning = device.running === true;
  const redDots = device.red_dot_pending ?? 0;
  const currentTarget = device.current_target;
  const followup = device.followup;
  const ai = device.ai;

  return (
    <div className={`
      p-3 rounded-lg border transition-all
      ${isRunning
        ? 'bg-white border-blue-100 shadow-sm'
        : 'bg-gray-50 border-gray-100'
      }
    `}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <Smartphone className={`w-4 h-4 ${isRunning ? 'text-blue-500' : 'text-gray-400'}`} />
        <span className="font-medium text-xs text-gray-700 truncate flex-1">
          {device.name || device.serial}
        </span>
        {isRunning && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        )}
      </div>

      {/* Status Pills */}
      <div className="flex flex-wrap gap-1 mb-2">
        {isRunning ? (
          <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
            running
          </span>
        ) : (
          <span className="text-[10px] px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded font-medium">
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

      {/* Red Dot & Target */}
      {(redDots > 0 || currentTarget) && (
        <div className="flex items-center gap-2 mb-1.5 text-[10px]">
          {redDots > 0 && (
            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-medium">
              <Circle className="w-1.5 h-1.5 fill-red-500 text-red-500" />
              {redDots}
            </span>
          )}
          {currentTarget && (
            <span className="text-red-600 truncate" title={currentTarget}>
              → {currentTarget}
            </span>
          )}
        </div>
      )}

      {/* Followup */}
      {followup?.in_progress && (
        <div className="flex items-center gap-1.5 mb-1.5 text-[10px]">
          <Crosshair className="w-3 h-3 text-amber-600" />
          <span className="text-amber-700 truncate" title={followup.target ?? undefined}>
            补刀: {followup.target || '...'}
          </span>
        </div>
      )}

      {/* AI Stats */}
      {ai && ai.requests_total > 0 && (
        <div className="flex items-center gap-1.5 pt-1.5 border-t border-gray-100 text-[10px] text-gray-500">
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
