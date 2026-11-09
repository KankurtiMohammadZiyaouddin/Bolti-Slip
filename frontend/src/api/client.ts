// src/api/client.ts
// Typed API wrappers for the Bolti Slip FastAPI backend.
// All requests go to /api/* — proxied to http://localhost:8000 by Vite.

import type {
  AuthResponse,
  Customer,
  CustomerCreate,
  CustomerUpdate,
  CustomerWithHistory,
  ExtractionResult,
  LoginCredentials,
  RegisterCredentials,
  Shop,
  Ticket,
  TicketCreate,
  TicketStatus,
  TranscribeResult,
} from '../types/ticket';

const BASE = '/api';
const TOKEN_KEY = 'bolti_slip_auth_token';

// ---------------------------------------------------------------------------
// Token Management
// ---------------------------------------------------------------------------

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

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
// Authentication
// ---------------------------------------------------------------------------

export async function loginUser(credentials: LoginCredentials): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  const data = await handleResponse<AuthResponse>(res);
  setAuthToken(data.token);
  return data;
}

export async function registerUser(credentials: RegisterCredentials): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  const data = await handleResponse<AuthResponse>(res);
  setAuthToken(data.token);
  return data;
}

export async function fetchCurrentUser(): Promise<Shop> {
  const res = await fetch(`${BASE}/auth/me`, {
    headers: getHeaders(),
  });
  return handleResponse<Shop>(res);
}

export async function changePassword(current_password: string, new_password: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${BASE}/auth/change-password`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ current_password, new_password }),
  });
  return handleResponse<{ success: boolean; message: string }>(res);
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${BASE}/auth/logout`, {
      method: 'POST',
      headers: getHeaders(),
    });
  } finally {
    setAuthToken(null);
  }
}

// ---------------------------------------------------------------------------
// Transcription
// ---------------------------------------------------------------------------

export async function transcribeAudio(audioBlob: Blob, filename = 'audio.wav'): Promise<TranscribeResult> {
  const form = new FormData();
  form.append('audio_file', audioBlob, filename);
  const res = await fetch(`${BASE}/transcribe`, {
    method: 'POST',
    headers: getHeaders(),
    body: form,
  });
  return handleResponse<TranscribeResult>(res);
}

// ---------------------------------------------------------------------------
// Extraction
// ---------------------------------------------------------------------------

export async function extractTranscript(transcript: string): Promise<ExtractionResult> {
  const res = await fetch(`${BASE}/extract`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ transcript }),
  });
  return handleResponse<ExtractionResult>(res);
}

// ---------------------------------------------------------------------------
// Tickets
// ---------------------------------------------------------------------------

export async function createTicket(data: TicketCreate): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  return handleResponse<Ticket>(res);
}

export async function listTickets(status?: TicketStatus): Promise<Ticket[]> {
  const url = status ? `${BASE}/tickets?status=${status}` : `${BASE}/tickets`;
  const res = await fetch(url, {
    headers: getHeaders(),
  });
  return handleResponse<Ticket[]>(res);
}

export async function getTicket(id: number): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets/${id}`, {
    headers: getHeaders(),
  });
  return handleResponse<Ticket>(res);
}

export async function updateTicketStatus(id: number, status: TicketStatus): Promise<Ticket> {
  const res = await fetch(`${BASE}/tickets/${id}/status`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ status }),
  });
  return handleResponse<Ticket>(res);
}

// ---------------------------------------------------------------------------
// Customers
// ---------------------------------------------------------------------------

export async function listCustomers(q?: string): Promise<Customer[]> {
  const url = q ? `${BASE}/customers?q=${encodeURIComponent(q)}` : `${BASE}/customers`;
  const res = await fetch(url, {
    headers: getHeaders(),
  });
  return handleResponse<Customer[]>(res);
}

export async function getCustomerDetails(id: number): Promise<CustomerWithHistory> {
  const res = await fetch(`${BASE}/customers/${id}`, {
    headers: getHeaders(),
  });
  return handleResponse<CustomerWithHistory>(res);
}

export async function createCustomer(data: CustomerCreate): Promise<Customer> {
  const res = await fetch(`${BASE}/customers`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  return handleResponse<Customer>(res);
}

export async function updateCustomer(id: number, data: CustomerUpdate): Promise<Customer> {
  const res = await fetch(`${BASE}/customers/${id}`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  return handleResponse<Customer>(res);
}

// ---------------------------------------------------------------------------
// Speech / TTS
// ---------------------------------------------------------------------------

export async function speakText(text: string, voice = 'Devansh', language = 'hi-IN'): Promise<Blob> {
  const res = await fetch(`${BASE}/speak`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ text, voice, language }),
  });
  if (!res.ok) throw new Error(`TTS failed: HTTP ${res.status}`);
  return res.blob();
}

export async function confirmTicket(id: number): Promise<Blob> {
  const res = await fetch(`${BASE}/tickets/${id}/confirm`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error(`Confirm TTS failed: HTTP ${res.status}`);
  return res.blob();
}
