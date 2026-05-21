// EditorPage — full-viewport editing of one glyph.
//
// Left half: large bbox crop with baseline (red) and midband (purple)
// drag handles and a stylus capture overlay. Right half: calibration
// fields, n_anchors selector, exclude list, save/cancel buttons, info.
//
// The crop is auto-scaled to fit the viewport. Calibration handles
// drag via PointerEvent in CHART-pixel space (mapped back from CSS
// coords through the scale factor). Stylus input is filtered to
// pointerType === 'pen' or 'mouse' (touch is ignored so the user's
// palm doesn't draw).

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ClearIcon from '@mui/icons-material/Clear';
import CreateIcon from '@mui/icons-material/Create';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import UndoIcon from '@mui/icons-material/Undo';
import {
  Alert,
  Box,
  Button,
  Divider,
  IconButton,
  Paper,
  Snackbar,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { cropUrl, postResample, postTrace, putBbox } from '../api';
import { useAdmin } from '../state';
import type { GlyphBbox, StrokePoint } from '../types';

type Mode = 'view' | 'trace';
type CalibField = 'baseline_y' | 'midband_y';

// Calibration row: numeric input plus ↑/↓ icon buttons that move the line
// in the VISUAL direction the user expects. Because chart-y increases
// downward in pixel coordinates, "up" needs to DECREASE the stored value;
// the bare number-input spinner does the opposite, which is the source of
// the bug report "klick hoch → linie geht runter".
function CalibrationRow({
  label,
  value,
  color,
  onSet,
}: {
  label: string;
  value: number | null | undefined;
  color: string;
  onSet: (v: number | null) => void;
}) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <TextField
        label={label}
        type="number"
        size="small"
        value={value ?? ''}
        onChange={(e) => onSet(e.target.value === '' ? null : Number(e.target.value))}
        slotProps={{ input: { sx: { color, fontFamily: 'monospace' } } }}
        sx={{ flex: 1 }}
      />
      <Tooltip title="Linie 1 Pixel nach oben">
        <span>
          <IconButton
            size="small"
            disabled={value == null}
            onClick={() => onSet((value ?? 0) - 1)}
            sx={{ color }}
          >
            <ArrowUpwardIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title="Linie 1 Pixel nach unten">
        <span>
          <IconButton
            size="small"
            disabled={value == null}
            onClick={() => onSet((value ?? 0) + 1)}
            sx={{ color }}
          >
            <ArrowDownwardIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}

interface CalibDragState {
  field: CalibField;
  curY: number;
}

export function EditorPage() {
  const { glyphKey: raw } = useParams();
  const glyphKey = raw ? decodeURIComponent(raw) : null;
  const navigate = useNavigate();
  const { bboxes, cropCacheBust, canonStatus, updateBbox, markCanonical, setActiveGlyph } = useAdmin();
  const bbox: GlyphBbox | null = glyphKey && bboxes ? (bboxes.bboxes[glyphKey] ?? null) : null;
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [hostSize, setHostSize] = useState({ w: 0, h: 0 });
  const [mode, setMode] = useState<Mode>('view');
  const [pathPts, setPathPts] = useState<StrokePoint[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [calibDrag, setCalibDrag] = useState<CalibDragState | null>(null);
  const [snack, setSnack] = useState<{ kind: 'info' | 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (glyphKey) setActiveGlyph(glyphKey);
  }, [glyphKey, setActiveGlyph]);

  // Reset state when glyph changes.
  useEffect(() => {
    setMode('view');
    setPathPts([]);
    setDrawing(false);
    setCalibDrag(null);
  }, [glyphKey]);

  // Track host size for auto-scale.
  useLayoutEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setHostSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    setHostSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const cropW = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropH = bbox ? bbox.y1 - bbox.y0 : 0;
  const scale = useMemo(() => {
    if (!cropW || !cropH || !hostSize.w || !hostSize.h) return 1;
    const padding = 32;
    const fitW = (hostSize.w - padding) / cropW;
    const fitH = (hostSize.h - padding) / cropH;
    return Math.max(0.5, Math.min(fitW, fitH));
  }, [cropW, cropH, hostSize]);
  const displayW = cropW * scale;
  const displayH = cropH * scale;

  const cssToChartY = useCallback(
    (clientY: number, host: Element | null) => {
      if (!host || !bbox) return 0;
      const r = host.getBoundingClientRect();
      return Math.round(bbox.y0 + (clientY - r.top) / scale);
    },
    [bbox, scale],
  );

  const cssToChartXY = useCallback(
    (clientX: number, clientY: number, host: Element | null) => {
      if (!host || !bbox) return { x: 0, y: 0 };
      const r = host.getBoundingClientRect();
      return {
        x: bbox.x0 + (clientX - r.left) / scale,
        y: bbox.y0 + (clientY - r.top) / scale,
      };
    },
    [bbox, scale],
  );

  // ---- Calibration handle drag ----
  // Capture the pointer on the SVG itself (not the handle rect), so subsequent
  // pointermove events fire reliably on the SVG even if the pointer leaves
  // the handle's tiny bounding box during a slow drag on a tablet.
  const startCalibDrag = useCallback(
    (field: CalibField) => (e: React.PointerEvent<SVGElement>) => {
      e.stopPropagation();
      e.preventDefault();
      const svg = e.currentTarget.ownerSVGElement;
      if (!svg) return;
      const y = cssToChartY(e.clientY, svg);
      setCalibDrag({ field, curY: y });
      svg.setPointerCapture(e.pointerId);
    },
    [cssToChartY],
  );

  const onCalibMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!calibDrag) return;
      const y = cssToChartY(e.clientY, e.currentTarget);
      setCalibDrag({ ...calibDrag, curY: y });
    },
    [calibDrag, cssToChartY],
  );

  const onCalibUp = useCallback(async () => {
    if (!calibDrag || !glyphKey || !bbox) {
      setCalibDrag(null);
      return;
    }
    const next: GlyphBbox = { ...bbox, [calibDrag.field]: calibDrag.curY };
    setCalibDrag(null);
    try {
      const saved = await putBbox(glyphKey, next);
      updateBbox(glyphKey, saved);
    } catch (err) {
      setSnack({ kind: 'error', text: `Kalibrierung speichern fehlgeschlagen: ${err}` });
    }
  }, [calibDrag, glyphKey, bbox, updateBbox]);

  // ---- Stylus drawing ----
  const onStylusDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (mode !== 'trace') return;
      if (e.pointerType !== 'pen' && e.pointerType !== 'mouse') return;
      e.preventDefault();
      const { x, y } = cssToChartXY(e.clientX, e.clientY, e.currentTarget);
      setDrawing(true);
      setPathPts([{ x, y, pressure: e.pressure || null, t: 0 }]);
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [mode, cssToChartXY],
  );

  const onStylusMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (calibDrag) return onCalibMove(e);
      if (!drawing) return;
      const { x, y } = cssToChartXY(e.clientX, e.clientY, e.currentTarget);
      setPathPts((prev) => {
        const last = prev[prev.length - 1];
        if (last) {
          const dx = x - last.x;
          const dy = y - last.y;
          if (dx * dx + dy * dy < 0.36) return prev;
        }
        return [...prev, { x, y, pressure: e.pressure || null, t: performance.now() }];
      });
    },
    [calibDrag, drawing, cssToChartXY, onCalibMove],
  );

  const onStylusUp = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (calibDrag) return onCalibUp();
      setDrawing(false);
      e.preventDefault();
    },
    [calibDrag, onCalibUp],
  );

  const saveTrace = useCallback(async () => {
    if (!glyphKey || pathPts.length < 2) return;
    setSnack({ kind: 'info', text: 'speichere Canonical…' });
    try {
      const canon = await postTrace(glyphKey, { path: pathPts });
      markCanonical(glyphKey, canon);
      setSnack({ kind: 'success', text: `gespeichert · ${canon.strokes[0].anchors.length} Anker · ${pathPts.length} Pen-Punkte` });
      setPathPts([]);
      setMode('view');
    } catch (err) {
      setSnack({ kind: 'error', text: String(err) });
    }
  }, [glyphKey, pathPts, markCanonical]);

  const updateField = useCallback(
    async (patch: Partial<GlyphBbox>) => {
      if (!glyphKey || !bbox) return;
      const next: GlyphBbox = { ...bbox, ...patch };
      try {
        const saved = await putBbox(glyphKey, next);
        updateBbox(glyphKey, saved);
      } catch (err) {
        setSnack({ kind: 'error', text: `Speichern fehlgeschlagen: ${err}` });
      }
    },
    [glyphKey, bbox, updateBbox],
  );

  if (!glyphKey) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>Kein Glyph ausgewählt.</Typography>
      </Box>
    );
  }
  if (!bbox) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>{glyphKey}</Typography>
        <Typography color="text.secondary">
          Noch keine Bbox — zurück zur Übersicht, Modus „Bbox" wählen, diesen Glyph aktivieren und ein Rechteck ziehen.
        </Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Zurück zur Übersicht
        </Button>
      </Box>
    );
  }

  // Calibration line CSS positions.
  // Ascender and descender are derived from the Loth 2:1:2 ratio
  // (ascender region and descender region each span twice the x-height).
  // They're shown as light guide lines so the user can verify the bbox
  // covers the full letter — if the actual ink reaches further than the
  // guide, baseline/midband calibration is probably off.
  const baselineCss = bbox.baseline_y != null ? (bbox.baseline_y - bbox.y0) * scale : null;
  const midbandCss = bbox.midband_y != null ? (bbox.midband_y - bbox.y0) * scale : null;
  const dragCss = calibDrag ? (calibDrag.curY - bbox.y0) * scale : null;
  const xHeightPx = bbox.baseline_y != null && bbox.midband_y != null ? bbox.baseline_y - bbox.midband_y : null;
  const ascenderY = xHeightPx != null && bbox.midband_y != null ? bbox.midband_y - 2 * xHeightPx : null;
  const descenderY = xHeightPx != null && bbox.baseline_y != null ? bbox.baseline_y + 2 * xHeightPx : null;
  const ascenderCss = ascenderY != null ? (ascenderY - bbox.y0) * scale : null;
  const descenderCss = descenderY != null ? (descenderY - bbox.y0) * scale : null;

  return (
    <>
      <Paper square sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderBottom: 1, borderColor: 'divider' }}>
        <IconButton size="small" onClick={() => navigate('/')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6" sx={{ fontFamily: 'ui-monospace, Menlo, monospace' }}>{glyphKey}</Typography>
        <Box sx={{ flex: 1 }} />
        <ToggleButtonGroup
          size="small"
          value={mode}
          exclusive
          onChange={(_e, v: Mode | null) => v && setMode(v)}
        >
          <ToggleButton value="view">Ansicht</ToggleButton>
          <ToggleButton value="trace"><CreateIcon fontSize="small" />&nbsp;Strich zeichnen</ToggleButton>
        </ToggleButtonGroup>
      </Paper>

      <Box sx={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 320px', overflow: 'hidden' }}>
        {/* Crop pane */}
        <Box
          ref={hostRef}
          sx={{
            position: 'relative',
            bgcolor: '#0a0a0a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            p: 2,
          }}
        >
          {displayW > 0 && (
            <Box sx={{ position: 'relative', width: displayW, height: displayH, boxShadow: 4 }}>
              <img
                src={cropUrl(glyphKey, cropCacheBust)}
                alt={glyphKey}
                width={displayW}
                height={displayH}
                draggable={false}
                style={{ display: 'block', background: '#fff', userSelect: 'none' }}
              />
              <svg
                width={displayW}
                height={displayH}
                viewBox={`0 0 ${displayW} ${displayH}`}
                onPointerDown={onStylusDown}
                onPointerMove={onStylusMove}
                onPointerUp={onStylusUp}
                onPointerCancel={() => { setDrawing(false); setCalibDrag(null); }}
                style={{ position: 'absolute', inset: 0, touchAction: 'none' }}
              >
                {/* ascender — derived from 2:1:2 ratio, read-only guide */}
                {ascenderCss != null && ascenderCss >= 0 && ascenderCss <= displayH && (
                  <g style={{ pointerEvents: 'none' }}>
                    <line
                      x1={0}
                      y1={ascenderCss}
                      x2={displayW}
                      y2={ascenderCss}
                      stroke="#888"
                      strokeWidth={1}
                      strokeDasharray="2 4"
                      opacity={0.6}
                    />
                    <text x={displayW - 90} y={ascenderCss - 3} fontSize={10} fill="#888" opacity={0.8}>
                      ascender (2:1:2)
                    </text>
                  </g>
                )}
                {/* descender — derived from 2:1:2 ratio, read-only guide */}
                {descenderCss != null && descenderCss >= 0 && descenderCss <= displayH && (
                  <g style={{ pointerEvents: 'none' }}>
                    <line
                      x1={0}
                      y1={descenderCss}
                      x2={displayW}
                      y2={descenderCss}
                      stroke="#888"
                      strokeWidth={1}
                      strokeDasharray="2 4"
                      opacity={0.6}
                    />
                    <text x={displayW - 100} y={descenderCss - 3} fontSize={10} fill="#888" opacity={0.8}>
                      descender (2:1:2)
                    </text>
                  </g>
                )}
                {/* baseline */}
                {baselineCss != null && (
                  <g>
                    <line
                      x1={0}
                      y1={baselineCss}
                      x2={displayW}
                      y2={baselineCss}
                      stroke="#ff5060"
                      strokeWidth={1.5}
                      strokeDasharray="6 4"
                      style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                      onPointerDown={startCalibDrag('baseline_y')}
                    />
                    <rect
                      x={4}
                      y={baselineCss - 9}
                      width={86}
                      height={16}
                      fill="#ff5060"
                      style={{ cursor: 'ns-resize' }}
                      onPointerDown={startCalibDrag('baseline_y')}
                    />
                    <text x={8} y={baselineCss + 3} fontSize={11} fill="#1a0000" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                      baseline {bbox.baseline_y}
                    </text>
                  </g>
                )}
                {/* midband */}
                {midbandCss != null && (
                  <g>
                    <line
                      x1={0}
                      y1={midbandCss}
                      x2={displayW}
                      y2={midbandCss}
                      stroke="#c060ff"
                      strokeWidth={1.5}
                      strokeDasharray="3 3"
                      style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                      onPointerDown={startCalibDrag('midband_y')}
                    />
                    <rect
                      x={4}
                      y={midbandCss - 9}
                      width={86}
                      height={16}
                      fill="#c060ff"
                      style={{ cursor: 'ns-resize' }}
                      onPointerDown={startCalibDrag('midband_y')}
                    />
                    <text x={8} y={midbandCss + 3} fontSize={11} fill="#1a001a" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                      midband {bbox.midband_y}
                    </text>
                  </g>
                )}
                {/* drag-in-progress ghost */}
                {dragCss != null && calibDrag && (
                  <line
                    x1={0}
                    y1={dragCss}
                    x2={displayW}
                    y2={dragCss}
                    stroke={calibDrag.field === 'baseline_y' ? '#ff5060' : '#c060ff'}
                    strokeWidth={2}
                    opacity={0.6}
                  />
                )}
                {/* stylus stroke */}
                {pathPts.length > 1 && (
                  <polyline
                    fill="none"
                    stroke="#00d2ff"
                    strokeWidth={2}
                    points={pathPts.map((p) => `${(p.x - bbox.x0) * scale},${(p.y - bbox.y0) * scale}`).join(' ')}
                  />
                )}
              </svg>
            </Box>
          )}
        </Box>

        {/* Right panel: controls */}
        <Box sx={{ borderLeft: 1, borderColor: 'divider', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          <Stack spacing={2} sx={{ p: 2 }}>
            <Box>
              <Typography variant="overline" color="text.secondary">Kalibrierung</Typography>
              <Stack spacing={1.5} sx={{ mt: 1 }}>
                <CalibrationRow
                  label="baseline_y"
                  value={bbox.baseline_y}
                  color="#ff5060"
                  onSet={(v) => updateField({ baseline_y: v })}
                />
                <CalibrationRow
                  label="midband_y"
                  value={bbox.midband_y}
                  color="#c060ff"
                  onSet={(v) => updateField({ midband_y: v })}
                />
                <Typography variant="caption" color="text.secondary">
                  x-Höhe = {bbox.baseline_y != null && bbox.midband_y != null ? bbox.baseline_y - bbox.midband_y : '—'} px
                </Typography>
              </Stack>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">Resampling</Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: 'center' }}>
                <TextField
                  label="n_anchors (Standard 14)"
                  type="number"
                  size="small"
                  value={bbox.n_anchors ?? ''}
                  placeholder="14"
                  onChange={(e) => updateField({ n_anchors: e.target.value === '' ? null : Number(e.target.value) })}
                  sx={{ flex: 1 }}
                />
                <Tooltip title="Bestehenden Strich mit der neuen Anker-Anzahl neu abtasten (kein neues Zeichnen nötig)">
                  <span>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      disabled={!canonStatus[glyphKey]}
                      onClick={async () => {
                        try {
                          const canon = await postResample(glyphKey, bbox.n_anchors ?? 14);
                          markCanonical(glyphKey, canon);
                          setSnack({ kind: 'success', text: `neu abgetastet · ${canon.strokes[0].anchors.length} Anker` });
                        } catch (err) {
                          setSnack({ kind: 'error', text: String(err) });
                        }
                      }}
                    >
                      Neu abtasten
                    </Button>
                  </span>
                </Tooltip>
              </Stack>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                Der ursprüngliche Pen-Pfad ist im Canonical gespeichert (`_trace.raw_path`); du kannst n_anchors beliebig oft anpassen.
              </Typography>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">Ausschluss-Rechtecke ({bbox.exclude.length})</Typography>
              <Stack spacing={0.5} sx={{ mt: 1, maxHeight: 120, overflowY: 'auto' }}>
                {bbox.exclude.map((ex, i) => (
                  <Paper key={i} variant="outlined" sx={{ p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                      ({ex.x0},{ex.y0})→({ex.x1},{ex.y1})
                    </Typography>
                    <Tooltip title="diesen Ausschluss entfernen">
                      <IconButton
                        size="small"
                        onClick={() => updateField({ exclude: bbox.exclude.filter((_, j) => j !== i) })}
                      >
                        <ClearIcon fontSize="inherit" />
                      </IconButton>
                    </Tooltip>
                  </Paper>
                ))}
                {bbox.exclude.length === 0 && (
                  <Typography variant="caption" color="text.disabled">keine</Typography>
                )}
              </Stack>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">Strich</Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Tooltip title="letzten Pen-Punkt rückgängig">
                  <span>
                    <IconButton size="small" disabled={pathPts.length === 0} onClick={() => setPathPts((p) => p.slice(0, -1))}>
                      <UndoIcon />
                    </IconButton>
                  </span>
                </Tooltip>
                <Button
                  size="small"
                  variant="outlined"
                  color="warning"
                  startIcon={<ClearIcon />}
                  disabled={pathPts.length === 0}
                  onClick={() => setPathPts([])}
                >
                  Verwerfen
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={pathPts.length < 2}
                  onClick={saveTrace}
                >
                  Canonical speichern
                </Button>
              </Stack>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                {pathPts.length} Pen-Punkte aufgenommen · schalte oben auf „Strich zeichnen" und ziehe dann mit dem S-Pen über den Buchstaben.
              </Typography>
            </Box>
          </Stack>
        </Box>
      </Box>

      <Snackbar
        open={snack !== null}
        autoHideDuration={3000}
        onClose={() => setSnack(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snack?.kind ?? 'info'} onClose={() => setSnack(null)} variant="filled">
          {snack?.text}
        </Alert>
      </Snackbar>
    </>
  );
}
