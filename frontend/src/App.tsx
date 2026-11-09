// src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './layouts/AppLayout';

import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import NewTicketPage from './pages/NewTicket/NewTicketPage';
import TicketHistoryPage from './pages/TicketHistory/TicketHistoryPage';
import ReviewTicketPage from './pages/ReviewTicket/ReviewTicketPage';
import CustomersPage from './pages/Customers/CustomersPage';
import SettingsPage from './pages/Settings/SettingsPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Authenticated Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="/new-ticket" element={<NewTicketPage />} />
            <Route path="/new" element={<Navigate to="/new-ticket" replace />} />
            <Route path="/tickets" element={<TicketHistoryPage />} />
            <Route path="/tickets/:id" element={<ReviewTicketPage />} />
            <Route path="/review-ticket" element={<ReviewTicketPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
