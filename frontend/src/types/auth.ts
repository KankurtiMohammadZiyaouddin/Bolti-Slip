// src/types/auth.ts
// Shopkeeper authentication and profile interfaces

export interface Shop {
  id: number;
  username: string;
  shop_name: string;
  owner_name: string;
  phone?: string | null;
  branch?: string | null;
  address?: string | null;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  shop: Shop;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  password: string;
  shop_name: string;
  owner_name: string;
  phone?: string;
  branch?: string;
  address?: string;
}
