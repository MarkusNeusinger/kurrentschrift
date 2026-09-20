// The Landmarken-Linse (`docs/proposals/optimierungs-werkbank.md` §8): what the
// structure detectors see in one letter, shown ON the written form so the
// author can point at it instead of describing it — and complain about it.
//
// The doctrine's reason for existing at all (§3): the landmark layer is
// GENERATED, so it may only ever be flagged, never hand-patched. Nothing on
// this panel writes geometry; the one action it offers is „Bemängeln".
//
// Three things it deliberately shows rather than hides:
//   * a letter in which nothing is detected says so, instead of a blank glyph;
//   * a Kringel the frozen catalogue knows but no detector found stays visible
//     as an unmatched row (the `t`, whose three plate counters have no loop
//     range at all);
//   * a missing marker can be reported at all — „hier fehlt eine Marke" —
//     either by clicking the empty area (which pins the exact place) or from
//     the button below the letter, which files the same complaint without a
//     position. The button is not a fallback for the mouse: it is the KEYBOARD
//     path, and the report it files is the one that must not be lost.

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { getLandmarks } from '@/lib/api';
import type { GlyphLandmarksOut, LandmarkOut, TemplateLandmarksOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { LandmarkOverlay } from '@/sections/admin/letters/LandmarkOverlay';
import { landmarkColors } from '@/sections/admin/overlayColors';
import { landmarkKey, type LandmarkRef } from '@/sections/admin/shell/model';
import { hitArea } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

// The lens draws bigger than the small faces above it: the markers carry a
// 44 px hit area (design-system.md §9.3), and at the 190 px face height that
// target would swallow its own neighbours on a letter with an ascender.
const LENS_H = 320;
// A definite cap, never `Infinity`: `WrittenGlyph` derives its width from the
// room its parent offers, so "let height decide" plus a shrink-to-fit parent is
// a ratchet — one click re-measured the box and the letter grew each round.
const LENS_MAX_W = 420;

// Legend order — reading order of the ductus, not alphabetical: what the pen
// does (Absetzen, Umkehrecke), then what the path does to itself (Kreuzung,
// Retrace, Berührung, Verschmelzung), then what it encloses (Kringel).
const KIND_ORDER = ['lift', 'corner', 'crossing', 'retrace', 'touch', 'overlap', 'loop'] as const;

interface Props {
  sourceId: string;
  glyphKey: string;
  cacheBust?: number;
  onMark: (glyphKey: string, variant: number, landmark: LandmarkRef) => void;
}

export function LandmarkPanel({ sourceId, glyphKey, cacheBust, onMark }: Props) {
  const t = de.admin.letters;
  const [data, setData] = useState<GlyphLandmarksOut | null>(null);
  const [error, setError] = useState(false);
  const [variant, setVariant] = useState(0);
  const [selected, setSelected] = useState<LandmarkOut | null>(null);
  const [hidden, setHidden] = useState<ReadonlySet<string>>(() => new Set());

  // Retire the previous letter's payload DURING RENDER (React's "adjusting
  // state when a prop changes"), so the overlay never paints one frame of the
  // last letter's markers over this one's ink.
  //
  // A SPACE separates the two parts, and it is unambiguous because neither a
  // source id nor a glyph key may contain one. The first draft used a raw NUL
  // byte, which made git classify this whole file as BINARY — no diff of it
  // rendered, for a reviewer or for Copilot. `WrittenGlyph.tsx` carries the
  // same scar and escapes its separator as `\0` for exactly this reason.
  const loadKey = `${sourceId} ${glyphKey}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setData(null);
    setError(false);
    setSelected(null);
    setVariant(0);
  }

  useEffect(() => {
    let cancelled = false;
    getLandmarks(sourceId, glyphKey)
      .then((out) => {
        if (!cancelled) setData(out);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, glyphKey]);

  const row: TemplateLandmarksOut | undefined = useMemo(
    () => data?.rows.find((r) => r.variant === variant) ?? data?.rows[0],
    [data, variant],
  );
  const shownKinds = useMemo(() => new Set(KIND_ORDER.filter((kind) => !hidden.has(kind))), [hidden]);
  const present = useMemo(() => {
    const counts = new Map<string, number>();
    for (const lm of row?.landmarks ?? []) counts.set(lm.kind, (counts.get(lm.kind) ?? 0) + 1);
    return counts;
  }, [row]);

  if (error) return <Alert severity="warning">{t.landmarksError}</Alert>;
  if (!data || !row) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={18} />
        <Typography variant="caption">{t.landmarksLoading}</Typography>
      </Box>
    );
  }

  const toggleKind = (kind: string) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });

  const mark = (ref: LandmarkRef) => onMark(glyphKey, row.variant, ref);
  const markSpot = (at?: { x: number; y: number }) => {
    setSelected(null);
    mark({ kind: 'spot', index: null, ...at, numbers: {} });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      {/* Which stored row is under the lens. Only offered where a Laufform
          exists — most letters have none, and that is information. */}
      {data.rows.length > 1 && (
        <ToggleButtonGroup
          size="small"
          exclusive
          value={row.variant}
          onChange={(_e, next) => {
            if (next === null) return;
            setVariant(next);
            setSelected(null);
          }}
          aria-label={t.landmarksTitle}
        >
          {data.rows.map((r) => (
            <ToggleButton key={r.variant} value={r.variant} sx={{ textTransform: 'none', py: 0.75 }}>
              {r.variant === 0 ? t.landmarksRowChart : t.landmarksRowLaufform}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      )}

      {/* Letter left, legend and numbers right on a wide screen; stacked below
          it. The glyph's own box must NOT hug its content — `WrittenGlyph`
          sizes itself from the room its PARENT offers, so a shrink-to-fit
          parent and a height-driven child ratchet each other open. */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(280px, 420px) 1fr' },
          gap: 2,
          alignItems: 'start',
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
          <Box
            sx={{
              bgcolor: '#fff',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1,
              display: 'flex',
              justifyContent: 'center',
              minWidth: 0,
            }}
          >
            <WrittenGlyph
              key={`landmarks-${glyphKey}-${row.variant}`}
              glyphKey={glyphKey}
              sourceId={sourceId}
              variant={row.variant}
              height={LENS_H}
              maxWidth={LENS_MAX_W}
              cacheBust={cacheBust}
              tight
              animate={false}
              overlay={(frame) => (
                <LandmarkOverlay
                  row={row}
                  frame={frame}
                  shown={shownKinds}
                  selectedKey={selected ? landmarkKey(selected) : null}
                  onSelect={setSelected}
                  onSpot={(x, y) => markSpot({ x, y })}
                />
              )}
            />
          </Box>
          {/* The keyboard's way to the same complaint. It files WITHOUT a
              position rather than inventing one — the author says in words
              where the marker is missing, and „x 0 y 0" would be a measurement
              that never happened. */}
          <Button size="small" sx={{ alignSelf: 'flex-start', minHeight: 44 }} onClick={() => markSpot()}>
            {`⚑ ${t.landmarkSpotButton}`}
          </Button>
          <Typography variant="caption" color="textSecondary">
            {t.landmarkSpotHint}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25, minWidth: 0 }}>
          {row.landmarks.length === 0 && <Alert severity="info">{t.landmarksNone}</Alert>}

          {/* Legend AND filter in one control: a chip names the colour, says
              how many of that kind were found, and switches the layer off. */}
          <Box>
            <Stack direction="row" spacing={0.5} sx={{ mb: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
              <Typography variant="caption" color="textSecondary">
                {`${t.landmarksLegend} · ${fmt(t.landmarksCount, { count: row.landmarks.length })}`}
              </Typography>
              {/* What the seven kinds MEAN hung as a native `title=` on each
                  chip — hover only, so neither the keyboard nor the tablet ever
                  saw a definition (V25, design-system.md §9.4). Seven tooltips
                  are also seven copies of one subject: the legend explains the
                  legend, once, from a real button (§9.4 „ein Gegenstand, eine
                  Marke"). */}
              <InfoHint title={t.landmarkKindsTitle} label={t.landmarkKindsAria}>
                <Stack spacing={0.75}>
                  {KIND_ORDER.map((kind) => (
                    <Typography key={kind} variant="body2">
                      <Box component="span" sx={{ color: paper.ink, fontWeight: 600 }}>
                        {t.landmarkKind[kind]}
                      </Box>
                      {` — ${t.landmarkKindHint[kind]}`}
                    </Typography>
                  ))}
                </Stack>
              </InfoHint>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, rowGap: 1.5 }}>
              {KIND_ORDER.map((kind) => {
                const count = present.get(kind) ?? 0;
                const off = hidden.has(kind);
                return (
                  <Chip
                    key={kind}
                    size="small"
                    clickable
                    variant={off ? 'outlined' : 'filled'}
                    onClick={() => toggleKind(kind)}
                    aria-pressed={!off}
                    label={`${t.landmarkKind[kind]} · ${count}`}
                    sx={{
                      height: 32,
                      borderColor: landmarkColors[kind],
                      color: off ? 'text.secondary' : '#fff',
                      bgcolor: off ? 'transparent' : landmarkColors[kind],
                      opacity: count === 0 ? 0.55 : 1,
                      '&:hover': { bgcolor: off ? 'action.hover' : landmarkColors[kind] },
                      ...hitArea(),
                    }}
                  />
                );
              })}
            </Box>
          </Box>

          <Divider />

          {selected ? (
            <LandmarkDetail landmark={selected} onMark={() => mark(refOf(selected))} />
          ) : (
            <Typography variant="caption" color="textSecondary">
              {t.landmarkSelectHint}
            </Typography>
          )}
        </Box>
      </Box>

      {/* The catalogue's own voice: which hand it was read on, or that it has
          nothing to say about this Vorlage. */}
      <Typography variant="caption" color="textSecondary">
        {data.catalogue.available
          ? fmt(t.landmarksCatalogueOn, { style: data.catalogue.style ?? '?', root: data.catalogue.root ?? '?' })
          : t.landmarksCatalogueOff}
      </Typography>

      {row.unmatched_catalogue.length > 0 && (
        <Alert severity="info" sx={{ '& .MuiAlert-message': { width: '100%' } }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {t.landmarksUnmatchedTitle}
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
            {t.landmarksUnmatchedBody}
          </Typography>
          <Stack spacing={0.5}>
            {row.unmatched_catalogue.map((entry) => (
              <Box key={entry.loop} sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Typography variant="caption">
                  {fmt(t.landmarksUnmatchedRow, {
                    loop: entry.loop,
                    size: entry.size_class,
                    state: entry.state,
                  })}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {t.landmarkNoRange}
                </Typography>
                <Button
                  size="small"
                  sx={{ minHeight: 44 }}
                  // No position: this loop is exactly the one the detectors did
                  // NOT find, so there is nowhere to point at.
                  onClick={() =>
                    mark({
                      kind: 'loop',
                      index: entry.loop,
                      numbers: {
                        katalog: 'nicht zugeordnet',
                        size_class: entry.size_class,
                        state: entry.state,
                        d0_plate: entry.d0_plate,
                        occurrences: entry.occurrences,
                        with_counter: entry.with_counter,
                      },
                    })
                  }
                >
                  {t.landmarkMark}
                </Button>
              </Box>
            ))}
          </Stack>
        </Alert>
      )}
    </Box>
  );
}

function LandmarkDetail({ landmark, onMark }: { landmark: LandmarkOut; onMark: () => void }) {
  const t = de.admin.letters;
  const numbers = Object.entries(landmark.numbers).filter(([, value]) => value !== null && value !== undefined);
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <Box aria-hidden sx={{ width: 14, height: 14, borderRadius: '50%', bgcolor: landmarkColors[landmark.kind] }} />
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {`${t.landmarkKind[landmark.kind]} #${landmark.index}`}
        </Typography>
        <Typography variant="caption" color="textSecondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
          {`x ${landmark.x.toFixed(3)} · y ${landmark.y.toFixed(3)}`}
        </Typography>
      </Box>
      <Typography variant="caption" color="textSecondary">
        {t.landmarkKindHint[landmark.kind]}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, rowGap: 0.75 }}>
        {numbers.map(([key, value]) => (
          <Chip
            key={key}
            size="small"
            variant="outlined"
            label={`${t.landmarkNumber[key as keyof typeof t.landmarkNumber] ?? key}: ${formatValue(value)}`}
            sx={{ fontVariantNumeric: 'tabular-nums' }}
          />
        ))}
        {landmark.kind === 'loop' && landmark.numbers.anchor_range == null && (
          <Chip size="small" variant="outlined" color="warning" label={t.landmarkNoRange} />
        )}
      </Box>
      <Button size="small" variant="outlined" sx={{ alignSelf: 'flex-start', minHeight: 44 }} onClick={onMark}>
        {`⚑ ${t.landmarkMark}`}
      </Button>
    </Box>
  );
}

const refOf = (landmark: LandmarkOut): LandmarkRef => ({
  kind: landmark.kind,
  index: landmark.index,
  x: landmark.x,
  y: landmark.y,
  numbers: landmark.numbers,
});

function formatValue(value: number | string | boolean | null): string {
  if (typeof value === 'boolean') return value ? 'ja' : 'nein';
  // Cap at four decimals — the payload's own precision — but drop the trailing
  // zeros `toFixed` adds back: an angle the detector rounded to 80.6 read as
  // „80.6000", which claims three digits nobody measured.
  if (typeof value === 'number') return String(Number(value.toFixed(4)));
  return String(value);
}
