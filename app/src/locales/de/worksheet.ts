// German strings for the worksheet generator (sections/worksheet/* +
// lib/lineatur.ts preset labels). Pre-i18n message catalog — key tree mirrors
// a future i18next `worksheet` namespace.

export const worksheet = {
  title: 'Übungsblatt für die deutsche Schreibschrift',
  //   preserves the DIN&nbsp;A4 non-breaking space from the JSX original.
  intro:
    'Hilfslinien für die deutsche Schreibschrift auf DIN A4. Wähle eine der drei Ausgangsschriften, passe das Verhältnis von Ober-, Mittel- und Unterlänge nach Belieben an, nimm auf Wunsch Schräglinien dazu — und lade das Blatt als PDF zum Ausdrucken. Auf Wunsch mit einer Vorschrift: dein Text in Sütterlin auf den Zeilen, darunter in Grau zum Nachspuren und Platz zum Nachschreiben.',
  preview: 'Vorschau · DIN A4',
  // The Übungstext (sections/worksheet/useWorksheetText.ts + lib/uebungstext.ts).
  text: {
    heading: 'Übungstext',
    label: 'Vorschrift (optional)',
    placeholder: 'z. B. Guten Morgen',
    help: 'Jede Zeile wird in der nachgeschriebenen Sütterlin-Vorlage auf eine Zeile des Blattes gesetzt — darunter auf Wunsch in Grau zum Nachspuren, dann Leerzeilen zum Nachschreiben.',
    trace: 'Nachspur-Zeile in Grau',
    hint: 'Der Text wird in der Sütterlin-Vorlage gesetzt — der einzigen bislang nachgeschriebenen Schrift; die Lineatur darüber bleibt frei wählbar. Höchstens {{lines}} Zeilen mit je {{chars}} Zeichen; eine Zeile, die bei dieser Mittellänge nicht in die Breite passt, bleibt weg.',
    practiceRows: 'Leerzeilen je Vorschrift',
    loading: 'Der Text wird geschrieben …',
    error: 'Der Text konnte nicht gesetzt werden — der Server ist gerade nicht erreichbar.',
    tooWide: 'Zu breit für diese Mittellänge, bleibt weg: {{lines}}',
    noRow: 'Kein Platz mehr auf dem Blatt: {{lines}}',
    missing: 'Noch nicht nachgeschrieben, bleibt frei: {{letters}}',
  },
  // Footer spec fragments printed on the sheet (fmt templates).
  spec: {
    slant: 'Schräglage {{deg}}°',
    pen: 'Feder {{deg}}°',
  },
  // The three start-script presets (lib/lineatur.ts PRESETS).
  presets: {
    // Angles name their reference (slant to the baseline vs. the pen-edge
    // angle) so the two never get read as one figure.
    kurrent: { label: 'Kurrent', note: '2 : 1 : 2 · Schräglage 60–70° zur Grundlinie (um 1900) · Spitzfeder, Schwellzug im Abstrich' },
    suetterlin: { label: 'Sütterlin', note: '1 : 1 : 1 · senkrecht (90° zur Grundlinie) · Gleichzugfeder (gleichmäßiger Strich)' },
    offenbacher: { label: 'Offenbacher', note: '2 : 3 : 2 · Schräglage 75–80° zur Grundlinie · Breitfeder, Federkante 15–20° zur Schreiblinie' },
  },
  config: {
    presetHeading: 'Ausgangsschrift',
    customSetting: 'Eigene Einstellung',
    ratioHeading: 'Verhältnis · Oberlänge : Mittellänge : Unterlänge',
    ratioAscender: 'Ober',
    ratioXHeight: 'Mittel',
    ratioDescender: 'Unter',
    xHeight: 'Mittellänge (Schreibhöhe)',
    rowGap: 'Zeilenabstand',
    margin: 'Seitenrand',
    lineSystemHeading: 'Liniensystem',
    lineSystemFour: 'Vier Linien',
    lineSystemTwo: 'Doppellinie',
    lineSystemOne: 'Nur Grundlinie',
    lineSystemHint:
      'Die klassische Lern-Progression: vier Linien für den Anfang, die Doppellinie für die Mittellänge, später nur noch die Grundlinie.',
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
