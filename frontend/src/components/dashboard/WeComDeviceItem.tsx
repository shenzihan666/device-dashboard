import { useState } from 'react';
import { Smartphone, Brain, Crosshair, Circle, Play, Pause, Square, RotateCcw, RefreshCw } from 'lucide-react';
import type { WeComDevice } from '../../services/api';
import { sendDeviceCommand, restartWecomApp } from '../../services/api';

interface WeComDeviceItemProps {
  device: WeComDevice;
  instanceId?: string;
  online?: boolean;
}

export default function WeComDeviceItem({ device, instanceId, online }: WeComDeviceItemProps) {
  const isRunning = device.running === true;
  const redDots = device.red_dot_pending ?? 0;
  const currentTarget = device.current_target;
  const followup = device.followup;
  const ai = device.ai;
  const [loading, setLoading] = useState<string | null>(null);

  const canControl = online && instanceId;

  async function handleCommand(action: 'start' | 'stop' | 'pause' | 'resume' | 'restart') {
    if (!instanceId) return;
    setLoading(action);
    try {
      await sendDeviceCommand(instanceId, device.serial, action);
    } catch {
      // Error handled silently — UI will update on next heartbeat
    } finally {
      setLoading(null);
    }
  }

  async function handleAppRestart() {
    if (!instanceId) return;
    setLoading('app_restart');
    try {
      await restartWecomApp(instanceId, device.serial);
    } catch {
      // Error handled silently
    } finally {
      setLoading(null);
    }
  }

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

      {/* Control Buttons */}
      {canControl && (
        <div className="flex items-center gap-1 mb-2">
          {!isRunning ? (
            <button
              onClick={() => handleCommand('start')}
              disabled={loading !== null}
              className="p-1 rounded hover:bg-emerald-100 text-emerald-600 disabled:opacity-30 transition-colors"
              title="启动实时回复"
            >
              <Play className="w-3.5 h-3.5" />
            </button>
          ) : (
            <>
              <button
                onClick={() => handleCommand('pause')}
                disabled={loading !== null}
                className="p-1 rounded hover:bg-amber-100 text-amber-600 disabled:opacity-30 transition-colors"
                title="暂停实时回复"
              >
                <Pause className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleCommand('resume')}
                disabled={loading !== null}
                className="p-1 rounded hover:bg-blue-100 text-blue-600 disabled:opacity-30 transition-colors"
                title="恢复实时回复"
              >
                <Play className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleCommand('stop')}
                disabled={loading !== null}
                className="p-1 rounded hover:bg-red-100 text-red-600 disabled:opacity-30 transition-colors"
                title="停止实时回复"
              >
                <Square className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          <button
            onClick={() => handleCommand('restart')}
            disabled={loading !== null}
            className="p-1 rounded hover:bg-violet-100 text-violet-600 disabled:opacity-30 transition-colors"
            title="重启实时回复"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading === 'restart' ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleAppRestart}
            disabled={loading !== null}
            className="p-1 rounded hover:bg-orange-100 text-orange-600 disabled:opacity-30 transition-colors ml-auto"
            title="重启手机企微App"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading === 'app_restart' ? 'animate-spin' : ''}`} />
          </button>
        </div>
      )}

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
