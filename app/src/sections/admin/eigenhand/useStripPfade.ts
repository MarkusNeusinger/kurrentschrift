// The followed pen paths of one Fassung — the data half of the Bahn layer.

import { useEffect, useState } from 'react';

import { getEigenhandPfade } from '@/lib/api';
import type { EigenhandPfad } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';

// One request per Fassung even when several tiles want it at once: the gallery
// shows a tile per matching WORD BOX, so a strip whose row holds three matching
// words would otherwise ask the same route three times in the same frame. Only
// the in-flight promise is shared — never the resolved value — so nothing here
// can serve a stale path after the follower has pushed a new one.
const pfadeInFlight = new Map<string, Promise<EigenhandPfad[] | null>>();

function fetchPfadeOnce(hand: string, strip: string, fassung: string): Promise<EigenhandPfad[] | null> {
  const key = `${hand}/${strip}/${fassung}`;
  const running = pfadeInFlight.get(key);
  if (running) return running;
  const pending = getEigenhandPfade(hand, strip, fassung)
    .then((data) => data.pfade)
    .finally(() => pfadeInFlight.delete(key));
  pfadeInFlight.set(key, pending);
  return pending;
}

/**
 * The Streifen-Pfade of one Fassung, fetched at most once and only when the
 * layer is actually switched on.
 *
 * Deliberately per Fassung and on demand, exactly like the pixels: the listing
 * carries no paths (the column is deferred server-side for the same reason),
 * and a gallery page of 24 crops must not fire 24 path requests the moment a
 * coverage cell is clicked. `null` from the server means „nobody has followed
 * this Fassung yet", which is not the same as „followed, nothing found".
 */
export function useStripPfade(hand: string, strip: string, fassung: string, enabled: boolean) {
  const [pfade, setPfade] = useState<EigenhandPfad[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiErrorText | null>(null);

  // Same render-time reset as the image hook — React's "adjusting state when a
  // prop changes" (react-hooks/set-state-in-effect).
  const loadKey = `${hand} ${strip} ${fassung} ${enabled}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setLoading(enabled);
    setError(null);
    setPfade(null);
  }

  useEffect(() => {
    if (!enabled) return undefined;
    let alive = true;
    fetchPfadeOnce(hand, strip, fassung)
      .then((rows) => alive && setPfade(rows))
      .catch((err: unknown) => alive && setError(apiErrorText(err)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [hand, strip, fassung, enabled]);

  return { pfade, loading, error };
}
