import { Handle, Position } from '@xyflow/react';
import { Server } from 'lucide-react';

interface ServerNodeData {
  label: string;
  url: string;
  deviceCount: number;
  [key: string]: unknown;
}

interface ServerNodeProps {
  data: ServerNodeData;
  selected?: boolean;
}

export default function ServerNode({ data, selected }: ServerNodeProps) {
  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] max-w-[220px] transition-all
      bg-[#0a1a24] border-foundry-accent
      ${selected ? 'shadow-lg ring-2 ring-foundry-accent/50' : ''}
    `}>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-foundry-accent !border-foundry-accent" />

      <div className="flex items-center gap-2 mb-2">
        <div className="text-foundry-accent">
          <Server className="w-5 h-5" />
        </div>
        <div className="font-semibold text-sm text-foundry-accent truncate">
          {data.label}
        </div>
      </div>

      <div className="text-xs text-foundry-text-dim truncate mb-1.5">
        {data.url}
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-foundry-border">
        <span className="text-xs font-mono text-foundry-text-dim">
          Devices:
        </span>
        <span className="text-xs font-bold text-foundry-accent">
          {data.deviceCount}
        </span>
      </div>
    </div>
  );
}
