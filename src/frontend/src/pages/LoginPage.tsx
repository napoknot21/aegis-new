import { useNavigate } from 'react-router-dom';
import { useThemeStore } from '../store/themeStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();

  const handleLogin = () => {
    navigate('/trading');
  };

  const isLight = theme === 'light' || theme === 'white';

  return (
    <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
      <div className="glass-panel fade-in" style={{ padding: '48px', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '400px' }}>
        <img
          src={isLight ? '/heroics_aegis_logo.png' : '/heroics_aegis_logo_white.png'}
          alt="AEGIS Logo"
          style={{ height: '120px', objectFit: 'contain', marginBottom: '24px' }}
        />
        <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: 600 }}>AEGIS System</h2>
        <p style={{ margin: '0 0 32px 0', color: 'var(--text-secondary)', textAlign: 'center' }}>Hedge Fund Management & Controls</p>
        
        <button 
          onClick={handleLogin}
          className="btn-primary" 
          style={{ width: '100%', padding: '12px', fontSize: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
        >
          Sign in
        </button>
      </div>
    </div>
  );
}
