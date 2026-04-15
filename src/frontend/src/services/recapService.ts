import { apiGet, apiPost } from '../lib/backendClient';

export interface TradeRecapRecord {
  TradeId: string;
  Portfolio: string;
  ProductType: string;
  Quantity: number;
  Price: number;
  Currency: string;
  Status: string;
  Date: string;
  TradeDate: string;
}

interface RunTradeRecapResponse {
  records: TradeRecapRecord[];
}

export interface BookTradeRecapResponse {
  booked_count: number;
}

function toRecapError(error: unknown, fallbackMessage: string): Error {
  if (error instanceof Error && error.message.startsWith('404')) {
    return new Error('The trade recap API is not available on the backend yet.');
  }

  return error instanceof Error ? error : new Error(fallbackMessage);
}

export async function runTradeRecap(options: {
  reportDate?: string;
  tradeDate?: string;
}): Promise<TradeRecapRecord[]> {
  try {
    const response = await apiGet<RunTradeRecapResponse>('/recap/run', {
      date: options.reportDate || undefined,
      trade_date: options.tradeDate || undefined,
    });
    return Array.isArray(response.records) ? response.records : [];
  } catch (error) {
    throw toRecapError(error, 'Unable to load trade recap data.');
  }
}

export async function bookTradeRecap(records: TradeRecapRecord[]): Promise<BookTradeRecapResponse> {
  try {
    return await apiPost<BookTradeRecapResponse, TradeRecapRecord[]>('/recap/book', records);
  } catch (error) {
    throw toRecapError(error, 'Unable to book trade recap records.');
  }
}
