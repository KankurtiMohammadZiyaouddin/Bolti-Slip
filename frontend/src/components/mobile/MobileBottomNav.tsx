// src/components/mobile/MobileBottomNav.tsx
import { NavLink } from 'react-router-dom';

export default function MobileBottomNav() {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 pb-safe bg-surface/95 backdrop-blur-xl border-t border-outline-variant/60 shadow-[0_-2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex items-center justify-around h-16 px-space-xs">
        {/* Dashboard */}
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-secondary'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">grid_view</span>
          <span className="font-label-xs text-[10px] mt-0.5">Dashboard</span>
        </NavLink>

        {/* Customers */}
        <NavLink
          to="/customers"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-secondary'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">group</span>
          <span className="font-label-xs text-[10px] mt-0.5">Customers</span>
        </NavLink>

        {/* New Ticket (Elevated Mic CTA) */}
        <NavLink
          to="/new-ticket"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-secondary'
            }`
          }
        >
          <div className="w-10 h-10 -mt-3 rounded-full bg-primary-container shadow-md flex items-center justify-center text-on-primary">
            <span className="material-symbols-outlined text-[22px]">mic</span>
          </div>
          <span className="font-label-xs text-[10px] mt-0.5 text-on-surface font-medium">New Slip</span>
        </NavLink>

        {/* Ticket History */}
        <NavLink
          to="/tickets"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-secondary'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">history</span>
          <span className="font-label-xs text-[10px] mt-0.5">History</span>
        </NavLink>

        {/* Settings */}
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-secondary'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">settings</span>
          <span className="font-label-xs text-[10px] mt-0.5">Settings</span>
        </NavLink>
      </div>
    </nav>
  );
}
