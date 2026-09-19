// Which own hand the workbench is on — and why it can never be a foreign one.
//
// Two facts collide here. A Vorlage belongs to exactly ONE script
// (`templates.style_id`), and an Eigenhand id spells its script in its own
// suffix (`<schreiber>-<stil>`, core/eigenhand/ids.py). So „the active hand" is
// not a free choice: a Sütterlin Vorlage beside a Kurrent hand would put two
// scripts' numbers under one heading, which is the label error the Scope-Leiste
// exists to end (admin-redesign.md V19, Q25 a). The rule is ONE function here
// rather than a branch in the bar, the picker and the URL reader, because three
// copies of a coupling rule is how the scopes drifted apart in the first place.
//
// The style list is NOT a twin of `core/eigenhand/ids.py:STYLE_IDS`:
// `GET /eigenhand/hands` ships its `styles`, so the suffix rule reads the
// server's list and there is nothing to keep in sync.
//
// Nothing here knows a writer prefix. `mn-` is one author's shorthand, not a
// rule — the hand a Vorlage works with comes from the DB, never from a literal.

/** A hand the admin may work on, with the script it belongs to. */
export type HandCandidate = { id: string; style: string | null };

/** The script a `<schreiber>-<stil>` id names, or null if it names none. */
export function styleOfHand(hand: string, styles: readonly string[]): string | null {
  for (const style of styles) if (hand.endsWith(`-${style}`)) return style;
  return null;
}

/**
 * Every hand the admin knows, from the two reads that each know half of them.
 *
 * `GET /eigenhand/hands` is built from sheets ∪ Fassungen
 * (`core/database/repositories.py`), so a hand whose setup was typed before its
 * first sheet is invisible there; `GET /eigenhand/setups` carries exactly those
 * — and states their style outright instead of leaving it to the suffix, which
 * is why a setup wins over the derived reading.
 *
 * Sorted by a plain code-point compare, not `localeCompare`: this order is the
 * order the Eigenhand picker offers, and a list that depends on the browser's
 * locale would put the same hands in a different order on two machines.
 */
export function handCandidates(
  hands: readonly string[],
  setups: readonly { hand: string; style: string }[],
  styles: readonly string[],
): HandCandidate[] {
  const byId = new Map<string, HandCandidate>();
  for (const id of hands) byId.set(id, { id, style: styleOfHand(id, styles) });
  for (const setup of setups) byId.set(setup.hand, { id: setup.hand, style: setup.style });
  return [...byId.values()].sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

/** The hands of one script — the only legal picks while that Vorlage is open. */
export const handsOfStyle = (candidates: readonly HandCandidate[], styleId: string | null): string[] =>
  styleId ? candidates.filter((c) => c.style === styleId).map((c) => c.id) : [];

/** The script of a known hand, or null when it is none of the candidates. */
export const handStyle = (candidates: readonly HandCandidate[], hand: string): string | null =>
  candidates.find((c) => c.id === hand)?.style ?? null;

/**
 * V19 in one function: the active hand always belongs to the Vorlage's script.
 *
 * Keep what is chosen while it fits; on a switch to another script fall back to
 * the hand last CHOSEN for that script, else to nothing. Two fallbacks, not
 * three — V19 reads „die zuletzt gewählte Hand dieses Stils oder leer", and the
 * tempting third („else its first hand") would put a scope nobody picked under
 * the heading and into every Korb link the basket writes. An empty field is the
 * honest answer, both for a script whose own hand has not been written yet and
 * for one whose hands were never looked at.
 */
export function resolveHand(
  current: string | null,
  styleId: string | null,
  candidates: readonly HandCandidate[],
  lastByStyle: Readonly<Record<string, string>>,
): string | null {
  if (!styleId) return null;
  const ofStyle = handsOfStyle(candidates, styleId);
  if (current && ofStyle.includes(current)) return current;
  const last = lastByStyle[styleId];
  return last && ofStyle.includes(last) ? last : null;
}
