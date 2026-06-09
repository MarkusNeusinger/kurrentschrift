// EB Garamond, self-hosted. Actually exercised today: 400-italic (hero + footer)
// and 600 (card/roadmap titles). 400-regular is kept as headroom — body currently
// renders in the theme sans stack, but moving body to Garamond is a live Phase-B
// dial (style-guide §3). Unused @font-face faces are declared but not fetched until
// a matching glyph needs them.
import '@fontsource/eb-garamond/400.css';
import '@fontsource/eb-garamond/400-italic.css';
import '@fontsource/eb-garamond/600.css';
// Cormorant Garamond — display/headline + brand wordmark. Faces used: 500 + 500-italic
// (hero h1 + accent word), 600 + 600-italic (brand + ".ink"); 400 as the base.
import '@fontsource/cormorant-garamond/400.css';
import '@fontsource/cormorant-garamond/500.css';
import '@fontsource/cormorant-garamond/500-italic.css';
import '@fontsource/cormorant-garamond/600.css';
import '@fontsource/cormorant-garamond/600-italic.css';

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
