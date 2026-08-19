# Werkzeuge — die Dev-Tools unter `tools/`

> **Status (2026-08-12): lebend.** Index über die Dev-Tools unter `tools/`;
> jedes neue, umbenannte oder entfernte Werkzeug und jede geänderte CLI
> (Flags, Modulpfade, `viz`-Extra, `--live`) gehört hier hinein.

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

Aus diesem Rahmen fällt allein der **Urteils-Durchgang** ganz unten: er
braucht kein `viz`-Extra, weil seine Ausgabe eine HTML-Seite statt eines
matplotlib-PNGs ist, und er kennt kein `--live` — was er überhaupt liest,
liest er über die deployte Lese-API. Geschrieben wird auch dort nichts.

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
```

**`tools/pairlab`** — seziert EINEN Buchstaben-Übergang gegen seine echten
Vorkommen in den Vorlagen, jeder Buchstabe UNABHÄNGIG neu eingepasst:
trennt Konnektor-Form von Platzierungsfehler und misst, wie weit die echte
Feder Schwanz/Kopf der Glyphen für den Join umformt. Befund + Optionen in
[`../proposals/uebergaenge-befund.md`](../proposals/uebergaenge-befund.md).

```bash
uv run --extra viz python -m tools.pairlab re [longs,a] [--set words|pairs|all]
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

```bash
uv run python -m tools.laufform.harvest [--style suetterlin] [--min-n 4]
    [--rmse-max 2.2] [--apply --base-url http://localhost:8000 --source-id <id>]
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
einer Runde in [`qualitaetsmetrik.md`](qualitaetsmetrik.md).

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

## Benches und Generator (Verweise)

- **`tools/glyphbench`** — bewertet jeden autorisierten Buchstaben gegen
  eingefrorene Referenzen, EIN Skript pro Lauf; Metrik + Baseline-Historie
  in [`qualitaetsmetrik.md`](qualitaetsmetrik.md).
- **`tools/wordbench`** — bewertet KOMPONIERTE Wörter/Paare gegen die
  Abb.-19/-20-Vorlagen (gleiche Hand); Metrik + Doku in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §6. Drei Module hängen
  **Report-Spalten** an, die nie in den Loss eingehen (eigener try/except,
  hinter dem stabilen Block): `slant.py` (Schräglage Vorlage vs. komponiert,
  90° = senkrecht; R5), `gleichzug.py` (Ein-Fluss-/Ein-Breite-Audit auf der
  komponierten Centerline, ohne Vorlagenbezug; `jul30`) und `pairmeas.py`
  („gemessen vs. komponiert“ — die komponierten Joins gegen die sezierten
  `pair_instances` derselben Vorlagen; `aug02`). Die Fixture-Roots frieren
  seit `aug14` zusätzlich `word_instances.json` ein — die gespeicherten
  Wortbahnen des Sets samt Frame-Gate (`frame_stale`), deren
  `authored`-Zeilen der Referenzsatz des geplanten `tools/tracebench`
  sind ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md));
  Refill ohne Re-Baseline: `--only word-instances` bzw. `--only instances`.
  Ohne Cloud-SQL-Zugang baut `fetch_fixtures.py` dieselben Roots
  byte-kompatibel über HTTPS auf — der rein lesende Zwilling von
  `export_fixtures.py`, ausschließlich GETs, mit `--verify` als
  Abnahme-Gate:
  `uv run python -m tools.wordbench.fetch_fixtures --set all --verify`.
  Zwei Overlay-Flags für Trocken-Experimente (`aug19` erstmals im
  Feld, Laufform-Arme LF1–LF3): `--laufform <datei.json>` komponiert
  mit KANDIDATEN-Laufformen (Harvest-Draft `{anchors, n_occurrences}`
  oder volle Fixture-Zeile; Overlay — unbenannte Glyphen behalten die
  eingefrorene Zeile) und `--no-laufform` komponiert chart-treu ohne
  jede Laufform. Beide liefern per Doktrin §6 eine
  OFF-HEADLINE-Kandidatenzahl, nie die Headline.
- **`tools/inksight`** — die Route-B-Pipeline des Tintenfolger-Duells
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §4):
  drei Stufen (Crop-Vorbereitung → Inferenz im ISOLIERTEN
  Python-3.11-TF-venv → Kandidaten-JSON im Trace-Frame), Gewichte und
  venv bleiben untracked; reine Messschicht — die Ausgabe erreicht nie
  `core/`, die DB oder das Rendering.
- **`tools/quizgen`** — generiert die Lese-Quiz-Wortbank (~500 Wörter);
  Quellen + Distraktor-Modell in [`quiz-wortbank.md`](quiz-wortbank.md).
