// German strings for the Einrichtungs-Wizard (sections/admin/setup-wizard/*).
// Pre-i18n message catalog — key tree mirrors a future i18next `wizard`
// namespace. {{…}} placeholders are filled via fmt(); `…Bold`/fragment keys
// are composed around inline <b> markup in the step components.

export const wizard = {
  // Followed by the glyph label in the dialog title.
  title: 'Einrichten ·',
  steps: {
    mask: 'Ausschluss',
    lineatur: 'Lineatur',
    slant: 'Schräglage',
    weg: 'Weg',
    optimize: 'Optimieren',
    overview: 'Übersicht',
  },
  footer: {
    back: 'Zurück',
    close: 'Schließen',
    next: 'Weiter',
    finish: 'Abschließen & sperren',
  },
  // Floating zoom/pan controls on the crop canvas (WizardCanvas).
  canvas: {
    panTooltip: 'Schwenken — Ausschnitt verschieben',
    pan: 'Schwenken',
    zoomOut: 'herauszoomen',
    zoomIn: 'hineinzoomen',
    fitTooltip: 'Anpassen — ganzen Ausschnitt zeigen',
    fit: 'Anpassen',
  },
  mask: {
    title: 'Schritt 1 · Ausschluss & Tinte',
    body1:
      'Auf den Lehrtafeln stehen die Buchstaben dicht beieinander — ragt Tinte vom Nachbarn in diesen Ausschnitt, verfälscht sie später Skelett und Anker. Mit dem Pinsel direkt über die störenden Stellen malen; das Übermalte wird vor der Skelettberechnung entfernt.',
    body2: 'Nur fremde Tinte ausschließen — vom eigentlichen Buchstaben nichts wegradieren.',
    // Tool toggle: the eraser blanks neighbour ink, the ink brush fills specks.
    toolEraser: 'Radierer',
    toolInk: 'Tinte',
    // Shown when the ink brush is selected (replaces body1/2).
    inkBody:
      'Mit der Tinte weiße Flecken in einem sonst durchgehenden Strich auffüllen — das Gegenstück zum Radierer. Das Übermalte zählt vor der Skelettberechnung als Tinte.',
    // Followed by "{radius}px".
    brushSize: 'Pinselgröße:',
    // Followed by the stroke count "(…)".
    undo: 'Letzten Strich zurück',
    // Per-glyph speck auto-fill slider. Followed by the value or "aus" at 0.
    fillHoles: 'Lücken füllen:',
    fillHolesOff: 'aus',
    fillHolesHint:
      'Füllt kleine eingeschlossene weiße Flecken automatisch (bis zur eingestellten Fleckgröße); echte Punzen bleiben offen. Pro Buchstabe — aus, wenn es mehr schadet als hilft.',
    // "Maske zeigen" preview: swaps the raw scan for the binarised mask, with a
    // legend so the auto-fill result and the gaps still to ink are readable.
    showMask: 'Maske zeigen',
    showMaskHint: 'Zeigt, was das Skelett sieht — so wird die Füllung sichtbar und du erkennst, wo noch Tinte fehlt.',
    legendInk: 'Tinte',
    legendAuto: 'automatisch gefüllt',
    legendGap: 'Lücke → tinten',
  },
  lineatur: {
    title: 'Schritt 2 · Lineatur',
    // Composed around the coloured <b>Grundlinie</b>/<b>Mittellinie</b>/… line
    // names (common LINEATUR_LABELS) and the "({ratio})." readout.
    bodyIntro: 'Die',
    bodyAfterBaseline: '(auf der die Mittellänge aufsitzt) und die',
    bodyAfterMidband: '(Oberkante der Mittellänge) direkt im Bild an die richtige Höhe ziehen.',
    bodyAnd: 'und',
    bodyDerived: '(grau) ergeben sich automatisch aus dem Stil-Verhältnis',
    body2:
      'Diese vier Linien bilden das Vierliniensystem (Zonen: Oberlänge · Mittellänge · Unterlänge) und den Bezug für alle weiteren Maße.',
    readout: 'Grundlinie {{baseline}} · Mittellinie {{midband}} · Mittellänge (x-Höhe) {{xHeight}}px',
  },
  slant: {
    title: 'Schritt 3 · Schräglage',
    body1:
      'Die Schräglage ist die Neigung der Grundstriche (Abstriche), gemessen von der Grundlinie aus — 90° = senkrecht. Sütterlin steht aufrecht (90°); die Loth-Tafel liegt bei ≈50°, die Kurrent um 1900 bei 60–70°. Den grünen Punkt ziehen, um eine Linie über den Buchstaben zu legen.',
    // Composed around <b>eine</b>.
    body2BeforeBold: 'Für die meisten Buchstaben reicht',
    body2Bold: 'eine',
    body2AfterBold:
      'Linie. Bei mehreren gleich geneigten Grundstrichen (m · n · u) kannst du weitere Linien hinzufügen und jede einzeln platzieren — alle teilen denselben Winkel.',
    angleLabel: 'Schräglage',
    // Followed by the line count "(…)".
    linesHeading: 'Schräglinien',
    addLine: 'Linie hinzufügen',
    // Followed by the line number in the chip label.
    lineChip: 'Linie',
    dragHint: 'Den grünen Punkt einer Linie ziehen, um sie zu verschieben; das ✕ am Chip entfernt sie.',
  },
  trace: {
    title: 'Schritt 4 · Weg (Duktus)',
    body1:
      'Den Buchstaben in Schreibrichtung mit dem Stift (S-Pen) oder der Maus nachziehen — das ist der Duktus, die eigentliche Vorlage über der Tafel-Geometrie.',
    // Composed around the inline <b>u</b>.
    penLiftBold: 'Jedes Absetzen beginnt einen neuen Strich',
    penLiftAfterBold: '— zwischen den Strichen wird keine Verbindungslinie gezogen. Beim',
    penLiftRest: 'also erst den ersten Abstrich, absetzen, dann den zweiten — nacheinander, nicht in einem Zug.',
    // Zeichnen = draw new strokes; Anpassen = drag the drawn line to fix a wobble.
    toolDraw: 'Zeichnen',
    toolAdjust: 'Anpassen',
    nudgeRadius: 'Radius',
    adjustHint:
      'Die gezeichnete Linie mit gedrückter Maustaste ziehen, um einen Wackler zu glätten — Punkte im Radius folgen, außen läuft die Linie weich zurück. Wirkt nur auf den noch nicht gespeicherten Entwurf.',
    // Followed by the stroke count "(…)".
    undoStroke: 'Letzter Strich',
    discardAll: 'Alles verwerfen',
    save: 'Weg speichern',
    saved: 'Weg gespeichert. Weiter zum Optimieren.',
    showSaved: 'Gespeicherten Weg & Anker einblenden',
    anchorsLabel: 'Anker (n_anchors)',
    resample: 'Neu abtasten',
    anchorsHint:
      'n_anchors = Zahl der Stützpunkte, auf die der Pen-Pfad abgetastet wird. Der Originalpfad bleibt erhalten, also jederzeit ohne Neuzeichnen neu abtastbar.',
    entryCoupling: 'Kopplung Anfang',
    exitCoupling: 'Kopplung Ende',
    couplingHint:
      'Höhe, auf der ein Nachbarbuchstabe ansetzt (Anfang) bzw. weiterläuft (Ende). Greift bei bestehendem Canonical sofort beim nächsten Speichern.',
  },
  optimize: {
    title: 'Schritt 5 · Optimierung prüfen',
    body:
      'Der gespeicherte Weg wird zum Vergleich zweimal abgeleitet: einmal roh (nur gemessen) und einmal optimiert — bei der optimierten Variante werden Anker und Strichbreiten auf die Tintenkante des Originals gezogen, Umkehrpunkte bleiben spitz. Gespeichert ist bereits die optimierte Form (Schritt „Weg“); hier siehst du, was die Optimierung bringt und wo sie noch nicht perfekt passt.',
    computing: 'Vergleich wird gerechnet…',
    crop: 'Original (Crop)',
    before: 'Vorher (roh gemessen)',
    after: 'Nachher (optimiert)',
    score: 'Score',
    viewSide: 'Nebeneinander',
    viewOverlay: 'Überlagert',
    overlayHeading: 'Optimierte Silhouette über dem Original',
    overlayCaption:
      'Rot = die gerenderte Form über dem Crop. Wo Tinte ohne Rot ist, deckt das Rendering nicht; wo Rot über hellem Papier liegt, rendert es zu viel — so siehst du die Stellen, die noch nicht passen.',
    // Followed by the score delta, e.g. "+3.1".
    delta: 'Δ Score (optimiert − roh):',
    needTrace: 'Noch kein Weg vorhanden — erst im Schritt „Weg“ zeichnen.',
    recompute: 'Neu berechnen',
    // Per-category penalty breakdown of the optimized score (like the glyph bench):
    // shows where the form loses points (higher penalty = bigger deduction).
    breakdownHeading: 'Abzüge nach Kategorie (optimiert)',
    breakdownHint: 'Wo die optimierte Form Punkte verliert — höher = mehr Abzug, wie im Glyph-Bench.',
    breakdownNone: 'Keine nennenswerten Abzüge — die Form ist sauber.',
    // Short category labels mirroring the naturalness metric's components.
    cat: {
      smoothness: 'Glätte',
      verticality: 'Senkrechte',
      corner: 'Ecken',
      collinearity: 'Kreuzung',
      retrace: 'Doppelzug',
      coverage: 'Deckung',
    },
    catHint: {
      smoothness: 'Bögen ohne Zacken',
      verticality: 'Abstriche wirklich senkrecht',
      corner: 'Umkehrpunkte sauber spitz',
      collinearity: 'Strich bleibt durch eine Kreuzung gerade',
      retrace: 'Hin- und Rückzug laufen parallel',
      coverage: 'Form deckt die Originaltinte (Gate)',
    },
  },
  overview: {
    title: 'Schritt 6 · Übersicht & Freigabe',
    // Composed around the inline <b>Diagnose</b>.
    bodyBeforeBold: 'Alles geprüft? Mit der',
    bodyBold: 'Diagnose',
    bodyAfterBold:
      'kannst du das Ergebnis groß ansehen: der reine Crop, das Skelett mit Ankern und die kanonische Vorlage nebeneinander (plus den M4-Fit).',
    openDiagnose: 'Diagnose öffnen',
    noTraceYet: 'Noch kein Weg gezeichnet — Schritt „Weg“ zuerst.',
    positionsHeading: 'Positionen (Anfang · Mitte · Ende)',
    unifiedOption: 'Eine Form für alle Positionen',
    splitOption: 'Nur „{{position}}“ getrennt einrichten (abweichende Form)',
    unifiedCaption:
      'Diese Form gilt für alle drei Positionen; die Anschlussstriche werden je Position aus Anfang/Ende erzeugt. Im Quiz und in der Sidebar erscheint der Buchstabe einmal.',
    splitCaption:
      'Nur „{{position}}“ bekommt diese Form, die anderen Positionen behalten ihre eigene. Der Buchstabe erscheint dann pro Position getrennt.',
    // Composed around the inline <b>diese</b>.
    overwriteBeforeBold: 'Der Buchstabe ist aktuell aufgetrennt — „Eine Form für alle“ überträgt',
    overwriteBold: 'diese',
    overwriteAfterBold: 'Form auf alle drei Positionen und überschreibt die abweichenden.',
    lockCaption:
      'Mit „Abschließen & sperren“ wird der Glyph gesperrt (🔒) und ist erst nach Entsperren wieder änderbar.',
  },
  snack: {
    // Followed by the error in the snackbar message.
    saveFailed: 'Speichern fehlgeschlagen:',
    baselineBelowMidband: 'Grundlinie muss unter der Mittellinie liegen.',
    traceSaved: 'Weg gespeichert · {{count}} Anker',
    resampled: 'neu abgetastet · {{count}} Anker',
    // Followed by the error in the snackbar message.
    finishFailed: 'Abschließen fehlgeschlagen:',
  },
} as const;
