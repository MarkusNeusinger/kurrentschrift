// EB Garamond, self-hosted. Exercised today: 400 carries the site-wide body/UI
// (the theme's fontFamily, theme/typography.ts — the style-guide §3 Phase-B dial
// has been pulled), 400-italic (hero + footer) and 600 (card/roadmap titles).
// Unused @font-face faces are declared but not fetched until a matching glyph
// needs them.
import '@fontsource/eb-garamond/400.css';
import '@fontsource/eb-garamond/400-italic.css';
import '@fontsource/eb-garamond/600.css';
// Playfair Display — display/headline + brand wordmark (user decision: the
// Didone/Scotch register of 19th-century German Antiqua book print; Sorts Mill
// Goudy — a genuine 1915 design — remains the open alternative if this proves
// too sharp). Faces used: 500 + 500-italic (hero h1 + accent word),
// 600 + 600-italic (brand + ".ink", pillar titles); 400 as the base so
// default-weight `display` usages (header nav) don't synthesize.
import '@fontsource/playfair-display/400.css';
import '@fontsource/playfair-display/500.css';
import '@fontsource/playfair-display/500-italic.css';
import '@fontsource/playfair-display/600.css';
import '@fontsource/playfair-display/600-italic.css';

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
