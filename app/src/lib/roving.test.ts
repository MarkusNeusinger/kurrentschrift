import { describe, expect, it } from 'vitest';

import { cellAtFlatIndex, isRovingKey, rovingTarget } from './roving';

// Three shapes cover every surface the admin has: the work lists (many rows,
// several controls each), a wrapping grid (ONE row, many controls) and the
// ragged case a row without controls makes (a ligature cell opens nothing).
const LIST = [3, 2, 3];
const GRID = [5];
const RAGGED = [2, 0, 2];

describe('rovingTarget', () => {
  it('walks rows with Up/Down and keeps the column', () => {
    expect(rovingTarget('ArrowDown', { row: 0, column: 1 }, LIST)).toEqual({ row: 1, column: 1 });
    expect(rovingTarget('ArrowUp', { row: 2, column: 2 }, LIST)).toEqual({ row: 1, column: 1 });
  });

  it('clamps the column onto a narrower row instead of losing it', () => {
    // Row 1 has two controls, so column 2 becomes column 1 — and stepping on
    // does NOT restore column 2: the reader is where they last stood.
    expect(rovingTarget('ArrowDown', { row: 0, column: 2 }, LIST)).toEqual({ row: 1, column: 1 });
  });

  it('walks the controls of one row with Left/Right', () => {
    expect(rovingTarget('ArrowRight', { row: 0, column: 0 }, LIST)).toEqual({ row: 0, column: 1 });
    expect(rovingTarget('ArrowLeft', { row: 0, column: 1 }, LIST)).toEqual({ row: 0, column: 0 });
  });

  it('does not wrap at any end', () => {
    expect(rovingTarget('ArrowUp', { row: 0, column: 0 }, LIST)).toBeNull();
    expect(rovingTarget('ArrowDown', { row: 2, column: 0 }, LIST)).toBeNull();
    expect(rovingTarget('ArrowLeft', { row: 1, column: 0 }, LIST)).toBeNull();
    expect(rovingTarget('ArrowRight', { row: 1, column: 1 }, LIST)).toBeNull();
  });

  it('jumps to the ends with Home/End', () => {
    expect(rovingTarget('Home', { row: 2, column: 2 }, LIST)).toEqual({ row: 0, column: 0 });
    expect(rovingTarget('End', { row: 0, column: 0 }, LIST)).toEqual({ row: 2, column: 2 });
  });

  it('gives Home and End back to the browser when the list is already there', () => {
    // Otherwise a reader standing on the first control would lose „scroll to
    // top" to a key press that does nothing.
    expect(rovingTarget('Home', { row: 0, column: 0 }, LIST)).toBeNull();
    expect(rovingTarget('End', { row: 2, column: 2 }, LIST)).toBeNull();
  });

  it('offers no vertical movement in a wrapping grid', () => {
    // One row: Left/Right walk the cells, Up/Down are not this grid's to take
    // (a flex grid has no stable column count).
    expect(rovingTarget('ArrowRight', { row: 0, column: 0 }, GRID)).toEqual({ row: 0, column: 1 });
    expect(rovingTarget('ArrowDown', { row: 0, column: 0 }, GRID)).toBeNull();
    expect(rovingTarget('ArrowUp', { row: 0, column: 3 }, GRID)).toBeNull();
    expect(rovingTarget('End', { row: 0, column: 0 }, GRID)).toEqual({ row: 0, column: 4 });
  });

  it('steps over a row that holds no control', () => {
    expect(rovingTarget('ArrowDown', { row: 0, column: 0 }, RAGGED)).toEqual({ row: 2, column: 0 });
    expect(rovingTarget('ArrowUp', { row: 2, column: 1 }, RAGGED)).toEqual({ row: 0, column: 1 });
    expect(rovingTarget('End', { row: 0, column: 0 }, RAGGED)).toEqual({ row: 2, column: 1 });
  });

  it('answers null for every key it does not own', () => {
    // The load-bearing case: the caller only calls preventDefault on a non-null
    // answer, so Enter and Space keep reaching the button underneath.
    for (const key of ['Enter', ' ', 'a', 'Tab', 'PageDown', 'Escape']) {
      expect(rovingTarget(key, { row: 0, column: 0 }, LIST), key).toBeNull();
      expect(isRovingKey(key), key).toBe(false);
    }
    expect(isRovingKey('ArrowDown')).toBe(true);
  });

  it('answers null for an empty list', () => {
    expect(rovingTarget('ArrowDown', { row: 0, column: 0 }, [])).toBeNull();
    expect(rovingTarget('Home', { row: 0, column: 0 }, [0, 0])).toBeNull();
  });

  it('recovers from a position that no longer exists', () => {
    // The row was filtered away between the key press and this call: treat the
    // reader as standing at the top rather than swallowing the key.
    expect(rovingTarget('ArrowDown', { row: 7, column: 0 }, LIST)).toEqual({ row: 1, column: 0 });
  });
});

describe('cellAtFlatIndex', () => {
  it('counts across the rows', () => {
    expect(cellAtFlatIndex(LIST, 0)).toEqual({ row: 0, column: 0 });
    expect(cellAtFlatIndex(LIST, 3)).toEqual({ row: 1, column: 0 });
    expect(cellAtFlatIndex(LIST, 7)).toEqual({ row: 2, column: 2 });
    expect(cellAtFlatIndex(LIST, 8)).toBeNull();
  });
});
