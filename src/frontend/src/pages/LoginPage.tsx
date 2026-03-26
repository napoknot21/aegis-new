import { useNavigate } from 'react-router-dom';
import { useThemeStore } from '../store/themeStore';
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export default function LoginPage() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const [quoteData, setQuoteData] = useState<{ quote: string; author: string } | null>(null);

  useEffect(() => {
    async function fetchQuote() {
      try {
        const { data, error } = await supabase
          .from('quotes')
          .select('quote, author');
        
        if (!error && data && data.length > 0) {
          const randomIndex = Math.floor(Math.random() * data.length);
          setQuoteData(data[randomIndex]);
        }
      } catch (err) {
        console.error('Error fetching quotes:', err);
      }
    }
    
    fetchQuote();
  }, []);

  const handleLogin = () => {
    navigate('/trading');
  };

  const isLight = theme === 'light' || theme === 'white';

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
          style={{ width: '100%', padding: '12px', fontSize: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
        >
          Sign in
        </button>
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
