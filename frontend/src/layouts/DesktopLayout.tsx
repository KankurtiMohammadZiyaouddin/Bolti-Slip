// src/layouts/DesktopLayout.tsx
import { Outlet } from 'react-router-dom';
import DesktopSidebar from '../components/desktop/DesktopSidebar';
import DesktopHeader from '../components/desktop/DesktopHeader';

export default function DesktopLayout() {
  return (
    <div className="bg-surface font-sans text-on-surface antialiased min-h-screen">
      {/* 248px Persistent Left Sidebar */}
      <DesktopSidebar />

      {/* Main Workspace Frame */}
      <div className="pl-[248px]">
        {/* Sticky 64px Top Header */}
        <DesktopHeader />

        {/* Content Canvas */}
        <main className="relative pt-16 w-full p-margin bg-surface min-h-screen">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
