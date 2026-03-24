import { create } from 'zustand';

interface AppStore {
  selectedFund: number | null;
  globalDate: string;
  setSelectedFund: (fundId: number | null) => void;
  setGlobalDate: (date: string) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  selectedFund: null,
  globalDate: new Date().toISOString().split('T')[0], // Sets to today (YYYY-MM-DD)
  setSelectedFund: (fundId) => set({ selectedFund: fundId }),
  setGlobalDate: (date) => set({ globalDate: date }),
}));
