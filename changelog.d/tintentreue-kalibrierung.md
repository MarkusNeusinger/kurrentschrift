### Added

- **Das Kalibrier-Instrument für die Tintentreue-Ampel.** Jede der acht
  Schwellen in `core/eigenhand/tintentreue.py` ist geborgt — von der Platte,
  vom dev-19-Satz oder von gar keiner Messung —, und die einzige gemessene
  gehört zu einem bekannten Abdeckungsversagen. `tools/eigenhand/
  tintentreue_calibration.py` baut die Runde, die sie ersetzt: 30 Wortkästen
  einer Hand, blind in drei Stufen plus vier Merkmale beurteilt, gezogen nach
  der vorläufigen Stufe geschichtet, mit Rückhaltemenge, blinden
  Wiederholungen und Provenienz-Stempel; `analyse` rechnet den Ergebnistext in
  der vorregistrierten Reihenfolge durch und DRUCKT einen `Schwellen(…)`-Block,
  statt ihn zu schreiben — die Übernahme ist ein datierter Schritt des Autors.
  Ein Nachbau und kein Modus von `humanbench`: dessen Crops kommen aus
  eingefrorenen Fixture-Wurzeln, seine Taxonomie hat sechs Fit-Kategorien, und
  seine Seite wird veröffentlicht — diese nie, denn ihre Ausschnitte sind die
  reservierten Eigenhand-Pixel. Geteilt wird genau eine Sache: die Seite.
- **Ein vierter Kategoriensatz für die Urteils-Seite.** `page.py` kennt neben
  den sechs Fit-Kategorien die drei Ampelstufen mit ihren vier Merkmalen
  (`STRIP_CATEGORIES`, Frage `tintentreue`). Neu daran ist die Art `detail`:
  ein Merkmal addiert sich zur Stufe, statt sie zu löschen, wie es eine
  Fehlerart beim „Gut" tut — die Stufe IST hier das Urteil, und ein Merkmal
  sagt nur, welcher Sensor sie hätte sehen müssen.
- **Das Verfahren steht vor dem Code.** `menschliche-bewertung.md` §8b trägt
  Frage, Kategorien, die Abbildung auf die drei Stufen, die
  Konstruktionsregeln und den Auswerteplan; die Runde selbst ist in
  `messjournal.md` §14 vorregistriert, samt Schranken, Quantil-Regel,
  Rundungsrichtung und Kill-Kriterien. Die Runde läuft noch nicht: sie braucht
  30 echte Kästen und den blinden Durchgang des Autors, also bleibt
  `VORLAEUFIG` unberührt und das Etikett „vorläufig" stehen.
