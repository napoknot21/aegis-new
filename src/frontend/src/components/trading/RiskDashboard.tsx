import Plot from 'react-plotly.js';
import { useThemeStore } from '../../store/themeStore';
import './RiskDashboard.css';

export default function RiskDashboard() {
  const { theme } = useThemeStore();
  
  // Dynamicly adapt plotly to the CSS theme variables manually, 
  // since Plotly draws within canvas/SVG and relies on fixed colors.
  const isDark = theme === 'dark';
  const fontColor = isDark ? '#9ca3af' : '#4b5563';
  const gridColor = isDark ? '#2e303a' : '#e5e7eb';
  const paperBg = 'rgba(0,0,0,0)'; // transparent
  const plotBg = 'rgba(0,0,0,0)';   // transparent

  const layoutTpl = {
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: 'inherit' },
    margin: { l: 40, r: 20, t: 40, b: 40 },
    xaxis: { gridcolor: gridColor, zerolinecolor: gridColor },
    yaxis: { gridcolor: gridColor, zerolinecolor: gridColor }
  };

  return (
    <div className="risk-container fade-in">
      <div className="header-titles">
        <h2>Risk & Exposure</h2>
        <p>Real-time analytics for portfolio risk limits and market exposure.</p>
      </div>

      <div className="charts-grid">
        <div className="glass-panel chart-box">
          <h3>Market Value (Historical)</h3>
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
            layout={{ ...layoutTpl, height: 300, width: undefined, autosize: true }}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
          />
        </div>

        <div className="glass-panel chart-box">
          <h3>Exposure by Asset Class</h3>
          <Plot
            data={[
              {
                x: ['Equities', 'FX', 'Rates', 'Commodities'],
                y: [450, 200, 300, 150],
                type: 'bar',
                marker: { color: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'] }
              },
            ]}
            layout={{ ...layoutTpl, height: 300, width: undefined, autosize: true }}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      </div>

      <div className="glass-panel risk-limits">
        <h3>Current Limits</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Desk</th>
              <th>Current Utilization</th>
              <th>Max Limit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>G10 FX Spot</td>
              <td>$4,500,000</td>
              <td>$10,000,000</td>
              <td><span className="badge" style={{ color: 'var(--success)' }}>45%</span></td>
            </tr>
            <tr>
              <td>US Rates Swap</td>
              <td>$22,000,000</td>
              <td>$25,000,000</td>
              <td><span className="badge" style={{ color: 'var(--warning)' }}>88%</span></td>
            </tr>
            <tr>
              <td>EM Equities</td>
              <td>$8,000,000</td>
              <td>$5,000,000</td>
              <td><span className="badge" style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }}>160% (Breach)</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
