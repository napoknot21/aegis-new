import { apiGet } from '../lib/backendClient';
import { getActiveOrgId } from '../store/appStore';
import type {
  AssetClass,
  Book,
  Counterparty,
  Currency,
  Fund,
  TradeFormReferences,
} from '../types/reference';
import type { TradeLabel } from '../types/reference';

interface ReferenceQueryOptions {
  includeInactive?: boolean;
  idOrg?: number;
  idFund?: number | null;
}
export async function fetchAssetClasses(includeInactive = false): Promise<AssetClass[]> {
  return apiGet<AssetClass[]>('/reference/asset-classes', { include_inactive: includeInactive });
}

export async function fetchCurrencies(includeInactive = false): Promise<Currency[]> {
  return apiGet<Currency[]>('/reference/currencies', { include_inactive: includeInactive });
}

export async function fetchFunds(options: ReferenceQueryOptions = {}): Promise<Fund[]> {
  const idOrg = options.idOrg ?? getActiveOrgId();
  return apiGet<Fund[]>('/reference/funds', {
    id_org: idOrg,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchBooks(options: ReferenceQueryOptions = {}): Promise<Book[]> {
  const idOrg = options.idOrg ?? getActiveOrgId();
  return apiGet<Book[]>('/reference/books', {
    id_org: idOrg,
    id_f: options.idFund ?? undefined,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchTradeLabels(idOrg = getActiveOrgId()): Promise<TradeLabel[]> {
  return apiGet<TradeLabel[]>('/trades/labels', { id_org: idOrg });
}

export async function fetchCounterparties(options: ReferenceQueryOptions = {}): Promise<Counterparty[]> {
  const idOrg = options.idOrg ?? getActiveOrgId();
  return apiGet<Counterparty[]>('/reference/counterparties', {
    id_org: idOrg,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchTradeFormReferences(idOrg = getActiveOrgId()): Promise<TradeFormReferences> {
  const [assetClasses, currencies, books, tradeLabels, counterparties] = await Promise.all([
    fetchAssetClasses(),
    fetchCurrencies(),
    fetchBooks({ idOrg }),
    fetchTradeLabels(idOrg),
    fetchCounterparties({ idOrg }),
  ]);

  return {
    assetClasses,
    currencies,
    books,
    portfolios: books,
    tradeLabels,
    counterparties,
  };
}
