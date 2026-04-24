import { apiGet } from '../lib/backendClient';
import type { CurrentSession } from '../types/auth';

export interface LoginQuote {
  quote: string;
  author: string;
}

export async function fetchLoginQuote(): Promise<LoginQuote> {
  return apiGet<LoginQuote>('/system/login-quote');
}

export async function fetchCurrentSession(): Promise<CurrentSession> {
  return apiGet<CurrentSession>('/system/me');
}
