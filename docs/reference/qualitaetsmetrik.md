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
| Rückzug | 0.10 | **Treue (v2)**: wie viel der Tinte im Rückzugs-Gebiet das Rendering FÜLLT (Recall) — Über-Kollaps und Linse lassen Tinte ungefüllt → niedrig, ein sauberes V füllt → hoch | echter Rückzug: beide Pässe über **Stammlänge** gerade |

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
killte den e-Fehlfeuer im Re-Baseline 2026-06-18). Über diese Geradheits-
plus Spalt-Gates (`RETRACE_MAX_GAP_NIB`) feuert der Term nur auf f/k/ſ/q —
b/g/l/h (Schleife streift Stamm) fallen schon an der Stammlängen-Geradheit
heraus. Der frühere **Winkel-Apply-Gate** (`RETRACE_APPLY_ANGLE_DEG`)
diente nur dem alten Parallelitäts-Signal und ist mit der Treue-v2 (s.u.)
entfallen: ein divergierendes sauberes V ist genau das, was die Treue
*belohnt*, nicht ausschließt. Ein Term, der nicht anwendbar ist, fällt aus
dem gewichteten Mittel (renormiert).

**Messboden / Anti-Gaming:** Vier Terme (Glätte, Vertikalität, Ecke,
Kollinearität) sind referenzfrei — robust gegen Scan-Pixelung (genau der
Punkt). Der fünfte, **Rückzug-Treue (v2)**, ist der eine *crop-referenzierte*
Term: die Spitzen-Treue ist auf dem Centerline allein unsichtbar (ein
deckungsgleicher Über-Kollaps ist makellos glatt + parallel), gegen den Scan
aber offensichtlich. Ein Verstecken von Features verhindert ohnehin das
Deckungs-Tor: die Ableitung ist skelettgelockt (`core/suetterlin.py` snappt
auf die Medial-Achse), und `Q_geo`/`Q_chamfer` bestrafen jedes Abdriften.
Ein Skelett-Präsenz-Orakel (Term = 0, wenn die Tinte das Feature hat,
das Rendering nicht) ist die v2-Härtung für einen *nicht* skelett-
gelockten Generator — bewusst zurückgestellt.

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

### Phase B — Generierung: Kollinearität an Kreuzungen (2026-06-19, Lauf `jun19-suet`)

**`/optimize-glyphs`-Lauf gegen die eingefrorene Metrik** (nur `core/suetterlin.py`
geändert; Metrik unverändert → Zahlen **mit der 0.2126-Baseline vergleichbar**).
`bench_loss 0.2126 → 0.1983` (−6.4 %, Kollinearität 0.185 → 0.081). Neue letzte
Generierungsstufe `_straighten_crossings`: nach der Vertikalisierung wird auf den
finalen Ankern jede *transversale* Kreuzung (gefunden mit der Metrik-eigenen
`detect_crossing_passages`, also exakt die von `crossing_collinearity` bewerteten
Stellen) geprüft — laufen die beiden Anläufe eines durchlaufenden Stamms gerade
und in *einer* Linie, wird der Stamm auf eine TLS-Gerade (bei Quasi-Vertikale auf
echte Senkrechte) gezogen, sonst unberührt gelassen. Drei behaltene Hebel:

1. **Geraden-Durchführung auf den finalen Ankern** (nach Vertikalisierung, damit
   keine spätere Stufe sie wieder verbiegt). d/g/l/B/E/p/h Kreuzungen sauber.
2. **Quasi-vertikaler Stamm → echte Senkrechte** statt der leicht gekippten
   TLS-Geraden (heilt eine Vertikalitäts-Regression, macht den Stamm exakt kollinear).
3. **Prüf-Fenster 0.45u (weiter) entkoppelt vom Fit-Fenster 0.35u**: das weite
   Prüf-Fenster lässt die Anläufe einer *kurzen* Geraden zwischen Bögen (d/p
   Bauch→Stamm) im Winkel auseinanderlaufen → Winkel-Gate schließt sie aus (sie
   sind in der Metrik N/A und dürfen nicht zu einem bewerteten Knick werden); ein
   echter langer Stamm (f/g/l/ſ) bleibt unter dem Winkel.

**Verworfen im Lauf:** Trigger über den *breitenbasierten* `_crossing_mask` (verfehlt
Schlaufe-über-Stamm-Kreuzungen, die nicht 2× breit sind); Straffung **vor** der
Vertikalisierung (verbiegt d/k/p neu); Fit-Fenster 0.09-Toleranz (schließt ſ aus);
Nachbar-Blob-Merge (heilt ſ nicht, schadet p). **Offen:** der ſ-Rückzug bleibt bei
~0.76 — die *breite* Projektion (nötig für die Kollinearität von B/l/E/p/g) treibt
ſ's eng benachbarte Doppelstamm-Pässe auseinander; ſ ist dennoch besser als die
Baseline (0.407 → 0.373). Ein **eigener Rückzug-Straffer** (jede Einweg-Bahn auf
eine Gerade fitten) wäre der nächste, separate Schritt — mit Risiko für t/f/k/q.

### Re-Baseline 2026-06-20 — Rückzug-Treue + lokales Geo-Totband

**Bewusste Metrik-Re-Baseline (kein `/optimize-glyphs`-Lauf):** die §1–§4-/Phase-B-Zahlen
sind hierüber **nicht** vergleichbar. Anlass: der gerenderte Spitzen-Tip von ſ/t sah trotz
guter Metrik unnatürlich aus (PR #105 ersetzte den binären Tip-Kollaps durch einen
*getaperten* Offset — scharfe Spitze, dann sauberes V). Die alte Metrik **belohnte den
Über-Kollaps**: zwei deckungsgleiche Pässe sind perfekt parallel (Rückzug-q→1) *und* bleiben
auf der Medial-Achse (Geo-Tor hoch) — genau die „2 Linien perfekt übereinander". Zwei
pro-Kollaps-Signale wurden gefixt:

1. **Rückzug: Parallelität → Treue.** `retrace_parallelism` → `retrace_fidelity`: statt des
   Winkels zwischen den Pässen misst der Term den **Recall des Renderings gegen die Crop-Tinte**
   im Rückzugs-Gebiet (Pixel innerhalb `RETRACE_REGION_RADIUS_NIB` = 2.5·nib der geraden+nahen
   Paare). Über-Kollaps verfehlt die Keil-Flanken, eine Linse die feste Mitte — beide → niedrig;
   ein treues V → hoch. Behebt zugleich die **k/q-Blindheit** (ihre kurzen Tips lasen früher
   `retr 0.000` egal was gerendert wurde; jetzt anwendbar + korrekt bewertet). Kein neues
   Fehlfeuer (gleiche f/k/ſ/q-Fläche). ſ-Rückzug **0.806 → 0.135** (auf dem korrekten Taper-Render).
2. **Geo-Tor: lokales Totband.** `geo_db_rmse` bestrafte jeden Sample fürs Verlassen der
   Medial-Achse — also den *legitimen* Kantenversatz im verschmolzenen Gebiet, womit das Tor den
   Kollaps belohnte. Fix: das Totband ist nun **lokal** = `max(DEAD_BAND_PX, lokale_Skelett-Halbbreite −
   nib)` (die Halbbreite am nächsten Skelettpunkt aus `width_map`). Auf einem Einzelstrich ist die
   Skelett-Halbbreite ≈ nib → Totband = `DEAD_BAND_PX`, **nichts ändert sich**; nur verschmolzene
   Gebiete (Spitzen-Doppelstamm, Schlaufe-über-Stamm) verzeihen den Versatz bis zum Merge-Überschuss.

Damit bevorzugt die Metrik den korrekten Render: ſ Taper-`loss` **0.112 < 0.128** Binär-Kollaps
(vorher umgekehrt). **Bekannte Grenze — t:** t's kurzer, gebogener Tip fällt am Stammlängen-
Geradheits-Gate heraus (N/A, wie der e-Bogen, das Gate muss eng bleiben), und der Kollaps *glättet*
zudem t's Centerline (bessere Glätte/Vertikalität/Ecke) — die Metrik bevorzugt für t den Kollaps
noch knapp (~0.012). Ein Lockern des Geradheits-Gates fängt t nicht (Rückzug-Gewicht 0.10 zu klein,
und es addiert kleine e/K/p-Strafen) → bewusst nicht getan; t's Rest-Bias ist ein tieferes
Glätte/Ecken-Thema (der Term belohnt das Weglassen einer echten Kehre) für einen späteren Schritt.

**Neue Baseline (35 deduplizierte Glyphen, 2026-06-20):**

| `bench_loss` | Glätte | Vertik. | Ecke | Kollin. | Rückzug | Deckung |
|---|---|---|---|---|---|---|
| **0.1865** | 0.126 | 0.058 | 0.073 | 0.055 | 0.008 | 0.184 |

ſ fällt auf 0.112 (war als Härtester gestartet); Deckung sinkt netto (0.191 → 0.184), weil das
lokale Totband den legitimen Kantenversatz auch an Schlaufen-Kreuzungen (b/d/g/o…) nicht mehr
bestraft. Tests: `tests/test_quality_components.py` pinnt jetzt **Treue füllt > unterfüllt** statt
parallel > divergent. `core/quality_suetterlin.py` + `core/geometry.py` bleiben im Loop eingefroren.

---

## 6. Wort-Bench: Übergänge gegen echte Wortproben (2026-07-02)

Eine Ebene über der Glyph-Bench: `tools/wordbench` bewertet das **komponierte
Wort** — Platzierung + generierte Übergänge aus `core/shaping.py` +
`core/compose.py` (seit PR #143 die einzige Kompositionsquelle, auch hinter
`GET /write/word`) — gegen **gemeinfreie Wortproben derselben Hand**. Für
Sütterlin: alle 63 Wörter der Abbildung 19 des Leitfadens 1922 („Die
Ausgangsschrift im Zusammenhang geschrieben") plus, als **getrenntes Set mit
eigener Headline `pair_loss`**, die 33 isolierten Buchstabenverbindungen der
Abbildung 20 — vermessen in `data/sources/suetterlin-1922/words.json`
(Rechteck + aus der Tinte gemessene Grund-/Mittellinie je Zeile; die Tafeln
haben keine gedruckte Lineatur; Boxen vorgeschlagen von
`tools/wordbench/propose_boxes.py` und Zeile für Zeile visuell verifiziert).
Werkzeug-Details und Output-Contract: `tools/wordbench/README.md`; die Metrik
liegt in `tools/wordbench/metric.py` (Bench-only, nicht Produktionscode).

**Score:**

```
loss = 0.45·Übergang + 0.35·Deckung + 0.20·Breite      (je ∈ [0,1], kleiner besser)
```

- **Übergang** — Vorwärts-Chamfer der *generierten Verbindungsstriche* zum
  Proben-Skelett plus Rückwärts-Chamfer der Proben-Tinte innerhalb der
  Konnektor-x-Spannen. Das Leitsignal: liegt der Übergang da, wo die echte
  Feder lief?
- **Deckung** — symmetrischer Chamfer über alle komponierten Centerlines.
  Bewegt sich auch mit der Autoring-Qualität der Einzelglyphen → Tor, nicht
  Entscheider.
- **Breite** — |log|-Verhältnis der Gesamt-Tintenbreite: Rhythmus-/
  Spacing-Fehler, die punktweiser Chamfer kaum sieht. Bei den PAAREN trägt
  diese Komponente einen konstanten Bias (die Tafel zeichnet An-/Auslauf-
  striche, die das isoliert komponierte Paar nicht hat) — für Paare ist
  `Übergang` das Leitsignal.
- Ein Wort, dessen Komposition crasht, zählt `1.0` (Glyph-Bench-Regel).
  Ein Eintrag, dessen Template schlicht **noch nicht autorisiert** ist, wird
  beim Export als `scorable: false` eingefroren und vom Runner **geskippt +
  namentlich reportet** (`words_skipped_ids:`) — eine Autoring-Lücke darf die
  Kompositions-Headline nicht ertränken, bleibt aber sichtbar (seit dem
  Re-Baseline `jul05`; davor zählte auch das fehlende Template `1.0`).

**Frozen-Reference-Regel erweitert:** Eingefroren sind Maske (binarisiert +
entfleckt), Skelett + EDT, die **geshapten Slots** (eine Shaping-Änderung ist
ein bewusstes Re-Baseline, kein stiller Input-Shift), die Template-Zeilen und
der gepoolte Nib. Die **Registrierung ist Teil der Metrik und begrenzt**:
Skala fix aus der gemessenen Lineatur, Translation ±0,6 x-Höhen / ±4 px per
Vorwärts-Chamfer gewählt und pro Wort reportet — ein Experiment kann sich
nicht durch Verschieben verbessern. Ein Lauf = eine Schrift (kein kombinierter
`bench_loss`, wie bei der Glyph-Bench). **Cross-Hand-Vorsicht:** strenge
Ganzwort-Tore nur gegen gleiche Hand; Fremdhand-Proben (Vos, Petzendorfer)
später nur für Übergangs-/Form-Scores.

**Baseline (15 Wörter, Abbildung 19, 2026-07-02):**

| `bench_loss` | Übergang | Deckung | Breite | schlechtestes Wort |
|---|---|---|---|---|
| **0.1397** | 0.104 | 0.133 | 0.231 | `wenn` 0.263 |

Die Komponenten decken sich mit dem Prod-Live-Befund vom Audit 2026-07-01:
Breite ist die größte Strafe (komponierte Wörter deutlich schmaler als die
Probe — der konstante `CONNECT_GAP` erzeugt keinen Gleichmaß-Rhythmus), und
die schlechtesten Wörter (`wenn` 0.263, `zwei` 0.244, `einen` 0.239) enthalten
die w-/Mittelband-Exit-Verbindungen, deren Kollaps der Live-Test zeigte. Damit
misst die Bench genau das, was Phase D (Exit-Klassen, Kopplungshöhen,
G2-Joins, paarabhängiger Abstand) verbessern soll.

**Frozen-Liste des `/optimize-glyphs`-Loops erweitert:** bei Wort-Läufen sind
zusätzlich `tools/wordbench/metric.py`, `tools/wordbench/export_fixtures.py`
und die Fixtures eingefroren; editiert wird `core/compose.py` (und ggf.
`core/pipeline.py`-Rendergeometrie), nie die Messlatte.

### Lauf `jul02` — Übergangs-Redesign in `core/compose.py` (2026-07-02)

Erster Experiment-Loop gegen die eingefrorene Wort-Metrik (nur
`core/compose.py` geändert → Zahlen **mit der 0.1397-Baseline vergleichbar**).
`bench_loss` **0.1397 → 0.1206** (−13,6 %; Übergang 0.104→0.113,
Deckung 0.133→0.118, Breite 0.231→0.142). Die Katastrophen-Wörter des
Prod-Audits tragen den Gewinn: `wenn` 0.263→0.202, `zwei` 0.244→0.178,
`einen` 0.178→0.075, `zum` 0.154→0.104. Behaltene Hebel:

1. **Rückwärts-Exit-Guard**: Zeigt die gerenderte Auslauf-Tangente nach links
   (w/v-Bogen rollt am Ende zurück, gemessen −151° bei w), zielt der
   Verbindungsstrich auf die nächste Entry statt der Tangente zu folgen —
   der „wovon"-Schleifenkollaps aus dem Live-Test ist damit weg.
2. **Tinten-Freiraum im Verbindungsband** (`INK_CLEARANCE` 0.14 in
   `JOIN_BAND_Y` −0.15..0.8): Platzierung als
   `max(exit + CONNECT_GAP, ink_maxX + clearance)` — die Exit-Anker allein
   tragen den Rhythmus nicht (w's Exit liegt 0,27 Einheiten LINKS seiner
   rechtesten Tinte → Folgebuchstabe startete in der Tinte). Kerning-Prinzip:
   Ober-/Unterlängen außerhalb des Bands dürfen die Nachbarspalte überlappen
   wie auf der Lehrtafel (heilte das/die/regieren nach dem ersten Versuch mit
   Ganzhöhen-Extents).
3. **Handle-Clamp an der Horizontaldistanz** (`min(0.4·span, 0.5·hspan)`):
   steile Abstiege (d/t hoch → tiefe Entry) beulten die Kubik als S-Bogen aus.
4. **Hoch-Exit-Chord** (`HIGH_EXIT_Y` 1.05): das hohe d kehrt sichtbar in den
   Join um — die Sehne ist dort die ehrliche Ecke.
5. **Bogen-Launch-Clamp** (`BOW_EXIT_Y` 0.7, Startwinkel −35°..+5°): b's
   Bogen schließt steigend (44°), der Join läuft aber flach aus dem Bogen —
   metrisch neutral, im Overlay/`haben` sichtbar deckungsgleicher.

**Verworfen im Lauf:** pauschal `CONNECT_GAP` 0.16→0.30 (Netto nur −0.004:
richtig breite Wörter wie `das`/`mit` überschießen — der Abstand muss an der
Tinte hängen, nicht am Anker); Tinten-Freiraum über die GANZE Glyphhöhe
(drückt Nachbarn von d-Schleifen weg, +0.07 auf `das`). **Erkenntnis zur
Metrik:** Die globale Registrierung vermengt Buchstabenbreiten-Unterschiede
(Autoring: unsere e/n sind schmaler als die der Probe) mit Join-Qualität —
ein Rest-Drift in `unter`/`mit` ist Autoring-, nicht Compose-Thema. Die
Golden-Fixture (`tests/fixtures/compose_golden.json.gz`) wurde nach dem Lauf
bewusst re-baselined (`REGEN_GOLDEN=1`) — sie pinnt jetzt die NEUE Komposition.

### Re-Baseline `jul05` — Vollabdeckung Abb. 19 + Paar-Bench Abb. 20 (2026-07-05)

Bewusstes Re-Baseline durch **Datenerweiterung**, Composer unverändert
(Zahlen daher **nicht** mit 0.1206 vergleichbar — 0.1206 bleibt der letzte
Compose-Stand über den historischen 15 Wörtern):

- `words.json` vollständig: **63 Wörter** (statt 15) der Abbildung 19 und
  **alle 33 Paare** der Abbildung 20 (`kind: pair`). Boxen automatisch
  vorgeschlagen (`tools/wordbench/propose_boxes.py`: Zeilenbänder aus der
  Tinten-Projektion, Komponenten-Clustering mit 5-px-Lückenschwelle,
  Lineatur aus der Hüllkurve; validiert gegen die 15 Bestands-Boxen mit
  Lineatur-Fehler ≤1 px) und Zeile für Zeile visuell verifiziert. Die
  Paar-**Transkription** wurde formverifiziert gegen die Buchstabenzellen
  der eigenen Tafel (Schluss-s = „6" mit voller Oberlänge, top 2,0 x-Höhen
  wie b/k — Höhe trennt nicht, nur die Form; x = offene Schleife unter die
  Grundlinie): sieben Paare der früheren `SOURCE.md`-Lesung waren s/x-als-
  b/e-Verwechslungen (bb→bs, be→bx, db→ds, de→dx, vb→vs, ve→vx, re→rx),
  dazu der Reihe-4-Tippfehler „ri"→„xi" sowie — vom Autor am 2026-07-06
  entschieden — „vu"→`on` (erster Buchstabe ist o, kein v; ohne u-Bogen = n)
  und „Ju"→`In` (Versal ohne Unterlänge = I, kein J; ohne u-Bogen = n).
  Duplikate tragen `id`-Suffixe (`muß`/`muß-2`/`muß-3`), Interpunktion und
  die Apostrophe der Elisionen (`han`, `Sporn`) bleiben per
  Box-Grenze/`exclude` draußen.
- Exporter/Runner: `--set words|pairs|all`, Paar-Fixtures als
  Geschwister-Set `suetterlin-1922-pairs`, `scorable`-Skip-Semantik (s. o.),
  optionales `slots`-Override pro Sidecar-Eintrag (für Paare, deren isolierte
  Schreibung vom Wort-Shaping abweichen sollte — Stand jul05 ungenutzt:
  die Paare sind mit An-/Auslauf als Initial+Final-Formen stimmig).

**Baselines (Composer-Stand = `jul02`/PR #145):**

| Set | Headline | Übergang | Deckung | Breite | gescort / geskippt | schlechtester Eintrag |
|---|---|---|---|---|---|---|
| Wörter (Abb. 19) | `bench_loss` **0.1844** | 0.166 | 0.185 | 0.224 | 48 / 15 | `Einen` 0.532 |
| Paare (Abb. 20) | `pair_loss` **0.1793** | 0.142 | 0.154 | 0.307 | 31 / 2 | `Bi` 0.341 |

Geskippt (Autoring-Backlog, nicht Compose): `S-initial` (Soldaten, Seiten,
Säbel, Silber, Sporn, Sprünge), `Z-initial` (Zaum, Zügel, Zorn), `W-initial`
(Wer, Wu), `sz-final/-medial/-initial` (muß ×3, daß, schießen, ßi). Bemerkens-
wert: D/J/O/B/E/F/G/K/P-Versalien sind autorisiert — 31 von 33 Paaren und 48
von 63 Wörtern scoren sofort, **0 Crashes**. Die schlechtesten gescorten
Einträge (`Einen` 0.532, `zu` 0.496, `wenn-2` 0.475; Paare `Bi` 0.341,
`xi` 0.314) sind die Zielliste für den nächsten Compose-Loop.
**Festlegung (User, 2026-07-06):** Optimiert wird gegen die
**Wort-Headline** (`--set words`, der Normalfall der Schrift); die Paare
sind ausdrücklich die „nicht selbstverständlichen" Sonderfälle und bleiben
Mess-Evidenz (`pair_loss` wird reportet, nie Optimierungsziel des ersten
Loops — erst wenn die Wörter sitzen).

### Segment-Attribution + `tools/wordlab` (2026-07-08)

Diagnostik-Ausbau **vor** dem ersten Compose-Loop (Frozen-Metric-Disziplin:
Messlatten-Änderungen landen vor dem Loop, nie währenddessen). Beide
Headlines byte-identisch verifiziert (0.184426 / 0.179312 vor = nach):

- `compose_word(..., provenance=False)`: bei `True` tragen Glyph-Items
  `slot_index`/`glyph_key`, Konnektoren `pair=[prev_key, curr_key]` +
  `from_slot`/`to_slot`. Default off — `/write/word`-Payload und
  Golden-Fixture unverändert (kein `REGEN_GOLDEN`). Dieselbe Naht ist später
  der Hook für per-Paar-Overrides nach Vorschlag B (gegated, nichts wird
  gespeichert).
- `score_word_segments` (additiv in `tools/wordbench/metric.py`, gehört ab
  jetzt zur eingefrorenen Messlatte): pro Konnektor Vorwärts-/Rückwärts-
  Chamfer in der eigenen x-Spanne, pro Glyphe (Körper + nachgestellte
  Diakritika) dasselbe über die eigenen Samples — auf der Registrierung und
  Sättigungsskala der Headline, in Schreibreihenfolge gelabelt. Damit ist
  eine Abweichung einem Buchstaben **oder** einer konkreten Verbindung
  zuzuordnen, nicht nur dem Wort.
- `tools/wordlab` (Gegenstück zu glyphlab, geteilter Render-Kern): Overlay
  Probe + Skelett + farbcodierte komponierte Centerlines mit
  per-Konnektor-Penalty-Callouts; `--set pairs`, `--live` (read-only),
  `--sweep core.compose.KONSTANTE=v1,v2`. Die Zahl sagt wie viel, das
  Overlay sagt wo und warum.

### Re-Baseline `jul08` — Exclude-Kanten-Artefakt in den Referenzen (2026-07-08)

Erster Fund des neuen Wordlab, noch vor dem ersten Loop: In den `jul05`-
Referenzen zog sich durch **genau die sieben schlechtesten Wörter** (Einen,
kann, von, zu, wenn-2, mit-2, Kugel) ein horizontales Fake-Tinten-Band —
die Exclude-Rects wurden vor der Binarisierung papierweiß übermalt, und die
harte Weiß→Papier-Stufe an der Malkante binarisierte als durchgehende Linie
(bei `wenn-2` 30 % aller Skelett-Pixel). Der Reverse-Chamfer bestrafte jede
Komposition dafür, ein Artefakt nicht zu decken: die alte Worst-Liste war
überwiegend artefaktgetrieben (`Einen` 0.532 → 0.17, `kann` 0.487 → 0.182).

**Fix im Exporter** (`clear_excluded`): binarisiert wird der UNBEMALTE Crop
(keine Kante), Fremdtinte fliegt komponentenweise raus — jede Komponente mit
≥ 50 % ihrer Fläche in der Exclude-Vereinigung wird ganz entfernt (Schwänze
inklusive), Pixel strikt im Rect immer; weiß übermalt wird nur noch das
gespeicherte `crop.png` (Overlay-Hintergrund). Das einzig verbliebene
„Band" (`dk`, Paare) ist echte Tinte: der lange Deckstrich-Join des d→k.

**Baselines `jul08` (Composer unverändert = PR-#145-Stand; nicht mit `jul05`
vergleichbar):**

| Set | Headline | Übergang | Deckung | Breite | gescort / geskippt | schlechtester Eintrag |
|---|---|---|---|---|---|---|
| Wörter (Abb. 19) | `bench_loss` **0.1284** | 0.102 | 0.120 | 0.202 | 48 / 15 | `han` 0.265 |
| Paare (Abb. 20) | `pair_loss` **0.1762** | 0.142 | 0.146 | 0.307 | 31 / 2 | `ssi` 0.332 |

**Bereinigte Evidenz für den Loop** (Segment-Attribution über alle 48
Wörter): systematisch schlecht sind die Halbhoch-Exits `f→e` 0.220 / `t→e`
0.204 (Exit-Klassen-These aus Phase D), `n→n` 0.191 und `e→n` 0.160 bei
**12 Vorkommen** (größter Frequenz-Hebel); Einzelfälle `h→r` 0.326,
`r→f` 0.317, `l→v` 0.312, `e→h` 0.298, `z→w` 0.266. Schlechteste Glyphen-
Deckung: `d-initial` 0.223 (6×), `n-final` 0.179 (17×). Neue Zielliste:
`han` 0.265, `fechten` 0.243, `Gewehr` 0.233, `schwer` 0.227, `wenn` 0.203.
Breite bleibt die größte Komponente (0.202) — die Wörter komponieren
weiterhin zu schmal (kurze Joins, s. `zu`-Overlay).
