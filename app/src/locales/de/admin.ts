// German strings for the admin surface (chart editor, sidebar, diagnostics,
// admin layout). Pre-i18n message catalog — key tree mirrors a future i18next
// `admin` namespace. {{…}} placeholders are filled via fmt().

export const admin = {
  layout: {
    openMenu: 'Menü öffnen',
  },
  // The shell: the header over all three views, the Vorlage picker the admin is
  // entered through, and the Auftragskorb drawer.
  shell: {
    areaLetters: 'Buchstaben',
    areaJoins: 'Übergänge',
    areaWords: 'Wörter',
    areaNavAria: 'Bereiche der Werkbank',
    switchSource: 'Vorlage wechseln',
    noSource: 'keine Vorlage',
    openKorb: 'Auftragskorb öffnen',
    closeKorb: 'Auftragskorb schließen',
    startEyebrow: 'Werkbank',
    startTitle: 'Welche Vorlage?',
    startIntro:
      'Alles in der Werkbank gehört zu genau einer Vorlage und ihrer Hand — Buchstaben, Übergänge und Wörter werden immer an einer Schrift gearbeitet. Darum steht die Wahl am Anfang und nicht in einem Menü.',
    startRatio: 'Verhältnis {{ratio}}',
    startSlant: 'Schräglage {{deg}}°',
    startNoSources: 'Keine Tafel-Vorlagen gefunden — läuft die API und ist die Datenbank eingerichtet?',
    startHint: 'Die gewählte Vorlage bleibt in diesem Browser gespeichert; die öffentlichen Seiten bleiben unberührt.',
    // The shared states of every occurrence-backed block.
    evidenceLoading: 'wird geladen …',
    evidenceError: 'Die gespeicherten Vorkommen konnten nicht geladen werden — neu laden oder die API prüfen.',
  },
  // The Buchstaben view: one letter's whole life, from the chart cell to how it
  // is finally written, plus the ways over to its joins and its words.
  letters: {
    overviewTitle: 'Buchstaben',
    overviewIntro:
      'Jeder erstellte Buchstabe viermal nebeneinander: der Tafel-Ausschnitt, die daraus geschriebene Tafel-Form, die Laufform für fließende Wörter und die Statistik dahinter — der Median dieser Hand über ihren gemessenen Vorkommen, die Vorkommen selbst dünn dahinter. Daneben die Kennzahlen: wie viele Vorkommen, wie gut die Einpassung sitzt, wie die Form bewertet ist. „Öffnen“ führt in den einzelnen Buchstaben mit allen Werkzeugen.',
    pickLetter: 'Buchstabe wählen',
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
    },
  },
  // The Übergänge view: the generated join first, the measurement beside it,
  // the override last — the order the stage doctrine prescribes.
  joins: {
    overviewTitle: 'Übergänge',
    overviewIntro:
      'Der Übergang ist das, was die Engine zwischen zwei Buchstaben erzeugt. Hier steht jede Zweierkombination — auch solche, die keine Platte je geschrieben hat: tippe sie einfach ein. Ein Klick auf eine Zelle öffnet die Verbindung mit Messung, Statistik und (als letztes Mittel) dem Paar-Editor.',
    pickLeft: 'links',
    pickRight: 'rechts',
    freeTextLabel: 'Kombination eintippen',
    freeTextHint: 'Zwei Zeichen, z. B. „ab“ — auch ohne Vorkommen.',
    freeTextSubmit: 'Ansehen',
    freeTextInvalid: 'Das ergibt keine Verbindung — zwei Buchstaben eingeben (ch, ck, tz, ſt, qu, ß sind je EINE Glyphe).',
    toOverview: 'Alle Kombinationen',
    generated: 'generiert',
    occurrenceCount: '{{count}} Vorkommen',
    writtenTitle: 'Wie es geschrieben wird',
    writtenCaption:
      'Beide Buchstaben mit dem generierten Übergang, serverseitig komponiert — genau so, wie die Engine sie in einem Wort schreibt.',
    writtenCaptionOverride:
      'Für dieses Paar ist ein freigegebener Override gespeichert: gezeichnet statt generiert, verbatim gerendert.',
    overrideLastResort:
      'Erst die Klassenregel schärfen (hebt alle Paare derselben Art), zeichnen nur als letztes Mittel — jeder Override friert eine Stelle ein.',
    toLetter: 'Buchstabe {{key}}',
    statsTitle: 'Gemessen vs. komponiert',
    statsCaption:
      'Die gemessene Median-Verbindung über den Vorkommen, aus denen sie verdichtet wurde — die Prüfzahl dafür, wie weit der Generator von dieser Hand entfernt liegt.',
    // The traced drill plate of exactly this pair (the Verbindungs-Platten
    // cell), shown as the same evidence card the Wörter view uses.
    drillTitle: 'Platten-Beleg (nachgefahren)',
    drillCaption:
      'Die Verbindungs-Platte genau dieser Kombination — grün die Nachfahrung, rot darüber die Engine-Tinte, beide in der vermessenen Registrierung der Spur; rechts schreibt das System dieselbe Verbindung im gleichen Maßstab.',
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
      'Im Wort wird sichtbar, was einzeln noch stimmte. Jede Wortprobe der Vorlage steht neben demselben Wort „wie geschrieben“; „Öffnen“ führt in das einzelne Wort mit Spur, Vorkommen und Bewertung. Oben lässt sich jeder beliebige Text eintippen — auch einer, den keine Platte enthält.',
    freeTextLabel: 'Wort oder Satz',
    freeTextHint: 'Beliebiger Text — er muss in keiner Wortprobe vorkommen.',
    freeTextSubmit: 'Schreiben',
    filterLabel: 'Proben filtern',
    toOverview: 'Alle Wortproben',
    traceCount: '{{count}} Belege',
    traceCountOne: '{{count}} Beleg',
    writtenTitle: 'Wie es geschrieben wird',
    writtenCaption:
      'Serverseitig komponiert: Buchstaben der Bibliothek, dazwischen die erzeugten Übergänge — dieselbe Ausgabe, die die öffentlichen Seiten schreiben.',
    partsTitle: 'Woraus es besteht',
    partsCaption:
      'Die Buchstaben und die Übergänge dieses Textes. Ein Klick führt in die jeweilige Ansicht — der Weg von „hier stimmt etwas nicht“ zur Ursache.',
    noJoins: 'Keine verbundenen Übergänge in diesem Text.',
    noSpecimen:
      'Zu diesem Text gibt es keine nachgefahrene Wortprobe dieser Hand — beurteilt wird dann allein das Schriftbild oben. Bemängeln geht trotzdem: ⚑ oben.',
    scoreButton: 'Bewerten',
    scoreHint: 'Der eingefrorene Wortbench-Maßstab auf genau dieser Komposition (niedriger ist besser).',
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
    belegeOverview: 'Belege (nachgefahrene Wörter)',
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
      'Kräftig: der Median je Anker über den Vorkommen dieser Hand · dünn: die einzelnen Vorkommen · Kreise: MAD-Streuung · gestrichelt rot: die aktuell geschriebene Laufform · Linien: Grund- und Mittellinie.',
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
    overlayHeading: 'Überlagert (Original + Geschrieben in Rot)',
    // The two grids double as the overviews of the Buchstaben/Wörter views, so
    // every card carries the way into its own detail.
    openLetter: 'Öffnen',
    openWord: 'Öffnen',
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
    // Specimen scores (redesign R1b Stufe 2): the frozen wordbench ruler per
    // card, worst first = the work list.
    scoreButton: 'Scores berechnen & sortieren',
    scoreBusy: 'Berechne',
    scoreFailed: 'nicht bewertbar',
    scoreError: 'Einzelne Scores konnten nicht berechnet werden.',
    scoreWorstSegments: 'Größte Abweichungen:',
    openPairEditor: 'Im Paar-Editor öffnen',
    // „Measured vs. composed" on the pair cards (Handmodell H2): what the
    // occurrence and the aggregate layers know about exactly this join. The
    // detailed numbers in the tooltip deliberately reuse the wording of the
    // Werkbank lens (the same statistic must not be named twice differently).
    measuredLabel: 'Gemessen',
    measuredGenChamfer: 'Generator-Abstand ⌀ {{value}}',
    // The four reasons a card can carry no measured median, short enough for
    // the chip row — the tooltip spells each of them out in the Werkbank's
    // words. „keine Messung" is reserved for the case it describes: the hand's
    // aggregates are loaded, this join is simply not among them.
    measuredNone: 'keine Messung',
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
    asFirst: '„{{glyph}}“ als erster Buchstabe',
    asSecond: '„{{glyph}}“ als zweiter Buchstabe',
    empty: 'Noch keine erstellten Glyphen — erst im Wizard einen Weg zeichnen.',
    badgeApproved: 'Override',
    badgeDraft: 'Entwurf',
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
  // The Belege strings (now the Wörter view's specimen cards): a stored
  // word-occurrence trace over its specimen crop — the error-finding surface
  // over the occurrence layer (handmodell H1/H2) and the entry point into the
  // word editor (Werkbank W3: manual re-tracing → authored rows).
  belege: {
    title: 'Belege — nachgefahrene Wörter',
    intro:
      'Jedes gespeicherte Wort-Vorkommen der aktiven Vorlage: der Platten-Ausschnitt, darüber der nachgefahrene Schreibpfad. Sortiert nach Fehlern (nicht gefittete Buchstaben zuerst, dann höchste Abweichung) — die Arbeitsliste fürs manuelle Nachfahren.',
    filterLabel: 'Wort suchen',
    empty: 'Noch keine gespeicherten Vorkommen — erst die Ernte laufen lassen (tools/laufform/harvest.py --apply).',
    loadError: 'Belege konnten nicht geladen werden.',
    cropAlt: 'Platten-Ausschnitt',
    // {{fitted}}/{{total}} letter slots the automatic fit handled cleanly.
    fittedChip: '{{fitted}}/{{total}} gefittet',
    // Followed by the space-joined letters the fit could not place.
    unfittedPrefix: 'fehlt: ',
    rmseChip: 'RMSE ⌀ {{value}} px',
    provenanceTraced: 'automatisch nachgefahren',
    provenanceAuthored: 'von Hand nachgefahren',
    // A stored trace whose specimen crop is missing from the sidecar.
    noSample: 'Kein Platten-Ausschnitt zur specimen_id {{id}} — Sidecar prüfen.',
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
    editorModePan: 'Verschieben',
    // Accessible name of the mode toggle group.
    editorModeGroup: 'Modus',
    editorZoomHint: 'Finger sind deaktiviert — zum Verschieben den Schalter nutzen.',
    editorReset: 'Auf gespeicherten Stand zurück',
    editorShowStored: 'Gespeicherte Spur zeigen',
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
    provenanceTraced: 'automatisch nachgefahren',
    provenanceAuthored: 'von Hand nachgefahren',
    noSample: 'Kein Platten-Ausschnitt zur specimen_id {{id}} — Sidecar prüfen.',
    // The two faces of a word card: left what was MEASURED, right what the
    // engine writes from it — same scale, same Grundlinie, so „trifft der Fit?"
    // und „was macht das System daraus?" nebeneinander lesbar sind.
    faceSpecimenBase: 'Vorlage',
    faceLayerTrace: 'Nachfahrung (grün)',
    faceLayerEngine: 'Engine (rot)',
    faceWritten: 'Vom System geschrieben',
    faceWrittenPending: 'wird geschrieben …',
    // The per-layer switches above the cards.
    layersLabel: 'Ebenen über der Vorlage',
    layerTrace: 'Nachfahrung',
    layerEngine: 'Engine',
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
    // The dashed chain: what the engine writes TODAY, against the median that
    // would replace it — the „see the difference" view before the overwrite.
    statsLetterSketchLegendLaufform: 'gestrichelt rot: die aktuell geschriebene Laufform',
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
      word_trace: 'Wort-Spur',
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
    buttonTooltip:
      'Alle erstellten Glyphen mit aktuellem Code und aktueller Ankerdichte neu berechnen und überschreiben — mit Vorher/Nachher-Tabelle pro Buchstabe',
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
} as const;
