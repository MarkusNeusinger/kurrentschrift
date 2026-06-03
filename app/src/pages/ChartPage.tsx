// ChartPage — chart.jpg with bbox/exclude overlays for the visible glyphs.
//
// Modes:
//   - PAN: drag scrolls the chart container.
//   - BBOX: drag creates a bbox for the active glyph (replaces any existing).
//          Requires baseline_y/midband_y to be set before saving; if the
//          glyph doesn't have those yet, the new bbox seeds reasonable
//          defaults (top quarter as midband, bottom quarter as baseline).
//   - EXCLUDE: drag adds an exclude rect (must start inside existing bbox).

import AddBoxIcon from '@mui/icons-material/AddBox';
import AddIcon from '@mui/icons-material/Add';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import EditIcon from '@mui/icons-material/Edit';
import OpenWithIcon from '@mui/icons-material/OpenWith';
import RemoveIcon from '@mui/icons-material/Remove';
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  Paper,
  Slider,
  Snackbar,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { chartUrl, putBbox } from '../api';
import { useAdmin } from '../state';
import type { BboxIn, BboxOut, ExcludeRect } from '../types';

type Mode = 'pan' | 'bbox' | 'exclude';

interface DragState {
  mode: 'bbox' | 'exclude';
  startX: number;
  startY: number;
  curX: number;
  curY: number;
}

interface PanState {
  startClientX: number;
  startClientY: number;
  startScrollLeft: number;
  startScrollTop: number;
}

const ZOOM_PRESETS = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4];
const ZOOM_MIN = ZOOM_PRESETS[0];
const ZOOM_MAX = ZOOM_PRESETS[ZOOM_PRESETS.length - 1];

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

export function ChartPage() {
  const { source, bboxesByKey, activeGlyph, visibleGlyphs, upsertBbox } = useAdmin();
  const navigate = useNavigate();
  const stageRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [mode, setMode] = useState<Mode>('pan');
  const [zoom, setZoom] = useState(0.75);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [pan, setPan] = useState<PanState | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  if (!source) return null;
  const { w: width, h: height } = source.chart_size;

  const pointToImage = useCallback(
    (clientX: number, clientY: number) => {
      const el = stageRef.current;
      if (!el) return { x: 0, y: 0 };
      const rect = el.getBoundingClientRect();
      const x = Math.round((clientX - rect.left) / zoom);
      const y = Math.round((clientY - rect.top) / zoom);
      return { x: Math.max(0, Math.min(width, x)), y: Math.max(0, Math.min(height, y)) };
    },
    [zoom, width, height],
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (e.button !== 0 && e.pointerType !== 'pen' && e.pointerType !== 'touch') return;
      if (mode === 'pan') {
        const sc = scrollRef.current;
        if (!sc) return;
        setPan({
          startClientX: e.clientX,
          startClientY: e.clientY,
          startScrollLeft: sc.scrollLeft,
          startScrollTop: sc.scrollTop,
        });
        (e.target as Element).setPointerCapture?.(e.pointerId);
        e.preventDefault();
        return;
      }
      if (!activeGlyph) {
        setSnack('Wähle erst einen Glyph in der Liste links.');
        return;
      }
      const { x, y } = pointToImage(e.clientX, e.clientY);
      if (mode === 'exclude') {
        const current = bboxesByKey[activeGlyph];
        if (!current) {
          setSnack(`${activeGlyph}: hat noch keine Bbox — erst im Modus „Bbox" zeichnen.`);
          return;
        }
        if (x < current.x0 || x > current.x1 || y < current.y0 || y > current.y1) {
          setSnack('Ausschluss muss innerhalb der aktiven Bbox starten.');
          return;
        }
        setDrag({ mode: 'exclude', startX: x, startY: y, curX: x, curY: y });
      } else {
        setDrag({ mode: 'bbox', startX: x, startY: y, curX: x, curY: y });
      }
      (e.target as Element).setPointerCapture?.(e.pointerId);
      e.preventDefault();
    },
    [mode, activeGlyph, bboxesByKey, pointToImage],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (pan) {
        const sc = scrollRef.current;
        if (!sc) return;
        sc.scrollLeft = pan.startScrollLeft - (e.clientX - pan.startClientX);
        sc.scrollTop = pan.startScrollTop - (e.clientY - pan.startClientY);
        return;
      }
      if (!drag) return;
      const { x, y } = pointToImage(e.clientX, e.clientY);
      setDrag({ ...drag, curX: x, curY: y });
    },
    [drag, pan, pointToImage],
  );

  const onPointerUp = useCallback(async () => {
    if (pan) {
      setPan(null);
      return;
    }
    if (!drag || !activeGlyph) {
      setDrag(null);
      return;
    }
    const x0 = Math.min(drag.startX, drag.curX);
    const y0 = Math.min(drag.startY, drag.curY);
    const x1 = Math.max(drag.startX, drag.curX);
    const y1 = Math.max(drag.startY, drag.curY);
    if (x1 - x0 < 6 || y1 - y0 < 6) {
      setDrag(null);
      return;
    }
    const current = bboxesByKey[activeGlyph];
    let next: BboxIn;
    if (drag.mode === 'exclude' && current) {
      const ex: ExcludeRect = { x0, y0, x1, y1 };
      next = { ...bboxInFromOut(current), excludes: [...current.excludes, ex] };
    } else {
      // New bbox: seed midband/baseline at sensible defaults (caller refines
      // them in the editor). Midband at top quarter, baseline 5px above the
      // bottom edge so the calibration drag handles are visible immediately.
      const h = y1 - y0;
      next = {
        x0,
        y0,
        x1,
        y1,
        excludes: [],
        baseline_y: current?.baseline_y ?? Math.round(y0 + h * 0.7),
        midband_y: current?.midband_y ?? Math.round(y0 + h * 0.35),
        n_anchors: current?.n_anchors ?? 50,
      };
    }
    setDrag(null);
    try {
      const saved = await putBbox(activeGlyph, next);
      upsertBbox(activeGlyph, saved);
      setSnack(drag.mode === 'bbox' ? `${activeGlyph}: Bbox gespeichert.` : `${activeGlyph}: Ausschluss hinzugefügt.`);
    } catch (err) {
      setSnack(`Speichern fehlgeschlagen: ${err}`);
    }
  }, [drag, pan, activeGlyph, bboxesByKey, upsertBbox]);

  // Mouse-wheel zooms (centered on the cursor); no modifier key needed.
  useEffect(() => {
    const sc = scrollRef.current;
    if (!sc) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      const newZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, zoom * factor));
      if (newZoom === zoom) return;
      const rect = sc.getBoundingClientRect();
      // Image-space point under the cursor, kept fixed across the zoom.
      const imgX = (e.clientX - rect.left + sc.scrollLeft) / zoom;
      const imgY = (e.clientY - rect.top + sc.scrollTop) / zoom;
      setZoom(newZoom);
      requestAnimationFrame(() => {
        sc.scrollLeft = imgX * newZoom - (e.clientX - rect.left);
        sc.scrollTop = imgY * newZoom - (e.clientY - rect.top);
      });
    };
    sc.addEventListener('wheel', onWheel, { passive: false });
    return () => sc.removeEventListener('wheel', onWheel);
  }, [zoom]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrag(null);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  const cursorStyle: React.CSSProperties = mode === 'pan' ? { cursor: pan ? 'grabbing' : 'grab' } : { cursor: 'crosshair' };
  const stageWidthCss = width * zoom;
  const stageHeightCss = height * zoom;

  return (
    <>
      <Paper square sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderBottom: 1, borderColor: 'divider', flexWrap: 'wrap' }}>
        <ToggleButtonGroup size="small" value={mode} exclusive onChange={(_e, v: Mode | null) => v && setMode(v)}>
          <ToggleButton value="pan">
            <OpenWithIcon fontSize="small" />
            &nbsp;Schwenken
          </ToggleButton>
          <ToggleButton value="bbox">
            <AddBoxIcon fontSize="small" />
            &nbsp;Bbox
          </ToggleButton>
          <ToggleButton value="exclude">
            <ContentCutIcon fontSize="small" />
            &nbsp;Ausschluss
          </ToggleButton>
        </ToggleButtonGroup>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 300 }}>
          <IconButton
            size="small"
            onClick={() => setZoom((z) => Math.max(ZOOM_PRESETS[0], ZOOM_PRESETS[Math.max(0, ZOOM_PRESETS.findIndex((p) => p >= z) - 1)]))}
          >
            <RemoveIcon />
          </IconButton>
          <Slider
            size="small"
            sx={{ width: 160 }}
            value={zoom}
            min={ZOOM_MIN}
            max={ZOOM_MAX}
            step={0.05}
            marks={ZOOM_PRESETS.map((p) => ({ value: p }))}
            onChange={(_e, v) => typeof v === 'number' && setZoom(v)}
          />
          <IconButton
            size="small"
            onClick={() =>
              setZoom(
                (z) =>
                  ZOOM_PRESETS[
                    Math.min(
                      ZOOM_PRESETS.length - 1,
                      ZOOM_PRESETS.findIndex((p) => p > z) === -1 ? ZOOM_PRESETS.length - 1 : ZOOM_PRESETS.findIndex((p) => p > z),
                    )
                  ],
              )
            }
          >
            <AddIcon />
          </IconButton>
          <Typography variant="caption" sx={{ minWidth: 50 }}>
            {Math.round(zoom * 100)}%
          </Typography>
        </Box>

        <Box sx={{ flex: 1 }} />

        {activeGlyph ? <Chip label={`aktiv: ${activeGlyph}`} color="primary" size="small" /> : <Chip label="kein aktiver Glyph" size="small" variant="outlined" />}
        <Tooltip title="Editor für den aktiven Glyph öffnen">
          <span>
            <Button
              size="small"
              variant="contained"
              startIcon={<EditIcon />}
              disabled={!activeGlyph || !(activeGlyph in bboxesByKey)}
              onClick={() => activeGlyph && navigate(`/admin/edit/${encodeURIComponent(activeGlyph)}`)}
            >
              Bearbeiten
            </Button>
          </span>
        </Tooltip>
      </Paper>

      <Box ref={scrollRef} sx={{ flex: 1, overflow: 'auto', bgcolor: '#111', position: 'relative' }}>
        <Box ref={stageRef} sx={{ width: stageWidthCss, height: stageHeightCss, position: 'relative', ...cursorStyle }}>
          <img
            src={chartUrl()}
            alt={source.title}
            width={stageWidthCss}
            height={stageHeightCss}
            draggable={false}
            style={{ display: 'block', pointerEvents: 'none' }}
          />
          <svg
            width={stageWidthCss}
            height={stageHeightCss}
            viewBox={`0 0 ${width} ${height}`}
            style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
          >
            {Object.entries(bboxesByKey).map(([key, b]) => {
              if (!visibleGlyphs.has(key)) return null;
              const isActive = key === activeGlyph;
              const stroke = isActive ? '#ffae00' : '#5da8ff';
              return (
                <g key={key}>
                  <rect
                    x={b.x0}
                    y={b.y0}
                    width={b.x1 - b.x0}
                    height={b.y1 - b.y0}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={isActive ? 3 : 1.5}
                    strokeDasharray={isActive ? undefined : '4 4'}
                  />
                  <text x={b.x0} y={b.y0 - 4} fontSize={14} fill={stroke} style={{ userSelect: 'none' }}>
                    {key}
                  </text>
                  {b.excludes.map((ex, i) => (
                    <rect
                      key={i}
                      x={ex.x0}
                      y={ex.y0}
                      width={ex.x1 - ex.x0}
                      height={ex.y1 - ex.y0}
                      fill={stroke}
                      fillOpacity={0.18}
                      stroke={stroke}
                      strokeDasharray="3 3"
                      strokeWidth={1}
                    />
                  ))}
                </g>
              );
            })}
            {drag && (
              <rect
                x={Math.min(drag.startX, drag.curX)}
                y={Math.min(drag.startY, drag.curY)}
                width={Math.abs(drag.curX - drag.startX)}
                height={Math.abs(drag.curY - drag.startY)}
                fill={drag.mode === 'exclude' ? '#ff6b35' : '#00d2ff'}
                fillOpacity={0.18}
                stroke={drag.mode === 'exclude' ? '#ff6b35' : '#00d2ff'}
                strokeWidth={1.5}
                strokeDasharray="5 3"
              />
            )}
          </svg>
          <Box
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={() => {
              setDrag(null);
              setPan(null);
            }}
            sx={{ position: 'absolute', inset: 0, touchAction: 'none' }}
          />
        </Box>
      </Box>

      <Snackbar open={snack !== null} autoHideDuration={3000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity="info" onClose={() => setSnack(null)} variant="filled">
          {snack}
        </Alert>
      </Snackbar>
    </>
  );
}
