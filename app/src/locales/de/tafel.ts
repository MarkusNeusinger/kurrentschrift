// German strings for the public Schreibtafel page (sections/tafel/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `tafel` namespace.

export const tafel = {
  title: 'Schreibtafel',
  intro:
    'Die Vorlage, nach der hier geschrieben wird. Schalte zwischen dem Original-Scan und der nachgeschriebenen Fassung um: In der nachgeschriebenen Ansicht schreibt sich jeder Buchstabe Zug um Zug selbst — in der Reihenfolge der Feder. Tippe einen Buchstaben an, um ihm beim Schreiben noch einmal zuzusehen.',
  // The Original/Geschrieben toggle.
  viewToggleAria: 'Ansicht umschalten',
  viewOriginal: 'Original',
  viewWritten: 'Geschrieben',
  // Caption under the original scan.
  originalAlt: 'Original-Schreibtafel (Scan der Vorlage)',
  // Empty state when no letter is finished (locked) and written yet.
  empty: 'Buchstaben erscheinen hier, sobald sie fertig nachgeschrieben und freigegeben sind.',
  // Per-card / modal helpers.
  replayHint: 'antippen zum Nachschreiben',
  close: 'Schließen',
} as const;
