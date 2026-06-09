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
    deleteConfirmCanonical: ' Das gespeicherte Canonical wird mit entfernt.',
    deleted: '{{glyph}}: gelöscht.',
    // Followed by the error in the snackbar message.
    deleteFailed: 'Löschen fehlgeschlagen:',
  },
  sidebar: {
    groupLower: 'Kleinbuchstaben',
    groupUpper: 'Großbuchstaben',
    groupComb: 'Kombinationen',
    toHome: 'Zur Startseite',
    chartOverview: 'Chart-Übersicht',
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
    drawBboxFirst: 'Erst eine Bbox ziehen',
    lockedUnlockAbove: 'Gesperrt — oben entsperren',
    setup: 'Einrichten',
    diagnose: 'Diagnose',
    noBboxHint: 'Noch keine Bbox — im Modus „Bbox“ ein Rechteck auf der Vorlage ziehen.',
    lockedHint: '🔒 Gesperrt (fertig) — oben in der Leiste entsperren, um zu bearbeiten.',
  },
  diagnostics: {
    // Followed by the glyph label in the dialog title.
    title: 'Diagnose ·',
    close: 'Diagnose schließen',
    tabDiagnostic: 'Skelett & Canonical',
    tabFit: 'Fit (M4)',
    noCanonical: 'Noch kein Canonical — erst im Einrichten-Wizard einen Weg zeichnen und speichern.',
    diagnosticIntro:
      'Die drei Verarbeitungsschritte nebeneinander: der reine Loth-Crop, das daraus gewonnene Skelett mit den abgetasteten Ankern und schließlich die kanonische Vorlage in Template-Koordinaten (Grundlinie = 0, Mittellinie = 1).',
    fitIntro:
      'Die kanonische Vorlage auf ihr eigenes Skelett gefittet (M4): Skelett, Vorlage (grau) und Fit (rot) übereinander, dazu die Fehlermaße. Mit dem λ-Regler die Regularisierung abwägen — niedrig folgt dem Skelett, hoch hält die Form zusammen.',
    computing: 'Diagnose wird gerechnet…',
    noCanonicalShort: 'noch kein Canonical — erst Strich aufnehmen',
    reload: 'neu laden',
    cropHeading: 'Loth-Crop',
    // Followed by the anchor count "(…)" in the column heading.
    skeletonHeading: 'Skelett + Anker',
    // Followed by "{deg}°)" in the column heading.
    canonicalHeading: 'Canonical (Template-Koords, Schräge',
    guidesReadout: 'Grundlinie=0 · Mittellinie=1 · Oberlinie={{ascender}} · Unterlinie={{descender}}',
  },
  fit: {
    computing: 'Fit wird gerechnet…',
    overlayHeading: 'Crop · Skelett · Canonical (grau) · Fit (rot)',
    converged: 'konvergiert',
    notConverged: 'nicht konvergiert',
    // Preceded by the iteration count in the chip label.
    iterations: 'Iter.',
    // Composed metric labels (values + units stay in the component).
    geoRmse: 'Geometrie-RMSE:',
    widthRmse: 'Breiten-RMSE:',
    maxAnchorDelta: 'max. Anker-Δ:',
    lambdaHint: 'Geometrie folgt dem Skelett; λ (Tikhonov) hält die Vorlage zusammen — niedrig = näher am Skelett, hoch = formtreuer.',
    // Followed by the current λ value.
    regularization: 'Regularisierung λ =',
  },
} as const;
