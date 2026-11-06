// src/components/StatusBadge.tsx
import type { TicketStatus } from '../types/ticket';

const LABELS: Record<TicketStatus, string> = {
  open:        'Pending',
  in_progress: 'In Progress',
  resolved:    'Completed',
  closed:      'Closed',
};

interface Props {
  status: TicketStatus;
}

export default function StatusBadge({ status }: Props) {
  return (
    <span className={`badge badge-${status}`}>
      {LABELS[status] ?? status}
    </span>
  );
}
