// Eigenhand — the fourth view, and the only one that belongs to a HAND rather
// than to a Vorlage. It answers the two questions the capture chain could
// otherwise only answer in a terminal: what does my own hand already hold, and
// give me the next sheets to write.
//
// The numbers come from the shared compute in `core/eigenhand` (same module the
// terminal report prints), measured against the committed strip plan — so
// „belegt" means the same here and there, and the denominators are honest:
// how many glyphs and joins the plan can produce at all, capitals, digits and
// signs included.
//
// What is NOT here, on purpose: the SCANS. Uploading a capture stays a local
// step — ingest needs the file on disk and the Siebung is a local page — so the
// hint under the printer names the command that continues the loop.
//
// The STRIPS themselves do appear (owner, 2026-08-24): they live in the DB so
// the workbench can show a written Streifen the way it shows a chart crop.
// They stay the reserved own-hand dataset — admin-gated, uncacheable, never in
// the repository, and loaded only when asked for (StripsPanel).
//
// Since the `?reiter=` split this file is the SHELL: it owns the one Bestand
// read behind all four Unteransichten, the last print job's sheet ids, and the
// switch between them (admin-redesign.md V2). Everything that used to stand
// under each other on one very long page now lives in BestandView, StripsPanel,
// StatistikView and DruckenView. Four surfaces, one read — a per view load
// would fire four requests for the same payload and lose the `angenommen`
// counter the strips gallery uses as its cache buster.
//
// What it no longer owns is the HAND. It is a scope, not a setting of this
// page: the Scope-Leiste names it everywhere, the Korb links carry it, and two
// Vorlagen of one script share it — none of which survives in a component that
// unmounts (admin-redesign.md V19, Q25 a; `context/AdminContext.tsx` +
// `shell/handScope.ts`). This page keeps the one thing that IS its own: the
// picker, the only place the hand is chosen.

import {
  Alert,
  Box,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { getEigenhandBestand } from '@/lib/api';
import type { EigenhandBestand, EigenhandStripFilter } from '@/lib/api';
import { latestRequestGate } from '@/lib/latestRequest';
import { de, fmt } from '@/locales/admin';
import { BestandView } from '@/sections/admin/eigenhand/BestandView';
import { glyphOf } from '@/sections/admin/eigenhand/coverageLabels';
import { DruckenView } from '@/sections/admin/eigenhand/DruckenView';
import { StatistikView } from '@/sections/admin/eigenhand/StatistikView';
import { StripsPanel } from '@/sections/admin/eigenhand/StripsPanel';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { EIGENHAND_ANSICHTEN, eigenhandUrl, readEigenhandFocus } from '@/sections/admin/shell/focus';
import { ViewHeader } from '@/sections/admin/shell/Panel';
import { TOUCH_TARGET } from '@/styles/hitArea';

// `glyphOf` moved to coverageLabels.ts, where the key-to-character map is
// DERIVED from the glyph registry instead of hand-written a second time. It had
// drifted by two entries, which is why the grid printed the literal word
// "semicolon" among twelve characters — the reason is recorded there.

// A coverage item as the view names it: `a>b` → „a › b", `a@medial` → „a
// (medial)", a bare key → its glyph.
const itemLabel = (item: string): string => {
  if (item.includes('>')) return item.split('>').map(glyphOf).join(' › ');
  const [key, position] = item.split('@');
  return position ? `${glyphOf(key)} (${position})` : glyphOf(key);
};

export function EigenhandView() {
  const t = de.admin.eigenhand;
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { ansicht, item, wort } = readEigenhandFocus(params);
  // The hand and the hands on offer both come from the admin scope: which ones
  // are legal is decided by the Vorlage's script, not by this page (V19).
  const { handId, handChoices, setHand, handsLoaded, handsError, source } = useAdmin();
  const hand = handId ?? '';
  const [bestand, setBestand] = useState<EigenhandBestand | null>(null);
  const [loadError, setLoadError] = useState<ApiErrorText | null>(null);
  const [loading, setLoading] = useState(false);
  // Hoisted out of the print block: the sheet ids of the last job drive the
  // „Stapel als PDF" and per-Bogen buttons, and a hop to the Bestand and back
  // would otherwise leave the printed sheets on the server with nothing on
  // screen that can name them.
  const [printed, setPrinted] = useState<string[]>([]);

  // The hands themselves are read once by the admin provider, for the whole
  // workbench. What used to stand here — a default of `mn-${styles[1]}` —
  // is gone with it: it hard-wired one writer's prefix AND a position in the
  // styles array, and it invented an id no read had ever returned (Q25 a). A
  // script without a written hand now says so instead (`noHands`).

  // Which hand the Bestand on screen belongs to. Arming the spinner and
  // clearing the error happens DURING RENDER on a switch — React's "adjusting
  // state when a prop changes" (react-hooks/set-state-in-effect) — which is why
  // `reload` below carries the request alone: an effect that called it would
  // otherwise be setting state synchronously through the callback.
  const [loadingFor, setLoadingFor] = useState(hand);
  if (loadingFor !== hand) {
    setLoadingFor(hand);
    // The Bestand on screen belongs to the hand just left. Dropping it here is
    // the whole point of the switch: otherwise the new hand's name stands over
    // the previous hand's Streifen, Fassungen and open joins — numbers that
    // look authoritative and are simply someone else's.
    setBestand(null);
    // Same reasoning for the printed sheets, and hoisting them made it
    // visible: a sheet id belongs to ONE hand, so keeping the last job across
    // a switch would offer „Stapel als PDF" buttons that ask the new hand for
    // the old hand's Bögen.
    setPrinted([]);
    // Guarded like `reload` itself: no hand means no request, so nothing to
    // wait for either.
    if (hand) {
      setLoading(true);
      setLoadError(null);
    }
  }

  // Only the newest Bestand request may write. Two switches in quick succession
  // (or a switch while a slow load is in flight) otherwise let the OLDER
  // response land last and stick — the panel would then show hand A's numbers
  // under hand B's name until the next reload, with no error to hint at it.
  const beginBestand = useRef(latestRequestGate()).current;

  const reload = useCallback(
    (target: string) => {
      if (!target) return;
      const isCurrent = beginBestand();
      getEigenhandBestand(target, { retries: 2 })
        .then((data) => isCurrent() && setBestand(data))
        .catch((err: unknown) => {
          if (!isCurrent()) return;
          setBestand(null);
          // The 400 branch that used to stand here read
          // `… === 400 ? String(err) : String(err)` — both arms identical, so
          // whatever it once meant to spare the reader, it never did. The German
          // layer covers the case properly now: a malformed hand id (the only
          // 400 this route raises) gets the „Angaben stimmen nicht" sentence and
          // the server's own line underneath.
          setLoadError(apiErrorText(err));
        })
        .finally(() => {
          // The spinner belongs to the newest request too: an outdated one
          // clearing it would uncover an empty panel while the current load is
          // still running.
          if (isCurrent()) setLoading(false);
        });
    },
    [beginBestand],
  );

  useEffect(() => {
    reload(hand);
  }, [hand, reload]);

  // A printed Bogen moves strips into „unterwegs", so the counters are stale
  // the moment the job returns. The hand has not changed in the usual case, so
  // the render guard above says nothing — an event continuation sets its own
  // flags.
  //
  // `forHand` is the guard for the unusual case: the selector stays enabled
  // while a job runs, so a print started for one hand can land after the shell
  // moved to another. Its sheet ids belong to the hand that was printed for,
  // and reloading its Bestand would be a legitimately NEWER request for the
  // wrong subject — which is exactly what `beginBestand` cannot catch, and how
  // one hand's numbers end up under another's name.
  const handlePrinted = useCallback(
    (forHand: string, sheets: string[]) => {
      if (forHand !== hand) return;
      setPrinted(sheets);
      setLoading(true);
      setLoadError(null);
      reload(hand);
    },
    [hand, reload],
  );

  // A saved setup is the same shape of event: the `setup_pull` Übergabekarte is
  // derived on the SERVER from the row the panel just wrote, so without this
  // re-read the card it promises would only turn up after a reload. No spinner
  // for it — the panels on screen stay valid, only the due list gains a card —
  // and the same `forHand` guard, because the selector stays enabled while the
  // save is in flight.
  const handleSetupSaved = useCallback(
    (forHand: string) => {
      if (forHand !== hand) return;
      reload(hand);
    },
    [hand, reload],
  );

  // What the strips gallery shows, read from the URL rather than from state:
  // the producer (a coverage cell on `bestand`) and the consumer (`streifen`)
  // stopped sharing a component when the page split, and a filter that lives
  // in the address bar is also a link the Korb can file.
  //
  // Memoised on the two strings: StripsPanel's search debounce has `filter` in
  // its effect deps, and a fresh object every render would re-arm the timer on
  // every keystroke instead of settling after 300 ms.
  const stripFilter = useMemo<EigenhandStripFilter>(
    () => ({ item: item ?? undefined, wort: wort ?? undefined }),
    [item, wort],
  );

  // A filter change REPLACES: the search box writes one entry per settled
  // keystroke, and the back button is supposed to walk the inspection history
  // (focus.ts), not a typing log.
  const setStripFilter = useCallback(
    (next: EigenhandStripFilter) => {
      navigate(eigenhandUrl(ansicht, { item: next.item, wort: next.wort }), { replace: true });
    },
    [ansicht, navigate],
  );

  // A coverage cell used to scroll to the gallery further down the page; with
  // the split it navigates. PUSHED on purpose — back returns to the Bestand
  // with the grid where it stood, which is the whole reason the subject lives
  // in the query string.
  // `wort` rides along: before the split the jump merged the item INTO the
  // standing filter, so a word typed in the search survived a look at the
  // coverage grid. Dropping it here would silently widen the gallery the
  // author was narrowing.
  const showBelege = useCallback(
    (selected: string) => navigate(eigenhandUrl('streifen', { item: selected, wort })),
    [navigate, wort],
  );

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      {/* The role's gloss on its first appearance (Q8 a), composed from the
          shared `shell.role*` constant rather than written into `intro`: the
          Scope-Leiste will name the same role, and one wording cannot drift
          into two. */}
      <ViewHeader
        eyebrow={de.admin.shell.startEyebrow}
        title={t.title}
        intro={`${de.admin.shell.roleEigenhandGloss} — ${t.intro}`}
      />

      <Stack direction="row" spacing={2} sx={{ mb: 3, flexWrap: 'wrap', rowGap: 2, alignItems: 'center' }}>
        <TextField
          select
          size="small"
          label={t.hand}
          value={hand}
          // No free-text fallback any more: a hand is created by writing and
          // printing, never by typing an id into this field, and the list is
          // now the authoritative set of legal picks for this Vorlage.
          disabled={!handChoices.length}
          onChange={(e) => {
            setHand(e.target.value);
            // The filter belongs to the hand just left: an item another hand
            // never wrote would show an empty gallery under a live chip.
            navigate(eigenhandUrl(ansicht), { replace: true });
          }}
          sx={{ minWidth: '14rem' }}
        >
          {handChoices.map((id) => (
            <MenuItem key={id} value={id}>
              {id}
            </MenuItem>
          ))}
        </TextField>

        {/* Links, not a handler: middle-click, „copy link" and the back button
            all keep working, and the switch is the repo's ToggleButtonGroup
            rather than Tabs (which has no precedent anywhere in app/src).
            `aria-current` carries the state to a screen reader, and
            `aria-pressed` has to be switched OFF: MUI writes it unconditionally
            for a real <button>, but on `component={RouterLink}` the element is
            an <a role=link>, where the attribute is not allowed ARIA. It spreads
            our props after its own, so passing undefined removes it.
            The strips filter travels only between the two views that share it:
            the coverage grid on `bestand` produces it, the gallery on
            `streifen` consumes it, so the round trip keeps a narrowed gallery
            narrow. `statistik` and `drucken` read neither, and a copied
            `?reiter=drucken&item=a%3Eb` would carry a parameter that does
            nothing but mislead the next reader. */}
        <ToggleButtonGroup size="small" exclusive value={ansicht} aria-label={t.ansichtAria}>
          {EIGENHAND_ANSICHTEN.map((name) => (
            <ToggleButton
              key={name}
              value={name}
              component={RouterLink}
              to={eigenhandUrl(name, name === 'streifen' || name === 'bestand' ? { item, wort } : undefined)}
              aria-current={name === ansicht ? 'page' : undefined}
              aria-pressed={undefined}
              // 40.5 px painted at every breakpoint — the theme lifts toggle
              // groups only below `sm`, and this is the page's own tab row on
              // the tablet the author re-traces on. A group's buttons touch, so
              // the element grows rather than wearing an invisible hit area
              // (§9.3, „wo Nachbarn dicht stehen").
              sx={{ textTransform: 'none', px: 1.5, minHeight: TOUCH_TARGET }}
            >
              {t.ansichten[name]}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        {loading && <CircularProgress size={16} />}
      </Stack>

      {/* The two reads behind the picker are admin-gated and a 401 is not
          retried, so their failure is permanent — and until it is named, the
          disabled picker below looks exactly like „this script has no hand". */}
      {handsError !== null && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <ErrorText error={apiErrorText(handsError)} prefix={t.handsError} />
        </Alert>
      )}

      {/* „this Vorlage's script", not „at all": the hand always belongs to the
          script in front of the workbench (V19), so a Kurrent Vorlage beside a
          written Sütterlin hand still stands here with none. Shown only once
          the reads have ANSWERED — before that it would be a claim about data
          nobody has yet.

          It names the command, not the printer: a hand is minted by the first
          thing written under its id, and the one in-app way to do that used to
          be a free-text field seeded with an INVENTED `mn-<stil>` (gone with
          the scope, see above). `setup` is the honest first step — it writes
          the server record, so the hand shows up in this very picker through
          GET /eigenhand/setups and the printer can work under it. */}
      {handsLoaded && !handChoices.length && (
        <Box sx={{ mb: 3 }}>
          <TerminalCommand
            lead={t.noHands}
            command={fmt(t.noHandsCommand, { style: source?.style_id ?? '<stil>' })}
          />
        </Box>
      )}

      {loadError && !bestand && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <ErrorText error={loadError} prefix={t.loadError} />
        </Alert>
      )}

      {/* ONE gate for all four Unteransichten, as before the split: a hand
          whose Bestand failed to load has no numbers to show anywhere, and
          four spinners would only say the same thing four times. */}
      {bestand && (
        <>
          {ansicht === 'bestand' && (
            <BestandView
              hand={hand}
              bestand={bestand}
              labelOf={itemLabel}
              onShowBelege={showBelege}
              onSetupSaved={handleSetupSaved}
            />
          )}
          {ansicht === 'streifen' && (
            /* Keyed by hand: a switch remounts the panel, so no search term,
               page count or loaded pixels of the previous hand survive. */
            <StripsPanel
              key={hand}
              hand={hand}
              version={bestand.fassungen.angenommen}
              filter={stripFilter}
              onFilter={setStripFilter}
              labelOf={itemLabel}
            />
          )}
          {ansicht === 'statistik' && <StatistikView bestand={bestand} />}
          {ansicht === 'drucken' && <DruckenView hand={hand} printed={printed} onPrinted={handlePrinted} />}
        </>
      )}
    </Box>
  );
}
