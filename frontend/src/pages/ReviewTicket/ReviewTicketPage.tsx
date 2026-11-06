// src/pages/ReviewTicket/ReviewTicketPage.tsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTicket, updateTicketStatus, confirmTicket } from '../../api/client';
import StatusBadge from '../../components/common/StatusBadge';
import AudioPlayer from '../../components/AudioPlayer';
import { formatCurrency, formatDate } from '../../utils/formatters';
import type { Ticket, TicketStatus } from '../../types/ticket';

export default function ReviewTicketPage() {
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
      <div className="py-16 text-center text-secondary font-body-md">
        लोड हो रहा है… (Loading ticket details)
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-xl mx-auto py-12 px-4 text-center">
        <div className="bg-surface-container-lowest rounded-2xl p-8 border border-outline-variant shadow-sm flex flex-col items-center">
          <span className="material-symbols-outlined text-[36px] text-error mb-2">error</span>
          <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
            त्रुटि (Error)
          </h2>
          <p className="text-secondary font-body-md mb-6">{error || 'पर्ची नहीं मिली।'}</p>
          <Link
            to="/tickets"
            className="px-5 py-2.5 rounded-xl bg-primary-container text-on-primary font-label-md"
          >
            ← वापस सूची में जाएं
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between pb-4">
        <Link
          to="/tickets"
          className="inline-flex items-center gap-1.5 text-secondary hover:text-primary font-label-sm text-label-sm font-medium transition-colors"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          <span>Back to Ticket History</span>
        </Link>
        <span className="font-mono font-bold text-primary bg-secondary-container px-3 py-1 rounded-lg text-[13px]">
          {ticket.ticket_number}
        </span>
      </div>

      {/* Title & Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 gap-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-headline-lg text-headline-lg text-on-surface font-semibold tracking-tight">
              Review Repair Ticket
            </h1>
            <StatusBadge status={ticket.status} />
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-primary font-label-xs text-label-xs font-semibold">
              <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
              Gnani Prisma &amp; Timbre
            </span>
          </div>
          <p className="font-body-md text-body-md text-secondary">
            Created on {formatDate(ticket.created_at)}
          </p>
        </div>

        {/* Spoken Confirmation Action */}
        <button
          onClick={handlePlayConfirmation}
          disabled={loadingAudio}
          type="button"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md shadow-sm transition-all cursor-pointer"
        >
          <span className="material-symbols-outlined text-[20px]">volume_up</span>
          <span>{loadingAudio ? 'ऑडियो तैयार हो रहा है…' : '🔊 बोलती पुष्टि सुनें (Timbre TTS)'}</span>
        </button>
      </div>

      {audioError && (
        <div className="p-3 mb-4 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm">
          {audioError}
        </div>
      )}

      {audioUrl && (
        <div className="p-4 mb-6 rounded-2xl bg-surface-container-low border border-outline-variant shadow-sm max-w-xl">
          <AudioPlayer url={audioUrl} label="🔊 बोलती पुष्टि (Timbre TTS Spoken Confirmation):" />
        </div>
      )}

      {/* Main Review Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (8 Cols on Desktop): Structured Fields */}
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-6 flex flex-col gap-6">
          {/* Section 1: Customer Information */}
          <div className="flex flex-col gap-4 border-b border-outline-variant/60 pb-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">person</span>
              <h2 className="font-headline-sm text-[16px] font-semibold text-on-surface">
                Customer Information
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Customer Name
                </span>
                <p className="font-headline-sm text-[15px] font-semibold text-on-surface mt-1">
                  {ticket.customer_name || '—'}
                </p>
              </div>
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Phone Number
                </span>
                <p className="font-headline-sm text-[15px] font-semibold text-on-surface mt-1">
                  {ticket.customer_phone || '— (Not stated in audio)'}
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Device Information */}
          <div className="flex flex-col gap-4 border-b border-outline-variant/60 pb-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">devices</span>
              <h2 className="font-headline-sm text-[16px] font-semibold text-on-surface">
                Device Information
              </h2>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Device Description
                </span>
                <p className="font-headline-sm text-[15px] font-semibold text-on-surface mt-1">
                  {ticket.device_description}
                </p>
              </div>
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Reported Problem
                </span>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1 p-3 rounded-lg bg-surface-container-low border border-outline-variant/60">
                  {ticket.reported_problem || '—'}
                </p>
              </div>
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Repair Instructions
                </span>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                  {ticket.repair_instructions || '— (No explicit technician notes)'}
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Service Details */}
          <div className="flex flex-col gap-4 border-b border-outline-variant/60 pb-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">event_available</span>
              <h2 className="font-headline-sm text-[16px] font-semibold text-on-surface">
                Service Details
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Expected Delivery Date
                </span>
                <p className="font-headline-sm text-[15px] font-semibold text-on-surface mt-1">
                  {formatDate(ticket.expected_delivery)}
                </p>
              </div>
              <div>
                <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary">
                  Estimated Cost
                </span>
                <p className="font-headline-sm text-[16px] font-bold text-emerald-700 mt-1">
                  {formatCurrency(ticket.estimated_cost)}
                </p>
              </div>
            </div>
          </div>

          {/* Section 4: Status Workflow Changer */}
          <div className="flex flex-col gap-3">
            <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary font-semibold">
              Update Ticket Status
            </span>
            <div className="flex flex-wrap gap-2">
              {(['open', 'in_progress', 'resolved', 'closed'] as TicketStatus[]).map((s) => {
                const isActive = ticket.status === s;
                return (
                  <button
                    key={s}
                    disabled={updating || isActive}
                    onClick={() => handleStatusChange(s)}
                    className={`px-4 py-2 rounded-xl text-label-sm font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-primary-container text-on-primary shadow-sm'
                        : 'border border-outline-variant hover:bg-surface-container-low text-secondary hover:text-on-surface'
                    }`}
                    type="button"
                  >
                    {s === 'open' && 'Pending (लंबित)'}
                    {s === 'in_progress' && 'In Progress (प्रगति पर)'}
                    {s === 'resolved' && 'Resolved (पूर्ण)'}
                    {s === 'closed' && 'Closed (बंद)'}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (4 Cols on Desktop): Original Audio & Summary */}
        <div className="lg:col-span-4 flex flex-col gap-6 w-full">
          {/* Transcript Box */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-5">
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60 mb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">graphic_eq</span>
                <h3 className="font-headline-sm text-[15px] font-semibold text-on-surface">
                  Original Voice Transcript
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-secondary-container text-primary font-label-xs text-label-xs font-semibold">
                Prisma v3.0
              </span>
            </div>
            <div className="text-body-sm text-body-sm text-on-surface leading-relaxed p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/40 italic">
              {ticket.transcript_raw ? `“${ticket.transcript_raw}”` : 'No raw audio transcript recorded.'}
            </div>
          </div>

          {/* Ticket Summary Card */}
          <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-5">
            <div className="flex items-center gap-2 mb-3 pb-3 border-b border-outline-variant/60">
              <span className="material-symbols-outlined text-primary text-[20px]">receipt_long</span>
              <h3 className="font-headline-sm text-[15px] font-semibold text-on-surface">
                Slip Summary
              </h3>
            </div>
            <div className="text-body-sm text-on-surface flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-secondary">Ticket:</span>
                <span className="font-mono font-semibold text-primary">{ticket.ticket_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Customer:</span>
                <span className="font-medium">{ticket.customer_name || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Device:</span>
                <span className="font-medium truncate max-w-[150px]">{ticket.device_description}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Delivery:</span>
                <span className="font-medium">{formatDate(ticket.expected_delivery)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Cost:</span>
                <span className="font-bold text-emerald-700">{formatCurrency(ticket.estimated_cost)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
