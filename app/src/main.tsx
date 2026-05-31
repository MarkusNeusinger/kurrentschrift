import '@fontsource/eb-garamond/400-italic.css';

import { CssBaseline, ThemeProvider } from '@mui/material';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { AdminProvider } from './state';
import { theme } from './theme';

const root = document.getElementById('root');
if (!root) throw new Error('no #root');
createRoot(root).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AdminProvider>
        <RouterProvider router={router} />
      </AdminProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
