const DEFAULT_BACKEND_API_URL = 'http://localhost:8000/api/v1';
const DEFAULT_ORG_ID = 1;
const DEFAULT_FRONTEND_ORIGIN = 'http://localhost:5173';

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined) {
    return fallback;
  }

  const normalized = value.trim().toLowerCase();
  if (normalized === 'true') {
    return true;
  }
  if (normalized === 'false') {
    return false;
  }

  return fallback;
}

function normalizeBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() || DEFAULT_BACKEND_API_URL;
  return candidate.endsWith('/') ? candidate.slice(0, -1) : candidate;
}

function parseOrgId(value: string | undefined): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_ORG_ID;
}

function getBrowserOrigin(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }

  return DEFAULT_FRONTEND_ORIGIN;
}

function normalizeOptionalValue(value: string | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function resolveRedirectUrl(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    return `${getBrowserOrigin()}/`;
  }

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }

  if (trimmed.startsWith('/')) {
    return `${getBrowserOrigin()}${trimmed}`;
  }

  return `${getBrowserOrigin()}/${trimmed}`;
}

function parseScopes(value: string | undefined, clientId: string | null): string[] {
  const parsed = (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  if (parsed.length > 0) {
    return parsed;
  }

  if (clientId) {
    return [`${clientId}/.default`];
  }

  return [];
}

export const runtimeConfig = {
  backendApiUrl: normalizeBaseUrl(import.meta.env.VITE_BACKEND_API_URL),
  defaultOrgId: parseOrgId(import.meta.env.VITE_DEFAULT_ORG_ID),
  auth: {
    clientId: normalizeOptionalValue(import.meta.env.VITE_MSAL_CLIENT_ID),
    authority: normalizeOptionalValue(import.meta.env.VITE_MSAL_AUTHORITY),
    redirectUri: resolveRedirectUrl(import.meta.env.VITE_MSAL_REDIRECT_URI),
    postLogoutRedirectUri: resolveRedirectUrl(import.meta.env.VITE_MSAL_POST_LOGOUT_REDIRECT_URI),
    scopes: parseScopes(import.meta.env.VITE_MSAL_SCOPES, normalizeOptionalValue(import.meta.env.VITE_MSAL_CLIENT_ID)),
    cacheLocation: normalizeOptionalValue(import.meta.env.VITE_MSAL_CACHE_LOCATION) ?? 'localStorage',
    storeAuthStateInCookie: parseBoolean(import.meta.env.VITE_MSAL_STORE_AUTH_STATE_IN_COOKIE, true),
  },
};
