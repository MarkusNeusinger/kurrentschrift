// 3-column diagnostic SVG: Crop pur | Crop + skeleton + anchors | Canonical template.
//
// Backend (`core.pipeline.diagnostic_for_glyph`) does the heavy lifting:
// skeleton extraction, slant-shear, outline polygon construction. Frontend
// just renders polylines and polygons from the JSON arrays.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';

import { cropUrl, getDiagnostic } from '@/lib/api';
import type { DiagnosticData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales';
import { useColumnWidth } from '@/sections/admin/diagnostics/useColumnWidth';

interface Props {
  glyphKey: string;
  cropCacheBust?: number;
  // Override the responsive default column width (e.g. the Diagnose modal wants
  // big columns); still clamped to the viewport so it never overflows a phone.
  colWidth?: number;
  // Height of each column box; defaults to COL_H but the big modal goes taller.
  colHeight?: number;
  // Surfaces the fetched payload so the caller can reuse it (the Diagnose
  // dialog hands it to WrittenGlyph instead of fetching the same data twice).
  onData?: (data: DiagnosticData) => void;
}

const COL_H = 360;

export function DiagnosticView({ glyphKey, cropCacheBust, colWidth, colHeight, onData }: Props) {
  const COL_W = useColumnWidth(colWidth);
  const COL_H_PX = colHeight ?? COL_H;
  const [data, setData] = useState<DiagnosticData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onDataRef = useRef(onData);
  onDataRef.current = onData;

  const fetch = useCallback(() => {
    setLoading(true);
    setError(null);
    getDiagnostic(glyphKey)
      .then((d) => {
        setData(d);
        onDataRef.current?.(d);
      })
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
          {de.admin.diagnostics.computing}
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity={error.includes('404') ? 'info' : 'error'}>
          {error.includes('404') ? de.admin.diagnostics.noCanonicalShort : error}
        </Alert>
        <Button size="small" startIcon={<RefreshIcon />} onClick={fetch} sx={{ mt: 1 }}>
          {de.admin.diagnostics.reload}
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
  // Template x has its origin at the ductus' FIRST sample (pipeline x_origin),
  // so a glyph drawn from the right (e.g. K) lies entirely in negative x — span
  // the real anchor extent instead of assuming [0, advance].
  const tpl = data.template_guides;
  const tplXs = data.anchors_template.map((a) => a[0]);
  const tplX0 = (tplXs.length ? Math.min(0, ...tplXs) : 0) - 0.5;
  const tplX1 = (tplXs.length ? Math.max(0.5, ...tplXs) : 0.5) + 0.5;
  const tplViewH = tpl.ascender - tpl.descender;
  const tplViewBox = `${tplX0} ${-tpl.ascender - 0.3} ${tplX1 - tplX0} ${tplViewH + 0.6}`;

  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      {/* Column 1 — Crop pur */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: Math.max(cropDisplayW, 180) }}>
        <Typography variant="caption" color="text.secondary">
          {de.admin.diagnostics.cropHeading}
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
        <Typography variant="caption" color="text.disabled">
          {de.admin.diagnostics.cropCaption}
        </Typography>
      </Box>

      {/* Column 2 — Crop + skeleton + anchors */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: Math.max(cropDisplayW, 180) }}>
        <Typography variant="caption" color="text.secondary">
          {de.admin.diagnostics.skeletonHeading} ({data.anchors_px.length})
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
            {/* corner knots (Umkehrpunkte) — diamonds where the spline splits */}
            {(data.corner_anchors ?? []).map((ci) => {
              const a = data.anchors_px[ci];
              if (!a) return null;
              const [x, y] = a;
              return (
                <rect
                  key={`corner-${ci}`}
                  x={x - 3}
                  y={y - 3}
                  width={6}
                  height={6}
                  transform={`rotate(45 ${x} ${y})`}
                  fill="#00b8d4"
                  stroke="#fff"
                  strokeWidth={0.6}
                />
              );
            })}
          </svg>
        </Box>
        <Typography variant="caption" color="text.disabled">
          {de.admin.diagnostics.skeletonCaption}
        </Typography>
      </Box>

      {/* Column 3 — Canonical template */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, maxWidth: Math.max(COL_W, 180) }}>
        <Typography variant="caption" color="text.secondary">
          {de.admin.diagnostics.canonicalHeading} {data.slant_deg}°)
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
              <line x1={tplX0} y1={tpl.baseline} x2={tplX1} y2={tpl.baseline} stroke="#bbb" strokeWidth={0.015} />
              <line x1={tplX0} y1={tpl.midband} x2={tplX1} y2={tpl.midband} stroke="#ddd" strokeWidth={0.015} strokeDasharray="0.08 0.06" />
              <line x1={tplX0} y1={tpl.ascender} x2={tplX1} y2={tpl.ascender} stroke="#eee" strokeWidth={0.015} strokeDasharray="0.04 0.05" />
              <line x1={tplX0} y1={tpl.descender} x2={tplX1} y2={tpl.descender} stroke="#eee" strokeWidth={0.015} strokeDasharray="0.04 0.05" />
              {/* Filled silhouette — capsule-union rings per pen-stroke (holes
                  stay open via evenodd); legacy ribbon polygons as fallback. */}
              {data.outline_paths?.length
                ? data.outline_paths.map((rings, i) => (
                    <path key={i} d={ringsToPathD(rings)} fill="#111" fillRule="evenodd" />
                  ))
                : (data.outline_polygons ?? (data.outline_polygon.length > 2 ? [data.outline_polygon] : [])).map(
                    (poly, i) =>
                      poly.length > 2 ? (
                        <polygon key={i} points={poly.map(([x, y]) => `${x},${y}`).join(' ')} fill="#111" />
                      ) : null,
                  )}
              {/* Anchor dots */}
              {data.anchors_template.map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r={0.025} fill="#ffae00" />
              ))}
              {/* corner knots — same diamonds as the skeleton column */}
              {(data.corner_anchors ?? []).map((ci) => {
                const a = data.anchors_template[ci];
                if (!a) return null;
                const [x, y] = a;
                return (
                  <rect
                    key={`corner-${ci}`}
                    x={x - 0.035}
                    y={y - 0.035}
                    width={0.07}
                    height={0.07}
                    transform={`rotate(45 ${x} ${y})`}
                    fill="#00b8d4"
                  />
                );
              })}
            </g>
          </svg>
        </Box>
        <Typography variant="caption" color="text.disabled">
          {de.admin.diagnostics.canonicalCaption}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace' }}>
          {fmt(de.admin.diagnostics.guidesReadout, { ascender: tpl.ascender.toFixed(2), descender: tpl.descender.toFixed(2) })}
        </Typography>
      </Box>
    </Box>
  );
}
