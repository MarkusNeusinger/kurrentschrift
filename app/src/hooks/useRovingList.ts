// The roving list, wired to real elements — `lib/roving.ts` says where a key
// moves, this says what moves and keeps the one tab stop true across a render.
//
// Callers mark the CONTAINER and each ROW, and nothing else:
//
//   const roving = useRovingList();
//   <Box {...roving.containerProps}>
//     {rows.map((row) => <WorkRow {...roving.rowProps(row.glyphKey)} … />)}
//   </Box>
//
// The controls inside a row are FOUND rather than registered. That is the whole
// reason this fits in one hook: a work row carries its „aufklappen" button in
// the shared `WorkRow`, its „öffnen" button in the caller's `actions`, and its
// one Erklärmarke in whichever of the two slots the row's state puts it — three
// components, three files, and a registration prop threaded through all of them
// to say what a `querySelectorAll` already knows. The cost is one imperative
// `tabIndex` per control per render, which React does not fight: no call site
// passes `tabIndex`, so React has no opinion to restore.
//
// What is deliberately NOT managed:
//   · anything under `data-roving-skip` — the body a work row expands INTO. The
//     row is one stop; the card inside it is content and keeps its own tab
//     order, or opening a row would bury its controls behind the arrows.
//   · text fields. A list whose toolbar sits inside its container would
//     otherwise eat the arrow keys of its own search box, and Left/Right in a
//     text field is how you edit text.
//   · Enter and Space. The controls are real buttons; the browser already
//     activates them, and `rovingTarget` returns `null` so this handler never
//     calls `preventDefault()` on them.
//
// Focus survives a filter, a page change and a re-render by REMEMBERING THE ROW
// KEY, not an index: when the key is gone the stop passes to whatever now
// stands at that index, and when the element that had focus was removed with
// it, focus is put back there — otherwise a filter click would drop the reader
// on `<body>` and the next Tab would restart at the top of the document.

import { useCallback, useLayoutEffect, useRef } from 'react';
import type { FocusEvent, KeyboardEvent } from 'react';

import { isRovingKey, rovingTarget, type RovingCell } from '@/lib/roving';

/** Button-like controls. Text fields are absent on purpose (see the head). */
const CONTROLS = 'a[href], button, [role="button"], [role="link"]';

/** Marks the row a control belongs to; also how document order is read back. */
const ROW_ATTR = 'data-roving-row';
/** A subtree this list does not manage — an expanded row's body. */
const SKIP_ATTR = 'data-roving-skip';

type Row = { key: string; controls: HTMLElement[] };

/** Where the tab stop stands, remembered across renders. The INDEX rides along
 * so a row that disappears can hand the stop to its neighbour. */
type Remembered = { key: string; index: number; column: number };

export type RovingListOptions = {
  /**
   * `vertical` (the default) — each marked element is a ROW: Up/Down walk the
   * rows, Left/Right the controls within one.
   *
   * `horizontal` — the marked elements are CELLS of one wrapping grid: their
   * controls form a single row, so Left/Right walk the cells and Up/Down do
   * nothing. A flex grid re-wraps with the window and has no stable column
   * count (`lib/roving.ts`).
   */
  orientation?: 'vertical' | 'horizontal';
};

export type RovingList = {
  containerProps: {
    ref: (element: HTMLElement | null) => void;
    onKeyDown: (event: KeyboardEvent<HTMLElement>) => void;
    onFocusCapture: (event: FocusEvent<HTMLElement>) => void;
    onBlurCapture: (event: FocusEvent<HTMLElement>) => void;
  };
  /** Marks one row (or, horizontally, one cell). The key identifies the SUBJECT,
   * so the tab stop survives a re-order. */
  rowProps: (key: string) => { [ROW_ATTR]: string };
};

const visible = (element: HTMLElement): boolean =>
  !element.hasAttribute('disabled') &&
  element.getAttribute('aria-hidden') !== 'true' &&
  // `offsetParent === null` also catches `display: none` on any ancestor, which
  // is what a collapsed block looks like when it is hidden rather than
  // unmounted. Nothing here is `position: fixed`, the one false positive.
  element.offsetParent !== null;

export function useRovingList(options: RovingListOptions = {}): RovingList {
  const horizontal = options.orientation === 'horizontal';
  const containerRef = useRef<HTMLElement | null>(null);
  const activeRef = useRef<Remembered | null>(null);
  // Whether the reader is standing IN this list, and on which element. Both are
  // needed to tell „the row I was on was filtered away" (restore focus) from
  // „the reader clicked somewhere else" (leave focus alone).
  const insideRef = useRef(false);
  const focusedRef = useRef<HTMLElement | null>(null);

  const readRows = useCallback((): Row[] => {
    const container = containerRef.current;
    if (!container) return [];
    const marked = [...container.querySelectorAll<HTMLElement>(`[${ROW_ATTR}]`)];
    const cells = marked.map((element) => ({
      key: element.getAttribute(ROW_ATTR) ?? '',
      // A marked element that IS a control is its own only control — a pair
      // cell is the `ButtonBase`, not a box around one — and a marked element
      // that is a container owns the controls inside it.
      controls: (element.matches(CONTROLS) ? [element] : [...element.querySelectorAll<HTMLElement>(CONTROLS)]).filter(
        (control) => !control.closest(`[${SKIP_ATTR}]`) && visible(control),
      ),
    }));
    // One row of everything: a wrapping grid is walked left to right, and its
    // cells are the columns. The key of the whole row is the first cell's, so a
    // grid that loses its first cell still hands the stop on by index.
    if (!horizontal) return cells;
    return [{ key: cells[0]?.key ?? '', controls: cells.flatMap((cell) => cell.controls) }];
  }, [horizontal]);

  /** Which cell of `rows` the tab stop should stand on. */
  const resolve = useCallback((rows: Row[]): RovingCell | null => {
    const filled = (index: number) => index >= 0 && index < rows.length && rows[index].controls.length > 0;
    const seek = (from: number): number | null => {
      for (let i = from; i < rows.length; i += 1) if (filled(i)) return i;
      for (let i = Math.min(from, rows.length - 1); i >= 0; i -= 1) if (filled(i)) return i;
      return null;
    };
    const remembered = activeRef.current;
    let row = remembered === null ? seek(0) : rows.findIndex((r) => r.key === remembered.key && r.controls.length > 0);
    // The remembered row is gone (a filter, a page, a deleted subject): the stop
    // goes to whatever now stands where it stood, never back to the top.
    if (row === null || row < 0) row = seek(Math.min(remembered?.index ?? 0, Math.max(rows.length - 1, 0)));
    if (row === null) return null;
    return { row, column: Math.min(remembered?.column ?? 0, rows[row].controls.length - 1) };
  }, []);

  /** Re-apply the one tab stop, and put focus back if the list just lost it. */
  const apply = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const rows = readRows();
    const active = resolve(rows);
    rows.forEach((row, rowIndex) =>
      row.controls.forEach((control, column) => {
        control.tabIndex = active !== null && active.row === rowIndex && active.column === column ? 0 : -1;
      }),
    );
    if (active === null) return;
    activeRef.current = { key: rows[active.row].key, index: active.row, column: active.column };
    // Only when the element that HAD focus was removed from the document —
    // never when the reader simply clicked elsewhere, which would make the list
    // steal focus back on its next render.
    const lost = insideRef.current && focusedRef.current !== null && !focusedRef.current.isConnected;
    if (lost) rows[active.row].controls[active.column].focus();
  }, [readRows, resolve]);

  // After EVERY render of the caller: the row set may have changed, and a
  // control that arrived with it would otherwise carry the browser's default
  // tabIndex and be a second stop.
  useLayoutEffect(apply);

  const onKeyDown = useCallback(
    (event: KeyboardEvent<HTMLElement>) => {
      // A modifier means the key belongs to somebody else — Alt+Shift+←/→ is the
      // Subjekt-Stepper, and Shift+Arrow is a text selection.
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (!isRovingKey(event.key)) return;
      const rows = readRows();
      // Where the key came from. A target that is not one of our controls — a
      // search field, the body of an expanded row — is none of our business.
      const from = ((): RovingCell | null => {
        for (let row = 0; row < rows.length; row += 1) {
          const column = rows[row].controls.findIndex((control) => control.contains(event.target as Node));
          if (column >= 0) return { row, column };
        }
        return null;
      })();
      if (from === null) return;
      const target = rovingTarget(event.key, from, rows.map((row) => row.controls.length));
      if (target === null) return;
      event.preventDefault();
      activeRef.current = { key: rows[target.row].key, index: target.row, column: target.column };
      rows[target.row].controls[target.column].focus();
    },
    [readRows],
  );

  const onFocusCapture = useCallback(
    (event: FocusEvent<HTMLElement>) => {
      const rows = readRows();
      for (let row = 0; row < rows.length; row += 1) {
        const column = rows[row].controls.findIndex((control) => control.contains(event.target));
        if (column < 0) continue;
        insideRef.current = true;
        focusedRef.current = rows[row].controls[column];
        // Tab or a click landed on a different control than the one holding the
        // stop — the stop follows, so leaving and re-entering comes back here.
        activeRef.current = { key: rows[row].key, index: row, column };
        apply();
        return;
      }
    },
    [apply, readRows],
  );

  const onBlurCapture = useCallback((event: FocusEvent<HTMLElement>) => {
    // `relatedTarget` is null both when the window loses focus AND when the
    // focused element was removed from the document — and the second is exactly
    // the case `apply` has to repair. So only a focus that demonstrably landed
    // somewhere ELSE on the page ends the list's claim on it.
    const next = event.relatedTarget;
    if (next instanceof Node && !containerRef.current?.contains(next)) insideRef.current = false;
  }, []);

  const setContainer = useCallback((element: HTMLElement | null) => {
    containerRef.current = element;
  }, []);

  return {
    containerProps: { ref: setContainer, onKeyDown, onFocusCapture, onBlurCapture },
    rowProps: (key: string) => ({ [ROW_ATTR]: key }),
  };
}

/** The attribute a caller puts on a subtree this list must leave alone — the
 * body a work row expands into. Exported so `WorkList` does not spell it. */
export const ROVING_SKIP = { [SKIP_ATTR]: '' } as const;
