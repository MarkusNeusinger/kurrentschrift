// German strings for the public Schreibtafel page (sections/tafel/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `tafel` namespace.

export const tafel = {
  title: 'Schreibtafel',
  intro:
    'Die Vorlagen, nach denen hier geschrieben wird — die drei deutschen Ausgangsschriften nebeneinander. Wo eine Schrift schon nachgebildet ist, schreibt sich jeder Buchstabe Zug um Zug selbst; sonst zeigt die Tafel den Original-Scan der historischen Lehrtafel.',
  note: 'Die gemeinfreien Vorlagen liefern die Formen; die nachgeschriebene Bewegung — der Zug der Feder — ist die eigene Rekonstruktion dieses Projekts. Tippe einen geschriebenen Buchstaben an, um ihm noch einmal zuzusehen.',
  // The Original/Geschrieben toggle (only on a script that is already written).
  viewToggleAria: 'Ansicht umschalten',
  viewOriginal: 'Original',
  viewWritten: 'Geschrieben',
  // Alt text for the original scan.
  originalAlt: 'Original-Schreibtafel (Scan der Vorlage)',
  // Empty state when a written script has no finished (locked) letter yet.
  empty: 'Buchstaben erscheinen hier, sobald sie fertig nachgeschrieben und freigegeben sind.',
  // Per-script writing instrument (echoes the landing's "drei Federn"), by style_id.
  feder: {
    kurrent: 'Spitzfeder',
    suetterlin: 'Gleichzugfeder',
    offenbacher: 'Breitfeder',
  } as Record<string, string>,
  // Short state label shown next to a script title.
  state: {
    written: 'nachgeschrieben',
    original: 'noch nicht nachgeschrieben',
    pending: 'in Vorbereitung',
  },
  // Placeholder for a script without any chart source yet.
  pendingNote: 'Für diese Schrift liegt noch keine Vorlage bereit. Sie kommt später dazu.',
  // Per-source provenance, shown under each script that has a chart.
  source: {
    heading: 'Über die Vorlage',
    licenseLabel: 'Lizenz',
    originLink: 'Zur Originalquelle',
  },
  // Click/tap a written letter on the sheet to re-write it in place.
  replayHint: 'antippen zum Nachschreiben',
  // Tap/click-to-zoom on the original scan (OriginalScan): aria labels only —
  // the zoom-in/grab cursor signals the affordance, no visible hint (minimal).
  zoomIn: 'Tafel vergrößern',
  zoomOut: 'Tafel verkleinern',
} as const;
