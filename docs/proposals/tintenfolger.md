# Tintenfolger: der Prüfstand und die zwei Routen zur Wortbahn

> **Status (2026-08-15): Das Duell ist komplett, der Optimierungsplan
> steht in §7.** Alle Stufen der Leiter sind gemergt (#337–#356): die
> Baseline eingefroren (`dtw_xh` 0,062 med, Strukturzähler v2.1),
> die Arme ①⑤⑥⑥b⑨ gemessen (alle ehrliche Negative; Route-A-Fazit
> aus Arm ⑨: der Kettenfit steht am struktur-sicheren Optimum DIESER
> Formulierung), Route G als prior-freie Kontrolle (dtw 0,82 = 13×
> Kette — was der Duktus-Prior kauft), InkSight-T0 roh gemessen
> (derender 0,096 = 1,5× Kette, Kreuzungen sauberer, Retraces
> verloren). Kein `FOLLOW_*`-Default adoptiert. Die nächste Kampagne
> ist §7: der Optimierungsplan je Verfahren (Befund-Matrix +
> Recherche-Runde 2026-08-15, vier parallele Agenten).
> Ursprünglicher Plan-Kopf: Dieses
> Doc ist der fortschreibbare Plan zum §6-Nachtrag „Tintenfolger" in
> [`../research/bildsynthese-und-stiftbahn.md`](../research/bildsynthese-und-stiftbahn.md):
> das automatische Nachfahren der Wortproben (heute der Stage-B-Kettenfit)
> soll messbar besser werden, gemessen an einem manuell nachgefahrenen
> Referenzsatz — und zwei Routen treten dabei gegeneinander an. Baseline-
> Zahlen und Rundenergebnisse werden in
> [`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md)
> (neuer §14) geführt; dieses Doc trägt Plan, Stand und Entscheidungen.
> Jede Behauptung über Fremdsysteme/Metriken wurde in einer Recherche-Runde
> (2026-08-14, vier parallele Web-Agenten) gegen die Primärquellen geprüft;
> die Korrekturen sind eingearbeitet und unter „Verworfen / korrigierte
> Annahmen" festgehalten.

## 1 Ausgangslage

Alle automatischen Wortbahnen (`word_instances`, Provenienz `traced`) sind
Ausgaben des Kettenfits (`tools/pairlab/chain.py` via
`tools/laufform/harvest.py --path chain`). Der Kettenfit ist ein
**Mess-Fit**: seine Regularisierung zieht die Bahn absichtlich Richtung
Vorlagenform, damit die Hand-Statistik robust wird — als Tintenfolger war
er nie gedacht, und der Owner beurteilt ihn dort als „weit weg von
perfekt". Ein Kandidat kann nicht sein eigener Maßstab sein
(bildsynthese-und-stiftbahn.md §6 Nachtrag), deshalb war der erste
Handgriff Handarbeit:

**Der Referenzsatz.** Am 2026-08-13 hat der Autor 10 Abb.-19-Wörter im
Wort-Editor (Werkbank W3) per S-Pen nachgefahren, gespeichert als
`provenance: "authored"` (von keiner Re-Ernte überschreibbar):

> die · laden · linken · mit · muß · und · unter · Wer · will · zwei

Das ist der eingefrorene **Entwicklungssatz** (`TRACEBENCH_DEV_IDS`,
append-never). Jedes SPÄTER nachgefahrene Wort ist per Definition
**Bestätigungsmaterial** (Reserve-Muster der humanbench-Methodik) und
wandert nie in den Dev-Satz — so bleibt prüfbar, ob ein Folger-Gewinn echt
ist oder Anpassung an die ersten 10 Wörter. Abdeckungslücken des Dev-Satzes
(bewusst benannt): kein Umlaut-Wort, kein langes ſ, nur ein Versal; genau
die stehen im Autoren-Brief für den Bestätigungssatz (Todoist).

**Die zwei Routen:**

- **Route A — der prior-geführte Weg:** Kettenfit als Initialisierung
  (Topologie, Strichfolge, Kreuzungsauflösung aus dem Duktus-Prior), darauf
  eine neue **Verfeinerungsstufe**, die die Form-Regularisierung Richtung
  Vorlage löst und die Bahn auf das gemessene Skelett zieht — „Geometrie
  ganz aus der Tinte, Ordnung ganz aus dem Prior". Kein GPU, kein
  Fremdmodell.
- **Route B — der gelernte Weg:** InkSight Small-p (Apache 2.0, offene
  Gewichte), zuerst roh als T0-Prüfstein (dokumentiert die
  Out-of-Distribution-Lücke); danach NICHT das ursprünglich angedachte
  Fine-Tuning (unmöglich, siehe §5), sondern perspektivisch ein kleines,
  eigenes Trajektorien-Modell auf Engine-Paaren (GPU: RTX 4090 vorhanden,
  sobald der PC läuft).

Beide Routen liefern Kandidaten im selben Frame und werden auf demselben
Prüfstand gemessen; später ist auch ein **Fusions-Kandidat** denkbar
(Übereinstimmung = Konfidenz, Widerspruch = Prüfstelle — die wertvollste
Handarbeit wandert an die informativsten Stellen). Die Duktus-Wahrheit
(Ordnung, Richtung) bleibt dabei IMMER beim Prior: gelernte Bahnen sind
Geometrie-Material, nie Duktus-Quelle.

## 2 Der Prüfstand (`tools/tracebench`)

### 2.1 Der Vergleichs-Frame (tragende Entscheidung)

Gespeicherte `(u,v)`-Trace-Koordinaten sind NICHT kanonisch: `tx` stammt
aus der Composer-Grid-Search (±0,6 xh, bewegt sich mit dem Composer), und
der Editor faltet `ty` (±4 px) in `baseline_row`. Ein Vergleich in den
eigenen Labels meldet Registrierungs-Buchhaltung als Nachfahr-Fehler.
**Bench-Frame = Crop-Pixelgitter, re-expressed in xh, abgeleitet NUR aus
den eingefrorenen Fixture-Daten** (`word.json`: `xh = baseline_y −
midband_y`, `baseline_row = baseline_y − rect[1]`). Jede Bahn — Referenz
UND Kandidat — wird über ihre EIGENE Registrierung zurück nach Crop-px und
dann in den Bench-Frame gemappt.

### 2.2 Das eingefrorene Referenz-Artefakt (Stufe A — gebaut)

`fixtures/<style>/<source>[-set]/word_instances.json` neben
`pair_instances.json` (gleiches Muster: `{hand_id (modal), rows[...]}`,
atomarer Write, `--only`-Refill): ALLE Zeilen des Sets, `authored` wie
`traced`, lean projection `WORD_MEASUREMENT_KEYS = (registration_px,
xh_px, fit_path)`. Dazu das **Frame-Gate** — die #334/#336-Fehlerklasse
(Rect unter gespeicherter Bahn editiert) als Maschinencheck:
`|baseline_row+ty − (baseline_y−rect[1])| ≤ 4 px` und `|xh_px −
(baseline_y−midband_y)| ≤ 0.51`; Fehlschlag stempelt `frame_stale` mit
Grund, nie gedroppt (excluded-and-counted). Beim `--only`-Refill prüft das
Gate gegen die EINGEFRORENEN `word.json` des Roots (über deren Crop
zeichnet der Bench), nicht gegen das heutige Sidecar — der Live-Beweis am
Bautag: gegen die alten Roots (2026-07-31) stempelte es exakt die vier
#334/#336-Zeilen (`ein`, `einen`, `regieren`, `zwei`).

### 2.3 Die Maße (Stufe B — nach Recherche korrigiert definiert)

Keine Referenz-Implementierung existiert im Feld (PEN-Net-Repo enthält nur
Trainingscode, TRACE hat keins); Validierung daher über synthetische
Verzerrungen nach PEN-Nets eigenem Rezept, und **kein Kriterium
referenziert publizierte Zahlen**.

- **`dtw_xh`** (Headline, EIGENER Name): unconstrained DTW, euklidisch in
  Bench-xh, forward-only (Richtung ist Duktus-Wahrheit; report-only
  `dtw_reversed_better`), normalisiert durch die Länge des optimalen
  Warping-Pfads (= PEN-Nets LDTW-Normalisierung), beide Seiten vorher
  arc-length-resampelt (Schrittweite: Start 0,02 xh, einmaliger
  dokumentierter Sweep 0,02/0,03/0,05). Nicht vergleichbar mit
  publizierten LDTW-Werten (Resampling + xh-Einheit) — deshalb eigener
  Name. QC-Spalte `dtw_max_absorption` (Singularitäts-Wächter).
- **`aiou`** (papertreu, gegen die TINTENMASKE): Kandidat 1 px gerastert
  (Pen-Lifts nie überbrückt), 3×3-Dilatation iterativ bis IoU maximal —
  gegen `ref_mask.png`, NICHT gegen eine Referenzbahn. Funktioniert
  dadurch auf allen 63 Wörtern ohne Nachfahrung. Publizierte
  Größenordnungen (0,45–0,55 CASIA-Zeichen; ~0,75 Diffusion 2026) sind
  auflösungs- und skriptabhängig und NIE Zielwerte.
- **Chamfer, getrennt in beide Richtungen** (TRACE-Präzedenz):
  `chamfer_cand_ref_xh` (Precision) und `chamfer_ref_cand_xh` (Recall —
  ein fehlender i-Punkt bläht NUR diese Hälfte). Kein symmetrisches
  Mittel als Headline.
- **Strich-Behandlung:** Marken (i-Punkt/-Strich, Umlaut, u-Deckstrich —
  Klassifikation via `DIACRITIC_MIN_Y` + Bogenlänge ≤ 0,8 xh) werden vor
  dem Body-DTW herausgelöst (Delayed-Strokes-Praxis; entschärft zugleich
  die Deferred-Diakritika-Ordnungsfalle der Engine) und per Zentroid mit
  Refusal gematcht: **`marks_missing` ist Co-Primär-Gate**, mit gutem
  Body-DTW nicht rückkaufbar. Body beider Seiten in Schreibreihenfolge
  konkateniert (die Reihenfolge ist die Wahrheit); Pen-Lifts bleiben
  AUSSERHALB der DTW-Kosten → Spalten `lift_delta`, `lift_pos_err_xh`.
- **Fehlerzähler an den harten Stellen** (Kontrakt: detect auf beiden
  Seiten, Match mit Refusal, `ref/cand/matched/missing/spurious/pos_err`):
  Schleifenkreuzungen (`landmarks.landmark_crossings`, Schwellen
  unverändert, Match 0,55 xh), Marken (s. o.), Retrace-Segmente
  (`core.geometry.detect_retrace_pairs`, robusteste Zahl
  `retrace_arc_ratio`).
- **Einmaliger Richtungs-Audit** der authored-Bahnen gegen die
  Duktus-Richtung des Priors (Forward-only-DTW macht Richtungs-Willkür
  der Nachfahrung sonst zu Modellfehlern); Abweichung =
  Fixture-Qualitätssignal, nicht Kandidatenfehler.
- **Benannte Vertagungen:** semantische Read-back-Spalte (Lexikon-argmin
  über `score_word`), Subsequenz-DTW-Strichmatching, pfad-constrained
  LDTW, Wordbench-AIoU-Spalte (anderes Objekt, eigenes Issue).

### 2.4 Harness, Kandidaten-Kontrakt, Split (Stufe C)

CLI `uv run python -m tools.tracebench.run [--split dev|confirm|all]
[--candidate chain|authored|traced|file] [--compare …]`. Ein Kandidat ist
wörtlich eine `word_instances`-Zeile (Strokes + Registrierung + xh) —
Bench-Input = Produkt-Speicherformat; File-Provider mit Pflicht-Literal
`"frame": "word_registration"` + Schema-Bounds-Validierung. Provider:
`chain` (Baseline — läuft über den Harvest-Codepfad selbst, nie eine
Nachbildung), `authored` (Identitäts-GATE: dtw=0, alle Zähler matched,
sonst ist das Lineal kaputt und keine Zahl wird gelesen), `traced`, `file`
(Folger/InkSight). `TRACEBENCH_DEV_IDS` = die 10 oben, committete
Konstante, append-never; `--split confirm` verweigert unter 5 Wörtern;
Startup-Assertion: jede Dev-Id muss authored und nicht-frame-stale im
Artefakt sein, sonst harter Fehler.

**Kriterien (relativ, vorregistriert in qualitaetsmetrik §14 VOR der
ersten Zahl):** Primär `dtw_xh`-Median der gepaarten Differenzen vs.
Chain-Baseline ≥ 20 % Fall; Co-Primär-Gates `marks_missing` und
`cross_missing+spurious` ohne Netto-Anstieg; Kosten-Wächter (p90 ≤ +10 %,
`aiou` fällt nicht, Recall-Chamfer fällt nicht, `retrace_arc_ratio`
entfernt sich nicht von 1); Sanity `dtw_reversed_better = 0`. **Ein
Strukturdefekt vetot jeden Distanzgewinn.** Kill: Gewinn überlebt den
Bestätigungssatz nicht → verworfen; Marken/Kreuzungen verloren →
verworfen, nicht nachgestimmt. Mit dem Commit der ersten Baseline-Tabelle
friert das Lineal (Metrik-Module, `landmarks.py`, `core/geometry.py`,
Fixture-Roots) — jede spätere Änderung ist eine datierte Re-Baseline.

## 3 Route A: die Verfeinerungsstufe (`tools/pairlab/follow.py`)

**Formulierung: re-linearisierender Restart, KEIN Snake.** Zweiter Solve
auf einem NEU gebauten `_ChainProblem`, Init-Anker = Chain-Optimum
(`respec_from_solution`): frische Spline-Parameterisierung (die
Chord-Parameterisierung friert heute an den Canonical-Ankern — nach
0,75-xh-Deltas genau dort stale, wo der Fit am härtesten arbeitete),
frische Landmark-Korrespondenz, eigenes Reisebudget relativ zum
Chain-Optimum. Im Rebuild wird der Tikhonov-Term zu δ vom Chain-Optimum =
**Proximal-/Trust-Region-Term**, kein Form-Prior mehr — das IST „die
Form-Regularisierung Richtung Vorlage lösen". λ_prox bleibt > 0 (der
EDT-Term hat entlang des Grats Null-Gradient; λ=0 ist die dokumentierte
Zick-Zack-Degenerierung, als Charakterisierungstest gepinnt). Ein dichter
Snake kauft bei ~1,5-px-Ankerabstand auf ~4-px-Strich KEINE Auflösung und
verlöre Width-Term und Landmark-Op — die zwei Kreuzungs-Auflöser.

**Geschärft nach Recherche:**

- **Retrace ist der blinde Fleck beider Datenterme** (Reverse-Coverage ist
  von EINEM Pass über doppelt beschriebene Tinte befriedigt; Ridge-Pull
  belohnt den Kollaps beider Pässe auf den Grat; nur der Form-Prior
  unterscheidet sie): Retrace-Zonen (Detektor auf der Init-Bahn) behalten
  volles λ.
- **Width als Modulator, nicht Residual** (eigener Arm): publizierte
  Praxis RELAXIERT die Zentrierung, wo die Breite lokal hoch ist
  (Kreuzungen/Retraces — dort verdoppelt sich die gemessene Breite; ein
  Konsistenz-Residual kämpft gegen die richtige Antwort).
- **Landmark-Ziele = extrapolierte Schnittpunkte der einlaufenden
  Centerlines**, nicht rohe Skelett-Branch-Points (publizierte
  Junction-Unsicherheit ≈ lokale Strichdicke, ±2–4 px > Ankerabstand);
  Kalibrierung im eigenen vorregistrierten A/B.
- **Mechanik ehrlich:** Die Chain-Anker liegen schon in der Haarlinie zur
  TINTE — die Gewinne kommen aus STRUKTUR (Drift −0,5 xh, Kreuzungshöhen
  0,202 xh), und genau die sieht der Bench, weil er gegen die NACHFAHRUNG
  misst. `stranded_anchors` ist Pflicht-Kostenspalte (§11a: Coverage 32×
  anti-aligned — Reg-Release dreht die Strandungskraft auf); λ_prox wird
  aus den gemessenen Term-Verhältnissen am Solve-1-Optimum kalibriert
  (`gradlab`), nie als „klein" behauptet; Akzeptanz entscheidet NIE das
  DT-Residual, das der Solve selbst minimiert — nur der Bench.

**Arme (einer je Runde, v1 ändert genau EINE Sache: reg→prox):**
① λ_prox {0 · 1 % · 10 % · 50 % von e_geo · 1.0-Kontrolle} ② rounds
③ samples/Anker ④ coverage (Kostenspalte stranded) ⑤ overlap {0.2, 0}
(§13-Bremse-Hypothese) ⑥ landmark · ⑥b klassenbewusste Korrespondenz
(die vorregistrierte Antwort auf die Korrespondenz-Kappe des
⑤/⑥-Befunds) ⑦ width-Modulator ⑧ bind (zuletzt, nur
bei überlebendem Zick-Zack, mit §11d-Nachmess-Pflicht). Erwartete
Fehlermodi je Wort stehen in §14; Kill-Kriterien s. dort.

**Leitplanken:** strikt additiv/opt-in; `KS_FOLLOW_*` bewegt nie
`CHAIN_*`; Chain-Solves byte-identisch (Test); Harvest bekommt in diesen
PRs keinen Folger-Pfad; `instances`/`letter_gate`/`pair_aggregates`
unberührt. Späterer DB-Schrieb: eigener PR, Owner-Go, `dbsnapshot`
vorher; Empfehlung `provenance: "traced"` + `fit_path: "follow"` — **nie
`authored`** (reserviert für die menschliche Hand; die API-Protection
hält den Folger von seiner eigenen Ground Truth fern).

## 4 Route B: InkSight T0 (`tools/inksight/`)

Isoliertes Python-3.11-venv (tensorflow-text-Wheels sind die Bindung),
`tensorflow-cpu==2.20.0` + `tensorflow-text==2.20.1`, **XLA-Flags aus
InkSights `utils/tensorflow.py` VOR dem TF-Import** (TF ≥ 2.18 ändert
sonst still die erzeugte Bahn — für ein Messprojekt der schlimmste
Fehlermodus). Laden über das GCS-Zip `small-p-cpu.zip` +
`tf.saved_model.load` (der dokumentierte `from_pretrained_keras`-Weg ist
mit huggingface_hub v1.0 tot). Drei Stufen, damit keine Dependency
kreuzt: `prepare.py` (Repo-venv: Crops + Engine-Render + lateinisches
Kontrollwort + 2–3 unnachgefahrene ſ-Wörter → PNGs + `frames.json`) →
`run_inksight.py` (TF-venv; alle DREI Prompts je Crop, insbesondere
`"Derender the ink: <wort>"` mit unserem perfekten Text; Token-Zahl
loggen, Decoder-Kontext ≈ 500 Punkte) → `to_candidate.py` (Affine exakt
invertieren, **Quantisierungsschritt des 225er-Token-Gitters in Crop-px
je Wort mitreporten**, Umrechnung über dieselbe Funktion wie der Folger).
Strokes EXAKT wie emittiert — keine Säuberung. CPU-Laufzeit ist unbelegt:
erste halbe Stunde MESSEN; pathologisch → 4090 (Ada, vom sm_120-Bug nicht
betroffen) oder GPU-Stunde. InkSight-Geometrie bleibt in `tools/`
(Messschicht) — nie `core/`, DB oder Rendering (deckt sich mit der
Ethik-Notiz der Model-Card).

### 4b Route G — der prior-freie Kontrollkandidat (Owner-Entscheid 2026-08-14)

Als dritter Kandidat kommt der lernfreie geometrische Klassiker aufs
Duell: Skelett → Segmentgraph → Kreuzungsauflösung per Gute-Fortsetzung
(Diaz et al. 2022, Writing-Order-Recovery, Code offen — Quellen im
Recherche-Doc §8). Seine Rolle ist nicht „Konkurrent", sondern
**Kontrolle**: Er rät Ordnung und Astwahl OHNE den Duktus-Prior — die
Differenz zwischen ihm und dem Kettenfit auf denselben 10 Wörtern
beziffert erstmals, wie viel der Prior wirklich kauft (architektur.md §2
als gemessene Zahl statt Architektur-Glaube; schlägt der Kettenfit ihn
NICHT klar, ist das ein Befund erster Güte). Anschluss über den
Kandidaten-Kontrakt (§2.4, eigener `--candidate-file`, isoliertes
Tool-Verzeichnis nach dem `tools/inksight`-Muster), kein GPU; nach der
Baseline, unabhängig von Folger und InkSight.

**Nachtrag 2026-08-14 — der Referenz-Code ist MATLAB, die Kontrolle ist
darum eine eigene Minimalfassung (`tools/routeg`):**
<https://github.com/gioelecrispo/wor> trägt eine echte
**MIT-Lizenz** (LICENSE-Datei, „Copyright (c) 2020 Gioele Crispo") — die
Lizenz ist NICHT die Schranke. Die Schranke ist die Laufzeit: 234
`.m`-Dateien, **MATLAB 2016a+ mit der Image Processing Toolbox**, kein
PyPI-Paket, kein `setup.py`, keine Octave-Zusage (classdef mit
`persistent`-Settern, `+logging`-Paketordner); dazu ein unlizenziertes
`SalernoSkeletonization.jar` im Baum (quellen-und-rechte.md: die Lizenz
folgt den Bytes — nicht vendorn). Letzter Commit 2022-10-06, ein offener
PR seit ~4 Jahren. Weder MATLAB noch Octave existieren hier oder in CI,
also wäre eine `wor()`-Zahl von niemandem reproduzierbar, der die Gates
dieses Repos laufen lässt. Statt eine Abhängigkeit zu erfinden oder den
Kontroll-Platz leer zu lassen, füllt ihn die **eigene Minimalfassung**:
Skelett → Segmentgraph (benachbarte Verzweigungspixel = EIN Knoten, der
„Cluster" des Papiers) → Greedy-Traversierung per Gute-Fortsetzung, drei
Entscheidungen (linkester Endpunkt · ein Skalarprodukt am Knoten ·
Absetzen bei Sackgasse). Die Tür zum echten Lauf bleibt offen:
`prepare.py` schreibt genau das dokumentierte `wor()`-Eingabeformat (vor-
gedünntes, 8-verbundenes PNG, Tinte = 0). Bewusst NICHT übernommen sind
die gewichtete `π_ij`-Fortsetzung samt Cluster-Rang-Klassifikation und
Dijkstra durch den Cluster — und vor allem der **gelernte
Startpunkt-Prior** `statisticalInitialPointComputed.mat` (2-D-Gauß, auf
SigComp2009-UNTERSCHRIFTEN gefittet): eine Kontrolle, die eine gelernte
Tabelle borgt, ist nicht mehr prior-frei. Ehrlich mitgesagt: Die
publizierte Abstimmung und Auswertung von WOR ist durchweg auf
Unterschriften, und das Papier nennt die Dünnungsqualität selbst als
begrenzenden Faktor — verbundene deutsche Kurrent ist härter als alles
dort Gemessene. Zahlen des Kontrollaufs in
[`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md)
§14, Rezept und Provenienz in `tools/routeg/README.md`.

### 4c Duell-Ansicht + Chronik (Owner-Wunsch 2026-08-14)

Die Verfahren sollen SICHTBAR gegeneinander stehen — nicht nur als
Zahlenzeilen: **`tools/tracebench/view.py`** rendert je Wort alle
Kandidaten als schaltbare Ebenen über dem echten Crop, die
Hand-Nachfahrung immer als grüne Referenz (zuletzt gezeichnet, damit
kein Kandidat sie überdeckt), mit Zahlenleiste je Kandidat — und einem
Play-Knopf, der alle sichtbaren Bahnen SYNCHRON in Schreibreihenfolge
animiert (`stroke-dashoffset`, konstante Stiftgeschwindigkeit in xh,
Absetzen als echte Lücke; die MVP-Animationsdoktrin aus
animation-rendering.md). Ein selbst-enthaltenes HTML, deterministische
Bytes, kein CDN.

**Chronik:** Jede Optimierungsrunde wird als create-only Snapshot
außerhalb des Arbeitsbaums abgelegt (`tools/tracebench/chronik.py`,
dbsnapshot-Disziplin: Wurzel neben dem privaten Archiv-Klon, nie
löschen/überschreiben, leere Snapshots verweigert, INDEX.md je Zeile)
— Bahndaten sind gelernter Datensatz und bleiben per Open-Core-Regel
aus dem Repo. Benanntes Fernziel des Owners: eine öffentliche
Website-Seite, die das Verfahren grob erklärt und mit kuratierten
Beispielen aus dieser Chronik visualisiert, was die Schritte waren —
eine bewusste Produkt-Flächen-Entscheidung wie `/write`, getroffen
DANN, nicht implizit jetzt.

## 5 Verworfen / korrigierte Annahmen

- **„Small-p auf der 4090 fein-tunen" — verworfen (2026-08-14):** Es gibt
  keinen Trainingscode und wird keinen geben (Autoren: PaLI-Stack nie
  open-source, Release „unlikely"; frozen SavedModel; keine
  Community-Fine-Tunes). Ein Fine-Tune hieße ViT-B/16 + mT5-base
  reimplementieren — ein eigenes Forschungsprojekt. Ersatzrichtung: nach
  T0 ein kleines, EIGENES Trajektorien-Modell auf Engine-Paaren
  (Cursive-Transformer-Präzedenz: ~3.500 Wörter genügen); Gewichte auf
  DB-Inhalten bleiben per Open-Core-Regel außerhalb des Repos.
- **„LDTW = auf 512 Punkte resampeln und durch 512 teilen" — verworfen:**
  PEN-Nets LDTW ist unconstrained DTW geteilt durch die Länge des
  OPTIMALEN Pfads. Unsere Headline übernimmt genau diese Normalisierung
  und heißt `dtw_xh`, weil Resampling + xh-Einheit sie trotzdem
  unvergleichbar mit publizierten Werten machen.
- **„AIoU = beide Bahnen mit gemessenem Halbbreiten-Radiusfeld sweepen" —
  verworfen:** Das Paper vergleicht die PREDICTION per
  argmax-3×3-Dilatation gegen die TINTENMASKE des Bildes; ein
  Halbbreiten-Radiusfeld würde den bewusst getrennten Breiten-Kanal in
  die Geometriezahl zurückkoppeln und wäre kein AIoU. Wir implementieren
  papertreu gegen `ref_mask.png` — was die Spalte nebenbei auf alle 63
  Wörter ohne Nachfahrung ausdehnt.
- **Symmetrisches Chamfer-Mittel als Begleitzahl — verworfen:** Es
  maskiert genau die Asymmetrie (fehlende Marke → nur Recall-Hälfte),
  die das Marken-Gate braucht; beide Richtungen werden getrennt geführt.
- **Ein einziger gewichteter `trace_loss` — verworfen:** Ein erfundenes
  Gewicht zwischen „0,02 xh Body-Fehler" und „ein fehlender i-Punkt"
  wäre eine Zahl, die niemand gemessen hat; deshalb Co-Primär-Gates
  statt Loss-Faltung.

## 6 Stand & Leiter

| Stufe | Inhalt | Stand |
|---|---|---|
| **A** | `word_instances.json`-Artefakt + Frame-Gate (Exporter + Fetcher), deklarierter Fixture-Re-Export (Re-Baseline nach #334/#336), dieses Doc | **PR #337** |
| **B** | `tools/tracebench`-Lineal (Metriken + Zähler + Split) + Vorregistrierung §14 + Glossar | **PR #339** |
| **C** | Harness + Provider + authored-Gate + erste Baseline-Tabelle (= Freeze-Akt; Kette: dtw 0,062 med · 19 erfundene Kreuzungen · Retrace-Ratio 1,51) | **PR #341** |
| **D** | **Duell-Ansicht** (alle Kandidaten + Hand-Referenz über dem Crop, final UND als Schreib-Animation) + **Chronik** (create-only Rundenhistorie, dbsnapshot-Muster) | **PR #344** |
| **1** | `tools/pairlab/trace.py`-Move + 3 additive chain.py-Affordances (inert bewiesen) | **PR #338** |
| **2/3** | `tools/pairlab/follow.py` + CLI + Tests (**PR #343**); §14-Vorregistrierung der Arme (**PR #342**) | **gemergt** |
| **4** | Folger-Sweeps: Arm ① λ-Leiter (**PR #345**, ehrliches Negativ), Arm-⑥-Unterbau (**PR #346**), Arme ⑤+⑥ (**PR #347**, Overlap freigesprochen · Korrespondenz-Kappe), Arm ⑥b klassenbewusste Korrespondenz (**PR #348**, Hypothese bestätigt, keine Adoption), Arm ⑨ Topologie-Wächter (**PR #355**, Kontrakt hält, beide Kills feuern — Route-A-Fazit); kein Default adoptiert | **abgeschlossen** |
| **5** | `tools/inksight/`-Pipeline (isoliert, Umgebung verifiziert, erstes Kurrent-Ergebnis) | **PR #340** |
| **6** | Das Duell: Struktur-Zähler v2/v2.1 + Soll-Spalten (**PR #351/#352/#353**), Route G (**PR #354**), InkSight-T0 (**PR #356**), Duell-Seite mit 6 Ebenen | **abgeschlossen** |
| **7** | humanbench-WORT-Runde (neuer Item-Renderer; Bias benannt: der Autor beurteilt eigene Nachfahrungen — Abkühl-Abstand oder Zweitrichter) | offen, braucht den Autor |

**Betriebsregeln:** DB wird von Bench/Folger nie beschrieben; Fixtures +
`landmarks.py` + `core/geometry.py` + `core/quality_suetterlin.py`
(Retrace-Konstante) sind während einer Folger-Runde eingefroren; ein Voll-Re-Export der Fixture-Roots ist IMMER eine
deklarierte Doppel-Re-Baseline (wordbench + tracebench) mit datiertem
§-Eintrag — der erste Akt einer Runde ist `--only instances` gegen die
bestehenden Roots.

## 7 Optimierungsplan je Verfahren (2026-08-15)

Grundlage: die Befund-Matrix „Wort × Verfahren" über alle
Duell-Artefakte (`temp/tb-v21-chain-r0`, `tb-guard-*`,
`follow-guard-*-run`, `tb-inksight-*`, `tb-routeg-t0`) plus eine
Recherche-Runde (vier parallele Agenten: Befund-Mining, Route-A- und
Route-B-Literatur mit Quellen-Verifikation, Composer-Verortung im
Code). Jede Maßnahme unten ist ein KANDIDAT — sie wird erst gebaut,
wenn sie ihren eigenen vorregistrierten §14-Eintrag hat, und nach den
bestehenden Betriebsregeln gemessen (tracebench + Soll-Spalten
eingefroren; Composer-Änderungen messen zusätzlich wordbench
`word_loss`/`pair_loss` und deklarieren den compose-golden-Bruch als
datierte Re-Baseline).

### 7.1 Befundlage — wo die Fehler wirklich sitzen

1. **Zwei Wörter tragen 59,8 % des Kettenfit-Fehlers:** `unter`
   (dtw 0,4389 — Berührungs-/Überlagerungs-Stapel: `touch` 1→5,
   `overlap` 0→3) und `muß` (0,2421 — die ß-Retrace-Zone sitzt am
   falschen Ort, `retrace_matched` 0). Bei `muß` ist InkSight roh
   **2,9× besser** als der Kettenfit auf demselben Bild — der Defekt
   ist fit-spezifisch, nicht bildbedingt.
2. **Die Berührungs-Klasse bricht 6 von 7 Wächter-Zurückweisungen**
   und kostet damit den gesamten Release-Gewinn (dtw-Δ Median exakt
   0,0 auf allen drei prox-Sprossen).
3. **Strukturdefekte sind dtw-unsichtbar:** `will` schreibt 1 von 3
   Kreuzungen bei unauffälliger dtw 0,0453, `laden` hat 2 fehlende +
   2 erfundene Kreuzungen bei 0,0746. Nur die Zähler sehen das.
4. **Die i-Punkte sitzen beim Kettenfit SCHLECHTER als bei der
   prior-freien Kontrolle** (`mark_pos_err_xh` Median 0,129 gegen
   0,046) — ein isolierter, billig behebbarer Defekt.
5. **InkSight:** `und` ist ein reiner Bahnfehler (0,395 = 8–9,6×
   Kette bei Struktur-Σ 0), `Wer` scheitert an einem
   Ein-Punkt-Strich (Kontraktverletzung, `status: failed`), und die
   Retraces gehen systematisch verloren (11–12 von 15 Zonen, +20/21
   Pen-Lifts). Verdacht für das „hinten heraus kippt es"-Muster
   (Owner-Beobachtung an `unter`): die breitesten Crops (bis 310 px,
   w/h ≈ 4–5) liegen an bzw. jenseits der
   Aspect-Ratio-Filtergrenze 4,0 der InkSight-Trainingsdaten.
6. **Korrektur einer §14-Attribution:** die „9 erfundenen
   Berührungen der Komposition" (Arm-⑨-Fazit) gehören dem
   KETTENFIT (`touch_cand` 17 gegen Hand 8). Die Komposition selbst
   schreibt nur 2 Berührungen (beide w-intern) und 4 Überlagerungen
   (alle t-Balken-intern) vor — sie ist strukturell knapp, aber
   nicht zu eng. Nachtrag in §14 im selben PR.

### 7.2 Verfahren 1: die Komposition (Initialisierung) — der Top-Hebel

Gemessen: Komposition 22 Kreuzungen gegen Hand 23, aber die Differenz
ist wortweise größer, als die Summe zeigt (`soll_cross_agree` 7/10,
`soll_zones_agree` 6/10 — Abweichler `mit`, `unter`, `Wer`, `zwei`,
`linken`). Drei Mechanismen, alle im Code verortet:

- **K1 — „Schnitt am Kreuzungspunkt" wird „Schnitt mit Überstand".**
  Drei Klassenregeln schneiden heute je genau eine Kreuzung weg, weil
  der Strich AM Kreuzungspunkt endet und der Durchstoß-Zähler
  (`PIERCE_MARGIN_UNITS` 0,05 xh) eine Endpunkt-Berührung nicht
  zählt: der t-Balken-Schnitt (`BAR_EXIT_BASES`,
  `core/compose.py:1720-1748`), `LOOP_EXIT` am
  Schleifen-Selbstschnitt (`:1666-1682`) und `KRINGEL_EXIT`
  (`:1689-1711`). Kandidat: ein kleiner Überstand (~0,03 xh, auf den
  Platten nachmessbar) jenseits des Schnittpunkts; beim t zusätzlich
  die Startanker-Frage (Join ab Stamm vs. ab Balkenende — die
  Gegenprobe „Schnitt ganz aus" gewinnt die t-Kreuzung, verliert aber
  die Join-Kreuzung, das Wort-Total bleibt 2/3). Misst:
  `soll_cross_agree` JE WORT (nie über die Summe — 2 fehlende und 1
  überzählige Kreuzung heben sich sonst auf), `word_loss` der
  t-Wörter.
- **K2 — Pass-Through-Kopplung.** Jede Kopplungsregel endet den
  Verbinder heute AUF dem Zielbuchstaben (der Endpunkt `p3` ist das
  x-verschobene erste Tinten-Sample des Zielglyphen,
  `core/compose.py:1194`) und löscht den Anstrich unter dem
  Kopplungspunkt (`:2100-2113`); die join-gebildete Schleife (d/e —
  in `die` ist die EINZIGE Hand-Kreuzung join-gebildet) entsteht nur
  dort, wo zufällig nicht getrimmt wird. Die Gegenprobe zeigt: Trim
  abschalten allein erzeugt KEINE Kreuzung (22 bleibt 22, Zonen
  11→14) — der Wirkstoff ist ein ÜBERSCHIESSEN des Verbinders über
  den Kopplungspunkt hinaus (~0,08–0,12 xh, Kreuzungshöhe =
  `ENTRY_COUPLE_Y`). Risiko: Doppelung statt Schleife bei zu kurzem
  Überstand; `linken` liegt schon bei Soll 4 gegen Hand 3
  (Über-Kreuzen möglich).
- **K3 — der W-Ansatz ist KEIN Composer-Fehler.** Der Composer hat
  gar keinen Eintritts-Retrace-Mechanismus, und die W-Chartzeile ist
  ein einziger Strich ohne Retrace-Paare und ohne Laufform-Zeile —
  Stufe `chart_ductus`: das W braucht eine Neu-Tracierung mit
  Ansatz-Retrace durch den Autor (+ danach die W-Laufform). Ein im
  Composer ERFUNDENER Ansatz ohne Plattenmessung wäre
  Doktrin-widrig. → Korb/Todoist, Owner-Schritt.
- **K4 — keine Berührungs-Maßnahme.** Nach der korrigierten
  Attribution (§7.1 Punkt 6) gibt es composer-seitig nichts zu
  entschärfen; die Kandidaten-Konstanten (`ARM_FUSE_GAP`,
  `ALIGN_MIN_CLEARANCE`) feuern auf diesem Wortsatz nachweislich
  nicht.

### 7.3 Verfahren 2: Kettenfit + Folger (Route A) — Formulierung statt Gewichte

Das Arm-⑨-Fazit steht: mit DIESER Formulierung (EDT-Punktdatenterm +
Prox-Release + Budget-Veto nach dem Solve) ist der Fit am
struktur-sicheren Optimum; weitere Gewichts-Arme sind sinnlos. Was
bleibt, sind Änderungen der FORMULIERUNG — geordnet nach
Aufwand/Risiko:

- **A1 — Marken separat nachfitten (billig, isoliert).** Die
  Kontrolle beweist, dass 0,046 xh Marken-Ortsfehler aus derselben
  Tinte lesbar ist; der Kettenfit liegt bei 0,129, und bei
  muß/und/unter/zwei matcht gar keine Marke. Ein Mini-Fit nur der
  Marken-Striche auf die Restmaske (Tinte minus Körper-Claim), nach
  dem Körper-Solve, unabhängig vom Solver.
- **A2 — Datenterm härten: SDM + Dichtebewusstheit.** Der
  EDT-Punktterm ist tangential blind (Anker rutschen ENTLANG der
  Tinte) und dichteblind (zwei Pässe auf einer Kante kosten nichts).
  Squared Distance Minimization (Wang/Pottmann/Liu, ACM TOG 2006)
  liefert das korrekte lokale Abstandsmodell (tangential weich,
  normal steif); ein dichtebewusster Chamfer-Term (Density-aware CD,
  Wu et al., NeurIPS 2021) bestraft Mehrfachzuordnung. Adressiert
  Stranding UND den Pass-Kollaps mit der kleinsten Code-Änderung.
- **A3 — Kreuzungen als explizite Variablen.** Die
  PolyVector-Flow-Zerlegung (Puhachov et al., SIGGRAPH Asia 2021):
  erst Keypoints (Kreuzungen/Endpunkte), dann Topologie (wer
  verbindet sich mit wem), dann erst Geometrie. Unser
  `landmarks.py` ist bereits die Ink-Seite dieser Korrespondenz,
  und das Duktus-Soll sagt a priori, WELCHE Kreuzungen existieren
  müssen — die KreuzungsHÖHE wird damit gemessene Variable statt
  Nebenprodukt. Direkt gegen `laden`/`will`/`zwei` (fehl- oder
  unplatzierte Kreuzungen bei unauffälliger dtw).
- **A4 — Barriere statt Veto.** Das IPC-Muster (Li et al., ACM TOG
  2020): die vom Duktus-SOLL erlaubten Kreuzungspaare werden von der
  Prüfung ausgenommen, jedes andere Segmentpaar bekommt eine glatte
  Barriere plus eine kollisionsgefilterte Schrittweite — dann KANN
  der Fit keine neue Kreuzung erfinden, das Budget-Veto wird
  strukturell überflüssig (und das Budget kommt aus dem Soll statt
  aus der Chain-Init, die es heute selbst verletzt). Preis: eigene
  Line-Search oder eine äußere Augmented-Lagrange-Schleife um
  L-BFGS-B; das ist die teuerste Route-A-Maßnahme.
- **A5 — Retrace als Zwei-Pass-Zwang aus Breiten-Evidenz.** Der
  gemessene Blindfleck beider Datenterme. Die Breite liegt als
  2·EDT längst vor: eine Zone mit lokaler Breite ≈ 2× Strich-Median
  ist Doppelpass-Evidenz (Kato/Yasuhara führen „double-traced" als
  eigenen Kantentyp; StrokeStrip zeigt die gemeinsame
  Parametrisierung, in der zwei Pässe verschiedene
  Parameterintervalle belegen und der Kollaps nicht mehr
  kostenfrei ist). Direkt gegen `muß` (ß-Zone) und die
  Retrace-Ortsfehler (`laden` 0,246 xh).
- **A6 — Schedule umdrehen (GNC).** Heute: erst fitten, dann Veto.
  Standard der Literatur: Struktur-Constraints hart ab Iteration 0,
  Datenterme über einen Graduated-Non-Convexity-Kern langsam
  hochfahren (Blake/Zisserman 1987; Yang et al., RA-L 2020). Erst
  sinnvoll, wenn A4 die harten Constraints liefert.

Reihenfolge: A1 → A2 → A3 → (A4 oder A5) → A6. NICHT wieder
aufgenommen: weitere λ/Gewichts-Sweeps der alten Formulierung (durch
①⑤⑥⑥b⑨ erschöpfend negativ beantwortet).

### 7.4 Verfahren 3: InkSight roh (Route B1) — ohne Training

- **B1 — Best-of-N über Input-Augmentierungen (~1 Tag, erster
  Griff).** N Decodes über augmentierte Crops (Rotation-,
  Scale-Jitter, Strichbreite — exakt die InkSight-eigenen
  Trainings-Augmentierungen, also in-distribution), gerankt mit
  unserem vorhandenen Lineal gegen die GEMESSENE Tinte
  (Chamfer/DTW). Präzedenz aus derselben Gruppe: Afonin et al.,
  ICDAR 2023 („more than halving the character error rate").
  Nebeneffekt: der `Wer`-Ein-Punkt-Strich verschwindet, sobald EIN
  Ensemble-Mitglied kontraktkonform ist.
- **B2 — Tiling auf Seitenverhältnis ≤ 2 (1–2 Tage).** Die
  InkSight-Trainingscrops sind auf 0,5 &lt; w/h &lt; 4,0 gefiltert;
  unsere breitesten Wörter liegen daran/darüber und verschenken über
  die Langseiten-Skalierung die halbe Token-Auflösung in y. Zwei
  überlappende Fenster je breitem Wort, Bahn-Stitching im Overlap —
  die Rücktransformation existiert in `to_candidate.py` bereits.
  Erklärungs-Kandidat für das Owner-beobachtete „hinten heraus
  kompletter Quatsch" bei `unter`.
- **B3 — billige A/Bs (Stunden).** Padding-Farbe (`pad_black` ist
  Colab-Default, für Papier-Crops nicht offensichtlich richtig),
  Kontrast/Binarisierung vor der Inferenz; einmalig `Recognize and
  derender.` messen (erwartet schlechter: konditioniert auf die
  eigene Fehllesung — der text-Prompt-Befund legt das nahe).
  Decoder-Parameter sind im SavedModel NICHT exponiert
  (`serving_default` nimmt nur `input_text` + `image/encoded`).
- **B4 — InkSight als Initialisierung des eigenen Fits (Tage).**
  Das etablierte Muster „learned init + classical refine"
  (ConvexAdam; Deep Vectorization of Technical Drawings): unsere
  Verfeinerung existiert bereits, nur die Init wird getauscht.
  Ehrlich segmentweise einsetzen, nicht global — InkSight ist in
  dtw 1,5× schlechter, aber an Kreuzungen sauberer und bei `muß`
  2,9× besser: der Tausch lohnt DORT, wo der Composer-Init
  nachweislich schwach ist.
- **B5 — Retrace-Rückgewinnung über den Prior (Tage bis 1 Woche).**
  Der SET/SORT-Befund benennt das Formulierungsproblem: eine
  Segment-PERMUTATION kann einen Retrace nicht ausdrücken, eine
  Segment-SEQUENZ MIT WIEDERHOLUNG schon. Die vom Duktus-Soll
  geforderten, von InkSight ausgelassenen Zonen werden als
  Wiederholung des betroffenen Segments wieder eingesetzt, die +20
  Lifts entlang der Soll-Strichfolge wieder verbunden — Ordnung und
  Retrace-Wissen kommen vom Prior, die Geometrie bleibt gelernt.

### 7.5 Verfahren 4: eigenes Trajektorien-Modell (Route B2, 4090)

Erst NACH den B1-Hebeln (einziger Punkt mit echtem Projektrisiko).
Zuschnitt nach Cursive-Transformer-Vorbild (Greydanus/Wimpee 2025:
442k Parameter, 3.500 Wörter genügten; Repo ohne Lizenz → aus dem
Paper nachimplementieren, keinen Code kopieren), bildkonditioniert
per Cross-Attention; Ausgabe ist eine geordnete Koordinatensequenz,
Retraces sind also NATIV darstellbar — der Punkt, an dem InkSight
strukturell scheitert. Trainingsdaten: Engine-Renderings
(kalligrafisch korrekt über die Federmodelle — das verkleinert den
Sim-to-Real-Gap gegenüber naiven Rasterizern) mit
Augraphy-Degradation (MIT; Tinten-Bleed, Papiertextur,
Scan-Artefakte), 3.500–50.000 Wörter, auf der 4090 in 1–2 Wochen
messbar. Die ~63 getracten Belege sind der Held-out-Realtest; die
Gewichte bleiben per Open-Core-Regel außerhalb des Repos (auf
DB-Inhalten trainiert). Skriptübergreifender Transfer ist belegt
(Diffusion-TR generalisiert von Chinesisch auf ungesehene lateinische
Buchstaben). Fallback, falls from-scratch stockt: keiner über
InkSight (kein Trainingscode, §5) — dann ist B4/B5 die Route.

### 7.6 Verfahren 5: Fusion (nach ersten §7-Ergebnissen)

Ordnung/Strichfolge/Retrace-Wissen vom Prior, Geometrie vom besten
verfügbaren Kandidaten je Region; Übereinstimmung = Konfidenz,
Widerspruch = Prüfstelle. Publizierte Vorbilder für die Mechanik:
Raster-to-Vector (Liu et al., ICCV 2017 — Netz schlägt Junctions
vor, ein Integer-Programm erzwingt die Topologie) und Free2CAD
(Li et al., SIGGRAPH 2022 — Zwischenergebnisse werden geometrisch
korrigiert, BEVOR sie als Kontext weiterlaufen: das Gegenmittel
gegen Reihenfolge-Drift). Ehrlicher Befund der Recherche: KEINE
publizierte Arbeit fusioniert eine handautorierte Duktus-Bibliothek
mit einem gelernten Derendering-Modell — hier gibt es kein Rezept
zum Abschreiben. Die Kontrolle `routeg` wird grundsätzlich NICHT
optimiert (sie bleibt die Nulllinie des Duktus-Prior-Werts).

### 7.7 Wellen, Messdisziplin, Owner-Schritte

| Welle | Maßnahmen | Charakter |
|---|---|---|
| **1** (sofort, billig, unabhängig) | K1 + K2 (Composer-Topologie) · A1 (Marken-Nachfit) · B3 (A/Bs) · B1 (Ensembling) | Stunden bis ~1 Tag je Maßnahme |
| **2** | B2 (Tiling) · A2 (SDM/DCD) · K3 (Owner: W-Trace + Laufform) | 1–3 Tage je Maßnahme |
| **3** | A3 (Kreuzungs-Variablen) · B4 (Init-Tausch, segmentweise) · A5 (Zwei-Pass-Zwang) | Tage bis 1 Woche |
| **4** | A4 (Barriere) · A6 (GNC) · Route B2 (eigenes Modell) · Fusion | die großen Umbauten |

Messdisziplin unverändert: jede Maßnahme bekommt VOR der ersten Zahl
ihren §14-Eintrag (Hypothese, erwartete Wörter, Kill-Kriterien);
Composer-Maßnahmen (K1/K2) messen dreifach — `soll_cross_agree`/
`soll_zones_agree` je Wort, wordbench `word_loss`/`pair_loss` (dürfen
nicht regressieren) und den deklarierten compose-golden-Bruch als
datierte Re-Baseline; alle Nachfahr-Maßnahmen laufen auf den 10
Dev-Wörtern, der Bestätigungssatz (Owner, sobald wieder am Tablet:
Umlautwort, langes ſ, +1 Versal, Marken mit Absetzen) bleibt der
Schlussstein, an dem jeder adoptierte Gewinn bestehen muss.
