// German strings for the public live-writing page (sections/scribe/*).
// Pre-i18n message catalog — mirrors a future i18next `scribe` namespace.

export const scribe = {
  heading: 'Beliebige Wörter live geschrieben',
  lead: 'Tippe ein Wort oder einen Satz — der synthetisierte Duktus schreibt es Zug um Zug in Sütterlin, mit den Übergängen zwischen den Buchstaben. Lang-s, Schluss-s und die Ligaturen (ch · ck · tz · ſt · qu · ß) werden automatisch gesetzt.',
  inputLabel: 'Dein Text',
  inputPlaceholder: 'lesen und schreiben',
  replay: '↻ nochmal schreiben',
  // Examples the user can drop into the field.
  examplesLabel: 'Beispiele:',
  examples: ['lesen', 'schreiben', 'denen', 'das', 'Glück'],
  // Shown when some letters have no curated canonical yet (interpolates {{letters}}).
  missingNote: 'Noch nicht kuratiert und darum ausgelassen: {{letters}}',
  emptyHint: 'Tippe oben etwas, um es geschrieben zu sehen.',
  // Compose fetch failed even after the cold-start retries (API unreachable).
  loadError: 'Der Schreibdienst ist gerade nicht erreichbar — die Feder muss kurz pausieren.',
  retry: 'Erneut versuchen',
  // Share the current text as a ?text= link (label swaps briefly after copying).
  copyLink: 'Link kopieren',
  copied: 'Link kopiert!',
  // Honest provenance note, mirroring the landing disclaimer.
  disclaimer: 'Synthese, klar gekennzeichnet — nachgebildete Schrift aus der Sütterlin-Ausgangsschrift 1922, kein historisches Original.',
} as const;
