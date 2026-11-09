// src/pages/Settings/SettingsPage.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { changePassword } from '../../api/client';

export default function SettingsPage() {
  const { shop } = useAuth();
  const [shopName, setShopName] = useState(shop?.shop_name || 'Sharma Electronics');
  const [branchName, setBranchName] = useState(shop?.branch || 'Pune Branch');
  const [shopAddress, setShopAddress] = useState(shop?.address || 'Shop #4, Laxmi Road, Pune - 411030');
  const [shopPhone, setShopPhone] = useState(shop?.phone || '9822012345');
  const [sttModel] = useState('Gnani Prisma v3.0 (Indic-ASR)');
  const [ttsVoice, setTtsVoice] = useState('Devansh');
  const [saved, setSaved] = useState(false);

  // Password change state
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [pwdError, setPwdError] = useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null);
  const [isChangingPwd, setIsChangingPwd] = useState(false);

  useEffect(() => {
    if (shop) {
      if (shop.shop_name) setShopName(shop.shop_name);
      if (shop.branch) setBranchName(shop.branch);
      if (shop.address) setShopAddress(shop.address);
      if (shop.phone) setShopPhone(shop.phone);
    }
  }, [shop]);

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);

    if (!currentPwd.trim() || !newPwd.trim()) {
      setPwdError('कृपया वर्तमान और नया पासवर्ड दोनों दर्ज करें।');
      return;
    }

    if (newPwd.length < 6) {
      setPwdError('नया पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।');
      return;
    }

    if (newPwd !== confirmPwd) {
      setPwdError('नया पासवर्ड और पुष्टि पासवर्ड मेल नहीं खाते।');
      return;
    }

    setIsChangingPwd(true);
    try {
      const res = await changePassword(currentPwd, newPwd);
      setPwdSuccess(res.message || 'पासवर्ड सफलतापूर्वक बदल दिया गया। (Password changed successfully)');
      setCurrentPwd('');
      setNewPwd('');
      setConfirmPwd('');
    } catch (err: any) {
      setPwdError(err.message || 'पासवर्ड बदलने में त्रुटि। वर्तमान पासवर्ड जांचें।');
    } finally {
      setIsChangingPwd(false);
    }
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="flex flex-col w-full">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-sm mb-6">
        <div>
          <div className="flex items-center gap-space-xs text-secondary font-label-xs text-label-xs uppercase tracking-wider mb-1">
            <span>Workshop Console</span>
            <span>/</span>
            <span className="text-primary font-semibold">Settings</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">
            Settings
          </h1>
          <p className="font-body-md text-body-md text-secondary mt-1">
            Manage your workshop preferences, language models and Gnani audio configurations.
          </p>
        </div>

        <div className="flex items-center gap-space-sm">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-xs text-label-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Speech Services: Configured (Prisma v3.0 &amp; Timbre v3.0)
          </span>
        </div>
      </div>

      {saved && (
        <div className="p-4 mb-6 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 font-label-md flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px]">check_circle</span>
          <span>सेटिंग्स सफलतापूर्वक सहेजी गईं (Settings saved successfully).</span>
        </div>
      )}

      {/* Settings Form */}
      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (7 cols): Shop & Branch Profile */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <section className="bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-6">
            <div className="flex items-center gap-space-sm pb-4 mb-4 border-b border-outline-variant/60">
              <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[20px]">storefront</span>
              </div>
              <div>
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                  Shop &amp; Branch Profile
                </h2>
                <p className="font-label-xs text-label-xs text-secondary">
                  Displayed on customer physical repair slips and printed tags
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold">
                  Shop Name
                </label>
                <input
                  type="text"
                  value={shopName}
                  onChange={(e) => setShopName(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold">
                  Branch Name
                </label>
                <input
                  type="text"
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                  required
                />
              </div>

              <div className="sm:col-span-2 space-y-1.5">
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold">
                  Address / Location
                </label>
                <input
                  type="text"
                  value={shopAddress}
                  onChange={(e) => setShopAddress(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold">
                  Contact Phone
                </label>
                <input
                  type="tel"
                  value={shopPhone}
                  onChange={(e) => setShopPhone(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                  required
                />
              </div>
            </div>
          </section>
        </div>

        {/* Right Column (5 cols): Voice Engine & Audio Preferences */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <section className="bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-6">
            <div className="flex items-center gap-space-sm pb-4 mb-4 border-b border-outline-variant/60">
              <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[20px]">graphic_eq</span>
              </div>
              <div>
                <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                  Speech &amp; AI Engine
                </h2>
                <p className="font-label-xs text-label-xs text-secondary">
                  Gnani Prisma v3.0 STT &amp; Timbre v3.0 TTS
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold mb-1">
                  Speech Recognition Engine
                </label>
                <input
                  type="text"
                  readOnly
                  value={sttModel}
                  className="w-full h-10 px-3 bg-surface-container-low rounded-lg font-body-sm text-body-sm text-secondary border border-outline-variant cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block font-label-sm text-label-sm text-on-surface font-semibold mb-1">
                  Spoken Confirmation Voice (Timbre TTS)
                </label>
                <select
                  value={ttsVoice}
                  onChange={(e) => setTtsVoice(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
                >
                  <option value="Devansh">Devansh (Hindi Male)</option>
                  <option value="Kavya">Kavya (Hindi Female)</option>
                  <option value="Nikhil">Nikhil (Indian English)</option>
                </select>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-2.5 px-4 rounded-xl bg-primary-container hover:bg-primary text-on-primary font-label-md text-label-md shadow-sm transition-all cursor-pointer font-semibold"
                >
                  Save Settings (सेव करें)
                </button>
              </div>
            </div>
          </section>
        </div>
      </form>

      {/* Security & Password Change Section */}
      <section className="mt-8 bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-6 max-w-2xl">
        <div className="flex items-center gap-space-sm pb-4 mb-4 border-b border-outline-variant/60">
          <div className="w-9 h-9 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-[20px]">lock_reset</span>
          </div>
          <div>
            <h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              सुरक्षा और पासवर्ड सेटअप (Security &amp; Password)
            </h2>
            <p className="font-label-xs text-label-xs text-secondary">
              अपनी दुकान के अकाउंट का पासवर्ड सुरक्षित रूप से बदलें
            </p>
          </div>
        </div>

        {pwdSuccess && (
          <div className="p-3.5 mb-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
            <span>{pwdSuccess}</span>
          </div>
        )}

        {pwdError && (
          <div className="p-3.5 mb-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">error</span>
            <span>{pwdError}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block font-label-sm text-label-sm text-on-surface font-semibold mb-1">
              वर्तमान पासवर्ड (Current Password) *
            </label>
            <input
              type="password"
              required
              value={currentPwd}
              onChange={(e) => setCurrentPwd(e.target.value)}
              placeholder="••••••••"
              className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-label-sm text-label-sm text-on-surface font-semibold mb-1">
                नया पासवर्ड (New Password) *
              </label>
              <input
                type="password"
                required
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
                placeholder="कम से कम 6 अक्षर"
                className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
              />
            </div>

            <div>
              <label className="block font-label-sm text-label-sm text-on-surface font-semibold mb-1">
                नया पासवर्ड दोहराएं (Confirm Password) *
              </label>
              <input
                type="password"
                required
                value={confirmPwd}
                onChange={(e) => setConfirmPwd(e.target.value)}
                placeholder="••••••••"
                className="w-full h-10 px-3 bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface border border-outline-variant focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isChangingPwd}
              className="py-2.5 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-label-md text-label-md shadow-sm transition-all cursor-pointer font-semibold disabled:opacity-60"
            >
              {isChangingPwd ? 'बदला जा रहा है...' : 'पासवर्ड अपडेट करें (Update Password)'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
