// Nachfahr-Übersicht — every hand-authored word trace of this source, stacked,
// each over its own specimen crop. A quality pass over one's OWN pen work:
// after a tablet session the author scans down the column, spots where a line
// sat beside the ink or wobbled, and jumps straight into the editor to fix
// exactly that spot (Anpassen mode). Only `authored` rows appear — the
// automatic fits have their own faces in the compare view; here the question
// is „wie sauber ist meine Bahn?", nothing else.
//
// The crop can be blended out („nur die Bahn"): a wobble reads best on the
// naked line, a registration error only against the ink — both one switch.

import { Alert, Box, Button, Chip, CircularProgress, FormControlLabel, Switch, Tooltip, Typography } from '@mui/material';
import { useMemo, useState } from 'react';

import { useInView } from '@/hooks/useInView';
import { useAdmin } from '@/context/AdminContext';
import { wordSampleCropUrl } from '@/lib/api';
import type { WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { frameStale, traceRegistration } from '@/sections/admin/belege/registration';
import { WordTraceEditorDialog } from '@/sections/admin/belege/WordTraceEditorDialog';
import { isDevSetSpecimen } from '@/sections/admin/belege/tracebenchDevSet';
import { WERKBANK_COLORS, traceFrameOf, traceMatrix } from '@/sections/admin/shell/model';
import { useWorkbench } from '@/sections/admin/shell/WorkbenchData';
import { garamond } from '@/styles/paper';

// Taller than the compare cards' 220 px: judging one's own line needs room —
// this face carries no second engine face beside it competing for width.
const REVIEW_H = 300;

function ReviewRow({
  row,
  sample,
  sourceId,
  bare,
  onEdit,
  onOpenWord,
}: {
  row: WordInstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  bare: boolean;
  onEdit: () => void;
  onOpenWord: () => void;
}) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const t = de.admin.words;
  const tb = de.admin.belege;
  // The exporter's frame gate, client-side — the editor heals a flagged row
  // on open (re-anchoring), so the badge's remedy really is „Nachfahren".
  const stale = frameStale(traceRegistration(row.measurements, sample), sample);
  const dev = isDevSetSpecimen(row.kind, row.specimen_id);
  const width = (REVIEW_H / sample.height) * sample.width;

  return (
    <Box ref={ref} sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper' }}>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>{row.word}</Typography>
        <Typography variant="caption" color="text.secondary">
          {row.specimen_id}
        </Typography>
        {dev && (
          <Tooltip title={t.reviewDevChipHint}>
            <Chip size="small" color="info" variant="outlined" label={t.reviewDevChip} />
          </Tooltip>
        )}
        {stale && (
          <Tooltip title={t.reviewFrameStaleHint}>
            <Chip size="small" color="warning" label={t.reviewFrameStale} />
          </Tooltip>
        )}
        {sample.sample_set && <Chip size="small" variant="outlined" label={sample.sample_set} />}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <Button size="small" onClick={onOpenWord}>
            {t.reviewOpenWord}
          </Button>
          <Button size="small" variant="outlined" onClick={onEdit}>
            {tb.editOpen}
          </Button>
        </Box>
      </Box>
      {inView ? (
        <Box sx={{ overflowX: 'auto' }}>
          <svg
            width={width}
            height={REVIEW_H}
            viewBox={`0 0 ${sample.width} ${sample.height}`}
            style={{ display: 'block', background: '#fff', maxWidth: '100%', height: 'auto' }}
            aria-label={`${tb.cropAlt} ${row.word}`}
          >
            {!bare && (
              <image
                href={wordSampleCropUrl(sourceId, sample.id)}
                x={0}
                y={0}
                width={sample.width}
                height={sample.height}
                preserveAspectRatio="none"
              />
            )}
            <g transform={traceMatrix(traceFrameOf(row, sample))}>
              {row.strokes.map((stroke, i) => (
                <path
                  key={i}
                  d={stroke.map(([x, y], j) => `${j === 0 ? 'M' : 'L'}${x},${y}`).join(' ')}
                  fill="none"
                  // On the naked white ground the dark sketch green reads best;
                  // over plate ink only the bright token survives (the same
                  // split the colour tokens exist for).
                  stroke={bare ? WERKBANK_COLORS.trace : WERKBANK_COLORS.traceOverInk}
                  strokeOpacity={0.95}
                  // Thinner than the compare cards' 0.11: this view exists to
                  // judge the line AGAINST the ink, so the ink must stay
                  // visible on both sides of it even on a small crop.
                  strokeWidth={0.07}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
            </g>
          </svg>
        </Box>
      ) : (
        <Box sx={{ height: REVIEW_H }} />
      )}
    </Box>
  );
}

export function AuthoredTraceReview({
  filterText,
  onPickWord,
}: {
  filterText: string;
  // Jump to the word's detail view (the full evidence: engine face, boxes).
  onPickWord: (word: string, specimenId: string) => void;
}) {
  const { source, sourceId } = useAdmin();
  const workbench = useWorkbench();
  const t = de.admin.words;
  const [bare, setBare] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);

  const rows = useMemo(() => {
    const needle = filterText.trim().toLowerCase();
    return workbench.wordRows
      .filter((row) => row.provenance === 'authored' && workbench.sampleById.has(row.specimen_id))
      .filter((row) => !needle || row.word.toLowerCase().includes(needle))
      .sort((a, b) => a.word.localeCompare(b.word, 'de') || a.specimen_id.localeCompare(b.specimen_id, 'de'));
  }, [workbench.wordRows, workbench.sampleById, filterText]);

  if (workbench.error) return <Alert severity="warning">{de.admin.shell.evidenceError}</Alert>;
  if (workbench.loading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={24} />
      </Box>
    );
  }
  if (rows.length === 0) return <Alert severity="info">{t.reviewEmpty}</Alert>;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="caption" color="text.secondary">
          {fmt(rows.length === 1 ? t.reviewCountOne : t.reviewCount, { count: rows.length })}
        </Typography>
        <FormControlLabel
          control={<Switch size="small" checked={bare} onChange={(e) => setBare(e.target.checked)} />}
          label={<Typography variant="caption">{t.reviewBareToggle}</Typography>}
        />
      </Box>
      {rows.map((row) => {
        const sample = workbench.sampleById.get(row.specimen_id);
        if (!sample) return null;
        return (
          <ReviewRow
            key={`${row.kind}:${row.specimen_id}`}
            row={row}
            sample={sample}
            sourceId={sourceId}
            bare={bare}
            onEdit={() => setEditing(row.specimen_id)}
            onOpenWord={() => onPickWord(row.word, row.specimen_id)}
          />
        );
      })}
      {editing &&
        (() => {
          const row = rows.find((r) => r.specimen_id === editing);
          const sample = row ? workbench.sampleById.get(row.specimen_id) : undefined;
          if (!row || !sample) return null;
          return (
            <WordTraceEditorDialog
              open
              row={row}
              sample={sample}
              sourceId={sourceId}
              fallbackHandId={source?.hand_id ?? null}
              onClose={() => setEditing(null)}
              // The stored row changed under the list — refetch the traces so
              // the review shows what was saved, not the load-time snapshot.
              onSaved={() => {
                setEditing(null);
                workbench.refreshWordTraces();
              }}
            />
          );
        })()}
    </Box>
  );
}
