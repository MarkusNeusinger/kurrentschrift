import { Box } from '@mui/material';
import { useMemo } from 'react';

import { A4, DRAW_ORDER, ROLE_STYLES, type LineRole, type RoleStyle, type Segment, type TextMark } from '@/lib/lineatur';

export function PreviewSvg({
  segments,
  marks,
  footerLeft,
  footerRight,
  // Ruling colour scheme; pass the same map to lineaturePdf so preview and
  // print never diverge (defaults to the standard print look).
  styles = ROLE_STYLES,
}: {
  segments: Segment[];
  marks: TextMark[];
  footerLeft: string;
  footerRight: string;
  styles?: Record<LineRole, RoleStyle>;
}) {
  // Paint in the same role order the PDF uses, so crossings look identical in
  // preview and print (stable sort keeps per-row order within a role).
  const ordered = useMemo(
    () => [...segments].sort((a, b) => DRAW_ORDER.indexOf(a.role) - DRAW_ORDER.indexOf(b.role)),
    [segments],
  );
  return (
    <Box
      component="svg"
      viewBox={`0 0 ${A4.widthMm} ${A4.heightMm}`}
      sx={{
        width: '100%',
        maxWidth: 480,
        height: 'auto',
        display: 'block',
        bgcolor: '#FFFFFF',
        boxShadow: '0 1px 6px rgba(0,0,0,0.12)',
      }}
    >
      <rect x={0} y={0} width={A4.widthMm} height={A4.heightMm} fill="#FFFFFF" stroke="none" />
      {ordered.map((s, i) => {
        const st = styles[s.role];
        return (
          <line
            key={i}
            x1={s.x1}
            y1={s.y1}
            x2={s.x2}
            y2={s.y2}
            stroke={st.color}
            strokeWidth={st.widthMm}
            strokeLinecap="round"
            strokeDasharray={st.dash ? `${st.dash[0]} ${st.dash[1]}` : undefined}
          />
        );
      })}
      {marks.map((m, i) => (
        <text
          key={`m${i}`}
          x={m.x}
          y={m.y}
          fontSize={m.sizeMm}
          fill={m.color ?? '#6B6A63'}
          fontFamily="sans-serif"
        >
          {m.text}
        </text>
      ))}
      {footerLeft.trim() && (
        <text x={12} y={A4.heightMm - 9} fontSize={3.2} fill="#6B6A63" fontFamily="sans-serif">
          {footerLeft}
        </text>
      )}
      {footerRight.trim() && (
        <text
          x={A4.widthMm - 12}
          y={A4.heightMm - 9}
          fontSize={3.2}
          fill="#6B6A63"
          fontFamily="sans-serif"
          textAnchor="end"
        >
          {footerRight}
        </text>
      )}
    </Box>
  );
}
