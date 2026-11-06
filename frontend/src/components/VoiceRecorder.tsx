// src/components/VoiceRecorder.tsx
// Records audio from microphone, supports audio file upload, shows duration & playback,
// and delegates to transcribeAudio() for Gnani Prisma v3.0 STT processing.

import { useState, useRef } from 'react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { transcribeAudio } from '../api/client';
import AudioPlayer from './AudioPlayer';
import type { TranscribeResult } from '../types/ticket';

interface Props {
  /** Called when transcription succeeds — passes transcript text and raw result to parent */
  onTranscript: (transcript: string, raw: TranscribeResult) => void;
}

export default function VoiceRecorder({ onTranscript }: Props) {
  const {
    state,
    audioBlob,
    audioUrl,
    formattedDuration,
    startRecording,
    stopRecording,
    setUploadedFile,
    reset,
    error,
  } = useVoiceRecorder();

  const [transcribing, setTranscribing] = useState(false);
  const [transcribeError, setTranscribeError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function handleTranscribe() {
    if (!audioBlob) return;
    setTranscribing(true);
    setTranscribeError(null);
    try {
      const filename = audioBlob instanceof File ? audioBlob.name : 'recording.webm';
      const result = await transcribeAudio(audioBlob, filename);
      if (result.success && result.transcript) {
        onTranscript(result.transcript, result);
        reset();
      } else {
        setTranscribeError(result.error ?? 'ट्रांसक्रिप्शन विफल हुआ। Gnani Prisma API एरर।');
      }
    } catch (e) {
      setTranscribeError(e instanceof Error ? e.message : 'सर्वर या नेटवर्क त्रुटि।');
    } finally {
      setTranscribing(false);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm text-body-sm">
          {error}
        </div>
      )}

      {/* STATE 1: IDLE — Ready to record or upload */}
      {state === 'idle' && (
        <div className="flex flex-col items-center text-center py-4">
          <button
            type="button"
            onClick={startRecording}
            aria-label="Start Voice Recording"
            className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-primary-container hover:bg-primary text-on-primary flex items-center justify-center transition-all shadow-md active:scale-95 group mx-auto cursor-pointer"
          >
            <span className="material-symbols-outlined text-[36px] md:text-[42px] group-hover:scale-105 transition-transform">
              mic
            </span>
          </button>
          <h3 className="font-headline-sm text-headline-sm text-on-surface mt-4 font-semibold">
            Click to Start Speaking
          </h3>
          <p className="font-body-sm text-body-sm text-secondary mt-1 max-w-sm mx-auto">
            Speak customer name, device, fault, and delivery date in Hindi, English or Hinglish.
          </p>

          <div className="flex items-center gap-3 mt-5">
            <button
              type="button"
              onClick={startRecording}
              className="bg-primary-container text-on-primary px-5 py-2.5 rounded-xl font-label-md text-label-md flex items-center gap-2 hover:bg-primary transition-colors cursor-pointer shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px]">radio_button_checked</span>
              <span>Start Recording</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low text-on-surface px-5 py-2.5 rounded-xl font-label-md text-label-md flex items-center gap-2 transition-colors cursor-pointer shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px] text-secondary">upload_file</span>
              <span>Upload Audio</span>
            </button>
          </div>
          <p className="font-label-xs text-label-xs text-secondary mt-3">
            Supports live microphone or audio files (WAV, MP3, M4A, WEBM)
          </p>
        </div>
      )}

      {/* STATE 2: RECORDING — Active timer and stop button */}
      {state === 'recording' && (
        <div className="flex flex-col items-center text-center py-4">
          <div className="relative flex items-center justify-center my-3">
            <div className="w-28 h-28 md:w-32 md:h-32 rounded-full border-4 border-red-200 flex items-center justify-center bg-red-50/60 animate-pulse">
              <button
                type="button"
                onClick={stopRecording}
                aria-label="Stop Recording"
                className="w-18 h-18 md:w-20 md:h-20 rounded-full bg-error hover:bg-red-700 text-on-primary flex items-center justify-center transition-transform active:scale-95 shadow-md cursor-pointer"
              >
                <span className="w-6 h-6 md:w-7 md:h-7 rounded-[4px] bg-white" />
              </button>
            </div>
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 text-error font-label-xs text-label-xs font-semibold mt-1">
            <span className="w-2 h-2 rounded-full bg-error animate-ping" />
            <span>Recording audio buffer locally...</span>
          </div>

          <div className="font-headline-lg text-headline-lg text-on-surface tracking-tight mt-2 font-mono font-bold">
            {formattedDuration}
          </div>

          <p className="font-body-sm text-body-sm text-secondary mt-1">
            Capturing voice audio for Gnani Prisma STT batch dispatch.
          </p>

          <div className="flex items-center gap-3 mt-5">
            <button
              type="button"
              onClick={stopRecording}
              className="bg-error hover:bg-red-700 text-white px-6 py-2.5 rounded-xl font-label-md text-label-md flex items-center gap-2 transition-colors cursor-pointer shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px]">stop_circle</span>
              <span>Stop &amp; Review Audio</span>
            </button>

            <button
              type="button"
              onClick={reset}
              className="border border-outline-variant hover:bg-surface-container-low text-secondary px-4 py-2.5 rounded-xl font-label-md text-label-md transition-colors cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* STATE 3: STOPPED — Audio preview, transcribe action, and reset */}
      {state === 'stopped' && (
        <div className="flex flex-col gap-4 py-2">
          {audioUrl && (
            <div className="bg-surface-container-low rounded-xl border border-outline-variant/60 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-sm text-label-sm font-semibold text-on-surface flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-primary text-[18px]">audio_file</span>
                  <span>Audio Captured ({formattedDuration !== '00:00' ? formattedDuration : 'File Upload'})</span>
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-label-xs text-label-xs bg-emerald-100 text-emerald-800 font-medium">
                  <span className="material-symbols-outlined text-[13px]">check</span>
                  <span>Ready</span>
                </span>
              </div>
              <AudioPlayer url={audioUrl} label="Audio Preview:" />
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleTranscribe}
              disabled={transcribing}
              className="flex-1 bg-primary-container hover:bg-primary text-on-primary py-3 px-5 rounded-xl font-label-md text-label-md flex items-center justify-center gap-2 shadow-sm transition-all active:scale-[0.99] cursor-pointer disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[20px]">
                {transcribing ? 'sync' : 'transcribe'}
              </span>
              <span>{transcribing ? 'Prisma STT द्वारा टेक्स्ट बन रहा है…' : '✔ ट्रांसक्राइब करें (Transcribe Speech)'}</span>
            </button>

            <button
              type="button"
              onClick={reset}
              disabled={transcribing}
              className="border border-outline-variant hover:bg-surface-container-low text-secondary px-4 py-3 rounded-xl font-label-md text-label-md transition-colors cursor-pointer"
            >
              ↺ Reset
            </button>
          </div>
        </div>
      )}

      {/* Hidden File Input for Audio Upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*,.wav,.mp3,.m4a,.webm,.ogg"
        onChange={handleFileChange}
        className="hidden"
      />

      {transcribeError && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm text-body-sm">
          {transcribeError}
        </div>
      )}
    </div>
  );
}
