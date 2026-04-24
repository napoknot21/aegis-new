import { useNavigate } from 'react-router-dom';
import { useThemeStore } from '../store/themeStore';
import { useState, useEffect } from 'react';
import { fetchLoginQuote, type LoginQuote } from '../services/systemService';
import { login } from '../lib/authClient';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const [quoteData, setQuoteData] = useState<LoginQuote | null>(null);
  const { isEnabled, isAuthenticated, isInitializing, sessionStatus, session, error, account } = useAuthStore();

  useEffect(() => {
    let isMounted = true;

    async function fetchQuote() {
      try {
        const quote = await fetchLoginQuote();
        if (isMounted) {
          setQuoteData(quote);
        }
      } catch (err) {
        console.error('Error fetching quotes:', err);
      }
    }

    fetchQuote();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isEnabled && !isInitializing) {
      return;
    }

    if (isAuthenticated && sessionStatus === 'ready' && session && session.orgs.length > 0) {
      navigate('/trading', { replace: true });
    }
  }, [isAuthenticated, isEnabled, isInitializing, navigate, session, sessionStatus]);

  const handleLogin = async () => {
    if (!isEnabled) {
      navigate('/trading');
      return;
    }

    await login();
  };

  const isLight = theme === 'light' || theme === 'white';
  const signInLabel = isEnabled ? 'Sign in with Microsoft' : 'Enter Aegis';

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      <div className="glass-panel fade-in" style={{ padding: '48px', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '400px', zIndex: 10 }}>
        <img
          src={isLight ? '/heroics_aegis_logo.png' : '/heroics_aegis_logo_white.png'}
          alt="AEGIS Logo"
          style={{ height: '120px', maxWidth: '100%', objectFit: 'contain', marginBottom: '24px' }}
        />
        <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: 600, color: 'var(--text-primary)' }}>AEGIS System</h2>
        <p style={{ margin: '0 0 32px 0', color: 'var(--text-secondary)', textAlign: 'center' }}>Hedge Fund Management & Controls</p>

        <button
          onClick={handleLogin}
          className="btn-primary"
          disabled={isInitializing}
          style={{ width: '100%', padding: '12px', fontSize: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', opacity: isInitializing ? 0.7 : 1 }}
        >
          {isInitializing ? 'Initializing...' : signInLabel}
        </button>

        {isEnabled && account && (
          <p style={{ margin: '16px 0 0 0', color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center' }}>
            Signed in as {account.username}
          </p>
        )}

        {error && (
          <p style={{ margin: '16px 0 0 0', color: '#dc2626', fontSize: '13px', textAlign: 'center' }}>
            {error}
          </p>
        )}
      </div>

      {quoteData && (
        <div style={{ position: 'absolute', bottom: '10%', width: '100vw', padding: '24px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', opacity: 0.85, zIndex: 5 }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '16px', fontStyle: 'italic', textAlign: 'center', maxWidth: '800px', lineHeight: 1.5 }}>
            &ldquo;{quoteData.quote}&rdquo;
          </div>
          <div style={{ marginTop: '12px', color: 'var(--text-primary)', fontSize: '13px', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase' }}>
            &mdash; {quoteData.author}
          </div>
        </div>
      )}
    </div>
  );
}
