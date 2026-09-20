// The strip pixels, fetched as blobs.
//
// These pixels are the reserved own-hand dataset: admin-gated, `private,
// no-store`, never in the repository. They reach the browser as blobs rather
// than as <img src> URLs, because the admin token travels as a header in dev
// and a plain image request would not send it — the same reason the Bogen PDF
// is fetched.
//
// Loaded on demand, one Fassung at a time: a strip is ~350 KB, and a hand with
// a few waves behind it would otherwise pull tens of megabytes into a view
// whose usual question is „did this row come out well".
//
// A word cut is not a second stored image. `crop_origin_mm` plus the pixel
// width give the millimetre scale, the Bogen's layout says where the word box
// sits, and the server cuts it out — which is why every word of a row is one
// click away without anything extra having been kept.

import { useEffect, useState } from 'react';

import { fetchEigenhandStrip } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';

/**
 * One strip image (whole, or one word box) as an object URL for as long as
 * the caller shows it. Revoked on every change and on unmount: the browser
 * holds the blob until then, and these are exactly the bytes that should not
 * linger. A fetch resolving after the cleanup makes no URL at all.
 */
export function useStripImage(
  hand: string,
  strip: string,
  fassung: string,
  box: number | null,
  enabled: boolean,
  ohneLineatur: boolean,
  roh = false,
  // Bumped after a Fleckenmaske is saved: the URL is unchanged but the served
  // pixels are not, and a browser has no way of knowing that.
  reload = 0,
) {
  const [url, setUrl] = useState<string | null>(null);
  // A tile that is asked for its pixels right away shows the spinner from the
  // first frame, the way the effect below used to arrange one frame later.
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<ApiErrorText | null>(null);

  // The spinner and the cleared error move to render time — React's "adjusting
  // state when a prop changes" (react-hooks/set-state-in-effect). The key
  // carries exactly the effect's inputs; the free-form word never enters it,
  // so no separator can be mistaken for a value.
  const loadKey = `${hand} ${strip} ${fassung} ${box ?? ''} ${enabled} ${ohneLineatur} ${roh} ${reload}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    // `enabled`, not `true`: a tile being CLOSED has no request to wait for,
    // and the in-flight one it leaves behind can no longer clear the spinner
    // itself — the effect's cleanup disarms its `finally`. Written here, the
    // closed tile never keeps a spinner (or the previous cut's error) standing
    // behind it.
    setLoading(enabled);
    setError(null);
  }

  useEffect(() => {
    if (!enabled) return undefined;
    let alive = true;
    let objectUrl: string | null = null;
    fetchEigenhandStrip(hand, strip, fassung, box ?? undefined, ohneLineatur, roh)
      .then((blob) => {
        if (!alive) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((err: unknown) => alive && setError(apiErrorText(err)))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      setUrl(null);
    };
  }, [hand, strip, fassung, box, enabled, ohneLineatur, roh, reload]);

  return { url, loading, error };
}
