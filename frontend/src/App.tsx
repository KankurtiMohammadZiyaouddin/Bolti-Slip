// src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/Dashboard/DashboardPage';
import NewTicketPage from './pages/NewTicket/NewTicketPage';
import TicketHistoryPage from './pages/TicketHistory/TicketHistoryPage';
import ReviewTicketPage from './pages/ReviewTicket/ReviewTicketPage';
import SettingsPage from './pages/Settings/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* Core Navigation Routes matching Stitch Specifications */}
        <Route path="/" element={<DashboardPage />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/new-ticket" element={<NewTicketPage />} />
        <Route path="/new" element={<Navigate to="/new-ticket" replace />} />
        <Route path="/tickets" element={<TicketHistoryPage />} />
        <Route path="/tickets/:id" element={<ReviewTicketPage />} />
        <Route path="/review-ticket" element={<ReviewTicketPage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
