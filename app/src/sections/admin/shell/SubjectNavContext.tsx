// The provider behind `subjectNav.ts`: it holds the Kurztasten preference and
// the order each overview last published, for everything under the admin shell.
//
// Two pieces of state that look unrelated share one provider on purpose — they
// are the two halves of ONE feature. The switch in the Scope-Leiste arms the
// binding; the order says what the binding steps through; and the detail views
// that use the second also have to ask about the first. A second provider would
// buy nothing but a second wrapper in `AdminLayout`.
//
// Neither belongs in the URL, and for opposite reasons: the preference is about
// the READER (a link must not carry someone else's keyboard habits, the rule
// `listState.ts` is built on), and the order is a derived answer far too long
// for a query string — up to 169 specimen ids.

import { useCallback, useMemo, useState, type ReactNode } from 'react';

import { readShortcutsEnabled, storeShortcutsEnabled } from './shortcuts';
import { sameSubjectKeys, SubjectNavCtx, type SubjectOrder, type SubjectOrders } from './subjectNav';

export function SubjectNavProvider({ children }: { children: ReactNode }) {
  // Read once, lazily: `localStorage` can throw on the property access itself,
  // and an initialiser keeps that out of every later render.
  const [shortcuts, setShortcutsState] = useState<boolean>(() => readShortcutsEnabled());
  // ONE order PER KIND, not one slot for all three. The admin's whole point is
  // walking between the views — a letter detail links into „Alle Übergänge",
  // whose matrix publishes a join order — and a single slot would have thrown
  // the letter order away on the way there, so the browser Back the linking
  // doctrine rests on would land on a stepper walking the alphabet.
  const [orders, setOrders] = useState<SubjectOrders>({});

  const setShortcuts = useCallback((enabled: boolean) => {
    setShortcutsState(enabled);
    storeShortcutsEnabled(enabled);
  }, []);

  const publishOrder = useCallback((next: SubjectOrder) => {
    // Same order, same object: an overview republishes whenever its rows are
    // rebuilt, and a fresh object each time would re-render every consumer and
    // feed the publisher's own effect back to itself.
    setOrders((prev) => {
      const held = prev[next.kind];
      if (held !== undefined && held.caption === next.caption && sameSubjectKeys(held.keys, next.keys)) return prev;
      return { ...prev, [next.kind]: next };
    });
  }, []);

  const value = useMemo(
    () => ({ shortcuts, setShortcuts, orders, publishOrder }),
    [shortcuts, setShortcuts, orders, publishOrder],
  );
  return <SubjectNavCtx.Provider value={value}>{children}</SubjectNavCtx.Provider>;
}
