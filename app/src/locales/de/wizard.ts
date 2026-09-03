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
    weg: 'Weg',
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
    zoom: 'Vergrößerung',
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
    // Short essential lead under the tool toggle (the full explanation is behind
    // the heading's info mark).
    leadEraser: 'Fremde Tinte vom Nachbarn übermalen — vom Buchstaben selbst nichts.',
    leadInk: 'Weiße Lücken in einem durchgehenden Strich auffüllen.',
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
    // Third tool: "Zelle einsetzen" — copy ink from another cell of the same
    // chart into this crop, for glyphs with no own cell (ü/ö borrowing ä's
    // umlaut over a u/o body). The donor's ink wins by darken, so its white
    // background never erases the base.
    toolPatch: 'Zelle einsetzen',
    leadPatch: 'Tinte aus einer anderen Zelle einsetzen — z. B. die Umlaut-Striche vom ä über ein u/o für ü/ö.',
    patchBody:
      'Manche Buchstaben fehlen als eigene Zelle auf der Tafel: ü und ö gibt es nicht, wohl aber ein u/o und das ä mit seinen zwei Umlaut-Strichen. Hier eine Spenderzelle wählen (die Striche vom ä), sie über den Grundbuchstaben setzen und dann ganz normal nachfahren. Den u-Bogen vorher mit dem Radierer entfernen.',
    // Button that opens the donor picker (full chart).
    patchPick: 'Spenderzelle wählen',
    patchListTitle: 'Eingesetzte Zellen',
    patchEmpty: 'Noch keine Zelle eingesetzt.',
    // Followed by the 1-based index.
    patchItem: 'Zelle',
    patchRemove: 'Entfernen',
    patchDragHint: 'Im Bild an die richtige Stelle über dem Grundbuchstaben ziehen.',
  },
  // Donor picker dialog: choose a region of the full chart to copy in.
  donor: {
    title: 'Spenderzelle wählen',
    help: 'Einen Rahmen um die Stelle ziehen, deren Tinte eingesetzt werden soll — z. B. die zwei Umlaut-Striche über dem ä.',
    redraw: 'Neu ziehen',
    cancel: 'Abbrechen',
    confirm: 'Übernehmen',
  },
  lineatur: {
    title: 'Schritt 2 · Lineatur & Schräglage',
    // Short essential lead (the full four-line-system explanation is behind the
    // heading's info mark); composed after the two coloured line names.
    leadAction: 'an die richtige Höhe ziehen.',
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
    title: 'Schräglage',
    // Short essential lead (the full convention explanation is behind the info
    // mark); the green handle sits just below the Grundlinie.
    lead: 'Neigung der Abstriche — 90° = senkrecht. Den grünen Punkt unter der Grundlinie ziehen, um eine Linie zu legen.',
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
  },
  trace: {
    title: 'Schritt 3 · Weg (Duktus)',
    // Short essential lead (the full explanation + the pen-lift rule sit behind
    // the heading's info mark).
    lead: 'Den Buchstaben in Schreibrichtung nachziehen — jedes Absetzen beginnt einen neuen Strich.',
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
    // Two states that used to share one green box. `saved` is the EVENT — it
    // belongs to the alert bar, which announces it once. `hasSaved` is the
    // standing condition, written in the present tense and set quietly: it
    // showed on every opening of a glyph traced months ago, so a screen reader
    // called out „Weg gespeichert" as fresh news, and it stood just as green on
    // a locked glyph where saving is guaranteed to fail.
    saved: 'Weg gespeichert. Vorschau unten · weiter zur Übersicht.',
    hasSaved: 'Ein Weg ist gespeichert — er wird unten eingeblendet; neu zeichnen überschreibt ihn.',
    showSaved: 'Gespeicherten Weg & Anker einblenden',
    anchorsLabel: 'Anker (n_anchors)',
    resample: 'Neu abtasten',
    anchorsHint:
      'n_anchors = Zahl der Stützpunkte, auf die der Pen-Pfad abgetastet wird. Der Originalpfad bleibt erhalten, also jederzeit ohne Neuzeichnen neu abtastbar.',
  },
  // Inline Weg preview (WegPreview, shown under the Weg controls once saved).
  optimize: {
    title: 'Optimierung (Vorschau)',
    body:
      'Die gespeicherte Form über dem Original — rot, mit gemessener Strichbreite. Der volle Vergleich (roh vs. optimiert, alle Maße) liegt in der Diagnose.',
    computing: 'Vorschau wird gerechnet …',
    score: 'Score',
    overlayCaption:
      'Rot = die gerenderte Form über dem Crop. Wo Tinte ohne Rot ist, deckt das Rendering nicht; wo Rot über hellem Papier liegt, rendert es zu viel — so siehst du die Stellen, die noch nicht passen.',
    // Followed by the score delta, e.g. "+3.1".
    delta: 'Δ Score (optimiert − roh):',
    recompute: 'Neu berechnen',
    // Per-category penalty breakdown of the optimized score (like the glyph bench):
    // shows where the form loses points (higher penalty = bigger deduction).
    breakdownHeading: 'Abzüge nach Kategorie (optimiert)',
    breakdownHint: 'Wo die optimierte Form Punkte verliert — höher = mehr Abzug, wie im Glyph-Bench.',
    breakdownNone: 'Keine nennenswerten Abzüge — die Form ist sauber.',
    // Prefix on the one-line variant (ScoreBreakdownInline, letter overview).
    // The full breakdown carries `breakdownHint` under its bars to say which
    // way the numbers run; the short form had no room for it and so showed a
    // bare „Deckung 0.99", which reads as a result rather than as a deduction.
    breakdownInlinePrefix: 'Abzüge:',
    // Short category labels mirroring the naturalness metric's components.
    // Every one of them is an ABZUG — höher = schlechter. `coverage` therefore
    // reads „Deckungslücke", not „Deckung": the value is `1 − gate`, and the
    // gate is the COMPOSITE `dice · q_chamfer · q_geo`
    // (`core/quality_suetterlin.py`) — overlap, boundary distance and
    // centerline position together, not the missed-ink share alone. Under the
    // old label the same panel printed „Deckung (IoU): 0.105" and „Deckung
    // 0.99" three lines apart, and the 0.99 read like an excellent result
    // while being the maximum possible deduction (author decision 2026-09-03).
    cat: {
      smoothness: 'Glätte',
      verticality: 'Senkrechte',
      corner: 'Ecken',
      collinearity: 'Kreuzung',
      retrace: 'Doppelzug',
      coverage: 'Deckungslücke',
    },
    catHint: {
      smoothness: 'Bögen ohne Zacken',
      verticality: 'Abstriche wirklich senkrecht',
      corner: 'Umkehrpunkte sauber spitz',
      collinearity: 'Strich bleibt durch eine Kreuzung gerade',
      retrace: 'Hin- und Rückzug laufen parallel',
      coverage: 'Abzug aus dem Deckungs-Gate — Überlappung, Randabstand und Mittellinien-Lage zusammen',
    },
  },
  overview: {
    title: 'Schritt 4 · Übersicht & Freigabe',
    // Verification panel on the right (OverviewVerify): crop · written · overlaid
    // + the score criteria, so it's visible at a glance that the form fits.
    verify: {
      title: 'Prüfen — sitzt alles?',
      body:
        'Die Vorlage, die live geschriebene Form und beide übereinander — so siehst du sofort, ob der synthetisierte Zug die Tinte trifft, bevor du sperrst.',
      cellCrop: 'Vorlage',
      cellWritten: 'Geschrieben',
      cellOverlay: 'Überlagert',
      rewrite: 'Neu schreiben',
    },
    // Composed around the inline <b>Diagnose</b>.
    bodyBeforeBold: 'Alles geprüft? Mit der',
    bodyBold: 'Diagnose',
    bodyAfterBold:
      'kannst du das Ergebnis groß ansehen: der reine Crop, das Skelett mit Ankern und die kanonische Vorlage nebeneinander (plus den M4-Fit).',
    openDiagnose: 'Diagnose öffnen',
    noTraceYet: 'Noch kein Weg gezeichnet — Schritt „Weg“ zuerst.',
    // Says what the lock does AFTER the doctrine change (2026-09-03): it marks
    // the glyph as finished and puts a confirmation in front of the next write
    // — it no longer makes the wizard refuse until someone unlocks in the Tafel.
    // The old wording („erst nach Entsperren wieder änderbar") promised exactly
    // that, two steps away from the step that now contradicts it.
    lockCaption:
      'Mit „Abschließen & sperren“ gilt der Glyph als fertig (🔒). Ändern bleibt möglich — der Wizard fragt dann vor dem Überschreiben noch einmal nach.',
  },
  // Every message that reaches the wizard's alert bar. It carries a severity of
  // its own now: a failed write is red, a refused gesture amber, a saved Weg
  // green — before, all of them rendered as the same blue-grey `info`, so a 423
  // Locked looked exactly like a confirmation.
  snack: {
    saveFailed: 'Die Änderung konnte nicht gespeichert werden.',
    baselineBelowMidband: 'Grundlinie muss unter der Mittellinie liegen.',
    traceSaved: 'Weg gespeichert · {{count}} Anker',
    traceFailed: 'Der Weg konnte nicht gespeichert werden.',
    resampled: 'neu abgetastet · {{count}} Anker',
    resampleFailed: 'Das neue Abtasten ist fehlgeschlagen.',
    previewFailed: 'Die Vorschau konnte nicht gerechnet werden.',
    finishFailed: 'Abschließen fehlgeschlagen.',
  },
  // Leaving with an undrawn Weg still on the canvas. The Weg is the one thing
  // in this dialog that is NOT live-committed, and nobody but the author can
  // draw it again — so Escape, a backdrop click and „Schließen" all ask first.
  confirmClose: {
    title: 'Gezeichneten Weg verwerfen?',
    body:
      'Der gezeichnete Weg ist noch nicht gespeichert. Alles andere in diesem Fenster — Ausschluss, Tinte, Lineatur und Schräglage — steht bereits in der Datenbank; nur der Weg ginge verloren.',
    // Followed by the stroke count.
    strokes: 'Ungespeichert: {{count}} Strich(e).',
    keep: 'Zurück zum Zeichnen',
    discard: 'Verwerfen und schließen',
  },
  // The rescued draft, offered on the Weg step when the last visit was closed
  // with strokes on the canvas (sessionStorage — the tab's own memory).
  draft: {
    // Followed by the stroke count.
    offer: 'Nicht gespeicherter Weg von vorhin — {{count}} Strich(e).',
    restore: 'Wiederherstellen',
    dismiss: 'Verwerfen',
  },
  // The lock, as the author decided it should behave (2026-09-03): a locked
  // glyph stays fully offered and is marked with the lock; overwriting is one
  // deliberate confirmation away, not a trip to the Tafel and back. The gate
  // is still real — the server refuses without `force` (423), and only the
  // dialog below ever sends it.
  lock: {
    chip: '🔒 gesperrt',
    warning:
      'Diese Glyphe ist gesperrt — sie gilt als fertig. Zeichnen darfst du trotzdem; beim Speichern fragt die Werkbank noch einmal nach, bevor der bestehende Weg überschrieben wird.',
    // The save button's label while the glyph is locked, so the click never
    // comes as a surprise.
    saveLocked: 'Weg speichern (gesperrt)',
    confirm: {
      title: 'Gesperrten Weg überschreiben?',
      body:
        'Für diese Glyphe liegt bereits ein abgeschlossener Weg. „Überschreiben“ ersetzt ihn durch den soeben gezeichneten — die alte Fassung ist danach nicht mehr abrufbar.',
      // A bbox can carry the lock WITHOUT a stored Weg — the lock is a column
      // on the bbox, and an import or a direct PUT can set it before anything
      // was traced. Then „ersetzt die alte Fassung" would be a plain untruth,
      // so that state gets its own sentence.
      titleFirst: 'Auf gesperrter Glyphe speichern?',
      bodyFirst:
        'Diese Glyphe ist als fertig gesperrt, es liegt aber noch kein Weg vor. Gespeichert wird also der erste — überschrieben wird nichts.',
      // Shown under the body, so what is at stake is a fact and not a memory.
      hint: 'Die Sperre bleibt danach bestehen; nur der Weg wechselt.',
      hintFirst: 'Die Sperre bleibt danach bestehen.',
      cancel: 'Abbrechen',
      confirm: 'Trotzdem überschreiben',
      confirmFirst: 'Trotzdem speichern',
    },
    // Same question for the second write on the Weg step.
    confirmResample: {
      title: 'Gesperrte Glyphe neu abtasten?',
      body:
        'Neu abtasten schreibt die gespeicherte Vorlage neu — aus demselben Roh-Weg, aber mit der eingestellten Ankerzahl. Die bisherige Fassung wird dabei ersetzt.',
      hint: 'Die Sperre bleibt danach bestehen; nur die Abtastung wechselt.',
    },
  },
} as const;
