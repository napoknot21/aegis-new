import { apiGet } from '../lib/backendClient';

export interface LoginQuote {
  quote: string;
  author: string;
}

export async function fetchLoginQuote(): Promise<LoginQuote> {
  return apiGet<LoginQuote>('/system/login-quote');
}
