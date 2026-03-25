import { useState } from 'react';
import Plot from 'react-plotly.js';
import { useThemeStore } from '../../store/themeStore';
import './RiskDashboard.css';

const TABS = [
  'Leverages',
  'VaR & SIMM',
  'Sensitivities',
  'P&L',
  'Counterparty',
  'Credit',
  'Operational',
  'ESG',
  'Breaches'
];

export default function ControlsDashboard() {
  const { theme } = useThemeStore();
  const [activeTab, setActiveTab] = useState(TABS[0]);
  
  const isDark = theme === 'dark';
  const fontColor = isDark ? '#9ca3af' : '#4b5563';
  const gridColor = isDark ? '#2e303a' : '#e5e7eb';
  const paperBg = 'rgba(0,0,0,0)'; 
  const plotBg = 'rgba(0,0,0,0)';   

  const layoutTpl = {
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: 'inherit' },
    margin: { l: 40, r: 20, t: 40, b: 40 },
    xaxis: { gridcolor: gridColor, zerolinecolor: gridColor },
    yaxis: { gridcolor: gridColor, zerolinecolor: gridColor }
  };

  return (
    <div className="risk-container fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="header-titles">
        <h2>Regulatory Controls</h2>
        <p>Monitor limits, market exposure, and compliance checks.</p>
      </div>

      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', overflowX: 'auto' }}>
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              background: activeTab === tab ? 'var(--bg-secondary)' : 'transparent',
              color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-secondary)',
              border: '1px solid',
              borderColor: activeTab === tab ? 'var(--border-hover)' : 'transparent',
              fontWeight: 500,
              flexShrink: 0
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="glass-panel" style={{ padding: '24px', minHeight: '400px' }}>
        <h3>{activeTab} Overview</h3>
        {activeTab === 'VaR & SIMM' && (
          <div className="charts-grid" style={{ marginTop: '20px' }}>
            <div className="chart-box">
              <Plot
                data={[
                  {
                    x: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    y: [100, 130, 110, 150, 140],
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: '#3b82f6' },
                    line: { shape: 'spline', color: '#3b82f6', width: 3 },
                  },
                ]}
                layout={{ ...layoutTpl, height: 300, autosize: true, title: { text: 'Historical VaR' } }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
            <div className="chart-box">
              <Plot
                data={[
                  {
                    x: ['Equities', 'FX', 'Rates', 'Commodities'],
                    y: [450, 200, 300, 150],
                    type: 'bar',
                    marker: { color: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'] }
                  },
                ]}
                layout={{ ...layoutTpl, height: 300, autosize: true, title: { text: 'SIMM Exposure' } }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>
        )}

        {activeTab !== 'VaR & SIMM' && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '300px', color: 'var(--text-muted)' }}>
            Data for {activeTab} is currently being aggregated...
          </div>
        )}
      </div>
    </div>
  );
}
