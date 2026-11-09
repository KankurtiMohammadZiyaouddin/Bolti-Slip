// src/components/mobile/MobileHeader.tsx
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function MobileHeader() {
  const { shop, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-surface/90 backdrop-blur-xl border-b border-outline-variant/60 pt-safe">
      <div className="h-16 px-space-md flex items-center justify-between">
        <div className="flex items-center gap-space-sm">
          <div className="w-9 h-9 rounded-lg bg-primary-container flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-on-primary text-[20px]">mic</span>
          </div>
          <div className="flex flex-col">
            <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight leading-none font-semibold">
              Bolti Slip
            </span>
            <span className="font-label-xs text-label-xs text-secondary font-medium">
              {shop?.shop_name || 'Sharma Electronics'}
            </span>
          </div>
        </div>

        <div className="relative flex items-center gap-space-xs">
          <button
            type="button"
            aria-label="Profile Menu"
            onClick={() => setShowMenu((prev) => !prev)}
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary shrink-0"
          >
            <span className="material-symbols-outlined text-[18px]">person</span>
          </button>

          {showMenu && (
            <div className="absolute right-0 top-11 w-48 rounded-xl border border-gray-100 bg-white p-2 shadow-xl">
              <div className="border-b border-gray-100 px-3 py-2">
                <p className="text-xs font-semibold text-gray-900 truncate">{shop?.owner_name}</p>
                <p className="text-[11px] text-gray-500 truncate">{shop?.branch || 'Main Branch'}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowMenu(false);
                  logout();
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors mt-1"
              >
                <span className="material-symbols-outlined text-[16px]">logout</span>
                <span>लॉगआउट (Logout)</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
