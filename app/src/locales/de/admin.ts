// German strings for the admin surface (chart editor, sidebar, diagnostics,
// admin layout). Pre-i18n message catalog — key tree mirrors a future i18next
// `admin` namespace. {{…}} placeholders are filled via fmt().

export const admin = {
  layout: {
    openMenu: 'Menü öffnen',
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
    overlayToggle: 'Überlagern',
    overlayHeading: 'Überlagert (Original + Geschrieben in Rot)',
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
    // Specimen scores (redesign R1b Stufe 2): the frozen wordbench ruler per
    // card, worst first = the work list.
    scoreButton: 'Scores berechnen & sortieren',
    scoreBusy: 'Berechne',
    scoreFailed: 'nicht bewertbar',
    scoreError: 'Einzelne Scores konnten nicht berechnet werden.',
    scoreWorstSegments: 'Größte Abweichungen:',
    openPairEditor: 'Im Paar-Editor öffnen',
  },
  // The pair matrix (/admin/paare): every two-letter combination of one chosen
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
  // The Belege page (/admin/belege): every stored word-occurrence trace over
  // its specimen crop, worst first — the error-finding surface over the
  // occurrence layer (handmodell H1/H2) and the entry point into the word
  // editor (Werkbank W3: manual re-tracing → authored rows).
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
    // Word editor (Werkbank W3) — manual re-tracing over dem Platten-Ausschnitt.
    editOpen: 'Nachfahren',
    editorTitle: 'nachfahren · {{specimen}}',
    editorIntro:
      'Den Schreibweg mit dem Stift direkt über dem Platten-Ausschnitt nachfahren. Jedes Absetzen beginnt einen neuen Zug — die blaue Grundlinie und die gestrichelte Mittellinie zeigen den Rahmen, in dem der Weg gespeichert wird. Gespeichert wird er als „von Hand nachgefahren" (authored): Grundwahrheit für Statistik und Training, keine Rendering-Korrektur — und von keiner Neu-Ernte je überschrieben.',
    editorUndo: 'Letzten Zug zurück',
    editorClear: 'Alle Züge löschen',
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
  },
  // The Werkbank (/admin/werkbank, proposal optimierungs-werkbank.md §2): ONE
  // optimisation surface — the word spine on the left (where errors become
  // visible), a context lens on the right that switches between the clicked
  // letter and the clicked join, and the Auftragskorb (work_items) that
  // replaces feedback-by-screenshot. The ⚑ dialog asks the §4 pre-sort
  // question for letters: solo-wrong belongs in the wizard (the author's own
  // ductus is the truth), word-only-wrong is an algorithm complaint.
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
    fitDoubtful: 'Fit unsicher',
    // The Auftragskorb.
    korbTitle: 'Auftragskorb',
    korbOpenCount: '{{count}} offen',
    korbEmpty: 'Noch keine Aufträge — ⚑ markiert ein Element und legt es hier ab.',
    korbShowDone: 'erledigte anzeigen',
    korbDelete: 'Auftrag löschen',
    korbLoadError: 'Aufträge konnten nicht geladen werden (Admin-Zugang nötig).',
    korbDeleteError: 'Löschen fehlgeschlagen — der Auftrag liegt weiter im Korb.',
    kindLetter: 'Buchstabe',
    kindPair: 'Übergang',
    kindWord: 'Wort',
    // The filing dialog.
    dialogTitle: 'Auftrag einreichen',
    dialogTarget: 'Ziel',
    dialogSeenIn: 'gesehen in',
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
