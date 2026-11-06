// src/pages/NewTicket/NewTicketPage.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import VoiceRecorder from '../../components/VoiceRecorder';
import TicketForm from '../../components/TicketForm';
import AudioPlayer from '../../components/AudioPlayer';
import { confirmTicket, extractTranscript } from '../../api/client';
import type { ExtractionResult, Ticket, TranscribeResult } from '../../types/ticket';

export default function NewTicketPage() {
  const [transcript, setTranscript] = useState('');
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  const [createdTicket, setCreatedTicket] = useState<Ticket | null>(null);
  const [confirmAudioUrl, setConfirmAudioUrl] = useState<string | null>(null);
  const [playingConfirm, setPlayingConfirm] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  async function handleTranscript(text: string, _raw: TranscribeResult) {
    setTranscript(text);
    setCreatedTicket(null);
    setConfirmAudioUrl(null);
    setExtractError(null);

    // Call extraction API automatically
    setExtracting(true);
    try {
      const result = await extractTranscript(text);
      setExtraction(result);
    } catch (err) {
      console.error('Failed to extract transcript fields:', err);
      setExtractError('फ़ील्ड्स स्वतः निकालने में समस्या आई। आप मैन्युअल भर सकते हैं।');
      setExtraction(null);
    } finally {
      setExtracting(false);
    }
  }

  async function handleTicketCreated(ticket: Ticket) {
    setCreatedTicket(ticket);
    setTranscript('');
    setExtraction(null);
    setConfirmError(null);

    // Auto-fetch spoken confirmation from Timbre TTS
    try {
      setPlayingConfirm(true);
      const audioBlob = await confirmTicket(ticket.id);
      const url = URL.createObjectURL(audioBlob);
      setConfirmAudioUrl(url);
    } catch (err) {
      setConfirmError(err instanceof Error ? err.message : 'आवाज़ पुष्टि लोड करने में असमर्थ।');
    } finally {
      setPlayingConfirm(false);
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-sm mb-6">
        <div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            New Ticket (बोलती पर्ची)
          </h1>
          <p className="font-body-md text-body-md text-secondary mt-1">
            Speak naturally in Hindi, English or Hinglish. Gnani Prisma v3.0 processes speech into structured repair slips.
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-label-xs text-label-xs bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
          Gnani Prisma v3.0 &amp; Timbre v3.0 Connected
        </div>
      </div>

      {createdTicket && (
        <div className="mb-6 p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-center flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mb-2">
            <span className="material-symbols-outlined text-[28px]">check_circle</span>
          </div>
          <h2 className="font-headline-sm text-headline-sm text-emerald-900 font-bold mb-1">
            🎉 पर्ची सफलतापूर्वक बनाई गई!
          </h2>
          <p className="font-mono text-[16px] font-bold text-emerald-800 mb-3">
            पर्ची क्रमांक: {createdTicket.ticket_number}
          </p>

          {playingConfirm && (
            <p className="font-body-sm text-secondary italic mb-2">
              🔊 हिंदी में पुष्टि तैयार हो रही है (Timbre TTS)...
            </p>
          )}

          {confirmAudioUrl && (
            <div className="w-full max-w-md mx-auto mb-4">
              <AudioPlayer url={confirmAudioUrl} label="🔊 बोलती पुष्टि (Spoken Confirmation):" />
            </div>
          )}

          {confirmError && (
            <p className="text-error font-body-sm text-body-sm mb-3">{confirmError}</p>
          )}

          <div className="flex items-center gap-3">
            <Link
              to={`/tickets/${createdTicket.id}`}
              className="px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md transition-colors"
            >
              विवरण देखें (Ticket Details) →
            </Link>
            <button
              onClick={() => {
                setCreatedTicket(null);
                setConfirmAudioUrl(null);
              }}
              className="px-4 py-2.5 rounded-xl border border-outline-variant hover:bg-surface-container-low text-secondary font-label-md text-label-md transition-colors cursor-pointer"
              type="button"
            >
              + नई पर्ची बनाएं
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Voice Intake & Extraction Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Voice Intake Recording */}
        <section className="lg:col-span-6 bg-surface-container-lowest rounded-2xl border border-outline-variant p-6 shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between pb-3 border-b border-outline-variant/60">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[20px]">mic</span>
              <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                Voice Intake
              </h2>
            </div>
            <span className="font-label-xs text-label-xs px-2.5 py-0.5 rounded-full bg-secondary-container text-primary font-medium">
              Audio Input
            </span>
          </div>

          <VoiceRecorder onTranscript={handleTranscript} />

          {/* Processing Status Banner */}
          {extracting && (
            <div className="p-4 rounded-xl bg-primary-fixed/30 border border-primary/20 text-primary font-label-sm flex items-center justify-center gap-2 animate-pulse">
              <span className="material-symbols-outlined text-[18px]">sync</span>
              <span>⚡ आवाज़ से पर्ची के विवरण (डिवाइस, समस्या, तारीख, लागत) पहचाने जा रहे हैं...</span>
            </div>
          )}

          {extractError && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 font-label-sm">
              {extractError}
            </div>
          )}
        </section>

        {/* Right Column: Ticket Form with Auto-fill */}
        <section className="lg:col-span-6">
          <TicketForm
            initialTranscript={transcript}
            extractedFields={extraction}
            onTicketCreated={handleTicketCreated}
          />
        </section>
      </div>
    </div>
  );
}
