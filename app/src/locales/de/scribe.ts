// German strings for the public live-writing page (sections/scribe/*).
// Pre-i18n message catalog — mirrors a future i18next `scribe` namespace.

export const scribe = {
  // The page says its own name (the nav and every card link call it
  // "Federprobe" — that short name lives in common.nav.scribe) and, since the
  // SEO audit 2026-08-29, what it does in the words a person searches for;
  // the former heading line lives on as the lead's opener.
  heading: 'Federprobe: Text in Sütterlin schreiben lassen',
  // „die Feder" in prose, „Synthese"/„Synthese-Engine" only where the page
  // LABELS what it shows (the disclaimer below); the s allographs keep the
  // glossary's names — langes ſ / rundes s (website audit 2026-09-02).
  lead: 'Beliebige Wörter, live geschrieben: Tippe ein Wort oder einen Satz — die Feder schreibt es Zug um Zug in Sütterlin, mit den Übergängen zwischen den Buchstaben. Das lange ſ, das runde s und die Ligaturen (ch · ck · tz · ſt · qu · ß) werden automatisch gesetzt.',
  // The explanatory paragraph under the lead — what this page actually is
  // (a composed movement, not a font) and how far it reaches today.
  about:
    'Die Federprobe ist die Schreibhand dieses Projekts: Aus den Buchstaben der gemeinfreien Sütterlin-Ausgangsschrift von 1922, jeder einzeln nachgeschrieben, setzt sie deinen Text Zug um Zug zusammen — nicht als Schriftart, sondern als Bewegung der Feder, mit Ansatz, Auslauf und den Übergängen von Buchstabe zu Buchstabe. So siehst du, wie ein Wort aus deinem Brief geschrieben worden wäre, und kannst es neben das Original halten. Die Sütterlin ist bislang die einzige Schrift, die hier schreibt; Kurrent und Offenbacher sollen folgen. Den Link auf eine Schreibprobe kannst du kopieren und weitergeben.',
  inputLabel: 'Dein Text',
  inputPlaceholder: 'lesen und schreiben',
  // Under the field, left of the counter: the one thing about the field a
  // visitor cannot see (Enter writes a break instead of sending).
  inputHint: 'Mit Enter beginnst du eine neue Zeile.',
  // The Schriftgröße switch — three steps instead of a zoom (the browser's own
  // pinch zoom stays untouched).
  sizeLabel: 'Schriftgröße:',
  sizeAria: 'Schriftgröße der Schreibprobe',
  sizes: { klein: 'klein', mittel: 'mittel', gross: 'groß' },
  replay: '↻ noch einmal schreiben',
  // Examples the user can drop into the field.
  examplesLabel: 'Beispiele:',
  examples: ['lesen', 'schreiben', 'denen', 'das', 'Glück'],
  // Shown when some letters have no curated canonical yet (interpolates {{letters}}).
  missingNote: 'Diese Buchstaben sind noch nicht nachgeschrieben und bleiben darum frei: {{letters}}',
  emptyHint: 'Tippe oben etwas, um es geschrieben zu sehen.',
  // Compose fetch failed even after the cold-start retries (API unreachable).
  loadError: 'Die Feder muss gerade pausieren — der Server ist nicht erreichbar.',
  retry: 'Erneut versuchen',
  // Share the current text as a ?text= link (label swaps briefly after copying).
  copyLink: 'Link kopieren',
  copied: 'Link kopiert!',
  // Honest provenance note, mirroring the landing disclaimer.
  disclaimer: 'Synthese, klar gekennzeichnet — nachgebildete Schrift aus der Sütterlin-Ausgangsschrift von 1922, kein historisches Original.',
} as const;
