// German strings for the public Schreibtafel page (sections/tafel/*). Pre-i18n
// message catalog — key tree mirrors a future i18next `tafel` namespace.

export const tafel = {
  // `title` is the short name (nav, cards, breadcrumbs); `heading` the page's
  // H1 with the search term in it (SEO audit 2026-08-29, locales/de/seo.ts).
  title: 'Schreibtafel',
  heading: 'Schreibtafel: Sütterlin-, Kurrent- und Offenbacher-Alphabet',
  intro:
    'Die drei Schreibvorlagen, mit denen dieses Projekt beginnt, nebeneinander — nach ihnen wird hier geschrieben. Wo eine Schrift schon nachgebildet ist, schreibt sich jeder Buchstabe Zug um Zug selbst; sonst zeigt die Tafel den Original-Scan der historischen Lehrtafel.',
  note: 'Die gemeinfreien Vorlagen liefern die Formen; die nachgeschriebene Bewegung — der Zug der Feder — ist die eigene Rekonstruktion dieses Projekts. Tippe einen geschriebenen Buchstaben an, um ihm noch einmal zuzusehen.',
  // The Original/Geschrieben toggle (only on a script that is already written).
  viewToggleAria: 'Ansicht umschalten',
  viewOriginal: 'Original',
  viewWritten: 'Geschrieben',
  // Alt text for the original scan.
  originalAlt: 'Original-Schreibtafel (Scan der Vorlage)',
  // Empty state when a written script has no finished (locked) letter yet.
  empty: 'Buchstaben erscheinen hier, sobald sie fertig nachgeschrieben und freigegeben sind.',
  // Accessible label for the loader shown in the ruling while the glyphs load.
  loading: 'Buchstaben werden geladen …',
  // Batch fetch of the written letters failed (API unreachable after retries);
  // shown in the ruling with a retry button (label = de.common.boot.retry).
  loadError: 'Die Buchstaben konnten gerade nicht geladen werden — der Server ist nicht erreichbar.',
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
  // The printable Lesetafel (lib/lesetafel.ts, useLesetafelPdf): all three
  // Vorlagen on A4 — the written script as letters on a ruling, the others as
  // their original plates — to lay beside an old letter while deciphering.
  pdf: {
    button: 'Lesetafel als PDF',
    building: 'PDF wird erstellt …',
    hint: 'Alle drei Vorlagen auf A4 zum Ausdrucken — die Sütterlin Buchstabe für Buchstabe nachgeschrieben, Kurrent und Offenbacher als Originaltafel. Zum Danebenlegen beim Entziffern.',
    // Generic on purpose: the build can fail at the payload fetch, the plate
    // raster, the JPEG encoding or the composition — the console has the cause.
    error: 'Das PDF konnte gerade nicht erstellt werden. Bitte noch einmal versuchen.',
    filename: 'lesetafel-kurrentschrift.pdf',
    // Strings printed on the sheet itself (Helvetica, WinAnsi — no ſ).
    heading: 'Lesetafel',
    writtenLine: 'nachgeschrieben aus der gemeinfreien Vorlage — Synthese, kein Original',
    plateLine: 'Originaltafel (gemeinfrei), noch nicht nachgeschrieben',
    footer: 'kurrentschrift.ink/tafel',
    longS: 'langes s',
  },
  // Click/tap a written letter on the sheet: it re-writes itself in place and
  // opens the letter detail below (?g=<key>).
  replayHint: 'antippen: nachschreiben und im Detail ansehen',
  // The letter detail (LetterDetail.tsx, /tafel?g=<key>): stroke order,
  // Ansatz/Auslauf, the write-in at two tempi, look-alikes, a jump into the
  // Federprobe. Vision goal 3 („Buchstaben in Aktion").
  detail: {
    heading: 'Buchstabe im Detail',
    close: 'Detail schließen',
    animated: 'Zug um Zug',
    tempoLabel: 'Tempo',
    tempoNormal: 'normal',
    tempoSlow: 'langsam',
    strokeOrder: 'Strichfolge',
    strokeOrderAria: 'Strichfolge des Buchstabens mit nummerierten Zügen',
    // Stepper under the stroke-order view (interpolates {{n}} and {{total}}).
    step: 'Zug {{n}} von {{total}}',
    stepPrev: 'einen Zug zurück',
    stepNext: 'einen Zug weiter',
    stepAll: 'alle Züge',
    singleStroke: 'ein einziger Zug, ohne Absetzen',
    // Legend of the markers: numbered starts, the hollow rings at Ansatz/Auslauf.
    markers: 'Zahlen: Beginn jedes Zugs · Ringe: Ansatz und Auslauf zum Nachbarbuchstaben',
    lookalikes: 'Verwechsler',
    // Jump into the Federprobe with a word that contains the letter (interpolates {{word}}).
    inWord: 'im Wort sehen: „{{word}}“',
    unavailable: 'Für diesen Buchstaben liegt gerade keine nachgeschriebene Form vor.',
    // One sentence for the crawler page and the section hint.
    hint: 'Ein Tipp auf einen nachgeschriebenen Buchstaben öffnet ihn im Detail: die Strichfolge mit nummerierten Zügen, Ansatz und Auslauf, das Schreiben Zug um Zug in zwei Tempi, die Verwechsler daneben — und ein Sprung in die Federprobe, um ihn im Wort zu sehen.',
  },
  // Tap/click-to-zoom on the original scan (OriginalScan): aria labels only —
  // the zoom-in/grab cursor signals the affordance, no visible hint (minimal).
  zoomIn: 'Tafel vergrößern',
  zoomOut: 'Tafel verkleinern',
} as const;
