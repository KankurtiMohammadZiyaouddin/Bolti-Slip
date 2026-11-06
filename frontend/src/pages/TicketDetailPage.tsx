// src/pages/TicketDetailPage.tsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTicket, updateTicketStatus, confirmTicket } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AudioPlayer from '../components/AudioPlayer';
import type { Ticket, TicketStatus } from '../types/ticket';

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [updating, setUpdating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getTicket(Number(id));
        setTicket(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'पर्ची लोड नहीं हो सकी।');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  async function handleStatusChange(newStatus: TicketStatus) {
    if (!ticket) return;
    setUpdating(true);
    try {
      const updated = await updateTicketStatus(ticket.id, newStatus);
      setTicket(updated);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'स्थिति बदलने में विफल।');
    } finally {
      setUpdating(false);
    }
  }

  async function handlePlayConfirmation() {
    if (!ticket) return;
    setLoadingAudio(true);
    setAudioError(null);
    try {
      const blob = await confirmTicket(ticket.id);
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      setAudioError(err instanceof Error ? err.message : 'ऑडियो लोड करने में विफल।');
    } finally {
      setLoadingAudio(false);
    }
  }

  if (loading) {
    return (
      <div style={{ maxWidth: '750px', margin: '2rem auto', textAlign: 'center', color: 'var(--color-muted)' }}>
        लोड हो रहा है…
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div style={{ maxWidth: '750px', margin: '2rem auto', padding: '1rem' }}>
        <div className="card" style={{ textAlign: 'center', color: 'var(--color-danger)' }}>
          <h3>त्रुटि</h3>
          <p>{error ?? 'पर्ची नहीं मिली।'}</p>
          <Link to="/tickets">
            <button className="btn-secondary" style={{ marginTop: '1rem' }}>
              ← वापस सूची में जाएं
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '750px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/tickets" style={{ fontSize: '.9rem', color: 'var(--color-primary)' }}>
          ← सभी पर्चियां (Back to tickets)
        </Link>
      </div>

      <div className="card">
        {/* Top Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <h1 style={{ fontSize: '1.6rem', color: 'var(--color-primary)' }}>
              पर्ची: #{ticket.ticket_number}
            </h1>
            <p style={{ color: 'var(--color-muted)', fontSize: '.85rem' }}>
              दर्ज: {new Date(ticket.created_at).toLocaleString('hi-IN')}
            </p>
          </div>
          <StatusBadge status={ticket.status} />
        </div>

        {/* Status Change Bar */}
        <div style={{ background: '#f8f9fa', padding: '.75rem 1rem', borderRadius: 'var(--radius)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '.75rem' }}>
          <span style={{ fontSize: '.9rem', fontWeight: 600 }}>स्थिति बदलें (Update Status):</span>
          <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
            <button
              disabled={updating || ticket.status === 'open'}
              onClick={() => handleStatusChange('open')}
              className={ticket.status === 'open' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '.35rem .75rem', fontSize: '.82rem' }}
            >
              लंबित (Pending)
            </button>
            <button
              disabled={updating || ticket.status === 'in_progress'}
              onClick={() => handleStatusChange('in_progress')}
              className={ticket.status === 'in_progress' ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '.35rem .75rem', fontSize: '.82rem' }}
            >
              प्रगति पर (In Progress)
            </button>
            <button
              disabled={updating || ticket.status === 'resolved'}
              onClick={() => handleStatusChange('resolved')}
              className={ticket.status === 'resolved' ? 'btn-success' : 'btn-secondary'}
              style={{ padding: '.35rem .75rem', fontSize: '.82rem' }}
            >
              पूर्ण (Completed)
            </button>
            <button
              disabled={updating || ticket.status === 'closed'}
              onClick={() => handleStatusChange('closed')}
              className={ticket.status === 'closed' ? 'btn-danger' : 'btn-secondary'}
              style={{ padding: '.35rem .75rem', fontSize: '.82rem' }}
            >
              बंद (Closed)
            </button>
          </div>
        </div>

        {/* Ticket Details Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>उपकरण (Device):</strong>
            <p style={{ fontSize: '1.05rem', marginTop: '.25rem' }}>{ticket.device_description}</p>
          </div>

          {ticket.reported_problem && (
            <div>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>समस्या (Problem):</strong>
              <p style={{ fontSize: '1rem', marginTop: '.25rem' }}>{ticket.reported_problem}</p>
            </div>
          )}

          {ticket.repair_instructions && (
            <div>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>रिपेयर निर्देश (Repair Instructions):</strong>
              <p style={{ fontSize: '1rem', marginTop: '.25rem' }}>{ticket.repair_instructions}</p>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
            <div>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>ग्राहक (Customer):</strong>
              <p style={{ fontSize: '.95rem', marginTop: '.25rem' }}>
                {ticket.customer_name || 'उपलब्ध नहीं'} {ticket.customer_phone ? `(${ticket.customer_phone})` : ''}
              </p>
            </div>

            <div>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>अनुमानित लागत (Estimated Cost):</strong>
              <p style={{ fontSize: '.95rem', marginTop: '.25rem' }}>
                {ticket.estimated_cost != null ? `₹${ticket.estimated_cost}` : 'तय नहीं'}
              </p>
            </div>

            <div>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>अपेक्षित डिलीवरी (Expected Delivery):</strong>
              <p style={{ fontSize: '.95rem', marginTop: '.25rem' }}>
                {ticket.expected_delivery || 'तय नहीं'}
              </p>
            </div>
          </div>

          {ticket.transcript_raw && (
            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
              <strong style={{ display: 'block', fontSize: '.85rem', color: 'var(--color-muted)' }}>मूल आवाज़ ट्रांसक्रिप्ट (Raw Transcript):</strong>
              <p style={{ fontSize: '.9rem', fontStyle: 'italic', background: '#f5f5f5', padding: '.5rem .75rem', borderRadius: 'var(--radius)', marginTop: '.25rem' }}>
                "{ticket.transcript_raw}"
              </p>
            </div>
          )}
        </div>

        {/* Spoken Confirmation / TTS Section */}
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1.25rem', marginTop: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '.5rem' }}>🔊 बोलती पुष्टि (Spoken Confirmation)</h3>
          <p style={{ fontSize: '.85rem', color: 'var(--color-muted)', marginBottom: '.75rem' }}>
            Gnani Timbre TTS द्वारा ग्राहक के लिए आवाज़ में पुष्टि तैयार करें और सुनें
          </p>

          <button
            className="btn-primary"
            onClick={handlePlayConfirmation}
            disabled={loadingAudio}
          >
            {loadingAudio ? 'आवाज़ तैयार हो रही है…' : '🔊 पुष्टि सुनें (Listen Confirmation)'}
          </button>

          {audioError && (
            <p style={{ color: 'var(--color-danger)', fontSize: '.85rem', marginTop: '.5rem' }}>{audioError}</p>
          )}

          {audioUrl && (
            <AudioPlayer url={audioUrl} label="ऑडियो प्लेयर:" />
          )}
        </div>
      </div>
    </div>
  );
}
