# MVP-Roadmap

Operative Zerlegung des MVP aus [`architektur.md`](architektur.md) §8 in
ausführbare Meilensteine. Sprache: Deutsch (Prosa) / Englisch (Code,
Schema, Pfade — siehe [Sprachregelung](../reference/sprachregelung.md)).

---

## Status (2026-05-21)

Die Implementierung läuft jetzt durchgängig über die Web-Admin-UI (`/app/`)
gegen das FastAPI-Backend (`/api/`) und Postgres (`/core/database/` +
`/alembic/`). Der frühere `/mvp/`-Ordner mit JSON-Files und Konsolenskripten
(`trace_skeleton.py`, `inspect_crop.py`, `render_canonicals.py`) ist aufgelöst
— alle Berechnungen passieren im Backend, alle Canonicals werden in der
`glyphs`-Tabelle gespeichert. Die unten beschriebenen Meilensteine M0–M7
bleiben inhaltlich gültig (Scope, Glyphen, Wortset, vier Validierungs-Gates
inkl. abgespeckter Animation in M7), nur das *wie* wechselt: ein neuer Trace
startet als Stylus-Strich im Editor und endet als Row in der Datenbank, nicht
als JSON-Diff.

Der MVP validiert den Render-Kern (Falsifikations-Test aus §7). Die
Endnutzer-Website mit ihren sieben Zielen in drei Clustern (Schreiben:
Einstieg · Schreiben üben + Lineatur · animierte Buchstaben-Tafel;
Lesen: Lesen üben · Lese-Hilfe via HTR inkl. Lese-Lupe; Forschung:
Stil-Analyse inkl. Hände-Vergleich · offene Datensätze; plus
Zweisprachig-Leitprinzip — siehe [`vision.md`](vision.md)) liegt fast
komplett *nach* dem MVP. Frühe Parallel-Wins laut
[`architektur.md`](architektur.md) §10: Lese-Hilfe (P1) und die
Frontend-Infrastruktur (§16) parallel zur ersten Phase.

## Context

Die Design-Docs sind abgeschlossen; der Code wächst entlang dieser
Roadmap (Stand siehe „Status" oben — Admin-UI + Backend laufen). §10
sagt: **erst der kleinste lauffähige Kern, dann alles andere.** Mit dem in §8
festgelegten Scope (Lowercase-Kern-Alphabet, sieben Wörter, ein
zusätzliches generalisiertes Wort, vier Validierungs-Gates inkl.
abgespeckter Animation) ist das kein Wegwerf-Spike mehr, sondern ein
**MVP**: vorzeigbares Render-Ergebnis statt Throwaway-Probe.
Spike-Essenz (billige Risiko-Falsifikation aus §7) bleibt erhalten —
als vier harte Gates *innerhalb* des MVP, die wie der ursprüngliche
Spike funktionieren: erfüllen sie sich nicht, ist der Kernel
falsifiziert und das Ergebnis ist trotzdem in Tagen statt Monaten
klar.

Diese Roadmap zerlegt den MVP in Schritt 0 + M0–M7, jeder Meilenstein
einzeln in einer Sitzung erledigbar, jeder mit klarem
Abschlusskriterium.

### MVP-Scope (fix, bewusst minimal)

- **6 Kleinbuchstaben** plus der ſ/s-Allograph-Split — kein Buchstabe
  mehr als nötig.
- **Keine Ligaturen** im MVP — die Ligatur-Mechanik aus §4 kommt mit
  dem Rest-Alphabet danach.
- **Großbuchstaben** explizit ausgeklammert — eigene Allograph-Klasse
  mit anderem Ductus.

### MVP-Alphabet (6 lowercase Buchstaben + Allograph-Split = 7 Glyphen)

`a · d · e · l · n · ſ · s` (ſ und s als getrennte Allographe nach §3).

Begründung: **das ist exakt das Letter-Set, das die §9-Pflicht-Anker
`lesen` und `das` brauchen** — `lesen` = {l, e, ſ, n}, `das` = {d, a, s}.
Unter sechs geht nicht, ohne einen §9-Anker zu opfern. Über sechs ist
Zusatz-Komfort, kein Muss.

### MVP-Wortset (in §9 verankert)

| Wort | Schreibweise (Kurrent) | Glyph-Beitrag |
|---|---|---|
| `lesen` | l-e-ſ-e-n | l-init, e-med ×2, ſ-med, n-final |
| `das` | d-a-s | d-init, a-med, s-final |
| `den` | d-e-n | d-init, e-med, n-final |
| `lese` | l-e-ſ-e | l-init, e-med, ſ-med, **e-final** |
| `lasen` | l-a-ſ-e-n | l-init, a-med, ſ-med, e-med, n-final |
| `als` | a-l-s | **a-init**, **l-med**, s-final |
| `dann` | d-a-n-n | d-init, a-med, **n-med**, n-final |

Generalisierungs-Wort (nicht in der Schreib-Vorlage): **`denen`**
(d-init, e-med, n-med, e-med, n-final) — alle Positionen vom MVP
abgedeckt, aber kein direkter Fit. Wird aus aggregierten Per-Glyph-Stats
in derselben Hand gerendert; beweist *Scan → Stats → beliebiges Wort
in der Hand*.

Bewusste Lücken (in §9 doc-explizit benannt): ſ-initial, d-final,
d-medial, a-final, l-final — kommen mit dem Rest-Alphabet.

### Datenstrategie: Wiederholungen statt Drills

**Per-Instanz-Statistik fällt aus Wort-Wiederholungen.** Jedes Wort
2–4× geschrieben (mehr für die §9-Kernglyphen-Träger). Aus 5× `lesen`
fallen automatisch 10 medial-e-Instanzen + 5 medial-ſ + 5 final-n
heraus, jede mit echtem Wortkontext — speist sowohl die §6-Statistik
als auch direkt M6.

Damit entfallen isolierte Glyph-Drill-Sheets („ſ ſ ſ ſ ſ"-Blätter)
komplett.

### MVP-Validierungs-Gates

Alle vier erfüllt → Kernel validiert; sonst Negativergebnis (§8
Schlusssatz: „in Tagen statt Monaten geklärt").

1. **Stabilität:** Die drei §9-Kernglyphen (medial ſ, finales s,
   medial e) zeigen über je ≥10 Fits stabile Kontrollpunkt-Cluster.
2. **Allograph-Trennung (§7):** Cross-Fit zwischen medial ſ und
   finalem s trennt sauber pro Hand.
3. **Wort-Rendering:** Die Mehrheit der sieben MVP-Wörter wird aus den
   gefitteten Templates + norm-erzeugten Übergängen erkennbar wie die
   eigene Vorlage rekonstruiert *und* `denen` (oder ein vergleichbares
   neues Wort) wird aus aggregierten Per-Glyph-Stats erkennbar in
   derselben Hand gerendert.
4. **Animation (abgespeckt):** Eines der MVP-Glyphen spielt mit korrekter
   Schreibreihenfolge ab — `stroke-dashoffset` auf der Centerline,
   konstante Breite. Voller Schwellzug-Aufbau ist Post-MVP (siehe
   [`architektur.md`](architektur.md) §11). Implementiert in M7.

Aufwand: ein bis zwei Wochenenden — bewusst klein gehalten.

---

## Schritt 0 — Doc-Pflege & Folder-Rename

*(Dieser Schritt erfolgt bei Erstanlage dieser Roadmap. Er ist hier
dokumentiert, damit der Kontext nach dem Commit nachvollziehbar bleibt.)*

Inhaltliche Änderungen `architektur.md`: §8 umbenannt und neu gefasst
(MVP-Scope inkl. Gate 3 mit `denen`-Generalisierung), §9 erweitert
(Wortset-Tabelle + Generalisierungs-Wort + bewusste Lücken), §10
Schritt 1 von „Spike" auf „MVP" umetikettiert.

Folder-Rename `/spike/` → `/mvp/`: in
[`naming-und-setup.md`](naming-und-setup.md) §3, in `pyproject.toml`
(ruff isort `known-first-party`), in [`README.md`](../../README.md), in
[`CLAUDE.md`](../../CLAUDE.md), in [`contributing.md`](../contributing.md)
und in [`data/variants/v0-loth-1866/README.md`](../../data/variants/v0-loth-1866/README.md).

Diese Roadmap (`mvp-roadmap.md`) angelegt als Repo-Referenz neben
`architektur.md`.

---

## Meilensteine

### M0 — Pipeline-Toolchain & Zweikanal-Demo

**Was:** Erstes lauffähiges Stück Code. Lade
`data/sources/loth-1866/chart.jpg`, adaptive Binarisierung, Skelett
(`skimage.morphology.skeletonize`), Distanztransformation
(`scipy.ndimage.distance_transform_edt`). Output: Overlay-PNG (Original
+ Skelett rot + Breitenprofil farbcodiert).

**Wo:** neuer Ordner `/mvp/`. Erste Datei `mvp/extract.py` +
`mvp/demo.ipynb` oder `mvp/run_demo.py`. Output unter `/mvp/out/`
(gitignored).

**Deps in `pyproject.toml` ergänzen:** `numpy`, `scipy`, `scikit-image`,
`pillow`, `matplotlib`. Optional `cairosvg` falls SVG → Raster nötig.

**Fertig wenn:** Overlay-PNG sichtbar zeigt, dass Skelett + Breitenkanal
getrennt funktionieren. Konkrete Beobachtung notieren: **bricht das
Skelett an verblassten Stellen?** (= §5 „Binarisierungsfalle" empirisch
geprüft, bevor sie auf eigene Hand zuschlägt.)

---

### M-Admin — Web-Admin-UI für Canonical-Extraktion

**Was:** FastAPI Backend (`/api/`) plus React-Frontend (`/app/`) für die
interaktive Canonical-Erzeugung. Maus zieht Bbox- und Exclude-Rechtecke
direkt auf `chart.jpg`, baseline/midband sind draggable Linien, der
Ductus-Pfad wird mit Stylus (S-Pen) auf einem Samsung-Tablet
gezeichnet. Backend liest/schreibt die existierenden Files in
`mvp/canonical/`, sodass die CLI-Werkzeuge (`mvp.tools.trace_skeleton`,
`mvp.render_canonicals`) weiter funktionieren.

**Begründung der Einschiebung:** Die ursprüngliche Reihenfolge nach §10
war „M3 zuerst, Tools danach". In der Umsetzung von M3 Phase A wurde
klar, dass das per-JSON-Eintippen von Bboxes, Excludes und
(Multi-Stroke-)Waypoints nicht auf die 8 Phase-B-Templates skaliert,
geschweige denn auf das Voll-Alphabet. Die Web-Admin-UI ist
Tool-Investition mit positivem Hebel: M3 Phase B, alle späteren
Allograph-Erweiterungen und (mit minimaler Erweiterung) das M1
own-hand-Schreiben profitieren davon.

**Architektur:** spiegelt anyplot (`~/projects/anyplot/`) — `/api/`
FastAPI mit Routern pro Resource (`health`, `chart`, `bboxes`,
`canonical`), `/app/` React + Vite + TypeScript, lokal über zwei
Terminals (`uvicorn` :8000, `npm run dev` :3000 mit `/api`-Proxy).
Dockerfiles und `cloudbuild.yaml` werden als Platzhalter angelegt für
spätere Cloud-Run-Migration; in v1 nicht ausgeführt.

**Schwellzug:** Die `half_widths` kommen weiterhin aus dem M0
Distance-Transform der Loth-Tinte — die geometrische Wahrheit kommt
vom Bild, nicht vom Tablet. `event.pressure` wird parallel aufgezeichnet
und unter `_trace.pen_pressure_raw` gespeichert (für M1
Own-Hand-Modus, wo es die primäre Schwellzug-Quelle wird).

**Fertig wenn:** Alle 11 MVP-Canonicals (Phase A + B) sind über die
Web-UI traced, identisches Schema wie CLI-Output, `mvp.render_canonicals`
zeigt sie korrekt im Side-by-Side mit Loth.

**Abhängigkeiten:** M0 (Pipeline existiert). Blockiert dann effektiv
M3 Phase B — wird stattdessen *als* Phase B durchgeführt.

---

### M1 — Eigenhandvorlagen schreiben & einscannen

Das Wortset ist mit §9 fixiert. Hier nur noch ausführen:
Wiederholungszahlen so wählen, dass die §9-Kernglyphen-Targets
erreicht werden.

**Glyph-Zielzahlen (aus dem fixen Wortset abgeleitet):**

- **medial e ≥10** → `lesen` × 5 liefert schon 10 (2 medial-e pro
  lesen); `lese` und `lasen` legen drauf.
- **medial ſ ≥10** → `lesen` × 5 + `lese` × 3 + `lasen` × 2 = 10. Oder
  einfacher: jedes der drei ſ-Wörter 4× = 12.
- **final s ≥10** → `das` × 7 + `als` × 3 = 10. Oder `das` × 10 +
  `als` × 3.
- Andere Glyph-Positionen brauchen je ≥3 Instanzen → 2–4
  Wiederholungen der übrigen Wörter reichen.

**Statistik fällt aus den Wiederholungen** — keine isolierten
Glyph-Sheets. Jede Instanz hat dabei realen Wortkontext, der den
Übergangstest in M6 mitspeist.

**Schreiben:** alle Wörter konsistent (gleicher Stift, gleiche
Beleuchtung, gleiches Papier, ≥300 DPI). Eine A4-Seite reicht
typischerweise. Pro Blatt: Wort + Wiederholungen blockweise.

**Wo:** `/data/samples/own-hand/` (bisher nicht vorhanden — anlegen):

- Eine oder zwei Bilddateien pro Wort-Cluster oder ein einziges Blatt
  mit allen Wörtern.
- `wordlist.md`: Soll- und Ist-Zählung pro `(glyph, position)`.
- `SOURCE.md`: Author = du, License = MIT/CC0, Stift, Papier, Datum
  (Pflichtfelder nach [`datenablage.md`](../reference/datenablage.md) §2).

**Fertig wenn:** Scans im Repo committet (eigenes Copyright →
committable, [`quellen-und-rechte.md`](../reference/quellen-und-rechte.md)
§2), `wordlist.md`-Sollzahlen erreicht.

---

### M2 — Glyph-Segmentierung der eigenen Hand

**Was:** Manuelle Crops jeder Glyph-Instanz aus den M1-Scans, mit
Positions-Tag (`initial`/`medial`/`final`) und Kontext-Tag (umgebende
Glyphen — für Übergangstest in M6).

**Sieb-Disziplin (Sampling-Bias vermeiden):** Anders als beim *Lesen*
(Recall-kritisch — jeder Glyph muss gefunden werden,
[`architektur.md`](architektur.md) §13) ist die Statistik
**Präzisions-kritisch**: nicht jede Instanz muss segmentiert werden, es
zählen nur genügend *saubere* pro Bucket. Mehrdeutige oder überlappende
Crops dürfen also wegfallen — die M1-Wort-Wiederholungen liefern Ersatz.
**Bedingung:** der Miss muss *zufällig* sein, nicht *selektiv*. Wer
systematisch die schwer-trennbaren — also *eng verbundenen* — Instanzen
verwirft, sampelt genau die Ko-Artikulation weg, die §4/§7 interessiert
(vorausschauender `exit`-Shift je nach Nachbar). Regel: Aussieben nur nach
**Fit-Qualität** („verrutscht/topologisch falsch = raus"), **nie** nach
Verbindungsenge („eng am Nachbarn" = Signal, nicht Müll). Gleiche Logik
wie §6 Stufe 1 (robuste Statistik), nur eine Stufe früher beim Croppen.

**Wo:** `/data/samples/own-hand/segmented/` mit Schema
`<wort>-<runde>_pos<n>-<position>-<glyph>.png`, z. B.
`lesen-03_pos03-medial-langs.png`. Index in `instances.json`: pro Crop
`{file, glyph, position, source_word, source_image, neighbors: [prev, next]}`.

**Skript:** `mvp/segment.py` (interaktives Croppen via matplotlib oder
rein manuell mit GIMP — bei dieser Menge lohnt sich ein simpler
Klick-Workflow).

**Fertig wenn:** Alle Glyph-Instanzen segmentiert; M1-Sollzahlen
tatsächlich erreicht; M0-Pipeline läuft auf jedem Crop ohne
Skelettbruch; `instances.json` validiert.

---

### M3 — Canonical-Ductus-Templates (11 Templates, handmodelliert)

**Was:** `canonical`-Einträge nach Schema [`architektur.md`](architektur.md)
§3 — handmodelliert, nicht aus Loth abgelesen. Loth-SVG nur geometrische
Referenz; der **Ductus** ist eigene Autorenleistung (§2 / Quellen-Policy §6).

**Scope v0 (fix, genau die im Wortset vorkommenden `(glyph, position)`-
Kombinationen):**

| # | Glyph | Position | Vorkommen |
|---|---|---|---|
| 1 | a | initial | als |
| 2 | a | medial | das, lasen, dann |
| 3 | d | initial | das, den, dann |
| 4 | e | medial | lesen, den, lese, lasen |
| 5 | e | final | lese |
| 6 | l | initial | lesen, lese, lasen |
| 7 | l | medial | als |
| 8 | n | medial | dann |
| 9 | n | final | lesen, den, lasen, dann |
| 10 | ſ | medial | lesen, lese, lasen |
| 11 | s | final | das, als |

**= 11 Templates.** Keine Ligatur in v0.

**Arbeitsteilung Ductus-Modellierung:**

1. **Phase A — §9-Kernglyphen** (medial ſ, finales s, medial e):
   penibel modellieren, das sind die MVP-Gate-Tragenden.
2. **Phase B — Rest** (8 weitere Templates): schneller, mit dem Wissen
   aus A.

**Datenstruktur:** Python-`dataclass` oder JSON, exakt die Felder aus
§3 (`glyph`, `position`, `variant: 0`, `canonical.strokes[]`,
`entry/exit.{xy,tangent,coupling}`). Render-Funktion: Template →
SVG/PNG für visuelle Validierung gegen die Loth-Tafel.

**Wo:** `/mvp/canonical/<glyph>_<position>_v0.json` + `mvp/template.py`
(Loader, Renderer, Schema). *Noch nicht* `/core/library/` —
Library-Split aus [Naming-Setup](naming-und-setup.md) §3 erst nach
validiertem MVP.

**Fertig wenn:** Übersichts-Render (alle 11 Templates auf einer Seite)
deckt sich grob mit den entsprechenden Glyphen auf der Loth-Tafel;
`(glyph, position, variant)`-Schlüsselung konsistent.

---

### M4 — Fit-Routine (Template → Instanz)

**Was:** Gegeben ein Canonical-Template + Skelett +
Distanztransformation einer Instanz: optimiere Template-Kontrollpunkte,
sodass die Template-Kurve nahe am Skelett liegt und die Template-Breite
zum Distance-Transform-Profil passt, mit Regularisierung gegen zu
starke Deformation (Tikhonov auf Kontrollpunkt-Verschiebung oder
ARAP-light).

**Skizze:** `scipy.optimize.minimize`, Skelett-Distanz via
`scipy.spatial.cKDTree`, Breitenresidual als zweiter Term. Bewusst
einfach — der MVP validiert das Prinzip, nicht den Optimierer.

**Wo:** `mvp/fit.py`. Output pro Instanz: gefülltes `library entry`
nach §3-Schema (`control_points`, `width_profile`, gefittete
`entry/exit`).

**Fertig wenn:** Visualisierungs-PNG zeigt für eine Einzelinstanz:
Original + Canonical (grau) + Fit (rot). Fit folgt sichtbar dem
Skelett, sprengt aber nicht die Topologie (keine Schleife öffnet sich,
keine Kreuzung dreht).

---

### M5 — Statistik, Allograph-Modellselektion & Personal-Canonical

Klar getrennt in **(A) MVP-Gates 1+2** (eng, an §9-Kernglyphen),
**(B) Breitenreport** und **(C) Personal-Canonical-Aggregation** für
Gate 3.

**(A) MVP-Validierung (Gates 1+2) — nur Kernglyphen:**

1. **Stabilität (Gate 1, ≥10 Instanzen pro Kernglyph):** Pro Template
   über seine eigenen Instanzen — Mahalanobis / Median+MAD pro
   Kontrollpunkt (Stufe 1 der Qualitätspipeline §6). Streuung
   visualisieren.
2. **Allograph-Modellselektion (Gate 2, §7-zweite-Risikoausprägung):**
   Cross-Fit zwischen medial ſ und finalem s — jede Instanz gegen
   beide Templates fitten, prüfen ob das jeweils richtige Template
   besser scoret. Pro Hand rechnen.

**(B) Breitenreport — alle 11 Templates × gefitteten Instanzen:**

3. **Positions-Abdeckung:** Pro `(glyph, position)`-Bucket: Anzahl
   Instanzen, mittlere Fit-Qualität, Ausreißer. Markiert Buckets als
   „M6-tauglich" oder „nicht tauglich".

**(C) Personal-Canonical-Aggregation (für Gate 3 / M6 Generalisierung):**

4. Pro `(glyph, position)`-Bucket: **Cluster-Mittelpunkt** (Median pro
   Kontrollpunkt, nach Ausreißer-Entfernung aus A) **+
   Abweichungs-Hüllkurve** (MAD oder Kovarianzmatrix). Das ergibt die
   „personal canonical" für *diese* Hand — eine Instanz pro Template,
   die direkt für M6 verwendbar ist, um beliebige Wörter zu rendern.
   Speichern unter `/mvp/personal/<glyph>_<position>_aggregated.json`.

**Wo:** `mvp/stats.py` + `mvp/aggregate.py` + `mvp/out/stats-report.md`
mit Plots und numerischen Ergebnissen.

**Fertig wenn:** (A) liefert klare Aussage zu beiden Gates. (B)
markiert Buckets. (C) erzeugt pro Template eine aggregierte
Per-Hand-Version, einsatzbereit für M6.

---

### M6 — Übergangskurve & End-to-End-Wortrendering (MVP-Gate 3)

**Was:** Aus gefitteten bzw. aggregierten `exit`/`entry` (Tangente +
Kopplungshöhe) die Verbindungslinie zum Folgebuchstaben generieren (§4
— kein eigenes Datum, geometrisch determiniert). Zwei Render-Klassen:

1. **Rekonstruktion der sieben MVP-Wörter:** Pro Wort die in M4
   gefitteten Per-Instanz-Templates wählen (= identische Glyph-
   Geometrie wie in der Vorlage) und mit norm-erzeugten Übergängen
   verketten. Vergleich Side-by-Side zur Vorlage.
2. **Generalisierungs-Render von `denen`:** Aus M5(C)-aggregierten
   Templates (Personal-Canonical) zusammensetzen — d-init, e-med,
   n-med, e-med, n-final. Beweist: scanned hand → aggregated stats →
   beliebiges neues Wort.

**Keine Ligatur-Klasse** im MVP — die wird erst mit dem Rest-Alphabet
(post-MVP) getestet.

**Wo:** `mvp/transition.py` + `mvp/render.py` + `mvp/out/<wort>-rendered.png`
(eines pro Wort des Sets + `denen-generalized.png`, Side-by-Side zur
Vorlage bzw. zu einem hand-geschriebenen Vergleichswort).

**Fertig wenn:** MVP-Gate 3 erfüllt — die §9-Pflicht-Anker sehen
kontinuierlich aus (kein Sprung, kein doppelter Strich an der Naht),
die Mehrheit der sieben Wörter ist erkennbar wie die eigene Vorlage,
**und** `denen` ist als plausibles Wort in derselben Hand erkennbar.
Buckets, die M5(B) als „nicht tauglich" markiert hat, dürfen schlechter
aussehen — diagnostisch, kein MVP-Fehlschlag.

---

### M7 — Animation (abgespeckt, MVP-Gate 4)

**Was:** Eines der MVP-Glyphen spielt mit korrekter Schreibreihenfolge ab.
`stroke-dashoffset` auf der Centerline, konstante Breite. WAAPI-Timeline
für die Stroke-Sequenz. Keine Schwellzug-Animation (kommt post-MVP
zusammen mit dem Canvas-2D-Stroker, siehe
[`architektur.md`](architektur.md) §11).

**Wo:** Frontend-Komponente, eingebettet in den Editor (`/app/`) als
„Animation"-Tab im EditorPage. Render-Daten kommen aus
`GET /sources/{source_id}/glyphs/{glyph_key}/diagnostic` —
**`anchors_px`** (die geordnete Ductus-Sequenz im Crop-Pixelraum) ist
die Polyline-Quelle. **Nicht** `skeleton_polyline_px`: das Feld trägt
die unsortierten Skelett-Pixel aus `np.where(skel)` und ergibt als
SVG-Pfad nur eine Pixelwolke (siehe
[`reference/animation-rendering.md`](../reference/animation-rendering.md)).

**Skizze:** Eine React-Komponente, die `anchors_px` aus dem
Diagnostic-Endpoint nimmt, einen SVG-`<path>` (`M ax0 ay0 L ax1 ay1 …`)
baut, dessen `stroke-dasharray` = Pfadlänge und `stroke-dashoffset` von
Pfadlänge auf 0 animiert wird. Play-/Pause-/Replay-Buttons;
Geschwindigkeit einstellbar (200 ms bis 2000 ms pro Stroke). WAAPI über
`element.animate(...)`.

**Fertig wenn:** Eines der MVP-Glyphen (vorzugsweise eine
Pflicht-Anker-Glyph: medial ſ, finales s oder medial e) spielt ab — Klick
auf einen Play-Button startet die Animation, der Strich entsteht in
sichtbarer Reihenfolge. Demo-Wirkung steht; voller Schwellzug-Aufbau ist
ausdrücklich nicht im Scope.

**Abhängigkeiten:** M3 Phase A (Templates für mindestens eine
Pflicht-Anker-Glyph vorhanden). Kann parallel zu M4/M5 laufen, weil es
nur die Centerline visualisiert, keinen Fit nutzt. Idealerweise nach M3
Phase A, damit echte Daten zum Animieren da sind.

---

## Kritischer Pfad & Parallelisierung

```
M0 ──┬──► M2 ──► M4 ──► M5 ──► M6
M1 ──┘                    ▲
M3 (Phase A) ──────┬──────┘
                   └──► M7
M3 (Phase B)
```

**Sofort parallel startbar:**

- **M0** (Coding-Session am Rechner).
- **M1** (Pen-on-Paper, offline, parallel zwischen Coding-Sessions).
- **M3 Phase A** (Kernglyphen-Templates, mit der §8/§9-Doc als Spec).

M2 erst, wenn M1 fertig. M4 fasst alles zusammen. M5/M6 sequenziell.
M7 (Animation) hängt nur an M3 Phase A — kann sehr früh parallel zu
M4/M5 starten, weil es nur die Centerline-Visualisierung braucht.

---

## Kritische Dateien & Wiederverwendung

**Existiert, als Input für den MVP:**

- [`data/sources/loth-1866/chart.jpg`](../../data/sources/loth-1866/chart.jpg),
  [`chart.svg`](../../data/sources/loth-1866/chart.svg) — geometrische
  Referenz für M0 und M3.
- [`pyproject.toml`](../../pyproject.toml) — `dependencies = []`; M0
  ergänzt.

**Wird angelegt:**

- `/mvp/` — gesamter MVP-Code.
- `/data/samples/own-hand/` — laut
  [`datenablage.md`](../reference/datenablage.md) §1 vorgesehene Lage;
  `SOURCE.md` pro Unterordner Pflicht.

**Schema-Referenz (1:1 abbilden, nicht neu erfinden):**

- [`architektur.md`](architektur.md) §3 — library-entry-JSON ist genau
  das Zielformat für M3 (`canonical`) und M4 (`control_points`/
  `width_profile`/`entry`/`exit`).

---

## Verifikation

| Schritt | Was geprüft wird | Wie |
|---|---|---|
| M0 | Skelett + Breitenkanal trennbar, §5-Falle beobachtet | Overlay-PNG mit Auge prüfen |
| M1 | Alle sieben Wörter geschrieben, `wordlist.md`-Sollzahlen erreicht | Zählung + M0 auf einen Crop |
| M2 | Alle deklarierten `(glyph, position)`-Buckets erreicht | `instances.json`-Bucket-Counts; M0 auf alle |
| M3 | Alle 11 Templates vorhanden, plausibel gerendert | Übersichts-Render, Vergleich mit Loth |
| M4 | Fit folgt Skelett ohne Topologiebruch (Stichprobe) | Original vs. Fit-PNG |
| M5(A) | MVP-Gates 1+2: stabile Kernglyph-Cluster, ſ/s trennbar | Numerischer Report |
| M5(B) | Welche Glyphen M6-tauglich | Bucket-Report |
| M5(C) | Personal-Canonical pro Template aggregiert | `mvp/personal/`-Inhalt + Render |
| M6 | MVP-Gate 3: Pflicht-Anker kontinuierlich, Mehrheit der 7 Wörter erkennbar, `denen` aus Stats plausibel | Side-by-Side-PNGs |
| M7 | MVP-Gate 4: ein MVP-Glyph spielt mit korrekter Schreibreihenfolge ab | Demo im Editor (Play-Button → Centerline-Animation) |

**MVP-Gesamtverifikation:** alle vier MVP-Gates erfüllt (Stabilität,
Allograph-Trennung, Wort-Rendering inkl. Generalisierung, Animation
abgespeckt).

---

## Was diese Roadmap explizit aufschiebt

- **Großbuchstaben** — eigene Allograph-Klasse mit anderem Ductus.
- **Alle Ligaturen** des closed set (ch, ck, tz, ſt, qu, ß) — kommen
  mit dem Rest-Alphabet, sobald die nötigen Buchstaben dazukommen.
- **Restliche Kleinbuchstaben** (b, c, f, g, h, i, j, k, m, o, p, q,
  r, t, u, v, w, x, y, z + ä, ö, ü, ß) — Erweiterung nach validiertem
  MVP.
- **ſ in initial-Position** — kein Wort des 6-Buchstaben-Sets startet
  mit ſ. Kommt automatisch mit dem Rest-Alphabet (`ſie`, `ſehen`, …).
- **[architektur.md](architektur.md) §10-Schritte 2–7:** Extraktions-
  Tool als Produktivsystem, formale Bibliothek unter `/core/library/`,
  Verbindungs-Engine als Modul, dreistufige Qualitätspipeline
  vollständig (M5 ist nur Stufe 1, ohne Closed-Loop/Handkuratierung),
  Lese-Feature, Übe-Schleife.
- **Korpus-Statistik** aus Zenodo — erst nach eigener Hand
  ([`datenablage.md`](../reference/datenablage.md) §4).
- **Multi-Hand / Multi-Stil** — nach MVP, wenn der Varianten-
  Auswahlvektor steht (architektur.md §10 Multi-Stil-Konsequenz).

**Pre-MVP-Hygiene auch aufgeschoben:**
[`data/DATA_PROVENANCE.md`](../../data/DATA_PROVENANCE.md)-Index
aktualisieren (kommt automatisch beim Hinzufügen von
`/data/samples/own-hand/` in M1). `.gitignore` für `mvp/out/` bei M0
mitnehmen, trivial.
