// WAAPI-driven stroke reveal: animates `stroke-dashoffset` per mask path with
// the non-linear offset table from lib/strokeTiming (two-thirds-law kinematics)
// WITHOUT injecting per-stroke @keyframes rules into the global Emotion
// stylesheet — live typing on /federprobe would grow that sheet without bound.
// Animations are scoped to the elements and cancelled on cleanup;
// `fill: 'forwards'` holds the revealed end state like the CSS version did.

import { useEffect, type MutableRefObject } from 'react';

export interface RevealTiming {
  dur: number;
  delay: number;
  // Arc fraction reached at each even time step (from strokeTimeProfile).
  arcAtTime: number[];
}

export function useStrokeReveal(
  pathRefs: MutableRefObject<Array<SVGPathElement | null>>,
  timing: RevealTiming[],
  animate: boolean,
  runKey: unknown,
): void {
  useEffect(() => {
    if (!animate) return undefined;
    const anims: Animation[] = [];
    // Iterate the timing table, not pathRefs.current: the ref array only ever
    // grows (live typing on /federprobe), while timing always matches the
    // strokes currently rendered.
    timing.forEach((t, i) => {
      const el = pathRefs.current[i];
      if (!el) return;
      const steps = t.arcAtTime.length - 1;
      // No WAAPI (very old engines) or a degenerate single-sample profile:
      // reveal instantly instead of throwing — the finished word is the floor,
      // like the reduced-motion path.
      if (typeof el.animate !== 'function' || steps <= 0) {
        el.style.strokeDashoffset = '0';
        return;
      }
      const frames = t.arcAtTime.map((s, k) => ({
        strokeDashoffset: `${(1 - s).toFixed(4)}`,
        offset: k / steps,
      }));
      anims.push(el.animate(frames, { duration: t.dur, delay: t.delay, fill: 'forwards', easing: 'linear' }));
    });
    return () => anims.forEach((a) => a.cancel());
    // timing is derived in the same memo as the paths; runKey remounts restart.
  }, [pathRefs, timing, animate, runKey]);
}
