// The written strips, as the workbench shows a chart crop today.
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

import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';

import { fetchEigenhandStrip, getEigenhandStrips } from '@/lib/api';
import type { EigenhandStrip } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

/** One stored Fassung: its metadata, and — once asked for — its pixels. */
function StripTile({ hand, row }: { hand: string; row: EigenhandStrip }) {
  const t = de.admin.eigenhand;
  const [url, setUrl] = useState<string | null>(null);
  // The box INDEX identifies the shown cut, not the word text: a row may carry
  // the same word twice (the plan does — `ja!`, `„wohl“`), and addressing it by
  // text would serve the first box under every later chip and light them all.
  const [shown, setShown] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Object URLs are revoked by hand: the browser holds the blob until then,
  // and these are exactly the bytes that should not linger.
  const objectUrl = useRef<string | null>(null);
  // Set on unmount so a fetch that resolves afterwards revokes its blob
  // instead of parking it in a dead component's ref for the page's lifetime.
  const alive = useRef(true);

  const release = useCallback(() => {
    if (objectUrl.current) {
      URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = null;
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      release();
    };
  }, [release]);

  const show = (index: number | null) => {
    setLoading(true);
    setError(null);
    fetchEigenhandStrip(hand, row.strip, row.fassung, index ?? undefined)
      .then((blob) => {
        if (!alive.current) {
          URL.revokeObjectURL(URL.createObjectURL(blob));
          return;
        }
        release();
        objectUrl.current = URL.createObjectURL(blob);
        setUrl(objectUrl.current);
        setShown(index);
      })
      .catch((err: unknown) => alive.current && setError(String(err)))
      .finally(() => alive.current && setLoading(false));
  };

  const hide = () => {
    release();
    setUrl(null);
    setShown(null);
  };

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1.5, mb: 1.5 }}>
      <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
        <Typography variant="subtitle2" sx={{ color: paper.ink }}>
          {row.strip} · {row.fassung}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.stripMeta, {
            sheet: row.sheet,
            row: row.row_index,
            width: row.width_px,
            height: row.height_px,
            dpi: Math.round(row.dpi),
          })}
        </Typography>
        {loading && <CircularProgress size={14} />}
        <Box sx={{ flexGrow: 1 }} />
        {url ? (
          <Button size="small" onClick={hide}>
            {t.stripHide}
          </Button>
        ) : (
          <Button size="small" variant="outlined" onClick={() => show(null)}>
            {t.stripShow}
          </Button>
        )}
      </Stack>

      {url && (
        <>
          <Box sx={{ mt: 1, overflowX: 'auto', bgcolor: paper.hi, borderRadius: 1 }}>
            <Box
              component="img"
              src={url}
              alt={`${row.strip} ${row.fassung}${shown === null ? '' : ` — ${row.words[shown] ?? ''}`}`}
              sx={{ display: 'block', maxWidth: 'none', height: '5.5rem' }}
            />
          </Box>
          <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', rowGap: 0.5 }}>
            <Chip
              size="small"
              label={t.stripWhole}
              variant={shown === null ? 'filled' : 'outlined'}
              onClick={() => show(null)}
            />
            {row.words.map((candidate, index) => (
              <Chip
                key={`${candidate}-${index}`}
                size="small"
                label={candidate}
                variant={shown === index ? 'filled' : 'outlined'}
                onClick={() => show(index)}
              />
            ))}
          </Stack>
        </>
      )}

      {error && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          {t.stripImagesError} {error}
        </Alert>
      )}
    </Box>
  );
}

export function StripsPanel({ hand, version }: { hand: string; version?: number }) {
  const t = de.admin.eigenhand;
  const [strips, setStrips] = useState<EigenhandStrip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getEigenhandStrips(hand, { retries: 2 })
      .then((data) => !cancelled && setStrips(data.strips))
      .catch((err: unknown) => !cancelled && setError(String(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [hand, version]);

  return (
    <Panel
      title={t.stripImagesTitle}
      caption={strips.length ? fmt(t.stripCount, { count: strips.length }) : t.stripImagesIntro}
    >
      {loading && <CircularProgress size={16} />}
      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t.stripImagesError} {error}
        </Alert>
      )}
      {!loading && !error && strips.length === 0 && (
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.stripImagesEmpty, { hand })}
        </Typography>
      )}
      {/* The hand belongs in the key: strip ids come from the frozen,
          hand-independent plan, so `S0001/F01` exists for every hand — without
          it React reuses the tile across a hand switch and keeps the previous
          hand's already-loaded pixels on screen. */}
      {strips.map((row) => (
        <StripTile key={`${hand}/${row.strip}/${row.fassung}`} hand={hand} row={row} />
      ))}
    </Panel>
  );
}
