import { Routes, Route, Navigate } from 'react-router-dom';
import TopNav from '../components/TopNav';
import TradeBooker from '../components/trading/TradeBooker';
import DataViewer from '../components/trading/DataViewer';
import TradeChecker from '../components/trading/TradeChecker';
import RiskDashboard from '../components/trading/RiskDashboard';

export default function TradingDashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <header style={{ padding: '32px 40px 16px', backgroundColor: 'var(--bg-primary)' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 500, margin: 0 }}>TRADING</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
          Manage your trade bookings, data review, validation, and risk limits.
        </p>
      </header>
      
      <TopNav />

      <div style={{ padding: '32px 40px', flex: 1, overflowY: 'auto' }}>
        <Routes>
          <Route path="/" element={<Navigate to="booker" replace />} />
          <Route path="booker" element={<TradeBooker />} />
          <Route path="viewer" element={<DataViewer />} />
          <Route path="checker" element={<TradeChecker />} />
          <Route path="risks" element={<RiskDashboard />} />
        </Routes>
      </div>
    </div>
  );
}
