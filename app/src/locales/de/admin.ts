// German strings for the admin surface (chart editor, sidebar, diagnostics,
// admin layout). Pre-i18n message catalog — key tree mirrors a future i18next
// `admin` namespace. {{…}} placeholders are filled via fmt().

export const admin = {
  layout: {
    openMenu: 'Menü öffnen',
  },
  // The German error layer (sections/admin/shell/apiErrorText.ts, rendered by
  // ErrorText.tsx beside it): one sentence per HTTP status, each naming the
  // next step rather than the failure. The raw English line stays reachable
  // under `detailSummary` — the sentence is the answer, the detail is the
  // evidence.
  errors: {
    offline: 'Keine Verbindung zur API — läuft der Server noch?',
    badRequest: 'Die Anfrage passt nicht zu den Daten — die Angaben stimmen so nicht.',
    noAdmin: 'Kein Admin-Zugang — Anmeldung bzw. Token prüfen.',
    notFound: 'Dazu liegt nichts vor — es ist noch nicht angelegt oder gerade gelöscht worden.',
    conflict: 'Der Stand hat sich inzwischen geändert — erst neu laden, dann noch einmal.',
    tooLarge: 'Die Datei ist zu groß für diesen Weg.',
    invalid: 'Die Angaben sind unvollständig oder unzulässig.',
    locked: 'Diese Glyphe ist gesperrt — erst in der Tafel entsperren, dann speichern.',
    tooMany: 'Zu viele Anfragen kurz hintereinander — einen Moment warten.',
    server: 'Der Server konnte das nicht verarbeiten — der Fehler liegt nicht bei dir.',
    // Label of the collapsed <details> that carries the raw server line.
    detailSummary: 'Technische Meldung',
  },
  // The shell: the header over all three views, the Vorlage picker the admin is
  // entered through, and the Auftragskorb drawer.
  shell: {
    areaLetters: 'Buchstaben',
    areaJoins: 'Übergänge',
    areaWords: 'Wörter',
    areaEigenhand: 'Eigenhand',
    areaNavAria: 'Bereiche der Werkbank',
    noSource: 'keine Vorlage',
    // `switchSource` („Vorlage wechseln") is gone: its only reader was the
    // Vorlagen-Chip's tooltip, and the chip moved into the Scope-Leiste, whose
    // Vorlage field is the same link.
    //
    // The Scope-Leiste under the header: two fields that say what the open page
    // is about, and never switch it (admin-redesign.md §7.2). The colons are
    // part of the visible label, which is why they live here.
    scopeAria: 'Arbeitsbereich',
    scopeSource: 'Vorlage:',
    scopeHand: 'Hand:',
    // Not every script has an own hand — an em-dash is the honest answer, an
    // invented id would not be (V19).
    scopeHandNone: '—',
    openKorb: 'Auftragskorb öffnen',
    // The badge names its scope, visibly in the Vorlage field and in the
    // button's name — before, it stood nowhere, not even in the hover. The id
    // rides along because one script can be taught by several charts, so the
    // style alone does not say WHICH basket this is.
    korbOpen: '{{n}} offen',
    korbScoped: 'Auftragskorb der Vorlage {{style}} · {{id}} öffnen',
    // With the badge gone, the flag itself is the only carrier of the count on
    // a phone: the Scope-Leiste scrolls its ACTIVE field into view, which on
    // /admin/eigenhand is the Hand field, so the Vorlage field with its „⚑ 3
    // offen" can sit off screen. The number rides in the button's name too.
    korbScopedOpen: 'Auftragskorb der Vorlage {{style}} · {{id}} öffnen — {{n}} offen',
    closeKorb: 'Auftragskorb schließen',
    startEyebrow: 'Werkbank',
    startTitle: 'Welche Vorlage?',
    startIntro:
      'Alles in der Werkbank gehört zu genau einer Vorlage und ihrer Hand — Buchstaben, Übergänge und Wörter werden immer an einer Schrift gearbeitet. Darum steht die Wahl am Anfang und nicht in einem Menü.',
    startRatio: 'Verhältnis {{ratio}}',
    startSlant: 'Schräglage {{deg}}°',
    startNoSources: 'Keine Tafel-Vorlagen gefunden — läuft die API und ist die Datenbank eingerichtet?',
    startHint: 'Die gewählte Vorlage bleibt in diesem Browser gespeichert; die öffentlichen Seiten bleiben unberührt.',
    // The three roles of vision.md as ONE set of labels (author decision
    // 2026-09-18, Q8 a): Tafel is the teaching chart, Platte the historical
    // hand's plate, Eigenhand the author's own. They live in the shell rather
    // than in a view because a role is never a property of one surface — the
    // Scope-Leiste, the Rollen-Spalten (Phase 3) and every future panel head
    // name the same three. The Gloss variants are for the FIRST appearance on
    // a surface; afterwards the bare label carries it.
    roleTafel: 'Tafel',
    rolePlatte: 'Platte',
    roleEigenhand: 'Eigenhand',
    rolePlatteGloss: 'Platte (historische Hand)',
    roleEigenhandGloss: 'Eigenhand (meine Hand)',
    // The Kurztasten switch at the end of the Scope-Leiste (author decision
    // P1-Q11 b). The state is VISIBLE TEXT beside the switch, not the knob's
    // position alone — a switch read by its position is a colour-only state in
    // another shape (§9.5). The hint names the binding, because a key nobody is
    // told about is a key nobody presses.
    shortcutsLabel: 'Kurztasten',
    shortcutsOn: 'an',
    shortcutsOff: 'aus',
    shortcutsHint: 'Alt + Umschalt + ← / → blättert zum vorigen oder nächsten Gegenstand.',
    // The shared states of every occurrence-backed block.
    evidenceLoading: 'wird geladen …',
    evidenceError: 'Die gespeicherten Vorkommen konnten nicht geladen werden — neu laden oder die API prüfen.',
  },
  // The Arbeitslisten: the toolbar vocabulary every overview shares (view,
  // filter, sort, page), so the same control carries the same word everywhere.
  liste: {
    viewLabel: 'Ansicht',
    viewList: 'Liste',
    viewGallery: 'Galerie',
    filterLabel: 'Filter',
    // How much of how much is on screen.
    counter: '{{shown}} von {{total}}',
    // Once a filter is on, „how many match this selection?" is the question,
    // and the page size does not answer it: 30 selected rows would otherwise
    // read as „24 von 63". The chip counts cannot answer it either — each one
    // deliberately counts on its own.
    counterFiltered: '{{shown}} von {{selected}} gewählten · {{total}} insgesamt',
    // The same question on a surface without a pager, where „wieviel davon ist
    // auf dem Schirm?" has only one possible answer: all of it. Two numbers
    // rather than the three above, so the line stops repeating one of them.
    counterSelected: '{{selected}} von {{total}} gewählt',
    pagerLabel: 'Seiten',
    pageAria: 'Seite {{n}}',
    pageAll: 'alle zeigen',
    // The second silence: not „there is nothing here" but „there is nothing
    // matching this selection" — with the way back.
    emptyFiltered: 'Kein Eintrag passt zu dieser Auswahl.',
    // The THIRD silence, and the one that is not an answer at all: a ticked
    // chip whose evidence has not arrived selects no row, and reporting that
    // as „nothing matches" would be a claim about the data made on a read that
    // never landed.
    emptyPending: 'Diese Auswahl braucht eine Angabe, die noch geladen wird.',
    resetFilters: 'Filter zurücksetzen',
    chipKorb: '{{count}} im Korb',
    // What ‹ › walks, said in the detail head. The stepper follows the order of
    // the overview the reader came from — filter and Sortierung included —, so
    // the same two buttons mean something different after a filter click and
    // have to say which (P1-Q12 a; design-system.md §9.5).
    orderPrefix: 'Reihenfolge: ',
    orderFiltered: 'gefiltert',
    // The fallback: nobody published an order, so the stepper walks the
    // register — a deep link straight into a detail, or a subject the filtered
    // overview does not list.
    orderRegistry: 'Registerfolge',
  },
  // The Buchstaben view: one letter's whole life, from the chart cell to how it
  // is finally written, plus the ways over to its joins and its words.
  letters: {
    overviewTitle: 'Buchstaben',
    overviewIntro:
      'Jeder erstellte Buchstabe als Zeile: Bewertung, Abzüge und die Merkmale, an denen Arbeit hängt — gesperrt, ohne Laufform, ohne Vorkommen, offene Aufträge. Eine Zeile klappt an Ort und Stelle die vier Flächen auf (Tafel-Ausschnitt, Tafel-Form, Laufform, Median & Vorkommen); „Galerie“ zeigt sie für alle Buchstaben untereinander. „Öffnen“ führt in den einzelnen Buchstaben mit allen Werkzeugen.',
    // The work list's filter chips, in the order they stand in (letterRows.ts
    // carries the same order as data).
    filters: {
      gesperrt: 'gesperrt',
      'ohne-laufform': 'ohne Laufform',
      'ohne-vorkommen': 'ohne Vorkommen',
      'mit-korb': 'mit Korb-Auftrag',
    },
    // The expander names its letter: 63 buttons all called „Aufklappen" are a
    // list without content to a screen reader.
    rowExpand: 'Buchstabe {{key}} aufklappen',
    rowCollapse: 'Buchstabe {{key}} zuklappen',
    // Both directions get a chip — a missing one would be indistinguishable
    // from „not loaded yet".
    chipLaufform: 'Laufform',
    chipNoLaufform: 'ohne Laufform',
    // The detail view's heading as plain text. Its visible head is the paging
    // arrows around a glyph chip, which cannot BE an h1 — this is the h1 behind
    // it, so the page keeps a document outline (see ViewHeader `titleText`).
    letterHeading: 'Buchstabe {{key}}',
    pickLetter: 'Buchstabe wählen',
    // The chip SHOWS the open letter, and an `aria-label` replaces what it
    // shows — so the name says which letter is open, not only what the control
    // is for.
    pickLetterChosen: 'Buchstabe {{glyph}} — anderen wählen',
    prevLetter: 'Vorheriger Buchstabe',
    nextLetter: 'Nächster Buchstabe',
    toOverview: 'Alle Buchstaben',
    stateCanonical: 'erstellt',
    stateBbox: 'nur Ausschnitt',
    stateEmpty: 'leer',
    stateLocked: 'gesperrt',
    occurrenceCount: '{{count}} Vorkommen',
    tafelTitle: 'Tafel-Ausschnitt',
    tafelCaption:
      'Der Ausschnitt aus der Lehrtafel, so wie er nach Radierer, Tinte und Maske in die Verarbeitung geht. „Einrichten“ öffnet den Wizard (Ausschluss · Lineatur · Weg), „Diagnose“ zeigt Skelett, kanonische Form und Einpassung.',
    noBbox: 'Für diesen Buchstaben gibt es noch keinen Ausschnitt — unten die Tafel öffnen und ein Rechteck ziehen.',
    showChart: 'Tafel öffnen (Ausschnitt anlegen)',
    hideChart: 'Tafel schließen',
    writtenTitle: 'Wie es geschrieben wird',
    writtenCaption:
      'Links die Tafel-Form aus dem nachgefahrenen Duktus, rechts die Laufform — der Median aus den Vorkommen in Wörtern, den der Composer in fließenden Läufen einsetzt.',
    faceChart: 'Tafel-Form (Variante 0)',
    faceLaufform: 'Laufform (Variante 100)',
    noLaufform: 'Noch keine Laufform gespeichert — sie entsteht erst aus den Aggregaten (apply-laufform).',
    noCanonical: 'Noch kein Weg nachgefahren — erst im Wizard zeichnen, dann schreibt die Engine den Buchstaben.',
    occurrencesTitle: 'Vorkommen in Wörtern ({{count}})',
    occurrencesCaption:
      'Jedes vermessene Vorkommen auf den Platten, schlechteste Einpassung zuerst. Ein Klick springt in das Wort, in dem es steht.',
    loadingOccurrences: 'Vorkommen werden geladen …',
    statsTitle: 'Statistik der Hand',
    statsCaption:
      'Wozu sich die Vorkommen verdichten: der Median je Anker mit seiner Streuung — die Quelle der Laufform. Nur Anschauung; übernommen wird sie ausdrücklich getrennt.',
    joinsTitle: 'Übergänge dieses Buchstabens',
    joinsCaption: 'Die Verbindungen, die auf den Platten wirklich gemessen wurden — mit Anzahl der Vorkommen.',
    noJoins: 'Keine gemessenen Übergänge mit diesem Buchstaben.',
    allJoins: 'Alle Kombinationen ansehen',
    wordsTitle: 'Wörter mit diesem Buchstaben',
    wordsCaption: 'Die Wortproben, in denen der Buchstabe vermessen wurde.',
    noWords: 'Keine Wortprobe enthält ein vermessenes Vorkommen dieses Buchstabens.',
    // The one rendering-changing step, kept visually apart from the panels
    // above it (they inspect; this one writes).
    applyBlockTitle: 'Laufform übernehmen',
    applyBlockBody:
      'Schreibt die gespeicherten Aggregate dieser Hand als Laufform (Variante 100) — ab dann schreibt die Engine in fließenden Läufen den gemessenen Median statt der bisherigen Form. Der einzige Schritt im Handmodell, der das Schreiben verändert.',
    applyBlockButton: 'Laufform überschreiben …',
    applyBlockNoHand: 'Ohne Hand an den Vorkommen gibt es keine Aggregate, die übernommen werden könnten.',
    // The Landmarken-Linse (optimierungs-werkbank.md §8): what the structure
    // detectors see in this letter, drawn ON the written form so „hier fehlt
    // eine Kreuzung“ can be pointed at instead of described.
    landmarksTitle: 'Landmarken',
    landmarksCaption:
      'Was die Erkennung in diesem Buchstaben findet: Kreuzungen, Retrace-Zonen, Absetzer, Umkehrecken und Kringel — dieselben Erkenner, mit denen der Tintenfolger misst. Eine Marke anklicken zeigt ihre Zahlen und legt sie bei Bedarf als Auftrag in den Korb; ein Klick ins Leere meldet eine Stelle, an der eine Marke FEHLT.',
    landmarksToggle: 'Landmarken zeigen',
    landmarksLoading: 'Landmarken werden berechnet …',
    landmarksError: 'Landmarken konnten nicht geladen werden.',
    landmarksNone: 'Die Erkennung findet in diesem Buchstaben keine Struktur — weder Kreuzung noch Schleife noch Retrace-Zone.',
    landmarksRowChart: 'Tafel-Duktus (Variante 0)',
    landmarksRowLaufform: 'Laufform (Variante 100)',
    landmarksCount: '{{count}} Marken',
    landmarksLegend: 'Legende',
    // The legend's ONE explanation. The seven definitions below used to hang as
    // a native `title=` on the seven filter chips — hover only, so a reader on
    // the tablet or at the keyboard never met a single one (V25, §9.4).
    landmarkKindsTitle: 'Was die Marken bedeuten',
    landmarkKindsAria: 'Die Landmarken-Arten erklären',
    // The vocabulary the overlay draws and the Korb files against.
    landmarkKind: {
      crossing: 'Kreuzung',
      retrace: 'Retrace-Zone',
      touch: 'Berührung',
      overlap: 'Verschmelzung',
      lift: 'Absetzen',
      corner: 'Umkehrecke',
      loop: 'Kringel',
      spot: 'Stelle ohne Marke',
    },
    landmarkKindHint: {
      crossing: 'Eine Stelle, an der die Bahn eine andere wirklich DURCHSTÖSST — rein auf der einen, raus auf der anderen Seite.',
      retrace: 'Ein Stück, das derselbe Zug zweimal schreibt (hin und zurück über dieselbe Tinte).',
      touch: 'Zwei Durchgänge laufen nah aneinander vorbei, aber mit einem weiten Weg dazwischen — aneinander vorbei, nicht übereinander.',
      overlap: 'Zwei VERSCHIEDENE Federzüge liegen an derselben Stelle — ein Zeichen reitet auf dem Körper.',
      lift: 'Hier wurde die Feder abgesetzt und neu aufgesetzt.',
      corner: 'Ein im Duktus festgehaltener Umkehrpunkt — dort bleibt der Knick beim Zeichnen erhalten.',
      loop: 'Eine geschlossene Schleife. Der Kreis zeigt ihre gemessene Öffnungsweite D0; Klasse und Zustand kommen aus dem eingefrorenen Kringel-Katalog.',
      spot: 'Eine Stelle, an der du eine Marke erwartest, aber keine steht.',
    },
    // Field labels for the numbers a marker carries.
    landmarkNumber: {
      angle_deg: 'Winkel',
      arc_separation: 'Bogenabstand',
      stroke_i: 'Zug A',
      stroke_j: 'Zug B',
      self_crossing: 'kreuzt sich selbst',
      arc: 'Bogenlänge',
      samples: 'Abtastpunkte',
      anchor: 'Anker',
      stroke: 'Zug',
      d0: 'Öffnungsweite D0',
      area: 'Fläche',
      size_class: 'Größenklasse',
      state: 'Zustand',
      d0_plate: 'D0 auf der Platte',
      occurrences: 'Vorkommen',
      with_counter: 'davon mit Binnenfläche',
      anchor_range: 'Schleifenbereich',
    },
    landmarkNoRange: 'kein Schleifenbereich erkannt',
    // The honest half: catalogue rows no detected loop could be paired with.
    landmarksUnmatchedTitle: 'Im Katalog, hier nicht gefunden',
    landmarksUnmatchedBody:
      'Die Platte hält an diesen Schleifen eine Binnenfläche, die Erkennung findet in dieser Zeile keine dazu. Das ist ein Befund, keine Lücke — beim t ist es der bekannte Fall.',
    landmarksUnmatchedRow: 'Kringel #{{loop}} · {{size}} · {{state}}',
    landmarksCatalogueOff:
      'Kein Kringel-Katalog für diese Vorlage — die Schleifen kommen ohne Urteil (Klasse und Zustand bleiben „unbekannt“). Ein Katalog gilt für genau eine Hand mit einer Feder.',
    landmarksCatalogueOn: 'Kringel-Katalog: {{style}} · {{root}}',
    landmarkMark: 'Bemängeln',
    landmarkSelectHint: 'Eine Marke anklicken, um ihre Zahlen zu sehen.',
    landmarkAria: '{{kind}} Nummer {{index}} bei x {{x}}, y {{y}} — anklicken für die Zahlen',
    // Reporting a marker that ISN'T there. Two ways in, and the button is the
    // one that also works from the keyboard: es meldet dieselbe Sache ohne
    // Ortsangabe, statt eine zu erfinden.
    landmarkSpotButton: 'Fehlende Marke melden',
    landmarkSpotHint:
      'Ins Leere klicken meldet die Stelle mit ihrer Position; der Knopf meldet dasselbe ohne Ortsangabe — dann steht im Auftrag, was du beschreibst, keine erfundene Koordinate.',
    // The Abzugs-Linse (optimierungs-werkbank.md §9): WHERE the Gleichzug
    // score takes its points off, drawn over the Tafel-Ausschnitt the ruler
    // measured in. The caption is the author's own framing — a deduction is
    // where the ruler subtracts, not a defect list to be hand-fixed.
    penalties: {
      title: 'Abzüge',
      caption: 'Wo das Lineal abzieht — kein Fehlerbefund.',
      toggle: 'Abzüge zeigen',
      loading: 'Abzüge werden neu gemessen …',
      errorPrefix: 'Abzüge konnten nicht gemessen werden:',
      // The route's 409: a row without pixel anchors, or one whose geometry the
      // metric cannot score. Reloading cannot help — the generic conflict
      // sentence would send the author the wrong way.
      unscorable:
        'Diese Zeile lässt sich nicht auswerten — ihr fehlen die Pixel-Anker, oder ihre Geometrie ist ungültig. Erst im Wizard neu abtasten oder nachzeichnen.',
      // Which row is under the lens, and why only that one.
      rowNote:
        'Tafel-Duktus (Variante 0), neu gemessen gegen den Ausschnitt. Die Laufform ist nicht gegen die Tafel gemessen — ihr gespeicherter Score ist eine Kopie dieser Zeile.',
      measuredLead: 'Abzüge (neu gemessen):',
      storedLead: 'gespeichert:',
      storedNote: 'Stand der letzten Ableitung — weicht um mehr als 0.005 ab.',
      notApplicable: 'nicht anwendbar',
      noPlace: 'ohne Ort',
      // A category whose map the core dropped (`in_sync` false): the number
      // stands, its places do not — not the same thing as a part without a place.
      mapDropped: 'Karte verworfen (Nachrechnung weicht ab)',
      // „4 Stellen", „1 Stelle", „keine Stelle" — the count a chip carries.
      sitesOne: '1 Stelle',
      sitesMany: '{{count}} Stellen',
      sitesNone: 'keine Stelle',
      legendTitle: 'Was die Marken zeigen',
      legendAria: 'Die Abzugs-Marken erklären',
      legendIntro:
        'Die Form sagt die Kategorie, die Breite oder Größe den Anteil am Abzug; die dünne durchgezogene Linie ist die gemessene Mittellinie, die Scheiben ①–⑤ die fünf teuersten Stellen. Die Stellen einer Kategorie summieren sich auf die gezeigte Zahl bis zur vierten Stelle.',
      // The context marks: they frame a deduction and are none — own form, own
      // hue (styles/paper.ts `penalty.context`); the text names forms only.
      legendContextLabel: 'Kontext',
      legendContext:
        'kein Abzug. Dünn gestrichelt umrissen: die Doppelzug-Zone. Gestrichelt unterlegt, mit Querbalken an den Enden: die Eckfenster der Glätte.',
      legendExact:
        'Term: die Stelle IST ein Summand der Zahl (Ecken, Kreuzungsflucht, Doppelzug). Anteil: der Abzug läuft durch eine Exponentialfunktion, ein Produkt oder eine Wurzel und ist proportional verteilt (Glätte, Senkrechte, Deckungslücke).',
      legendPoints:
        'Punkte sind linearisiert — die Näherung, um wie viel der Score stiege, fiele diese eine Stelle weg. Sie reihen die Stellen, sie sind nie die Hauptzahl.',
      legendNoPlace:
        'Ohne Ort: was zählt, aber keine Stelle hat — vor allem der 1,5-px-Saum der Deckungslücke (Kantenquantisierung der Binarisierung).',
      // One line per category: what its mark is. Shapes and strokes only —
      // no colour words (design-system.md §2, Strichart-Regel).
      markerHint: {
        smoothness:
          'Band entlang der Mittellinie, je Punkt so breit wie sein Anteil am Ruck. Wo es aussetzt, liegt ein Eckfenster (Kontext) — das zählt unter Ecken.',
        verticality:
          'Klammer neben dem Lauf, gestrichelt die ideale Senkrechte, die gemessene Abweichung überhöht gezeichnet — ×20, weniger, wo sie sonst weiter als 0.15 x-Höhen ausschlüge.',
        corner:
          'Quadrat am Scheitel, die beiden Anlaufstücke, gestrichelt ihre Sehnen, ein Punkt an der größten Abweichung.',
        collinearity: 'Ring an der Kreuzung und die beiden gefitteten Geraden davor und dahinter.',
        retrace: 'Kreuzschraffiert: fehlende Tinte in der Doppelzug-Zone; die Zone selbst ist Kontext.',
        coverage:
          'Schraffiert: tiefe Tintenlücken. Gerastert: Render über Papier. Kurze Querstriche über den Rand: Chamfer. Fühler vom Mittellinienpunkt zum Skelett: Geo.',
      },
      pinsTitle: 'Die fünf teuersten Stellen',
      pinsNone: 'Keine Stelle mit Ort trägt einen Abzug.',
      // „0.0954 von 0.1711" — the site's part of its category's number.
      ofCategory: '{{value}} von {{total}}',
      pointsShort: '≈ {{points}} Punkte',
      pointsLong: '≈ {{points}} Punkte (linearisiert — nur zum Reihen)',
      exactTerm: 'Term',
      exactShare: 'Anteil',
      selectHint: 'Eine Stelle in der Liste oder im Bild antippen, um ihre Zahlen zu sehen.',
      position: 'x {{x}} · y {{y}} Pixel im Ausschnitt',
      positionNone: 'ohne Ort — zählt in der Zahl, hat aber keine Stelle im Ausschnitt',
      exaggerated: 'Abweichung ×{{factor}} überhöht gezeichnet — echt ist sie meist unter einem Pixel.',
      windowsNote:
        'Gestrichelt unterlegt, mit Querbalken an den Enden: die Eckfenster — was dort liegt, zählt unter Ecken.',
      partOf: 'Teil {{part}}',
      allToggle: 'Alle Stellen ({{count}})',
      allHide: 'Stellenliste schließen',
      // Beside a category group in „Alle Stellen" when its legend chip is off:
      // the switch acts on the image only, and choosing a row shows it again.
      hiddenNote: 'im Bild ausgeblendet',
      // The pin's rank, spoken: the ①–⑤ disc beside a row is aria-hidden.
      rankPrefix: 'Rang {{rank}} · ',
      belowOne: '+ 1 Stelle unter 0.0001 — ohne Anteil an der gezeigten Zahl, nicht gezeichnet',
      belowCount: '+ {{count}} Stellen unter 0.0001 — ohne Anteil an der gezeigten Zahl, nicht gezeichnet',
      mark: 'Bemängeln',
      markHint:
        'Legt einen Buchstaben-Auftrag an; die erste Zeile nennt die Stelle und ihre Zahl. Ein Streit mit dem Lineal selbst ist kein Korb-Fix, sondern ein Vorschlag samt Re-Baseline.',
      // What a site IS, per payload `kind`.
      kind: {
        segment: 'Abschnitt',
        run: 'Senkrechtlauf',
        corner: 'Ecke',
        passage: 'Durchgang',
        missed_ink: 'fehlende Tinte',
        excess_render: 'Render über Papier',
        edge: 'Randstück',
        off_skeleton: 'neben dem Skelett',
        rim: 'Saum (Kantenquantisierung)',
        unlocated: 'Nachrechnung weicht ab',
      },
      // The three factors of the coverage gate.
      part: {
        dice: 'Dice',
        chamfer: 'Chamfer',
        geo: 'Geo',
      },
      // Field labels for the numbers a site carries; an unknown key shows raw.
      number: {
        anchor: 'Anker',
        sample: 'Abtastpunkt',
        s_in: 'Anlauf ein',
        s_out: 'Anlauf aus',
        q: 'q',
        stroke: 'Zug',
        from: 'von Punkt',
        to: 'bis Punkt',
        samples: 'Abtastpunkte',
        peak_sample: 'Spitze bei',
        stroke_end_share: 'Anteil am Strichende',
        rms_px: 'rms (px)',
        rms_units: 'rms (x-Höhen)',
        length_units: 'Länge (x-Höhen)',
        max_dev_px: 'größte Abweichung (px)',
        lean_deg: 'Neigung (°)',
        x_ideal: 'Ideal-x (px)',
        partner: 'Partnerpunkt',
        dtheta_deg: 'Knick δθ (°)',
        ddist_units: 'Versatz δd (x-Höhen)',
        ddist_px: 'Versatz δd (px)',
        pixels: 'Pixel',
        render_px: 'Randpixel Render',
        ink_px: 'Randpixel Tinte',
        max_offset_px: 'größter Abstand (px)',
        missed_px: 'fehlende Pixel',
        excess_px: 'überschüssige Pixel',
        rim_px: 'Saumbreite (px)',
        reason: 'Grund',
      },
    },
  },
  // The deliberate promotion of learned statistics into rendering (issue #270).
  laufform: {
    title: 'Laufform überschreiben?',
    warning:
      'Dieser Schritt verändert, wie die Engine schreibt — auch auf den öffentlichen Seiten. Alles andere im Handmodell misst nur; dies hier wird gerendert.',
    intro:
      'Übernommen werden die GESPEICHERTEN Aggregate der Hand „{{hand}}" (nicht neu gerechnet — dafür ist der Neuaufbau da). Anker kommen aus dem Median, Breiten, Strich-Topologie und An-/Abstrich weiterhin aus der Tafelzeile.',
    previewSummary: '{{total}} Buchstaben mit Aggregat, davon {{changing}} mit Änderung.',
    previewSelected: '{{selected}} ausgewählt.',
    // Says both halves of the doctrine: thin medians are proposed unchecked,
    // and a deliberate tick still carries — only now the request says so, and
    // an unticked thin row is refused by the endpoint rather than by this list.
    previewSelectionHint:
      'Vorgeschlagen sind die Buchstaben mit mindestens {{count}} Vorkommen — darunter kann der Median einen einzelnen Ausreißer nicht mehr überstimmen. Dünner belegte lassen sich weiterhin übernehmen, aber nur ausdrücklich angehakt.',
    nothingToApply: 'Keine übernehmbaren Aggregate — erst die Statistik neu aufbauen.',
    selectAll: 'Alle auswählen',
    selectRow: '{{key}} auswählen',
    colGlyph: 'Buchstabe',
    colOccurrences: 'Vorkommen',
    // Short on purpose: the column has to survive a 390px dialog, and the
    // paragraph above already says what the distance is measured against.
    colDeviation: 'Abstand',
    cellNew: 'neu',
    cellUnchanged: 'unverändert',
    cellIncomparable: 'nicht vergleichbar',
    // A median over one or two Vorkommen: stated at the moment of the decision.
    cellLowN: 'nur {{count}} Vorkommen',
    // „1 Laufform" vs. „5 Laufformen" — the button says how many rows the tick
    // marks will actually write.
    confirm: 'Ja, {{count}} Laufformen überschreiben',
    confirmOne: 'Ja, 1 Laufform überschreiben',
    failed: 'Übernahme fehlgeschlagen — es wurde nichts geschrieben.',
    doneSummary: '{{applied}} Laufformen geschrieben, {{skipped}} übersprungen.',
    doneCreated: '{{key}} · neu',
    doneUpdated: '{{key}} · Abstand {{value}} geschlossen',
    doneSkippedLabel: 'Übersprungen:',
    doneExcluded: '{{count}} nicht ausgewählt und daher unverändert: {{keys}}',
    doneHint:
      'Die Laufform ist jetzt ein Abbild der gespeicherten Statistik. Ändern sich Tafel-Duktus oder Vorkommen, veraltet sie wieder — sichtbar am Abstand hier.',
    // The endpoint's fixed skip vocabulary.
    skipReason: {
      laufform_variant: 'ist selbst schon Laufform',
      non_base_variant: 'keine Basis-Variante',
      no_base_template: 'keine Tafelzeile',
      anchor_count: 'Ankerzahl weicht ab',
      below_min_occurrences: 'zu wenige Vorkommen',
      anchor_spike: 'Ankersprung (Anker im leeren Papier)',
      head_deviation: 'Kopf dreht ab (Landerichtung gegen die Tafel)',
      foreign_hand: 'gehört einer anderen Hand',
    },
  },
  // The Übergänge view: the generated join first, the measurement beside it,
  // the override last — the order the stage doctrine prescribes.
  joins: {
    overviewTitle: 'Übergänge',
    overviewIntro:
      'Der Übergang ist das, was die Engine zwischen zwei Buchstaben erzeugt. Hier steht jede Zweierkombination eines Buchstabens — auch solche, die keine Platte je geschrieben hat: tippe sie einfach ein. Jede Zelle sagt in Worten, was zu ihr vorliegt: wie oft die Platten sie schreiben, ob eine Übersteuerung gespeichert ist und was im Korb liegt; „Galerie“ komponiert dieselben Zellen zusätzlich. Ein Klick öffnet die Verbindung mit Messung, Statistik und (als letztes Mittel) dem Paar-Editor.',
    // Plain-text h1 behind the two-picker head (see letters.letterHeading).
    joinHeading: 'Übergang {{left}} → {{right}}',
    pickLeft: 'links',
    pickRight: 'rechts',
    // The chip SHOWS the chosen letter; an `aria-label` replaces what it shows,
    // so „links" alone would leave a screen reader without the one thing the
    // control states. Name the side AND the current value.
    pickLeftEmpty: 'Linken Buchstaben wählen',
    pickRightEmpty: 'Rechten Buchstaben wählen',
    pickLeftChosen: 'Links: {{glyph}} — anderen Buchstaben wählen',
    pickRightChosen: 'Rechts: {{glyph}} — anderen Buchstaben wählen',
    freeTextLabel: 'Kombination eintippen',
    freeTextHint: 'Zwei Zeichen, z. B. „ab“ — auch ohne Vorkommen.',
    freeTextSubmit: 'Ansehen',
    freeTextInvalid: 'Das ergibt keine Verbindung — zwei Buchstaben eingeben (ch, ck, tz, ſt, qu, ß sind je EINE Glyphe).',
    toOverview: 'Alle Kombinationen',
    // The Subjekt-Stepper of this view. It names the SUBJECT, not the
    // direction: three details step, and „Vorheriger" alone would leave a
    // screen reader to guess through what.
    prevJoin: 'Vorheriger Übergang',
    nextJoin: 'Nächster Übergang',
    generated: 'generiert',
    occurrenceCount: '{{count}} Vorkommen',
    writtenTitle: 'Wie es geschrieben wird',
    writtenCaption:
      'Beide Buchstaben mit dem generierten Übergang, serverseitig komponiert — genau so, wie die Engine sie in einem Wort schreibt.',
    writtenCaptionOverride:
      'Für dieses Paar ist ein freigegebener Override gespeichert: gezeichnet statt generiert, verbatim gerendert.',
    // Shown instead of the mute white box when NEITHER letter is authored yet.
    // The view invites typing any pair, so this is a normal answer, not a fault
    // — and the „Buchstabe x/y" buttons right below it are the next step.
    writtenNoneCreated:
      'Für diesen Übergang ist noch keiner der beiden Buchstaben erstellt — erst im Wizard zeichnen, dann schreibt die Engine das Paar.',
    overrideLastResort:
      'Erst die Klassenregel schärfen (hebt alle Paare derselben Art), zeichnen nur als letztes Mittel — jeder Override friert eine Stelle ein.',
    toLetter: 'Buchstabe {{key}}',
    statsTitle: 'Gemessen vs. komponiert',
    statsCaption:
      'Die gemessene Median-Verbindung über den Vorkommen, aus denen sie verdichtet wurde — die Prüfzahl dafür, wie weit der Generator von dieser Hand entfernt liegt.',
    // The traced drill plate of exactly this pair (the Verbindungs-Platten
    // cell), shown as the same evidence card the Wörter view uses.
    drillTitle: 'Bahn der Platte (nachgefahren)',
    drillCaption:
      'Die Verbindungs-Platte genau dieser Kombination — die Bahn, darüber die Engine-Tinte, beide in derselben vermessenen Registrierung; rechts schreibt das System dieselbe Verbindung im gleichen Maßstab. Welche Linie welche ist, sagen die Schalter darüber.',
    occurrencesTitle: 'Vorkommen ({{count}})',
    occurrencesCaption:
      'Jede herausgezogene Verbindung als Ausschnitt der Platte — die Tinte selbst, mit dem Abstand Δ zum generierten Zug. Ein Klick springt in das Wort, in dem sie steht.',
    noOccurrences: 'Diese Verbindung kommt auf den Platten nicht vor — beurteilt wird dann allein das Schriftbild oben.',
    // Occurrences without a showable crop. Two causes, and the label names
    // neither: either the plate has no fitted letters at that slot, or the two
    // harvests disagree about the word's slotting — in both cases the honest
    // statement is that the spot cannot be located on the plate.
    occurrencesNoCrop: '{{count}} ohne Ausschnitt (Stelle auf der Platte nicht eindeutig auffindbar):',
    loadingOccurrences: 'Vorkommen werden geladen …',
    wordsTitle: 'Wörter mit diesem Übergang',
    wordsCaption: 'Die Wortproben, in denen die Verbindung vermessen wurde.',
    noWords: 'Keine Wortprobe enthält ein vermessenes Vorkommen dieser Verbindung.',
    showMatrix: 'Alle Kombinationen einblenden',
    hideMatrix: 'Alle Kombinationen ausblenden',
    // The Abb.-20 plates: the only specimens that are pure joins.
    showSpecimens: 'Verbindungs-Platten der Vorlage einblenden',
    hideSpecimens: 'Verbindungs-Platten ausblenden',
  },
  // The Wörter view: any text, written by the engine — with the traced specimen
  // underneath wherever this hand happened to write the same word.
  words: {
    overviewTitle: 'Wörter',
    overviewIntro:
      'Im Wort wird sichtbar, was einzeln noch stimmte. Jede Wortprobe der Vorlage als Zeile: das Wort, gespeicherte Bahnen, Stand im Nachfahren, offene Aufträge und — sobald berechnet — der Loss. Eine Zeile klappt an Ort und Stelle Original und „wie geschrieben“ auf; „Galerie“ zeigt beide Flächen für alle Proben untereinander, „Öffnen“ führt in das einzelne Wort mit Bahn, Vorkommen und Bewertung. Oben lässt sich jeder beliebige Text eintippen — auch einer, den keine Platte enthält.',
    // Plain-text h1 behind the Garamond-set word (see letters.letterHeading).
    wordHeading: 'Wort {{text}}',
    freeTextLabel: 'Wort oder Satz',
    freeTextHint: 'Beliebiger Text — er muss in keiner Wortprobe vorkommen.',
    freeTextSubmit: 'Schreiben',
    filterLabel: 'Proben filtern',
    toOverview: 'Alle Wortproben',
    // The Subjekt-Stepper of this view; it walks WORTPROBEN, not words — two
    // plates can carry the same text, and each is its own piece of evidence.
    prevWord: 'Vorherige Wortprobe',
    nextWord: 'Nächste Wortprobe',
    // The work list (V14). The expander names its Wortprobe: a list of rows
    // all called „Aufklappen" is a list without content to a screen reader.
    rowExpand: 'Wortprobe {{word}} aufklappen',
    rowCollapse: 'Wortprobe {{word}} zuklappen',
    tabsLabel: 'Reiter',
    sortOrder: 'Reihenfolge der Vorlage',
    sortWorstUnavailable:
      'Noch kein Score berechnet — „Scores berechnen & sortieren“ oben holt sie und ordnet danach.',
    // „Bahn" rather than „Beleg" for a stored line (author decision
    // 2026-09-18, Q8 a): in the own-hand Bestandsbericht „Beleg" counts the
    // accepted Fassungen of an item, so the same word for the line over a plate
    // Wortprobe was two counting units under one name. This chip led; Q8 (b)
    // then made „Bahn" the ONE noun across plate and strip, which is what
    // `admin.vocabulary.test.ts` beside this file now keeps from rotting back.
    traceCount: '{{count}} Bahnen',
    traceCountOne: '{{count}} Bahn',
    // Beside it, since the detail builds its list from the WORTPROBEN: how many
    // samples the plate has of this text — the Bahnen are the subset of them
    // that already carry a line. Both counts are this hand's own; a foreign
    // writer's samples get `werkbank.foreignCount`.
    sampleCount: '{{count}} Wortproben',
    sampleCountOne: '{{count}} Wortprobe',
    writtenTitle: 'Wie es geschrieben wird',
    writtenCaption:
      'Serverseitig komponiert: Buchstaben der Bibliothek, dazwischen die erzeugten Übergänge — dieselbe Ausgabe, die die öffentlichen Seiten schreiben.',
    partsTitle: 'Woraus es besteht',
    partsCaption:
      'Die Buchstaben und die Übergänge dieses Textes. Ein Klick führt in die jeweilige Ansicht — der Weg von „hier stimmt etwas nicht“ zur Ursache.',
    noJoins: 'Keine verbundenen Übergänge in diesem Text.',
    // „keine Wortprobe" rather than „keine nachgefahrene Wortprobe": now that
    // the detail lists the samples themselves, an untraced one appears here
    // with its crop and the way into the editor — so this message means the
    // plate does not write the text at all.
    noSpecimen:
      'Zu diesem Text gibt es keine Wortprobe dieser Hand — beurteilt wird dann allein das Schriftbild oben. Bemängeln geht trotzdem: ⚑ oben.',
    scoreButton: 'Bewerten',
    scoreHint: 'Der eingefrorene Wortbench-Maßstab auf genau dieser Komposition (niedriger ist besser).',
    // Nachfahr-Übersicht: the overview's third tab — every hand-authored word
    // trace stacked over its crop, as a quality pass over one's own pen work.
    tabAuthored: 'Nachgefahren',
    reviewEmpty: 'Noch keine von Hand nachgefahrenen Wortproben.',
    reviewCount: '{{count}} von Hand nachgefahrene Bahnen',
    reviewCountOne: '{{count}} von Hand nachgefahrene Bahn',
    // Blend the plate ink out — a wobble reads best on the naked line.
    reviewBareToggle: 'Nur die Bahn',
    reviewOpenWord: 'Zum Wort',
    reviewDevChip: 'Entwicklungssatz',
    reviewChipsAria: 'Was die Marken dieser Zeile bedeuten',
    reviewDevChipHint:
      'Eines der zehn eingefrorenen Lineal-Wörter des Trace-Benchs — neu speichern verändert die Referenz aller bisherigen Messungen.',
    reviewFrameStale: 'Rahmen veraltet',
    reviewFrameStaleHint:
      'Die gespeicherte Registrierung passt nicht mehr zur Lineatur der Wortprobe — beim nächsten Fixture-Abgleich fiele diese Bahn aus dem Bench. „Nachfahren" öffnet die Bahn im aktuellen Rahmen; Speichern dort schreibt ihn fest.',
  },
  toolbar: {
    pan: 'Schwenken',
    bbox: 'Bbox',
    edit: 'Verschieben',
    lockNeedsBbox: 'Glyph mit Bbox wählen, um ihn als fertig zu sperren',
    unlock: 'Entsperren (wieder bearbeitbar)',
    lock: 'Als fertig sperren (vor Änderungen schützen)',
    unlockAria: 'Glyph entsperren',
    lockAria: 'Glyph als fertig sperren',
    // Followed by the glyph key in the chip label.
    activeGlyph: 'aktiv:',
    noActiveGlyph: 'kein aktiver Glyph',
    deleteBbox: 'Bbox des aktiven Glyphs löschen',
    lockedFirstUnlock: '{{glyph}} ist gesperrt — erst entsperren',
    openWizard: 'Einrichtungs-Wizard für den aktiven Glyph öffnen',
    setup: 'Einrichten',
    diagnoseTooltip: 'Diagnose (Skelett · Canonical · Fit) groß ansehen',
    diagnoseNeedsCanonical: 'Noch kein Canonical — erst im Wizard einen Weg zeichnen',
    diagnose: 'Diagnose',
  },
  // Snackbar + confirm strings of the bbox editing flow (useBboxEditing).
  snack: {
    pickGlyphFirst: 'Wähle erst einen Glyph in der Liste links.',
    lockedNoEdit: '🔒 {{glyph}} ist gesperrt — oben entsperren, um zu ändern.',
    noBboxDrawFirst: '{{glyph}}: hat noch keine Bbox — erst im Modus „Bbox“ zeichnen.',
    editHandleHint: 'Zum Verschieben in die Box fassen, zum Skalieren an einen Griffpunkt (Ecke/Kantenmitte).',
    boxMoved: '{{glyph}}: Box verschoben.',
    boxResized: '{{glyph}}: Box angepasst.',
    bboxSaved: '{{glyph}}: Bbox gespeichert.',
    // Followed by the error in the snackbar message.
    saveFailed: 'Speichern fehlgeschlagen:',
    noBboxYet: '{{glyph}}: noch keine Bbox.',
    locked: '🔒 „{{name}}“ gesperrt.',
    unlocked: '🔓 „{{name}}“ entsperrt.',
    deleteConfirm: 'Bbox für „{{glyph}}“ löschen?',
    deleteConfirmCanonical: ' Das gespeicherte Canonical wird mit entfernt.',
    deleted: '{{glyph}}: gelöscht.',
    // Followed by the error in the snackbar message.
    deleteFailed: 'Löschen fehlgeschlagen:',
  },
  sidebar: {
    sourceLabel: 'Vorlage',
    groupLower: 'Kleinbuchstaben',
    groupUpper: 'Großbuchstaben',
    groupComb: 'Kombinationen',
    groupDigit: 'Ziffern',
    groupPunct: 'Satzzeichen',
    toHome: 'Zur Startseite',
    chartOverview: 'Chart-Übersicht',
    compareOverview: 'Vergleich aller Buchstaben',
    pairsOverview: 'Paar-Matrix (alle Verbindungen)',
    werkbankOverview: 'Werkbank (Wörter · Linsen · Auftragskorb)',
    overlays: 'Overlays',
    all: 'alle',
    none: 'keine',
    // Letter tooltip fragments (composed with the glyph + note).
    statusCanonical: ' · Canonical vorhanden',
    statusBbox: ' · Bbox gesetzt',
    statusEmpty: ' · leer',
    statusLocked: ' · gesperrt (fertig)',
    actionsHint: 'Einrichten · Diagnose · Sperren in der Leiste oben.',
    noBboxHint: 'Noch keine Bbox — im Modus „Bbox“ ein Rechteck auf der Vorlage ziehen.',
    lockedHint: '🔒 Gesperrt (fertig) — oben in der Leiste entsperren, um zu bearbeiten.',
  },
  // Side-by-side comparison of every authored letter (ComparePage): the soll/ist
  // the Diagnose modal only shows one glyph at a time.
  compare: {
    title: 'Vergleich aller Buchstaben',
    intro:
      'Jeder erstellte Buchstabe groß nebeneinander: der unveränderte Tafel-Ausschnitt und „wie geschrieben“ — so lässt sich die Formtreue über das ganze Alphabet auf einen Blick beurteilen, statt Glyphe für Glyphe in der Diagnose.',
    colCrop: 'Original',
    colCanonical: 'Kanonische Form',
    colWritten: 'Wie geschrieben',
    // The two derived faces beside the pair above: what the composer writes in
    // running text, and the statistics that form comes from.
    colLaufform: 'Laufform',
    colSketch: 'Median & Vorkommen',
    colSketchHint:
      'Kräftig: der Median je Anker über den Vorkommen dieser Hand · dünn: die einzelnen Vorkommen · Kreise: MAD-Streuung · gepunktet: die aktuell geschriebene Laufform · Linien: Grund- und Mittellinie.',
    noLaufformShort: 'noch keine Laufform',
    // Two different answers, deliberately not one: below the rebuild's minimum
    // vs. never rebuilt at all for this hand.
    noAggregateShort: 'zu wenige Vorkommen für eine Statistik',
    noAggregateLayer: 'Statistik dieser Hand noch nicht gebildet',
    occurrencesUnknown: 'Vorkommen werden geladen …',
    // Key numbers per letter — the details stay in the detail view.
    fitMean: 'Fit ⌀ {{value}} px',
    fitMeanHint: 'Mittlere Abweichung der eingepassten Vorkommen (geo_rmse) — je kleiner, desto besser sitzt die Form in den Wörtern.',
    scoreNone: 'kein Score',
    scoreNoneHint:
      'Für diese Form ist kein Bildmaß gespeichert — sie wurde vor der Metrik abgeleitet. „Diagnose“ rechnet es neu.',
    // „Bewertung", not „Deckung": which metric stands behind the number depends
    // on the script (Kurrent misst Pixel/Breite, Sütterlin Natürlichkeit hinter
    // einem Deckungs-Gate, qualitaetsmetrik.md §1–§5).
    scoreHint:
      'Bewertung der gespeicherten Form gegen ihren Tafel-Ausschnitt — je nach Schrift Deckung oder Natürlichkeit. Gestempelt bei der letzten Ableitung, nicht neu gerechnet; die Neuberechnung steht in der Diagnose.',
    sortLabel: 'Sortierung',
    sortAlpha: 'Alphabet',
    sortWorst: 'Schlechteste zuerst',
    sortWorstUnavailable: 'Kein gespeicherter Score gelesen — ohne Bewertung gäbe das wieder die alphabetische Reihenfolge.',
    overlayToggle: 'Überlagern',
    overlayHeading: 'Überlagert (Original + Engine darüber)',
    // The two grids double as the overviews of the Buchstaben/Wörter views, so
    // every card carries the way into its own detail.
    openLetter: 'Öffnen',
    openWord: 'Öffnen',
    // The visible word stays „Öffnen" — the card around it says which subject
    // it belongs to. A screen reader gets no card, though: /admin/woerter alone
    // listed 63 buttons all called „Öffnen", so the accessible name names the
    // subject and the visible label stays short.
    openLetterFor: 'Buchstabe {{key}} öffnen',
    openWordFor: 'Wort {{word}} öffnen',
    showCorners: 'Ecken markieren',
    animate: 'Schreiben animieren',
    reload: 'Neu laden',
    empty: 'Noch keine erstellten Glyphen — erst im Wizard einen Weg zeichnen und sperren.',
    noCanonical: 'kein Canonical',
    loadError: 'Diagnose konnte nicht geladen werden.',
    // Tabs: letters (the classic view) vs the connected-writing specimens.
    tabLetters: 'Buchstaben',
    tabWords: 'Wörter',
    tabPairs: 'Verbindungen',
    tabOther: 'Andere Hand',
    wordsIntro:
      'Jede Wortvorlage der Tafel neben demselben Wort „wie geschrieben“ — überlagert liegt die Engine-Schrift maßstabsgetreu (über die Lineatur registriert) auf der Vorlage, damit sofort sichtbar ist, wo Buchstaben oder Übergänge noch abweichen.',
    otherIntro:
      'Vorlagen einer anderen Hand (z. B. die Schülerschrift der Abb. 22) — nur zur Anschauung, nie Referenz der Bewertung.',
    wordsEmpty: 'Diese Vorlage hat keine Wortproben (words.json-Sidecar fehlt).',
    wordsLoadError: 'Wortproben konnten nicht geladen werden.',
    wordRenderError: 'Wort konnte nicht komponiert werden.',
    // Followed by the comma-joined missing glyph_keys.
    missingPrefix: 'fehlend: ',
    specimenAlt: 'Vorlage',
    // Progress of the manual reference set: per-card chip for an authored
    // trace (wording shared with belege.provenanceAuthored) + a toolbar tally.
    authoredChip: 'von Hand ✓',
    authoredCount: '{{done}}/{{total}} von Hand nachgefahren',
    // A specimen whose own ink is clipped: never nachfahrbar, so it leaves the
    // open list and the tally's denominator instead of sitting there forever.
    incompleteChip: 'unvollständig',
    incompleteChipHint:
      'Die Tinte dieser Probe ist angeschnitten (i-Punkt oder letzter Buchstabe fehlt) — sie lässt sich nicht von Hand nachfahren und zählt darum nicht zum Soll. Vermerkt im words.json-Sidecar der Vorlage.',
    // Appended to the tally when the list holds flagged specimens.
    incompleteCount: '{{count}} unvollständig',
    // The status filter over the specimen list — the answer to „was fehlt noch?“
    statusLabel: 'Nachfahren',
    statusAll: 'Alle',
    statusOpen: 'Offen',
    statusAuthored: 'Nachgefahren',
    statusIncomplete: 'Unvollständig',
    statusEmpty: 'Keine Wortprobe passt zu dieser Auswahl (Status oder Suchtext).',
    // Specimen scores (redesign R1b Stufe 2): the frozen wordbench ruler per
    // card, worst first = the work list.
    scoreButton: 'Scores berechnen & sortieren',
    scoreBusy: 'Berechne',
    scoreFailed: 'nicht bewertbar',
    scoreError: 'Einzelne Scores konnten nicht berechnet werden.',
    scoreWorstSegments: 'Größte Abweichungen:',
    scoreLossTitle: 'Loss dieser Wortprobe',
    scoreLossAria: 'Loss erklären',
    openPairEditor: 'Im Paar-Editor öffnen',
    // „Measured vs. composed" on the pair cards (Handmodell H2): what the
    // occurrence and the aggregate layers know about exactly this join. The
    // detailed numbers in the tooltip deliberately reuse the wording of the
    // Werkbank lens (the same statistic must not be named twice differently).
    measuredLabel: 'Gemessen',
    measuredSheetAria: 'Gemessene Werte im Einzelnen',
    measuredGenChamfer: 'Generator-Abstand ⌀ {{value}}',
    // The four reasons a card can carry no measured median, short enough for
    // the chip row — the tooltip spells each of them out in the Werkbank's
    // words. „keine Messung" is reserved for the case it describes: the hand's
    // aggregates are loaded, this join is simply not among them.
    measuredNone: 'keine Messung',
    measuredNoOccurrences: 'keine Vorkommen',
    measuredNoHand: 'keine Hand',
    measuredNoRebuild: 'kein Aggregat',
    measuredNoAccess: 'nicht ladbar',
    measuredFitWarn: 'Fit unsicher',
    measuredFitHint: 'Der Fit dieses Vorkommens ist als unsicher markiert — die Messung trägt hier wenig.',
    measuredUnavailable: 'Messwerte der Hand nicht ladbar (Admin-Zugang nötig) — gezeigt werden nur die Vorkommen.',
    measuredLoadError: 'Vorkommen der Übergänge konnten nicht geladen werden.',
  },
  // The pair matrix (the Übergänge view's overview): every combination of one chosen
  // letter, server-composed — capitals only on the left, per the redesign (R1).
  pairs: {
    title: 'Paar-Matrix',
    intro:
      'Alle Zweier-Verbindungen eines Buchstabens, aus den Einzelformen plus generiertem Übergang komponiert (Versalien nur links). So fällt eine unnatürliche Verbindung sofort auf, ohne sie in einem Wort suchen zu müssen. Klick auf eine Zelle öffnet den Paar-Editor.',
    pickLetter: 'Buchstabe',
    // 30 buttons all called „a", „b", „c" name nothing to a screen reader.
    pickLetterFor: 'Kombinationen von {{key}} zeigen',
    // The NAMES of the two roving `toolbar`s of this view. A container that owns
    // one tab stop needs a composite role, or a screen reader stays in
    // Lesemodus and never hands the arrow keys on (§9.5) — and a role without a
    // name is an unannounced „Symbolleiste".
    anchorBarLabel: 'Ankerbuchstaben',
    cellsLabel: 'Paar-Zellen',
    asFirst: '„{{glyph}}“ als erster Buchstabe',
    asSecond: '„{{glyph}}“ als zweiter Buchstabe',
    empty: 'Noch keine erstellten Glyphen — erst im Wizard einen Weg zeichnen.',
    badgeApproved: 'Override',
    badgeDraft: 'Entwurf',
    // The matrix as a work list (V14): the filter chips, in the order
    // `pairRows.ts` carries them as data.
    filters: {
      'mit-uebersteuerung': 'mit Übersteuerung',
      'mit-korb': 'mit Korb-Auftrag',
      'ohne-vorkommen': 'ohne Vorkommen',
    },
    sortOccurrences: 'Meiste Vorkommen',
    sortOccurrencesUnavailable:
      'Keine gemessenen Vorkommen gelesen — ohne Zahlen gäbe das wieder die alphabetische Reihenfolge.',
    // A cell whose zwei Zeichen fold into ONE glyph: no join to inspect, to
    // override or to complain about, so it carries no counters and opens nichts.
    ligature: 'eine Glyphe',
    // The counters rest on an admin-gated read, so its absence is said out
    // loud rather than shown as „generiert" in every cell.
    overridesUnknown: 'Gespeicherte Übersteuerungen nicht gelesen (Admin-Zugang nötig).',
    openPair: 'Verbindung {{pair}} öffnen',
    // Pair editor (the review/approval surface over glyph_pairs).
    editorTitle: 'Paar-Editor · {{pair}}',
    editorIntro:
      'Beide Buchstaben liegen an der einstellbaren Kopplung (Versatz des rechten Ansatzpunkts relativ zum Abgang des linken). Den Verbindungszug mit dem Stift/Zeiger direkt zeichnen; gespeichert wird er relativ zum Abgangspunkt. Nur freigegebene Overrides ersetzen den generierten Übergang.',
    offsetLabel: 'Versatz',
    clearConnector: 'Zug löschen',
    showSpecimen: 'Vorlage unterlegen',
    previewHeading: 'Live-Ergebnis (/write/word)',
    approveLabel: 'Freigegeben (ersetzt den Generator)',
    approveHint: 'Ohne Freigabe bleibt der Override gespeicherter Entwurf — gerendert wird weiter der Generator.',
    noRowYet: 'Noch kein Override — der Generator schreibt dieses Paar.',
    // {{provenance}} = harvested/authored, {{specimen}} = words.json-Id.
    rowState: 'Override vorhanden · {{provenance}} · Vorlage: {{specimen}}',
    save: 'Speichern',
    close: 'Schließen',
    deleteOverride: 'Override löschen',
    saveFailed: 'Speichern fehlgeschlagen.',
    deleteFailed: 'Löschen fehlgeschlagen.',
    editorLoadError: 'Paar-Daten konnten nicht geladen werden.',
  },
  // What is left of the retired /admin/belege page: the word editor (Werkbank
  // W3: manual re-tracing over the specimen crop → authored rows) plus the
  // three strings the Wörter view still reads beside it (`cropAlt`,
  // `provenanceAuthored`, `editOpen`). The namespace KEY stays `belege` — renaming
  // it would touch four files for no reader, while the visible word „Beleg"
  // now belongs to the Eigenhand Bestand alone (author decision 2026-09-18,
  // Q8 a). The ten leftover keys of the dead page went with that decision,
  // because they carried the retired vocabulary into nothing.
  belege: {
    cropAlt: 'Platten-Ausschnitt',
    provenanceAuthored: 'von Hand nachgefahren',
    // Word editor (Werkbank W3) — manual re-tracing over the specimen crop.
    editOpen: 'Nachfahren',
    editorTitle: 'nachfahren · {{specimen}}',
    editorIntro:
      'Den Schreibweg mit dem Stift direkt über dem Platten-Ausschnitt nachfahren. Jedes Absetzen beginnt einen neuen Zug — die blaue Grundlinie und die gestrichelte Mittellinie zeigen den Rahmen, in dem der Weg gespeichert wird. Gespeichert wird er als „von Hand nachgefahren" (authored): Grundwahrheit für Statistik und Training, keine Rendering-Korrektur — und von keiner Neu-Ernte je überschrieben.',
    editorUndo: 'Letzten Zug zurück',
    editorClear: 'Alle Züge löschen',
    // Zoom slider: scales the crop up to natural writing size on a tablet.
    editorZoom: 'Größe',
    // Fingers are fully inert on the canvas (the writing hand rests there);
    // panning is an explicit mode instead.
    editorModeDraw: 'Schreiben',
    // Anpassen drags the drawn line locally (the wizard's Weg mechanism) —
    // for the one tablet wobble a whole redraw would be disproportionate to.
    editorModeAdjust: 'Anpassen',
    editorModePan: 'Verschieben',
    // Accessible name of the mode toggle group.
    editorModeGroup: 'Modus',
    editorZoomHint: 'Finger sind deaktiviert — zum Verschieben den Schalter nutzen.',
    // Falloff radius of the adjust drag, in x-heights.
    editorNudgeRadius: 'Radius',
    editorAdjustHint:
      'Die Bahn mit dem Stift an einer Stelle ziehen: Punkte im Kreis folgen, außen läuft die Linie weich zurück. Züge werden nie geteilt oder zusammengelegt — nur verschoben.',
    // Saving one of the ten frozen dev-split words re-baselines the trace
    // bench (docs/proposals/tintenfolger.md §2.4) — warn, don't block.
    editorDevWordWarning:
      'Dieses Wort gehört zum eingefrorenen Entwicklungssatz des Trace-Benchs (Lineal). Speichern verändert die Referenz, gegen die alle bisherigen Messungen liefen — danach ist ein datierter §14-Re-Baseline-Eintrag plus Fixture-Abgleich fällig.',
    editorSaveDevConfirm: 'Trotzdem speichern',
    // Shown when the stored registration failed the frame gate: the editor
    // re-expressed the strokes into the sample's current frame on open.
    editorFrameReanchored:
      'Der gespeicherte Rahmen war veraltet — die Bahn liegt jetzt im aktuellen Rahmen der Wortprobe (gleiche Lage im Ausschnitt). Speichern schreibt den neuen Rahmen fest.',
    editorReset: 'Auf gespeicherten Stand zurück',
    editorShowStored: 'Gespeicherte Bahn zeigen',
    // {{strokes}} = number of strokes the save would write.
    editorStrokeCount: '{{strokes}} Züge',
    // {{slots}} = the row's slot labels, unchanged by the editor.
    editorSlots: 'Buchstaben: {{slots}}',
    editorAuthoredHint: 'Speichern ersetzt das automatisch nachgefahrene Vorkommen.',
    editorSave: 'Speichern',
    editorClose: 'Schließen',
    editorSaveFailed: 'Speichern fehlgeschlagen.',
    editorNoHand: 'Keine Hand hinterlegt (weder am Vorkommen noch an der Vorlage) — Speichern nicht möglich.',
    // Shown when the hands row could not be loaded: saving would wipe its
    // era/note (the batch upserts the writer row whole), so it stays disabled.
    editorHandUnresolved:
      'Die Hand „{{id}}" ließ sich nicht laden — Speichern bleibt deaktiviert, damit ihre Metadaten nicht überschrieben werden.',
  },
  // The workbench vocabulary shared by all three views (proposal
  // optimierungs-werkbank.md §2): the statistics blocks (Stufen-Einsicht), the
  // occurrence readouts, and the Auftragskorb (work_items) that replaces
  // feedback-by-screenshot. The ⚑ dialog asks the §4 pre-sort question for
  // letters: solo-wrong belongs in the wizard (the author's own ductus is the
  // truth), word-only-wrong is an algorithm complaint.
  werkbank: {
    title: 'Werkbank',
    intro:
      'Links die Wörter als Rückgrat: jedes nachgefahrene Vorkommen über seinem Platten-Ausschnitt, schlechteste zuerst. Ein Klick auf eine Buchstaben-Box oder einen Übergangs-Punkt schaltet rechts die Linse um; ⚑ (oder Umschalt-Klick) legt das Element als Auftrag in den Korb.',
    loadError: 'Werkbank-Daten konnten nicht geladen werden.',
    empty: 'Noch keine gespeicherten Wort-Vorkommen — erst die Ernte laufen lassen (tools/laufform/harvest.py --apply).',
    filterLabel: 'Wort suchen',
    spineHeading: 'Wörter (schlechteste zuerst)',
    lensHeading: 'Kontext-Linse',
    cropAlt: 'Platten-Ausschnitt',
    // Chips on a word card — same reading as on der Belege-Seite.
    fittedChip: '{{fitted}}/{{total}} gefittet',
    unfittedPrefix: 'fehlt: ',
    rmseChip: 'RMSE ⌀ {{value}} px',
    // The Herkunfts-Chip of a plate line (§5.0, author decision 2026-09-18,
    // Q8 b). „automatisch" WITHOUT the follower's name, unlike the strip chip:
    // `word_instances` records no Verfahren, and rows harvested before the
    // Tintenpfad became the standard follower (A45) may have been laid by the
    // Kette — naming a method here would be a claim the row cannot back.
    provenanceTraced: 'automatisch',
    provenanceAuthored: 'von Hand',
    noSample: 'Kein Platten-Ausschnitt zur specimen_id {{id}} — Sidecar prüfen.',
    // A sample from a FOREIGN writer's plate (the Abb.-22 Schülerschrift). It
    // may stand in this hand's detail as context, but the chip has to say so
    // where the reader looks — never only in the tooltip, because „zählt nicht
    // mit" is a decision, not a detail.
    foreignSetChip: 'andere Hand · {{set}}',
    foreignSetAria: 'Was „andere Hand" bedeutet',
    // The one clause of `foreignSetHint` that has to be READABLE on a work-list
    // row: the consequence. The full sentence stays in the card's InfoHint.
    foreignSetShort: 'zählt in keine Statistik dieser Hand',
    foreignSetHint:
      'Diese Wortprobe stammt aus einem anderen Satz der Vorlage und damit von einer anderen Hand. Sie steht hier als Kontext — in keine Statistik und in keine Kopfzahl dieser Hand geht sie ein, und nachgefahren wird sie hier nicht.',
    // The head of the word detail counts the foreign samples under their own
    // name. Folding them into „n Wortproben" would put another writer into this
    // hand's numbers; leaving them out silently would make the head disagree
    // with the cards below it. One form for both counts — the phrase does not
    // inflect with the number.
    foreignCount: '{{count}} von anderer Hand',
    // The two faces of a word card: left what was MEASURED, right what the
    // engine writes from it — same scale, same Grundlinie, so „trifft der Fit?"
    // und „was macht das System daraus?" nebeneinander lesbar sind.
    faceSpecimenBase: 'Vorlage',
    // No colour names in a caption: „erster Zug grün, letzter blau" is exactly
    // the sentence a colour-blind reader cannot use, and it goes wrong again on
    // every palette tune. The legend carries the mapping instead — the layer
    // switches show colour AND stroke style (Strichart-Regel, design-system §2).
    // The nouns are the one vocabulary of #621: the line is „Bahn", and the
    // layer that reads it as a movement is „Bewegung".
    faceLayerTrace: 'Bahn',
    // „gepunktet", not „gestrichelt": the lift is `liftConnector`, whose stroke
    // is `strokeStyle.dotted` (styles/paper.ts) — a legend that names the
    // wrong stroke style fails the one reader the Strichart-Regel is for.
    faceLayerPath: 'Bewegung (Schreibreihenfolge, Absetzer gepunktet)',
    faceLayerEngine: 'Engine',
    // Herkunft + Datum der gezeichneten Linie. Ohne beides ist ein Pfad eine
    // undatierte Überlagerung und kein Beleg.
    tracePedigree: 'Herkunft: {{herkunft}} · {{datum}} · {{zuege}} Züge',
    pedigreeNoDate: 'ohne Datum',
    faceWritten: 'Vom System geschrieben',
    faceWrittenPending: 'wird geschrieben …',
    // The per-layer switches above the cards.
    layersLabel: 'Ebenen über der Vorlage',
    layersAria: 'Die Ebenen erklären',
    // Both buttons show the SAME line, so they cannot both be „Bahn": the
    // second one is named after what it ADDS — the writing movement — which is
    // what its hint has said all along (author decision 2026-09-18, Q8 b, and
    // the plan's Q10 (i) recommendation).
    layerTrace: 'Bahn',
    layerPath: 'Bewegung',
    layerPathHint:
      'Dieselbe Bahn, als Bewegung gelesen: Farbverlauf in Schreibreihenfolge vom ersten zum letzten Zug, Punkt am Ansatz, Pfeilspitze am Zugende, gepunktet die Absetzer. Bringt die Bahn mit, denn die Bewegung schmückt sie.',
    layerEngine: 'Engine',
    // The Abstandsprofil under a word card: nearest distance of the engine
    // composition per point of the stored trace. A DISPLAY measure of the
    // Werkbank — deliberately not the bench's DTW residual (glossar:
    // Abstandsprofil vs. Residualprofil), which the caption says outright so
    // the curve is never read as dtw_xh.
    profileTitle: 'Abstandsprofil',
    profileCaption:
      'Abstand der Engine zur Bahn, je Punkt der Bahn (nächster Abstand, in x-Höhen; Anzeige-Maß, nicht die Bench-Zahl dtw_xh). Flach nahe 0 = deckungsgleich, Berge = daneben; gestrichelte Senkrechte = Absetzer. Maus über der Kurve zeigt die Stelle im Ausschnitt.',
    profileAxis: 'Bogenlänge der Bahn (xh) → Abstand der Engine (xh)',
    // Interactive overlay elements (also their aria-labels).
    letterBoxAria: 'Buchstabe {{key}} in {{word}} — anklicken für die Buchstaben-Linse',
    joinDotAria: 'Übergang {{left}}→{{right}} in {{word}} — anklicken für die Paar-Linse',
    letterBoxTitle: '{{key}} · RMSE {{rmse}} px',
    letterBoxTitleNoRmse: '{{key}}',
    joinDotTitle: '{{left}}→{{right}}',
    markWord: 'Wort markieren',
    markLetter: 'Buchstabe markieren',
    markPair: 'Übergang markieren',
    // The lens.
    lensEmpty:
      'Nichts ausgewählt. Eine gestrichelte Buchstaben-Box oder einen braunen Übergangs-Punkt im Wort anklicken — hier erscheint dann die passende Linse.',
    lensLetterHeading: 'Buchstabe {{key}}',
    lensPairHeading: 'Übergang {{left}}→{{right}}',
    lensSeenIn: 'gesehen in {{word}}',
    chartFormLabel: 'Tafel-Form',
    chartFormAlt: 'Tafel-Ausschnitt von {{key}}',
    occurrencesLabel: 'Vorkommen in Wörtern ({{count}})',
    noOccurrences: 'Keine gespeicherten Vorkommen zu diesem Element.',
    openWizard: 'Im Wizard öffnen',
    openPairEditor: 'Paar-Editor öffnen',
    // Per-occurrence caption of a pair row: the generated Übergang's distance
    // from the specimen ink (xh units, lower better).
    genChamfer: 'Generator-Abstand {{value}}',
    // The same number under a crop thumbnail, where the tile is ~100 px wide:
    // „Δ" plus the value, the full wording in the tile's title tooltip.
    genChamferShort: 'Δ {{value}}',
    fitDoubtful: 'Fit unsicher',
    // The statistics layers of the Handmodell (Stufenplan H1/H2) inside the
    // lenses: a letter gets its aggregate median with the MAD spread and the
    // pooled layer-1 numbers, a join the measured median connector over its
    // occurrences. Inspection only — nothing is applied (apply-laufform) here.
    // Both blocks name the hand they were derived for; `statsMixedHands` is the
    // warning for occurrences that do not all name the same one.
    statsLetterHeading: 'Statistik',
    statsPairHeading: 'Gemessen vs. komponiert',
    statsHand: 'Hand {{hand}}',
    statsMixedHands: 'mehrere Hände in den Vorkommen — gezeigt: {{hand}}',
    statsLoading: 'Statistik wird geladen …',
    // The first-run silence, and the one that used to speak for it. With zero
    // occurrences there is nothing that could carry a hand, so „keine Hand"
    // named an impossible cause on every card of a fresh Vorlage; this one
    // names the next step instead.
    statsNoOccurrences: 'Noch keine Vorkommen geerntet — die Statistik entsteht aus den vermessenen Wörtern.',
    statsNoHand: 'Keine Hand an den Vorkommen hinterlegt — ohne Hand gibt es keine Statistik.',
    statsUnavailable: 'Statistik nicht ladbar (Admin-Zugang nötig).',
    // Two different silences: the hand has no aggregates at all, or it has
    // them and this one key is missing from them.
    statsNoRebuild: 'Noch kein Aggregat-Neuaufbau für diese Hand.',
    statsNoneLetter: 'Kein Aggregat für diesen Buchstaben (unter der Mindest-Vorkommenszahl).',
    statsNonePair: 'Kein Aggregat für diesen Übergang (unter der Mindest-Vorkommenszahl oder ohne sauberen Fit).',
    statsInstances: '{{count}} Vorkommen',
    statsSpecimens: '{{count}} Vorlagen',
    // German has no plural-s on „Vorkommen", but „Vorlage" needs its singular.
    statsSpecimensOne: '{{count}} Vorlage',
    statsRmse: 'RMSE ⌀ {{mean}} / max {{max}} px',
    statsXh: 'x-Höhe ⌀ {{value}} px',
    statsPositionsLabel: 'Positionen',
    statsKindsLabel: 'Herkunft',
    statsLetterSketch: 'Aggregat-Median (Laufform-Quelle)',
    statsLetterSketchAria: 'Median-Anker von {{key}} mit MAD-Streuung',
    statsLetterSketchLegend: 'Punkte: Median-Anker · Kreise: MAD-Streuung · Linien: Grund- und Mittellinie',
    // With the occurrence chains drawn behind the median: the same reading as
    // the pair sketch („dünn: Vorkommen · kräftig: Median"), so both layers
    // answer „sind sich die Vorkommen ähnlich?" the same way.
    statsLetterSketchLegendWithOcc:
      'dünn: die einzelnen Vorkommen · kräftig: Median-Anker · Kreise: MAD-Streuung · Linien: Grund- und Mittellinie',
    // The dotted chain: what the engine writes TODAY, against the median that
    // would replace it — the „see the difference" view before the overwrite.
    // Names the stroke style, never the hue (Strichart-Regel, design-system §2).
    statsLetterSketchLegendLaufform: 'gepunktet: die aktuell geschriebene Laufform',
    // Freshness of the rendered running form, read straight off the row.
    laufformCurrent: 'Laufform aktuell',
    laufformStale: 'Laufform veraltet · Abstand {{value}}',
    laufformNone: 'noch keine Laufform gespeichert',
    laufformIncomparable: 'Laufform nicht vergleichbar (Ankerzahl)',
    statsPairSketchAria: 'Median-Verbindung {{left}}→{{right}} über den gespeicherten Vorkommen',
    statsPairSketchLegend: 'dünn: Vorkommen · kräftig: Median · Punkt: Versatz mit MAD',
    // Occurrences the rebuild itself skipped (fit_bad) are not drawn — said
    // out loud so the sketch is not read as "all occurrences".
    statsPairSketchHidden: '{{count}} ohne sauberen Fit ausgeblendet',
    statsPairReadOnly: 'Nur Anschauung: geschrieben wird weiter der generierte Übergang.',
    // The pooled dissection QC (all in x-height units, lower better).
    statsGenChamfer: 'Generator-Abstand ⌀ {{mean}} / max {{max}}',
    statsHarvestChamfer: 'Ernte-Abstand ⌀ {{value}}',
    statsResid: 'Fit-Rest ⌀ {{mean}} / max {{max}}',
    statsGapInk: 'Tinte im Zwischenraum {{value}}',
    // With and without a stored spread: an absent MAD gets no ± clause at all
    // („± 0,00" would claim a measurement nobody made).
    statsOffset: 'Versatz {{x}} / {{y}} ± {{madX}} / {{madY}}',
    statsOffsetNoMad: 'Versatz {{x}} / {{y}}',
    // Rebuild (admin POST, per layer). Non-rendering maintenance, deliberately
    // quiet — the Laufform-Übernahme is NOT offered here.
    statsRebuild: 'Neu aufbauen',
    statsRebuildFailed: 'Neuaufbau fehlgeschlagen.',
    statsRebuiltLetters: '{{stored}} Buchstaben aus {{count}} Vorkommen, {{skipped}} übersprungen',
    statsRebuiltPairs: '{{stored}} Paare aus {{count}} Vorkommen, {{skipped}} übersprungen',
    // The Auftragskorb.
    korbTitle: 'Auftragskorb',
    korbOpenCount: '{{count}} offen',
    korbEmpty: 'Noch keine Aufträge — ⚑ markiert ein Element, „Notiz anlegen“ hält eine Kleinigkeit fest.',
    korbShowDone: 'erledigte anzeigen',
    korbDelete: 'Auftrag löschen',
    korbLoadError: 'Aufträge konnten nicht geladen werden (Admin-Zugang nötig).',
    korbDeleteError: 'Löschen fehlgeschlagen — der Auftrag liegt weiter im Korb.',
    // The three selects over the loaded rows. „Status" reuses the short words
    // below rather than the group headings, which are sentences. Choosing
    // „Erledigt" also reveals the archive — otherwise the filter would visibly
    // select nothing while the switch is off.
    korbFilterStatus: 'Status',
    korbFilterKind: 'Ebene',
    korbFilterStage: 'Stufe',
    korbFilterAll: 'alle',
    korbStatusShort: {
      open: 'Offen',
      ack: 'In Arbeit',
      done: 'Erledigt',
      returned: 'Zurückgegeben',
    },
    korbNoMatch: 'Kein Auftrag passt zu diesem Filter.',
    // Only shown while the archive really is hidden: most rows that carry a
    // Stufe are erledigt, so without this line a Stufen-Filter reads as broken.
    korbNoMatchDone: 'Erledigte sind ausgeblendet — „erledigte anzeigen“ einschalten.',
    // Deleting is irreversible and there is no undo, so it gets a question
    // first — and an erledigter Auftrag gets a second sentence, because with it
    // the whole handling record (Verstandenes · Stufe · Auflösung) goes.
    korbDeleteConfirmTitle: 'Auftrag löschen?',
    korbDeleteConfirmBody: 'Der Auftrag wird endgültig entfernt — das lässt sich nicht rückgängig machen.',
    korbDeleteConfirmArchive:
      'Dieser Auftrag ist bereits abgeschlossen. Sein Protokoll — Verstandenes, diagnostizierte Stufe und Auflösung — ist Historie und kann später noch gebraucht werden. Mit „erledigte anzeigen“ ausblenden statt löschen.',
    korbDeleteConfirmSubmit: 'Endgültig löschen',
    // The target-less quick note: a general Kleinigkeit (a UI wrinkle, a
    // wording slip) that belongs to no letter and is too small for an Issue.
    korbAddNote: 'Notiz anlegen',
    korbNoteLabel: 'Was ist aufgefallen?',
    korbNotePlaceholder: 'z. B. „Löschen im Korb wirkt erst nach Neuladen“',
    korbAddSubmit: 'Ablegen',
    korbAddError: 'Notiz konnte nicht abgelegt werden.',
    // The handling protocol (§5): what the working session wrote back before it
    // started, and the admin's veto if it understood the wrong thing.
    korbReturned: 'Zurückgegeben — braucht deine Hand',
    korbInProgress: 'In Arbeit',
    korbDoneHeading: 'Erledigt',
    korbUnderstanding: 'Verstanden als:',
    korbReproduced: {
      yes: 'nachvollzogen',
      partly: 'teilweise nachvollzogen',
      no: 'nicht nachvollziehbar',
    },
    // The diagnosed stage of the writing path (§3), as the archive shows it.
    korbStage: {
      chart_ductus: 'Tafel-Duktus',
      laufform: 'Laufform',
      join_rule: 'Übergangs-Grammatik',
      composition: 'Komposition',
      pair_override: 'Paar-Override',
      // The KEY is the wire value `word_trace` and stays; only the label moves
      // to the one noun.
      word_trace: 'Wort-Bahn',
      // Names no step of the writing path: der Buchstabe stimmte, der Erkenner
      // nicht (§8).
      landmark_detector: 'Landmarken-Erkennung',
      not_reproducible: 'nicht nachvollziehbar',
    },
    korbReject: 'missverstanden',
    korbRejectLabel: 'Was ist gemeint?',
    korbRejectSubmit: 'zurück in den Korb',
    korbCorrectionPrefix: 'Korrektur:',
    korbRejectError: 'Zurückweisen fehlgeschlagen — der Auftrag bleibt in Arbeit.',
    kindLetter: 'Buchstabe',
    kindPair: 'Übergang',
    kindWord: 'Wort',
    kindNote: 'Notiz',
    kindLandmark: 'Landmarke',
    // Not a Korb kind of its own: an Abzug from the Abzugs-Linse files as a
    // plain LETTER item (author decision 2026-09-23). The word heads the first
    // line of its note and names it in the filing dialog.
    penaltyHead: 'Abzug',
    // The filing dialog.
    dialogTitle: 'Auftrag einreichen',
    dialogTarget: 'Ziel',
    dialogSeenIn: 'gesehen in',
    // A freely typed combination or word has no plate to point at — the row
    // says so rather than inventing a reference.
    dialogNoSpecimen: 'ohne Vorlagenbezug (frei eingetippt)',
    // The §4 pre-sort question — the ONE triage step asked of the human; the
    // stage diagnosis itself stays the working session's duty.
    presortQuestion: 'Sieht der Buchstabe einzeln (in der Tafel-Ansicht daneben) auch falsch aus?',
    presortHint:
      'Ja heißt: der eigene Duktus ist die Wahrheit — im Wizard nachbessern, kein Auftrag. Nein heißt: solo stimmt er, im Wort nicht — das ist Algorithmus-Gebiet und gehört in den Korb.',
    presortYes: 'Ja — im Wizard nachbessern',
    presortNo: 'Nein — Auftrag einreichen',
    noteLabel: 'Notiz (was stört?)',
    submit: 'In den Korb legen',
    cancel: 'Abbrechen',
    submitFailed: 'Auftrag konnte nicht gespeichert werden.',
    submitted: 'Auftrag abgelegt.',
  },
  diagnostics: {
    // Followed by the glyph label in the dialog title.
    title: 'Diagnose ·',
    close: 'Diagnose schließen',
    noCanonical: 'Noch kein Canonical — erst im Einrichten-Wizard einen Weg zeichnen und speichern.',
    // Section headings of the single-page diagnostic flow.
    sectionPipeline: 'Vom Original zur Vorlage',
    sectionFit: 'Einpassung an das Original',
    sectionWritten: 'Fertig geschrieben',
    diagnosticIntro:
      'Alle Verarbeitungsstufen auf einen Blick: vom unveränderten Ausschnitt der Vorlage über das gemessene Skelett bis zur fertigen kanonischen Form — jede Stufe soll dem Original ähnlicher werden, nicht abstrakter.',
    fitIntro:
      'Die Generalprobe der Bibliothek: Die kanonische Vorlage wird elastisch auf das Skelett des Originals gelegt — mit derselben Einpassung werden später echte Schreibproben vermessen. Mit dem λ-Regler die Regularisierung abwägen: niedrig folgt dem Skelett, hoch hält die Form zusammen.',
    writtenCaption:
      'Die Vorlage, wie der Duktus sie schreibt: Strich für Strich, mit echtem Absetzen zwischen den Zügen. Genau so erscheint der Buchstabe später im Quiz — und so soll er einmal auf der Startseite schreiben.',
    computing: 'Diagnose wird gerechnet …',
    noCanonicalShort: 'noch kein Canonical — erst Strich aufnehmen',
    // The quality route's 409: a row older than the pixel-space trace meta.
    // „neu laden" cannot help there, so it gets its own sentence.
    noPixelAnchors: 'Dieser Zeile fehlen die Pixel-Anker — erst im Wizard neu abtasten oder nachzeichnen.',
    reload: 'neu laden',
    cropHeading: 'Original (Tafel-Ausschnitt)',
    cropCaption:
      'Der unveränderte Ausschnitt der Vorlage (nach Ausschluss-Maske). Er ist der Maßstab: Jede weitere Stufe wird an diesem Bild gemessen.',
    // Followed by the anchor count "(…)" in the column heading.
    skeletonHeading: 'Skelett & Stützstellen',
    skeletonCaption:
      'Rot: die Mittelachse (Skelett) der binarisierten Tinte — auf ihr wird die Strichbreite (Schwellzug) gemessen. Orange: die Stützstellen des nachgezeichneten Wegs. Türkise Rauten: erkannte Umkehrpunkte (Ecken) — dort wird der Spline geteilt, damit die Ecke spitz bleibt. Liegen Stützstellen neben der Tinte, leidet die Breitenmessung — dann den Weg im Wizard neu zeichnen.',
    // Followed by "{deg}°)" in the column heading.
    canonicalHeading: 'Kanonische Form (Stil-Schräglage',
    canonicalCaption:
      'Die fertige Vorlage in Schriftkoordinaten (Grundlinie = 0, Mittellinie = 1): Weg plus gemessene Strichbreite als gefüllte Silhouette, Schleifenaugen bleiben offen. Sie soll dem Original links zum Verwechseln ähnlich sehen.',
    guidesReadout: 'Grundlinie=0 · Mittellinie=1 · Oberlinie={{ascender}} · Unterlinie={{descender}}',
  },
  fit: {
    computing: 'Einpassung wird gerechnet …',
    overlayHeading: 'Original · Skelett · Ausgangslage (grau) · Einpassung (rot)',
    overlayCaption:
      'Die rote Füllung ist die eingepasste Vorlage mit ihrer gemessenen Strichbreite — sie soll die Originaltinte decken. Grau gestrichelt: die Ausgangslage vor der Einpassung; blassrot: das Skelett, auf das eingepasst wird.',
    converged: 'eingepasst',
    notConverged: 'Abweichung zu groß',
    // Preceded by the iteration count in the chip label.
    iterations: 'Iter.',
    // Composed metric labels (values + units stay in the component).
    geoRmse: 'Geometrie-RMSE:',
    widthRmse: 'Breiten-RMSE:',
    coverageRmse: 'Abdeckungs-RMSE:',
    maxAnchorDelta: 'max. Anker-Δ:',
    lambdaHint: 'Geometrie folgt dem Skelett; λ (Tikhonov) hält die Vorlage zusammen — niedrig = näher am Skelett, hoch = formtreuer.',
    // Followed by the current λ value.
    regularization: 'Regularisierung λ =',
  },
  quality: {
    sectionTitle: 'Qualität & Neu ableiten',
    intro:
      'Bildraum-Vergleich: Wie gut deckt die gerenderte Silhouette die Originaltinte? Links der gespeicherte Stand, rechts was eine Neuableitung aus dem gezeichneten Weg mit dem aktuellen Code erreichen würde — erst vergleichen, dann übernehmen.',
    computing: 'Qualität wird gerechnet …',
    // Heading of the per-category breakdown here: the wizard's version says
    // „(optimiert)" because it breaks down a preview — these two cards break
    // down a form that exists.
    breakdownHeading: 'Abzüge nach Kategorie',
    breakdownHint: 'Wo diese Form Punkte verliert — höher = mehr Abzug, wie im Glyph-Bench.',
    stored: 'Gespeichert',
    candidate: 'Neu ableitbar',
    noCandidate: 'Kein Roh-Weg gespeichert — Neuableitung nicht möglich.',
    // Composed metric labels (values + units stay in the component).
    //
    // `iou` and `gate` below keep the word „Deckung" on purpose: both are the
    // POSITIVE quantity, higher = better. Only the per-category ABZUG in the
    // breakdown is „Deckungslücke" (de/wizard.ts `optimize.cat.coverage`) —
    // that one is `1 − gate`. Two names because they run in opposite
    // directions and used to stand three lines apart under one word.
    score: 'Score',
    iou: 'Deckung (IoU):',
    chamfer: 'Randabstand:',
    geoRmse: 'Mittellinien-RMSE:',
    waviness: 'Welligkeit:',
    // Sütterlin (Gleichzug) naturalness metric: overall naturalness + coverage gate.
    naturalness: 'Natürlichkeit:',
    gate: 'Deckungs-Gate:',
    // Followed by the score delta, e.g. "+2.3".
    delta: 'Δ Score:',
    apply: 'Neu ableiten & speichern',
    applyHint:
      'Überschreibt die gespeicherte Vorlage mit der Neuableitung aus dem Roh-Weg — bewusste Aktion, wirkt auch bei gesperrten Glyphen.',
    applied: 'Vorlage neu abgeleitet und gespeichert.',
  },
  // Bulk re-derive of all authored glyphs (RederiveAllDialog).
  rederive: {
    button: 'Alle neu ableiten',
    // The button had a hover that described the overwrite. It said what `intro`
    // says one click later, where every reader meets it and nothing has been
    // written yet — so the hover was a mouse-only duplicate of a warning, and
    // a second home for one sentence is how wording drifts (V25, §9.4).
    title: 'Alle Glyphen neu ableiten',
    intro:
      'Berechnet jede erstellte Glyphe aus ihrem Roh-Weg neu (aktueller Code, aktuelle Ankerdichte) und überschreibt die gespeicherte Vorlage — mit Score vorher/nachher pro Buchstabe. Rote Δ-Werte heißen: verschlechtert — in der Diagnose prüfen.',
    start: 'Alle neu berechnen & überschreiben',
    cancel: 'Abbrechen',
    close: 'Schließen',
    colLetter: 'Buchstabe',
    colBefore: 'vorher',
    colAfter: 'nachher',
    colDelta: 'Δ Score',
    colStatus: 'Status',
    statusPending: 'wartet',
    statusScoring: 'rechnet …',
    statusApplying: 'speichert …',
    statusDone: 'fertig',
    statusFailed: 'Fehler',
    noRawPath: 'Kein Roh-Weg gespeichert — im Wizard neu zeichnen.',
    summary: '{{improved}} verbessert · {{worse}} verschlechtert · Ø Δ {{mean}}.',
    worseHint: 'Verschlechterte Buchstaben in der Diagnose prüfen — ggf. den Weg neu zeichnen.',
    empty: 'Keine erstellten Glyphen vorhanden.',
  },
  // Die Eigenhand-Ansicht: Bestand der eigenen Schreibproben (welche Streifen
  // gibt es wie oft, welche Zeichen und Übergänge sind damit belegt) und der
  // Bogendruck. Die Scans selbst bleiben lokal — hier stehen nur die Zahlen.
  eigenhand: {
    title: 'Eigenhand',
    // The role's first appearance on its own page carries the gloss once
    // (author decision 2026-09-18, Q8 a); the nav item and the chips after it
    // stay the bare label. The gloss itself is NOT inlined here — `EigenhandView`
    // prefixes `shell.roleEigenhandGloss`, so the wording of a role lives in
    // exactly one place and the Scope-Leiste cannot drift away from this page.
    intro:
      'Die eigene Schreibprobe: welche Streifen bereits geschrieben und angenommen sind, welche Zeichen und Übergänge damit belegt sind — gemessen an dem, was der Streifenplan insgesamt hergibt. Die Scans selbst bleiben auf dem eigenen Rechner; hier stehen nur die Zahlen und der Druck.',
    // The four Unteransichten behind `?reiter=` (shell/focus.ts). The name is
    // spelled out in the address bar, so it is the button's label here too — a
    // switch whose caption cannot be found again in the URL would give half the
    // linkability back.
    ansichten: {
      bestand: 'Bestand',
      streifen: 'Streifen',
      statistik: 'Statistik',
      drucken: 'Drucken',
    },
    ansichtAria: 'Unteransicht der Eigenhand',
    // The tab title carries three segments: hand area · Unteransicht ·
    // Werkbank („Eigenhand · Streifen · Werkbank"). „Streifen" alone does not
    // say what the strips are OF when a second tab is open beside it.
    tabSubject: 'Eigenhand · {{ansicht}}',
    hand: 'Hand',
    // `handHelp` („Neue Hand: <schreiber>-<stil>") is gone: the field is now
    // always a picker over the hands the server knows. That also took the old
    // way to the FIRST hand with it — it hung on exactly this free-text field
    // and on an invented `mn-<stil>` default. So the sentence may not promise
    // it any more; it names the path that really exists. `setup` writes the
    // server record, which puts the hand into this very picker through
    // GET /eigenhand/setups and lets the sheet printer work under it
    // (tools/eigenhand/setup.py).
    //
    // Since the `?reiter=` split this sits in the SHELL, so it shows on all
    // four Unteransichten — „unten" pointed at nothing on three of them. It
    // says „für diese Schrift": the active hand always belongs to the
    // Vorlage's script (V19), so a Kurrent Vorlage stands here without one
    // even beside a written Sütterlin hand.
    noHands:
      'Für diese Schrift ist noch keine Hand erfasst. Eine neue entsteht mit ihrem stehenden Setup — danach steht sie hier zur Auswahl und kann Bögen drucken:',
    // The placeholder is QUOTED: `<schreiber>` unquoted is a redirection to
    // bash, so one copy-and-run would write a file into the working directory
    // instead of passing an argument. The style comes from the open Vorlage,
    // so the line never names a script that is not in front of the reader.
    noHandsCommand:
      'ADMIN_TOKEN=… uv run python -m tools.eigenhand.setup --hand "<schreiber>-{{style}}" --feder … --tinte … --papier … --geraet scanner',
    // The reads behind the picker are admin-gated and a 401 is not retried.
    // Without this sentence the result would look like „this script has no
    // hand" — a claim about data that never arrived.
    handsError: 'Die erfassten Hände konnten nicht geladen werden.',
    loadError: 'Der Bestand konnte nicht geladen werden.',
    stripsTitle: 'Streifen',
    stripsBelegt: 'belegt',
    stripsUnterwegs: 'unterwegs',
    stripsGeplant: 'geplant',
    stripsTotal: 'im Plan',
    fassungenTitle: 'Fassungen',
    fassungenAngenommen: 'angenommen',
    fassungenVerworfen: 'verworfen',
    sheetsTitle: 'Bögen',
    sheetsPrinted: 'gedruckt',
    sheetsLast: 'zuletzt {{sheet}}',
    coverageTitle: 'Zeichen',
    coverageJoins: 'Übergänge',
    coverageOf: '{{covered}} von {{possible}}',
    coverageBelege: '{{belege}} Belege',
    bucketKlein: 'Kleinbuchstaben',
    bucketGross: 'Großbuchstaben',
    bucketLigatur: 'Ligaturen',
    bucketZiffer: 'Ziffern',
    bucketZeichen: 'Sonderzeichen',
    keyTooltip: '{{key}}: {{belege}} geschrieben, {{planned}} im Plan',
    joinsIntro:
      'Alle Übergänge, die der Plan hergibt — die noch offenen zuerst, nach Häufigkeit im Plan sortiert.',
    joinsShowOpen: 'nur offene zeigen',
    joinsEmpty: 'Alle Übergänge des Plans sind belegt.',
    quotenTitle: 'Quoten',
    // The panel's caption used to be `quotenTitle` again by mistake, so „Quoten"
    // stood twice above its own text. This is the caption the neighbours all
    // have: one line saying what the block shows.
    quotenCaption:
      'Wie viel des Übergangsraums die Hand schon belegt und wie tief — gewichtet nach Häufigkeit im Korpus.',
    // The panel says WHAT is missing; the command that fixes it stands once, in
    // „Am Rechner weiter" (`uebergabe.karten.universe_push`). Before the
    // Übergabekarten this sentence carried its own copyable command, and the
    // same step was then stated in two places at once.
    quotenNone:
      'Erstbeleg- und Ausbau-Quote brauchen die Übergangsraum-Gewichte; die liegen noch nicht in der Datenbank. Der Befehl dazu steht auf dieser Seite unter „Am Rechner weiter".',
    // The statistik Unteransicht. It carries two of the four §7.2 figures:
    // the pen half width and the Tintentreue distribution (`statistikTreue`).
    // The other two stand as a labelled Leerfläche — saying what will land
    // here is more honest than a surface that looks as though there is
    // nothing to be had.
    statistikIntro:
      'Was die Tinte dieser Hand sagt — im Unterschied zum Bestand, der sagt, wie weit die Hand gekommen ist. Gemessen wird je Fassung beim Einlesen; hier steht die Zusammenfassung über alle.',
    statistikNibTitle: 'Feder-Halbbreite',
    statistikNibCaption:
      'Median der halben Strichbreite auf der Mittellinie, in x-Höhen — über alle angenommenen Fassungen dieser Hand, an denen eine Messung liegt, unabhängig davon, ob ihr Streifenbild schon hochgeschoben ist. Dieselbe Zahl dient jeder Fassung als Vergleichsmaß am Befund.',
    statistikNibValue: '{{value}} x-Höhen',
    statistikNibFrom: 'Median aus {{count}} gemessenen Fassungen',
    statistikNibNone: 'nicht gemessen',
    statistikNibNoneHint:
      'Keine angenommene Fassung dieser Hand trägt eine Federmessung — entweder ist noch keine Siebung hochgeschoben, oder die Fassungen stammen aus der Zeit vor dem Streifen-Befund. Eine fehlende Messung ist keine Null.',
    statistikSoonTitle: 'Kommt hierher',
    statistikSoonCaption:
      'Beschriftete Leerfläche: die beiden übrigen Größen aus dem Plan sind noch nicht gebaut; sie stehen hier, damit die Fläche sagt, was sie einmal trägt.',
    // The Tintentreue distribution: the per-box Ampel COUNTED over the hand,
    // never folded into one number. Step and reason are the server's words
    // (`core/eigenhand/tintentreue.py`); these strings only say what the count
    // itself says. A link into the Nachfahr-Liste stands only where a list
    // axis selects EXACTLY the counted boxes.
    statistikTreue: {
      title: 'Tintentreue-Verteilung',
      caption:
        'Bei wie vielen Wortkästen dieser Hand die Bahn der Tinte folgt, teils folgt oder nicht folgt — und wie viele noch niemand beurteilt hat, mit ihrem Grund. Gezählt über alle abgelegten Fassungen, dieselben Kästen wie in der Nachfahr-Liste.',
      vorlaeufig: 'vorläufig',
      vorlaeufigTitle: 'Schwellen der Ampel',
      vorlaeufigAria: 'Warum die Verteilung vorläufig ist',
      stand: 'Schwellen vom {{stand}}.',
      // More than one date means the count spans a calibration; neither is
      // then printed as „the" date.
      staende: 'Die gezählten Kästen tragen mehrere Schwellen-Stände: {{staende}}.',
      eineHand:
        'Die Schwellen gelten für diese eine Hand. Die Verteilung einer anderen Hand ist mit dieser nicht vergleichbar.',
      loading: 'Kästen werden gezählt …',
      loadError: 'Die Kästen dieser Hand konnten nicht gelesen werden.',
      emptyNoStrips:
        'Für diese Hand ist noch kein Streifen abgelegt — es gibt keine Kästen zu zählen. Die Streifen kommen mit „sync --mit-streifen" herauf.',
      emptyNoBoxes: 'Die abgelegten Fassungen dieser Hand tragen keinen Wortkasten aus dem Streifenplan.',
      // `kaesten`/`fassungen` arrive with their noun already inflected.
      summary: '{{kaesten}} in {{fassungen}} · {{gemessen}} davon beurteilt',
      kasten: { one: '{{count}} Kasten', many: '{{count}} Kästen' },
      fassung: { one: '{{count}} Fassung', many: '{{count}} Fassungen' },
      nothingMeasured:
        'Noch ist kein Kasten gemessen — alle stehen grau. Die Ampel liest die Sensoren, die der Folger beim Nachfolgen mitschreibt; Fassungen aus einem Lauf vor dem Formatwechsel bleiben grau, bis sie einmal neu gefolgt werden.',
      count: '{{kaesten}} ({{share}} %)',
      gruendeSensor: 'entschieden von',
      gruendeGrau: 'Grund',
      grund: '{{name}}: {{count}}',
      link: 'in der Liste',
      linkAria: '{{name}}: {{kaesten}} in der Nachfahr-Liste zeigen',
      // The list deliberately has no axis per Ampel step, but its Schwere
      // order puts the red boxes first anyway.
      toList: 'Zur Nachfahr-Liste — rot zuerst',
      perFassungShow: 'Je Fassung ({{count}})',
      perFassungHide: 'Je Fassung ausblenden',
      perFassungAria: 'Tintentreue je Fassung',
      colFassung: 'Streifen · Fassung',
      colKaesten: 'Kästen',
    },
    statistikSoonBelege:
      'Belegzahlen im Verlauf — wie die Abdeckung über die Sitzungen gewachsen ist. Braucht einen datierten Bestandsverlauf (Phase 3).',
    statistikSoonStapel:
      'Ausschnitt-Stapel — dieselbe Stelle aus allen Fassungen übereinander, als Bild. Braucht die Fassungs-Auswahl aus der Streifen-Ansicht (Phase 3).',
    queueTitle: 'Nächste Streifen',
    printTitle: 'Bogen drucken',
    printIntro:
      'Erzeugt die nächsten Bögen aus der Warteschlange und schreibt sie mit — dieselbe Auswahl wie im Terminal. Jeder Auftrag beginnt vorn im Plan, ohne die schon belegten Streifen (ein gedruckter, aber nicht geschriebener Bogen hält nichts zurück); die Seiten eines Stapels setzen die Reihe fort, und der Stapel kommt als ein PDF.',
    printSheets: 'Bögen',
    printRepeat: 'Versuche je Streifen',
    printAction: 'Bögen erzeugen',
    printing: 'wird erzeugt …',
    printError: 'Der Bogen konnte nicht erzeugt werden.',
    printed: '{{count}} Bogen erzeugt: {{sheets}}',
    openPdf: 'PDF öffnen',
    openStackPdf: 'Stapel als ein PDF öffnen ({{count}} Seiten)',
    pdfError: 'Das PDF konnte nicht geladen werden.',
    // No command under the print result any more: the `pull` of the Bogen just
    // printed is an Übergabekarte on the Bestand now and survives a reload
    // there — this hint existed only in the session that had just printed.
    printedNext: 'Der nächste Schritt am Rechner steht unter „Bestand → Am Rechner weiter" — auch nach dem Neuladen.',
    setupTitle: 'Stehendes Setup',
    setupIntro:
      'Feder, Tinte und Papier sind Parameter der ganzen Kampagne, nicht Angaben eines einzelnen Imports — einmal hier eintragen, dann liest ingest sie als Vorgabe. Was eine Sitzung wirklich benutzt hat, steht zusätzlich an jeder Fassung.',
    setupFeder: 'Feder',
    setupTinte: 'Tinte',
    setupPapier: 'Papier',
    setupGeraet: 'Aufnahmegerät',
    setupLabel: 'Bezeichnung',
    setupNote: 'Notiz',
    setupSave: 'Setup sichern',
    setupSaving: 'wird gesichert …',
    setupSaved: 'Gesichert, Stand {{stand}}.',
    setupNone:
      'Für diese Hand ist noch kein Setup hinterlegt. Vor der ersten Sitzung eintragen — Fassungen, die davor eingelesen werden, tragen keine Feder-, Tinten- und Papierangabe.',
    setupError: 'Das Setup konnte nicht gesichert werden.',
    // Label + confirmation of the copy button beside every command.
    commandCopy: 'Befehl kopieren',
    commandCopied: 'kopiert',
    // ——— Übergabekarten ———
    // A media break shown rather than hidden: what can only happen at the
    // machine stands as a card with a title, the reason, the command and
    // „Danach hier" — and goes as soon as the state is there. WHICH card is
    // due is decided once, server-side (`core/eigenhand/faellig.py`); the
    // commands arrive as code from there and only the German copy lives here,
    // keyed by rule id. An id without copy renders no card — never a blank one.
    uebergabe: {
      title: 'Am Rechner weiter',
      caption:
        'Schritte, die am Schreib-Rechner laufen müssen — in der Reihenfolge, in der sie dran sind. Gezeigt wird nur, was der Server sehen kann: einen Schnappschuss oder ein eingelesenes Blatt kann er nicht bestätigen.',
      // The clipboard does not reach from the tablet to the machine, so under
      // the cards stands the twin that prints the same list over there.
      rechnerLead: 'Am Rechner: ',
      rechnerBefehl: 'uv run python -m tools.eigenhand.report --hand {{hand}} --faellig',
      danach: 'Danach hier: {{was}}',
      reihenfolge: 'Reihenfolge: {{wie}}',
      // Only when the server sees more than one open Bogen: the command on the
      // card fetches ONE, and a sheet left lying around must not hide the one
      // just printed.
      weitereBoegen: 'Auch offen: {{weitere_boegen}} — je Bogen ein eigener Aufruf.',
      karten: {
        setup_pull: {
          titel: 'Ausrüstung auf den Schreib-Rechner holen',
          warum:
            'Feder, Tinte und Papier stehen in der Datenbank, gelesen werden sie beim Einlesen aber lokal. Was auf dem Schreib-Rechner liegt, sieht der Server nie.',
          danach: 'nichts — die Karte geht, sobald die erste Fassung dieser Hand ankommt.',
          reihenfolge: 'einmal je Rechner, vor der ersten Sitzung.',
        },
        universe_push: {
          titel: 'Übergangsraum-Gewichte fehlen',
          warum:
            'Erstbeleg- und Ausbau-Quote rechnen gegen die Gewichte aus den Konsult-Korpora, und die Warteschlange ordnet danach. Die Korpus-Bytes bleiben lizenzbedingt lokal; hochgeschoben wird nur die abgeleitete Tabelle.',
          danach: 'die Quoten-Tafel füllt sich, und die nächsten Streifen stehen nach gewichtetem Soll-Gewinn.',
          // This push is the ONE eigenhand write that replaces an existing
          // build (proposal §7.1), so the snapshot stands in front of it, the
          // way it does for --apply.
          reihenfolge:
            'vom Rechner mit den Konsult-Korpora, und weil dieser Push einen vorhandenen Bau ersetzt: erst ein Schnappschuss (tools.dbsnapshot), dann --push.',
        },
        bogen_pull: {
          titel: 'Bogen {{sheet}} ist unterwegs — {{offen}} Zeile/Zeilen ohne Fassung',
          warum:
            'Gedruckt ist er, verbucht noch nicht. Layout und PDF holt sich der Schreib-Rechner selbst; der Scan bleibt lokal, ihn kann der Server nicht sehen.',
          danach: 'die Zeilen zählen als Fassungen, sobald sie hochgeschoben sind.',
          reihenfolge: 'danach einlesen → Siebung → ablegen → hochschieben.',
        },
        sync_streifen: {
          titel: '{{ohne_bild}} Fassung/Fassungen ohne Streifenbild',
          warum:
            'Die Zählung ist oben, das Bild liegt noch auf dem Rechner: Streifenbilder reisen nur auf ausdrückliches Verlangen mit, weil sie zum reservierten Datensatz gehören.',
          danach: 'die Streifen erscheinen unter „Geschriebene Streifen".',
          reihenfolge: 'jederzeit; das private Archiv bleibt die Urfassung.',
        },
        // This one card the view builds itself: which Fassung carries a Bahn
        // is something the strips listing cannot say today (the column is
        // deferred), while in the open Fassung the answer is loaded anyway.
        // So it stands at the Fassung, not in the block above — and its
        // command is the DRY RUN, because a copy button never hands over a
        // command that replaces what is there.
        bahn_folgen: {
          titel: 'Für diese Fassung ist noch keine Bahn gespeichert',
          warum:
            'Der Folger liegt im Werkzeug-Teil des Repositoriums, den das API-Abbild nicht mitbringt — er läuft am Rechner und schiebt sein Ergebnis über den Admin-Schreibweg hoch.',
          danach: 'die Bahn liegt über dem Streifen, sobald der Lauf hochgeschoben ist.',
          reihenfolge: 'erst ein Schnappschuss, dann derselbe Befehl mit --apply.',
        },
      },
      bahnBefehl: 'uv run python -m tools.eigenhand.pfad --hand {{hand}} --strip {{strip}} --fassung {{fassung}}',
    },
    stripImagesTitle: 'Geschriebene Streifen',
    stripImagesIntro:
      'Die eingelesenen Streifen, wie sie in der Datenbank liegen — admin-geschützt, nie öffentlich, nie im Repository. Der Wort-Ausschnitt wird aus dem Bogen-Layout berechnet und braucht keinen eigenen Speicher.',
    // Both empty answers name the STATE rather than a command: while no
    // accepted Fassung owes its image, the step does not exist at all — and a
    // pointer to a block this hand does not have would be worse than none.
    // Once it does exist, the card knows HOW MANY Fassungen are affected;
    // here it was all-or-nothing.
    stripImagesEmpty:
      'Noch keine Streifenbilder hochgeschoben. Sobald angenommene Fassungen ohne Bild vorliegen, steht der Befehl dazu im Bestand unter „Am Rechner weiter".',
    stripImagesError: 'Der Streifen konnte nicht geladen werden.',
    stripErrorAria: 'Fehlermeldung im Wortlaut',
    // The gallery's one opener, named: „Streifen-Bild s03/F01 · Übung groß
    // ansehen". A tile carries several controls, so „vergrößern" alone would
    // not say WHICH image.
    stripLupeOpen: '{{was}} groß ansehen',
    stripSwitchesTitle: 'Die drei Schalter',
    stripSwitchesAria: 'Die drei Schalter erklären',
    stripShow: 'Streifen zeigen',
    stripHide: 'einklappen',
    stripWhole: 'ganzer Streifen',
    stripMeta: '{{sheet}} · Zeile {{row}} · {{width}}×{{height}} px · {{dpi}} dpi',
    stripCount: '{{count}} Streifen gespeichert',
    stripSearch: 'Wort suchen',
    stripSearchHelp: 'Teilwort genügt, Groß/Klein egal',
    stripFilterItem: 'Belege für {{item}}',
    stripFilterClear: 'Filter aufheben',
    stripZoom: 'Vergrößerung',
    stripLupeClose: 'schließen',
    stripBelegeCount: 'Belege: {{count}} in {{strips}} Streifen',
    stripBelegeEmpty:
      'Kein gespeicherter Streifen trägt das. Die Zeichen-Tafel zählt auch Fassungen, deren Bild noch nicht hochgeschoben ist — steht eine davon aus, nennt der Bestand unter „Am Rechner weiter" den Befehl dazu.',
    stripBelegeIntro:
      'Gezeigt wird der Wort-Ausschnitt; das Zeichen sitzt darin. Die Zerlegung in einzelne Buchstaben ist Sache des Tintenfolgers (Phase 5), nicht der Kartei.',
    // The NAME of the roving gallery (a `toolbar`): one tab stop needs a
    // composite role, and the role needs a name (§9.5).
    stripGalleryLabel: 'Streifen-Belege',
    stripMore: 'weitere {{count}} laden',
    stripNoRulings: 'Lineatur ausblenden',
    stripNoRulingsHint:
      'Abgeleitete Ansicht: Blau-Kanal plus Cyan-Maske, berechnet beim Abruf. Wirkt nur bei farbig eingelesenen Streifen — ein Graustufen-Streifen bleibt, wie er ist. Gespeichert wird immer das Rohbild.',
    keyTooltipShow: ' · anklicken zeigt die Belege',
    // Der Streifen-Pfad: die nachgefolgte Federbahn je geschriebenem Wort.
    // Gerechnet wird sie außerhalb (Tintenfolger, `tools.eigenhand.pfad`) und
    // über den Admin-Schreibweg gespeichert — der Admin ZEIGT nur. Das Bild
    // bleibt unberührt, der Pfad liegt als Daten daneben.
    //
    // „Streifen-Pfad" is the glossary name of the FIELD
    // `eigenhand_strips.pfade`, never a UI word: on screen the line is „Bahn"
    // (author decision 2026-09-18, Q8 b). That is why the keys below keep
    // saying `pfad*` while their values say „Bahn" — the key points at the
    // field, the value speaks to the reader.
    pfadShow: 'Bahn zeigen',
    pfadShowHint:
      'Legt die gefolgte Bahn über den Streifen: Farbverlauf in Schreibreihenfolge vom ersten zum letzten Zug, Punkt am Ansatz, Pfeilspitze am Zugende, gepunktet die Absetzer. Bringt auch die Rohzahlen je Kasten mit — sie stecken in denselben Daten, also kostet das keinen zweiten Abruf. Wird je Fassung einzeln geladen und nur für sichtbare Bilder.',
    // Date and word count stay in the caption; the origin sits beside it as
    // the Herkunfts-Chip below.
    pfadPedigree: 'Bahn: {{datum}} · {{woerter}} Wort/Wörter',
    pfadNoDate: 'ohne Datum',
    // The Herkunfts-Chip (§5.0, Q8 b). Unlike a plate line, a strip row stores
    // its own `verfahren`, so the origin here may NAME the follower. An
    // unknown Verfahren is shown raw instead of relabelled: the column is free
    // text, and a silent swap would turn a foreign follower into a Tintenpfad.
    verfahrenTintenpfad: 'automatisch (Tintenpfad)',
    verfahrenAuthored: 'von Hand',
    // Eine Fassung trägt nicht zwangsläufig EINEN Lauf: `--box` mischt ein neu
    // gefolgtes Wort über die übrigen, und ein Zeilenlauf lässt jedem
    // übersprungenen Kasten seinen älteren Pfad. Dann gehört die Herkunft dem
    // einzelnen Pfad, nicht der Liste — und das wird gesagt, statt dem ersten
    // Wort die Herkunft aller zu leihen.
    pfadPedigreeMixed: 'Bahn: verschiedene Läufe · {{woerter}} Wort/Wörter',
    pfadMixedHint:
      'Die Bahnen dieser Fassung stammen aus mehreren Läufen — einzelne Wörter wurden später noch einmal gefolgt. Herkunft je Wort:',
    // Names of the InfoHints that replaced the hover-only hints of this panel
    // (V25): a Tooltip over a chip nothing can focus reaches neither keyboard
    // nor finger. One hint per Fassung row carries all three subjects, so the
    // title names the row rather than any single chip (§9.4).
    pfadPedigreeMixedTitle: 'Diese Fassung',
    pfadSeedAria: 'Herkunft, Saat und Maske dieser Fassung erklären',
    // The old sentence carried its command in the middle of running text, with
    // „…" instead of the strip and the Fassung and no copy button — exactly
    // the case the Übergabekarte exists for. It is a card at the Fassung now,
    // with the real ids; this key stays for the gallery tile, which has no
    // room for a card.
    pfadNoneShort: 'noch keine Bahn gespeichert',
    // Die drei leeren Antworten sind NICHT dasselbe: „noch niemand gefolgt"
    // (null), „gefolgt, nichts gefunden" (leere Liste) und „dieses Wort hat
    // keinen". Ein stummes Bild sähe in allen drei Fällen gleich aus.
    pfadEmpty:
      'Dieser Fassung wurde gefolgt, es kam aber keine Bahn zurück — der Folger hat kein Wort lesen können. Erneut folgen lassen oder den Streifen neu schreiben.',
    pfadNotInBox: 'Für dieses Wort ist keine Bahn gespeichert; andere Wörter der Fassung haben eine.',
    pfadNoBox:
      'Kein Kasten-Rechteck: dieser Bogen wurde gedruckt, bevor es die Schnitt-Geometrie gab — eine Bahn lässt sich im Ausschnitt nicht platzieren.',
    pfadError: 'Die Bahn konnte nicht geladen werden.',
    pfadSeed: 'Saat: Tafel-Duktus',
    pfadSeedHint:
      'Reihenfolge und Richtung kommen aus dem Duktus der Grundvorlage, nicht aus dieser Hand — der Folger nimmt die Saat nur als Vorschlag, die Bahn selbst liegt auf der Tinte. Auch die Lineatur der Saat ist die GEDRUCKTE, nicht die gemessene.',
    // Nur noch das Chip-Wort der Nachfahr-Zeile: der frei stehende Hinweis im
    // Streifen-Untertitel ist weg (die Ampel sagt dasselbe), und seinen Text
    // trägt jetzt `nachfahren.maskeHint` neben dem Befehl, der ihn behebt.
    pfadStale: 'Maske geändert',
    // The raw numbers per box: what the follower recorded while following,
    // with no colour and no verdict. The verdict is the Tintentreue traffic
    // light's (since #638), shown in the list under „Nachfahren" and on the
    // word crops of the FILTERED gallery (`CropTile`) — never these numbers.
    // The whole-strip tile (`StripTile`) shows this hint too and carries no
    // Ampel, so the hint says so. A single missing number reads as a dash, a
    // Bahn with no sensors at all as „nicht gemessen"; neither passes for a
    // zero.
    pfadRohzahlen: 'Zahl, kein Urteil',
    pfadRohzahlenHint:
      'Die gespeicherten Sensoren des Folgers, ungewichtet und unbewertet. „Tinte ohne Bahn“: der Anteil der Tinte, den die Bahn nie befährt. „Absetzer“: wie oft die Feder vom Papier genommen wurde. „Sprünge“: Wechsel auf einen anderen Strang. „Haken“: Umkehrpunkte auf demselben Strang. Ein Strich steht für eine Zahl, die dieser Lauf nicht ausgerechnet hat — nicht für null. Über dem ganzen Streifen trägt jede Zeile ihre Kastennummer, von 0 an gezählt: dieselbe, die „--box“ beim Nachfolgen nimmt. Im Wort-Ausschnitt und bei ausgewähltem Wort steht sie nicht dabei — dort gilt die eine Zeile dem Kasten, der gerade gezeigt wird. Ob die Bahn der Tinte folgt, sagt keine dieser Zahlen — das sagt die Tintentreue-Ampel: in der Liste unter „Nachfahren“ und auf jedem Wort-Ausschnitt der Galerie, sobald nach einem Wort oder Zeichen gefiltert ist; der ganze Streifen trägt keine. Ihre Schwellen sind bis zur Kalibrierung vorläufig.',
    pfadRohzahlenUnvisited: 'Tinte ohne Bahn {{prozent}} %',
    pfadRohzahlenUnvisitedNone: 'Tinte ohne Bahn –',
    pfadRohzahlenLifts: 'Absetzer {{zahl}}',
    pfadRohzahlenJumps: 'Sprünge {{zahl}}',
    pfadRohzahlenHairpins: 'Haken {{zahl}}',
    // Der Kasten-INDEX, nicht nur das Wort: acht Zeilen des Streifenplans
    // tragen dasselbe Wort zweimal („ja!“, „„wohl““, „Übung“ …), und zwei
    // gleiche Vorspänne ließen die Lesung keinem Kasten mehr zuordnen. Die
    // Nummer ist die von `--box`, also lässt sich eine schlechte Lesung genau
    // so neu nachfolgen, wie der Chip sie nennt.
    pfadRohzahlenBox: 'Kasten {{nr}} · {{wort}}:',
    pfadRohzahlenNone: 'nicht gemessen',
    pfadRohzahlenNoneHint:
      'Diese Bahn trägt keine Sensoren — von Hand nachgefahren, oder aus einem Lauf, bevor der Folger sie mitgeschrieben hat. Keine Zahl heißt nicht null.',
    // Der Streifen-Befund: ein VORSCHLAG, nie ein Urteil. Der Haken auf dem
    // Blatt bleibt die Entscheidung; hier steht nur, was auffällt und welche
    // Fassung eines Streifens die schwächste ist.
    befundRank: 'Rang {{rang}}/{{von}}',
    befundReplaced: 'ersetzt durch {{fassung}}',
    befundReplacedHint:
      'Eine spätere Fassung desselben Streifens ist sauberer. Der Bestand zählt beide weiter als Beleg — aus den Trainingsdaten nimmt eine Fassung nur „redo --retire“.',
    befundTooltip:
      'Vorschlag aus dem Streifen-Befund, kein Urteil: Güte {{guete}} · Feder {{feder}} der Hand · Knick max {{knick}}° ({{knicke}}) · Wackler {{wackler}}° · Kringel zu {{kringel}}',
    befundNone: 'kein Befund',
    befundNoneHint:
      'Diese Fassung wurde abgelegt, bevor der Streifen-Befund gemessen wurde. Fehlende Messung heißt nicht schlechte Fassung.',
    befundNoneAria: 'Warum kein Befund',
    befundSheetTitle: 'Befund dieser Fassung',
    befundSheetAria: 'Befund dieser Fassung anzeigen',
    befundSort: 'nach Befund sortieren',
    befundSortHint: 'Schwächste Fassung zuerst — was zuerst neu geschrieben werden sollte.',
    // Die Nachfahr-Liste: eine Zeile je geschriebenem WORTKASTEN — die
    // Arbeitsliste der Eigenhand (§6.4). Sie steht auf derselben Fläche wie
    // die Streifen-Galerie und wird mit demselben Umschalter gewählt, den die
    // drei Übersichten haben: `?reiter=streifen&ansicht=liste|galerie`. Die
    // Ampel, ihr Grund und der benennende Sensor kommen als FERTIGE deutsche
    // Sätze vom Server (`core/eigenhand/tintentreue.py`); hier steht nur, was
    // die Liste selbst sagt.
    nachfahren: {
      title: 'Nachfahren',
      caption:
        'Eine Zeile je geschriebenem Wortkasten: ob die Bahn der Tinte folgt, woher sie kommt und was als Nächstes dran ist. Ohne Bilder — die stehen in der Galerie daneben.',
      // Der Umschalter trägt die Wörter der Übersichten („Liste"/„Galerie");
      // was die beiden hier BEDEUTEN, sagt diese eine Zeile.
      viewHint:
        'Liste: eine Zeile je Wortkasten mit Ampel und nächstem Schritt. Galerie: die Streifenbilder mit Befund, Fleckenpinsel und Bahn-Ebene.',
      filters: {
        'maske-geaendert': 'Maske geändert',
        'tafel-fehlt': 'Tafel fehlt',
        uebersprungen: 'übersprungen',
        'von-hand': 'von Hand',
      },
      statusLabel: 'Nachfahren',
      statuses: {
        alle: 'Alle',
        noetig: 'Nötig',
        erledigt: 'Erledigt',
        'ohne-bahn': 'Ohne Bahn',
      },
      // „Erledigt" sind genau zwei Zustände, und der zweite ist der
      // überraschende: eine von Hand gezeichnete Bahn ist Wahrheit, kein
      // Mangel — sie ist nur noch nicht gemessen.
      statusHint:
        'Nötig: alles, was noch Nachfahr-Arbeit ist. Erledigt: die Bahn folgt der Tinte — oder du hast sie selbst gezogen. Ohne Bahn: der Kasten trägt gar keinen Eintrag oder einen, der sagt, warum keiner da ist.',
      rowExpand: '{{wort}} aufklappen',
      rowCollapse: '{{wort}} zuklappen',
      rowPlace: '{{strip}} · {{fassung}} · Kasten {{nr}}',
      // Der Zähler der ganzen Liste, nie der gefilterten Auswahl: eine Zahl,
      // die mit jedem Chip wandert, beantwortet bei jedem Klick eine andere
      // Frage (Autor-Entscheid E).
      // „(ungemessen)" ist kein Beiwerk: der Chip „von Hand" oben zählt die
      // HERKUNFT, dieser Zähler die von Hand gezogenen Bahnen, die noch nichts
      // gemessen hat (V21). Sobald das Werkzeug über eine davon gelaufen ist,
      // stehen die beiden Zahlen auseinander — mit dem Zusatz sagen sie warum.
      tally: '{{kaesten}} Kästen · {{folgt}} folgen · {{vonHand}} von Hand (ungemessen) · {{offen}} offen',
      // Ohne eine einzige Messung ist „Schwere zuerst" stillschweigend die
      // Streifenfolge. Das wird gesagt, statt eine Rangfolge zu behaupten.
      notRanked: 'Noch ist kein Kasten gemessen — die Reihenfolge ist die des Streifenplans.',
      notRankedHint:
        'Die Ampel liest die Sensoren, die der Folger beim Nachfolgen mitschreibt. Fassungen aus einem Lauf vor dem Formatwechsel tragen zwei davon nicht und bleiben grau, bis sie einmal neu gefolgt werden.',
      empty: 'Für diese Hand ist noch kein Streifen abgelegt.',
      loadError: 'Die Kastenliste konnte nicht geladen werden.',
      // Nach jedem gespeicherten Kasten wird die Liste neu gelesen. Scheitert
      // das, bleibt die Liste stehen — ein offener Editor darf darüber nicht
      // verschwinden — und sagt nur, dass der gezeigte Stand älter ist.
      refreshError: 'Der Stand der Kästen konnte nicht neu gelesen werden — die Liste zeigt den vorherigen.',
      // Der Zeichen-Filter der Galerie hat in der Liste keinen Gegenstand: der
      // Kasten-Read trägt das Wort, aber nicht die Items, die es belegt.
      itemFilterNote:
        'Der Zeichen-Filter gilt nur in der Galerie — eine Kasten-Zeile weiß nicht, welche Zeichen ihr Wort belegt.',
      itemFilterAction: 'zur Galerie',
      // Die Ampel selbst. Stufe und Grund kommen im Klartext vom Server; der
      // Chip färbt nur ein. „vorläufig" steht dabei, solange die Schwellen die
      // geliehenen sind — eine Kalibrierung, die es nicht gab, darf keine
      // Oberfläche behaupten (Q10 b).
      ampelAria: 'Ampel, Sensoren und Schwellen dieses Kastens',
      ampelTitle: 'Tintentreue dieses Kastens',
      ampelVorlaeufig: 'Schwellen vorläufig (Stand {{stand}})',
      ampelVorlaeufigHint:
        'Die acht Schwellen sind von der Platte und aus dem dev-19-Satz geliehen, nicht an dieser Hand gemessen. Sie werden EINMAL je Hand in einer blinden Runde ersetzt; bis dahin ist die Stufe ein Hinweis, kein Maß.',
      ampelFormat: 'Format {{format}}',
      sensorHeader: 'Sensoren dieses Kastens',
      sensorValue: '{{name}}: {{wert}}',
      sensorNone: '{{name}}: –',
      sensorBounds: 'grün ab {{gruen}} · gelb ab {{gelb}}',
      sensorSoll: 'Soll {{soll}}',
      absetzerSoll: 'Absetzer-Soll {{zahl}}',
      absetzerSollHint:
        'So viele verbundene Körperläufe schreibt die Schrift dieses Wort — ohne Markenzüge (i-Punkt, Umlaut), die zählt diese Zahl nicht mit. Sie ist das Soll, gegen das der Absetzer-Sensor misst.',
      herkunft: 'Bahn: {{verfahren}} · {{datum}}',
      // Ein Skip-Eintrag trägt dasselbe `verfahren` wie jeder andere Eintrag —
      // nur eben keine Bahn. „Bahn: Tintenpfad" wäre dort das Gegenteil dessen,
      // was Ampel und Status sagen; dies nennt dieselben zwei Angaben als das,
      // was sie waren: ein Versuch.
      herkunftVersuch: 'Keine Bahn · Versuch: {{verfahren}} · {{datum}}',
      herkunftNone: 'kein Eintrag',
      skipDetail: 'Grund laut Folger: {{detail}}',
      // Die drei Umleitungen aus §6.4. Jede sagt, WO die Arbeit liegt — die
      // Liste löst nichts aus, sie verlinkt (Arbeitslisten-Regel).
      tafelFehlt: 'Tafel fehlt: {{keys}}',
      tafelFehltHint:
        'Dieses Wort enthält Zeichen, die auf der Tafel noch nicht eingerichtet sind — der Folger hat deshalb gar nicht erst angefangen. Das ist Ground Truth und gehört an die Tafel, nicht in den Korb.',
      tafelFehltAction: '{{key}} einrichten',
      // Die dritte Umleitung aus §6.4, und die einzige, die nirgendwohin
      // führt: „nie machbar". Der Kasten hat kein Rechteck, der Folger bricht
      // genau deshalb ab — ein Befehl darunter würde denselben Übersprung noch
      // einmal erzeugen und so tun, als wäre das Arbeit.
      bogenOhneGeometrie:
        'Dieser Kasten stammt von einem Bogen, der vor der Schnitt-Geometrie gedruckt wurde — er lässt sich nicht nachfahren. Erst ein neu gedruckter und geschriebener Bogen trägt dieses Wort wieder.',
      maskeAction: 'erst neu folgen lassen',
      maskeHint:
        'Diese Bahn wurde unter einer anderen Fleckenmaske gefolgt als der Streifen jetzt trägt — sie lief also auf anderer Tinte, als hier zu sehen ist. Der Befehl unten folgt ihr mit der heutigen Maske noch einmal.',
      neuFolgen: 'neu folgen',
      // Wie die Übergabekarte reicht auch diese Zeile den TROCKENLAUF weiter:
      // `--apply` überschreibt gespeicherte Geometrie und gehört hinter einen
      // Schnappschuss, nicht hinter einen Kopierknopf.
      neuFolgenHint:
        'Der Trockenlauf für genau diesen Kasten — „--box" zählt von 0, wie die Kastennummer oben. Gespeichert wird erst mit „--apply", und davor gehört ein Schnappschuss.',
      befehl:
        'uv run python -m tools.eigenhand.pfad --hand {{hand}} --strip {{strip}} --fassung {{fassung}} --box {{box}}',
      // Auf einem von Hand gezogenen Kasten wird NICHT zum Neu-Folgen
      // eingeladen: das ist die eigene Linie des Autors, und der Folger darf
      // sie nicht ersetzen. Wer es doch will, tut es am Terminal mit
      // `--replace-authored` — und sieht dort die Warnung.
      authoredKeinNeuFolgen:
        'Von Hand gezogen — diese Bahn ist deine eigene Linie. Der Folger ersetzt sie nicht; das ginge nur am Terminal mit „--replace-authored".',
      korbMark: 'Kasten markieren',
      trace: 'Nachfahren',
    },
    // Die Fläche, auf der der Autor einen Kasten mit dem Stift nachfährt —
    // schlank neben dem Platten-Editor und mit ihm auf einer Zeichenfläche
    // (Autor-Entscheid G, 2026-09-20). Was hier anders ist als auf der Platte:
    // die Unterlage ist ein Blob (die Streifen sind admin-gegatet und
    // `private, no-store`), der Rahmen kommt aus der gespeicherten Bahn minus
    // dem Kastenrechteck, und „Speichern & weiter" geht zum nächsten Kasten
    // der Liste, ohne die Fläche zu verlassen.
    editor: {
      title: 'Kasten nachfahren',
      place: '{{strip}} · {{fassung}} · Kasten {{nr}}',
      queue: '{{nr}} von {{total}}',
      intro:
        'Den Schreibweg mit dem Stift über der eigenen Schrift nachfahren. Jedes Absetzen beginnt einen neuen Zug; die blaue Grundlinie und die gestrichelte Mittellinie zeigen den Rahmen, in dem die Bahn gespeichert wird. Gespeichert wird sie als „von Hand" — deine eigene Linie, Grundwahrheit fürs Training, die kein Folger-Lauf ersetzt.',
      introAria: 'Was diese Fläche speichert',
      close: 'Schließen',
      save: 'Speichern',
      saveNext: 'Speichern & weiter',
      saveLast: 'Letzter Kasten der Liste — „Speichern" schließt die Runde ab.',
      strokeCount: '{{zuege}} Züge',
      // Prüfstein 7: ohne diese Zahl liefert Nachfahren still eine neue
      // Strichreihenfolge per Bild. Das Soll zählt NUR Körperläufe (Korrektur
      // T5) — der i-Punkt und der Umlaut stehen nicht darin, ein Zug mehr ist
      // also oft richtig und zwei sind ein anderer Duktus.
      absetzerSoll: 'Soll (Körper) {{soll}}',
      // Kein eigener Satz für den Gleichstand: der Chip zeigt beide Zahlen
      // nebeneinander und wechselt Farbe UND Variante. Ein „stimmt überein"
      // im `title` wäre nur auf Hover zu erreichen — V25 verbietet das.
      absetzerMismatch:
        'Diese Bahn hat {{zuege}} Züge, die Schrift schreibt das Wort in {{soll}} verbundenen Körperläufen. Markenzüge — i-Punkt, Umlaut — zählt das Soll nicht mit: ein Zug mehr kann also richtig sein, zwei sind eine andere Strichreihenfolge.',
      modeDraw: 'Schreiben',
      modeAdjust: 'Anpassen',
      modeSpans: 'Grenzen',
      modePan: 'Verschieben',
      modeGroup: 'Modus',
      zoom: 'Größe',
      nudgeRadius: 'Radius',
      undo: 'Letzten Zug zurück',
      clear: 'Alle Züge löschen',
      reset: 'Auf gespeicherten Stand zurück',
      showStored: 'Gespeicherte Bahn zeigen',
      drawHint: 'Finger sind deaktiviert — zum Verschieben den Schalter nutzen.',
      adjustHint:
        'Die Bahn mit dem Stift an einer Stelle ziehen: Punkte im Kreis folgen, außen läuft die Linie weich zurück. Züge werden nie geteilt oder zusammengelegt — nur verschoben.',
      // Q15 (b) mit dem Autor-Zusatz: die Grenzen werden zugeordnet, gezeigt
      // UND sind von Hand korrigierbar — und die Korrektur ist Trainingsstoff.
      // Das steht hier, weil genau das der Grund ist, warum danach gefragt
      // wird.
      spansHint:
        'Die Marke zwischen zwei Buchstaben mit dem Stift verschieben: sie sitzt auf dem letzten Punkt des linken Buchstabens. Eine so korrigierte Grenze ist Trainingsstoff für den Grenzen-Zuordner — sie wird als „von Hand" gespeichert und von keinem späteren Lauf überschrieben. Grenzen, die du nicht anfasst, bleiben die des Folgers.',
      // The Zuordner exists since #650 and runs at the terminal, over a
      // stored Bahn — so the sentence names the step, not a future.
      spansNone:
        'Für diese Bahn sind noch keine Buchstabengrenzen zugeordnet. Das tut der Zuordner am Terminal: tools.eigenhand.pfad --spans über diesen Streifen, mit --apply gespeichert. Danach lassen sich die Grenzen hier verschieben.',
      spansCount: '{{zahl}} Grenzen',
      spansAuthored: '{{zahl}} von Hand',
      spansDropped:
        'Die Züge sind neu gezeichnet: die gespeicherten Buchstabengrenzen zeigen auf Punkte, die es nicht mehr gibt, und werden beim Speichern nicht mitgeschickt. Der Zuordner vergibt sie neu.',
      // Der Rahmen kommt aus der gespeicherten Bahn — außer es gibt keine.
      saat: 'In diesem Kasten steht noch keine Bahn: gezeichnet wird auf der GEDRUCKTEN Lineatur des Bogens (Saat), nicht auf einer Messung. Die gespeicherte Bahn bringt danach ihren eigenen Rahmen mit.',
      loading: 'Die Bahnen dieser Fassung werden geladen …',
      loadError: 'Die Bahnen dieser Fassung konnten nicht geladen werden.',
      imageLoading: 'Der Ausschnitt dieses Kastens wird geladen …',
      // Ohne das Bild wird nicht gezeichnet: eine Bahn über einer leeren oder
      // fremden Unterlage sieht auf dem Schirm aus wie jede andere.
      imageError:
        'Der Ausschnitt dieses Kastens konnte nicht geladen werden. Solange er fehlt, wird hier nicht gezeichnet — sonst entstünde eine Bahn über einem leeren oder fremden Bild.',
      saveError: 'Die Bahn konnte nicht gespeichert werden.',
      // 412: zwischen Lesen und Schreiben hat jemand — oder ein Folger-Lauf —
      // dieselbe Fassung ersetzt. Die Zeichnung bleibt stehen; neu eingelesen
      // wird nur der Stand, gegen den gespeichert wird.
      conflict:
        'Auf diese Fassung wurde geschrieben, seit sie hier gelesen wurde — gespeichert wurde nichts. Deine Zeichnung steht noch. „Stand neu einlesen" holt den aktuellen Stand; danach ersetzt Speichern, was inzwischen in diesem Kasten steht.',
      conflictAction: 'Stand neu einlesen',
      noToken:
        'Dieser Fassung fehlt die Marke des gelesenen Standes — ohne sie wird nicht blind geschrieben. „Stand neu einlesen" holt sie.',
      noGeometry:
        'Dieser Kasten stammt von einem Bogen, der vor der Schnitt-Geometrie gedruckt wurde — er hat kein Rechteck, in dem eine Bahn liegen könnte. Nachfahren geht hier nicht.',
      empty: 'Kein Kasten zum Nachfahren ausgewählt.',
      // Eine von Hand gezeichnete Bahn gibt es nirgendwo sonst: kein
      // Folger-Lauf stellt sie wieder her. Darum fragt die Fläche, bevor sie
      // sie wegwirft.
      discardTitle: 'Gezeichnete Bahn verwerfen?',
      discardBody:
        'In diesem Kasten steht eine ungespeicherte Zeichnung. Beim Schließen ist sie weg — von Hand gezeichnete Bahnen lassen sich nicht neu berechnen.',
      discardStay: 'Weiterzeichnen',
      discardLeave: 'Verwerfen und schließen',
    },
    // Die Fleckenmaske: die Toner-Punkte des Druckers, entfernt als DATEN.
    // Das gespeicherte Bild bleibt unberührt — die Kreise werden beim Abruf
    // mit Papierfarbe gefüllt, „roh" zeigt jederzeit die echten Bytes.
    fleckenTitle: 'Flecken radieren',
    fleckenStart: 'Flecken radieren',
    fleckenStartHint:
      'Runder Pinsel: Klick setzt einen Kreis, Klick auf einen vorhandenen nimmt ihn weg. Gespeichert wird die Kreisliste, nie ein verändertes Bild — der Streifen bleibt Byte für Byte, wie er eingelesen wurde.',
    fleckenChip: '{{count}} Fleck(en) maskiert',
    fleckenChipTitle: 'Maskierte Flecken',
    fleckenChipAria: 'Maskierte Flecken erklären',
    fleckenChipHint:
      'So viele Kreise trägt dieser Streifen. Beim Abruf wird dort Papierfarbe eingefüllt; das gespeicherte Bild bleibt unverändert.',
    fleckenBrush: 'Pinsel',
    fleckenBrushSize: '{{mm}} mm',
    fleckenCount: '{{count}} Kreise',
    fleckenUndo: 'Rückgängig',
    fleckenSave: 'Speichern',
    fleckenSaved: 'Maske gespeichert.',
    fleckenSaveError: 'Die Fleckenmaske konnte nicht gespeichert werden.',
    fleckenClose: 'fertig',
    fleckenRaw: 'roh',
    fleckenRawAria: 'Was „roh" zeigt',
    fleckenRawHint:
      'Zeigt die eingelesenen Bytes mit allen Flecken — zum Nachsehen, was der Drucker wirklich hinterlassen hat.',
    fleckenHint:
      'Grün: automatisch erkannt. Braun: von Hand gesetzt. Nah an der Schrift wird nie automatisch radiert — i-Punkte, Kommas und eigene Kleckse bleiben stehen und sind hier von Hand zu treffen.',
  },
} as const;
