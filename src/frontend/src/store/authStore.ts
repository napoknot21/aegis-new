import type { AccountInfo } from '@azure/msal-browser';
import { create } from 'zustand';
import type { CurrentSession } from '../types/auth';

type SessionStatus = 'idle' | 'loading' | 'ready' | 'error';

interface AuthStore {
  isEnabled: boolean;
  isInitializing: boolean;
  isAuthenticated: boolean;
  account: AccountInfo | null;
  sessionStatus: SessionStatus;
  session: CurrentSession | null;
  error: string | null;
  setEnabled: (isEnabled: boolean) => void;
  finishInitialization: (account: AccountInfo | null) => void;
  setAccount: (account: AccountInfo | null) => void;
  startSessionLoading: () => void;
  setSession: (session: CurrentSession) => void;
  setError: (message: string) => void;
  clearSession: () => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  isEnabled: false,
  isInitializing: true,
  isAuthenticated: false,
  account: null,
  sessionStatus: 'idle',
  session: null,
  error: null,
  setEnabled: (isEnabled) => set({ isEnabled }),
  finishInitialization: (account) =>
    set({
      isInitializing: false,
      account,
      isAuthenticated: Boolean(account),
      sessionStatus: 'idle',
      session: null,
      error: null,
    }),
  setAccount: (account) =>
    set({
      account,
      isAuthenticated: Boolean(account),
      session: null,
      error: null,
      sessionStatus: 'idle',
    }),
  startSessionLoading: () =>
    set({
      sessionStatus: 'loading',
      error: null,
    }),
  setSession: (session) =>
    set({
      session,
      sessionStatus: 'ready',
      error: null,
    }),
  setError: (message) =>
    set({
      error: message,
      sessionStatus: 'error',
    }),
  clearSession: () =>
    set({
      session: null,
      sessionStatus: 'idle',
      error: null,
    }),
  clearAuth: () =>
    set({
      isInitializing: false,
      isAuthenticated: false,
      account: null,
      sessionStatus: 'idle',
      session: null,
      error: null,
    }),
}));
