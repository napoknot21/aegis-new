import { NavLink } from 'react-router-dom';

const SUB_TABS = [
  { name: 'Booker', path: 'booker' },
  { name: 'Data Viewer', path: 'viewer' },
  { name: 'Checker', path: 'checker' },
  { name: 'Controls', path: 'controls' },
  { name: 'Recap', path: 'recap' },
];

export default function TopNav() {
  return (
    <nav style={{
      display: 'flex',
      gap: '8px',
      padding: '0 40px',
      borderBottom: '1px solid var(--border-color)',
      backgroundColor: 'var(--bg-primary)',
      alignItems: 'center',
      minHeight: '60px'
    }}>
      {SUB_TABS.map((tab) => (
        <NavLink 
          key={tab.name}
          to={`/trading/${tab.path}`}
          style={({ isActive }) => ({
            textDecoration: 'none',
            fontSize: '14px',
            fontWeight: 500,
            color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
            padding: '12px 16px',
            borderBottom: isActive ? '2px solid var(--accent-color)' : '2px solid transparent',
            transition: 'all 0.2s ease'
          })}
        >
          {({ isActive }) => (
            <span style={{ opacity: isActive ? 1 : 0.8 }}>{tab.name}</span>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
