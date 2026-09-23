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
 * the hand last CHOSEN for that script, else to the script's ONLY hand, else to
 * nothing.
 *
 * The third step is the author's tip of the open taste question „Hand: —"
 * (admin-redesign.md §15.5 Nr. 13, 2026-09-23): a fresh browser — the tablet
 * above all — stood on an empty field beside a script with exactly one hand to
 * offer, and had to be told the obvious once per device. It is „the only one",
 * never „the first one", and that difference is what keeps V19's objection
 * answered: a sole candidate is not a pick anybody could have made differently,
 * so the scope it writes into every Korb link is the one the author would have
 * chosen. With two hands of one script the first by code point WOULD be the
 * unchosen scope V19 was written against, so the field stays empty there until
 * a hand is picked — and it stays empty for a script with no written hand,
 * rather than inventing an id no read has returned (Q25 a).
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
  if (last && ofStyle.includes(last)) return last;
  return ofStyle.length === 1 ? ofStyle[0] : null;
}
