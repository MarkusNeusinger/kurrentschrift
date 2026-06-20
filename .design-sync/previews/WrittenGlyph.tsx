// WrittenGlyph — a canonical glyph rendered "as written": the filled Schwellzug
// silhouette revealed stroke-by-stroke in pen order. The reveal is a timed CSS
// animation, which a frozen-clock screenshot would catch mid-stroke (half the
// ink hidden). The component already has a static path: under
// prefers-reduced-motion it renders the COMPLETE, settled (oxidized) glyph with
// no animation. We force that media state here so the captured card is the
// finished letter, deterministically — not a frame of the write-in.
//
// The payloads in _writtenGlyphData.ts are real diagnostics (the author's own
// ductus), so these are the actual letters, not a hand-built stand-in.
import { WrittenGlyph } from 'kurrentschrift-app';

import { paper } from '../../app/src/styles/paper';

import { eMedial, tMedial } from './_writtenGlyphData';

// Make usePrefersReducedMotion() report `reduce` so the glyph renders static and
// complete. Only the reduced-motion query is overridden; everything else (MUI
// breakpoints etc.) delegates to the real matchMedia.
if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
  const orig = window.matchMedia.bind(window);
  window.matchMedia = ((query: string) =>
    query.includes('prefers-reduced-motion')
      ? {
          matches: true,
          media: query,
          onchange: null,
          addEventListener() {},
          removeEventListener() {},
          addListener() {},
          removeListener() {},
          dispatchEvent: () => false,
        }
      : orig(query)) as typeof window.matchMedia;
}

export const BuchstabeE = () => <WrittenGlyph glyphKey="e-medial" data={eMedial} height={200} surfaceBg={paper.bg} />;

// `t` is drawn in two pen-strokes — the reveal lifts between them (a real gap,
// not a bar bridging the Absetzen).
export const BuchstabeT = () => <WrittenGlyph glyphKey="t-medial" data={tMedial} height={220} surfaceBg={paper.bg} />;
