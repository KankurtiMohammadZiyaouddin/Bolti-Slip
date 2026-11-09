// src/pages/Customers/CustomersPage.tsx
import React, { useState, useEffect } from 'react';
import { listCustomers, getCustomerDetails } from '../../api/client';
import type { Customer, CustomerWithHistory } from '../../types/ticket';
import StatusBadge from '../../components/StatusBadge';
import { formatDate } from '../../utils/formatters';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected customer for history view
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerWithHistory | null>(null);

  const fetchCustomers = async (query = '') => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listCustomers(query);
      setCustomers(data);
    } catch (err: any) {
      setError(err.message || 'ग्राहकों की सूची लोड करने में विफल।');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers(searchQuery);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCustomers(searchQuery);
  };

  const handleOpenHistory = async (customer: Customer) => {
    try {
      const details = await getCustomerDetails(customer.id);
      setSelectedCustomer(details);
    } catch (err: any) {
      alert(`ग्राहक का विवरण प्राप्त नहीं हो सका: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            ग्राहक डायरेक्टरी (Customers Directory)
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            आपकी दुकान के सभी पंजीकृत ग्राहक और उनका रिपेयर इतिहास
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative w-full sm:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="नाम या मोबाइल नंबर से खोजें..."
              className="w-full rounded-xl border border-gray-300 bg-white py-2 pl-9 pr-4 text-sm text-gray-900 shadow-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-600/20"
            />
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
          <button
            type="submit"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            खोजें
          </button>
        </form>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">कुल ग्राहक (Customers)</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{customers.length}</p>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">कुल टिकट्स (Repairs)</p>
          <p className="mt-1 text-2xl font-bold text-indigo-600">
            {customers.reduce((acc, c) => acc + (c.total_tickets || 0), 0)}
          </p>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-gray-200 bg-white">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
            <span>ग्राहक सूची लोड हो रही है...</span>
          </div>
        </div>
      ) : customers.length === 0 ? (
        <div className="flex h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
          <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-semibold text-gray-900">कोई ग्राहक नहीं मिला</h3>
          <p className="mt-1 text-xs text-gray-500">
            जब आप नया वॉयस टिकट बनाएंगे, तो ग्राहक का नंबर यहाँ अपने आप सेव हो जाएगा।
          </p>
        </div>
      ) : (
        /* Customers Grid */
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {customers.map((c) => (
            <div
              key={c.id}
              className="flex flex-col justify-between rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 font-bold text-indigo-600">
                      {c.name ? c.name.charAt(0).toUpperCase() : 'G'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{c.name || 'Valued Customer'}</h3>
                      <p className="text-xs text-gray-500">ID: #{c.id}</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                    {c.total_tickets || 0} टिकट्स
                  </span>
                </div>

                <div className="mt-4 space-y-2 text-xs text-gray-600">
                  <div className="flex items-center gap-2">
                    <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                      />
                    </svg>
                    <a
                      href={`tel:${c.phone}`}
                      className="font-medium text-indigo-600 hover:underline"
                    >
                      {c.phone}
                    </a>
                  </div>

                  {c.notes && (
                    <p className="mt-1 line-clamp-2 rounded-lg bg-gray-50 p-2 text-gray-500 italic">
                      "{c.notes}"
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-5 border-t border-gray-100 pt-3">
                <button
                  type="button"
                  onClick={() => handleOpenHistory(c)}
                  className="flex w-full items-center justify-center rounded-xl bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-colors"
                >
                  रिपेयर इतिहास देखें (View History) →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Customer Details & History Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">{selectedCustomer.name}</h2>
                <p className="text-xs text-gray-500">
                  फ़ोन: <a href={`tel:${selectedCustomer.phone}`} className="text-indigo-600 underline">{selectedCustomer.phone}</a>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedCustomer(null)}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-800">
                रिपेयर टिकट्स ({selectedCustomer.tickets?.length || 0})
              </h3>

              {selectedCustomer.tickets?.length === 0 ? (
                <p className="mt-3 text-xs text-gray-400">इस ग्राहक के लिए कोई पिछला टिकट दर्ज नहीं है।</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {selectedCustomer.tickets?.map((t) => (
                    <div
                      key={t.id}
                      className="rounded-xl border border-gray-200 p-3.5 hover:border-indigo-300 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-indigo-600">{t.ticket_number}</span>
                        <StatusBadge status={t.status} />
                      </div>
                      <p className="mt-1 text-sm font-medium text-gray-900">{t.device_description}</p>
                      {t.reported_problem && (
                        <p className="mt-0.5 text-xs text-gray-500">समस्या: {t.reported_problem}</p>
                      )}
                      <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
                        <span>दिनांक: {formatDate(t.created_at)}</span>
                        {t.estimated_cost != null && (
                          <span className="font-semibold text-gray-700">₹{t.estimated_cost}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-6 border-t border-gray-100 pt-3 text-right">
              <button
                type="button"
                onClick={() => setSelectedCustomer(null)}
                className="rounded-xl bg-gray-100 px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-200"
              >
                बंद करें (Close)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
