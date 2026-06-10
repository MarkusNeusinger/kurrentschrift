// The wizard canvas' crop viewport: fit-to-view scaling plus a shared zoom/pan
// carried across every step (wheel or the floating −/slider/+ control). Owns the
// committed view state (userZoom/pan/Schwenken toggle); the live pan-drag
// gesture itself stays in WizardCanvas.

import { useCallback, useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react';

import { useElementSize } from '@/hooks/useElementSize';
import type { BboxOut } from '@/lib/api';

// Wizard canvas zoom. 1 = fit-to-view (the whole bbox fills the frame); above
// that the crop is magnified and can be panned (Schwenken) to reach the box
// edges, where a neighbour's ink pokes in and needs erasing.
export const ZOOM_MIN = 1;
export const ZOOM_MAX = 6;

const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

// Keep the panned content from being dragged off-screen: the offset can move at
// most half the overflow (content beyond the viewport) in each direction, so a
// content edge never crosses past the matching viewport edge. When the content
// fits (no overflow) the offset is pinned to 0 → centred.
export const clampPan = (offset: number, content: number, viewport: number): number => {
  const limit = Math.max(0, (content - viewport) / 2);
  return clamp(offset, -limit, limit);
};

// Pick a starting zoom so the letter already fills the frame on the first step
// instead of sitting small in the middle. A fresh bbox seeds its x-height band
// at ~35 % of the box height, so a letter without ascender/descender (e.g. `a`)
// only paints that middle slice — fit-to-view then shows mostly empty margin.
// We zoom roughly in inverse proportion to that band fraction, gently capped so
// tall letters (ascender + descender) are never clipped hard; Anpassen (fit)
// and the slider stay one tap away.
function defaultZoomFor(b: BboxOut | null): number {
  if (!b) return 1;
  const h = b.y1 - b.y0;
  if (h <= 0) return 1;
  const bandFraction = Math.max(0.18, (b.baseline_y - b.midband_y) / h);
  return clamp(0.62 / bandFraction, 1, 1.6);
}

export interface CropView {
  hostRef: (el: HTMLDivElement | null) => void;
  hostSize: { w: number; h: number };
  userZoom: number;
  panX: number;
  panY: number;
  setPanX: Dispatch<SetStateAction<number>>;
  setPanY: Dispatch<SetStateAction<number>>;
  panning: boolean;
  setPanning: Dispatch<SetStateAction<boolean>>;
  scale: number;
  displayW: number;
  displayH: number;
  applyZoom: (next: number) => void;
  zoomBy: (factor: number) => void;
  fitZoom: () => void;
  cssToChart: (clientX: number, clientY: number, host: Element | null) => { x: number; y: number };
}

export function useCropView(bbox: BboxOut | null, glyphKey: string, open: boolean): CropView {
  // Always-current bbox, read (not subscribed) by the open/reset effect so it can
  // seed the default zoom without re-running on every mask/lineature edit.
  const bboxRef = useRef(bbox);
  bboxRef.current = bbox;

  // The canvas host node, held in STATE via a callback ref: the dialog's portal
  // mounts it a render after this hook's effects first run, so effects key on the
  // element itself (size measure + wheel listener) instead of open/step.
  const [hostEl, setHostEl] = useState<HTMLDivElement | null>(null);
  const hostRef = useCallback((el: HTMLDivElement | null) => setHostEl(el), []);
  const hostSize = useElementSize(hostEl);

  // Canvas zoom/pan, shared by every step. `userZoom` multiplies the fit scale;
  // pan{X,Y} translate the magnified crop in CSS px; `panning` is the Schwenken
  // toggle (drags pan instead of draw).
  const [userZoom, setUserZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [panning, setPanning] = useState(false);

  // Mounted once and reused for every glyph: when a different glyph opens (or the
  // dialog reopens), drop the view state so one glyph's zoom never leaks onto the
  // next.
  useEffect(() => {
    // Fresh letter → re-centre and seed the auto-zoom from its bbox.
    setPanX(0);
    setPanY(0);
    setPanning(false);
    setUserZoom(defaultZoomFor(bboxRef.current));
  }, [glyphKey, open]);

  const cropW = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropH = bbox ? bbox.y1 - bbox.y0 : 0;
  // baseScale fits the whole bbox into the host; `scale` is that times the user
  // zoom and is what every coordinate transform below uses (so nothing else has
  // to know about zoom). displayW/H are the on-screen crop size at that scale.
  const baseScale = useMemo(() => {
    if (!cropW || !cropH || !hostSize.w || !hostSize.h) return 1;
    const padding = 24;
    return Math.max(0.4, Math.min((hostSize.w - padding) / cropW, (hostSize.h - padding) / cropH));
  }, [cropW, cropH, hostSize]);
  const scale = baseScale * userZoom;
  const displayW = cropW * scale;
  const displayH = cropH * scale;

  // Set the zoom and re-clamp the pan to the new crop size (so zooming out never
  // leaves the crop stranded off-centre). Centred on the frame, not the cursor.
  const applyZoom = useCallback(
    (next: number) => {
      const z = clamp(next, ZOOM_MIN, ZOOM_MAX);
      setUserZoom(z);
      setPanX((p) => clampPan(p, cropW * baseScale * z, hostSize.w));
      setPanY((p) => clampPan(p, cropH * baseScale * z, hostSize.h));
    },
    [cropW, cropH, baseScale, hostSize],
  );
  const zoomBy = useCallback((factor: number) => applyZoom(userZoom * factor), [applyZoom, userZoom]);
  const fitZoom = useCallback(() => {
    setUserZoom(1);
    setPanX(0);
    setPanY(0);
  }, []);

  // Live view geometry for the wheel handler. Refreshed every render so the
  // once-attached listener always reads current values, and rewritten within a
  // wheel burst so several ticks before React re-renders compound (each anchors
  // on the previous tick's zoom/pan) instead of all snapping off one stale frame.
  const viewRef = useRef({ userZoom, panX, panY, baseScale, cropW, cropH });
  viewRef.current = { userZoom, panX, panY, baseScale, cropW, cropH };

  // Mouse-wheel zoom, anchored on the cursor so the point under it stays put
  // (mirrors the chart). Needs a non-passive listener to preventDefault the page
  // scroll, so it's attached imperatively. Re-attached only when the canvas host
  // node (re)appears — keyed on the element like the resize observer — never on
  // zoom/pan, which the handler reads from viewRef instead.
  useEffect(() => {
    const el = hostEl;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const v = viewRef.current;
      const nz = clamp(v.userZoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15), ZOOM_MIN, ZOOM_MAX);
      if (nz === v.userZoom) return;
      const rect = el.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const dW0 = v.cropW * v.baseScale * v.userZoom;
      const dH0 = v.cropH * v.baseScale * v.userZoom;
      // Fraction of the current crop under the cursor (crop is centred + panned).
      const leftX = rect.width / 2 - dW0 / 2 + v.panX;
      const topY = rect.height / 2 - dH0 / 2 + v.panY;
      const fracX = dW0 > 0 ? clamp((cx - leftX) / dW0, 0, 1) : 0.5;
      const fracY = dH0 > 0 ? clamp((cy - topY) / dH0, 0, 1) : 0.5;
      const dW = v.cropW * v.baseScale * nz;
      const dH = v.cropH * v.baseScale * nz;
      const npx = clampPan(cx - rect.width / 2 + dW / 2 - fracX * dW, dW, rect.width);
      const npy = clampPan(cy - rect.height / 2 + dH / 2 - fracY * dH, dH, rect.height);
      viewRef.current = { ...v, userZoom: nz, panX: npx, panY: npy };
      setUserZoom(nz);
      setPanX(npx);
      setPanY(npy);
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [hostEl]);

  const cssToChart = useCallback(
    (clientX: number, clientY: number, host: Element | null) => {
      if (!host || !bbox) return { x: 0, y: 0 };
      const r = host.getBoundingClientRect();
      return { x: bbox.x0 + (clientX - r.left) / scale, y: bbox.y0 + (clientY - r.top) / scale };
    },
    [bbox, scale],
  );

  return {
    hostRef,
    hostSize,
    userZoom,
    panX,
    panY,
    setPanX,
    setPanY,
    panning,
    setPanning,
    scale,
    displayW,
    displayH,
    applyZoom,
    zoomBy,
    fitZoom,
    cssToChart,
  };
}
