// Pure helpers for the wizard canvas' pointer gestures — no React.
//
// A canvas gesture has TWO lifetimes that must not be conflated:
//   1. the pointer's — pen down → pen up. While it runs, pointer-moves drive the
//      gesture (extend the eraser draft, follow the Grundlinie with the pointer).
//   2. the preview's — until the write the release triggered has landed. Dropping
//      it at pen-up would re-render from the still-unsaved bbox, so the guide line
//      visibly snaps back and jumps forward again a round trip later (PR #230).
//
// The grip below is lifetime 1, commitThenClear is lifetime 2. Keeping them apart
// is what stops a stray move during the commit round trip from rewriting the
// gesture that is only being HELD for its preview — which would make the identity
// clear miss and strand the gesture forever.

/** The pointerId currently driving a canvas gesture; null between gestures. */
export interface Grip {
  current: number | null;
}

/**
 * Claim the canvas for `pointerId`. One gesture at a time: a second pointer — a
 * palm resting beside the S-Pen, a second finger — is refused rather than allowed
 * to hijack or extend the running one. Returns false if the canvas is already held.
 */
export function takeGrip(grip: Grip, pointerId: number): boolean {
  if (grip.current !== null) return false;
  grip.current = pointerId;
  return true;
}

/** True while `pointerId` is the pointer driving the gesture. */
export const holdsGrip = (grip: Grip, pointerId: number): boolean => grip.current === pointerId;

/** True while some pointer drives a gesture (i.e. a button/tip is down). */
export const gripHeld = (grip: Grip): boolean => grip.current !== null;

/**
 * Release the canvas if `pointerId` holds it, and report whether it did — only the
 * owning pointer's release ends the gesture and may commit it. A release from any
 * other pointer (the palm lifting, a stray up after the grip was already dropped)
 * is a no-op, so it can never commit a gesture it did not draw.
 */
export function releaseGrip(grip: Grip, pointerId: number): boolean {
  if (grip.current !== pointerId) return false;
  grip.current = null;
  return true;
}

/**
 * Hand a finished gesture to its commit and only THEN drop the in-flight preview
 * (see lifetime 2 above). Cleared by IDENTITY, so a gesture begun while the PUT
 * was still in flight survives its predecessor's landing.
 *
 * `finally`, not `then`: a REJECTED save leaves the bbox unchanged, so keeping the
 * preview would paint a value that was never stored. The gesture is dropped either
 * way and the canvas falls back to the true stored state — the commit paths report
 * the failure through the wizard's snack (useWizard's updateBboxField catches, so
 * in practice only an unexpected throw lands here).
 *
 * The identity clear is only correct while nothing else writes `setGesture` during
 * the await; the grip above is what guarantees that, because the pointer's lifetime
 * has already ended when this runs.
 */
export async function commitThenClear<T>(
  gesture: T,
  setGesture: (update: (g: T | null) => T | null) => void,
  commit: () => Promise<void>,
): Promise<void> {
  try {
    await commit();
  } finally {
    setGesture((g) => (g === gesture ? null : g));
  }
}
