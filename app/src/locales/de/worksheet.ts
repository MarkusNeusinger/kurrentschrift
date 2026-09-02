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
  // The character counts are never written out as a fixed number: what a row
  // holds depends on the Mittellänge, and the sheet says so (audit 2026-09-02).
  text: {
    heading: 'Übungstext',
    label: 'Vorschrift (optional)',
    placeholder: 'z. B. Guten Morgen',
    help: 'Jede Zeile kommt in der Sütterlin-Vorlage auf eine Zeile des Blattes — bei {{xh}} mm Mittellänge sind das etwa {{chars}} Zeichen. Darunter auf Wunsch eine graue Zeile zum Nachspuren, dann Leerzeilen zum Nachschreiben.',
    trace: 'Nachspur-Zeile in Grau',
    hint: 'Der Text wird in der Sütterlin-Vorlage gesetzt — der einzigen bislang nachgeschriebenen Schrift; die Lineatur darüber bleibt frei wählbar. Höchstens {{lines}} Zeilen, bei {{xh}} mm Mittellänge mit je etwa {{chars}} Zeichen. Was breiter gerät, wird weder verkleinert noch umgebrochen — eine Vorschrift soll genau zwischen ihren Linien stehen; die Zeile bleibt stattdessen ungeschrieben, ihr Platz auf dem Blatt bleibt gewahrt, und sie wird unter dem Feld beim Namen genannt.',
    practiceRows: 'Leerzeilen je Vorschrift',
    loading: 'Der Text wird geschrieben …',
    error: 'Der Text konnte nicht gesetzt werden — der Server ist gerade nicht erreichbar.',
    tooWide: 'Zeile {{no}} ist mit {{chars}} Zeichen zu breit für {{xh}} mm Mittellänge — höchstens {{fits}} passen.',
    // Only reachable with an x-height so large that even one letter overruns
    // the row; naming a count of 0 would read like a riddle.
    tooWideNone: 'Zeile {{no}} passt bei {{xh}} mm Mittellänge in keiner Länge in die Breite — eine kleinere Mittellänge schafft Raum.',
    noRow: 'Für {{lines}} ist auf dem Blatt kein Platz mehr — weniger Leerzeilen oder eine kleinere Mittellänge schaffen welchen.',
    lineNo: 'Zeile {{no}}',
    missing: 'Noch nicht nachgeschrieben, bleibt frei: {{letters}}',
    scriptMismatch: 'Die Vorschrift wird in Sütterlin gesetzt — {{script}} ist noch nicht nachgeschrieben. Die Lineatur bleibt {{script}}.',
    // Title of the dashed mark the preview draws over a row held open for a
    // line too wide to be written.
    markTitle: 'Zeile {{no}} — zu breit für diese Mittellänge, bleibt ungeschrieben',
  },
  // What the preview says instead of showing an empty page.
  sheet: {
    empty: 'Bei dieser Einstellung passt keine einzige Zeile auf das Blatt — eine kleinere Mittellänge, ein flacheres Verhältnis oder ein schmalerer Seitenrand bringt die Lineatur zurück.',
    incomplete: 'Ein Feld ist gerade leer — sobald wieder eine Zahl darin steht, kommt die Lineatur zurück.',
  },
  // Footer spec fragments printed on the sheet (fmt templates).
  spec: {
    slant: 'Schräglage {{deg}}°',
    pen: 'Feder {{deg}}°',
    // Printed alongside the ratio when the Vorschrift's script is not the
    // ruling's, so a sheet on the table explains itself.
    vorschrift: 'Vorschrift in Sütterlin',
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
    ratioHeading: 'Verhältnis',
    // Its own caption line under the overline instead of one long heading: as
    // one 13px overline with letter-spacing it broke after the first colon on
    // a 360px screen and left the colon dangling (audit 2026-09-02). The
    // colons are bound with non-breaking spaces (U+00A0, as in the DIN A4
    // above) so the ratio never splits across two lines.
    ratioParts: 'Oberlänge : Mittellänge : Unterlänge',
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
