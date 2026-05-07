import { Handle, Position } from '@xyflow/react';
import { Monitor } from 'lucide-react';

interface HostNodeData {
  label: string;
  status: string;
  deviceCount: number;
  [key: string]: unknown;
}

interface HostNodeProps {
  data: HostNodeData;
  selected?: boolean;
}

export default function HostNode({ data, selected }: HostNodeProps) {
  const isOffline = data.status === 'offline';
  const borderColor = isOffline ? 'border-foundry-red' : 'border-foundry-green';
  const iconColor = isOffline ? 'text-foundry-red' : 'text-foundry-green';

  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 shadow-md min-w-[180px] max-w-[200px] transition-all
      bg-[#0f1a14] ${borderColor}
      ${selected ? 'shadow-lg ring-2 ring-foundry-green/50' : ''}
    `}>
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-foundry-green !border-foundry-green" />

      <div className="flex items-center gap-2 mb-2">
        <div className={iconColor}>
          <Monitor className="w-5 h-5" />
        </div>
        <div className="font-semibold text-sm text-foundry-text truncate">
          {data.label}
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2 border-t border-foundry-border">
        <div className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${isOffline ? 'bg-foundry-red' : 'bg-foundry-green'}`} />
          <span className={`text-xs font-mono ${isOffline ? 'text-foundry-red' : 'text-foundry-green'}`}>
            {data.status}
          </span>
        </div>
        <span className="text-xs text-foundry-text-dim">
          {data.deviceCount} devices
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-foundry-green !border-foundry-green" />
    </div>
  );
}
