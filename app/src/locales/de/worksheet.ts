// German strings for the worksheet generator (sections/worksheet/* +
// lib/lineatur.ts preset labels). Pre-i18n message catalog — key tree mirrors
// a future i18next `worksheet` namespace.

export const worksheet = {
  title: 'Lineatur-Vorlage zum Schreiben üben',
  //   preserves the DIN&nbsp;A4 non-breaking space from the JSX original.
  intro:
    'Hilfslinien für deutsche Schreibschrift auf DIN A4. Wähle eine der drei Start-Schriften, passe das Verhältnis von Ober-, Mittel- und Unterband nach Belieben an, nimm auf Wunsch Schräglinien dazu — und lade das Blatt als PDF zum Ausdrucken.',
  preview: 'Vorschau · DIN A4',
  // Footer spec fragments printed on the sheet (fmt templates).
  spec: {
    slant: 'Schräglage {{deg}}°',
    pen: 'Feder {{deg}}°',
  },
  // The three start-script presets (lib/lineatur.ts PRESETS).
  presets: {
    kurrent: { label: 'Kurrent', note: '2 : 1 : 2 · Schräglage 60–70° (um 1900) · Spitzfeder, Schwellzug im Abstrich' },
    suetterlin: { label: 'Sütterlin', note: '1 : 1 : 1 · senkrecht (90°) · Gleichzugfeder (gleichmäßiger Strich)' },
    offenbacher: { label: 'Offenbacher', note: '2 : 3 : 2 · Schräglage 75–80° · Breitfeder 15–20°' },
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
    lineSystemHeading: 'Liniensystem',
    lineSystemFour: 'Vier Linien',
    lineSystemTwo: 'Doppellinie',
    lineSystemOne: 'Nur Grundlinie',
    lineSystemHint:
      'Die klassische Lern-Progression: vier Linien für den Anfang, die Doppellinie fürs Mittelband, später nur noch die Grundlinie.',
    slantToggle: 'Schräglinien (Schräglage)',
    slantAngle: 'Schräglage',
    slantSpacing: 'Abstand der Schräglinien',
    penAngleToggle: 'Federwinkel (Stifthaltung)',
    penAngle: 'Federwinkel',
    penAngleHint:
      'Federwinkel: Winkel der Federkante zur Schreiblinie — als Winkelmarke oben links. Bei der Spitzfeder (Kurrent) kommt die Strichstärke aus dem Druck, nicht aus dem Winkel.',
    rulingHeading: 'Druckfarbe',
    rulingDruck: 'Schwarz (Druck)',
    rulingSchulheft: 'Schulheft um 1900',
    rulingNote:
      'Gedruckte Schulheft-Lineatur ist ab 1871 belegt: blaue Schreiblinien, ab etwa 1900 mit roter Randleiste — sie hielt den Korrekturrand für den Lehrer frei.',
    marginToggle: 'Rote Randleiste (Korrekturrand)',
    captionLabel: 'Titel / Name (optional)',
    captionPlaceholder: 'z. B. Kurrent',
    captionHelp: 'Erscheint mit Verhältnis/Schräglage/Federwinkel unten links; kurrentschrift.ink steht unten rechts.',
    download: 'Als PDF herunterladen',
  },
} as const;
