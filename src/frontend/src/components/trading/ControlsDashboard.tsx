import { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useThemeStore } from '../../store/themeStore';
import { useAppStore } from '../../store/appStore';
import { fetchFundControls, type ControlLevel, type ControlDefinition, type RiskCategory } from '../../services/riskService';
import './RiskDashboard.css';

export default function ControlsDashboard() {
  const { theme } = useThemeStore();
  const { selectedFund, globalDate } = useAppStore();
  
  const [loading, setLoading] = useState(false);
  const [controlsCache, setControlsCache] = useState<ControlLevel[]>([]);
  const [activeTab, setActiveTab] = useState<string>('');

  const isDark = theme !== 'light' && theme !== 'white'; 
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

  useEffect(() => {
    if (!selectedFund) return;
    
    let isMounted = true;
    setLoading(true);
    
    fetchFundControls(selectedFund).then(data => {
      if (!isMounted) return;
      setControlsCache(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      if (isMounted) setLoading(false);
    });
    
    return () => { isMounted = false; };
  }, [selectedFund]);

  // Grouping logic: map RiskCategory name to its Definition & associated Levels
  const groupedData = useMemo(() => {
    const map = new Map<string, { category: RiskCategory, controls: Map<number, { definition: ControlDefinition, levels: ControlLevel[] }> }>();
    
    (controlsCache || []).forEach(level => {
      const def = level?.control_definitions;
      if (!def) return;
      const cat = def.risk_categories;
      if (!cat) return;
      
      const catName = cat.name;
      if (!map.has(catName)) {
        map.set(catName, { category: cat, controls: new Map() });
      }
      
      const catGroup = map.get(catName)!;
      if (!catGroup.controls.has(def.id_control)) {
        catGroup.controls.set(def.id_control, { definition: def, levels: [] });
      }
      
      catGroup.controls.get(def.id_control)!.levels.push(level);
    });
    
    return map;
  }, [controlsCache]);

  const tabs = Array.from(groupedData.keys());
  
  // Auto-select first tab
  useEffect(() => {
    if (tabs.length > 0 && !tabs.includes(activeTab)) {
      setActiveTab(tabs[0]);
    }
  }, [tabs, activeTab]);

  return (
    <div className="risk-container fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="header-titles">
        <h2>Regulatory Controls</h2>
        <p>Monitor limits, market exposure, and compliance checks.</p>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading controls for fund...
        </div>
      ) : tabs.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No risk controls implemented for this fund.
        </div>
      ) : (
        <>
          {/* Dynamic Tabs */}
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', overflowX: 'auto' }}>
            {tabs.map(tab => (
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
                  flexShrink: 0,
                  transition: 'all 0.2s'
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            {activeTab && groupedData.has(activeTab) && Array.from(groupedData.get(activeTab)!.controls.values()).map(({ definition, levels }) => (
              <div key={definition.id_control} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                
                {/* Section 1: Header */}
                <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '20px', color: 'var(--text-primary)' }}>
                    {groupedData.get(activeTab)!.category.name} - {definition.name} ({definition.code})
                  </h3>
                  <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
                    {definition.description}
                  </p>
                </div>

                {/* Section 2: Monitoring Levels */}
                <div>
                  <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)' }}>
                    Monitored Thresholds ({definition.unit})
                  </h4>
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    {levels.sort((a, b) => a.level_rank - b.level_rank).map(lvl => (
                      <div key={lvl.id_level} style={{ padding: '8px 16px', background: 'var(--bg-tertiary)', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '14px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', marginRight: '8px' }}>{lvl.level_name.toUpperCase()}:</span>
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {lvl.side === 'left' ? `x <= ${lvl.upper_bound}` : lvl.side === 'right' ? `x >= ${lvl.lower_bound}` : `${lvl.lower_bound} ${lvl.lower_inclusive ? '<=' : '<'} x ${lvl.upper_inclusive ? '<=' : '<'} ${lvl.upper_bound}`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sections 3 & 4: Visuals & Metrics Table */}
                <div style={{ display: 'flex', gap: '24px', marginTop: '8px', flexWrap: 'wrap' }}>
                  {/* Left Chart */}
                  <div style={{ flex: '1 1 400px', minWidth: '300px', height: '300px', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
                    <Plot
                      data={[
                        {
                          x: ['2026-03-20', '2026-03-21', '2026-03-22', '2026-03-23', '2026-03-24'],
                          y: [Math.random() * 100, Math.random() * 100, Math.random() * 100, Math.random() * 100, Math.random() * 100],
                          type: 'scatter',
                          mode: 'lines+markers',
                          marker: { color: 'var(--accent-color)' },
                          line: { shape: 'spline', color: 'var(--accent-color)', width: 3 },
                          name: definition.code
                        },
                      ]}
                      layout={{ ...layoutTpl, height: 300, autosize: true, margin: { l: 40, r: 20, t: 20, b: 40 } }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                    />
                  </div>

                  {/* Right Metrics Table */}
                  <div style={{ flex: '1 1 400px', minWidth: '300px' }}>
                     <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                       <thead>
                         <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>Date</th>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>Value</th>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>1D Var</th>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>1W Var</th>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>1M Var</th>
                           <th style={{ padding: '12px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>Inception</th>
                         </tr>
                       </thead>
                       <tbody>
                         <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                           <td style={{ padding: '12px 8px', color: 'var(--text-primary)' }}>{globalDate || '2026-03-24'}</td>
                           <td style={{ padding: '12px 8px', color: 'var(--text-primary)', fontWeight: 700 }}>{(Math.random() * 100).toFixed(2)} {definition.unit}</td>
                           <td style={{ padding: '12px 8px', color: 'var(--success)' }}>+1.2%</td>
                           <td style={{ padding: '12px 8px', color: 'var(--danger)' }}>-0.5%</td>
                           <td style={{ padding: '12px 8px', color: 'var(--success)' }}>+4.1%</td>
                           <td style={{ padding: '12px 8px', color: 'var(--success)' }}>+12.0%</td>
                         </tr>
                       </tbody>
                     </table>
                     <div style={{ marginTop: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
                       <em>* Metric variables and historical graphics are mocked until data-pipelines are fully available.</em>
                     </div>
                  </div>
                </div>

              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
