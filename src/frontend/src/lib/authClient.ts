import {
  EventType,
  type AccountInfo,
  type EventMessage,
  type AuthenticationResult,
  InteractionRequiredAuthError,
  PublicClientApplication,
} from '@azure/msal-browser';
import { loginRequest, logoutRequest, msalConfig, msalEnabled } from '../authConfig';
import { useAppStore } from '../store/appStore';
import { useAuthStore } from '../store/authStore';

export const msalInstance = msalEnabled ? new PublicClientApplication(msalConfig) : null;

let eventCallbackRegistered = false;

function syncActiveAccount(account: AccountInfo | null) {
  const previousAccount = useAuthStore.getState().account;
  const accountChanged =
    previousAccount?.homeAccountId !== account?.homeAccountId;

  if (msalInstance && account) {
    msalInstance.setActiveAccount(account);
  }

  useAuthStore.getState().setAccount(account);

  if (!account || accountChanged) {
    useAppStore.getState().resetSelections();
  }
}

function registerMsalEventCallback() {
  if (!msalInstance || eventCallbackRegistered) {
    return;
  }

  msalInstance.addEventCallback((event: EventMessage) => {
    if (
      event.eventType === EventType.LOGIN_SUCCESS ||
      event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS
    ) {
      const payload = event.payload as AuthenticationResult | null;
      if (payload?.account) {
        syncActiveAccount(payload.account);
      }
      return;
    }

    if (event.eventType === EventType.LOGOUT_SUCCESS) {
      useAuthStore.getState().clearAuth();
      useAppStore.getState().resetSelections();
    }
  });

  eventCallbackRegistered = true;
}

export async function initializeAuth(): Promise<void> {
  useAuthStore.getState().setEnabled(msalEnabled);

  if (!msalEnabled || !msalInstance) {
    useAuthStore.getState().finishInitialization(null);
    return;
  }

  try {
    registerMsalEventCallback();

    await msalInstance.initialize();
    const redirectResult = await msalInstance.handleRedirectPromise();

    const account =
      redirectResult?.account ??
      msalInstance.getActiveAccount() ??
      msalInstance.getAllAccounts()[0] ??
      null;

    if (account) {
      msalInstance.setActiveAccount(account);
    }

    useAuthStore.getState().finishInitialization(account);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unknown MSAL initialization failure.';

    useAuthStore.getState().finishInitialization(null);
    useAuthStore.getState().setError(`Microsoft sign-in could not initialize: ${message}`);
  }
}

export function getActiveAccount(): AccountInfo | null {
  if (!msalInstance) {
    return null;
  }

  return msalInstance.getActiveAccount() ?? msalInstance.getAllAccounts()[0] ?? null;
}

export async function login(): Promise<void> {
  if (!msalInstance || !msalEnabled) {
    return;
  }

  await msalInstance.loginRedirect(loginRequest);
}

export async function logout(): Promise<void> {
  if (!msalInstance || !msalEnabled) {
    return;
  }

  useAuthStore.getState().clearAuth();
  useAppStore.getState().resetSelections();
  await msalInstance.logoutRedirect(logoutRequest);
}

export async function acquireBackendAccessToken(): Promise<string | null> {
  if (!msalInstance || !msalEnabled) {
    return null;
  }

  const account = getActiveAccount();
  if (!account) {
    return null;
  }

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account,
    });
    return response.accessToken;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      await msalInstance.acquireTokenRedirect({
        ...loginRequest,
        account,
      });
      return null;
    }

    throw error;
  }
}
