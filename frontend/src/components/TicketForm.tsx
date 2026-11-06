// src/components/TicketForm.tsx
import { useState, useEffect, type FormEvent } from 'react';
import { createTicket } from '../api/client';
import type { ExtractionResult, Ticket, TicketCreate } from '../types/ticket';

interface Props {
  initialTranscript?: string;
  extractedFields?: ExtractionResult | null;
  onTicketCreated?: (ticket: Ticket) => void;
}

const FIELD_LABELS: Record<string, string> = {
  customer_name: 'ग्राहक का नाम (Customer Name)',
  customer_phone: 'फ़ोन नंबर (Phone Number)',
  device_description: 'उपकरण (Device)',
  reported_problem: 'समस्या (Problem)',
  repair_instructions: 'रिपेयर निर्देश (Instructions)',
  expected_delivery: 'डिलीवरी तारीख (Delivery Date)',
  estimated_cost: 'अनुमानित लागत (Cost)',
};

export default function TicketForm({ initialTranscript = '', extractedFields, onTicketCreated }: Props) {
  const [deviceDescription, setDeviceDescription] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [reportedProblem, setReportedProblem] = useState('');
  const [repairInstructions, setRepairInstructions] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-fill from extraction result or fallback to raw transcript
  useEffect(() => {
    if (extractedFields?.fields) {
      const f = extractedFields.fields;
      if (f.device_description) setDeviceDescription(f.device_description);
      else if (initialTranscript) setDeviceDescription(initialTranscript);

      if (f.reported_problem) setReportedProblem(f.reported_problem);
      if (f.expected_delivery) setExpectedDelivery(f.expected_delivery);
      if (f.estimated_cost != null) setEstimatedCost(String(f.estimated_cost));
      if (f.customer_phone) setCustomerPhone(f.customer_phone);
      if (f.customer_name) setCustomerName(f.customer_name);
      if (f.repair_instructions) setRepairInstructions(f.repair_instructions);
    } else if (initialTranscript) {
      setDeviceDescription(initialTranscript);
    }
  }, [extractedFields, initialTranscript]);

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
        📝 नई रिपेयर पर्ची बनाएं (Repair Ticket)
      </h3>

      {/* Raw voice transcript box if available */}
      {initialTranscript && (
        <div
          style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            padding: '.75rem',
            borderRadius: 'var(--radius)',
            marginBottom: '1rem',
            fontSize: '.9rem',
          }}
        >
          <strong style={{ color: 'var(--color-primary)' }}>🎙️ मूल आवाज़ ट्रांसक्रिप्ट:</strong>
          <p style={{ marginTop: '.25rem', color: 'var(--color-text)', fontStyle: 'italic' }}>
            "{initialTranscript}"
          </p>
        </div>
      )}

      {/* Confirmation warning if fields are ambiguous or inferred */}
      {extractedFields && extractedFields.needs_confirmation.length > 0 && (
        <div
          style={{
            background: '#fff8e1',
            border: '1px solid #ffe082',
            padding: '.75rem',
            borderRadius: 'var(--radius)',
            marginBottom: '1rem',
            fontSize: '.88rem',
            color: '#b78103',
          }}
        >
          <strong>⚠️ कृपया जाँचें (Please Confirm):</strong> निम्न जानकारी आवाज़ से अनुमानित की गई है, कृपया सही मान की पुष्टि करें:
          <ul style={{ marginLeft: '1.25rem', marginTop: '.35rem' }}>
            {extractedFields.needs_confirmation.map((field) => (
              <li key={field}>
                <strong>{FIELD_LABELS[field] || field}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing fields notification */}
      {extractedFields && extractedFields.missing_fields.length > 0 && (
        <div
          style={{
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            padding: '.6rem .75rem',
            borderRadius: 'var(--radius)',
            marginBottom: '1rem',
            fontSize: '.82rem',
            color: '#0369a1',
          }}
        >
          ℹ️ <strong>छूटी हुई जानकारी:</strong> आवाज़ में ये विवरण नहीं मिले, आप इन्हें नीचे मैन्युअल भर सकते हैं:{' '}
          {extractedFields.missing_fields.map((f) => FIELD_LABELS[f] || f).join(', ')}
        </div>
      )}

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
        उपकरण का विवरण (Device Description) *
        <textarea
          rows={2}
          placeholder="उदा. Mixer Grinder"
          value={deviceDescription}
          onChange={(e) => setDeviceDescription(e.target.value)}
          required
          style={{ ...inputStyle, resize: 'vertical' }}
        />
      </label>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        <label style={labelStyle}>
          समस्या (Reported Problem)
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
          अनुमानित लागत (Estimated Cost ₹)
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
