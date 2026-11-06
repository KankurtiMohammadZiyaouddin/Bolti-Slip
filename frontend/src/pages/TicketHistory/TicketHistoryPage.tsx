// src/pages/TicketHistory/TicketHistoryPage.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listTickets } from '../../api/client';
import StatusBadge from '../../components/common/StatusBadge';
import { formatDate } from '../../utils/formatters';
import type { Ticket, TicketStatus } from '../../types/ticket';

export default function TicketHistoryPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [statusFilter, setStatusFilter] = useState<TicketStatus | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchTickets() {
    setLoading(true);
    setError(null);
    try {
      const data = await listTickets(statusFilter);
      setTickets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'पर्चियां लोड करने में त्रुटि।');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchTickets();
  }, [statusFilter]);

  // Client-side text search by ID, customer name, device or phone
  const filteredTickets = tickets.filter((t) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.ticket_number.toLowerCase().includes(q) ||
      (t.customer_name && t.customer_name.toLowerCase().includes(q)) ||
      t.device_description.toLowerCase().includes(q) ||
      (t.customer_phone && t.customer_phone.includes(q)) ||
      (t.reported_problem && t.reported_problem.toLowerCase().includes(q))
    );
  });

  const filterTabs: { label: string; value?: TicketStatus }[] = [
    { label: 'All', value: undefined },
    { label: 'Pending', value: 'open' },
    { label: 'In Progress', value: 'in_progress' },
    { label: 'Completed', value: 'resolved' },
  ];

  return (
    <div className="flex flex-col w-full">
      {/* Top Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md mb-6">
        <div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            Ticket History
          </h1>
          <p className="font-body-md text-body-md text-secondary mt-1">
            {tickets.length} repair slips recorded (SQLite Database)
          </p>
        </div>

        <div className="flex items-center gap-space-sm">
          <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container text-secondary text-label-xs font-label-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
            Live records • Bolti Slip
          </span>
          <button
            onClick={fetchTickets}
            className="h-10 px-4 bg-surface-container-lowest hover:bg-surface-container-low text-secondary hover:text-on-surface font-label-md text-label-md rounded-xl shadow-sm border border-outline-variant flex items-center gap-2 transition-colors cursor-pointer"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Search Bar & Filter Tabs */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 mb-6">
        <div className="flex flex-wrap items-center gap-4 flex-1">
          {/* Search Input */}
          <div className="relative flex items-center w-full sm:w-80 md:w-96 shadow-sm rounded-xl">
            <span className="material-symbols-outlined absolute left-3.5 text-secondary text-[20px] pointer-events-none">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Ticket ID, customer name, device or phone..."
              className="w-full h-10 pl-11 pr-space-md bg-surface-container-lowest border border-outline-variant rounded-xl font-body-sm text-body-sm text-on-surface placeholder:text-secondary focus:outline-none focus:ring-2 focus:ring-primary-container transition-all"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 p-1 bg-surface-container rounded-full shadow-inner overflow-x-auto">
            {filterTabs.map((tab) => {
              const isActive = statusFilter === tab.value;
              return (
                <button
                  key={tab.label}
                  onClick={() => setStatusFilter(tab.value)}
                  type="button"
                  className={`px-3.5 py-1.5 rounded-full font-label-sm text-label-sm transition-all cursor-pointer whitespace-nowrap ${
                    isActive
                      ? 'bg-primary-container text-on-primary shadow-sm font-semibold'
                      : 'bg-transparent text-secondary hover:text-on-surface'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-6 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm text-body-sm">
          {error}
        </div>
      )}

      {/* Tickets Table / List */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant overflow-hidden flex flex-col">
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse min-w-[760px]">
            <thead>
              <tr className="bg-surface-container-low border-b border-outline-variant">
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                  Ticket ID
                </th>
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                  Customer
                </th>
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                  Device
                </th>
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                  Date
                </th>
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                  Status
                </th>
                <th className="py-3.5 px-6 font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold text-right">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="font-body-md text-body-md text-on-surface divide-y divide-outline-variant">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-secondary">
                    लोड हो रहा है…
                  </td>
                </tr>
              ) : filteredTickets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-secondary">
                    कोई पर्ची नहीं मिली (No tickets found).
                  </td>
                </tr>
              ) : (
                filteredTickets.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-surface-container-low transition-colors group">
                    <td className="py-4 px-6 font-label-md text-label-md text-primary font-semibold font-mono">
                      {ticket.ticket_number}
                    </td>
                    <td className="py-4 px-6 font-medium text-on-surface">
                      {ticket.customer_name || '—'}
                      {ticket.customer_phone && (
                        <div className="font-body-sm text-body-sm text-secondary">
                          {ticket.customer_phone}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6 text-on-surface-variant font-body-sm text-body-sm max-w-xs truncate">
                      {ticket.device_description}
                    </td>
                    <td className="py-4 px-6 text-secondary font-body-sm text-body-sm">
                      {formatDate(ticket.created_at)}
                    </td>
                    <td className="py-4 px-6">
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="py-4 px-6 text-right">
                      <Link
                        to={`/tickets/${ticket.id}`}
                        className="font-label-sm text-label-sm text-primary hover:text-primary-container font-semibold px-3 py-1.5 rounded-lg hover:bg-surface-container transition-colors inline-block"
                      >
                        View Slip →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
