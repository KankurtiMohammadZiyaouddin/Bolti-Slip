// src/components/AudioPlayer.tsx
// Simple audio player that accepts a Blob URL or object URL

interface Props {
  url: string;
  label?: string;
}

export default function AudioPlayer({ url, label = 'रिकॉर्डिंग सुनें' }: Props) {
  return (
    <div style={{ marginTop: '0.75rem' }}>
      {label && <p style={{ fontSize: '.85rem', color: 'var(--color-muted)', marginBottom: '.25rem' }}>{label}</p>}
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio controls src={url} style={{ width: '100%' }} />
    </div>
  );
}
