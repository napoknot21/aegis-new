// import { Configuration, LogLevel } from '@azure/msal-browser';

// export const msalConfig: Configuration = {
//   auth: {
//     clientId: 'ENTER_CLIENT_ID_HERE', 
//     authority: 'https://login.microsoftonline.com/ENTER_TENANT_ID_HERE', 
//     redirectUri: '/', 
//   },
//   cache: {
//     cacheLocation: 'sessionStorage',
//     storeAuthStateInCookie: false,
//   },
//   system: {
//     loggerOptions: {
//       // eslint-disable-next-line @typescript-eslint/no-explicit-any
//       loggerCallback: (level: any, message: any, containsPii: any) => {
//         if (containsPii) { return; }
//         switch (level) {
//           // case LogLevel.Error: console.error(message); return;
//           // case LogLevel.Info: console.info(message); return;
//           // case LogLevel.Verbose: console.debug(message); return;
//           // case LogLevel.Warning: console.warn(message); return;
//         }
//       }
//     }
//   }
// };

export const loginRequest = {
  scopes: ['User.Read']
};
