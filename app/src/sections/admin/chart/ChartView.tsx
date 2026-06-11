// ChartView — chart.jpg with bbox overlays for the visible glyphs.
//
// Modes:
//   - PAN: drag scrolls the chart container.
//   - BBOX: drag creates a bbox for the active glyph (replaces any existing).
//          Requires baseline_y/midband_y to be set before saving; if the
//          glyph doesn't have those yet, the new bbox seeds reasonable
//          defaults (NEW_BBOX_MIDBAND_RATIO/NEW_BBOX_BASELINE_RATIO of the
//          box height, see chartConstants).
//   - EDIT: move/resize an existing bbox via grips.
// The freeform eraser (Ausschluss/Radierer), Lineatur, Schräglage and Weg now live
// in the step-by-step Einrichtungs-Wizard, opened with "Einrichten".
//
// This file is the composition: it owns the mode and the single pointer-routing
// layer (priority: pinch → pan → edit → draw), delegating to useChartViewport
// (zoom/pan/pinch/coords) and useBboxEditing (draw/move/resize/lock/delete),
// and renders ChartToolbar + the stage (img + BboxOverlay) + the snackbar.

import { Alert, Box, Snackbar } from '@mui/material';
import { useCallback, useState } from 'react';

import { chartUrl } from '@/lib/api';
import { isLetterSplit, siblingKeys } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { overlay } from '@/sections/admin/overlayColors';
import { BboxOverlay } from './BboxOverlay';
import { ChartToolbar } from './ChartToolbar';
import { RederiveAllDialog } from './RederiveAllDialog';
import { useBboxEditing } from './useBboxEditing';
import { useChartViewport } from './useChartViewport';
import type { Mode } from './chartConstants';
import type { SourceOut } from '@/lib/api';

interface ChartViewProps {
  // Required: the page mounts ChartView only once the source has loaded, so
  // every hook below runs unconditionally (rules of hooks).
  source: SourceOut;
}

export function ChartView({ source }: ChartViewProps) {
  const { bboxesByKey, glyphsByKey, activeGlyph, visibleGlyphs, openWizard, openDiagnose } = useAdmin();
  const [mode, setMode] = useState<Mode>('pan');
  const [rederiveOpen, setRederiveOpen] = useState(false);
  const { w: width, h: height } = source.chart_size;

  const {
    stageRef,
    scrollRef,
    zoom,
    setZoom,
    zoomOut,
    zoomIn,
    pointToImage,
    panning,
    beginPointer,
    startPan,
    pinchMove,
    panMove,
    releasePointer,
    endPan,
    cancelGesture,
  } = useChartViewport(width, height);

  const {
    drag,
    edit,
    snack,
    setSnack,
    startEditOrDraw,
    updateEditOrDraw,
    commitEditOrDraw,
    cancelDraw,
    cancelInteraction,
    toggleLock,
    deleteActive,
  } = useBboxEditing({ width, height, zoom, mode, pointToImage });

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (e.button !== 0 && e.pointerType !== 'pen' && e.pointerType !== 'touch') return;
      // Second finger down → switch to a pinch-zoom gesture, dropping any
      // pan/drag the first finger started.
      const pinch = beginPointer(e);
      if (pinch === 'start') {
        cancelDraw();
        (e.target as Element).setPointerCapture?.(e.pointerId);
        e.preventDefault();
        return;
      }
      if (pinch === 'active') return; // already pinching — ignore extra contacts
      if (mode === 'pan') {
        if (!startPan(e)) return;
        (e.target as Element).setPointerCapture?.(e.pointerId);
        e.preventDefault();
        return;
      }
      if (!startEditOrDraw(e)) return;
      (e.target as Element).setPointerCapture?.(e.pointerId);
      e.preventDefault();
    },
    [mode, beginPointer, cancelDraw, startPan, startEditOrDraw],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (pinchMove(e)) return;
      if (panMove(e)) return;
      updateEditOrDraw(e);
    },
    [pinchMove, panMove, updateEditOrDraw],
  );

  const onPointerUp = useCallback(
    async (e: React.PointerEvent<HTMLDivElement>) => {
      if (releasePointer(e)) return;
      if (endPan()) return;
      await commitEditOrDraw();
    },
    [releasePointer, endPan, commitEditOrDraw],
  );

  // Lock state of the affected scope: the whole letter for a unified glyph (the
  // three positions move as one, matching the sidebar icon and the fan-out
  // toggle), or just the active position for a split letter. The button is
  // reachable as long as a relevant position has a bbox.
  const activeSplit = activeGlyph ? isLetterSplit(activeGlyph, bboxesByKey) : false;
  const activeSiblings = activeGlyph
    ? (activeSplit ? [activeGlyph] : siblingKeys(activeGlyph)).filter((k) => k in bboxesByKey)
    : [];
  const activeLocked = activeSiblings.some((k) => bboxesByKey[k]?.locked === true);
  const activeHasCanonical = activeGlyph ? glyphsByKey[activeGlyph]?.has_data === true : false;
  const cursorStyle: React.CSSProperties =
    mode === 'pan'
      ? { cursor: panning ? 'grabbing' : 'grab' }
      : activeLocked
        ? { cursor: 'not-allowed' }
        : mode === 'edit'
          ? { cursor: 'move' }
          : { cursor: 'crosshair' };
  const stageWidthCss = width * zoom;
  const stageHeightCss = height * zoom;

  return (
    <>
      <ChartToolbar
        mode={mode}
        onModeChange={setMode}
        activeGlyph={activeGlyph}
        activeSplit={activeSplit}
        activeLocked={activeLocked}
        hasLockableBbox={activeSiblings.length > 0}
        hasActiveBbox={!!activeGlyph && activeGlyph in bboxesByKey}
        activeHasCanonical={activeHasCanonical}
        zoom={zoom}
        onZoomChange={setZoom}
        onZoomOut={zoomOut}
        onZoomIn={zoomIn}
        onToggleLock={toggleLock}
        onDelete={deleteActive}
        onOpenWizard={() => activeGlyph && openWizard(activeGlyph)}
        onOpenDiagnose={() => activeGlyph && openDiagnose(activeGlyph)}
        onOpenRederiveAll={() => setRederiveOpen(true)}
      />
      <RederiveAllDialog open={rederiveOpen} onClose={() => setRederiveOpen(false)} />

      <Box ref={scrollRef} sx={{ flex: 1, overflow: 'auto', bgcolor: overlay.canvasBg, position: 'relative' }}>
        <Box ref={stageRef} sx={{ width: stageWidthCss, height: stageHeightCss, position: 'relative', ...cursorStyle }}>
          <img
            src={chartUrl()}
            alt={source.title}
            width={stageWidthCss}
            height={stageHeightCss}
            draggable={false}
            style={{ display: 'block', pointerEvents: 'none' }}
          />
          <BboxOverlay
            width={width}
            height={height}
            stageWidthCss={stageWidthCss}
            stageHeightCss={stageHeightCss}
            zoom={zoom}
            mode={mode}
            bboxesByKey={bboxesByKey}
            visibleGlyphs={visibleGlyphs}
            activeGlyph={activeGlyph}
            activeLocked={activeLocked}
            drag={drag}
            edit={edit}
          />
          <Box
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={(e) => {
              cancelGesture(e);
              cancelInteraction();
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
