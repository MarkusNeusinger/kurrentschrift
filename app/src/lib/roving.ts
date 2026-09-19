// Where an arrow key moves inside a ROVING LIST — the arithmetic alone, with no
// DOM and no React in it (the idiom of `lineWrap.ts`, so the truth table is a
// flat unit test rather than something to read out of an effect).
//
// A roving list is a list that owns ONE tab stop: Tab enters it at the row the
// reader last stood on, the arrows walk it, Tab leaves it. The admin needs it
// because its overviews are long — the Buchstaben list offers three controls on
// each of up to 63 rows, so UNPAGINATED a reader who wanted the toolbar under
// the list pressed Tab ~190 times to get there. Measured on the paginated page
// as it ships: 77 stops before this, 19 after (the Paar-Matrix 142 → 44).
//
// The list is modelled as ROWS of CONTROLS, and that one shape serves both
// surfaces the admin has:
//   · a work list — one row per subject, several controls in it (aufklappen,
//     öffnen, die eine Erklärmarke). Up/Down walk the subjects, Left/Right the
//     controls of the row you are on.
//   · a wrapping grid — the pair cells, the Streifen-Galerie. It is handed in as
//     ONE row of many controls, so Left/Right walk the cells and Up/Down do
//     nothing at all. That is deliberate (and not a shortcut taken): a flex grid
//     re-wraps with the window, so it has no stable column count, and a Down
//     that jumped four cells at 1440 px and two at 1024 px would be worse than
//     no Down at all.
//
// Two rules the callers depend on:
//   · NO WRAP at the ends. In a 63-row list a wrap puts the reader at the other
//     end of the page with no way to notice — the cost of a dead key press is
//     far lower.
//   · `null` for anything this module does not own — including a key it owns
//     that cannot move. The caller only calls `preventDefault()` on a non-null
//     answer, so Enter and Space keep reaching the button underneath, and an
//     ArrowDown on the last row scrolls the page the way it always did.

/** A position in the list: which row, and which control inside it. */
export type RovingCell = { row: number; column: number };

/** How many controls each row holds, in the list's own order. A row may be
 * empty (a pair cell that is a ligature opens nothing) and is then skipped. */
export type RovingShape = readonly number[];

const ROVING_KEYS = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End']);

/** Whether this list would act on the key at all — the cheap first test a
 * keydown handler makes before it looks anything up. */
export const isRovingKey = (key: string): boolean => ROVING_KEYS.has(key);

/** The first row from `start` (inclusive) in `step` direction that holds a
 * control, or `null` when there is none. */
function seekRow(shape: RovingShape, start: number, step: number): number | null {
  for (let row = start; row >= 0 && row < shape.length; row += step) {
    if (shape[row] > 0) return row;
  }
  return null;
}

const sameCell = (a: RovingCell, b: RovingCell): boolean => a.row === b.row && a.column === b.column;

/**
 * Where `key` moves the focus from `from`, or `null` when it moves nowhere —
 * because the key is not one of ours, because the list is empty, or because the
 * edge is reached.
 *
 * Up/Down keep the COLUMN where the next row is wide enough for it and clamp to
 * that row's last control otherwise: walking a list of work rows must not lose
 * the „öffnen" column just because one row in the middle carries no score mark.
 */
export function rovingTarget(key: string, from: RovingCell, shape: RovingShape): RovingCell | null {
  if (!isRovingKey(key)) return null;

  const first = seekRow(shape, 0, 1);
  const last = seekRow(shape, shape.length - 1, -1);
  if (first === null || last === null) return null;

  // A `from` that no longer exists (the row was filtered away between the
  // keydown and this call) is treated as „at the top", so the key still moves
  // somewhere sensible instead of being swallowed.
  const row = shape[from.row] > 0 ? from.row : first;
  const column = Math.min(Math.max(from.column, 0), shape[row] - 1);
  const current: RovingCell = { row, column };

  const target = ((): RovingCell | null => {
    switch (key) {
      case 'Home':
        return { row: first, column: 0 };
      case 'End':
        return { row: last, column: shape[last] - 1 };
      case 'ArrowLeft':
        return column > 0 ? { row, column: column - 1 } : null;
      case 'ArrowRight':
        return column + 1 < shape[row] ? { row, column: column + 1 } : null;
      case 'ArrowUp':
      case 'ArrowDown': {
        const step = key === 'ArrowDown' ? 1 : -1;
        const next = seekRow(shape, row + step, step);
        // Keep the column where the next row is wide enough for it.
        return next === null ? null : { row: next, column: Math.min(column, shape[next] - 1) };
      }
      default:
        return null;
    }
  })();

  // „Home" while already home is not a move, and swallowing it would take the
  // browser's own Home (scroll to top) away from a reader who is already there.
  return target === null || sameCell(target, current) ? null : target;
}
