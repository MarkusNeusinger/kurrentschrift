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
    unlockSplit: 'Entsperren (nur diese Position — aufgetrennt)',
    lockSplit: 'Als fertig sperren (nur diese Position — aufgetrennt)',
    unlockUnified: 'Entsperren (alle Positionen, wieder bearbeitbar)',
    lockUnified: 'Als fertig sperren (alle Positionen, vor Änderungen schützen)',
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
    scopeAllPositions: ' (alle Positionen)',
    locked: '🔒 „{{name}}“ gesperrt{{scope}}.',
    unlocked: '🔓 „{{name}}“ entsperrt{{scope}}.',
    deleteConfirm: 'Bbox für „{{glyph}}“ löschen?',
    deleteConfirmScope: ' Alle Positionen dieses Buchstabens werden entfernt, damit du neu anfangen kannst.',
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
    overlays: 'Overlays',
    all: 'alle',
    none: 'keine',
    // Letter tooltip fragments (composed with the glyph + note).
    statusCanonical: ' · Canonical vorhanden',
    statusBbox: ' · Bbox gesetzt',
    statusEmpty: ' · leer',
    statusLocked: ' · gesperrt (fertig)',
    statusSplit: ' · aufgetrennt (pro Position)',
    splitCaption: 'aufgetrennt · pro Position',
    unifiedCaption: 'eine Form für alle Positionen',
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
    // Followed by the position label when a letter is authored per position.
    positionPrefix: 'Position: ',
    noCanonical: 'kein Canonical',
    loadError: 'Diagnose konnte nicht geladen werden.',
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
    // Non-split letters share one form — applying fans out over all positions.
    applyAll: 'Neu ableiten & speichern (alle {{count}} Positionen)',
    applyHint:
      'Überschreibt die gespeicherte Vorlage mit der Neuableitung aus dem Roh-Weg — bewusste Aktion, wirkt auch bei gesperrten Glyphen.',
    applyHintAll:
      'Der Buchstabe teilt eine Form über alle Positionen — die Neuableitung überschreibt alle {{count}} zusammen (bewusste Aktion, wirkt auch bei gesperrten Glyphen).',
    applied: 'Vorlage neu abgeleitet und gespeichert.',
  },
  // Bulk re-derive of all authored glyphs (RederiveAllDialog).
  rederive: {
    button: 'Alle neu ableiten',
    buttonTooltip:
      'Alle erstellten Glyphen mit aktuellem Code und aktueller Ankerdichte neu berechnen und überschreiben — mit Vorher/Nachher-Tabelle pro Buchstabe',
    title: 'Alle Glyphen neu ableiten',
    intro:
      'Berechnet jede erstellte Glyphe aus ihrem Roh-Weg neu (aktueller Code, aktuelle Ankerdichte) und überschreibt die gespeicherte Vorlage — mit Score vorher/nachher pro Buchstabe. Nicht aufgetrennte Buchstaben werden über alle Positionen zusammen aktualisiert. Rote Δ-Werte heißen: verschlechtert — in der Diagnose prüfen.',
    start: 'Alle neu berechnen & überschreiben',
    cancel: 'Abbrechen',
    close: 'Schließen',
    colLetter: 'Buchstabe',
    colPositions: 'Pos.',
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
