// src/App.tsx
import { Routes, Route, Link, NavLink } from 'react-router-dom';
import HomePage from './pages/HomePage';
import TicketListPage from './pages/TicketListPage';
import TicketDetailPage from './pages/TicketDetailPage';

export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar */}
      <nav
        style={{
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow)',
          padding: '0.75rem 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <Link
          to="/"
          style={{
            fontSize: '1.25rem',
            fontWeight: 'bold',
            color: 'var(--color-primary)',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '.5rem',
          }}
        >
          <span>🎙️</span>
          <span>बोलती स्लिप</span>
          <span style={{ fontSize: '.8rem', color: 'var(--color-muted)', fontWeight: 'normal' }}>
            Bolti Slip
          </span>
        </Link>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <NavLink
            to="/"
            end
            style={({ isActive }) => ({
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '.95rem',
              color: isActive ? 'var(--color-primary)' : 'var(--color-muted)',
              borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
              paddingBottom: '.25rem',
            })}
          >
            ➕ नई पर्ची (New)
          </NavLink>

          <NavLink
            to="/tickets"
            style={({ isActive }) => ({
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '.95rem',
              color: isActive ? 'var(--color-primary)' : 'var(--color-muted)',
              borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
              paddingBottom: '.25rem',
            })}
          >
            📋 पर्चियां (History)
          </NavLink>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, paddingBottom: '2rem' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/tickets" element={<TicketListPage />} />
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer
        style={{
          textAlign: 'center',
          padding: '1rem',
          borderTop: '1px solid var(--color-border)',
          color: 'var(--color-muted)',
          fontSize: '.85rem',
          background: 'var(--color-surface)',
        }}
      >
        बोलती स्लिप • Voice-Powered Repair Slip • Gnani Prisma v3.0 STT & Timbre v3.0 TTS
      </footer>
    </div>
  );
}
