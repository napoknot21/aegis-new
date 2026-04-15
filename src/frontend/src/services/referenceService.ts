import { runtimeConfig } from '../config/runtime';
import { apiGet } from '../lib/backendClient';
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

const defaultOrgId = runtimeConfig.defaultOrgId;

export async function fetchAssetClasses(includeInactive = false): Promise<AssetClass[]> {
  return apiGet<AssetClass[]>('/reference/asset-classes', { include_inactive: includeInactive });
}

export async function fetchCurrencies(includeInactive = false): Promise<Currency[]> {
  return apiGet<Currency[]>('/reference/currencies', { include_inactive: includeInactive });
}

export async function fetchFunds(options: ReferenceQueryOptions = {}): Promise<Fund[]> {
  return apiGet<Fund[]>('/reference/funds', {
    id_org: options.idOrg ?? defaultOrgId,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchBooks(options: ReferenceQueryOptions = {}): Promise<Book[]> {
  return apiGet<Book[]>('/reference/books', {
    id_org: options.idOrg ?? defaultOrgId,
    id_f: options.idFund ?? undefined,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchTradeLabels(idOrg = defaultOrgId): Promise<TradeLabel[]> {
  return apiGet<TradeLabel[]>('/trades/labels', { id_org: idOrg });
}

export async function fetchCounterparties(options: ReferenceQueryOptions = {}): Promise<Counterparty[]> {
  return apiGet<Counterparty[]>('/reference/counterparties', {
    id_org: options.idOrg ?? defaultOrgId,
    include_inactive: options.includeInactive ?? false,
  });
}

export async function fetchTradeFormReferences(idOrg = defaultOrgId): Promise<TradeFormReferences> {
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
