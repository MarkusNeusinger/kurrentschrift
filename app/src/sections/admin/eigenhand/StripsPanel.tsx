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
//
// Since the Streifen-Befund (owner, 2026-09-07) every Fassung also carries its
// verdict sheet: the suggestion, the ONE reason that dominates it and its rank
// among the Fassungen of the same strip. It is a SUGGESTION — the tick on the
// paper stays the verdict, nothing here rejects anything, and „ersetzt durch
// F0n" says a later Fassung came out cleaner, not that this one stopped
// counting. Sorting by it turns the panel into the rewrite list: weakest
// first, which is the question „what do I write again" made clickable.

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

import { fetchEigenhandStrip, getEigenhandPfade, getEigenhandStrips } from '@/lib/api';
import type {
  EigenhandBefund,
  EigenhandFleck,
  EigenhandPfad,
  EigenhandStrip,
  EigenhandStripBox,
  EigenhandStripFilter,
} from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de, fmt } from '@/locales/admin';
import { VORSCHLAG_COLOR, byBefund } from '@/sections/admin/eigenhand/befundOrder';
import { FleckenEditor, MIN_ERASE_ZOOM } from '@/sections/admin/eigenhand/FleckenEditor';
import { pfadHerkunft } from '@/sections/admin/eigenhand/pfadHerkunft';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel } from '@/sections/admin/shell/Panel';
import { PathOverlay } from '@/sections/admin/shell/PathOverlay';
import type { Stroke } from '@/sections/admin/shell/pathOverlay';
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
function useStripPfade(hand: string, strip: string, fassung: string, enabled: boolean) {
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

/**
 * The followed pen paths laid over a strip image — or over one word cut out of
 * it. The stored registration is the STRIP's own pixel frame, so a word crop
 * is served by subtracting that crop's rectangle: one stored frame, both views,
 * and nothing about the crop's padding has to be remembered with the path.
 */
function PfadLayer({
  pfade,
  widthPx,
  heightPx,
  zoom,
  originX = 0,
  originY = 0,
  showIndex = false,
}: {
  pfade: EigenhandPfad[];
  widthPx: number;
  heightPx: number;
  zoom: Zoom;
  originX?: number;
  originY?: number;
  showIndex?: boolean;
}) {
  return (
    <Box
      component="svg"
      viewBox={`0 0 ${widthPx} ${heightPx}`}
      width={widthPx * zoom}
      height={heightPx * zoom}
      // Over the image, never in its way: the strip's own click opens the Lupe.
      sx={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}
    >
      {pfade.map((pfad) => {
        const xh = pfad.xh_px;
        const tx = pfad.registration_px.tx - originX;
        const baseline = pfad.registration_px.baseline_row + pfad.registration_px.ty - originY;
        return (
          <g key={pfad.box_index} transform={`matrix(${xh} 0 0 ${-xh} ${tx} ${baseline})`}>
            <PathOverlay
              strokes={pfad.strokes as Stroke[]}
              // One DISPLAYED pixel in path units — the image is scaled by the
              // shared zoom, so a hairline stays a hairline at ¼ and at 2×.
              unit={1 / (zoom * xh)}
              detail
              showIndex={showIndex}
            />
          </g>
        );
      })}
    </Box>
  );
}

/**
 * Herkunft, Datum and the honest caveats of a drawn path: the seed is the
 * chart ductus of the style, not this hand, and a Fleckenmaske edited after
 * the follow means the path read different ink than the picture now shows.
 */
function PfadCaption({ pfade, flecken }: { pfade: EigenhandPfad[]; flecken: EigenhandFleck[] | null | undefined }) {
  const t = de.admin.eigenhand;
  // Herkunft belongs to the single path, not to the list: a Fassung can hold
  // paths from several runs, so a Verfahren and a day are named only while
  // every drawn path agrees on them — picking one word narrows `pfade` to that
  // word, and the line becomes its own provenance. A mixed list says so and
  // carries the per-word detail in its tooltip, instead of letting the first
  // entry speak for the others (Copilot review, PR #598).
  const herkunft = pfadHerkunft(pfade, t.pfadNoDate);
  const stale = pfade.some((p) => typeof p.flecken_n === 'number' && flecken != null && p.flecken_n !== flecken.length);
  const pedigree = (
    <Typography variant="caption" sx={{ color: paper.inkSoft }}>
      {herkunft.gemischt
        ? fmt(t.pfadPedigreeMixed, { woerter: pfade.length })
        : fmt(t.pfadPedigree, {
            verfahren: herkunft.verfahren ?? '',
            datum: herkunft.datum ?? '',
            woerter: pfade.length,
          })}
    </Typography>
  );
  return (
    <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap', rowGap: 0.5, alignItems: 'center' }}>
      {herkunft.gemischt ? (
        <Tooltip title={<Box sx={{ whiteSpace: 'pre-line' }}>{[t.pfadMixedHint, ...herkunft.laeufe].join('\n')}</Box>}>
          {pedigree}
        </Tooltip>
      ) : (
        pedigree
      )}
      <Tooltip title={t.pfadSeedHint}>
        <Chip size="small" variant="outlined" label={t.pfadSeed} />
      </Tooltip>
      {stale && (
        <Tooltip title={t.pfadStaleHint}>
          <Chip size="small" color="warning" variant="outlined" label={t.pfadStale} />
        </Tooltip>
      )}
    </Stack>
  );
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

function num(value: unknown, digits = 1): string {
  return typeof value === 'number' ? value.toFixed(digits) : '–';
}

/**
 * One Fassung's verdict sheet as chips: the suggestion, the dominant reason,
 * the rank among its strip's Fassungen, and — where a later Fassung came out
 * cleaner — that it has been superseded. A Fassung filed before the Befund
 * existed says so rather than showing a blank: a missing reading is not a bad
 * reading, and it must not look like one.
 */
function BefundChips({ befund }: { befund: EigenhandBefund | null | undefined }) {
  const t = de.admin.eigenhand;
  if (!befund) {
    return (
      <Tooltip title={t.befundNoneHint}>
        <Chip size="small" variant="outlined" label={t.befundNone} />
      </Tooltip>
    );
  }
  const tooltip = fmt(t.befundTooltip, {
    guete: num(befund.guete),
    feder: `${Math.round(Number(befund.nib?.zur_hand ?? 1) * 100)} %`,
    knick: num(befund.unstetigkeit?.kink_max_deg),
    knicke: String(befund.unstetigkeit?.kink_count ?? 0),
    wackler: num(befund.unstetigkeit?.wobble),
    kringel: String((befund.kringel?.zu as number | undefined) ?? 0),
  });
  return (
    <>
      <Tooltip title={tooltip}>
        <Chip size="small" color={VORSCHLAG_COLOR[befund.vorschlag]} label={befund.vorschlag} />
      </Tooltip>
      <Chip size="small" variant="outlined" label={befund.grund} />
      {befund.rang !== null && befund.von !== null && befund.von > 1 && (
        <Chip size="small" variant="outlined" label={fmt(t.befundRank, { rang: befund.rang, von: befund.von })} />
      )}
      {befund.abgeloest_von && (
        <Tooltip title={t.befundReplacedHint}>
          <Chip
            size="small"
            variant="outlined"
            color="info"
            label={fmt(t.befundReplaced, { fassung: befund.abgeloest_von })}
          />
        </Tooltip>
      )}
    </>
  );
}


/**
 * A strip or word image at the shared zoom; a click hands it to the Lupe.
 *
 * `overlay` is drawn ON TOP at the same scale — the Streifen-Pfad, which is
 * positioned in the image's own pixels and therefore has to travel with it
 * through the zoom and the horizontal scroll.
 */
function StripImage({
  url,
  alt,
  heightPx,
  zoom,
  onLupe,
  overlay,
}: {
  url: string;
  alt: string;
  heightPx: number;
  zoom: Zoom;
  onLupe: (target: LupeTarget) => void;
  overlay?: React.ReactNode;
}) {
  return (
    <Box sx={{ overflowX: 'auto', bgcolor: paper.hi, borderRadius: 1 }}>
      <Box sx={{ position: 'relative', display: 'inline-block', lineHeight: 0 }}>
        <Box
          component="img"
          src={url}
          alt={alt}
          title={alt}
          onClick={() => onLupe({ url, title: alt, heightPx })}
          sx={{ display: 'block', maxWidth: 'none', height: `${heightPx * zoom}px`, cursor: 'zoom-in' }}
        />
        {overlay}
      </Box>
    </Box>
  );
}

/** One stored Fassung: its metadata, and — once asked for — its pixels. */
function StripTile({
  hand,
  row,
  zoom,
  ohneLineatur,
  pfade: wantPfade,
  onLupe,
  onZoom,
  onFlecken,
}: {
  hand: string;
  row: EigenhandStrip;
  zoom: Zoom;
  ohneLineatur: boolean;
  pfade: boolean;
  onLupe: (target: LupeTarget) => void;
  onZoom: (level: Zoom) => void;
  onFlecken: (strip: string, fassung: string, circles: EigenhandFleck[]) => void;
}) {
  const t = de.admin.eigenhand;
  // `open` says whether pixels are wanted at all; `shown` which cut. The box
  // INDEX identifies the cut, not the word text: a row may carry the same
  // word twice (the plan does — `ja!`, `„wohl“`), and addressing it by text
  // would serve the first box under every later chip and light them all.
  const [open, setOpen] = useState(false);
  const [shown, setShown] = useState<number | null>(null);
  // The eraser works on the WHOLE strip: the mask's millimetres are the
  // strip's own, and a word cut would put them against another origin.
  const [erasing, setErasing] = useState(false);
  const [roh, setRoh] = useState(false);
  const [reload, setReload] = useState(0);
  const { url, loading, error } = useStripImage(
    hand,
    row.strip,
    row.fassung,
    erasing ? null : shown,
    open,
    // „roh" promises the FILED bytes, so it has to switch the ruling view off
    // too — a raw strip still run through `without_rulings` is a derived image
    // like any other, and the promise would be false (Copilot review, PR #568).
    ohneLineatur && !roh,
    roh,
    reload,
  );
  // The paths are asked for only while the layer is on and the tile is open —
  // and never at all while the brush is out, where the picture is the raw
  // strip and a path over it would only be in the way.
  const showPfade = wantPfade && open && !erasing;
  const pfade = useStripPfade(hand, row.strip, row.fassung, showPfade);
  const title = `${row.strip} · ${row.fassung}${shown === null ? '' : ` · ${row.words[shown] ?? ''}`}`;
  const flecken = row.flecken ?? [];
  // A word cut needs its own frame; the box rectangle comes from the listing.
  const cut = shown === null ? null : (row.boxes[shown]?.rect_px ?? null);
  const drawn = (pfade.pfade ?? []).filter((p) => shown === null || p.box_index === shown);
  // A word cut without a box rectangle cannot carry an overlay at all — an old
  // Bogen has no cut geometry to place one against. That is a state of its
  // own: without it a stored path for exactly this word would be silently
  // suppressed and the tile would look as if the layer had not worked (review
  // of PR #598). CropTile has always said it out loud; so does this one now.
  const placeable = shown === null || cut !== null;

  const startErasing = () => {
    setShown(null);
    setOpen(true);
    // The brush has to be aimable: at ¼ the smallest one is under a display
    // pixel across. The zoom is lifted rather than the brush grown — a brush
    // size is a millimetre fact about the paper.
    if (zoom < MIN_ERASE_ZOOM) onZoom(MIN_ERASE_ZOOM);
    setErasing(true);
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
        <BefundChips befund={row.befund} />
        {flecken.length > 0 && !erasing && (
          <Tooltip title={t.fleckenChipHint}>
            <Chip size="small" variant="outlined" label={fmt(t.fleckenChip, { count: flecken.length })} />
          </Tooltip>
        )}
        <Box sx={{ flexGrow: 1 }} />
        {!erasing && (
          <Tooltip title={t.fleckenStartHint}>
            <Button size="small" onClick={startErasing}>
              {t.fleckenStart}
            </Button>
          </Tooltip>
        )}
        {open ? (
          <Button size="small" onClick={() => setOpen(false)} disabled={erasing}>
            {t.stripHide}
          </Button>
        ) : (
          <Button size="small" variant="outlined" onClick={() => setOpen(true)}>
            {t.stripShow}
          </Button>
        )}
      </Stack>

      {open && erasing && (
        <FleckenEditor
          // Keyed by the Fassung alone: the editor takes the stored list when
          // the mode opens and owns it from there, so a save must not remount
          // it out from under its own confirmation.
          key={`${row.strip}/${row.fassung}`}
          hand={hand}
          strip={row.strip}
          fassung={row.fassung}
          url={url}
          widthPx={row.width_px}
          heightPx={row.height_px}
          dpi={row.dpi}
          zoom={zoom}
          initial={flecken}
          roh={roh}
          onRoh={setRoh}
          onClose={() => {
            setErasing(false);
            setRoh(false);
          }}
          onSaved={(circles) => {
            onFlecken(row.strip, row.fassung, circles);
            // The URL has not changed but the served pixels have.
            setReload((n) => n + 1);
          }}
        />
      )}

      {open && !erasing && (
        <>
          {url && (
            <Box sx={{ mt: 1 }}>
              <StripImage
                url={url}
                alt={title}
                heightPx={row.height_px}
                zoom={zoom}
                onLupe={onLupe}
                overlay={
                  drawn.length > 0 && placeable ? (
                    <PfadLayer
                      pfade={drawn}
                      widthPx={cut ? cut[2] - cut[0] : row.width_px}
                      heightPx={cut ? cut[3] - cut[1] : row.height_px}
                      zoom={zoom}
                      originX={cut ? cut[0] : 0}
                      originY={cut ? cut[1] : 0}
                      showIndex={shown !== null}
                    />
                  ) : undefined
                }
              />
            </Box>
          )}
          {showPfade && (
            <>
              {pfade.loading && <CircularProgress size={12} sx={{ mt: 1 }} />}
              {drawn.length > 0 && placeable && <PfadCaption pfade={drawn} flecken={row.flecken} />}
              {/* The empty answers are DIFFERENT and each is said out loud:
                  `null` is „nobody has followed this Fassung", an empty result
                  is „followed, nothing came back", a row with paths but none
                  for the word currently shown is a third — and a word cut
                  without a box rectangle is a fourth, where even a stored path
                  cannot be placed. A silent picture would make all four look
                  alike. */}
              {!pfade.loading && !pfade.error && (!placeable || drawn.length === 0) && (
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.inkSoft }}>
                  {!placeable
                    ? t.pfadNoBox
                    : pfade.pfade === null
                      ? t.pfadNone
                      : pfade.pfade.length === 0
                        ? t.pfadEmpty
                        : t.pfadNotInBox}
                </Typography>
              )}
              {pfade.error && (
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: 'warning.main' }}>
                  {t.pfadError} {pfade.error.sentence}
                </Typography>
              )}
            </>
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
  pfade: wantPfade,
  onLupe,
}: {
  hand: string;
  row: EigenhandStrip;
  box: EigenhandStripBox;
  zoom: Zoom;
  ohneLineatur: boolean;
  pfade: boolean;
  onLupe: (target: LupeTarget) => void;
}) {
  const t = de.admin.eigenhand;
  const ref = useRef<HTMLDivElement | null>(null);
  const near = useNearViewport(ref);
  const { url, loading, error } = useStripImage(hand, row.strip, row.fassung, box.index, near, ohneLineatur);
  // Gated on the SAME „near the viewport" the image is: with the layer on, a
  // page of 24 tiles asks for exactly the paths of the tiles one can see.
  const cut = box.rect_px ?? null;
  const pfade = useStripPfade(hand, row.strip, row.fassung, wantPfade && near && cut !== null);
  const drawn = (pfade.pfade ?? []).filter((p) => p.box_index === box.index);
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
        <StripImage
          url={url}
          alt={title}
          heightPx={row.height_px}
          zoom={zoom}
          onLupe={onLupe}
          overlay={
            drawn.length > 0 && cut ? (
              <PfadLayer
                pfade={drawn}
                widthPx={cut[2] - cut[0]}
                heightPx={cut[3] - cut[1]}
                zoom={zoom}
                originX={cut[0]}
                originY={cut[1]}
                showIndex
              />
            ) : undefined
          }
        />
      ) : (
        // The strip's height is known before a byte arrives, so the tile takes
        // its final height at once: tiles below the fold then really ARE below
        // the fold, and the observer above decides on the true layout instead
        // of on a row of collapsed captions.
        <Box sx={{ height: `${row.height_px * zoom}px`, minWidth: '8rem', bgcolor: paper.hi, borderRadius: 1 }} />
      )}
      {/* The layer is on and nothing is drawn: say WHICH of the empty answers
          this is, rather than leaving the tile looking as if the switch had
          not worked. */}
      {wantPfade && drawn.length === 0 && !pfade.loading && !pfade.error && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.inkSoft }}>
          {cut === null ? t.pfadNoBox : pfade.pfade === null ? t.pfadNoneShort : t.pfadNotInBox}
        </Typography>
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
  // Off by default: the first question about a strip is „ist die Zeile gut
  // geworden", and a path over every open tile would answer a different one.
  // It also costs a request per shown Fassung, so it stays a deliberate act.
  const [pfade, setPfade] = useState(false);
  const [lupe, setLupe] = useState<LupeTarget | null>(null);
  const [query, setQuery] = useState(filter.wort ?? '');
  const [shownCount, setShownCount] = useState(PAGE);
  // Off by default: the listing's own order (strip, then Fassung) is what one
  // reads when looking for a particular row. The Befund order answers the
  // other question — what to write again — and is one click away.
  const [byWeakest, setByWeakest] = useState(false);
  // Bumped when a Fleckenmaske is saved: the server re-measures the Befund
  // against it, and everything the tiles show about quality is derived from
  // that measurement.
  const [refresh, setRefresh] = useState(0);
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
  }, [hand, version, filter.wort, filter.item, refresh]);

  // A saved Fleckenmaske lands straight in the listed row — the tile is the
  // authority on the mask it just wrote — and then the listing is fetched
  // again: the server RE-MEASURES the Streifen-Befund against the new mask,
  // and the suggestion, the reason and the rank are all derived from it, so
  // keeping the old ones on screen would show a verdict about ink that is no
  // longer there.
  const applyFlecken = (strip: string, fassung: string, circles: EigenhandFleck[]) => {
    setStrips((rows) =>
      rows.map((row) => (row.strip === strip && row.fassung === fassung ? { ...row, flecken: circles } : row)),
    );
    setRefresh((n) => n + 1);
  };

  // The listing's order — plan order, or weakest first when the switch is on.
  // BOTH display modes read it: the tiles below and the filtered gallery, so
  // the switch means the same thing whether or not a filter is active.
  const listed = useMemo(() => (byWeakest ? [...strips].sort(byBefund) : strips), [strips, byWeakest]);

  // The gallery: every (strip, box) that holds the filter. A strip the server
  // listed always contributes — should the two halves of the match ever
  // disagree on a box, the whole row is shown rather than nothing, because
  // hiding evidence the server found is the worse error.
  const belege = useMemo(
    () =>
      filtered
        ? listed.flatMap((row) => {
            const matching = row.boxes.filter((box) => boxMatches(box, filter));
            return (matching.length ? matching : row.boxes).map((box) => ({ row, box }));
          })
        : [],
    [listed, filter, filtered],
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
          <Tooltip title={t.befundSortHint}>
            <FormControlLabel
              control={<Switch size="small" checked={byWeakest} onChange={(e) => setByWeakest(e.target.checked)} />}
              label={<Typography variant="caption">{t.befundSort}</Typography>}
              sx={{ mr: 0 }}
            />
          </Tooltip>
          <Tooltip title={t.pfadShowHint}>
            <FormControlLabel
              control={<Switch size="small" checked={pfade} onChange={(e) => setPfade(e.target.checked)} />}
              label={<Typography variant="caption">{t.pfadShow}</Typography>}
              sx={{ mr: 0 }}
            />
          </Tooltip>
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
                pfade={pfade}
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
        listed.map((row) => (
          <StripTile
            key={`${hand}/${row.strip}/${row.fassung}`}
            hand={hand}
            row={row}
            zoom={zoom}
            ohneLineatur={ohneLineatur}
            pfade={pfade}
            onLupe={setLupe}
            onZoom={setZoom}
            onFlecken={applyFlecken}
          />
        ))
      )}

      {/* Keyed by image, so every opening starts at the default scale. */}
      <Lupe key={lupe?.url ?? 'none'} target={lupe} onClose={() => setLupe(null)} />
    </Panel>
  );
}
