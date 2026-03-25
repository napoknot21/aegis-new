import { Routes, Route, Navigate } from 'react-router-dom';
// import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import Sidebar from './components/Sidebar';
import TradingDashboard from './pages/TradingDashboard';
import PlaceholderPage from './pages/PlaceholderPage';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <>
      <Sidebar />
      <main style={{ flex: 1, overflowY: 'auto', backgroundColor: 'var(--bg-primary)' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/trading" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/trading/*" element={<TradingDashboard />} />
          <Route path="/compliance" element={<PlaceholderPage title="COMPLIANCE" />} />
          <Route path="/research" element={<PlaceholderPage title="RESEARCH" />} />
          <Route path="/technology" element={<PlaceholderPage title="TECHNOLOGY" />} />
          <Route path="/advisory" element={<PlaceholderPage title="ADVISORY" />} />
          <Route path="/sales" element={<PlaceholderPage title="SALES" />} />
        </Routes>
      </main>
    </>
  );
}

export default App;
