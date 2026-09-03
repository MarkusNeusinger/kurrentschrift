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

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  fetchEigenhandSheetPdf,
  fetchEigenhandStackPdf,
  getEigenhandBestand,
  getEigenhandHands,
  printEigenhandSheets,
} from '@/lib/api';
import type { EigenhandBestand, EigenhandBucket, EigenhandStripFilter } from '@/lib/api';
import { latestRequestGate } from '@/lib/latestRequest';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de, fmt } from '@/locales/admin';
import { glyphOf } from '@/sections/admin/eigenhand/coverageLabels';
import { SetupPanel } from '@/sections/admin/eigenhand/SetupPanel';
import { StripsPanel } from '@/sections/admin/eigenhand/StripsPanel';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

const BUCKET_LABELS: Record<string, string> = {
  klein: de.admin.eigenhand.bucketKlein,
  gross: de.admin.eigenhand.bucketGross,
  ligatur: de.admin.eigenhand.bucketLigatur,
  ziffer: de.admin.eigenhand.bucketZiffer,
  zeichen: de.admin.eigenhand.bucketZeichen,
};

// `glyphOf` moved to coverageLabels.ts, where the key-to-character map is
// DERIVED from the glyph registry instead of hand-written a second time. It had
// drifted by two entries, which is why the grid printed the literal word
// "semicolon" among twelve characters — the reason is recorded there.

// A coverage item as the view names it: `a>b` → „a › b", `a@medial` → „a
// (medial)", a bare key → its glyph.
const itemLabel = (item: string): string => {
  if (item.includes('>')) return item.split('>').map(glyphOf).join(' › ');
  const [key, position] = item.split('@');
  return position ? `${glyphOf(key)} (${position})` : glyphOf(key);
};

function Stat({ value, label }: { value: number | string; label: string }) {
  return (
    <Box sx={{ minWidth: '5.5rem' }}>
      <Typography variant="h5" sx={{ color: paper.ink, lineHeight: 1.1 }}>
        {value}
      </Typography>
      <Typography variant="caption" sx={{ color: paper.inkSoft }}>
        {label}
      </Typography>
    </Box>
  );
}

/**
 * One glyph class as a grid of its keys — written ones inked, open ones pale.
 * A written key is a button: it brings up the words that hold the glyph.
 */
function BucketGrid({
  name,
  bucket,
  onSelect,
}: {
  name: string;
  bucket: EigenhandBucket;
  onSelect: (key: string) => void;
}) {
  const t = de.admin.eigenhand;
  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction="row" spacing={1} sx={{ mb: 0.5, flexWrap: 'wrap', alignItems: 'baseline' }}>
        <Typography variant="subtitle2" sx={{ color: paper.ink }}>
          {BUCKET_LABELS[name] ?? name}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.coverageOf, { covered: bucket.covered, possible: bucket.possible })} ·{' '}
          {fmt(t.coverageBelege, { belege: bucket.belege })}
        </Typography>
      </Stack>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {bucket.keys.map((row) => (
          <Tooltip
            key={row.key}
            describeChild
            title={`${fmt(t.keyTooltip, { key: row.key, belege: row.belege, planned: row.planned })}${
              row.belege ? t.keyTooltipShow : ''
            }`}
          >
            {/* A written key is a real <button> (native keyboard + semantics);
                an unwritten one has nothing to show and stays a plain cell. */}
            <Box
              component={row.belege ? 'button' : 'div'}
              type={row.belege ? 'button' : undefined}
              onClick={row.belege ? () => onSelect(row.key) : undefined}
              sx={{
                minWidth: '2.1rem',
                px: 0.5,
                py: 0.25,
                textAlign: 'center',
                font: 'inherit',
                appearance: 'none',
                border: 1,
                borderRadius: 1,
                borderColor: row.belege ? paper.sepia : 'divider',
                bgcolor: row.belege ? 'action.hover' : 'transparent',
                color: row.belege ? paper.ink : 'text.disabled',
                cursor: row.belege ? 'pointer' : 'default',
              }}
            >
              <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                {glyphOf(row.key)}
              </Typography>
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'inherit' }}>
                {row.belege}
              </Typography>
            </Box>
          </Tooltip>
        ))}
      </Box>
    </Box>
  );
}

export function EigenhandView() {
  const t = de.admin.eigenhand;
  const [hands, setHands] = useState<string[]>([]);
  const [hand, setHand] = useState('');
  const [bestand, setBestand] = useState<EigenhandBestand | null>(null);
  const [loadError, setLoadError] = useState<ApiErrorText | null>(null);
  const [loading, setLoading] = useState(false);
  const [sheets, setSheets] = useState(1);
  const [repeat, setRepeat] = useState(1);
  const [printing, setPrinting] = useState(false);
  const [printed, setPrinted] = useState<string[]>([]);
  // The print block reports two different failures — the Bogen could not be
  // generated, or its PDF could not be fetched — so the lead sentence travels
  // WITH the error instead of being fixed at the render site. Before this both
  // arrived under „Der Bogen konnte nicht erzeugt werden.", the PDF case with
  // its own lead pasted in front of the raw line on top of that.
  const [printError, setPrintError] = useState<{ prefix: string; error: ApiErrorText } | null>(null);
  const [openOnly, setOpenOnly] = useState(true);
  // What the strips panel shows: a word, an item, or everything. A cell of
  // the coverage grid sets the item and brings the panel into view.
  const [stripFilter, setStripFilter] = useState<EigenhandStripFilter>({});
  const stripsRef = useRef<HTMLDivElement | null>(null);
  const showBelege = useCallback((item: string) => {
    setStripFilter((current) => ({ ...current, item }));
    // An instant jump, not a smooth scroll: the grid sits below the panel, so
    // a smooth scroll would sweep the viewport across the whole gallery on its
    // way up and every crop tile would count as seen — and load at once.
    stripsRef.current?.scrollIntoView({ block: 'start' });
  }, []);

  useEffect(() => {
    let cancelled = false;
    getEigenhandHands({ retries: 2 })
      .then((data) => {
        if (cancelled) return;
        setHands(data.hands);
        // A first-run admin has no hand yet; the styles tell us what a legal
        // one looks like, so the field starts on a usable default instead of
        // empty.
        setHand((current) => current || data.hands[0] || `mn-${data.styles[1] ?? 'suetterlin'}`);
      })
      .catch((err: unknown) => !cancelled && setLoadError(apiErrorText(err)));
    return () => {
      cancelled = true;
    };
  }, []);

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

  const openJoins = useMemo(
    () => (bestand ? bestand.joins.rows.filter((row) => !openOnly || row.belege === 0) : []),
    [bestand, openOnly],
  );

  const print = () => {
    setPrinting(true);
    setPrintError(null);
    printEigenhandSheets({ hand, sheets, repeat })
      .then((res) => {
        setPrinted(res.sheets.map((s) => s.sheet));
        // The hand has not changed, so the render guard above says nothing —
        // a refresh sets its own flags, which an event continuation may.
        setLoading(true);
        setLoadError(null);
        reload(hand);
      })
      .catch((err: unknown) => setPrintError({ prefix: t.printError, error: apiErrorText(err) }))
      .finally(() => setPrinting(false));
  };

  const showPdf = (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank', 'noopener');
    // The tab keeps its own reference; releasing ours right away would race
    // the open in some browsers, so give it a beat.
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  };

  const openPdf = async (sheet: string) => {
    try {
      showPdf(await fetchEigenhandSheetPdf(hand, sheet));
    } catch (err: unknown) {
      setPrintError({ prefix: t.pdfError, error: apiErrorText(err) });
    }
  };

  // The whole job as ONE document — what goes to the printer. The per-Bogen
  // buttons stay for reprinting a single page.
  const openStackPdf = async () => {
    try {
      showPdf(await fetchEigenhandStackPdf(hand, printed));
    } catch (err: unknown) {
      setPrintError({ prefix: t.pdfError, error: apiErrorText(err) });
    }
  };

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      <ViewHeader eyebrow={de.admin.shell.startEyebrow} title={t.title} intro={t.intro} />

      <Stack direction="row" spacing={2} sx={{ mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          select={hands.length > 0}
          size="small"
          label={t.hand}
          value={hand}
          helperText={hands.length ? undefined : t.handHelp}
          onChange={(e) => {
            setHand(e.target.value);
            setStripFilter({});
          }}
          sx={{ minWidth: '14rem' }}
        >
          {hands.map((id) => (
            <MenuItem key={id} value={id}>
              {id}
            </MenuItem>
          ))}
        </TextField>
        {loading && <CircularProgress size={16} />}
        {!hands.length && (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.noHands}
          </Typography>
        )}
      </Stack>

      {loadError && !bestand && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <ErrorText error={loadError} prefix={t.loadError} />
        </Alert>
      )}

      {bestand && (
        <Stack spacing={3}>
          <SetupPanel hand={hand} />

          <Panel title={t.stripsTitle} caption={t.queueTitle}>
            <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', rowGap: 2 }}>
              <Stat value={bestand.strips.belegt} label={t.stripsBelegt} />
              <Stat value={bestand.strips.unterwegs} label={t.stripsUnterwegs} />
              <Stat value={bestand.strips.geplant} label={t.stripsGeplant} />
              <Stat value={bestand.strips.total} label={t.stripsTotal} />
              <Stat value={bestand.fassungen.angenommen} label={t.fassungenAngenommen} />
              <Stat value={bestand.fassungen.verworfen} label={t.fassungenVerworfen} />
              <Stat value={bestand.sheets.printed} label={t.sheetsPrinted} />
            </Stack>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 2 }}>
              {bestand.queue.map((sid) => (
                <Chip key={sid} size="small" variant="outlined" label={sid} />
              ))}
            </Box>
          </Panel>

          <Box ref={stripsRef}>
            {/* Keyed by hand: a switch remounts the panel, so no search term,
                page count or loaded pixels of the previous hand survive. */}
            <StripsPanel
              key={hand}
              hand={hand}
              version={bestand.fassungen.angenommen}
              filter={stripFilter}
              onFilter={setStripFilter}
              labelOf={itemLabel}
            />
          </Box>

          <Panel
            title={t.coverageTitle}
            caption={fmt(t.coverageOf, {
              covered: Object.values(bestand.glyphs).reduce((sum, b) => sum + b.covered, 0),
              possible: Object.values(bestand.glyphs).reduce((sum, b) => sum + b.possible, 0),
            })}
          >
            {Object.entries(bestand.glyphs).map(([name, bucket]) => (
              <BucketGrid key={name} name={name} bucket={bucket} onSelect={showBelege} />
            ))}
          </Panel>

          <Panel
            title={t.coverageJoins}
            caption={`${fmt(t.coverageOf, {
              covered: bestand.joins.covered,
              possible: bestand.joins.possible,
            })} — ${t.joinsIntro}`}
            actions={
              <FormControlLabel
                control={<Switch size="small" checked={openOnly} onChange={(e) => setOpenOnly(e.target.checked)} />}
                label={<Typography variant="caption">{t.joinsShowOpen}</Typography>}
              />
            }
          >
            {openJoins.length === 0 ? (
              <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                {t.joinsEmpty}
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: '20rem', overflowY: 'auto' }}>
                {openJoins.map((row) => (
                  <Chip
                    key={row.item}
                    size="small"
                    variant={row.belege ? 'filled' : 'outlined'}
                    label={`${itemLabel(row.item)}${row.belege ? ` · ${row.belege}` : ''}`}
                    onClick={row.belege ? () => showBelege(row.item) : undefined}
                  />
                ))}
              </Box>
            )}
          </Panel>

          <Panel title={t.printTitle} caption={t.printIntro}>
            <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', rowGap: 2, alignItems: 'center' }}>
              <TextField
                type="number"
                size="small"
                label={t.printSheets}
                value={sheets}
                onChange={(e) => setSheets(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
                sx={{ width: '8rem' }}
              />
              <TextField
                type="number"
                size="small"
                label={t.printRepeat}
                value={repeat}
                onChange={(e) => setRepeat(Math.max(1, Math.min(8, Number(e.target.value) || 1)))}
                sx={{ width: '11rem' }}
              />
              <Button variant="contained" onClick={print} disabled={printing || !hand}>
                {printing ? t.printing : t.printAction}
              </Button>
            </Stack>

            {printError && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <ErrorText error={printError.error} prefix={printError.prefix} />
              </Alert>
            )}

            {printed.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {fmt(t.printed, { count: printed.length, sheets: printed.join(', ') })}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
                  <Button size="small" variant="contained" onClick={openStackPdf}>
                    {fmt(t.openStackPdf, { count: printed.length })}
                  </Button>
                  {printed.length > 1 &&
                    printed.map((sheet) => (
                      <Button key={sheet} size="small" variant="outlined" onClick={() => openPdf(sheet)}>
                        {sheet} · {t.openPdf}
                      </Button>
                    ))}
                </Stack>
                <Box sx={{ mt: 1.5 }}>
                  <TerminalCommand
                    lead={t.localHint}
                    command={fmt(t.localHintCommand, { hand, sheet: printed[0] })}
                  />
                </Box>
              </Box>
            )}
          </Panel>

          <Panel title={t.quotenTitle} caption={t.quotenCaption}>
            {bestand.quoten ? (
              <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', rowGap: 2 }}>
                <Stat
                  value={`${(bestand.quoten.erstbeleg_weighted * 100).toFixed(1)} %`}
                  label={`Erstbeleg (gewichtet) · ${bestand.quoten.erstbeleg}/${bestand.quoten.items}`}
                />
                <Stat
                  value={`${(bestand.quoten.ausbau_weighted * 100).toFixed(1)} %`}
                  label={`Ausbau (gewichtet) · ${bestand.quoten.ausbau}/${bestand.quoten.soll_belege}`}
                />
              </Stack>
            ) : (
              <TerminalCommand lead={fmt(t.quotenNone, { hand })} command={t.quotenNoneCommand} />
            )}
          </Panel>
        </Stack>
      )}
    </Box>
  );
}
