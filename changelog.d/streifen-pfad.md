### Added

- **Der Streifen-Pfad: die gefolgte Federbahn eines geschriebenen Wortes, als
  Daten neben dem Bild.** Eine Fassung trug bisher ein Bild, ein Verdikt, einen
  Befund und eine Fleckenmaske — aber keinen Duktus; das Bild sagte, WO die
  Tinte liegt, und nie, in welcher Reihenfolge die Feder sie gelegt hat. Neu
  speichert `eigenhand_strips.pfade` (Migration `0031`) je Wortkasten die Züge
  in den Einheiten des Wortes — demselben Rahmen, den `word_instances.strokes`
  benutzt —, die Registrierung in den Pixeln des Streifens, das Verfahren, die
  Folger-Konfiguration, das Datum und die Maskengröße, unter der gefolgt wurde.
  Gerechnet wird außerhalb und über `PUT /eigenhand/strips/…/pfade` abgelegt:
  das API-Abbild liefert `tools/` nicht aus, also kann der Server nie selbst
  folgen. Die Spalte ist wie das PNG verzögert geladen, damit keine
  Bestandsabfrage jede Bahn jeder Fassung mitschleppt.
- **`tools.eigenhand.pfad` — folgen, ansehen, dann erst schreiben.** Holt
  Streifenbild, Bogen-Layout und Kasten-Rechtecke über die Admin-API, schneidet
  jedes Wort heraus und lässt den Tintenpfad mit der festgezurrten
  Konfiguration darüber laufen (`tip_read` · `rail=tentfit` · `edt_upsample=4`
  · `ink_bridge_xh=1.0` · `hairpin_tip` · `ride_back` · `tip_grey_stop` ·
  `self_jump`), die mit in die Zeile wandert. **Trockenlauf ist die Vorgabe**;
  `--apply` schreibt in die geteilte Datenbank und gehört hinter einen
  Archiv-Schnappschuss.
- **Ein Pfad-Overlay für beide Flächen.** In den Wörtern steht „Pfad" als
  dritter Ebenen-Knopf neben Nachfahrung und Engine, in der Eigenhand-Ansicht
  legt „Pfad zeigen" die Bahn über Streifen und Wort-Ausschnitte: Farbverlauf
  in Schreibreihenfolge, Punkt am Ansatz, Pfeilspitze am Zugende und
  **gestrichelte Verbinder für die Absetzer** — das Stück, das eine einfarbige
  Linie vollständig verbirgt, weil ein Absetzer dort aussieht wie eine Ecke.
  Dazu Herkunft und Datum als Bildunterschrift; `WordInstanceOut` trägt dafür
  nun sein `updated_at`, und die Streifen-Liste je Wortkasten sein
  Pixel-Rechteck.
