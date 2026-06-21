// Übersicht verification panel — the "does everything fit?" surface, shown on
// the right of the final step. Three aligned cells side by side: the original
// crop (Vorlage), the synthesised ductus written live (Geschrieben — the
// animated WrittenGlyph, replayable via "Neu schreiben") and the two laid over
// each other (Überlagert — the optimized silhouette in red over the crop, so a
// mismatch jumps out). Below them the score and the per-category breakdown
// (Bewertungskriterien). All of it reads the same trace-preview dry run the Weg
// step computed (or computes it on arrival if the user jumped straight here).

import ReplayIcon from '@mui/icons-material/Replay';
import { Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useEffect, useRef, useState, type ReactNode } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useAdmin } from '@/context/AdminContext';
import { cropUrl } from '@/lib/api';
import type { TracePreviewOut } from '@/lib/api';
import { de } from '@/locales';
import { HintHeading } from './HintHeading';
import { ScoreBreakdown, SilhouetteSvg, scoreColor } from './previewParts';

const CELL_H = 150;

export function OverviewVerify({
  glyphKey,
  cropCacheBust,
  hasCanonical,
  nAnchors,
  preview,
  previewBusy,
  computePreview,
}: {
  glyphKey: string;
  cropCacheBust?: number;
  hasCanonical: boolean;
  nAnchors?: number;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  computePreview: (nAnchors: number) => Promise<void>;
}) {
  const { sourceId } = useAdmin();
  const t = de.wizard.overview.verify;
  // Bumping this remounts the WrittenGlyph so the write-in animation replays.
  const [replayKey, setReplayKey] = useState(0);

  // Compute the comparison once on arrival when there is none yet (the user
  // jumped straight to Übersicht). If the Weg step already produced one, reuse
  // it as-is. One attempt per glyph — a failed dry run doesn't loop.
  const tried = useRef(false);
  useEffect(() => {
    tried.current = false;
  }, [glyphKey]);
  useEffect(() => {
    if (!preview && !previewBusy && hasCanonical && typeof nAnchors === 'number' && nAnchors > 0 && !tried.current) {
      tried.current = true;
      void computePreview(nAnchors);
    }
  }, [preview, previewBusy, hasCanonical, nAnchors, computePreview]);

  if (!hasCanonical) return null;

  const refined = preview?.refined;
  const cropW = refined?.crop_size.w ?? 1;
  const cropH = refined?.crop_size.h ?? 1;
  const cellW = (CELL_H * cropW) / cropH;
  const delta =
    preview?.raw.quality && preview?.refined.quality ? preview.refined.quality.score - preview.raw.quality.score : null;

  return (
    <Stack spacing={1.5}>
      <HintHeading
        title={t.title}
        action={
          <Button size="small" startIcon={<ReplayIcon />} onClick={() => setReplayKey((k) => k + 1)} disabled={!refined}>
            {t.rewrite}
          </Button>
        }
      >
        <Typography variant="body2" gutterBottom>
          {t.body}
        </Typography>
        <Typography variant="body2">{de.wizard.optimize.overlayCaption}</Typography>
      </HintHeading>

      {previewBusy && !refined && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
          <CircularProgress size={16} />
          <Typography variant="caption" color="text.secondary">
            {de.wizard.optimize.computing}
          </Typography>
        </Box>
      )}

      {refined && (
        <>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Cell label={t.cellCrop}>
              <Box sx={{ width: cellW, height: CELL_H, bgcolor: '#fff', border: 1, borderColor: 'divider' }}>
                <img
                  src={cropUrl(sourceId, glyphKey, cropCacheBust)}
                  alt={t.cellCrop}
                  width={cellW}
                  height={CELL_H}
                  style={{ display: 'block', objectFit: 'fill' }}
                />
              </Box>
            </Cell>
            <Cell label={t.cellWritten}>
              <Box
                sx={{
                  height: CELL_H,
                  minWidth: cellW,
                  px: 1,
                  bgcolor: '#fff',
                  border: 1,
                  borderColor: 'divider',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <WrittenGlyph
                  key={replayKey}
                  glyphKey={glyphKey}
                  data={refined}
                  cacheBust={cropCacheBust}
                  tight
                  height={CELL_H - 12}
                  maxWidth={cellW * 2}
                  surfaceBg="#fff"
                />
              </Box>
            </Cell>
            <Cell label={t.cellOverlay}>
              <Box sx={{ width: cellW, height: CELL_H, bgcolor: '#fff', border: 1, borderColor: 'divider', position: 'relative' }}>
                <img
                  src={cropUrl(sourceId, glyphKey, cropCacheBust)}
                  alt={t.cellOverlay}
                  width={cellW}
                  height={CELL_H}
                  style={{ display: 'block', position: 'absolute', inset: 0, objectFit: 'fill' }}
                />
                <Box sx={{ position: 'absolute', inset: 0 }}>
                  <SilhouetteSvg data={refined} w={cellW} h={CELL_H} fill="#e02030" fillOpacity={0.42} />
                </Box>
              </Box>
            </Cell>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            {refined.quality && (
              <Chip size="small" color={scoreColor(refined.quality.score)} label={`${de.wizard.optimize.score} ${refined.quality.score.toFixed(1)}`} />
            )}
            {delta != null && (
              <Typography variant="caption" sx={{ fontFamily: 'monospace' }} color={delta >= 0 ? 'success.main' : 'error.main'}>
                {de.wizard.optimize.delta} {delta >= 0 ? '+' : ''}
                {delta.toFixed(1)}
              </Typography>
            )}
          </Box>
          {refined.quality && <ScoreBreakdown quality={refined.quality} />}
        </>
      )}
    </Stack>
  );
}

function Cell({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Stack spacing={0.5} sx={{ alignItems: 'flex-start' }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      {children}
    </Stack>
  );
}
