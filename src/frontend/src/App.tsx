import { useEffect, type ReactNode } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TradingDashboard from './pages/TradingDashboard';
import PlaceholderPage from './pages/PlaceholderPage';
import LoginPage from './pages/LoginPage';
import { fetchCurrentSession } from './services/systemService';
import { useAuthStore } from './store/authStore';
import { useAppStore } from './store/appStore';

function FullScreenMessage({ title, description }: { title: string; description: string }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)',
        padding: '24px',
        textAlign: 'center',
      }}
    >
      <h2 style={{ margin: '0 0 12px 0' }}>{title}</h2>
      <p style={{ margin: 0, color: 'var(--text-secondary)', maxWidth: '560px' }}>{description}</p>
    </div>
  );
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isEnabled, isInitializing, isAuthenticated, sessionStatus, session, error } = useAuthStore();

  if (isInitializing || (isEnabled && isAuthenticated && sessionStatus === 'loading')) {
    return (
      <FullScreenMessage
        title="Checking session"
        description="Aegis is validating your Microsoft Entra session and loading your organisation access."
      />
    );
  }

  if (isEnabled && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (isEnabled && sessionStatus === 'error') {
    return (
      <FullScreenMessage
        title="Access not ready"
        description={error ?? 'Your identity was accepted, but the backend could not resolve your application access.'}
      />
    );
  }

  if (isEnabled && sessionStatus === 'ready' && session && session.orgs.length === 0) {
    return (
      <FullScreenMessage
        title="No organisation access"
        description="Your Microsoft account is authenticated, but no active Aegis organisation membership was found in the application database."
      />
    );
  }

  return <>{children}</>;
}

function App() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/' || location.pathname === '/login';
  const {
    isEnabled,
    isAuthenticated,
    session,
    sessionStatus,
    startSessionLoading,
    setSession,
    setError,
    clearSession,
  } = useAuthStore();

  useEffect(() => {
    if (!isEnabled) {
      clearSession();
      return;
    }

    if (!isAuthenticated) {
      clearSession();
      return;
    }

    if (session || sessionStatus === 'loading') {
      return;
    }

    let isMounted = true;
    startSessionLoading();

    fetchCurrentSession()
      .then((currentSession) => {
        if (!isMounted) {
          return;
        }

        setSession(currentSession);

        const selectedOrg = currentSession.default_org_id;
        if (selectedOrg !== null) {
          useAppStore.getState().setSelectedOrg(selectedOrg);
        }
      })
      .catch((error) => {
        if (!isMounted) {
          return;
        }

        const message =
          error instanceof Error ? error.message : 'Unable to resolve the authenticated user session.';
        setError(message);
      });

    return () => {
      isMounted = false;
    };
  }, [clearSession, isAuthenticated, isEnabled, session, sessionStatus, setError, setSession, startSessionLoading]);

  return (
    <>
      {!isLoginPage && <Sidebar />}
      <main style={{ flex: 1, overflowY: 'auto', backgroundColor: 'var(--bg-primary)' }}>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route
            path="/trading/*"
            element={
              <ProtectedRoute>
                <TradingDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/compliance"
            element={
              <ProtectedRoute>
                <PlaceholderPage title="COMPLIANCE" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research"
            element={
              <ProtectedRoute>
                <PlaceholderPage title="RESEARCH" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/technology"
            element={
              <ProtectedRoute>
                <PlaceholderPage title="TECHNOLOGY" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/advisory"
            element={
              <ProtectedRoute>
                <PlaceholderPage title="ADVISORY" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sales"
            element={
              <ProtectedRoute>
                <PlaceholderPage title="SALES" />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  );
}

export default App;
