// The Landmarken-Linse's drawing half: the detected structures of ONE stored
// row, drawn inside the written glyph's own viewBox
// (`docs/proposals/optimierungs-werkbank.md` §8).
//
// It is a render prop of `WrittenGlyph` rather than an absolutely-positioned
// sibling, because the frame is decided in there — the tight framing, and for
// the Gleichzug path the render-time widened anchors. A marker positioned from
// the outside would sit NEAR the letter; here it sits ON it.
//
// Coordinates: template units (baseline 0, midband 1, y up). SVG y points down,
// so every y is negated at the point of use — the same convention
// `WrittenGlyph` itself follows, and the reason `-y` appears literally rather
// than through a flipped `<g>` (a nested transform would scale the stroke
// widths and the hit areas with it).

import { useMemo } from 'react';

import type { GlyphFrame } from '@/components/WrittenGlyph';
import type { LandmarkOut, TemplateLandmarksOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { landmarkColors } from '@/sections/admin/overlayColors';
import { landmarkKey } from '@/sections/admin/shell/model';

// Half of the 44 px the design system demands on the smaller edge
// (design-system.md §9.3). Converted to template units per render, because the
// same unit is a different number of pixels on a lowercase letter and on one
// with an ascender.
const HIT_RADIUS_PX = 22;

// Marker geometry, in template units. Small enough not to bury the letter,
// large enough to read at the 390 px viewport; the invisible hit circle above
// carries the touch target.
const RING_R = 0.085; // Kreuzung
const CORNER_HALF = 0.06; // Umkehrecke
const TICK_HALF = 0.09; // Absetzen
const ZONE_W = 0.1; // Retrace/Berührung band
const MERGE_W = 0.13; // Verschmelzung band (hatched)
const STROKE = 0.022;

export interface LandmarkOverlayProps {
  row: TemplateLandmarksOut;
  frame: GlyphFrame;
  // Which kinds are drawn. Absent = all of them.
  shown?: ReadonlySet<string>;
  // The marker currently under inspection, as `kind#index`.
  selectedKey?: string | null;
  onSelect: (landmark: LandmarkOut) => void;
  // A click on the letter's empty area, in template units (y already flipped
  // back to "up"), so the author can report a marker that is MISSING.
  onSpot: (x: number, y: number) => void;
}

export function LandmarkOverlay({ row, frame, shown, selectedKey, onSelect, onSpot }: LandmarkOverlayProps) {
  const t = de.admin.letters;
  const hit = frame.pxPerUnit > 0 ? HIT_RADIUS_PX / frame.pxPerUnit : RING_R * 2;
  const visible = useMemo(
    () => row.landmarks.filter((lm) => !shown || shown.has(lm.kind)),
    [row.landmarks, shown],
  );

  return (
    <g>
      {/* The empty area, under every marker: a click that hits no marker is a
          report that one is MISSING — the complaint this layer most needs to
          be able to receive, and the one a marker-only overlay cannot take.
          It is POINTER SUGAR and says so to assistive tech: the same complaint
          has a real, focusable button under the letter („Fehlende Marke
          melden"), and the only thing this adds is pinning the exact place. A
          `role="button"` that cannot be tabbed to or activated by key would be
          a promise the element does not keep. */}
      <rect
        x={frame.minX}
        y={frame.vbY}
        width={frame.vbW}
        height={frame.vbH}
        fill="transparent"
        aria-hidden="true"
        style={{ cursor: 'crosshair' }}
        onClick={(event) => {
          const box = event.currentTarget.getBoundingClientRect();
          if (!box.width || !box.height) return;
          const x = frame.minX + ((event.clientX - box.left) / box.width) * frame.vbW;
          const yDown = frame.vbY + ((event.clientY - box.top) / box.height) * frame.vbH;
          onSpot(round4(x), round4(-yDown));
        }}
      />

      {visible.map((lm) => {
        const key = landmarkKey(lm);
        const selected = selectedKey === key;
        const colour = landmarkColors[lm.kind];
        return (
          <g key={key} className="landmark-marker">
            <Shape landmark={lm} colour={colour} selected={selected} />
            {/* The touch target, always ≥ 44 px and always last so it wins the
                click over the drawn shape underneath it. */}
            <circle
              cx={lm.x}
              cy={-lm.y}
              r={hit}
              fill="transparent"
              role="button"
              tabIndex={0}
              aria-label={fmt(t.landmarkAria, {
                kind: t.landmarkKind[lm.kind],
                index: lm.index,
                x: lm.x.toFixed(2),
                y: lm.y.toFixed(2),
              })}
              style={{ cursor: 'pointer' }}
              onClick={(event) => {
                event.stopPropagation();
                onSelect(lm);
              }}
              onKeyDown={(event) => {
                if (event.key !== 'Enter' && event.key !== ' ') return;
                event.preventDefault();
                onSelect(lm);
              }}
            >
              <title>{`${t.landmarkKind[lm.kind]} #${lm.index}`}</title>
            </circle>
          </g>
        );
      })}
    </g>
  );
}

function Shape({ landmark, colour, selected }: { landmark: LandmarkOut; colour: string; selected: boolean }) {
  const width = selected ? STROKE * 2 : STROKE;
  const common = { stroke: colour, strokeWidth: width, fill: 'none' as const };
  const path = landmark.points.map(([x, y]) => `${x},${-y}`).join(' ');

  switch (landmark.kind) {
    case 'crossing':
      // A ring AT the point, plus its centre — the ring reads at a glance, the
      // dot says exactly where the two passes met.
      return (
        <>
          <circle cx={landmark.x} cy={-landmark.y} r={RING_R} {...common} />
          <circle cx={landmark.x} cy={-landmark.y} r={STROKE} fill={colour} />
        </>
      );
    case 'loop': {
      // Scaled to the measured aperture D0, so a Kringel that has run tight
      // LOOKS tight — the whole point of the class the catalogue assigns it.
      const d0 = Number(landmark.numbers.d0 ?? 0);
      return (
        <circle
          cx={landmark.x}
          cy={-landmark.y}
          r={Math.max(STROKE * 2, d0 / 2)}
          {...common}
          strokeDasharray={`${STROKE * 3} ${STROKE * 2}`}
        />
      );
    }
    case 'corner':
      return (
        <rect
          x={landmark.x - CORNER_HALF}
          y={-landmark.y - CORNER_HALF}
          width={CORNER_HALF * 2}
          height={CORNER_HALF * 2}
          {...common}
        />
      );
    case 'lift':
      // A tick where the pen came down again, plus a dot on the point itself.
      return (
        <>
          <line
            x1={landmark.x}
            y1={-landmark.y - TICK_HALF}
            x2={landmark.x}
            y2={-landmark.y + TICK_HALF}
            {...common}
            strokeLinecap="round"
          />
          <circle cx={landmark.x} cy={-landmark.y} r={STROKE * 1.5} fill={colour} />
        </>
      );
    case 'overlap':
      // Hatched: a thick dashed band along the pass, so „two strokes in one
      // place" reads differently from the solid band of a retrace even in
      // greyscale or for a red-green-blind reader.
      return (
        <polyline
          points={path}
          stroke={colour}
          strokeWidth={MERGE_W}
          fill="none"
          strokeDasharray={`${STROKE * 1.5} ${STROKE * 1.5}`}
          opacity={selected ? 0.85 : 0.6}
        />
      );
    case 'retrace':
    case 'touch':
      return (
        <polyline
          points={path}
          stroke={colour}
          strokeWidth={ZONE_W}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={landmark.kind === 'touch' ? `${STROKE * 4} ${STROKE * 3}` : undefined}
          opacity={selected ? 0.8 : 0.5}
        />
      );
    default:
      return null;
  }
}

const round4 = (value: number): number => Math.round(value * 10000) / 10000;
