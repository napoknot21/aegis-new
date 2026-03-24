import { Sun, Moon, Monitor } from 'lucide-react';
import { useThemeStore } from '../store/themeStore';

export default function ThemeToggle() {
  const { theme, setTheme } = useThemeStore();

  return (
    <div className="theme-toggle" style={{ display: 'flex', gap: '8px', padding: '12px' }}>
      <button 
        onClick={() => setTheme('dark')}
        style={{ color: theme === 'dark' ? 'var(--accent-color)' : 'var(--text-secondary)' }}
        title="Dark Theme"
      >
        <Moon size={18} />
      </button>
      <button 
        onClick={() => setTheme('light')}
        style={{ color: theme === 'light' ? 'var(--accent-color)' : 'var(--text-secondary)' }}
        title="Light Theme"
      >
        <Sun size={18} />
      </button>
      <button 
        onClick={() => setTheme('white')}
        style={{ color: theme === 'white' ? 'var(--accent-color)' : 'var(--text-secondary)' }}
        title="White Theme"
      >
        <Monitor size={18} />
      </button>
    </div>
  );
}
