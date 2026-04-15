const DEFAULT_BACKEND_API_URL = 'http://localhost:8000/api/v1';
const DEFAULT_ORG_ID = 1;

function normalizeBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() || DEFAULT_BACKEND_API_URL;
  return candidate.endsWith('/') ? candidate.slice(0, -1) : candidate;
}

function parseOrgId(value: string | undefined): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_ORG_ID;
}

export const runtimeConfig = {
  backendApiUrl: normalizeBaseUrl(import.meta.env.VITE_BACKEND_API_URL),
  defaultOrgId: parseOrgId(import.meta.env.VITE_DEFAULT_ORG_ID),
};
