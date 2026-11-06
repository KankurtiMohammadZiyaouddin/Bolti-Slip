// src/components/mobile/MobileHeader.tsx

export default function MobileHeader() {
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
              Sharma Electronics
            </span>
          </div>
        </div>

        <div className="flex items-center gap-space-xs">
          <button
            type="button"
            aria-label="Notifications"
            className="w-10 h-10 flex items-center justify-center rounded-full text-secondary hover:text-on-surface transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[22px]">notifications</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary shrink-0">
            <span className="material-symbols-outlined text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
}
