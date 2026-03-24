import { useState, useEffect } from 'react';
import { Filter, Search, Download } from 'lucide-react';
import { fetchTrades } from '../../services/tradeService';
import type { Trade } from '../../services/tradeService';
import './DataViewer.css';

export default function DataViewer() {
  const [searchTerm, setSearchTerm] = useState('');
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchTrades();
        if (data && data.length > 0) {
          setTrades(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredTrades = trades.filter(t => 
    (t.instrument || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
    (t.id || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="viewer-container fade-in">
      <div className="viewer-header">
        <div className="header-titles">
          <h2>Trade Blotter</h2>
          <p>Review and filter all historical and intraday trades.</p>
        </div>
        
        <div className="header-actions">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search instrument or ID..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="btn-icon"><Filter size={18} /> Filter</button>
          <button className="btn-icon"><Download size={18} /> Export</button>
        </div>
      </div>

      <div className="table-wrapper glass-panel">
        <table className="data-table">
          <thead>
            <tr>
              <th>Trade ID</th>
              <th>Date</th>
              <th>Type</th>
              <th>Instrument</th>
              <th className="number-col">Quantity</th>
              <th className="number-col">Price</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="empty-state">Loading trades from Supabase...</td>
              </tr>
            ) : filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">No trades found matching your criteria.</td>
              </tr>
            ) : (
              filteredTrades.map((trade) => (
                <tr key={trade.id}>
                  <td className="fw-500">{trade.id}</td>
                  <td className="text-secondary">{trade.date}</td>
                  <td><span className="badge">{trade.type}</span></td>
                  <td className="fw-500">{trade.instrument}</td>
                  <td className="number-col text-secondary">{trade.qty}</td>
                  <td className="number-col fw-500">{trade.price}</td>
                  <td>
                    <span className={`status-dot ${trade.status.toLowerCase()}`}></span>
                    {trade.status}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
