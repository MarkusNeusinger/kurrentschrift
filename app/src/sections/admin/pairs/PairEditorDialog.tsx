// Pair editor (redesign R3) — the human review/approval surface over the
// glyph_pairs override layer. Shows the two letters at an adjustable offset
// (the right glyph's entry relative to the left glyph's exit, template
// units), lets the admin DRAW the connector with the pointer, and saves the
// override via PUT /pairs — freehand saves are marked `authored`; approving
// an untouched harvested row keeps its provenance + specimen reference. A
// live panel shows what /write/word now actually renders (cache-busted).

import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Slider,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { ApiError, deletePair, getPair, getWriteWord, putPair, wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, GlyphPairOut, GlyphRenderData, WordSampleOut } from '@/lib/api';
import { fetchRenderGlyphs } from '@/lib/api/renderCache';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';

type Pt = [number, number];

const DEFAULT_OFFSET_DX = 0.3; // xh — a sensible starting gap for a fresh pair

interface Props {
  open: boolean;
  onClose: () => void;
  // The letter pair as typed text (cell label) and as shaped glyph_keys.
  pairText: string;
  leftKey: string;
  rightKey: string;
  sourceId: string;
  // Called after a successful save/delete so the matrix can refresh its badges.
  onChanged?: () => void;
  // Optional connected-writing specimen (an Abb.-20 pair sample) rendered as a
  // registered underlay in the editing scene — the redesign's circle back from
  // a bad pair card to the editor, drawing over the real pen's path.
  specimen?: WordSampleOut;
}

function exitOf(data: GlyphRenderData): Pt {
  const xy = data.exit_pt?.xy;
  if (xy) return [xy[0], xy[1]];
  const lines = data.centerlines_template ?? [];
  const last = lines[lines.length - 1];
  return last && last.length ? (last[last.length - 1] as Pt) : [0, 0];
}

function entryOf(data: GlyphRenderData): Pt {
  const xy = data.entry?.xy;
  if (xy) return [xy[0], xy[1]];
  const first = (data.centerlines_template ?? [])[0];
  return first && first.length ? (first[0] as Pt) : [0, 0];
}

// Static mini-renderer for the live /write/word result (no reveal animation).
function ComposedPreview({ composed }: { composed: ComposedWordOut }) {
  const b = composed.bounds;
  const pad = 0.2;
  const w = b.max_x - b.min_x + 2 * pad;
  const h = b.max_y - b.min_y + 2 * pad;
  return (
    <svg
      viewBox={`${b.min_x - pad} ${-b.max_y - pad} ${w} ${h}`}
      style={{ height: 110, display: 'block', background: '#fff', maxWidth: '100%' }}
    >
      <g transform="scale(1,-1)">
        <line x1={b.min_x} x2={b.max_x} y1={0} y2={0} stroke="#b9c4c0" strokeWidth={0.015} />
        <line x1={b.min_x} x2={b.max_x} y1={1} y2={1} stroke="#b9c4c0" strokeWidth={0.015} strokeDasharray="0.05" />
        {composed.items.map((it, i) =>
          it.rings ? (
            <path key={i} d={ringsToPathD(it.rings)} fill="#20302c" fillRule="evenodd" />
          ) : (
            <path
              key={i}
              d={polylineToPathD(it.centerline)}
              fill="none"
              stroke="#20302c"
              strokeWidth={it.stroke_width ?? it.mask_width}
              strokeLinecap="round"
            />
          ),
        )}
      </g>
    </svg>
  );
}

export function PairEditorDialog({ open, onClose, pairText, leftKey, rightKey, sourceId, onChanged, specimen }: Props) {
  const [left, setLeft] = useState<GlyphRenderData | null>(null);
  const [right, setRight] = useState<GlyphRenderData | null>(null);
  const [row, setRow] = useState<GlyphPairOut | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [offsetDx, setOffsetDx] = useState(DEFAULT_OFFSET_DX);
  const [connector, setConnector] = useState<Pt[]>([]); // relative to the left exit
  const [approved, setApproved] = useState(false);
  const [geometryDirty, setGeometryDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const [preview, setPreview] = useState<ComposedWordOut | null>(null);
  const bustRef = useRef(1);

  const loadPreview = useCallback(() => {
    getWriteWord(sourceId, pairText, { retries: 1 }, bustRef.current++)
      .then(setPreview)
      .catch(() => setPreview(null));
  }, [sourceId, pairText]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoaded(false);
    setError(null);
    setRow(null);
    setPreview(null);
    Promise.all([
      fetchRenderGlyphs(sourceId, [leftKey, rightKey]),
      getPair(sourceId, leftKey, rightKey).catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      }),
    ])
      .then(([glyphs, pair]) => {
        if (cancelled) return;
        setLeft(glyphs.get(leftKey) ?? null);
        setRight(glyphs.get(rightKey) ?? null);
        setRow(pair);
        setOffsetDx(pair ? (pair.geometry.offset[0] ?? DEFAULT_OFFSET_DX) : DEFAULT_OFFSET_DX);
        setConnector(pair ? pair.geometry.connector.map((p) => [p[0], p[1]] as Pt) : []);
        setApproved(pair?.approved ?? false);
        setGeometryDirty(false);
        setLoaded(true);
        loadPreview();
      })
      .catch(() => {
        if (!cancelled) setError(de.admin.pairs.editorLoadError);
      });
    return () => {
      cancelled = true;
    };
  }, [open, sourceId, leftKey, rightKey, loadPreview]);

  const leftExit = useMemo(() => (left ? exitOf(left) : ([0, 0] as Pt)), [left]);
  const rightEntry = useMemo(() => (right ? entryOf(right) : ([0, 0] as Pt)), [right]);
  // Translate the right glyph so its entry lands at leftExit + offset.
  const rightDx = leftExit[0] + offsetDx - rightEntry[0];

  const [showSpecimen, setShowSpecimen] = useState(true);

  // Specimen underlay in template coords: scale from the crop-local lineature
  // (baseline_y − midband_y px per x-height unit), baseline on y = 0, left
  // edge aligned to the left glyph's ink left edge (specimen boxes are tight —
  // an approximate registration meant as tracing paper, not as a metric).
  const underlay = useMemo(() => {
    if (!specimen) return null;
    const unitPx = specimen.baseline_y - specimen.midband_y;
    if (unitPx <= 0) return null;
    const xs = (left?.centerlines_template ?? []).flatMap((line) => line.map(([x]) => x));
    return {
      x: xs.length ? Math.min(...xs) : 0,
      topY: specimen.baseline_y / unitPx, // template y of crop row 0
      w: specimen.width / unitPx,
      h: specimen.height / unitPx,
    };
  }, [specimen, left]);

  // Editing scene bounds (template units), padded.
  const scene = useMemo(() => {
    const xs: number[] = [];
    const ys: number[] = [];
    const eat = (data: GlyphRenderData | null, dx: number) => {
      for (const line of data?.centerlines_template ?? [])
        for (const [x, y] of line) {
          xs.push(x + dx);
          ys.push(y);
        }
    };
    eat(left, 0);
    eat(right, rightDx);
    if (underlay) {
      xs.push(underlay.x, underlay.x + underlay.w);
      ys.push(underlay.topY - underlay.h, underlay.topY);
    }
    if (!xs.length) return { minX: -0.2, maxX: 2, minY: -1.2, maxY: 2.2 };
    const pad = 0.35;
    return {
      minX: Math.min(...xs) - pad,
      maxX: Math.max(...xs) + pad,
      minY: Math.min(...ys, -0.2) - pad,
      maxY: Math.max(...ys, 1.2) + pad,
    };
  }, [left, right, rightDx, underlay]);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const drawingRef = useRef(false);

  const toTemplate = useCallback(
    (clientX: number, clientY: number): Pt | null => {
      const svg = svgRef.current;
      if (!svg) return null;
      const rect = svg.getBoundingClientRect();
      const x = scene.minX + ((clientX - rect.left) / rect.width) * (scene.maxX - scene.minX);
      // The viewBox is y-flipped (template y grows up).
      const y = scene.maxY - ((clientY - rect.top) / rect.height) * (scene.maxY - scene.minY);
      return [x, y];
    },
    [scene],
  );

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    const p = toTemplate(e.clientX, e.clientY);
    if (!p) return;
    drawingRef.current = true;
    (e.target as Element).setPointerCapture?.(e.pointerId);
    setConnector([[p[0] - leftExit[0], p[1] - leftExit[1]]]);
    setGeometryDirty(true);
  };
  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!drawingRef.current) return;
    const p = toTemplate(e.clientX, e.clientY);
    if (!p) return;
    setConnector((prev) => {
      const rel: Pt = [p[0] - leftExit[0], p[1] - leftExit[1]];
      const last = prev[prev.length - 1];
      if (last && Math.hypot(rel[0] - last[0], rel[1] - last[1]) < 0.02) return prev;
      return [...prev, rel];
    });
  };
  const onPointerUp = () => {
    drawingRef.current = false;
  };

  const canSave = loaded && connector.length >= 2 && !saving;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      // An untouched harvested row keeps its provenance + specimen citation
      // (approving is not re-authoring); any redrawn geometry is authored.
      const keepHarvest = row?.provenance === 'harvested' && !geometryDirty;
      const saved = await putPair(sourceId, leftKey, rightKey, {
        geometry: {
          offset: [Math.round(offsetDx * 10000) / 10000, 0],
          connector: connector.map(([x, y]) => [Math.round(x * 10000) / 10000, Math.round(y * 10000) / 10000]),
        },
        provenance: keepHarvest ? 'harvested' : 'authored',
        specimen_id: keepHarvest ? row?.specimen_id : null,
        approved,
      });
      setRow(saved);
      setGeometryDirty(false);
      loadPreview();
      onChanged?.();
    } catch {
      setError(de.admin.pairs.saveFailed);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setSaving(true);
    setError(null);
    try {
      await deletePair(sourceId, leftKey, rightKey);
      setRow(null);
      setConnector([]);
      setApproved(false);
      setGeometryDirty(false);
      loadPreview();
      onChanged?.();
    } catch {
      setError(de.admin.pairs.deleteFailed);
    } finally {
      setSaving(false);
    }
  };

  const sceneW = scene.maxX - scene.minX;
  const sceneH = scene.maxY - scene.minY;

  const paintGlyph = (data: GlyphRenderData | null, dx: number, keyPrefix: string) =>
    (data?.outline_paths ?? []).map((rings, i) => (
      <path
        key={`${keyPrefix}${i}`}
        d={ringsToPathD(rings)}
        fill="#20302c"
        fillOpacity={0.85}
        fillRule="evenodd"
        transform={`translate(${dx} 0)`}
      />
    ));

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{fmt(de.admin.pairs.editorTitle, { pair: pairText })}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {de.admin.pairs.editorIntro}
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <Box sx={{ flex: '1 1 420px', minWidth: 320 }}>
            <svg
              ref={svgRef}
              viewBox={`${scene.minX} ${-scene.maxY} ${sceneW} ${sceneH}`}
              style={{ width: '100%', background: '#fff', borderRadius: 6, touchAction: 'none', cursor: 'crosshair' }}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerLeave={onPointerUp}
            >
              {/* Specimen underlay in root coords (SVG y-down): crop row r sits
                  at template y = (baseline_y − r)/unitPx, i.e. root y = −topY
                  at the top edge, growing downward with the crop rows. */}
              {underlay && specimen && showSpecimen && (
                <image
                  href={wordSampleCropUrl(sourceId, specimen.id)}
                  x={underlay.x}
                  y={-underlay.topY}
                  width={underlay.w}
                  height={underlay.h}
                  opacity={0.35}
                  preserveAspectRatio="none"
                />
              )}
              <g transform="scale(1,-1)">
                <line x1={scene.minX} x2={scene.maxX} y1={0} y2={0} stroke="#b9c4c0" strokeWidth={0.015} />
                <line
                  x1={scene.minX}
                  x2={scene.maxX}
                  y1={1}
                  y2={1}
                  stroke="#b9c4c0"
                  strokeWidth={0.015}
                  strokeDasharray="0.05"
                />
                {paintGlyph(left, 0, 'l')}
                {paintGlyph(right, rightDx, 'r')}
                {/* exit/entry markers */}
                <circle cx={leftExit[0]} cy={leftExit[1]} r={0.035} fill="#1f8a5a" />
                <circle cx={rightEntry[0] + rightDx} cy={rightEntry[1]} r={0.035} fill="#8a1f3a" />
                {connector.length >= 2 && (
                  <path
                    d={polylineToPathD(connector.map(([x, y]) => [x + leftExit[0], y + leftExit[1]] as Pt))}
                    fill="none"
                    stroke="#c23a4b"
                    strokeWidth={0.05}
                    strokeLinecap="round"
                    strokeOpacity={0.85}
                  />
                )}
              </g>
            </svg>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
              <Typography variant="caption" sx={{ whiteSpace: 'nowrap' }}>
                {de.admin.pairs.offsetLabel}
              </Typography>
              <Slider
                size="small"
                min={-0.6}
                max={1.6}
                step={0.01}
                value={offsetDx}
                onChange={(_, v) => {
                  setOffsetDx(v as number);
                  setGeometryDirty(true);
                }}
              />
              <Typography variant="caption" sx={{ width: 48, textAlign: 'right' }}>
                {offsetDx.toFixed(2)}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
              <Button size="small" onClick={() => setConnector([])} disabled={!connector.length}>
                {de.admin.pairs.clearConnector}
              </Button>
              {underlay && (
                <FormControlLabel
                  sx={{ mr: 0 }}
                  control={
                    <Checkbox size="small" checked={showSpecimen} onChange={(e) => setShowSpecimen(e.target.checked)} />
                  }
                  label={<Typography variant="caption">{de.admin.pairs.showSpecimen}</Typography>}
                />
              )}
              <Typography variant="caption" color="text.secondary">
                {row
                  ? fmt(de.admin.pairs.rowState, {
                      provenance: row.provenance,
                      specimen: row.specimen_id ?? '—',
                    })
                  : de.admin.pairs.noRowYet}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ flex: '1 1 260px', minWidth: 240 }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.pairs.previewHeading}
            </Typography>
            <Box sx={{ bgcolor: '#fff', borderRadius: 1, p: 1, mt: 0.5 }}>
              {preview ? (
                <ComposedPreview composed={preview} />
              ) : (
                <Typography variant="caption" color="text.disabled">
                  …
                </Typography>
              )}
            </Box>
            <FormControlLabel
              sx={{ mt: 1 }}
              control={<Checkbox size="small" checked={approved} onChange={(e) => setApproved(e.target.checked)} />}
              label={<Typography variant="body2">{de.admin.pairs.approveLabel}</Typography>}
            />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {de.admin.pairs.approveHint}
            </Typography>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        {row && (
          <Button color="error" onClick={remove} disabled={saving}>
            {de.admin.pairs.deleteOverride}
          </Button>
        )}
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>{de.admin.pairs.close}</Button>
        <Button variant="contained" onClick={save} disabled={!canSave}>
          {de.admin.pairs.save}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
