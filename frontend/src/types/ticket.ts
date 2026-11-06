// src/types/ticket.ts
// Shared TypeScript types matching the backend Pydantic models

export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';

export interface Ticket {
  id: number;
  ticket_number: string;
  customer_name: string | null;
  customer_phone: string | null;
  device_description: string;
  transcript_raw: string | null;
  reported_problem: string | null;
  repair_instructions: string | null;
  expected_delivery: string | null;
  estimated_cost: number | null;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
}

export interface TranscribeResult {
  success: boolean;
  transcript: string | null;
  detected_language_code: string | null;
  model: string;
  http_status_code: number | null;
  api_processing_time: number | null;
  request_elapsed_seconds: number | null;
  error: string | null;
  error_type: string | null;
}

export interface TicketCreate {
  customer_name?: string;
  customer_phone?: string;
  device_description: string;
  transcript_raw?: string;
  reported_problem?: string;
  repair_instructions?: string;
  expected_delivery?: string;
  estimated_cost?: number;
}
