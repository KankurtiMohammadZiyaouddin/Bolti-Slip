// src/components/VoiceRecorder.tsx
// Records audio from the microphone, shows playback, and calls
// transcribeAudio() from the API client.

import { useState } from 'react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { transcribeAudio } from '../api/client';
import AudioPlayer from './AudioPlayer';
import type { TranscribeResult } from '../types/ticket';

interface Props {
  /** Called when transcription succeeds — gives parent the transcript text */
  onTranscript: (transcript: string, raw: TranscribeResult) => void;
}

export default function VoiceRecorder({ onTranscript }: Props) {
  const { state, audioBlob, audioUrl, startRecording, stopRecording, reset, error } =
    useVoiceRecorder();
  const [transcribing, setTranscribing] = useState(false);
  const [transcribeError, setTranscribeError] = useState<string | null>(null);

  async function handleTranscribe() {
    if (!audioBlob) return;
    setTranscribing(true);
    setTranscribeError(null);
    try {
      const result = await transcribeAudio(audioBlob, 'recording.webm');
      if (result.success && result.transcript) {
        onTranscript(result.transcript, result);
        reset();
      } else {
        setTranscribeError(result.error ?? 'ट्रांसक्रिप्शन विफल हुआ।');
      }
    } catch (e) {
      setTranscribeError(e instanceof Error ? e.message : 'अज्ञात त्रुटि।');
    } finally {
      setTranscribing(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: '1rem' }}>
      <h3 style={{ marginBottom: '.75rem' }}>🎙️ आवाज़ से शिकायत दर्ज करें</h3>

      {error && <p style={{ color: 'var(--color-danger)', marginBottom: '.5rem' }}>{error}</p>}

      <div style={{ display: 'flex', gap: '.75rem', flexWrap: 'wrap' }}>
        {state === 'idle' && (
          <button className="btn-primary" onClick={startRecording}>
            ● रिकॉर्ड करें
          </button>
        )}
        {state === 'recording' && (
          <button className="btn-danger" onClick={stopRecording}>
            ■ रोकें
          </button>
        )}
        {state === 'stopped' && (
          <>
            <button
              className="btn-primary"
              onClick={handleTranscribe}
              disabled={transcribing}
            >
              {transcribing ? 'ट्रांसक्राइब हो रहा है…' : '✔ टेक्स्ट बनाएं'}
            </button>
            <button className="btn-secondary" onClick={reset} disabled={transcribing}>
              ↺ फिर से रिकॉर्ड करें
            </button>
          </>
        )}
      </div>

      {audioUrl && state === 'stopped' && (
        <AudioPlayer url={audioUrl} label="रिकॉर्ड की गई आवाज़:" />
      )}

      {transcribeError && (
        <p style={{ color: 'var(--color-danger)', marginTop: '.5rem' }}>{transcribeError}</p>
      )}
    </div>
  );
}
