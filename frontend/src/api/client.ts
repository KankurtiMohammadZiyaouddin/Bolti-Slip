// src/api/client.ts
// Typed API wrappers for the Bolti Slip FastAPI backend.
// All requests go to /api/* — proxied to http://localhost:8000 by Vite.

import type { Ticket, TicketCreate, TicketStatus, TranscribeResult } from '../types/ticket';

const BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse error, use status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Transcription
// ---------------------------------------------------------------------------

export async function transcribeAudio(audioBlob: Blob, filename = 'audio.wav'): Promise<TranscribeResult> {
  const form = new FormData();
  form.append('audio_file', audioBlob, filename);
  const res = await fetch(`${BASE}/transcribe`, { method: 'POST', body: form });
  return handleResponse<TranscribeResult>(res);
}

// ---------------------------------------------------------------------------
// Tickets
// ---------------------------------------------------------------------------

export async function createTicket(data: TicketCreate): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Ticket>(res);
}

export async function listTickets(status?: TicketStatus): Promise<Ticket[]> {
  const url = status ? `${BASE}/tickets?status=${status}` : `${BASE}/tickets`;
  const res = await fetch(url);
  return handleResponse<Ticket[]>(res);
}

export async function getTicket(id: number): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets/${id}`);
  return handleResponse<Ticket>(res);
}

export async function updateTicketStatus(id: number, status: TicketStatus): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return handleResponse<Ticket>(res);
}

// ---------------------------------------------------------------------------
// Speech / TTS
// ---------------------------------------------------------------------------

export async function speakText(text: string, voice = 'Devansh', language = 'hi-IN'): Promise<Blob> {
  const res = await fetch(`${BASE}/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice, language }),
  });
  if (!res.ok) throw new Error(`TTS failed: HTTP ${res.status}`);
  return res.blob();
}

export async function confirmTicket(id: number): Promise<Blob> {
  const res = await fetch(`${BASE}/tickets/${id}/confirm`, { method: 'POST' });
  if (!res.ok) throw new Error(`Confirm TTS failed: HTTP ${res.status}`);
  return res.blob();
}
