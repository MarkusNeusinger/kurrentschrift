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
import ControlCameraIcon from '@mui/icons-material/ControlCamera';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
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

import { chartUrl, deleteBbox, deleteGlyph, putBbox } from '../api';
import { useAdmin } from '../state';
import type { BboxIn, BboxOut, ExcludeRect } from '../types';

type Mode = 'pan' | 'bbox' | 'exclude' | 'edit';

interface DragState {
  mode: 'bbox' | 'exclude';
  startX: number;
  startY: number;
  curX: number;
  curY: number;
}

// Move/resize of an existing bbox. `handle` is which grip was grabbed ('move'
// = the body, the rest are edges/corners). We keep the original rect so each
// move recomputes from a fixed origin, and a live `cur` rect for the preview.
type EditHandle = 'move' | 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw';
interface Rect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}
interface EditState {
  handle: EditHandle;
  startX: number;
  startY: number;
  orig: Rect;
  cur: Rect;
}

const MIN_BOX = 6;
// Resize grips are only the eight little squares (corners + edge midpoints).
// GRIP_HIT is their hit half-size in screen px (the caller divides by zoom),
// kept a touch larger than the drawn handle so it stays easy to grab on touch.
const GRIP_HIT = 12;

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
    guides: b.guides,
  };
}

const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

// Which grip of rect `b` sits at image point (x,y)? Resize only triggers on the
// eight little grip squares (corners + edge midpoints); the rest of the box body
// — edges included — moves, so the border lines never block a drag. `tol` is the
// grip hit half-size in image px (the caller scales it by zoom).
function hitHandle(b: Rect, x: number, y: number, tol: number): EditHandle | null {
  const mx = (b.x0 + b.x1) / 2;
  const my = (b.y0 + b.y1) / 2;
  const onGrip = (gx: number, gy: number) => Math.abs(x - gx) <= tol && Math.abs(y - gy) <= tol;
  if (onGrip(b.x0, b.y0)) return 'nw';
  if (onGrip(b.x1, b.y0)) return 'ne';
  if (onGrip(b.x0, b.y1)) return 'sw';
  if (onGrip(b.x1, b.y1)) return 'se';
  if (onGrip(mx, b.y0)) return 'n';
  if (onGrip(mx, b.y1)) return 's';
  if (onGrip(b.x0, my)) return 'w';
  if (onGrip(b.x1, my)) return 'e';
  // Inclusive bounds so grabbing exactly on a border (between grips) still moves.
  if (x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1) return 'move';
  return null;
}

// Apply a drag delta to the original rect for the grabbed handle, clamped to
// the chart bounds and a minimum size.
function applyHandle(handle: EditHandle, orig: Rect, dx: number, dy: number, w: number, h: number): Rect {
  if (handle === 'move') {
    const tx = clamp(dx, -orig.x0, w - orig.x1);
    const ty = clamp(dy, -orig.y0, h - orig.y1);
    return { x0: orig.x0 + tx, y0: orig.y0 + ty, x1: orig.x1 + tx, y1: orig.y1 + ty };
  }
  let { x0, y0, x1, y1 } = orig;
  if (handle.includes('n')) y0 = clamp(y0 + dy, 0, y1 - MIN_BOX);
  if (handle.includes('s')) y1 = clamp(y1 + dy, y0 + MIN_BOX, h);
  if (handle.includes('w')) x0 = clamp(x0 + dx, 0, x1 - MIN_BOX);
  if (handle.includes('e')) x1 = clamp(x1 + dx, x0 + MIN_BOX, w);
  return { x0, y0, x1, y1 };
}

// Build the BboxIn for a finished move/resize. A move carries the baseline,
// midband and excludes along by the same offset; a resize keeps the guide
// lines but clamps them (and clips the excludes) into the new bounds.
function editedBbox(current: BboxOut, handle: EditHandle, cur: Rect): BboxIn {
  const r = { x0: Math.round(cur.x0), y0: Math.round(cur.y0), x1: Math.round(cur.x1), y1: Math.round(cur.y1) };
  const base = bboxInFromOut(current);
  if (handle === 'move') {
    const dx = r.x0 - current.x0;
    const dy = r.y0 - current.y0;
    return {
      ...base,
      ...r,
      baseline_y: current.baseline_y + dy,
      midband_y: current.midband_y + dy,
      excludes: current.excludes.map((ex) => ({ x0: ex.x0 + dx, y0: ex.y0 + dy, x1: ex.x1 + dx, y1: ex.y1 + dy })),
    };
  }
  const excludes = current.excludes
    .map((ex) => ({
      x0: clamp(ex.x0, r.x0, r.x1),
      y0: clamp(ex.y0, r.y0, r.y1),
      x1: clamp(ex.x1, r.x0, r.x1),
      y1: clamp(ex.y1, r.y0, r.y1),
    }))
    .filter((ex) => ex.x1 - ex.x0 >= 1 && ex.y1 - ex.y0 >= 1);
  return { ...base, ...r, baseline_y: clamp(current.baseline_y, r.y0, r.y1), midband_y: clamp(current.midband_y, r.y0, r.y1), excludes };
}

export function ChartPage() {
  const { source, bboxesByKey, glyphsByKey, activeGlyph, visibleGlyphs, upsertBbox, removeBbox, removeGlyph } = useAdmin();
  const navigate = useNavigate();
  const stageRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [mode, setMode] = useState<Mode>('pan');
  // Lock freezes every box: no move/resize/draw, grips hidden — only pan/zoom.
  // Flip it on once boxes are placed so a stray drag can't nudge them.
  const [locked, setLocked] = useState(false);
  const [zoom, setZoom] = useState(0.75);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [edit, setEdit] = useState<EditState | null>(null);
  const [pan, setPan] = useState<PanState | null>(null);
  const [snack, setSnack] = useState<string | null>(null);
  // Two-finger pinch-zoom (touch): track live pointers and the gesture anchor.
  const pointersRef = useRef<Map<number, { x: number; y: number }>>(new Map());
  const pinchRef = useRef<{ startDist: number; startZoom: number } | null>(null);

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
      pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      // Second finger down → switch to a pinch-zoom gesture, dropping any
      // pan/drag the first finger started.
      if (pointersRef.current.size === 2) {
        setPan(null);
        setDrag(null);
        const [a, b] = [...pointersRef.current.values()];
        pinchRef.current = { startDist: Math.hypot(a.x - b.x, a.y - b.y), startZoom: zoom };
        (e.target as Element).setPointerCapture?.(e.pointerId);
        e.preventDefault();
        return;
      }
      if (pinchRef.current) return; // already pinching — ignore extra contacts
      // Locked: only pan/zoom, never edit — drag the chart instead of a box.
      if (mode === 'pan' || locked) {
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
      if (mode === 'edit') {
        const current = bboxesByKey[activeGlyph];
        if (!current) {
          setSnack(`${activeGlyph}: hat noch keine Bbox — erst im Modus „Bbox" zeichnen.`);
          return;
        }
        const handle = hitHandle(current, x, y, GRIP_HIT / zoom);
        if (!handle) {
          setSnack('Zum Verschieben in die Box fassen, zum Skalieren an einen Griffpunkt (Ecke/Kantenmitte).');
          return;
        }
        const r: Rect = { x0: current.x0, y0: current.y0, x1: current.x1, y1: current.y1 };
        setEdit({ handle, startX: x, startY: y, orig: r, cur: r });
      } else if (mode === 'exclude') {
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
    [mode, locked, activeGlyph, bboxesByKey, pointToImage, zoom],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const pinch = pinchRef.current;
      if (pinch && pointersRef.current.has(e.pointerId)) {
        pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
        const pts = [...pointersRef.current.values()];
        if (pts.length < 2 || pinch.startDist === 0) return;
        const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        const midX = (pts[0].x + pts[1].x) / 2;
        const midY = (pts[0].y + pts[1].y) / 2;
        const sc = scrollRef.current;
        if (!sc) return;
        const rect = sc.getBoundingClientRect();
        setZoom((prevZoom) => {
          // Read pinch geometry from the captured local, not pinchRef.current:
          // the ref may have been cleared by pointerup before this runs.
          const target = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, pinch.startZoom * (dist / pinch.startDist)));
          if (target === prevZoom) return prevZoom;
          // Keep the image point under the pinch midpoint fixed across the zoom.
          const imgX = (midX - rect.left + sc.scrollLeft) / prevZoom;
          const imgY = (midY - rect.top + sc.scrollTop) / prevZoom;
          requestAnimationFrame(() => {
            sc.scrollLeft = imgX * target - (midX - rect.left);
            sc.scrollTop = imgY * target - (midY - rect.top);
          });
          return target;
        });
        return;
      }
      if (pan) {
        const sc = scrollRef.current;
        if (!sc) return;
        sc.scrollLeft = pan.startScrollLeft - (e.clientX - pan.startClientX);
        sc.scrollTop = pan.startScrollTop - (e.clientY - pan.startClientY);
        return;
      }
      if (edit) {
        const { x, y } = pointToImage(e.clientX, e.clientY);
        const cur = applyHandle(edit.handle, edit.orig, x - edit.startX, y - edit.startY, width, height);
        setEdit({ ...edit, cur });
        return;
      }
      if (!drag) return;
      const { x, y } = pointToImage(e.clientX, e.clientY);
      setDrag({ ...drag, curX: x, curY: y });
    },
    [drag, edit, pan, pointToImage, width, height],
  );

  const onPointerUp = useCallback(async (e: React.PointerEvent<HTMLDivElement>) => {
    pointersRef.current.delete(e.pointerId);
    if (pinchRef.current) {
      if (pointersRef.current.size < 2) pinchRef.current = null;
      return;
    }
    if (pan) {
      setPan(null);
      return;
    }
    if (edit) {
      const ed = edit;
      setEdit(null);
      const current = activeGlyph ? bboxesByKey[activeGlyph] : null;
      if (!activeGlyph || !current) return;
      const unchanged =
        Math.round(ed.cur.x0) === current.x0 &&
        Math.round(ed.cur.y0) === current.y0 &&
        Math.round(ed.cur.x1) === current.x1 &&
        Math.round(ed.cur.y1) === current.y1;
      if (unchanged) return;
      try {
        const saved = await putBbox(activeGlyph, editedBbox(current, ed.handle, ed.cur));
        upsertBbox(activeGlyph, saved);
        setSnack(`${activeGlyph}: Box ${ed.handle === 'move' ? 'verschoben' : 'angepasst'}.`);
      } catch (err) {
        setSnack(`Speichern fehlgeschlagen: ${err}`);
      }
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
  }, [drag, edit, pan, activeGlyph, bboxesByKey, upsertBbox]);

  const deleteActive = useCallback(async () => {
    if (!activeGlyph || !(activeGlyph in bboxesByKey)) return;
    const hasGlyph = glyphsByKey[activeGlyph]?.has_data === true;
    const ok = window.confirm(
      `Bbox für „${activeGlyph}" löschen?${hasGlyph ? ' Das gespeicherte Canonical wird mit entfernt.' : ''}`,
    );
    if (!ok) return;
    try {
      if (hasGlyph) {
        await deleteGlyph(activeGlyph);
        removeGlyph(activeGlyph);
      }
      await deleteBbox(activeGlyph);
      removeBbox(activeGlyph);
      setSnack(`${activeGlyph}: gelöscht.`);
    } catch (err) {
      setSnack(`Löschen fehlgeschlagen: ${err}`);
    }
  }, [activeGlyph, bboxesByKey, glyphsByKey, removeBbox, removeGlyph, deleteBbox, deleteGlyph]);

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
      if (e.key === 'Escape') {
        setDrag(null);
        setEdit(null);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  const cursorStyle: React.CSSProperties =
    locked || mode === 'pan'
      ? { cursor: pan ? 'grabbing' : 'grab' }
      : mode === 'edit'
        ? { cursor: 'move' }
        : { cursor: 'crosshair' };
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
          <ToggleButton value="bbox" disabled={locked}>
            <AddBoxIcon fontSize="small" />
            &nbsp;Bbox
          </ToggleButton>
          <ToggleButton value="edit" disabled={locked}>
            <ControlCameraIcon fontSize="small" />
            &nbsp;Verschieben
          </ToggleButton>
          <ToggleButton value="exclude" disabled={locked}>
            <ContentCutIcon fontSize="small" />
            &nbsp;Ausschluss
          </ToggleButton>
        </ToggleButtonGroup>

        <Tooltip title={locked ? 'Boxen gesperrt — zum Bearbeiten entsperren' : 'Boxen sperren (nur Schwenken/Zoomen)'}>
          <ToggleButton
            size="small"
            value="lock"
            selected={locked}
            color="warning"
            aria-label={locked ? 'Boxen entsperren' : 'Boxen sperren'}
            onChange={() => setLocked((v) => !v)}
          >
            {locked ? <LockIcon fontSize="small" /> : <LockOpenIcon fontSize="small" />}
          </ToggleButton>
        </Tooltip>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: { xs: 0, sm: 300 }, flex: { xs: 1, sm: 'none' } }}>
          <IconButton
            size="small"
            onClick={() => setZoom((z) => Math.max(ZOOM_PRESETS[0], ZOOM_PRESETS[Math.max(0, ZOOM_PRESETS.findIndex((p) => p >= z) - 1)]))}
          >
            <RemoveIcon />
          </IconButton>
          <Slider
            size="small"
            sx={{ width: { xs: 'auto', sm: 160 }, flex: { xs: 1, sm: 'none' } }}
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
        <Tooltip title="Bbox des aktiven Glyphs löschen">
          <span>
            <IconButton
              size="small"
              color="error"
              aria-label="Bbox des aktiven Glyphs löschen"
              disabled={locked || !activeGlyph || !(activeGlyph in bboxesByKey)}
              onClick={deleteActive}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
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
            {mode === 'edit' &&
              !locked &&
              activeGlyph &&
              bboxesByKey[activeGlyph] &&
              (() => {
                const b: Rect = edit ? edit.cur : bboxesByKey[activeGlyph];
                const hs = 9 / zoom; // handle half-size in image px (≈18px on screen)
                const mx = (b.x0 + b.x1) / 2;
                const my = (b.y0 + b.y1) / 2;
                const grips: Array<[number, number]> = [
                  [b.x0, b.y0],
                  [b.x1, b.y0],
                  [b.x0, b.y1],
                  [b.x1, b.y1],
                  [mx, b.y0],
                  [mx, b.y1],
                  [b.x0, my],
                  [b.x1, my],
                ];
                return (
                  <g style={{ pointerEvents: 'none' }}>
                    <rect
                      x={b.x0}
                      y={b.y0}
                      width={b.x1 - b.x0}
                      height={b.y1 - b.y0}
                      fill="#ffae00"
                      fillOpacity={0.1}
                      stroke="#ffae00"
                      strokeWidth={2 / zoom}
                    />
                    {grips.map(([gx, gy], i) => (
                      <rect
                        key={i}
                        x={gx - hs}
                        y={gy - hs}
                        width={hs * 2}
                        height={hs * 2}
                        fill="#ffae00"
                        stroke="#1a1200"
                        strokeWidth={1 / zoom}
                      />
                    ))}
                  </g>
                );
              })()}
          </svg>
          <Box
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={(e) => {
              pointersRef.current.delete(e.pointerId);
              pinchRef.current = null;
              setDrag(null);
              setEdit(null);
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
