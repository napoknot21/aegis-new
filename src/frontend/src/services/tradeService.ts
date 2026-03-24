import { supabase } from '../lib/supabase';

export interface Trade {
  id: string;
  type: string;
  instrument: string;
  qty: string;
  price: string;
  date: string;
  status: 'Booked' | 'Pending' | 'Settled';
}

export interface AssetClass {
  id_ac: number;
  name: string;
  code: string;
}

export const fetchAssetClasses = async (): Promise<AssetClass[]> => {
  const { data, error } = await supabase.from('asset_classes').select('*');
  
  if (error) {
    console.error('Error fetching asset classes:', error);
    return [];
  }
  
  return (data || []) as AssetClass[];
};

export interface Currency {
  id_ccy: number;
  name: string;
  code: string;
  symbol: string;
}

export const fetchCurrencies = async (): Promise<Currency[]> => {
  const { data, error } = await supabase.from('currencies').select('*');
  
  if (error) {
    console.error('Error fetching currencies:', error);
    return [];
  }
  
  return (data || []) as Currency[];
};

export const fetchLabels = async (): Promise<any[]> => {
  const { data } = await supabase.from('trade_disc_labels').select('*');
  return data || [];
};

export const fetchBooks = async (): Promise<any[]> => {
  const { data } = await supabase.from('books').select('*'); // Assumed table name
  return data || [];
};

export const fetchPortfolios = async (): Promise<any[]> => {
  const { data } = await supabase.from('portfolios').select('*'); // Assumed table name
  return data || [];
};

export const fetchCounterparties = async (): Promise<any[]> => {
  const { data } = await supabase.from('counterparties').select('*'); // Assumed table name
  return data || [];
};

export const fetchFunds = async (): Promise<any[]> => {
  const { data } = await supabase.from('funds').select('*');
  return data || [];
};

export const fetchTrades = async (): Promise<Trade[]> => {
  const { data, error } = await supabase.from('trades').select('*');
  
  if (error) {
    console.error('Error fetching trades from Supabase:', error);
    return [];
  }
  
  return data as Trade[];
};

export const bookTrade = async (tradeData: any, legData: any, instrumentData?: any, premiumData?: any) => {
  try {
    // 1. Insert into trade_disc
    const { data: tradeResult, error: tradeError } = await supabase
      .from('trade_disc')
      .insert([tradeData])
      .select('id_spe')
      .single();

    if (tradeError) throw tradeError;

    // 2. Insert Premium (if provided)
    let id_prem = null;
    if (premiumData && (premiumData.amount !== null || premiumData.total !== null)) {
      const { data: premResult, error: premError } = await supabase
        .from('trade_disc_premiums')
        .insert([premiumData])
        .select('id_prem')
        .single();
      if (premError) throw premError;
      id_prem = premResult.id_prem;
    }

    // 3. Insert Instrument (if provided)
    let id_inst = null;
    if (instrumentData && (instrumentData.instrument_code || instrumentData.instrument_name)) {
      const { data: instResult, error: instError } = await supabase
        .from('trade_disc_instruments')
        .insert([instrumentData])
        .select('id_inst')
        .single();
      if (instError) throw instError;
      id_inst = instResult.id_inst;
    }

    // 4. Add foreign keys to legData
    const legPayload = {
      ...legData,
      id_disc: tradeResult.id_spe,
      id_prem: id_prem,
      id_inst: id_inst
    };

    const { error: legError } = await supabase
      .from('trade_disc_legs')
      .insert([legPayload]);

    if (legError) throw legError;

    return { success: true };
  } catch (error) {
    console.error('Error booking trade:', error);
    return { success: false, error };
  }
};

export const fetchRiskLimits = async () => {
  // Keeping as stub, replace when risk table is built on backend
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { desk: 'G10 FX Spot', utilization: 4500000, limit: 10000000, ratio: 0.45 },
        { desk: 'US Rates Swap', utilization: 22000000, limit: 25000000, ratio: 0.88 },
      ]);
    }, 400);
  });
};
