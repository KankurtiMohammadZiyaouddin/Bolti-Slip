// src/components/TicketForm.tsx
import { useState, useEffect, type FormEvent } from 'react';
import { createTicket } from '../api/client';
import type { Ticket, TicketCreate } from '../types/ticket';

interface Props {
  initialTranscript?: string;
  onTicketCreated?: (ticket: Ticket) => void;
}

export default function TicketForm({ initialTranscript = '', onTicketCreated }: Props) {
  const [deviceDescription, setDeviceDescription] = useState(initialTranscript);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [reportedProblem, setReportedProblem] = useState('');
  const [repairInstructions, setRepairInstructions] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialTranscript) {
      setDeviceDescription(initialTranscript);
    }
  }, [initialTranscript]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!deviceDescription.trim()) {
      setError('उपकरण का विवरण आवश्यक है।');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: TicketCreate = {
      device_description: deviceDescription.trim(),
      customer_name: customerName.trim() || undefined,
      customer_phone: customerPhone.trim() || undefined,
      reported_problem: reportedProblem.trim() || undefined,
      repair_instructions: repairInstructions.trim() || undefined,
      expected_delivery: expectedDelivery.trim() || undefined,
      estimated_cost: estimatedCost ? parseFloat(estimatedCost) : undefined,
      transcript_raw: initialTranscript || undefined,
    };

    try {
      const ticket = await createTicket(payload);
      // Reset form
      setDeviceDescription('');
      setCustomerName('');
      setCustomerPhone('');
      setReportedProblem('');
      setRepairInstructions('');
      setExpectedDelivery('');
      setEstimatedCost('');
      if (onTicketCreated) {
        onTicketCreated(ticket);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'टिकट बनाने में विफल।');
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    width: '100%',
    padding: '.6rem .75rem',
    borderRadius: 'var(--radius)',
    border: '1px solid var(--color-border)',
    fontSize: '.95rem',
    marginTop: '.25rem',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '.85rem',
    fontWeight: 600,
    color: 'var(--color-text)',
    marginBottom: '.75rem',
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '.5rem' }}>
        📝 नई रिपेयर पर्ची बनाएं
      </h3>

      {error && (
        <div style={{ color: 'var(--color-danger)', background: '#ffebee', padding: '.6rem', borderRadius: 'var(--radius)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <label style={labelStyle}>
          ग्राहक का नाम
          <input
            type="text"
            placeholder="उदा. रमेश कुमार"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          फ़ोन नंबर
          <input
            type="tel"
            placeholder="उदा. 9876543210"
            value={customerPhone}
            onChange={(e) => setCustomerPhone(e.target.value)}
            style={inputStyle}
          />
        </label>
      </div>

      <label style={labelStyle}>
        उपकरण का विवरण / ट्रांसक्रिप्ट *
        <textarea
          rows={3}
          placeholder="उदा. Mixer Grinder (बटन नहीं चल रहा)"
          value={deviceDescription}
          onChange={(e) => setDeviceDescription(e.target.value)}
          required
          style={{ ...inputStyle, resize: 'vertical' }}
        />
      </label>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <label style={labelStyle}>
          समस्या (Problem)
          <input
            type="text"
            placeholder="उदा. मोटर बंद है / तार जल गया"
            value={reportedProblem}
            onChange={(e) => setReportedProblem(e.target.value)}
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          रिपेयर निर्देश (Repair Instructions)
          <input
            type="text"
            placeholder="उदा. नया स्विच लगाएं"
            value={repairInstructions}
            onChange={(e) => setRepairInstructions(e.target.value)}
            style={inputStyle}
          />
        </label>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <label style={labelStyle}>
          अपेक्षित डिलीवरी (Expected Date)
          <input
            type="date"
            value={expectedDelivery}
            onChange={(e) => setExpectedDelivery(e.target.value)}
            style={inputStyle}
          />
        </label>

        <label style={labelStyle}>
          अनुमानित लागत (₹)
          <input
            type="number"
            min="0"
            step="any"
            placeholder="उदा. 350"
            value={estimatedCost}
            onChange={(e) => setEstimatedCost(e.target.value)}
            style={inputStyle}
          />
        </label>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
        <button type="submit" className="btn-primary" disabled={loading} style={{ minWidth: '150px' }}>
          {loading ? 'बनाया जा रहा है…' : '✔ पर्ची जनरेट करें'}
        </button>
      </div>
    </form>
  );
}
