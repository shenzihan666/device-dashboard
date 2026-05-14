import { LayoutGrid, Activity } from 'lucide-react';

type Page = 'canvas' | 'dashboard';

interface SidebarProps {
  currentPage: Page;
  onPageChange: (page: Page) => void;
}

export default function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  return (
    <div className="w-16 h-full bg-white border-r border-geist-border flex flex-col items-center py-4 gap-2">
      <button
        onClick={() => onPageChange('canvas')}
        className={`
          w-12 h-12 rounded-lg flex items-center justify-center transition-all
          ${currentPage === 'canvas'
            ? 'bg-geist-accent text-white shadow-md'
            : 'text-geist-fg-muted hover:bg-geist-bg-muted hover:text-geist-fg'
          }
        `}
        title="Canvas (Topology)"
      >
        <LayoutGrid className="w-5 h-5" />
      </button>

      <button
        onClick={() => onPageChange('dashboard')}
        className={`
          w-12 h-12 rounded-lg flex items-center justify-center transition-all
          ${currentPage === 'dashboard'
            ? 'bg-geist-accent text-white shadow-md'
            : 'text-geist-fg-muted hover:bg-geist-bg-muted hover:text-geist-fg'
          }
        `}
        title="Dashboard"
      >
        <Activity className="w-5 h-5" />
      </button>
    </div>
  );
}
