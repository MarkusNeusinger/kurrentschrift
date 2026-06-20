// design-sync bundle entry — NOT part of the running app.
//
// This file is the single entry the /design-sync converter bundles into the
// claude.ai/design "design system" bundle. It re-exports the paper-&-ink brand
// components and adds an `AppProviders` wrapper so every preview card renders
// inside the real MUI theme + a router (PublicHeader/PublicFooter need routing
// context; everything needs the theme).
//
// It lives in app/ (not app/src/) on purpose: it is OUTSIDE tsconfig's
// `include: ["src"]`, so it never enters the app's type-check / CI, and it is
// never imported by the app itself (dead code there). The converter resolves
// the `@/*` alias via app/tsconfig.json's compilerOptions.paths.
import type { ReactNode } from 'react';

import { CssBaseline, ThemeProvider } from '@mui/material';
import { MemoryRouter } from 'react-router-dom';

import { theme } from '@/theme';

export { BootStatus } from '@/components/BootStatus/BootStatus';
export { InfoHint } from '@/components/InfoHint/InfoHint';
export { PaperBackground } from '@/components/PaperBackground/PaperBackground';
export { PublicFooter } from '@/components/PublicFooter/PublicFooter';
export { PublicHeader } from '@/components/PublicHeader/PublicHeader';
export { WrittenGlyph } from '@/components/WrittenGlyph/WrittenGlyph';

// Preview provider: theme + baseline reset + an in-memory router so cards that
// use react-router (useNavigate / <Link>) render in context instead of blank.
export function AppProviders({ children }: { children?: ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  );
}
