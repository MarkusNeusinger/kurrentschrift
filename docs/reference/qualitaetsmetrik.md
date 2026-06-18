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

> **Zwei Metriken, eine pro Schrift (Stand 2026-06-18).** Kurrent und
> Sütterlin nutzen verschiedene Schreibgeräte (Spitzfeder/Schwellzug vs.
> Redisfeder/Gleichzug) und haben darum **getrennte** Metriken. Die
> Abschnitte §1–§4 unten beschreiben ab jetzt **nur die Kurrent-/
> Schwellzug-Metrik** (`core/quality.py::template_quality_metrics`,
> unverändert). Die **Sütterlin-Natürlichkeitsmetrik** steht in §5
> (`core/quality_suetterlin.py`). Der Bench läuft **eine Schrift pro
> Lauf** (`--style suetterlin` Default · `--style kurrent`); es gibt
> **keinen** kombinierten `bench_loss` über beide — einen Schwellzug-
> und einen Gleichzug-Score zu mitteln wäre bedeutungslos.

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

---

## 5. Sütterlin-Natürlichkeitsmetrik (Re-Baseline 2026-06-18)

Die §1–§4-Metrik bewertet **Pixeltreue zum Scan** (Dice + Chamfer
dominieren). Für Sütterlin ist das falsch: der Scan ist pixelig, und der
Welligkeits-Term ist bei konstanter Breite tot (`tv_rendered ≈ 0` →
immer 1.0). Oberstes Kredo hier: der gerenderte Buchstabe soll **von
einem mit Stift geschriebenen nicht unterscheidbar** sein — nicht
pixelgenau zum zackigen Scan passen. Implementierung:
`core/quality_suetterlin.py` (+ reine Primitive in `core/geometry.py`).

**Zwei Stufen — Deckung als Tor, Natürlichkeit als Entscheider:**

```
score = 100 · Tor^0.5 · Natürlichkeit
Tor   = Dice · Q_chamfer · Q_geo          (∈ [0,1])
Natürlichkeit = Σ w_k·Q_k / Σ w_k   über die ANWENDBAREN Terme
loss  = 1 − score/100
```

Das Tor ist multiplikativ: eine glatte Glyphe am falschen Ort kann nicht
hoch scoren. Chamfer und Geo-RMSE laufen mit einem **Pixel-Totband**
(`DEAD_BAND_PX = 0.75`): Abweichung unterhalb der Scan-Quantisierung
kostet nichts — Sub-Pixel-Treue zum jagged Scan wird weder belohnt noch
bestraft.

**Natürlichkeitsterme (referenzfrei, am gerenderten Centerline, je 0–1):**

| Term | Gewicht | Misst | Anwendbar wenn |
|---|---|---|---|
| Glätte | 0.30 | keine Zacken: geglättete **2.-Differenz** der Krümmung (0 für Gerade, Kreis *und* fließenden Übergang; nur Oszillation zählt) | immer |
| Vertikalität | 0.25 | RMS-Horizontalwander gerader Senkrechtläufe | ein Senkrechtlauf existiert |
| Eckenschärfe | 0.20 | Geradheit der beiden Anläufe an die Kehre (Apex ausgenommen) | eine Within-Stroke-Ecke existiert |
| Kollinearität | 0.15 | gerader Strich durch eine Kreuzung: Gerade vor/nach identisch (δθ, δd) | echte Gerade-kreuzt-Gerade |
| Rückzug | 0.10 | zwei deckungsgleiche Pässe bleiben parallel (das s/t hin-und-zurück) | echter Rückzug: beide Pässe über **Stammlänge** gerade |

**Anwendbarkeits-Gates (zentral):** Kollinearität und Rückzug feuern in
Sütterlin-Kleinbuchstaben fast nie, weil es dort kaum echte Gerade-
kreuzt-Gerade-Kreuzungen oder gerade Rückzüge gibt. Eine **gebogene
Schleifen-Selbstkreuzung** (e, d, l, g, b) ist *keine* Geraden-Kreuzung
→ N/A, nicht bestraft (Gate: Vorher-/Nachher-Gerade müssen ≈ eine Linie
sein, < `CROSS_APPLY_ANGLE_DEG` = 10°). Ein Rückzug muss über Pässe
laufen, die über eine **stammlange** Fensterlänge gerade sind
(`RETRACE_STEM_WINDOW_UNITS` = 0.45, `…_TOL` = 0.10): so fällt der
n-artige **e**-Doppelbogen raus — seine beiden anti-parallelen Hälften
sind über kurze Strecke gerade, biegen sich aber über Stammlänge (das
killte den e-Fehlfeuer im Re-Baseline 2026-06-18). Eine Schleife, die nur
einen Stamm streift (b/g/l), ist gerade *und* deckungsgleich, aber unter
> 15° → vom Winkel-Apply-Gate (`RETRACE_APPLY_ANGLE_DEG` = 15°)
ausgeschlossen. Ein Term, der nicht anwendbar ist, fällt aus dem
gewichteten Mittel (renormiert).

**Messboden / Anti-Gaming:** Die Natürlichkeitsterme sind referenzfrei —
robust gegen Scan-Pixelung (genau der Punkt). Ein Verstecken von
Features (um den Term zu umgehen) verhindert das Deckungs-Tor: die
Sütterlin-Ableitung ist skelettgelockt (`core/suetterlin.py` snappt auf
die Medial-Achse), und `Q_geo`/`Q_chamfer` bestrafen jedes Abdriften.
Ein Skelett-Präsenz-Orakel (Term = 0, wenn die Tinte das Feature hat,
das Rendering nicht) ist die v2-Härtung für einen *nicht* skelett-
gelockten Generator — bewusst zurückgestellt. Ebenfalls v2: die volle
Spitzen-Schärfe + die legitime ~2×-Silhouette beim Rückzug (brauchen die
Medial-Achse des *gerenderten* Bildes).

**Kalibrierung (Mensch-im-Loop, gegen die 60 gesperrten Glyphen):**
Konstanten sind so getunt, dass die Metrik-Rangfolge der menschlichen
Natürlichkeits-Wahrnehmung folgt; die *Richtung* jedes Terms ist per
Test gepinnt (`tests/test_quality_components.py`), nur die Magnituden
sind getunt. Erkenntnisse der ersten Kalibrierung: Glätte als 1.-
Differenz der Krümmung konnte eine fließende Schleife nicht von Zacken
unterscheiden → 2.-Differenz + Krümmungs-Glättung. Eckenschärfe als
Apex-Konzentration war strukturell zu streng (der Spline verteilt einen
echten C0-Knick über mehrere Samples) → reine Anlauf-Geradheit. Ecken
sind seither ~0.08 statt ~0.42. **Re-Baseline 2026-06-18 (Rückzug):** ein
Sweep über den vollen gesperrten Satz fand genau einen Rückzug-Fehlfeuer
— das **e** (n-artiger Doppelbogen ohne Stamm) wurde als hin-und-zurück
bestraft, weil seine Bogen-Hälften über das kurze 0.20u-Fenster gerade
wirken. Fix: Geradheit über **Stammlänge** prüfen (0.45u). Das war der
*einzige* Diskriminator, der e isoliert (globale Geradheit, Nettodrehung,
Spitzen-Krümmung trennen e nicht — e hat eine scharfe Spitze wie ein
echter Rückzug). Nebeneffekt (adversarial verifiziert als korrekt, keine
Regression): k/q verlieren ihre Schleifen-Übergangs-Enden (gebogen, keine
Divergenz) → ~0; t/ſ steigen (echte Divergenz der geraden Pässe). v2-Idee:
jeden Einweg-Pass direkt auf eine Gerade fitten (fängt einen Veer, bei dem
*beide* Pässe im Gleichschritt biegen — heute winkelblind).

**Baseline (35 deduplizierte gesperrte Sütterlin-Glyphen, 2026-06-18):**

| `bench_loss` | Glätte | Vertik. | Ecke | Kollin. | Rückzug | Deckung |
|---|---|---|---|---|---|---|
| **0.2126** | 0.131 | 0.054 | 0.077 | 0.185 | 0.048 | 0.185 |

Der gesperrte Satz wuchs auf das volle Alphabet (a–z, ä, A/B/C/D/E, K,
**ſ**); identische Positions-Fan-outs werden zu einer Berechnung
zusammengefasst (35 statt 60 Keys). Schlechteste: `ſ` 0.407 (Rückzug +
Kollinearität — das Lang-s ist der härteste Rückzug), dann `B` 0.391,
`E` 0.309, `t` 0.293. **Diese Zahlen sind NICHT mit §1–§4 noch mit der
0.21-Baseline vom 60-Key-Satz vergleichbar** (andere Metrik bzw. anderer
Fixture-Satz). `core/quality_suetterlin.py` + `core/geometry.py` sind mit
der Metrik **eingefroren** (gehören in die Frozen-Liste des Loops); die
intrinsischen Terme haben kein eingefrorenes Ziel — die Frozen-Reference-
Regel bindet nur die Deckung.
