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

### 2.5 Split-Neuziehung (vorregistriert 2026-08-16, Owner-Go)

Die 10 Dev-Wörter aus §2.4 sind die zufällig ZUERST nachgefahrenen — kein
gewählter Schnitt. Owner-Entscheid: Sobald **alle 63 Wörter** `authored`
sind, wird der Split stratifiziert neu gezogen. Der Schlüssel ist hiermit
VOR jeder Zahl festgelegt (performance-blind: er liest ausschließlich die
eingefrorenen Slot-Inhalte, nie eine Bench-Zahl; die neu nachgefahrenen
Wörter waren zum Zeitpunkt dieser Festlegung noch nie gebencht).

**Der Schlüssel.** Buchstaben-Klassen über `glyph_keys`: Arkade
(n m i u ü) · Rundkörper (a o e c ä ö) · Schleifen-Oberlänge (l h k b f t)
· d-Schleife (d) · Unterlänge (g z p q j) · s-Formen (s ſ ß) · r-Arm (r)
· w/v/x · Versal · Marken-Träger (i u ü ä ö t z ß). Wiederholungen
(die-2, muß-2/-3, und-2/-3/-4 …) splitten als WORT, nie über die Grenze.
Die 10 getunten Wörter sind VERBRANNT und liegen zwingend auf der
Dev-Seite; frei verteilt werden nur die 53 übrigen. Dev wird greedy
aufgefüllt, bis jede Klasse ≥ 2-mal vertreten ist (Gewinn = meiste noch
unterdeckte Klassen; Gleichstand: weniger Vorkommen, dann alphabetisch);
der Rest teilt sich klassensortiert alternierend in zwei Hälften.

**Die Zuordnung (hiermit fixiert, 12 / 19 / 19 Wörter):**

- **Dev (Tuning, 19 Vorkommen):** die 10 aus §2.4 + **Galoppieren** +
  **das**.
- **Bestätigung A (offen, 20 Vorkommen):** Einen · Gaul · Gewehr · Kugel
  · Silber · Soldaten · Sporn · Säbel · Zorn · auch(+1) · daß · ein ·
  han · im · macht · regieren · scharfen · von · zu („+n" =
  Wiederholungs-Vorkommen desselben Worts).
- **Bestätigung B (VERSIEGELT, 24 Vorkommen):** Feinde · Pulver · Seiten
  · Sprünge · Zaum · Zügel · an · der(+2) · einen · einer · er(+2) ·
  fechten · haben · kann · schießen · schwer · streiten · wenn(+1) · zum.

**Inkraftsetzung, zweistufig.** Die **Versiegelung gilt ab sofort**:
Bestätigungswörter werden außerhalb einer vorregistrierten
Bestätigungsmessung nicht gebencht, B-Wörter gar nicht — B öffnet erst
für die großen Adoptionsentscheidungen (gestaffeltes Aufdecken gegen
Bestätigungs-Abnutzung). Die **Dev-Erweiterung** (Galoppieren + das,
Änderung von `TRACEBENCH_DEV_IDS` in `tools/tracebench/sets.py`) tritt
erst in Kraft, wenn alle 63 Wörter `authored` sind — als deklarierte
Lineal-Änderung mit datiertem Re-Baseline-Lauf aller stehenden Routen
(Kette · Lotse · InkSight · Nullprobe) auf dem neuen Dev-Satz.

**Aktivierungs-Nachtrag (Owner-Go in Session, 2026-08-17):** Die
Dev-Erweiterung tritt VOR der Voll-Autorisierung in Kraft — zu dem
Zeitpunkt, an dem der DEV-Satz vollständig `authored` ist (alle 19
Vorkommen, inkl. Galoppieren + das; Bestätigung A stand bei 5/20,
B bei 4/24). Das ändert am Blindheits-Argument nichts: die Zuordnung
selbst war seit 2026-08-16 fixiert, Galoppieren/das waren nie
gebencht, und der Weg Dev → Bestätigung existiert nicht — vorgezogen
wird nur der Messbeginn, nicht die Wahl. Die Versiegelung von A/B
gilt unverändert. Der datierte Re-Baseline-Lauf der stehenden Routen
auf dem 19er-Dev-Satz steht in `qualitaetsmetrik.md` §14
(„Re-Baseline `aug17`").

**Benannter Notausgang.** Wird die Kapital-Join-Klasse Tuning-Fokus,
darf EIN weiteres Versal-Wort mit eigener Vorregistrierung von A nach
Dev wandern — BEVOR die erste Kapital-Tuning-Zahl gelesen ist, nie
danach. Der umgekehrte Weg (Dev → Bestätigung) existiert nicht.

**Drills sind keine Wörter.** Die 33 Abb.-20-Paare bilden einen EIGENEN
Pool außerhalb des Wort-Splits (die K3-Lektion aus §7.9: derselbe Join
verhält sich im Wort und im Drill gegenläufig — gemischt verwässern
beide Signale). Ihre eigene Zweiteilung wird HIERMIT gezogen — jetzt,
weil kein Drill je getraced oder trace-gebencht wurde und die Blindheit
darum vollständig ist. Schlüssel: Exit-Klasse des linken Buchstabens
(Kringel b/o · Schleife d/s · r-Arm · Rückwärts-Curl v/w/x · ſ · ß ·
Versal), je Klasse alphabetisch alternierend. Es gibt keinen
Drill-Dev-Zwang (nichts ist verbrannt), also zwei Gruppen:

- **Drill-offen (18):** bi · Bi · bs · bz · df · do · ds · dx · In ·
  rb · rx · sa · ssi · vp · vx · wi · Wu · ßi — für vorregistrierte
  Wort/Drill-Diagnosen und etwaiges künftiges Drill-Tuning.
- **Drill-versiegelt (15):** bp · bx · dk · dp · dt · Du · dz · Of ·
  on · rp · rz · sg · vs · vz · xi — Bestätigungsmaterial, öffnet wie
  Bestätigung B erst für große Entscheidungen. (IDs wie im Sidecar;
  sa/sg/ssi schreiben auf der Platte ſ.)

Die Versiegelung betrifft AUSSCHLIESSLICH die Rolle als nachgefahrene
Trace-Referenz (das Ink-Folgen). Die KOMPOSITIONS-Messung läuft
unverändert über alle 33: `wordbench --set pairs` (`pair_loss`) misst
die komponierten Joins gegen die Drill-Tinte, und die sezierten
`pair_instances` (doff/dconn, pairmeas) bleiben Platzierungs-Evidenz —
genau darin liegt der Wert der Drills fürs RICHTIGE SCHREIBEN: 31 der
33 tragen Übergänge, die in keinem einzigen der 63 Wörter vorkommen
(nur `on` und `wi` überlappen). Fürs Schreiben sind sie damit die
einzige Evidenz dieser Join-Klassen; fürs Ink-Folgen sind sie
Rückhaltematerial.

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
  **Zurückgezogen `aug19`** (§14 „Zweiter Nachtrag"): die
  19er-Referenz zeigt KEINEN W-Ansatz-Retrace — die These stammte
  aus der Zeit vor der Nachfahrung. Die fehlende Wer-Soll-Zone ist
  die doppelt gefahrene e→r-Diagonale der Hand
  (Beleg-Eigenschaft). Das reale W-Problem ist per Autopsie (§14
  „Dritter Nachtrag") NICHT der Join (Verbinder bleibt ≤ 0,56 xh,
  komponiertes e normal bei 0,94): die komponierte W-FORM liegt
  ~0,4 xh links der Hand-Apexe, das folgende e startet in der
  dritten Hand-W-Schleife — die Laufform-Lücke des W (1 QC-Fit,
  kein `LAUFFORM_SX`-Eintrag) — Laufform-Arm, kein
  Autorenschritt.
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
| **1** (sofort, billig, unabhängig) | K1 ✓ (#358) · K1b ✓ (#359, ersetzte K2: der Evidenz-Rest war das Stamm-Retrace, nicht die Kopplung) · A1 ✓ (#360, −55 % Marken-Ortsfehler, opt-in) · B1 ✓ gemessen (ehrliches Negativ: Orakel-Lücke = der Fund) · B3 (A/Bs, offen) | **abgeschlossen bis auf B3** |
| **1b — Vorschub** (Owner-Fund an den K1b-Overlays) | P1 ✓ (#361: Bowl-Tuck · w/v-Rückwärts · Balken-Steigung) · P1b ✓ (#362: longs-Ausnahme) · P2 ✓ (#363: align-Floor; Arkaden = Beleg-Varianz, geschlossen) — `word_loss` 0,1110 → 0,1081, `pair_loss` 0,1657 → 0,1466 | **abgeschlossen**; §14 „Welle 2 · P1/P1b/P2" |
| **2** | **P3 KOARTIKULATION (Owner-Priorität „zeitnah", 2026-08-15) — ABGESCHLOSSEN `aug16`, §14 „Welle 2 · P3": die Vorstudie (248 Vorkommen) maß die Asymmetrie — Schwanz = Klassenkonstante (Chart-/Laufform-Frage), Kopf = echte Koartikulation nach Hoch-Exits (p < 0,0001); die drei vorregistrierten Entry-Klassenregeln K1 (Balken→Rund) · K3 (Deckstrich→Arkade) · K2 (d-Abgangs-WINKEL) wurden alle gemessen und von ihren eigenen Gates verworfen (K1: Klassen-Split, K3: Wort/Drill-Split, K2: beide Lineale monoton dagegen) — die Knöpfe bleiben deklariert-aber-neutral für die Bestätigungssatz-Nachkalibrierung; stehend: Verbinderform-Hypothese + O2-Trim-Jitter-Bugfix** · B2 (Tiling) · A2 (SDM/DCD) · K3 (Owner: W-Trace + Laufform, z prüfen) | je eigene Vorregistrierung |
| **3** | A3 (Kreuzungs-Variablen) · B4 (Init-Tausch, segmentweise) · A5 (Zwei-Pass-Zwang) · ordnungs-bewusstes B1-Auswahlsignal (Ziel +0,0067, Deckel −0,0124) | Tage bis 1 Woche |
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

**Nachkalibrierungs-Protokoll bei neuen authored-Wörtern**
(Owner-Direktive 2026-08-15: „nur 10 Wörter — fix einplanen, dass
weiter getuned wird, wenn mehr verfügbar sind"). Die Evidenz der
Kalibrierungen hat zwei EHRLICH VERSCHIEDENE Böden: Die
VORSCHUB-Konstanten (Bowl-Tuck, w/v-Rückwärts, Balken-Steigung,
align-Floor) ruhen auf den ~218 QC-gefilterten Dissektionen des
HARVESTS über alle 63 Wörter + 33 Drills — aus dem Scan lesbar,
ohne Nachfahrung, solide n. Die TOPOLOGIE- und ORDNUNGS-Wahrheiten
(dtw, Strukturzähler, Marken-Orte, Soll-Vergleiche, Retraces —
alles, was der Scan prinzipiell NICHT hergibt: Strichfolge,
Absetzen, doppelt beschriebene Tinte) ruhen auf den 10
nachgefahrenen Wörtern und sind entsprechend dünn (Balken-Klasse
n=6, longs-Rückwärts n=1). DESHALB, stehend: Jede neue
authored-Charge löst denselben Ablauf aus — (1) `--only
word-instances`-Refill der Fixture-Roots, (2) die
Diagnose-Erhebung neu (Drift-Profil + signierte doff-Attribution
je Platzierungsregel), (3) jede Konstante, deren Klassen-Median
sich um > 0,05 xh bewegt oder deren Varianz-Verdikt kippt
(Arkaden-Luft!, Diagonalen-Trim, longs-Ausnahme), bekommt eine
datierte Nachkalibrierung mit den P1/P2-Gates, (4) die
`--split confirm`-Wörter bleiben dabei Bestätigung und wandern NIE
in den Dev-Satz (Append-never).

### 7.8 Namensfamilie und die Lotse-Route (Owner-Entscheid 2026-08-16)

**Die Anzeige-Namen.** Die Duell-Seite (und die spätere öffentliche
Methoden-Seite) führt die Verfahren unter lesbaren Namen; die
technischen Namen (Kettenfit, Route G, `routeg-graph`) bleiben in
Code und datierten §14-Einträgen unverändert — die Übersetzungstabelle
ist der Glossar-Eintrag „Duell-Namen":

| Anzeige-Name | technisch | Stand |
|---|---|---|
| **Hand** | die eigene S-Pen-Nachfahrung (Referenz) | steht |
| **Kette** | Kettenfit MIT Struktur-Wächter (Arm ⑨) | steht |
| **InkSight** | Small-p, derender-Prompt | steht (text-Prompt = Diagnose, von der Seite genommen) |
| **Nullprobe** | Route G / `tools/routeg` | steht |
| **Zögling** | eigenes Trajektorien-Modell (Route B2, §7.5) | geplant |
| **Vier Augen** | Fusion (§7.6) | geplant |
| **Feinschliff** | Natürlichkeitsfilter (zweite Stufe, Glättung mit Struktur-Wächter) | als MESS-Arm verworfen (§14 Lotse v0.6 `aug16`: das Lineal sieht den Zickzack nie — Resampling schluckt ihn; Glättung ist eine reine Darstellungsstufe beim Konsumenten) |
| **Chor** | ordnungs-bewusste Auswahl unter Varianten (B1-Nachfolger) | Welle 3 |
| **Lotse** *(Arbeitstitel)* | Skelett direkt fahren, Duktus als Karte (unten) | v0.9 (`aug17`, §14): dev-19 dtw 0,0578 = Ketten-Niveau, gepaart −24 %, p90 halbiert, Netto-Kreuzungsdefekte 7 (Rest = Soll-Differenzen); adoptiert: Auslauf 1,0 · Doppelzonen-Kartenfahrt · Zonen-Ausweitung 0,35 · gepinnte Selbstschnitt-Fenster 0,35 |

**Verfahrensseiten (seit 2026-08-18):** Je stehendem Verfahren führt
eine Register-Seite Steckbrief + Versions-Ledger —
[`../reference/verfahren.md`](../reference/verfahren.md) (Übersicht +
Versions-Konvention) mit den Seiten Kette · Lotse · InkSight ·
Nullprobe. Diese Tabelle bleibt die Übersetzungstabelle der Namen;
Zahlen wohnen weiter in qualitaetsmetrik.md §14.

**„Kette+ ist die einzige Kette."** Owner-Entscheid nach der
Kreuzungs-Frage: es gibt KEIN Beispiel, wo eine vom Fit ERFUNDENE
Kreuzung das Wort richtiger macht — join-gebildete Kreuzungen (der
einlaufende Verbinder formt die e-Schleife) stecken bereits im
Soll-Budget, und wo die HAND mehr kreuzt als die Komposition
(t-Deckstrich, ß, e-Einläufe), ist das ein Composer-Defekt, der am
Soll zu fixen ist, nie eine Fit-Freiheit. Die Duell-Seite zeigt
darum nur noch die gewachte Variante als „Kette". Die
PRODUKTIONS-Seite (structure_guard als Harvest-Default für die
`traced`-Zeilen) ist ein eigener, messungs-affiner Schritt mit
eigener §14-Vorregistrierung: dtw-neutral erwartet (Arm ⑨ maß Δ
exakt 0), die Strukturzähler müssen Richtung Soll fallen, dbsnapshot
vor jedem Re-Harvest, Owner-Go vor dem DB-Write.

**Route „Lotse" (Owner-Idee 2026-08-16).** Nicht Buchstabe
auflegen-und-verformen (Kette), sondern wie die Nullprobe DIREKT auf
der Tinten-Mitte fahren (Skelett-Graph) — und nur an den
Entscheidungsstellen (Kreuzung, Berührung, Abzweig, Lücke) den
Duktus wie eine KARTE fragen: links oder rechts? Geometrie damit
ganz aus dem Skelett (die Nullprobe zeigt, dass genau das perfekt
auf der Tinte liegt: AIoU 0,833 > Hand 0,685), Ordnung, Topologie
und jeder Abbiege-Entscheid ganz aus dem Prior (komponierte Bahn
oder Chain-Init als Karte) — die Doktrin „Geometrie aus der Tinte,
Ordnung aus dem Prior" radikaler als die Kette, und kein
#278-Bruch, denn der Duktus entscheidet die Route. Bausteine liegen
bereit: der routeg-Skelettgraph, `landmarks.py`, das Soll-Budget
(Kreuzungen/Retraces a priori), Retrace = dieselbe Kante zweimal
fahren, Marken per Prior zuweisen, Lücken als Prior-Brücke. Eigene
§14-Vorregistrierung VOR der ersten Zahl, wenn begonnen.

### 7.9 Rettungswege der ehrlichen Negative (stehende Liste)

**Owner-Direktive 2026-08-16** (nach der P3-0/3-Runde): Ideen, die
beim Verwerfen aufkommen — und was eine verworfene Maßnahme doch noch
ins Ziel bringen könnte — werden festgehalten statt in §14-Schwänzen
zu verstreuen. Stehende Regel: **jeder §14-Ergebnis-Eintrag eines
Verworfenen schließt mit benannten Rettungswegen oder explizit
„keiner benannt"**, und diese Tabelle wird im selben PR ergänzt.
Leitplanke: Konversion heißt immer neuer MECHANISMUS, neue EVIDENZ
oder neuer SENSOR mit frischer Vorregistrierung — nie derselbe Knopf
mit weicheren Gates (das wäre genau das Nachstimmen, das die
Disziplin verhindert).

| Verworfen (§14) | Fund / gemessene Decke | Rettungsweg | Auslöser |
|---|---|---|---|
| B1 Best-of-N (`aug15`) | Orakel −0,0124 in denselben N Antworten bewiesen; Ranker ist ordnungs-blind | ordnungs-bewusstes Auswahlsignal („Chor", Ziel +0,0067) | Welle 3 |
| P3-K1 Balken→Rund (`aug16`) | +126°-Ankunftsfehler bleibt real; verworfen wurde nur der HÖHEN-Knopf | Verbinder-FORM: gekrümmter Einfall statt gerader Balken-Linie | eigene Pre-Reg |
| P3-K3 Arkaden-Lift (`aug16`) | Wort/Drill-Split desselben Joins; Nebenfund: Spline-Jitter deaktiviert den generischen O2-Trim für Arkaden-Köpfe | (a) O2-Trim-Jitter-Bugfix als eigener Gewinnkandidat; (b) Kontext-Regel statt Uniform-Konstante | (a) sofort pre-registrierbar; (b) Bestätigungssatz |
| P3-K2 d-Abgangswinkel (`aug16`) | beide Lineale monoton dagegen, kein Split | nur Nachkalibrierung (Klassen-n 8/18) | Bestätigungssatz |
| Arm ⑨ Topologie-Wächter (`aug16`) | Tinten-Gewinn und Struktur-Erfindung in DIESER Formulierung untrennbar; `structure_guard` bleibt Werkzeug | Route „Lotse" (§7.8): Skelett fahren, Duktus als Karte | eigene Pre-Reg |
| Arm ⑥/⑥b Landmark-Gewicht (`aug14`) | Korrespondenz-Kappe gelöst (classed punktweise kostenlos), Gewicht trotzdem nutzlos im Folger-Setting | klassenbewusste Ziele stehen bereit für ein Setting, in dem die Kreuzung wirklich wandern kann (Lotse) | mit der Lotse-Runde |
| P2a Arkaden-Luft · P1 Diagonalen-Trim (`aug15`) | Beleg-Varianz ±0,1 xh, Ruler monoton dagegen | Dissektions-Forderung im Nachkalibrierungs-Protokoll (§7.7) | Bestätigungssatz |
| Methodik-Lücke (quer, `aug16`) | drei Kills wurden von Netto-Deltas ≤ 0,0007 entschieden — das Lineal ZUCKT dort nur, die Gates machen daraus ein Nein | humanbench-WORT-Runde als vorregistrierter Tie-Breaker für ruler-indifferente Fälle (\|Netto-Δ\| < ε bei starker Dissektions-Evidenz) | eigene Pre-Reg + Runde |
| Lotse v0.10 Punkt-Knoten (`aug19`) | Anker-Offsets als Punkt-Knoten scheren das Feld an der Kreuzung (Merge/Oskulation in dichten Clustern); Gewinnseite real (aiou +0,027, Ortsfehler halbiert, Spurious-Heilung) | Plateau-Feld = starre Cluster-Translation → **UMGESETZT als v0.11, adoptiert** | erledigt |
| Lotse v0.11 Stufe "all" (`aug19`) | Zonen-Rides/Brücken-Pinning scheitert um genau EIN Galoppieren-Doppel-X (Netto 8 > 7); die Doppel-X-Duplikate sind 4 der 6 Rest-Spurious | EIN X je Knoten-Cluster — als v0.12 Plateau-Sehne versucht und VERWORFEN (s. u.); wartet auf einen Mechanismus, der Duplikate schließt, ohne das X zu kosten | wartet |
| Lotse v0.12 Plateau-Sehne (`aug19`) | der Wackel WAR das X: an Schleifenschlüssen laufen beide Pässe tangential, ihre Sehnen sind parallel und schneiden sich gar nicht (missing 1 → 8, Retraces zerstört); die Duplikate sind zugleich KEINE Topologie-Erfindung (das X ist real, nur doppelt) | (a) Entdrillung des kleineren Wiggle-Bogens zwischen Duplikat-Paaren; (b) asymmetrische Sehne (nur der spätere Pass) | je eigene Pre-Reg, geringer Leidensdruck |
| K0-Wächter „strikt besser" (`aug16` zweiseitig · `aug19` soll-bewusst) | die Struktur friert beide Male (104=104 bzw. 107=107); das aug19-Protokoll beweist die Ursache: die runden-ATOMARE Rückweisung verwirft eine gebündelte Soll-Reparatur (unter: overlap 3→2 erlaubt, touch 3→6 verboten — beides in EINEM Solve) | **zonale Rückweisung**: nur die Anker-Nachbarschaft der verletzenden Zone einfrieren/zurücksetzen statt des ganzen Rounds | eigene Pre-Reg |
| Lotse v0.13 Stufe 0,8 (`aug19`) | das weite Entdrillungs-Fenster tötet auch GENUIN nahe echte Paare (mits t-Doppel 0,07 xh) — Geometrie allein kann Gewebe-Duplikat und echtes enges Doppel nicht trennen. **Autopsie-Nachmessung `aug20`:** auch MIT Lineal-Soll-Budget bleibt 0,8 tot — Galoppieren würde komplett heilen (Netto 2 → 0), aber unter verliert ALLE drei X, weil die Karte unters Kreuzungs-ORTE nicht kennt (vierte Platzierungs-Bestätigung); der Punkt-Abstand trennt die Klassen nicht (0,27–0,29 gegen 0,17–0,32 xh, überlappend) | erst die Karten-PLATZIERUNG reparieren (K1-p-Arm, e→r-Platzierung), dann das Fenster mit Lineal-Soll-Budget wiedervorlegen | Platzierungs-Arme zuerst |
| Lotse v0.14 „all"+Entdrillung (`aug19`) | Tinten-Gewinne real (aiou +0,012, G erstmals fast hand-gleich geritten — Sichtbeweis), aber die Struktur kippt in GENAU den zwei schlimmsten Karten-Form-Regionen (G-Kopf-X stirbt an der formfremden G-Karte, p erfindet eines) — Netto 8 > 6. **Wiedervorlage `aug19` spät auf der LF3b-Karte: erneut verworfen (Netto 7 > 5), und die Karten-Form-These ist damit WIDERLEGT** — dieselbe Galoppieren-Bruchstelle auf topologie-sauberer Chart-G-Karte; die Tinten-Gewinne bestätigen sich (aiou +0,004, p90 −0,001, kein dtw-Verlierer) | (a) G-Kopf-Ritt-Autopsie unter „all" → **ERLEDIGT `aug20`**: der Riss ist die parität-blinde ENTDRILLUNG, nicht die Pinnung (vor der Entdrillung hat „all" das X und den saubersten Ritt); (b) selektive Pinn-Stufe → **UMGESETZT als v0.16-Leiter**: „bridges"+Lineal-Soll-Budget ADOPTIERT (reiner Tinten-Gewinn, Struktur stellen-identisch), „zones"/„all" scheitern nur noch an der p-Oskulation (+1, Platzierungs-Familie) — das G-Kopf-X überlebt dort unter Budget | Zonen-Stufe: nach dem K1-p-Platzierungs-Arm wiedervorlegen |
| Lotse v0.15 soll-budgetierte Entdrillung (`aug19`) | das Budget erbt die Karten-Platzierungsfehler (unters e→r-Soll liegt neben der Tinte → echtes Paar stirbt trotz Budget) und die Radius-Zählung vetiert wills Fix (benachbartes echtes X in der Gewebe-Nachbarschaft) — dritte unabhängige Bestätigung der Karten-Form-Decke | Wiedervorlage GEMEINSAM mit v0.14 nach den Laufform-Armen → **UMGESETZT `aug20` als Lineal-Soll-Budget (v0.16), ADOPTIERT**: die Autopsie fand die Wurzel — die rohe Soll-Zählung listet jeden Karten-Schnitt ~doppelt (wills falsches Veto: 6 „Soll" gegen wahre 4); mit dem gefrorenen Kreuzungs-Detektor als Soll-Quelle löst sich wills Veto und das G-Kopf-Veto feuert korrekt | erledigt |
| Lotse v0.8 Selbstschnitt-Fenster (`aug17`) | Topologie vollständig bestätigt (Netto-Defekte 32 → 4, dtw erstmals unter der Kette), aber die ROHE Karten-Geometrie der Fenster kostet Tinten-Deckung (aiou-Kill um 0,003 bzw. 0,075) | v0.9: dieselben Fenster ans Ink GEPINNT (Topologie/Winkel von der Karte, Lage von den Board-Punkten) | eigene Pre-Reg, gemessen in derselben Runde |
| Laufform LF1 Lücken-Schluss, beide Stufen (`aug19`) | die Gewinnseite ist die größte der Lotse-Kampagne (aiou 0,7398 → 0,7527, wordbench −0,0024, spurious 5 → 3, linken-Soll heilt) — verworfen an EINEM Riss: der frische G-Median verliert die zweite Chart-G-Kreuzung (`cross_missing` 2 > 1), und auch die G-Einzelfits zählen nur 0/1/1 | **Topologie-Reparatur LF3**: lokale Chart-Rückblendung im 0,5-xh-Fenster um die verlorene Kreuzung, minimales t per Bisektion — Breite bleibt Laufform, Topologie bleibt Chart | eigene Pre-Reg, gemessen in derselben Runde |
| Laufform LF2 Topologie-Wächter, Voll-Entfernung (`aug19`) | Kern-Erwartung erfüllt (Galoppieren-Soll 6 → 8 = Hand-Übereinstimmung, netto 4), aber die volle Breiten-Entfernung kostet Tinte (+0,00136, schießen +0,034) und kippt den Galoppieren-i-Punkt aus dem Ritt (Marken-Gate) | Reparatur statt Entfernung (→ LF3); der Wächter selbst bleibt als Write-Path-Prinzip (nie eine Zeile speichern, die Topologie verliert) | eigene Pre-Reg, gemessen in derselben Runde |
| Laufform LF3 Buchstaben-Orakel (`aug19`) | Mechanismus richtig (Marken bleiben, aiou +0,007), Orakel zu schwach: das minimale Zellen-t überlebt den Kompositions-Kontext nicht (Galoppieren Buchstaben-Soll 7, Kompositions-Soll bleibt 6) | Kompositions-Orakel → **UMGESETZT als LF3b, alle Gates bestanden, als Kandidaten-Karte adoptiert** | erledigt |

### 7.10 Runde aug17: die Befund-Matrix des 19er-Dev-Satzes und der Maßnahmenplan

Grundlage: die Re-Baseline aller stehenden Routen auf dem
aktivierten 19er-Dev-Satz (qualitaetsmetrik.md §14 „Re-Baseline
`aug17`") plus die Autopsien derselben Session (Kreuzungs-
Positionskarten Hand/Kette/Lotse, Ritt-Instrumentierung `will`,
Fenster-Bilder will/die/muß, Kompositions-Soll-Abgleich
Galoppieren). Jede Maßnahme ist ein KANDIDAT mit eigener
§14-Vorregistrierung vor der ersten Zahl.

**Befundlage — präzisiert gegenüber §7.1:**

1. **Die muß-Klasse ist klassenhaft, kein Einzel-Beleg:** alle drei
   Vorkommen tragen beim Kettenfit dtw 0,21–0,24 mit derselben
   Signatur (ß-Retrace-Zone 0/1 gematcht, r 0,18–0,24). Der Lotse
   gewinnt die Klasse geschlossen (0,11–0,15), verliert aber die
   ß-Stamm-Kreuzung und führt die ß-Bögen als eigenen Strich ohne
   Stamm-Durchstoß (+1 Lift je Vorkommen, `direction_uncertain`
   je 1 Strich — Autopsie-Bild: Bögen erreichen den Stamm nie,
   der Stamm selbst ist ein Deckungs-Ritt-Gewirr mit
   Skelett-Spornen).
2. **Galoppieren (neu, 0,2349 Kette) zerlegt sich in DREI
   Mechanismen:** (a) 2 der 8 Hand-Kreuzungen fehlen schon der
   KOMPOSITION — die p-Unterlängen: die Tafel-Hand schreibt die
   p-Rückkehr als schmale Schleife (Kreuzung bei v ≈ 0,1–0,2),
   die Vorlage als exakten Retrace → Stufe `chart_ductus`/
   Laufform, Autorenfrage (wie K3/W-Ansatz); (b) 3 weitere hat
   die Komposition, der FIT verliert sie (die §13a-Höhenfrage);
   (c) der Lotse verliert alle 8 (Befund 3). Dazu die fehlende
   i-Marke und +1 Lift.
3. **Der Lotse-Kreuzungsverlust ist mechanisch lokalisiert — der
   JUNCTION-PINCH:** am Schleifenschluss routet der Viterbi beide
   Pässe über dieselben 1–3 Korridor-Pixel des Knotens; statt
   eines transversalen X entstehen zwei tangentiale
   Y-Zusammenläufe, die der Durchstoß-Zähler zu Recht nicht
   zählt. Die adoptierte v0.5-Kartenfahrt TRIGGERT dort korrekt —
   aber nur auf 1–2 Samples (Instrumentierung `will`: 4 von 173
   Samples, je 1 pro l-Schleifenschluss), und ein einzelnes
   karten-gerittenes Sample macht aus dem Pinch kein X. Der
   Trigger ist richtig, die WIRKUNG zu schmal. 31 von 46
   Hand-Kreuzungen fehlen; JEDES Wort verliert, auch die
   join-gebildete die-Kreuzung.
4. **Die Kreuzungs-HÖHE bleibt der Ketten-Restdefekt der kleinen
   Wörter:** das stapelt die d-Schleifen-Kreuzung dreifach auf
   1,0–1,26 xh (Hand 0,94 → 2 unechte), die/die-2 setzen sie
   0,25–0,3 xh zu hoch — dieselbe §13a-Klasse, jetzt mit
   frischen Belegen.
5. **Soll-Abweichler des 19er-Satzes benannt:** Galoppieren 6 vs 8
   (Befund 2a), Wer-Zonen 1 vs 2 (der W-Ansatz-Retrace, K3 —
   steht beim Autor), linken 4 vs 3 und mit-2 2 vs 1
   (Beleg-Varianz: DIESE Hand kreuzt das t nicht).
6. **InkSight-Prüffall:** der Galoppieren-Crop liegt mit
   w/h = 4,34 ERSTMALS jenseits der
   InkSight-Trainingsfiltergrenze 4,0 — der vorregistrierte
   B2-Fall (Tiling) hat damit seinen Probestein im Dev-Satz.
7. **Fusion-Orakel neu:** 0,0491 (worst muß-2 0,147) — die Decke
   liegt weiter unter beiden Routen; der referenzfreie Auswähler
   bleibt bis zum Bestätigungssatz gesperrt (Dev-Fishing-Verbot).
8. **Fixture-Qualität:** `marks_uncertain` 9/19 (verbundene
   Marken) — der Bestätigungs-Brief-Hinweis gilt fort.

**Maßnahmenplan (Reihenfolge = erwarteter Ertrag ÷ Risiko):**

| # | Maßnahme | Mechanismus | Stufe/Route | Stand |
|---|---|---|---|---|
| L1 | **Zonen-Ausweitung der Ritt-Doppelzonen-Kartenfahrt** (`RIDE_DOUBLE_ZONE_MARGIN_UNITS`) | der v0.5-Trigger bleibt, seine Wirkung wird zum ZONEN-Fenster ausgeweitet — der spätere Pass fährt die Karte durch den GANZEN Pinch, das X entsteht mit dem Winkel der Karte | Lotse | **v0.7 adoptiert 0,35** (§14; Punkt-Pinch-Klasse; Schleifen-Klasse blieb → L1b) |
| L1b/L1c | **Karten-Vorfahrt an Karten-Selbstschnitten**, roh (v0.8) bzw. ans Ink gepinnt (v0.9) | die Schleifen-Klasse ist kein Occupancy-Fall — der Ritt ersetzt den Karten-Selbstschnitt durch einen Board-Hop; das Fenster fährt die Karte, gepinnt an die Board-Punkte | Lotse | **v0.8 verworfen (aiou-Kill), v0.9 adoptiert 0,35** (§14: dev-19 gepaart −24 %, Netto-Defekte 7) |
| L1d/L1e | **Knoten-Anker-Pinnung der Karten-Läufe** (v0.10 Punkt-Knoten, v0.11 Plateau-Feld) | der Owner-Sichtfund aug19 (k-Kringel/W/r): verschmolzene Fenster-Läufe bis 4,3 xh reichen die rohe Karte durch; Anker = nächster Skelett-Verzweigungsknoten je Karten-Selbstschnitt, als starres Plateau global fusioniert | Lotse | **v0.10 verworfen (Punkt-Feld schert), v0.11 adoptiert "windows"** (§14 `aug19`: Defekte 7, missing 3 → 1, Ortsfehler −43 %, k-Kringel nachgefahren; "all" um ein Doppel-X verworfen) |
| L2 | ß-Klasse des Lotsen (Bögen-Strich ohne Stamm-Durchstoß, Sporn-Ritte) | Autopsie nach L1 (L1 kann die Stamm-Kreuzung schon liefern); dann eigener Arm | Lotse | durch v0.9 weitgehend gedeckt; **Rest-Autopsie erledigt `aug19`, Attribution korrigiert** (§14 „L2-Rest-Autopsie"): die Kollaps-Klasse unter + muß×3 ist ORDNUNGS-dominiert, aber KETTEN-seitig — die Assembly emittiert den abgesetzten Deckbogen zwischen den Runs (Permutations-Beweis: unter 0,450 → 0,085 byte-geometriegleich); Kandidat „marken-endständige Assembly" (eigene Pre-Reg + Re-Baseline) |
| G1 | p-Unterlängen-Schleife (Tafel kreuzt, Vorlage retraced) | Autorenentscheid Chart/Laufform — KEIN Composer-Hack (Doktrin: Manual nur, wo es Ground Truth schafft) | chart_ductus | **aufgelöst `aug19`** (§14 „Zweiter/Dritter Nachtrag"): die Komposition fährt die Unterschleife MIT, und das CHART-p kreuzt sogar — verloren geht der Durchstoß in der **Laufform-AGGREGATION** (der Anker-Median bügelt den Schleifenschluss glatt: Annäherungs-Spalt 0,126 → 0,081, der v2.1-Retrace-Filter wirft das tangentiale X zu Recht); messbarer Laufform-Arm **LF2 „p-Topologie"** (eigene Pre-Reg nach Autopsie), kein Composer-Hack, kein Autorenschritt |
| A3′ | Kreuzungs-Höhen als Variablen (jetzt mit das/die-Stapel-Evidenz) | die §7.3-A3-Route, unverändert Welle 3 | Kette | wartet |
| B2 | Tiling w/h ≤ 2 | die §7.4-Maßnahme; Galoppieren-T0-Zahl entscheidet die Dringlichkeit | InkSight | nach dem T0-Lauf dieser Session |
| — | Auswähler „Vier Augen" | gesperrt bis Bestätigungssatz | Fusion | steht |

Messdisziplin unverändert (§7.7): Lotse-Arme messen auf dem
19er-Dev-Satz gegen die `aug17`-Ketten-Baseline, Gates wie v0.1
plus die aiou-Zusatz-Kill-Schranke; Komposition/Kette bleiben in
dieser Runde unberührt (kein compose-golden-Bruch).
