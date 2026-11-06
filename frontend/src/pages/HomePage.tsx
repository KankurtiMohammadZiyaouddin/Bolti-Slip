// src/pages/HomePage.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import VoiceRecorder from '../components/VoiceRecorder';
import TicketForm from '../components/TicketForm';
import AudioPlayer from '../components/AudioPlayer';
import { confirmTicket, extractTranscript } from '../api/client';
import type { ExtractionResult, Ticket, TranscribeResult } from '../types/ticket';

export default function HomePage() {
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
    // Clear previous confirmation if any
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
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.2rem', color: 'var(--color-primary)', marginBottom: '.5rem' }}>
          🎙️ बोलती स्लिप (Bolti Slip)
        </h1>
        <p style={{ color: 'var(--color-muted)', fontSize: '1.05rem' }}>
          आवाज़ से बोलकर तुरंत रिपेयर रसीद बनाएं और हिंदी में पुष्टि सुनें
        </p>
      </div>

      {createdTicket && (
        <div
          className="card"
          style={{
            background: '#e8f5e9',
            border: '1px solid #c8e6c9',
            marginBottom: '1.5rem',
            textAlign: 'center',
            padding: '1.5rem',
          }}
        >
          <h2 style={{ color: 'var(--color-success)', marginBottom: '.5rem' }}>
            🎉 पर्ची सफलतापूर्वक बनाई गई!
          </h2>
          <p style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            पर्ची क्रमांक: {createdTicket.ticket_number}
          </p>

          {playingConfirm && (
            <p style={{ color: 'var(--color-muted)', fontStyle: 'italic' }}>
              🔊 हिंदी में पुष्टि तैयार हो रही है (Timbre TTS)...
            </p>
          )}

          {confirmAudioUrl && (
            <div style={{ maxWidth: '400px', margin: '0 auto 1rem' }}>
              <AudioPlayer url={confirmAudioUrl} label="🔊 बोलती पुष्टि (Spoken Confirmation):" />
            </div>
          )}

          {confirmError && (
            <p style={{ color: 'var(--color-danger)', fontSize: '.9rem' }}>{confirmError}</p>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
            <Link to={`/tickets/${createdTicket.id}`}>
              <button className="btn-primary">विवरण देखें (Ticket Details) →</button>
            </Link>
            <button
              className="btn-secondary"
              onClick={() => {
                setCreatedTicket(null);
                setConfirmAudioUrl(null);
              }}
            >
              + नई पर्ची बनाएं
            </button>
          </div>
        </div>
      )}

      {/* Step 1: Voice Recording */}
      <VoiceRecorder onTranscript={handleTranscript} />

      {/* Extraction loading status indicator */}
      {extracting && (
        <div
          style={{
            textAlign: 'center',
            padding: '.75rem',
            margin: '1rem 0',
            background: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: 'var(--radius)',
            color: 'var(--color-primary)',
            fontWeight: 500,
          }}
        >
          ⚡ आवाज़ से पर्ची के विवरण (डिवाइस, समस्या, तारीख, लागत) पहचाने जा रहे हैं...
        </div>
      )}

      {extractError && (
        <div
          style={{
            textAlign: 'center',
            padding: '.6rem',
            margin: '1rem 0',
            background: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: 'var(--radius)',
            color: '#92400e',
            fontSize: '.9rem',
          }}
        >
          {extractError}
        </div>
      )}

      {/* Step 2: Form */}
      <TicketForm
        initialTranscript={transcript}
        extractedFields={extraction}
        onTicketCreated={handleTicketCreated}
      />
    </div>
  );
}
