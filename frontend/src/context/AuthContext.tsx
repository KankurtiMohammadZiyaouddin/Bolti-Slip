// src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { LoginCredentials, RegisterCredentials, Shop } from '../types/ticket';
import {
  fetchCurrentUser,
  getAuthToken,
  loginUser,
  logoutUser,
  registerUser,
  setAuthToken,
} from '../api/client';

interface AuthContextType {
  shop: Shop | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [shop, setShop] = useState<Shop | null>(null);
  const [token, setToken] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  // Check existing session token on application load
  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      const existingToken = getAuthToken();
      if (!existingToken) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const currentShop = await fetchCurrentUser();
        if (isMounted) {
          setShop(currentShop);
          setToken(existingToken);
        }
      } catch (err) {
        console.warn('Existing session invalid or expired:', err);
        setAuthToken(null);
        if (isMounted) {
          setShop(null);
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await loginUser(credentials);
      setToken(res.token);
      setShop(res.shop);
    } catch (err: any) {
      const msg = err.message || 'Login failed. Please check your credentials.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await registerUser(credentials);
      setToken(res.token);
      setShop(res.shop);
    } catch (err: any) {
      const msg = err.message || 'Registration failed. Please try again.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await logoutUser();
    } catch (err) {
      console.warn('Logout network error:', err);
    } finally {
      setShop(null);
      setToken(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        shop,
        token,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
