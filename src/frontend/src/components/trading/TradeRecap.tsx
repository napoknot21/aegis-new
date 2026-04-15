import { useState } from 'react';

import {
  bookTradeRecap as submitTradeRecapBooking,
  runTradeRecap as fetchTradeRecap,
  type TradeRecapRecord,
} from '../../services/recapService';

export default function TradeRecap() {
  const [data, setData] = useState<TradeRecapRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  const [reportDate, setReportDate] = useState('');
  const [tradeDate, setTradeDate] = useState('');

  const runTradeRecap = async () => {
    setLoading(true);
    setError(null);
    setIsEditing(false);
    try {
      const records = await fetchTradeRecap({
        reportDate,
        tradeDate,
      });
      setData(records);
    } catch (err) {
      setError(toErrorMessage(err, 'Error fetching trade recap data'));
    } finally {
      setLoading(false);
    }
  };

  const handleCellChange = (rowIndex: number, field: keyof TradeRecapRecord, value: string) => {
    const newData = [...data];
    newData[rowIndex] = { ...newData[rowIndex], [field]: value };
    // Auto-cast numerics if applicable
    if (field === 'Quantity' || field === 'Price') {
       newData[rowIndex][field] = Number(value) || 0;
    }
    setData(newData);
  };

  const bookTrades = async () => {
    setBooking(true);
    setError(null);
    try {
      const result = await submitTradeRecapBooking(data);
      alert(`Successfully booked ${result.booked_count} trades!`);
      setIsEditing(false);
    } catch (err) {
      setError(toErrorMessage(err, 'Error booking trades'));
    } finally {
      setBooking(false);
    }
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap', justifyContent: 'space-between' }}>
          
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
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
              disabled={loading || booking}
              style={{ padding: '10px 24px', height: 'fit-content', alignSelf: 'flex-end' }}
            >
              {loading ? 'Running...' : 'Run trade Recap'}
            </button>
          </div>

          {data.length > 0 && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                className="btn-secondary" 
                onClick={() => setIsEditing(!isEditing)}
                disabled={loading || booking}
                style={{ padding: '10px 24px', height: 'fit-content' }}
              >
                {isEditing ? 'Cancel Edit' : 'Edit Table'}
              </button>
              
              {isEditing && (
                <button 
                  className="btn-primary" 
                  onClick={bookTrades}
                  disabled={loading || booking}
                  style={{ padding: '10px 24px', height: 'fit-content', backgroundColor: 'var(--accent-color)' }}
                >
                  {booking ? 'Booking...' : 'Book Trades'}
                </button>
              )}
            </div>
          )}
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
                    <td style={{ padding: '4px 12px', color: 'var(--text-primary)' }}>{row.TradeId}</td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-secondary)' }}>
                      {isEditing ? <input type="date" value={row.Date} onChange={e => handleCellChange(idx, 'Date', e.target.value)} style={{ width: '100%', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.Date}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-secondary)' }}>
                      {isEditing ? <input type="date" value={row.TradeDate} onChange={e => handleCellChange(idx, 'TradeDate', e.target.value)} style={{ width: '100%', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.TradeDate}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-primary)' }}>
                      {isEditing ? <input type="text" value={row.Portfolio} onChange={e => handleCellChange(idx, 'Portfolio', e.target.value)} style={{ width: '100%', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.Portfolio}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-secondary)' }}>
                      {isEditing ? <input type="text" value={row.ProductType} onChange={e => handleCellChange(idx, 'ProductType', e.target.value)} style={{ width: '100%', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.ProductType}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-primary)' }}>
                      {isEditing ? <input type="number" value={row.Quantity} onChange={e => handleCellChange(idx, 'Quantity', e.target.value)} style={{ width: '80px', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.Quantity.toLocaleString()}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-primary)' }}>
                      {isEditing ? <input type="number" step="0.0001" value={row.Price} onChange={e => handleCellChange(idx, 'Price', e.target.value)} style={{ width: '80px', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.Price.toFixed(4)}
                    </td>
                    
                    <td style={{ padding: '4px 12px', color: 'var(--text-secondary)' }}>
                      {isEditing ? <input type="text" value={row.Currency} onChange={e => handleCellChange(idx, 'Currency', e.target.value)} style={{ width: '60px', background: 'transparent', border: '1px solid var(--border-color)', color: 'inherit', padding: '4px' }}/> : row.Currency}
                    </td>
                    
                    <td style={{ padding: '4px 12px' }}>
                      {isEditing ? (
                        <select value={row.Status} onChange={e => handleCellChange(idx, 'Status', e.target.value)} style={{ width: '100%', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '4px' }}>
                          <option value="PENDING">PENDING</option>
                          <option value="SETTLED">SETTLED</option>
                          <option value="CANCELLED">CANCELLED</option>
                        </select>
                      ) : (
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
                      )}
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

function toErrorMessage(error: unknown, fallbackMessage: string): string {
  return error instanceof Error ? error.message : fallbackMessage;
}
