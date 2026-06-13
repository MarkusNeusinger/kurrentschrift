// Admin comparison view — every authored letter as a big comparison of the
// unaltered chart crop (the goal) and "as written" (the WrittenGlyph the quiz
// uses). Two modes: side by side, or overlaid (the written silhouette projected
// back onto the crop pixels, so coverage of the original ink is judged directly).
// The Diagnose modal shows this for one glyph at a time; here the whole alphabet
// is on one page so shape fidelity can be judged at a glance.
//
// One tile per LETTER: non-split letters share a single authored form across
// positions, so a representative position stands in; a split (per-position)
// letter contributes one tile per canonical position.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, CircularProgress, FormControlLabel, Switch, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useAdmin } from '@/context/AdminContext';
import { glyphKeyFor, isLetterSplit, LETTERS, POSITIONS } from '@/domain/glyphs';
import type { Position } from '@/domain/glyphs';
import { ApiError, cropUrl, getDiagnostic } from '@/lib/api';
import type { DiagnosticData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de, POSITION_LABEL } from '@/locales';

const FACE_H = 320; // px — both faces rendered large

interface Tile {
  key: string;
  letterGlyph: string;
  caption: string;
}

function buildTiles(
  glyphsByKey: Record<string, { has_data: boolean }>,
  bboxesByKey: Record<string, { locked?: boolean; split?: boolean }>,
): Tile[] {
  const hasCanon = (key: string) => glyphsByKey[key]?.has_data === true;
  const tiles: Tile[] = [];
  for (const letter of LETTERS) {
    const canonPositions = POSITIONS.filter((p) => hasCanon(glyphKeyFor(letter, p)));
    if (canonPositions.length === 0) continue;
    const split = isLetterSplit(glyphKeyFor(letter, 'medial'), bboxesByKey);
    if (split) {
      for (const p of canonPositions) {
        tiles.push({
          key: glyphKeyFor(letter, p),
          letterGlyph: letter.glyph,
          caption: `${de.admin.compare.positionPrefix}${POSITION_LABEL[p as Position]}`,
        });
      }
    } else {
      tiles.push({
        key: glyphKeyFor(letter, canonPositions[0]),
        letterGlyph: letter.glyph,
        caption: de.admin.sidebar.unifiedCaption,
      });
    }
  }
  return tiles;
}

function Face({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'center', flex: 1, minWidth: 0 }}>
      <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'flex-start' }}>
        {heading}
      </Typography>
      <Box
        sx={{ height: FACE_H, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}
      >
        {children}
      </Box>
    </Box>
  );
}

// Written silhouette projected back onto the crop pixels and drawn translucent
// over the original ink — direct coverage check. The canonical is normalised
// (baseline=0, midband=1, x-origin at the first sample); the inverse map is a
// pure scale+translate for an upright source (Sütterlin 90°): 1 template unit =
// (baseline_y_crop - midband_y_crop) px, pinned by the first anchor.
function CropWrittenOverlay({
  data,
  sourceId,
  glyphKey,
  cropCacheBust,
  height,
}: {
  data: DiagnosticData;
  sourceId: string;
  glyphKey: string;
  cropCacheBust: number;
  height: number;
}) {
  const cropW = data.crop_size.w;
  const cropH = data.crop_size.h;
  const unitPx = data.baseline_y_crop - data.midband_y_crop; // px per template unit
  const a0px = data.anchors_px[0];
  const a0t = data.anchors_template[0];
  const canMap = !!a0px && !!a0t && Number.isFinite(unitPx) && unitPx > 0;
  // template (x,y up) -> crop px: px_x = unitPx*x + ex ; px_y = -unitPx*y + baseline
  const ex = canMap ? a0px[0] - a0t[0] * unitPx : 0;
  const matrix = `matrix(${unitPx} 0 0 ${-unitPx} ${ex} ${data.baseline_y_crop})`;
  const scale = height / cropH;
  return (
    <svg width={cropW * scale} height={height} viewBox={`0 0 ${cropW} ${cropH}`} style={{ display: 'block', background: '#fff', maxWidth: '100%' }}>
      <image href={cropUrl(sourceId, glyphKey, cropCacheBust)} x={0} y={0} width={cropW} height={cropH} preserveAspectRatio="none" />
      {canMap && (
        <g transform={matrix}>
          {(data.outline_paths ?? []).map((rings, i) => (
            <path key={i} d={ringsToPathD(rings)} fill="#e02030" fillOpacity={0.42} fillRule="evenodd" />
          ))}
        </g>
      )}
    </svg>
  );
}

function CompareCard({
  glyphKey,
  letterGlyph,
  caption,
  sourceId,
  cropCacheBust,
  reloadKey,
  overlay,
}: {
  glyphKey: string;
  letterGlyph: string;
  caption: string;
  sourceId: string;
  cropCacheBust: number;
  reloadKey: number;
  overlay: boolean;
}) {
  const [data, setData] = useState<DiagnosticData | null>(null);
  // notFound = no canonical traced yet (typed ApiError 404); anything else is a
  // real load error. Branching on the typed status avoids parsing String(e).
  const [error, setError] = useState<{ notFound: boolean } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    getDiagnostic(sourceId, glyphKey)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError({ notFound: e instanceof ApiError && e.status === 404 });
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, glyphKey, cropCacheBust, reloadKey]);

  const cropDisplay = useMemo(() => {
    if (!data) return null;
    const scale = FACE_H / data.crop_size.h;
    return { w: data.crop_size.w * scale, h: FACE_H };
  }, [data]);

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper', display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
        <Typography sx={{ fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 28, lineHeight: 1 }}>{letterGlyph}</Typography>
        <Typography variant="caption" color="text.secondary">
          {glyphKey}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ ml: 'auto' }}>
          {caption}
        </Typography>
      </Box>

      {error ? (
        <Alert severity={error.notFound ? 'info' : 'error'} sx={{ py: 0 }}>
          {error.notFound ? de.admin.compare.noCanonical : de.admin.compare.loadError}
        </Alert>
      ) : !data ? (
        <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <CircularProgress size={24} />
        </Box>
      ) : overlay ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {de.admin.compare.overlayHeading}
          </Typography>
          <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}>
            <CropWrittenOverlay data={data} sourceId={sourceId} glyphKey={glyphKey} cropCacheBust={cropCacheBust} height={FACE_H} />
          </Box>
        </Box>
      ) : (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <Face heading={de.admin.compare.colCrop}>
            {cropDisplay && (
              <img
                src={cropUrl(sourceId, glyphKey, cropCacheBust)}
                alt={`${glyphKey} crop`}
                width={cropDisplay.w}
                height={cropDisplay.h}
                style={{ display: 'block', maxWidth: '100%', objectFit: 'contain' }}
              />
            )}
          </Face>
          <Face heading={de.admin.compare.colWritten}>
            {/* Pass the already-fetched payload so WrittenGlyph renders the
                admin's active source without a second fetch. Keyed by reload so
                the write-in animation restarts on "Neu laden". */}
            <WrittenGlyph key={reloadKey} glyphKey={glyphKey} data={data} height={FACE_H} tight maxWidth={9999} />
          </Face>
        </Box>
      )}
    </Box>
  );
}

export function GlyphComparison() {
  const { source, sourceId, glyphsByKey, bboxesByKey, cropCacheBust } = useAdmin();
  const [reloadKey, setReloadKey] = useState(0);
  const [overlay, setOverlay] = useState(false);
  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  const tiles = useMemo(() => buildTiles(glyphsByKey, bboxesByKey), [glyphsByKey, bboxesByKey]);

  if (!source) return null;

  return (
    <Box sx={{ overflowY: 'auto', height: '100%', p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        <Box sx={{ flex: 1, minWidth: 260 }}>
          <Typography variant="h6">{de.admin.compare.title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
            {de.admin.compare.intro}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
            label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
          />
          <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={reload}>
            {de.admin.compare.reload}
          </Button>
        </Box>
      </Box>

      {tiles.length === 0 ? (
        <Alert severity="info">{de.admin.compare.empty}</Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1100 }}>
          {tiles.map((t) => (
            <CompareCard
              key={t.key}
              glyphKey={t.key}
              letterGlyph={t.letterGlyph}
              caption={t.caption}
              sourceId={sourceId}
              cropCacheBust={cropCacheBust}
              reloadKey={reloadKey}
              overlay={overlay}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
