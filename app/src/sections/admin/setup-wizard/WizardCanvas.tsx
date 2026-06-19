// The wizard's crop canvas: the bbox crop image + the per-step SVG overlay
// (lineature drag lines, slant guides + handles, eraser strokes, the Weg trace)
// + the floating zoom toolbar. Owns ONLY in-flight gesture state (an eraser
// stroke being painted, a lineature/slant drag, a live pan, the pen-down flag);
// finished gestures are handed to the wizard's commit* callbacks, and committed
// Weg strokes live in useWizard (the in-progress stroke is appended live via
// setStrokes so the trace renders while drawing).

import AddIcon from '@mui/icons-material/Add';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import OpenWithIcon from '@mui/icons-material/OpenWith';
import RemoveIcon from '@mui/icons-material/Remove';
import { Box, IconButton, Slider, Tooltip, Typography } from '@mui/material';
import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from 'react';

import { cropUrl } from '@/lib/api';
import { de } from '@/locales';
import { overlay } from '@/sections/admin/overlayColors';
import type { KnownGlyph } from '@/domain/glyphs';
import type { BboxOut, SourceOut, StrokePoint } from '@/lib/api';
import { splitRawPath } from './strokeUtils';
import { clampPan, ZOOM_MAX, ZOOM_MIN, type CropView } from './useCropView';
import { SLANT_COLOR } from './wizardTypes';
import type { SavedTraceOverlay } from './useWizard';
import type { CalibField, CommitCalib, CommitMaskStroke, CommitSlant, GuideValues, StepId } from './wizardTypes';

// Warp a snapshot of the Weg strokes toward a drag: every point within `radius`
// (chart px) of the grab point moves by the drag delta, weighted by a smoothstep
// falloff so the grabbed spot follows the pointer fully and the line eases back
// to its original shape at the rim — irons out a local wobble without a hard
// kink. Points keep their pressure/timestamp/pen_up.
function warpStrokes(
  snapshot: StrokePoint[][],
  grabX: number,
  grabY: number,
  dx: number,
  dy: number,
  radius: number,
): StrokePoint[][] {
  const r2 = radius * radius;
  return snapshot.map((stroke) =>
    stroke.map((p) => {
      const d2 = (p.x - grabX) ** 2 + (p.y - grabY) ** 2;
      if (d2 >= r2) return p;
      const t = 1 - Math.sqrt(d2) / radius;
      const w = t * t * (3 - 2 * t); // smoothstep
      return { ...p, x: p.x + dx * w, y: p.y + dy * w };
    }),
  );
}

// A dark halo behind the thin dashed guide lines so the bright colours stay
// legible over both light paper and dark ink in the scanned crop.
const GUIDE_SHADOW = 'drop-shadow(0 0 1.5px rgba(0,0,0,0.9))';

export function WizardCanvas({
  glyphKey,
  open,
  stepId,
  bbox,
  source,
  known,
  guideVals,
  view,
  cropCacheBust,
  maskRadius,
  tool,
  wegTool,
  nudgeRadius,
  showMask,
  strokes,
  setStrokes,
  savedTrace,
  showSaved,
  commitCalib,
  commitSlant,
  commitMaskStroke,
  commitInkStroke,
}: {
  glyphKey: string;
  open: boolean;
  stepId: StepId;
  bbox: BboxOut;
  source: SourceOut;
  known: KnownGlyph;
  guideVals: GuideValues;
  view: CropView;
  cropCacheBust: number;
  maskRadius: number;
  tool: 'eraser' | 'ink';
  wegTool: 'draw' | 'adjust';
  nudgeRadius: number;
  showMask: boolean;
  strokes: StrokePoint[][];
  setStrokes: Dispatch<SetStateAction<StrokePoint[][]>>;
  savedTrace: SavedTraceOverlay | null;
  showSaved: boolean;
  commitCalib: CommitCalib;
  commitSlant: CommitSlant;
  commitMaskStroke: CommitMaskStroke;
  commitInkStroke: CommitMaskStroke;
}) {
  const { hostRef, hostSize, userZoom, panX, panY, setPanX, setPanY, panning, setPanning, scale, displayW, displayH, applyZoom, zoomBy, fitZoom, cssToChart } = view;

  // Per-step in-flight gesture state. `drawing` is the pen-down flag of the Weg
  // capture; the strokes themselves live in useWizard.
  const [drawing, setDrawing] = useState(false);
  const [maskDraft, setMaskDraft] = useState<Array<[number, number]> | null>(null);
  // Live eraser cursor (chart coords): a ring drawn at the pointer on the
  // Ausschluss step so the brush's real footprint relative to the crop is visible
  // before painting — and it resizes live as the radius slider changes.
  const [hoverPt, setHoverPt] = useState<{ x: number; y: number } | null>(null);
  const [calibDrag, setCalibDrag] = useState<{ field: CalibField; curY: number } | null>(null);
  // Which slant line is being dragged (index into slant_xs) and its live x.
  const [slantDrag, setSlantDrag] = useState<{ index: number; curX: number } | null>(null);
  // Weg "Anpassen" warp-drag: where the grab started (chart coords) and a frozen
  // snapshot of the strokes at grab time, so each move re-warps from the original
  // shape rather than compounding. Cleared on pointer-up.
  const [nudge, setNudge] = useState<{ x: number; y: number; snapshot: StrokePoint[][] } | null>(null);
  // `panDrag` holds a live pan gesture (a drag while the Schwenken toggle is on).
  const [panDrag, setPanDrag] = useState<{ sx: number; sy: number; px: number; py: number } | null>(null);

  // When a different glyph opens (or the dialog reopens), drop any in-flight
  // gesture — mirrors the wizard-level reset, so one glyph's draft never leaks
  // onto the next.
  useEffect(() => {
    setDrawing(false);
    setMaskDraft(null);
    setHoverPt(null);
    setCalibDrag(null);
    setSlantDrag(null);
    setNudge(null);
    setPanDrag(null);
  }, [glyphKey, open]);

  // ------------------------------------------------------------- pointer routing
  const onSvgPointerDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
      if (panning) {
        e.preventDefault();
        setPanDrag({ sx: e.clientX, sy: e.clientY, px: panX, py: panY });
        e.currentTarget.setPointerCapture(e.pointerId);
        return;
      }
      const { x, y } = cssToChart(e.clientX, e.clientY, e.currentTarget);
      if (stepId === 'mask') {
        e.preventDefault();
        setHoverPt({ x, y });
        setMaskDraft([[x, y]]);
        e.currentTarget.setPointerCapture(e.pointerId);
      } else if (stepId === 'weg') {
        if (e.pointerType !== 'pen' && e.pointerType !== 'mouse' && e.pointerType !== 'touch') return;
        e.preventDefault();
        if (wegTool === 'adjust') {
          // Grab the line where the pointer went down and warp it from there; a
          // grab with no strokes yet is a no-op.
          if (strokes.length > 0) {
            setNudge({ x, y, snapshot: strokes });
            e.currentTarget.setPointerCapture(e.pointerId);
          }
          return;
        }
        setDrawing(true);
        // Each pen-down opens a new stroke; the previous one is left as-is, so a
        // pen lift never draws a line to the next stroke's start.
        setStrokes((prev) => [...prev, [{ x, y, pressure: e.pressure || null, t: prev.length === 0 ? 0 : performance.now() }]]);
        e.currentTarget.setPointerCapture(e.pointerId);
      }
    },
    [bbox, stepId, wegTool, strokes, cssToChart, panning, panX, panY, setStrokes],
  );

  const onSvgPointerMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
      if (panDrag) {
        setPanX(clampPan(panDrag.px + (e.clientX - panDrag.sx), displayW, hostSize.w));
        setPanY(clampPan(panDrag.py + (e.clientY - panDrag.sy), displayH, hostSize.h));
        return;
      }
      const { x, y } = cssToChart(e.clientX, e.clientY, e.currentTarget);
      if (stepId === 'mask' || (stepId === 'weg' && wegTool === 'adjust')) setHoverPt({ x, y });
      if (nudge) {
        setStrokes(warpStrokes(nudge.snapshot, nudge.x, nudge.y, x - nudge.x, y - nudge.y, nudgeRadius));
        return;
      }
      if (calibDrag) {
        setCalibDrag({ ...calibDrag, curY: Math.round(y) });
        return;
      }
      if (slantDrag) {
        setSlantDrag({ ...slantDrag, curX: x });
        return;
      }
      if (stepId === 'mask' && maskDraft) {
        const last = maskDraft[maskDraft.length - 1];
        if (last && (x - last[0]) ** 2 + (y - last[1]) ** 2 < 1) return;
        setMaskDraft([...maskDraft, [x, y]]);
        return;
      }
      if (stepId === 'weg' && drawing) {
        setStrokes((prev) => {
          if (prev.length === 0) return prev;
          const stroke = prev[prev.length - 1];
          const last = stroke[stroke.length - 1];
          if (last && (x - last.x) ** 2 + (y - last.y) ** 2 < 0.36) return prev;
          const extended = [...stroke, { x, y, pressure: e.pressure || null, t: performance.now() }];
          return [...prev.slice(0, -1), extended];
        });
      }
    },
    [bbox, calibDrag, slantDrag, nudge, nudgeRadius, wegTool, stepId, maskDraft, drawing, cssToChart, panDrag, displayW, displayH, hostSize, setPanX, setPanY, setStrokes],
  );

  const onSvgPointerUp = useCallback(async () => {
    if (panDrag) {
      setPanDrag(null);
      return;
    }
    if (nudge) {
      // The warped strokes are already live in `strokes`; just end the gesture.
      setNudge(null);
      return;
    }
    if (calibDrag) {
      const { field, curY } = calibDrag;
      setCalibDrag(null);
      await commitCalib(field, curY);
      return;
    }
    if (slantDrag) {
      const { index, curX } = slantDrag;
      setSlantDrag(null);
      await commitSlant(index, curX);
      return;
    }
    if (stepId === 'mask' && maskDraft) {
      const points = maskDraft;
      setMaskDraft(null);
      await (tool === 'ink' ? commitInkStroke : commitMaskStroke)(points);
      return;
    }
    if (stepId === 'weg') setDrawing(false);
  }, [panDrag, calibDrag, slantDrag, nudge, stepId, maskDraft, tool, commitCalib, commitSlant, commitMaskStroke, commitInkStroke]);

  // ------------------------------------------------------------- geometry (css)
  const baselineCss = (bbox.baseline_y - bbox.y0) * scale;
  const midbandCss = (bbox.midband_y - bbox.y0) * scale;
  const xHeightPx = bbox.baseline_y - bbox.midband_y;
  const [aR, xR, dR] = source.style_ratio;
  const ascenderCss = (bbox.midband_y - (aR / xR) * xHeightPx - bbox.y0) * scale;
  const descenderCss = (bbox.baseline_y + (dR / xR) * xHeightPx - bbox.y0) * scale;
  const dragCss = calibDrag ? (calibDrag.curY - bbox.y0) * scale : null;

  const tanSlant = Math.tan(((90 - guideVals.slantDeg) * Math.PI) / 180);
  const slantLineCss = (xBase: number) => ({
    x1: (xBase + tanSlant * (bbox.baseline_y - bbox.y0) - bbox.x0) * scale,
    y1: 0,
    x2: (xBase + tanSlant * (bbox.baseline_y - bbox.y1) - bbox.x0) * scale,
    y2: displayH,
  });
  // Live positions: the dragged line follows the pointer; the rest stay put.
  const slantXsLive = slantDrag
    ? guideVals.slantXs.map((x, i) => (i === slantDrag.index ? slantDrag.curX : x))
    : guideVals.slantXs;

  const toLocal = (pts: Array<[number, number]>) =>
    pts.map(([x, y]) => `${(x - bbox.x0) * scale},${(y - bbox.y0) * scale}`).join(' ');

  // Render one committed brush stroke (eraser or ink). A single-point stroke is
  // a tap/dab — it bakes into the crop as a disc but a 1-point <polyline> draws
  // nothing, so it gets a <circle> instead (otherwise taps show no overlay).
  const renderStroke = (m: { points: Array<[number, number]>; radius: number }, key: string, color: string) => {
    if (m.points.length >= 2) {
      return (
        <polyline
          key={key}
          points={toLocal(m.points)}
          fill="none"
          stroke={color}
          strokeOpacity={0.55}
          strokeWidth={Math.max(1, m.radius * 2 * scale)}
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ pointerEvents: 'none' }}
        />
      );
    }
    const p = m.points[0];
    if (!p) return null;
    return (
      <circle key={key} cx={(p[0] - bbox.x0) * scale} cy={(p[1] - bbox.y0) * scale} r={Math.max(0.5, m.radius * scale)} fill={color} fillOpacity={0.55} style={{ pointerEvents: 'none' }} />
    );
  };

  return (
    <Box ref={hostRef} sx={{ flex: 1, minHeight: 0, position: 'relative', bgcolor: overlay.canvasBg, overflow: 'hidden' }}>
      {displayW > 0 && (
        <Box
          sx={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            width: displayW,
            height: displayH,
            transform: `translate(-50%, -50%) translate(${panX}px, ${panY}px)`,
          }}
        >
          <img
            src={cropUrl(source.id, glyphKey, cropCacheBust, stepId === 'mask' && showMask ? 'mask' : undefined)}
            alt={known.label}
            width={displayW}
            height={displayH}
            draggable={false}
            style={{ display: 'block', imageRendering: 'pixelated', pointerEvents: 'none' }}
          />
          <svg
            width={displayW}
            height={displayH}
            style={{
              position: 'absolute',
              inset: 0,
              touchAction: 'none',
              cursor: panning
                ? panDrag
                  ? 'grabbing'
                  : 'grab'
                : stepId === 'weg' && wegTool === 'adjust'
                  ? nudge
                    ? 'grabbing'
                    : 'grab'
                  : stepId === 'mask' || stepId === 'weg'
                    ? 'crosshair'
                    : 'default',
            }}
            onPointerDown={onSvgPointerDown}
            onPointerMove={onSvgPointerMove}
            onPointerUp={onSvgPointerUp}
            onPointerCancel={() => {
              setPanDrag(null);
              setCalibDrag(null);
              setSlantDrag(null);
              setNudge(null);
              setMaskDraft(null);
              setHoverPt(null);
              setDrawing(false);
            }}
            // Hide the brush/nudge ring when the pointer leaves the crop — but not
            // mid-gesture (capture keeps it alive past the edge).
            onPointerLeave={() => {
              if (!maskDraft && !nudge) setHoverPt(null);
            }}
          >
            {/* Lineature guides — hidden on the Ausschluss step (the eraser works
                on the bare crop; the lines first appear on their own step) and
                read-only except on that step */}
            {stepId !== 'mask' && (
              <>
                {guideVals.showAscender && ascenderCss >= 0 && ascenderCss <= displayH && (
                  <line x1={0} y1={ascenderCss} x2={displayW} y2={ascenderCss} stroke="#bbb" strokeWidth={1.5} strokeDasharray="2 4" opacity={0.9} style={{ filter: GUIDE_SHADOW }} />
                )}
                {guideVals.showDescender && descenderCss >= 0 && descenderCss <= displayH && (
                  <line x1={0} y1={descenderCss} x2={displayW} y2={descenderCss} stroke="#bbb" strokeWidth={1.5} strokeDasharray="2 4" opacity={0.9} style={{ filter: GUIDE_SHADOW }} />
                )}
                <g>
                  {stepId === 'lineatur' && (
                    <line
                      x1={0}
                      y1={baselineCss}
                      x2={displayW}
                      y2={baselineCss}
                      stroke="transparent"
                      strokeWidth={22}
                      style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                      onPointerDown={(e) => {
                        if (panning) return; // let the drag bubble to the SVG → pan
                        e.stopPropagation();
                        setCalibDrag({ field: 'baseline_y', curY: bbox.baseline_y });
                        e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                      }}
                    />
                  )}
                  <line x1={0} y1={baselineCss} x2={displayW} y2={baselineCss} stroke="#ff5060" strokeWidth={2.25} strokeDasharray="6 4" style={{ pointerEvents: 'none', filter: GUIDE_SHADOW }} />
                </g>
                <g>
                  {stepId === 'lineatur' && (
                    <line
                      x1={0}
                      y1={midbandCss}
                      x2={displayW}
                      y2={midbandCss}
                      stroke="transparent"
                      strokeWidth={22}
                      style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                      onPointerDown={(e) => {
                        if (panning) return; // let the drag bubble to the SVG → pan
                        e.stopPropagation();
                        setCalibDrag({ field: 'midband_y', curY: bbox.midband_y });
                        e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                      }}
                    />
                  )}
                  <line x1={0} y1={midbandCss} x2={displayW} y2={midbandCss} stroke="#c060ff" strokeWidth={2.25} strokeDasharray="3 3" style={{ pointerEvents: 'none', filter: GUIDE_SHADOW }} />
                </g>
                {dragCss != null && (
                  <line x1={0} y1={dragCss} x2={displayW} y2={dragCss} stroke={calibDrag?.field === 'baseline_y' ? '#ff5060' : '#c060ff'} strokeWidth={2} opacity={0.6} style={{ pointerEvents: 'none' }} />
                )}
              </>
            )}

            {/* Slant guide(s) — one or more parallel lines, each draggable on the slant step */}
            {(stepId === 'slant' || stepId === 'weg') &&
              slantXsLive.map((xb, i) => {
                const ln = slantLineCss(xb);
                const dragging = slantDrag?.index === i;
                return (
                  <line
                    key={i}
                    x1={ln.x1}
                    y1={ln.y1}
                    x2={ln.x2}
                    y2={ln.y2}
                    stroke={SLANT_COLOR}
                    strokeWidth={dragging ? 2.5 : 2}
                    strokeDasharray="5 4"
                    opacity={dragging ? 0.7 : 0.95}
                    style={{ pointerEvents: 'none', filter: GUIDE_SHADOW }}
                  />
                );
              })}
            {stepId === 'slant' &&
              slantXsLive.map((xb, i) => (
                <circle
                  key={i}
                  cx={(xb - bbox.x0) * scale}
                  cy={baselineCss}
                  r={8}
                  fill={SLANT_COLOR}
                  stroke="#0a2a14"
                  strokeWidth={1}
                  style={{ cursor: 'ew-resize' }}
                  onPointerDown={(e) => {
                    if (panning) return; // let the drag bubble to the SVG → pan
                    e.stopPropagation();
                    setSlantDrag({ index: i, curX: guideVals.slantXs[i] });
                    e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                  }}
                />
              ))}

            {/* Eraser strokes (Radierer) — committed; taps render as discs */}
            {bbox.mask_strokes.map((m, i) => renderStroke(m, `m${i}`, overlay.eraser))}
            {/* Ink strokes (Tinte) — committed */}
            {bbox.ink_strokes.map((m, i) => renderStroke(m, `ink-${i}`, overlay.ink))}
            {/* In-progress brush stroke — coloured by the active tool */}
            {maskDraft && <polyline points={toLocal(maskDraft)} fill="none" stroke={tool === 'ink' ? overlay.ink : overlay.eraser} strokeOpacity={0.8} strokeWidth={Math.max(1, maskRadius * 2 * scale)} strokeLinecap="round" strokeLinejoin="round" style={{ pointerEvents: 'none' }} />}
            {/* Brush cursor: a ring at the pointer sized to the real footprint
                (radius in chart px → CSS px via scale), coloured by the tool. */}
            {stepId === 'mask' && !panning && hoverPt && (
              <circle
                cx={(hoverPt.x - bbox.x0) * scale}
                cy={(hoverPt.y - bbox.y0) * scale}
                r={maskRadius * scale}
                fill={tool === 'ink' ? overlay.ink : overlay.eraser}
                fillOpacity={0.12}
                stroke={tool === 'ink' ? overlay.ink : overlay.eraser}
                strokeOpacity={0.9}
                strokeWidth={1}
                style={{ pointerEvents: 'none' }}
              />
            )}

            {/* Nudge ring: the warp footprint on the Weg "Anpassen" tool — points
                inside follow the drag, easing back to the line at the rim. */}
            {stepId === 'weg' && wegTool === 'adjust' && !panning && hoverPt && (
              <circle
                cx={(hoverPt.x - bbox.x0) * scale}
                cy={(hoverPt.y - bbox.y0) * scale}
                r={nudgeRadius * scale}
                fill={overlay.draft}
                fillOpacity={0.1}
                stroke={overlay.draft}
                strokeOpacity={0.9}
                strokeWidth={1}
                style={{ pointerEvents: 'none' }}
              />
            )}

            {/* Saved Weg + anchors (faint reference, toggleable): the committed
                canonical under the in-progress draft. The raw path is in chart
                coordinates, the anchors in crop-local pixels. */}
            {stepId === 'weg' && showSaved && savedTrace && (
              <g style={{ pointerEvents: 'none' }}>
                {splitRawPath(savedTrace.rawPath).map((stroke, i) => (
                  <polyline
                    key={`saved-${i}`}
                    points={stroke.map((p) => `${(p.x - bbox.x0) * scale},${(p.y - bbox.y0) * scale}`).join(' ')}
                    fill="none"
                    stroke={overlay.locked}
                    strokeOpacity={0.4}
                    strokeWidth={2}
                  />
                ))}
                {savedTrace.anchorsPx.map(([x, y], i) => (
                  <circle key={`anchor-${i}`} cx={x * scale} cy={y * scale} r={2.5} fill={overlay.active} fillOpacity={0.75} />
                ))}
              </g>
            )}

            {/* Trace draft — one polyline + start dot per stroke; pen lifts stay gaps */}
            {strokes.map((stroke, i) =>
              stroke.length > 1 ? (
                <polyline
                  key={`stroke-${i}`}
                  points={stroke.map((p) => `${(p.x - bbox.x0) * scale},${(p.y - bbox.y0) * scale}`).join(' ')}
                  fill="none"
                  stroke={overlay.draft}
                  strokeWidth={2}
                  style={{ pointerEvents: 'none' }}
                />
              ) : null,
            )}
            {strokes.map((stroke, i) =>
              stroke.length > 0 ? (
                <circle
                  key={`start-${i}`}
                  cx={(stroke[0].x - bbox.x0) * scale}
                  cy={(stroke[0].y - bbox.y0) * scale}
                  r={4}
                  fill="#fff"
                  stroke={overlay.draft}
                  style={{ pointerEvents: 'none' }}
                />
              ) : null,
            )}
          </svg>
        </Box>
      )}
      {/* Floating zoom controls — Schwenken toggle · −/Slider/+ · Anpassen (fit) */}
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 0.25,
          px: 0.5,
          py: 0.25,
          borderRadius: 1,
          bgcolor: 'rgba(20, 20, 20, 0.78)',
        }}
      >
        <Tooltip title={de.wizard.canvas.panTooltip}>
          <IconButton
            size="small"
            onClick={() => setPanning((p) => !p)}
            sx={{ color: panning ? SLANT_COLOR : '#bbb' }}
            aria-label={de.wizard.canvas.pan}
            aria-pressed={panning}
          >
            <OpenWithIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <IconButton size="small" onClick={() => zoomBy(1 / 1.3)} sx={{ color: '#bbb' }} aria-label={de.wizard.canvas.zoomOut}>
          <RemoveIcon fontSize="small" />
        </IconButton>
        <Slider
          size="small"
          sx={{ width: 84, color: '#ccc' }}
          min={ZOOM_MIN}
          max={ZOOM_MAX}
          step={0.05}
          value={userZoom}
          onChange={(_e, v) => typeof v === 'number' && applyZoom(v)}
        />
        <IconButton size="small" onClick={() => zoomBy(1.3)} sx={{ color: '#bbb' }} aria-label={de.wizard.canvas.zoomIn}>
          <AddIcon fontSize="small" />
        </IconButton>
        <Tooltip title={de.wizard.canvas.fitTooltip}>
          <IconButton size="small" onClick={fitZoom} sx={{ color: '#bbb' }} aria-label={de.wizard.canvas.fit}>
            <CenterFocusStrongIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Typography variant="caption" sx={{ color: '#bbb', minWidth: 32, textAlign: 'right' }}>
          {Math.round(userZoom * 100)}%
        </Typography>
      </Box>
    </Box>
  );
}
