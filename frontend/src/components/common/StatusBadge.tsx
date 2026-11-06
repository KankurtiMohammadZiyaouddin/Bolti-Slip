// src/components/common/StatusBadge.tsx
import type { TicketStatus } from '../../types/ticket';
import { mapStatusToUi } from '../../utils/formatters';

interface Props {
  status: TicketStatus;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: Props) {
  const { label, bgStyle, dotStyle } = mapStatusToUi(status);

  return (
    <span
      className={`inline-flex items-center gap-1.5 h-6 px-2.5 rounded-full text-[11px] font-semibold uppercase tracking-wider ${className}`}
      style={bgStyle}
    >
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={dotStyle} />
      <span>{label}</span>
    </span>
  );
}
