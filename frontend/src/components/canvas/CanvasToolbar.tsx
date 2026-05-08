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
      <div className="flex gap-0.5 bg-geist-bg-muted border border-geist-border rounded-lg p-0.5 shadow-sm">
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            mode === 'view'
              ? 'bg-white shadow-sm text-geist-fg'
              : 'text-geist-fg-muted hover:text-geist-fg hover:bg-geist-bg-subtle'
          }`}
          onClick={() => onModeChange('view')}
        >
          <Eye className="w-3.5 h-3.5" />
          View
        </button>
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            mode === 'edit'
              ? 'bg-white shadow-sm text-geist-fg'
              : 'text-geist-fg-muted hover:text-geist-fg hover:bg-geist-bg-subtle'
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
            bg-white border border-geist-border text-geist-fg-muted
            hover:text-red-600 hover:border-red-300 transition-all shadow-sm"
          onClick={onResetLayout}
          title="Reset all node positions to auto-layout"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
      )}

      {/* Edit mode indicator */}
      {mode === 'edit' && (
        <div className="px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-700 text-[10px] font-medium uppercase tracking-wider shadow-sm">
          Editing
        </div>
      )}
    </div>
  );
}
