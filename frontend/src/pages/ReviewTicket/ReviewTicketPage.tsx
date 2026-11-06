// src/pages/ReviewTicket/ReviewTicketPage.tsx
// Displays and reviews repair ticket details. Supports both:
// 1. Existing saved tickets via route `/tickets/:id`
// 2. Draft reviews from voice extraction before saving via route `/review-ticket`

import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { getTicket, createTicket, updateTicketStatus, confirmTicket } from '../../api/client';
import StatusBadge from '../../components/common/StatusBadge';
import AudioPlayer from '../../components/AudioPlayer';
import { formatCurrency, formatDate } from '../../utils/formatters';
import type { Ticket, TicketCreate, TicketStatus, ExtractionResult } from '../../types/ticket';

export default function ReviewTicketPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  // Location state can pass draft extraction from NewTicketPage
  const stateExtraction = (location.state as { extraction?: ExtractionResult; transcript?: string } | null);

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [error, setError] = useState<string | null>(null);

  // Form fields for editing/saving
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [deviceDescription, setDeviceDescription] = useState('');
  const [reportedProblem, setReportedProblem] = useState('');
  const [repairInstructions, setRepairInstructions] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');
  const [rawTranscript, setRawTranscript] = useState('');

  const [needsConfirmation, setNeedsConfirmation] = useState<string[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);

  const [saving, setSaving] = useState(false);
  const [savedTicket, setSavedTicket] = useState<Ticket | null>(null);

  // Status & Audio playback
  const [updating, setUpdating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  // 1. If ID is provided, load existing saved ticket from backend
  useEffect(() => {
    if (!id) return;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getTicket(Number(id));
        setTicket(data);
        setCustomerName(data.customer_name || '');
        setCustomerPhone(data.customer_phone || '');
        setDeviceDescription(data.device_description || '');
        setReportedProblem(data.reported_problem || '');
        setRepairInstructions(data.repair_instructions || '');
        setExpectedDelivery(data.expected_delivery || '');
        setEstimatedCost(data.estimated_cost ? String(data.estimated_cost) : '');
        setRawTranscript(data.transcript_raw || '');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'पर्ची लोड नहीं हो सकी।');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  // 2. If no ID but draft extraction passed from New Ticket, populate draft
  useEffect(() => {
    if (id) return; // not a draft
    if (stateExtraction?.extraction?.fields) {
      const f = stateExtraction.extraction.fields;
      setCustomerName(f.customer_name || '');
      setCustomerPhone(f.customer_phone || '');
      setDeviceDescription(f.device_description || '');
      setReportedProblem(f.reported_problem || '');
      setRepairInstructions(f.repair_instructions || '');
      setExpectedDelivery(f.expected_delivery || '');
      setEstimatedCost(f.estimated_cost != null ? String(f.estimated_cost) : '');
      setRawTranscript(f.transcript_raw || stateExtraction.transcript || '');
      setNeedsConfirmation(stateExtraction.extraction.needs_confirmation || []);
      setMissingFields(stateExtraction.extraction.missing_fields || []);
    }
  }, [id, stateExtraction]);

  // Handle Saving New Ticket
  async function handleConfirmAndSave() {
    if (!deviceDescription.trim()) {
      alert('उपकरण का विवरण आवश्यक है (Device description is required).');
      return;
    }

    setSaving(true);
    setError(null);

    const payload: TicketCreate = {
      device_description: deviceDescription.trim(),
      customer_name: customerName.trim() || undefined,
      customer_phone: customerPhone.trim() || undefined,
      reported_problem: reportedProblem.trim() || undefined,
      repair_instructions: repairInstructions.trim() || undefined,
      expected_delivery: expectedDelivery.trim() || undefined,
      estimated_cost: estimatedCost ? parseFloat(estimatedCost) : undefined,
      transcript_raw: rawTranscript || undefined,
    };

    try {
      const created = await createTicket(payload);
      setSavedTicket(created);
      setTicket(created);

      // Auto-fetch spoken confirmation from Timbre TTS
      try {
        setLoadingAudio(true);
        const blob = await confirmTicket(created.id);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
      } catch (audioErr) {
        // Audio failure does NOT lose the saved ticket
        console.warn('Audio confirmation failed:', audioErr);
        setAudioError('आवाज़ पुष्टि लोड करने में असमर्थ। पर्ची सुरक्षित है।');
      } finally {
        setLoadingAudio(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'पर्ची सुरक्षित करने में विफल।');
    } finally {
      setSaving(false);
    }
  }

  // Handle Status Update on Saved Ticket
  async function handleStatusChange(newStatus: TicketStatus) {
    const targetId = ticket?.id || savedTicket?.id;
    if (!targetId) return;
    setUpdating(true);
    try {
      const updated = await updateTicketStatus(targetId, newStatus);
      setTicket(updated);
      if (savedTicket) setSavedTicket(updated);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'स्थिति बदलने में विफल।');
    } finally {
      setUpdating(false);
    }
  }

  async function handlePlayConfirmation() {
    const targetId = ticket?.id || savedTicket?.id;
    if (!targetId) return;
    setLoadingAudio(true);
    setAudioError(null);
    try {
      const blob = await confirmTicket(targetId);
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

  if (error && !ticket && !stateExtraction) {
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

  const isSaved = Boolean(ticket || savedTicket);
  const activeTicket = ticket || savedTicket;

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
          {activeTicket ? activeTicket.ticket_number : 'Draft Slip'}
        </span>
      </div>

      {/* Title & Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 gap-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-headline-lg text-headline-lg text-on-surface font-semibold tracking-tight">
              {isSaved ? 'Review Repair Ticket' : 'Review & Confirm Repair Ticket'}
            </h1>
            {isSaved && activeTicket ? (
              <StatusBadge status={activeTicket.status} />
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FEF3C7] text-[#B45309] font-label-xs text-label-xs font-semibold uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D97706]" />
                Draft - Pending Confirmation
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container text-primary font-label-xs text-label-xs font-semibold">
              <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
              AI-extracted from Audio
            </span>
          </div>
          <p className="font-body-md text-body-md text-secondary">
            {isSaved && activeTicket
              ? `Created on ${formatDate(activeTicket.created_at)}`
              : 'Verify the extracted information before saving to the database.'}
          </p>
        </div>

        {/* Action: Play spoken confirmation if ticket exists */}
        {isSaved && (
          <button
            onClick={handlePlayConfirmation}
            disabled={loadingAudio}
            type="button"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md shadow-sm transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-[20px]">volume_up</span>
            <span>{loadingAudio ? 'ऑडियो तैयार हो रहा है…' : '🔊 बोलती पुष्टि सुनें (Timbre TTS)'}</span>
          </button>
        )}
      </div>

      {/* Success Notification after Saving */}
      {savedTicket && (
        <div className="p-5 mb-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-emerald-600 text-[28px]">verified</span>
            <div>
              <h3 className="font-headline-sm text-[16px] font-bold">
                🎉 पर्ची सफलतापूर्वक बनाई गई! (Ticket Saved)
              </h3>
              <p className="font-body-sm text-body-sm text-emerald-800">
                पर्ची क्रमांक: <strong className="font-mono">{savedTicket.ticket_number}</strong>. डाटाबेस में सुरक्षित।
              </p>
            </div>
          </div>
          <Link
            to="/tickets"
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-label-sm text-label-sm text-center font-semibold"
          >
            View in History →
          </Link>
        </div>
      )}

      {/* Missing Information Notice Banner (Stitch 04-review-ticket reference) */}
      {!isSaved && missingFields.includes('customer_phone') && (
        <div className="border rounded-xl p-4 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs bg-surface-container-low border-outline-variant/60">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-secondary-container flex items-center justify-center shrink-0 text-primary">
              <span className="material-symbols-outlined text-[20px]">info</span>
            </div>
            <div className="flex flex-col">
              <span className="font-label-md text-label-md text-on-surface font-semibold">
                Notice: Phone number was not mentioned in audio
              </span>
              <span className="font-body-sm text-body-sm text-secondary">
                Optional field. You can add it now for customer SMS/WhatsApp updates or proceed without it.
              </span>
            </div>
          </div>
          <span className="font-label-xs text-label-xs text-secondary bg-surface-container px-3 py-1 rounded-lg shrink-0">
            Optional Field
          </span>
        </div>
      )}

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
        {/* Left Column: Form & Details (8 cols) */}
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
              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Customer Name</span>
                  {customerName && (
                    <span className="text-[11px] font-normal text-[#059669] flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">check_circle</span>
                      Extracted
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="उदा. रमेश कुमार"
                  disabled={isSaved}
                  className="w-full h-10 px-3.5 bg-surface-container-lowest text-on-surface font-body-md text-body-md rounded-lg border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container disabled:bg-surface-container-low"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Phone Number</span>
                  <span className="font-label-xs text-label-xs text-secondary bg-surface-container px-2 py-0.5 rounded font-normal normal-case">
                    {customerPhone ? 'Captured' : 'Optional — not captured in audio'}
                  </span>
                </label>
                <div className="relative flex items-center">
                  <span className="material-symbols-outlined absolute left-3 text-[#D97706] text-[18px]">
                    call
                  </span>
                  <input
                    type="tel"
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="Enter 10-digit mobile number (optional)"
                    disabled={isSaved}
                    className="w-full h-10 pl-9 pr-3.5 bg-surface-container-lowest border border-outline-variant text-on-surface placeholder:text-secondary font-body-md text-body-md rounded-lg focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container disabled:bg-surface-container-low"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Device Information */}
          <div className="flex flex-col gap-4 border-b border-outline-variant/60 pb-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">tv</span>
              <h2 className="font-headline-sm text-[16px] font-semibold text-on-surface">
                Device Information
              </h2>
            </div>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Device Description *</span>
                  {deviceDescription && (
                    <span className="text-[11px] font-normal text-[#059669] flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">check_circle</span>
                      Extracted
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={deviceDescription}
                  onChange={(e) => setDeviceDescription(e.target.value)}
                  placeholder="उदा. Samsung 43 LED TV"
                  required
                  disabled={isSaved}
                  className="w-full h-10 px-3.5 bg-surface-container-lowest text-on-surface font-body-md text-body-md rounded-lg border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container disabled:bg-surface-container-low"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Reported Problem</span>
                  {reportedProblem && (
                    <span className="text-[11px] font-normal text-[#059669] flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">check_circle</span>
                      Extracted
                    </span>
                  )}
                </label>
                <textarea
                  rows={2}
                  value={reportedProblem}
                  onChange={(e) => setReportedProblem(e.target.value)}
                  placeholder="उदा. स्क्रीन चालू नहीं हो रही है"
                  disabled={isSaved}
                  className="w-full p-3 bg-surface-container-lowest text-on-surface font-body-md text-body-md rounded-lg border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container resize-none disabled:bg-surface-container-low"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Repair Instructions</span>
                  <span className="font-label-xs text-label-xs text-secondary bg-surface-container px-2 py-0.5 rounded font-normal normal-case">
                    Optional technician notes
                  </span>
                </label>
                <textarea
                  rows={2}
                  value={repairInstructions}
                  onChange={(e) => setRepairInstructions(e.target.value)}
                  placeholder="उदा. पैनल या कैपेसिटर जांचें (optional)"
                  disabled={isSaved}
                  className="w-full p-3 bg-surface-container-lowest text-on-surface font-body-md text-body-md rounded-lg border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container resize-none disabled:bg-surface-container-low"
                />
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
              <div className="flex flex-col gap-1.5">
                <label
                  className={`font-label-sm text-label-sm uppercase tracking-wider flex items-center justify-between font-semibold ${
                    needsConfirmation.includes('expected_delivery') ? 'text-[#B45309]' : 'text-secondary'
                  }`}
                >
                  <span>Expected Delivery</span>
                  {needsConfirmation.includes('expected_delivery') && (
                    <span className="font-label-xs text-label-xs text-[#B45309] bg-[#FEF3C7] px-2 py-0.5 rounded font-semibold uppercase">
                      Action: Confirm Date
                    </span>
                  )}
                </label>
                <div className="relative flex items-center">
                  <input
                    type="date"
                    value={expectedDelivery}
                    onChange={(e) => setExpectedDelivery(e.target.value)}
                    disabled={isSaved}
                    className={`w-full h-10 px-3.5 font-body-md text-body-md rounded-lg border focus:outline-none disabled:bg-surface-container-low ${
                      needsConfirmation.includes('expected_delivery')
                        ? 'bg-[#FFFBEB] text-[#92400E] border-2 border-[#F59E0B]'
                        : 'bg-surface-container-lowest text-on-surface border-outline-variant'
                    }`}
                  />
                </div>
                {needsConfirmation.includes('expected_delivery') && (
                  <p className="font-label-xs text-label-xs text-[#B45309] flex items-center gap-1 mt-0.5 font-medium">
                    <span className="material-symbols-outlined text-[14px]">warning</span>
                    Ambiguous relative date in audio. Please verify or select exact delivery date.
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-sm text-label-sm uppercase tracking-wider text-secondary flex items-center justify-between">
                  <span>Estimated Cost</span>
                  {estimatedCost && (
                    <span className="text-[11px] font-normal text-[#059669] flex items-center gap-1 font-sans">
                      <span className="material-symbols-outlined text-[12px]">check_circle</span>
                      Extracted
                    </span>
                  )}
                </label>
                <div className="relative flex items-center">
                  <input
                    type="number"
                    step="any"
                    min="0"
                    placeholder="उदा. 2500"
                    value={estimatedCost}
                    onChange={(e) => setEstimatedCost(e.target.value)}
                    disabled={isSaved}
                    className="w-full h-10 px-3.5 bg-surface-container-lowest text-on-surface font-body-md text-body-md rounded-lg border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container font-semibold disabled:bg-surface-container-low"
                  />
                </div>
                <p className="font-label-xs text-label-xs text-secondary mt-0.5">
                  Approximate amount stated in voice recording.
                </p>
              </div>
            </div>
          </div>

          {/* Action Row */}
          {!isSaved ? (
            <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center pt-2 gap-3">
              <button
                type="button"
                onClick={() => navigate('/new-ticket')}
                className="px-4 py-2.5 rounded-lg border border-outline-variant bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                <span>Back to Recording</span>
              </button>

              <button
                type="button"
                onClick={handleConfirmAndSave}
                disabled={saving}
                className="px-6 py-2.5 rounded-lg bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md flex items-center justify-center gap-2 transition-colors shadow-md cursor-pointer font-medium disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[18px]">check_circle</span>
                <span>{saving ? 'सुरक्षित हो रहा है…' : 'Confirm and Save Ticket'}</span>
              </button>
            </div>
          ) : (
            /* Status Workflow Update for Saved Ticket */
            <div className="flex flex-col gap-3">
              <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary font-semibold">
                Update Ticket Status
              </span>
              <div className="flex flex-wrap gap-2">
                {(['open', 'in_progress', 'resolved', 'closed'] as TicketStatus[]).map((s) => {
                  const isActive = activeTicket?.status === s;
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
          )}
        </div>

        {/* Right Column: Original Transcript & Checklist (4 cols) */}
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
              {rawTranscript ? `“${rawTranscript}”` : 'No raw audio transcript recorded.'}
            </div>

            {/* Checklist */}
            <div className="flex flex-col gap-2 pt-4 mt-3 border-t border-outline-variant/40">
              <span className="font-label-xs text-label-xs uppercase tracking-wider text-secondary font-semibold">
                Extraction Checklist
              </span>
              <div className="flex flex-col gap-1.5 text-[12px]">
                <div className="flex items-center justify-between py-1">
                  <span className="text-on-surface flex items-center gap-1.5">
                    <span className={`material-symbols-outlined text-[15px] ${customerName ? 'text-[#059669]' : 'text-secondary'}`}>
                      {customerName ? 'check_circle' : 'info'}
                    </span>
                    Customer Name
                  </span>
                  <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${customerName ? 'text-[#059669] bg-[#ECFDF5]' : 'text-secondary bg-surface-container'}`}>
                    {customerName ? 'Verified' : 'Optional — unstated'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-on-surface flex items-center gap-1.5">
                    <span className={`material-symbols-outlined text-[15px] ${deviceDescription ? 'text-[#059669]' : 'text-secondary'}`}>
                      {deviceDescription ? 'check_circle' : 'warning'}
                    </span>
                    Device Description
                  </span>
                  <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${deviceDescription ? 'text-[#059669] bg-[#ECFDF5]' : 'text-[#B45309] bg-[#FEF3C7]'}`}>
                    {deviceDescription ? 'Verified' : 'Required'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-on-surface flex items-center gap-1.5">
                    <span className={`material-symbols-outlined text-[15px] ${reportedProblem ? 'text-[#059669]' : 'text-secondary'}`}>
                      {reportedProblem ? 'check_circle' : 'info'}
                    </span>
                    Reported Problem
                  </span>
                  <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${reportedProblem ? 'text-[#059669] bg-[#ECFDF5]' : 'text-secondary bg-surface-container'}`}>
                    {reportedProblem ? 'Verified' : 'Unstated'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-on-surface flex items-center gap-1.5">
                    <span className={`material-symbols-outlined text-[15px] ${estimatedCost ? 'text-[#059669]' : 'text-secondary'}`}>
                      {estimatedCost ? 'check_circle' : 'info'}
                    </span>
                    Cost Estimate
                  </span>
                  <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${estimatedCost ? 'text-[#059669] bg-[#ECFDF5]' : 'text-secondary bg-surface-container'}`}>
                    {estimatedCost ? 'Verified' : 'Unstated'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-on-surface flex items-center gap-1.5">
                    <span className={`material-symbols-outlined text-[15px] ${customerPhone ? 'text-[#059669]' : 'text-secondary'}`}>
                      {customerPhone ? 'check_circle' : 'info'}
                    </span>
                    Phone Number
                  </span>
                  <span className={`font-medium px-2 py-0.5 rounded text-[11px] ${customerPhone ? 'text-[#059669] bg-[#ECFDF5]' : 'text-secondary bg-surface-container'}`}>
                    {customerPhone ? 'Verified' : 'Optional — unstated'}
                  </span>
                </div>
              </div>
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
                <span className="font-mono font-semibold text-primary">
                  {activeTicket ? activeTicket.ticket_number : 'Draft'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Customer:</span>
                <span className="font-medium">{customerName || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Device:</span>
                <span className="font-medium truncate max-w-[150px]">{deviceDescription || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Delivery:</span>
                <span className="font-medium">
                  {expectedDelivery ? formatDate(expectedDelivery) : 'Requires confirmation'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Cost:</span>
                <span className="font-bold text-emerald-700">
                  {estimatedCost ? formatCurrency(parseFloat(estimatedCost)) : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary">Status:</span>
                <span className="font-semibold">
                  {activeTicket ? (
                    <StatusBadge status={activeTicket.status} />
                  ) : (
                    <span className="text-secondary">Unsaved Draft</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
