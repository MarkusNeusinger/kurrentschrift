// @vitest-environment jsdom
//
// jsdom because half of this module asks the DOM what has the focus — the
// „nie in Eingabefeldern, nie in einem offenen Dialog" rule is a `closest()`
// call, and a string-based stand-in would pass while the real one failed.

import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  isInDialog,
  isTypingTarget,
  readShortcutsEnabled,
  SHORTCUTS_STORAGE_KEY,
  storeShortcutsEnabled,
  subjectStep,
} from './shortcuts';

/** A `localStorage` that answers, remembers, or refuses — the three states a
 * browser actually offers (normal, private window, site data blocked). */
function stubStorage(store: Map<string, string> | null) {
  if (store === null) {
    vi.stubGlobal('localStorage', {
      getItem() {
        throw new DOMException('denied', 'SecurityError');
      },
      setItem() {
        throw new DOMException('denied', 'SecurityError');
      },
    });
    return;
  }
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
  });
}

const el = (html: string): Element => {
  const host = document.createElement('div');
  host.innerHTML = html;
  return host.firstElementChild as Element;
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('the Kurztasten preference', () => {
  it('is on by default', () => {
    stubStorage(new Map());
    expect(readShortcutsEnabled()).toBe(true);
  });

  it('round-trips both ways', () => {
    const store = new Map<string, string>();
    stubStorage(store);
    storeShortcutsEnabled(false);
    expect(store.get(SHORTCUTS_STORAGE_KEY)).toBe('aus');
    expect(readShortcutsEnabled()).toBe(false);
    storeShortcutsEnabled(true);
    expect(readShortcutsEnabled()).toBe(true);
  });

  it('reads a value it did not write as the default', () => {
    // Something else wrote the key, or an older build used another vocabulary:
    // an unreadable preference is not a decision to switch the feature off.
    stubStorage(new Map([[SHORTCUTS_STORAGE_KEY, 'vielleicht']]));
    expect(readShortcutsEnabled()).toBe(true);
  });

  it('survives a storage that throws on every access', () => {
    stubStorage(null);
    expect(readShortcutsEnabled()).toBe(true);
    // And writing must not take the switch down with it — the preference is
    // simply not remembered past this session.
    expect(() => storeShortcutsEnabled(false)).not.toThrow();
  });

  it('survives a browser with no storage object at all', () => {
    vi.stubGlobal('localStorage', undefined);
    expect(readShortcutsEnabled()).toBe(true);
    expect(() => storeShortcutsEnabled(false)).not.toThrow();
  });
});

describe('isTypingTarget', () => {
  it('is true for everything that takes typed characters', () => {
    expect(isTypingTarget(el('<input />'))).toBe(true);
    expect(isTypingTarget(el('<textarea></textarea>'))).toBe(true);
    expect(isTypingTarget(el('<select></select>'))).toBe(true);
    expect(isTypingTarget(el('<div contenteditable="true"></div>'))).toBe(true);
    expect(isTypingTarget(el('<div role="textbox"></div>'))).toBe(true);
    expect(isTypingTarget(el('<div role="combobox"></div>'))).toBe(true);
  });

  it('is true for a child of an editable element', () => {
    // Focus often sits on a span inside the editable host.
    const host = el('<div contenteditable="true"><span>a</span></div>');
    expect(isTypingTarget(host.querySelector('span'))).toBe(true);
  });

  it('is false for the controls the binding is meant to work over', () => {
    expect(isTypingTarget(el('<button>öffnen</button>'))).toBe(false);
    expect(isTypingTarget(el('<div></div>'))).toBe(false);
    expect(isTypingTarget(el('<a href="#x">zur Tafel</a>'))).toBe(false);
    expect(isTypingTarget(null)).toBe(false);
  });
});

describe('isInDialog', () => {
  it('is true anywhere inside an open dialog — the wizard owns its own keys', () => {
    const dialog = el('<div role="dialog"><div><button>weiter</button></div></div>');
    expect(isInDialog(dialog.querySelector('button'))).toBe(true);
    expect(isInDialog(el('<div role="alertdialog"></div>'))).toBe(true);
  });

  it('is false on the page behind it', () => {
    expect(isInDialog(el('<button>öffnen</button>'))).toBe(false);
    expect(isInDialog(null)).toBe(false);
  });
});

describe('subjectStep', () => {
  const event = (over: Partial<KeyboardEvent>) => ({
    key: 'ArrowRight',
    altKey: true,
    shiftKey: true,
    ctrlKey: false,
    metaKey: false,
    ...over,
  });

  it('reads Alt+Shift+←/→', () => {
    expect(subjectStep(event({ key: 'ArrowRight' }))).toBe(1);
    expect(subjectStep(event({ key: 'ArrowLeft' }))).toBe(-1);
  });

  it('leaves the browser its own Alt+←', () => {
    // THE reason for P1-Q11 (b): Alt+← is Back on Windows and Linux, and the
    // admin's linking doctrine lives off the back button. Without Shift this
    // module must not claim the key.
    expect(subjectStep(event({ key: 'ArrowLeft', shiftKey: false }))).toBeNull();
    expect(subjectStep(event({ key: 'ArrowRight', shiftKey: false }))).toBeNull();
  });

  it('claims nothing with a further modifier or another key', () => {
    expect(subjectStep(event({ ctrlKey: true }))).toBeNull();
    expect(subjectStep(event({ metaKey: true }))).toBeNull();
    expect(subjectStep(event({ altKey: false }))).toBeNull();
    expect(subjectStep(event({ key: 'ArrowDown' }))).toBeNull();
    // No single-letter shortcuts exist, by decision (§5.1 Idee 18).
    expect(subjectStep(event({ key: 'n' }))).toBeNull();
    expect(subjectStep(event({ key: 'j' }))).toBeNull();
  });
});
