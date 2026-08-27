// Fonts are NOT imported here: every @font-face (EB Garamond, Playfair
// Display, the show scripts) is declared early in index.html against verbatim
// self-hosted woff2 copies under public/fonts/, so the critical faces can be
// preloaded before this bundle has even finished loading. A new cut needs a
// file there plus a rule in index.html — a @fontsource import no longer ships
// anything (the packages remain devDependencies as source + update channel;
// `npm run fonts:sync` re-copies and verifies the files).

import { CssBaseline, ThemeProvider } from '@mui/material';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/routes';
import { theme } from '@/theme';

const root = document.getElementById('root');
if (!root) throw new Error('no #root');
createRoot(root).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <RouterProvider router={router} />
    </ThemeProvider>
  </React.StrictMode>,
);
