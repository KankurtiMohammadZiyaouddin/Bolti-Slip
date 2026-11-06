// src/components/desktop/DesktopHeader.tsx
import { useLocation } from 'react-router-dom';

const TITLE_MAP: Record<string, string> = {
  '/': 'Dashboard',
  '/dashboard': 'Dashboard',
  '/new-ticket': 'New Ticket',
  '/tickets': 'Ticket History',
  '/settings': 'Settings',
};

export default function DesktopHeader() {
  const location = useLocation();

  // Handle dynamic ticket detail title or default
  let title = TITLE_MAP[location.pathname];
  if (!title && location.pathname.startsWith('/tickets/')) {
    title = 'Review Repair Ticket';
  }
  if (!title) title = 'Bolti Slip';

  return (
    <header className="fixed top-0 left-[248px] right-0 h-16 bg-surface-container-lowest border-b border-outline-variant z-40 px-space-xl flex items-center justify-between">
      <div className="flex items-center gap-space-sm text-secondary">
        <span className="font-headline-sm text-headline-sm text-on-surface font-semibold tracking-tight">
          {title}
        </span>
      </div>

      <div className="flex items-center gap-space-md">
        {/* Search */}
        <div className="relative flex items-center">
          <span className="material-symbols-outlined absolute left-3 text-secondary text-[18px] pointer-events-none">
            search
          </span>
          <input
            type="text"
            placeholder="Search tickets, customers..."
            className="w-64 h-10 pl-9 pr-space-md bg-surface-container-lowest border border-outline-variant rounded-lg font-body-sm text-body-sm text-on-surface placeholder:text-secondary focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
          />
        </div>

        {/* Notifications */}
        <button
          type="button"
          aria-label="Notifications"
          className="w-10 h-10 rounded-lg border border-outline-variant bg-surface-container-lowest text-secondary hover:text-on-surface hover:bg-surface-container-low flex items-center justify-center transition-colors cursor-pointer"
        >
          <span className="material-symbols-outlined text-[20px]">notifications</span>
        </button>

        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 text-on-primary">
          <span className="material-symbols-outlined text-[18px]">person</span>
        </div>
      </div>
    </header>
  );
}
