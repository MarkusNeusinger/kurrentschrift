// How wide the label column of a penalty breakdown has to be — its own module
// because `scoreParts.tsx` may only export components (react-refresh).

/** Characters in the longest of `labels` — the width the label column needs. */
export function labelColumnChars(labels: readonly string[]): number {
  // NFC first: „Deckungslücke" is 13 characters with a precomposed ü and 14
  // with a combining one, and only the precomposed count matches what the
  // monospace face actually advances.
  return labels.reduce((widest, label) => Math.max(widest, label.normalize('NFC').length), 0);
}
