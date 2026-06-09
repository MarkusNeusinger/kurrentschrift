// Viewport state for the chart editor: zoom (slider, preset −/+ stepping,
// cursor-anchored wheel zoom, two-finger pinch), pan-by-drag scrolling and the
// CSS→image coordinate mapping. Owns scrollRef (the scrolling container) and
// stageRef (the zoomed stage). ChartView keeps the single pointer-routing layer
// and calls into the gesture primitives returned here.

import { useCallback, useEffect, useRef, useState } from 'react';

import { ZOOM_MAX, ZOOM_MIN, ZOOM_PRESETS } from './chartConstants';

interface PanState {
  startClientX: number;
  startClientY: number;
  startScrollLeft: number;
  startScrollTop: number;
}

export function useChartViewport(width: number, height: number) {
  const stageRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [zoom, setZoom] = useState(0.75);
  const [pan, setPan] = useState<PanState | null>(null);
  // Two-finger pinch-zoom (touch): track live pointers and the gesture anchor.
  const pointersRef = useRef<Map<number, { x: number; y: number }>>(new Map());
  const pinchRef = useRef<{ startDist: number; startZoom: number } | null>(null);

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

  // Register a pointer contact. Second finger down → switch to a pinch-zoom
  // gesture (returns 'start'; the caller drops any pan/drag the first finger
  // started — pan is cleared here, the draw-drag by the routing layer). While a
  // pinch is live, extra contacts report 'active' so the caller ignores them.
  const beginPointer = useCallback(
    (e: React.PointerEvent<HTMLDivElement>): 'start' | 'active' | null => {
      pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointersRef.current.size === 2) {
        setPan(null);
        const [a, b] = [...pointersRef.current.values()];
        pinchRef.current = { startDist: Math.hypot(a.x - b.x, a.y - b.y), startZoom: zoom };
        return 'start';
      }
      if (pinchRef.current) return 'active'; // already pinching — ignore extra contacts
      return null;
    },
    [zoom],
  );

  // Start a pan-scroll drag; false when the scroll container isn't mounted yet
  // (the caller then skips pointer capture, as before).
  const startPan = useCallback((e: React.PointerEvent<HTMLDivElement>): boolean => {
    const sc = scrollRef.current;
    if (!sc) return false;
    setPan({
      startClientX: e.clientX,
      startClientY: e.clientY,
      startScrollLeft: sc.scrollLeft,
      startScrollTop: sc.scrollTop,
    });
    return true;
  }, []);

  // Pinch half of the pointer-move routing: true when the move belonged to a
  // live pinch gesture (consumed), false to fall through to pan/edit/draw.
  const pinchMove = useCallback((e: React.PointerEvent<HTMLDivElement>): boolean => {
    const pinch = pinchRef.current;
    if (!pinch || !pointersRef.current.has(e.pointerId)) return false;
    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const pts = [...pointersRef.current.values()];
    if (pts.length < 2 || pinch.startDist === 0) return true;
    const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
    const midX = (pts[0].x + pts[1].x) / 2;
    const midY = (pts[0].y + pts[1].y) / 2;
    const sc = scrollRef.current;
    if (!sc) return true;
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
    return true;
  }, []);

  // Pan half of the pointer-move routing: true when a pan drag is live.
  const panMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>): boolean => {
      if (!pan) return false;
      const sc = scrollRef.current;
      if (!sc) return true;
      sc.scrollLeft = pan.startScrollLeft - (e.clientX - pan.startClientX);
      sc.scrollTop = pan.startScrollTop - (e.clientY - pan.startClientY);
      return true;
    },
    [pan],
  );

  // Unregister a lifted pointer. True while a pinch was consuming the gesture
  // (the pinch ends once fewer than two contacts remain).
  const releasePointer = useCallback((e: React.PointerEvent<HTMLDivElement>): boolean => {
    pointersRef.current.delete(e.pointerId);
    if (pinchRef.current) {
      if (pointersRef.current.size < 2) pinchRef.current = null;
      return true;
    }
    return false;
  }, []);

  // End a pan drag; true when one was live (consumed the pointerup).
  const endPan = useCallback((): boolean => {
    if (!pan) return false;
    setPan(null);
    return true;
  }, [pan]);

  // pointercancel: drop the contact and any pinch/pan in flight.
  const cancelGesture = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    pointersRef.current.delete(e.pointerId);
    pinchRef.current = null;
    setPan(null);
  }, []);

  // Preset stepping for the toolbar's −/+ buttons.
  const zoomOut = useCallback(() => {
    setZoom((z) => Math.max(ZOOM_PRESETS[0], ZOOM_PRESETS[Math.max(0, ZOOM_PRESETS.findIndex((p) => p >= z) - 1)]));
  }, []);
  const zoomIn = useCallback(() => {
    setZoom(
      (z) =>
        ZOOM_PRESETS[
          Math.min(
            ZOOM_PRESETS.length - 1,
            ZOOM_PRESETS.findIndex((p) => p > z) === -1 ? ZOOM_PRESETS.length - 1 : ZOOM_PRESETS.findIndex((p) => p > z),
          )
        ],
    );
  }, []);

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

  return {
    stageRef,
    scrollRef,
    zoom,
    setZoom,
    zoomOut,
    zoomIn,
    pointToImage,
    panning: pan !== null,
    beginPointer,
    startPan,
    pinchMove,
    panMove,
    releasePointer,
    endPan,
    cancelGesture,
  };
}
