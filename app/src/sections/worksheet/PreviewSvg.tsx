import { Box } from '@mui/material';
import { useMemo } from 'react';

import { A4, DRAW_ORDER, ROLE_STYLES, type LineRole, type RoleStyle, type Segment, type TextMark } from '@/lib/lineatur';
import type { InkShape } from '@/lib/pdf';
import type { RowMark } from '@/lib/uebungstext';
import { de, fmt } from '@/locales';
import { schulheft } from '@/styles/paper';

// Page millimetres to two decimals: a letter's silhouette has hundreds of
// vertices, and a sheet of Übungstext holds hundreds of letters.
const mm = (v: number) => v.toFixed(2);
const ringsD = (rings: readonly (readonly [number, number])[][]) =>
  rings.map((ring) => ring.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${mm(x)},${mm(y)}`).join(' ') + ' Z').join(' ');
const pointsAttr = (points: readonly (readonly [number, number])[]) => points.map(([x, y]) => `${mm(x)},${mm(y)}`).join(' ');

export function PreviewSvg({
  segments,
  marks,
  footerLeft,
  footerRight,
  // Ruling colour scheme; pass the same map to lineaturePdf so preview and
  // print never diverge (defaults to the standard print look).
  styles = ROLE_STYLES,
  // The Übungstext's ink (lib/uebungstext.ts), the same list lineaturePdf draws.
  shapes = [],
  // Rows held open for a line the ruling is too narrow for. Preview only —
  // they are deliberately NOT passed to lineaturePdf: a printed practice
  // sheet carries no warning bands, it just keeps the row free.
  rowMarks = [],
}: {
  segments: Segment[];
  marks: TextMark[];
  footerLeft: string;
  footerRight: string;
  styles?: Record<LineRole, RoleStyle>;
  shapes?: readonly InkShape[];
  rowMarks?: readonly RowMark[];
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
      {shapes.map((s, i) =>
        s.kind === 'fill' ? (
          <path key={`s${i}`} d={ringsD(s.rings)} fill={s.color} fillRule="evenodd" stroke="none" />
        ) : (
          <polyline
            key={`s${i}`}
            points={pointsAttr(s.points)}
            fill="none"
            stroke={s.color}
            strokeWidth={s.widthMm}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ),
      )}
      {rowMarks.map((r) => (
        <g key={`r${r.no}`}>
          <title>{fmt(de.worksheet.text.markTitle, { no: r.no })}</title>
          <rect
            x={r.x}
            y={r.y}
            width={r.width}
            height={r.height}
            fill="none"
            stroke={schulheft.marginRed}
            strokeWidth={0.4}
            strokeDasharray="2 1.5"
          />
          {/* The row number in the margin, so the sentence under the text
              field and the marked row name the same line. */}
          <text
            x={Math.max(1, r.x - 1)}
            y={r.y + r.height}
            fontSize={Math.min(4, r.height)}
            fill={schulheft.marginRed}
            fontFamily="sans-serif"
            textAnchor="end"
          >
            {r.no}
          </text>
        </g>
      ))}
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
