import { useNavigate } from 'react-router-dom';
import { useThemeStore } from '../store/themeStore';

const QUOTES = [
  "Risk comes from not knowing what you're doing.",
  "The four most dangerous words in investing are: 'This time it's different'.",
  "In investing, what is comfortable is rarely profitable.",
  "Price is what you pay. Value is what you get.",
  "The stock market is a device for transferring money from the impatient to the patient."
];

export default function LoginPage() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();

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
          style={{ height: '120px', objectFit: 'contain', marginBottom: '24px' }}
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

      <div style={{ position: 'absolute', bottom: '10%', width: '100vw', overflow: 'hidden', padding: '16px 0', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', opacity: 0.8 }}>
        <div 
          style={{ 
            display: 'flex',
            width: 'max-content',
            animation: 'marquee 40s linear infinite'
          }}
        >
          {[...QUOTES, ...QUOTES, ...QUOTES, ...QUOTES].map((quote, idx) => (
            <div key={idx} style={{ flex: '0 0 auto', padding: '0 60px', color: 'var(--text-secondary)', fontSize: '14px', letterSpacing: '2px', fontWeight: 500, textTransform: 'uppercase' }}>
              &ldquo;{quote}&rdquo;
            </div>
          ))}
        </div>
      </div>
      
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
