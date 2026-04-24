import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, ShieldCheck, Microscope, Cpu, Users, Briefcase, ChevronLeft, ChevronRight } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAppStore } from '../store/appStore';
import { useAuthStore } from '../store/authStore';
import { useThemeStore } from '../store/themeStore';
import { logout } from '../lib/authClient';
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
  const { selectedOrg, selectedFund, globalDate, setSelectedOrg, setSelectedFund, setGlobalDate } = useAppStore();
  const { isEnabled, account, session } = useAuthStore();
  const { theme } = useThemeStore();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const organisations = session?.orgs ?? [];

  useEffect(() => {
    if (selectedOrg === null) {
      setFunds([]);
      return;
    }

    fetchFunds({ idOrg: selectedOrg })
      .then((data) => {
        setFunds(data);
        if (data.length > 0) {
          const currentFund = useAppStore.getState().selectedFund;
          const matchingFund = data.find((item) => item.id_f === currentFund);
          if (!matchingFund) {
            useAppStore.getState().setSelectedFund(data[0].id_f);
          }
        } else {
          useAppStore.getState().setSelectedFund(null);
        }
      })
      .catch((error) => {
        console.error(error);
        setFunds([]);
        useAppStore.getState().setSelectedFund(null);
      });
  }, [selectedOrg]);

  useEffect(() => {
    if (selectedOrg !== null || session?.default_org_id === null || session?.default_org_id === undefined) {
      return;
    }

    setSelectedOrg(session.default_org_id);
  }, [selectedOrg, session?.default_org_id, setSelectedOrg]);

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
            <label>Organisation</label>
            <select
              value={selectedOrg || ''}
              onChange={(e) => setSelectedOrg(e.target.value ? Number.parseInt(e.target.value, 10) : null)}
              className="sidebar-input"
              disabled={organisations.length === 0}
            >
              {organisations.length > 0 && selectedOrg === null && (
                <option value="" disabled>
                  Select organisation
                </option>
              )}
              {organisations.length === 0 ? (
                <option value="">No access</option>
              ) : (
                organisations.map((org) => (
                  <option key={org.id_org} value={org.id_org}>
                    {org.org_name}
                  </option>
                ))
              )}
            </select>
          </div>
          <div className="filter-group">
            <label>Fund</label>
            <select
              value={selectedFund || ''}
              onChange={(e) => setSelectedFund(e.target.value ? Number.parseInt(e.target.value, 10) : null)}
              className="sidebar-input"
              disabled={selectedOrg === null || funds.length === 0}
            >
              {selectedOrg === null ? (
                <option value="">Select organisation first</option>
              ) : funds.length === 0 ? (
                <option value="">No funds available</option>
              ) : (
                funds.map((f) => (
                  <option key={f.id_f} value={f.id_f}>
                    {f.name}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        {!isCollapsed && isEnabled && account && (
          <div style={{ marginBottom: '12px', width: '100%', padding: '0 20px', boxSizing: 'border-box' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>Signed in</div>
            <div style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '8px', wordBreak: 'break-word' }}>
              {account.username}
            </div>
            <button
              type="button"
              onClick={() => {
                void logout();
              }}
              className="sidebar-input"
              style={{ cursor: 'pointer' }}
            >
              Log out
            </button>
          </div>
        )}
        <ThemeToggle />
      </div>
    </aside>
  );
}
