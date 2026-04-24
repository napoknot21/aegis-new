import { useState, useEffect, type ChangeEvent, type FormEvent } from 'react';
import { fetchTradeFormReferences } from '../../services/referenceService';
import { bookTrade } from '../../services/tradeService';
import { useAppStore } from '../../store/appStore';
import type { AssetClass, Book, Counterparty, Currency, TradeLabel } from '../../types/reference';
import type { BuySell, DiscTradeCreatePayload, IceTradeStatus, OriginatingAction } from '../../types/trades';
import './TradeBooker.css';

export default function TradeBooker() {
  const { selectedFund, selectedOrg } = useAppStore();
  const activeOrgId = selectedOrg;

  const [formData, setFormData] = useState({
    // Trade Disc (General)
    ice_trade_id: '',
    external_id: '',
    trade_name: '',
    description: '',
    trade_date: useAppStore.getState().globalDate,
    id_book: '',
    id_portfolio: '',
    id_ctpy: '',
    id_label: '',
    volume: '',
    ice_status: '',
    originating_action: '',
    
    // Trade Disc Legs (Instruments)
    leg_id: '',
    id_ac: '',
    direction: '',
    notional: '',
    id_ccy: '',

    // Instrument (trade_disc_instruments)
    instrument_code: '',
    instrument_name: '',
    inst_id_ac: '',
    category: '',
    underlying: '',
    isin: '',
    bbg_ticker: '',

    // Premium (trade_disc_premiums)
    prem_amount: '',
    prem_id_ccy: '',
    prem_date: useAppStore.getState().globalDate,
    markup: '',
    total: ''
  });

  const [assetClasses, setAssetClasses] = useState<AssetClass[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [labels, setLabels] = useState<TradeLabel[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [portfolios, setPortfolios] = useState<Book[]>([]);
  const [counterparties, setCounterparties] = useState<Counterparty[]>([]);
  
  const [loadingRefs, setLoadingRefs] = useState(true);

  useEffect(() => {
    if (activeOrgId === null) {
      setAssetClasses([]);
      setCurrencies([]);
      setLabels([]);
      setBooks([]);
      setPortfolios([]);
      setCounterparties([]);
      setLoadingRefs(false);
      return;
    }

    const loadData = async () => {
      setLoadingRefs(true);
      try {
        const references = await fetchTradeFormReferences(activeOrgId);
        setAssetClasses(references.assetClasses);
        setCurrencies(references.currencies);
        setLabels(references.tradeLabels);
        setBooks(references.books);
        setPortfolios(references.portfolios);
        setCounterparties(references.counterparties);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingRefs(false);
      }
    };
    loadData();
  }, [activeOrgId]);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (activeOrgId === null) {
      alert('Please select an organisation before booking a trade.');
      return;
    }

    if (!selectedFund) {
      alert('Please select a fund before booking a trade.');
      return;
    }

    const direction = toNullableString(formData.direction) as BuySell | null;
    const instrument = buildInstrumentPayload(formData, direction);
    const premium = buildPremiumPayload(formData);

    const payload: DiscTradeCreatePayload = {
      id_org: activeOrgId,
      id_f: selectedFund,
      booked_by: null,
      status: 'booked',
      id_book: Number.parseInt(formData.id_book, 10),
      id_portfolio: toNullableInt(formData.id_portfolio),
      id_ctpy: Number.parseInt(formData.id_ctpy, 10),
      id_label: Number.parseInt(formData.id_label, 10),
      ice_trade_id: toNullableString(formData.ice_trade_id),
      external_id: toNullableString(formData.external_id),
      description: toNullableString(formData.description),
      trade_name: toNullableString(formData.trade_name),
      trade_date: toNullableString(formData.trade_date),
      creation_time: null,
      last_update_time: null,
      volume: toNullableInt(formData.volume),
      ice_status: toNullableString(formData.ice_status) as IceTradeStatus | null,
      originating_action: toNullableString(formData.originating_action) as OriginatingAction | null,
      legs: [
        {
          id_ac: Number.parseInt(formData.id_ac, 10),
          leg_id: formData.leg_id.trim(),
          leg_code: null,
          direction,
          notional: toNullableFloat(formData.notional),
          id_ccy: toNullableInt(formData.id_ccy),
          instrument,
          premium,
          settlement: null,
          fields: null,
        },
      ],
    };

    try {
      await bookTrade(payload);
      alert('Trade booked successfully.');
      clearForm();
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : 'Error booking trade.');
    }
  };

  const clearForm = () => {
    setFormData({
      ice_trade_id: '', external_id: '', trade_name: '', description: '', trade_date: useAppStore.getState().globalDate,
      id_book: '', id_portfolio: '', id_ctpy: '', id_label: '', volume: '', ice_status: '', originating_action: '',
      leg_id: '', id_ac: '', direction: '', notional: '', id_ccy: '',
      instrument_code: '', instrument_name: '', inst_id_ac: '', category: '', underlying: '', isin: '', bbg_ticker: '',
      prem_amount: '', prem_id_ccy: '', prem_date: useAppStore.getState().globalDate, markup: '', total: ''
    });
  };

  return (
    <div className="booker-container fade-in">
      <div className="booker-header">
          <h2>Trade Booker</h2>
        <p>Hedge fund trade booking form.</p>
      </div>

      {activeOrgId === null && (
        <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', color: 'var(--text-secondary)' }}>
          Select an organisation in the sidebar to load reference data and book trades.
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', marginBottom: '24px' }}>
        <div 
          className="glass-panel" 
          style={{ flex: 1, padding: '32px 24px', textAlign: 'center', borderStyle: 'dashed', cursor: 'pointer', transition: 'all 0.2s', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--accent-color)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
        >
          <h4 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: 500 }}>Drop trade confirmation file</h4>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-secondary)' }}>Drag and drop file here</p>
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: 'var(--text-muted)' }}>Limit 200MB per file • CSV, TXT, XLSX, PDF, MSG, PNG, JPG, JPEG</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontWeight: 500 }}>
          OR
        </div>
        <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 500 }}>Drop trade text input</h4>
          <textarea 
            placeholder="Paste trade text here..." 
            className="form-control"
            style={{ flex: 1, minHeight: '80px', padding: '12px', resize: 'none' }}
          ></textarea>
        </div>
      </div>

      <form className="trade-form" onSubmit={handleSubmit}>
        {/* General Info Section (trade_disc) */}
        <section className="form-section glass-panel">
          <h3>General Information</h3>
          <div className="form-grid">
            <div className="floating-group">
              <input type="text" id="ice_trade_id" className="floating-input" placeholder=" " required value={formData.ice_trade_id} onChange={handleChange} />
              <label htmlFor="ice_trade_id" className="floating-label">Trade ID (ICE)</label>
            </div>
            <div className="floating-group">
              <input type="text" id="external_id" className="floating-input" placeholder=" " value={formData.external_id} onChange={handleChange} />
              <label htmlFor="external_id" className="floating-label">External ID</label>
            </div>
            <div className="floating-group">
              <input type="text" id="trade_name" className="floating-input" placeholder=" " value={formData.trade_name} onChange={handleChange} />
              <label htmlFor="trade_name" className="floating-label">Trade Name</label>
            </div>
            <div className="floating-group" style={{ gridColumn: '1 / -1' }}>
              <input type="text" id="description" className="floating-input" placeholder=" " value={formData.description} onChange={handleChange} />
              <label htmlFor="description" className="floating-label">Description</label>
            </div>
            <div className="floating-group">
              <input type="date" id="trade_date" className="floating-input" placeholder=" " required value={formData.trade_date} onChange={handleChange} />
              <label htmlFor="trade_date" className="floating-label">Trade Date</label>
            </div>
            
            <div className="floating-group">
              <select id="id_book" className="floating-select" required disabled={loadingRefs} value={formData.id_book} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {books.filter(b => selectedFund ? b.id_f === selectedFund : true).map((b) => (
                  <option key={b.id_book} value={b.id_book}>{b.name}</option>
                ))}
              </select>
              <label htmlFor="id_book" className="floating-label">Book</label>
            </div>
            
            <div className="floating-group">
              <select id="id_portfolio" className="floating-select" required disabled={loadingRefs} value={formData.id_portfolio} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {portfolios.filter((p) => selectedFund ? p.id_f === selectedFund : true).map((p) => (
                  <option key={p.id_book} value={p.id_book}>{p.name}</option>
                ))}
              </select>
              <label htmlFor="id_portfolio" className="floating-label">Portfolio</label>
            </div>
            
            <div className="floating-group">
              <select id="id_ctpy" className="floating-select" required disabled={loadingRefs} value={formData.id_ctpy} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {counterparties.map((c) => (
                  <option key={c.id_ctpy} value={c.id_ctpy}>{c.display_name}</option>
                ))}
              </select>
              <label htmlFor="id_ctpy" className="floating-label">Counterparty</label>
            </div>
            
            <div className="floating-group">
              <select id="id_label" className="floating-select" required disabled={loadingRefs} value={formData.id_label} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {labels.map((l) => (
                  <option key={l.id_label} value={l.id_label}>{l.code}</option>
                ))}
              </select>
              <label htmlFor="id_label" className="floating-label">Label</label>
            </div>

            <div className="floating-group">
              <input type="number" id="volume" className="floating-input" placeholder=" " value={formData.volume} onChange={handleChange} />
              <label htmlFor="volume" className="floating-label">Volume</label>
            </div>
            <div className="floating-group">
              <select id="ice_status" className="floating-select" value={formData.ice_status} onChange={handleChange}>
                <option value="" hidden></option>
                <option value="Success">Success</option>
                <option value="Failed">Failed</option>
              </select>
              <label htmlFor="ice_status" className="floating-label">ICE Status</label>
            </div>
            <div className="floating-group">
              <select id="originating_action" className="floating-select" value={formData.originating_action} onChange={handleChange}>
                <option value="" hidden></option>
                <option value="New">New</option>
                <option value="Exercise">Exercise</option>
                <option value="Amendment">Amendment</option>
                <option value="Early termination">Early termination</option>
              </select>
              <label htmlFor="originating_action" className="floating-label">Origin Action</label>
            </div>
          </div>
        </section>

        {/* Instruments Section (trade_disc_legs) */}
        <section className="form-section glass-panel">
          <h3>Leg Details</h3>
          <div className="form-grid">
            <div className="floating-group">
              <input type="text" id="leg_id" className="floating-input" placeholder=" " required value={formData.leg_id} onChange={handleChange} />
              <label htmlFor="leg_id" className="floating-label">Leg ID</label>
            </div>
            <div className="floating-group">
              <select id="id_ac" className="floating-select" required disabled={loadingRefs} value={formData.id_ac} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {assetClasses.map((ac) => (
                  <option key={ac.id_ac} value={ac.id_ac}>
                    {ac.name || ac.code || ac.id_ac}
                  </option>
                ))}
              </select>
              <label htmlFor="id_ac" className="floating-label">Asset Class</label>
            </div>
            <div className="floating-group">
              <select id="direction" className="floating-select" required value={formData.direction} onChange={handleChange}>
                <option value="" disabled hidden></option>
                <option value="Buy">Buy</option>
                <option value="Sell">Sell</option>
              </select>
              <label htmlFor="direction" className="floating-label">Direction</label>
            </div>
            <div className="floating-group">
              <input type="number" step="0.01" id="notional" className="floating-input" placeholder=" " required min="0" value={formData.notional} onChange={handleChange} />
              <label htmlFor="notional" className="floating-label">Notional / Quantity</label>
            </div>
            <div className="floating-group">
              <select id="id_ccy" className="floating-select" required disabled={loadingRefs} value={formData.id_ccy} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {currencies.map((ccy) => (
                  <option key={ccy.id_ccy} value={ccy.id_ccy}>
                    {ccy.code} ({ccy.symbol})
                  </option>
                ))}
              </select>
              <label htmlFor="id_ccy" className="floating-label">Currency (CCY)</label>
            </div>
          </div>
        </section>

        {/* Instruments Reference Section */}
        <section className="form-section glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Instrument Details</h3>
            <span style={{ fontSize: '12px', color: 'var(--warning)', background: 'rgba(245, 158, 11, 0.1)', padding: '6px 12px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
              Instrument Name is mandatory. Please type instrument name (for Instrument details)
            </span>
          </div>
          <div className="form-grid" style={{ marginTop: 0 }}>
            <div className="floating-group">
              <input type="text" id="instrument_code" className="floating-input" placeholder=" " value={formData.instrument_code} onChange={handleChange} />
              <label htmlFor="instrument_code" className="floating-label">Instrument Code</label>
            </div>
            <div className="floating-group">
              <input type="text" id="instrument_name" className="floating-input" placeholder=" " value={formData.instrument_name} onChange={handleChange} />
              <label htmlFor="instrument_name" className="floating-label">Instrument Name</label>
            </div>
            <div className="floating-group">
              <select id="inst_id_ac" className="floating-select" disabled={loadingRefs} value={formData.inst_id_ac} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? '...' : ''}</option>
                {assetClasses.map((ac) => (
                  <option key={ac.id_ac} value={ac.id_ac}>{ac.name || ac.code}</option>
                ))}
              </select>
              <label htmlFor="inst_id_ac" className="floating-label">Asset Class</label>
            </div>
            <div className="floating-group">
              <input type="text" id="category" className="floating-input" placeholder=" " value={formData.category} onChange={handleChange} />
              <label htmlFor="category" className="floating-label">Category</label>
            </div>
            <div className="floating-group">
              <input type="text" id="underlying" className="floating-input" placeholder=" " value={formData.underlying} onChange={handleChange} />
              <label htmlFor="underlying" className="floating-label">Underlying</label>
            </div>
            <div className="floating-group">
              <input type="text" id="isin" className="floating-input" placeholder=" " value={formData.isin} onChange={handleChange} />
              <label htmlFor="isin" className="floating-label">ISIN</label>
            </div>
            <div className="floating-group">
              <input type="text" id="bbg_ticker" className="floating-input" placeholder=" " value={formData.bbg_ticker} onChange={handleChange} />
              <label htmlFor="bbg_ticker" className="floating-label">BBG Ticker</label>
            </div>
          </div>
        </section>

        {/* Premium Section */}
        <section className="form-section glass-panel">
          <h3>Premium Details</h3>
          <div className="form-grid">
            <div className="floating-group">
              <input type="number" step="0.01" id="prem_amount" className="floating-input" placeholder=" " value={formData.prem_amount} onChange={handleChange} />
              <label htmlFor="prem_amount" className="floating-label">Amount</label>
            </div>
            <div className="floating-group">
              <select id="prem_id_ccy" className="floating-select" disabled={loadingRefs} value={formData.prem_id_ccy} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? '...' : ''}</option>
                {currencies.map((ccy) => (
                  <option key={ccy.id_ccy} value={ccy.id_ccy}>{ccy.code}</option>
                ))}
              </select>
              <label htmlFor="prem_id_ccy" className="floating-label">Premium Currency</label>
            </div>
            <div className="floating-group">
              <input type="date" id="prem_date" className="floating-input" placeholder=" " value={formData.prem_date} onChange={handleChange} />
              <label htmlFor="prem_date" className="floating-label">Date</label>
            </div>
            <div className="floating-group">
              <input type="number" step="0.01" id="markup" className="floating-input" placeholder=" " value={formData.markup} onChange={handleChange} />
              <label htmlFor="markup" className="floating-label">Markup</label>
            </div>
            <div className="floating-group">
              <input type="number" step="0.01" id="total" className="floating-input" placeholder=" " value={formData.total} onChange={handleChange} />
              <label htmlFor="total" className="floating-label">Total</label>
            </div>
          </div>
        </section>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={clearForm}>Clear Form</button>
          <button type="submit" className="btn-primary">Book Trade</button>
        </div>
      </form>
    </div>
  );
}

function toNullableString(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function toNullableInt(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function toNullableFloat(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function hasAnyValue(values: Array<string | number | null | undefined>): boolean {
  return values.some((value) => {
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  });
}

function buildInstrumentPayload(
  formData: {
    instrument_code: string;
    instrument_name: string;
    inst_id_ac: string;
    category: string;
    underlying: string;
    isin: string;
    bbg_ticker: string;
    notional: string;
    id_ccy: string;
    trade_date: string;
  },
  direction: BuySell | null,
) {
  if (
    !hasAnyValue([
      formData.instrument_code,
      formData.instrument_name,
      formData.inst_id_ac,
      formData.category,
      formData.underlying,
      formData.isin,
      formData.bbg_ticker,
    ])
  ) {
    return null;
  }

  return {
    id_ac: toNullableInt(formData.inst_id_ac),
    notional: toNullableFloat(formData.notional),
    id_ccy: toNullableInt(formData.id_ccy),
    buysell: direction,
    i_type: toNullableString(formData.category),
    trade_date: toNullableString(formData.trade_date),
    isin: toNullableString(formData.isin),
    bbg_ticker: toNullableString(formData.bbg_ticker),
    payload_json: {
      instrument_code: toNullableString(formData.instrument_code),
      instrument_name: toNullableString(formData.instrument_name),
      underlying: toNullableString(formData.underlying),
    },
  };
}

function buildPremiumPayload(formData: {
  prem_amount: string;
  prem_id_ccy: string;
  prem_date: string;
  markup: string;
  total: string;
}) {
  if (
    !hasAnyValue([
      formData.prem_amount,
      formData.prem_id_ccy,
      formData.prem_date,
      formData.markup,
      formData.total,
    ])
  ) {
    return null;
  }

  return {
    amount: toNullableFloat(formData.prem_amount),
    id_ccy: toNullableInt(formData.prem_id_ccy),
    p_date: toNullableString(formData.prem_date),
    markup: toNullableFloat(formData.markup),
    total: toNullableFloat(formData.total),
    payload_json: null,
  };
}
