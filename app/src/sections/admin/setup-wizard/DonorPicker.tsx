// Donor picker for "Zelle einsetzen": shows the full chart and lets the user
// rubber-band a rectangle around the ink to copy into the crop (e.g. the two
// umlaut strokes over the ä). Returns the selection as chart-pixel coords
// [x0, y0, x1, y1]; the wizard then composites it into the crop as a patch.
//
// The chart fits the dialog width; the SVG overlay uses viewBox="0 0 W H" so the
// selection rect is drawn directly in chart pixels, and the pointer is mapped to
// chart pixels via the image's bounding rect (scale-independent).

import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from '@mui/material';
import { useCallback, useRef, useState } from 'react';

import { chartUrl } from '@/lib/api';
import { de } from '@/locales';
import { overlay } from '@/sections/admin/overlayColors';

const MIN_SIZE = 4; // chart px: reject an accidental dot

type Sel = { x0: number; y0: number; x1: number; y1: number };

export function DonorPicker({
  open,
  onClose,
  onConfirm,
  sourceId,
  chartW,
  chartH,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (src: [number, number, number, number]) => void;
  sourceId: string;
  chartW: number;
  chartH: number;
}) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [drag, setDrag] = useState<{ sx: number; sy: number } | null>(null);
  const [sel, setSel] = useState<Sel | null>(null);

  // Pointer → chart-pixel coords via the rendered image's bounding rect, clamped
  // to the chart (works at any display scale and scroll offset).
  const toChart = useCallback(
    (clientX: number, clientY: number): [number, number] => {
      const r = imgRef.current?.getBoundingClientRect();
      if (!r || r.width === 0 || r.height === 0) return [0, 0];
      const x = ((clientX - r.left) / r.width) * chartW;
      const y = ((clientY - r.top) / r.height) * chartH;
      return [Math.max(0, Math.min(chartW, x)), Math.max(0, Math.min(chartH, y))];
    },
    [chartW, chartH],
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      const [x, y] = toChart(e.clientX, e.clientY);
      setDrag({ sx: x, sy: y });
      setSel({ x0: x, y0: y, x1: x, y1: y });
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [toChart],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!drag) return;
      const [x, y] = toChart(e.clientX, e.clientY);
      setSel({
        x0: Math.min(drag.sx, x),
        y0: Math.min(drag.sy, y),
        x1: Math.max(drag.sx, x),
        y1: Math.max(drag.sy, y),
      });
    },
    [drag, toChart],
  );

  const onPointerUp = useCallback(() => setDrag(null), []);

  const valid = sel != null && sel.x1 - sel.x0 >= MIN_SIZE && sel.y1 - sel.y0 >= MIN_SIZE;

  const reset = () => {
    setDrag(null);
    setSel(null);
  };

  const confirm = () => {
    if (!sel || !valid) return;
    onConfirm([Math.round(sel.x0), Math.round(sel.y0), Math.round(sel.x1), Math.round(sel.y1)]);
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="lg">
      <DialogTitle>{de.wizard.donor.title}</DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {de.wizard.donor.help}
        </Typography>
        <Box sx={{ maxHeight: '64vh', overflow: 'auto', bgcolor: overlay.canvasBg, borderRadius: 1 }}>
          <Box sx={{ position: 'relative', width: '100%' }}>
            <img
              ref={imgRef}
              src={chartUrl(sourceId)}
              alt={de.wizard.donor.title}
              draggable={false}
              style={{ display: 'block', width: '100%', height: 'auto', userSelect: 'none' }}
            />
            <svg
              viewBox={`0 0 ${chartW} ${chartH}`}
              preserveAspectRatio="none"
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', touchAction: 'none', cursor: 'crosshair' }}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
            >
              {sel && (
                <rect
                  x={sel.x0}
                  y={sel.y0}
                  width={sel.x1 - sel.x0}
                  height={sel.y1 - sel.y0}
                  fill={overlay.patch}
                  fillOpacity={0.18}
                  stroke={overlay.patch}
                  strokeWidth={2}
                  vectorEffect="non-scaling-stroke"
                />
              )}
            </svg>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={reset} disabled={!sel}>
          {de.wizard.donor.redraw}
        </Button>
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>{de.wizard.donor.cancel}</Button>
        <Button variant="contained" onClick={confirm} disabled={!valid}>
          {de.wizard.donor.confirm}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
