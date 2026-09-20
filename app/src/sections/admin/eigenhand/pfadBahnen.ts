// Which stored entries of a Fassung are actually a BAHN — and which only say
// why there is none.
//
// Since Streifen-Pfad format 2 the stored list holds both (the Skip-Eintrag,
// author decision C of 2026-09-20). A skip has no strokes, no registration and
// no x-height, so every surface that draws or counts a path has to take it out
// first — and doing that with a hand-written `.filter` at each call site is how
// one of them ends up dereferencing `registration_px.tx` on an entry that has
// none. One predicate, and it NARROWS: what comes back is a path, and TypeScript
// knows it.

import type { EigenhandPfad, EigenhandPfadRegistration } from '@/lib/api';

/** A stored entry that really carries a path — frame and scale included. */
export type EigenhandBahn = EigenhandPfad & {
  registration_px: EigenhandPfadRegistration;
  xh_px: number;
};

/**
 * The entries of a Fassung that carry a path, in the order they were stored.
 *
 * `status` is what decides, not an empty `strokes`: a reader must never have to
 * infer a skip from the absence of something, which is exactly the guessing the
 * Skip-Eintrag was introduced to end. The frame and scale are checked alongside
 * because they are what an overlay needs — a row written under format 1 always
 * has them, and only a skip does not.
 */
export function bahnenOf(pfade: readonly EigenhandPfad[] | null | undefined): EigenhandBahn[] {
  return (pfade ?? []).filter(
    (pfad): pfad is EigenhandBahn =>
      pfad.status !== 'skipped' && pfad.registration_px !== null && pfad.xh_px !== null,
  );
}
