// Router-level error surface. Its main real-world trigger is a failed lazy
// chunk load (e.g. an old tab requesting hashed chunks that a new deploy
// replaced) — a full reload fetches the current bundle and recovers.
//
// Since the audit of 2026-09-02 that recovery is automatic, following the
// sibling repo's boundary (owner rule "Gute Sachen aufs Schwesterprojekt"):
// asking a visitor to press "Seite neu laden" for a failure they did not cause
// and cannot understand is a worse page than one that heals itself. Exactly
// ONE automatic reload is allowed, guarded by a sessionStorage flag — a stale
// index.html that keeps pointing at dead chunks would otherwise put the tab in
// a reload loop. The manual button stays for the second failure and for every
// other error.
//
// A thrown 404 response renders the real 404 page instead of a generic
// apology, so a bad `?g=`-style deep link ends on the page that offers a way
// out (and reports itself as a miss).
import { useEffect, useState } from 'react';

import { Box, Button, Typography } from '@mui/material';
import { isRouteErrorResponse, useRouteError } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';
import { de } from '@/locales';
// Eager, not lazy: the failure this boundary exists for IS a failing lazy
// import — a code-split fallback could fail the same way.
import { NotFoundPage } from '@/pages/NotFoundPage';

const RELOAD_ATTEMPT_KEY = 'kurrentschrift:chunk-reload-attempt';

function messageOf(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const maybe = (error as { message?: unknown }).message;
    if (typeof maybe === 'string') return maybe;
  }
  return '';
}

// The four wordings browsers use for "the module you asked for isn't there":
// Chrome/Edge, Safari, Firefox, and webpack-era bundles that still surface a
// named ChunkLoadError.
function isChunkLoadError(error: unknown): boolean {
  const message = messageOf(error);
  if (!message) return false;
  return (
    /Failed to fetch dynamically imported module/i.test(message) ||
    /Importing a module script failed/i.test(message) ||
    /error loading dynamically imported module/i.test(message) ||
    /ChunkLoadError/i.test(message)
  );
}

// sessionStorage throws in some privacy modes. Both accessors swallow — a
// missing loop guard must not itself become the error — but they fail toward
// NOT reloading: an automatic reload without a guard is the one case that can
// spin a tab forever (a stale index.html that keeps naming dead chunks would
// fail, reload, fail again, with nothing able to remember the first attempt).
function hasAttemptedReload(): boolean {
  try {
    return Boolean(sessionStorage.getItem(RELOAD_ATTEMPT_KEY));
  } catch {
    // No storage means no guard: report the attempt as already spent so the
    // visitor gets the manual button rather than a loop.
    return true;
  }
}

function markReloadAttempted(): void {
  try {
    sessionStorage.setItem(RELOAD_ATTEMPT_KEY, String(Date.now()));
  } catch {
    // Unreachable in practice — a storage that cannot be written cannot be read
    // either, so `hasAttemptedReload` has already suppressed the reload.
  }
}

export function RouteError() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  // Decided from pure reads so the render stays side-effect free; the write and
  // the reload happen in the effect below. `hasAttemptedReload` is read once at
  // mount rather than on every render for the same reason.
  const [autoReloading] = useState(() => isChunkLoadError(error) && !hasAttemptedReload());

  useEffect(() => {
    if (!autoReloading) return;
    markReloadAttempted();
    window.location.reload();
  }, [autoReloading]);

  if (notFound) return <NotFoundPage source="route_error" />;

  return (
    <PaperBackground minHeight="100dvh">
      <Box
        sx={{
          minHeight: '100dvh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          px: 3,
          textAlign: 'center',
        }}
      >
        {autoReloading ? (
          <Typography color="text.secondary">{de.common.routeError.reloading}</Typography>
        ) : (
          <>
            <Typography variant="h5">{de.common.routeError.title}</Typography>
            <Typography color="text.secondary" sx={{ maxWidth: 480 }}>
              {de.common.routeError.body}
            </Typography>
            {error instanceof Error && (
              <Typography variant="body2" color="text.disabled">
                {error.message}
              </Typography>
            )}
            <Button variant="outlined" onClick={() => window.location.reload()}>
              {de.common.routeError.reload}
            </Button>
          </>
        )}
      </Box>
    </PaperBackground>
  );
}
