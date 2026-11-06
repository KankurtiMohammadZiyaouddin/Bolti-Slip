// src/utils/formatters.ts
import type { TicketStatus } from '../types/ticket';

/**
 * Format currency with Indian Rupee symbol and Indian numbering comma grouping.
 * Example: 2500 -> ₹2,500
 */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return '—';
  return `₹${Number(amount).toLocaleString('en-IN')}`;
}

/**
 * Format date string into "31 Oct 2026" standard format per Stitch design.
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return dateString;
  }
}

/**
 * Maps backend TicketStatus ('open' | 'in_progress' | 'resolved' | 'closed')
 * to Stitch UI badge visual properties (Pending, In Progress, Completed).
 */
export function mapStatusToUi(status: TicketStatus): {
  label: string;
  uiStatus: 'pending' | 'in_progress' | 'completed';
  bgStyle: { backgroundColor: string; color: string };
  dotStyle: { backgroundColor: string };
} {
  switch (status) {
    case 'open':
      return {
        label: 'PENDING',
        uiStatus: 'pending',
        bgStyle: { backgroundColor: '#FEF3C7', color: '#B45309' },
        dotStyle: { backgroundColor: '#D97706' },
      };
    case 'in_progress':
      return {
        label: 'IN PROGRESS',
        uiStatus: 'in_progress',
        bgStyle: { backgroundColor: '#DBEAFE', color: '#1D4ED8' },
        dotStyle: { backgroundColor: '#2563EB' },
      };
    case 'resolved':
    case 'closed':
    default:
      return {
        label: 'COMPLETED',
        uiStatus: 'completed',
        bgStyle: { backgroundColor: '#D1FAE5', color: '#047857' },
        dotStyle: { backgroundColor: '#059669' },
      };
  }
}
