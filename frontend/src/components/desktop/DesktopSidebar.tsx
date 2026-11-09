// src/components/desktop/DesktopSidebar.tsx
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface NavItem {
  name: string;
  path: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: 'dashboard' },
  { name: 'New Ticket', path: '/new-ticket', icon: 'mic' },
  { name: 'Customers', path: '/customers', icon: 'group' },
  { name: 'Ticket History', path: '/tickets', icon: 'history' },
  { name: 'Settings', path: '/settings', icon: 'settings' },
];

export default function DesktopSidebar() {
  const { shop, logout } = useAuth();

  const shopInitials = shop?.shop_name
    ? shop.shop_name
        .split(' ')
        .map((w) => w[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'BS';

  return (
    <aside className="fixed left-0 top-0 h-full w-[248px] bg-surface-container-lowest border-r border-outline-variant z-50 flex flex-col justify-between">
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="h-16 px-space-md border-b border-outline-variant flex items-center gap-space-sm">
          <div className="w-9 h-9 rounded-lg bg-primary-container flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-on-primary text-[20px]">mic</span>
          </div>
          <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight font-semibold">
            Bolti Slip
          </span>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-col gap-space-xs p-space-md">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center gap-space-sm px-space-sm py-2 rounded-lg transition-colors font-label-md text-label-md ${
                  isActive
                    ? 'bg-secondary-container text-primary font-medium'
                    : 'text-secondary hover:text-on-surface hover:bg-surface-container-low'
                }`
              }
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Shop Profile & Logout */}
      <div className="p-space-md border-t border-outline-variant flex flex-col gap-2">
        <div className="flex items-center gap-space-sm p-space-xs rounded-lg hover:bg-surface-container-low transition-colors">
          <div className="w-8 h-8 rounded-full bg-secondary-container text-secondary flex items-center justify-center font-label-md text-label-md font-semibold shrink-0">
            {shopInitials}
          </div>
          <div className="flex flex-col min-w-0 flex-1">
            <span className="font-label-md text-label-md text-on-surface truncate font-medium">
              {shop?.shop_name || 'Sharma Electronics'}
            </span>
            <span className="font-label-xs text-label-xs text-secondary truncate">
              {shop?.branch || 'Pune Branch'}
            </span>
          </div>
        </div>

        {/* Logout Button */}
        <button
          type="button"
          onClick={() => logout()}
          className="flex w-full items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
        >
          <span className="material-symbols-outlined text-[16px]">logout</span>
          <span>लॉगआउट (Logout)</span>
        </button>
      </div>
    </aside>
  );
}
