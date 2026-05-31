// EditorPage — full-viewport editing of one glyph.
//
// Left pane: large bbox crop with baseline (red) and midband (purple) drag
// handles and a stylus capture overlay. Right pane: calibration, n_anchors,
// excludes, save/cancel, and the 3-column DiagnosticView once a canonical
// exists in the DB.

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
import { DiagnosticView } from '../components/DiagnosticView';
import { FitView } from '../components/FitView';
import { knownGlyph } from '../constants';
import { useAdmin } from '../state';
import type { BboxIn, BboxOut, StrokePoint } from '../types';

type Mode = 'view' | 'trace';
type CalibField = 'baseline_y' | 'midband_y';

function bboxInFromOut(b: BboxOut): BboxIn {
  return {
    y0: b.y0,
    y1: b.y1,
    x0: b.x0,
    x1: b.x1,
    excludes: b.excludes,
    baseline_y: b.baseline_y,
    midband_y: b.midband_y,
    n_anchors: b.n_anchors,
  };
}

function CalibrationRow({
  label,
  value,
  color,
  onSet,
}: {
  label: string;
  value: number;
  color: string;
  onSet: (v: number) => void;
}) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <TextField
        label={label}
        type="number"
        size="small"
        value={value}
        onChange={(e) => onSet(Number(e.target.value))}
        slotProps={{ input: { sx: { color, fontFamily: 'monospace' } } }}
        sx={{ flex: 1 }}
      />
      <Tooltip title="Linie 1 Pixel nach oben">
        <IconButton size="small" onClick={() => onSet(value - 1)} sx={{ color }}>
          <ArrowUpwardIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Tooltip title="Linie 1 Pixel nach unten">
        <IconButton size="small" onClick={() => onSet(value + 1)} sx={{ color }}>
          <ArrowDownwardIcon fontSize="small" />
        </IconButton>
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
  const { source, bboxesByKey, glyphsByKey, cropCacheBust, upsertBbox, markGlyphTraced, setActiveGlyph } = useAdmin();
  const bbox = glyphKey ? (bboxesByKey[glyphKey] ?? null) : null;
  const known = glyphKey ? knownGlyph(glyphKey) : null;
  const hasCanonical = glyphKey ? glyphsByKey[glyphKey]?.has_data === true : false;
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

  useEffect(() => {
    setMode('view');
    setPathPts([]);
    setDrawing(false);
    setCalibDrag(null);
  }, [glyphKey]);

  useLayoutEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setHostSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setHostSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const cropW = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropH = bbox ? bbox.y1 - bbox.y0 : 0;
  const scale = useMemo(() => {
    if (!cropW || !cropH || !hostSize.w || !hostSize.h) return 1;
    const padding = 32;
    return Math.max(0.5, Math.min((hostSize.w - padding) / cropW, (hostSize.h - padding) / cropH));
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
      return { x: bbox.x0 + (clientX - r.left) / scale, y: bbox.y0 + (clientY - r.top) / scale };
    },
    [bbox, scale],
  );

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

  const updateBboxField = useCallback(
    async (patch: Partial<BboxIn>) => {
      if (!glyphKey || !bbox) return;
      const next: BboxIn = { ...bboxInFromOut(bbox), ...patch };
      try {
        const saved = await putBbox(glyphKey, next);
        upsertBbox(glyphKey, saved);
      } catch (err) {
        setSnack({ kind: 'error', text: `Speichern fehlgeschlagen: ${err}` });
      }
    },
    [glyphKey, bbox, upsertBbox],
  );

  const onCalibUp = useCallback(async () => {
    if (!calibDrag || !glyphKey || !bbox) {
      setCalibDrag(null);
      return;
    }
    const field = calibDrag.field;
    const value = calibDrag.curY;
    setCalibDrag(null);
    await updateBboxField({ [field]: value });
  }, [calibDrag, glyphKey, bbox, updateBboxField]);

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
    if (!glyphKey || pathPts.length < 2 || !known) return;
    setSnack({ kind: 'info', text: 'speichere Canonical…' });
    try {
      const g = await postTrace(glyphKey, {
        glyph: known.glyph,
        position: known.position,
        raw_path: pathPts,
        n_anchors: bbox?.n_anchors ?? null,
      });
      markGlyphTraced(glyphKey, {
        glyph_key: g.glyph_key,
        glyph: g.glyph,
        position: g.position,
        variant: g.variant,
        advance: g.advance,
        has_data: true,
      });
      setSnack({ kind: 'success', text: `gespeichert · ${g.anchors.length} Anker · ${pathPts.length} Pen-Punkte` });
      setPathPts([]);
      setMode('view');
    } catch (err) {
      setSnack({ kind: 'error', text: String(err) });
    }
  }, [glyphKey, pathPts, known, bbox, markGlyphTraced]);

  if (!glyphKey || !known) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>Kein gültiger Glyph ausgewählt.</Typography>
      </Box>
    );
  }
  if (!source) return null;
  if (!bbox) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          {known.label}
        </Typography>
        <Typography color="text.secondary">
          Noch keine Bbox — zurück zur Übersicht, Modus „Bbox" wählen, diesen Glyph aktivieren und ein Rechteck ziehen.
        </Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/chart')} sx={{ mt: 2 }}>
          Zurück zur Übersicht
        </Button>
      </Box>
    );
  }

  const baselineCss = (bbox.baseline_y - bbox.y0) * scale;
  const midbandCss = (bbox.midband_y - bbox.y0) * scale;
  const dragCss = calibDrag ? (calibDrag.curY - bbox.y0) * scale : null;
  const xHeightPx = bbox.baseline_y - bbox.midband_y;
  const [aR, xR, dR] = source.style_ratio;
  const ascenderY = bbox.midband_y - (aR / xR) * xHeightPx;
  const descenderY = bbox.baseline_y + (dR / xR) * xHeightPx;
  const ascenderCss = (ascenderY - bbox.y0) * scale;
  const descenderCss = (descenderY - bbox.y0) * scale;

  return (
    <>
      <Paper square sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderBottom: 1, borderColor: 'divider' }}>
        <IconButton size="small" onClick={() => navigate('/admin/chart')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6" sx={{ fontFamily: 'ui-monospace, Menlo, monospace' }}>
          {known.label}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
          {glyphKey}
        </Typography>
        <Box sx={{ flex: 1 }} />
        <ToggleButtonGroup size="small" value={mode} exclusive onChange={(_e, v: Mode | null) => v && setMode(v)}>
          <ToggleButton value="view">Ansicht</ToggleButton>
          <ToggleButton value="trace">
            <CreateIcon fontSize="small" />
            &nbsp;Strich zeichnen
          </ToggleButton>
        </ToggleButtonGroup>
      </Paper>

      <Box sx={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 380px', overflow: 'hidden' }}>
        <Box ref={hostRef} sx={{ position: 'relative', bgcolor: '#0a0a0a', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', p: 2 }}>
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
                onPointerCancel={() => {
                  setDrawing(false);
                  setCalibDrag(null);
                }}
                style={{ position: 'absolute', inset: 0, touchAction: 'none' }}
              >
                {ascenderCss >= 0 && ascenderCss <= displayH && (
                  <g style={{ pointerEvents: 'none' }}>
                    <line x1={0} y1={ascenderCss} x2={displayW} y2={ascenderCss} stroke="#888" strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
                    <text x={displayW - 90} y={ascenderCss - 3} fontSize={10} fill="#888" opacity={0.8}>
                      ascender ({source.style_ratio.join(':')})
                    </text>
                  </g>
                )}
                {descenderCss >= 0 && descenderCss <= displayH && (
                  <g style={{ pointerEvents: 'none' }}>
                    <line x1={0} y1={descenderCss} x2={displayW} y2={descenderCss} stroke="#888" strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
                    <text x={displayW - 100} y={descenderCss - 3} fontSize={10} fill="#888" opacity={0.8}>
                      descender ({source.style_ratio.join(':')})
                    </text>
                  </g>
                )}
                <g>
                  <line x1={0} y1={baselineCss} x2={displayW} y2={baselineCss} stroke="#ff5060" strokeWidth={1.5} strokeDasharray="6 4" style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }} onPointerDown={startCalibDrag('baseline_y')} />
                  <rect x={4} y={baselineCss - 9} width={86} height={16} fill="#ff5060" style={{ cursor: 'ns-resize' }} onPointerDown={startCalibDrag('baseline_y')} />
                  <text x={8} y={baselineCss + 3} fontSize={11} fill="#1a0000" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                    baseline {bbox.baseline_y}
                  </text>
                </g>
                <g>
                  <line x1={0} y1={midbandCss} x2={displayW} y2={midbandCss} stroke="#c060ff" strokeWidth={1.5} strokeDasharray="3 3" style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }} onPointerDown={startCalibDrag('midband_y')} />
                  <rect x={4} y={midbandCss - 9} width={86} height={16} fill="#c060ff" style={{ cursor: 'ns-resize' }} onPointerDown={startCalibDrag('midband_y')} />
                  <text x={8} y={midbandCss + 3} fontSize={11} fill="#1a001a" fontWeight="bold" style={{ pointerEvents: 'none' }}>
                    midband {bbox.midband_y}
                  </text>
                </g>
                {dragCss != null && calibDrag && (
                  <line x1={0} y1={dragCss} x2={displayW} y2={dragCss} stroke={calibDrag.field === 'baseline_y' ? '#ff5060' : '#c060ff'} strokeWidth={2} opacity={0.6} />
                )}
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

        <Box sx={{ borderLeft: 1, borderColor: 'divider', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          <Stack spacing={2} sx={{ p: 2 }}>
            <Box>
              <Typography variant="overline" color="text.secondary">
                Kalibrierung
              </Typography>
              <Stack spacing={1.5} sx={{ mt: 1 }}>
                <CalibrationRow label="baseline_y" value={bbox.baseline_y} color="#ff5060" onSet={(v) => updateBboxField({ baseline_y: v })} />
                <CalibrationRow label="midband_y" value={bbox.midband_y} color="#c060ff" onSet={(v) => updateBboxField({ midband_y: v })} />
                <Typography variant="caption" color="text.secondary">
                  x-Höhe = {xHeightPx} px
                </Typography>
              </Stack>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">
                Resampling
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: 'center' }}>
                <TextField
                  label="n_anchors"
                  type="number"
                  size="small"
                  value={bbox.n_anchors}
                  onChange={(e) => updateBboxField({ n_anchors: Math.max(4, Number(e.target.value)) })}
                  sx={{ flex: 1 }}
                />
                <Tooltip title="Bestehenden Strich mit der neuen Anker-Anzahl neu abtasten (kein neues Zeichnen nötig)">
                  <span>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      disabled={!hasCanonical}
                      onClick={async () => {
                        try {
                          const g = await postResample(glyphKey, bbox.n_anchors);
                          markGlyphTraced(glyphKey, {
                            glyph_key: g.glyph_key,
                            glyph: g.glyph,
                            position: g.position,
                            variant: g.variant,
                            advance: g.advance,
                            has_data: true,
                          });
                          setSnack({ kind: 'success', text: `neu abgetastet · ${g.anchors.length} Anker` });
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
                Der ursprüngliche Pen-Pfad bleibt im Canonical erhalten — n_anchors kann beliebig oft angepasst werden.
              </Typography>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">
                Ausschluss-Rechtecke ({bbox.excludes.length})
              </Typography>
              <Stack spacing={0.5} sx={{ mt: 1, maxHeight: 120, overflowY: 'auto' }}>
                {bbox.excludes.map((ex, i) => (
                  <Paper key={i} variant="outlined" sx={{ p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                      ({ex.x0},{ex.y0})→({ex.x1},{ex.y1})
                    </Typography>
                    <Tooltip title="diesen Ausschluss entfernen">
                      <IconButton
                        size="small"
                        onClick={() => updateBboxField({ excludes: bbox.excludes.filter((_, j) => j !== i) })}
                      >
                        <ClearIcon fontSize="inherit" />
                      </IconButton>
                    </Tooltip>
                  </Paper>
                ))}
                {bbox.excludes.length === 0 && (
                  <Typography variant="caption" color="text.disabled">
                    keine
                  </Typography>
                )}
              </Stack>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">
                Strich
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
                <Tooltip title="letzten Pen-Punkt rückgängig">
                  <span>
                    <IconButton size="small" disabled={pathPts.length === 0} onClick={() => setPathPts((p) => p.slice(0, -1))}>
                      <UndoIcon />
                    </IconButton>
                  </span>
                </Tooltip>
                <Button size="small" variant="outlined" color="warning" startIcon={<ClearIcon />} disabled={pathPts.length === 0} onClick={() => setPathPts([])}>
                  Verwerfen
                </Button>
                <Button size="small" variant="contained" startIcon={<SaveIcon />} disabled={pathPts.length < 2} onClick={saveTrace}>
                  Canonical speichern
                </Button>
              </Stack>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                {pathPts.length} Pen-Punkte aufgenommen · oben auf „Strich zeichnen" wechseln, dann mit dem S-Pen (oder der Maus) den Buchstaben nachfahren.
              </Typography>
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">
                Diagnose
              </Typography>
              {hasCanonical ? (
                <Box sx={{ mt: 1 }}>
                  <DiagnosticView glyphKey={glyphKey} cropCacheBust={cropCacheBust} />
                </Box>
              ) : (
                <Alert severity="info" sx={{ mt: 1 }}>
                  noch kein Canonical — erst einen Strich aufnehmen und speichern.
                </Alert>
              )}
            </Box>

            <Divider />

            <Box>
              <Typography variant="overline" color="text.secondary">
                Fit (M4)
              </Typography>
              {hasCanonical ? (
                <Box sx={{ mt: 1 }}>
                  <FitView glyphKey={glyphKey} cropCacheBust={cropCacheBust} />
                </Box>
              ) : (
                <Alert severity="info" sx={{ mt: 1 }}>
                  noch kein Canonical — der Fit braucht eine gespeicherte Vorlage.
                </Alert>
              )}
            </Box>
          </Stack>
        </Box>
      </Box>

      <Snackbar open={snack !== null} autoHideDuration={3000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={snack?.kind ?? 'info'} onClose={() => setSnack(null)} variant="filled">
          {snack?.text}
        </Alert>
      </Snackbar>
    </>
  );
}
