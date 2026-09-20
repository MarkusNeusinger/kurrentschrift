// Which word boxes of one hand are in which state — ONE request for the whole
// hand (`GET /eigenhand/pfade/{hand}`), without a single point of a Bahn.
//
// Lifted out of `NachfahrListe` when the gallery needed the same answer: since
// the free-standing „Maske geändert" chip gave way to the Ampel, a crop tile
// said nothing at all about the box it shows, and §7.2 wants the verdict on
// both surfaces. Two callers, one reader — the alternative was a second fetch
// with its own reset rules, which is how two surfaces start disagreeing about
// the same box.
//
// The two callers are mutually exclusive (`?ansicht=liste` shows one, `galerie`
// the other), so `enabled` keeps the surface that is NOT on screen from paying
// for a read nothing consumes.

import { useEffect, useState } from 'react';

import { getEigenhandPfadBoxes } from '@/lib/api';
import type { EigenhandPfadFassung } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';

export function useEigenhandPfadBoxes(hand: string, enabled = true) {
  const [fassungen, setFassungen] = useState<EigenhandPfadFassung[] | null>(null);
  const [error, setError] = useState<ApiErrorText | null>(null);
  // Bumped after a box was written by hand: the Ampel of that box is derived
  // from what was just stored, so the surfaces have to ask again.
  const [token, setToken] = useState(0);

  // Drop the previous hand's boxes DURING RENDER — React's "adjusting state
  // when a prop changes". Without it the new hand's name would stand over the
  // old hand's Kästen until the request lands.
  const loadKey = `${hand} ${enabled}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setFassungen(null);
    setError(null);
  }

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    getEigenhandPfadBoxes(hand, undefined, { retries: 2 })
      .then((data) => !cancelled && setFassungen(data.fassungen))
      .catch((err: unknown) => {
        if (cancelled) return;
        setFassungen(null);
        setError(apiErrorText(err));
      });
    return () => {
      cancelled = true;
    };
  }, [hand, enabled, token]);

  return { fassungen, error, reload: () => setToken((n) => n + 1) };
}
