// German strings for the worksheet generator (sections/worksheet/* +
// lib/lineatur.ts preset labels). Pre-i18n message catalog — key tree mirrors
// a future i18next `worksheet` namespace.

export const worksheet = {
  pageTitle: 'Lineatur-Vorlage · kurrentschrift',
  title: 'Lineatur-Vorlage zum Schreiben üben',
  //   preserves the DIN&nbsp;A4 non-breaking space from the JSX original.
  intro:
    'Hilfslinien für deutsche Schreibschrift auf DIN A4. Wähle eine der drei Start-Schriften als Ausgangspunkt, passe das Verhältnis von Ober-, Mittel- und Unterband frei an, schalte bei Bedarf Schräglinien dazu — und lade das Blatt als PDF zum Ausdrucken.',
  preview: 'Vorschau · DIN A4',
  // Footer spec fragments printed on the sheet (fmt templates).
  spec: {
    slant: 'Neigung {{deg}}°',
    pen: 'Feder {{deg}}°',
  },
  // The three start-script presets (lib/lineatur.ts PRESETS).
  presets: {
    kurrent: { label: 'Kurrent', note: '2 : 1 : 2 · ~30° geneigt · Spitzfeder' },
    suetterlin: { label: 'Sütterlin', note: '1 : 1 : 1 · aufrecht · gleichmäßige Strichstärke' },
    offenbacher: { label: 'Offenbacher', note: '2 : 1 : 2 · leicht geneigt · Breitfeder ~35°' },
  },
  config: {
    presetHeading: 'Start-Schrift',
    customSetting: 'Eigene Einstellung',
    ratioHeading: 'Verhältnis · Ober : Mittel : Unter',
    ratioAscender: 'Ober',
    ratioXHeight: 'Mittel',
    ratioDescender: 'Unter',
    xHeight: 'Mittelband (x-Höhe)',
    rowGap: 'Zeilenabstand',
    margin: 'Seitenrand',
    slantToggle: 'Schräglinien (Neigung)',
    slantAngle: 'Neigungswinkel',
    slantSpacing: 'Abstand der Schräglinien',
    penAngleToggle: 'Federwinkel (Stifthaltung)',
    penAngle: 'Federwinkel',
    penAngleHint:
      'Anstellwinkel der Feder zur Schreiblinie — als Winkelmarke oben links. Bei der Spitzfeder (Kurrent) kommt die Strichstärke aus dem Druck, nicht aus dem Winkel.',
    captionLabel: 'Titel / Name (optional)',
    captionPlaceholder: 'z. B. Kurrent',
    captionHelp: 'Erscheint mit Verhältnis/Neigung/Feder unten links; kurrentschrift.ink steht unten rechts.',
    download: 'Als PDF herunterladen',
  },
} as const;
