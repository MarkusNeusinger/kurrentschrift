// The written strips, as the workbench shows a chart crop today.
//
// These pixels are the reserved own-hand dataset: admin-gated, `private,
// no-store`, never in the repository. How they reach the browser — as blobs,
// on demand, one Fassung at a time — is `useStripImage`; a word cut is served
// from the same stored strip rather than kept as a second image.
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
//
// The panel is the HOST: it owns the listing, the filter, the shared zoom and
// the three switches, and hands them to the pieces beside it — `StripTile` per
// Fassung, `StripGallery` for the filtered view, `Lupe` for a closer look.
//
// Since the Nachfahr-Liste it hosts TWO surfaces over the same hand, and the
// switch between them is the one every overview has: `?ansicht=liste` is the
// work list with one row per word box, `?ansicht=galerie` the pictures above.
// A second Unteransicht was refused for it (V2 — „Unterrouten erst, wenn die
// Nachfahr-Liste eine eigene Fläche wird"), and the compact list is the
// default because that is what V14 says an overview opens as. What the two
// surfaces can answer differs and is not hidden: the word search narrows both,
// the coverage ITEM only the gallery — a box row carries its word, never the
// items that word covers.

import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getEigenhandStrips } from '@/lib/api';
import type { EigenhandFleck, EigenhandPfadBox, EigenhandStrip, EigenhandStripFilter } from '@/lib/api';
import { InfoHint } from '@/components/InfoHint';
import { useRovingList } from '@/hooks/useRovingList';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de, fmt } from '@/locales/admin';
import { byBefund } from '@/sections/admin/eigenhand/befundOrder';
import { Lupe } from '@/sections/admin/eigenhand/Lupe';
import type { LupeTarget } from '@/sections/admin/eigenhand/Lupe';
import { NachfahrListe } from '@/sections/admin/eigenhand/NachfahrListe';
import { STRIP_BOX_LIST_SPEC } from '@/sections/admin/eigenhand/stripBoxRows';
import { boxMatches } from '@/sections/admin/eigenhand/stripFilter';
import { useEigenhandPfadBoxes } from '@/sections/admin/eigenhand/useEigenhandPfadBoxes';
import { stripBoxSpecimen } from '@/sections/admin/shell/focus';
import { GALLERY_PAGE, StripGallery } from '@/sections/admin/eigenhand/StripGallery';
import type { Beleg } from '@/sections/admin/eigenhand/StripGallery';
import { StripTile } from '@/sections/admin/eigenhand/StripTile';
import { ZOOMS, ZOOM_LABELS } from '@/sections/admin/eigenhand/stripZoom';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { readListState, writeListState, type ListView } from '@/sections/admin/shell/listState';
import { Panel } from '@/sections/admin/shell/Panel';
import { ListViewSwitch } from '@/sections/admin/shell/WorkList';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

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
  // Which of the two surfaces is on. It is LIST state, so it lives in the URL
  // beside the list's own filters rather than in component state — a Korb link
  // or a pasted address opens the surface it was written on. The spec is the
  // list's, because `ansicht` belongs to whichever list is being looked at;
  // everything else in that spec only matters once the list is mounted.
  const [params, setParams] = useSearchParams();
  const view = readListState(params, STRIP_BOX_LIST_SPEC).view;
  const setView = (next: ListView) =>
    setParams(writeListState(params, { view: next }, STRIP_BOX_LIST_SPEC), { replace: true });
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
  const [shownCount, setShownCount] = useState(GALLERY_PAGE);
  // Off by default: the listing's own order (strip, then Fassung) is what one
  // reads when looking for a particular row. The Befund order answers the
  // other question — what to write again — and is one click away.
  const [byWeakest, setByWeakest] = useState(false);
  // Bumped when a Fleckenmaske is saved: the server re-measures the Befund
  // against it, and everything the tiles show about quality is derived from
  // that measurement.
  const [refresh, setRefresh] = useState(0);
  const filtered = Boolean(filter.wort || filter.item);
  // The filtered gallery below is one tab stop; see the grid itself. It is
  // remembered HERE rather than inside the gallery, so the stop survives a
  // filter being cleared and set again.
  const galleryRoving = useRovingList({ orientation: 'horizontal', label: t.stripGalleryLabel });

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
    setShownCount(GALLERY_PAGE);
  }

  // The GALLERY's listing, and only the gallery's. Since the list became the
  // default surface of this tab, an unconditional fetch here meant opening
  // `?reiter=streifen` cost two hand-wide reads — this one plus the list's own
  // meta read — for a listing nothing on screen consumes (Copilot review). The
  // display mode is therefore a dependency, so the switch to „Galerie" is what
  // fetches it.
  useEffect(() => {
    if (view !== 'galerie') return undefined;
    let cancelled = false;
    getEigenhandStrips(hand, { wort: filter.wort, item: filter.item }, { retries: 2 })
      .then((data) => !cancelled && setStrips(data.strips))
      .catch((err: unknown) => !cancelled && setError(apiErrorText(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [hand, version, filter.wort, filter.item, refresh, view]);

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

  // The Ampel per box, for the GALLERY's tiles: the same hand-wide read the
  // list runs on, because a crop tile has said nothing about the state of the
  // box it shows since the free-standing „Maske geändert" chip gave way to the
  // Tintentreue (§7.2 wants the verdict on both surfaces, and the gallery is
  // where a coverage cell lands). Only while the pictures are on screen — the
  // list mounts its own reader.
  const ampeln = useEigenhandPfadBoxes(hand, view === 'galerie');
  const ampelByBox = useMemo(() => {
    if (ampeln.fassungen === null) return null;
    const out = new Map<string, EigenhandPfadBox>();
    for (const fassung of ampeln.fassungen) {
      for (const box of fassung.kaesten) {
        out.set(stripBoxSpecimen(fassung.strip, fassung.fassung, box.box_index), box);
      }
    }
    return out;
  }, [ampeln.fassungen]);

  // The listing's order — plan order, or weakest first when the switch is on.
  // BOTH display modes read it: the tiles below and the filtered gallery, so
  // the switch means the same thing whether or not a filter is active.
  const listed = useMemo(() => (byWeakest ? [...strips].sort(byBefund) : strips), [strips, byWeakest]);

  // The gallery: every (strip, box) that holds the filter. A strip the server
  // listed always contributes — should the two halves of the match ever
  // disagree on a box, the whole row is shown rather than nothing, because
  // hiding evidence the server found is the worse error.
  const belege = useMemo<Beleg[]>(
    () =>
      filtered
        ? listed.flatMap((row) => {
            const matching = row.boxes.filter((box) => boxMatches(box, filter));
            return (matching.length ? matching : row.boxes).map((box) => ({ row, box }));
          })
        : [],
    [listed, filter, filtered],
  );

  const liste = view === 'liste';
  const caption = liste
    ? t.nachfahren.caption
    : filtered
      ? fmt(t.stripBelegeCount, { count: belege.length, strips: strips.length })
      : strips.length
        ? fmt(t.stripCount, { count: strips.length })
        : t.stripImagesIntro;

  return (
    <Panel
      title={liste ? `${t.stripImagesTitle} · ${t.nachfahren.title}` : t.stripImagesTitle}
      caption={caption}
      actions={
        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
          {/* A `Tooltip` around a `FormControlLabel` is hover-only: the label
              is not focusable and MUI composes its `onFocus` onto the label,
              not onto the switch inside. What each of the three switches DOES
              therefore never reached the tablet this panel is used on — so the
              three hints sit in ONE InfoHint at the head of the row. */}
          <InfoHint title={t.stripSwitchesTitle} label={t.stripSwitchesAria}>
            <Stack spacing={0.75}>
              <Typography variant="body2">{t.nachfahren.viewHint}</Typography>
              <Typography variant="body2">{`${t.befundSort} — ${t.befundSortHint}`}</Typography>
              <Typography variant="body2">{`${t.pfadShow} — ${t.pfadShowHint}`}</Typography>
              <Typography variant="body2">{`${t.stripNoRulings} — ${t.stripNoRulingsHint}`}</Typography>
            </Stack>
          </InfoHint>
          {/* The switch stands on BOTH surfaces; the three below it belong to
              the pictures and are gone while the list is on — a „Lineatur
              ausblenden" over a list of rows would be a control with nothing
              to do. */}
          <ListViewSwitch view={view} onChange={setView} />
          {!liste && (
            <>
              <FormControlLabel
                control={<Switch size="small" checked={byWeakest} onChange={(e) => setByWeakest(e.target.checked)} />}
                label={<Typography variant="caption">{t.befundSort}</Typography>}
                sx={{ mr: 0 }}
              />
              <FormControlLabel
                control={<Switch size="small" checked={pfade} onChange={(e) => setPfade(e.target.checked)} />}
                label={<Typography variant="caption">{t.pfadShow}</Typography>}
                sx={{ mr: 0 }}
              />
              <FormControlLabel
                control={
                  <Switch size="small" checked={ohneLineatur} onChange={(e) => setOhneLineatur(e.target.checked)} />
                }
                label={<Typography variant="caption">{t.stripNoRulings}</Typography>}
                sx={{ mr: 0 }}
              />
              <ToggleButtonGroup
                size="small"
                exclusive
                value={zoom}
                aria-label={t.stripZoom}
                onChange={(_e, value: Zoom | null) => value && setZoom(value)}
              >
                {/* „¼ ½ 1:1 2×" measured 27–35 × 31 px — the smallest targets
                    left on the page the author works on with a finger. A
                    group's buttons touch, so they grow in BOTH edges rather
                    than overlapping each other's hit areas (§9.3). The sweep
                    never caught them: it only sees this page's shell, because
                    no hand is resolved until one is chosen and no script can
                    operate a picker. */}
                {ZOOMS.map((level) => (
                  <ToggleButton
                    key={level}
                    value={level}
                    sx={{ px: 1, py: 0.25, textTransform: 'none', minWidth: TOUCH_TARGET, minHeight: TOUCH_TARGET }}
                  >
                    {ZOOM_LABELS[level]}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </>
          )}
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
        {loading && !liste && <CircularProgress size={16} />}
      </Stack>

      {error && !liste && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <ErrorText error={error} prefix={t.stripImagesError} />
        </Alert>
      )}

      {/* The empty state says WHICH emptiness this is and where the step
          stands. The command itself is no longer copied here: „no strips at
          all" was all-or-nothing, while the Übergabekarte on the Bestand knows
          how many Fassungen still owe their image. The list has its own three
          silences and answers out of its own read, so this one belongs to the
          pictures alone. */}
      {!loading && !error && !liste && strips.length === 0 && (
        <Typography variant="caption" sx={{ display: 'block', color: paper.inkSoft }}>
          {filtered ? t.stripBelegeEmpty : t.stripImagesEmpty}
        </Typography>
      )}

      {liste ? (
        <NachfahrListe
          // Keyed by hand like the panel itself: no page, filter or open row of
          // the previous hand survives a switch.
          key={hand}
          hand={hand}
          wort={filter.wort ?? ''}
          item={filter.item ?? null}
          onShowGalerie={() => setView('galerie')}
        />
      ) : filtered ? (
        <StripGallery
          hand={hand}
          belege={belege}
          shownCount={shownCount}
          onMore={() => setShownCount((n) => n + GALLERY_PAGE)}
          zoom={zoom}
          ohneLineatur={ohneLineatur}
          pfade={pfade}
          ampelByBox={ampelByBox}
          onLupe={setLupe}
          roving={galleryRoving}
        />
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
