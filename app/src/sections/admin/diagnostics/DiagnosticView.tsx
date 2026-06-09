// 3-column diagnostic SVG: Crop pur | Crop + skeleton + anchors | Canonical template.
//
// Backend (`core.pipeline.diagnostic_for_glyph`) does the heavy lifting:
// skeleton extraction, slant-shear, outline polygon construction. Frontend
// just renders polylines and polygons from the JSON arrays.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { cropUrl, getDiagnostic } from '@/lib/api';
import type { DiagnosticData } from '@/lib/api';
import { useColumnWidth } from '@/sections/admin/diagnostics/useColumnWidth';

interface Props {
  glyphKey: string;
  cropCacheBust?: number;
  // Override the responsive default column width (e.g. the Diagnose modal wants
  // big columns); still clamped to the viewport so it never overflows a phone.
  colWidth?: number;
  // Height of each column box; defaults to COL_H but the big modal goes taller.
  colHeight?: number;
}

const COL_H = 360;

export function DiagnosticView({ glyphKey, cropCacheBust, colWidth, colHeight }: Props) {
  const COL_W = useColumnWidth(colWidth);
  const COL_H_PX = colHeight ?? COL_H;
  const [data, setData] = useState<DiagnosticData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(() => {
    setLoading(true);
    setError(null);
    getDiagnostic(glyphKey)
      .then((d) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [glyphKey]);

  useEffect(() => {
    fetch();
  }, [fetch, cropCacheBust]);

  if (loading && !data) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
        <CircularProgress size={16} />
        <Typography variant="caption" color="text.secondary">
          Diagnose wird gerechnet…
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity={error.includes('404') ? 'info' : 'error'}>
          {error.includes('404') ? 'noch kein Canonical — erst Strich aufnehmen' : error}
        </Alert>
        <Button size="small" startIcon={<RefreshIcon />} onClick={fetch} sx={{ mt: 1 }}>
          neu laden
        </Button>
      </Box>
    );
  }

  if (!data) return null;

  const cropW = data.crop_size.w;
  const cropH = data.crop_size.h;
  const cropScale = Math.min(COL_W / cropW, COL_H_PX / cropH);
  const cropDisplayW = cropW * cropScale;
  const cropDisplayH = cropH * cropScale;

  // Template-view viewBox: cover ascender..descender plus a bit of x-padding.
  const tpl = data.template_guides;
  const advance = data.anchors_template.length
    ? Math.max(0.5, ...data.anchors_template.map((a) => a[0])) - Math.min(0, ...data.anchors_template.map((a) => a[0]))
    : 1;
  const tplViewH = tpl.ascender - tpl.descender;
  const tplViewBox = `${-0.5} ${-tpl.ascender - 0.3} ${advance + 1.0} ${tplViewH + 0.6}`;

  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      {/* Column 1 — Crop pur */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Loth-Crop
        </Typography>
        <Box sx={{ width: cropDisplayW, height: cropDisplayH, bgcolor: '#fff' }}>
          <img
            src={cropUrl(glyphKey, cropCacheBust)}
            alt="crop"
            width={cropDisplayW}
            height={cropDisplayH}
            style={{ display: 'block' }}
          />
        </Box>
      </Box>

      {/* Column 2 — Crop + skeleton + anchors */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Skelett + Anker ({data.anchors_px.length})
        </Typography>
        <Box sx={{ position: 'relative', width: cropDisplayW, height: cropDisplayH, bgcolor: '#fff' }}>
          <img
            src={cropUrl(glyphKey, cropCacheBust)}
            alt="overlay"
            width={cropDisplayW}
            height={cropDisplayH}
            style={{ display: 'block', position: 'absolute', inset: 0, opacity: 0.35 }}
          />
          <svg width={cropDisplayW} height={cropDisplayH} viewBox={`0 0 ${cropW} ${cropH}`} style={{ position: 'absolute', inset: 0 }}>
            {/* baseline + midband */}
            <line x1={0} y1={data.baseline_y_crop} x2={cropW} y2={data.baseline_y_crop} stroke="#ff5060" strokeWidth={1} strokeDasharray="5 3" />
            <line x1={0} y1={data.midband_y_crop} x2={cropW} y2={data.midband_y_crop} stroke="#c060ff" strokeWidth={1} strokeDasharray="3 3" />
            {/* skeleton points */}
            {data.skeleton_polyline_px.map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r={0.6} fill="#ff3030" />
            ))}
            {/* anchor dots */}
            {data.anchors_px.map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r={2.2} fill="#ffae00" stroke="#fff" strokeWidth={0.6} />
            ))}
          </svg>
        </Box>
      </Box>

      {/* Column 3 — Canonical template */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Canonical (Template-Koords, Schräge {data.slant_deg}°)
        </Typography>
        <Box sx={{ width: COL_W, height: COL_H_PX, bgcolor: '#fff' }}>
          <svg
            width={COL_W}
            height={COL_H_PX}
            viewBox={tplViewBox}
            preserveAspectRatio="xMidYMid meet"
            style={{ display: 'block', background: '#fff' }}
          >
            {/* y is flipped in SVG; wrap in a group that flips Y around 0 */}
            <g transform="scale(1, -1)">
              {/* Guide lines */}
              <line x1={-0.5} y1={tpl.baseline} x2={advance + 0.5} y2={tpl.baseline} stroke="#bbb" strokeWidth={0.015} />
              <line x1={-0.5} y1={tpl.midband} x2={advance + 0.5} y2={tpl.midband} stroke="#ddd" strokeWidth={0.015} strokeDasharray="0.08 0.06" />
              <line x1={-0.5} y1={tpl.ascender} x2={advance + 0.5} y2={tpl.ascender} stroke="#eee" strokeWidth={0.015} strokeDasharray="0.04 0.05" />
              <line x1={-0.5} y1={tpl.descender} x2={advance + 0.5} y2={tpl.descender} stroke="#eee" strokeWidth={0.015} strokeDasharray="0.04 0.05" />
              {/* Outline polygons — one per pen-stroke (slant applied server-side),
                  so a pen lift is a real gap, not a bar bridging the strokes */}
              {(data.outline_polygons ?? (data.outline_polygon.length > 2 ? [data.outline_polygon] : [])).map((poly, i) =>
                poly.length > 2 ? (
                  <polygon key={i} points={poly.map(([x, y]) => `${x},${y}`).join(' ')} fill="#111" />
                ) : null,
              )}
              {/* Anchor dots */}
              {data.anchors_template.map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r={0.025} fill="#ffae00" />
              ))}
            </g>
          </svg>
        </Box>
        <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace' }}>
          Grundlinie=0 · Mittellinie=1 · Oberlinie={tpl.ascender.toFixed(2)} · Unterlinie={tpl.descender.toFixed(2)}
        </Typography>
      </Box>
    </Box>
  );
}
