import { useState } from 'react';

interface TradeRecord {
  TradeId: string;
  Portfolio: string;
  ProductType: string;
  Quantity: number;
  Price: number;
  Currency: string;
  Status: string;
  Date: string;
  TradeDate: string;
}

export default function TradeRecap() {
  const [data, setData] = useState<TradeRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [reportDate, setReportDate] = useState('');
  const [tradeDate, setTradeDate] = useState('');

  const runTradeRecap = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (reportDate) params.append('date', reportDate);
      if (tradeDate) params.append('trade_date', tradeDate);

      const qs = params.toString() ? `?${params.toString()}` : '';
      const response = await fetch(`http://localhost:8000/api/v1/recap/run${qs}`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      
      const json = await response.json();
      if (json.records) {
        setData(json.records);
      } else {
         setData([]);
      }
    } catch (err: any) {
      setError(err.message || 'Error fetching trade recap data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Report Date (Optional)</label>
            <input 
              type="date"
              value={reportDate}
              onChange={(e) => setReportDate(e.target.value)}
              className="input-field"
              style={{ padding: '8px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-primary)' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>Trade Date (Optional)</label>
            <input 
              type="date"
              value={tradeDate}
              onChange={(e) => setTradeDate(e.target.value)}
              className="input-field"
              style={{ padding: '8px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-primary)' }}
            />
          </div>

          <button 
            className="btn-primary" 
            onClick={runTradeRecap}
            disabled={loading}
            style={{ padding: '10px 24px', height: 'fit-content' }}
          >
            {loading ? 'Running...' : 'Run trade Recap'}
          </button>
        </div>

        {error && (
          <div style={{ color: '#ef4444', padding: '16px', background: '#fee2e2', borderRadius: '4px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <div className="glass-panel" style={{ padding: '24px', overflowX: 'auto' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, margin: '0 0 16px 0' }}>Recap Data</h2>
          
          {data.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Trade ID</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Date</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Trade Date</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Portfolio</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Product Type</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Quantity</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Price</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Currency</th>
                  <th style={{ padding: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px', color: 'var(--text-primary)' }}>{row.TradeId}</td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{row.Date}</td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{row.TradeDate}</td>
                    <td style={{ padding: '12px', color: 'var(--text-primary)' }}>{row.Portfolio}</td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{row.ProductType}</td>
                    <td style={{ padding: '12px', color: 'var(--text-primary)' }}>{row.Quantity.toLocaleString()}</td>
                    <td style={{ padding: '12px', color: 'var(--text-primary)' }}>{row.Price.toFixed(4)}</td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{row.Currency}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        fontSize: '12px', 
                        fontWeight: 600,
                        backgroundColor: row.Status === 'SETTLED' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(234, 179, 8, 0.1)',
                        color: row.Status === 'SETTLED' ? '#22c55e' : '#eab308'
                      }}>
                        {row.Status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
             <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '40px 0' }}>
               No trade data to display. Click "Run trade Recap" to fetch records.
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
