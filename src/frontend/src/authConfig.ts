import {
  BrowserCacheLocation,
  type Configuration,
  type EndSessionRequest,
  type RedirectRequest,
  LogLevel,
} from '@azure/msal-browser';
import { runtimeConfig } from './config/runtime';

const cacheLocation =
  runtimeConfig.auth.cacheLocation === 'sessionStorage'
    ? BrowserCacheLocation.SessionStorage
    : BrowserCacheLocation.LocalStorage;

export const msalEnabled = Boolean(runtimeConfig.auth.clientId && runtimeConfig.auth.authority);

export const msalConfig: Configuration = {
  auth: {
    clientId: runtimeConfig.auth.clientId ?? 'msal-disabled',
    authority: runtimeConfig.auth.authority ?? 'https://login.microsoftonline.com/common',
    redirectUri: runtimeConfig.auth.redirectUri,
    postLogoutRedirectUri: runtimeConfig.auth.postLogoutRedirectUri,
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation,
    storeAuthStateInCookie: runtimeConfig.auth.storeAuthStateInCookie,
  },
  system: {
    loggerOptions: {
      loggerCallback(level: LogLevel, message: string, containsPii: boolean) {
        if (containsPii) {
          return;
        }

        switch (level) {
          case LogLevel.Error:
            console.error(message);
            return;
          case LogLevel.Warning:
            console.warn(message);
            return;
          case LogLevel.Info:
            console.info(message);
            return;
          default:
            console.debug(message);
        }
      },
      piiLoggingEnabled: false,
    },
  },
};

export const loginRequest: RedirectRequest = {
  scopes: runtimeConfig.auth.scopes,
};

export const logoutRequest: EndSessionRequest = {
  postLogoutRedirectUri: runtimeConfig.auth.postLogoutRedirectUri,
};
