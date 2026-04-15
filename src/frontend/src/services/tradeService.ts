import { runtimeConfig } from '../config/runtime';
import { apiGet, apiPost } from '../lib/backendClient';
import type {
  DiscTradeAggregateResponse,
  DiscTradeCreatePayload,
  TradeSummary,
} from '../types/trades';

const defaultOrgId = runtimeConfig.defaultOrgId;

export async function fetchTrades(idOrg = defaultOrgId): Promise<TradeSummary[]> {
  return apiGet<TradeSummary[]>('/trades', { id_org: idOrg });
}

export async function bookTrade(payload: DiscTradeCreatePayload): Promise<DiscTradeAggregateResponse> {
  return apiPost<DiscTradeAggregateResponse, DiscTradeCreatePayload>('/trades/disc', payload);
}
