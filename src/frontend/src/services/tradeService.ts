import { apiGet, apiPost } from '../lib/backendClient';
import { getActiveOrgId } from '../store/appStore';
import type {
  DiscTradeAggregateResponse,
  DiscTradeCreatePayload,
  TradeSummary,
} from '../types/trades';

export async function fetchTrades(idOrg = getActiveOrgId()): Promise<TradeSummary[]> {
  return apiGet<TradeSummary[]>('/trades', { id_org: idOrg });
}

export async function bookTrade(payload: DiscTradeCreatePayload): Promise<DiscTradeAggregateResponse> {
  return apiPost<DiscTradeAggregateResponse, DiscTradeCreatePayload>('/trades/disc', payload);
}
