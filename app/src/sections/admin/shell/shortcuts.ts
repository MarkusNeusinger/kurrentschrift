// The Kurztasten of the admin: what they are, when they may fire, and how the
// one switch that turns them off is remembered.
//
// Exactly ONE binding exists — Alt+Shift+← / → steps to the previous or next
// subject (author decision P1-Q11 b of 2026-09-19, Vorgabe V24). Two things
// about that choice are worth keeping written down, because both have been got
// wrong once already:
//
//   · It is Alt+SHIFT, not Alt alone. `Alt+←` IS Back on Windows and Linux, and
//     the whole linking doctrine of this admin rests on the back button walking
//     the inspection history (`focus.ts`). A binding that swallowed it would
//     take the reader's way back away wherever it was armed.
//   · The switch is NOT there because of WCAG SC 2.1.4. That criterion covers
//     shortcuts made of letters, digits, punctuation or symbols; a binding with
//     modifiers is out of its scope, and the single-letter shortcuts (`n`/`p`,
//     `j`/`k`) were dropped from the plan before it. The switch exists because
//     V24 asks for it: a key the author does not want is a key he can turn off.
//
// The preference is the one piece of admin state that lives in `localStorage`
// rather than in the URL, and deliberately so: it is a property of the READER's
// keyboard habits, not of what is being looked at, so a link must not carry it
// (the rule the whole of `listState.ts` is built on). Every access goes through
// a try/catch — a private window and blocked site data both throw on the
// property access itself, not on the call (the idiom of `sections/scribe/size.ts`).

/** Where the preference is kept. Prefixed like every other key this app owns. */
export const SHORTCUTS_STORAGE_KEY = 'kurrentschrift.admin.kurztasten';

/** On unless the reader turned them off: the binding is the feature, and a
 * default of „off" would hide it from everyone who never finds the switch. */
export const SHORTCUTS_DEFAULT = true;

/**
 * Whether the Kurztasten are armed. Any failure — no storage, a throwing
 * accessor, a value written by something else — reads as the default: a
 * preference that cannot be read is not a decision to switch the feature off.
 */
export function readShortcutsEnabled(): boolean {
  try {
    const stored = globalThis.localStorage?.getItem(SHORTCUTS_STORAGE_KEY);
    if (stored === 'an') return true;
    if (stored === 'aus') return false;
    return SHORTCUTS_DEFAULT;
  } catch {
    return SHORTCUTS_DEFAULT;
  }
}

/** Remember the switch. A storage that refuses is not an error the reader has
 * to see — the switch still works for this session, it just does not outlive it. */
export function storeShortcutsEnabled(enabled: boolean): void {
  try {
    globalThis.localStorage?.setItem(SHORTCUTS_STORAGE_KEY, enabled ? 'an' : 'aus');
  } catch {
    // Deliberately silent — see above.
  }
}

/**
 * Is the reader typing, or standing in something that owns its own keys?
 *
 * Both halves are the same rule („the key belongs to what has the focus") and
 * both have a concrete owner in this app: the free-text fields of the Wörter
 * and Übergänge heads, and the two editors — the Einrichtungs-Wizard and the
 * Bahn-Editor — which are MUI `Dialog`s and therefore carry `role="dialog"`
 * around everything inside them.
 */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  const tag = target.tagName.toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
  // `closest` rather than a property test: focus often sits on a child of the
  // editable element, and MUI's own comboboxes are a `div[role=textbox]`.
  return target.closest('[contenteditable=""], [contenteditable="true"], [role="textbox"], [role="combobox"]') !== null;
}

/** An open dialog — the wizard, the Bahn-Editor, a confirm — owns every key
 * while it is up, and this asks whether the EVENT came from inside one. */
export function isInDialog(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest('[role="dialog"], [role="alertdialog"]') !== null;
}

/**
 * Is any dialog up at all, wherever the focus happens to sit?
 *
 * `isInDialog` alone is not enough for a listener bound to `window`, and that
 * listener handles events from `<body>` ON PURPOSE (it is where focus sits
 * right after a navigation). MUI's focus trap makes focus-on-body with a modal
 * open unusual, not impossible — a transition frame, a nested dialog, a
 * `disableEnforceFocus` — and the cost of being wrong is the reader stepping to
 * another subject BEHIND the editor they are working in.
 *
 * A plain document probe is safe here because no `Dialog` in this app is
 * `keepMounted`: a closed one is unmounted and takes its `role` with it.
 */
export function isDialogOpen(doc: Document | null | undefined): boolean {
  if (!doc) return false;
  return doc.querySelector('[role="dialog"], [role="alertdialog"]') !== null;
}

/** −1 for „previous subject", +1 for „next", `null` for every other key.
 *
 * Deliberately strict about the modifiers: `Alt+←` alone stays the browser's
 * Back, and a Ctrl or Meta on top belongs to the operating system. */
export function subjectStep(event: {
  key: string;
  altKey: boolean;
  shiftKey: boolean;
  ctrlKey: boolean;
  metaKey: boolean;
}): -1 | 1 | null {
  if (!event.altKey || !event.shiftKey || event.ctrlKey || event.metaKey) return null;
  if (event.key === 'ArrowLeft') return -1;
  if (event.key === 'ArrowRight') return 1;
  return null;
}
