import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, ShieldCheck, Microscope, Cpu, Users, Briefcase } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAppStore } from '../store/appStore';
import { useThemeStore } from '../store/themeStore';
import { fetchFunds } from '../services/tradeService';
import './Sidebar.css';

const TABS = [
  { name: 'TRADING', path: '/trading', icon: Activity },
  { name: 'COMPLIANCE', path: '/compliance', icon: ShieldCheck },
  { name: 'RESEARCH', path: '/research', icon: Microscope },
  { name: 'TECHNOLOGY', path: '/technology', icon: Cpu },
  { name: 'ADVISORY', path: '/advisory', icon: Users },
  { name: 'SALES', path: '/sales', icon: Briefcase },
];

export default function Sidebar() {
  const { selectedFund, globalDate, setSelectedFund, setGlobalDate } = useAppStore();
  const { theme } = useThemeStore();
  const [funds, setFunds] = useState<any[]>([]);

  useEffect(() => {
    fetchFunds().then((data) => {
      setFunds(data);
      if (data.length > 0 && !useAppStore.getState().selectedFund) {
        useAppStore.getState().setSelectedFund(data[0].id_f || data[0].id);
      }
    });
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-header" style={{ padding: '20px', display: 'flex', justifyContent: 'center' }}>
        <img
          src={theme === 'light' || theme === 'white' ? '/heroics_aegis_logo.png' : '/heroics_aegis_logo_white.png'}
          alt="AEGIS Logo"
          style={{ height: '32px', objectFit: 'contain' }}
        />
      </div>

      <div className="sidebar-filters">
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
              <option key={f.id_f || f.id} value={f.id_f || f.id}>{f.name}</option>
            ))}
          </select>
        </div>
      </div>

      <nav className="nav-menu">
        {TABS.map((tab) => (
          <NavLink
            key={tab.name}
            to={tab.path}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <tab.icon size={20} className="nav-icon" />
            <span className="nav-text">{tab.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <ThemeToggle />
      </div>
    </aside>
  );
}
