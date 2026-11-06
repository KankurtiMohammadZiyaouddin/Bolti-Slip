// src/pages/TicketListPage.tsx
import { useState, useEffect } from 'react';
import { listTickets } from '../api/client';
import TicketCard from '../components/TicketCard';
import type { Ticket, TicketStatus } from '../types/ticket';

export default function TicketListPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [statusFilter, setStatusFilter] = useState<TicketStatus | undefined>(undefined);
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

  const filterButtons: { label: string; value?: TicketStatus }[] = [
    { label: 'सभी (All)', value: undefined },
    { label: 'लंबित (Pending)', value: 'open' },
    { label: 'प्रगति पर (In Progress)', value: 'in_progress' },
    { label: 'पूर्ण (Completed)', value: 'resolved' },
    { label: 'बंद (Closed)', value: 'closed' },
  ];

  return (
    <div style={{ maxWidth: '850px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', color: 'var(--color-primary)' }}>📋 सभी रिपेयर पर्चियां</h1>
          <p style={{ color: 'var(--color-muted)', fontSize: '.9rem' }}>
            कुल {tickets.length} पर्चियां उपलब्ध हैं
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchTickets} disabled={loading}>
          🔄 रिफ्रेश करें
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {filterButtons.map((btn) => {
          const isActive = statusFilter === btn.value;
          return (
            <button
              key={btn.label}
              onClick={() => setStatusFilter(btn.value)}
              className={isActive ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '.45rem .9rem', fontSize: '.88rem' }}
            >
              {btn.label}
            </button>
          );
        })}
      </div>

      {error && (
        <div style={{ color: 'var(--color-danger)', background: '#ffebee', padding: '.75rem', borderRadius: 'var(--radius)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--color-muted)' }}>
          लोड हो रहा है…
        </div>
      ) : tickets.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-muted)' }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>कोई पर्ची नहीं मिली।</p>
        </div>
      ) : (
        <div>
          {tickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}
    </div>
  );
}
