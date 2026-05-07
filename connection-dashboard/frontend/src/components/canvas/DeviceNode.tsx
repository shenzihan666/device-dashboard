import { Handle, Position } from '@xyflow/react';
import { Smartphone } from 'lucide-react';

interface DeviceNodeData {
  label: string;
  serial: string;
  host?: string;
  aiUrl: string;
  status: string;
  [key: string]: unknown;
}

interface DeviceNodeProps {
  data: DeviceNodeData;
  selected?: boolean;
}

export default function DeviceNode({ data, selected }: DeviceNodeProps) {
  const isOffline = data.status === 'offline';
  const borderColor = isOffline ? 'border-foundry-red' : 'border-foundry-purple';
  const iconColor = isOffline ? 'text-foundry-red' : 'text-foundry-purple';

  const shortUrl = (data.aiUrl || '')
    .replace('http://', '')
    .replace('/chat', '');

  return (
    <div className={`
      px-3 py-2.5 rounded-lg border-2 shadow-md min-w-[160px] max-w-[180px] transition-all
      bg-[#12101e] ${borderColor}
      ${selected ? 'shadow-lg ring-2 ring-foundry-purple/50' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-foundry-purple !border-foundry-purple" />

      <div className="flex items-center gap-2 mb-1.5">
        <div className={iconColor}>
          <Smartphone className="w-4 h-4" />
        </div>
        <div className="font-semibold text-xs text-foundry-text font-mono">
          {data.label}
        </div>
      </div>

      {data.host && (
        <div className="text-[10px] text-foundry-text-dim truncate mb-1">
          Host: {data.host}
        </div>
      )}

      <div className="text-[10px] text-foundry-amber truncate mb-1.5">
        {shortUrl || 'No server'}
      </div>

      <div className="flex items-center gap-1 pt-1.5 border-t border-foundry-border">
        <span className={`w-1.5 h-1.5 rounded-full ${isOffline ? 'bg-foundry-red' : 'bg-foundry-green'}`} />
        <span className={`text-[10px] font-mono ${isOffline ? 'text-foundry-red' : 'text-foundry-green'}`}>
          {data.status}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-foundry-purple !border-foundry-purple" />
    </div>
  );
}
