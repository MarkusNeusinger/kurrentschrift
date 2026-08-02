// Werkbank (/admin/werkbank) — ONE optimisation surface instead of the split
// between Vergleich, Paar-Matrix and Belege (proposal optimierungs-werkbank.md
// §2). Left: the word spine, worst first, where errors actually become visible.
// Right: the Auftragskorb and a context lens that switches to whatever element
// was clicked in a word — a letter with its chart form and all its occurrences,
// or a join with its dissections and the way into the pair editor.
//
// All four occurrence sources load once per source and are joined client-side:
// word traces + word samples (the spine), letter instances (the boxes and the
// letter lens) and pair instances (the pair lens). A few hundred rows each —
// one round trip beats a request per card.
//
// The hand's STATISTICS layers (Stufenplan H1/H2) load separately, keyed on the
// hand the occurrences name: they are admin-gated and secondary, so a failure
// there must degrade to "keine Statistik" instead of taking the whole page down
// with it — same rule the Auftragskorb follows. Letters and joins are two
// INDEPENDENT layers (own state, own error flag, own refetch): rebuilding one
// must neither blank the other lens nor swallow its own result caption.

import { Alert, Box, CircularProgress, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAdmin } from '@/context/AdminContext';
import { LETTER_BY_KEY } from '@/domain/glyphs';
import {
  getWordSamples,
  listAggregates,
  listInstances,
  listPairAggregates,
  listPairInstances,
  listWordInstances,
  rebuildAggregates,
  rebuildPairAggregates,
} from '@/lib/api';
import type {
  AggregateOut,
  InstanceOut,
  PairAggregateOut,
  PairInstanceOut,
  WordInstanceOut,
  WordSampleOut,
} from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';

import { ContextLens } from './ContextLens';
import { KorbPanel } from './KorbPanel';
import type { StatsContext, StatsStatus } from './LensStats';
import { MarkDialog } from './MarkDialog';
import { WordSpineCard } from './WordSpineCard';
import { badness, markKey, pairKeyOf, scrollToCard, type Mark, type Selection } from './model';

// One loaded statistics layer, tagged with the hand it was loaded FOR. Tagging
// instead of resetting is what makes the two behaviours coexist: a hand switch
// invalidates the rows implicitly (they are simply not this hand's), while a
// refetch after a rebuild leaves them mounted until the fresh ones arrive —
// stale-while-revalidate, so the rebuild's caption stays readable.
interface StatsLayer<T> {
  handId: string | null;
  rows: T[] | null;
  error: boolean;
}

// The layer's rows for the CURRENT hand, or null while they still belong to a
// previous one.
const rowsFor = <T,>(layer: StatsLayer<T>, handId: string | null): T[] | null =>
  handId !== null && layer.handId === handId ? layer.rows : null;

function statsContextOf<T>(
  layer: StatsLayer<T>,
  rows: T[] | null,
  handId: string | null,
  handsMixed: boolean,
): StatsContext {
  const status: StatsStatus = !handId
    ? 'no-hand'
    : layer.handId === handId && layer.error
      ? 'unavailable'
      : rows === null
        ? 'loading'
        : 'ready';
  return { status, handId, handsMixed, layerEmpty: rows !== null && rows.length === 0 };
}

export function WerkbankView() {
  const { source, sourceId, setActiveGlyph } = useAdmin();
  const navigate = useNavigate();
  const t = de.admin.werkbank;

  const [rows, setRows] = useState<WordInstanceOut[] | null>(null);
  const [samples, setSamples] = useState<WordSampleOut[] | null>(null);
  const [instances, setInstances] = useState<InstanceOut[] | null>(null);
  const [pairInstances, setPairInstances] = useState<PairInstanceOut[] | null>(null);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState('');
  const [selection, setSelection] = useState<Selection | null>(null);
  const [mark, setMark] = useState<Mark | null>(null);
  // Bumped after a filing so the Korb refetches; also the pair editor's
  // "something changed" signal is not needed here (the spine shows specimen
  // ink, not the composition).
  const [korbTick, setKorbTick] = useState(0);
  const [editingPair, setEditingPair] = useState<{ text: string; left: string; right: string } | null>(null);
  // The statistics layers, loaded per hand rather than per source — one state
  // each, so a failure or a rebuild stays inside its own layer.
  const [letterLayer, setLetterLayer] = useState<StatsLayer<AggregateOut>>({
    handId: null,
    rows: null,
    error: false,
  });
  const [pairLayer, setPairLayer] = useState<StatsLayer<PairAggregateOut>>({
    handId: null,
    rows: null,
    error: false,
  });
  // Bumped by a rebuild so THAT layer refetches (a rebuild replaces wholesale).
  const [letterTick, setLetterTick] = useState(0);
  const [pairTick, setPairTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    setSamples(null);
    setInstances(null);
    setPairInstances(null);
    setError(false);
    setSelection(null);
    setMark(null);
    setEditingPair(null);
    Promise.all([
      listWordInstances(sourceId, undefined, { retries: 2 }),
      getWordSamples(sourceId, { retries: 2 }),
      listInstances(sourceId, undefined, { retries: 2 }),
      listPairInstances(sourceId, undefined, { retries: 2 }),
    ])
      .then(([wordRows, wordSamples, letterRows, joinRows]) => {
        if (cancelled) return;
        setRows(wordRows);
        setSamples(wordSamples);
        setInstances(letterRows);
        setPairInstances(joinRows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  // The Werkbank always shows exactly one source and therefore one hand
  // (optimierungs-werkbank.md §6). WHICH hand comes from the loaded rows, never
  // from a constant: the most frequent non-null hand_id across all three
  // occurrence levels. Rows may predate the hands wiring and carry none — if no
  // row names a hand at all, there simply is no statistics layer to show.
  // `mixed` is the honesty flag: once a second writer is harvested (the Abb.-22
  // Schülerhand under its own id), showing one hand's medians over another
  // hand's occurrences must be said out loud rather than happen silently.
  const { handId, handsMixed } = useMemo(() => {
    const counts = new Map<string, number>();
    const tally = (id: string | null | undefined) => {
      if (id) counts.set(id, (counts.get(id) ?? 0) + 1);
    };
    for (const inst of instances ?? []) tally(inst.hand_id);
    for (const occ of pairInstances ?? []) tally(occ.hand_id);
    for (const row of rows ?? []) tally(row.hand_id);
    let best: string | null = null;
    let bestCount = 0;
    for (const [id, count] of counts) {
      if (count > bestCount) {
        best = id;
        bestCount = count;
      }
    }
    return { handId: best, handsMixed: counts.size > 1 };
  }, [instances, pairInstances, rows]);

  // Deliberately NOT part of the spine's Promise.all, and one effect per layer:
  // these reads are admin-gated and secondary (a 401, or an empty statistics
  // table, must leave the word spine and both lenses fully usable), and the
  // per-layer rebuild refetches only its own list. Nothing is reset here — the
  // result carries its hand, so a hand switch invalidates the rows on read and
  // a rebuild refetch keeps the previous ones on screen meanwhile.
  useEffect(() => {
    if (!handId) return;
    let cancelled = false;
    listAggregates(handId, { retries: 1 })
      .then((glyphRows) => {
        if (!cancelled) setLetterLayer({ handId, rows: glyphRows, error: false });
      })
      .catch(() => {
        if (!cancelled) setLetterLayer({ handId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [handId, letterTick]);

  useEffect(() => {
    if (!handId) return;
    let cancelled = false;
    listPairAggregates(handId, undefined, { retries: 1 })
      .then((joinRows) => {
        if (!cancelled) setPairLayer({ handId, rows: joinRows, error: false });
      })
      .catch(() => {
        if (!cancelled) setPairLayer({ handId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [handId, pairTick]);

  const aggregates = rowsFor(letterLayer, handId);
  const pairAggregates = rowsFor(pairLayer, handId);

  const sampleById = useMemo(() => new Map((samples ?? []).map((s) => [s.id, s])), [samples]);

  // Boxes per word card, ascending by composer slot (the join dots pair up
  // neighbours in that order).
  const boxesBySpecimen = useMemo(() => {
    const map = new Map<string, InstanceOut[]>();
    for (const inst of instances ?? []) {
      const id = inst.measurements.specimen_id;
      if (!id) continue;
      const list = map.get(id);
      if (list) list.push(inst);
      else map.set(id, [inst]);
    }
    for (const list of map.values()) list.sort((a, b) => (a.measurements.slot ?? 0) - (b.measurements.slot ?? 0));
    return map;
  }, [instances]);

  const instancesByKey = useMemo(() => {
    const map = new Map<string, InstanceOut[]>();
    for (const inst of instances ?? []) {
      const list = map.get(inst.glyph_key);
      if (list) list.push(inst);
      else map.set(inst.glyph_key, [inst]);
    }
    return map;
  }, [instances]);

  const pairsByKey = useMemo(() => {
    const map = new Map<string, PairInstanceOut[]>();
    for (const occ of pairInstances ?? []) {
      const key = pairKeyOf(occ.left_key, occ.right_key);
      const list = map.get(key);
      if (list) list.push(occ);
      else map.set(key, [occ]);
    }
    return map;
  }, [pairInstances]);

  // One row per glyph key, lowest variant wins: the lens asks about the LETTER,
  // and the base variant is the row the Laufform is derived from.
  const aggregatesByKey = useMemo(() => {
    const map = new Map<string, AggregateOut>();
    for (const agg of aggregates ?? []) {
      const prev = map.get(agg.glyph_key);
      if (!prev || agg.variant < prev.variant) map.set(agg.glyph_key, agg);
    }
    return map;
  }, [aggregates]);

  const pairAggregateByKey = useMemo(
    () => new Map((pairAggregates ?? []).map((agg) => [pairKeyOf(agg.left_key, agg.right_key), agg])),
    [pairAggregates],
  );

  // Worst first — the same ranking the Belege page uses, and the reason the
  // spine is a work list rather than a gallery.
  const visible = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    return (rows ?? [])
      .filter((r) => !needle || r.word.toLowerCase().includes(needle))
      .filter((r) => sampleById.has(r.specimen_id))
      .sort((a, b) => badness(b) - badness(a));
  }, [rows, filter, sampleById]);

  const orphans = useMemo(
    () => (rows ?? []).filter((r) => !sampleById.has(r.specimen_id)),
    [rows, sampleById],
  );

  // The lens' rows for the current selection: letters worst-first (highest fit
  // residual on top), joins in specimen order.
  const letterOccurrences = useMemo(() => {
    if (selection?.target.kind !== 'letter') return [];
    return [...(instancesByKey.get(selection.target.glyphKey) ?? [])].sort(
      (a, b) => (b.measurements.geo_rmse_px ?? 0) - (a.measurements.geo_rmse_px ?? 0),
    );
  }, [selection, instancesByKey]);

  const pairOccurrences = useMemo(() => {
    if (selection?.target.kind !== 'pair') return [];
    return pairsByKey.get(pairKeyOf(selection.target.leftKey, selection.target.rightKey)) ?? [];
  }, [selection, pairsByKey]);

  // The pair editor is keyed on TEXT (it composes the pair via /write/word), so
  // the lens can only hand over when the two glyphs' characters shape back to
  // exactly these keys — `ſ`+`t` folds into the ſt ligature and has no join.
  const pairEditorTarget = useMemo(() => {
    if (selection?.target.kind !== 'pair') return null;
    const { leftKey, rightKey } = selection.target;
    const text = `${LETTER_BY_KEY[leftKey]?.glyph ?? ''}${LETTER_BY_KEY[rightKey]?.glyph ?? ''}`;
    const keys = text.length === 2 ? pairKeysOf(text) : null;
    return keys && keys[0] === leftKey && keys[1] === rightKey ? { text, left: leftKey, right: rightKey } : null;
  }, [selection]);

  // What each lens' statistics block can show right now — per layer, so a
  // failing pair read never mutes the letter block.
  const letterStats = statsContextOf(letterLayer, aggregates, handId, handsMixed);
  const pairStats = statsContextOf(pairLayer, pairAggregates, handId, handsMixed);

  const letterAggregate =
    selection?.target.kind === 'letter' ? aggregatesByKey.get(selection.target.glyphKey) : undefined;
  const pairAggregate =
    selection?.target.kind === 'pair'
      ? pairAggregateByKey.get(pairKeyOf(selection.target.leftKey, selection.target.rightKey))
      : undefined;

  // Recompute ONE statistics layer and report the outcome back as a caption.
  // Non-rendering by design (optimierungs-werkbank.md §3): this condenses
  // occurrences into medians — writing a Laufform row (`apply-laufform`) does
  // affect rendering and is deliberately not offered on this surface.
  const rebuildLetterStats = handId
    ? async () => {
        const out = await rebuildAggregates(handId);
        setLetterTick((n) => n + 1);
        return fmt(t.statsRebuiltLetters, {
          stored: out.stored,
          count: out.keys.reduce((n, key) => n + key.n_instances, 0),
          skipped: Object.values(out.skipped).reduce((n, value) => n + value, 0),
        });
      }
    : undefined;

  const rebuildPairStats = handId
    ? async () => {
        const out = await rebuildPairAggregates(handId);
        setPairTick((n) => n + 1);
        return fmt(t.statsRebuiltPairs, {
          stored: out.stored,
          count: out.pairs.reduce((n, pair) => n + pair.n_instances, 0),
          skipped: Object.values(out.skipped).reduce((n, value) => n + value, 0),
        });
      }
    : undefined;

  const openWizard = (glyphKey: string) => {
    setActiveGlyph(glyphKey);
    navigate(paths.admin.chart);
  };

  // A lens occurrence jumps back into its word: scroll the card into view and
  // move the selection onto that specimen, so the spine highlight follows.
  const jumpTo = (specimenId: string) => {
    const sample = sampleById.get(specimenId);
    if (sample && selection) {
      setSelection({ ...selection, specimen: { id: sample.id, kind: sample.kind, word: sample.word } });
    }
    scrollToCard(specimenId);
  };

  if (!source) return null;
  if (error) return <Alert severity="error">{t.loadError}</Alert>;
  if (rows === null || samples === null || instances === null || pairInstances === null) {
    return (
      <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  return (
    <Box sx={{ overflowY: 'auto', height: '100%', p: { xs: 2, md: 3 } }}>
      <Typography variant="h6">{t.title}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720, mb: 2 }}>
        {t.intro}
      </Typography>

      {rows.length === 0 ? (
        <Alert severity="info">{t.empty}</Alert>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: 'minmax(340px, 1.2fr) minmax(300px, 1fr)' },
            gap: 2,
            alignItems: 'start',
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" color="text.secondary" sx={{ display: 'block' }}>
              {t.spineHeading}
            </Typography>
            <TextField
              size="small"
              label={t.filterLabel}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              sx={{ mb: 2, maxWidth: 280 }}
            />
            {orphans.map((r) => (
              <Alert key={`${r.kind}:${r.specimen_id}`} severity="warning" sx={{ mb: 1 }}>
                {fmt(t.noSample, { id: r.specimen_id })}
              </Alert>
            ))}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {visible.map((r) => (
                <WordSpineCard
                  key={`${r.kind}:${r.specimen_id}`}
                  row={r}
                  sample={sampleById.get(r.specimen_id) as WordSampleOut}
                  sourceId={sourceId}
                  boxes={boxesBySpecimen.get(r.specimen_id) ?? []}
                  selection={selection}
                  onSelect={setSelection}
                  onMark={setMark}
                />
              ))}
            </Box>
          </Box>

          {/* The WHOLE right column sticks (not the lens card): a sticky child
              can only travel within its parent, and this column is content-
              sized — sticking the column against the tall spine track is what
              keeps Korb + lens beside the word the admin just clicked. Taller
              than the viewport it scrolls internally. Single-column (xs) has
              no track to stick in, so it stays in flow. */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              minWidth: 0,
              position: { md: 'sticky' },
              top: { md: 16 },
              // `vh` base with a `dvh` upgrade — same pitfall as PaperBackground:
              // on browsers without the unit the whole declaration is dropped.
              maxHeight: { md: 'calc(100vh - 96px)' },
              '@supports (height: 1dvh)': { maxHeight: { md: 'calc(100dvh - 96px)' } },
              overflowY: { md: 'auto' },
            }}
          >
            <KorbPanel sourceId={sourceId} refreshKey={korbTick} />
            <Box>
              <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                {t.lensHeading}
              </Typography>
              <ContextLens
                sourceId={sourceId}
                selection={selection}
                letterOccurrences={letterOccurrences}
                pairOccurrences={pairOccurrences}
                sampleById={sampleById}
                letterAggregate={letterAggregate}
                pairAggregate={pairAggregate}
                letterStats={letterStats}
                pairStats={pairStats}
                onRebuildAggregates={rebuildLetterStats}
                onRebuildPairAggregates={rebuildPairStats}
                onJump={jumpTo}
                onMark={setMark}
                onOpenWizard={openWizard}
                onOpenPairEditor={pairEditorTarget ? () => setEditingPair(pairEditorTarget) : undefined}
              />
            </Box>
          </Box>
        </Box>
      )}

      {mark && (
        <MarkDialog
          key={markKey(mark)}
          mark={mark}
          sourceId={sourceId}
          onClose={() => setMark(null)}
          onFiled={() => setKorbTick((n) => n + 1)}
          onOpenWizard={openWizard}
        />
      )}
      {editingPair && (
        <PairEditorDialog
          open
          onClose={() => setEditingPair(null)}
          pairText={editingPair.text}
          leftKey={editingPair.left}
          rightKey={editingPair.right}
          sourceId={sourceId}
          // A pair-drill specimen (Abb. 20) registers as the editor's underlay;
          // a whole-word crop would not, so it is deliberately not passed.
          specimen={
            selection && selection.specimen.kind === 'pair' ? sampleById.get(selection.specimen.id) : undefined
          }
        />
      )}
    </Box>
  );
}
