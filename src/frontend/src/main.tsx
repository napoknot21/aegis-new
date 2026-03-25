import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
// import { PublicClientApplication } from '@azure/msal-browser';
// import { MsalProvider } from '@azure/msal-react';
// import { msalConfig } from './authConfig';
import App from './App.tsx';
import './index.css';

// const msalInstance = new PublicClientApplication(msalConfig);

// MSAL configuration is disabled for now.
// msalInstance.initialize().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      {/* <MsalProvider instance={msalInstance}> */}
        <BrowserRouter>
          <App />
        </BrowserRouter>
      {/* </MsalProvider> */}
    </StrictMode>,
  );
// });
