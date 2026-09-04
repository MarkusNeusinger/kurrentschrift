// One written line: the SVG half of `WrittenWord`, split out because a wrapped
// text renders SEVERAL of these and each one needs its own reveal — the WAAPI
// hook takes one ref array per stroke run, and hooks cannot be called in a loop.
//
// A line is a whole composition of its own (`GET /write/word` per line), so its
// strokes run continuously from the first Anstrich to the last Auslauf; what
// this component does not own is WHEN it writes. The block's schedule is
// computed once for all lines in WrittenWord and handed down as `timing`, and
// the ink settle is timed to the block's end so a wrapped text ages as one page
// rather than line by line.

import { Box } from '@mui/material';
import { useRef } from 'react';

import { InkBleedFilter, InkGuides, RevealMask } from '@/components/inkReveal';
import { inkGroupSx } from '@/components/inkReveal/inkGroupSx';
import { useStrokeReveal } from '@/hooks/useStrokeReveal';
import type { ComposedWordOut, DrawItemOut } from '@/lib/api';
import type { RevealTiming } from '@/lib/strokeTiming';
import { SETTLE_MS } from '@/lib/strokeTiming';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';

// Geometry of one line in template units (baseline = 0, midband = 1, y up; SVG
// y points down, so y is negated in the rendered data).
export interface LineGeom {
  minX: number;
  vbW: number;
  vbY: number;
  vbH: number;
  items: DrawItemOut[];
  guides: ComposedWordOut['guides'];
}

interface Props {
  geom: LineGeom;
  // Rendered size in px. Both come from ONE scale shared by every line of the
  // block, so all lines write at the same x-height.
  width: number;
  height: number;
  // Leading before this line, px — 0 for the first line of a block, one line
  // gap inside a paragraph, a doubled one where the writer typed a blank row.
  // It rides on the line because a flex `gap` can only be one number.
  marginTop?: number;
  timing: RevealTiming[];
  animate: boolean;
  // Bumped on replay: remounts the mask paths and restarts the whole block.
  run: number;
  maskId: string;
  showLineature: boolean;
  surfaceBg: string;
  inkColor?: string;
  // End of the BLOCK's write-in, so every line settles together.
  writeEndMs: number;
}

export function WrittenLine({
  geom,
  width,
  height,
  marginTop = 0,
  timing,
  animate,
  run,
  maskId,
  showLineature,
  surfaceBg,
  inkColor,
  writeEndMs,
}: Props) {
  const { minX, vbW, vbY, vbH, items, guides } = geom;
  const maskPathRefs = useRef<Array<SVGPathElement | null>>([]);
  useStrokeReveal(maskPathRefs, timing, animate, `${run}|${maskId}`);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`${minX} ${vbY} ${vbW} ${vbH}`}
      preserveAspectRatio="xMidYMid meet"
      // The block carries the accessible name (WrittenWord's wrapper); a line is
      // a fragment of it and would only repeat the text to a screen reader.
      aria-hidden
      style={{ display: 'block', background: surfaceBg, maxWidth: '100%', overflow: 'visible', marginTop }}
    >
      <defs>
        <InkBleedFilter
          id={`${maskId}-bleed`}
          scale={0.016}
          inset={{ x: '-3%', y: '-5%', width: '106%', height: '110%' }}
        />
        <RevealMask
          id={maskId}
          bounds={{ x: minX, y: vbY, width: vbW, height: vbH }}
          strokes={items.map((it) => ({ centerline: it.centerline, maskWidth: it.mask_width }))}
          pathRefs={maskPathRefs}
          animate={animate}
          runKey={run}
        />
      </defs>

      {showLineature && guides && (
        <InkGuides minX={minX} width={vbW} baseline={guides.baseline} midband={guides.midband} />
      )}

      <Box
        component="g"
        key={`ink-${run}`}
        mask={`url(#${maskId})`}
        filter={`url(#${maskId}-bleed)`}
        sx={inkGroupSx({ animate, writeEndMs, settleMs: SETTLE_MS, inkColor, withStroke: true })}
      >
        {items.map((it, i) =>
          it.rings ? (
            // Glyph silhouette: filled (inherits group fill), never stroked.
            <path key={i} d={ringsToPathD(it.rings, true)} fillRule="evenodd" stroke="none" />
          ) : (
            // Connector: stroked capsule (inherits group stroke), never filled.
            <path
              key={i}
              d={polylineToPathD(it.centerline)}
              fill="none"
              strokeWidth={it.stroke_width}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ),
        )}
      </Box>
    </svg>
  );
}
