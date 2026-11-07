// src/hooks/useVoiceRecorder.ts
// Custom hook that wraps the MediaRecorder API with duration tracking,
// safe microphone permission error diagnostics, and file upload support.

import { useState, useRef, useCallback, useEffect } from 'react';

export type RecorderState = 'idle' | 'recording' | 'stopped';

export interface MicErrorInfo {
  title: string;
  instruction: string;
  isPermissionDenied?: boolean;
  isInsecureContext?: boolean;
}

export interface UseVoiceRecorderReturn {
  state: RecorderState;
  audioBlob: Blob | null;
  audioUrl: string | null;
  recordedMimeType: string | null;
  durationSeconds: number;
  formattedDuration: string;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  setUploadedFile: (file: File) => void;
  reset: () => void;
  error: string | null;
  errorInfo: MicErrorInfo | null;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [state, setState] = useState<RecorderState>('idle');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordedMimeType, setRecordedMimeType] = useState<string | null>(null);
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [errorInfo, setErrorInfo] = useState<MicErrorInfo | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<number | null>(null);

  // Timer effect for recording duration
  useEffect(() => {
    if (state === 'recording') {
      setDurationSeconds(0);
      timerRef.current = window.setInterval(() => {
        setDurationSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [state]);

  const startRecording = useCallback(async () => {
    setError(null);
    setErrorInfo(null);
    chunksRef.current = [];

    // 1. Check secure context requirement for mobile browsers over HTTPS
    if (
      typeof window !== 'undefined' &&
      !window.isSecureContext &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1'
    ) {
      const info: MicErrorInfo = {
        title: 'सुरक्षित कनेक्शन (HTTPS) आवश्यक है',
        instruction:
          'मोबाइल ब्राउज़र में माइक्रोफोन उपयोग करने के लिए HTTPS या localhost आवश्यक है। कृपया ऐप को HTTPS या localhost से खोलें।',
        isInsecureContext: true,
      };
      setError(info.instruction);
      setErrorInfo(info);
      return;
    }

    // 2. Check mediaDevices API availability in the browser
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const info: MicErrorInfo = {
        title: 'माइक्रोफोन समर्थित नहीं है (MediaDevices Unsupported)',
        instruction:
          'आपका वर्तमान ब्राउज़र MediaRecorder ऑडियो रिकॉर्डिंग का समर्थन नहीं करता है। कृपया आधुनिक Chrome या Edge ब्राउज़र का उपयोग करें, या नीचे "Upload Audio" बटन से ऑडियो फ़ाइल अपलोड करें।',
      };
      setError(info.instruction);
      setErrorInfo(info);
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err: unknown) {
      const errorObj = err as { name?: string; message?: string };
      console.warn('Microphone access denied or failed:', err);

      if (errorObj?.name === 'NotAllowedError' || errorObj?.name === 'PermissionDeniedError') {
        const info: MicErrorInfo = {
          title: 'माइक्रोफोन अनुमति अस्वीकृत (Microphone Blocked)',
          instruction:
            'ब्राउज़र में माइक्रोफोन अनुमति ब्लॉक है। अनुमति देने के लिए:\n1. एड्रेस बार में ताला (🔒) या सेटिंग्स आइकन पर टैप करें।\n2. "Permissions" -> "Microphone" को "Allow" (अनुमति दें) पर सेट करें।\n3. इसके बाद पेज को रीफ़्रेश करें।',
          isPermissionDenied: true,
        };
        setError('माइक्रोफोन अनुमति अस्वीकृत है। कृपया ब्राउज़र सेटिंग्स में अनुमति दें।');
        setErrorInfo(info);
      } else if (errorObj?.name === 'NotFoundError' || errorObj?.name === 'DevicesNotFoundError') {
        const info: MicErrorInfo = {
          title: 'कोई माइक्रोफोन उपकरण नहीं मिला (No Microphone Found)',
          instruction:
            'आपके डिवाइस में कोई ऑडियो इनपुट उपकरण नहीं मिला। आप नीचे "Upload Audio" बटन का उपयोग करके ऑडियो फ़ाइल (WAV/MP3) भी अपलोड कर सकते हैं।',
        };
        setError('कोई माइक्रोफोन उपकरण नहीं मिला।');
        setErrorInfo(info);
      } else {
        const info: MicErrorInfo = {
          title: 'रिकॉर्डिंग प्रारंभ करने में विफल',
          instruction: errorObj?.message || 'माइक्रोफोन प्रारंभ नहीं किया जा सका।',
        };
        setError(info.instruction);
        setErrorInfo(info);
      }
      return;
    }

    // Check supported audio MIME types across modern mobile and desktop browsers:
    // 1. Android Chrome: audio/webm;codecs=opus, audio/webm
    // 2. iOS Safari: audio/mp4, audio/aac
    // 3. Desktop Firefox / others: audio/ogg;codecs=opus
    let mimeType = '';
    const candidateTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/aac',
      'audio/ogg;codecs=opus',
      'audio/ogg',
    ];

    for (const candidate of candidateTypes) {
      if (typeof MediaRecorder.isTypeSupported === 'function' && MediaRecorder.isTypeSupported(candidate)) {
        mimeType = candidate;
        break;
      }
    }

    try {
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const actualMime = recorder.mimeType || mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: actualMime });
        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);
        setRecordedMimeType(actualMime);
        setState('stopped');
        // Stop all tracks to release microphone hardware
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      setState('recording');
    } catch (err: unknown) {
      console.error('Failed to start MediaRecorder:', err);
      const info: MicErrorInfo = {
        title: 'MediaRecorder प्रारंभ करने में त्रुटि',
        instruction: 'ऑडियो रिकॉर्डर आरंभ नहीं हो सका। कृपया पुनः प्रयास करें।',
      };
      setError(info.instruction);
      setErrorInfo(info);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, [state]);

  const setUploadedFile = useCallback((file: File) => {
    if (!file) return;
    setError(null);
    setErrorInfo(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    const url = URL.createObjectURL(file);
    setAudioBlob(file);
    setAudioUrl(url);
    setRecordedMimeType(file.type || null);
    setState('stopped');
  }, [audioUrl]);

  const reset = useCallback(() => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordedMimeType(null);
    setDurationSeconds(0);
    setState('idle');
    setError(null);
    setErrorInfo(null);
  }, [audioUrl]);

  const mins = Math.floor(durationSeconds / 60);
  const secs = durationSeconds % 60;
  const formattedDuration = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  return {
    state,
    audioBlob,
    audioUrl,
    recordedMimeType,
    durationSeconds,
    formattedDuration,
    startRecording,
    stopRecording,
    setUploadedFile,
    reset,
    error,
    errorInfo,
  };
}
