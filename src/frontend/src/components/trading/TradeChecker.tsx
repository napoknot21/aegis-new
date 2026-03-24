import { CheckCircle, XCircle } from 'lucide-react';

export default function TradeChecker() {
  return (
    <div className="checker-container fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="header-titles">
        <h2>Trade Checker</h2>
        <p>Approve or reject trades pending authorization based on four-eyes principle.</p>
      </div>
      
      <div className="checker-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {[1, 2, 3].map((_, idx) => (
          <div key={idx} className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontWeight: 500 }}>TRD-109{idx + 7}</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Requires Compliance Approval - High Volume Warning</span>
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn-icon" style={{ color: 'var(--success)', borderColor: 'var(--border-color)' }}>
                <CheckCircle size={18} /> Approve
              </button>
              <button className="btn-icon" style={{ color: 'var(--danger)', borderColor: 'var(--border-color)' }}>
                <XCircle size={18} /> Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
