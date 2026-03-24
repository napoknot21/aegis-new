import { useState, useEffect } from 'react';
import { 
  fetchAssetClasses, fetchCurrencies, 
  fetchLabels, fetchBooks, fetchPortfolios, fetchCounterparties 
} from '../../services/tradeService';
import type { AssetClass, Currency } from '../../services/tradeService';
import { useAppStore } from '../../store/appStore';
import './TradeBooker.css';

export default function TradeBooker() {
  const { selectedFund } = useAppStore();

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
  const [labels, setLabels] = useState<any[]>([]);
  const [books, setBooks] = useState<any[]>([]);
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [counterparties, setCounterparties] = useState<any[]>([]);
  
  const [loadingRefs, setLoadingRefs] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [acData, ccyData, lblData, bkData, pfData, cpData] = await Promise.all([
          fetchAssetClasses(), fetchCurrencies(), fetchLabels(),
          fetchBooks(), fetchPortfolios(), fetchCounterparties()
        ]);
        setAssetClasses(acData); setCurrencies(ccyData); setLabels(lblData);
        setBooks(bkData); setPortfolios(pfData); setCounterparties(cpData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingRefs(false);
      }
    };
    loadData();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const tradeData = {
      ice_trade_id: formData.ice_trade_id, external_id: formData.external_id, trade_name: formData.trade_name,
      description: formData.description, trade_date: formData.trade_date,
      id_book: formData.id_book ? parseInt(formData.id_book) : null,
      id_portfolio: formData.id_portfolio ? parseInt(formData.id_portfolio) : null,
      id_ctpy: formData.id_ctpy ? parseInt(formData.id_ctpy) : null,
      id_label: formData.id_label ? parseInt(formData.id_label) : null,
      volume: formData.volume ? parseInt(formData.volume) : null,
      ice_status: formData.ice_status, originating_action: formData.originating_action,
    };

    const legData = {
      leg_id: formData.leg_id,
      id_ac: formData.id_ac ? parseInt(formData.id_ac) : null,
      direction: formData.direction,
      notional: formData.notional ? parseFloat(formData.notional) : null,
      id_ccy: formData.id_ccy ? parseInt(formData.id_ccy) : null,
    };

    const instrumentData = {
      instrument_code: formData.instrument_code, instrument_name: formData.instrument_name,
      id_ac: formData.inst_id_ac ? parseInt(formData.inst_id_ac) : null,
      category: formData.category, underlying: formData.underlying,
      isin: formData.isin, bbg_ticker: formData.bbg_ticker,
    };

    const premiumData = {
      amount: formData.prem_amount ? parseFloat(formData.prem_amount) : null,
      id_ccy: formData.prem_id_ccy ? parseInt(formData.prem_id_ccy) : null,
      date: formData.prem_date,
      markup: formData.markup ? parseFloat(formData.markup) : null,
      total: formData.total ? parseFloat(formData.total) : null,
    };

    const { bookTrade } = await import('../../services/tradeService');
    const result = await bookTrade(tradeData, legData, instrumentData, premiumData);
    
    if (result.success) {
      alert('Trade, Leg, Instrument & Premium successfully booked!');
    } else {
      alert('Error booking trade. Check console.');
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
        <h2>Book New Trade</h2>
        <p>Enter the specifics. Data saved across trade_disc, trade_disc_legs, instruments and premiums.</p>
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
                  <option key={b.id_book || b.id} value={b.id_book || b.id}>{b.name}</option>
                ))}
              </select>
              <label htmlFor="id_book" className="floating-label">Book</label>
            </div>
            
            <div className="floating-group">
              <select id="id_portfolio" className="floating-select" required disabled={loadingRefs} value={formData.id_portfolio} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {portfolios.map((p) => (
                  <option key={p.id_portfolio || p.id} value={p.id_portfolio || p.id}>{p.name}</option>
                ))}
              </select>
              <label htmlFor="id_portfolio" className="floating-label">Portfolio</label>
            </div>
            
            <div className="floating-group">
              <select id="id_ctpy" className="floating-select" required disabled={loadingRefs} value={formData.id_ctpy} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {counterparties.map((c) => (
                  <option key={c.id_ctpy || c.id} value={c.id_ctpy || c.id}>{c.name}</option>
                ))}
              </select>
              <label htmlFor="id_ctpy" className="floating-label">Counterparty</label>
            </div>
            
            <div className="floating-group">
              <select id="id_label" className="floating-select" required disabled={loadingRefs} value={formData.id_label} onChange={handleChange}>
                <option value="" disabled hidden>{loadingRefs ? 'Chargement...' : ''}</option>
                {labels.map((l) => (
                  <option key={l.id_label || l.id} value={l.id_label || l.id}>{l.code}</option>
                ))}
              </select>
              <label htmlFor="id_label" className="floating-label">Label</label>
            </div>

            <div className="floating-group">
              <input type="number" id="volume" className="floating-input" placeholder=" " value={formData.volume} onChange={handleChange} />
              <label htmlFor="volume" className="floating-label">Volume</label>
            </div>
            <div className="floating-group">
              <input type="text" id="ice_status" className="floating-input" placeholder=" " value={formData.ice_status} onChange={handleChange} />
              <label htmlFor="ice_status" className="floating-label">ICE Status</label>
            </div>
            <div className="floating-group">
              <input type="text" id="originating_action" className="floating-input" placeholder=" " value={formData.originating_action} onChange={handleChange} />
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
          <h3>Instrument Details</h3>
          <div className="form-grid">
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
              <label htmlFor="prem_id_ccy" className="floating-label">Premium Date</label>
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
