// The one key binding of the admin: Alt+Shift+← / → steps to the previous or
// next subject (Vorgabe V24, author decision P1-Q11 b). `shortcuts.ts` says
// what the keys are and when they may not fire; this binds them.
//
// On `window` rather than on the view's container — a deliberate departure from
// the first sketch of this PR. Scoped to a container the binding would be dead
// whenever focus sits on `<body>`, which is exactly where it sits right after a
// navigation: the moment the reader reaches for „next". The guard does the work
// the container position would have done, and does it better, because it names
// the owners (a text field, an open dialog) instead of inferring them from
// where in the DOM the focus happens to be.
//
// `preventDefault` is called ONLY when a step really happens. So the key falls
// through untouched in a field, inside the wizard, with the Kurztasten off, and
// at either end of the order — and the browser's own Alt+← (Back) is never
// touched at all, because this binding does not carry that combination.

import { useEffect, useRef } from 'react';

import { isDialogOpen, isInDialog, isTypingTarget, subjectStep } from './shortcuts';
import { useShortcutsEnabled } from './subjectNav';

export type SubjectStep = {
  /** The subject one step back, or null at the start of the order. */
  prev: string | null;
  next: string | null;
  /** Focus that subject — the view's own `focus()`, which MERGES the query, so
   * the list state and the scope's `h=` survive a step. */
  onStep: (key: string) => void;
};

export function useSubjectStepper({ prev, next, onStep }: SubjectStep): void {
  const enabled = useShortcutsEnabled();
  // The listener is bound once per switch state and reads the current
  // neighbours through a ref — re-binding it on every focus change would put an
  // add/remove pair on the window for each keystroke in the head's text field.
  const latest = useRef<SubjectStep>({ prev, next, onStep });
  useEffect(() => {
    latest.current = { prev, next, onStep };
  });

  useEffect(() => {
    if (!enabled) return;
    const onKeyDown = (event: KeyboardEvent) => {
      const step = subjectStep(event);
      if (step === null) return;
      // Three questions, not two: „is the reader typing", „did this come from
      // inside a dialog" and — because this listener answers events from
      // `<body>` on purpose — „is a dialog up at all". Without the third, a key
      // pressed while focus had slipped to the body stepped to another subject
      // BEHIND the open editor.
      if (isTypingTarget(event.target) || isInDialog(event.target) || isDialogOpen(document)) return;
      const { prev: back, next: forward, onStep: go } = latest.current;
      const target = step === -1 ? back : forward;
      if (target === null) return;
      event.preventDefault();
      go(target);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [enabled]);
}
