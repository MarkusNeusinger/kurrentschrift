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

import { Alert, Box, CircularProgress, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAdmin } from '@/context/AdminContext';
import { LETTER_BY_KEY } from '@/domain/glyphs';
import {
  getWordSamples,
  listInstances,
  listPairInstances,
  listWordInstances,
} from '@/lib/api';
import type { InstanceOut, PairInstanceOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';

import { ContextLens } from './ContextLens';
import { KorbPanel } from './KorbPanel';
import { MarkDialog } from './MarkDialog';
import { WordSpineCard } from './WordSpineCard';
import { badness, markKey, pairKeyOf, scrollToCard, type Mark, type Selection } from './model';

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
