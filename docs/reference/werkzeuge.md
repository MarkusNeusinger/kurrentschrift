# Werkzeuge — die Dev-Tools unter `tools/`

> **Status (2026-09-05): lebend.** Der Index über die Dev-Tools unter
> `tools/` — was es gibt, wie man es aufruft, und welche Invariante daran
> hängt. **Nicht** der Ablauf einer Mess-Runde: der steht in
> `/verify-trace` und nur dort.
>
> **Was gilt.** Drei Gattungen, streng getrennt. **Labs** zeigen
> (matplotlib-PNGs nach `temp/`, immer `uv run --extra viz`):
> [Inspektions-Labs](#die-drei-inspektions-labs-sehen-nicht-nur-messen).
> **Benches** messen gegen eingefrorene Referenzen:
> [Benches und Generator](#benches-und-generator-verweise) — glyphbench
> (Buchstabe) · wordbench (komponiertes Wort/Paar) · tracebench
> (Wortbahn). **Schreibende** gibt es genau drei:
> die [Ernte-Werkzeuge](#die-zwei-ernte-werkzeuge-vorlage--db-über-die-admin-api)
> (über die Admin-API), das
> [Lesart-Wörterbuch](#das-lesart-wörterbuch-toolslesarten) und die
> Eigenhand ([Erfassung](#die-eigenhand-erfassung-toolseigenhand) ·
> [Bahnen](#die-eigenhand-bahnen-toolseigenhand)); Labs und Benches
> schreiben **nie** in die DB, `--live` liest nur.
> Der [Archiv-Schnappschuss](#der-archiv-schnappschuss-toolsdbsnapshot)
> ist create-only, der
> [Changelog-Schnitt](#der-changelog-schnitt-toolschangelog), die
> [Teilen-Karte](#die-teilen-karte-toolsogcard) und die
> [Seiten-Icons](#die-seiten-icons-toolsfavicon) fassen nur den Arbeitsbaum
> an.
>
> **Zwei Invarianten, die nicht verhandelbar sind.** `core/`, `api/` und
> `alembic/` importieren **nie** `tools` (das API-Image liefert es nicht
> aus; gepinnt von `tests/test_imports.py`), und ein Bench ändert während
> eines Laufs weder Lineal noch Fixture-Wurzel.
>
> **Was offen ist.** Für Labs und Ernte gibt es keinen `/verify-*`-Loop,
> die Prüfung ist der Bench-Lauf und das Auge; einen Skill hat nur die
> Tintenfolger-Runde (`/verify-trace`). Die Methode und die Zahlen eines
> Laufs stehen nicht hier, sondern in
> [`qualitaetsmetrik.md`](qualitaetsmetrik.md) (Regeln) und
> [`messjournal.md`](messjournal.md) (Läufe).
>
> **Nachzieh-Anlass.** Jedes neue, umbenannte oder entfernte
> Werkzeug/Einstiegsskript unter `tools/` und jede geänderte CLI (Flags,
> Modulpfade, `viz`-Extra, `--live`).

Einstiegspunkt für die Entwickler-Werkzeuge, die bislang nur in den
Agenten-Guides (`CLAUDE.md`, `.github/copilot-instructions.md`)
dokumentiert waren. Die meisten Tools haben eine eigene README im jeweiligen
`tools/<name>/`-Verzeichnis mit allen Optionen; hier steht das Wesentliche.

Alle Labs rendern matplotlib-PNGs nach `temp/` (git-ignoriert; Pfad wird
ausgegeben). matplotlib ist das dev-only `viz`-Extra — Aufruf immer mit
`uv run --extra viz`. `--live` liest die Datenbank **nur lesend** (braucht
`DATABASE_URL`, `.env` wird automatisch geladen); Labs, Benches und
Generator schreiben nie in die DB. Einzige schreibende Gattung sind die
beiden **Ernte-Werkzeuge** weiter unten — und auch die schreiben nicht
selbst, sondern über die admin-gegateten Endpunkte, damit deren Validierung
greift.

Aus diesem Rahmen fallen zwei Familien: der **Urteils-Durchgang** (kein
`viz`-Extra, weil seine Ausgabe eine HTML-Seite statt eines
matplotlib-PNGs ist; kein `--live` — was er überhaupt liest, liest er über
die deployte Lese-API; geschrieben wird nichts) und die
**Eigenhand-Erfassung** weiter unten (kein `viz`-Extra — PDF und
HTML-Seite entstehen dependency-frei, Bildarbeit läuft über
Pillow/scikit-image aus den Runtime-Deps; keine DB in beiden Richtungen —
geschrieben werden ausschließlich lokale Dateien unter dem gitignorten
`data/samples/own-hand/`).

## Die drei Inspektions-Labs (sehen, nicht nur messen)

**`tools/glyphlab`** — Overlays der Ableitung EINES Buchstabens
(Crop · Skelett · Centerline · Ecken · gefüllte Silhouette), aus einer
Fixture oder live aus der DB. Annotiert jedes Panel mit seiner
Penalty-Kategorie: die Bench-Zahl sagt *wie viel*, das Overlay *warum*.

```bash
uv run --extra viz python -m tools.glyphlab <key> [--live] [--stages] [--style dots]
```

**`tools/wordlab`** — das Wort-Level-Pendant: zeichnet ein KOMPONIERTES
Wort (Platzierung + generierte Übergänge aus `core/shaping.py` +
`core/compose.py`) über seine Wordbench-Vorlage, mit Penalty-Callouts pro
Konnektor. `--sweep` variiert eine Compose-Konstante spaltenweise.

```bash
uv run --extra viz python -m tools.wordlab <id> [--set pairs] [--live] [--sweep core.compose.CONST=v1,v2]
    [--fixtures DIR] [--laufform KANDIDATEN.json]
```

`--fixtures` zeigt auf eine andere (z. B. gepatchte) Fixture-Root,
`--laufform` legt Kandidaten-Laufformen über die eingefrorenen — DIESELBE
Datei und dieselbe Ableitung wie `wordbench.run --laufform` (`aug29`), damit
das Overlay zeigt, was die Bench misst. Die Kandidaten-Karten der
Endblende-Arme (§14 LF5/LF6, beide verworfen) baut
`tools/laufform/endblend.py` aus einer Root (`--window`, `--chart-fallback
KEY`, `--full-blend`); `--window 0` kopiert die gespeicherten Zeilen
wörtlich, sodass eine reine Chart-Rückfall-Karte (K0-Arm) nichts anderes
bewegt.

**`tools/laufform/smoothrow.py`** — baut die Kandidaten-Karten des Arms
LF11 „glatte Zeile" (§14 `sep02`) aus den VORKOMMEN eines Harvests
(`--occurrences`, die `--occ-out`-Datei) plus den Tafelzeilen einer Root:
je Zug eine Projektion auf eine kubische B-Spline mit Knoten alle `--knots`
x-Höhen, Median über die Kontrollpunkte, zurück auf die Tafelanker
(`core.aggregate.spline_basis_median`). `--knots 0` ist der KONTROLL-Arm —
dieselben Vorkommen durch den heutigen Per-Anker-Median, damit die Glättung
von der Ableitungsdrift eines frischen Harvests unterscheidbar bleibt.
Ausgabe sind volle Fixture-Zeilen, die `wordbench.run --laufform`,
`wordlab --laufform` und `humanbench.wordarm --laufform` wörtlich nehmen;
je Zeile werden Glätte-Sensor, Sprung- und Kopf-Gate und die
Kopf-/Schwanz-Bewegung berichtet. Standardmäßig nennt die Karte genau die
Schlüssel, für die die Root schon eine Zeile hat (`--keys stored`) — eine
Karte mit zusätzlichen Zeilen komponierte einen anderen Buchstabensatz als
die Basis, gegen die sie gemessen wird. `--loop-window` schaltet die
Schleifen-Registrierung von LF13 davor (`--no-loop-scale` ist deren
Kontroll-Arm, Lage ohne Größe); 0 ist aus und liefert byte-gleich die
LF11/LF12-Zeilen. Kein DB-Write.

```bash
uv run python -m tools.laufform.harvest --path chain --sets words --min-n 1 \
    --jobs 4 --occ-out temp/lf11/occ.json
uv run python -m tools.laufform.smoothrow --occurrences temp/lf11/occ.json \
    --knots 0.16 --out temp/lf11/cand.json
```

**`tools/laufform/inventory.py`** — die Bestandsaufnahme der gespeicherten
Laufform-Zeilen gegen ihre Tafelformen (§14 LF7/LF8/LF9/LF10): je Zeile n, die
Sprung-Ratio (`core.laufform.anchor_spike_ratio` auf der ZEILE — das
Sprung-Gate) und die Kopf-Abweichung `head°` (`core.laufform.head_deviation`,
die Landerichtung des ersten Zugs gegen die Tafel — das Kopf-Gate) neben der
Natürlichkeits-Lücke und dem Glätte-Sensor `zig`
(`core.laufform.zigzag_rate`, Krümmungs-Umkehrungen je x-Höhe, neben der
Rate der eigenen Tafelzeile; §14 LF11) als Berichts-Spalten, dazu das
datengetriebene τ der
Sprung-Ratio (Maximum der Zeilen mit n ≥ 3, aufgerundet), das
Doktrin-τ des Kopf-Gates (15°) und die Zeilen über dem einen wie dem
anderen (Spalte `gates`). Seit LF10 dazu der Form-Abstand
(`core.laufform.form_distance`: je Anker der Abstand zur gerenderten
Mittellinie desselben Zugs der Gegenseite in Nib-Radien der Tafel, beide
Richtungen; Spalten `form` = schlechteres p90, `f-med`, `f-max`, `dir`), sein
datengetriebenes τ_form und die vorregistrierten Varianten im Fuß —
Berichts-Spalte, kein Gate im Schreibweg. `--laufform DATEI.json` misst
KANDIDATEN-Zeilen (Harvest-Draft-Format `{key: {anchors, n_occurrences}}`,
dieselbe Datei wie `wordbench.run --laufform`; in der Tabelle mit `*`, nie in
einem τ) über den Tafeln der Root; `--png` zeichnet ausgewählte Zeilen über
ihre Tafelform, die Anker ab dem eigenen p90 schwarz — auf der Seite, von der
die schlechtere Richtung misst (Zeile bei `row_to_chart`, Tafel bei
`chart_to_row`; im Panel-Titel als `Z→T`/`T→Z` genannt) — das Bild, das das
Wort-Lineal nie ansieht.

```bash
uv run python -m tools.laufform.inventory [--root DIR] [--json out.json]
uv run --extra viz python -m tools.laufform.inventory --png inventory.png --only K,t,E
uv run python -m tools.laufform.inventory --root temp/lf10-root/suetterlin/suetterlin-1922 --laufform drafts.json
```

Die Ernte (`tools/laufform/harvest.py --apply`) läuft seit LF7 gegen den
Boden des Endpunkts: ein Draft unter `LAUFFORM_MIN_OCCURRENCES` wird
abgewiesen, außer `--min-occurrences N` senkt ihn ausdrücklich für DIESEN
Lauf (die LF1-Autor-Aussage); Sprung-Gate und Kopf-Gate haben keinen
Override.

**`tools/pairlab`** — seziert EINEN Buchstaben-Übergang gegen seine echten
Vorkommen in den Vorlagen, jeder Buchstabe UNABHÄNGIG neu eingepasst:
trennt Konnektor-Form von Platzierungsfehler und misst, wie weit die echte
Feder Schwanz/Kopf der Glyphen für den Join umformt. Befund + Optionen in
[`../proposals/uebergaenge-befund.md`](../proposals/uebergaenge-befund.md).

```bash
uv run --extra viz python -m tools.pairlab re [longs,a] [--set words|pairs|all]
    [--expect-root <digest>]
```

**Datierter Hinweis 2026-09-04 — was die Übergänge-Sektion seither misst.**
Bis zum 2026-09-04 zeichnete `analyze.py::_generate_connector` den
Verbinder selbst nach: 22 Zeilen, die im Docstring behaupteten, „die
exakte Mathematik" des Produktions-Join-Blocks zu sein, zuletzt angefasst
am 2026-07-11 — während `core/compose.py::_connector_centerline` dreimal
umgebaut wurde (Audit-Befund 18). Seither ruft pairlab den
**Produktions-Verbinder selbst** auf: `prodconn.py` schneidet den Aufruf
mit, den `compose_word` für diese Naht macht, und spielt ihn an der
unabhängigen Platzierung erneut ab. In `tools/` steht damit keine Zeile
Join-Grammatik mehr; ein Umbau in `core/` erreicht pairlab beim nächsten
Lauf. **Zahlen, die sich dadurch verschieben:** `gen_chamfer`/`gen_px` der
Dissektion (89 von 248 Nähten wichen ab, Median 0,0562 xh, Majuskeln
1,0365; `gen_chamfer` im Median 0,0434 → 0,0392), die Overlays, die
`gen_chamfer`-Spalte eines künftigen `pairlab.harvest`-Laufs und die
`base_gen_*`-Spalten von `chainbench`. **Unberührt:** `core/`, der
Golden, die Headlines, `doff`/`dconn` — und der Init des Kettenfits, der
weiter den eingefrorenen Spiegel benutzt (per Docstring Initialisierung,
nie Ziel; ihn nachzuziehen wäre eine deklarierte Re-Baseline der Kette).
Belege: [`messjournal.md`](messjournal.md) §14 „Übergänge P-Spiegel
`sep04`", Parität gepinnt von `tests/test_pairlab_connector_parity.py`.

**`tools/pairlab/spanmeas.py`** — der Sensor `dspan`, die
ausdehnungs-normierte Formdistanz einer Naht: komponierter gegen
gemessenen Verbinder, aber nur über den GEMEINSAMEN Abschnitt (beide vom
gemeinsamen Ende auf `min(Bogenlänge)` zurückgeschnitten), dann
bogengleich abgetastet und start-ausgerichtet. Antwort auf den blinden
Fleck von `dconn`, das eine Regel, die die Grenze Buchstabe/Verbinder
verschiebt, als Formunterschied bucht (Rettungsweg 2 des #488-Negativs;
Pre-Reg und Abnahme: [`messjournal.md`](messjournal.md) §14 „Übergänge
S1"). Report-only, kein DB-Zugriff, `core/word_metric.py` und
`tools/wordbench/pairmeas.py` unberührt.

```bash
uv run python -m tools.pairlab.spanmeas --set words --expect-root <digest> --json temp/base.json
uv run python -m tools.pairlab.spanmeas --set words --expect-root <digest> --no-exit-trim --base temp/base.json
```

Um `pairlab` herum sind messende Einstiegsskripte gewachsen (keines
schreibt in DB oder Rendering): `chain.py`/`chainbench.py` — der
Kettenfit (ein durchgehender Schreibpfad statt unabhängiger Einzelfits)
und sein Stage-A-Vergleich gegen den unabhängigen Fit über dieselben
eingefrorenen Vorkommen; `gradlab.py` — zerlegt am gefundenen Optimum
den Gradienten in die sieben gewichteten Kräfte je freiem Anker
(Methode: [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §11);
`anchors.py` — der EINE geteilte Detektor für gestrandete Anker samt
Reparatur, den die Ernte nach dem Gate anwendet; `bindab.py` — der
A/B-Runner, der das vorregistrierte Binding-Term-Protokoll ausführt;
`peaklab.py` (`viz`-Extra) — kleines benanntes Arbeitsset inkl.
Kontrollwörtern, Ankerkette überm Skelett mit eingekreisten Ausreißern,
`--compare` für gefittet vs. repariert; `landmarks.py` — der EINE
geteilte Landmarken-Detektor (die echten Selbstkreuzungen einer
Duktus-Polylinie plus die Verzweigungspunkte des Skeletts, eine
mehrdeutige Zuordnung wird verweigert statt geraten); `landmarklab.py` —
das Kalibrier- und Wirkungs-Labor dazu (`--calibrate` liest
`e_geo / e_landmark` am Baseline-Optimum, der Wirkungslauf hält die
gefittete Kreuzungshöhe gegen das Tinten-Ziel) für den Landmarken-Term
`CHAIN_LANDMARK_WEIGHT`, Voreinstellung 0,0. Beide brauchen kein
`viz`-Extra und sind reine Messung — kein DB-, API-, `core/`- oder
Rendering-Zugriff.

## Die zwei Ernte-Werkzeuge (Vorlage → DB, über die Admin-API)

Beide lesen die eingefrorenen Wordbench-Fixtures, sezieren die echten
Vorkommen und schreiben das Ergebnis als **Entwürfe** durch die
admin-gegateten Endpunkte (`ADMIN_TOKEN` nötig). Ohne `--apply` entsteht nur
ein JSON-Report zum Nachsehen — die Freigabe bleibt Menschensache.

**`tools/laufform/harvest.py`** — die Laufform- und Vorkommens-Ernte
(PR #246, um die Vorkommens-Schicht erweitert in PR #250): M4-fittet jedes
Buchstaben-Vorkommen der Abb.-19-Wörter und schreibt drei Artefakte —
die per-Buchstabe-Mediane als Laufform-Varianten
(`PUT /sources/{id}/templates/{key}/laufform`, `variant=100`), jeden
sauberen Einzelfit als `instances`-Zeile und je Vorlage eine nachgefahrene
Wortspur als `word_instances`-Zeile (`authored`-Zeilen bleiben unangetastet).
Die `hands`-Zeile der schreibenden Hand entsteht dabei im selben Request:
die admin-gegateten Batch-`PUT`s des `instances`-Routers legen sie an,
falls sie fehlt (get-or-create), und verweigern eine Id, die bereits
unter einem anderen Stil registriert ist — eine Hand entsteht also durch
eine Ernte-Schreibung, nicht durch eine Migration oder einen manuellen
Schritt (→ [`../proposals/handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md) H1).
Die Laufform-Zeilen wirken **sofort** auf jedes fließende `/write/word` —
gegen Prod nur mit ausdrücklicher Freigabe.

**Die Ernte seedet aus dem Chart** (`--chain-seed`, Default `chart` seit
dem Autor-Entscheid **A38** vom 2026-09-07, §14 „Laufform LF16"). Der
Kettenlauf setzt auf einer Komposition OHNE Laufform-Zeilen auf, also auf
dem Duktus-Prior, den keine Ernte schreibt — damit ist die Ernte eine
Abbildung von Tinte und Prior allein, und ihr zweiter Durchlauf
reproduziert die eigene Karte byte-gleich, Vorkommen eingeschlossen.
`--chain-seed composed` bleibt erreichbar und ist, was jede Runde vor
`sep06` benutzt hat.

**Warum das ein eigener Default ist** (gemessen `sep06`, §14 „Laufform
LF14" und „Laufform LF15"): `derive_word` komponiert das Wort AUS den
Laufform-Zeilen, und `chain_seed="composed"` startet den Kettenlöser auf
dieser Komposition — die Ernte liest also die Zeilen, die sie ersetzen
wird. Das war nie eine Nichtreproduzierbarkeit (`--jobs 1` und `--jobs 4`
sind byte-gleich, und derselbe Befehl zweimal gibt dieselbe Karte),
sondern eine Rückkopplung, und sie klang nicht ab: die Iteration
`H0 → H1 → H2 → H3` bewegte in JEDEM Schritt Zeilen um 0,005–0,063 xh,
und die Zahl der angenommenen Vorkommen wanderte 235 → 232 → 239 mit.
Der Preis der Chart-Saat steht in LF15/LF16 und ist nicht null (`sep07`:
227 statt 234 angenommene Vorkommen, an `connector_degenerate`, nicht an
der Fitgüte).

**Der Trace-Bench und der Folger behalten `composed`** (`tracebench
--chain-seed`, `pairlab.follow --chain-seed`): deren `chain`-Kandidat ist
die eingefrorene Basis jedes gemessenen Arms, und eine Basis, die unter
der Route wegrutscht, macht jedes gespeicherte Delta unlesbar. Nur die
ERNTE hat den Default geflippt.

**Die Selbstprüfung vor jedem Laufform-Write: zweimal ernten.** Sie steht
seit LF15 und ist nicht gestrichen, sondern hat ihren Anlass verloren:
mit der Chart-Saat MUSS der zweite Lauf byte-gleich sein, und jede
Abweichung ist ab `sep07` ein Befund (ein Werkzeug hat sich bewegt) statt
einer Iteration. Deshalb bleibt sie ein Schritt, und zwar derselbe:

```bash
uv run python -m tools.laufform.harvest --path chain --sets words --min-n 1 \
    --jobs 4 --expect-root <digest> --occ-out temp/lf/occ-1.json
uv run python -m tools.laufform.smoothrow --occurrences temp/lf/occ-1.json \
    --knots 0 --floor 1 --keep-stored --out temp/lf/karte-1.json
# …und dieselbe Ernte noch einmal, jetzt auf der eigenen Karte:
uv run python -m tools.laufform.harvest --path chain --sets words --min-n 1 \
    --jobs 4 --expect-root <digest> --laufform temp/lf/karte-1.json \
    --occ-out temp/lf/occ-2.json
uv run python -m tools.laufform.smoothrow --occurrences temp/lf/occ-2.json \
    --knots 0 --floor 1 --keep-stored --out temp/lf/karte-2.json
cmp temp/lf/karte-1.json temp/lf/karte-2.json && cmp temp/lf/occ-1.json temp/lf/occ-2.json
```

Beide `cmp` gehören still zu bleiben — Karte UND Vorkommensdatei. Sind sie
es nicht, ist etwas anderes gewandert als die Zeilen; bewegt sich eine
Zeile um mehr als 0,002 xh, ist die Karte kein Fixpunkt, und die Differenz
gegen den Bestand gehört zum Teil dieser Bewegung und nicht dem gemessenen
Arm.
`--laufform` nimmt dieselbe Datei wie `wordbench.run --laufform`
(Overlay, die eingefrorene Wurzel bleibt unberührt), `--expect-root`
nennt und prüft die Basis wie jeder Bench — die Ernte ist das Werkzeug,
dessen Ausgabe ein Write in die Produktion stellt, also nennt sie ihre
Wurzel. Die zweite stehende Vergleichsgröße bleibt die **Kontrollkarte**
aus demselben Lauf mit `--chain-seed composed`: eine Karte gegen den
Bestand allein zu halten sagt nicht, wie viel davon der gemessene Arm
ist.

`--loop-aware-repair` ist der andere `sep06`-Arm (Default aus, verworfen
an zwei Gates): die Nachreparatur gestrandeter Anker lässt die Anker in
Ruhe, die innerhalb einer Schleife der Chart-Zeile liegen.

**Welcher Folger die Bahn legt** (`--follower`, Vorgabe `tintenpfad` seit
dem Autor-Entscheid **A45** vom 2026-09-12, §14 „Tintenpfad-Adoption
`sep12`"): die gespeicherte Wortspur kommt aus der Strang-Dekodierung
(`tools/pairlab/tintenpfad`), und die Buchstabengrenzen der Dekodierung
(`letter_spans`) stehen im Wort-Record daneben. Der Record nennt den
Folger, der seine Striche gelegt hat, in `measurements.follower` UND in
`measurements.fit_path` — sonst läse ein Verbraucher, der nur das Feld
kennt, die Bahn des Dekoders als Ketten-Fit; die VORKOMMEN behalten ihr
eigenes `fit_path: "chain"`, sie kommen weiter von dort.
`--follower chain` ist der Stand davor, byte für byte. **Der Schalter bewegt nur, was die Ernte
ZEIGT:** Vorkommen, Mediane und jedes Gate werden weiter am
Buchstabenfit abgelesen. Dasselbe Muster wie K-A/K-B/A1. Ein Wort, das der
Tintenpfad nicht dekodiert, fällt auf den Fit zurück — ein Urteil je Wort,
kein Abbruch.
**Ein `--apply`-Lauf muss den Folger ausdrücklich nennen** (und davor einen
`dbsnapshot` nehmen): `--apply` schreibt die gespeicherten Bahnen, und ein
bewegter Default darf keine geänderte Bahn in die Produktion tragen.

**Woher die Anker eines VORKOMMENS kommen** (`--occurrences`, Vorgabe
`fit`): `tintenpfad` liest sie über die **Saat-Korrespondenz**
(`tools/laufform/saatkorrespondenz.py`) von der dekodierten Bahn ab —
jeder Bahn-Zustand kennt seine Saat-Probe, jede Saat-Probe ihre Stelle im
komponierten Buchstaben, und der komponierte Buchstabe ist eine Abtastung
der Tafelzeilen-Anker. Nichts wird über die Bogenlänge verteilt; die
Stelle im komponierten Buchstaben wird BEWIESEN (affine Scheiben-Identität
je Punkt, Rest < 1e-6). Ein Anker ohne Beweis oder ohne Saat auf der Tinte
ist ungedeckt, und ein Slot mit einem ungedeckten Anker fällt als
`tintenpfad_gap` heraus statt halb gemessen zu werden; `corr_covered` /
`corr_total` im `--diag-csv` zerlegen jeden solchen Ausfall. Der Dekode
läuft auf der `--chain-seed`-Komposition, mit der Chart-Saat also
zeilenunabhängig wie der Kettenfit. **Messarm, nicht schreibbar:**
`--apply` verweigert ihn (A48, §14 „Laufform A48 `sep13`" — dort auch, was
die Abdeckung kostet).

```bash
uv run python -m tools.laufform.harvest [--style suetterlin] [--min-n 4]
    [--rmse-max 2.2] [--loop-aware-repair]
    [--follower tintenpfad|chain]        # default tintenpfad (A45)
    [--occurrences fit|tintenpfad]       # default fit (A48-Messarm)
    [--chain-seed chart|composed|grid]   # default chart (A38)
    [--laufform karte.json] [--expect-root <digest>]
    [--apply --base-url http://localhost:8000 --source-id <id>]
```

**`tools/pairlab/harvest.py`** — die Erstbefüllung der Paar-Schicht
(Redesign R3, PR #220; `--store-occurrences` seit PR #250): leitet aus jeder
sezierten Paar-Vorlage eine `PairGeometry` ab (Offset aus den beiden
starren Einzelfits, Konnektor aus dem echten Verbindungsstrich) und legt sie
als **nicht freigegebene** `glyph_pairs`-Entwürfe mit `provenance:
harvested` + Specimen-Beleg ab; `--approve left:right` gibt nur gemessene
Gewinner frei, `--store-occurrences` schreibt zusätzlich die
`pair_instances`. Freigabe sonst im Paar-Editor unter `/admin/uebergaenge`.

```bash
uv run python -m tools.pairlab.harvest [--style suetterlin] [--sets pairs]
    [--ids Bi,Du] [--apply] [--store-occurrences] [--approve B:i,D:u]
```

## Der Urteils-Durchgang (was keine Kennzahl sieht)

Eigene Gattung, weil weder „Lab“ noch „Bench“ trägt: Ein Lab zeigt EINE
Ableitung im Detail, damit ein Mensch sie versteht; ein Bench misst mit einer
Kennzahl gegen eine eingefrorene Referenz. Hier ist der Messfühler selbst der
**Mensch**, und die Frage lautet nicht „wie viel Abweichung?“, sondern
„welche Fehlerart sieht welche Kennzahl überhaupt?“. Das Werkzeug steht damit
*neben* den Benches statt unter ihnen: Es erzeugt nicht eine weitere Zahl,
sondern die Urteile, gegen die eine Zahl gehalten wird.

**`tools/humanbench`** — der blinde Bewertungsdurchgang über die
gespeicherten Fits, in drei Schritten und drei Modulen. `build.py` zieht die
Stichprobe einer Runde und schreibt Payload, Schlüssel, **schmalen
Schlüssel**, Rückhaltemenge und Provenienz-Stempel (geschichtet nach Schwere,
**innerhalb** der Bänder gemischt, mit blinden Wiederholungen als
Verlässlichkeitsschranke; `--only` beschränkt eine Runde auf die
Rückhaltemenge einer früheren).
`page.py` rendert daraus EINE in sich geschlossene HTML-Seite — Crops als
`data:`-URIs, Stil und Skript inline, kein Font, kein CDN, kein Netzzugriff;
der Modus folgt dem Payload statt einem Flag: ein Panel je Bild ergibt den
Kategorien-Durchgang, zwei den paarigen Vorher/Nachher-Vergleich, dessen
Seitenzuordnung nur im Schlüssel steht. `analyse.py` wertet den emittierten
Ergebnistext in der Reihenfolge aus, die der vorregistrierte Plan **vor** den
Labels festgelegt hat. Verfahren, Fehler-Taxonomie und Aufbewahrungsregeln
stehen in [`menschliche-bewertung.md`](menschliche-bewertung.md), die Befunde
einer Runde in [`messjournal.md`](messjournal.md).

Seit 2026-09-02 kommt ein dritter Modus dazu, die **Wortrunde auf der
Echtheitsfrage** (`--word-arms BASIS KANDIDAT`,
[`menschliche-bewertung.md`](menschliche-bewertung.md) §8a): ein ganzes
Specimen-Wort aus einer eingefrorenen Wordbench-Wurzel, darüber zwei
Kompositionen **als Tinte** — der einzige Aufbau, in dem Zickzack,
Strichstärke und Naht-Knick überhaupt sichtbar sind. `wordarm.py` ist der
Referenz-Erzeuger der beiden Arme (`--laufform` für eine Kandidatenkarte,
`--nib` für einen anderen Federmodus, `--apex-handover`/`--stem-depart` für
die beiden Übergangsregeln der Klassenregel J5, `--no-exit-trim` für die
pre-adoption Basis des J4-Trims, `--seam-negotiation` (J6, die
Nahtverhandlung, mit `--seam-negotiation-max-jump` für die J6b-Verengung, die
ein Runden-Ergebnis lizenzieren kann), `--registration-from` zum
Pinnen der Platzierung); er komponiert per Import wie `tools/wordbench/run.py`
und platziert mit demselben Lineal. Jede Armdatei schreibt ihre
`join_rules` in die Einstellungen — eine Runde erbt nie stillschweigend
einen Default.

`tracearm.py` ist der zweite Erzeuger, für Runden, deren Kandidat eine
**gefolgte Bahn** ist statt einer Komposition (`sep07`, Runde 9 zur
K-E-Claim-Trennung): er nimmt eine `tools.tracebench`-Kandidatendatei —
typisch das `--candidate-out` des Tintenfolgers — und legt sie in den Rahmen
des eingefrorenen Fixture-Eintrags; er komponiert nichts und misst nichts.
Eine solche Runde läuft auf der GENAUIGKEITS-Frage (`--question ink`) und in
der Mittellinien-Anzeige der Buchstabenrunden — beides stellt sich von selbst
ein, weil ein Bahn-Arm weder Silhouetten noch Strichbreiten trägt und die
Seite daran ihre Darstellung abliest
([`menschliche-bewertung.md`](menschliche-bewertung.md) §8a, „Ein Arm kann
auch eine BAHN sein“).

Zwei Konstruktions-Hinweise aus der J5-Runde, damit die nächste sie nicht
neu lernt: eine **blinde Wiederholung** braucht mehr als
`--min-repeat-gap` + 25 Bildschirme (im Wortmodus-Default 15 also mehr als
40), eine Runde von zehn Wörtern kann also gar keine tragen; und
**Nullproben** — Wörter, die der Kandidat gar nicht
berührt, deren beide Tafeln also bit-identisch sind — kosten wenig, heben
die Runde über diesen Boden und messen nebenbei, wie der Richter „kein
Unterschied" überhaupt benutzt: genau die Größe, an der das LF11-Verdikt
hing.

Geschrieben wird nirgends — weder in die Datenbank noch über die API.
`page.py` und `analyse.py` sehen beides überhaupt nicht: Die Seite ist ein
reiner Renderer, die Auswertung liest nur Dateien. Einzig `build.py` greift
nach außen, und auch nur lesend — die Vorkommen aus Dateien oder, ohne
Datei, per GET über die deployte Lese-API. Payload, voller Schlüssel und
jede Kennzahlentabelle je Vorkommen sind Vorkommens-Geometrie und bleiben
unter `temp/humanbench/runde-<n>/` (git-ignoriert); committet wird die
menschliche Hälfte unter `data/humanbench/` — Urteilstext, schmaler
Schlüssel (uid → Glyph, Wort, Slot), Stempel, `SOURCE.md`
([`quellen-und-rechte.md`](quellen-und-rechte.md) §5).

```bash
uv run python -m tools.humanbench.build --round 2 --n-label 150 --repeats 12
uv run python -m tools.humanbench.build --round 3 \
    --paired temp/fits-alt.json temp/fits-neu.json

# Wortrunde: zwei Arme erzeugen, bauen, mit der Echtheitsfrage rendern
uv run python -m tools.humanbench.wordarm --arm Basis --out temp/basis.json
uv run python -m tools.humanbench.wordarm --arm LF11 --laufform temp/lf11-karte.json \
    --registration-from temp/basis.json --out temp/lf11.json
# … oder ein Übergangsregel-Arm gegen dieselbe Basis (J5)
uv run python -m tools.humanbench.wordarm --arm J5 --apex-handover --stem-depart \
    --registration-from temp/basis.json --out temp/j5.json
uv run python -m tools.humanbench.build --round 5 \
    --word-arms temp/basis.json temp/lf11.json --strata temp/klassen.json
uv run python -m tools.humanbench.page --question authentic \
    --payload temp/humanbench/runde-5/payload.json \
    --out temp/humanbench/runde-5/echtheit.html --round 5

# … oder zwei gefolgte BAHNEN statt zweier Kompositionen (Genauigkeitsfrage)
uv run python -m tools.humanbench.tracearm --arm Basis \
    --candidate temp/base-cand.json --out temp/basis-bahn.json
uv run python -m tools.humanbench.tracearm --arm K-E2 \
    --candidate temp/ke2-cand.json --out temp/ke2-bahn.json
uv run python -m tools.humanbench.build --round 9 \
    --word-arms temp/basis-bahn.json temp/ke2-bahn.json --strata temp/klassen.json
# … und wenn das ganze Wort den Unterschied nicht trägt: der AUSSCHNITT um die
# größte Arm-Trennung, gezoomt (Konstruktionsregel §8a/§3.4a — eigene Anzeige,
# eigene Runde, Zahlen NICHT mit einer Wortrunde vergleichbar)
uv run python -m tools.humanbench.build --round 11 \
    --word-arms temp/basis-bahn.json temp/kg-bahn.json --strata temp/klassen.json \
    --window-xh 1.5 --zoom 4
# die Frage kommt aus den ARMEN, nicht von der Kommandozeile: VERGLEICH statt ECHTHEIT
uv run python -m tools.humanbench.page \
    --payload temp/humanbench/runde-9/payload.json \
    --out temp/humanbench/runde-9/vergleich.html

uv run python -m tools.humanbench.page \
    --payload temp/humanbench/runde-2/payload.json \
    --out temp/humanbench/runde-2/befund.html --round 2

uv run python -m tools.humanbench.analyse \
    --result temp/humanbench/runde-2/urteile.txt \
    --key temp/humanbench/runde-2/key.json \
    --rows temp/humanbench/runde-2/rows.json \
    [--spots temp/humanbench/runde-2/spots.json] [--gate 'spike>=8.0:A']
    [--union W,B] [--drop-unsure] [--json auswertung.json]
```

`--rows`/`--spots` sind Vorkommens-Statistik und liegen deshalb außerhalb des
Repos; ohne sie laufen Verlässlichkeit, Besetzung, Drift und die Notizen
vollständig, und die Auswertung sagt, welche Schritte sie auslassen musste —
über dem committeten Bestand also direkt nachrechenbar:

```bash
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-01-urteile.txt \
    --key    data/humanbench/runde-01-vorkommen.json
```

**`tools/eigenhand/tintentreue_calibration.py`** — der vierte Modus, und das
einzige Geschwister außerhalb von `tools/humanbench`: der
**Kalibrier-Durchgang** über die Wortkästen EINER Hand, der die geborgten
Schwellen der → Tintentreue durch gemessene ersetzt (Autor-Entscheid Q10 b,
einmal je Hand). Er wohnt hier, weil er die reservierten Eigenhand-Pixel
liest — ausschließlich über die admin-gegatete API, nie über die Datenbank —
und nicht aus einer eingefrorenen Fixture-Wurzel schneidet wie
`humanbench.build`; geteilt wird nur die SEITE (`page.py`, Kategoriensatz
`STRIP_CATEGORIES`: drei Stufen plus vier Merkmale statt sechs
Fit-Kategorien). `build` zieht nach der VORLÄUFIGEN Stufe geschichtet,
blendet alles Ungemessene aus, legt blinde Wiederholungen über die Stufen und
schreibt Payload, Schlüssel, Rückhaltemenge, Stempel und die Seite;
`analyse` rechnet den Ergebnistext in der vorregistrierten Reihenfolge durch
(Verlässlichkeit zuerst, dann Besetzung, Ampel gegen Mensch, Quantil-Schnitt)
und DRUCKT einen `Schwellen(…)`-Block — übernommen wird er vom Autor, nie vom
Werkzeug. Verfahren: [`menschliche-bewertung.md`](menschliche-bewertung.md)
§8b, Vorregistrierung: [`messjournal.md`](messjournal.md) §14
„Tintentreue-Kalibrierung `sep20`".

**Die Seite dieser Runde wird nie veröffentlicht** — anders als eine
humanbench-Seite: ihre Ausschnitte sind die eigene Handschrift und damit der
reservierte Datensatz. Sie wird lokal geöffnet und bleibt unter `temp/`.

```bash
ADMIN_TOKEN=… uv run python -m tools.eigenhand.tintentreue_calibration build \
    --hand mn-suetterlin --round 1 [--n-label 30] [--repeats 8] [--only reserve.json]

uv run python -m tools.eigenhand.tintentreue_calibration analyse \
    --round-dir temp/tintentreue-kalibrierung/r1 --result urteile.txt
```

**`tools/fitview`** — der Betrachter über die BEURTEILTEN Screens:
fittet die im Urteils-Durchgang bewerteten Vorkommen live neu und
zeichnet Vorher/Nachher im SELBEN Fenster-Pad/4×-Zoom-Rahmen, in dem
geurteilt wurde, die Owner-Markierungen als Kreuze — eine in sich
geschlossene HTML-Seite, kein `viz`-Extra. Die Minuten-Schleife, um eine
Reparatur gegen die schon bezahlten menschlichen Urteile zu halten, ohne
eine neue Runde zu ziehen.

```bash
uv run python -m tools.fitview [--round 02|all] [--category A|AW] [--limit 40]
```

## Der Archiv-Schnappschuss (`tools/dbsnapshot`)

Wieder eine eigene Gattung: nicht messen, sondern sichern. `fetch.py`
zieht über die deployte Lese-API (`ADMIN_TOKEN`) einen Schnappschuss
dessen, was keine Neuberechnung zurückbringt — `bboxes` und
`templates.raw_path` —, prüft die Plausibilität gegen das vorige
Manifest (ein Lauf, der WENIGER Zeilen ablegen würde, schlägt ohne
`--allow-shrink` fehl) und legt ihn als neues, zeitgestempeltes
Verzeichnis im PRIVATEN Archiv-Klon außerhalb des Arbeitsbaums ab
(`--archive` bzw. `KURRENTSCHRIFT_ARCHIVE`; ohne ihn bleibt er im
Staging unter `--out`). Frei anlegen — und Pflicht vor allem, was
Geometrie überschreiben kann (`apply-laufform`, Migrationen mit DROP,
Ernte mit `replace`) sowie nach einer Autoring-Sitzung; nie in ein
bestehendes Verzeichnis schreiben, nie eines löschen oder umbenennen
(Regeln: `CLAUDE.md` § „Working guardrails").
Die `eigenhand_*`-Tabellen fahren OHNE die PNG-Spalte mit, dazu ein
`strip_hashes`-Manifest: der Master der Streifenbilder ist der
`own-hand/`-Baum desselben Archivs, und die Hashes sind, woran ein
Restore sie prüft — und woran auffällt, wenn DB und Archiv
auseinandergelaufen sind, bevor der Tag kommt, an dem es zählt
(Wiederherstellungsweg: proposals/eigenhand-erfassung.md §8.1). Die Spalte
`eigenhand_strips.pfade` trägt er ebenfalls nicht — seit dem 2026-09-20
steht das ausdrücklich in den `known_gaps` des Manifests, samt Ort des
Masters: ein GEFOLGTER Pfad wird durch einen neuen `pfad`-Lauf gemacht,
eine von Hand nachgefahrene Bahn liegt im `own-hand/`-Baum in der
`kartei.json` (`pull --pfade` → `sync --from`). Ein Leser des Manifests
soll den Schnappschuss nicht für vollständiger halten, als er ist.
`restore.py` ist für Drills gegen eine Wegwerf-Postgres gebaut: verlangt
die Ziel-URL explizit (`--database-url`, absichtlich nie aus der
Umgebung), verweigert ein Ziel gleich `DATABASE_URL`, verweigert ein
besetztes Ziel ohne `--replace` und schreibt ohne `--apply` nichts —
ein Restore Richtung Prod ist prod-berührend und braucht die
ausdrückliche Freigabe des Autors in derselben Sitzung.

```bash
uv run python -m tools.dbsnapshot.fetch [--archive <privater-klon>] [--push]
uv run python -m tools.dbsnapshot.restore <snapshot-dir> --database-url postgresql://… [--apply] [--replace]
```

## Die Eigenhand-Erfassung (`tools/eigenhand`)

Die Werkzeugkette, mit der der Autor seine eigene Hand als Trainingsdaten
erfasst — Konzept, Begriffe und Doktrin in
[`proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md),
Betrieb in `data/samples/own-hand/README.md`. Jedes Modul ist ein eigener
CLI-Einstieg (`uv run python -m tools.eigenhand.<modul>`), Humanbench-Stil:

- **`universe`** — baut den lokalen Übergangsraum (Soll-Gewichte) aus den
  Konsultationskorpora unter `data/corpora/frequencywords-2018/` (vorher
  deren `fetch_frequencywords.py` laufen lassen; Bytes bleiben gitignored).
  **`--push`** schiebt die Tabelle danach als vollständiges Soll-Universum
  (∪ Pool-Items zu 0, mit Provenienz) über `PUT /eigenhand/uebergangsraum`
  in die geteilte DB (Proposal §7.1; `--push-only` schiebt die vorhandene
  lokale Datei ohne Neubau, `--dry-run` zeigt nur die Kennzahlen);
  idempotent per Prüfsumme, ein anderer Bau ersetzt die Zeile — deshalb
  vorher `tools.dbsnapshot.fetch`. Braucht `ADMIN_TOKEN`.
- **`pool`** — baut/erweitert den committeten Streifenplan
  (`core/eigenhand/streifen.json`), deterministisch und append-never;
  **`pool pin`** hängt die angehefteten Wörter (`corpus.PINNED_FIRST`)
  als eigene Streifen an und stellt sie über den Planblock `pins` an die
  Spitze der Reihenfolge — der Weg, ein Wort in einen bereits
  eingefrorenen Plan zu bekommen (Proposal §4; `--word` für einen
  einmaligen Pin). In `PINNED_FIRST` stehen neben den eigens dafür
  kuratierten Wörtern die **Referenzwörter** (`corpus.REFERENCE_WORDS`:
  die drei §9-Wörter `lesen` · `das` · `denen` + die Worttexte des
  Entwicklungssatzes dev-19), die aus
  anderen Kurationsschichten stammen; ein Wort, das der Plan schon
  trägt, wird gemeldet und übersprungen, nicht ein zweites Mal
  eingeplant. **`pool everyday`** hängt den **Grundwortschatz**
  (`corpus.EVERYDAY_WORDS`) als gepackte Welle an und trägt sie in den
  Planblock `everyday` ein — der sich in der Reihenfolge mit den
  eingefrorenen Streifen **verschränkt** statt sie anzuführen
  (Proposal §4). Der Lauf ist rein lokal — Kuration lesen, `streifen.json`
  schreiben, kein Netz und keine DB —, aber er ändert eine committete
  Datei: er gehört in einen PR, nicht in eine Sitzung, und „Bögen
  erzeugen" kennt die neuen Wörter erst nach dem Deploy;
  **`gaps`** listet unerreichbare Übergänge samt echter
  Trägerwort-Kandidaten für die nächste Kurationsrunde in `corpus.py`.
- **`sheet`** — druckt einen Bogen (PDF + `layout.json`-Sidecar) aus der
  Warteschlange (Redo > nie belegt > gewichteter Wiederholungs-Gewinn);
  `--repeat N` für Mehrfach-Versuche, `--strips` für gezielte Streifen.
  Die Auswahl-, Layout- und PDF-Rechnung selbst liegt in
  `core/eigenhand/bogen.py`, weil die Werkbank dieselben Bögen druckt.
- **`setup`** — erklärt das stehende Setup einer Hand (Feder, Tinte,
  Papier, Aufnahmegerät) EINMAL: schreibt den Serverdatensatz und legt
  eine lokale Kopie (`setup.json`) daneben, aus der `ingest` seine
  Vorgaben liest. `--pull` holt es auf einen anderen Rechner, `--show`
  zeigt die lokale Kopie ohne Netz. Vor der ersten Sitzung ausführen —
  danach eingelesene Fassungen tragen sonst keine Feder/Tinte/Papier.
- **`sync` ↔ `pull`** — die Brücke zur Werkbank-Ansicht (Proposal §7.1,
  §7.2): `sync` schiebt die lokale Buchführung (Bögen samt Layout,
  Fassungen samt Verdikt und effektivem Setup) über die admin-gesicherte
  HTTP-Schnittstelle hoch; **`--mit-streifen`** nimmt zusätzlich die
  Streifenbilder mit (opt-in — reservierter Datensatz, und schon
  gespeicherte Bytes werden per SHA256 übersprungen). Fehlt zu einer
  angenommenen Fassung die Datei, wird erst alles Vorhandene hochgeschoben
  und der Lauf dann mit Namen der Fehlstellen abgebrochen: ein stiller
  Übersprung würde gerade auf dem Wiederherstellungsweg Erfolg melden und
  Streifen weglassen. `pull --sheet B0007`
  holt einen im Admin gedruckten Bogen (Layout + PDF) auf die Platte,
  damit `ingest` dagegen registrieren kann; **`pull --flecken`** holt die
  Gegenrichtung: die im Admin von Hand korrigierten **Fleckenmasken**
  zurück in Kartei und `meta.json`, damit der nächste Schnappschuss sie
  trägt (§7.4 — die Maske ist das einzige Feld der Kette, dessen Master der
  Server ist; `sync` füllt oben nur, was noch keine hat, und überschreibt
  nie eine). **`pull --pfade`** holt das einzige Datum, das GANZ oben
  entsteht: die in der Werkbank von Hand **nachgefahrenen Bahnen**
  (`verfahren: authored`) einer Hand — ein Lesen je gespeicherter Fassung,
  abgelegt als Satz in der zentralen `kartei.json` und nirgends sonst
  (Autor-Entscheid A vom 2026-09-20: die Kartei fährt in jedem
  Schnappschuss VOLL mit, ein abgelegtes Fassungs-Verzeichnis ist eine
  unveränderliche Kopiereinheit und würde eine nachträglich hineingelegte
  Datei still überspringen). Gefolgte Pfade bleiben oben — sie sind
  ableitbar. Der Satz trägt ZWEI Versionen: `format` (die Form der
  Kartei-Zeile) und `pfad_format` (das Streifen-Pfad-Format, unter dem die
  ZEILE geantwortet wurde — `eigenhand_strips.pfade_format`, Migration
  `0032`, nicht die Konstante des laufenden Abbilds, zwei Fassungen einer
  Hand dürfen also verschieden sein); ein Satz in unbekannter Form wird
  verweigert, nie als
  „keine Bahn" gelesen — unbekannt heißt NEUER, nie älter, denn eine
  archivierte Kartei wird nie umgeschrieben. Eine Fassung, die dieser Rechner nicht kennt,
  beendet den Lauf laut, statt still übersprungen zu werden. Alle drei
  brauchen `ADMIN_TOKEN`; `--api` zeigt auf eine andere Instanz.
  **`sync --from <Archiv-Snapshot>`** ist der Wiederherstellungsweg: dieselbe
  Push-Logik, nur aus dem Archiv statt aus der Arbeitskopie — damit bringt
  Repo + Archiv die vier hand-gebundenen `eigenhand_*`-Tabellen samt Bildern
  zurück (Rezept und Drill: Proposal §8.1); die fünfte, das Soll-Universum,
  kommt aus ihrer eigenen Quelle (`universe --push`). Genannt wird IRGENDEIN Schnappschuss der Hand;
  seine Geschwister im selben Verzeichnis kommen automatisch dazu (neuester
  gewinnt), weil `snapshot.py` inkrementell ablegt und nur der erste
  Schnappschuss vollständig ist. Die **Kartei** kommt dabei immer aus dem
  NEUESTEN Schnappschuss der Hand, gleich welcher genannt wurde, und der Lauf
  sagt, aus welchem: jeder Schnappschuss trägt eine vollständige Kartei, ein
  älterer also einen vollständigen FRÜHEREN Stand — und eine Bahn, die seit
  dem Entscheid A nur noch dort wohnt, wäre sonst still weg. Das stehende Setup wird dabei nur gesetzt,
  wenn der Server keines hat, und der Lauf bricht mit Namen ab, wenn eine
  angenommene Fassung oder ein Bogen-Layout im Archiv fehlt.
  **Nur `--from` stellt auch die nachgefahrenen Bahnen wieder her** (seit
  2026-09-20): der gewöhnliche `sync` schiebt keine hoch, sonst stünde eine
  bewusst aufgegebene Zeichnung beim nächsten Lauf wieder da. Gefüllt werden
  nur Kästen, für die der Server KEINEN Pfad hat; ein Kasten, der schon einen
  trägt, bleibt unangetastet und wird benannt — das Archiv ist Herr über das
  Fehlende, nie über das Lebende (dieselbe Regel wie beim stehenden Setup:
  eine seither in der Werkbank korrigierte Zeichnung oder ein bewusst
  übergebener Kasten würde sonst still zurückgedreht). Der Push
  mischt je Fassung um die Kästen herum, die der Server schon trägt, und
  der Lauf schließt mit der Zeile „`k` restored, `m` already there, `n` NOT
  restored" (dazwischen „`j` left as the server has them", wenn es solche
  Kästen gab). Gezählt wird, was die ANTWORT des Servers zurückgibt, nicht was
  der Lauf geschickt hat — es ist die eine Zahl, an der diese Kette gemessen
  wird. Ist `n` > 0 (typisch: ohne `--mit-streifen` gibt es oben
  keine Streifenzeile, an der eine Bahn hängen könnte), bricht er ab. Eine
  Zeichnung lässt sich nicht neu folgen, also schließt sich die Lücke nicht
  von selbst. Trägt das Archiv gar keine Bahn, sagt der Lauf auch das —
  „keine im Archiv" und „diese Hand hatte nie eine" sehen von hier
  identisch aus, und nur eines davon ist in Ordnung.
  Seit 2026-09-20 nennt jeder Pfad-Push die Liste, auf der seine Mischung
  gemacht wurde (`If-Match` mit der → Bahn-Marke des eigenen GET); der Server
  verweigert ihn mit 412, wenn die gespeicherte Liste sich seither bewegt hat.
  Das ist genau das Fenster zwischen Lesen und Ersetzen: ein Kasten, den der
  Autor währenddessen in der Werkbank zeichnet, würde sonst still auf den
  Archivstand zurückgesetzt. Ein 412 heißt: Lauf wiederholen, der frische Lesevorgang
  trägt die Zeichnung. Dasselbe gilt für `pfad --apply`.
  Eine so verweigerte Fassung zählt im Restore wie eine, deren Streifenzeile
  fehlt: als **NOT restored**, mit Namen, mit den Worten des Servers und mit
  dem Hinweis auf denselben `--from`-Lauf. Ihre „already there"/„left alone"-
  Zahlen fallen mit ihr weg — sie stammen aus genau der Liste, die der Server
  eben für überholt erklärt hat. Der Durchlauf geht weiter — eine bewegte
  Liste sagt nichts über die übrigen Fassungen — und die Schlusszeile bricht
  trotzdem laut ab.
  `pfad --apply` hingegen hält an und nennt den Befehl, mit dem **diese
  Fassung** neu gefolgt und gespeichert wird (ohne `--replace-authored`: was
  inzwischen dort gelandet ist, ist genau das, was ein pauschales Übergehen
  wieder aufgäbe; mit `--api`, weil die Zeile sonst auf `$EIGENHAND_API` oder
  die Produktion zurückfiele und eine Übung so ihre eigene Abhilfe auf die
  echten Daten zeigen würde) — und, wenn der Lauf ohne `--fassung` lief,
  zusätzlich die Fassungen dahinter, die er nicht mehr erreicht hat. Wiederholt wird nie
  automatisch — derselbe Merge ein zweites Mal gegen die neue Liste geschickt
  wäre genau die verlorene Änderung, die die Marke eben verweigert hat.
- **`ingest` → `apply --haken`** (Normalfall) bzw. **`ingest` → `page` →
  `apply <Ergebnis>`** — Scan/Foto entzerren (Passmarken, scikit-image,
  300 DPI Arbeitsauflösung) und die Haken vom Blatt lesen; `apply --haken`
  verbucht sie direkt (Haken = angenommen, ohne Haken zählt die Zeile nicht
  und bleibt offen — Autor-Regel 2026-08-26); die Siebung auf der
  Offline-HTML-Seite braucht es nur für ein ausdrückliches `verworfen` mit
  Grund oder eine Anmerkung. Nur angenommene Zeilen werden als Fassungen
  abgelegt (idempotent). Eine Farbaufnahme ergibt seit dem 2026-08-27 einen
  **RGB-Streifen** (`scan.mode: rgb`); `--channel` wählt nur noch die
  Arbeitsebene für Passmarken, QC und Vorschau (Vorgabe: Blau), nicht mehr,
  was abgelegt wird. Die Lineatur verschwindet nicht beim Einlesen, sondern
  als abgeleitete Ansicht beim Abruf (`?lineatur=ohne`, Werkbank-Schalter).
  Ebenso die **Fleckenmaske** (2026-09-07, §7.4): `ingest` erkennt die
  Toner-Punkte des Druckers je Zeile, legt sie als Kreisliste in die
  `payload.json` und flaggt `flecken:<n>`; die Siebung-Seite zeichnet sie
  über den Crop; `apply` schreibt sie in `meta.json` und Kartei und misst
  den Befund auf der maskierten Ebene. Gerechnet wird beim Abruf
  (`?flecken=mit` zeigt die rohen Bytes), radiert wird in der Werkbank —
  das abgelegte Bild bleibt Byte für Byte, wie es eingelesen wurde. Auch
  der Haken wird so gelesen: punktgroße Komponenten fallen aus der Zählung,
  ein Haken muss ein Strich sein.

Was auf dem abgelegten Streifen aufsetzt — Bahn, Buchstabengrenzen,
Trainingssatz, Bericht und Archiv — steht im nächsten Abschnitt.

## Die Eigenhand-Bahnen (`tools/eigenhand`)

Dieselbe Werkzeugkette, zweite Hälfte: sie setzt auf einem Streifen auf, der
schon abgelegt IST. Hierher gehört, wer die Federbahn sucht, ihre
Buchstabengrenzen setzt, daraus einen Trainingssatz zieht oder den Bestand
berichtet und archiviert. Die Erfassung davor — Plan, Bogen, Scan, Siebung,
Ablage — steht im Abschnitt darüber, die Doktrin in
[`proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md).

- **`pfad`** — folgt der **Federbahn** eines geschriebenen Streifens und
  schiebt sie in die Werkbank (Proposal §7.5, Migration `0031`):
  `uv run python -m tools.eigenhand.pfad --hand mn-suetterlin --strip S0001`.
  Liest alles über die Admin-API (Streifen-Liste samt Kasten-Rechtecken,
  Bogen-Layout, das Streifenbild ohne Lineatur und mit angewandter
  Fleckenmaske), schneidet jedes Wort heraus, binarisiert und skelettiert es
  wie der Bench (`core.extract`) und lässt `tools.pairlab.tintenpfad` mit der
  festgezurrten Konfiguration darüber laufen (`tip_read` · `rail=tentfit` ·
  `edt_upsample=4` · `ink_bridge_xh=1.0` · `hairpin_tip` · `ride_back` ·
  `tip_grey_stop` · `self_jump`) — die Duktus-Saat kommt aus der Tafel und
  nicht aus dieser Hand: **die Vorlagen live über die Admin-API derselben
  Quelle** (seit 2026-09-13; die eingefrorene Bench-Wurzel trägt nur die 34
  Glyphen ihrer 63 Bench-Wörter, und ein Streifen wird nie gegen deren
  Referenz gemessen), aus der Fixture-Wurzel nur noch die Stil-Konstanten des
  Manifests (das Werkzeug sagt es, wenn die gitignorten Wurzeln fehlen, und
  nennt `fetch_fixtures`). Eine Ligatur ohne eigene Vorlage zerfällt wie im
  `/write`-Pfad in ihre Buchstaben — sonst fällt jedes Wort mit `ch` aus.
  Seit dem **2026-09-20 schreibt das Werkzeug Streifen-Pfad-Format 2**
  (`PFAD_FORMAT`, die zweite Hälfte des Lockstep; die API liest und
  akzeptiert 2 seit einem Release davor). Das bringt zweierlei. **Acht
  Sensoren statt sechs:** sechs kommen aus der Folger-Diagnose, zwei misst
  das Werkzeug selbst gegen die EIGENE Tintenmaske des Wortkastens — die
  **Papier-Exkursion** (`paper_excursion_xh`, der Kern des K-D-Sensors
  `tools/tracebench/excursions.py`, in x-Höhen) und die **AIoU**
  (`tools/tracebench/metric.py`). Beide sind referenzfrei — ein Streifen hat
  per Doktrin keine Referenzspur — und reine Beobachter: gemessen wird die
  AUSGELIEFERTE Bahn, die Geometrie bewegt sich nicht. Sie landen in
  `meta.tintenpfad`, wo die → Tintentreue-Ampel sie liest
  (Autor-Entscheid D: „Gemessen wird gespeichert, beurteilt wird
  abgeleitet"). Die Projektion ist eine feste Liste — ein Sensor, der nicht
  darin steht, erreicht die DB nie und ist danach nicht von „0 gemessen" zu
  unterscheiden. **Und Skip-Einträge:** ein Kasten, den der Lauf nicht folgen
  konnte, sagt das jetzt in derselben Liste (`status: "skipped"` + `grund`)
  statt einfach zu fehlen — `no_geometry` (Bogen ohne Schnittgeometrie),
  `unauthored` (Glyphen nicht auf der Tafel), `gave_up` (Folger). Den vierten
  Grund `not_selected` schreibt es bewusst NICHT: `--box` grenzt den Lauf ein
  und beurteilt nicht die übrigen Kästen. Und ein Skip verdrängt nie eine
  gespeicherte Bahn — „unautoriert" hängt an der Tafel von heute,
  „aufgegeben" an den Armen dieses Laufs, also lässt das Werkzeug seinen
  eigenen Skip fallen und sagt es in der Zeile. Ein Kasten, den die GEDRUCKTE
  Zeile gar nicht kennt (Streifenliste und Bogen-Layout widersprechen sich),
  bleibt dagegen eine Lücke statt ein Skip: ein Eintrag mit diesem Index
  brächte den Push der ganzen Fassung zu Fall, und in Frage steht nur der
  eine Kasten.
  Die vom Folger zugeordneten Buchstabengrenzen wandern damit nicht mehr ins
  freie `meta`, sondern ins **geprüfte Feld** (`letter_spans`, Herkunft
  `auto`): sie fallen bei der Dekodierung ohnehin an, und ohne sie erreichte
  eine gefolgte Bahn den Streifen-Editor ohne eine Naht zum Ziehen. Wo die
  AUSGELIEFERTEN Züge sie nicht mehr tragen (`cap_word_strokes` dünnt jenseits
  von 128 Zügen aus und unterabtastet jenseits von 4096 Punkten), fallen sie
  weg statt auf fremde Tinte zu zeigen — jeder Index wäre danach noch
  wohlgeformt, und genau das sieht die Server-Prüfung nicht. Von Hand
  korrigierte Grenzen bleiben unberührt und reisen weiter mit.
  **`--spans` ist der zweite Modus** und folgt NICHTS: er liest die
  gespeicherte Liste, ordnet den Bahnen darin Grenzen zu (→ `spans` unten) und
  legt jeden Pfad unverändert zurück — er kann keine Koordinate einer Bahn
  bewegen, und das ist die Eigenschaft, die ihn auf Handarbeit richten lässt.
  Er bearbeitet die Kästen ohne Grenzen; einen Kasten, dessen Grenzen der Autor
  korrigiert hat, lässt er GANZ in Ruhe und nennt ihn (eine Grenze ist nur
  neben den benachbarten sinnvoll). `--replace-authored` ist neben diesem Modus
  verweigert — hier gibt es nichts aufzugeben. Gespeichert wird nur, wenn
  wirklich eine Grenze entstanden ist: eine Fassung ohne Bahn bleibt auf
  `pfade: null` (das heißt „noch niemand gefolgt", nicht „gefolgt, nichts
  zurück"), und ein Lauf ohne neue Grenze schickt gar keinen Push — eine
  Voll-Ersetzung ist nie folgenlos, sie hebt die Inhaltsmarke und stempelt
  eine Format-1-Zeile auf 2.
  **Trockenlauf ist die Vorgabe** — ohne `--apply`
  landet das Ergebnis nur als JSON unter der lokalen Hand; `--apply` schreibt
  es über `PUT /eigenhand/strips/{hand}/{strip}/{fassung}/pfade` in die
  GETEILTE DB, braucht `ADMIN_TOKEN` und gehört hinter einen
  `tools.dbsnapshot.fetch`. `--fassung` und `--box` grenzen ein; weil der
  Schreibweg eine VOLLE Ersetzung ist, mischt **jeder** Lauf die gefolgten
  Kästen über die gespeicherten — auch der Zeilenlauf, denn der überspringt
  einen Kasten ohne Rahmen, ohne autorierte Glyphen oder mit gescheitertem
  Folger, und nur das Gefolgte zu schicken löschte deren Pfade still. Der
  Trockenlauf legt genau diese gemischte Liste ab, sonst prüfte man etwas
  anderes, als man schriebe. **Eine von Hand gezeichnete Bahn** (`verfahren:
  "authored"`) überlebt jeden Lauf: das Werkzeug mischt um ihren Kasten herum
  und lässt das eigene Ergebnis dafür fallen, der Server weist einen Push, der
  sie verdrängen würde, als Ganzes ab (409). `--replace-authored` gibt sie auf
  — die einzige Fläche dafür, und bewusst kein Knopf in der Werkbank
  (Autor-Entscheid Q4 (i), 2026-09-18). Seit dem 2026-09-20 **verweigert das
  Flag, solange der Kasten nicht archiviert ist** (Autor-Entscheid B):
  geprüft wird nicht „gibt es einen Satz in der Kartei", sondern „ist es
  DIESE Zeichnung" — eine vor der letzten Korrektur gezogene Kopie zählt
  nicht. Die Verweigerung nennt den einen Befehl, der sie auflöst
  (`pull --pfade`); ein zweites „ich weiß, was ich tue"-Flag gibt es nicht.
  Die Erfolgsmeldung nennt dafür den nächsten Schritt: geprüft ist nur, dass
  die Kopie in der `kartei.json` dieses Rechners liegt, also auf EINER
  Platte — `snapshot` trägt sie ins private Archiv. Und der Server-Override
  `?replace_authored=true` reitet nur auf der Zeile mit, die wirklich eine
  Zeichnung übergibt: das Flag gilt für den ganzen Streifen, der 409 ist aber
  die einzige Prüfung, die nicht auf diesem Rechner läuft.
  **Drei Eingabestufen** (seit 2026-09-24, jede einzeln schaltbar; alle
  aus = der Lauf, mit dem jede Bahn vor diesem Tag gefolgt wurde, Byte für
  Byte) ändern, was der Folger BEKOMMT, nie den Folger — der Dekoder bleibt
  der A45-Standard der Platte:
  `--mask-labels` (**Vorgabe AN** seit dem Autor-Entscheid vom 2026-09-24,
  aus mit `--no-mask-labels`) löscht die gedruckte Streifen-ID, die
  Herkunftszeile und die
  Wort-Beschriftungen NACH der Binarisierung aus Maske und Skelett (die
  Zonen aus denselben Seitenprimitiven, aus denen das Bogen-PDF gezeichnet
  wird; Kasten-Rechteck und gespeicherter Rahmen bleiben, wie sie sind);
  `--resample-plate` folgt den Kasten bei den 31 px je x-Höhe der Platte
  (nur außerhalb ihres Bereichs 28–33, also auf keinem Plattenwort) und
  bildet die Bahn exakt auf die Streifenpixel zurück; `--register-seed` legt
  die Saat auf x-Höhe, Grundlinie und Breite der Hand statt auf die gedruckte
  Lineatur — anisotrop, sy und Grundlinie aus den Moden der spaltenweisen
  Skelett-Extreme (an der Platte kalibriert), sx aus Tinten- gegen
  Kompositionsbreite; unlesbare Moden oder ein Maß jenseits der
  x-Höhen-Toleranz der API lassen die Saat unverändert. Die Rechnung steht
  in `core/eigenhand/follower_input.py`; eine gespeicherte Zeile nennt die
  Stufen (`konfiguration.input`) und was sie gemessen haben (`meta.input`).
  Herkunft: die Eigenhand-Diagnose vom 2026-09-24 (Beschriftung als Tinte
  gefahren, Pixelpreise mit 0,44× Plattenreichweite, Saat auf der gedruckten
  statt der geschriebenen Lineatur). Die Leiter ist gemessen (§14
  „Folger-Eingabe-Leiter `sep24`" in `messjournal.md`); `--resample-plate`
  und `--register-seed` bleiben aus, bis eine vorregistrierte Runde sie
  trägt.
  BLAS-Fäden
  pinnt das Modul selbst (Vorgabewerte), weil die Kettenlösung sonst je nach
  Umgebung anders läuft.
- **`spans`** — der **Span-Zuordner**, die Rechenhälfte hinter `pfad --spans`.
  Er baut dieselbe Saat, gegen die der Folger dekodiert (`derive_word` +
  `register_letters` + `seed_samples`, auf der Tinte des Wortkastens
  registriert), ordnet jedem Stützpunkt der Bahn einen Saat-Punkt zu und gibt
  ihm dessen Slot. Zwei Regeln: **`dtw`** (Vorgabe) hält die Zuordnung je Zug
  monoton — der Saat-Index darf beliebig weit vor, nie zurück —, **`nearest`**
  ist die ordnungslose Basis, gegen die sie gemessen wurde. Züge werden
  EINZELN zugeordnet, sonst schöbe ein nachgetragener i-Punkt auf den falschen
  Buchstaben. BLAS-Fäden pinnt das Modul selbst, die Wurzel nennt es vor der
  ersten Messung und `--expect-root` macht sie zur Vorbedingung. `--check` ist
  die §14-Runde (`… spans --check --expect-root <präfix> --json <bericht>`,
  gepinnt): die eingefrorenen Wörter gefolgt, die Bahn „wie von Hand
  gezeichnet" neu zugeordnet, verglichen — plus ein **Wackel-Arm**
  (`--wobble`), weil der saubere Vergleich zirkulär ist. Zahlen, Schranken und
  diese Grenze: §14 „Span-Zuordner `sep20`" in
  [`messjournal.md`](messjournal.md).
- **`training_set`** — der lokale, gitignorte **Trainingssatz** der von Hand
  nachgefahrenen Bahnen (Autor-Zusatz zu Q4: „die hand nachgefahrenen linien
  dienen auch als trainingsmenge um den folger nachhaltig immer besser zu
  machen"). Der Begriff bleibt deutsch, die Bezeichner sind englisch —
  „training set" und „hold-out set" sind etabliert
  ([sprachregelung.md](sprachregelung.md) §5).
  Zwei Befehle. **`--draw <Schlüssel>`** zieht EINMAL je Hand die
  zwei getrennten **Rückhaltemengen** (Autor-Entscheid 2026-09-20, zugleich die
  Antwort auf FM3): `holdout-follower` für die Folger-Arbeit,
  `holdout-release` für die Freigabe-Prüfung, der Rest ist `practice`. Gezogen
  wird über die STREIFEN des eingefrorenen Plans — ohne Netz, ohne eine einzige
  Bahn, also am besten VOR der ersten; die Zugehörigkeit ist eine reine
  Funktion aus Schlüssel, Hand und Streifen-ID, ein später angehängter Streifen
  fällt deshalb dorthin, wo derselbe Schlüssel ihn immer hingelegt hätte, und
  wird beim nächsten Lauf mit Datum nachgetragen und genannt. Ein zweites
  Ziehen wird verweigert, ohne Override. Die Ziehung liegt in der
  `kartei.json`
  (Entscheid A — volle Kopie in jedem Schnappschuss) und ist das Einzige hier,
  was nicht neu herstellbar ist; der Lauf sagt darum hinterher, dass jetzt ein
  Schnappschuss fällig ist. Weil `sync --from` eine archivierte Kartei nach
  OBEN schiebt und die lokale nie zurückschreibt, sähe ein verlorener
  Datenbestand aus wie „nie gezogen" — vor einer Ziehung und vor einem Export
  wird darum auch das Archiv gelesen (`$KURRENTSCHRIFT_ARCHIVE` bzw.
  `--archive`, nur lesend): liegt dort eine Ziehung, bricht der Lauf ab und
  nennt den Schnappschuss, aus dem die Kartei zurückzuholen ist. **Der Export** schneidet jeden Kasten mit
  Handarbeit — gezeichnete Bahn ODER von Hand korrigierte Grenzen — genau so
  heraus, wie der Folger ihn liest (`bahn.json` + `kasten.png` + `tinte.png`);
  der Statusfilter kommt aus dem Archiv-Read (nur `angenommen`, die
  Streifenliste trägt gar keinen Status), und eine zurückgezogene Fassung
  verlässt den Baum beim nächsten Lauf wieder. In jedem `bahn.json` steht
  neben dem eigenen Hüllen-Format auch das `pfad_format` der ZEILE — sonst
  sähe „keine Grenzen von Hand" genauso aus wie „vor `letter_spans`
  geschrieben". Wurzel
  `tools/eigenhand/training-sets/`, gitignored, **kein Mess-Satz**: ein
  Streifen hat keine Referenzspur (Prüfstein 2), darum heißt das Manifest
  bewusst nicht `manifest.json` und ein Test pinnt die Trennung von den
  Bench-Wurzeln. Zwei Verweigerungen schützen die Zusage „kein Byte im
  Repo": ein Ziel INNERHALB des Checkouts, das die eine gitignore-Regel
  nicht deckt (`--out .`, `EIGENHAND_TRAINING_SET`), und eine zweite Hand
  in demselben `--out` — dort würden sich die Läufe gegenseitig die Fälle
  wegräumen, weil eine Fall-ID keine Hand trägt. Vorregistrierung der Ziehung:
  [`messjournal.md`](messjournal.md) §14 „Trainingssatz `sep20`".
- **`report`** — Bestandsbericht (Erstbeleg-/Ausbau-Quote, Fehlstellen,
  Druckvorschlag) und, seit dem **Streifen-Befund** (2026-09-07), die
  Gegenrichtung: je angenommener Fassung Vorschlag (`sauber` · `brauchbar` ·
  `neu schreiben`), dominierender Grund und Rang unter den Fassungen ihres
  Streifens, dann die Liste „neu schreiben, schwächste zuerst"; `--befund`
  zeigt nur diese. Gemessen wird beim Ablegen (`apply`), abgeleitet beim
  Lesen — der Haken bleibt das Urteil, nichts verwirft automatisch
  (eigenhand-erfassung.md §7.3). **`--faellig` ist der EINE Modus dieses
  Werkzeugs, der die API liest** (`--api`/`--token` wie bei `pull`/`sync`
  über `apiclient`, nie die Datenbank): er druckt die fälligen lokalen
  Schritte, die der SERVER sieht, in Reihenfolge — der Zwilling der
  Übergabekarten im Admin, weil die Zwischenablage nicht vom Tablet zum
  Rechner reicht. Lokal gerechnet sähe eine fällige Liste immer erledigt
  aus (die Gewichtsdatei liegt hier, jedes Streifenbild liegt hier), darum
  entscheidet die Regeln einmal `core/eigenhand/faellig.py` und dieser
  Modus druckt nur. Jeder andere Modus bleibt vollständig offline und macht
  keinen einzigen HTTP-Aufruf (`tests/test_eigenhand_report.py`);
  **`progression`** — die Plan-Sicht dazu: kumulierte
  Zählungen je Glyphe (klein · groß · Ligatur · Ziffer · Zeichen) und je
  Übergang an Checkpoints alle N Streifen, mit `--json` für Auswertungen
  („nach 10, 20, … Streifen — wie oft ist jede Glyphe dran?“), und
  schließt mit der Prüfzeile zur Mindestbelegung (≥3 je Glyphe);
  **`redo`** stellt Streifen neu an (`--retire` zieht
  alte Fassungen zurück); **`snapshot`** sichert inkrementell und
  create-only ins private Archiv (`KURRENTSCHRIFT_ARCHIVE`, dieselbe
  Clone wie die DB-Snapshots; dbsnapshot-Disziplin inkl.
  Schrumpf-Verweigerung). Kartei, Streifenplan und das stehende Setup
  fahren in jedem Schnappschuss vollständig mit; Fassungen und Bögen nur
  als Zuwachs — wer aus dem Archiv liest, muss die Schnappschüsse deshalb
  als einen geschichteten Baum lesen, so wie `sync --from` es tut. Die
  volle Kartei-Kopie ist dabei tragend und keine Bequemlichkeit: sie ist
  der Weg, auf dem Fleckenmasken und nachgefahrene Bahnen von LÄNGST
  abgelegten Fassungen ins Archiv kommen — beide entstehen erst, nachdem
  das Fassungs-Verzeichnis archiviert ist, und das überspringt der Lauf am
  relativen Pfad.

Invarianten wie überall: kein DB-Schreibpfad — `sync` spricht die
Admin-API, nie die Datenbank —, eingefrorene Mess-Sätze
bleiben unberührt (der Streifenplan ist Trainingsdaten, kein Mess-Satz),
und die abgelegten Streifen sind Teil des reservierten Datensatzes
(Open-Core): sie liegen lokal, im privaten Archiv und — seit Migration
`0025` — admin-gesichert in der DB, nie im Repository und nie öffentlich.

## Das Lesart-Wörterbuch (`tools/lesarten`)

Die Wörter, die die Lesart-Seite (`/lesen/vergleichen`) als echte Lesarten
anbietet, kommen aus der geteilten DB (`lesart_forms`, Migration 0028);
dieses Werkzeug füllt sie — Muster wie `tools.eigenhand.universe --push`:
lokal bauen, über die admin-gesicherte API laden, nie direkt in die DB.

- **`expand`** — expandiert das igerman98/frami-Wörterbuch
  (`data/corpora/igerman98/`, vorher `fetch_igerman98.py`; GPL-Bytes
  gitignored, `SOURCE.md`) um eine Affix-Schicht: ≈ 720 000
  Buchstaben-Formen ohne freie Komposita (hunspell setzt Kirchenbuch zur
  Laufzeit zusammen) — `uv run python -m tools.lesarten.expand` zählt.
- **`sync`** — vereinigt die Formen mit der Quiz-Wortbank
  (`tools/quizgen/quiz_words.json`, unique; Bankwörter markiert, sie
  ranken bei Gleichstand zuerst) und lädt sie generationsweise:
  `POST /lesarten/dictionary/generations` (öffnet; derselbe Bau = 409,
  nichts zu tun) → Batches à 20 000 Wörter (der Server berechnet den
  Verwechsler-Schlüssel selbst, `core.lesarten.lesart_key`) → `commit`
  schaltet die Generation live und löscht die alte; ein Abbruch löscht
  die angefangene. Jede Batch-Zeile nennt ihre Sekunden — die Zahl muss
  über den ganzen Lauf flach bleiben; wächst sie mit den schon
  gespeicherten Zeilen, ist die Ladefunktion wieder auf einen Lesevorgang
  vor dem Insert zurückgefallen (2026-09-02). Wörter über
  `core.lesarten.WORD_MAX` = 64 Zeichen fallen vor dem Push heraus (die
  Spalte ist `String(64)`, die API weist den ganzen Batch mit 400 ab);
  der Bau sagt beim Start, wie viele — aktuell zwei
  67-Zeichen-Verwaltungskomposita, die als Lesart ohnehin nie in Frage
  kommen (eine Anfrage ist auf 32 Zeichen begrenzt). `--dry-run` zeigt
  nur die Zahlen. Braucht `ADMIN_TOKEN`
  (`ADMIN_TOKEN=… uv run python -m tools.lesarten.sync`). Nach einem
  Wörterbuch-Update (neuer Pin in `fetch_igerman98.py` + `SOURCE.md`)
  oder einer Bank-Erweiterung einmal laufen lassen — **und nach jeder
  Änderung der Verwechsler-Tabelle** (→ Lesart-Schlüsselversion,
  `glossar.md` §1): Der Schlüssel steckt seit 2026-09-04 im Inhalts-Hash,
  derselbe Wortbestand unter neuer Tabelle ist also ein neuer Bau, und
  das Quell-Label trägt die Version (`lesart-key/vN`). Reihenfolge:
  erst deployen, dann laden — eine API mit älterer Tabelle weist den
  Bau mit 409 ab und nennt beide Versionen, weil sie die Schlüssel
  selbst berechnet. Bis zum Nachladen meldet
  `GET /lesarten/dictionary` `stale: true`, und die Seite sagt statt
  „wohl eindeutig", dass das Wörterbuch gerade umgestellt wird.

## Der Changelog-Schnitt (`tools/changelog`)

Kein Mess-, sondern das Release-Werkzeug: jede PR legt EIN Fragment
`changelog.d/<slug>.md` ab (Format = das der CHANGELOG selbst, `### Category`
über fett betitelten englischen Bullets; `changelog.d/README.md`) statt einen
Bullet in `CHANGELOG.md` zu schreiben — die eine geteilte Stelle, an der bis
2026-08-30 jeder Geschwister-Merge die anderen PRs in den Konflikt schickte
(der Union-Merge-Treiber heilte nur den lokalen Rebase; GitHubs eigene
Mergebarkeitsprüfung ignoriert ihn). Nur Standardbibliothek, damit der CI-Job
ohne Projekt-Extras läuft; kein Netz, keine DB — es schreibt ausschließlich in
den Arbeitsbaum.

- **`check [--base origin/main]`** — jedes Fragment ist wohlgeformt (bekannte
  Kategorie, fett betitelte Bullets — der schließende `**` darf auf der
  Folgezeile stehen, muss aber da sein —, kein unausgefüllter `(#NNN)`,
  sonst nichts). Mit `--base` die PR-Regel
  des CI-Jobs „Changelog (fragment)": das Diff trägt ein Fragment (oder ist
  ein Release-Schnitt, der Fragmente löscht, oder rein `data/`), und
  `[Unreleased]` hat keinen Bullet dazubekommen — dazubekommen heißt einen
  neuen fetten Titel (oder eine weitere Kopie eines vorhandenen); den
  Wortlaut eines dort schon stehenden Eintrags zu korrigieren ist erlaubt.
  Ausnahmen laufen über den Job, nicht über das Werkzeug: Label
  `skip-changelog` und Dependabot als PR-Autor — in beiden Fällen läuft der
  Job gar nicht erst.
- **`preview`** — der gesammelte `[Unreleased]`-Abschnitt, wie ihn der
  nächste Schnitt schreiben würde: die Fragmente, neueste zuerst je
  Kategorie nach dem Commit, der sie anlegte (ein noch nicht committetes
  zuoberst), darunter, was die Datei noch aus der Zeit vor den Fragmenten
  hält.
- **`release X.Y.Z --title "…" [--date YYYY-MM-DD] [--dry-run]`** — der
  Schnitt: neue Versionsüberschrift im Format der Datei
  (`## [X.Y.Z] — Datum — Titel`), `pyproject.toml`, `uv.lock` und
  `CITATION.cff` gehoben (je Zeile genau ein Treffer, sonst Abbruch),
  Fragmente gelöscht; `--dry-run` zeigt Plan und Abschnitt, schreibt nichts.
  Commit, Tag auf dem Merge-Commit und die kondensierte GitHub-Release
  bleiben Handarbeit (Kopf der CHANGELOG).
  `uv run python -m tools.changelog release 0.28.0 --title "…"`.

## Die Teilen-Karte (`tools/ogcard`)

Baut `app/public/og.png` — das Bild, das eine Vorschau von
kurrentschrift.ink in Chat, Feed oder Suchergebnis zeigt. Bis 2026-08-30
stand der Markenschriftzug darauf in der **Schau-Schrift**
GL-GermanCursive; das widersprach der Seite, für die die Karte wirbt: der
Hero schreibt „Kurrentſchrift“ mit der Synthese-Engine und fällt nur bei
kaltem Backend auf den Font zurück. Die Karte geht jetzt denselben Weg wie
der Hero — `GET /sources/{id}/write/word.svg` — und ist damit an die
Vorlage gebunden statt an eine Schriftdatei: nach einem Re-Trace wird sie
neu gebaut, nicht neu gemalt.

Was aus der Seite zitiert wird (gespiegelt, nicht importiert — hier Python,
dort TypeScript; jede Konstante nennt ihr Gegenstück): das Wort über
`PUBLIC_SOURCE_ID` ohne Lineatur, der viridiane Schwung als der
`Flourish`-Pfad aus `HeroWritten.tsx` samt seiner Platzierung, die
Wortmarke aus `HeaderBar` — ohne ihren Punkt, weil Schwung und `.ink` den
Akzent schon tragen — und die Farben aus `paper.ts`. Kein Fixture pinnt
das: ein Bild hat keine Byte-Gleichheit, die sich zu prüfen lohnt; wandert
eine der vier Quellen, wird die Karte neu gebaut und angesehen.

Nur Standardbibliothek plus Pillow (Runtime-Dep), ein öffentlicher GET,
kein Admin-Token, keine DB. Gerendert wird mit dem **headless Chromium, das
Playwright für `/verify-frontend` ohnehin installiert** — hier wird nichts
nachgeladen; `OGCARD_CHROME=<Pfad>` übersteuert die Suche. Der
`headless_shell`-Build ist der richtige: `chrome` bemisst im neuen
Headless-Modus das **Fenster** statt des Viewports und lässt einen weißen
Streifen unter der Seite. Genau das prüft der Bau nach (Größe stimmt, das
Papier erreicht alle vier Ecken), bevor er die Datei schreibt — der Fehler
sieht in einer Dateiliste sonst unauffällig aus.

Die komponierte Geometrie wird geholt und **nie committet** (reservierter
Datensatz, [`quellen-und-rechte.md`](quellen-und-rechte.md) §5); im Repo
landet das 1200×630-Raster eines einzigen Wortes — das veröffentlichte
Teilen-Bild selbst, bewusste Produktfläche wie die `/write`-Payloads, aus
denen es stammt.

- **`uv run python -m tools.ogcard`** — holen, rendern, `app/public/og.png`
  schreiben. `--api http://localhost:8000` gegen die lokale API,
  `--svg <Datei>` mit einem schon vorliegenden Wort-SVG, `--out <Datei>`
  woandershin, `--html-only <Datei>` schreibt nur die komponierte Seite
  (zum Ansehen im Browser, ohne Screenshot).
- **Alt-Text nachziehen** ist Handarbeit: `og:image:alt` steht in
  `app/index.html` und als `OG_IMAGE_ALT` in `app/src/lib/seo/prerender.ts`
  — danach `npm run prerender`, sonst tragen die ausgelieferten
  Prerender-Seiten weiter die alte Beschreibung.

## Die Seiten-Icons (`tools/favicon`)

Baut `app/public/favicon.svg`, `favicon.ico` (16/32/48) und
`apple-touch-icon.png` (180) — das Zeichen im Browser-Tab, in der
Google-Trefferzeile und auf dem Home-Bildschirm. Bis 2026-09-19 war das ein
großes K in der **Schau-Schrift** GL-GermanCursive, einmalig von Hand
gerendert: das letzte Markenbild, das eine fremde Schrift statt des Produkts
zeigte, ohne Vektorform und ohne Weg, es neu zu bauen. Das Icon geht jetzt
denselben Weg wie die Teilen-Karte — ein öffentlicher GET,
`/sources/{id}/write/glyphs/K.svg` — und zeigt das geschriebene K der
Vorlage mit dem viridianen Punkt der Wortmarke aus `HeaderBar`; die Farben
sind aus `paper.ts` gespiegelt.

Der Umriss kommt als geschlossene Polygone (`M`/`L`/`Z` unter
`fill-rule="evenodd"`), ein `<path>` je Federzug. Deshalb rastert **Pillow
allein**: jede Teilfläche füllen, **innerhalb eines Zuges** per XOR
verrechnen, die Züge per ODER vereinen (wo zwei Züge sich kreuzen, bleibt
Tinte und entsteht kein Loch), achtfach überabtasten, herunterskalieren — kein
Browser, keine SVG-Bibliothek. SVG und Raster teilen sich eine eingepasste
Geometrie, also zeigen Tab und `/favicon.ico` dasselbe Zeichen. Ein
Kurvenbefehl oder ein gestrichener Pfad im Glyphen-SVG bricht den Bau mit
einer Meldung ab, statt still etwas anderes zu zeichnen. Weil ein Federzug
bei 16 px zur Haarlinie wird, verstärkt `INK_BOOST` den Umriss (im SVG als
gleichfarbiger Strich, im Raster als Linie entlang des Polygons).

Wie bei der Karte wird die Geometrie geholt und **nie committet**
([`quellen-und-rechte.md`](quellen-und-rechte.md) §5); im Repo landet das
veröffentlichte Icon eines Buchstabens.

- **`uv run python -m tools.favicon`** — holen, einpassen, die drei Dateien
  schreiben. `--api http://localhost:8000` gegen die lokale API,
  `--svg <Datei>` mit einem schon vorliegenden Glyphen-SVG, `--out <Ordner>`
  woandershin.
- **Die Icon-Links stehen zweimal:** in `app/index.html` und als
  `ICON_LINKS` in `app/src/lib/seo/prerender.ts` — ein Crawler bekommt die
  SPA-Hülle nie zu sehen, ohne die Links bliebe ihm nur der
  `/favicon.ico`-Fallback. Nach einer Änderung dort `npm run prerender`.
- **`/favicon.ico` muss weiter antworten** (`/verify-frontend` wertet ein
  404 darauf als Regression). Nach einem neuen Icon die Startseite in der
  Search Console neu indexieren lassen; Google tauscht Favicons über Tage
  bis Wochen.

## Die Wurzel-Angabe jedes Messlaufs (`--expect-root`)

Jeder Einstieg, der eine Fixture-Wurzel liest, nennt sie **vor** der ersten
Messung — `root: <name> exported_at=…` und `digest=<12 hex>` — und
`--expect-root <präfix>[,<präfix>…]` macht die erwartete Grundlage zur
Vorbedingung: passt eine Wurzel nicht, oder passt ein genanntes Präfix zu
keiner Wurzel, bricht der Lauf ab, bevor er misst. Die Wurzeln sind
gitignored, ein Neu-Export hinterlässt sonst keine Spur (Prüfung
`sep02`). **Wer eine Zahl aus der Sitzung trägt, läuft mit
`--expect-root`** — und eine Runde nimmt denselben Präfix in *jeden* ihrer
Aufrufe, sonst ist nicht belegt, dass Abnahme, Folger und Wertungen
dieselbe Grundlage gesehen haben. Eine Umsetzung für alle:
`tools/wordbench/roots.py`, getragen seit `sep05` von **jedem** Einstieg,
der eine Wurzel liest — `tools.wordbench.run`, `tools.tracebench.run` ·
`.k0eval` · `.view` · `.excursions`, `tools.pairlab` selbst sowie
`.follow` · `.spanmeas` · `.chainbench` · `.bindab` · `.gradlab` ·
`.peaklab` · `.landmarklab` · `.harvest` sowie `tools.eigenhand.spans
--check`; volle Digests im `--json` unter `roots`. Der Kopf nagelt den **Lauf** fest; den **Vergleich** nageln
`--compare` (Wordbench, Tracebench), `--rows` (Duell-Seite) und `--base`
(spanmeas) fest: sie lesen den `roots`-Block der gespeicherten Datei und
verweigern eine Basis aus einem anderen Export, bevor gemessen wird — eine
Datei ohne `roots` (vor dem Sensor geschrieben) wird gelesen und mit einer
Warnung versehen. Begriff und Hausregel:
[Wurzel-Digest](glossar.md#4-metriken-und-benchmarks).

## Benches und Generator (Verweise)

- **`tools/glyphbench`** — bewertet jeden autorisierten Buchstaben gegen
  eingefrorene Referenzen, EIN Skript pro Lauf; Metrik + Baseline-Historie
  in [`qualitaetsmetrik.md`](qualitaetsmetrik.md). `export_fixtures.py`
  (der einzige DB-Zugriff, rein lesend) exportiert nur Zeilen MIT
  Stylus-Pfad — die Bench leitet jede Kanonische daraus neu ab, eine
  Laufform-Zeile hat keinen — und **ersetzt** die Wurzel bei jedem Lauf,
  statt in sie hineinzuschreiben: gebaut wird in einem
  Staging-Geschwister, getauscht wird am Ende, ein Abbruch lässt die
  vorherige Wurzel unangetastet. Beides seit der Re-Baseline `sep03`:
  vorher überschrieb die Laufform-Zeile im gemeinsamen Verzeichnis
  `<glyph_key>/` die Tafelzeile (44 Abstürze), und Verzeichnisse aus einem
  älteren Schema blieben unsichtbar liegen
  ([`qualitaetsmetrik.md`](qualitaetsmetrik.md) §5).
- **`tools/wordbench`** — bewertet KOMPONIERTE Wörter/Paare gegen die
  Abb.-19/-20-Vorlagen (gleiche Hand); Metrik + Doku in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §6. Fünf Module hängen
  **Report-Spalten** an, die nie in den Loss eingehen (eigener try/except,
  hinter dem stabilen Block): `slant.py` (Schräglage Vorlage vs. komponiert,
  90° = senkrecht; R5), `gleichzug.py` (Ein-Fluss-/Ein-Breite-Audit auf der
  komponierten Centerline, ohne Vorlagenbezug; `jul30`), `pairmeas.py`
  („gemessen vs. komponiert“ — die komponierten Joins gegen die sezierten
  `pair_instances` derselben Vorlagen; `aug02`), `seam.py` (Naht-Winkel
  `dep`/`arr`; `sep02`) und `continuity.py` — der **Unstetigkeits-Sensor**
  (`cont_*`, `sep06`): Knick, Wackler und Pfeilhöhe an jedem Punkt der
  komponierten Mittellinie, der keine Landmarke ist (Federabsetzen,
  Kreuzung, Retrace-Zone, Umkehrecke — je eine Feder Radius, alle vier
  gezählt). Er misst als einziger nicht ABSTAND, sondern Stetigkeit; die
  Fenster kommen aus der Feder (halbe Feder · eine Feder · zwei Federn),
  die Schwelle ist arcsin(0,2) = 11,537°. Abgenommen an den
  humanbench-Runden 5 und 6 ([`messjournal.md`](messjournal.md) §14
  „Übergänge S2"), Report-only, kein DB-Zugriff, `core/word_metric.py`
  unberührt. Die Fixture-Roots frieren
  seit `aug14` zusätzlich `word_instances.json` ein — die gespeicherten
  Wortbahnen des Sets samt Frame-Gate (`frame_stale`), deren
  `authored`-Zeilen der Referenzsatz von `tools/tracebench` sind
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md));
  Refill ohne Re-Baseline: `--only word-instances` bzw. `--only instances`.
  Ohne Cloud-SQL-Zugang baut `fetch_fixtures.py` dieselben Roots
  byte-kompatibel über HTTPS auf — der rein lesende Zwilling von
  `export_fixtures.py`, ausschließlich GETs, mit `--verify` als
  Abnahme-Gate:
  `uv run python -m tools.wordbench.fetch_fixtures --set all --verify`.
  Zwei Overlay-Flags für Trocken-Experimente (`aug19` erstmals im
  Feld, Laufform-Arme LF1–LF3): `--laufform <Datei.json>` komponiert
  mit KANDIDATEN-Laufformen (Harvest-Draft `{anchors, n_occurrences}`
  oder volle Fixture-Zeile; Overlay — unbenannte Glyphen behalten die
  eingefrorene Zeile) und `--no-laufform` komponiert chart-treu ohne
  jede Laufform. Beide liefern per Doktrin §6 eine
  OFF-HEADLINE-Kandidatenzahl, nie die Headline. Dieselbe Disziplin gilt für
  die **Übergangs-Schalter**. `--apex-handover`, `--stem-depart` (J5) und
  `--seam-negotiation` (Arm J6, die **Nahtverhandlung**, mit
  `--seam-negotiation-max-jump` als J6b-Verengung auf die Nähte, deren beide
  Seiten sich treffen können) stehen im Composer standardmäßig aus und
  werden hier zugeschaltet; der **Austritts-Trim ist seit dem 2026-09-06
  Standard** (Autor-Entscheid A37), also läuft er ohne Flag mit und
  `--no-exit-trim` misst die pre-adoption Basis — mit
  `--exit-trim-min-kink` als J4b-Verengung, die sich mit `--no-exit-trim`
  ausschließt. Jede Abweichung vom ausgelieferten Stand nennt sich im Kopf des
  Laufs und im `--json`-Bericht, damit eine Leitersprosse sich nie unter dem
  Namen der Basis ablegt.
- **`tools/wordbench/repair_boxes.py` + `shift_registrations.py`** (`aug31`)
  — die Reparatur eines Rechtecks, das die EIGENE Tinte seiner Probe
  anschneidet (der abgeschnittene i-Strich, der halbe letzte Buchstabe).
  `propose_boxes` schneidet mit 3 px Rand auf der **despeckelten** Maske;
  ein dünnes Sütterlin-Diakritikum fällt unter diese Schwelle oder landet
  auf der Kante. `repair_boxes` misst auf der ROHEN Maske nach und zieht
  nur die Kanten heraus, deren Luft unter dem Plattenstandard liegt — alles
  andere bleibt Byte für Byte stehen (gemessen: 169 der 202 Proben liegen
  exakt auf den 3 px und werden nicht angefasst). Was eigene Tinte ist,
  entscheidet die **Lineatur der Zeile** (`midband_y`/`baseline_y`), nicht
  eine Pixelzahl: Komponenten außerhalb ±1,35 xh gehören der Nachbarzeile;
  Interpunktion hängt ganz unter der Mittellinie und kommt nie herein (jeder
  Rechts-Kandidat des ersten Laufs war ein Komma); blasser Durchschlag fällt
  am Schwärze-Vergleich mit dem eigenen Strich aus. Über 2 x-Höhen
  Wachstum wird **gemeldet statt angewandt** — nur Rückfallebene hinter
  den Regeln davor, und bewusst locker: bei einer x-Höhe verweigerte der
  Deckel `regieren`, dessen letztes `n` wirklich um 37 px angeschnitten
  ist. Die `exclude`-Boxen wandern mit: was das gewachsene Stück NEU
  einschließt und dem Wort nicht gehört, bekommt eine (das Komma neben
  `regieren`s Auslauf), und eine Box, die nur noch eigene Tinte verdeckt,
  fällt weg (`zum`s Box hing am alten Oberrand und malte einen weißen
  Kasten auf sauberes Papier). Eine Box, die weiter Fremdtinte deckt,
  bleibt in jedem Fall stehen — handgesetztes Urteil.
  `--report` · `--sheets <dir>` (Vorher/Nachher-Kacheln, rot/grün) ·
  `--apply`.
  **Zwei Dinge wandern mit** und dürfen nicht vergessen werden:
  gespeicherte Wortbahnen registrieren CROP-lokal, also verschiebt ein
  bewegtes `x0`/`y0` sie — `shift_registrations.py --baseline <alte
  words.json>` rechnet genau den Ursprungs-Versatz auf `tx`/`baseline_row`
  und leitet ihn aus den beiden Sidecar-STÄNDEN selbst ab, sodass zwischen
  den Werkzeugen keine Liste hin und her wandert. Welchem Ausschnitt eine
  Zeile gerade folgt, wird **festgehalten**: eine verschobene Zeile trägt
  ihren Ursprung als `measurements.rect_origin`, eine Zeile ohne Stempel
  gehört zum `--baseline`-Stand. Ohne das ist ein Lauf auf der x-Achse
  nicht wiederholbar — ein Test über `baseline_row` allein sieht eine
  reine Links-Reparatur (`das`, `und`) gar nicht, und deren `tx` bliebe
  stumm zurück, wo die senkrechte Drift wenigstens als „Rahmen veraltet"
  auffiele. `--apply` schreibt in die GETEILTE DB und braucht die Zusage
  des Autors. Und die Fixture-Roots frieren die Rechtecke ein: eine
  reparierte Platte braucht einen Fixture-Re-Export plus datierten
  Re-Baseline-Eintrag in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §15.
- **`tools/tracebench` + `tools/pairlab/follow`** — das Lineal und der
  Mess-Kandidat des Tintenfolger-Duells
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md);
  Zahlen und Vorregistrierungen in
  [`messjournal.md`](messjournal.md) §14). Einstiegspunkte:
  `tools.pairlab.follow` (Folger-Lauf → Kandidaten-JSON),
  `tools.tracebench` (dev-19-Wertung gegen die authored Wortbahnen),
  `.k0eval` (referenzfreies 63er-Protokoll), `.excursions`
  (Papier-Exkursions-Inventar, der stehende K-D-Sensor), `.reversals`
  (**Papier-Umkehren** — der Zickzack IM PAPIER, getrennt von dem in der
  Tinte, der Duktus ist; `--paper`, `--words-file`), `.kringelcat`
  (baut den eingefrorenen Kringel-Katalog aus EINER Wurzel; `.kringel`
  ist der Sensor, der ihn liest — Report-Spalte `kringel_lost`, §14
  „Kringel-Landmarke `sep06`") und `.view`
  (Duell-/Augenschein-Seite). `tools.pairlab.zweizuege` ist das
  **Zwei-Züge-Modell** (§14 „Kette R3 `sep07`"): `--zwei-zuege`, Vorgabe
  AUS, korrigiert die fertige Bahn an verschmolzenen Schleifen und meldet
  je Schleife Korrektur oder Verweigerung. `tools.pairlab.counterfield` ist
  dieselbe Aussage als Term IM Solve (**Binnenflächen-Bedingung**, §14
  „Kette R3c `sep07`"): `--counter-constraint --counter-weight W`, Vorgabe
  AUS; als eigenes Modul aufgerufen (`python -m tools.pairlab.counterfield
  <kandidat> [--base <kandidat>]`) druckt es die Öffnungsweite je
  Katalogschleife und ist damit das Gate-(a)-Lineal der Runde.
  `tools.pairlab.counterevidence` ist die dritte Stelle derselben
  Aussage — die **Feder-Entfaltung** an der EVIDENZ (§14 „Kette R4
  `sep07`"): `--counter-evidence`, Vorgabe AUS, ersetzt an jeder
  `offen`-Binnenfläche das eingeschnürte Skelett durch die Niveaulinie
  einer Federhalbbreite und meldet je Schleife Korrektur oder
  Verweigerung. `tools.pairlab.seedgap` misst nicht die Bahn, sondern
  ihren START — den **Saat-Abstand** je Buchstaben-Slot, getrennt in
  Saat-Versatz (Platzierung, vom Slot-Block absorbierbar) und Saat-Rest
  (Form, nur composer-seitig heilbar); kein Solve, kein Kandidat, nur
  Wurzel und Komposition (§14 „Kette K-G Saat-Registrierung `sep09`").
  Der Schalter dazu am Folger ist `--chain-seed grid`. Die Nachtschleife
  `sep10` gab dem Folger sieben Schalter, alle standardmäßig AUS und dann
  bytegleich:
  `--bar-bridge`, `--chain-seed grid-scale|affine --seed-ramp`,
  `--paper-weight`, `--soll-source ink`, `--kink-weight`, `--letter-smooth`,
  `--seed-form laufform`, `--no-init-terms` (Glossar §3: t-Brücke ·
  Saat-Form · Gauß-Verschiebung · Tinten-Klammer · Tinten-Soll ·
  Unstetigkeits-Preis · Formglätte); `.reversals` druckt seither auch die
  **Papier-Strecke** je Wort. **Wellen-Basis** (Glossar §3): Baustein seit
  `sep13`, `--wave-spacing`, Vorgabe AUS.
  Alle nennen ihre Wurzel im Kopf und
  nehmen `--expect-root` (siehe oben); die Arm- und Archäologie-Flags
  stehen im jeweiligen `--help` und je Arm in seinem §14-Eintrag.
  Invarianten: reine Messschicht (nie DB/`core/`/Rendering), der
  Dev-Split ist eingefroren und append-never, und gepaarte Vergleiche
  gelten nur innerhalb EINER gepinnten Umgebung und EINER Wurzel.

  **Die Reihenfolge dieser Aufrufe steht hier nicht mehr, sondern in
  [`/verify-trace`](../../.claude/skills/verify-trace/SKILL.md).** Der
  Skill ist die ausführbare Form der stehenden Mess-Liturgie, die die
  §14-Einträge seit `aug19` fahren: Vorregistrierung, Fixture-Abnahme,
  Folger-Lauf mit gepinntem BLAS, dev-19-Scoring, 63er-k0-Protokoll,
  Sensoren — und die Ablage der Runde (§14-Eintrag, Register-Zeile,
  Ledger-Zeile, bei einem Negativ die Rettungswege). Er wird **vor**
  einer Mess-Runde aufgerufen, nicht nachgeschlagen, und lädt sich dann
  als Checkliste; das ist der Punkt, denn zweimal in zwei Tagen
  (`aug25` L-U, `aug26` v5) wurde gegen den falschen Folger gemessen,
  weil die Schritte aus dem Gedächtnis kamen. Diese Doku bleibt das
  Inventar — was es gibt, wie es heißt, welche Invariante daran hängt;
  der Ablauf einer Runde hat genau eine Quelle. (Bis `sep05` stand er
  hier ein zweites Mal, und beide Kopien mussten dieselbe
  `--expect-root`-Änderung erhalten.)
- **`tools/pairlab/tintenpfad`** — der **Tintenpfad**, der
  Strang-Dekodier-Folger (Glossar §3: Strang · Strang-Dekodierung): Tinte
  zuerst, Buchstaben danach. Stufe 1 baut aus dem eingefrorenen Skelett die
  **Stränge** (Sporn-Ausdünnung, glatteste Fortsetzung je Knoten,
  Sub-Pixel-Schiene); Stufe 2 dekodiert die Gauß-verschobene Saat per
  Viterbi durch die Stränge (monotone Fahrt, bepreiste Haken, Sprünge und
  Papier-Ein-/Ausstiege, Hysterese) und legt die
  Strangpixel selbst als Bahn aus, mit Hermite-Brücken an Sprüngen.
  Keine Anker, kein Verschiebungsfeld: frei
  sind nur Strang, Richtung und Absetzen, und jede Wahl bewegt einen
  ganzen Strang. Aufruf:

  ```bash
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python -m tools.pairlab.tintenpfad \
      [--all | ids…] --expect-root <digest> --jobs 2 \
      --candidate-out <dir>/cand.json --json <dir>/report.json \
      [--legacy-p6 | --legacy-p5] [--weight NAME=VALUE …]
  ```

  Alle Konstanten stehen eingefroren in `TintenpfadWeights` und wandern
  per `asdict` in den Kandidaten. **Seit A45 (2026-09-12) sind die
  Vorgaben die erklärte Konfiguration** (`tip_read` · `rail=tentfit` ·
  `edt_upsample=4` · `ink_bridge_xh=1.0` · `hairpin_tip` · `ride_back` ·
  `tip_grey_stop` · `self_jump`): ein Lauf ohne Flags IST der
  Standard-Folger. `--legacy-p6` ist der Stand davor (alle acht aus, die
  Basis jeder Ledger-Zeile des `sep11`/`sep12`), `--legacy-p5` die
  Prototyp-Zeile — ganze Konfigurationen, damit keine gemessene Zeile
  ihren Stack verliert. Sensoren je Wort in `meta.tintenpfad`:
  unbesuchte Tinte (`ink_unvisited_share` über 0,10 ist ein erklärter
  Skip), Hin-und-zurück je Brücke und Schiene, Knick- und Drehwinkel,
  Zuordnung (`label_agreement`), Verschiebungskohärenz; die
  Buchstabengrenzen stehen als `meta.letter_spans` daneben.
  Reine Messschicht,
  `core.skeleton_graph` und `core.continuity` nur importiert. Der
  Tracebench fährt ihn seit A45 direkt: `--candidate tintenpfad
  [--tintenpfad-stand default|legacy-p6|legacy-p5] [--tintenpfad-weight
  NAME=VALUE …]`, wobei Stand und Arm den Lauf labeln. Artefakte
  `temp/wellen-sep11/`, `temp/adoption-sep12/`.
- **`tools/pairlab/schlange`** — die **Schlange** (Hook B der Welle-Runde,
  §14 „Welle `sep11`"): ein Folger als elastische Kurve NEBEN der Kette, seit
  `sep12` im Repo als eigenständiger Baustein ohne Schalter im bestehenden
  Code; die §14-Zahlen sind Geschichte — ein Ecken-Index-Fehler in `seed_curve`
  wurde erst in der Review-Runde behoben, das eingecheckte Modul reproduziert
  sie nicht mehr. Aufruf `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run
  python -m tools.pairlab.schlange --set words --jobs 2
  --candidate-out <dir>/cand.json --json <dir>/schlange.json --expect-root
  <digest> <wort …>`; Details Glossar „Schlange".
- **`tools/inksight`** — die Route-B-Pipeline des Tintenfolger-Duells
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §4):
  drei Stufen (Crop-Vorbereitung → Inferenz im ISOLIERTEN
  Python-3.11-TF-venv → Kandidaten-JSON im Trace-Frame), Gewichte und
  venv bleiben untracked; reine Messschicht — die Ausgabe erreicht nie
  `core/`, die DB oder das Rendering.
- **`tools/inkpilot`** — der Kandidat der Route **Lotse**
  ([`verfahren-lotse.md`](verfahren-lotse.md)): drei Schichten — die
  **Karte** (die komponierte Bahn als Duktus-Auskunft), der **Wasserweg**
  (der Skelettgraph aus `tools/routeg/graph.py`) und der **Ritt** (ein
  Viterbi über die Sample-Kette, der zwischen Tinten-Mitte und Karte
  umsteigt). Aufruf `uv run python -m tools.inkpilot`; die adoptierten
  Konstanten stehen gesammelt in `pilot.py` (Schienen-Auslauf,
  Ritt-Doppelzonen, gepinnte Fenster, Knoten-Plateaus, Entdrillung mit
  Lineal-Soll-Budget und Reservierungs-Veto) und sind auf der
  Verfahrensseite je Version belegt. Der Duell-Kandidat läuft über den
  File-Provider des Tracebench (`--candidate file --candidate-file`).
  Daneben liegt seit `sep04` der **Absprung-Sensor**
  `tools/inkpilot/forensics.py` (`uv run --extra viz python -m
  tools.inkpilot.forensics [ids …] --csv <datei> [--png-dir <dir>]
  [--panel WORT:INDEX,… --panel-out <png>]`): er misst je emittiertem
  Punkt den Abstand vom TINTENKÖRPER (Skelett + `width_map`) und hängt
  daran den Mechanismus, der ihn gesetzt hat — dazu `map_slack_xh`,
  den Abstand der Karte an derselben Stelle, der geerbte von selbst
  gemachten Absprüngen trennt (Glossar „Absprung", „Karten-Abdrift",
  „Fenster-Versatz"). Er spiegelt `pilot_word`, statt es zu ändern,
  und hält das Ergebnis bei jedem Lauf per `assert_matches_pilot`
  bit-gleich dagegen — der Folger bleibt während einer Mess-Runde
  unberührt. Reine Messschicht: keine DB, kein `core/`-Schreibzugriff.
- **`tools/routeg`** — der Kandidat der Kontrolle **Nullprobe**
  ([`verfahren-nullprobe.md`](verfahren-nullprobe.md)): Skelett →
  Segmentgraph (`graph.py`) → Greedy-Traversierung per Gute-Fortsetzung,
  in den Stufen `prepare.py` → `recover.py` → `to_candidate.py`; eigene
  Minimalfassung der Writing-Order-Recovery nach Diaz et al. 2022, weil
  die MATLAB-Referenz hier nicht lauffähig ist (Begründung und
  Reduktions-Liste: `tools/routeg/README.md`, eigene
  `requirements.txt`). **Dieses Werkzeug wird per Doktrin nie
  optimiert** — eine Nulllinie, die mitlernt, ist keine mehr
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §7.6);
  Änderungen jenseits von Bugfixes wären eine Doktrin-Entscheidung. Sein
  Skelettgraph ist zugleich der Wasserweg des Lotsen — Bausteine wandern,
  die Kontroll-Rolle nicht.
- **`tools/docs_register`** — das Gate über den Registern der Kampagne
  (`uv run python -m tools.docs_register check [--base origin/main]`,
  CI-Job „Docs-Register“): jeder `###`-Eintrag in
  [`messjournal.md`](messjournal.md) §14 braucht seine
  Registerzeile, jede Ledger-Zeile eine Zahl, die das Journal schon
  trägt, und jeder Eintrag einer Duell-Route — seit A43 (2026-09-09) auch
  jeder der Route „Übergänge“ — die Ledger-Zeile seines
  Datums auf der Verfahrensseite. Standardbibliothek only, wie
  `tools/changelog`; liest nur committete Dateien und schreibt nichts.
- **`tools/docs_budget`** — das Gate über den **Lesekosten**
  (`uv run python -m tools.docs_budget check`, CI-Job „Docs-Budget“;
  `… report` druckt die Tabelle). Vier Regeln: (1) die Pflichtlektüre und
  jeder in `CLAUDE.md` benannte Lesepfad bleiben unter ihrem Budget — die
  Liste wird **aus `CLAUDE.md` gelesen**, nicht dort abgeschrieben, also
  hebt ein neuer Listenpunkt die gemessene Summe; (2) ein `lebend`-Doc über
  10 000 Token trägt einen Stand-Block von 12 bis 40 Zeilen, dessen Datum
  höchstens 30 Tage alt ist — die Obergrenze zählt so viel wie die untere, ein
  Block über 40 Zeilen ist eine zweite Kopie des Docs; (3) die Karte in
  [`../index.md`](../index.md) trägt genau eine Zeile je `.md`-Datei unter
  `docs/`; (4) jeder relative Markdown-Link und jeder `#`-Anker im Repo
  löst auf. Zählt **ohne Tokenizer**: ein eigener, deterministischer Proxy
  (Wortstücke, lange deutsche Komposita alle vier Zeichen geteilt, mal
  einem Kalibrierungsfaktor), damit der Job wie die anderen Doc-Gates in
  der Standardbibliothek läuft und nicht bei jedem Lauf die BPE-Tabelle von
  `tiktoken` herunterlädt. Die Budgets stehen in **Proxy**-Einheiten, also
  vergleicht das Gate Gleiches mit Gleichem; der Abgleich gegen `tiktoken`
  `o200k_base` vom 2026-09-04 steht im Modul-Docstring. Ein Budget wird
  bewusst gehoben, mit Begründung im PR — nie stillschweigend.
- **`tools/quizgen`** — generiert die Lese-Quiz-Wortbank (~500 Wörter);
  Quellen + Distraktor-Modell in [`quiz-wortbank.md`](quiz-wortbank.md).
