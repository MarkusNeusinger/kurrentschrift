// What the three admin views are looking at, and how that travels in the URL.
//
// The redesign put ONE subject in front of the admin at a time — a letter, a
// join or a word — and made the three views lenses on it (docs/proposals/
// optimierungs-werkbank.md §2, extended to the whole admin). The subject lives
// in the query string rather than in a context, for three reasons: a view is
// linkable (the Korb, a lens thumbnail and the deep links all just navigate),
// the browser's back button walks the inspection history, and a reload lands
// where the work was.
//
// Pure functions only — the components read them through the hooks in
// useFocus.ts, and the unit tests cover the parsing/derivation here.

import { LETTER_BY_KEY, LETTERS, glyphKeyFor } from '@/domain/glyphs';
import { shapeText } from '@/domain/shaping';
import { paths } from '@/routes/paths';

// Query parameter names, deliberately short — they end up in every deep link.
export const FOCUS_PARAMS = { glyph: 'g', left: 'l', right: 'r', word: 'w', specimen: 's' } as const;

// Eigenhand is the one admin area whose URL carries a PLACE rather than a
// subject: the page holds four surfaces that answer four different questions
// about one hand, and they are too big to stand under each other. The names
// are spelled out because they are read by a human in the address bar, where
// a one-letter parameter would only save the author typing he never does.
//
// The parameter is `reiter`, not `ansicht`: `ansicht` belongs to the
// list/gallery display mode of the overviews (`?ansicht=liste|galerie`, plan
// V14, author decision Q1 c of 2026-09-19), while `reiter` means „which tab
// of this page" everywhere in the admin — the same word the Wörter overview's
// tabs take. The German-domain identifiers below keep saying Ansicht, because
// a sub-view IS an Unteransicht; only the spelled URL word is `reiter`.
//
// `item`/`wort` are the strips filter. They are here and not inside the
// gallery because the split tore producer and consumer apart: a coverage cell
// sits on `bestand`, the strips it selects on `streifen`.
export const EIGENHAND_PARAMS = { reiter: 'reiter', item: 'item', wort: 'wort' } as const;

// The first entry is the default: a bare /admin/eigenhand — and any nonsense
// a hand-typed URL carries — lands on the Bestand.
export const EIGENHAND_ANSICHTEN = ['bestand', 'streifen', 'statistik', 'drucken'] as const;

export type EigenhandAnsicht = (typeof EIGENHAND_ANSICHTEN)[number];

export type EigenhandFocus = {
  ansicht: EigenhandAnsicht;
  item: string | null;
  wort: string | null;
};

export interface LetterFocus {
  glyphKey: string | null;
}

export interface JoinFocus {
  leftKey: string | null;
  rightKey: string | null;
}

export interface WordFocus {
  text: string | null;
  specimenId: string | null;
}

// A key is only usable if the glyph registry knows it — a hand-edited URL must
// land on the view's overview rather than on a lens for a glyph that does not
// exist. `null` (absent parameter) is the overview, and so is nonsense.
const knownKey = (value: string | null): string | null =>
  value && LETTER_BY_KEY[value] ? value : null;

export function readLetterFocus(params: URLSearchParams): LetterFocus {
  return { glyphKey: knownKey(params.get(FOCUS_PARAMS.glyph)) };
}

export function readJoinFocus(params: URLSearchParams): JoinFocus {
  const leftKey = knownKey(params.get(FOCUS_PARAMS.left));
  const rightKey = knownKey(params.get(FOCUS_PARAMS.right));
  // A half-given pair has no join to show — treat it as no focus at all.
  return leftKey && rightKey ? { leftKey, rightKey } : { leftKey: null, rightKey: null };
}

export function readWordFocus(params: URLSearchParams): WordFocus {
  const text = (params.get(FOCUS_PARAMS.word) ?? '').trim();
  return { text: text || null, specimenId: params.get(FOCUS_PARAMS.specimen) || null };
}

const knownAnsicht = (value: string | null): value is EigenhandAnsicht =>
  Boolean(value) && (EIGENHAND_ANSICHTEN as readonly string[]).includes(value as string);

export function readEigenhandFocus(params: URLSearchParams): EigenhandFocus {
  const ansicht = params.get(EIGENHAND_PARAMS.reiter);
  return {
    ansicht: knownAnsicht(ansicht) ? ansicht : EIGENHAND_ANSICHTEN[0],
    // Deliberately NOT run through `knownKey`: a coverage item is `a>b` or
    // `a@medial` or a bare key, and the strip search is free text. Neither is
    // a glyph registry key, so validating them here would silently drop every
    // join filter a bucket cell files.
    item: params.get(EIGENHAND_PARAMS.item) || null,
    wort: params.get(EIGENHAND_PARAMS.wort) || null,
  };
}

const withParams = (path: string, entries: Array<[string, string | null | undefined]>): string => {
  const params = new URLSearchParams();
  for (const [key, value] of entries) if (value) params.set(key, value);
  const query = params.toString();
  return query ? `${path}?${query}` : path;
};

// The three link builders every cross-view button goes through, so no surface
// hand-assembles a query string.
export const lettersUrl = (glyphKey?: string | null): string =>
  withParams(paths.admin.letters, [[FOCUS_PARAMS.glyph, glyphKey]]);

export const joinsUrl = (leftKey?: string | null, rightKey?: string | null): string =>
  withParams(paths.admin.joins, [
    [FOCUS_PARAMS.left, leftKey],
    [FOCUS_PARAMS.right, rightKey],
  ]);

export const wordsUrl = (text?: string | null, specimenId?: string | null): string =>
  withParams(paths.admin.words, [
    [FOCUS_PARAMS.word, text],
    [FOCUS_PARAMS.specimen, specimenId],
  ]);

// The Eigenhand builder takes an OPTIONS object for everything past the view,
// so the parameters still to come — `h=` (the shared hand) and the Phase-3
// strip deep link `strip`/`fassung`/`box` — slot in without breaking a single
// call site. Called with nothing it yields the clean `/admin/eigenhand`, which
// lands on the Bestand by the reader's own fallback.
export const eigenhandUrl = (
  ansicht?: EigenhandAnsicht | null,
  opts?: { item?: string | null; wort?: string | null },
): string =>
  withParams(paths.admin.eigenhand, [
    [EIGENHAND_PARAMS.reiter, ansicht],
    [EIGENHAND_PARAMS.item, opts?.item],
    [EIGENHAND_PARAMS.wort, opts?.wort],
  ]);

// The characters behind a glyph_key, for the free-text fields and the pair
// preview: the composer is driven by TEXT (it shapes it itself), so a view that
// knows only keys has to spell them back out.
export const textForKey = (glyphKey: string): string => LETTER_BY_KEY[glyphKey]?.glyph ?? '';

export const textForPair = (leftKey: string, rightKey: string): string =>
  `${textForKey(leftKey)}${textForKey(rightKey)}`;

// The shaped glyph_keys behind a typed text — the same mapping the server does,
// so a freely typed combination is identified exactly as a harvested one is.
export const keysOfText = (text: string): string[] =>
  shapeText(text)
    .filter((slot) => slot.key && !slot.space)
    .map((slot) => slot.key as string);

// The adjacent JOINS of a typed word: every neighbouring pair of slots that
// both join and are not separated by a space. This is the same adjacency rule
// core/compose.py generates Übergänge for, so the chips a word view offers are
// exactly the joins the engine drew.
export function joinsOfText(text: string): Array<{ leftKey: string; rightKey: string }> {
  const slots = shapeText(text).filter((slot) => slot.key || slot.space);
  const out: Array<{ leftKey: string; rightKey: string }> = [];
  for (let i = 0; i + 1 < slots.length; i++) {
    const a = slots[i];
    const b = slots[i + 1];
    if (!a.key || !b.key || a.space || b.space || !a.joins || !b.joins) continue;
    out.push({ leftKey: a.key, rightKey: b.key });
  }
  return out;
}

// A two-character combination shaped back into its two keys — null when the two
// characters fold into a closed-set ligature (ſt, ch, …), which is ONE glyph
// and therefore has no join to inspect or override.
export function pairKeysOfText(text: string): [string, string] | null {
  const keys = keysOfText(text);
  return keys.length === 2 ? [keys[0], keys[1]] : null;
}

// Neighbours of a letter in the registry order, for the ‹ › stepper: staying
// inside the letter's own group (lowercase, uppercase, …) keeps the step
// predictable — ‹ from `a` should not jump into the punctuation block.
export function neighbourLetters(glyphKey: string): { prev: string | null; next: string | null } {
  const letter = LETTER_BY_KEY[glyphKey];
  if (!letter) return { prev: null, next: null };
  const group = LETTERS.filter((l) => l.group === letter.group);
  const index = group.findIndex((l) => glyphKeyFor(l) === glyphKey);
  if (index < 0) return { prev: null, next: null };
  return {
    prev: index > 0 ? glyphKeyFor(group[index - 1]) : null,
    next: index + 1 < group.length ? glyphKeyFor(group[index + 1]) : null,
  };
}
