// The trace bench's frozen development split — the ten hand-traced words every
// §14 tracebench number was measured against. Deliberately re-declared from
// `tools/tracebench/sets.py` (TRACEBENCH_DEV_IDS) the way `registration.ts`
// re-declares the schema bounds: the list is append-never by pre-registration
// (docs/proposals/tintenfolger.md §1/§2.4), so the copy cannot drift.
//
// The editor and the review section use it to WARN, not to block: re-saving
// one of these specimens changes the frozen ruler's reference and demands a
// dated §14 re-baseline plus a fixture refill — a deliberate owner act, never
// a casual wobble fix.
export const TRACEBENCH_DEV_SPECIMEN_IDS: ReadonlySet<string> = new Set([
  'die',
  'laden',
  'linken',
  'mit',
  'muß',
  'und',
  'unter',
  'Wer',
  'will',
  'zwei',
]);

export const isDevSetSpecimen = (kind: string, specimenId: string): boolean =>
  kind === 'word' && TRACEBENCH_DEV_SPECIMEN_IDS.has(specimenId);
