// src/layouts/AppLayout.tsx
import { useResponsive } from '../hooks/useResponsive';
import DesktopLayout from './DesktopLayout';
import MobileLayout from './MobileLayout';

/**
 * AppLayout dynamically renders DesktopLayout (for screens >= 768px)
 * or MobileLayout (for screens < 768px) according to the Stitch design specifications.
 */
export default function AppLayout() {
  const { isDesktop } = useResponsive(768);

  return isDesktop ? <DesktopLayout /> : <MobileLayout />;
}
