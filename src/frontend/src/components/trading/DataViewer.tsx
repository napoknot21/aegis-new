import { useState, useEffect } from 'react';
import { Filter, Search, Download } from 'lucide-react';
import { fetchTrades } from '../../services/tradeService';
import { useAppStore } from '../../store/appStore';
import type { TradeSummary } from '../../types/trades';
import './DataViewer.css';

export default function DataViewer() {
  const { selectedOrg } = useAppStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [trades, setTrades] = useState<TradeSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (selectedOrg === null) {
      setTrades([]);
      setLoading(false);
      return;
    }

    const loadData = async () => {
      setLoading(true);
      try {
        const data = await fetchTrades(selectedOrg);
        setTrades(data ?? []);
      } catch (err) {
        console.error(err);
        setTrades([]);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [selectedOrg]);

  const filteredTrades = trades.filter(t => 
    String(t.id_spe).includes(searchTerm) ||
    String(t.id_trade).includes(searchTerm) ||
    t.type_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.status.toLowerCase().includes(searchTerm.toLowerCase())
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
              <th>SPE</th>
              <th>Trade ID</th>
              <th>Booked At</th>
              <th>Type</th>
              <th>Fund</th>
              <th className="number-col">Booked By</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="empty-state">Loading trades from backend...</td>
              </tr>
            ) : filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">No trades found matching your criteria.</td>
              </tr>
            ) : (
              filteredTrades.map((trade) => (
                <tr key={trade.id_trade}>
                  <td className="fw-500">{trade.id_spe}</td>
                  <td className="fw-500">{trade.id_trade}</td>
                  <td className="text-secondary">{new Date(trade.booked_at).toLocaleString()}</td>
                  <td><span className="badge">{trade.type_code}</span></td>
                  <td className="fw-500">{trade.id_f}</td>
                  <td className="number-col text-secondary">{trade.booked_by ?? 'N/A'}</td>
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
