# Werkzeuge — die Dev-Tools unter `tools/`

> **Status (2026-08-23): lebend.** Index über die Dev-Tools unter `tools/`;
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

**`tools/laufform/inventory.py`** — die Bestandsaufnahme der gespeicherten
Laufform-Zeilen gegen ihre Tafelformen (§14 LF7/LF8/LF9): je Zeile n, die
Sprung-Ratio (`core.laufform.anchor_spike_ratio` auf der ZEILE — das
Sprung-Gate) und die Kopf-Abweichung `head°` (`core.laufform.head_deviation`,
die Landerichtung des ersten Zugs gegen die Tafel — das Kopf-Gate) neben der
Natürlichkeits-Lücke als Berichts-Spalte, dazu das datengetriebene τ der
Sprung-Ratio (Maximum der Zeilen mit n ≥ 3, aufgerundet), das
Doktrin-τ des Kopf-Gates (15°) und die Zeilen über dem einen wie dem
anderen (Spalte `gates`); `--png` zeichnet ausgewählte Zeilen über ihre
Tafelform — das Bild, das das Wort-Lineal nie ansieht.

```bash
uv run python -m tools.laufform.inventory [--root DIR] [--json out.json]
uv run --extra viz python -m tools.laufform.inventory --png inventory.png --only K,t,E
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
Die `eigenhand_*`-Tabellen fahren OHNE die PNG-Spalte mit, dazu ein
`strip_hashes`-Manifest: der Master der Streifenbilder ist der
`own-hand/`-Baum desselben Archivs, und die Hashes sind, woran ein
Restore sie prüft — und woran auffällt, wenn DB und Archiv
auseinandergelaufen sind, bevor der Tag kommt, an dem es zählt
(Wiederherstellungsweg: proposals/eigenhand-erfassung.md §8.1).
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
  damit `ingest` dagegen registrieren kann. Beide brauchen `ADMIN_TOKEN`;
  `--api` zeigt auf eine andere Instanz.
  **`sync --from <Archiv-Snapshot>`** ist der Wiederherstellungsweg: dieselbe
  Push-Logik, nur aus dem Archiv statt aus der Arbeitskopie — damit bringt
  Repo + Archiv die vier hand-gebundenen `eigenhand_*`-Tabellen samt Bildern
  zurück (Rezept und Drill: Proposal §8.1); die fünfte, das Soll-Universum,
  kommt aus ihrer eigenen Quelle (`universe --push`). Genannt wird IRGENDEIN Schnappschuss der Hand;
  seine Geschwister im selben Verzeichnis kommen automatisch dazu (neuester
  gewinnt), weil `snapshot.py` inkrementell ablegt und nur der erste
  Schnappschuss vollständig ist. Das stehende Setup wird dabei nur gesetzt,
  wenn der Server keines hat, und der Lauf bricht mit Namen ab, wenn eine
  angenommene Fassung oder ein Bogen-Layout im Archiv fehlt.
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
- **`report`** — Bestandsbericht (Erstbeleg-/Ausbau-Quote, Fehlstellen,
  Druckvorschlag); **`progression`** — die Plan-Sicht dazu: kumulierte
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
  als einen geschichteten Baum lesen, so wie `sync --from` es tut.

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
  die angefangene. `--dry-run` zeigt nur die Zahlen. Braucht `ADMIN_TOKEN`
  (`ADMIN_TOKEN=… uv run python -m tools.lesarten.sync`). Nach einem
  Wörterbuch-Update (neuer Pin in `fetch_igerman98.py` + `SOURCE.md`)
  oder einer Bank-Erweiterung einmal laufen lassen.

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
  Kategorie, fett betitelte Bullets, sonst nichts). Mit `--base` die PR-Regel
  des CI-Jobs „Changelog (fragment)": das Diff trägt ein Fragment (oder ist
  ein Release-Schnitt, der Fragmente löscht, oder rein `data/`), und
  `[Unreleased]` hat keinen direkt geschriebenen Bullet dazubekommen.
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
  OFF-HEADLINE-Kandidatenzahl, nie die Headline.
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
  am Schwärze-Vergleich mit dem eigenen Strich aus. Wächst eine Kante um
  mehr als eine x-Höhe, wird der Fall **gemeldet statt angewandt** — dann
  hängt Fremdes an der Tinte (bei `regieren` das Komma am Auslauf des
  letzten Buchstabens).
  `--report` · `--sheets <dir>` (Vorher/Nachher-Kacheln, rot/grün) ·
  `--apply` · `--registration-shift <json>`.
  **Zwei Dinge wandern mit** und dürfen nicht vergessen werden:
  gespeicherte Wortbahnen registrieren CROP-lokal, also verschiebt ein
  bewegtes `x0`/`y0` sie — `shift_registrations.py` rechnet genau den
  Ursprungs-Versatz auf `tx`/`baseline_row` (idempotent: es bewegt nur
  Zeilen, die noch besser zur ALTEN Geometrie passen; `--apply` schreibt in
  die GETEILTE DB und braucht die Zusage des Autors). Und die
  Fixture-Roots frieren die Rechtecke ein: eine reparierte Platte braucht
  einen Fixture-Re-Export plus datierten Re-Baseline-Eintrag in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §14.
- **`tools/tracebench` + `tools/pairlab/follow`** — das Lineal und der
  Mess-Kandidat des Tintenfolger-Duells
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md);
  Zahlen und Vorregistrierungen in
  [`qualitaetsmetrik.md`](qualitaetsmetrik.md) §14). Die stehende
  Mess-Liturgie einer Runde, wie sie die §14-Einträge seit `aug19`
  fahren:
  1. **Erster Akt** (Cloud-Session): `uv sync --all-extras`, dann
     `uv run python -m tools.wordbench.fetch_fixtures --set all
     --verify` (bit-exakte Abnahme der Fixture-Roots).
  2. **Folger-Lauf** (der Duell-Kette-Kandidat). **Seit Kette v5
     (`aug26`) ist der Duell-Stack der DEFAULT** — Kompositions-Soll,
     Ratsche, Zone 0,55 —, ein Lauf ohne Flags IST die Kette: BLAS
     gepinnt und `--jobs 4`, z. B. `OPENBLAS_NUM_THREADS=1
     OMP_NUM_THREADS=1 uv run python -m tools.pairlab.follow --all
     --set words --jobs 4 --json … --candidate-out …`. Die
     Archäologie-Flags reproduzieren jede ältere Basis:
     `--no-structure-guard-ratchet --structure-guard-zone 0
     --soll-source init` = der K0-Z-Soll-Stack (Basis von K0-S und
     L-U), `--no-structure-guard` = der Folger ohne Wächter
     („Kette-frei", NUR Diagnose-Arm — er deckt mehr Tinte, indem er
     Struktur zerstört, Init 86 → frei 125 Soll-Punkte). **Basis und
     Arm müssen bis auf den EINEN vorregistrierten Knopf derselbe
     Stack sein**; `k0eval` druckt beide Stacks und warnt bei
     Abweichung — zweimal in zwei Tagen (`aug25` L-U, `aug26` v5)
     wurde sonst gegen den falschen Folger gemessen. Die Arm-Flags
     (`--mark-claim` …) stehen im `--help` und je Arm in seinem
     §14-Eintrag.
  3. **dev-19-Scoring**: `uv run python -m tools.tracebench --split dev
     --candidate file --candidate-file <cand.json> --json …
     --compare <basis-report.json>` — gepaarte Deltas, Zähler, Gates.
  4. **63er-k0-Protokoll**: `uv run python -m tools.tracebench.k0eval
     <basis-cand.json> <arm-cand.json>` — referenzfrei über alle
     Wörter: Soll-Abstand je Wort (Kompositions-Soll durch
     `ductus_soll`), `aiou` gegen die eingefrorene Maske,
     Strich-Identitäts-Klassen (verglichen werden die geparsten
     Strichzüge, nicht die Datei-Bytes); ersetzt die bis `aug21` je
     Runde neu geschriebenen Scratch-Skripte. Ein Kandidat, der auf
     einer GEPATCHTEN Root gelöst wurde (Laufform-Kandidaten-Karte,
     §14 LF3b-W), wird mit `--fixtures <root>` gegen das Soll DIESER
     Root gewertet — das Kompositions-Soll wandert mit der Karte, das
     der eingefrorenen Root wäre dort das falsche Lineal; je Root ein
     eigener Aufruf, der Abstand wird von Hand nebeneinandergelegt.
  5. **Sensoren/Augenschein nach Bedarf**:
     `uv run python -m tools.tracebench.excursions <cand.json>` (das
     Papier-Exkursions-Inventar, der stehende K-D-Sensor) und
     `uv run python -m tools.tracebench.view` (die
     Duell-/Augenschein-Seite).
  Invarianten: alles reine Messschicht (nie DB/`core/`/Rendering);
  gepaarte Vergleiche gelten nur innerhalb EINER gepinnten Umgebung
  (aug16-Lehre); der Dev-Split ist eingefroren und append-never.
- **`tools/inksight`** — die Route-B-Pipeline des Tintenfolger-Duells
  ([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §4):
  drei Stufen (Crop-Vorbereitung → Inferenz im ISOLIERTEN
  Python-3.11-TF-venv → Kandidaten-JSON im Trace-Frame), Gewichte und
  venv bleiben untracked; reine Messschicht — die Ausgabe erreicht nie
  `core/`, die DB oder das Rendering.
- **`tools/quizgen`** — generiert die Lese-Quiz-Wortbank (~500 Wörter);
  Quellen + Distraktor-Modell in [`quiz-wortbank.md`](quiz-wortbank.md).
