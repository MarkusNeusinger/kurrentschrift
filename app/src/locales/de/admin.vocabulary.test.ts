// One noun for the line, kept from rotting back.
//
// Author decision 2026-09-18, Q8 (b) (`docs/proposals/admin-redesign.md` §5.0):
// the followed or traced line of a word is „Bahn" in EVERY German admin string,
// plate and strip alike. Before the rule the same line was „Pfad" on the
// Eigenhand page, „Nachfahrung" and „Pfad" on the two layer buttons, „Spur" in
// the Wörter intro and „Bahn" in the chips — a drift nobody notices while
// adding one string at a time, and the reason it is pinned here instead of
// reviewed by eye.
//
// What stays legal on purpose:
// * the locale KEYS (`pfadShow`, `layerPath`, the `belege` namespace) — they
//   point at `eigenhand_strips.pfade`, whose glossary name „Streifen-Pfad" is
//   the name of the FIELD and never a UI word;
// * a terminal command inside a German sentence — it is code, so
//   `tools.eigenhand.pfad` is copied verbatim or it does not run;
// * „Tintenpfad" as the follower's own name, which the Herkunfts-Chip is meant
//   to say where the row actually records it.

import { describe, expect, it } from 'vitest';

// The module under test, as its sibling — not through `@/locales/admin`, which
// the bundle guard in eslint.config.js reserves for admin directories. A test
// file is never reachable from `main.tsx`, so it cannot pull the admin strings
// into the public bundle the guard protects.
import { admin } from './admin';

// The retired names of the line. Case-insensitive, so „Pfade", „Schreibpfad"
// and „Nachfahrungen" are caught as well as the bare nouns.
const RETIRED = /nachfahrung|spur|pfad/i;

// Cut out before the check: module paths (`tools.eigenhand.pfad`,
// `tools/laufform/harvest.py`) and the follower's proper name.
const CODE = /\btools[./][\w./-]+|Tintenpfad/g;

// The six namespaces that talk about a drawn line. The rest of the catalog
// (chart editor, wizard, errors) never names one. `compare` carries no retired
// noun today and is listed anyway: it draws the same line over the same crops
// and reaches into `belege` for its tooltip, so leaving it out would keep one
// door unguarded for the sake of one array element.
const NAMESPACES = ['werkbank', 'words', 'belege', 'joins', 'eigenhand', 'compare'] as const;

/** Every string in the tree, each with the dotted path that leads to it. */
function strings(value: unknown, path: string): [string, string][] {
  if (typeof value === 'string') return [[path, value]];
  if (value !== null && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, inner]) =>
      strings(inner, `${path}.${key}`),
    );
  }
  return [];
}

const walked = NAMESPACES.flatMap((namespace) => strings(admin[namespace], namespace));

describe('admin vocabulary', () => {
  it('names the line „Bahn" in every namespace that draws one', () => {
    for (const [key, value] of walked) {
      expect(value.replace(CODE, ''), key).not.toMatch(RETIRED);
    }
  });

  it('actually walks the catalog, so the guard cannot pass on an empty sweep', () => {
    // A guard that reaches no string is green forever. Both halves are pinned:
    // the walk finds the strings, and the pattern recognises what it looks for.
    expect(walked.length).toBeGreaterThan(300);
    expect(walked.some(([key]) => key === 'eigenhand.pfadShow')).toBe(true);
    expect('Gespeicherte Spur zeigen').toMatch(RETIRED);
  });

  it('lets a terminal command and the follower keep their names', () => {
    expect('Lokal folgen: uv run python -m tools.eigenhand.pfad --apply.'.replace(CODE, '')).not.toMatch(RETIRED);
    expect('automatisch (Tintenpfad)'.replace(CODE, '')).not.toMatch(RETIRED);
  });
});
