// src/pages/Auth/RegisterPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function RegisterPage() {
  const { register, error, clearError } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [shopName, setShopName] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [phone, setPhone] = useState('');
  const [branch, setBranch] = useState('Main Branch');
  const [address, setAddress] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setFormError(null);

    if (!username.trim() || !password.trim() || !shopName.trim() || !ownerName.trim()) {
      setFormError('कृपया आवश्यक फ़ील्ड भरें (यूजरनेम, पासवर्ड, दुकान का नाम और मालिक का नाम)।');
      return;
    }

    if (password.length < 6) {
      setFormError('पासवर्ड कम से कम 6 अक्षरों का होना चाहिए। (Password must be at least 6 characters)');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        username: username.trim(),
        password,
        shop_name: shopName.trim(),
        owner_name: ownerName.trim(),
        phone: phone.trim() || undefined,
        branch: branch.trim() || 'Main Branch',
        address: address.trim() || undefined,
      });
      navigate('/', { replace: true });
    } catch (err: any) {
      setFormError(err.message || 'रजिस्ट्रेशन विफल रहा। कृपया विवरण पुनः जांचें।');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-slate-100 px-4 py-10 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg space-y-7 rounded-2xl border border-gray-100 bg-white p-8 shadow-xl">
        {/* Header */}
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
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h2 className="mt-3 text-2xl font-extrabold tracking-tight text-gray-900">
            नई दुकान जोड़ें (Register Shop)
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            बोलती स्लिप पर अपना नया अकाउंट बनाएं
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
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                दुकान का नाम (Shop Name) *
              </label>
              <input
                type="text"
                required
                value={shopName}
                onChange={(e) => setShopName(e.target.value)}
                placeholder="उदा. वर्मा मोबाइल सॉल्यूशंस"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                मालिक का नाम (Owner Name) *
              </label>
              <input
                type="text"
                required
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
                placeholder="उदा. संजय वर्मा"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                यूजरनेम (Username) *
              </label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="उदा. verma"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                पासवर्ड (Password) *
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="कम से कम 6 अक्षर"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                मोबाइल नंबर (Phone)
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="9876543210"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                शाखा (Branch)
              </label>
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="उदा. मेन ब्रांच"
                className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
              दुकान का पता (Address)
            </label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="दुकान नं. 12, मेन मार्केट"
              className="mt-1 w-full rounded-xl border border-gray-300 px-3.5 py-2 text-sm shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-200 transition-all hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-60"
            >
              {isSubmitting ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>रजिस्टर हो रहा है...</span>
                </div>
              ) : (
                'दुकान रजिस्टर करें (Complete Registration)'
              )}
            </button>
          </div>
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          पहले से अकाउंट है?{' '}
          <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-500 underline">
            यहाँ लॉगिन करें (Sign In)
          </Link>
        </div>
      </div>
    </div>
  );
}
