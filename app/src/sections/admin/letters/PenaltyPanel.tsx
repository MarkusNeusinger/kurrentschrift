// The Abzugs-Linse (`docs/proposals/optimierungs-werkbank.md` §9): WHERE the
// Gleichzug score takes its points off one letter, drawn over the Tafel-
// Ausschnitt the ruler measured in — so „Ecken 0.17" in the work list becomes a
// square on a corner the author can point at.
//
// What it is NOT (author decision 2026-09-23, Fable verdict „wie empfohlen"):
//   * a defect list. The subtitle says it — „Wo das Lineal abzieht — kein
//     Fehlerbefund." The ruler is not the eye (the author's Leitsatz of
//     2026-09-06), so no local threshold turns a number into a verdict here;
//   * a writing surface. Nothing on this panel writes geometry or re-derives;
//     its one action is ⚑, which files a plain LETTER item with a head the lens
//     writes (`shell/model.ts` `penaltyNoteHead`);
//   * a second metric. It shows TODAY's re-score of the stored chart row and
//     says so („neu gemessen"); where the list's stamped value differs by more
//     than the list's own epsilon, the stamp stands beside it („gespeichert").
//
// Three honesty rules carried over from the Landmarken-Linse: a term that never
// applied reads „nicht anwendbar", never 0; what counts but has no place is a
// row „ohne Ort", never paint; a script whose metric has no categories gets the
// sentence the list already uses, never a borrowed legend.
//
// It loads only when opened (the letter view mounts it in an `unmountOnExit`
// collapse): the re-score reloads, binarizes and skeletonizes the chart, 0.3 to
// 2.5 s per letter.

import { Alert, Box, Button, ButtonBase, Chip, CircularProgress, Divider, Stack, Typography } from '@mui/material';
import { visuallyHidden } from '@mui/utils';
import { useEffect, useMemo, useRef, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { useElementSize } from '@/hooks/useElementSize';
import { useRovingList } from '@/hooks/useRovingList';
import { cropUrl, getPenaltySites } from '@/lib/api';
import type { PenaltyCategoryKey, PenaltyCategoryOut, PenaltySiteOut, PenaltySitesOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import {
  PenaltyContextIcon,
  PenaltyOverlay,
  PenaltyPins,
  PenaltyShapeIcon,
} from '@/sections/admin/letters/PenaltyOverlay';
import {
  CATEGORY_SHAPE,
  categoryChips,
  coveragePart,
  formatNumber,
  fourPlaces,
  isLocated,
  lensScale,
  listedSites,
  PENALTY_CATEGORIES,
  penaltyRefOf,
  pinRank,
  revealCategory,
  sharePercent,
  shownPins,
  siteKey,
  siteKindLabel,
  siteShape,
  stampDrift,
  toggleCategory,
  verticalExaggeration,
} from '@/sections/admin/letters/penaltyLens';
import { apiErrorText, type ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { penaltyLabel, type PenaltyRef } from '@/sections/admin/shell/model';
import { hitArea, TOUCH_TARGET } from '@/styles/hitArea';
import { paper, penalty, penaltyCropAlpha } from '@/styles/paper';

// The crop is scaled UP to fit: two to five times its size on a desktop, which
// is what lets a 44 px touch target sit between neighbouring marks. The height
// cap keeps a tall letter (f, ſ) from pushing the lists off the screen; the
// scale cap keeps a tiny crop from turning into a wall of pixel blocks.
const LENS_MAX_H = 540;
const LENS_MAX_SCALE = 5;
// Room the image frame's own padding and border take from the column.
const FRAME_INSET = 18;
// A legend chip may WRAP: „Deckungslücke 0.1981 · 42 Stellen · 0.0658 ohne
// Ort" is wider than a phone, and MUI's default single line cut the one number
// that says how much has no place. 32 px plus the 12 px row gap is the 44 px
// the hit area needs (design-system.md §9.3, „Die Zeilenteilung zählt mit").
const CHIP_SX = {
  height: 'auto',
  minHeight: 32,
  fontVariantNumeric: 'tabular-nums',
  '& .MuiChip-label': { whiteSpace: 'normal', py: 0.5 },
} as const;

type Located = { category: PenaltyCategoryKey; site: PenaltySiteOut };

type Props = {
  sourceId: string;
  glyphKey: string;
  cacheBust?: number;
  onMark: (ref: PenaltyRef) => void;
};

export function PenaltyPanel({ sourceId, glyphKey, cacheBust, onMark }: Props) {
  const t = de.admin.letters.penalties;
  const [data, setData] = useState<PenaltySitesOut | null>(null);
  const [error, setError] = useState<ApiErrorText | null>(null);

  // Retire the previous letter's payload DURING RENDER (React's "adjusting
  // state when a prop changes"), so the overlay never paints one frame of the
  // last letter's marks over this one's crop. A space separates the parts —
  // `LandmarkPanel.tsx` says why it is not a NUL byte.
  const loadKey = `${sourceId} ${glyphKey} ${cacheBust ?? ''}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setData(null);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;
    getPenaltySites(sourceId, glyphKey)
      .then((out) => {
        if (!cancelled) setData(out);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(apiErrorText(e));
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, glyphKey, cacheBust]);

  if (error) {
    // No chart row yet is a state, not a failure (FitView's and QualityView's
    // own branch). A 409 is a row the ruler cannot score — no pixel anchors, or
    // geometry it refuses — and the generic conflict sentence („erst neu
    // laden") would send the author the wrong way; the lens says what helps,
    // and the raw line stays folded underneath.
    if (error.status === 404) return <Alert severity="info">{de.admin.diagnostics.noCanonicalShort}</Alert>;
    const shown = error.status === 409 ? { ...error, sentence: t.unscorable } : error;
    return (
      <Alert severity="warning">
        <ErrorText error={shown} prefix={t.errorPrefix} />
      </Alert>
    );
  }
  if (!data) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={18} />
        <Typography variant="caption">{t.loading}</Typography>
      </Box>
    );
  }
  // Kurrent and Offenbacher: their pixel/width metric has no deduction
  // categories, and the two metrics are never mixed — the list's own sentence.
  if (!data.sites || !data.frame || !data.centerline) {
    return <Alert severity="info">{de.wizard.optimize.breakdownNoComponents}</Alert>;
  }
  return (
    <PenaltyLens
      key={loadKey}
      sourceId={sourceId}
      glyphKey={glyphKey}
      cacheBust={cacheBust}
      data={{ ...data, sites: data.sites, frame: data.frame, centerline: data.centerline }}
      onMark={onMark}
    />
  );
}

type LensData = PenaltySitesOut & {
  sites: NonNullable<PenaltySitesOut['sites']>;
  frame: NonNullable<PenaltySitesOut['frame']>;
  centerline: NonNullable<PenaltySitesOut['centerline']>;
};

function PenaltyLens({
  sourceId,
  glyphKey,
  cacheBust,
  data,
  onMark,
}: {
  sourceId: string;
  glyphKey: string;
  cacheBust?: number;
  data: LensData;
  onMark: (ref: PenaltyRef) => void;
}) {
  const t = de.admin.letters.penalties;
  const [hidden, setHidden] = useState<ReadonlySet<PenaltyCategoryKey>>(() => new Set());
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [allOpen, setAllOpen] = useState(false);
  const [column, setColumn] = useState<HTMLElement | null>(null);
  const { w: columnWidth } = useElementSize(column);
  const detailRef = useRef<HTMLDivElement | null>(null);
  const pinRoving = useRovingList();
  const allRoving = useRovingList();

  const chips = useMemo(() => categoryChips(data.sites), [data.sites]);
  const drift = useMemo(() => stampDrift(data.stamped, data.components), [data.stamped, data.components]);
  // The pins the image draws — never one on a site apportioned 0.0000
  // (`shownPins`) — and the payload the overlay reads them from.
  const pins = useMemo(() => shownPins(data.pins, data.sites), [data.pins, data.sites]);
  const drawn = useMemo(() => ({ ...data, pins }), [data, pins]);
  const bySiteKey = useMemo(() => {
    const out = new Map<string, Located>();
    for (const category of PENALTY_CATEGORIES) {
      for (const site of data.sites[category].sites) out.set(siteKey(category, site.index), { category, site });
    }
    return out;
  }, [data.sites]);
  // What „Alle Stellen" lists: every site that carries a part of its number,
  // with or without a place (`listedSites`), in EVERY category — a legend chip
  // switches its category off on the image only, so the count and the list
  // stay one number whatever is switched off.
  const siteCount = useMemo(
    () => PENALTY_CATEGORIES.reduce((sum, key) => sum + listedSites(data.sites[key]).rows.length, 0),
    [data.sites],
  );

  // Until the column is measured, a phone-sized guess — never 0, which would
  // collapse the image to nothing for one frame.
  const room = (columnWidth || 320) - FRAME_INSET;
  const scale = Math.min(LENS_MAX_SCALE, lensScale(data.frame, room, LENS_MAX_H));

  const selected = selectedKey ? (bySiteKey.get(selectedKey) ?? null) : null;

  const select = (category: PenaltyCategoryKey, index: number) => {
    setHidden((prev) => revealCategory(prev, category));
    setSelectedKey((prev) => {
      const key = siteKey(category, index);
      return prev === key ? prev : key;
    });
  };
  // A tap on the IMAGE also brings the detail into view: on a phone it stands
  // below the crop, and a selection nobody can see the numbers of is half a
  // selection. The list rows do not scroll — they are the detail's neighbours.
  const selectFromImage = (category: PenaltyCategoryKey, index: number) => {
    select(category, index);
    // Read at the moment of the tap — the only moment the preference matters —
    // rather than subscribed to for the panel's whole life.
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    detailRef.current?.scrollIntoView?.({ block: 'nearest', behavior: reduced ? 'auto' : 'smooth' });
  };

  const rowFor = (entry: Located, withPin: boolean) => {
    const key = siteKey(entry.category, entry.site.index);
    return (
      <SiteRow
        key={key}
        entry={entry}
        owner={data.sites[entry.category]}
        rank={withPin ? pinRank(pins, entry.category, entry.site.index) : null}
        selected={key === selectedKey}
        onSelect={() => select(entry.category, entry.site.index)}
      />
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <Typography variant="caption" color="textSecondary">
        {t.rowNote}
      </Typography>

      {/* The „Abzüge (neu gemessen)" line IS the legend: each chip names its
          category, shows its mark, carries today's number and its site count,
          and switches the category off on the image. One explanation for all
          of it, from one button (design-system.md §9.4). */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, rowGap: 1.5 }}>
        <Typography variant="caption" sx={{ color: 'text.primary', fontWeight: 600 }}>
          {t.measuredLead}
        </Typography>
        {chips.map((chip) => {
          const icon = (
            <Box component="span" sx={{ display: 'inline-flex', ml: 0.75 }}>
              <PenaltyShapeIcon shape={CATEGORY_SHAPE[chip.key]} size={16} />
            </Box>
          );
          if (!chip.filterable) {
            // Nothing to draw — not applicable, nothing located, or a map that
            // was dropped: a label, not a switch, so it is no dead tab stop.
            return (
              <Chip
                key={chip.key}
                size="small"
                variant="outlined"
                icon={icon}
                label={chip.text}
                sx={{ ...CHIP_SX, color: 'text.secondary' }}
              />
            );
          }
          const off = hidden.has(chip.key);
          return (
            <Chip
              key={chip.key}
              size="small"
              clickable
              variant={off ? 'outlined' : 'filled'}
              icon={icon}
              label={chip.text}
              aria-pressed={!off}
              onClick={() => setHidden((prev) => toggleCategory(prev, chip.key))}
              sx={{
                ...CHIP_SX,
                color: off ? 'text.secondary' : 'text.primary',
                // Off is also a struck-through label, so the state is not
                // carried by the fill alone.
                textDecoration: off ? 'line-through' : 'none',
                ...hitArea(),
              }}
            />
          );
        })}
        <PenaltyLegend />
      </Box>

      {drift.length > 0 && (
        <Typography variant="caption" sx={{ color: 'text.secondary', fontVariantNumeric: 'tabular-nums' }}>
          <Box component="span" sx={{ color: 'text.primary', fontWeight: 600 }}>
            {`${t.storedLead} `}
          </Box>
          {drift.map((d) => `${d.label} ${fourPlaces(d.stamped)}`).join(' · ')}
          {` — ${t.storedNote}`}
        </Typography>
      )}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 3fr) minmax(280px, 2fr)' },
          gap: 2,
          alignItems: 'start',
        }}
      >
        <Box ref={setColumn} sx={{ minWidth: 0 }}>
          <Box
            sx={{
              bgcolor: '#fff',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1,
              width: 'fit-content',
              maxWidth: '100%',
            }}
          >
            <Box sx={{ position: 'relative', width: data.frame.width * scale, height: data.frame.height * scale }}>
              <img
                src={cropUrl(sourceId, glyphKey, cacheBust)}
                alt={fmt(de.admin.werkbank.chartFormAlt, { key: glyphKey })}
                width={data.frame.width * scale}
                height={data.frame.height * scale}
                // Dimmed so the marks read over the ink (the Diagnose skeleton
                // column's own recipe), and PIXELATED: the ruler scored these
                // pixels, and a smoothed upscale would put a hatched cell beside
                // the blur of the pixel it names.
                style={{
                  display: 'block',
                  position: 'absolute',
                  inset: 0,
                  opacity: penaltyCropAlpha,
                  imageRendering: 'pixelated',
                }}
              />
              <PenaltyOverlay
                data={drawn}
                scale={scale}
                hidden={hidden}
                selectedKey={selectedKey}
                onSelect={selectFromImage}
              />
              <PenaltyPins
                data={drawn}
                scale={scale}
                hidden={hidden}
                selectedKey={selectedKey}
                onSelect={selectFromImage}
              />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25, minWidth: 0 }}>
          <Typography component="h3" variant="caption" sx={{ color: 'text.primary', fontWeight: 600 }}>
            {t.pinsTitle}
          </Typography>
          {pins.length === 0 ? (
            <Typography variant="caption" color="textSecondary">
              {t.pinsNone}
            </Typography>
          ) : (
            <Box {...pinRoving.containerProps} sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {pins.map((pin) => {
                const entry = bySiteKey.get(siteKey(pin.category, pin.index));
                if (!entry) return null;
                return (
                  <Box key={pin.rank} {...pinRoving.rowProps(siteKey(pin.category, pin.index))}>
                    {rowFor(entry, true)}
                  </Box>
                );
              })}
            </Box>
          )}

          <Divider />

          <Box ref={detailRef}>
            {selected ? (
              <PenaltyDetail
                entry={selected}
                owner={data.sites[selected.category]}
                rank={pinRank(pins, selected.category, selected.site.index)}
                unitPx={data.frame.unit_px}
                onMark={() => onMark(penaltyRefOf(selected.category, selected.site, data.sites[selected.category]))}
              />
            ) : (
              <Typography variant="caption" color="textSecondary">
                {t.selectHint}
              </Typography>
            )}
          </Box>

          <Divider />

          {/* The disclosure pattern: the toggle IS the section's h3, so the
              per-category h4s below nest under „Alle Stellen" rather than
              under the pins' heading above. */}
          <Typography component="h3" variant="caption" sx={{ m: 0, alignSelf: 'flex-start' }}>
            <Button
              size="small"
              aria-expanded={allOpen}
              onClick={() => setAllOpen((v) => !v)}
              sx={{ minHeight: TOUCH_TARGET }}
            >
              {allOpen ? t.allHide : fmt(t.allToggle, { count: siteCount })}
            </Button>
          </Typography>
          {allOpen && (
            <Box {...allRoving.containerProps} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {/* Every applicable category, hidden or not: the legend switch
                  acts on the image, and a row chosen here shows its category
                  again (`revealCategory`). */}
              {chips
                .filter((chip) => chip.applicable)
                .map((chip) => {
                  const { rows, zero } = listedSites(data.sites[chip.key]);
                  return (
                    <Box key={chip.key} sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Typography
                        component="h4"
                        variant="caption"
                        sx={{ color: 'text.primary', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}
                      >
                        {chip.text}
                        {hidden.has(chip.key) && (
                          <Box component="span" sx={{ color: 'text.secondary', fontWeight: 400 }}>
                            {` · ${t.hiddenNote}`}
                          </Box>
                        )}
                      </Typography>
                      {rows.map((site) => (
                        <Box key={site.index} {...allRoving.rowProps(siteKey(chip.key, site.index))}>
                          {rowFor({ category: chip.key, site }, true)}
                        </Box>
                      ))}
                      {zero > 0 && (
                        <Typography variant="caption" color="textSecondary">
                          {zero === 1 ? t.belowOne : fmt(t.belowCount, { count: zero })}
                        </Typography>
                      )}
                    </Box>
                  );
                })}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

/** A ①–⑤ disc — the same mark the image draws, so list and image read as one. */
function PinDisc({ rank }: { rank: number }) {
  return (
    <Box
      aria-hidden
      sx={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        bgcolor: penalty.pin,
        color: '#fff',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        fontSize: '0.875rem',
        fontWeight: 600,
        lineHeight: 1,
      }}
    >
      {rank}
    </Box>
  );
}

/**
 * One selectable site — a real button, 44 px high, so the list is the
 * keyboard's and the screen reader's way to every mark on the image. Its
 * visible text IS its name; the pressed state says which one is chosen, and
 * the left bar shows it without relying on the tint.
 */
function SiteRow({
  entry,
  owner,
  rank,
  selected,
  onSelect,
}: {
  entry: Located;
  owner: PenaltyCategoryOut;
  rank: number | null;
  selected: boolean;
  onSelect: () => void;
}) {
  const t = de.admin.letters.penalties;
  const { category, site } = entry;
  return (
    <ButtonBase
      onClick={onSelect}
      aria-pressed={selected}
      sx={{
        width: '100%',
        minHeight: TOUCH_TARGET,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-start',
        gap: 1,
        px: 1,
        py: 0.5,
        textAlign: 'left',
        borderRadius: 1,
        borderLeft: 3,
        borderLeftColor: selected ? penalty.selected : 'transparent',
        bgcolor: selected ? 'action.selected' : 'transparent',
      }}
    >
      {rank !== null ? <PinDisc rank={rank} /> : <PenaltyShapeIcon shape={siteShape(category, site)} />}
      <Box sx={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Typography variant="body2" component="span" sx={{ color: 'text.primary' }}>
          {/* The disc is aria-hidden; its rank is part of the row's name, so
              „Alle Stellen" — sorted by value, not by rank — still says which
              rows are among the five marked on the image. */}
          {rank !== null && (
            <Box component="span" sx={visuallyHidden}>
              {fmt(t.rankPrefix, { rank })}
            </Box>
          )}
          {`${penaltyLabel({ category, index: site.index })} · ${siteKindLabel(site)}`}
        </Typography>
        <Typography
          variant="caption"
          component="span"
          sx={{ color: 'text.secondary', fontVariantNumeric: 'tabular-nums' }}
        >
          {[
            fmt(t.ofCategory, { value: fourPlaces(site.value), total: fourPlaces(owner.value) }),
            site.exact ? t.exactTerm : t.exactShare,
            isLocated(site) ? fmt(t.pointsShort, { points: site.points_est.toFixed(2) }) : t.noPlace,
          ].join(' · ')}
        </Typography>
      </Box>
    </ButtonBase>
  );
}

function PenaltyDetail({
  entry,
  owner,
  rank,
  unitPx,
  onMark,
}: {
  entry: Located;
  owner: PenaltyCategoryOut;
  rank: number | null;
  unitPx: number;
  onMark: () => void;
}) {
  const t = de.admin.letters.penalties;
  const { category, site } = entry;
  const part = coveragePart(category, site);
  const numbers = Object.entries(site.numbers).filter(([, value]) => value !== null && value !== undefined);
  const labels: Record<string, string> = t.number;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {rank !== null && <PinDisc rank={rank} />}
        <PenaltyShapeIcon shape={siteShape(category, site)} />
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {penaltyLabel({ category, index: site.index })}
        </Typography>
        <Typography variant="caption" color="textSecondary">
          {[siteKindLabel(site), part ? fmt(t.partOf, { part: t.part[part] }) : null].filter(Boolean).join(' · ')}
        </Typography>
      </Box>
      <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
        {`${fmt(t.ofCategory, { value: fourPlaces(site.value), total: fourPlaces(owner.value) })} (${sharePercent(site)} %) · ${site.exact ? t.exactTerm : t.exactShare}`}
      </Typography>
      <Typography variant="caption" color="textSecondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
        {fmt(t.pointsLong, { points: site.points_est.toFixed(2) })}
      </Typography>
      <Typography variant="caption" color="textSecondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
        {isLocated(site) ? fmt(t.position, { x: formatNumber(site.x), y: formatNumber(site.y) }) : t.positionNone}
      </Typography>
      {category === 'verticality' && (
        <Typography variant="caption" color="textSecondary">
          {fmt(t.exaggerated, {
            factor: verticalExaggeration(site.paths.find((p) => p.role === 'run')?.values ?? [], unitPx),
          })}
        </Typography>
      )}
      {category === 'smoothness' && (
        <Typography variant="caption" color="textSecondary">
          {t.windowsNote}
        </Typography>
      )}
      {numbers.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, rowGap: 0.75 }}>
          {numbers.map(([key, value]) => (
            <Chip
              key={key}
              size="small"
              variant="outlined"
              label={`${labels[key] ?? key}: ${formatNumber(value)}`}
              sx={{ fontVariantNumeric: 'tabular-nums' }}
            />
          ))}
        </Box>
      )}
      <Button size="small" variant="outlined" sx={{ alignSelf: 'flex-start', minHeight: TOUCH_TARGET }} onClick={onMark}>
        {`⚑ ${t.mark}`}
      </Button>
      <Typography variant="caption" color="textSecondary">
        {t.markHint}
      </Typography>
    </Box>
  );
}

/** The one explanation of the legend: what every mark shape means, and how to read the numbers. */
function PenaltyLegend() {
  const t = de.admin.letters.penalties;
  return (
    <InfoHint title={t.legendTitle} label={t.legendAria}>
      <Stack spacing={0.75}>
        <Typography variant="body2">{t.legendIntro}</Typography>
        <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {PENALTY_CATEGORIES.map((key) => (
            <Box component="li" key={key} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
              <Box sx={{ pt: 0.25 }}>
                <PenaltyShapeIcon shape={CATEGORY_SHAPE[key]} />
              </Box>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                <Box component="span" sx={{ color: paper.ink, fontWeight: 600 }}>
                  {de.wizard.optimize.cat[key]}
                </Box>
                {` — ${t.markerHint[key]}`}
              </Typography>
            </Box>
          ))}
          <Box component="li" sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <Box sx={{ pt: 0.25 }}>
              <PenaltyContextIcon />
            </Box>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              <Box component="span" sx={{ color: paper.ink, fontWeight: 600 }}>
                {t.legendContextLabel}
              </Box>
              {` — ${t.legendContext}`}
            </Typography>
          </Box>
        </Box>
        <Typography variant="body2">{t.legendExact}</Typography>
        <Typography variant="body2">{t.legendPoints}</Typography>
        <Typography variant="body2">{t.legendNoPlace}</Typography>
      </Stack>
    </InfoHint>
  );
}
