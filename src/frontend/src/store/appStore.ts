import { runtimeConfig } from '../config/runtime';
import { create } from 'zustand';

interface AppStore {
  selectedOrg: number | null;
  selectedFund: number | null;
  globalDate: string;
  setSelectedOrg: (orgId: number | null) => void;
  setSelectedFund: (fundId: number | null) => void;
  setGlobalDate: (date: string) => void;
  resetSelections: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  selectedOrg: null,
  selectedFund: null,
  globalDate: new Date().toISOString().split('T')[0], // Sets to today (YYYY-MM-DD)
  setSelectedOrg: (orgId) => set({ selectedOrg: orgId, selectedFund: null }),
  setSelectedFund: (fundId) => set({ selectedFund: fundId }),
  setGlobalDate: (date) => set({ globalDate: date }),
  resetSelections: () => set({ selectedOrg: null, selectedFund: null }),
}));

export function getActiveOrgId(): number {
  const selectedOrg = useAppStore.getState().selectedOrg;
  if (selectedOrg !== null) {
    return selectedOrg;
  }

  if (!runtimeConfig.auth.clientId || !runtimeConfig.auth.authority) {
    return runtimeConfig.defaultOrgId;
  }

  throw new Error('Select an organisation before loading organisation-scoped data.');
}
