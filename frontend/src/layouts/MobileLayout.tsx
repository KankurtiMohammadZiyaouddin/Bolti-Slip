// src/layouts/MobileLayout.tsx
import { Outlet } from 'react-router-dom';
import MobileHeader from '../components/mobile/MobileHeader';
import MobileBottomNav from '../components/mobile/MobileBottomNav';

export default function MobileLayout() {
  return (
    <div className="bg-surface font-sans text-on-surface flex flex-col min-h-screen">
      {/* Compact Top Mobile Header */}
      <MobileHeader />

      {/* Fluid Mobile Content Canvas with Bottom Nav Spacing */}
      <main className="flex-1 flex flex-col relative w-full pt-16 pb-20 bg-surface">
        <div className="flex flex-col w-full px-space-md py-space-md">
          <Outlet />
        </div>
      </main>

      {/* 4-Item Fixed Bottom Navigation Bar */}
      <MobileBottomNav />
    </div>
  );
}
