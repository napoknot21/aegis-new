export type TradeStatus = 'booked' | 'recap_done' | 'validated' | 'rejected' | 'cancelled';
export type TradeTypeCode = 'DISC' | 'ADV';
export type IceTradeStatus = 'Success' | 'Failed';
export type OriginatingAction = 'New' | 'Exercise' | 'Amendment' | 'Early termination';
export type BuySell = 'Buy' | 'Sell';

export interface TradeSummary {
  id_trade: number;
  id_org: number;
  id_spe: number;
  id_type: number;
  type_code: TradeTypeCode;
  id_f: number;
  booked_by: number | null;
  booked_at: string;
  last_modified_by: number | null;
  last_modified_at: string | null;
  status: TradeStatus;
}

export interface DiscTradeInstrumentCreatePayload {
  id_ac: number | null;
  notional: number | null;
  id_ccy: number | null;
  buysell: BuySell | null;
  i_type: string | null;
  trade_date: string | null;
  isin: string | null;
  bbg_ticker: string | null;
  payload_json: Record<string, unknown> | null;
}

export interface DiscTradePremiumCreatePayload {
  amount: number | null;
  id_ccy: number | null;
  p_date: string | null;
  markup: number | null;
  total: number | null;
  payload_json: Record<string, unknown> | null;
}

export interface DiscTradeFieldsCreatePayload {
  id_ccy: number | null;
  d_date: string | null;
  notional: number | null;
  payout_ccy_id: number | null;
  buysell: BuySell | null;
  i_type: string | null;
}

export interface DiscTradeLegCreatePayload {
  id_ac: number;
  leg_id: string;
  leg_code: string | null;
  direction: BuySell | null;
  notional: number | null;
  id_ccy: number | null;
  instrument: DiscTradeInstrumentCreatePayload | null;
  premium: DiscTradePremiumCreatePayload | null;
  settlement: null;
  fields: DiscTradeFieldsCreatePayload | null;
}

export interface DiscTradeCreatePayload {
  id_org: number;
  id_f: number;
  booked_by: number | null;
  status: TradeStatus;
  id_book: number;
  id_portfolio: number | null;
  id_ctpy: number;
  id_label: number;
  ice_trade_id: string | null;
  external_id: string | null;
  description: string | null;
  trade_name: string | null;
  trade_date: string | null;
  creation_time: string | null;
  last_update_time: string | null;
  volume: number | null;
  ice_status: IceTradeStatus | null;
  originating_action: OriginatingAction | null;
  legs: DiscTradeLegCreatePayload[];
}

export interface DiscTradeAggregateResponse {
  trade: TradeSummary;
  disc: {
    id_spe: number;
    id_org: number;
    id_book: number;
    id_portfolio: number | null;
    id_ctpy: number;
    id_label: number;
    ice_trade_id: string | null;
    external_id: string | null;
    description: string | null;
    trade_name: string | null;
    trade_date: string | null;
    creation_time: string | null;
    last_update_time: string | null;
    volume: number | null;
    ice_status: string | null;
    originating_action: string | null;
  };
  legs: Array<{
    id_leg: number;
    id_org: number;
    id_disc: number;
    id_ac: number;
    leg_id: string;
    leg_code: string | null;
    direction: string | null;
    notional: string | number | null;
    id_ccy: number | null;
  }>;
}
