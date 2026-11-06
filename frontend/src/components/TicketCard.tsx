// src/components/TicketCard.tsx
import { Link } from 'react-router-dom';
import type { Ticket } from '../types/ticket';
import StatusBadge from './StatusBadge';

interface Props {
  ticket: Ticket;
}

export default function TicketCard({ ticket }: Props) {
  const formattedDate = new Date(ticket.created_at).toLocaleDateString('hi-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="card" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--color-primary)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', color: 'var(--color-primary)' }}>
          <Link to={`/tickets/${ticket.id}`} style={{ color: 'inherit' }}>
            #{ticket.ticket_number}
          </Link>
        </h3>
        <StatusBadge status={ticket.status} />
      </div>

      <div style={{ marginBottom: '.5rem', fontSize: '.95rem' }}>
        <strong>उपकरण: </strong> {ticket.device_description}
      </div>

      {ticket.reported_problem && (
        <div style={{ marginBottom: '.5rem', fontSize: '.9rem', color: 'var(--color-text)' }}>
          <strong>समस्या: </strong> {ticket.reported_problem}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '.5rem', fontSize: '.85rem', color: 'var(--color-muted)', marginBottom: '.75rem' }}>
        {ticket.customer_name && (
          <div>
            👤 <strong>ग्राहक:</strong> {ticket.customer_name} {ticket.customer_phone ? `(${ticket.customer_phone})` : ''}
          </div>
        )}
        {ticket.estimated_cost != null && (
          <div>
            💰 <strong>अनुमानित लागत:</strong> ₹{ticket.estimated_cost}
          </div>
        )}
        {ticket.expected_delivery && (
          <div>
            📅 <strong>अपेक्षित तारीख:</strong> {ticket.expected_delivery}
          </div>
        )}
        <div>
          🕒 <strong>दिनांक:</strong> {formattedDate}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '.5rem' }}>
        <Link to={`/tickets/${ticket.id}`}>
          <button className="btn-secondary" style={{ padding: '.4rem .8rem', fontSize: '.85rem' }}>
            विवरण देखें →
          </button>
        </Link>
      </div>
    </div>
  );
}
