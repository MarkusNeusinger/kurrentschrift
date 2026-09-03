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
//
// Two ways in (author, 2026-08-26): a word search, and the coverage grid —
// a glyph cell or a join chip sets an item filter, and the panel turns into a
// gallery of exactly the written words that hold it. The crops are WORD crops
// with the letter somewhere inside; cutting a word into its glyphs is the
// Tintenfolger's job (Phase 5), not the Kartei's. Every image takes the shared
// zoom, and a click opens it in the Lupe at any magnification.

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Slider,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { RefObject } from 'react';

import { fetchEigenhandStrip, getEigenhandStrips } from '@/lib/api';
import type { EigenhandStrip, EigenhandStripBox, EigenhandStripFilter } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de, fmt } from '@/locales/admin';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

// CSS pixels per stored pixel. ¼ is what the old fixed tile height came to on
// a 300-dpi strip; 1:1 shows the scan as captured.
const ZOOMS = [0.25, 0.5, 1, 2] as const;
type Zoom = (typeof ZOOMS)[number];
const ZOOM_LABELS: Record<Zoom, string> = { 0.25: '¼', 0.5: '½', 1: '1:1', 2: '2×' };
const LUPE_ZOOMS = { min: 0.5, max: 4, step: 0.25 };
const PAGE = 24;

/**
 * Does one box hold the filter — the client half of the server's strip-level
 * match (`coverage.matches_item`). Plain `toLowerCase()`, the same simple
 * mapping as the server's `str.lower()`: a locale-aware or folding variant
 * (ß → ss, the Turkish i) would let the two halves disagree.
 */
function boxMatches(box: EigenhandStripBox, filter: EigenhandStripFilter): boolean {
  if (filter.wort && !box.word.toLowerCase().includes(filter.wort.toLowerCase())) return false;
  if (filter.item) {
    const wanted = filter.item;
    if (wanted.includes('>') || wanted.includes('@')) return box.items.includes(wanted);
    return box.items.some((item) => item.startsWith(`${wanted}@`));
  }
  return true;
}

/**
 * One strip image (whole, or one word box) as an object URL for as long as
 * the caller shows it. Revoked on every change and on unmount: the browser
 * holds the blob until then, and these are exactly the bytes that should not
 * linger. A fetch resolving after the cleanup makes no URL at all.
 */
function useStripImage(
  hand: string,
  strip: string,
  fassung: string,
  box: number | null,
  enabled: boolean,
  ohneLineatur: boolean,
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
  const loadKey = `${hand} ${strip} ${fassung} ${box ?? ''} ${enabled} ${ohneLineatur}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    // Only a load arms the spinner: a tile being closed has no request to
    // wait for, exactly as the effect's early return had it.
    if (enabled) {
      setLoading(true);
      setError(null);
    }
  }

  useEffect(() => {
    if (!enabled) return undefined;
    let alive = true;
    let objectUrl: string | null = null;
    fetchEigenhandStrip(hand, strip, fassung, box ?? undefined, ohneLineatur)
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
  }, [hand, strip, fassung, box, enabled, ohneLineatur]);

  return { url, loading, error };
}

/**
 * Whether an element has come within reach of the viewport — once true, it
 * stays true. The gallery fetches a crop only then: a page of 24 tiles would
 * otherwise fire 24 cuts at the server the moment a cell is clicked, most of
 * them for rows below the fold. Without IntersectionObserver (old browsers,
 * some test runners) everything counts as in view.
 */
function useNearViewport(ref: RefObject<HTMLElement | null>): boolean {
  // The fallback is DERIVED rather than written into state from an effect
  // (react-hooks/set-state-in-effect): whether the browser can observe at all
  // is not something that happens later, so with no observer every tile counts
  // as in view from its very first render.
  const observable = typeof IntersectionObserver !== 'undefined';
  const [seen, setSeen] = useState(false);
  const near = !observable || seen;
  useEffect(() => {
    const node = ref.current;
    if (!node || near) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { rootMargin: '300px 0px' },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref, near]);
  return near;
}

interface LupeTarget {
  url: string;
  title: string;
  heightPx: number;
}

/** A strip or word image at the shared zoom; a click hands it to the Lupe. */
function StripImage({
  url,
  alt,
  heightPx,
  zoom,
  onLupe,
}: {
  url: string;
  alt: string;
  heightPx: number;
  zoom: Zoom;
  onLupe: (target: LupeTarget) => void;
}) {
  return (
    <Box sx={{ overflowX: 'auto', bgcolor: paper.hi, borderRadius: 1 }}>
      <Box
        component="img"
        src={url}
        alt={alt}
        title={alt}
        onClick={() => onLupe({ url, title: alt, heightPx })}
        sx={{ display: 'block', maxWidth: 'none', height: `${heightPx * zoom}px`, cursor: 'zoom-in' }}
      />
    </Box>
  );
}

/** One stored Fassung: its metadata, and — once asked for — its pixels. */
function StripTile({
  hand,
  row,
  zoom,
  ohneLineatur,
  onLupe,
}: {
  hand: string;
  row: EigenhandStrip;
  zoom: Zoom;
  ohneLineatur: boolean;
  onLupe: (target: LupeTarget) => void;
}) {
  const t = de.admin.eigenhand;
  // `open` says whether pixels are wanted at all; `shown` which cut. The box
  // INDEX identifies the cut, not the word text: a row may carry the same
  // word twice (the plan does — `ja!`, `„wohl“`), and addressing it by text
  // would serve the first box under every later chip and light them all.
  const [open, setOpen] = useState(false);
  const [shown, setShown] = useState<number | null>(null);
  const { url, loading, error } = useStripImage(hand, row.strip, row.fassung, shown, open, ohneLineatur);
  const title = `${row.strip} · ${row.fassung}${shown === null ? '' : ` · ${row.words[shown] ?? ''}`}`;

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
        {open ? (
          <Button size="small" onClick={() => setOpen(false)}>
            {t.stripHide}
          </Button>
        ) : (
          <Button size="small" variant="outlined" onClick={() => setOpen(true)}>
            {t.stripShow}
          </Button>
        )}
      </Stack>

      {open && (
        <>
          {url && (
            <Box sx={{ mt: 1 }}>
              <StripImage url={url} alt={title} heightPx={row.height_px} zoom={zoom} onLupe={onLupe} />
            </Box>
          )}
          <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', rowGap: 0.5 }}>
            <Chip
              size="small"
              label={t.stripWhole}
              variant={shown === null ? 'filled' : 'outlined'}
              onClick={() => setShown(null)}
            />
            {row.words.map((candidate, index) => (
              <Chip
                key={`${candidate}-${index}`}
                size="small"
                label={candidate}
                variant={shown === index ? 'filled' : 'outlined'}
                onClick={() => setShown(index)}
              />
            ))}
          </Stack>
        </>
      )}

      {error && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          <ErrorText error={error} prefix={t.stripImagesError} />
        </Alert>
      )}
    </Box>
  );
}

/** One written word that holds the filter — fetched once it comes near the viewport. */
function CropTile({
  hand,
  row,
  box,
  zoom,
  ohneLineatur,
  onLupe,
}: {
  hand: string;
  row: EigenhandStrip;
  box: EigenhandStripBox;
  zoom: Zoom;
  ohneLineatur: boolean;
  onLupe: (target: LupeTarget) => void;
}) {
  const t = de.admin.eigenhand;
  const ref = useRef<HTMLDivElement | null>(null);
  const near = useNearViewport(ref);
  const { url, loading, error } = useStripImage(hand, row.strip, row.fassung, box.index, near, ohneLineatur);
  const title = `${row.strip} · ${row.fassung} · ${box.word}`;
  return (
    <Box
      ref={ref}
      sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1, maxWidth: '100%', minHeight: '4rem' }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
        <Typography variant="caption" sx={{ color: paper.ink, fontWeight: 600 }}>
          {box.word}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {row.strip} · {row.fassung}
        </Typography>
        {loading && <CircularProgress size={12} />}
      </Stack>
      {url ? (
        <StripImage url={url} alt={title} heightPx={row.height_px} zoom={zoom} onLupe={onLupe} />
      ) : (
        // The strip's height is known before a byte arrives, so the tile takes
        // its final height at once: tiles below the fold then really ARE below
        // the fold, and the observer above decides on the true layout instead
        // of on a row of collapsed captions.
        <Box sx={{ height: `${row.height_px * zoom}px`, minWidth: '8rem', bgcolor: paper.hi, borderRadius: 1 }} />
      )}
      {/* A tile in a gallery has no room for a fold-out, so the sentence stands
          alone and the raw line rides along as the tooltip — still one hover
          away, never lost. */}
      {error && (
        <Typography variant="caption" sx={{ color: 'warning.main' }} title={error.detail}>
          {t.stripImagesError} {error.sentence}
        </Typography>
      )}
    </Box>
  );
}

/** The Lupe: one image at any magnification, panned by scrolling. */
function Lupe({ target, onClose }: { target: LupeTarget | null; onClose: () => void }) {
  const t = de.admin.eigenhand;
  const [zoom, setZoom] = useState(2);
  return (
    <Dialog open={target !== null} onClose={onClose} fullWidth maxWidth="xl">
      {target && (
        <>
          <DialogTitle sx={{ pb: 0 }}>{target.title}</DialogTitle>
          <DialogContent>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center', my: 1 }}>
              <Typography variant="caption" sx={{ color: paper.inkSoft, whiteSpace: 'nowrap' }}>
                {t.stripZoom} {zoom}×
              </Typography>
              <Slider
                size="small"
                min={LUPE_ZOOMS.min}
                max={LUPE_ZOOMS.max}
                step={LUPE_ZOOMS.step}
                value={zoom}
                onChange={(_e, value) => setZoom(Array.isArray(value) ? value[0] : value)}
                sx={{ maxWidth: '20rem' }}
                aria-label={t.stripZoom}
              />
            </Stack>
            <Box sx={{ overflow: 'auto', maxHeight: '75vh', bgcolor: paper.hi, borderRadius: 1 }}>
              <Box
                component="img"
                src={target.url}
                alt={target.title}
                sx={{ display: 'block', maxWidth: 'none', height: `${target.heightPx * zoom}px` }}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>{t.stripLupeClose}</Button>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
}

export function StripsPanel({
  hand,
  version,
  filter,
  onFilter,
  labelOf,
}: {
  hand: string;
  version?: number;
  filter: EigenhandStripFilter;
  onFilter: (next: EigenhandStripFilter) => void;
  labelOf: (item: string) => string;
}) {
  const t = de.admin.eigenhand;
  const [strips, setStrips] = useState<EigenhandStrip[]>([]);
  const [error, setError] = useState<ApiErrorText | null>(null);
  // The listing runs on the first render too, so the panel starts in its
  // loading state instead of flashing the „nothing here yet" line for a frame.
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState<Zoom>(0.25);
  // The rulings are dropped by default — what one wants to look at is the
  // hand, not the print. The stored strip keeps them (and its colour).
  const [ohneLineatur, setOhneLineatur] = useState(true);
  const [lupe, setLupe] = useState<LupeTarget | null>(null);
  const [query, setQuery] = useState(filter.wort ?? '');
  const [shownCount, setShownCount] = useState(PAGE);
  const filtered = Boolean(filter.wort || filter.item);

  // The search box debounces into the filter: every keystroke is otherwise a
  // listing request, and the listing is cheap but not free.
  useEffect(() => {
    const trimmed = query.trim();
    if ((filter.wort ?? '') === trimmed) return undefined;
    const handle = window.setTimeout(() => onFilter({ ...filter, wort: trimmed || undefined }), 300);
    return () => window.clearTimeout(handle);
  }, [query, filter, onFilter]);

  // A word filter cleared from OUTSIDE (the parent resets on a hand switch)
  // empties the box too — otherwise the debounce above would put the old
  // term straight back. Only the transition to „no word" is mirrored, so
  // typing is never overwritten by a lagging filter value; watching for that
  // transition during render is React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect).
  const [mirroredWort, setMirroredWort] = useState(filter.wort);
  if (mirroredWort !== filter.wort) {
    setMirroredWort(filter.wort);
    if (filter.wort === undefined) setQuery('');
  }

  // Same move for the listing's own resets: the key holds exactly the effect's
  // inputs, with the free-form search term last so no value can straddle a
  // separator.
  const listKey = `${hand} ${version ?? ''} ${filter.item ?? ''} ${filter.wort ?? ''}`;
  const [listedFor, setListedFor] = useState(listKey);
  if (listedFor !== listKey) {
    setListedFor(listKey);
    setLoading(true);
    setError(null);
    setShownCount(PAGE);
  }

  useEffect(() => {
    let cancelled = false;
    getEigenhandStrips(hand, { wort: filter.wort, item: filter.item }, { retries: 2 })
      .then((data) => !cancelled && setStrips(data.strips))
      .catch((err: unknown) => !cancelled && setError(apiErrorText(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [hand, version, filter.wort, filter.item]);

  // The gallery: every (strip, box) that holds the filter, in plan order. A
  // strip the server listed always contributes — should the two halves of
  // the match ever disagree on a box, the whole row is shown rather than
  // nothing, because hiding evidence the server found is the worse error.
  const belege = useMemo(
    () =>
      filtered
        ? strips.flatMap((row) => {
            const matching = row.boxes.filter((box) => boxMatches(box, filter));
            return (matching.length ? matching : row.boxes).map((box) => ({ row, box }));
          })
        : [],
    [strips, filter, filtered],
  );

  const caption = filtered
    ? fmt(t.stripBelegeCount, { count: belege.length, strips: strips.length })
    : strips.length
      ? fmt(t.stripCount, { count: strips.length })
      : t.stripImagesIntro;

  return (
    <Panel
      title={t.stripImagesTitle}
      caption={caption}
      actions={
        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
          <Tooltip title={t.stripNoRulingsHint}>
            <FormControlLabel
              control={
                <Switch size="small" checked={ohneLineatur} onChange={(e) => setOhneLineatur(e.target.checked)} />
              }
              label={<Typography variant="caption">{t.stripNoRulings}</Typography>}
              sx={{ mr: 0 }}
            />
          </Tooltip>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={zoom}
            aria-label={t.stripZoom}
            onChange={(_e, value: Zoom | null) => value && setZoom(value)}
          >
            {ZOOMS.map((level) => (
              <ToggleButton key={level} value={level} sx={{ px: 1, py: 0.25, textTransform: 'none' }}>
                {ZOOM_LABELS[level]}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>
      }
    >
      <Stack direction="row" spacing={1.5} sx={{ mb: 2, flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
        <TextField
          size="small"
          label={t.stripSearch}
          value={query}
          helperText={t.stripSearchHelp}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ minWidth: '14rem' }}
        />
        {filter.item && (
          <Chip
            label={fmt(t.stripFilterItem, { item: labelOf(filter.item) })}
            onDelete={() => onFilter({ ...filter, item: undefined })}
          />
        )}
        {filtered && (
          <Button
            size="small"
            onClick={() => {
              setQuery('');
              onFilter({});
            }}
          >
            {t.stripFilterClear}
          </Button>
        )}
        {loading && <CircularProgress size={16} />}
      </Stack>

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <ErrorText error={error} prefix={t.stripImagesError} />
        </Alert>
      )}

      {!loading && !error && strips.length === 0 && (
        <TerminalCommand
          lead={filtered ? fmt(t.stripBelegeEmpty, { hand }) : t.stripImagesEmpty}
          command={fmt(t.syncCommand, { hand })}
        />
      )}

      {filtered ? (
        <>
          {belege.length > 0 && (
            <Typography variant="caption" sx={{ display: 'block', mb: 1.5, color: paper.inkSoft }}>
              {t.stripBelegeIntro}
            </Typography>
          )}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            {/* The hand belongs in every key: strip ids come from the frozen,
                hand-independent plan, and a tile reused across a hand switch
                would keep the previous hand's pixels on screen. */}
            {belege.slice(0, shownCount).map(({ row, box }) => (
              <CropTile
                key={`${hand}/${row.strip}/${row.fassung}/${box.index}`}
                hand={hand}
                row={row}
                box={box}
                zoom={zoom}
                ohneLineatur={ohneLineatur}
                onLupe={setLupe}
              />
            ))}
          </Box>
          {belege.length > shownCount && (
            <Button size="small" sx={{ mt: 1.5 }} onClick={() => setShownCount((n) => n + PAGE)}>
              {fmt(t.stripMore, { count: Math.min(PAGE, belege.length - shownCount) })}
            </Button>
          )}
        </>
      ) : (
        strips.map((row) => (
          <StripTile
            key={`${hand}/${row.strip}/${row.fassung}`}
            hand={hand}
            row={row}
            zoom={zoom}
            ohneLineatur={ohneLineatur}
            onLupe={setLupe}
          />
        ))
      )}

      {/* Keyed by image, so every opening starts at the default scale. */}
      <Lupe key={lupe?.url ?? 'none'} target={lupe} onClose={() => setLupe(null)} />
    </Panel>
  );
}
