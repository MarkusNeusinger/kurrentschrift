// „Flecken radieren" — the round brush over one written strip.
//
// The author's laser drops toner specks into the right part of the page; the
// import finds the obvious ones, and everything it deliberately does NOT touch
// (anything near the writing — a comma, an i-dot, a blot from his own nib) is
// what this brush is for. Both halves write the same thing: a list of circles
// in the strip's own millimetres.
//
// What it never does is change a pixel. The strip is the reserved dataset's
// primary evidence, so the mask is DATA and the server paints local paper into
// the circles on read (`core/eigenhand/crop.py::without_flecken`, the
// two-channel doctrine). That is also why removing a circle is as cheap as
// setting one, and why „roh" can always show what was actually captured — the
// bytes are still there, whole.
//
// One click, two meanings: on empty paper it adds a circle, on an existing one
// it takes that circle away (an automatic one included — a detector finding is
// a proposal). „Rückgängig" walks back step by step, „Speichern" replaces the
// stored list in full.

import {
  Alert,
  Box,
  Button,
  Chip,
  FormControlLabel,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useRef, useState } from 'react';

import { patchEigenhandFlecken } from '@/lib/api';
import type { EigenhandFleck } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { BRUSH_RADII_MM, displayScale, insideStrip, pointAt, toggleAt } from '@/sections/admin/eigenhand/flecken';
import type { BrushRadiusMm, PointMm } from '@/sections/admin/eigenhand/flecken';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { paper } from '@/styles/paper';

/**
 * The zoom the eraser needs. The brush is not a control but a pen tip, and it
 * still has to be AIMABLE: at ¼ the smallest brush is under a display pixel
 * across, at 2× on a 300-dpi strip it is ~14 px. Entering the mode lifts the
 * shared zoom to here rather than growing the brush, because the brush's size
 * is a millimetre fact about the paper and must not bend to the screen.
 */
export const MIN_ERASE_ZOOM = 2;

// Every control keeps the design system's 44 px hit target; MUI's `size=small`
// would otherwise come out at 30.
const HIT_TARGET = { minHeight: '2.75rem' };

export function FleckenEditor({
  hand,
  strip,
  fassung,
  url,
  widthPx,
  heightPx,
  dpi,
  zoom,
  initial,
  roh,
  onRoh,
  onClose,
  onSaved,
}: {
  hand: string;
  strip: string;
  fassung: string;
  url: string | null;
  widthPx: number;
  heightPx: number;
  dpi: number;
  zoom: number;
  initial: EigenhandFleck[];
  roh: boolean;
  onRoh: (next: boolean) => void;
  onClose: () => void;
  onSaved: (circles: EigenhandFleck[]) => void;
}) {
  const t = de.admin.eigenhand;
  const [circles, setCircles] = useState<EigenhandFleck[]>(initial);
  const [history, setHistory] = useState<EigenhandFleck[][]>([]);
  const [brush, setBrush] = useState<BrushRadiusMm>(BRUSH_RADII_MM[1]);
  const [cursor, setCursor] = useState<PointMm | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<ApiErrorText | null>(null);
  const surface = useRef<HTMLDivElement | null>(null);

  const scale = displayScale(dpi, zoom);
  const widthMm = widthPx / (dpi / 25.4);
  const heightMm = heightPx / (dpi / 25.4);
  const dirty = history.length > 0;

  // The pointer in the strip's own millimetres. Measured against the surface's
  // rectangle rather than the event target, so a click on the image and a
  // click on the overlay land at the same millimetre.
  //
  // Nothing lands while the image is still loading (or failed to): the surface
  // takes its full size from the strip's pixel dimensions either way, so a
  // click on blank paper would place a circle over ink the author never saw.
  const at = (event: { clientX: number; clientY: number }): PointMm | null => {
    const rect = surface.current?.getBoundingClientRect();
    if (!rect || !url) return null;
    const point = pointAt(event.clientX - rect.left, event.clientY - rect.top, scale);
    return insideStrip(point, widthMm, heightMm) ? point : null;
  };

  const step = (next: EigenhandFleck[]) => {
    setHistory([...history, circles]);
    setCircles(next);
    setSaved(false);
  };

  const undo = () => {
    if (!history.length) return;
    setCircles(history[history.length - 1]);
    setHistory(history.slice(0, -1));
    setSaved(false);
  };

  const save = () => {
    setSaving(true);
    setError(null);
    patchEigenhandFlecken(hand, strip, fassung, circles)
      .then((res) => {
        setCircles(res.flecken);
        setHistory([]);
        setSaved(true);
        onSaved(res.flecken);
      })
      .catch((err: unknown) => setError(apiErrorText(err)))
      .finally(() => setSaving(false));
  };

  return (
    <Box sx={{ mt: 1 }}>
      <Stack
        direction="row"
        spacing={1}
        sx={{ mb: 1, flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}
        role="toolbar"
        aria-label={t.fleckenTitle}
      >
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {t.fleckenBrush}
        </Typography>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={brush}
          aria-label={t.fleckenBrush}
          onChange={(_e, value: BrushRadiusMm | null) => value && setBrush(value)}
        >
          {BRUSH_RADII_MM.map((radius) => (
            <ToggleButton key={radius} value={radius} sx={{ px: 1.5, ...HIT_TARGET, textTransform: 'none' }}>
              {fmt(t.fleckenBrushSize, { mm: radius.toFixed(1) })}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <Chip size="small" variant="outlined" label={fmt(t.fleckenCount, { count: circles.length })} />
        <Button size="small" onClick={undo} disabled={!dirty} sx={HIT_TARGET}>
          {t.fleckenUndo}
        </Button>
        <Tooltip title={t.fleckenRawHint}>
          <FormControlLabel
            control={<Switch size="small" checked={roh} onChange={(e) => onRoh(e.target.checked)} />}
            label={<Typography variant="caption">{t.fleckenRaw}</Typography>}
            sx={{ mr: 0 }}
          />
        </Tooltip>
        <Box sx={{ flexGrow: 1 }} />
        <Button size="small" variant="contained" onClick={save} disabled={saving || !dirty} sx={HIT_TARGET}>
          {t.fleckenSave}
        </Button>
        <Button size="small" onClick={onClose} sx={HIT_TARGET}>
          {t.fleckenClose}
        </Button>
      </Stack>

      <Typography variant="caption" sx={{ display: 'block', mb: 1, color: paper.inkSoft }}>
        {t.fleckenHint}
      </Typography>

      <Box sx={{ overflowX: 'auto', bgcolor: paper.hi, borderRadius: 1 }}>
        <Box
          ref={surface}
          onPointerMove={(event) => setCursor(at(event))}
          onPointerLeave={() => setCursor(null)}
          onClick={(event) => {
            const point = at(event);
            if (point) step(toggleAt(circles, point, brush));
          }}
          sx={{
            position: 'relative',
            width: `${widthPx * zoom}px`,
            height: `${heightPx * zoom}px`,
            cursor: url ? 'crosshair' : 'progress',
            opacity: url ? 1 : 0.5,
            touchAction: 'none',
          }}
        >
          {url && (
            <Box
              component="img"
              src={url}
              alt={`${strip} · ${fassung}`}
              sx={{ display: 'block', width: '100%', height: '100%', maxWidth: 'none' }}
            />
          )}
          {/* Millimetres all the way down: the overlay's viewBox IS the strip's
              mm rectangle, so a circle sits where the stored number says and
              the zoom never enters the data. */}
          <Box
            component="svg"
            viewBox={`0 0 ${widthMm} ${heightMm}`}
            preserveAspectRatio="none"
            aria-hidden
            sx={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
          >
            {circles.map((circle, index) => (
              <circle
                key={`${circle.x_mm}-${circle.y_mm}-${index}`}
                cx={circle.x_mm}
                cy={circle.y_mm}
                r={circle.r_mm}
                fill="none"
                stroke={circle.quelle === 'auto' ? paper.viridian : paper.sepia}
                strokeWidth={0.12}
                opacity={0.9}
              />
            ))}
            {cursor && (
              <circle
                cx={cursor.x_mm}
                cy={cursor.y_mm}
                r={brush}
                fill={paper.viridian}
                fillOpacity={0.25}
                stroke={paper.viridianText}
                strokeWidth={0.1}
              />
            )}
          </Box>
        </Box>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          <ErrorText error={error} prefix={t.fleckenSaveError} />
        </Alert>
      )}
      {saved && !dirty && (
        <Typography variant="caption" sx={{ display: 'block', mt: 1, color: paper.viridianText }}>
          {t.fleckenSaved}
        </Typography>
      )}
    </Box>
  );
}
