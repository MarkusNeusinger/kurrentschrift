# Tintenfolger: der Prüfstand und die zwei Routen zur Wortbahn

> **Status (2026-08-14, abends): Prüfstand KOMPLETT — Baseline steht.**
> Stufen A/B/1/5 sind gemergt (PR #337/#339/#338/#340), Stufe C (Harness +
> erste Baseline = Freeze-Akt) ist dieser PR; die Kette misst gegen die
> Hand `dtw_xh` 0,062 med / 19 erfundene Kreuzungen / Retrace-Ratio 1,51
> (qualitaetsmetrik §14). Als Nächstes: die Folger-Arme (Stufe 2/3).
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
(§13-Bremse-Hypothese) ⑥ landmark ⑦ width-Modulator ⑧ bind (zuletzt, nur
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
| **C** | Harness + Provider + authored-Gate + erste Baseline-Tabelle (= Freeze-Akt; Kette: dtw 0,062 med · 19 erfundene Kreuzungen · Retrace-Ratio 1,51) | **in diesem PR** |
| **D** | **Duell-Ansicht** (alle Kandidaten + Hand-Referenz über dem Crop, final UND als Schreib-Animation) + **Chronik** (create-only Rundenhistorie, dbsnapshot-Muster) | **in diesem PR** |
| **1** | `tools/pairlab/trace.py`-Move + 3 additive chain.py-Affordances (inert bewiesen) | **PR #338** |
| **2/3** | `tools/pairlab/follow.py` + CLI + Tests; §14-Vorregistrierung der Arme | offen |
| **4** | Folger-Sweeps, kalibrierte Defaults (Owner-Go für Adoption) | offen |
| **5** | `tools/inksight/`-Pipeline (isoliert, Umgebung verifiziert, erstes Kurrent-Ergebnis) | **PR #340** |
| **6** | Das Duell: Folger vs. Chain vs. InkSight-roh vs. Route G, ehrliche Negative | offen |
| **7** | humanbench-WORT-Runde (neuer Item-Renderer; Bias benannt: der Autor beurteilt eigene Nachfahrungen — Abkühl-Abstand oder Zweitrichter) | offen, braucht den Autor |

**Betriebsregeln:** DB wird von Bench/Folger nie beschrieben; Fixtures +
`landmarks.py` + `core/geometry.py` + `core/quality_suetterlin.py`
(Retrace-Konstante) sind während einer Folger-Runde eingefroren; ein Voll-Re-Export der Fixture-Roots ist IMMER eine
deklarierte Doppel-Re-Baseline (wordbench + tracebench) mit datiertem
§-Eintrag — der erste Akt einer Runde ist `--only instances` gegen die
bestehenden Roots.
