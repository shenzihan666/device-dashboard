import { LayoutDashboard, PenTool, Settings } from 'lucide-react';

export type Page = 'dashboard' | 'canvas' | 'settings';

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

const NAV_ITEMS: { page: Page; icon: typeof LayoutDashboard; label: string }[] = [
  { page: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { page: 'canvas', icon: PenTool, label: 'Canvas' },
  { page: 'settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <nav className="h-full bg-white border-r border-geist-border flex flex-col">
      <div className="px-5 h-[56px] flex items-center border-b border-geist-border">
        <span className="text-geist-fg font-semibold text-sm tracking-tight whitespace-nowrap">
          &#x25C8; WeCom AI
        </span>
      </div>

      <div className="flex-1 py-2">
        {NAV_ITEMS.map(({ page, icon: Icon, label }) => (
          <button
            key={page}
            onClick={() => onNavigate(page)}
            className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-colors ${
              currentPage === page
                ? 'bg-geist-bg-muted text-geist-fg'
                : 'text-geist-fg-muted hover:bg-geist-bg-muted/50 hover:text-geist-fg'
            }`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
