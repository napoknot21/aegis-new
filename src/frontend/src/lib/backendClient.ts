import { acquireBackendAccessToken } from './authClient';
import { runtimeConfig } from '../config/runtime';

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${runtimeConfig.backendApiUrl}${normalizedPath}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      if (payload && typeof payload.detail === 'string') {
        message = payload.detail;
      }
    } catch {
      // Keep the HTTP status fallback when the body is not JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function buildHeaders(baseHeaders: HeadersInit): Promise<HeadersInit> {
  const accessToken = await acquireBackendAccessToken();

  if (!accessToken) {
    return baseHeaders;
  }

  return {
    ...baseHeaders,
    Authorization: `Bearer ${accessToken}`,
  };
}

export async function apiGet<T>(path: string, query?: Record<string, QueryValue>): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    method: 'GET',
    headers: await buildHeaders({
      Accept: 'application/json',
    }),
  });

  return parseResponse<T>(response);
}

export async function apiPost<TResponse, TBody>(path: string, body: TBody): Promise<TResponse> {
  const response = await fetch(buildUrl(path), {
    method: 'POST',
    headers: await buildHeaders({
      'Content-Type': 'application/json',
      Accept: 'application/json',
    }),
    body: JSON.stringify(body),
  });

  return parseResponse<TResponse>(response);
}
