// src/pages/Auth/LoginPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const { login, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);

    if (!username.trim() || !password.trim()) {
      setFormError('कृपया यूजरनेम और पासवर्ड दोनों दर्ज करें। (Please enter both username and password)');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ username: username.trim(), password });
      navigate(from, { replace: true });
    } catch (err: any) {
      setFormError(err.message || 'लॉगिन विफल रहा। कृपया अपने क्रेडेंशियल जांचें।');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-slate-100 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-gray-100 bg-white p-8 shadow-xl">
        {/* Header / Brand */}
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-200">
            <svg
              className="h-8 w-8"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"
              />
            </svg>
          </div>
          <h2 className="mt-4 text-2xl font-extrabold tracking-tight text-gray-900">
            बोलती स्लिप (Bolti Slip)
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            दुकानदार लॉगिन • Voice-to-Repair Ticket SaaS
          </p>
        </div>

        {/* Error Display */}
        {(formError || error) && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3.5 text-sm text-red-700">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{formError || error}</span>
            </div>
          </div>
        )}

        {/* Form */}
        <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              यूजरनेम (Username)
            </label>
            <div className="mt-1">
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="उदा. sharma"
                autoComplete="username"
                className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm shadow-sm transition-colors focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              पासवर्ड (Password)
            </label>
            <div className="mt-1">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                className="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm shadow-sm transition-colors focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-200 transition-all hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-60"
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>लॉगिन हो रहा है...</span>
                </div>
              ) : (
                'लॉगिन करें (Sign In)'
              )}
            </button>
          </div>
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          नई दुकान रजिस्टर करना चाहते हैं?{' '}
          <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-500 underline">
            यहाँ रजिस्टर करें (Register Shop)
          </Link>
        </div>
      </div>
    </div>
  );
}
