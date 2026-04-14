import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, ShieldCheck, Microscope, Cpu, Users, Briefcase, ChevronLeft, ChevronRight } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAppStore } from '../store/appStore';
import { useThemeStore } from '../store/themeStore';
import { fetchFunds } from '../services/referenceService';
import type { Fund } from '../types/reference';
import './Sidebar.css';

const TABS = [
  { name: 'Trading', path: '/trading', icon: Activity },
  { name: 'Compliance', path: '/compliance', icon: ShieldCheck },
  { name: 'Research', path: '/research', icon: Microscope },
  { name: 'Technology', path: '/technology', icon: Cpu },
  { name: 'Advisory', path: '/advisory', icon: Users },
  { name: 'Sales', path: '/sales', icon: Briefcase },
];

export default function Sidebar() {
  const { selectedFund, globalDate, setSelectedFund, setGlobalDate } = useAppStore();
  const { theme } = useThemeStore();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    fetchFunds().then((data) => {
      setFunds(data);
      if (data.length > 0 && !useAppStore.getState().selectedFund) {
        useAppStore.getState().setSelectedFund(data[0].id_f);
      }
    });
  }, []);

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <button className="collapse-toggle" onClick={() => setIsCollapsed(!isCollapsed)}>
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      <div className="sidebar-header" style={{ padding: isCollapsed ? '24px 8px' : '24px', display: 'flex', justifyContent: 'center' }}>
        <img
          src={isCollapsed 
            ? (theme === 'light' || theme === 'white' ? '/heroics_aegis_log_nowords.png' : '/heroics_aegis_log_nowords_white.png')
            : (theme === 'light' || theme === 'white' ? '/heroics_aegis_logo.png' : '/heroics_aegis_logo_white.png')
          }
          alt="AEGIS Logo"
          style={{ height: isCollapsed ? '48px' : 'auto', width: isCollapsed ? 'auto' : '100%', maxHeight: '80px', objectFit: 'contain', transition: 'all 0.3s' }}
        />
      </div>

      <nav className="nav-menu">
        {TABS.map((tab) => (
          <NavLink
            key={tab.name}
            to={tab.path}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            title={isCollapsed ? tab.name : undefined}
          >
            <tab.icon size={20} className="nav-icon" />
            {!isCollapsed && <span className="nav-text">{tab.name}</span>}
          </NavLink>
        ))}
      </nav>

      {!isCollapsed && (
        <div className="sidebar-filters" style={{ marginTop: 'auto', borderBottom: 'none', borderTop: '1px solid var(--border-color)' }}>
          <div className="filter-group">
            <label>Date</label>
            <input
              type="date"
              value={globalDate}
              onChange={(e) => setGlobalDate(e.target.value)}
              className="sidebar-input"
            />
          </div>
          <div className="filter-group">
            <label>Fund</label>
            <select
              value={selectedFund || ''}
              onChange={(e) => setSelectedFund(parseInt(e.target.value))}
              className="sidebar-input"
            >
              {funds.map(f => (
                <option key={f.id_f} value={f.id_f}>{f.name}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <ThemeToggle />
      </div>
    </aside>
  );
}
