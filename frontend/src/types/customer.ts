// src/types/customer.ts
// Customer profile and directory interfaces

import type { Ticket } from './ticket';

export interface Customer {
  id: number;
  shop_id: number;
  name: string;
  phone: string;
  alternate_phone?: string | null;
  email?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  total_tickets?: number;
}

export interface CustomerWithHistory extends Customer {
  tickets: Ticket[];
}

export interface CustomerCreate {
  name: string;
  phone: string;
  alternate_phone?: string;
  email?: string;
  notes?: string;
}

export interface CustomerUpdate {
  name?: string;
  phone?: string;
  alternate_phone?: string;
  email?: string;
  notes?: string;
}
