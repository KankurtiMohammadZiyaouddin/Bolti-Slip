// src/hooks/useResponsive.ts
import { useState, useEffect } from 'react';

/**
 * Hook to detect responsive desktop vs mobile layout.
 * Default breakpoint: 768px (md breakpoint aligned with Stitch layouts).
 */
export function useResponsive(breakpoint = 768) {
  const [isDesktop, setIsDesktop] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true;
    return window.innerWidth >= breakpoint;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const media = window.matchMedia(`(min-width: ${breakpoint}px)`);
    const update = (e: MediaQueryListEvent | MediaQueryList) => setIsDesktop(e.matches);

    setIsDesktop(media.matches);

    if (media.addEventListener) {
      media.addEventListener('change', update);
      return () => media.removeEventListener('change', update);
    } else {
      // Compatibility fallback
      media.addListener(update);
      return () => media.removeListener(update);
    }
  }, [breakpoint]);

  return { isDesktop, isMobile: !isDesktop };
}
