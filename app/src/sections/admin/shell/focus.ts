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
// Pure functions only — each view reads its own focus out of `useSearchParams`
// through the readers below, and the unit tests cover the parsing/derivation
// here. (The comment used to point at a `useFocus.ts` that never existed.)

import { LETTER_BY_KEY, LETTERS, glyphKeyFor } from '@/domain/glyphs';
import { shapeText } from '@/domain/shaping';
import { paths } from '@/routes/paths';
import { DEFAULT_LIST_VIEW, LIST_PARAMS, type ListView } from '@/sections/admin/shell/listState';

// Query parameter names, deliberately short — they end up in every deep link.
//
// `h` is the own HAND, and it is the one parameter that is not a subject: it
// says under WHICH hand the subject was looked at. A link the Korb or a task
// carries is otherwise scope-blind — it names the letter and leaves the second
// half of the premise to whatever the browser happened to remember
// (admin-redesign.md Q2 a). It is optional everywhere and never part of a
// page's title: the subject did not change because the hand did.
//
// In this phase it is WRITTEN and carried, not yet ADOPTED: nothing feeds a
// URL hand back into the active scope, so a pasted link states which hand it
// was filed under without switching the workbench to it. That is deliberate —
// adopting it needs a rule for the case where the URL and the picker disagree,
// and the row itself gets its own `work_items.hand_id` in Phase 3 (V7) — but
// it is the reason nobody should read `h=` as „this page acts on that hand".
export const FOCUS_PARAMS = { glyph: 'g', left: 'l', right: 'r', word: 'w', specimen: 's', hand: 'h' } as const;

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
//
// `strip`/`fassung`/`box` are the address of ONE written word box (V7). They
// are WRITTEN and not yet read: a Korb row filed on a box resolves to the strip
// surface with them, so the link is complete the day the surface opens on a
// single box — which is Phase 4 („Unterrouten erst, wenn die Nachfahr-Liste
// eine eigene Fläche wird", V2). Until then they name where the reader has to
// look rather than taking them there, which is a better link than none.
export const EIGENHAND_PARAMS = {
  reiter: 'reiter',
  item: 'item',
  wort: 'wort',
  strip: 'strip',
  fassung: 'fassung',
  box: 'box',
} as const;

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

// A hand id is `<schreiber>-<stil>`. This is WEAKER than
// `core/eigenhand/ids.py:HAND_ID`, on purpose and worth saying plainly: the
// server's pattern pins the suffix to a known style, this one only asks for
// hyphenated lowercase, so `h=mn-fraktur` and even a plate id like
// `h=suetterlin-1922-norm` pass it. Pinning the suffix would mean a second
// copy of `STYLE_IDS` in the SPA, and the module that HAS the styles — from
// the server's own payload — is `handScope.ts`, which is also the module that
// decides which hands exist at all. What is left here is the one job a pure
// reader can do: keep a typo or a pasted sentence out of every link the view
// then writes, dropped once, here, instead of travelling along.
const HAND_ID = /^[a-z0-9]+(?:-[a-z0-9]+)+$/;

export function readHandFocus(params: URLSearchParams): string | null {
  const hand = params.get(FOCUS_PARAMS.hand);
  return hand && HAND_ID.test(hand) ? hand : null;
}

/**
 * The hand carried through a focus change in a view that writes a FRESH query.
 *
 * It was written for the two views that still rewrote their whole query when
 * the subject changed: an `h=` off a Korb link evaporated on the first click,
 * so the link was scoped and the very next step was not. Since all three
 * overviews became work lists they all MERGE their query instead — the
 * Buchstaben view's pattern, named in this docstring before it was the rule —
 * and that carries the hand for free along with the list state, so no view
 * calls this today. It stays as the answer for a surface that has no list
 * state to keep and therefore has no reason to merge. The jumps BETWEEN views
 * pass the hand explicitly to the url builders, from the admin scope — so a
 * scope holds for a whole walk, not just for the next click.
 */
export function keepHand(params: URLSearchParams, next: Record<string, string>): Record<string, string> {
  const hand = readHandFocus(params);
  return hand ? { ...next, [FOCUS_PARAMS.hand]: hand } : next;
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
//
// `hand` is the LAST argument of each, and last for a reason: every existing
// call site and every URL already in a task stays byte-identical without it,
// and a surface that knows the hand only has to append it.
export const lettersUrl = (glyphKey?: string | null, hand?: string | null): string =>
  withParams(paths.admin.letters, [
    [FOCUS_PARAMS.glyph, glyphKey],
    [FOCUS_PARAMS.hand, hand],
  ]);

export const joinsUrl = (leftKey?: string | null, rightKey?: string | null, hand?: string | null): string =>
  withParams(paths.admin.joins, [
    [FOCUS_PARAMS.left, leftKey],
    [FOCUS_PARAMS.right, rightKey],
    [FOCUS_PARAMS.hand, hand],
  ]);

export const wordsUrl = (text?: string | null, specimenId?: string | null, hand?: string | null): string =>
  withParams(paths.admin.words, [
    [FOCUS_PARAMS.word, text],
    [FOCUS_PARAMS.specimen, specimenId],
    [FOCUS_PARAMS.hand, hand],
  ]);

// The Eigenhand builder takes an OPTIONS object for everything past the view,
// so the parameters that came later — `h=` (the shared hand), the box address
// `strip`/`fassung`/`box`, the display mode — slot in without breaking a single
// call site. Called with nothing it yields the clean `/admin/eigenhand`, which
// lands on the Bestand by the reader's own fallback.
//
// `modus` is the LIST/GALLERY display mode (`?ansicht=`, `shell/listState.ts`),
// not the Unteransicht — the first argument is that, and the two words are kept
// apart everywhere (author decision Q1 c). A jump passes it where it wants one
// of the two surfaces in particular; the default is left out, as everywhere.
export const eigenhandUrl = (
  ansicht?: EigenhandAnsicht | null,
  opts?: {
    item?: string | null;
    wort?: string | null;
    hand?: string | null;
    strip?: string | null;
    fassung?: string | null;
    box?: number | null;
    modus?: ListView | null;
  },
): string =>
  withParams(paths.admin.eigenhand, [
    [EIGENHAND_PARAMS.reiter, ansicht],
    [EIGENHAND_PARAMS.item, opts?.item],
    [EIGENHAND_PARAMS.wort, opts?.wort],
    [EIGENHAND_PARAMS.strip, opts?.strip],
    [EIGENHAND_PARAMS.fassung, opts?.fassung],
    // Box 0 is a real box — `withParams` drops falsy values, so the index goes
    // in as its own string rather than as a number that vanishes at zero.
    [EIGENHAND_PARAMS.box, opts?.box === null || opts?.box === undefined ? null : String(opts.box)],
    [FOCUS_PARAMS.hand, opts?.hand],
    [LIST_PARAMS.view, opts?.modus === DEFAULT_LIST_VIEW ? null : opts?.modus],
  ]);

// The address of ONE written word box, as `work_items.specimen_id` carries it:
// `S0041/F02#2` — strip, Fassung, box index (V7). The box INDEX and not the
// word, for the reason the Rohzahlen chips give: a row can hold the same word
// twice, and a reference by text would point at two places.
export const stripBoxSpecimen = (strip: string, fassung: string, boxIndex: number): string =>
  `${strip}/${fassung}#${boxIndex}`;

const STRIP_BOX_SPECIMEN = /^([^/]+)\/([^/#]+)#(\d+)$/;

/** That address read back, or `null` for anything that is not one — a filed id
 * is free text in the column, so the link builder has to be able to refuse. */
export function readStripBoxSpecimen(id: string | null): { strip: string; fassung: string; box: number } | null {
  const match = id === null ? null : STRIP_BOX_SPECIMEN.exec(id);
  return match ? { strip: match[1], fassung: match[2], box: Number(match[3]) } : null;
}

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
