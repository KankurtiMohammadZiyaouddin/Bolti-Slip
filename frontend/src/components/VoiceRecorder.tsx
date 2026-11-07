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
    recordedMimeType,
    formattedDuration,
    startRecording,
    stopRecording,
    setUploadedFile,
    reset,
    error,
    errorInfo,
  } = useVoiceRecorder();

  const [transcribing, setTranscribing] = useState(false);
  const [transcribeError, setTranscribeError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function handleTranscribe() {
    if (!audioBlob || transcribing) return;
    setTranscribing(true);
    setTranscribeError(null);

    // Determine correct filename and extension dynamically based on actual MIME type
    let filename = 'recording.webm';
    if (audioBlob instanceof File && audioBlob.name) {
      filename = audioBlob.name;
    } else {
      const type = (recordedMimeType || audioBlob.type || '').toLowerCase();
      if (type.includes('webm')) filename = 'recording.webm';
      else if (type.includes('mp4') || type.includes('m4a') || type.includes('aac')) filename = 'recording.m4a';
      else if (type.includes('ogg')) filename = 'recording.ogg';
      else if (type.includes('wav')) filename = 'recording.wav';
      else filename = 'recording.webm';
    }

    try {
      const result = await transcribeAudio(audioBlob, filename);
      if (result.success && result.transcript) {
        onTranscript(result.transcript, result);
        reset();
      } else {
        const errDetail = result.error || 'ट्रांसक्रिप्शन विफल हुआ। Gnani Prisma API एरर।';
        setTranscribeError(errDetail);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'सर्वर या नेटवर्क त्रुटि।';
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('Load failed')) {
        setTranscribeError(
          'नेटवर्क या टनल कनेक्शन त्रुटि (Failed to fetch). कृपया इंटरनेट और टनल कनेक्शन जांचें। आपका ऑडियो सुरक्षित है, कृपया "पुनः प्रयास करें" दबाएं।'
        );
      } else {
        setTranscribeError(msg);
      }
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
      {errorInfo ? (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-left flex flex-col gap-2 shadow-xs">
          <div className="flex items-center gap-2 text-amber-800 font-semibold font-label-md">
            <span className="material-symbols-outlined text-[20px] text-amber-700">mic_off</span>
            <span>{errorInfo.title}</span>
          </div>
          <p className="font-body-sm text-body-sm whitespace-pre-line text-amber-800">
            {errorInfo.instruction}
          </p>
          <div className="flex items-center gap-2 pt-2 border-t border-amber-200/60 mt-1">
            <button
              type="button"
              onClick={startRecording}
              className="px-3.5 py-1.5 rounded-lg bg-amber-700 hover:bg-amber-800 text-white font-label-sm font-medium transition-colors cursor-pointer"
            >
              🔄 पुनः प्रयास करें (Retry)
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-3.5 py-1.5 rounded-lg bg-white border border-amber-300 text-amber-900 font-label-sm font-medium hover:bg-amber-100 transition-colors cursor-pointer"
            >
              📁 ऑडियो फ़ाइल अपलोड करें
            </button>
          </div>
        </div>
      ) : error ? (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm text-body-sm">
          {error}
        </div>
      ) : null}

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
              <span className={`material-symbols-outlined text-[20px] ${transcribing ? 'animate-spin' : ''}`}>
                {transcribing ? 'progress_activity' : 'transcribe'}
              </span>
              <span>{transcribing ? 'Prisma STT द्वारा टेक्स्ट बन रहा है…' : '✔ ट्रांसक्राइब करें (Transcribe Speech)'}</span>
            </button>

            <button
              type="button"
              onClick={reset}
              disabled={transcribing}
              className="border border-outline-variant hover:bg-surface-container-low text-secondary px-4 py-3 rounded-xl font-label-md text-label-md transition-colors cursor-pointer disabled:opacity-40"
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
        accept="audio/*,.wav,.mp3,.m4a,.webm,.ogg,.aac,.flac"
        onChange={handleFileChange}
        className="hidden"
      />

      {transcribeError && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-error font-body-sm flex flex-col gap-2.5">
          <div className="flex items-start gap-2">
            <span className="material-symbols-outlined text-[20px] text-error shrink-0 mt-0.5">error</span>
            <span className="flex-1 font-medium">{transcribeError}</span>
          </div>
          <div className="flex items-center gap-2 pt-1 border-t border-red-200/60">
            <button
              type="button"
              onClick={handleTranscribe}
              disabled={transcribing}
              className="px-3.5 py-1.5 bg-error text-white rounded-lg font-label-sm font-semibold hover:bg-red-700 transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              <span>पुनः प्रयास करें (Retry Transcription)</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
