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
    pathRefs.current.forEach((el, i) => {
      const t = timing[i];
      if (!el || !t) return;
      const steps = t.arcAtTime.length - 1;
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
