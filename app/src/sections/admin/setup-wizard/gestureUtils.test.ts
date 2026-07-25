import { describe, expect, it } from 'vitest';

import { commitThenClear, gripHeld, holdsGrip, releaseGrip, takeGrip, type Grip } from './gestureUtils';

const newGrip = (): Grip => ({ current: null });

describe('grip', () => {
  it('is free before the first pointer and held after', () => {
    const g = newGrip();
    expect(gripHeld(g)).toBe(false);
    expect(takeGrip(g, 7)).toBe(true);
    expect(gripHeld(g)).toBe(true);
    expect(holdsGrip(g, 7)).toBe(true);
  });

  // A palm resting beside the S-Pen delivers its own pointerdown; it must not take
  // the canvas away from the pen that is mid-stroke.
  it('refuses a second pointer while one is held', () => {
    const g = newGrip();
    takeGrip(g, 7);
    expect(takeGrip(g, 8)).toBe(false);
    expect(holdsGrip(g, 7)).toBe(true);
    expect(holdsGrip(g, 8)).toBe(false);
  });

  it('is only released by the pointer holding it', () => {
    const g = newGrip();
    takeGrip(g, 7);
    expect(releaseGrip(g, 8)).toBe(false);
    expect(gripHeld(g)).toBe(true);
    expect(releaseGrip(g, 7)).toBe(true);
    expect(gripHeld(g)).toBe(false);
  });

  // The pointer-up handler commits only when the release actually ended a gesture,
  // so a stray up (grip already dropped by the missed-up backstop) commits nothing.
  it('reports no release when nothing was held', () => {
    const g = newGrip();
    expect(releaseGrip(g, 7)).toBe(false);
  });

  it('can be reclaimed after a release', () => {
    const g = newGrip();
    takeGrip(g, 7);
    releaseGrip(g, 7);
    expect(takeGrip(g, 8)).toBe(true);
  });
});

describe('commitThenClear', () => {
  it('clears the gesture only after the commit resolved', async () => {
    let state: string | null = 'stroke';
    let committed = false;
    let release!: () => void;
    const pending = new Promise<void>((r) => {
      release = r;
    });

    const done = commitThenClear<string>(
      'stroke',
      (update) => {
        state = update(state);
      },
      async () => {
        await pending;
        committed = true;
      },
    );

    expect(state).toBe('stroke'); // still previewed while the write is in flight
    release();
    await done;
    expect(committed).toBe(true);
    expect(state).toBeNull();
  });

  // The gesture is cleared by identity: a NEW gesture started while the previous
  // write was in flight must survive its predecessor's landing.
  it('leaves a newer gesture alone', async () => {
    let state: string | null = 'first';
    const done = commitThenClear<string>(
      'first',
      (update) => {
        state = update(state);
      },
      async () => {
        state = 'second'; // a fresh pointer-down during the round trip
      },
    );
    await done;
    expect(state).toBe('second');
  });

  // A rejected save leaves the bbox unchanged, so keeping the preview would paint a
  // value that was never stored — the gesture is dropped either way.
  it('clears the gesture and rethrows when the commit fails', async () => {
    let state: string | null = 'stroke';
    await expect(
      commitThenClear<string>(
        'stroke',
        (update) => {
          state = update(state);
        },
        async () => {
          throw new Error('PUT failed');
        },
      ),
    ).rejects.toThrow('PUT failed');
    expect(state).toBeNull();
  });
});
