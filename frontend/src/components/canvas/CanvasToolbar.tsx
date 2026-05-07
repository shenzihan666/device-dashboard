import { Pencil, Eye, RotateCcw } from 'lucide-react';

interface CanvasToolbarProps {
  mode: 'view' | 'edit';
  onModeChange: (mode: 'view' | 'edit') => void;
  onResetLayout: () => void;
}

export default function CanvasToolbar({ mode, onModeChange, onResetLayout }: CanvasToolbarProps) {
  return (
    <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
      {/* Mode toggle */}
      <div className="flex gap-0.5 bg-foundry-card border border-foundry-border rounded-lg p-1 shadow-lg">
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            mode === 'view'
              ? 'bg-foundry-accent/15 text-foundry-accent'
              : 'text-foundry-text-dim hover:text-foundry-text'
          }`}
          onClick={() => onModeChange('view')}
        >
          <Eye className="w-3.5 h-3.5" />
          View
        </button>
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            mode === 'edit'
              ? 'bg-foundry-amber/15 text-foundry-amber'
              : 'text-foundry-text-dim hover:text-foundry-text'
          }`}
          onClick={() => onModeChange('edit')}
        >
          <Pencil className="w-3.5 h-3.5" />
          Edit
        </button>
      </div>

      {/* Reset layout button (only in edit mode) */}
      {mode === 'edit' && (
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
            bg-foundry-card border border-foundry-border text-foundry-text-dim
            hover:text-foundry-red hover:border-foundry-red/50 transition-all shadow-lg"
          onClick={onResetLayout}
          title="Reset all node positions to auto-layout"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
      )}

      {/* Edit mode indicator */}
      {mode === 'edit' && (
        <div className="px-2.5 py-1 rounded-md bg-foundry-amber/10 border border-foundry-amber/30 text-foundry-amber text-[10px] font-medium uppercase tracking-wider shadow-lg">
          Editing
        </div>
      )}
    </div>
  );
}
