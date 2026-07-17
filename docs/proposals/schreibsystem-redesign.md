# Schreibsystem-Redesign 2026-07-17 — eine Form pro Glyphe, Paar-Matrix, geerntete Paar-Overrides, Schräglagen-Befund

**Status:** Richtungsentscheid des Nutzers (2026-07-17) nach kritischer
Prüfung: **angenommen** — inklusive des Positions-Rückbaus (R2).
**R1 und R1b Stufe 1 sind umgesetzt** (2026-07-17: `/admin/paare`
Paar-Matrix; `/admin/vergleich` mit Wortvorlagen-Tabs über die neuen
öffentlichen `/word-samples`-Reads, registrierte Überlagerung). Offen:
R1b Stufe 2 (Scores), R2–R5 (Reihenfolge s. §6). Dieses Dokument konkretisiert
[`planaenderungen.md`](planaenderungen.md) Vorschlag B (Paar-Overrides,
dort weiterhin der sanktionierte Rahmen) und baut auf dem
platzierungsbereinigten Paar-Befund in
[`uebergaenge-befund.md`](uebergaenge-befund.md) auf. Die betroffenen
Konzept-Passagen ([`architektur.md`](../concepts/architektur.md) §3
`position`, §4 Übergänge) werden erst **mit der jeweiligen
Implementierungs-PR** angepasst, nicht vorab.

## 1. Anlass: der Nutzer-Vorschlag

Trotz der Compose-Läufe `jul02`/`jul08`/`jul11` wirken einzelne Übergänge
im Live-Bild weiterhin unnatürlich. Der Vorschlag (2026-07-17):

1. **Nur noch eine Version pro Glyphe** (statt der drei Positions-Kopien
   initial/medial/final), festgelegt wie heute im Admin.
2. **Jede Zweier-Kombination sichtbar machen** — pro autorisierter Glyphe
   alle Kombinationen mit jedem anderen Buchstaben (Versalien nur links),
   per Default generiert aus den zwei Glyphen + Übergang.
3. **Beliebige Kombinationen manuell überschreibbar**: ein Admin-Editor
   mit beiden ausgeschnittenen Buchstaben nebeneinander, verschiebbar,
   Übergang zeichnen/löschen, dann den Weg nachziehen wie beim
   Einzelbuchstaben-Wizard.
4. Aus vielen manuell gezeichneten Paaren **lernen**, um die generierten
   zu verbessern.

## 2. Kritische Prüfung gegen die Mess-Evidenz

Die Paar-Sektion ([`uebergaenge-befund.md`](uebergaenge-befund.md), 87
platzierungsbereinigte Vorkommen über 45 Paare) beantwortet die Kernfrage
des Vorschlags bereits empirisch:

- **Platzierung ist der größte Einzelfehler** (39/87 Vorkommen brauchen
  ≥ 0,25 xh Korrektur; Median 0,19 xh, P75 0,36 xh). Ein manuell
  perfektes Paar behebt das nicht — im Wort schiebt das
  Advance-/Clearance-Modell, nicht das Paar.
- **Für Brot-und-Butter-Verbindungen ist der Generator nach korrekter
  Platzierung praktisch deckungsgleich mit der Probe** (Chamfer ≤ 0,07
  für e→n, n→e, t→e, f→e, …). Kein Kleinbuchstaben-Paar verhält sich
  idiosynkratisch; die Abweichungen gruppieren sich nach wenigen
  **Exit-Klassen** (d-Schleife, Deckstrich-Bogen o/b/v/w, r-Arm).
- **Echte Paar-Formen brauchen die Versal-Verbindungen** (B→i 0.258,
  I→n 0.249, D→u 0.195; tail_adapt bis 0,36 xh — die Feder schreibt die
  Glyphen-Enden um). Das deckt sich mit der Einschränkung des Vorschlags
  („Versalien nur links") und mit Vorschlag B, dessen motivierende
  C/H-Beobachtung ebenfalls Versalien betraf.

Dazu die Kombinatorik: ~30 Kleinbuchstaben rechts × (~30 klein + ~29
Versal) links ≈ **1 700–1 800 Paare**. Flächendeckendes Freihand-Autoring
wäre Wochen Arbeit für Verbindungen, die der Generator zu ~90 % bereits
richtig erzeugt — und ein freihand gezeichneter Übergang ist die
**falsche Hand**: das Projekt misst gegen die 1922er-Vorlagenhand
(Analysis-by-Synthesis), nicht gegen das Augenmaß des Autors. Das
bessere Lernmaterial existiert schon: der M4-Fit in pairlab §5b erntet
die **echten** Paar-Geometrien aus Abb. 19/20 (63 Wörter + 33
Buchstabenpaare, gleiche Hand wie das Chart).

**Ergebnis der Prüfung** (vom Nutzer angenommen): Punkt 1 und 2 ja;
Punkt 3 als *sparsame* Override-Schicht mit **Ernten vor Zeichnen**
(der Editor ist Prüf-/Korrektur-/Freigabe-Oberfläche, Freihand nur wo
keine Vorlage existiert); Punkt 4 invertiert — der Generator lernt aus
den **gefitteten Vorlagen-Paaren**, nicht aus Freihand-Zeichnungen.

## 3. Entscheid

1. **Eine Form pro Glyphe + Positions-Rückbau (R2).** Die drei
   Positions-Kopien pro Buchstabe entfallen; `position` wird vom
   Template-Key-Bestandteil zum reinen Render-Kontext. Echte Allographen
   (langes ſ vs. rundes s) bleiben getrennte Glyphen, positionssanktionierte
   Formvarianten bleiben `variant`-Zeilen — beides unverändert §3.
2. **Paar-Matrix-Ansicht im Admin (R1).** Alle Kombinationen einer
   Glyphe, serverseitig generiert (`/write/word`), sortierbar nach
   gemessener Abweichung. Reine Lese-Ansicht, keine Migration.
3. **Paar-Overrides sparsam und geerntet (R3).** Vorschlag-B-Schema
   (Override → Generator-Fallback); Erstbefüllung per M4-Fit aus den
   Abb.-20-Paaren, Versal-Verbindungen zuerst. Der Paar-Editor aus dem
   Nutzer-Vorschlag wird als Freigabe-/Korrektur-UI gebaut.
4. **Platzierungs-Restfehler + O3-Neubewertung (R4)** im
   Wordbench-Loop — laut Messung der größte Hebel gegen das
   „unnatürliche" Live-Bild bei Kleinbuchstaben.
5. **Schräglagen-Differenz (R5)**: neuer Messbefund (s. §4), zunächst
   als Bench-Report-Größe, dann klassenbasierte Korrektur im Loop.

## 4. Neuer Messbefund — Schräglage: Chart-Zellen vs. verbundene Schrift

Nutzer-Beobachtung (2026-07-17): die Schräglagen der geschriebenen
Sütterlin-Wörter wirken anders als die der Einzelbuchstaben. Nachgemessen
mit **demselben Schätzer auf beiden Seiten** (Scher-Suche −30°…+30° in
0,25°-Schritten, Maximierung der quadrierten Spaltenprofil-Summe —
klassische HTR-Slant-Schätzung; Konvention wie repo-weit: 90° = senkrecht,
< 90° = rechtslehnend):

- **Engine-Seite:** die 11 Wörter des Compose-Golden-Fixtures
  (`tests/fixtures/compose_golden.json.gz`, suetterlin-1922-Templates),
  mit `core/compose.py` komponiert und die Centerlines gerastert
  (60 px/xh).
- **Vorlagen-Seite:** alle 63 Abb.-19-Wortcrops aus
  `data/sources/suetterlin-1922/words.json` (Exclude-Rechtecke
  berücksichtigt, Otsu-Binarisierung); Abb. 20/22 als Kontext.

| Messung | n | Median | P25 | P75 | min | max |
|---|---|---|---|---|---|---|
| Engine-Wörter, volle Höhe | 11 | 90,00 | 89,88 | 90,00 | 88,25 | 90,00 |
| Abb. 19, volle Höhe | 63 | 90,00 | 89,25 | 90,00 | 85,00 | 97,00 |
| Abb. 19, nur Mittelband | 63 | 90,00 | 90,00 | 92,00 | 86,00 | 95,50 |
| Abb. 20 (Paare), volle Höhe | 33 | 90,75 | 89,00 | 91,75 | 81,50 | 109,25 |
| Abb. 22 (Schülerschrift, andere Hand), volle Höhe | 106 | 92,00 | 90,12 | 94,50 | 86,50 | 117,75 |

Lesart (Sichtprüfung an den Crops bestätigt):

1. **Im Median ist die Norm eingehalten** — die 1922er-Hand ist wie die
   Engine im Mittel senkrecht. Es gibt **keinen pauschalen
   Schräglagen-Offset**, den man global korrigieren müsste.
2. **Die Hand streut pro Wort um ±5°** (85°–97° über die Tafel), die
   Engine ist starr bei ~90° (Spannweite 1,75°). Diese Starrheit ist ein
   Teil des „zu glatt/zu mechanisch"-Eindrucks — aber Varianz-Nachbildung
   ist bewusst vertagt (s. Verworfen).
3. **Der systematische Anteil ist klassenförmig, nicht global:** die
   Wörter mit deutlicher Rechtslehnung bei voller Höhe sind die mit
   **d-Oberschleife** (`das` 85,0°, `der` 86,25°, `die` 86,75°/87,0° in
   beiden Vorkommen, `muß` 86,5°) — ihr Mittelband misst dabei ~90°: die
   Lehnung sitzt **oberhalb des Mittelbands, in der Schleife selbst**.
   Sichtbar auch in `und` (Mittelband ~95° leicht linksgelehnt, volle
   Höhe 90° — die rechtsgelehnte d-Schleife zieht den Vollhöhen-Wert
   zurück). Die d-Schleife ist damit in der verbundenen Schrift um
   ~4–5° rechtsgelehnt gegenüber der aufrechten Chart-Zelle — **dieselbe
   Klasse, die schon im Übergangs-Befund die schlechteste Exit-Klasse
   ist** (d→e 0.170 … d→p 0.200). Chart-Zelle ≠ fließende Form betrifft
   hier also nicht nur Bogenbreiten (jul08-Befund), sondern auch die
   Achse der Oberlängen-Schleife.
4. Abb. 22 bestätigt die Trennregel der Wordbench: der Schüler lehnt
   **links** (Median 92°) — eine andere Hand, die nie in die
   Headline-Mittelung gehört.

Konsequenz in R5: die Schräglage wird erst **Report-Größe** in der
Wordbench (nicht Headline), dann klassenbasierte Korrektur der
Oberlängen-Schleifen im gebundenen Kontext (analog O2: Renderpfad, nicht
Template; die gespeicherte Chart-Messung bleibt unangetastet) im
Keep/Discard-Loop.

## 5. Phasen

### R1 — Paar-Matrix-Ansicht (umgesetzt 2026-07-17)

Neue Admin-Seite `/admin/paare`: für eine gewählte Glyphe alle
Kombinationen (links Versalien + Kleinbuchstaben, rechts
Kleinbuchstaben), jede Zelle ein serverseitig komponiertes
Zwei-Buchstaben-„Wort" über den bestehenden cachebaren
`GET /write/word` (Zellen laden lazy per IntersectionObserver über den
gemeinsamen Render-Cache). Reine Lese-Ansicht; erzeugt die Sichtbarkeit
aus Punkt 2 des Nutzer-Vorschlags ohne jede Architektur-Festlegung.
Noch offen (mit R1b Stufe 2): Sortierung nach gemessener
Paar-Abweichung, damit die schlechtesten Joins oben stehen.

### R1b — Wortvergleich im Admin (Stufe 1 umgesetzt 2026-07-17)

Nutzer-Erweiterung (2026-07-17): die geschriebenen Vorlagen-Wörter fest
in den Admin einbauen — Vorlage und „wie geschrieben" immer als
Vergleich, damit sofort sichtbar ist, wo noch optimiert werden muss.

**Stufe 1 (umgesetzt):** `/admin/vergleich` bekommt Reiter
**Buchstaben · Wörter · Verbindungen · Andere Hand**. Die
Vorlagen-Daten kommen aus dem committeten `words.json`-Sidecar über
zwei neue **öffentliche** Reads (`GET /sources/{id}/word-samples` +
`/word-samples/{sample_id}/crop`, `core/chart.py::load_word_samples` /
`word_sample_crop_to_png_bytes`; öffentlich wie die Bbox-Crops, weil
`<img>`-Tags den Admin-Header nicht senden können, und die Tafeln sind
PD). Jede Karte zeigt den Vorlagen-Crop (Excludes weiß übermalt) neben
demselben Wort per `/write/word` — oder **überlagert**: die
Engine-Schrift maßstabsgetreu auf den Vorlagen-Pixeln, registriert über
die Sidecar-Lineatur (Skala = `baseline_y − midband_y` px pro x-Höhe,
linksbündig; exakt, kein Augenmaß). Fehlende Templates erscheinen als
`missing`-Chip; der „Andere Hand"-Reiter (Sidecar-`set`, z. B. die
Abb.-22-Schülerschrift) ist als Fremdhand beschriftet und bleibt reine
Anschauung, nie Referenz.

**Stufe 2 (offen):** derselbe Karten-Satz mit Zahlen — ein
Admin-Compute-Endpunkt reused `tools/wordbench/metric.py::
score_word_segments` + die Provenance-Attribution aus
`compose_word(..., provenance=True)` für Scores **pro Buchstabe und pro
Übergang** (Konnektor-Heatmap wie in wordlab, Sortierung
schlechteste zuerst; memoisiert pro (Wort × Template-Stand),
Invalidierung am Pooled-Nib-Hook). Die Wordbench bleibt der
Schiedsrichter — der Admin-Score ist dieselbe Metrik als Anzeige,
Optimierungs-Läufe laufen weiter nur im eingefrorenen Bench-Loop.
Später schließt sich der Kreis zu R3: aus einer schlechten Paar-Karte
direkt in den Paar-Editor mit dem Vorlagen-Crop als Unterlage.

### R2 — Positions-Rückbau (vor R3, damit Paar-Keys einfach bleiben)

Heute schreibt der Admin eine autorisierte Form per Fan-out auf drei
identische Template-Zeilen (`a-initial`/`a-medial`/`a-final`); `position`
ist seit Vorschlag A nur noch Lehrtafel-Rolle. Rückbau:

- **Schema:** eine Template-Zeile pro `(style, glyph_key, variant)` mit
  Basis-Key ohne Positions-Suffix (`a` statt `a-medial`). Echte
  Allographen behalten eigene Keys (`longs`, `s-round`); `variant`
  bleibt für positionssanktionierte Formvarianten („A = A").
- **Shaping:** `core/shaping.py` + TS-Twin liefern die Wort-Position
  weiter im Slot — aber nur noch als **Render-Kontext** für
  `core/compose.py` (Wortanfangs-Anstrich bleibt, Level-Auslauf am
  Wortende bleibt; beides ist heute schon Compose-Verhalten, keine
  Template-Eigenschaft).
- **Migration:** Dedupe der Fan-out-Drillinge (Identitäts-Check der
  `raw_path`s; ein tatsächlich „aufgetrennter" Buchstabe würde als
  `variant` erhalten — Stand heute existiert keiner). `bboxes.glyph_key`
  und `quiz`-Locking werden auf Basis-Keys migriert. Der in
  Vorschlag D angedachte Rename `position` → `chart_role` entfällt
  durch den Rückbau ersatzlos.
- **Blast Radius (bewusst groß, einmalig):** `core/shaping.py` +
  `app/src/domain/shaping.ts` + `shaping_cases.json`-Fixture,
  `tests/fixtures/compose_golden.json.gz` (Regen mit neuen Keys),
  `expected_glyph_key`-Backstop und Upsert-Konflikt-Target in
  `api/routers/templates.py`, Migration (Constraint aus 0015 neu),
  Admin-Sidebar/Wizard (Fan-out- und Auftrennen-UI entfallen),
  Quiz-Lock-Helfer, `docs/reference/write-api.md`, CLAUDE.md ↔
  copilot-instructions. Kein sichtbarer Render-Unterschied — genau
  deshalb wird R2 als **eigene, mechanische PR** geschnitten, nie
  vermischt mit Form-Änderungen.

### R3 — Paar-Schicht (Vorschlag B, konkretisiert)

- **Schema:** eigene Tabelle `glyph_pairs` — `(style_id, left_key,
  right_key, variant)`, Geometrie als JSONB (gefittetes Paar:
  Centerlines/Anker beider Buchstaben + Verbindungszug + relative
  Platzierung), `provenance` (`harvested` mit Vorlagen-Referenz |
  `authored`), Freigabe-Flag. Basis-Keys aus R2.
- **Renderpfad:** `core/compose.py` fragt pro Nachbarpaar zuerst die
  freigegebene Paar-Zeile ab, sonst §4-Generator — Vorschlag Bs
  Auflösungsregel, unverändert. Vorrang im Wort: das Override definiert
  Verbindungszug + Relativplatzierung des rechten Buchstabens; bei zwei
  angrenzenden Overrides gewinnt links-nach-rechts (der Advance wird
  fortgeschrieben). Cache-Invalidierung von `/write/word` bei
  Paar-Schreibzugriffen wie bei Template-Writes.
- **Erstbefüllung geerntet:** Importer über pairlab §5b (M4-Fit der
  Abb.-20-Paare, dann Abb.-19-Vorkommen) — beginnend mit den
  Versal-Paaren (Du, Ju, Of, Wu; stärkste gemessene Kandidaten B→i,
  I→n, D→u). Kleinbuchstaben-Paare nur, wenn ein Paar nach R4 messbar
  über den Klassenregeln liegt.
- **Paar-Editor (Nutzer-Vorschlag Punkt 3):** beide Buchstaben-Crops
  nebeneinander, gegeneinander verschiebbar, Verbindungszug
  zeichnen/löschen, Weg nachziehen wie im Wizard — als **Prüf-,
  Korrektur- und Freigabe-Oberfläche** über geernteten Paaren;
  Freihand-Neuanlage nur für Paare ohne Vorlagen-Beleg, als `authored`
  gekennzeichnet und in der Wordbench nie Referenz.

### R4 — Platzierungs-Rest + O3-Neubewertung (Wordbench-Loop)

Advance-/Clearance-Kalibrierung gegen die gemessenen Soll-Verschiebungen
(P75 0,36 xh; akkumulierend in langen Wörtern) und Neubewertung des
A-seitigen d-Trims (O3) — mit dem dokumentierten Metrik-Vorbehalt aus dem
Übergangs-Befund (die Übergangs-Komponente bestraft Spannen-Ausdehnung
konstruktionsbedingt; eine Metrik-Anpassung geschieht **zwischen** Loops
mit Baseline-Vermerk in `qualitaetsmetrik.md`, nie während eines Laufs).

### R5 — Schräglagen-Klassenkorrektur

1. Slant-Messung (Schätzer aus §4) als Report-Spalte in
   `tools/wordbench` (nicht Headline).
2. Klassenbasierte Korrektur der Oberlängen-Schleifen-Achse im
   gebundenen Kontext (d zuerst, dann b/h/k prüfen) als
   Renderpfad-Regel im Keep/Discard-Loop — Template bleibt
   Chart-Messung.

## 6. Reihenfolge

R1 + R1b Stufe 1 (unabhängig, umgesetzt) → R2 (mechanische Schema-PR) →
R3 (Paar-Schicht auf Basis-Keys) · R1b Stufe 2 (Scores) sobald sinnvoll ·
parallel dazu R4/R5 als Wordbench-Loops (unabhängig von R2/R3, können
jederzeit laufen).

## 7. Verworfen (bindend für dieses Redesign)

- **Flächendeckendes manuelles Paar-Autoring** (~1 800 Paare): Wochen
  Autoring für Verbindungen, die der Generator laut Messung zu ~90 %
  richtig erzeugt; die Restfehler sind klassen-, nicht paarförmig.
- **Freihand-Zeichnung als Erstweg oder als Lernquelle des Generators:**
  trainiert auf die Autoren-Hand statt der Vorlagen-Hand und würde von
  der Wordbench gegen die Probe bestraft. Ernten (M4-Fit) vor Zeichnen;
  Freihand nur als gekennzeichneter Fallback ohne Vorlagen-Beleg.
- **Globaler Schräglagen-Offset oder Wort-Slant-Jitter:** die Mediane
  sind identisch (kein Offset), und stochastische Varianz bräche
  Determinismus, HTTP-Caching und das Golden-Fixture. Varianz-Sampling
  bleibt post-MVP (Animation/Styleanalyse); jetzt nur die gemessene
  klassenbasierte d-Schleifen-Korrektur.
- **Positions-Rückbau vermischt mit Form-Änderungen:** R2 ist
  byte-identisch im Render-Output zu schneiden (eigene PR), sonst ist
  jede Regression unattribuierbar — die E4-Lektion auf Schema-Ebene.

## 8. Reproduktion des Schräglagen-Befunds

Einmalige Messung (2026-07-17), Methode vollständig in §4 beschrieben:
Scher-Suche über die Otsu-binarisierten Wortcrops aus
`data/sources/suetterlin-1922/words.json` (Exclude-Rechtecke
weiß übermalt) bzw. über die gerasterten Centerlines der mit
`core/compose.py` komponierten Golden-Fixture-Wörter; Band-Messung
zusätzlich auf die Pixel zwischen `midband_y` und `baseline_y`
beschränkt. Die dauerhafte, wiederholbare Fassung entsteht in R5 als
Wordbench-Report-Spalte.
