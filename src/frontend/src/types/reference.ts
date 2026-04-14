export interface AssetClass {
  id_ac: number;
  code: string;
  ice_code: string | null;
  name: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface Currency {
  id_ccy: number;
  code: string;
  name: string;
  symbol: string | null;
  iso_numeric: number | null;
  decimals: number;
  sort_order: number;
  is_active: boolean;
}

export interface Fund {
  id_f: number;
  id_org: number;
  id_ccy: number;
  name: string;
  code: string;
  fund_type: string | null;
  inception_date: string | null;
  is_active: boolean;
}

export interface Book {
  id_book: number;
  id_org: number;
  id_f: number;
  name: string;
  parent_id: number | null;
  is_active: boolean;
}

export interface TradeLabel {
  id_label: number;
  id_org: number;
  code: string;
}

export interface Counterparty {
  id_ctpy: number;
  id_org: number;
  id_bank: number | null;
  ice_name: string | null;
  ext_code: string | null;
  is_active: boolean;
  display_name: string;
}

export interface TradeFormReferences {
  assetClasses: AssetClass[];
  currencies: Currency[];
  books: Book[];
  portfolios: Book[];
  tradeLabels: TradeLabel[];
  counterparties: Counterparty[];
}
