// What „der nächste Gegenstand" means, and whether the Kurztasten are armed —
// the context object, its hooks and the two pure rules behind them. The
// provider lives beside this in `SubjectNavContext.tsx` (the split
// `korbState.ts` / `KorbContext.tsx` makes, for the same Fast-Refresh reason).
//
// ‹ › in a detail head follows THE ORDER OF THE OVERVIEW THE READER CAME FROM,
// including its filter and its sort (author question P1-Q12, option a). That is
// the whole point of the overviews having become Arbeitslisten: a reader who
// ranked the letters „Schlechteste zuerst" and opened the worst one wants › to
// be the second-worst, not „b". The cost is that ‹ › changes meaning when the
// sort does, which is why every stepper prints the order it is walking.
//
// The order is PUBLISHED by the overview rather than re-derived in the detail,
// and that is the load-bearing decision of this module. Re-deriving would mean
// repeating each view's filter/sort chain in its detail — and paying for the
// reads those chains stand on a second time (the letters' ranking is a
// per-template score read, the words' is one CPU-bound request per Wortprobe).
// The overview already holds the answer; it hands it over on its way out.
//
// Consequences, both deliberate:
//   · a deep link straight into a detail has no published order, so the stepper
//     falls back to the registry/alphabet order — and SAYS it does;
//   · one order is held PER KIND. A reader walks between the three views all
//     day („Alle Übergänge" out of a letter detail, „zum Buchstaben" back), and
//     a single slot would mean each of those walks silently demoted the order
//     behind it to the registry — on the Back button the admin is built on.

import { createContext, useContext, useEffect } from 'react';

import { de } from '@/locales/admin';

/** Which of the three subjects an order is about. Letters and joins are keyed
 * by their glyph keys, a word by its specimen id — the same keys the work lists
 * already build their rows on. */
export type SubjectKind = 'letter' | 'join' | 'word';

export type SubjectOrder = {
  kind: SubjectKind;
  /** The subjects as the overview showed them: filtered, sorted, all pages. */
  keys: readonly string[];
  /** „Reihenfolge: …" — what the reader is told ‹ › is walking. */
  caption: string;
};

/** The last order published for each kind — a kind is absent until its overview
 * has rendered once in this session. */
export type SubjectOrders = Partial<Record<SubjectKind, SubjectOrder>>;

export type SubjectNavState = {
  /** Are the Kurztasten armed? The ‹ › buttons work either way. */
  shortcuts: boolean;
  setShortcuts: (enabled: boolean) => void;
  /** What each overview last showed. */
  orders: SubjectOrders;
  publishOrder: (order: SubjectOrder) => void;
};

export const SubjectNavCtx = createContext<SubjectNavState | null>(null);

export function useSubjectNav(): SubjectNavState {
  const value = useContext(SubjectNavCtx);
  if (!value) throw new Error('useSubjectNav must be used inside <SubjectNavProvider>');
  return value;
}

export const useShortcutsEnabled = (): boolean => useSubjectNav().shortcuts;

/** The order published for ONE kind — what that kind's detail steps through.
 * A letter detail never sees the join order, and walking into the joins view
 * and back leaves the letter order standing. */
export const useSubjectOrder = (kind: SubjectKind): SubjectOrder | null => useSubjectNav().orders[kind] ?? null;

/** Two key lists, compared by value — the provider's „is this the same order?". */
export const sameSubjectKeys = (a: readonly string[], b: readonly string[]): boolean =>
  a.length === b.length && a.every((key, index) => key === b[index]);

/**
 * An overview hands its current order to the detail behind it.
 *
 * In an effect, not during render: publishing writes into a provider ABOVE the
 * caller, which React forbids on the render path. The dependency is the joined
 * key list rather than the object, because every overview rebuilds its rows
 * into a fresh array on each render — and the provider folds an unchanged order
 * back onto the same object, so this settles after one pass.
 *
 * `keys: null` publishes NOTHING, so a surface that is not the overview can
 * still call the hook unconditionally: the pair matrix is also embedded inside
 * the join detail as a cross-check, and that copy — unfiltered, with an anchor
 * of its own — must not overwrite the order the reader actually came from.
 */
export function usePublishSubjectOrder(kind: SubjectKind, keys: readonly string[] | null, caption: string): void {
  const { publishOrder } = useSubjectNav();
  const signature = keys === null ? null : keys.join('\u0000');
  useEffect(() => {
    if (signature === null) return;
    publishOrder({ kind, keys: signature === '' ? [] : signature.split('\u0000'), caption });
  }, [publishOrder, kind, signature, caption]);
}

/**
 * Which order a detail actually walks — the published one, or the fallback.
 *
 * The published order is used only when it is about THIS kind of subject AND
 * contains the subject in front of the reader. The second half matters: a
 * reader can reach a letter the filtered overview does not list (from the
 * picker, from a Korb link, from a join's „zum Buchstaben"), and a stepper that
 * went dead there would be worse than one that quietly walks the alphabet.
 */
export function stepOrder(
  published: SubjectOrder | null,
  kind: SubjectKind,
  current: string,
  fallback: { keys: readonly string[]; caption: string },
): { keys: readonly string[]; caption: string } {
  if (published === null || published.kind !== kind) return fallback;
  return published.keys.includes(current) ? published : fallback;
}

/** The neighbours of `current` in `keys` — `null` at either end, because the
 * list does not wrap (the reason `lib/roving.ts` gives for its own ends). */
export function neighboursInOrder(
  keys: readonly string[],
  current: string,
): { prev: string | null; next: string | null } {
  const index = keys.indexOf(current);
  if (index < 0) return { prev: null, next: null };
  return {
    prev: index > 0 ? keys[index - 1] : null,
    next: index + 1 < keys.length ? keys[index + 1] : null,
  };
}

/** „Reihenfolge: Schlechteste zuerst · gefiltert" — one wording for all three
 * steppers, so the caption reads the same wherever the reader meets it. */
export function orderCaption(sortLabel: string, filtered: boolean): string {
  const t = de.admin.liste;
  return `${t.orderPrefix}${sortLabel}${filtered ? ` · ${t.orderFiltered}` : ''}`;
}
