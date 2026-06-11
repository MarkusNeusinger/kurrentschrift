# Qualitätsmetrik & Glyph-Bench

Wie die Qualität einer kanonischen Glyphe gemessen wird, wie der
hermetische Benchmark (`tools/glyphbench`) und der Experiment-Loop
(`/optimize-glyphs`) damit arbeiten, und was die Läufe bisher gelernt
haben — inklusive der verworfenen Sackgassen, damit niemand sie erneut
probiert. Ergänzt [`architektur.md`](../concepts/architektur.md) §5
(Schwellzug vs. Tinte) und §6 (Qualitätspipeline); die Implementierung
liegt in `core/quality.py`, das Werkzeug in `tools/glyphbench/`
(englisches README mit Fixture-Format und Output-Contract).

Stand: 2026-06-11, nach den PRs #63–#71.

---

## 1. Die Metrik: Score 0–100, rein geometrisch

Pro Glyphe wird die **gerenderte Silhouette** (Kapsel-Union bei 240
Samples — exakt der Diagnose-/Animations-Render) gegen die
**binarisierte Tinte des Crops** bewertet. Vier Komponenten, gewichtet
zu einem Score (100 = perfekte Übereinstimmung):

| Komponente | Gewicht | Misst | Frage |
|---|---|---|---|
| Dice (Flächendeckung) | 0.45 | Überlappung Rendering ↔ Tinte | „Sieht es aus wie der Crop?“ |
| Chamfer (Randabstand) | 0.25 | Abstand der Konturen in px, symmetrisch, Mittel + p95 | „Liegt die Kante auf der Tintenkante?“ |
| Mittellinien-RMSE | 0.20 | Abstand Centerline ↔ Skelett | „Folgt der Weg beim Schreiben der Tinte?“ |
| Welligkeit | 0.10 | Totalvariation des Breitenprofils relativ zum Profil der Tinte selbst | „Ist der Schwellzug so ruhig wie das Original?“ |

Die Abkling-Konstanten der Exponentialterme sind dieselben Toleranzen
wie das `converged`-Verdikt des Fits (`CONVERGED_GEO_RMSE_UNITS` usw.)
— „eingepasst“ und „hoher Score“ stimmen per Konstruktion überein.

**`loss = 1 − score/100`** ist dieselbe Information, nur „kleiner ist
besser“ (Loop-Konvention). **`bench_loss`** ist der *Mittelwert* der
Glyph-Losses über alle Fixtures — bewusst Mittelwert statt Median,
damit eine einzelne verschlechterte Glyphe die Kopfzahl sichtbar
bewegt. Eine crashende Glyphe zählt als Loss 1.0.

**Graustufen gehen nicht in den Score ein.** Die Metrik ist rein
geometrisch; die Tintenschwärze (Eintauchzyklus, Ausbleichen) ist per
§5 ein getrennter Kanal für das authentische Rendern, nicht für die
Formtreue. Graustufen wirken nur an einer Stelle: bei der
Binarisierung, die festlegt, welche Pixel als Tinte zählen — und die
ist in den Referenzen eingefroren (siehe §2).

### Messboden — warum 100 unerreichbar ist

Selbst eine pixelperfekte Rückgabe des synthetischen Testbalkens
erreicht nur ≈ 92: runde Federkappen vs. eckige Balkenenden plus
±0.5 px Binarisierungs-Unsicherheit an jeder Kante des 1866er Drucks.
Auf den echten Glyphen heißt das: **hohe 80er / niedrige 90er ≈ im
Rahmen der Messbarkeit perfekt.** Die verbleibenden Verluste
konzentrieren sich auf Haarlinien (kleine Fläche → kleine Kantenfehler
kosten viel Dice) und Kreuzungen (die Distanztransformation misst den
Blob beider Striche). Für die letzten Punkte sind die Overlays
(`--artifacts`) aussagekräftiger als die Zahl.

---

## 2. Der Bench: eingefrorene Referenzen

`tools/glyphbench` ist hermetisch und deterministisch (zwei Läufe auf
identischem Code → bit-identische `bench_loss`):

- **Die Pipeline unter Test rechnet alles neu** — aus den committeten
  Chart-Bytes + den im Fixture-Snapshot eingefrorenen Roh-Wegen
  (`raw_path`) und Bbox-Kalibrierungen, mit dem aktuellen Code und der
  aktuellen empfohlenen Ankerdichte. Code-Änderungen schlagen also voll
  durch; gespeicherte Templates liest der Bench nie.
- **Das Bewertungsziel ist eingefroren** (`ref_mask.png`,
  `ref_skel.npz` aus dem einmaligen, read-only DB-Export). Ein
  Experiment kann die Metrik nicht „verbessern“, indem es die
  Binarisierung verschiebt — die Torpfosten stehen fest.
- **Re-Baseline ist eine bewusste menschliche Entscheidung**
  (Re-Export der Fixtures). Zahlen über eine Re-Baseline hinweg sind
  nicht vergleichbar. Ein Re-Export bei unveränderten Roh-Eingaben
  reproduziert die Referenzen bit-identisch (2026-06-11 verifiziert).

Befehle, Fixture-Layout und der greppbare Output-Contract stehen im
`tools/glyphbench/README.md`; das Experiment-Protokoll (eine Hypothese
→ ein Commit → ein Bench-Lauf → keep/revert, `results.tsv`) im Skill
`.claude/skills/optimize-glyphs/SKILL.md`.

---

## 3. Baseline-Historie

Alle Werte auf denselben eingefrorenen Referenzen (12 gesperrte
Loth-Glyphen, Positions-Fan-out dedupliziert):

| Datum | PR | Änderung | bench_loss | Ø-Score |
|---|---|---|---|---|
| 2026-06-11 | #63 | Metrik + Bench (Ausgangszustand der Pipeline) | 0.1641 | 83.6 |
| 2026-06-11 | #64 | Corner-Knoten + Boundary-Refine | 0.1488 | 85.1 |
| 2026-06-11 | #68 | Ankerdichte 50 → 120 | 0.1339 | 86.6 |
| 2026-06-11 | #71 | Druckkegel-Prior + Refine-Tuning (Lauf `jun11`) | 0.1251 | 87.5 |

Ankerdichte-Sweep (#68, alle 12 Glyphen): 50 → 0.1488 · 80 → 0.1363 ·
120 → 0.1339 · 160 → 0.1321 · **240 → 0.1563 (Regression!)**. 120 ist
das Knie mit der besten Worst-Glyph-Balance; jenseits von ~160 hört
das 240-Sample-Rendering auf, den Spline zu überabtasten, und das
Parameterbudget des Refines wächst über sein Iterationslimit.

---

## 4. Erkenntnisse aus Lauf `jun11` (#71)

### Behalten

- **Druckkegel-Prior** (`PRESSURE_CONE_WEIGHT = 0.2`): Spitzfeder-
  Mechanik als einseitige Obergrenze — die Federzungen spreizen nur
  beim *Ziehen* entlang der Druckachse; beim Auf- oder Querstrich
  bohrte sich die gespreizte Feder ins Papier. Gemessene Breiten über
  der richtungsabhängigen Kappe sind daher Messartefakte (Kreuzungs-
  Blobs, Treppenstufen), nie echte Tinte. Die Achse wird pro Glyphe
  selbst kalibriert (breitengewichtetes axiales Mittel der Tangenten);
  dünner als die Kappe ist immer erlaubt.
- **Iterationsbudget 100 → 200** (`REFINE_MAX_ITER`): war für ~50
  Anker dimensioniert; bei K=120 verdreifacht sich die Parameterzahl.
- **Sample-invariante Kappen-Gewichtung** (`CAP_TERM_WEIGHT`, eigene
  Normierer): Unter dem gemeinsamen Normierer verwässerte jede
  Erhöhung der Sampling-Dichte den Zug der vier Kappen-Punkte — vom
  Cap-Reach-Regressionstest korrekt als rotes Gate erwischt, bevor die
  Dichte-Erhöhung übernommen wurde.
- **Boundary-Sampling 120 → 180** (`DEFAULT_N_SAMPLES`): ≈ 1.5
  Randpunkte pro Anker; erst nach der Kappen-Invarianz sicher.

### Verworfen

- **Mehr als ~160 Anker** — Render-Budget (240 Samples) und
  Optimierer-Budget skalieren nicht mit; Qualität kippt (s. Sweep).
- **Gauß-Vorglättung vor der Binarisierung** (Subpixel-Kanten): schiebt
  die Kanten der abgeleiteten Maske systematisch gegen die
  *eingefrorene* Referenzmaske — verliert immer (0.138). Wer die
  Binarisierung selbst für falsch hält, braucht eine bewusste
  Re-Baseline, kein Experiment.
- **`width_smooth_weight` 1e-4 → 5e-5**: Mittelwert schlechter; der
  Druckkegel ersetzt die generische Glättung nicht.
- **Druckkegel-Gewicht 0.5**: drückt echte Breiten platt
  (Median-IoU sinkt) — 0.2 ist das Knie.
- **Vierte Outer-Round**: No-op, der 2-%-Early-Stop endet bei drei.

### Offene Richtungen

- **Richtungsabhängiges Breitenmodell** als Voll-Prior (wenige
  Parameter: Maximalbreite, Haarlinie, Kegelöffnung, Übergangsschärfe)
  — die Druckachse ≈ Schräglage ist pro Chart bekannt; die Parameter
  sind zugleich §12-Stilanalyse-Merkmale pro Hand.
- **Haarlinien & Kreuzungen** bleiben der Messboden; Fortschritt dort
  eher über bessere Vorlagen-Scans/eigene Handproben (mit echtem
  S-Pen-Druck als Eingangsdimension) als über weitere Regularisierer.

**Verbindlichkeit:** Die Verworfen-Punkte gelten wie überall im Repo —
neue Argumente dafür gehören nach `docs/proposals/`, nicht in einen
neuen Loop-Versuch mit denselben Mitteln.
