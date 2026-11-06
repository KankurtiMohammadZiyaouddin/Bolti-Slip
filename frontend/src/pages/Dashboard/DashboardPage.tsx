// src/pages/Dashboard/DashboardPage.tsx
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listTickets } from '../../api/client';
import StatusBadge from '../../components/common/StatusBadge';
import { formatDate } from '../../utils/formatters';
import type { Ticket } from '../../types/ticket';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      setError(null);
      try {
        const data = await listTickets();
        setTickets(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'डेटा लोड करने में त्रुटि।');
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  // Compute live statistics from real SQLite database records — strictly no hardcoded stats
  const totalCount = tickets.length;
  const pendingCount = tickets.filter((t) => t.status === 'open').length;
  const inProgressCount = tickets.filter((t) => t.status === 'in_progress').length;
  const completedCount = tickets.filter((t) => t.status === 'resolved' || t.status === 'closed').length;

  const recentTickets = [...tickets]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="flex flex-col w-full">
      {/* Top Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between pb-6 gap-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-headline-lg text-headline-lg text-on-surface font-semibold tracking-tight">
              Dashboard
            </h1>
            <span className="font-label-xs text-label-xs px-2.5 py-1 rounded-full bg-surface-container text-secondary font-medium border border-outline-variant flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
              SQLite Local Database • Live Store Records
            </span>
          </div>
          <p className="font-body-md text-body-md text-secondary">
            Manage your repair shop and track real-time customer service slips.
          </p>
        </div>

        {/* Primary CTA for New Ticket */}
        <button
          onClick={() => navigate('/new-ticket')}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md shadow-sm transition-all active:scale-[0.98] cursor-pointer"
          type="button"
        >
          <span className="material-symbols-outlined text-[20px]">mic</span>
          <span>+ Create New Ticket</span>
        </button>
      </div>

      {error && (
        <div className="p-4 mb-6 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm text-body-sm">
          {error}
        </div>
      )}

      {/* 4 Metrics Stat Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
        {/* Total Tickets */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-5 shadow-sm border border-outline-variant flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[20px]">confirmation_number</span>
            </div>
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider">Total</span>
          </div>
          <div className="mt-4 flex flex-col">
            <span className="font-headline-lg text-headline-lg text-on-surface font-semibold">
              {loading ? '…' : totalCount}
            </span>
            <span className="font-body-md text-body-md text-secondary font-medium">Total Tickets</span>
            <span className="font-label-xs text-label-xs text-secondary mt-1">Recorded in database</span>
          </div>
        </div>

        {/* Pending Tickets */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-5 shadow-sm border border-outline-variant flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#FEF3C7] text-[#B45309]">
              <span className="material-symbols-outlined text-[20px]">hourglass_top</span>
            </div>
            <span className="text-[11px] font-semibold text-[#B45309] bg-[#FEF3C7] px-2 py-0.5 rounded-full">
              Pending
            </span>
          </div>
          <div className="mt-4 flex flex-col">
            <span className="font-headline-lg text-headline-lg text-on-surface font-semibold">
              {loading ? '…' : pendingCount}
            </span>
            <span className="font-body-md text-body-md text-secondary font-medium">Pending Slips</span>
            <span className="font-label-xs text-label-xs text-secondary mt-1">Awaiting diagnosis</span>
          </div>
        </div>

        {/* In Progress Tickets */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-5 shadow-sm border border-outline-variant flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#DBEAFE] text-[#1D4ED8]">
              <span className="material-symbols-outlined text-[20px]">build</span>
            </div>
            <span className="text-[11px] font-semibold text-[#1D4ED8] bg-[#DBEAFE] px-2 py-0.5 rounded-full">
              In Progress
            </span>
          </div>
          <div className="mt-4 flex flex-col">
            <span className="font-headline-lg text-headline-lg text-on-surface font-semibold">
              {loading ? '…' : inProgressCount}
            </span>
            <span className="font-body-md text-body-md text-secondary font-medium">In Progress</span>
            <span className="font-label-xs text-label-xs text-secondary mt-1">On workbench</span>
          </div>
        </div>

        {/* Completed Tickets */}
        <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-5 shadow-sm border border-outline-variant flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#D1FAE5] text-[#047857]">
              <span className="material-symbols-outlined text-[20px]">check_circle</span>
            </div>
            <span className="text-[11px] font-semibold text-[#047857] bg-[#D1FAE5] px-2 py-0.5 rounded-full">
              Ready
            </span>
          </div>
          <div className="mt-4 flex flex-col">
            <span className="font-headline-lg text-headline-lg text-on-surface font-semibold">
              {loading ? '…' : completedCount}
            </span>
            <span className="font-body-md text-body-md text-secondary font-medium">Completed</span>
            <span className="font-label-xs text-label-xs text-secondary mt-1">Ready for pickup / delivered</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Recent Tickets & Workshop Quick Action */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Recent Tickets Table Container (8 Cols on Desktop) */}
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-2xl p-5 md:p-6 shadow-sm border border-outline-variant flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                Recent Tickets
              </h2>
              <span className="font-label-xs text-label-xs px-2.5 py-0.5 rounded-full bg-surface-container text-secondary font-medium">
                {recentTickets.length} entries
              </span>
            </div>
            <Link
              to="/tickets"
              className="font-label-md text-label-md text-primary hover:text-primary-container transition-colors flex items-center gap-1 font-medium"
            >
              <span>View all</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-secondary font-body-md">लोड हो रहा है…</div>
          ) : recentTickets.length === 0 ? (
            <div className="py-12 text-center text-secondary flex flex-col items-center justify-center gap-3">
              <span className="material-symbols-outlined text-[36px] text-secondary">inbox</span>
              <p className="font-body-md text-on-surface font-medium">No tickets created yet.</p>
              <p className="font-body-sm text-secondary">
                Tap "Create New Ticket" to record your first voice repair slip.
              </p>
            </div>
          ) : (
            <>
              {/* Mobile Card List (Visible on mobile screens) */}
              <div className="md:hidden flex flex-col gap-3">
                {recentTickets.map((ticket) => (
                  <Link
                    key={ticket.id}
                    to={`/tickets/${ticket.id}`}
                    className="bg-surface-container-low/60 rounded-xl p-3.5 border border-outline-variant/60 flex flex-col gap-2 hover:bg-surface-container-low transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-label-md text-label-md text-primary font-bold font-mono">
                            {ticket.ticket_number}
                          </span>
                          <span className="text-secondary text-[11px]">•</span>
                          <span className="font-body-md text-body-md text-on-surface truncate font-semibold">
                            {ticket.customer_name || 'Walk-in Customer'}
                          </span>
                        </div>
                        <span className="font-body-sm text-body-sm text-secondary truncate mt-0.5">
                          {ticket.device_description}
                        </span>
                      </div>
                      <StatusBadge status={ticket.status} />
                    </div>
                    {ticket.reported_problem && (
                      <div className="text-secondary text-[12px] bg-surface-container-lowest rounded-lg px-2.5 py-1 truncate">
                        "{ticket.reported_problem}"
                      </div>
                    )}
                    <div className="flex justify-between items-center text-[11px] text-secondary">
                      <span>{formatDate(ticket.created_at)}</span>
                      <span className="text-primary font-semibold">View Slip →</span>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Desktop Table View (Hidden on mobile) */}
              <div className="hidden md:block w-full overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-surface-container-low text-secondary font-label-xs text-label-xs uppercase tracking-wider">
                      <th className="py-3 px-4 rounded-l-lg font-semibold" scope="col">Ticket ID</th>
                      <th className="py-3 px-4 font-semibold" scope="col">Customer</th>
                      <th className="py-3 px-4 font-semibold" scope="col">Device</th>
                      <th className="py-3 px-4 font-semibold" scope="col">Date</th>
                      <th className="py-3 px-4 font-semibold" scope="col">Status</th>
                      <th className="py-3 px-4 rounded-r-lg font-semibold text-right" scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody className="font-body-md text-body-md text-on-surface divide-y divide-outline-variant/50">
                    {recentTickets.map((ticket) => (
                      <tr key={ticket.id} className="hover:bg-surface-container-low transition-colors group">
                        <td className="py-3.5 px-4 font-label-md text-label-md text-primary font-semibold font-mono">
                          {ticket.ticket_number}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-on-surface">
                          {ticket.customer_name || '—'}
                        </td>
                        <td className="py-3.5 px-4 text-on-surface-variant font-body-sm text-body-sm">
                          {ticket.device_description}
                        </td>
                        <td className="py-3.5 px-4 text-secondary font-body-sm text-body-sm">
                          {formatDate(ticket.created_at)}
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge status={ticket.status} />
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <Link
                            to={`/tickets/${ticket.id}`}
                            className="font-label-sm text-label-sm text-primary hover:text-primary-container font-medium px-2.5 py-1 rounded hover:bg-surface-container transition-colors inline-block"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Workshop Quick Action / Right Rail (4 Cols on Desktop) */}
        <div className="lg:col-span-4 flex flex-col gap-6 w-full">
          {/* Quick Voice Entry Card */}
          <div className="bg-surface-container-lowest rounded-2xl p-6 shadow-sm border border-outline-variant flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                Quick Action
              </span>
              <span className="font-label-xs text-label-xs px-2 py-0.5 rounded-full bg-secondary-container text-primary font-semibold">
                Gnani Prisma v3.0
              </span>
            </div>

            <div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-1">
                New Repair Entry
              </h3>
              <p className="font-body-sm text-body-sm text-secondary">
                Voice-driven intake in Hindi, English or Hinglish. Automatically extracts device &amp; issue.
              </p>
            </div>

            <button
              onClick={() => navigate('/new-ticket')}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary-container text-on-primary font-label-md text-label-md hover:bg-primary transition-all shadow-sm active:scale-[0.99] cursor-pointer"
              type="button"
            >
              <span className="material-symbols-outlined text-[20px]">mic</span>
              <span>Create New Ticket</span>
            </button>

            <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[18px] shrink-0">verified</span>
                <span className="font-label-xs text-label-xs text-on-surface font-semibold">
                  Workshop Philosophy
                </span>
              </div>
              <p className="font-label-xs text-label-xs text-secondary leading-relaxed">
                “जो बोला, वही लिखा। जो लिखा, वही कन्फर्म।” Instant acoustic STT transcription &amp; spoken confirmations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
