# Qualitätsmetrik & Glyph-Bench

> **Status (2026-08-12): lebend.** Fortlaufend gepflegte Messlatte und
> Baseline-Journal — jeder Bench-Lauf und jedes bewusste Re-Baseline
> schreibt hier einen datierten Abschnitt fort; aktuelle Headlines:
> Wörter 0,110392 · Paare 0,165678 (Re-Baseline `aug07`); das Journal
> reicht bis `aug11` (§11e). Die Verworfen-Listen (§4, §5, §6) bleiben
> geschlossen.

Wie die Qualität einer kanonischen Glyphe gemessen wird, wie der
hermetische Benchmark (`tools/glyphbench`) und der Experiment-Loop
(`/optimize-glyphs`) damit arbeiten, und was die Läufe bisher gelernt
haben — inklusive der verworfenen Sackgassen, damit niemand sie erneut
probiert. Ergänzt [`architektur.md`](../concepts/architektur.md) §5
(Schwellzug vs. Tinte) und §6 (Qualitätspipeline); die Implementierung
liegt in `core/quality.py`, das Werkzeug in `tools/glyphbench/`
(englisches README mit Fixture-Format und Output-Contract).

Stand: fortlaufend gepflegtes Journal — Grundfassung 2026-06-11 (nach den
PRs #63–#71), seither mit jedem Lauf/Befund fortgeschrieben; letzter
Eintrag 2026-08-02 (Lauf `aug02`, PR #268: Report-Spalte `meas`, Headlines
Wörter 0,116886 · Paare 0,164506).

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

### Der gespeicherte Score ist der Stand der Ableitung (gilt für beide Skript-Metriken)

Der Wert in `templates.trace_meta["quality"]` ist der Score **zum
Autorierungszeitpunkt** — die Zahl, die die Ableitung damals gestempelt hat,
keine Neubewertung mit der heutigen Metrik. Für Zeilen, die vor der Metrik
getract wurden, steht dort `null`. Eine Laufform-Zeile (Variante 100) erbt
das `trace_meta` der Chart-Zeile, ihr Score ist also eine **Kopie** — in der
Oberfläche wird deshalb nur der gestempelte Score der Variante 0 verwendet.
Neu abgeleitet wird ausschließlich über den per-Glyphen-Endpunkt
`GET …/templates/{glyph_key}/quality`; gespeicherter und nachgerechneter Wert
gehen in dem Moment auseinander, in dem sich die Metrik ändert — jede
Re-Baseline (§2) macht die gespeicherten Zahlen historisch.

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
liegt seit R1b Stufe 2 in **`core/word_metric.py`** (das API-Image liefert
`tools/` nicht aus, und der Admin-Score-Endpunkt
`GET /sources/{id}/word-samples/{sample_id}/score` serviert dieselbe Metrik
als Anzeige); `tools/wordbench/metric.py` bleibt als Re-Export-Shim der
historische Importpfad des Bench-Loops. Eine Implementierung, keine Drift —
die Freeze-Regel gilt durch den Shim hindurch für das Core-Modul.

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
zusätzlich `core/word_metric.py` (samt Shim `tools/wordbench/metric.py`),
`tools/wordbench/export_fixtures.py`
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

### Lauf `jul08` — erster Compose-Loop (Endstrich) + Struktur-Befund (2026-07-08)

Keep/Discard nur an `core/compose.py`, Ziel NUR die Wort-Headline
(User-Festlegung), Referenzen = `jul08`. Log:
`tools/wordbench/runs/loop-jul08/results.tsv`.

**Behalten — E1 Wort-End-Schwung (`bench_loss` 0.1284 → 0.1240):** Die
Ausgangsschrift beendet jedes Wort mit einem Endstrich — die steigende
Schlussflanke des letzten Buchstabens, GERADE verlängert Richtung
Mittellinie. Generiert am Wortende (`SWING_TOP_Y = 0.7`, Bench-Optimum;
Tafel-Mediane per Katalog: n≈0.53, m/e≈0.6, r≈0.82), nur bei niedrigem
vorwärts-steigendem Exit (< 0.7) — Bogen-/Deckstrich-Exits enden wie
gehabt. Erste Form (kubischer Haken, 55°) war schlechter (0.1356): der
Tafel-Endstrich ist die tangenten-gerade Fortsetzung, kein Schnörkel.
Golden-Fixture bewusst re-gepinnt (REGEN_GOLDEN, Endstrich ist jetzt Teil
des öffentlichen `/write/word`). Sichtbarster Gewinn bei kurzen Wörtern
(`Einen` 0.053 mit Breite 0.001, `zu` 0.111, `die` 0.099). **Paare:**
`pair_loss` 0.176 → 0.197 (nur Report, nie Ziel) — die isolierten
Abb.-20-Paare tragen eigene Auslaufstriche, der zusätzliche Endstrich
verschiebt deren Breiten-Bias.

**Verworfen — E2 uniformer Wortanfangs-Anstrich (+0.011):** Der
Höhen-Schwellwert ist der falsche Diskriminator. Tafel-Katalog (48 Crops,
formverifiziert): die Anstriche setzen bei ~0,5–0,7 x-Höhen an (NIE an der
Grundlinie), ~30–35° über ~0,5 xh — und genau das ZEICHNEN unsere
Entry-Stubs aus den Chart-Zellen bereits; a/z/f und alle Versalien öffnen
ohne Anstrich. Ein zusätzlicher Lead-in ist ein Doppel-Anstrich.

**Verworfen — E4 Stub-Trim + Diagonal-Platzierung (+0.11 … +0.32), mit dem
wichtigsten Struktur-Befund des Laufs:** Die Chart-Zellen zeichnen halb-hohe
Kopplungs-Stubs (Entry: Pen-down mitte → Bogenscheitel; Exit: Grundlinien-
Fuß → halbe Höhe). Im fließenden Schreiben ersetzt der Join beide Stubs
durch EINE flache Gerade — unser Konnektor überbrückt stattdessen die
Stub-Spitzen fast waagerecht („Shelf"). Der Umbau (Trim + Fuß→Scheitel-
Diagonale, Patch: `runs/loop-jul08/e4-stub-trim-full.patch`) legte offen:
**die Bögen der Glyphen selbst sind ~35 % schmaler als die fließende
Vorlage** (n intern 0,7 xh vs. 1,11 xh gemessen) — die Stubs kaschierten
das als Padding. Compose kann das nicht ehrlich kompensieren (Trim-only
kollabiert auf halbe Breite, Diagonal-Regel überdehnt die Joins); der Fix
liegt auf der **Glyph-Ebene** (Bogenbreite der autorisierten n/e/m/w-Formen
an die fließende Schrift anpassen) → eigenes Issue, eigener Lauf mit
Glyph-Bench-Gegenprobe.

**Zielliste danach:** `fechten` 0.257 (ch-Ligatur fehlt → komponiert
dekomponiert zu breit; Autoring), `Gewehr` 0.233, `schwer` 0.227, `an`
0.204 / `wenn` 0.197 (Bogenbreiten-Befund). Vorschlag-B-Residualtabelle:
`runs/loop-jul08/vorschlag-b-residuals.tsv` (Status-Notiz in
`planaenderungen.md` — Beobachtung, keine Übernahme).

**Nachtrag (gleicher Tag, Runde 2):**

- **Bogenbreiten-These RELATIVIERT** (Issue #167 umgescopet): eine
  einheitliche Steigungs-/Pitch-Messung (Strich-Kreuzungen auf 0,25/0,5/
  0,75 x-Höhe, identische Methode auf Proben-Skelett UND komponierten
  Centerlines) zeigt: Anstiege 32–45° (Probe) vs. 34–44° (komponiert),
  Abwärtsstriche beidseitig senkrecht, Bogen-Pitch vergleichbar. Die
  „~35 % schmaler"-Zahl aus dem E4-Lauf war verkettete Landmarken-
  Arithmetik, keine Direktmessung. Der E4-Kollaps geht aufs
  Platzierungsmodell (Clearance-Packung vs. Diagonal-Überdehnung), nicht
  auf die Glyphen. Offen bleibt ein BUCHSTABENSPEZIFISCHER Verdacht
  (e-intern ~0,25 xh vs. ~0,4–0,5 auf der Tafel) — per-Letter-Landmarken-
  tabelle in Arbeit, Glyph-Eingriffe erst danach.
- **Verworfen — E6 Level-Join-Begradigung** (`|Δy| ≤ 0,10…0,30` →
  +0,0016…+0,0082): Die These, der S-Schwung bei fast-levelen Joins
  (t→e, f→e) sei ein Artefakt der erzwungenen G1-Tangenten, hält der
  Messlatte nicht stand — die sanfte S-Kurve liegt näher an der Proben-
  Tinte als die Gerade. Der sichtbare „Wackler" ist offenbar authentisch
  (die Feder wippt beim Querbalken-Anschluss leicht durch).
- Die komponierte t-Form (Fußschleife, Stammhöhe) ist chart-treu
  (glyphlab-Gegenprobe der Zelle) — Abweichung zur fließenden Tafel ist
  Chart-vs-Fluent, kein Ableitungsfehler.

### Lauf `jul08` Runde 3 — Landmarken-Tabelle + Fluent-Weitung der Rundformen

Die per-Buchstaben-Landmarkenmessung (identischer Kreuzungs-Code auf
Template-Centerlines UND Proben-Skeletten, ≥5 Instanzen je Buchstabe aus
Wörtern + Paaren, gegen Zoom-Crops validiert) löst Issue #167 endgültig
auf: **Die Chart-Zellen quetschen die RUNDEN Körper**, nicht die Arkaden —
interner Pitch (xh): e 0,314 → Tafel 0,400 (+21 %), a-Schüssel 0,671 →
0,845 (+21 %), u 0,852 → 1,00 (+15 %), o 0,679 → 0,80 (+15 %); n +8 %
(grenzwertig, bleibt), m +4 % / d +6 % (ok). Auf Wortebene absorbiert die
Komposition ⅔ des Defizits (median spec/comp-Breite 1,051) — deshalb war
die Wort-Headline für die These fast blind.

**Behalten — Fluent-Weitung zur Renderzeit** (`core/pipeline.py`,
`FLUENT_BODY_PITCH`): Der Körper (erste↔letzte Vertikale von Stroke 0)
wird beim Rendern auf den gemessenen Tafel-Pitch gestreckt — stückweise
linear, Stubs bleiben, alles rechts rückt nach; entry/exit/advance werden
mitgeführt. NUR auf dem Gleichzug-Schreibpfad (`render_payload_for_
template` = `/write/*` + Wort-Bench): das gespeicherte Template bleibt die
Chart-Messung (§5-Resolver-Prinzip), Admin-Diagnose und Glyph-Bench
vergleichen weiter gegen die Zelle, und ein „Alle neu ableiten" überlebt
die Korrektur (zielbasiert: breiter autorisierte Körper ⇒ No-op).
**Bench-neutral** (λ-Sweep 0/0,25/0,5/0,75/1,0 → 0,1240/0,1244/0,1237/
0,1242/0,1253 — Spread 0,0017, die Wortmetrik wäscht Buchstabenform aus);
Entscheid fürs volle Mess-Ziel per Overlay-Sichtung (von 0,115, zu 0,061,
auch 0,101 — die geweiteten Rundformen liegen auf der Probe). Paare
(Report) 0,197 → 0,199. Neue Wort-Headline: **0,1253** (innerhalb des
Rauschens der 0,1240; die Wahrheit der Buchstabenformen war hier das
Kriterium, nicht die Proxy-Zahl).

**Nachtrag aug16 (#289):** Auf dem `/write`-Pfad war die Weitung von
Anfang an still deaktiviert — die zwei handgerollten
Produktions-Row-Builder (write-Router, wordlab-Live-Spiegel) ließen das
`glyph`-Feld weg, auf dem `_fluent_widen` keyt; nur die
Bench-Fixture-Rows trugen es (Divergenz gemessen beim
Fixture-Rebuild-Gate von PR #283: 0,145 xh auf `on`, 0,147 xh auf `u`).
Der Bench hat also durchgehend den hier beschlossenen Zustand gemessen,
die Auslieferung nicht. Seit #289 baut EIN gemeinsamer Builder
(`core.database.models.template_render_row`) die Rows beider Pfade, ein
Paritätstest (`tests/test_render_row.py`) pinnt den Fixture-Exporter an
dieselbe Form, und das `--verify`-Gate vergleicht volle Rows statt
`glyph` zu strippen. Bench-Zahlen per Konstruktion unverändert; nur die
ausgelieferte Geometrie bewegt sich — auf den Zustand zu, den die
eingefrorenen Lineale immer gemessen haben.

### Befund `jul11` — pairlab: unabhängige Paar-Sektion (2026-07-11)

Diagnostik-Ausbau, Composer und Messlatte unverändert: `tools/pairlab`
fittet jeden Buchstaben eines Proben-Worts UNABHÄNGIG (begrenzte
Translations-Suche) und seziert dann den Join — damit sind Konnektor-Form,
Platzierung und Glyphen-End-Anpassung erstmals getrennt messbar. Ergebnis
über 87 Vorkommen / 45 Paare: Platzierung ist der größte Einzelfehler
(39/87 brauchen ≥ 0,25 xh Korrektur), die Standard-Diagonale ist generisch
richtig (auch f→e/t→e — deren `jul08`-Penalty war Platzierung), und bei
Hoch-Exits (d-Schleife, Deckstrich-Bögen o/b/v/w, r-Arm) ersetzt die echte
Feder die Kopplungs-Stubs beider Seiten (0,2–0,4 xh je Seite) durch eine
Diagonale in den Scheitel des ersten Abstrichs. Befund + Optionen O1–O3:
[`docs/proposals/uebergaenge-befund.md`](../proposals/uebergaenge-befund.md).

### Lauf `jul11` — O1 Platzierungs-Kalibrierung + O2 Kopplungsanker (2026-07-11)

Keep/Discard nur an `core/compose.py` (plus ein Silhouetten-Helfer in
`core/template.py`), Ziel die Wort-Headline, Referenzen = `jul08`-Stand
(Fixtures identisch reproduziert; die unveränderte Baseline traf die
dokumentierte Headline exakt: 0.125337). Neu als Kalibriersignal neben der
Bench: die pairlab-Unabhängig-Fits ALLER Buchstaben der 48 scorbaren Wörter
(156 Joins; Soll-Korrektur pro Join = ddx(B) − ddx(A)) — die Bench wacht
über Regressionen, die Kalibrierung sagt, ob die Platzierung wirklich
stimmt. Log: `tools/wordbench/runs/loop-jul11/results.tsv` (lokal).

`bench_loss` **0.1253 → 0.1183** (−5,6 %; Deckung 0.121 → 0.113, Breite
0.162 → 0.135); `pair_loss` (Report, nie Ziel) 0.199 → 0.195.
Kalibrierung nachgemessen: Joins mit ≥ 0,25 xh Soll-Korrektur **31 → 21**
von 146, d-Klasse −0,33 → −0,07 med, w-Klasse +0,23 → +0,08 med.

Behalten (in Keep-Reihenfolge):

1. **Hoch-Exit-Tuck (O1):** der `gap`-Anker zieht `TUCK_RATE·(exit_y −
   TUCK_Y0)⁺` ab — ein hoher Exit ist eine Stub-Spitze, kein echter
   Abgang; die Tafel tuckt den Folgebuchstaben darunter (d-Klasse −0,33 xh
   bei exit 1,36). Der Ink-Clearance-Guard bleibt die Untergrenze.
2. **Rückwärts-Exit-Clearance (O1):** zeigt die Exit-Tangente nach links
   (w/v-Bogen), gilt `BACKWARD_INK_CLEARANCE` 0.30 statt 0.14 — der Join
   muss erst über den ganzen Bogen (w-Joins +0,23 xh med zu eng).
3. **Kopplungsanker B-seitig (O2):** nach hohem Exit (≥ 0,7: Deckstrich-
   Bogen, d-Schleife, r-Arm) zielt der Konnektor auf die STEIGENDE Flanke
   des ersten Abstrichs bei `ENTRY_COUPLE_Y` 0.78 statt auf den Stub-Fuß;
   das Stub-Stück darunter fliegt aus Centerline UND Silhouette
   (`core/template.py::erase_silhouette_piece`). Wortanfangs-Stubs bleiben
   (E2-Erkenntnis), Arkaden-Joins bleiben unangetastet (Befund §4).
4. **Level-Auslauf (O2-Rand):** ein hoher VORWÄRTS-Exit am Wortende
   (r-Arm ~0,86) läuft `SWING_HIGH_RUN` 0.25 xh eben aus statt abrupt zu
   enden — `der`/`der-2` trugen dafür die größten Breiten-Strafen
   (0,31/0,48). Ein stale Smoke-Test-Assert in `tests/test_wordlab.py`
   („Wort endet auf Glyph-Segment") wurde dafür korrigiert — die Annahme
   galt seit dem jul08-Endstrich nur noch zufällig; die eingefrorene
   Metrik (`tools/wordbench/metric.py`) blieb unangetastet.
5. **Tuck-Re-Sweep:** nach dem Kopplungsanker gewinnt `TUCK_RATE` 0.35
   (Konstanten interagieren — am Ende eines Laufs die frühen Keeps
   nachsweepen).

**Verworfen im Lauf:** pauschal `CONNECT_GAP` 0.16→0.08 (Übergang
verschlechtert — Bestätigung der jul02-Lektion in Gegenrichtung);
`INK_CLEARANCE` global 0.14→0.25 (kippt gap-Joins massenhaft in den
ink-Branch, +0,03); Descender-Exit mit breiter Clearance (headline-neutral);
Launch-Clamp auf die gemessenen +2…+13° (neutral bis minimal schlechter).
**Wichtigster Negativ-Befund — A-seitiger d-Stub-Trim:** der Abgang an der
Schleifenkreuzung (statt Stub-Spitze) verbessert die Deckung, aber die
Übergangs-Komponente bestraft konstruktionsbedingt die x-Spannen-Ausdehnung
des Konnektors in die d-Spalte (Reverse-Chamfer im Konnektor-Band);
medial-d-Wörter (laden, Feinde) besser, initial-d-Wörter (der, die)
schlechter, netto +0,001. Der d-Stub bleibt daher gezeichnet; seine
Platzierungs-Wirkung fängt der Tuck ab. Falls später gewünscht, braucht ein
ehrlicher A-Trim zuerst eine Metrik-Diskussion (Re-Baseline) — nicht im
Loop lösbar.

### Lauf `jul09/10` — Girlanden-Verbindungen, r-Absatz, Endstrich; drittes Set `abb22`

Der Join-Audit (Ranking aller generierten Übergänge über Wörter + Paare mit
Naht-Knick-Winkeln als „Zacken-Detektor") fand drei Systematiken, die der
Nutzer auch visuell gemeldet hatte (en-Zacken in „lesen", re-Wackler und
be-Zacken in „schreiben"):

1. **Höhenverlierende Exits** (r-Arm 0,86 · b-Bogen 0,98 · d-Schleife 1,36):
   der taute Einzel-Bézier schrieb V-Kerben/S-Wackler an der Naht (r→e
   72°/65° Knick, b→i 90°/77°). Die Platten schreiben eine **Grundlinien-
   Girlande** — Fall-Kubik, die tangential auf die rückwärts verlängerte
   Lead-in-Linie des Folgebuchstabens einschwenkt und sie gerade bis zum
   Entry reitet (`_garland_centerline`; Tiefe ∝ Senkrechtabstand des Exits
   zur Linie, `GARLAND_TURN_RATIO`). Exits NAHE der Linie (rb, on:
   d_perp ≤ `GARLAND_MERGE_EPS` 0,40) behalten die flache Kerbe des tauten
   Béziers — sie zu girlandieren kostete ~+0,01 pair_loss.
2. **r-Absatz**: innerhalb des Bogen-Bandes ist eine flache Vor-Klemm-
   Tangente (r ≈ +29° vs. o +39°/b +44°) der Deckstrich-Arm — die Platten
   setzen dort ab (Ecke) und fallen steil (−65°) in die Girlande; nur wenn
   eine echte Girlande folgt. Geklemmte BOGEN-Exits rollen stattdessen G1
   über den Scheitel (`CREST_ROLL_LEN` 0,09 — der „extra Zacken" bei b→e).
3. **Sägezahn-Durchschreiben**: zwischen zwei Mittelband-Diagonalen
   (e→n-Familie) entstand ein flaches „Regal"; die Platten führen EINE
   Diagonale durch. Platzierung zieht den Folgebuchstaben auf die
   Exit-Steigungslinie (`ALIGN_*`, Steigung ×0,8, Tinten-Floor 0,06,
   hohe Lead-ins h/t ausgenommen). Guard-Verschärfungen (min-rise 0,08,
   entry ≤0,58, clearance 0,10) und Ratio-Sweeps 0,7/0,9 waren alle
   schlechter — 0,8/0,62/0,06 ist das lokale Optimum.
4. **Endstrich**: Zwei-Tangenten-Quadratik (Exit-Tangente → 25° am Ende,
   Ziel `SWING_TOP_Y` 0,6, Kappung 0,9; Exits unter der Grundlinie — x —
   flicken nur 0,35 weit). Der alte gerade 0,7-Strich überschoss jede
   Probe (n→END mean 0,437, x→END 0,90).

**Headline: Wörter 0,1253 → 0,1247 · Paare 0,1992 → 0,1912** (bewusstes
Golden-Re-Baseline von `tests/fixtures/compose_golden.json.gz`). Die
Proxy-Zahlen unterschätzen den Effekt: die Naht-Knicke r→e/b→i sind von
72–97° auf ≲15° gefallen, sichtbar in den wordlab-Overlays (streiten,
fechten, haben, bi). Verworfen: Girlande mit fixer Bodentiefe (v1 —
rb/on-Regression), Absatz ohne Tiefen-Gate (rb-Spitze), END_DEG 12°
(0,9-lange flache Schwänze, Paare +0,033), lineare Kappungs-Stauchung
des Schwungs (dx/vx +0,1).

**Drittes Fixture-Set `abb22`** (Cross-Hand-Referenz, 2026-07-10):
Abbildung 22 des Leitfadens — „Schülerschrift aus der 39. Gemeindeschule
in Berlin … mit der Breitkantfeder" (S. 59; DNB-Blatt 61) — ist die
einzige weitere verbundene Ausgangsschrift-Probe der Quelle: 106 Wörter
in 19 Zeilen (Hoffmann von Fallersleben, „Hab' Dank, du lieber Wind!"),
signiert „Bruno Krüger" — **andere Hand, gleiche Norm**. Vermessen wie
Abb. 19 (propose_boxes + 19-Zeilen-QC + Handkorrekturen: Splits laden|ein
und|fern, Schmaus-Merge, ?- und !-Boxen verworfen, Interpunktions- und
Fremdtinten-Excludes, Zeile-15-Lineatur auf Median-xh korrigiert,
Diakritika-Excludes entfernt), Sidecar-Feld `set: "abb22"` → eigenes
Fixture-Root `suetterlin-1922-abb22` (`--set abb22`). Erste Zahl:
bench_loss 0,4628 (Breite 0,77 dominiert — die Schülerhand schreibt
sichtbar breiter als die Norm-Templates; Übergang 0,26). Die Zahl misst
GENERALISIERUNG über Schreiber hinweg und wird NIE mit den
Same-Hand-Headlines gemittelt.

**Korrektur (Nutzer-Review am Original, 2026-07-10):** Die erste
Girlanden-Fassung ließ auch r→e/d→a zur Grundlinie tauchen — die Originale
(ren/roten/ihren Abb. 22, das/do/der/regieren Abb. 19/20) zeigen: **Runde
Körper (e-Schleife, Schüsseln a o c d g q ä ö) koppeln nach hohen Exits
direkt OBEN an** — der Buchstabe hängt am Deckstrich-Übergang, der
angeautorte Anstrich wird vom Übergang absorbiert (Mückes e-vs-n-Regel).
Nur Arkaden-Eintritte (n m i u …) laufen durch die Girlande (bi/on tauchen
auch im Original). Implementiert als geschlossene Klassenmenge
`HIGH_COUPLE_BASES` (enumerate, don't generate) + Chord-Landung von oben.
Wörter 0,1247 → **0,1241**, Paare 0,1927; regieren r→e 0,49 → 0,12.
Merke: Overlay-Reviews immer gegen das ROHE Original-Tintenbild
gegenprüfen — im Overlay hatte ich den e-Ausgangs-Abstrich dem Übergang
zugeschrieben.

### Merge-Reconciliation `jul09/10` × `jul11` (2026-07-13)

Die beiden Läufe `jul09/10` (Girlanden-Grammatik) und `jul11`
(pairlab-Platzierung + Kopplungsanker) sind PARALLELE Zweige vom selben
`jul08`-Stand 0,1253 — ihre Headline-Deltas messen jeweils gegen diese
gemeinsame Basis, sie sind NICHT kumulativ. Beim Zusammenführen wurde die
Girlanden-Grammatik auf den bereits gelandeten `jul11`-Composer aufgesetzt:
`jul11` behält die B-seitige Kopplung (`entry_trim`/`couple_line`/
`ENTRY_COUPLE_Y`) und den Level-Auslauf hoher Vorwärts-Exits; darauf kommen
`jul09/10`s Girlande (nur für Arkaden-Eintritte, `high_couple` gated die
Rundkörper an die `jul11`-Kopplung), r-Absatz, Crest-Roll, Sägezahn-`ALIGN_*`
und die flach auslaufende Endstrich-Quadratik für niedrige Exits. Die
redundante Bogen-Klemme aus `jul11` entfällt (der Crest-Roll-Block deckt
dasselbe Band ab). Beide Composer-Unit-Suiten (`test_compose_coupling`,
`test_compose_joins`) prüfen disjunkte Zweige und bleiben grün; das
Golden-Fixture ist bewusst neu gepinnt. Die kombinierte Wort-Headline wurde
in der Merge-Umgebung NICHT nachgemessen (die Wortbench braucht die geteilte
Cloud-SQL-DB) — vor dem nächsten `/optimize`-Loop einmal
`export_fixtures` + `run --set all` fahren, um die reale kombinierte Zahl zu
setzen.

### Kombinierte Baseline + Loop `jul17` (2026-07-18, Issue #218)

**Kombinierte Baseline nach der Merge-Reconciliation:** gemessen auf den
EINGEFRORENEN `jul08`-Fixtures — bewusst ohne Re-Export: die
Sütterlin-Templates sind seit 2026-07-07 unverändert (R2 war geometrisch
byte-identisch, nur Keys), und die Session hatte keinen Cloud-SQL-Zugang
(Egress-IP nicht in den authorized networks). Der nachgeholte Re-Export auf
Basis-Keys bleibt eine spätere bewusste Re-Baseline-Entscheidung.
**Wörter 0,118532 · Paare 0,191805** (Komponenten 0,107/0,111/0,158 bzw.
0,161/0,131/0,369; 48/15 bzw. 31/2 gescort/übersprungen).

**Messwerkzeug-Erweiterungen (vor dem Loop, Headline-Neutralität
verifiziert):**

- **Slant-Report-Spalte** (R5 Stufe 1, `tools/wordbench/slant.py`):
  Scher-Suche −30°…+30° in 0,25°-Schritten, Maximierung der quadrierten
  Spaltenprofil-Summe (90° = senkrecht); pro Zeile `slant <Vorlage>/<Engine>`
  plus Blockmediane, JSON-Felder `slant_spec`/`slant_comp`. Headlines und
  alle Per-Wort-Losses byte-identisch (0,118532/0,191805). Reproduziert den
  §4-Befund des Redesign-Docs auf den frozen Referenzen: das 86,2°,
  der 87,2°, die 88,0° bei Engine ~90.
- **`--overrides <harvest.json>`** in `run.py`: komponiert jedes Wort mit den
  Paar-Overrides der Datei (Basis-Keys werden pro Wort auf die eingefrorenen
  Slot-Keys gemappt). Ein Override-Lauf ist eine EIGENE Messgröße und nie mit
  der Override-freien Headline vergleichbar; das JSON trägt das Feld
  `overrides`.

**Ernte (R3-Erstbefüllung, `tools/pairlab/harvest.py`):** 32 Abb.-20-Paare
geerntet — Offset aus den rigiden Einzel-Fits, Verbindungszug aus dem
Specimen-Zug, baseline-locked (der Composer hält beide Buchstaben auf der
Grundlinie, die relative vertikale Fit-Verschiebung wird linear über den
Pfad verteilt, `connector[-1] == offset`). Override-Messung: alle 32 →
pair_loss 0,1890; nur die vier Versal-Paare B→i/I→n/D→u/O→f → **0,1864**
(alle vier verbessern einzeln: In −0,085, Of −0,056, Bi −0,018, Du −0,008;
Wörter-Headline unverändert — kein Wort enthält sie). Berührungs-Paare ohne
Zwischenraum-Zug (df/dp/ds/bi) verschlechtern als Override — der
Override-Pfad rendert verbatim und verliert den O2-Entry-Trim — und bleiben
Entwürfe, konsistent mit der R3-Regel „Kleinbuchstaben erst nach R4".

**Loop `jul17`** (Composer editiert, Metrik/Fixtures/Slots eingefroren; Log
`tools/wordbench/runs/loop-jul17/results.tsv`, Residuen-Evidenz per pairlab:
kein globaler Advance-Bias mehr — Median −0,03 xh —, Restfehler klassenförmig
t −0,34 · c→h −0,25 · f→e −0,29 · a +0,16):

- **E1 Nested Fall — KEEP, Wörter 0,118532 → 0,117769** (Paare unverändert):
  steigende Mittelband-Exits, deren Nachbar UNTER dem Exit eintritt (t-Balken,
  f-Fahne — kein Sägezahn-ALIGN möglich), nesten auf der Platte unter der
  Exit-Tinte; die Ink-Schranke lockert auf `ALIGN_MIN_CLEARANCE`. Sweep:
  Schranke 0,06/0,0/−0,10 → 0,06 optimal; ein zusätzlicher Gap-Tuck band nie
  (E4-Check: alle Nest-Gewinne liegen bei rise ∈ (−0,15, 0,02)).
- **E2 Ligatur-Rest-Tuck — DISCARD** (+0,0014/+0,0023 Wörter bei 0,15/0,25):
  die enge Kopplung zerlegter ch/ck/tz/ſt/qu-Reste verschlechtert die
  Headline trotz der pairlab-Evidenz (−0,25 xh bei c→h).
- **E3/E3b O3 A-seitiger d-Trim — DISCARD, Befund geschärft** (0,1316/0,2126
  bzw. 0,1364/0,2189 mit Fall-Tangente): der Trim verschlechtert auch die
  DECKUNG — der d-Stub retraciert die Kreuzungsstrecke der Schleife, die auf
  der Platte eigene Tinte trägt; das ist ein substanzielles Negativ-Ergebnis,
  nicht nur das dokumentierte Spannen-Artefakt der Übergangs-Komponente. O3
  bleibt auch nach der Neubewertung auf dem gemergten Composer verworfen.
- **E5 (R5 Stufe 2) d-Schleifen-Lehnung — KEEP, Wörter 0,117999** (Paare
  unverändert): gebundene d (Lauf ≥ 3 Buchstaben — die isolierten
  Abb.-20-Drills messen aufrecht, §4-Median 90,75°) scheren oberhalb des
  Mittelbands um 4,5° nach rechts (Template bleibt Chart-Messung, ein
  solitäres d bleibt chart-treu). Bench-neutral (Winkel-Sweep 3/4,5/6°
  spreizt 0,0007 = Ruler-Rauschen) — entschieden per §4-Messung + Overlay
  (das/der: die komponierte Schleife liegt auf der lehnenden
  Vorlagen-Schleife; Präzedenz Fluent-Weitung). Slant-Spalte bestätigt:
  das/der/die 90,2 → ~89,0. **b/h/k geprüft und NICHT übernommen** (Delta
  sub-noise, §4-Tabelle zeigt für deren Wörter keine Lehnung).
  Golden-Fixture bewusst neu gepinnt (REGEN_GOLDEN).

**Endstand `jul17`: Wörter 0,117999 · Paare 0,191805**; Override-Lauf mit
den vier Versal-Entwürfen: pair_loss 0,1864.

### Änderung `jul20` — Geraden-Fit-Flankenkopplung („ne-Knick“, Headline offen)

Nutzer-Befund am Live-Bild: Bei Sägezahn-Paaren, deren Entry-Fuß auf/unter
dem Exit sitzt (n→e als Prototyp), lief der generierte Konnektor sichtbar
flacher als beide Tinten-Flanken — auf den Golden-Payloads n→e Chord **−7°**
zwischen 41°/39°-Flanken (Naht-Knicke −40°/+57°). Geometrische Ursache:
Kein Abstand kann den FUSS auf die Exit-Steigungslinie legen (näher = steiler
ABWÄRTS); die Tafel koppelt stattdessen auf der steigenden Flanke (§5b:
Arkaden-Ankünfte y 0,47–0,67, nicht der Stub-Fuß).

Umsetzung (`core/compose.py`, nur Nested-/Align-Klasse): Paar-Abstand und
Kopplungspunkt werden GEMEINSAM gelöst, zweistufig. **Stufe 1 — Fusion**
(`_fused_flank_placement`, Nutzer-Review-Runde 2 am selben Tag: die erste
Fassung mit ×0,8-abgeflachter Ziellinie las sich weiter als „andere
Schräge“): der Übergang setzt die STRICHRICHTUNG SELBST fort — das Paar
rückt zusammen, bis die Gerade durch den Exit mit der VOLLEN mittleren
Tinten-Tangente die Anstrichs-Flanke trifft; der Konnektor degeneriert zum
kurzen kollinearen Stück, die Züge verschmelzen, der Stub unter dem
Kopplungspunkt wird wie bei O2 aus Centerline UND Silhouette absorbiert.
Die Spalten-Tinten-Schranke kann eine solche Platzierung nicht beurteilen
(verschmelzende Strichenden überlappen absichtlich) — Legitimität prüft ein
HÖHENBEWUSSTER Clearance-Guard (`_fused_clearance_ok`, `FUSE_CLEAR_BINS`
y-Bins über dem Join-Band, Ausnahmeband ±`FUSE_BAND_PAD` um
[Exit-Höhe, Kopplungshöhe]). **Stufe 2 — Fallback** (`_flank_couple_steepest`):
wird die Fusion abgelehnt, platziert der Stub-relaxierte Spalten-Floor und
koppelt die steilste erreichbare Gerade am oberen Fensterrand (Kappe
`ALIGN_MAX_ENTRY_Y`) statt wie bisher unter beide Flanken durchzuhängen.
Liegt die Kreuzung bereits im Fenster (a→n, g→e), degeneriert der Konnektor
bei unveränderter Platzierung zur exakten Geraden. Golden-Effekt: n→e −6,6°
→ **+39,9° bei Flanken 41,2°/40,9°** — Nahtwinkel −1,3°/+1,0°, eine
durchgehende Diagonale; alle anderen Klassen byte-identisch. Schutz der
Verworfen-Einträge: `FLANK_COUPLE_MAX_DROP` 0,05 hält die
Nested-Fall-Klasse (t-Balken, f-Fahne — E1) heraus, deren sanfte S-Naht
laut E6 authentisch ist; E6 (Begradigung bei UNVERÄNDERTER Kopplung) bleibt
verworfen — hier ändern sich Kopplung UND Platzierung. Bewusst NICHT
angefasst: die floor-gebundenen Align-Paare (e→n 23°, n→n, a→s) — deren
Set-off ist das jul09/10-Bench-Optimum, und die jul17-Residuen (a-Klasse
+0,16 = eher weiten) warnen vor blindem Engerziehen ohne Messlatte.

**Offen:** Diese Session hatte keinen Cloud-SQL-Zugang (wie `jul13`) — die
Wort-/Paar-Headline ist NICHT nachgemessen. Vor dem nächsten
`/optimize`-Loop einmal `export_fixtures` + `run --set all` fahren; die
Guards (`FLANK_COUPLE_MAX_DROP`, Kappen-Wahl, Floor-Relaxierung) sind dann
die ersten Sweep-Kandidaten. Golden-Fixture bewusst neu gepinnt
(REGEN_GOLDEN). *(Nachtrag `jul29`: Headline auf den jul08-Fixtures
nachgemessen — Wörter 0,123703, Paare 0,191805; das ist die Baseline der
Skizzen-Runde unten.)*

### Runde `jul29/30` — Skizzen-Feedback: sechs Verbindungsklassen (PR #239)

Erste durchgängig NUTZER-GEFÜHRTE Runde: Der Autor markierte Defekte direkt
auf gerenderten Wörtern (annotierte Screenshots mit Soll-Linien), jede
Korrektur wurde als KLASSENREGEL umgesetzt (nie als Bigramm), gegen
wordbench + Golden verifiziert und sofort erneut vorgelegt. Leitsatz des
Autors, als prüfbare Invariante formuliert: *„Man muss das (bis auf
i-Punkte, paar Ausnahmen) in einem Fluss ohne Absetzen schreiben können —
dann muss bei Sütterlin die Linie immer perfekt gleich dick sein.“*
(→ Gleichzug-Audit, unten.)

Die sechs Änderungen (`core/compose.py`):

1. **Descender-Rückkehr** (ſ→c-Verdikt „das c muss von der Grundlinie aus
   losgehen"): Ein Descender-Schleifen-Exit kehrt DURCH die Grundlinie
   zurück und reitet die Anlauflinie des nächsten Buchstabens kollinear
   hoch (`DESCENDER_RETURN_GAP`/`_MAX_RUN`); geschlossene Anstrich-Klasse
   `DESCENDER_RIDE_BASES = {c, t}` — hängende Schüsseln koppeln direkt
   (erster Wurf ohne Klassen-Schranke: sg 0,20→0,38, behoben).
2. **Arm-Klassifikation exhaustiv** (Doppelwellen-Verdikt): Im Bogen-Band
   ist ein flacher Prä-Clamp-Tangens (<`ARM_TAN_MAX_DEG`) IMMER der Arm
   (r/p), nie ein schließender Bogen — kein Crest-Roll über dem Arm mehr;
   dazu Arm-exempte Clearance (Kerning gegen die Unter-Arm-Tinte,
   `ink_max_x_low`, Knubbel-Guard über das oberste Profil-Bin).
3. **Arm-Fusion** (Zielbild-Mockups re, dann rr): Der Arm-Bogen rollt in
   EINER Bewegung auf den Anlauf-SCHEITEL des nächsten Buchstabens
   (`_entry_apex_index` — Kopplung unterhalb des Scheitels ließ einen
   steigenden Rest parallel zum Bogen stehen, „als wäre der Stift kurz
   doppelt so breit"); Platzierung rückwärts aus dem Kopplungspunkt
   (`ARM_FUSE_GAP` 0,02), Launch höchstens waagerecht. Geschlossene
   B-Klasse `ARM_FUSE_BASES` = Rundkörper ∪ {r, i} — x/z/p messbar
   ausgeschlossen (rp 0,08→0,27 beim Klassen-Sweep).
4. **Gleich-Schräge-Kopplung** („wie eine perfekte Linie"): Sägezahn-Paare
   mit passenden Tangenten (±`SAMESLANT_TOL_DEG`) koppeln als EINE Gerade
   hoch auf der Flanke (`SAMESLANT_COUPLE_MAX_Y` 0,72; pairlab: reale
   Ankünfte 0,64–0,79), Platzierung unangetastet — das Engerziehen (F1)
   kostete +0,011 und widerspricht den pairlab-Abständen. Die
   floor-gebundenen Align-Paare aus `jul20` („bewusst NICHT angefasst")
   sind damit adressiert: nicht durch Engerziehen, sondern durch die
   hohe gerade Kopplung.
5. **Schleifen-Abgang ohne Absetzen** (d→e-Zielbild, drei Iterationen):
   Im GEBUNDENEN Kontext schreibt ein Schleifen-Buchstabe
   (`LOOP_EXIT_BASES = {d, s}` — das runde Schluss-s hat denselben
   Kringel) den Zier-Stub der Tafelzelle GAR NICHT — die Rückkehr kreuzt
   den Stamm und läuft ohne Absetzen weiter in den nächsten Buchstaben;
   Stub aus Centerline UND Silhouette geschnitten. Wortfinal bleibt die
   komplette Tafel-Form und erhält das neue Schleifen-Finial
   (`DLOOP_SWING_*`: flacher Launch, später langer Aufschwung — der
   r-Arm-Auslauf passte der d-Höhe nicht). **Ablösung von O3:** Der
   zweimal verworfene Stub-Trim scheiterte am TIP-verankerten Konnektor
   (Fall 0,4 u rechts der echten Stelle); mit Abfahrt an der Kreuzung
   stimmen Auge UND Messung überein — Wörter 0,1237→0,1220 in genau dem
   Schritt. O3 bleibt als Warnung vor Trim-bei-Tip-Anker gültig.
6. **`CONNECT_OVERLAP` 0,05:** Generierte Striche überlappen an offenen
   Enden minimal in die Nachbar-Tinte (unter der runden Kappe) — schließt
   die Haarrisse an den Item-Übergaben im gefüllten Rendering (die letzte
   „Neu-ansetzen"-Illusion). Ink-only, Stiftweg unverändert.

**Ergebnis:** Wörter 0,123703 → **0,122287**, Paare 0,191805 → **0,183317**
(do/ds tauschen bewusst etwas Chamfer gegen den fließenden Tiefeneinstieg —
Design-Entscheid des Autors). Bestätigung des §6-Dauerbefunds: Die Headline
ist gegen die meisten dieser sichtbaren Korrekturen nahezu blind
(Einzelschritte ±0,001), erst Klassen-Fehlgriffe schlagen aus (sg, rp) —
die Skizzen des Autors waren das Messinstrument, der Bench der
Regressionswächter.

**Gleichzug-Audit (Werkzeug-Idee, noch nicht im Ruler):** Zwei physikalische
Invarianten pro komponiertem Wort — (a) EIN FLUSS: aufeinanderfolgende
Pen-down-Items schließen Ende-an-Anfang (Lücke = Stift springt); (b) EINE
STRICHBREITE: zwei fast-parallele Pfadstücke im Abstand zwischen
Retrace-Epsilon und ~1,35×Feder lesen sich als doppelt breiter Strich
(exaktes Nachfahren und transversales Kreuzen erlaubt; Paare innerhalb
EINES Buchstabens sind Buchstabenform, nicht Compose). Prototyp im
Session-Scratchpad; als Report-Spalten neben Slant/Segment-Attribution
vorgesehen (headline-neutral, dann bewusster Fold-in). Offene Arbeitsliste
aus dem Audit: die ſ-Rückkehr läuft in „sch" ~0,3–0,6 u parallel zur
eigenen Unterschleife (Abstand ~0,12).

### Re-Baseline + Report-Spalten `jul30` — Gleichzug-Audit, Vollauthoring-Fixtures

**Gleichzug-Audit als Report-Spalten** (`tools/wordbench/gleichzug.py`,
konsumiert von `run.py` wie die Slant-Spalte — nie Teil des Loss): pro
Eintrag `flow gaps=… dbl=…`, pro Block `gleichzug_gaps`/`_doublings`.
Definitionen: (a) FLOW GAP — aufeinanderfolgende Pen-down-Items schließen
Ende-an-Anfang (Toleranz `CONNECT_OVERLAP`+0,02); (b) DOPPELUNG — zwei
fast-parallele Pfadstücke (<30° mod 180) mit SENKRECHTEM Versatz zwischen
0,035 und 1,35×Feder über ≥0,05 u Bogenlänge (euklidisch nah; der
senkrechte Versatz unterscheidet Seit-an-Seit von „auf derselben Linie
gleitend" = Retrace). Klassifikation über die compose-Provenance: Paare
innerhalb EINES Slots sind Buchstabenform (nicht gezählt), generierte
Samples auf eigener Buchstaben-Tinte werden dem Slot zugeschlagen
(Retrace). Resampling PRO Pen-down-Lauf (Lift-Split — sonst Phantom-
Brücken). `run.py` komponiert dafür mit `provenance=True` — Headline auf
den alten jul08-Fixtures byte-identisch verifiziert (0,122287).
Unit-Tests: `tests/test_wordbench_gleichzug.py` (7 Fälle inkl. Retrace-,
Kreuzungs- und Letterform-Ausnahme).

**Re-Export nach Vollauthoring** (der Autor hat alle Klein- UND
Großbuchstaben autorisiert; nur ß/sz fehlt): Wörter 58/63 bewertbar
(vorher 48 — neu: Wer, Soldaten, Seiten, Säbel, Silber, Sporn, Zaum,
Zügel, Sprünge, Zorn; offen nur die ß-Wörter muß×3, daß, schießen),
Paare 32/33 (neu: Wu; offen ßi), abb22 106/106 (vorher 95). **Neue
Headlines — NICHT mit den jul08-Fixture-Zahlen vergleichbar** (mehr und
schwerere Wörter, die Kapital-Joins sind die messbar schwächste Klasse):

- Wörter **0,131392** (worst: han 0,286; comp 0,124/0,121/0,168)
- Paare **0,182982** (worst: bx 0,324)
- abb22 **0,460933** (Kontext-Set, nie Headline)
- Gleichzug-Nulllinie: 0 Gaps überall; Doppelungen 110 (Wörter) / 68
  (Paare) — das ist die Arbeitsliste der kommenden Läufe, nicht Rauschen:
  dominiert von der ſ-Rückkehr, der d-Kurven-Anschmiegung und den
  Arm-Fusions-Nähten.

**Kalibrierung der Doppelungs-Erkennung (`jul30`, zweiter Schritt):** Die
110/68 enthielten zwei Klassen, die der Render-Abgleich als PEN-AUTHENTISCH
auswies — (a) voll verschmolzene Läufe (senkrechter Versatz < ½ Feder,
z. B. die ſ-Haken-Wende bei 0,06: liest sich als sanfte Schwellung wie das
Tinten-Pooling der Platte an jeder Schleifenschließung) und (b) kurze
Knoten-Loben an den vom Autor freigegebenen Fusionsnähten (Bogenlänge
0,17–0,22). Daher: Untergrenze des Bandes skaliert mit der Feder
(`DOUBLE_MIN_NIB_FACTOR` 0,5), `MIN_EVENT_ARC` 0,05 → 0,25,
`PARALLEL_DEG` 30 → 22 (flache Kreuzungen zählen nicht als parallel).
Headlines byte-identisch (Report-Spalte). **Kalibrierte Nulllinie:
Wörter 3 / Paare 17** — die Überlebenden sind die echte Shortlist, alle in
drei bekannten Klassen: Kapital-Joins (In 2, Of 3 — Befund §6 O3,
post-MVP-Kandidaten für gespeicherte Paar-Formen), d→Unterlängen
(df/dp/dx), ſ→Schüsseln (sa 2, sg 2, ssi 4 — der Grundlinien-Ride gilt
dort bewusst nicht); Wörter: Soldaten/scharfen/schwer je 1.

### Dehn-Runde Stufe 1 `jul30` — Lücken-Messung + höhenbewusstes Kerning

**Auslöser** (User, jul30): Das Wortbild wirke „in die Länge gezogen — so
würde niemand schreiben"; die Verbindungsschräge (z. B. en) solle stellbar
werden, damit alle Lücken vergleichbar sind. **Messung zuerst** (Auftakt
der Dehn-Runde): jeder Buchstabe aller 58 Wörter unabhängig aufs Specimen
gefittet (pairlab-Grid, vektorisiert); der Vorschub-Fehler eines Joins ist
`ddx_B − ddx_A`. Befund: **Gesamtbreite stimmt** (komponiert/Specimen
median 0,96; Join-Median ±0,00) — gestreckt wirkt der *ungleiche Rhythmus*
(sd 0,21): Hoch-Exits t −0,36 / f −0,29 / v −0,28 / b −0,28 / c −0,26 /
l −0,13 / o −0,13 ZU WEIT (die Platte schiebt den t-Balken sogar ÜBER den
Folgebuchstaben, Band-Lücke −0,15), während die Grundlinien-Diagonalen
(e→n +0,10, i→n +0,12, n→n +0,16) und die Fusionen (r→e, p) bereits enger
stehen als die Platte.

**Änderung — Kerning je Höhenzone** (`_profile_clearance_x`): die
Clearance-Platzierung vergleicht A-rechts/B-links **pro y-Bin** (die 9
`FUSE_CLEAR_BINS` des Fusion-Guards) statt an der skalaren Tintenkante;
Bins, in denen nur eine Seite Tinte hat, binden nicht — Tinte auf
verschiedenen Höhen darf Spalten überlappen wie auf der Tafel. Ersetzt
skalares Kerning, Align-/Nested-/Flanken-Floor; der Arm-Sonderweg
(Unter-Arm-Kante + Knauf-Guard, r/p) kollabiert als Spezialfall hinein,
die Arm-Fusion bleibt. Rückwärts-Exits (w/v) bleiben skalar
(`BACKWARD_INK_CLEARANCE`; die Platte ist bei w→e selbst +0,13 weiter).
Ergebnis: **Wörter 0,131392 → 0,130439, Paare 0,182982 → 0,174158**,
Gleichzug-Nulllinie unverändert 3/17, Klassen halbiert (c→h −0,26→−0,13,
b→e −0,28→−0,14, l 0,00), Streuung 0,210 → 0,197. Golden-Fixture
bewusst neu gepinnt.

**Offen, mit Plattenbeweis:** (a) t/f bewegen sich nicht — dort bindet der
Balken-Exit (`CONNECT_GAP` ab Balkenspitze), nicht die Clearance; die
Platte schreibt einen **Gabel-Join** (Retrace am eigenen Strich zurück,
dann fallen). Denselben Befund liefert die ſ-Vermessung (alle 7
`longs→X`-Vorkommen, pairlab-Sektion): Aufstieg skelett-identisch mit dem
ſ-Stamm bis zur Gabel bei y ≈ 0,25–0,4 (ſ→ſ 0,6; ſ→g Grundlinie), dann
SOFORT ~45° ausschwingend (½ Feder nach ≤0,05 u) — der komponierte
0,08-Parallelritt existiert auf der Platte nicht. Nächste Klassenregel:
Gabel-Join für Balken- (t/f) und ſ-Exits. (b) Die stellbare
Verbindungsschräge (en/in) ist Stufe 2 — Achtung: die Platte ist dort
WEITER als wir; das wird eine dokumentierte Geschmacksentscheidung gegen
den Bench-Gradienten, nicht Platten-Treue.

### Gabel-Runde `jul30` — ſ-Stammverschmelzung + t/f-Stammstart

Umsetzung des (a)-Befunds als zwei Klassen; die t/f-Messung (Zweitagent,
alle 8 gebundenen t/f-Vorkommen der Wörter — die Paar-Drills enthalten
keins) korrigierte die Retrace-These zu einem DRITTEN Bild: t's
Querbalken existiert auf der Platte nur LINKS vom Stamm (rechts 0,00–0,03
Tinte — der lange Chart-Balken ist Tabellenform), der Join verlässt den
STAMM bei y ≈ 0,34–0,53 und STEIGT mit 16–27° in den Apex des
Folgebuchstabens (0,88–1,0) bei +1,16–1,52 vom Stamm; f's tiefer Flag
kreuzt den Stamm und IST der Join. Kein Breiten-Beleg für ein Retrace.

- **ſ-Gabel** (`FORK_*`): Rückkehr schmiegt an den Stamm
  (`_stem_crossing_x` auf der Exit-Line), Retrace bis Gabelhöhe
  (0,42 × Koppelhöhe, geklemmt 0,18–0,55), dann Gerade in die HOHE
  Kopplung (`_fork_couple_index`: Apex ≤ 1,05, sonst Flanke bei 0,92).
  Platzierung: Schüsseln u. a. auf der 45°-Linie ab Gabel
  (`FORK_SWING_SLOPE` 0,75 nach Sweep, Profil-Floor); die Ride-Basen
  (c, t) behalten die kalibrierte run_down-Platzierung — das
  wordlab-Overlay zeigt sie platten-exakt (schwer longs→c 0,05) — und
  koppeln bei ENTRY_COUPLE_Y (im gemessenen Ankunftsband 0,75–0,9).
- **t/f-Stammstart** (`BAR_EXIT_BASES` {t, f}, geschlossen — Geometrie
  allein kann x' echte Kreuzungsform nicht vom Balken unterscheiden):
  Anker = LETZTE Kreuzung des Exit-Strokes mit eigener früherer Tinte
  (`_last_ink_crossing`; f's Flag kreuzt im selben Stroke). Gebunden wird
  t's Balken an der Kreuzung GEKAPPT (Centerline + Silhouette,
  Wort-Ende behält die Chart-Form — LOOP_EXIT-Präzedenz) und der Join
  ist EINE flache Gerade zur hohen Kopplung; Platzierung auf der
  Steiglinie ab Anker (`BAR_RISE_SLOPE` 0,55 nach Sweep 0,36–0,7).
- **Payload-Mutations-Fix:** die Cut-Klassen (LOOP_EXIT seit #239, jetzt
  Balken) mutierten die GETEILTEN Payload-Listen in place — bei
  gecachten Payloads (wordbench!) verlor jedes spätere Wort mit
  demselben Buchstaben den Strich (mit/mit-2/macht: End-t ohne Balken
  und Endstrich, +0,05–0,06 Phantom-Loss). compose kopiert die
  Stroke-Listen jetzt vor jeder Modifikation.

Ergebnis (Gabel-Runde): **Wörter 0,130439 → 0,130253, Paare 0,174158 → 0,170674**,
Gleichzug-Doppelungen **3 → 1 (Wörter) / 17 → 9 (Paare)** — die
ſ-Shortlist (sa 2, sg 2, ssi 4, schwer/scharfen) ist leer; übrig
Kapital-Joins (In/Of/Soldaten S→o) + d→Unterlängen. Per-Wort vs. main:
unter −0,014, fechten −0,009, streiten −0,006, scharfen −0,005;
Soldaten +0,015 (a→t 0,63 + Kapital-Join, geparkt). Golden bewusst
re-gepinnt. Verworfen in dieser Runde (gemessen): 45°-Platzierung auch
für Ride-Basen (Wort-Registrierung +0,5 xh, schwer +0,06),
Apex-Kopplung für c (jul29-Verdikt „c startet tief" gilt),
kollineare Anstrich-Linien-Platzierung (schwer 0,242 — zu eng).

### Laufform-Runde `jul31` — Dehnen als Renderkontext-Regel

**Messgrundlage** (User-Idee: „glyphen einzeln auf die beispielwörter
fitten"): alle 257 Buchstaben-Vorkommen der 58 Wörter per M4-Fit auf die
Platten gewarpt, affine Zerlegung Template→Laufform je Vorkommen (220
saubere Fits). Befund: die laufende Hand schreibt fast alle Buchstaben
3–11 % BREITER als die Chart-Zelle (e 1,083 · r 1,094 · h 1,102 ·
ſ 1,112 · l 1,091 · i 1,075 · u 1,072) bei leicht gestauchter Höhe;
Neigung aufrecht (±1,5°) bis auf d +5,1° (bestätigt ASCENDER_LEAN 4,5
unabhängig), w/b +4,6°, S −4,8°. Die Fluent-Weitung (`FLUENT_BODY_PITCH`,
jul08) erweist sich als dasselbe Modell für die Rundkörper — ihre Ziele
treffen die jul31-Mediane (e Body 0,31→0,40 ≈ sx 1,083).

**Änderung:** `LAUFFORM_SX` in `core/compose.py` — ganzheitliche
x-Skalierung je Buchstabe im GEBUNDENEN Kontext (Lauf ≥
ASCENDER_LEAN_MIN_RUN, Solo/Tafel bleibt chart-treu), Mediane mit n ≥ 5
und |sx−1| ≥ 0,03, OHNE die fluent-abgedeckten Rundkörper: i 1,08 ·
l 1,09 · h 1,10 · n 1,03 · r 1,09 · t 0,96 · d 0,97 · w 1,05 · ſ 1,11.
sy (0,96) bewusst NICHT angewandt (kollidiert mit der
Lineatur-Normierung); Neigen für w/b/S vertagt (S hängt an der offenen
Kapital-Join-Klasse).

Ergebnis: **Wörter 0,130253 → 0,121625** (größter Einzelsprung seit der
Girlanden-Runde; 28 Wörter besser — Einen −0,048, Gewehr −0,060,
einer −0,043 — 8 leicht schlechter, Ausreißer will +0,046: DIESES
Specimen ist eng geschrieben, Median-Modell), Paare 0,170674 → 0,169987,
Audit unverändert 1/9, Rhythmus-Streuung der Lücken 0,197 → 0,186,
Breiten-Ratio 0,966. Ein l-Sweep (1,05/1,07/1,09) war flach (Δ0,0005) —
der gemessene Median 1,09 bleibt: Konstanten kommen von der Platte, die
Bench ist Wächter, nicht Ziel. Golden bewusst re-gepinnt.

### Kapital-Runde `jul31` — Arbeits-Exit statt Zierbogen (User-Fund S→o)

**Auslöser:** Der User sah in der Runde-4-Galerie, dass Soldaten S→o
falsch koppelt — die Platte führt KEINE Linie oben weiter, sondern setzt
an der Grundlinie neu an. Messagent über ALLE 22 gebundenen
Kapital→Klein-Vorkommen (17 Wörter + Paare Bi/Du/In/Of/Wu): nirgends
eine hohe Decklinie; der Join ist die normale Kleinbuchstaben-Grammatik
ab dem **Arbeits-Exit** des Kapitals. Vier Exit-Klassen: Zierbogen
(S 1,76→0,30 · O 1,98→0,48), Tief-Ender (K/P/B → 0,0–0,2),
Unterschleife (G/Z — die Rückkehr IST der Join, das ſ-Gabel-Muster,
schon richtig), Mittel-Ender (E/F/W/I/D behalten ihren echten Exit).
Empfangsseite invariant: Rundkörper auf der Flanke 0,48–0,69 (Median
0,60, Anstrich intakt) — die 0,78-Top-Kopplung ist nach Kapitalen in
JEDEM Fall widerlegt. Null Parallelspuren auf der Platte: die
S→o-Audit-Doppelung war reines Composer-Artefakt.

**Änderung:** `CAP_RESTART_BASES` {S, O, B, K, P} — Abgang am letzten
tiefen Durchlauf (Rückwärtslauf über den finalen Aufschwung zum lokalen
Minimum ≤ `CAP_EXIT_MAX_Y` 0,55); der Zierbogen bleibt voll gezeichnet
und wird über die eigene Tinte RETRACED (Konnektor-Präfix, audit-
transparent — ſ-Präzedenz). `HIGH_COUPLE` nach Kapital-A-Seite
unterdrückt; Kapital-Joins girlanden nie (steigen monoton — der Dip lief
parallel über den Schüsselboden, die neuen Audit-Events des ersten
Wurfs) und bekommen die breitere Platten-Clearance
(`CAP_INK_CLEARANCE` 0,30; Sweep 0,22/0,30/0,38 — 0,22 ließ 8
Doppelungen, 0,38 kostete Bench).

Ergebnis: **Wörter 0,121625 → 0,120793, Paare 0,169987 → 0,165297**
(In/Of), **Gleichzug Wörter 0/0 — erstmals ganz leer**; Paare-Rest 6
(d→Unterlängen df/dp/dx + Wu). Seiten 0,101→0,068, Silber 0,120→0,098,
Säbel 0,165→0,115; Soldaten 0,232 (Wortende überläuft DIESES kompakte
Specimen — Median-Varianz wie „will", das Schriftbild stimmt jetzt).
Bekannt offen: In (I→n) — unser I-Template endet bei 0,41, die Platte
zieht den Schweif bis 0,83 weiter (Authoring-Frage, kein Composer-Fix).
Golden bewusst re-gepinnt.

### Median-Laufformen `jul31` — Doktrin-Split (Experiment → Mechanik)

User-Doktrin: „die geschriebenen Wörter sind das Vorbild, die Glyphen
zeigen den Duktus … Kreuzungen". Experiment: je Buchstabe der MEDIAN der
M4-gefitteten Anker über alle sauberen Wort-Vorkommen (218/249 Fits,
rmse ≤ 2,2 px; Median-vs-Chart nur 0,013–0,039 xh — der regularisierte
Fit dämpft, die Breiten-Signale sitzen in den Stub-Zonen), Topologie
bleibt per Konstruktion identisch. Bench mit Median-Ankern statt Chart:
**Wörter 0,1208 → 0,1136** (bester Stand), Paare leicht schlechter —
erwartbar, die Abb.-20-Drills sind chart-nah geschrieben; die
Lauf-≥3-Gattung hält sie ohnehin chart-treu. Entscheid (User):
Laufformen leben als **templates variant 1** (Architektur-§3-Einheit).
Mechanik gebaut (Endpoint + compose-Auswahl + `tools/laufform/harvest`),
Headline bewegt sich erst nach DB-Schreiben + Fixture-Re-Export
(dokumentierte Re-Baseline). Achtung Doppel-Korrektur: bei genutzter
Laufform ist `LAUFFORM_SX` je Slot deaktiviert (die Form trägt ihre
Breite selbst).

### H0-Anschluss `jul31` — Bench komponiert mit den Laufform-Varianten (Re-Baseline)

Abschluss der Laufform-Runde (handmodell-stufenplan.md H0): die 13
`LAUFFORM_VARIANT`-Zeilen (a d e g h i l m n r t u w) liegen in der DB,
Produktion (`/write/word`) komponiert seit der Mechanik-Runde mit ihnen —
die Bench misst jetzt denselben Stand. Der Export friert sie als
`templates_laufform.json` neben `templates.json` ein (Manifest-Feld
`laufform_keys`), der Runner reicht sie als `laufform_by_key` in
`compose_word` durch; `--no-laufform` läuft chart-only als
Diagnose-Zerlegung (eigene Zahl, nie die Headline). `tools/wordlab`
(Fixture- UND Live-Pfad) komponiert identisch, damit das Overlay zeigt,
was die Bench misst. **Freeze-Regel erweitert:**
`templates_laufform.json` ist Teil der eingefrorenen Fixtures — ein
Compose-Loop editiert nie die Laufform-Zeilen.

Re-Baseline in zwei Komponenten (Re-Export + Laufform), gemessen getrennt:

| Messung | Wörter | Paare |
|---|---|---|
| alte Fixtures (58/32 scorable) | 0,1208 | 0,1652 |
| Re-Export chart-only (`--no-laufform`) | 0,1222 | 0,1647 |
| **Re-Export + Laufformen (neue Baseline)** | **0,1169** | **0,1645** |

Der Export-Shift (+0,0014) kommt aus den 5 Wörtern + 1 Paar, die durch
die inzwischen autorisierten Kapitale **erstmals scorable** sind
(`words_scored` 58 → 63, `pairs_scored` 32 → 33, skipped jetzt 0) —
frisch autorisierte Einträge liegen über dem Schnitt. Der
Laufform-Effekt allein: **−0,0053** auf die Wörter; die Paare bewegen
sich praktisch nicht (Lauf-≥3-Schwelle — nur die Dreier-Drills wie
`ssi` können überhaupt Laufformen ziehen). Die ~0,1136 des
Median-Anker-Experiments treffen wir wegen des größeren Eintragssets
nicht exakt — das Experiment lief auf dem alten 58er-Set und tauschte
die Anker direkt statt über den Varianten-Renderpfad. Neue Headlines:
**Wörter 0,116886 · Paare 0,164506**.

### Report-Spalte `meas` `aug02` — gemessen vs. komponiert (Handmodell H2)

Dritte Spalte der Report-Linie **Slant (R5) → Gleichzug (jul30) → meas**:
dieselbe Doktrin, dieselbe Bauweise — eigener try/except, angehängt
NACH dem stabilen Block, nie Teil des Loss.

Die Vorkommens-Schicht weiß längst, was der Schreiber an jeder
Verbindung wirklich getan hat: `pair_instances` hält je gefundenem
Nachbarpaar EINE sezierte Verbindung derselben Specimens, die die Bench
scort (geerntet von `tools/pairlab/harvest.py`, darum decken sich die
Slot-Räume), im `glyph_pairs`-Rahmen — Konnektor-Mittellinie und
Platzierungs-Offset relativ zum Austritt des LINKEN Glyphs,
grundlinien-fest, Template-Einheiten. Der Composer erzeugt für denselben
Slot seine eigene Verbindung. Nebeneinandergelegt ergibt das zwei Zahlen
je Verbindung (`tools/wordbench/pairmeas.py`, xh-Einheiten):

- **`doff`** — Platzierung: der **horizontale** Versatz im
  **Körper-Rahmen**, `|Δx_komponiert − offset_x_gemessen|`. `Δx` wird
  genau dort abgelesen, wo die Ernte gemessen hat: zwischen dem Ende der
  LETZTEN Nicht-Diakritikum-Spur des linken Glyphs und dem Anfang der
  ERSTEN des rechten (`tools/pairlab/analyze.py`,
  `a_exit_line[-1]`/`b_first_line[0]`).
- **`dconn`** — Form: mittlerer punktweiser Abstand der beiden
  Mittellinien, jede bogenlängen-gleichmäßig auf
  `core.aggregate.PAIR_CONNECTOR_POINTS` (24) resampelt — dieselbe
  Parametrisierung wie die Paar-Aggregation — und anschließend auf ihren
  eigenen ersten Punkt gelegt. **Start-alignierte, damit
  translations-freie Form-und-Schwung-Distanz**: Platzierung ist allein
  Sache von `doff`.

**Warum Körper-Rahmen und warum x-only** (Befund der Review, mit
Messwerten): die Kopplungspunkte des Composers (`exit`/`entry`) sind
NICHT die Körper-Endpunkte — ein Kapital-Zierauslauf oder ein
getrimmter Anstrich verschiebt sie um bis zu ~2 xh. Der komponierte
Offset dort gegen eine im Körper-Rahmen gemessene Zahl gehalten meldet
einen reinen Rahmen-Artefakt: `Of` kam mit `d_exit` 2,037 auf `doff`
2,062, `Bi` 1,246/1,287, die sechs Kapital-S-Wörter alle um 1,8 — 24 %
aller Wort-Verbindungen waren zu ≥80 % Artefakt. Und die y-Komponente
des gemessenen Offsets trägt **per Konstruktion keine
Specimen-Information**: die Ernte rechnet den relativen vertikalen
Fit-Versatz heraus (`end_dy`, `tools/pairlab/harvest.py`), weil der
Composer beide Glyphen grundlinien-fest setzt — `offset_y` ist also das
komponierte Körper-Δy zum Erntezeitpunkt. Ein Vergleich dort würde den
Composer gegen sich selbst messen. Der horizontale Versatz ist zudem
genau die Größe, die uebergaenge-befund.md Befund 1 als dominant
ausgewiesen hat (Median-Korrekturbedarf 0,19 xh).

`compose_word(..., provenance=True)` nennt an jedem Verbindungs-Item
weiterhin die Kopplungspunkte `exit`/`entry` in Wortkoordinaten (der
Endstrich nur `exit`) — sie sind aus der Mittellinie nicht ablesbar
(`_overlap_extend` zieht deren ersten Punkt in die vorige Tinte zurück)
und bleiben für Overlay-Diagnostik nützlich; `doff` liest sie
ausdrücklich **nicht** mehr.

**Bewusst akzeptierte Vorbehalte.** (1) `doff`: ein HOHER Eintritt
schneidet Anstrich-Samples von der ersten Spur des rechten Glyphs
(`entry_trim`) — eine Composer-Entscheidung, die den komponierten
Körper-Start gegen eine eingefrorene Messung verschieben kann; klein und
als Verschiebung der ganzen Spalte sichtbar, nicht als Ausreißer.
(2) `dconn`: die komponierte Mittellinie ist die EMITTIERTE, trägt also
die Overlap-Verlängerung und nach einem Kapital den Zier-Retrace davor.
Die Start-Alignierung entfernt die daraus folgende Translation, nicht
diesen Vorlauf (die sechs Kapital-S-Wörter liegen dadurch bei ~0,82).
`dconn` ist damit kein kalibrierter Absolutabstand, sondern ein
monotones Signal (gleiche Verbindung, kleinere Zahl = näher am
Specimen). Für eine Report-Spalte genügt das.

**Ausschlüsse** (gezählt, nie stillschweigend): eine gemessene Zeile,
deren Dissektion die Ernte selbst verwirft
(`measurements.fit_ok` nicht gesetzt — dasselbe Tor, das der
Paar-Aggregat-Neuaufbau in `core.aggregate.aggregate_pair_instances`
anlegt: 11 von 199 Wort-Zeilen und 3 von 33 Paar-Zeilen der
1922er-Platten), und eine Verbindung, die der Composer aus einem
**freigegebenen Override** gerendert hat — ein Override IST eine
geerntete Mittellinie, gegen ihr eigenes Quell-Specimen misst sie
konstruktionsbedingt ~0 (dieselbe Doktrin wie „ein Override-Lauf ist
seine eigene Zahl").

Ausgabe: je gescorter Zeile `meas n=<zugeordnet>/<Verbindungen>
doff=… dconn=…` (Nullen inklusive, `-` wo nichts zugeordnet werden
konnte), je Block `meas_matched` + `meas_excluded: fit=… override=…` +
`meas_doff_median` + `meas_dconn_median` (Paare-Set mit Präfix `pair_`);
die Werte landen automatisch im JSON-Report (`pairmeas`). Zugeordnet wird
über `(kind, specimen_id, from_slot)` UND Übereinstimmung der beiden
Basis-Keys — passt das Paar nicht (verschobene Slots), zählt die
Verbindung als nicht zugeordnet, nie als Absturz. Ein unlesbares oder
kaputtes `pair_instances.json` verhält sich wie ein fehlendes: EINE
Warnzeile, Spalten weg, Lauf unverändert. Feuert der Per-Eintrag-Guard
(Schema-Bruch statt fehlendem Artefakt), steht ebenfalls genau eine
Warnzeile im Lauf — „keine Spalte" und „Spalte kaputt" dürfen von außen
nicht gleich aussehen.

**Freeze-Regel erweitert** (genau wie bei `templates_laufform.json`):
`pair_instances.json` ist ein NEUES eingefrorenes Fixture-Artefakt je
Set, geschrieben vom Export (`--only pair-instances` füllt es additiv in
bestehende Fixture-Wurzeln, ohne Crops/Masken/Slots/Templates — und damit
die Headlines — neu einzufrieren). Ein Compose-Loop editiert es nie; ein
Re-Export ist eine bewusste Re-Baseline DIESER Spalten.

**Headline-Nachweis** (Pflicht bei jeder Report-Spalte): Lauf vorher und
nachher, `--style suetterlin --set all` — `bench_loss` 0,116886 und
`pair_loss` 0,164506 bis zur letzten Stelle identisch, ebenso jeder
Einzelwert (`loss`, Komponenten, Registrierung, Slant, Gleichzug) über
alle 96 Einträge. Nulllinie der Spalte (Körper-Rahmen, x-only,
start-aligniert, mit den beiden Ausschlüssen): **Wörter 188/214
zugeordnet (11 `fit_ok`-Ausschlüsse, 0 Overrides), doff-Median 0,135 ·
dconn-Median 0,115; Paare 30/34 (3 `fit_ok`), doff-Median 0,192 ·
dconn-Median 0,217** — die isolierten Drills sitzen erwartungsgemäß
weiter weg als die Verbindungen im Wortfluss.

Zum Vergleich die verworfene erste Fassung (Kopplungs-Anker,
euklidisch): Wörter doff-Median 0,178, Paare 0,283. Der Rückgang ist
kein Fortschritt am Composer, sondern der entfernte Rahmen-Artefakt —
`Of` fällt von `doff` 2,062 auf 0,070, `wenn` von 0,238 auf 0,227. Die
schlechtesten Verbindungen sind seither die echten Platzierungsfehler
(`Za` 0,78 in *Zaum*, `re` 0,71 in *regieren*, `an` 0,65) statt der
Kapitalanschlüsse.

### Re-Baseline `aug04` — Nib-Präzision + erster Stufe-B-Kettenschrieb

Zwei Effekte, die zufällig zusammenfallen und deshalb wie bei der
Re-Baseline `jul31` **getrennt gemessen** werden: der eine korrigiert die
Fixtures, der andere ändert die DB.

**1. Nib-Präzision — die dokumentierte Zahl war richtig, der Export war
es nicht.** Der Gleichzug-Nib ist ein DB-Aggregat über ALLE
Template-Varianten der Quelle und kann aus gelesenen Chart-Zeilen nicht
zurückgerechnet werden; er muss transportiert werden. Vor der
Verfügbarkeit von `GET /sources/{id}/render-context` (PR #288) baute
`fetch_fixtures` ihn aus der 4-stelligen `/write/glyphs`-Rücklesung
(`nib_precision: "4dp-readback"`, 0,0731). Fixtures aus dieser Quelle
messen auf demselben DB-Stand **0,116688**, mit dem exakten Nib
(0,07309125) **0,116886** — also exakt die oben dokumentierte
`jul31`-Headline. Die scheinbare Baseline-Drift von 0,000198 war
demnach ein reines Export-Artefakt; die Headline stand nie falsch im
Dokument. Nachgemessen, nicht vermutet: dieselbe Bench mit auf 0,0731
gesetztem Fixture-Nib reproduziert 0,116688 auf alle sechs Stellen. Der
Mechanismus steht in `fetch_fixtures` (`DEFAULT_PLACEMENT_TOL`): die
Tintenfreiheits-Entscheidung liest Silhouetten-Ringe auf 2 Stellen
gerundet, ein Nib-Unterschied in der 5. Stelle kippt sie an
Messerschneiden chaotisch (beobachtetes Maximum 0,0148 xh Platzierung).
**Regel:** eine Fixture-Wurzel mit `nib_precision: "4dp-readback"` ist
kein gültiger Headline-Boden mehr — vor jeder Re-Baseline prüfen, dass
das Manifest `"exact"` sagt.

**2. Erster Stufe-B-Kettenschrieb in die DB („Satz A").**
„Satz A" ist das Etikett aus der Entscheidungsrunde für **den freigegebenen
Teil-Schlüsselsatz** — die 15 Schlüssel unten, gegen den vollen Entwurf von 18
abgegrenzt (`t`, `o`, `c`, `b` zurückgehalten). Der Begriff steht hier nur für
diesen einen Schnitt, nicht für eine Stufe.
Die Wort-Ernte des Ketten-Fits (`tools/pairlab/chain.py`, Stufe B Runde 1,
uebergaenge-befund.md §5c) hat 232 Vorkommen und 77 Wortspuren
geschrieben, daraus 35 Aggregate; auf **genau 15 Schlüssel** wurde
`apply-laufform` angewandt: `a d e g h i l m n r u w` (bestehende
Laufformen, frische Mediane) **+ `S` `sz` `z`** (Neuanlagen — erste
Laufformen überhaupt für diese drei). Gemessen gegen die frische
Nulllinie desselben Fixture-Standes:

| Lauf | `bench_loss` | Δ | `pair_loss` |
|---|---:|---:|---:|
| Nulllinie (exakter Nib, vor dem Schrieb) | 0,116886 | — | 0,164506 |
| **Satz A (15 Schlüssel) — neue Headline** | **0,115623** | **−0,001263** | **0,165519** |

Die Wörter verbessern sich um 0,001263 (Schranke der Freigabe war
„≤ Nulllinie + 0,0002"), die Paare geben 0,001013 ab — dasselbe Muster
wie `jul31`: die Abb.-20-Drills sind chart-nah geschrieben, eine
Laufform zieht sie vom Vorbild weg. Der Effekt ist etwas größer als die
Vorabmessung auf denselben Medianen (0,116112, −0,000774), weil der
Schrieb den **gepoolten Nib mitbewegt**: drei zusätzliche
Variante-100-Zeilen im Pool verschieben ihn von 0,07309125 auf
0,07302168… Das ist keine Störgröße, sondern die reale Folge des
Schriebs und Teil der neuen Headline.

**Warum vier Schlüssel bewusst NICHT geschrieben wurden** (je ein Satz,
alle vier stehen als `excluded` in der Apply-Antwort):

- **`t`** — die Stichprobe bricht von 8 auf 3 Vorkommen ein, unter jedes
  vernünftige `min_n`, und `t` ist der einzige Schlüssel, dessen
  `laufform_dev` über seinem eigenen MAD liegt (0,0143 vs. 0,0126). Seine
  Laufform bleibt stehen und ist damit messbar veraltet — bewusst und
  richtig, bis der `t`-Deckstrich-Befund (Runde 2) abgearbeitet ist.
- **`o`** — allein aufgelegt +0,00177 auf `bench_loss`, der klare
  Ausreißer des Entwurfs, bei nur n=5.
- **`c`** — allein +0,00022; zugleich der spektakulärste Ausbeutegewinn
  (1 → 7 Vorkommen), was ihn zum Ansehen-vor-Schreiben-Fall macht.
- **`b`** — allein ±0; kein Grund zu schreiben, kein Grund zu eilen.

**Verifikations-Gotcha für die nächste Re-Baseline:** `--verify` von
`fetch_fixtures` vergleicht Schicht 2 gegen `GET …/write/word`, und die
Route trägt `s-maxage=86400`. Unmittelbar nach einem
render-ändernden Schrieb antwortet die Cloudflare-Kante mit dem
VORHERIGEN Stand (`cf-cache-status: HIT`), das Gate meldet dann
Formabweichungen, die es gar nicht gibt. Schicht 1 (Zeilen gegen
`/write/glyphs`) lief hier frisch durch und war bit-exakt; die
Kompositionen wurden mit einem Cache-Busting-Parameter nachgeprüft:
12/12 bit-exakt, worst shape 0, worst placement 0.

### Re-Baseline `aug05` — zweiter Kettenschrieb, mit dem Überlappungsterm

Der erste Schrieb aus dem Objektiv mit Exklusivität (Überlappungsterm,
PR #300; Befundkette in `uebergaenge-befund.md` §5c). Protokoll wie bei
`aug04`, alle Tore vorab:

**Reproduktion.** Frische Fixtures (`fetch_fixtures --set all --verify`,
bit-exakt, exakter Nib) und frische Ernte auf `main` reproduzieren das
dokumentierte A/B exakt: 245 akzeptierte Slots, Tor-Verteilung 43/20/36
(`connector_degenerate` / `geo_rmse` / `not_converged_local`), 34 Flags,
die vier geheilten Verbindungen (`streiten|0`, `ssi|0`, `ssi|1`,
`regieren|3`) bleiben geheilt. Die Basislinien-Bench reproduziert den
`aug04`-Stand auf alle sechs Stellen (0,115623 / 0,165519).

**Guard.** Overlay der 18 Entwurfs-Schlüssel (alle n ≥ 4): Wörter
0,115623 → 0,114694, Paare 0,165519 → 0,164922 — **beide Sets verbessern
sich**, anders als bei `aug04`, wo die Paare den dokumentierten Trade
zahlten.

**Geschrieben** (Freigabe des Eigentümers, in-session): 245 Vorkommen
(`instances`, `replace`, 232 alte ersetzt), 96 Wortspuren
(`word_instances`, `replace`), Aggregat-Neuaufbau 35 Schlüssel,
Paar-Aggregate 123 (14 `fit_bad` übersprungen), `apply-laufform` auf
**alle 18** Entwurfs-Schlüssel — 14 aktualisiert, **4 neu angelegt**
(`c`, `longs`, `o`, `p` — ihre jeweils erste Laufform; damit sind auch
die `aug04` bewusst zurückgehaltenen Schlüssel geschrieben: `t` mit
n = 4 statt 3, `o` mit n = 5, `c` mit n = 7 statt 1, alle mit positivem
Overlay), 0 übersprungen, 17 unter `min_n` ausgeschlossen.

**Headline nach dem Schrieb** (frische Fixtures = neuer Live-Stand):
**Wörter 0,114563** (−0,001060), **Paare 0,164880** (−0,000639).
Report-Spalte, ehrlich mitgenannt: `meas_dconn_median` der Wörter
0,116 → 0,127 (reine Report-Größe, nie Teil des Loss).

**Verifikation.** Live-Zählungen 245/96, Varianten-100-Payloads für die
vier Neuanlagen vorhanden; das `aug04` dokumentierte CDN-Gotcha trat
erneut auf und wurde erneut per Cache-Bust widerlegt: das Gate mit
gebusteten `/write/word`-Kompositionen läuft **12/12 bit-exakt** (worst
shape 0, worst placement 0). Die Kante serviert bis zum Ablauf von
`s-maxage` den Vortagsstand — bekannt, harmlos, läuft aus.

### Re-Baseline `aug07` — Vertikalisierungs-Paar geschärft (Korb #5, das S)

Die Ableitung (`suetterlin._verticalize_downstrokes`) und die Metrik
(`geometry.detect_vertical_runs`, §5-Verticality) klassifizieren als Paar
„fast-vertikal + relativ gerade = Abstrich" und zogen mit der alten
Toleranz **0,10** (max. Bogen als Anteil der Sehne) auch die sanft
gebogenen Bauchflanken der großen Kapitälchen platt — sichtbar als die
Fillet-Ecken im S-Bauch, die Korb #5 bemängelte (die Chartzelle ist ein
glattes Oval). Kalibrierung über alle 61 authored Buchstaben der
Sütterlin-1922: echte Gleichzug-Stämme bogen ≤ 3,0 % (b 1,8, f 2,6,
longs 0,7), Ovalflanken ≥ 3,6 % (S 5,8/6,7, O 5,6, A 5,1, M 5,8).
**Neue geteilte Konstante `core.geometry.VERTICAL_STRAIGHT_TOL = 0.035`**,
von Ableitung UND Metrik importiert (vorher drei stille Kopien) — eine
bewusste Metrik-Änderung außerhalb jedes Experiment-Loops, beide Seiten
zusammen bewegt.

Glyph-Bench (Fixtures per API-Nachbau, volles Bbox-Dict inkl. `patches`):
`bench_loss` **0,183765 → 0,175550**; tintenverankerte Komponenten alle
besser (coverage 0,1722 → 0,1642, smoothness 0,1230 → 0,1158), S
0,182 → 0,156 mit glattem Bauch mittig in der Tinte. Ehrlicher
Verlierer: **Y +0,115** — seine entglättete Kurve triggert jetzt den
Collinearity-Term an der eigenen Kreuzung (Ys Tinten-Deckung verbessert
sich dabei 0,217 → 0,171; der Term ist auf gebogenen Durchgängen
möglicherweise übereifrig — offener Folgepunkt, nicht in dieser Runde).
Wordbench byte-identisch (0,110605/0,162783 — Komposition unberührt).
Gespeicherte Zeilen ändern sich erst durch Re-Derive (`POST
…/templates/{key}/resample`); der Schrieb ist ein eigener, abgestimmter
Schritt.

**Schrieb `aug07`** (Freigabe des Eigentümers, in-session, nach Deploy):

- **23 Resamples** (`S` sofort; danach `Y d M A O H V y Oe N Ae X W G x
  Q z R s P D Ue`) — jede Zeile vorher LOKAL abgeleitet und als Overlay
  über der Chartzelle begutachtet, Server-Scores 23/23 bit-exakt zur
  lokalen Ableitung. Bewusst NICHT geschrieben: `oe` (der zweite
  Umlautstrich deckt objektiv schlechter, coverage 0,170 → 0,231) und
  `U` (Δmax 0,001, kein Effekt). `Y` trotz Score-Einbruch geschrieben —
  die Form liegt sichtbar mittiger in der Tinte, der Einbruch ist der
  bekannte Collinearity-Folgepunkt.
- **`apply-laufform`** auf die 20 bestehenden Variante-100-Schlüssel
  (explizite `glyph_keys`, keine Neuanlagen), 0 übersprungen.
- **96 Wortspuren** neu geerntet (Chain-Pfad, words+pairs) und als
  Upsert OHNE `replace` geschrieben (0 gelöscht) — mit der neuen
  Absetz-Regel: der Säbel-Trace endet am S-Bogenende und setzt an der
  Grundlinie frisch an (4 Striche statt 1+2).

**Headline nach dem Schrieb** (frische Fixtures): Wörter **0,110392**
(−0,000213), Paare **0,165678** (+0,002895). Die Paar-Regression sitzt
fast vollständig in `dz` +0,083 / `dk` +0,040: das neu abgeleitete d
trägt jetzt die sanft gebogene Rückenlinie seiner CHARTZELLE (Glyph-Bench
coverage besser), während der Drill-Schreiber gerader schrieb —
Chart-Wahrheit gegen Drill-Ähnlichkeit, bewusst zugunsten der Chartzelle
entschieden (die Laufform der fließenden Wörter kommt ohnehin aus den
Medianen; die Wörter verbesserten sich: Zügel −0,016, Sprünge −0,013,
Soldaten −0,010).

**Verifikations-Befund (gelöst, Issue #311):** Das `--verify`-Gate von
`fetch_fixtures` lief direkt nach dieser Runde NICHT bit-exakt: 5 von 96
Kompositionen wichen ≤ 0,065 xh ab (u-Breite via Fluent-Weitung). Zwei
Ursachen, beide behoben:

1. **Nachbau statt Lesen.** Die Fixture-Laufformen wurden LOKAL aus den
   Aggregat-JSONs über `build_laufform_canonical` rekonstruiert — ein
   Nachbau, der an der HEUTIGEN Chartzeile hängt, während die
   gespeicherte Variante-100-Zeile die Chartzeile ZUM APPLY-ZEITPUNKT
   trägt; dazu lag mindestens ein Run auf der Messerkante der neuen
   Toleranz (u-Laufform bow 0,034756 bei tol 0,035), wo ein
   Schwellenvergleich Sub-1e-4-Rauschen zum diskreten Flip verstärkt.
   Fix: Der Admin-Einzeltemplate-Read nimmt jetzt `?variant=`, und
   `fetch_fixtures` liest die GESPEICHERTEN Variante-100-Zeilen
   wortwörtlich (Manifest `laufform_precision: "stored"`) — dieselbe
   Philosophie wie der `render-context`-Nib-Read: transportieren, nie
   nachrechnen. Ein älteres Deployment ignoriert den Parameter, liefert
   erkennbar die Variante-0-Zeile (`variant`-Feld der Antwort) und fällt
   sauber auf den Nachbau zurück (`"reconstructed"`). Merkregel an der
   Konstante (`core/geometry.py`): `VERTICAL_STRAIGHT_TOL` muss zu jedem
   gemessenen Populationswert echten Abstand halten, und grenznahe
   Klassifikationen werden gespeichert und transportiert, nie über
   Umgebungen hinweg re-klassifiziert.
2. **Ungebustetes Gate.** Das `aug04` dokumentierte CDN-Gotcha steckte
   auch im Gate selbst: seine `/write`-Reads liefen über die
   Cloudflare-Kante und konnten den Stand VOR der Schreibrunde
   „verifizieren". Das Gate bustet jetzt jeden eigenen Read
   (`_bust_token`) — Ground Truth ist der Origin, nie die Kante.

Kontrollmessung nach dem Fix (gebustetes Gate, Rekonstruktions-Pfad, da
das `?variant=`-Deploy noch ausstand): alle drei Roots **0 bad rows,
12/12 Kompositionen bit-exakt** (worst shape 0, worst placement 0) —
der aug07-Befund war zum Messzeitpunkt real, ist im heutigen DB-Stand
aber konvergiert; mit dem Stored-Read ist die Schicht künftig per
Konstruktion byte-treu statt per Glück.

### Re-Baseline `aug14` — Rect-Korrekturen in den Referenzen + das Wortbahn-Artefakt

Deklarierter Voll-Re-Export der drei Fixture-Roots (der erste seit
`jul31`), aus zwei Gründen zugleich:

1. **Die Referenz-Crops trugen die #334/#336-Rect-Korrekturen noch
   nicht** — `haben`/`ein`/`einen` (#334) und `zwei`/`regieren`/abb22-`in`
   (#336: abgetrennte i-Striche/-Punkte lagen KOMPLETT außerhalb ihrer
   Rects) waren in den eingefrorenen Masken beschnitten, d. h. die Bench
   bestrafte Kompositions-Tinte, für die die Referenz gar keine Tinte
   trug. Zudem lagen die lokalen Roots zwei Schreibrunden zurück
   (Templates vor dem `aug07`-Schrieb, 13 statt 19 Laufform-Schlüssel) —
   ihr Stand (Wörter 0,115646 / Paare 0,162325) ist deshalb nur als
   Transparenz notiert, nicht als Vergleichsanker.
2. **Das neue Set-Artefakt `word_instances.json`** (PR „tracebench
   Stufe A", docs/proposals/tintenfolger.md): die gespeicherten
   Wortbahnen des Sets — die 10 `authored`-Nachfahrungen als künftige
   tracebench-Referenz, die `traced`-Ernte-Fits als Kontext — mit dem
   **Frame-Gate** (`FRAME_BASELINE_TOL_PX`/`FRAME_XH_TOL_PX` in
   `export_fixtures.py`): eine Registrierung, die nicht mehr zur
   eingefrorenen Rect/Lineatur passt, wird `frame_stale` gestempelt,
   nie gedroppt. Live-Beweis am Bautag: der `--only`-Refill gegen die
   ALTEN `jul31`-Roots stempelte exakt die vier #334/#336-Zeilen
   (`ein` 61 vs. 48±4 · `einen` 59 vs. 48±4 · `regieren` 64 vs. 42±4 ·
   `zwei` **authored** 64 vs. 44±4); gegen die frischen Roots: 0 stale.
   Beim Refill prüft das Gate gegen die EINGEFRORENEN `word.json` des
   Roots (über deren Crop zeichnet der Konsument), beim Voll-Export
   gegen das Sidecar — am Exporttag identisch.

**Headline gegen den dokumentierten `aug07`-Stand** (0,110392 / 0,165678):
Wörter **0,110703** (+0,000311), Paare **0,165688** (+0,000010) — die
Komposition ist unberührt, die Bewegung sitzt in den Referenzen der
Rect-Wörter. Einzeln (gegen die veralteten Roots, also Rect- UND
Template-Effekt gemischt): `haben` 0,128 → 0,084, `ein` 0,069 → 0,033,
`einen` 0,064 → 0,054, `zwei` 0,080 → 0,073 — die Referenzen tragen
jetzt die Tinte, die die Komposition immer schon schrieb. Ehrlicher
Verlierer: **`regieren` 0,125 → 0,184** — sein i-Strich ist erstmals
Teil der Referenz, und die Komposition deckt ihn schlecht; das ist
keine Regression, sondern eine ehrlicher gewordene Referenz, die eine
echte Schwäche sichtbar macht. Abb.-22-Schiene (eigene Auswertung, nie
Teil der Headline): 0,445142 → 0,448502, gleicher Mechanismus beim
dortigen `in`.

**Diese frischen Roots sind zugleich der Startzustand des tracebench**
(dessen §14 die eigene Vorregistrierung trägt, sobald das Lineal
gebaut ist): die Betriebsregel bleibt, dass ein Voll-Re-Export ab jetzt
IMMER eine deklarierte Doppel-Re-Baseline (wordbench + tracebench) mit
datiertem Eintrag ist — der erste Akt einer Runde ist `--only
instances` gegen die bestehenden Roots.

---

## 7. Verworfen: Krümmungs-Regularisierer auf dem M4-Fit (`aug07`)

**Ergebnis: verworfen.** Global besteuern, um ein lokales Vergehen zu
verhindern, kostet auf der Bodenwahrheit mehr als es einbringt. Nicht
noch einmal in dieser Form versuchen — die tragfähige Alternative steht
unten.

### Der Befund, der den Versuch ausgelöst hat

Das Sütterlin-`S` wurde mit einem sichtbaren Zacken oben rechts
geschrieben. Ursachenkette, alles gemessen:

1. Die gerenderte Laufform (Variante 100) stammte aus einem Median über
   **zwei** Vorkommen. Bei n = 2 ist `np.median` das Mittel der beiden —
   keinerlei Ausreißerabweisung. (Das ist die
   **Vorkommensschranke**, `core.aggregate.LAUFFORM_MIN_OCCURRENCES`,
   seither von `apply-laufform` erzwungen.)
2. Eines der beiden Vorkommen („Sprünge") trägt einen kaputten M4-Fit:
   **ein einzelner Anker steht im leeren Papier** — 12 px von der
   nächsten Tinte, 9,3× der Median-Schrittweite von seinem Nachbarn
   entfernt — während 119 der 120 Anker sauber auf der Linie liegen. Die
   beiden `S` sind fast deckungsgleich *geschrieben*; der Unterschied ist
   der Fit, nicht die Hand.
3. Der Fit passierte seine QC (`geo_rmse_px` 1,261), weil diese ein
   Mittel über 240 Samples ist und eine lokale Nadel nicht sehen kann.

Warum der Fit das zulässt: **nichts in der Zielfunktion sieht einen
EINZELNEN Ausreißer.** `e_geo` ist ein Mittel über `DEFAULT_N_SAMPLES`
(1,5 Samples je Anker bei K=120), die Tikhonov-Energie ein Mittel über K
Anker, und `MAX_ANCHOR_DELTA` (0,75) ist viel zu locker. Wo das Template
länger läuft als die Tinte der Probe, sitzt ein Schwanz-Anker also gratis
im Nichts.

### Der Versuch

Zweite-Differenzen-Term (Biegeenergie, bogenlängen-normiert) auf dem
**Verformungsfeld** `anchors − template_anchors`, gebaut aus demselben
Operator, den die Verfeinerung längst auf das Breitenprofil anwendet.
Bestraft also die Krümmung, die der Fit *hinzufügt*, nie die des
Buchstabens — die Schale des S gehört dem Duktus-Prior. Gradient exakt
(5,6e-10 gegen finite Differenzen), Selektivität ~7e4 (eine Nadel gegen
eine glatte Ganzbuchstaben-Streckung gleicher Amplitude).

A/B über alle 245 gespeicherten Vorkommen, identischer Aufbau in beiden
Armen (rekonstruierte Ernte-Registrierung, daher *nicht* die absoluten
Zahlen der Ernte — nur der Vergleich zählt).

### Was die Formmaße sagten — und warum sie in die Irre führen

| Gewicht | Spike-Median | Fälle > 8× | Streuung MAD | Knick der Median-Kette |
|---|---|---|---|---|
| aus  | 3,29 | 39 | 0,0123 | 11,89° |
| 1e-5 | 1,81 | 17 | 0,0119 |  7,86° |
| 1e-4 | 1,40 |  7 | 0,0116 |  6,99° |
| 1e-3 | 1,25 |  0 | 0,0111 |  6,65° |

In 245 von 245 Vorkommen besser, in keinem schlechter. Der Median über
die Vorkommen wurde um 41 % weniger facettiert. Genau daraus entstand die
Fehleinschätzung, der Term sei ein reiner Gewinn.

`geo_rmse` stieg dabei (1,017 → 1,192 px), was zunächst als „weigert
sich, Pixelrauschen hinterherzulaufen" gedeutet wurde. **Diese Deutung
war für `geo_rmse` vertretbar, wurde aber unzulässig auf `coverage_rmse`
und die Konvergenzquote ausgedehnt.** Coverage misst Skelett → Template,
also ob die *gemessene Tinte* noch erreicht wird — das ist die
Treue-Richtung, kein Rauschen.

### Was die Bodenwahrheit sagt

Abstand der gefitteten **Mittellinie zur Tinte** (x-Höhen), gemessen auf
dem Skelett der Platte selbst — Maximum bepreist den Fehler, Mittelwert
bepreist den Schaden:

| Gewicht | ink_max Median | ink_max MAX | ink_mean Median | näher an der Tinte (mittel) |
|---|---|---|---|---|
| aus  | 0,0912 | 0,6129 | 0,0258 | — |
| 1e-5 | 0,0912 | 0,6864 | 0,0279 |  26 / 245 |
| 1e-4 | 0,0943 | 0,6549 | 0,0295 |   8 / 245 |
| 1e-3 | 0,1000 | 0,4534 | 0,0313 |   **3 / 245** |

**Der mittlere Abstand zur Tinte verschlechtert sich in 241 von 245
Vorkommen.** Nur der äußerste Ausläufer bessert sich (Maximum über alle
Vorkommen 0,61 → 0,45). Der Term repariert also tatsächlich die
Einzelnadel — aber er zieht dafür die gesamte Kette von der Tinte weg,
und dieser Preis übersteigt den Gewinn.

### Die Lehre (die eigentliche)

Spike-Maß und Vorkommens-Übereinstimmung sind **Form-Regelmäßigkeitsmaße**.
Jeder Term, der alles Richtung Prior zieht, verbessert beide — bis hin zum
Grenzfall „jeder Fit ist die Tafelform plus Verschiebung", wo sie perfekt
aussehen und nichts mehr gemessen wurde. Sie taugen daher **nie allein**
als Schiedsrichter; es braucht immer ein Maß, das die *gemessene Tinte*
bepreist, in beide Richtungen. Der Degenerationstest über die
Verformungsamplitude (bis 1e-3 stabil, bei 1e-2 Einbruch) war nötig, aber
nicht hinreichend — er schließt nur den Totalkollaps aus, nicht die
schleichende Entfernung von der Tinte.

### Was stattdessen zu versuchen ist

Das Vergehen ist **lokal** („Anker im leeren Papier"), die Biegeenergie
ist eine **globale** Steuer. Ein zielgenauer, **einseitiger** Term wäre
der nächste Versuch: eine Scharnier-Strafe auf den Abstand eines Ankers
zur Tinte, die erst jenseits eines Vielfachen der lokalen Strichbreite
greift. Anker, die auf der Tinte sitzen, zahlen dann exakt null — die
gemessene Verschlechterung des mittleren Abstands kann per Konstruktion
nicht auftreten. Offen bleibt die Kalibrierung des Einsatzpunkts und, wie
hier, die Pflicht, gegen `ink_mean` **und** `ink_max` zu messen.

Unabhängig davon bleibt die Vorkommensschranke die wirksame Absicherung:
sie verhindert nicht den kaputten Fit, aber dass ein einzelner ihn in den
Schreibpfad trägt.

---

## 8. Ernte-Gate gegen den „Anker im leeren Papier" (`aug07`)

**Ergebnis: übernommen** — als Gate, nicht als Fit-Term. §7 hatte den
globalen Biegeterm verworfen; hier steht, was stattdessen wirkt, und
warum der zweite, *zielgenaue* Fit-Term ebenfalls nicht angenommen wurde.

### Die Einsicht

Der Fit muss den Ausreißer nicht reparieren. **Eine Kette mit einer
Unstetigkeit hat die Hand nie gemessen** — sie zu verwerfen ist die
korrekte Aussage, kein Workaround. Die Ernte hat dafür längst ein
Vokabular (`not_converged_local` · `geo_rmse` · `at_bound` ·
`anchor_count` · `connector_degenerate`); es fehlte nur der Grund, der
diesen Fehler sieht.

### Die Kennzahl

`anchor_spike_ratio`: der größte Schritt zwischen benachbarten Ankern,
gemessen am Median-Schritt **seines eigenen Strichs**, maximiert über die
Striche. Absetzer zählen nie — eine Strichgrenze ist die Hand, die
woanders neu ansetzt, keine Unstetigkeit der Linie; würde man sie
mitzählen, flöge jeder mehrstrichige Buchstabe (i, u, ß, t, ä) dafür
raus, dass er genau seinen Duktus schreibt.

**Je Strich, nicht gepoolt.** Striche unterscheiden sich um ~1,5× im
Maßstab (Körper gegen Umlautpunkt). Ein gepoolter Median wird vom langen
Körperstrich dominiert und unterschätzt einen Zacken im kurzen: `ue` in
„Zügel" kommt gepoolt auf 7,21 (behalten), gegen den eigenen Strich auf
10,61. Die Verzerrung erzeugte nur falsche NEGATIVE, die Umstellung
verschärft das Gate also, sie weitet es nicht.

### Zwei Messrahmen, die nicht verwechselt werden dürfen

§8 nennt Zahlen aus **zwei** Quellen, und sie sind nicht vergleichbar:

* **gespeicherte Vorkommen** — die 245 Zeilen, die in der DB stehen. Daraus
  stammen die Kalibrierungs-Perzentile und die Ablehnungszahl (23).
* **Nachrechnung** — der A/B-Aufbau aus §7 mit *rekonstruierter*
  Ernte-Registrierung. Daraus stammen die Tintenabstände, die
  Scharnier-Tabelle und die Spike-Zahlen der Arme („aus" 3,29, 41
  Ablehnungen). Ein neutraler Ursprung statt der komponierten Platzierung
  belastet den Fit stärker, deshalb liegen dort mehr Ausreißer.

Wer die 23 und die 41 nebeneinander liest, liest zwei Populationen.
Perzentile sind hier durchweg **nearest-rank** (p90 7,28); `np.percentile`
mit Vorgabe-Interpolation liefert 6,89 — dieselben Daten, andere
Konvention.

### Kalibrierung

Über die 245 gespeicherten Vorkommen — die **alle** aus dem Ketten-Pfad
stammen (`fit_path == "chain"`, 245 von 245), Kalibrierungs- und
Anwendungspopulation sind also dieselbe: Median 2,68 · p75 3,86 ·
p90 7,28 · p99 23,29 · max 32,9 (nearest-rank).

Bei **8,0** werden 23 Vorkommen (9,4 %) verworfen und **kein einziger**
Buchstabe fällt unter `LAUFFORM_MIN_OCCURRENCES` = 3 (auch nicht unter
die `--min-n`-Vorgabe 4 der Ernte selbst): 12 von 35 lagen schon vorher
darunter, und es bleiben genau dieselben 12.

**Was die Tabelle verschweigt und hier stehen muss:** `S`, `s` und `ue`
gehen 2 → 1. Sie lagen schon unter der Schranke, das Rendering ändert sich
also nicht — aber der Buchstabe, um den diese ganze Runde ging, hat
danach **ein einziges** akzeptiertes Vorkommen. Das ist das stärkste
Argument dafür, die 23 zu *reparieren* statt sie dauerhaft wegzuwerfen
(siehe „Was offen bleibt").

Warum 8,0 und nicht 6,0: bei 6,0 fiele „g" von 3 auf 2. Das allein wäre
eine Qualitätsschwelle, kalibriert an einer Deckungs-Nebenwirkung — und
damit verdächtig. Es trägt nur zusammen mit dem Grund, aus dem die
Schranke bei 3 liegt: **ab drei Vorkommen überstimmt der Anker-Median ein
schlechtes Vorkommen.** „g" bei n = 3 ist also genau der Fall, für den die
Schranke gebaut wurde; ein viertes Gate obendrauf nähme ihm die Laufform,
ohne dass die vorhandene Absicherung versagt hätte.

Wirkung auf die akzeptierte Menge (Rahmen: Nachrechnung), gemessen als
Abstand der gefitteten Mittellinie zur echten Tinte: schlechtester Wert
**0,613 → 0,258** x-Höhen, p90 **0,194 → 0,149**. Das Gate fängt damit die
*Unstetigkeiten* — es ist ausdrücklich **kein** Detektor für „von der Tinte
weg": eine glatte, über viele Anker verteilte Abweichung passiert es
ungehindert, und der verbleibende Rest von 0,258 x-Höhen zeigt, dass es
solche gibt.

### Verworfen: das zielgenaue Scharnier im Fit

§7 hatte als Alternative eine **einseitige Scharnier-Strafe** auf den
Tintenabstand vorgeschlagen: `mean(max(0, d − τ)²)`, null für alles
innerhalb von τ, also beliebig hart machbar, ohne ehrliche Fits zu
besteuern. Gebaut, Gradient exakt, Null-Kosten-Eigenschaft bit-genau
verifiziert — und über alle 245 Vorkommen bei vier (Gewicht, τ)-Paaren
gemessen. Ergebnis:

| Arm | ink_max Median | ink_max MAX | ink_mean Median | spike Median | konv. |
|---|---|---|---|---|---|
| aus | 0,0912 | 0,6129 | 0,0258 | 3,29 | 224 |
| w5 τ0,15 | 0,0912 | 0,5842 | 0,0258 | 3,36 | 222 |
| w50 τ0,15 | 0,0912 | 0,3162 | 0,0258 | 3,41 | 208 |
| w50 τ0,25 | 0,0912 | 0,3801 | 0,0253 | 3,30 | 218 |

Anders als der Biegeterm lässt es `ink_mean` **unangetastet** (96 von 245
Fits kommen bit-identisch zurück) — die Null-Kosten-Eigenschaft
funktioniert. Aber:

1. **Es verfehlt sein Ziel.** Der `spike` bessert sich nicht, er wird
   eher schlechter (3,29 → 3,41). Das Scharnier begrenzt den *Abstand*,
   nicht die *Unstetigkeit*: es zieht den Ausreißer auf nahe Tinte, und
   ein Sprung auf nahe Tinte ist immer noch ein Sprung.
2. **Es kostet Deckung.** In *jeder* getesteten Konfiguration verliert
   „G" sein drittes Vorkommen (3 → 2) und damit die Laufform-Fähigkeit;
   bei w50 zusätzlich vier Vorkommen von „e".
3. **Es rettet nichts.** Es reduziert die Zahl der Gate-Ablehnungen
   nicht, es erhöht sie (41 → 43/46).
4. Zusätzlich fand die Gegenprüfung einen echten Defekt: außerhalb des
   Crops klemmt `_bilinear_with_grad` den Wert und nullt die Ableitung,
   das Scharnier berechnet dort bis zu 9 % der Strafe und **null**
   Rückstellkraft — genau dort, wo der Anker am tiefsten im leeren Papier
   steht. Jeder andere Distanzterm kompensiert das explizit.

Zusammen mit dem Gate bringt es nur noch `ink_max` MAX 0,258 → 0,172 bei
fünf akzeptierten Vorkommen weniger und einem Buchstaben unter der
Schranke. **Nicht übernommen.**

### Was offen bleibt: die Zacken sitzen nicht zufällig

Der Befund, der diese Runde eigentlich weiterträgt — gefunden erst beim
Gegenlesen, nachdem das Gate schon stand. **22 der 23 verworfenen
Vorkommen (96 %) haben ihren größten Schritt an einem Eckanker oder an
einem Strichrand:**

| Buchstabe | Ablehnungen | wo | `corner_anchors` |
|---|---|---|---|
| `e` | 7 | 43 (×5), 20, 75 | 19, 42, 74, 100 |
| `n` | 5 | 16 (×2), 77, 101, 1 | 16, 41, 77, 100 |
| `i` | 3 | 101, 119, 1 | Strichgrenzen (Punkt ab 100) |
| `u` | 2 | 119 (×2) | Strichende |
| `r`, `w` | je 1 | 18, 26 | 17 bzw. 26 |
| `S` | 1 | 113 | — (keine Eckanker) |

Fünf von sieben `e`-Ablehnungen liegen auf **demselben** Anker. Das ist
kein Rauschen, sondern eine **systematisch unterbestimmte Ankerklasse**:
die Abtastung teilt die Spline genau an Eckankern und Strichgrenzen
(`SamplePlan`), dort hat ein Anker die wenigste Sample-Stützung und damit
die schwächste Führung durch `e_geo` — bei 180 Samples auf 120 Anker fällt
das an einer Teilungsstelle sofort ins Gewicht.

Daraus folgt zweierlei. Erstens: die 23 sind **keine 23 unabhängig
kaputten Messungen, sondern ein Instrumentendefekt** — und damit
größtenteils rückholbar, statt dauerhaft verloren. Zweitens: das ist der
einzige Reparaturansatz, den §7 und §8 **nicht** ausschließen, weil beide
verworfenen Terme auf den falschen Mechanismus zielten. Der nächste
Schritt ist also nicht ein weiterer Regularisierer, sondern die
Sample-Stützung dieser Ankerklasse — mit anschließender Neu-Ernte, die die
23 (samt des zweiten S-Vorkommens) zurückholen würde. Das Gate bleibt
danach als Rückfalllinie.

### Die Lehre

Zwei aus dieser Runde, beide teuer erkauft:

1. **Das Vergehen benennen, nicht approximieren.** Der Defekt ist eine
   *Unstetigkeit*. Der Biegeterm bepreiste globale Krümmung, das
   Scharnier den Abstand — beide sind Stellvertreter, und beide
   verfehlten. Die Kennzahl, die den Defekt direkt misst
   (`anchor_spike_ratio`), löst ihn als Gate auf Anhieb.
2. **Ein Gate gehört an den Pfad, der die Daten produziert.** Die erste
   Fassung hing in `_harvest_case_slots`, während alle 245 gespeicherten
   Vorkommen aus `_harvest_case_chain` stammen — sie hätte in Produktion
   exakt null verworfen, bei grüner Testsuite, weil jeder neue Test den
   Slot-Pfad pinnte. Gefunden von der adversarischen Gegenprüfung, die
   die Nadel in den Ketten-Pfad injiziert und `['ok','ok','ok']`
   zurückbekam. Der Regressionstest
   `test_the_chain_path_rejects_an_anchor_in_blank_paper` hält das offen.

---

## 9. Menschliche Bewertung: was die Kennzahlen sehen — und was nicht (`aug08`)

Die Frage hinter §7 und §8 war nie beantwortet: **bedeutet eine kleinere
Zahl automatisch besser?** §8 hatte den Verdacht erhärtet, dass die
Zielfunktion einen sichtbaren Defekt nicht sieht — jeder ihrer Terme ist ein
Mittelwert über 120 Anker, ein einzelner Ausreißer bewegt sie nicht. Ob das
auch für die *anderen* Fehlerarten gilt, war Meinung.

Deshalb ein blinder Bewertungsdurchgang: 162 Bildschirme (150 Vorkommen +
12 blinde Wiederholungen), sechs Fehlerarten mit Mehrfachauswahl, ein
freiwilliger Ortsmarker je Bild. Der Auswerteplan wurde **vor** den Labels
geschrieben; Verfahren, Taxonomie und Fallstricke stehen in
[`menschliche-bewertung.md`](menschliche-bewertung.md), das Werkzeug ist
`tools/humanbench`. Die Bildschirme zeigten nur Crop und Centerline —
**keine Kennzahl**, damit das Urteil sie nicht spiegelt.

Was der Durchgang liefert: eine Abdeckungsmatrix (welche Fehlerart sieht
welche Kennzahl) und eine Validierung des in §8 ausgelieferten Gates. Was er
nicht liefert und nie sollte: Schwellwerte, einen Skalar-Score, einen
Trainingsdatensatz.

### Verlässlichkeit zuerst — und ihre Asymmetrie

10 von 12 blinden Wiederholungen ergaben exakt dieselbe Kategorienmenge, je
Kategorie 11–12/12. Das erlaubt überhaupt erst, von „blind" zu sprechen.

Die Einschränkung ist wichtiger als die Zahl: unter den 12 Paaren enthielten
`A` und `B` nur je **ein** Ja, `W` drei, `K` **null**. Deren hohe
Übereinstimmung kommt fast ganz aus Einigkeit über die Neins. Nur `E`
(6 Ja / 5 Nein / 1 uneinig) ist balanciert und damit belastbar geschätzt.

Die Folge ist **richtungsabhängig**, und das entscheidet, welche Aussagen
unten tragen: Labelrauschen, das von der Kennzahl unabhängig ist, drückt eine
AUC gegen 0,5 — es kann eine 0,84 nicht *erzeugen*, nur verkleinern. **Hohe
Zellen überleben dünne Verlässlichkeit, niedrige nicht.** Also: „Kennzahl X
sieht `W`" trägt; „Kennzahl X sieht `A`/`B` *nicht*" ist bei diesen
Besetzungen nicht interpretierbar, und die Gate-Trefferquote hängt an 15
`A`-Labels, deren Stabilität mit einem einzigen positiven Wiederholungspaar
abgesichert ist.

Konstruktionsfehler des Instruments, für die nächste Runde vorgemerkt: die
Wiederholungen wurden aus häufigen Glyphen gezogen, nicht nach
Verdachtskategorie geschichtet. Bei 10 % `A`-Prävalenz waren ~1,2 `A`-Paare
zu *erwarten* — der Durchgang konnte die `A`/`B`-Verlässlichkeit gar nicht
messen.

### Besetzung (150 Vorkommen)

| Kategorie | n | Anteil |
|---|---|---|
| `G` gut | 71 | 47,3 % |
| `E` Knick am Rand | 35 | 23,3 % |
| `W` Gewackel | 32 | 21,3 % |
| `B` Bereich daneben | 22 | 14,7 % |
| `A` Ausreißer | 15 | 10,0 % |
| `K` komplett daneben | 5 | 3,3 % (zu wenig, nur beschreibend) |

Knapp die Hälfte trägt keinen benennbaren Fehler. Kein Drift über die Sitzung;
die Mediandauer je Urteil fällt 9 s → 7 s → 5 s, der Kategorienmix bleibt
stabil.

**Wie diese 47 % zu lesen sind** (Kalibrierung des Autors): `G` heißt „der
Buchstabe ist sauber zu erkennen", **nicht** „schreibperfekt" — die Latte der
aktuellen Stufe, auf die erst einmal alles kommen soll. Die Quote ist damit
eine Aussage über Lesbarkeit, nicht über Schreibqualität, und „47 % gut" darf
nie als „47 % fertig" zitiert werden. Wie weit die guten Fits vom
Erreichbaren entfernt sind, sagt dieser Durchgang nicht und kann eine absolute
Skala auch nicht sagen; dafür ist der paarige Vergleich da
([`menschliche-bewertung.md`](menschliche-bewertung.md) §8).

### Das Gate aus §8, gegen Menschenurteile geprüft

`anchor_spike_ratio ≥ 8,0` lehnt 11 der 145 bewerteten Vorkommen ab
(`K` ausgeschlossen).

* gegen die `A`-Labels: Genauigkeit 8/11 = 0,73 · Trefferquote 8/15 = 0,53
* gegen „irgendein Fehler": Genauigkeit **11/11 = 1,00**

Die drei vermeintlichen Fehlalarme tragen `B` bzw. `BE`. **Das Gate hat kein
einziges als gut gelabeltes Vorkommen verworfen** — bei aufgebrauchtem
Ablehnungsbudget (12 von 35 Buchstaben liegen schon unter
`LAUFFORM_MIN_OCCURRENCES`) ist das die Eigenschaft, auf die es ankommt.

Es übersieht die Hälfte der Ausreißer, aber deren Spike-Werte (7,9 · 6,3 ·
5,9 · 4,7 · 3,3 · 2,0 · 2,0) liegen weit unter der Schwelle — das ist kein
Schwellwertproblem. Eine Schwelle um 2 würde massenhaft Gutes verwerfen. **Die
übersehenen Ausreißer gehören dem Fit, nicht dem Gate.**

### Abdeckungsmatrix (AUC, `K` ausgeschlossen, ± Hanley-McNeil-SE)

| Kennzahl | `A` | `W` | `B` | `E` | irgendein |
|---|---|---|---|---|---|
| Spitze → Tinte | 0,73±0,08 | 0,71±0,06 | **0,80**±0,06 | **0,71**±0,05 | **0,82**±0,04 |
| Median → Tinte | 0,49 | 0,68 | 0,55 | 0,51 | 0,63 |
| 90 % → Tinte | 0,48 | 0,78 | 0,75 | 0,65 | 0,76 |
| Anteil > 0,10 xh | 0,69 | 0,65 | 0,76 | 0,64 | 0,69 |
| Anteil > 0,20 xh | 0,63 | 0,48 | 0,51 | 0,50 | 0,53 |
| `geo_rmse` | 0,60 | 0,81 | 0,80 | 0,63 | 0,79 |
| `cov_rmse_local` | 0,70 | **0,84**±0,05 | 0,78 | 0,54 | 0,78 |
| Spike-Verhältnis | **0,86**±0,06 | 0,69 | 0,78 | 0,54 | 0,73 |

Die vorregistrierten Erwartungen und ihr Ausgang:

1. `A` wird von Spike-Verhältnis und Spitze gesehen — **teilweise**: Spike
   0,86 ja, Spitze 0,73 knapp darunter (innerhalb SE).
2. `W` wird von **keiner** Kennzahl gesehen (< 0,65) — **falsifiziert**.
   `cov_rmse` 0,84, `geo_rmse` 0,81.
3. `E` liegt am Anfang oder Ende der Ankerkette — **bestätigt**: 21/35 = 60 %
   gegen 19/110 = 17 % bei allen anderen.
4. `B` wird am besten vom Anteil außerhalb gesehen, nicht von der Spitze —
   **nicht bestätigt** (0,80 vs. 0,76, innerhalb SE).

Vorhersage 2 war die interessanteste, und sie ist falsch. **Die Aussage
„unsere Kennzahlen sehen nicht, was stört" gilt nur für die Ausreißer**
(`geo_rmse` dort 0,60). Für Gewackel und Bereich-daneben sind `geo_rmse` und
`cov_rmse` gute Detektoren. Die Falsifikation hält schärferer Prüfung stand:
über die 14 Bilder, die **nur** `W` tragen, gegen die 71 reinen `G` steigt
`cov` auf 0,87; `cov` trennt `W` auch von den *anderen* Fehlern (0,74, wo
Spike auf 0,55 und Spitze auf 0,50 fällt); und innerhalb derselben Glyphe
gepoolt bleiben 0,83. Es ist also kein Ko-Okkurrenz- und kein
Glyphen-Artefakt.

### Der Hauptbefund: `E` ist ein abgeschnittenes Strichende

74 der 79 Fehlerbilder tragen einen freiwillig gesetzten Ortsmarker (94 %).
Über die 49 eindeutig einfach gelabelten:

| | n | Anfang < 10 % | Mitte | Ende > 90 % | an Strichgrenze |
|---|---|---|---|---|---|
| `A` Ausreißer | 6 | 2 | 4 | 0 | **0** |
| `W` Gewackel | 14 | 6 | 5 | 3 | 0 |
| `B` Bereich daneben | 9 | 1 | 7 | 1 | 1 |
| `E` Knick am Rand | 20 | **15** | 2 | 3 | **20** |

Präzise formuliert — und die 100-%-Zahl ist dabei **kein zweiter Beleg**,
sondern für 15 der 20 Fälle dieselbe Beobachtung wie „im ersten Zehntel":
`E` ist ein **abgeschnittenes Strichende**, zu etwa 85 % ein Strichanfang
(3 der 20 sitzen am Kettenende, 2 an einem internen Strichstart, beide der
i-Punkt). Nicht ein Knick.

Was den Schluss trägt, ist der **Kontrast bei kategorieblinder Mechanik**:
die Abbildung Klick → Anker weiß nichts von der Kategorie, und trotzdem
landen `W` 0/14, `A` 0/6, `B` 1/9 an Strichgrenzen, gegen `E` 20/20 — bei
einer Basisrate von 7–9 % der Ankerindizes unter Zufallsklicks. Ein
Abbildungsartefakt kann diesen Kontrast nicht erzeugen. Ein Schnapp-Effekt
scheidet ohnehin aus: die `E`-Klicks liegen mit Median 0,02 xh (max 0,05)
praktisch auf dem Anker, und der Crop hat 0,4 xh Polster.

Die Notizen des Autors sagen dasselbe unabhängig: „der Buchstabe fängt zu
spät an, der halbe Anfangsstrich fehlt, der kommt eigentlich von der
Grundlinie" (t), „oben links fängt der Strich nicht am Anfang an" (P),
„startet aber auch nicht ganz links" (langes ſ, als **gut** gelabelt — die
wahre Prävalenz liegt also eher über 23 %).

> **Korrektur (`aug09`): die Überschrift ist falsch, der Befund bleibt.**
> Es ist **kein** abgeschnittenes Strichende. Die Ernte fittet ein ganzes Wort
> als EINE Kette (`_harvest_case_chain`, alle 245 Vorkommen tragen
> `fit_path: "chain"`), und die Verbindungsstücke gehören zu deren
> Connector-Segmenten, nicht zu den Ankern eines Buchstabens. Das
> Bewertungsblatt zeichnete nur die Buchstaben-Anker — jeder verbundene
> Buchstabe endete auf dem Bildschirm in der Luft. Nachgemessen: die Tinte
> jenseits des Buchstabens liegt 0,25 xh von der GEZEICHNETEN Linie, aber
> **0,02 xh vom gespeicherten Federweg** (24 von 26 gedeckt). Der Fit hatte
> sie die ganze Zeit.
>
> Die naheliegende Folgerung „dann sind die `E`-Labels ein Artefakt" ist
> allerdings ebenfalls falsch, und ihre eigene Kontrollgruppe widerlegt sie:
> **jeder** wortinterne als *gut* gelabelte Buchstabe trägt dieselbe
> ungezeichnete Connector-Tinte, im Median sogar weiter weg (0,50 xh gegen
> 0,25 xh). Derselbe Beurteiler sah denselben Hintergrund auf 71 guten Bildern
> und nannte ihn dort nicht — bei S121 sogar ausdrücklich notiert und trotzdem
> als gut gewertet.
>
> Was `E` real unterscheidet, ist die **Naht**: in der Umgebung der markierten
> Stelle weicht der gespeicherte Federweg SELBST maximal 0,105 xh von der
> Tinte ab, gegen 0,047 xh bei den guten — **AUC 0,84** (0,83 auf den reinen
> `E`-Bildern), dazu +0,032 xh Endanker-Abstand und +60° Endkrümmung im
> Vergleich gleicher Glyphen. „Knick am Rand" war wörtlich richtig: ein
> lokaler Defekt am Übergang Buchstabe → Connector.

**Warum keine Kennzahl das sieht:** nicht, weil `cov_rmse_local` seinen Fehler
wegdefiniert — es misst den FIT (Verbindung inbegriffen), während der Mensch
die ZEICHNUNG (ohne sie) beurteilt hat; die Kennzahl war nicht blind, die
Darstellung war unvollständig. Der Grund ist ein anderer und bleibt bestehen:
jede per-Buchstabe-Kennzahl hat ihr Fenster am Buchstaben, und der Defekt sitzt
an der Naht dahinter. Deshalb `cov` gegen `E` 0,54, und *unter den
Fehlerbildern* sogar **0,26** — `E`-Fälle sehen für `cov` besser aus als andere
Fehler, weil ihr Buchstabenteil tatsächlich gut sitzt.

Zwei Kennzahl-Versuche sind daran gescheitert, beide aus derselben falschen
Ursachenannahme: Tinte dem nächstgelegenen Buchstaben zuordnen (AUC 0,60) und
ein richtungsabhängiger Korridor entlang der Eintritts-Tangente (0,63). Beide
suchten unbedeckte Anstrich-Tinte, die es nicht gibt. Der Kandidat, der trägt,
ist die **naht-lokale Maximalabweichung Federweg ↔ Tinte** (0,84) — entwickelt
auf denselben 150 Labels und deshalb nach der eigenen Vorregistrierungsregel
erst an den 95 zurückgehaltenen Vorkommen zu bestätigen.

Zur Slot-Verteilung: **26 der 35 Fälle sind wortintern, 9 stehen auf Slot 0.**
Die frühere Zuspitzung, `t` (4/4) und `i` führten die Wortanfangs-Fälle an, ist
datenwidrig — kein einziges `t` steht auf Slot 0, alle vier sind wortintern.
Und von den 9 Slot-0-Fällen tragen 5 ihren Marker am AUSTRITT, nicht am
Eintritt; die Gruppe sagt also nichts über fehlende Anstriche am Wortanfang.
Genau ein Fall (`Z` in „Zügel", 0,28 xh) hat Tinte, die weder Buchstabe noch
Federweg deckt — dort fehlt wirklich etwas im Modell.

### Was dabei widerlegt wurde

Drei Aussagen aus §8 und aus der laufenden Arbeit halten nicht:

1. **„22 von 23 Gate-Ablehnungen sitzen an Eckankern/Strichgrenzen."** Die
   Zahl stammt aus dem Maximum des eigenen Detektors und ist zirkulär. Sie ist
   damit *unbelegt* — aber durch die menschlichen Marker auch nicht widerlegt:
   0 von 6 ist bei ~8 % Basisrate unter jeder Hypothese der Erwartungswert,
   und nur 2 der 6 markierten Ausreißer sind überhaupt Gate-Ablehnungen. Wer
   an dieser Stelle etwas baut, braucht vorher eine nicht-zirkuläre
   Ortsanalyse.
2. **Der Klick trifft das gemessene Maximum nur in 45 % der Fälle** (`W` 5/14,
   `E` 8/20). Der Mensch zeichnet nicht nach, was die Kennzahl anzeigt.
3. **Die Ortsprüfung ist unabhängig von der Kennzahl, nicht vom Fit.** Der
   Beurteiler sieht die gefittete Linie; bei `E` ist das sichtbare Symptom ihr
   Ende. Das entwertet den Kontrast nicht, gehört aber gesagt.

Die vorregistrierte Ausschlussregel „Mehrfachkategorien fallen aus der
kategoriespezifischen Ortsprüfung" ist nachträglich empirisch bestätigt: von
den 8 Wiederholungspaaren mit Marker auf beiden Seiten liegen die sechs
einfach gelabelten 3–12 px auseinander, die beiden Ausreißer (29 px, 97 px)
sind **genau** die Bilder mit zwei bzw. drei Kategorien.

### Trimm-Kalibrierung: zwei Populationen, bestätigt

Schritt 9 des Auswerteplans, gerechnet über den Anteil eigener Anker jenseits
von 4·MAD um den per-Anker-Median:

| `G` | `A` | `B` | `W` | `E` | `K` |
|---|---|---|---|---|---|
| 1,7 % | 3,3 % | 4,2 % | 4,6 % | 5,0 % | **58–68 %** |

Saubere Lücke: nichts Nicht-`K` über 51 %, kein `K` unter 57 %. Die
vorregistrierte Erwartung (lokale Defekte nahe dem Gesamtmedian, `K` deutlich
darüber) ist bestätigt — **lokaler Defekt und global misslungener Fit sind
zwei Populationen, keine Skala**. Das rechtfertigt, sie mit verschiedenen
Mitteln zu behandeln: pro Anker trimmen beim Aggregieren gegen das eine,
ganzflächige Ablehnung gegen das andere. Die Umsetzung ist rendering-ändernd
(über `apply-laufform`) und braucht deshalb A/B gegen die gemessene Tinte
plus Autorfreigabe.

### Grenzen dieses Durchgangs

* **Der Buchstabe wurde ohne seinen Federweg gezeigt** (siehe die Korrektur
  oben). Das kostete den Durchgang seine Hauptdeutung und verschiebt die
  Prävalenz: ohne `E` tragen **59 von 150 = 39 %** der Bilder einen Fehler
  statt 53 %, und 20 Bilder sind reine `E`. Behoben in
  `tools/humanbench/build.py::context_strokes`; der nächste Durchgang zeichnet
  die Verbindungen mit.
* **Die gelabelten Vorkommen sind die Überlebenden.** Die 99 nie geernteten
  und die 23 vom Gate abgelehnten sind nicht darunter. Eine an diesen Labels
  kalibrierte Kennzahl gilt für neu Geerntetes nur unter Vorbehalt.
* **Breite/Schwellzug war konstruktionsbedingt unsichtbar** — gezeigt wurde
  nur die Centerline. „Kein Breitenproblem gefunden" wäre daher kein Befund,
  sondern eine Lücke des Instruments.
* **Ein Beurteiler.** Test-Retest misst Konsistenz, nicht Konstruktvalidität.
  Für das Falsifizieren eigener Vorhersagen reicht das; für „was ist schön"
  nicht.
* Die 95 zurückgehaltenen Vorkommen sind unangetastet und stehen als
  Bestätigungssatz für jede neue Kennzahl bereit.

### Die Lehre

1. **Ein Messgerät, das weniger zeigt als es misst, erzeugt Befunde.** Das
   Blatt zeigte den Buchstaben ohne seinen Federweg, und der Durchgang lieferte
   prompt eine größte Fehlerklasse, die es so nicht gibt. Vor der ersten Runde
   gehört die Frage gestellt: ist das Gezeigte deckungsgleich mit dem, worüber
   geurteilt werden soll? Bemerkt wurde es nicht durch eine Messung, sondern
   weil der Autor sich an die Architektur erinnerte — ein Wort wird als eine
   Kette gefittet.
2. **Eine Kennzahl kann am falschen Ort messen.** `cov_rmse_local` endet am
   Buchstaben, der Defekt sitzt an der Naht dahinter — daher blind (0,54) und
   unter den Fehlerbildern sogar verkehrt herum (0,26). Beim Bau einer Kennzahl
   ist die erste Frage nicht „was misst sie", sondern „wo hört ihr Fenster auf".
3. **Auch die bequeme Widerlegung braucht ihre Kontrollgruppe.** „Alles nur ein
   Artefakt" wirkte zwingend, bis dieselbe ungezeichnete Tinte auf den GUTEN
   Bildern auftauchte — dort sogar reichlicher. Eine These, die den Befund
   erklärt, muss auch erklären, warum sie die Nicht-Befunde nicht erklärt.
4. **Blinde Wiederholungen sind kein Beiwerk.** Ohne sie wäre „unsere
   Kennzahlen sind blind für Gewackel" unfalsifizierbar geblieben — eine
   niedrige AUC hätte auch Labelrauschen sein können. Sie kosten 8 % der
   Bildschirme und entscheiden, welche Aussage überhaupt tragen darf.
5. **Die eigene Ortsbehauptung war zirkulär.** Wer prüft, ob Defekte an
   Eckankern sitzen, darf dafür nicht das Maximum des eigenen Detektors
   benutzen. Der freiwillige Marker kostete einen Klick je Bild und ist die
   einzige Ortsaussage im ganzen Durchgang, die nicht aus der Maschine kommt.

---

## 10. Runde 02: die Rückhaltemenge, und wie eine Kennzahl bestätigt und trotzdem unbrauchbar sein kann (`aug09`)

Der Bestätigungssatz aus §9 — die 95 nie gezeigten Vorkommen — ist gelabelt,
plus 10 blinde Wiederholungen, 105 von 105 geurteilt. Urteile und Schlüssel:
[`data/humanbench/runde-02-urteile.txt`](../../data/humanbench/runde-02-urteile.txt),
Stand des Instruments im zugehörigen Stempel. **Kein Fit hat sich seit §9
geändert** — was sich geändert hat, ist die Zeichnung: der gespeicherte
Wort-Federweg wird jetzt blass mitgezeichnet (die Korrektur aus §9).

### Besetzung, und was der Vergleich mit §9 trägt

| Kategorie | Runde 01 (150) | Runde 02 (95) |
|---|---|---|
| `G` gut | 47,3 % | **61,1 %** |
| `B` Bereich daneben | 14,7 % | **18,9 %** |
| `W` Gewackel | 21,3 % | 14,7 % |
| `A` Ausreißer | 10,0 % | 7,4 % |
| `E` Knick am Rand | **23,3 %** | **7,4 %** |
| `K` nicht bewertbar | 3,3 % | 2,1 % |

Verlässlichkeit: 8 von 10 Wiederholungspaaren tragen dasselbe ganze Urteil.
Gesichert im Sinne der Schranke aus §9 sind nur `G` (5 positive Paare) und `B`
(3); `W` hat 2, `E` eines, `A`/`K`/`U` keines. **Die in §9 vorgemerkte
Konstruktionslehre — Wiederholungen nach Verdachtskategorie schichten — wurde
wieder nicht umgesetzt, und wieder ist die Verlässlichkeit genau der Kategorien
unbestimmt, um die es geht.** Kein Drift (Mediandauer 6 s → 5 s → 5 s), `G` nie
gemeinsam mit einer Fehlerart, Marker auf 94,6 % der bemängelten Bilder.

**Der Verdacht „die Reserve ist einfach ein leichterer Satz" ist gemessen und
ausgeräumt:** auf der Größe, nach der geschichtet wurde, sind die beiden
Ziehungen ununterscheidbar — AUC 0,492 ± 0,038, Mediane 0,092 gegen 0,094.
Für `E` ist die Differenz 23,3 % → 7,4 % ein z ≈ 3,7; Stichprobenzufall
scheidet aus.

**Was bleibt, ist trotzdem nicht auflösbar.** Zwischen den Runden hat sich
nicht nur das Instrument geändert, sondern auch der Beurteiler: er ist Autor
der Korrektur, kannte die Vorhersage „`E` muss fallen" und hat danach gelabelt
— genau die Lage, für die
[`menschliche-bewertung.md`](menschliche-bewertung.md) §8 die Schlussfolgerung
ausdrücklich verbietet. Ein verblindeter Zeichnungsvergleich ist prinzipiell
unmöglich (man sieht dem Bild an, ob der Verbinder gezeichnet ist). Der
Prävalenzsturz ist damit **vereinbar mit** der Artefakt-Erklärung und belegt
sie nicht; der Beleg bleibt die mechanistische Geometriemessung aus §9 (Tinte
0,25 xh von der Zeichnung, 0,02 xh vom gespeicherten Federweg, 24 von 26
gedeckt). Die spiegelbildliche Arithmetik „−16 pp `E` ≈ +14 pp `G`" stand
nicht im Auswerteplan und ist ein Nachtrag, kein getroffener Vorhersagepunkt.

**Und die Gegenrichtung ist offen.** Der blass gezeichnete Federweg kann echte
Nahtdefekte auch *legitimieren* — das Auge schreibt die Naht-Tinte dem
Verbinder zu. Geprüft am `d_end` der GUT-Bilder beider Runden: Median 0,032 →
0,033, aber p90 **0,047 → 0,067** und AUC(Runde 02 > Runde 01) 0,571,
p = 0,082. Nicht signifikant, aber in genau der befürchteten Richtung: die
7,4 % `E` sind eher eine Unter- als eine Obergrenze.

### Die Nahtstellen-Kennzahl: bestätigt — und als Kriterium erledigt

Vorregistriert war die Bestätigung von `d_end` (Abstand des Kettenendes zur
nächsten Tinte, in x-Höhen) auf der Rückhaltemenge. Zwei Dinge mussten vorher
festgezurrt werden, und eines davon war ein Fehler in §9:

* **Markerfrei.** Die 0,84 aus §9 wählte das gemeinte Ende über den *Klick des
  Beurteilers*. Auf `G`-Bildern gibt es keinen Klick — die Zahl war also nach
  oben verzerrt und als Abnahmekriterium ohnehin unbrauchbar, weil im Betrieb
  kein Mensch klickt. Bestätigt wird die markerfreie Fassung: **das schlechtere
  der beiden Kettenenden, dieselbe Regel für jeden Bildschirm.**
* **Kriterium vor der Zahl** (unabhängig gesetzt, bevor gerechnet wurde):
  bestätigt bei exaktem einseitigem Mann-Whitney p < 0,05 **und**
  Punktschätzer ≥ 0,75.

Ergebnis: **AUC 0,764, p = 0,0117** bei n = 7 `E` gegen n = 58 `G`. Beide
Bedingungen erfüllt. Was damit gilt, ist ausschließlich „`d_end` sieht `E`
deutlich über Zufall"; bei dieser Besetzung ist das 95-%-Intervall rund
±0,19 breit, „AUC ≈ 0,84 bestätigt" wäre also nicht sagbar.

Zwei **nicht** vorregistrierte Nachprüfungen erledigen die Kennzahl trotzdem
als Abnahmekriterium:

| Kontrast | AUC |
|---|---|
| `E` gegen `G` | 0,764 |
| `W`/`B` gegen `G` | 0,721 |
| **`E` gegen `W`/`B`** | **0,539 ± 0,129** |

* **Sie ist nicht nahtspezifisch.** Gegenüber den anderen Fehlerarten trennt
  sie auf Zufallsniveau. Sie misst „an diesem Fit stimmt etwas nicht", nicht
  „die Naht stimmt nicht" — der Name war bereits die Behauptung.
* **Sie schlägt nicht, was wir haben.** Der größte Abstand irgendwo auf der
  Kette (`peak`, längst berechnet) trifft dasselbe Urteil besser: 0,803 gegen
  `E`, 0,884 gegen `W`/`B`, **0,888 ± 0,039 für „irgendein Mangel" gegen `G`**.
  Bei Schwelle 0,13 xh: Genauigkeit 0,83, Trefferquote 0,43.

`d_end` wird deshalb **nicht** als Kennzahl geführt. Der Ertrag der Runde ist
ein anderer: `peak` ist die beste automatische Entsprechung des Menschenurteils,
die das Projekt besitzt, und sie ist bereits im Einsatz.

### `B` ist ein `d`-Problem, kein Platzierungsproblem

`B` („ein ganzer Bereich liegt neben der Tinte") ist die einzige Fehlerart
dieser Runde mit gesicherter Verlässlichkeit, die vorhandenen Kennzahlen sehen
sie, und ein `B`-Segment verschiebt viele Anker kohärent — bei
`LAUFFORM_MIN_OCCURRENCES = 3` zieht ein einziges `B`-Vorkommen den
Per-Anker-Median. Dass sie mit 18,9 % jetzt die größte Klasse ist, trägt
dagegen nichts (14,7 % → 18,9 % ist z ≈ 0,9); sie führt nur, weil `E`
zusammengebrochen ist.

Zwei Diagnosen vor jedem Eingriff:

**Platzierung?** Nein. Eine starre Verschiebung des ganzen Buchstabens
(±0,25 xh, 0,025er Raster) holt aus den `B`-Vorkommen **0 %** des Residuums
heraus — der Fit sitzt bereits an der bestmöglichen starren Stelle.

| Gruppe | n | RMS jetzt | RMS bestmöglich | entfernt | Verschiebung |
|---|---|---|---|---|---|
| `G` | 58 | 0,031 | 0,030 | 0 % | 0,000 xh |
| `B` | 18 | 0,042 | 0,042 | 0 % | 0,025 xh |
| `W` | 7 | 0,048 | 0,046 | 3 % | 0,025 xh |

**Über die Glyphen verteilt?** Nein — es konzentriert sich:

| Glyphe | `B` / Vorkommen |
|---|---|
| **`d`** | **5 / 7** |
| `n` | 2 / 13 |
| `e` | 1 / 15 |
| `u` · `i` · `r` · `a` | 0 / 7 · 0 / 7 · 0 / 7 · 0 / 5 |

Fünf der sieben `d`-Vorkommen tragen `B`; die übrigen 13 `B`-Fälle verteilen
sich als Einzelstücke über zehn Glyphen. Nach der Stufendoktrin
([`optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md) §5) ist
das eine Aussage über die **Vorlage** (`chart_ductus` / `laufform`) und nicht
über die Zielfunktion: `core/fit.py` wäre der falsche Ort. Der nächste Schritt
ist die Autopsie der `d`-Tafelform gegen ihre fünf bemängelten Vorkommen — und
erst wenn die `d` sauber ist, sagt der dünne Rest, ob es überhaupt ein
glyphenübergreifendes `B`-Muster gibt.

### Die nicht-zirkuläre Ortsanalyse — und was sie dem Ausreißer-Fix nimmt

§9 hat die Aussage „22 von 23 Gate-Ablehnungen sitzen an Eckankern" als
zirkulär zurückgezogen (sie kam aus dem Maximum des eigenen Detektors) und
festgelegt: **wer dort etwas baut, braucht vorher eine nicht-zirkuläre
Ortsanalyse.** Runde 02 liefert die Daten dafür — 35 vom Menschen gesetzte
Marker gegen die Landmarken, die die Vorlage selbst führt
(`trace_meta.corner_anchors` und `stroke_starts`, Nachbarschaft ±3 Anker wie
`analyse.py::EDGE_ANCHORS`). Nullhypothese ist die Trefferquote, die reines
Zufallsklicken bei genau dieser Nachbarschaftsgröße erzeugt.

| Landmarken-Satz | Gruppe | n | am Landmark | Zufall | p |
|---|---|---|---|---|---|
| **mit** Kettenenden | alle Marker | 35 | 42,9 % | 23,0 % | **0,007** |
| mit Kettenenden | ohne `E`-Bilder | 28 | 32,1 % | 22,5 % | 0,158 |
| **ohne** Kettenenden | alle Marker | 31 | 12,9 % | 18,4 % | 0,848 |
| ohne Kettenenden | ohne `E`-Bilder | 25 | 16,0 % | 17,7 % | 0,669 |
| ohne Kettenenden | nur `A` | 4 | 50,0 % | 25,2 % | 0,265 |

Zeile 1 sieht nach Befund aus und ist keiner. Nimmt man die **Kettenenden**
aus dem Landmarken-Satz — dort sitzt `E` definitionsgemäß, „Knick nur am
Rand" —, verschwindet der Effekt vollständig und liegt sogar unter dem
Zufall. Es bleibt also: **die einzige Ortsstruktur in den Markern dieser Runde
ist `E` am Ende, und das ist eine Tautologie.** An Eckankern und inneren
Absetzern konzentriert sich nichts.

Damit ist die starke Fassung der §8-Vermutung — 96 % der Ablehnungen an einer
unterbestimmten Ankerklasse — **nicht mehr bloß unbelegt, sondern gemessen
widerlegt**, jedenfalls in jeder Größenordnung, die einen Eingriff getragen
hätte; ein schwacher Resteffekt ist bei n = 31 nicht auszuschließen. Der
letzte offene Reparaturweg für die Ausreißer, den §7 und §8 nicht schon
ausgeschlossen hatten, ist damit zu. Die Bilanz für `A` steht jetzt so da:

* **Biegeterm** (§7) — verworfen, bepreiste globale Krümmung statt der
  Unstetigkeit.
* **Scharnier** (§8) — verworfen, bepreiste den Abstand statt der
  Unstetigkeit, kostete Deckung und fand nebenbei einen echten Ableitungsfehler
  am Cropsrand.
* **Sample-Stützung der Eckanker-Klasse** — die Diagnose dahinter hält der
  nicht-zirkulären Prüfung nicht stand. **Nicht bauen.**
* **Das Gate** bleibt, was es ist: eine Rückfalllinie, die aussortiert statt
  zu reparieren.

Ein vierter Ansatz braucht eine neue Diagnose, nicht eine neue Zielfunktion —
und die Marker dieser Runde liefern sie nicht. Für `W` („Gewackel") ist
dagegen noch gar nichts versucht worden: beide verworfenen Terme zielten auf
den einzelnen Sprung, nicht auf die unruhige Linie, und die Kennzahlen sehen
`W` (`peak` 0,88 für `W`/`B` gegen `G`). Das ist die nächste offene Frage am
Fit — nach der `d`-Vorlage, die billiger und sicherer ist.

### Grenzen dieser Runde

* **Die Reserve ist aufgebraucht.** Jede weitere auf diesen Labels entwickelte
  Kennzahl hat keinen Bestätigungssatz mehr; der nächste braucht neue Urteile.
* **`U` = 0** ist kein gewachsenes Zutrauen, sondern möglicherweise eine
  Verschiebung im Gebrauch des Modifikators. Es macht nur die U-freie
  Zweitrechnung gegenstandslos.
* **61,1 % `G`** darf weder als Fit-Verbesserung zitiert werden (kein Fit hat
  sich geändert) noch als Aussage über die Grundgesamtheit (es sind die
  Überlebenden von Ernte und Gate).
* **Das Ernte-Gate gegen die beiden `K`-Fälle** ließ sich nicht prüfen: die
  gespeicherten `measurements` dieser Vorkommen führen kein
  `anchor_spike_ratio`, das Gate wirkt bei der Ernte. Für die Gegenprobe aus
  §8 müsste die Kennzahl aus den Ankern nachgerechnet werden.

### Die Lehre

1. **„Bestätigt" und „brauchbar" sind zwei Fragen.** `d_end` hat sein
   vorregistriertes Kriterium bestanden und ist trotzdem erledigt — weil
   niemand vorher gefragt hatte, ob sie das trennt, *wofür* sie benannt war,
   und ob sie eine vorhandene Kennzahl schlägt. Beide Fragen gehören in die
   Vorregistrierung, nicht hinterher.
2. **Ein Kennzahlname ist eine unbewiesene Behauptung.** „Nahtstellen-Kennzahl"
   klang nach Mechanismus und war eine Hoffnung; gemessen trennt sie `E` nicht
   von `W`/`B`. Wer eine Kennzahl benennt, hat die Spezifitätsprüfung damit
   versprochen.
3. **Eine Korrektur kann in beide Richtungen Artefakte machen.** Der
   nachgezeichnete Federweg beseitigt das Schweben und kann echte Nahtdefekte
   maskieren. Die Gegenprobe kostete eine Rechnung und hätte gefehlt, wenn nur
   die erwartete Richtung geprüft worden wäre.

---

## 11. Der Nachbarschaftsterm gegen den Einzelanker (`aug10`, vorregistriert)

> **Stand:** Der unten als Vorbedingung festgelegte Diagnoseschritt ist
> ausgeführt; sein Ergebnis steht in §11a. Der Plan darunter bleibt unverändert
> stehen — er ist vorregistriert und wird nicht nachträglich an die Zahl
> angepasst.


Kein Ergebnis, sondern ein **festgelegter Plan** — damit das Kriterium nicht
hinterher an die Zahl angepasst wird. Der Term ist gebaut und liegt inert im
Repo (`core/fit.py`, `smooth_weight` = 0,0).

### Was gemessen ist

* Der Defekt ist punktförmig: von 22 vom Autor markierten Ausreißern liegt der
  markierte Anker in 12 Fällen überhaupt neben der Tinte — und in **12 von 12
  ist der Ausflug genau ein Anker lang**. 17 der 22 sitzen auf einem Anker,
  dessen BEIDE Nachbarschritte ≥ 3× den Median seines Federzugs betragen.
* **Kein toter Fleck.** `|∇d|` des geglätteten Feldes am Anker: Median 0,898,
  0 von 49 auf einem Grat. **Aber diese Messung ist am falschen Ort** — die
  Zielfunktion liest das Feld nur an den ~180 Samples, nie am Anker
  (vom-scan-zum-schreiben.md Schritt 4). Sie beziffert eine Kraft, die der
  Optimierer nicht sieht, und ist damit **kein Beleg**, dass Rückstellkraft
  vorhanden ist. Nachzuholen: `d` an den Samples zwischen den beiden
  Nachbarankern.
* Der Anker ist gegenüber der Tafelform 0,208 Einheiten verschoben, seine vier
  Nachbarn 0,047 — elffach der Median aller Anker (0,018). Er wurde also
  dorthin getrieben; die Box-Schranken (0,75) sind nicht bindend.

### Der fehlende Schritt vor jedem Bau

Ein stationärer Punkt bei vorhandener Feldkraft heißt: **eine Gegenkraft
balanciert**, und die ist unbenannt. Kandidaten, alle im Code und alle in
derselben Größenordnung (~3e-3): die Spline-Kopplung (negative Nebenkeulen —
ein hinausgeschobener Stützpunkt kann die Nachbarsamples verbessern), der
Deckungsterm (ein unbedeckter Skelettrest zieht per ICP), der Breitenterm (auf
leerem Papier ist das propagierte Feld definiert, Gewicht 0,15), oder: **diese
Hand schreibt das Chart-Merkmal nicht** — dann repariert der Term einen
Messwert, den es nicht gibt.

**Erst die Gradientenzerlegung, dann der Term.** Pro Term und pro Anker die
Kraft am gefundenen Optimum. Bauregel: die Terme unabhängig rechnen und
prüfen, dass ihre **Summe exakt dem echten Gradienten** entspricht — sonst
driftet die Diagnostik von der Zielfunktion ab.

### Wo der Term hingehört

**Nicht dorthin, wo er gerade liegt.** Alle 245 gespeicherten Vorkommen kommen
aus `tools/pairlab/chain.py::fit_word_chain`, das eine **eigene** Zielfunktion
hat; `core/fit.py::_InstanceFit.objective` wird auf dem Ketten-Pfad nie
aufgerufen. Der Ketten-Löser besitzt bereits einen Zweite-Differenz-Term —
aber laut eigener Beschreibung „second differences of the **connector blocks
only**". Genau in den Buchstabenblöcken, wo die 49 Anker stranden, fehlt die
Bindung. Der Term in `core/fit.py` deckt denselben Mangel im
Einzelbuchstaben-Pfad, ist aber nicht der, den das A/B messen will.

Unterschied, der bleibt: der Verbinder-Term nimmt die zweite Differenz der
ANKER (bogenlängen-normiert) — richtig für einen frei erfundenen Verbinder.
Für einen Buchstaben wäre das der verworfene Biegeterm aus §7; dort muss es
die zweite Differenz der VERSCHIEBUNGEN sein.

### Das A/B — und die vier Stellen, an denen es sich schönrechnen lässt

Nutzen: Gate-Ablehnungen unter 23, Sprungverhältnis fällt. Kosten (Abbruch):
`cov_rmse_local` +2 %, `geo_rmse` +5 %, keine Konvergenz verloren. Genommen
wird das **kleinste wirksame Gewicht**, nicht das bestaussehende.

Vier Korrekturen daran, aus dem Gegenlesen:

1. **`anchor_spike_ratio` ist fast dieselbe Statistik, die der Term
   bestraft** — jedes Gewicht senkt sie per Konstruktion, auch wenn der Anker
   weiter im Papier steht. Es braucht ein tintenbezogenes Kriterium, das
   **nicht** in der Zielfunktion steht: Anteil der Anker mit `d(Anker)` über
   Schwelle, vorher/nachher.
2. **„Kleinstes wirksames Gewicht" auf denselben 245 ist Winner's Curse.**
   Vorregistrierte Leiter plus Bestätigung auf einer Rückhaltemenge — die des
   humanbench ist mit Runde 02 aufgebraucht, es braucht eine neue Teilung.
3. **Die Kostenschranken sind Mittelwerte.** Gepaart je Vorkommen rechnen,
   dazu Quantil-/Worst-Case-Schranken und die Zahl neu scheiternder
   Vorkommen. „Unter 23 Ablehnungen" ist eine grobe Ganzzahl — 23 → 22 ist
   Rauschen; es braucht McNemar über die Gate-Flips.
4. **Kontamination.** Der Baseline-Arm wird im selben Lauf mit Gewicht 0 neu
   gefittet (der Term ist inert, das garantiert Identität), nie gegen
   archivierte Fits verglichen. `interp+snap` ist in **beiden** Armen aus. Die
   Vorkommen, an denen die Diagnose entstand, werden ausgewiesen. Und geprüft
   wird, ob ein „wirksames" Gewicht nur Konditionierung oder Stoppverhalten
   verschiebt (nit-Verteilung beider Arme).

### `interp+snap` — die Nachbearbeitung, und warum sie nicht die Antwort ist

Gemessen über 245 Vorkommen: Gate 23 → 9 Ablehnungen (14 gerettet, 0 neu),
Peak-Median der 37 Betroffenen 0,1414 → 0,0975 xh, Sprungverhältnis
6,00 → 3,67, null Verschlechterungen, Detektor trifft in 16 von 17 Fällen den
markierten Anker. Trotzdem **nicht übernehmen**: „auf die nächste Tinte
schnappen" ist genau der Mechanismus des in §8 verworfenen Scharniers, nur
nachgelagert — an Kreuzungen schnappt es auf den falschen Ast. Und ein
reparierter Anker ist ein **erfundener Messwert**, der über `instances` in die
Per-Anker-Mediane läuft; gegen den einen schlechten Anker hat die Pipeline mit
`LAUFFORM_MIN_OCCURRENCES` bereits die richtige Verteidigung.

Legitim nur unter drei Bedingungen: in `fit_meta` als Reparatur protokolliert
(welche Anker, wie weit), das Gate urteilt über die **unreparierte** Geometrie
(eine Reparatur ist eine Beinahe-Ablehnung, nie ein Bestehen), und im A/B in
beiden Armen aus. Als **Diagnostik** ist sie wertvoll: hilft sie systematisch,
ist das der Beleg für die Sampling-Blindheit oben — dann die Zielfunktion
reparieren und den Patch wegwerfen.

---

## 11a. Die Gradientenzerlegung: was den Anker wirklich hinausträgt (`aug10`)

Der in §11 als Vorbedingung festgelegte Schritt, ausgeführt mit
`tools/pairlab/gradlab.py` über **96 Kettenlösungen, 41 280 Buchstabenanker**,
an genau den Optima, aus denen die gespeicherten Vorkommen stammen (dieselben
Fälle, Fenster und Fits wie die Ernte). Gestrandet nach der gemessenen Form des
Defekts — beide Nachbarschritte ≥ 3× den Medianschritt des eigenen Federzugs —:
**128 Anker in 82 von 344 Buchstaben-Vorkommen, verteilt über 27 Glyphen.**
Also kein Glyphenproblem, sondern eine Eigenschaft des Modells.

Die Bauregel hielt über den ganzen Lauf: schlechteste Abweichung der Summe vom
echten Gradienten **1,7e-13** relativ.

### Die Kräfte je Term (Median, gewichtet wie in der Zielfunktion)

| Term | gestrandet | Kontrolle | Verhältnis |
|---|---|---|---|
| **`coverage`** | 5,39e-4 | 1,67e-5 | **32,4×** |
| `reg` | 6,95e-4 | 8,17e-5 | 8,5× |
| `geo` | 1,70e-4 | 5,55e-5 | 3,1× |
| `width` | 1,49e-6 | 1,72e-6 | 0,9× |
| `crop` · `overlap` · `smooth` | 0 | 0 | — |
| **Gesamt** | 4,69e-6 | 1,68e-6 | — |

Der Gesamtgradient liegt zwei Größenordnungen unter jedem Einzelterm: es ist
ein echter stationärer Punkt, die Terme heben sich auf. Drei Zeilen erledigen
sich sofort:

* **`smooth` ist exakt 0 an jedem Buchstabenanker** — die strukturelle
  Bestätigung der §11-Prämisse: der Ketten-Glätter fasst nur Verbinder an.
* **`width` ist an gestrandeten Ankern schwächer** als an gesunden (0,9×). Der
  Breitenterm ist nicht beteiligt; damit ist einer der vier §11-Kandidaten
  gemessen erledigt.
* **`crop` ist 0** — keiner der Fälle hängt am Cropsrand.

### `reg` ist keine Erklärung, sondern dieselbe Aussage nochmal

Der Tikhonov-Zug ist konstruktiv linear in der Verschiebung
(`2λ·w·δ/n`). Kraft geteilt durch Verschiebung:

| | Median |
|---|---|
| gestrandet | 4,167e-3 |
| Kontrolle | 4,166e-3 |

**Auf vier Stellen identisch.** Die „8,5× größere Rückstellkraft" ist exakt die
9,2× größere Verschiebung (0,1849 gegen 0,0201 xh) — dieselbe Feder, weiter
gedehnt. `reg` verhält sich am gestrandeten Anker in nichts anders als
überall; als Erklärung für die Strandung ist er raus. Ohne die
Kontrollpopulation hätte man diese Zahl mit einiger Berechtigung für einen
Befund gehalten.

### Wer schiebt, wer hält — und dass §11 die Frage falsch herum gestellt hat

Median-Kosinus zwischen den Termkräften:

| Paar | gestrandet | Kontrolle |
|---|---|---|
| `coverage` vs. `reg` | **−0,996** | −0,966 |
| `geo` vs. `reg` | −0,849 | −0,997 |
| `coverage` vs. `geo` | **0,554** | 0,912 |

Weil der `reg`-Gradient konstruktiv **parallel zur Verschiebung** liegt, ist
diese Spalte zugleich die Richtungsmessung gegen die Verschiebung selbst. Und
sie sagt: **die Datenterme schieben den Anker hinaus, der Tikhonov-Zug ist das
Einzige, was hält.** Das gilt am gesunden Anker genauso — so soll es sein, das
ist der Fit. Was den gestrandeten unterscheidet, ist zweierlei:

1. **`coverage` dominiert mit 32×** und ist mit −0,996 fast perfekt entlang der
   Verschiebung ausgerichtet.
2. **`coverage` und `geo` haben sich entkoppelt** (0,912 → 0,554, also von
   ~24° auf ~56°). Die beiden Datenterme sind sich nicht mehr einig, wohin.

§11 hatte gefragt: „ein stationärer Punkt bei vorhandener Feldkraft heißt, eine
**Gegen**kraft balanciert — und die ist unbenannt." Gemessen ist es umgekehrt.
Es gibt keine geheimnisvolle Kraft, die den Anker draußen festhält. **Der
Deckungsterm trägt ihn hinaus**, das Feld widerspricht nur teilweise, und
`reg` ist die einzige Bremse. Von §11s vier Kandidaten bleibt genau einer
übrig — der genannte „unbedeckte Skelettrest zieht per ICP" —, und er ist nicht
Nebenwirkung, sondern Hauptantrieb.

### Warum die Zielfunktion das billig bekommt

Die dritte Messung, die §11 als nachzuholen markiert hatte — das Feld an den
**Samples** statt am Anker:

| | Anker-Auslenkung | `d` an den Samples (roh), Mittel | max |
|---|---|---|---|
| gestrandet | 0,1849 xh | 1,513 px | 5,343 px |
| Kontrolle | 0,0201 xh | 0,897 px | 2,240 px |

Bei ~31 px je xh sind 0,1849 xh rund **5,7 px Ankerreise** — und die kostet an
den Samples im Mittel **0,6 px** mehr Abstand zur Tinte. Die Spline schluckt
den Ausflug: was der Optimierer bezahlt, ist ein Bruchteil dessen, was der
Anker tut. Das ist die in §11 vermutete Sampling-Blindheit, jetzt beziffert,
und es erklärt, warum ein 32× stärkerer Deckungszug den Anker so weit tragen
kann, ohne dass ein Datenterm laut wird.

Der Nachbarabstand ist entsprechend deutlich: die Nachbarn des gestrandeten
Ankers stehen bei 0,0705 xh, er selbst bei 0,1849 — **Faktor 2,6**, gegen 1,02
in der Kontrolle. Die Größe, auf die ein Nachbarschaftsterm zielt, existiert
also und ist groß.

### Was das für den vorregistrierten Term heißt

Die §11-Frage ist beantwortet: **der Term stemmt sich gegen den Deckungsterm.**
Das reicht, um das A/B zu fahren — und es benennt zugleich, was das A/B *nicht*
klärt.

Ein Nachbarschaftsterm ist eine **Steifigkeitsantwort auf ein
Zuordnungsproblem**. Der Deckungsterm ist blind dafür, *wer* einen Skelettpunkt
abdecken soll — genau die Blindheit, für die der Überlappungsterm eingeführt
wurde (`CHAIN_OVERLAP_WEIGHT`: „die Zielfunktion prüft die VEREINIGUNG der
Segmente gegen die Vereinigung der Tinte und ist blind für Zuordnung"). Was
hier gemessen ist, sieht nach derselben Blindheit eine Ebene tiefer aus: ein
Skelettpunkt, den sonst kein Sample abdeckt, rekrutiert den nächstbesten Anker.
Wer den Anker versteift, macht diesen Zug teurer — er beseitigt ihn nicht.

Nach der Eigentümer-Vorgabe „die perfekte, nicht die schnelle Lösung"
(Modell reparieren, nie den Alarm stummschalten) ist das ausdrücklich
festzuhalten: **das A/B misst eine Bremse, keine Ursache.** Es bleibt richtig,
es zu fahren — der Term ist billig, vorregistriert und die Bremse fehlt
tatsächlich —, aber ein bestandenes Kriterium darf nicht als „die Strandung ist
verstanden" gelesen werden. Die offene Frage danach lautet: **deckt an einem
gestrandeten Anker ein Skelettpunkt auf, den kein anderes Sample beansprucht —
und gehört der überhaupt zu diesem Segment?** Das ist mit der
Deckungs-Zuordnung je Punkt messbar (`cKDTree`-Index je `cov_pt`), die
`gradlab` heute nicht ausgibt.

Für §11s Korrektur 1 („ein tintenbezogenes Kriterium, das **nicht** in der
Zielfunktion steht") liefert dieser Lauf die Größe gleich mit: `d_raw` an den
Samples des Ankers, vorher/nachher — roh, ungeglättet, und an dem Ort gelesen,
an dem der Anker überhaupt wirkt.

---

## 11b. Das A/B: vorregistriert, vor dem ersten Lauf (`aug10`)

Geschrieben und committet, **bevor irgendeine Zahl des Versuchs existiert**.
Das ist der ganze Zweck: §10 Lehre 1 („bestätigt" und „brauchbar" sind zwei
Fragen, beide gehören in die Vorregistrierung) und §11 Korrektur 2
(Winner's Curse) lassen sich nicht nachträglich herstellen.

### Die Leiter

`CHAIN_LETTER_BIND_WEIGHT` ∈ **{0 · 1e-4 · 1e-3 · 1e-2}**. Vier Arme, nicht
mehr — jede Zwischenstufe, die erst nach Sichtung eingeschoben wird, ist eine
verdeckte Mehrfachprüfung. Die Normierung ist die von
`core.fit._second_difference_operator` (Indexraum, Mittel über die Zeilen),
damit ein Gewicht auf beiden Fit-Pfaden ungefähr dasselbe bedeutet.

### Die Teilung

| | Menge | n Fälle |
|---|---|---|
| **Entwicklung** | Abb. 19, der `words`-Satz | 63 |
| **Bestätigung** | Abb. 20, der `pairs`-Satz | 33 |

Entlang der **Platten**, nicht zufällig über die Vorkommen: ein zufälliger
Schnitt legt Vorkommen **derselben Kettenlösung** auf beide Seiten, und dann
sind die Hälften nicht unabhängig. Dieselbe Hand, dieselbe Norm, andere Platte.
Die humanbench-Rückhaltemenge ist mit Runde 02 aufgebraucht (§10) und wird hier
nicht ein zweites Mal verbraucht — das hier ist eine **eigene** Teilung für eine
Geometriefrage, die keine Urteile braucht.

Auf der Entwicklungsmenge wird das kleinste wirksame Gewicht gewählt. Auf der
Bestätigungsmenge läuft **nur dieses eine** Gewicht gegen 0, mit denselben
Kriterien. Besteht es dort nicht, ist der Term verworfen — nicht nachjustiert.

### Das Kriterium: Nutzen

**Primär, und ausdrücklich nicht `anchor_spike_ratio`.** §11 Korrektur 1: das
Spike-Verhältnis ist fast dieselbe Statistik, die der Term bestraft — jedes
Gewicht senkt sie per Konstruktion, auch wenn der Anker weiter im Papier steht.
Gemessen wird stattdessen **tintenbezogen**:

> **Anteil der Buchstabenanker mit `d_raw` > 0,15 xh am ANKERORT.**

Drei Eigenschaften, jede absichtlich: `d_raw` ist die **ungeglättete** EDT,
während die Zielfunktion das geglättete Feld liest; gemessen wird **am Anker**,
wo die Zielfunktion nie hinsieht (§11a); und es ist ein **Schwellenanteil**,
keine quadratische Summe. Die Schwelle 0,15 xh ist
`CHAIN_OVERLAP_RADIUS_UNITS` — der im Repo bereits kalibrierte Abstand „noch
innerhalb eines gezogenen Strichs"; darüber liegt der Anker außerhalb der Tinte.

Am Ankerort und nicht an den Samples, obwohl §11a gezeigt hat, dass dort keine
Kraft wirkt: **gespeichert wird der Anker.** Er läuft über
`instances` in die Per-Anker-Mediane und damit in die Laufform, die das
Live-System schreibt. Wo die Kraft angreift, ist eine Frage an die
Zielfunktion; wo der Fehler landet, ist eine Frage an das Produkt.

**Bestehensschwelle:** der Anteil muss **relativ um ≥ 25 %** fallen, gepaart je
Vorkommen gerechnet.

### Das Kriterium: Kosten

§11 Korrektur 3 — keine Mittelwerte allein, gepaart je Vorkommen, mit
Quantil-Schranken und der Zahl neu scheiternder Vorkommen:

| Größe | Schranke |
|---|---|
| `geo_rmse_px`, Median der gepaarten Differenzen | ≤ +5 % |
| `geo_rmse_px`, p90 der gepaarten Differenzen | ≤ +10 % |
| `cov_rmse_local_px`, Median gepaart | ≤ +2 % |
| angenommene Vorkommen (Gate `ok`) | **kein Netto-Verlust** |
| Gate-Kipper | McNemar, nicht signifikant zuungunsten |

„Unter 23 Ablehnungen" aus §11 ist als Kriterium gestrichen: eine grobe
Ganzzahl, bei der 23 → 22 Rauschen ist. An seine Stelle tritt der McNemar-Test
über die Kipprichtungen.

### Das Kriterium: dass es nicht bloß anders rechnet

§11 Korrektur 4. Der Baseline-Arm wird **im selben Lauf** mit Gewicht 0 neu
gefittet; dass das eine Identität ist, ist keine Behauptung, sondern
byte-identisch geprüft (§11a). Zusätzlich berichtet wird die Verteilung von
`iterations` und `hit_iteration_cap` beider Arme: verschiebt ein „wirksames"
Gewicht nur die Kondition oder das Abbruchverhalten, ist der Nutzen ein
Artefakt. `interp+snap` ist in beiden Armen aus — es existiert im Code
ohnehin nicht.

**Die Vorkommen, an denen die Diagnose entstand**, werden ausgewiesen: die 128
gestrandeten Anker aus §11a sind auf der Entwicklungsmenge mitgemessen worden,
also ist der Entwicklungsarm in diesem Punkt nicht unschuldig. Die
Bestätigungsmenge ist es.

### Was das A/B ausdrücklich nicht beantwortet

§11a: der Term ist eine Bremse gegen einen Zug des Deckungsterms, nicht dessen
Ursache. Ein bestandenes Kriterium heißt „die Bremse wirkt und ist bezahlbar" —
nicht „die Strandung ist verstanden".

---

## 11c. Lauf 1: die Leiter hat den Term nie eingeschaltet (`aug10`)

Der in §11b vorregistrierte Versuch ist gelaufen — 63 Wörter, vier Arme, 277
gepaarte Vorkommen. **Kein Gewicht besteht.** Das ist das Ergebnis von
Protokoll wegen, und es steht.

| Gewicht | Anteil Anker außerhalb der Tinte | relativ | Nutzen | `geo` Median | `cov` Median | angenommen | Kosten |
|---|---|---|---|---|---|---|---|
| 0 | 0,0072 | — | — | — | — | 209 | — |
| 1e-4 | 0,0070 | −2,1 % | nein | +0,02 % | +0,03 % | 209 | ok |
| 1e-3 | 0,0072 | 0,0 % | nein | +0,03 % | +0,09 % | 209 | ok |
| 1e-2 | 0,0072 | −0,4 % | nein | +0,10 % | +0,60 % | 210 | ok |

Verlangt waren −25 %. Berichtet, nie Kriterium: die gestrandeten Anker
(98 → 94 → 102 → 97) — der Term senkt also **nicht einmal die Statistik, für
die er gebaut wurde**.

### Warum das kein Befund über den Term ist

Die Kosten sind der Hinweis: +0,10 % Median-Restfehler beim **höchsten**
Gewicht ist keine Zielfunktion, die kämpft, sondern eine, die den Term nicht
bemerkt. Nachgemessen an den Energien einer Lösung:

| | `e_geo` | `w · e_bind` bei 1e-2 |
|---|---|---|
| Wort `das` | 2,23e-3 | **4,9e-6** |

**450-fach kleiner als der Geometrieterm.** Und über acht Baseline-Lösungen
(Gewicht 0, also ohne jeden Blick auf einen Effekt) ist das Verhältnis
`e_geo / e_bind` im Median **3,2** (p10 1,5 · p90 5,3): erst ein Gewicht um 3
stellt die Bindung auf Augenhöhe mit der Geometrie. Die Leiter endete bei
1e-2 — **rund 320-fach zu niedrig**.

### Der Fehler, benannt

Die Leiter kam aus der Analogie zu `core.fit.DEFAULT_SMOOTH_WEIGHT`, „damit ein
Gewicht auf beiden Fit-Pfaden ungefähr dasselbe bedeutet" (§11b). Der Operator
ist derselbe — die **Energieskala der Zielfunktion, in der er steht, ist es
nicht.** Der Ketten-Pfad normiert anders, seine Restfehler leben in anderen
Größenordnungen, und ein aus der Ferne übernommenes Gewicht sagt darüber
nichts. Das ist dieselbe Verwechslung, die §11a an anderer Stelle aufgelöst
hat: zwei Pfade sind nicht vergleichbar, nur weil der Operator gleich aussieht.

Der Versuch hat damit die Hypothese **nicht geprüft**. Er ist kein Beleg gegen
den Nachbarschaftsterm; er ist ein Beleg dafür, dass eine Leiter ohne
Skalenkalibrierung ein leerer Lauf ist. Wer das Ergebnis als „Term wirkt nicht"
zitiert, zitiert einen Versuch, in dem der Term zu 0,2 % anwesend war.

### Vorregistrierung, Lauf 2

Wieder vor dem Lauf geschrieben und committet. Geändert wird **nur die
Leiter**; Teilung, Nutzenkriterium (−25 % relativ am tintenbezogenen Maß),
Kostenschranken und die Prüfungen aus §11 Korrektur 3/4 bleiben Wort für Wort
die aus §11b.

> **Leiter: 0 · 0,1 · 0,32 · 1,0 · 3,2** — geometrisch im Schritt ×3,16, so
> gelegt, dass die Bindung am Baseline-Optimum rund 3 % · 10 % · 31 % · 100 %
> des Geometrieterms beiträgt.

Die Kalibrierung stammt ausschließlich aus **Gewicht-0-Lösungen**, verrät also
nichts über den Effekt — dieselbe Regel wie bei der Instrumentenprüfung in
§11b, wo geprüft wurde, dass das Nutzenmaß überhaupt feuert (4 von 19
Vorkommen, ~0,57 % der Anker).

Zwei Dinge, die dabei ehrlich zu bleiben haben:

* **Die Entwicklungsmenge wird zum zweiten Mal benutzt.** Das ist ihr Zweck,
  aber es heißt, dass die Wahl des kleinsten wirksamen Gewichts jetzt auf einer
  zweifach besuchten Menge geschieht. Was die Aussage trägt, ist die
  **Bestätigungsmenge** — und Abb. 20 ist bis hierher **vollständig unberührt**,
  kein einziger Arm ist dort gelaufen.
* **Ein Gewicht um 3 ist kein kleiner Regularisierer mehr.** Wenn die Bindung
  so viel wiegt wie die Geometrie, formt sie den Buchstaben mit, statt nur
  einen Ausreißer zu bremsen. Genau dafür sind die Kostenschranken da, und
  wenn sie reißen, ist das die Antwort und nicht ein Grund, die Leiter noch
  einmal zu verschieben.

---

## 11d. VERWORFEN: Lauf 2, und warum das Kriterium sich bezahlt gemacht hat (`aug10`)

Mit der kalibrierten Leiter (§11c) **wirkt** der Term. Er tut genau das, wofür
er gebaut wurde — und wird trotzdem verworfen, weil das eine unabhängige Maß
zeigt, dass er den Defekt nicht behebt, sondern **verschmiert**.

63 Wörter, fünf Arme, 277 gepaarte Vorkommen.

| Gewicht | gestrandete Anker | Spike-Median | **Anker außerhalb der Tinte** | `geo` Median / p90 | `cov` Median | `ok` |
|---|---|---|---|---|---|---|
| 0 | 98 | 2,90 | 0,0072 | — | — | 209 |
| 0,1 | 79 | 2,53 | 0,0075 (**+4,6 %**) | +0,28 % / +2,21 % | +2,94 % | 214 |
| 0,32 | 70 | 2,20 | 0,0079 (**+9,6 %**) | +0,62 % / +3,65 % | +5,19 % | 216 |
| 1,0 | 49 | 1,85 | 0,0085 (**+18,4 %**) | +1,29 % / +6,36 % | +7,74 % | 217 |
| 3,2 | 41 | 1,59 | 0,0085 (**+18,4 %**) | +2,38 % / +8,75 % | +10,33 % | 218 |

**Der Term erreicht sein eigenes Ziel und verfehlt die Sache.** Die
gestrandeten Anker fallen um 58 %, das Spike-Verhältnis um 45 % — und
gleichzeitig stehen **mehr** Anker außerhalb der Tinte, nicht weniger.
Verlangt waren −25 %; gemessen sind +18 % in die Gegenrichtung. Die
Kostenschranken reißen zusätzlich schon auf der untersten Sprosse
(`cov` +2,94 % gegen +2 %).

### Der Mechanismus

Der Term glättet die zweite Differenz der **Verschiebungen**. Ein einzelner
Anker kann seinen Ausflug damit nicht mehr allein machen — also **nimmt er
seine Nachbarn mit**. Aus einem Anker im leeren Papier werden drei, die
gemeinsam etwas neben der Tinte liegen. Für jede Statistik, die auf den
*Sprung zwischen benachbarten Ankern* schaut, ist das eine Heilung; für die
Tinte ist es eine Verschlechterung, und für den Per-Anker-Median der Laufform
ist es die schlimmere Variante, weil jetzt mehrere Anker verunreinigt sind
statt einer.

### Der Ertrag ist zirkulär — vollständig

Der Ertrag steigt (209 → 218) und McNemar ist ab 0,32 sogar signifikant
zugunsten des Terms (p = 0,039 · 0,021 · 0,022). Das sieht nach dem
Live-System-Gewinn aus, um den es geht. Die Aufschlüsselung der Kipper zerstört
das:

| Gewicht | gewonnen | davon vorher abgelehnt wegen … |
|---|---|---|
| 0,1 | +6 | `anchor_spike` 6 |
| 0,32 | +8 | `anchor_spike` 8 |
| 1,0 | +9 | `anchor_spike` 9 |
| 3,2 | +11 | `anchor_spike` 9 · `connector_degenerate` 2 |

**Jeder Gewinn bis Gewicht 1,0 ist ein `anchor_spike`-Fall** — der Tor-Grund,
den der Term per Konstruktion unterdrückt. Das Gate zählt also dieselbe
Statistik, die der Term bestraft; sein „Mehr-Ertrag" ist dieselbe Zirkularität
wie beim verworfenen Nutzenkriterium, eine Ebene höher. Die Verteilung der
Ablehnungsgründe sagt es direkt:

| Gewicht | `ok` | `anchor_spike` | `not_converged_local` | `connector_degenerate` |
|---|---|---|---|---|
| 0 | 209 | 22 | 21 | 20 |
| 1,0 | 217 | **3** | **31** | 24 |
| 3,2 | 218 | 3 | 31 | 22 |

Der Term tauscht einen Ablehnungsgrund gegen einen anderen: `anchor_spike`
22 → 3, `not_converged_local` 21 → 31. Die **Konvergenz wird echt schlechter**,
und das ist kein Etikett, das der Term kontrolliert.

### Was daran gelungen ist

§11 Korrektur 1 hat sich vollständig bezahlt gemacht. Wäre — wie §11
ursprünglich vorsah — auf `anchor_spike_ratio` und „Gate-Ablehnungen unter 23"
gemessen worden, hätte dieser Term auf **jeder** Sprosse glänzend bestanden:
Spike-Median −45 %, Ablehnungen 68 → 59, McNemar signifikant. Genau die Zahlen,
die eine Übernahme getragen hätten. Das eine Maß, das nicht in der
Zielfunktion steht und nicht im Gate zählt — der Abstand des gespeicherten
Ankers zur Tinte — ist das einzige, das die Wahrheit sagt.

Das ist der Lehrsatz aus §10 („bestätigt" und „brauchbar" sind zwei Fragen) in
seiner härtesten Form: **eine Kennzahl, die der Eingriff selbst bestraft, kann
seinen Erfolg nicht bezeugen.**

### Die Bilanz für `A` („Einzelner Ausreißer")

* **Biegeterm** (§7) — verworfen, bepreiste globale Krümmung statt der Unstetigkeit.
* **Scharnier** (§8) — verworfen, bepreiste den Abstand.
* **Sample-Stützung der Eckanker-Klasse** (§10) — Diagnose hält der nicht-zirkulären Prüfung nicht stand.
* **Nachbarbindung** (§11–§11d) — **verworfen**: wirkt, senkt die eigene Zielstatistik um 58 %, und macht die Ankerlage zur Tinte um 18 % schlechter, während sie die Konvergenz kostet.
* **Das Gate** bleibt die Rückfalllinie, die aussortiert statt zu reparieren.

Vier Wege zu, alle gemessen. Was übrig bleibt, ist kein fünfter Term, sondern
die **Ursache** aus §11a: der Deckungsterm ist blind dafür, welches Segment
einen Skelettpunkt besitzt, und zieht deshalb den nächstbesten Anker heran.
Ein Term, der an der Steifigkeit ansetzt, kann das nicht heilen — dieser Lauf
ist der Beleg, nicht mehr die Vermutung.

### Die Bestätigungsmenge bleibt unberührt

Kein Arm ist auf Abb. 20 gelaufen. Das Protokoll aus §11b sieht die
Bestätigung nur für ein Gewicht vor, das auf der Entwicklungsmenge **beide**
Kriterien besteht; keines tut das. Eine Rückhaltemenge für eine bereits
gescheiterte Hypothese auszugeben, würde sie für die nächste verbrennen —
sie steht der Untersuchung der Deckungs-Zuordnung unverbraucht zur Verfügung.

### Zustand im Code

`CHAIN_LETTER_BIND_WEIGHT` bleibt auf 0,0 und ist als gemessen-verworfen
gekennzeichnet. Der Zwilling `core.fit.DEFAULT_SMOOTH_WEIGHT` auf dem
Einzelbuchstaben-Pfad ist **nicht** geprüft worden — er steht auf demselben
Mechanismus, aber auf einer anderen Zielfunktion, und nach der Lehre aus §11c
wird das hier nicht wieder aus der Ferne übertragen. Er bleibt auf 0,0; wer ihn
anhebt, braucht sein eigenes A/B.

---

## 11e. Die Reparatur ist eingebaut (`aug11`)

Nach vier gemessen verworfenen Zielfunktions-Termen (§7 · §8 · §10 · §11d) ist
der Ausreißer-Anker jetzt dort behoben, wo er landet: **als protokollierte
Reparatur bei der Ernte** (`tools/pairlab/anchors.py::repair_stranded_anchors`,
verdrahtet in beide Speicherpfade von `tools/laufform/harvest.py`). Die
Abwägung hat der Eigentümer ausdrücklich getroffen (2026-08-10): ein
interpolierter Anker minimal neben der Linie ist der kleinere Defekt; der Peak,
der über den Per-Anker-Median die Laufform vergiftet, ist der, der weg muss.
Die drei Bedingungen, die §11 für eine legitime Reparatur festgelegt hat,
sind erfüllt:

1. **Protokolliert:** `measurements.repaired_anchors` nennt die ersetzten
   Anker; das Fehlen des Schlüssels heißt unberührt (per Golden-Test
   byte-identisch gepinnt). Das gespeicherte `anchor_spike_ratio` bleibt die
   UNreparierte Zahl.
2. **Das Gate urteilt über die unreparierte Geometrie.** Eine Reparatur ist
   eine Beinahe-Ablehnung, nie ein Bestehen — kein Schwellwert, kein Ertrag
   bewegt sich. Ebenso bleibt die Wortspur unrepariert: die Inspektionsebene
   zeigt, was der Fit wirklich getan hat, und `gradlab`/`bindab` messen weiter
   die rohe Geometrie.
3. **Interpolation, nie Snap.** Ein Snap muss an einer Kreuzung einen Ast
   wählen und wählt den falschen (die Fehlform des §8-Scharniers); die
   Interpolation der Nachbarn im eigenen Federzug hat keinen Ast zu wählen.
   Absetzen wird nie überbrückt, zusammenhängende geflaggte Läufe werden als
   ein Stück ersetzt.

Gemessen am benannten Arbeitssatz (`tools/pairlab/peaklab.py`, 35 Vorkommen,
davon 5 Kontrollwörter ohne bekannten Peak):

| | Wert |
|---|---|
| Vorkommen mit Einzelanker-Ausflug | 10 von 35 |
| davon in einem Kontrollwort | **0** — der Detektor feuert nur auf die Fehlerform |
| Spike-Verhältnis der Betroffenen | 7,09 → **3,00** |
| schlimmster Fall (`e` in „schießen") | 15,07 → 2,96 |
| nicht bewegt | 1 von 10 (`i` in „zwei": 7,79 → 7,89) |

Der eine Nicht-Beweger ist ehrlich mitzunehmen: dort hat der Ausflug nicht die
Ein-Anker-Form, die die Interpolation voraussetzt. Und die Grenze bleibt, wie
sie in §11d gezogen wurde: die Reparatur behebt die `A`-Klasse (Einzelner
Ausreißer), **nicht** die `B`-Klasse („Bereich daneben") — deren Kandidat ist
die Landmarken-Korrespondenz (Vorlagen-Kreuzung ↔ Skelett-Kreuzung), mit der
Abstandsmessung VOR dem Term, wie es §11a vorgemacht hat.

Sichtprüfung: `tools/fitview` (die bewerteten humanbench-Schirme, vorher/
nachher im Urteilsrahmen samt gesetzter Marker) und `tools/pairlab/peaklab`
(benannter Arbeitssatz, Ankerkette über der Tinte, Minuten je Runde).

**Urteil des Eigentümers am Bild** (2026-08-11, nach Sicht der Vorher/
Nachher-Überlagerung über den Arbeitssatz): *„ja die peaks sind so weg"*.
Damit ist die `A`-Klasse an der Stelle geschlossen, an der sie überhaupt
beurteilbar ist — am Bild, nicht an einer Kennzahl. Das ist die
Arbeitsform, die die vier verworfenen Terme nie hatten: eine kurze
Rechenrunde, ein Bild, ein menschliches Urteil.

**Was damit noch NICHT im Live-System ist.** Die Reparatur wirkt bei der
ERNTE. Bis sie das Geschriebene erreicht, führt der Weg über vier weitere
Stufen: Neu-Ernte → `instances` → `aggregates`-Rebuild → `apply-laufform`
→ Rendering. Erst die letzte Stufe ändert, was die Feder schreibt, und
genau sie ist die einzige, die eine bewusste Freigabe braucht
(`LAUFFORM_MIN_OCCURRENCES`, Archiv-Momentaufnahme davor). Solange diese
Kette nicht gelaufen ist, ist der Befund oben eine Aussage über die
MESSUNG, nicht über das Produkt — und die Klage „viel gelernt, im System
nichts verbessert" bleibt bis dahin berechtigt.

---

## 12. Die Autopsie der `d`-Tafelform (`aug10`)

§10 hatte den `B`-Befund („Bereich daneben") auf eine Glyphe eingegrenzt —
`d` trägt ihn in 5 von 7 beurteilten Vorkommen, die übrigen 13 `B`-Fälle
verteilen sich über zehn Glyphen — und daraus die Stufenzuordnung abgeleitet:
eine Aussage über die **Vorlage**, nicht über die Zielfunktion. Der dort
benannte nächste Schritt ist hier ausgeführt.

### Was gemessen wurde

Alle 18 `d`-Schirme beider Runden (14 verschiedene Identitäten aus
`glyph`/`word`/`slot`, dazu vier Blindwiederholungen), die 14 gespeicherten
`instances`-Zeilen dazu — sie decken sich 1 : 1, keine Lücke in beide
Richtungen — und die Tafelzeile selbst. Die 5/7 aus §10 ist exakt
reproduzierbar. Zwei Korrekturen an der Prosa dort: die 13 übrigen `B`-Fälle
verteilen sich zwar über zehn Glyphen, sind aber nicht durchweg Einzelstücke
(`n` 2/13, `o` 2/3, `v` 2/2).

**Beide Blindwiederholungen eines `B`-Schirms kamen wieder als `B` zurück** —
das Urteil ist an dieser Glyphe reproduzierbar und kein Etikettierungszufall.

### Die Form der Abweichung: nicht starr, nicht affin

Je Vorkommen die Abweichung der gefitteten gegen die Tafelform, nacheinander
bereinigt um die beste Verschiebung (T), eine gleichförmige Skalierung (S) und
eine volle affine Abbildung (A — Skalierung, Drehung, Scherung/Schräglage
zusammen). Rest-RMS in xh:

| Gruppe | roh | −T | −S | −A | T erklärt | A erklärt |
|---|---|---|---|---|---|---|
| alle 14 | 0,052 | 0,052 | 0,051 | 0,046 | **0,6 %** | 10,6 % |
| `B`-Zeilen (8) | 0,059 | 0,059 | 0,058 | 0,053 | **0,7 %** | 10,3 % |
| ohne `B` (6) | 0,042 | 0,042 | 0,041 | 0,038 | 0,2 % | 11,1 % |

Die starre Verschiebung holt 0,6 % heraus — eine **unabhängige Bestätigung**
der 0 % aus §10, gemessen gegen eine andere Referenz (Tafelform statt Tinte).
Die volle affine Abbildung kommt auf 10,6 %: **rund 89 % der Abweichung sind
nicht-affin**, und affin erklärt in den `B`-Zeilen (10,3 %) genauso viel wie in
den sauberen (11,1 %) — es ist also nicht das, was sie unterscheidet. Es ist
eine **örtliche Umformung**, und zwar in genau einem Stück Duktus.

### Wo: Schlingenschluss und Auslauf, nicht die Schale

Mittlerer Betrag der Verschiebung je Ankerbereich (xh, ein einziger Federzug,
`stroke_starts == [0]`, kein Bereich überspringt ein Absetzen):

| Anker | Duktus-Teil | alle | `B` | ohne `B` |
|---|---|---|---|---|
| 0–19 | Anstrich + Scheitel (Ecke @12) | 0,043 | 0,049 | 0,036 |
| 20–49 | Abstrich + Schale | 0,031 | 0,033 | 0,032 |
| 50–69 | Oberlänge | 0,032 | 0,034 | 0,028 |
| 70–89 | Schlingenkopf | 0,044 | 0,053 | 0,033 |
| 90–109 | Schlingenabstieg + Schluss | 0,047 | 0,053 | 0,037 |
| **110–119** | **Auslauf** | **0,067** | **0,088** | 0,039 |

**Die Schale ist unauffällig** (0,033 gegen 0,032 — in `B`- und sauberen
Zeilen identisch). Die untere Hälfte der `d` stimmt; die obere ist zu breit.
Im Vorzeichen gelesen: um Anker 84–95 liegt die Tinte **rechts** der
Tafelform (die Schlinge baucht zu weit nach links aus), um 110–119 **links**
(der Auslauf reicht zu weit nach rechts). Zwei Flanken, die nach innen ziehen —
die Spannweite von Schlinge + Auslauf schrumpft von 1,103 auf ~0,838 Einheiten,
**−24 %**.

### Die nicht-zirkuläre Gegenprobe

§9/§10 haben eine Ortsaussage schon einmal als zirkulär zurückgezogen (sie kam
aus dem Maximum des eigenen Detektors). Hier ist die Gegenprobe unabhängig: die
vom Menschen **freiwillig gesetzten Marker** wurden in den Bildrahmen
zurückgerechnet, den `tools/humanbench/build.py` aufbaut, und auf den
gezeichneten Linienzug projiziert. **8 der 10 Marker auf `B`-Schirmen liegen
bei Anker 92–118** (Median 108, also Schlingenschluss). Das menschliche „was
fällt zuerst auf" und das Maximum der Verschiebung treffen dieselbe Strecke —
aus zwei unverbundenen Messungen. Die beiden Ausnahmen sind beide `der`, Erst-
und Blindwiederholung unabhängig bei Anker 4–5: dort sitzt ein **zweiter,
eigener Defekt am Anstrich**.

### Der Auslauf hängt am Übergang — und das ist die eigentliche Aussage

| Gruppe | n | trägt `B` | Auslauf-Bogen 110–119 gegen Tafel |
|---|---|---|---|
| `d` mit Folgebuchstabe | 10 | **8** (die 2 übrigen: `K` unbeurteilbar, `E`) | −17 % … −33 %, Endpunkt 0,12–0,26 xh zurückgezogen |
| `d` am Wortende (`und…`) | 4 | **0** (G,G,G,W) | −0,3 % … +6,5 %, Endpunkt +0,004…+0,023 |

**10 von 10 verbundenen `d` kürzen den Auslauf, 0 von 4 unverbundenen.** Die
Tafelzelle trägt einen vollen isolierten Auslauf; im laufenden Wort gibt es den
nicht, und der Fit kämpft an genau der Stelle, die der Mensch markiert hat,
0,2 xh gegen die Vorlage. (`Soldaten` ist die eine Variante: dort wird der
Auslauf nicht verkürzt, sondern nach unten gedreht, Δy −0,247.)

Der Vergleich `geo_rmse_px` sagt dasselbe ohne jedes Urteil: verbundene `d`
1,06–1,73 (Mittel 1,44), Wortende-`d` 0,68–1,08 (Mittel 0,86).

### Warum die Autorenmetrik das nicht sieht

Die Tafelzeile `d` hat `trace_meta["quality"]` **85,82 — Rang 46 von 62**
bewerteten Variante-0-Zeilen, über dem Alphabet-Median 84,16. Abzüge:
Glattheit 0,138 · Deckung 0,137 · Natürlichkeit 0,077 · Vertikalität 0,060 ·
Ecke 0,006. **Die Nachzeichnung ist der Tafelzelle treu — die Tafelzelle ist
nur nicht die Laufform.** Ein bildraum-treues Maß über die isolierte Zelle kann
das nicht finden; es ist kein Fehler der Metrik, sondern ihre Zuständigkeit.

### Was daraus folgt — und was ausdrücklich nicht

* **`chart_ductus` für die Schlingenflanke.** Die zu weit links ausbauchende
  Schlinge ist in allen 14 Zeilen da, auch in den vier sauberen
  Wortende-`d` — also **nicht** übergangsbedingt. Das ist ein Fall für den
  Einrichtungs-Wizard (menschliche Nachzeichnung, Ground Truth), nicht für Code.
* **Der Auslauf ist KEIN „Laufform-Endpunkt nach links schieben".** Variante 100
  trägt die Korrektur bereits — ihr Auslaufanker liegt 0,174 xh links des
  Tafelankers, exakt der Median der 14 Vorkommen. Aber es ist ein Median über
  **zwei systematisch verschiedene Grundgesamtheiten**: die vier
  Wortende-`und` mit legitim vollem Auslauf ziehen ihn zur Mitte (allein über
  die 10 verbundenen Zeilen wären es −0,196). Eine Laufform kann konstruktiv
  nicht beides sein. Entweder braucht `d` eine **Variantentrennung**
  (verbunden / terminal), oder der Auslauf gehört überhaupt nicht in die
  Ankerkette des Buchstabens, sondern in den Übergangsgenerator. Das ist eine
  Modellfrage und gehört vor jede Zahl entschieden.
* **`core/fit.py` bleibt der falsche Ort.** §10s Stufenzuordnung hält der
  Autopsie stand.

### Grenzen dieses Befunds

* **Die Aufteilung verbunden/terminal ist post hoc.** Sie ist eine
  Nachschichtung derselben Etiketten, auf denen §10 gebaut ist, und die
  Rückhaltemenge des humanbench ist mit Runde 02 aufgebraucht — als
  *Urteils*aussage ist sie eine Hypothese, kein bestätigter Befund. Was
  unabhängig davon steht, ist die **Geometrie**: „10 von 10 verbundenen kürzen
  den Auslauf, 0 von 4 nicht" kommt aus den gespeicherten Fits und kennt die
  Etiketten nicht.
* **Der Schnitt Buchstabe/Verbinder ist nicht ausgeschlossen.** Die Anker
  110–119 könnten teilweise davon herrühren, wo die Kette den Buchstaben vom
  Verbinder trennt, statt von der Hand. Dagegen spricht, dass dort echte
  Verbindungstinte im Fenster liegt (die Anker sind an Tinte gefittet, nicht
  frei) und dass die Wortende-Gruppe ohne Schnitt und ohne Verbinder gar keine
  Auslaufabweichung zeigt — beide Lesarten sagen das aber gleichermaßen vorher.
  Trennen lässt sich das nur mit `tools/pairlab` an einem `d`-Übergang.
* **n = 14.** Eine Glyphe, eine Hand, eine Vorlage.

---

## 13. Die Kreuzung als Landmarke — und die Drift (`aug11`)

Zwei Messrunden zum Eigentümer-Modell: *ein Buchstabe hat eine feste
Struktur (Kringel, Kreuzung, Schale in fester Reihenfolge); was je Vorkommen
und je Übergang wandert, ist deren LAGE — die Kreuzung sitzt mal höher, mal
tiefer, und der Fit muss dem folgen. „Das Wirklich Richtige ist eigentlich
nur, dass man der schwarzen Linie der Tinte folgen muss."*

Beide Runden liefen mit adversarischer Gegenprüfung jeder tragenden
Behauptung. Die Bilanz der Gegenprüfung ist selbst ein Befund und steht
deshalb vorne:

| Runde | Behauptungen | widerlegt |
|---|---|---|
| Kreuzungs-Landmarke | 12 | **0** |
| Drift / Tinte-Start / Breiten | 9 | **9** |

### 13a. Die Kreuzung ist übergangsabhängig — und der Fit folgt ihr nicht

| | Tinten-Kreuzung `d` (Höhe, buchstabenlokal) |
|---|---|
| mit Folgebuchstaben (10 Vorkommen, 6 Wörter, 3 Nachfolger) | **0,968 xh** (MAD 0,013) |
| am Wortende (4) | **1,211 xh** (MAD 0,010) |
| Differenz | **0,243 xh**, exakter Permutationstest p = 0,005 |

Das ist **19× das Rauschen** aus Wiederholungen desselben Worts (0,013 xh).
Binär, nicht pro Nachfolger: vor `a` 0,971 · `e` 0,964 · `i` 0,982
(Kruskal p = 0,70). Im Plattenrahmen gemessen wird die Differenz 0,361 xh —
Richtung und Signifikanz sind rahmenunabhängig, die **Größe nicht**.

**Der Fit folgt dem nicht.** Dieselbe Aufteilung an der GEFITTETEN Kreuzung:
**0,011 xh**, p = 0,43 — also 5 % der nötigen Größe, bei r = −0,25 sogar
leicht falsch gerichtet. Die Tafel-Kreuzung wird auf 0,002 xh reproduziert:
eine starre Kopie. Die Laufform erbt sie ungefiltert (v0 1,176 → v100
1,177).

**Warum die Zielfunktion das nicht sehen kann.** Jeder gefittete Anker liegt
0,019–0,046 xh von der Tinte, also innerhalb eines Haarstrichs. Der
Landmarken-Fehler von 0,202 xh ist **6× der mittlere Ankerabstand** und
1,6× der schlechteste Einzelanker. Der Fit ist überall gut und die
STRUKTUR trotzdem falsch — kein Genauigkeitsproblem, ein
Zuordnungsproblem. Genau die Blindheit, die §11a am Deckungsterm beziffert
hat, eine Ebene höher.

**Die Landmarke ist verfügbar.** 26 von 34 eingefrorenen v0-Zeilen tragen
43 gut konditionierte Selbstkreuzungen (Winkel ≥ 15°, Bogenabstand
≥ 0,35 xh), stabil auf 0,015 xh über die v0→v100-Ableitung, unverstärkt
unter 0,03 xh glattem Rauschen — und `core.geometry.detect_crossing_passages`
findet **alle 43** bereits, robust über prox_px 2–24 px und 5–80°.
`trace_meta.crossing_anchors` ist auf dem Gleichzug-Pfad absichtlich leer:
es ist dort die Breiten-Kontaminationsliste von `_resolve_crossing_widths`,
keine Landmarkenliste. Es fehlt also **kein Detektor, sondern der
Zuordnungsterm**.

Und ein solcher Term wäre **kein fünfter Anlauf** der verworfenen vier: §7
(Biegeenergie), §8 (Scharnier), §10 (Eckanker), §11d (Nachbarbindung) haben
alle einen STELLVERTRETER bepreist — Krümmung, Abstand, Steifigkeit — auf
einer zuordnungsblinden Zielfunktion. Eine Landmarken-Korrespondenz ist ein
DATENterm: dieser Punkt gehört auf jenen Punkt.

**Nachtrag (`aug11`, gleicher Zweig): der Zuordnungsterm existiert jetzt.**
`tools/pairlab/landmarks.py` trägt den geteilten Detektor (Selbstkreuzungen
der Ankerlinie + Skelett-Verzweigungspunkte, eine nicht entscheidbare
Zuordnung wird verworfen statt geraten), und `tools/pairlab/chain.py` preist
die Korrespondenz als Energieterm — `landmark` ist in `GRADIENT_TERMS`
aufgenommen, die Zerlegungsprobe deckt ihn also mit ab. Ausgeliefert ist er
**bewusst inert**: `CHAIN_LANDMARK_WEIGHT` steht auf 0,0 und ist dort
byte-identisch zur Abwesenheit des Terms (per Test festgenagelt). Die
Kalibrierung ist offen — die Sonde dafür ist `tools/pairlab/landmarklab.py`,
und aus dem 14-Vorkommen-Set eines einzigen Buchstabens wird hier absichtlich
kein Standardgewicht vorgeschlagen.

**Grenzen, die bleiben.** Der Effekt ist nicht allgemein: bei `a`, `l`, `r`,
`h` ist die Kreuzung *nicht* übergangsabhängig (p = 0,67–0,75) — er tritt
auf, wo die Kreuzung auf dem AUSLAUFweg liegt (beim `d` Anker 59/110, und
110–119 ist der in §12 als zu lang gemessene Auslauf: dieselbe Region, zwei
Symptome). Der Wortende-Arm sind 4 Vorkommen **eines** Worts („und"). Und
die Zuordnung Lücke ↔ menschliches `B`-Urteil ist NICHT sauber (AUC 0,88;
innerhalb der verbundenen Gruppe trennt sie die Labels gar nicht).
Gesichert ist: *die Lücke ist eine Eigenschaft des Übergangs* — nicht, dass
sie `B` erklärt.

Eine ungeprüfte Hypothese, die vor dem Bau eine Gegenprobe verdient: der
Überlappungsterm (`CHAIN_OVERLAP_RADIUS_UNITS` 0,15) verbietet dem
Buchstabenschwanz, auf den Samples des Verbinders zu liegen — und das ist
genau die Tinte, die der Schwanz besetzen müsste, um die Kreuzung
herunterzubringen. Möglicherweise ist die Bremse selbstgebaut.

### 13b. Die Drift: Befund bestätigt, mein Mechanismus war falsch

Reproduziert und unbestritten: die Platzierungskorrektur, die jeder
Buchstabe nach seiner eigenen Tinte braucht, wächst über das Wort —
`und` (3 Buchstaben) −0,10 xh, `laden` (5) **−0,48**, `unter` (5) −0,55,
`schießen` (8) −0,59, wobei dort die letzten DREI Buchstaben auf −0,594
stehen, dem Suchlimit. Gepoolt über 63 Wörter / 214 Schritte: Median
**−0,062 xh**, 61 % brauchen einen Linkszug. Zwei Buchstaben halten der
Bootstrap-Prüfung stand: `t` −0,323 (n = 6, KI [−0,422; −0,258]) und
`e` −0,097 (n = 38, KI [−0,161; −0,065]). Bei `i`, `n`, `w` schrammt das
Konfidenzintervall an der Null; 17 Glyphen haben n ≤ 4 und tragen keine
Zahl.

**Widerlegt — und die Korrektur gehört hierher, nicht in eine Fußnote:**
„die Vorschubbreiten sind zu groß" war als Mechanismus **falsch**.
`templates.advance` wird auf dem Schreibpfad für einen verbundenen
Buchstaben **nie gelesen** (`core/compose.py` kennt nur `SPACE_ADV` und
`MISSING_ADV`); der Schritt entsteht aus `prev.exit[0]` plus den
Join-Klassen-Zweigen. Es gibt also keine „komponierte Vorschubbreite", die
man korrigieren könnte — das ERGEBNIS (zu weite Setzung) stimmt, die
Ursache liegt in den Platzierungsregeln. Damit ist auch „einfach die
Laufform-Breiten nehmen" keine Option: das Feld wird nicht konsumiert, und
die Richtung wäre ohnehin falsch (Laufform-Breiten im Median +3 % weiter,
während 60 % der Schritte nach links müssen). Welcher Anteil auf die LÜCKE
und welcher auf die BUCHSTABENBREITE geht, ist offen — die Zerlegung wurde
in der Gegenprüfung ebenfalls gebrochen.

**Der Tinte-Start ist kein neuer Gedanke.** `chain_seed="grid"` ist
vorhanden, und das A/B dazu ist am 2026-08-05 vorregistriert gelaufen
(`uebergaenge-befund.md` §5c „Grid-Seed-A/B", angenommen 241 → 241) mit dem
Ergebnis: Standard bleibt `composed`. Die Wiederholung auf 12 Wörtern
bestätigt die Form (Gate 39 → 37, McNemar p = 0,754, gepaarte
Geometrieänderung −0,01 %); der Keim tauscht Ablehnungsgründe
(`not_converged_local` −2, `geo_rmse` −1 gegen `connector_degenerate` +3).
Zwei Dinge halten die Frage trotzdem offen, und beide sind Code-Fakten:
`harvest.py:933` hält den Keim für `at_bound`-Buchstaben ZURÜCK — also
genau für die abgedrifteten —, und die Gegenprüfung fand im Arm-Aufbau
jenes A/B einen Vorzeichen-/Rahmenfehler. Wo die Drift groß ist, wirkt der
Keim messbar (`fechten` n 5,208 → 0,910 px mit Konvergenz-Kipper;
„festsitzend" 5/20 → 0/20). Das trägt eine **gezielte Rettung**, nicht
einen neuen Standard — und es braucht ein eigenes, saubereres A/B.

Eine Formulierung ist zurückzunehmen: „der Fit bewegt den Buchstaben nie"
ist zu stark. Liest man nur den Slot-Block, realisiert der komponierte Arm
0,342 der geforderten Verschiebung; mit der globalen Wortverschiebung
zusammen 0,922. Die Wortverschiebung schluckt den Großteil der Drift —
was bleibt, ist die Verteilung INNERHALB des Worts.

---

## 14. Tintenfolger-Bench (`tracebench`): der nachgefahrene Referenzsatz als Maßstab (`aug14`)

Vorregistrierung VOR der ersten Zahl (die §11b-Praxis): Definitionen,
Split, Kriterien und Kill-Kriterien stehen hier, BEVOR irgendein
Kandidat gemessen wurde. Plan und Begründungen:
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md); die
Werkzeuge: `tools/tracebench/`.

### Was gemessen wird — und in welchem Rahmen

Ein **Kandidat** ist eine automatische Wortbahn über einem Specimen-Crop
(wörtlich eine `word_instances`-Zeile: Strokes + Registrierung + xh);
der **Maßstab** ist die manuell per S-Pen nachgefahrene `authored`-Bahn
desselben Specimens. Verglichen wird NIE in den gespeicherten
`(u,v)`-Labels (die Registrierung ist Composer-Buchhaltung): jede Bahn
wird über ihre EIGENE Registrierung nach Crop-px und von dort in den
**Bench-Frame** gemappt (`xh = baseline_y − midband_y`, Grundlinie =
`baseline_y − rect[1]` aus der eingefrorenen `word.json`) — der Frame
hängt damit nur an committeten Daten, ein veralteter Export kann das
Lineal nicht korrumpieren.

### Die Maße (Definitionen verbatim; keine referenziert publizierte Zahlen)

- **`dtw_xh`** — unconstrained DTW, euklidische Punktdistanz in xh
  (nicht quadriert), symmetric-1-Schritte, beide Enden verankert, kein
  Band; **normalisiert durch die Länge T des optimalen Warping-Pfads**
  (die LDTW-Normalisierung aus PEN-Net Eq. 1). Beide Seiten vorher
  arc-length-uniform resampelt (`TRACE_RESAMPLE_UNITS`; Startwert 0,02
  xh, einmaliger dokumentierter Schrittweiten-Sweep 0,02/0,03/0,05 im
  Baseline-Lauf). **Nur vorwärts** — die Richtung ist Duktus-Wahrheit;
  `dtw_reversed_better` (Kandidat rückwärts besser?) ist eine reine
  Report-Spalte. QC-Spalte `dtw_max_absorption` (max. Punkte einer
  Seite auf EIN Sample der anderen — der Singularitäts-Wächter der
  Konkatenation). EIGENER Name, bewusst nicht „LDTW": Resampling und
  xh-Einheit machen die Zahl mit publizierten Werten unvergleichbar.
- **`aiou`** — papertreu nach PEN-Net §3.1, gegen die eingefrorene
  **Tintenmaske** (`ref_mask.png`), nie gegen eine Referenzbahn:
  Kandidat 1 px gerastert (Pen-Lifts nie überbrückt), 3×3-Dilatation
  iterativ, `max_k IoU(ink, dilate^k(cand))`. Funktioniert deshalb auf
  allen Wörtern ohne Nachfahrung; Raster = Crop-px (mitreportet).
- **Chamfer, beide Richtungen getrennt** — `chamfer_cand_ref_xh`
  (Precision: liegt der Kandidat auf der menschlichen Bahn) und
  `chamfer_ref_cand_xh` (Recall: deckt er alles ab — ein fehlender
  i-Punkt bläht NUR diese Hälfte). Kein symmetrisches Mittel.
- **Strich-Behandlung** — Marken (nicht-erster Strich, komplett über
  `DIACRITIC_MIN_Y`, Bogen ≤ 0,8 xh: i-Punkt/-Strich, Umlaut,
  u-Deckstrich) werden VOR dem Body-DTW herausgelöst
  (Delayed-Strokes-Praxis; entschärft zugleich die Ordnungsfalle der
  deferred Diakritika der Engine) und per Zentroid mit Refusal
  gematcht (Radius 0,6 xh, Margin 0,25 xh). Body beider Seiten in
  Schreibreihenfolge konkateniert; Pen-Lifts bleiben AUSSERHALB der
  DTW-Kosten → `lift_delta`, `lift_pos_err_xh`.
- **Fehlerzähler** (je: ref/cand/matched/missing/spurious/ambiguous +
  Median-Positionsfehler): **Kreuzungen**
  (`landmarks.landmark_crossings`, Schwellen UNVERÄNDERT aus dem
  §13a-Zensus; Match 0,55 xh als Eins-zu-eins-Assignment über beide
  POPULATIONEN — die Refusal-Marge gehört allein den Marken, deren
  Einzelziel-Rahmen sie gebaut wurde; präzisiert nach dem ersten
  Identitätslauf, s. Baseline unten), **Marken** (s. o., Match mit
  Refusal 0,6/0,25 xh), **Retraces**
  (`core.geometry.detect_retrace_pairs`, prox 0,15 xh, ≥ 3 Paare;
  Zonen-Matching wie Kreuzungen; robusteste Zahl `retrace_arc_ratio`).
- **Validierung ohne Referenz-Implementierung:** Es existiert weltweit
  keine (PEN-Net-Repo: nur Training; TRACE: kein Repo) — die
  Unit-Tests kalibrieren gegen synthetische Verzerrungen nach PEN-Nets
  eigenem Fig.-1-Rezept (halbe Punkte um festen Betrag verschoben:
  AIoU muss deutlich fallen, wo RMSE konstruktionsbedingt flach
  bleibt).

### Split (append-never)

`TRACEBENCH_DEV_IDS` = **die · laden · linken · mit · muß · und ·
unter · Wer · will · zwei** (die 10 am 2026-08-13 nachgefahrenen
Wörter) — committete Konstante. Jedes SPÄTER nachgefahrene Wort ist
per Definition Bestätigungsmaterial und wandert NIE in den Dev-Satz
(eine nach den Zahlen umdefinierbare Rückhaltemenge ist keine).
`--split confirm` verweigert unter 5 Wörtern; Startup-Assertion: jede
Dev-Id muss als authored, nicht-`frame_stale` Zeile im Artefakt sein —
sonst harter Fehler (das Lineal hat ein Wort verloren). Benannte
Abdeckungslücke des Dev-Satzes: kein Umlaut, kein langes ſ, ein
einziger Versal — erster Punkt des Bestätigungs-Briefs.

### Kriterien (relativ, gepaart je Wort gegen die Chain-Baseline)

| Rolle | Größe | Schwelle |
|---|---|---|
| Primär (Nutzen) | `dtw_xh`, Median der gepaarten Differenzen | ≥ 20 % relativer Fall |
| Co-Primär (Gate) | `marks_missing` gesamt | kein Netto-Anstieg |
| Co-Primär (Gate) | `cross_missing + cross_spurious` gesamt | kein Netto-Anstieg |
| Kosten | p90 der gepaarten `dtw_xh`-Differenzen | ≤ +10 % |
| Kosten | `aiou`-Median · `chamfer_ref_cand`-Median | fällt nicht |
| Kosten | `retrace_arc_ratio`-Abstand zu 1,0 | wächst nicht |
| Sanity | `dtw_reversed_better` | 0 |
| Sanity | failed/skipped-Wörter | kein Netto-Anstieg |

Bei n = 10 ist der Median der gepaarten Differenzen die ehrliche
Statistik; ein Sign-Test wird berichtet, nie als Gate gelesen. **Ein
Strukturdefekt (verlorene Marke, verlorene/erfundene Kreuzung,
kollabierter Deckstrich, doppelter Strich) vetot jeden
Distanzgewinn.**

### Kill-Kriterien

- Geometrie besser, aber Marken/Kreuzungen verloren → die Änderung ist
  verworfen, nicht nachgestimmt (Struktur schlägt Distanz).
- Ein Gewinn überlebt den Bestätigungssatz nicht → verworfen (§11b
  wörtlich).
- `authored` vs. `authored` ist keine exakte Identität (dtw = 0, alle
  Zähler matched) → das LINEAL ist kaputt; keine Kandidaten-Zahl wird
  gelesen, bis es repariert ist.

### Freeze-Deklaration

Mit dem Commit der ersten Baseline-Tabelle friert das Lineal:
`tools/tracebench/{metric,frames,counters,sets}.py`,
`tools/pairlab/landmarks.py`, `core/geometry.py`,
`core/quality_suetterlin.py` (der Retrace-Zähler importiert dessen
`MIN_RETRACE_PAIRS`) und die Fixture-Roots. Jede spätere Änderung an einem davon ist eine datierte
Re-Baseline (wordbench UND tracebench — die Roots sind geteilt).
VOR diesem Commit sind Lineal-Bugfixes frei: ein kaputter Frame beim
ersten Lauf ist Debugging, kein p-Hacking — der Unterschied ist HIER
festgehalten, nicht hinterher.

### Was der Bench nicht beantwortet

Einen historisch falschen, aber glatten Duktus sieht kein Bahnmaß
(bildsynthese-und-stiftbahn.md §7); das Endkriterium bleibt der blinde
Paarvergleich nach humanbench-Methode (Folger ununterscheidbar vom
manuellen Nachfahren) — mit dem benannten Bias, dass der Autor eigene
Nachfahrungen beurteilt (Abkühl-Abstand oder Zweitrichter).

### Baseline `aug14` — der Kettenfit gegen die Hand (Freeze-Akt)

**Vorspiel, wie §14 es vorsah:** Der erste `--candidate authored`-Lauf
schlug an — auf `unter`/`mit`/`linken` verweigerte der Kreuzungs-Matcher
die IDENTITÄT (je 2 missing/spurious/ambiguous), weil zwei ECHTE
Kreuzungen dieser Wörter näher als die 0,20-xh-Refusal-Marge beieinander
liegen und `nearest_unique_point` dann selbst bei Distanz 0 verweigert.
Diagnose: Die Marge gehört dem Einzelziel-Rahmen der Landmarken („dieser
Duktuspunkt → WELCHER Ast"); Kreuzungs- und Retrace-Zählung sind ein
anderer Rahmen — beide Seiten tragen die Population DESSELBEN Detektors,
und zwei Strukturen eine Strichbreite auseinander sind zwei Strukturen,
keine Ambiguität. Reparatur (im vorregistrierten freien Fenster VOR der
ersten Baseline): `frames.match_points_one_to_one` — greedy nach
aufsteigender Distanz, Radius-Cap 0,55 xh, eins-zu-eins; Marken behalten
die Refusal-Semantik. Danach: **Identitäts-Gate PASS** (dtw 0, beide
Chamfer 0, alle Zähler voll gematcht, `direction_uncertain` 0 — die 10
Nachfahrungen stimmen überall mit der Duktus-Richtung des Priors
überein).

**Fixture-Qualitätsbefund `marks_uncertain` (4/10):** `zwei`, `und`,
`unter`, `muß` — die Slots erwarten eine Marke (i-Strich bzw.
u-Deckstrich), die authored-Bahn trägt keinen eigenen schwebenden
Strich: der Autor hat die Marke verbunden gezeichnet bzw. unterhalb der
Diakritika-Schwelle angesetzt. Kein Kandidatenfehler; ihre Marken-Zähler
sind flag-markiert. Für den Bestätigungssatz gilt der Hinweis: Marken
mit eigenem Absetzen zeichnen, wie die Tafel es tut.

**Die erste Baseline** (`--candidate chain --split dev`, Schritt 0,02,
446 s, 10/10 gescort, 0 failed):

```
dtw_xh_median:   0.061985    aiou_median:              0.6831
dtw_xh_p90:      0.261818    chamfer_cand_ref_median:  0.0398
dtw_xh_worst:    unter 0.4389 chamfer_ref_cand_median: 0.0467
marks_missing:   0  (+1 spurious)
cross_missing:   7   cross_spurious:   19
retrace_missing: 4   retrace_spurious: 21
retrace_arc_ratio_median: 1.513
lift_delta_total: 3  dtw_reversed_better: 0  dtw_max_absorption_max: 132
```

Je Wort (dtw · aiou · cross m/s · retrace-Ratio): unter **0,439** ·
0,676 · 0/7 · 1,51 — laden 0,075 · 0,686 · 0/8 · 1,75 — muß **0,242** ·
0,680 · 2/0 · 0,24 — zwei 0,076 · 0,602 · 2/1 · 1,86 — die 0,077 ·
0,622 · 0/3 · 1,71 — mit 0,042 · 0,756 · 1/0 · 0,53 — und 0,049 ·
0,696 · 0/0 · — — linken 0,049 · 0,745 · 1/0 · 1,03 — Wer 0,044 ·
0,675 · 1/0 · 0,80 — will 0,045 · 0,755 · 0/0 · 2,15.

**Lesart — die vorregistrierte Erwartung in Zahlen:** Die Punktdistanz
ist meist ordentlich (Median 0,062 xh); die Beschwerde sitzt in der
STRUKTUR. Die Kette erfindet 19 Kreuzungen und 21 Retrace-Zonen, die
die Hand nicht schreibt, und retraced 51 % mehr Bogen als der Autor
(`retrace_arc_ratio` 1,51) — Kollaps-Doppelungen und
Verbinder-Schleifen, nicht Mess-Rauschen. Zwei Wörter tragen den p90:
`unter` 0,439 (der bekannte Kollaps-Probefall, `dtw_max_absorption`
132 — die Singularitäts-Wache zeigt genau dorthin) und `muß` 0,242
(ß-Schleife, dazu 2 verlorene Kreuzungen). Das sind die Ziele der
Folger-Arme (①–⑧): Struktur zuerst, Distanz als Wächter.

**Schrittweiten-Sweep (einmalig, dokumentiert):** 0,02 → 0,03 → 0,05
bewegt `dtw_xh` nur 0,0620 → 0,0631 → 0,0650 (+5 %) und `aiou` gar
nicht; die Kreuzungszähler wackeln um ±2; das Retrace-Bogen-Maß hängt
dagegen klar am Schritt (1,51 → 1,37 → 1,17 — gröbere Abtastung
verschluckt schmale Zonen über die ≥-3-Samples-Schwelle). **0,02 bleibt
der gepinnte Schritt** — fein genug fürs Strukturmaß, und die Laufzeit
(447 s vs. 387 s über 10 Wörter) kauft nichts, was die Vergleichbarkeit
wert wäre.

**Hiermit friert das Lineal** (die Freeze-Deklaration oben ist aktiv):
Metrik-Module, `landmarks.py`, `core/geometry.py`,
`core/quality_suetterlin.py`, Fixture-Roots. Jede spätere Änderung ist
eine datierte Re-Baseline. Artefakte des Laufs:
`temp/tracebench-baseline-chain.{json,csv}` (gitignoriert), Kommandos in
`tools/tracebench/README.md`.

### Vorregistrierung der Folger-Arme (`aug14`, VOR dem ersten Sweep)

Das Experiment-Protokoll für die Verfeinerungsstufe
(`tools/pairlab/follow.py`,
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §3),
festgehalten
BEVOR irgendein Arm gelaufen ist. Es gilt die Ein-Knopf-Regel (§11c/§11d:
dieses Projekt lernt nur aus Ein-Faktor-Leitern) und die §14-Kriterien
oben — gepaart je Wort gegen die eingefrorene `aug14`-Chain-Baseline,
**ein Strukturdefekt vetot jeden Distanzgewinn**, Adoption erst nach dem
Bestätigungssatz.

**Framing (damit das Experiment sich nicht selbst falsch liest):** Die
Baseline zeigt die Beschwerde in der STRUKTUR (19 erfundene Kreuzungen,
21 erfundene Retrace-Zonen, Bogen-Verhältnis 1,51) und in zwei
Kollaps-Wörtern (`unter` 0,439 · `muß` 0,242); die Fläche der
Punktdistanz ist eng (Median 0,062). Erwartete Gewinne sitzen in den
Ausreißern und den Struktur-Zählern; ein Arm, der nur den Median poliert
und Struktur verliert, ist per Veto tot.

**Reihenfolge der Arme** (v1 ändert genau EINE Sache: reg → prox):

| # | Knopf | Stufen | Pflicht-Kostenspalten |
|---|---|---|---|
| ① | λ_prox | {0 · 1 % · 10 % · 50 % von e_geo am Solve-1-Optimum (gradlab-Zerlegung) · Chain-Kontrolle} | Zick-Zack-Sichtung, stranded_anchors |
| ② | rounds | 1 / 2 / until-still (+ absteigende λ-Schedule als Unterarm) | Rundenprotokoll (Motion je Runde) |
| ③ | samples/Anker | 1,5 / 2,5 / 4 | Laufzeit |
| ④ | coverage | 0,3 / 0,6 / 1,0 | **stranded_anchors** (§11a: 32× anti-aligned — Reg-Release nimmt die Bremse) |
| ⑤ | overlap | 0,2 / 0 | §13a-Kreuzungshöhen-Statistik auf die/laden/und (§13-Bremse-Hypothese) |
| ⑥ | landmark | 0 / kalibriert, Ziele = extrapolierte Schnittpunkte (nie rohe Branch-Points) | Drop-Reasons der Korrespondenz |
| ⑦ | width | Term wie Chain / als Modulator des Ridge-Pulls | Width-Residual auf Hochkrümmungs-Samples |
| ⑧ | bind | 0 / kalibriert — NUR falls Zick-Zack λ_prox überlebt | §11d-Statistik in der Trace-Währung neu messen (Pflicht) |

**Erwartete Fehlermodi je Wort** (benannt, damit ein Negativ lesbar ist):
`unter` Stapel-Kollaps (max_absorption 132) · `laden` eingefrorene
Kreuzungshöhe (+8 spurious) · `muß` ß-Schleifen-Refusal (2 verlorene
Kreuzungen) · `Wer` Retrace-Prefix ins Leere · `die`/`mit`/`will`/
`linken` i-Marken-Attribution · `mit`/`unter` kollabierter t-Deckstrich ·
`zwei` Grat-Reiten (Width-Residual-Spalte) · `will` Retrace-Ratio 2,15.

**Kill-Kriterien der Formulierung**
([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §3):
bestes kalibriertes Setting verliert den gepaarten Sign-Test oder ist
auf > 2/10 Wörtern schlechter ODER erzeugt einen neuen Strukturdefekt
auf ≥ 2 Wörtern → Formulierung verworfen, nicht nachgestimmt. λ_prox = 0
≈ bestes λ_prox → die Release-Prämisse ist widerlegt; das ehrliche
Negativ kommt hierher, und die nächste Hypothese ist die
Attributions-/Sampling-Schicht, nicht mehr Gewichts-Tuning.
stranded_anchors über der Chain-Baseline → der Arm fällt, unabhängig von
jeder anderen Zahl.

**Was ein Arm-Lauf abliefert:** die `--compare`-Paartabelle gegen
`temp/tracebench-baseline-chain.json`, die Kostenspalten des Arms, und
einen datierten Eintrag HIER — auch (gerade) bei einem Negativ.

### Arm ① `aug14` — die λ_prox-Leiter: Formulierung v1 verworfen, der Tinten-Zug validiert

Erster Lauf des vorregistrierten Protokolls — mit EINER benannten
Abweichung in der Sprossen-Wahl: Die Vorregistrierung wollte λ so
kalibrieren, dass e_prox ≈ {1 %, 10 %, 50 %} von e_geo AM
Solve-1-Optimum liegt; an einem Restart ist das aber schlecht
definiert, weil e_prox(x0) dort per Konstruktion 0 ist (δ = 0) und der
Zielwert erst am unbekannten Folger-Optimum entsteht. Gefahren wurde
deshalb die Dekaden-Leiter **{0 · 0,01 · 0,1 · 1,0} × Chain-λ** und je
Sprosse das REALISIERTE Verhältnis am Ende gelesen — die
§11c-konforme Lesart (am Optimum messen statt per Analogie wählen),
als Abweichung hier festgehalten statt wegdefiniert. Rounds 2, alles
andere Chain-Default; je Sprosse `--compare` gepaart gegen die
eingefrorene `aug14`-Baseline; Artefakte je Sprosse in der Chronik.

| λ_prox | `dtw_xh` Δmed (gepaart) | Sign | `aiou` | `cross_missing`+`spurious` | `retrace_arc_ratio` |
|---|---|---|---|---|---|
| Chain (Referenz) | — | — | 0,683 | 7+19 = 26 | 1,51 |
| 0,0 | +0,0001 | 6/4 p=0,75 | **0,784** | 8+43 = **51** | **3,04** |
| 0,01 | +0,00001 | 5/5 p=1,0 | 0,782 | 9+57 = **66** | 2,58 |
| 0,1 | +0,00002 | 5/5 p=1,0 | 0,778 | 10+52 = **62** | 2,55 |
| 1,0 | −0,0008 (−1,5 %) | 3/7 p=0,34 | 0,777 | 10+33 = **43** | 2,09 |

**Verdikt nach den vorregistrierten Kriterien — verworfen, nicht
nachgestimmt:** Jede Sprosse reißt das Co-Primär-Gate (Netto-Anstieg
`cross_missing + cross_spurious`, 26 → 43–66), und das Primärkriterium
(≥ 20 % dtw-Fall) ist mit bestenfalls −1,5 % nirgends in Sicht. Die
beiden Kollaps-Wörter heilen nicht (`unter` 0,439 → 0,417, `muß`
0,242 → 0,236). Marken bleiben überall vollständig (0 missing),
`dtw_reversed_better` überall 0.

**Was der Arm POSITIV bewiesen hat:** Der Tinten-Zug wirkt — AIoU
steigt auf JEDER Sprosse um ~+0,10 (0,683 → 0,777–0,784): punktweise
schmiegt sich die freigelassene Bahn deutlich enger an die Tinte. Der
Preis ist erfundene STRUKTUR (Zick-Zack-Kreuzungen, verdoppelte
Züge) — die dokumentierte Degenerierung, jetzt beziffert, und schon
1 % Chain-λ ist keine Bremse (66 statt 51 bei λ=0 liegt im Rauschen
der Zonen-Zerlegung).

**Prämissen-Lesart (die λ=0-Probe):** λ=0 ist NICHT ≈ bestes λ — die
Struktur verschlechtert sich monoton mit fallendem λ. Die
Release-Prämisse ist damit in verschärfter Form bestätigt: Die
Form-Regularisierung hält nicht nur die Bahn von der Tinte fern,
sie ist derzeit auch das EINZIGE, was die Struktur zusammenhält.
Der vorregistrierte nächste Schritt gilt wörtlich: Die Struktur muss
aus den DATENTERMEN kommen — Arm ⑤ (Overlap-Hypothese §13) und vor
allem Arm ⑥ (Landmark-Term mit extrapolierten Schnittpunkt-Zielen),
BEVOR irgendeine weitere λ-Feinabstimmung sinnvoll ist. Kein Default
wird adoptiert; `FOLLOW_*` bleibt `provisional`.

### Arme ⑤ + ⑥ `aug14` — Overlap freigesprochen, die Korrespondenz-Kappe gefunden

**Arm ⑤ (Overlap {0,2 · 0}, ein Faktor gegen die λ=1,0-Schwester):** Die
§13-Hypothese „Overlap als selbstgebaute Bremse“ ist BEANTWORTET — der
Term ist es nicht. Ihn abzuschalten macht alles mild besser (isoliert:
dtw −0,2 %, Sign 6/8; Kreuzungen m+s 43 → 38, Retrace-Ratio
2,09 → 1,87), aber gegen die Chain-Baseline bleibt das Struktur-Veto
(26 → 38). Keine Adoption; der Freispruch des Terms ist der Befund.

**Arm ⑥ (Landmark 0 / kalibriert, extrapolierte vs. rohe Ziele):**
Zwei Vorstufen, beide gemessen statt geglaubt: (a) Die Kalibrierung
(Parität w = 0,507; Sprossen {0,005 · 0,051 · 0,507}) lief nach der
§11c-Disziplin am Optimum. (b) Die Extrapolation feuerte auf echter
Tinte zuerst 0/21 — Diagnose auf den realen Skeletten ergab drei
Mechanismen (euklidisches Annulus-Verschweißen der Schenkel; Thinning
spaltet eine Kreuzung in zwei Y-Junctions mit 1,2–1,7 Strichbreiten
Brücke; Sehnen- statt Krümmungstoleranz), Fix per geodätischem Walk +
krümmungs-abgeleiteter 35°-Toleranz → 8 der 9 verfeinerbaren
Junctions feuern (Verschiebungen 2,6–4,5 px, im publizierten
Junction-Bound). Messung dann: mittlere Sprosse isoliert NULL
(p = 1,0, ext ≡ raw im Rauschen); volle Parität punktweise SIGNIFIKANT
schlechter (dtw +0,9 %, Sign 8/9, p = 0,039) bei milder
Strukturlinderung (m+s 43 → 39, bester Folger-Wert — Veto vs. Baseline
26 bleibt). Keine Adoption, `FOLLOW_*` bleibt `provisional`.

**Der Befund, der beide Arme überragt — die Korrespondenz-Kappe:**
12 der 21 Landmark-Korrespondenzen der Dev-Wörter zeigen auf Tinte,
die GAR KEINE Kreuzung trägt (5 Touch-Points mit 2 Schenkeln, 7
T-Junctions mit 3) — die Bahn kreuzt sich dort, die Tinte nur berührt
sich. Solange die Korrespondenz diese Klassen nicht kennt, zieht jeder
Landmark-Zug an der Hälfte der Ziele in eine Struktur, die es nicht
gibt — das deckelt jeden möglichen Effekt und erklärt das
Voll-Paritäts-Ergebnis. **Nächste vorregistrierte Hypothese:
Klassenbewusstsein der Korrespondenz** (Touch-Points/T-Junctions gar
nicht erst als Kreuzungsziele; folger-seitig umsetzbar, die
eingefrorene `landmarks.py` bleibt unberührt) — NICHT mehr Gewicht,
nicht mehr λ-Feinabstimmung. Artefakte: Chronik `arm5-overlap` +
`arm6-landmark`.

### Arm ⑥b `aug14` — Vorregistrierung: Klassenbewusste Korrespondenz

Geschrieben und committet VOR der ersten Zahl dieses Arms (§11b-Disziplin).

**Hypothese (aus der Korrespondenz-Kappe des ⑤/⑥-Eintrags):** Die Kappe
ist die bindende Schranke des Landmark-Terms. Erwartung, falsifizierbar:
Mit klassenbewusster Korrespondenz — Touch-Points und T-Junctions tragen
Gewicht 0 — verschwindet die punktweise Verschlechterung der vollen
Parität (Arm ⑥: dtw +0,9 %, Sign 8/9, p = 0,039 gegen die
λ=1,0-Schwester), und die milde Strukturlinderung (m+s 43 → 39) bleibt
oder verbessert sich.

**Umsetzung (folger-seitig, das Lineal unberührt):** neuer Zielmodus
`extrapolated_classed` in `tools/pairlab/follow.py` — die extrapolierte
Zielbildung selbst unverändert, danach Gewicht 0 für jede Zeile, deren
Verfeinerungsgrund eine By-Design-Nichtkreuzung der Tinte ist
(`LANDMARK_NONCROSSING_REASONS` = `touch_point` · `t_junction`); die
1/σ²-Gewichte der behaltenen Zeilen werden über die BEHALTENEN auf
Mittel 1 renormiert. Gewicht 0 wirkt über das bestehende Pre-Whitening
(√w skaliert Operator-Zeile UND Ziel), also ohne jede Änderung an
`chain.py` oder der eingefrorenen `landmarks.py`. Die Walk-Fehlschläge
(`few_branches` · `no_continuation_pair` · `no_junction` ·
`ill_conditioned` · `far_from_branch`) behalten ihr rohes Ziel wie
bisher — dort KANN die Tinte eine Kreuzung tragen, nur die Verfeinerung
fand sie nicht.

**Protokoll:** Kalibrierung nach §11c am eigenen Optimum der
λ=1,0-Schwester (Term inert, classed-Parität gemessen — die Parität
ändert sich, weil `e_landmark` nur noch die behaltenen Zeilen zählt);
zwei Sprossen {0,1·Parität · Parität}, Basis identisch mit Arm ⑥
(prox 1 · rounds 2 · coverage 0,3). Gepaart über die 10 Dev-Wörter
gegen die λ=1,0-Schwester UND die eingefrorene Chain-Baseline;
Co-Primär-Gates, Kosten-Wächter und Struktur-Veto unverändert.

**Kill-Kriterien:** Bleibt die volle classed-Parität punktweise
signifikant schlechter als die Schwester → die Kappe war nicht die
bindende Schranke, Hypothese verworfen — und mit ihr die Gewichts-Route
des Landmark-Terms in dieser Formulierung (die nächste Hypothese wäre
dann die Korrespondenz-Bildung selbst, nicht ihr Gewicht). Steigen
`marks_missing` oder `cross_missing+spurious` netto gegen die
Schwester → verworfen. Keine Adoption eines `FOLLOW_*`-Defaults ohne
Owner-Go, unabhängig vom Ausgang.

### Arm ⑥b `aug15` — die Kappe WAR die Schranke: klassenbewusst ist der Term punktweise kostenlos, adoptiert wird trotzdem nichts

**Messung (Protokoll wie vorregistriert):** classed-Parität am inerten
Optimum 0,3704 (Kalibrierung §11c im eigenen Modus; der Zensus ist
exakt die Kappe: 8 ok · 1 `no_continuation_pair` · 7 `t_junction` · 5
`touch_point` = 12/21 klassifiziert raus — in den re-linearisierten
Runde-2-Problemen, deren Korrespondenz der frische Detektor-Lauf neu
bildet, 11/15). Sprossen {0,037 · 0,370}, Basis prox 1 · rounds 2 ·
coverage 0,3, gepaart über die 10 Dev-Wörter.

**Ergebnis — die Vorhersage trifft ein:** Die volle classed-Parität
ist gegen die λ=1,0-Schwester punktweise NICHT mehr schlechter
(dtw Δ-Median 0,000, Sign 4/2 bei 4 Ties, p = 0,69; die per-Wort-Deltas
sind gemischtes Rauschen ±0,002 — Arm ⑥ voll war 8/9 schlechter,
p = 0,039), bei erhaltener Strukturlinderung: cross m+s 43 → 39 (der
beste Folger-Wert, jetzt ohne punktweise Kosten), Marken 0 → 0,
AIoU/Chamfer flach. Der Schaden des Arm-⑥-Volllaufs kam also aus den
12 falschen Zielen, nicht aus dem Gewicht. Ehrlich daneben: (a) die
Mittelsprosse 0,037 ist isoliert strukturell SCHLECHTER als die
Schwester (m+s 43 → 47) — die Zähler sind über die Leiter nicht
monoton; (b) der Retrace-Ratio-Abstand zu 1,0 wächst auf beiden
Sprossen (1,09 → 1,32 bzw. 1,46) — der Kosten-Wächter meldet, dass
der Term Retrace-Zonen leicht auseinanderzieht.

**Verdikt:** Hypothese BESTÄTIGT im falsifizierbaren Sinn — und
trotzdem keine Adoption: gegen die eingefrorene Chain-Baseline steht
das Struktur-Veto in voller Höhe (cross m+s 26 → 39, Retrace-Gap
0,51 → 1,32; dtw −1,5 % rel, n. s.; AIoU +0,094 = der validierte
Tinten-Zug). Der Landmark-Term zielt jetzt sauber und kostet nichts —
aber die ERFUNDENE Struktur des Folgers entsteht nicht an seinen
Zielen, sondern in den Datentermen des Form-Release selbst (der
Arm-①-Befund, hier ein zweites Mal bestätigt). `FOLLOW_*` bleibt
`provisional`; für jeden KÜNFTIGEN Landmark-Arm ist
`extrapolated_classed` der empfohlene Modus (kostenlos schlägt
schädlich), der Default bleibt bis zum Owner-Go unverändert.
Artefakte: Chronik `arm6b-classed`.

### Struktur-Zähler v2 `aug16` — Vorregistrierung & Re-Baseline-Deklaration

Anlass: das manuelle Owner-Audit der 10 Dev-Wörter über die
Duell-Seite — die erste systematische Prüfung der Zähler gegen das
Duktus-Wissen statt gegen sich selbst. Befund: v1 zählte KONSISTENT
(dieselben Detektoren auf beiden Seiten, Identitäts-Gate intakt), aber
teils die falschen Kategorien: ein 17,8°/0,48-xh-Grenzgänger am
unter-e ist eine Retrace-Ablösung, keine Kreuzung; die
15°-Winkel-Schwelle schneidet am linken-k mitten durch dieselbe
Abzweig-Geometrie (12,1°/14,0°/9,0° verworfen, 82°/72° gezählt); der
mit-Kringel gegen den t-Anstrich (Partner-Lücke 4,3 xh entlang des
Wegs) ist Vorbeischreiben, kein Retrace; die laden-l-a-Spitze
(Pass-Arc 0,16/0,24 xh) ist eine auseinanderlaufende Spitze, keine
Zone.

**Die drei Regeln (Owner-Spezifikation, wörtlich übernommen):**

1. **Kreuzung nur bei DURCHSTOSS** — eine Linie kommt eindeutig auf
   einer Seite herein und auf der anderen wieder heraus. Formal: TLS-
   Gerade durch das ±`PIERCE_WINDOW_UNITS`-Fenster (0,25 xh, nie über
   eine Strichgrenze) JEDES Passes; die Fensterenden des jeweils
   anderen Passes müssen auf ENTGEGENGESETZTEN Seiten liegen, beide
   mit |Abstand| ≥ `PIERCE_MARGIN_UNITS` = 0,05 xh (≈ halbe
   Strichbreite: der andere Strich muss jenseits der eigenen Tinte
   wieder austreten). Beide Pässe müssen durchstoßen. Die
   15°-Winkel-Schwelle ENTFÄLLT als eigene Regel — Fenster × Marge
   implizieren einen ehrlichen Konditionierungs-Boden von
   arcsin(0,05/0,25) ≈ 11,5°, unter dem sich zwei Linien im
   Viertel-xh nicht über die halbe Strichbreite trennen und die Tinte
   die Frage selbst nicht beantwortet; die Bogen-Trennung ≥ 0,35 xh
   bleibt (der Wobble-Pin bleibt gültig). Gemessen an den Dev-Händen:
   die Owner-Streitfälle fallen richtig (der tangentiale unter-e-Ring
   raus, die und-d-Schleife bleibt), und am linken-k entscheidet EINE
   Regel statt einer Schwelle: die Schleifen-Schlüsse des Kringels
   durchstoßen (bleiben), die bloßen Abzweig-Gabelungen nicht (fallen
   — beide Klassen gleich beurteilt, was die v1-Winkelschwelle nicht
   leistete).
2. **Retrace nur bei bogen-nahem Partner** — Hin-und-zurück heißt: die
   Partner-Samples liegen entlang des Wegs UNMITTELBAR daneben.
   Pass-Klassifikation: Partner im ANDEREN Strich →
   **Überlagerung**; Partner-Lücke > `RETRACE_MAX_PARTNER_GAP_UNITS`
   = 1,0 xh → **Berührung** (Vorbeischreiben, mit oder ohne
   Tinten-Kontakt); Pass-Arc < `RETRACE_MIN_PASS_ARC_UNITS` = 0,30 xh
   → Spitzen-Graze, keine Zone. Konstanten aus der Messung: echte
   Zonen haben Lücke 0,38–0,66 und Arc ≥ 0,36; die Owner-Fälle Lücke
   1,16–8,34 bzw. Arc ≤ 0,24 — der Schnitt bei 1,0/0,30 liegt
   jeweils mitten im leeren Band.
3. **Berührung und Überlagerung sind eigene, BERICHTETE Klassen** —
   gezählt und ausgewiesen (Report/Seite), nie Teil eines Loss.

**Validierung (vorregistriert):** die Owner-Verdikte werden als Tests
gepinnt — unter-e: keine Kreuzung (tangentialer Dip); linken-k: beide
Abzweig-Klassen nach DERSELBEN Regel beurteilt; mit-t: genau EINE
Retrace-Zone im selben Strich, die Querstrich-Fälle Überlagerung,
Kringel-gegen-Anstrich Berührung; laden-l-a: keine Zone; der
Wobble-Out-and-back bleibt Retrace ohne Ring; und-d bleibt Kreuzung.
Das Identitäts-Gate (`--candidate authored`) muss exakt bestehen
bleiben. dtw/aiou/Chamfer/Marken/Lifts sind NICHT berührt.

**Re-Baseline-Deklaration:** `tools/tracebench/counters.py` verlässt
mit diesem Eintrag DATIERT den Freeze — die v1-Strukturzahlen der
`aug14`-Baseline und der Arme ①⑤⑥⑥b bleiben gültig und archiviert
(Chronik), sind aber mit v2-Zahlen NICHT vergleichbar; die
v2-Baseline-Tabelle folgt in diesem Eintrag nach der Implementierung.
`landmarks.py`, `core/geometry.py` und der Landmark-Term des Folgers
bleiben eingefroren (der Chain-Korrespondenz-Zensus §13a behält seine
eigenen Schwellen).

**v2-Baseline (Kette gegen die Hand, 10 Dev-Wörter; gemessen nach der
Implementierung, alle Verdikt-Pins grün, Identitäts-Gate PASS):**
`dtw_xh` 0,061985 med / 0,2618 p90 — byte-gleich zur v1-Baseline, wie
deklariert (nur die Strukturzähler änderten die Bedeutung). Struktur:

| Zähler | Hand (Σ) | Kette (Σ) | missing+spurious |
|---|---|---|---|
| Kreuzungen (Durchstoß) | 27 | 35 | 5+13 = 18 (v1: 26) |
| Retrace-Zonen | 15 | 18 | 2+5 = 7 (v1: 21 erfunden) |
| Berührungen | 8 | 17 | berichtet, nie Loss |
| Überlagerungen | 0 | 6 | berichtet, nie Loss |

**Nachtrag v2.1 (Owner-Audit der v2-Seite, gleicher Tag):** Drei Ringe
überlebten v2, die Abzweig-Ablösungen sind (unter-t 44,8° · mit-t
35,0° · zwei-w-Ende 24,0°). Die Regel, die sie trifft, ist die
wörtliche Anwendung des Owner-Prinzips auf den Ring selbst: Ein Ring,
dessen beide Chords EINANDER Antiparallel-Partner des
Retrace-Detektors sind (`CROSS_PARTNER_NEAR_UNITS` 0,16 xh ≈ die
eigene Proximity des Detektors, ≥ 2 Treffer beidseitig), ist der
beiläufige Selbstschnitt eines Hin-und-zurück-mit-Ablösung —
retrace-intern, keine Struktur-Kreuzung. Ein Retrace durch FREMDE
Tinte (linkens Kringel-Durchgänge) behält seine Ringe: seine Chords
partnern mit den eigenen Rückschenkeln, nicht miteinander. Gemessen
fallen exakt die beanstandeten Ringe (plus der gleichartige
linken-k-Ausgang, 53,1°; Partner-Hits 4–13 beidseitig), jeder
behaltene liest 0/0. Ehrliche Konsequenz: Für antiparallel-benachbarte
Paare steigt der effektive Ring-Boden auf die Antiparallel-Toleranz
des Detektors (25°) — alle echten Hand-Ringe liegen ≥ 45°, der
13°-Durchstoß-Pin wurde entsprechend auf die v2.1-Semantik
umgeschrieben. Zwei Entscheidungen dokumentiert: (a) Gezählt werden
Kreuzungs-ORTE, nicht -Ereignisse — linkens „runter 2× gekreuzt, dann
zurück-retraced = eigentlich 4" ist als Ereigniszählung richtig, aber
der Ort ist die stabile Währung: das Duktus-Budget hinge sonst an der
Retrace-Anzahl, und das Positions-Matching kann ko-lokalisierte
Ereignisse ohnehin nicht trennen. (b) Berührungen und Überlagerungen
stehen seither auch in der Zahlen-Tabelle der Duell-Seite.

**v2.1-Baseline (nach dem Nachtrag; Identitäts-Gate PASS, dtw
byte-gleich):** Hand 23 Kreuzungen · 15 Retrace-Zonen · 8 Berührungen ·
0 Überlagerungen; Kette 20 · 18 · 17 · 6. Missing+spurious: Kreuzungen
7+4 = 11 (v2: 18, v1: 26), Zonen 2+5 = 7. Der Löwenanteil der
v1-„Erfindungen" an den Stapel-Wörtern war RETRACE-INTERN — die
überlappenden Striche der Kette partnern antiparallel und schneiden
sich beiläufig; die präzise Klage lautet seither: 4 erfundene Ringe,
5 erfundene Zonen, 9 erfundene Berührungen (zu enges Vorbeischreiben),
6 Überlagerungen. Hand je Wort: die 1 · laden 3 · linken 3 (der
k-Ausgang fiel als Ablösung; das Soll rechnet mit denselben Zählern
und zieht mit) · mit 2 · muß 1 · und 1 · unter 3 · Wer 3 · will 3 ·
zwei 3 (= z2+w1).

Lesart (v2-Stand vor dem Nachtrag): Von den 19 „erfundenen Kreuzungen"
der v1-Kette waren 6 tangentiale Artefakte, die der Durchstoß nicht
mehr zählt — 13 echte Erfindungen bleiben die Klage. Die 21 „erfundenen
Retrace-Zonen" der v1 zerlegen sich in 5 echte Erfindungen, **9
erfundene Berührungen** (die Komposition schreibt Buchstaben zu eng
aneinander vorbei — eine präzisere Diagnose als „Retrace") und 6
Überlagerungen. `retrace_arc_ratio` med fällt 1,51 → 0,83: die Kette
retraced jetzt WENIGER Bogen als die Hand — die ehrliche Richtung,
denn die echten Hand-Retraces (t-Stamm, ß) sind lang, und die
Erfindungen sind in ihre eigenen Klassen umgezogen. Hand-seitig
rücken die Zählungen auf die Duktus-Budgets (Wer 5 → 3 = W2+r1,
muß 3 → 1 = ß-Budget, unter 5 → 4). Kandidat der Baseline ist die
verifizierte Chain-Identität (`follow --rounds 0`,
Byte-Identitäts-Pin) über den File-Provider.

### Route B T0 `aug15` — InkSight Small-p roh auf den Dev-Wörtern

Der T0-Prüfstein aus tintenfolger.md §4: das veröffentlichte
Small-p-Checkpoint (Apache 2.0), unadaptiert, CPU, über die
`tools/inksight`-Pipeline (#340) — Umgebung wie im README verifiziert
(Python 3.11 · tf-cpu 2.20.0 · tf-text 2.20.1, XLA-Flags gesetzt).
Laufzeit-Befund: `derender`/`text` ≈ 2–6 min je Wort auf 8 Kernen;
der `r+d`-Prompt (erst Texterkennung, dann Tinte) ≈ 43 min je Wort und
wurde nach EINEM Datenpunkt abgebrochen — der eine genügt für die
OOD-Diagnose: das Modell liest das Sütterlin-„Wer" als „Olomi".
Kein Call erreichte den 1024-Token-Deckel (max. 441, linken); die
Gitter-Auflösung lag bei 1,00–1,41 Crop-px je Wort.

| Kandidat | dtw med | p90 | AIoU | cross m+s | Zonen m+s | Lifts Δ |
|---|---|---|---|---|---|---|
| Kette (v2.1-Baseline) | 0,0620 | 0,262 | 0,683 | 7+4 | 2+5 | +3 |
| **InkSight derender** | **0,0956** | 0,391 | 0,697 | **9+1** | 11+2 | +21 |
| InkSight text | 0,1145 | 0,383 | 0,680 | **5+1** | 12+1 | +20 |
| routeg-Kontrolle | 0,8198 | 1,027 | 0,833 | 15+3 | 15+0 | +90 |

Lesart: (a) Roh und nie auf deutscher Kurrentschrift trainiert landet
Small-p bei **1,5× der Kette** und **8,6× vor der prior-freien
Kontrolle** — die Route-B-Prämisse (gelernte Verfahren tragen echtes
Geometrie-Wissen bei) ist damit bestätigt, nicht nur behauptet.
(b) Überraschung gegen die Paper-Ablation: der `text`-Prompt („Derender
the ink: <wort>") ist SCHLECHTER als das nackte `derender` — die
Wort-Konditionierung zieht das Modell bei einer Schrift, deren
Buchstabenformen es nicht kennt, Richtung lateinischer Schreibung
statt zur Tinte. (c) Die KREUZUNGS-Struktur des Modells ist sauberer
als die der Kette (nur 1 erfundener Ring auf beiden Prompts, text
verpasst nur 5 von 23) — was fehlt, sind die RETRACES (11–12 von 15
verloren; das Modell setzt ab statt zurückzufahren, +20 Lifts, 3–9
Striche je Wort) — exakt die Klasse, die der Duktus-Prior beherrscht.
Schlechtestes Wort beider Prompts: und (0,395/0,396 — es schreibt das
„und" als lateinisches Wortbild). Konsequenz wie in §4b geplant: T0
ist die dokumentierte OOD-Basislinie; der nächste Route-B-Schritt
bleibt das EIGENE kleine Trajektorien-Modell auf Engine-Paaren
(Fine-Tuning von Small-p ist ohne Trainingscode unmöglich).
Artefakte: Chronik `inksight-t0`; Kandidaten/Rohantworten bleiben
unter `tools/inksight/out/` (gitignored, Messschicht).

### Arm ⑨ `aug16` — Vorregistrierung: der Topologie-Wächter

Geschrieben und committet VOR der ersten Zahl dieses Arms.

**Befund, der den Arm begründet (v2.1-Zähler):** Schon die
λ=1,0-Schwester ERFINDET Struktur gegenüber ihrer eigenen
Chain-Initialisierung — Berührungen 17 → 27, erfundene Zonen 5 → 10,
Kreuzungen m+s 11 → 15 — und Arm ① zeigte, dass jede Release-Sprosse
am Struktur-Veto scheitert, während der Tinten-Zug selbst validiert
ist (AIoU +0,10 überall). Die Hypothese, falsifizierbar: **Die
Distanz-/AIoU-Gewinne des Release sind von seinen
Struktur-Erfindungen trennbar.** Der Owner-Satz dazu: Kringel,
Kreuzungen und Retraces sind duktus-fix und ändern sich durch das
Verfeinern nicht.

**Mechanismus (folger-seitig, opt-in, kein neuer Objective-Term):**
eine Runden-AKZEPTANZREGEL statt einer Kraft. Vor Runde 1 wird das
Struktur-Budget der Initialisierung gemessen — die v2.1-Klassenzählung
(Kreuzungen · Retrace-Zonen · Berührungen · Überlagerungen,
`tools.tracebench.counters` auf den assemblierten Pen-down-Polylinien
des Runs, in xh-Einheiten). Eine gelöste Runde wird nur AKZEPTIERT,
wenn keine Klassenzahl ihr Budget übersteigt; eine verletzende Runde
wird mit HALBIERTEN Reisebudgets (`max_delta`/`connector_max_delta`)
neu gelöst, höchstens zweimal; verletzt sie weiter, behält der Run die
Geometrie der Vorrunde und die Runde ist als `structure_rejected`
protokolliert (die Schleife endet — dieselbe Bewegung würde erneut
scheitern). `FollowWeights.structure_guard` (bool, default False =
byte-identisch, Pin) schaltet den Wächter je Arm zu; das Lineal misst,
der Wächter entscheidet — derselbe Zähler, keine zweite Semantik.

**Protokoll:** Sprossen prox ∈ {0,01 · 0,1} (die Release-Sprossen, auf
denen Arm ① die größten Gewinne bei tödlichem Veto zeigte) und die
1,0-Schwester als Kontrolle (der Wächter sollte auch ihren
27-Berührungs-Drift einfangen), Basis sonst Arm-⑥-identisch. Gepaart
über die 10 Dev-Wörter gegen die eingefrorene v2.1-Chain-Baseline;
`stranded_anchors` bleibt Pflicht-Kostenspalte.

**Kriterien:** Primär `dtw_xh` (Median der gepaarten Differenzen)
fällt gegenüber der Chain-Baseline; Co-Primär Marken und Kreuzungen
ohne Netto-Verschlechterung; der Wächter-KONTRAKT ist selbst messbar:
jede Klassenzahl des Kandidaten ≤ der Chain-eigenen Zahl (Berührungen
≤ 17, Zonen-spurious ≤ 5 …). Kosten-Wächter wie §14 üblich.

**Kill-Kriterien:** Blockiert der Wächter auf den Release-Sprossen
jede Bewegung (dtw im Rauschen der Kette, `max_anchor_motion` ≈ 0) →
die Gewinne WAREN die Erfindungen, Formulierung verworfen, ehrliches
Negativ. Laufen die meisten Runden in die Retry-Erschöpfung → der
Mechanismus (Akzeptanz statt Kraft) ist ungeeignet, nächste Hypothese
wäre ein differenzierbarer Abstands-Term, nicht mehr Retries. Keine
Adoption eines Defaults ohne Owner-Go.

**Ergebnis (`aug16`, beide Kill-Kriterien gefeuert — das wertvollste
Negativ der Kampagne):** Der Wächter-KONTRAKT hält perfekt: Auf allen
drei Sprossen bleibt jede Klassenzahl ≤ der Chain-eigenen (Kreuzungen
m+s exakt 7+4, Berührungen ≤ 17, Zonen ≤ 7) — zum ersten Mal besteht
ein released Folger das Struktur-Gate. Aber der Preis beantwortet die
Hypothese abschlägig: dtw-Δ gegen die Kette ist EXAKT null (Δ-Median
0,000000; 6–8 von 10 Wörtern byte-identisch, Sign-Test p = 1,0 auf
allen Sprossen), weil 13 von ~21 Runden nach Retry-Erschöpfung
zurückgewiesen wurden (26–28 Retries je Arm). Nur der AIoU-Rest der
akzeptierten, gedämpften Runden bleibt (+0,033 bei prox 0,1 — ein
Drittel des ungewachten +0,10). **Die Tinten-Gewinne des Release und
seine Struktur-Erfindungen sind nicht trennbar: die Bewegung zur
Tinte hin IST das Erfinden** — engeres Aneinander-vorbei-Schreiben
senkt die Distanz und erzeugt exakt die Berührungen, die die Hand
nicht hat. Konsequenz für Route A: Der Kettenfit steht bereits am
struktur-sicheren Optimum dieser Formulierung; die verbleibende
dtw-Lücke zur Hand ist mit „Form-Prior lösen" in keiner der fünf
gemessenen Varianten (①⑤⑥⑥b⑨) zu kaufen. Die nächsten Hebel liegen
COMPOSER-seitig (Platzierung/Joins — die Soll-Abweichler t · W ·
join-Schleifen, plus die 9 erfundenen Berührungen der Komposition
selbst) und bei fundamental anderen Kandidaten (Route B). Der
Wächter selbst bleibt als Werkzeug im Repo (`structure_guard`,
default False): er ist das erste Instrument, das einen Folger-Lauf
GARANTIERT struktur-sauber hält, und der prox-0,1-Lauf ist als
einziger struktur-sauberer Release-Kandidat auf der Duell-Seite.
Artefakte: Chronik `arm9-wächter`.

**Nachtrag `aug15` — korrigierte Attribution der Berührungen.** Die
Formulierung „die 9 erfundenen Berührungen der Komposition selbst"
oben ist falsch zugeordnet: nachgemessen mit den eingefrorenen
v2.1-Zählern über die Fixtures schreibt die KOMPOSITION der 10
Dev-Wörter nur 2 Berührungen (beide w-intern: `will` x≈1,95, `zwei`
x≈3,10) und 4 Überlagerungen (alle t-Balken-gegen-Stamm in
`mit`/`unter`) vor — keine einzige zwischen zwei Buchstaben. Der
Überschuss von 8 auf 17 Berührungen gehört dem KETTENFIT
(`touch_cand` 17 gegen Hand 8). Der Composer-Hebel bleibt real,
liegt aber bei den Schnitt-Klassenregeln und der Kopplung
(Unter-Kreuzen), nicht bei den Berührungen; Plan in
`../proposals/tintenfolger.md` §7.

### Route G `aug14` — die prior-freie Kontrolle: was der Duktus-Prior kauft

Der Kontrollkandidat aus
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §4b, jetzt
gemessen. **Was gelaufen ist, ist nicht der publizierte Code:** Das
Referenz-Repo (Diaz et al. 2022) ist MATLAB 2016a+ mit Image Processing
Toolbox — MIT lizenziert, aber hier und in CI nicht ausführbar, also
wäre eine `wor()`-Zahl von niemandem nachrechenbar (Befund und
Belegstellen im §4b-Nachtrag). Gelaufen ist die eigene Minimalfassung
`tools/routeg`: eingefrorenes Skelett → Segmentgraph (benachbarte
Verzweigungspixel = EIN Knoten) → Greedy-Traversierung, drei
Entscheidungen (linkester Endpunkt · ein Skalarprodukt am Knoten ·
Absetzen bei Sackgasse), **kein gelernter Anteil, kein Template, keine
Ground Truth**. Das Kandidatenlabel heißt darum `routeg-graph`, nicht
`routeg-wor`.

Lauf: `--candidate file --candidate-file temp/routeg-t0.json --label
routeg-t0 --split dev`, Schritt 0,02, 175 s, 10/10 gescort, 0 failed.
Referenzseite identisch zur v2.1-Baseline (23 Kreuzungen · 15
Retrace-Zonen · 8 Berührungen · 0 Überlagerungen) — dieselben
eingefrorenen Zähler, also ist die Gegenüberstellung wörtlich
vergleichbar. Nach den Soll-Spalten (#353) einmal nachgemessen: **jede
Zahl byte-gleich**, nur die zwei neuen Report-Zeilen kommen hinzu
(`soll_cross_agree` 7/10, `soll_zones_agree` 6/10) — die
Report-Spalten-Regel hält also auch für diesen Kandidaten.

```
dtw_xh_median:   0.819847    aiou_median:              0.8333
dtw_xh_p90:      1.026691    chamfer_cand_ref_median:  0.0365
dtw_xh_worst:    die 1.0355  chamfer_ref_cand_median:  0.0411
marks_missing:   0   marks_spurious:   4
cross_missing:   15  cross_spurious:   3
retrace_missing: 15  retrace_spurious: 0
retrace_arc_ratio_median: 0.000
lift_delta_total: 90  dtw_reversed_better: 0  dtw_max_absorption_max: 222
touch_ref 8 / touch_cand 4 · overlap_ref 0 / overlap_cand 25
```

Je Wort (dtw · aiou · Kreuzungen gefunden/Soll · Striche
Kandidat/Hand): die **1,036** · 0,854 · 0/1 · 6/2 — linken **1,026** ·
0,821 · 1/3 · 18/2 — zwei 0,907 · 0,813 · 1/3 · 13/1 — laden 0,833 ·
0,859 · 2/3 · 11/1 — will 0,832 · 0,841 · 0/3 · 9/2 — Wer 0,808 ·
0,880 · 0/3 · 11/1 — muß 0,681 · 0,829 · 1/1 · 11/2 — unter 0,656 ·
0,829 · 1/3 · 16/2 — und 0,428 · 0,838 · 1/1 · 9/2 — mit 0,414 ·
0,801 · 1/2 · 7/2.

**Gegenüberstellung** (gleiche Wörter, gleiches Lineal). Der Kettenfit
wurde für diese Zeile am selben Tag NEU gerechnet
(`--candidate chain --split dev`, 2808 s) statt aus der v2.1-Baseline
abgeschrieben — und reproduziert sie exakt: dtw 0,061985 · aiou 0,6831 ·
p90 0,261818 · worst `unter` 0,438926 · Chamfer 0,0398/0,0467 ·
Kreuzungen 7 fehlend/4 erfunden · Zonen 2/5 · `retrace_arc_ratio` 0,830 ·
Berührungen 8/17 · Überlagerungen 0/6 · `lift_delta_total` 3. Die
Gegenüberstellung ist damit gemessen, nicht zitiert:

| | Hand (Referenz) | Kettenfit | Route G |
|---|---|---|---|
| `dtw_xh` Median | 0 (Identitäts-Gate) | **0,062** | **0,820** |
| `aiou` Median | 0,685 | 0,683 | **0,833** |
| Kreuzungen (Soll 23) | 23 | 20 · 7 fehlen, 4 erfunden | 8 · **15 fehlen**, 3 erfunden |
| Retrace-Zonen (Soll 15) | 15 | 18 · 2 fehlen, 5 erfunden | 0 · **15 fehlen**, 0 erfunden |
| Absetz-Differenz Σ | 0 | 3 | **90** |

**Lesart — die Kontrolle tut genau, was eine Kontrolle soll.** Drei
Dinge stehen nebeneinander, und nur zusammen ergeben sie einen Satz:

1. **`aiou` ist HÖHER als die der Hand gegen sich selbst** (0,833 gegen
   0,685). Das ist kein Sieg, sondern der Beweis, dass die Spalte
   Tintendeckung misst und nicht Schreiben: Die Traversierung läuft
   qua Konstruktion auf dem Skelett, die Handbahn ist ein Stiftweg, der
   die Tinte nicht deckungsgleich abfährt. **Auf der Tinte zu liegen
   ist nicht dasselbe wie sie zu schreiben** — die schärfste verfügbare
   Warnung davor, `aiou` je als Kopfzahl zu lesen.
2. **`dtw_xh` ist 13× so groß wie beim Kettenfit** (0,820 gegen 0,062).
   Das ist die Zahl, für die Route G gebaut wurde: So weit ist der Weg
   durch dieselbe Tinte, wenn niemand weiß, wie man schreibt.
   architektur.md §2 hat damit erstmals eine Messzahl statt eines
   Architektur-Arguments.
3. **Die Struktur bricht ganz weg.** 15 der 23 Kreuzungen verloren, alle
   15 Retrace-Zonen verloren (bauartbedingt — die Traversierung läuft
   jede Kante genau einmal), und 90 zusätzliche Absetzer (`lift_delta`
   zählt Körperstriche, Marken sind ausklassifiziert; über alle Striche
   gerechnet sind es 111 gegen 17). Die Hand schreibt diese Wörter in
   **1–2 Zügen**, die Kontrolle braucht **6–18**. Genau hier — nicht in
   der Distanz — sitzt der Unterschied
   zwischen „Tinte nachfahren" und „Schreiben".

**Was das für die Folger-Arme heißt:** Die Kill-Kriterien des §14 sind
gegen den Kettenfit vorregistriert, und Route G bestätigt deren
Richtung ohne sie zu berühren — der Prior schlägt die prior-freie
Kontrolle klar (der Fall „schlägt ihn NICHT klar" aus §4b tritt nicht
ein), und zwar in der STRUKTUR deutlicher als in der Distanz. Route G
ist damit erledigt als Frage und bleibt als Bodenmarke: Ein Folgerarm,
der Struktur gegen Distanz eintauscht, kann an dieser Zeile ablesen,
wo das endet.

**Grenzen dieser Zahl, ehrlich benannt:** (a) Die Kontrolle ist eine
REDUKTION des publizierten Verfahrens, keine Reimplementierung — ohne
gewichtete `π_ij`-Fortsetzung, ohne Cluster-Rang-Klassifikation, ohne
Dijkstra durch den Cluster und ohne Retrace-Modell. Die echte WOR-Zahl
läge besser, und **um wie viel, ist hier NICHT gemessen**: Die ersten
drei fehlenden Bausteine adressieren die Astwahl (also `dtw` und die
Kreuzungsspalte), das fehlende Retrace-Modell dagegen genau die beiden
Zeilen, die hier am lautesten sind — Retrace-Zonen und Absetz-Differenz.
Wer die Lücke zum Prior beziffern will, statt sie nur zu sehen, muss
diese Zahl mit MATLAB nachziehen; bis dahin ist die Aussage die
schwächere und sichere: **so weit ist der Weg mindestens.** (b) Sie ist auf
denselben 10 Dev-Wörtern gemessen wie alles andere und trägt deren
blinde Flecken (kein Umlautwort, kein langes ſ, eine Majuskel).
(c) `marks_uncertain` gilt für dieselben 4 Wörter wie in der Baseline.
Artefakte: `temp/routeg-t0.json`, `temp/tb-routeg-t0.{json,txt}`
(gitignoriert); Rezept in `tools/routeg/README.md`.

### Welle 1 · K1 `aug15` — Vorregistrierung: t-Balken-Schnitt mit Überstand

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.2).

**Hypothese.** Das gebundene t unter-kreuzt, weil die
Balken-Schnittregel (`BAR_EXIT_BASES`, `core/compose.py`) den
Deckstrich exakt AN seiner Kreuzung mit dem Stamm endet — für den
Durchstoß-Zähler (`PIERCE_MARGIN_UNITS` 0,05 xh) ist ein Endpunkt
keine Kreuzung. Ein kleiner Überstand jenseits des Schnittpunkts
stellt die duktus-fixe Kreuzung wieder her, ohne die
B-Platzierung zu bewegen (deren Anker bleibt der STAMM,
`stem_launch`); der Join startet an der neuen Balkenspitze statt am
Stamm — wie auf den Platten, wo der Balken durch den Stamm läuft und
erst dahinter in die Verbindung übergeht.

**Konstante, gemessen statt gewählt.** `BAR_CROSS_OVERRUN_UNITS =
0.2`: In der authored-Referenz von `mit` (wortfinales t, der Balken
endet frei) liegt die Balkenspitze 0,16–0,22 xh rechts der beiden
Stamm-Pässe (Spitze x≈4,78 gegen Kreuzungen x≈4,56/4,62). Die
authored-Referenz von `unter` (gebundenes t) präzisiert die
MECHANIK: die Hand schreibt keinen toten Balken — der Deckstrich ist
eine Schleife (Stamm runter/retrace hoch, kleine Linksschleife auf
Mittelhöhe), deren Auslauf-Pass den Stamm DURCHSTICHT (Kreuzungen
mit Abstrich x≈4,63 und Aufstrich x≈4,70), ~0,1 xh danach frei von
der Stammtinte ist und ohne Absatz als die jul30-gemessene
16–27°-Join-Haarlinie weitersteigt. Der jul30-Ink-Befund („0,00–0,03
xh Balkentinte rechts des Stamms") und diese Bahn beschreiben
DIESELBE Tinte — verschieden ist die Topologie: die Platte hat dort
Join-Tinte, und der Stift läuft DURCH den Stamm, nicht bis an ihn.
Überstand + Join-Start an der Spitze reproduzieren diese Topologie
mit minimalem Eingriff (der Balken bleibt der authored Chart-Strich;
die Linksschleifen-Form selbst wäre eine Chart-Duktus-Frage). 0,2
liegt im Beleg-Bereich beider Wörter und komfortabel über der
Pierce-Marge.

**Erwartung.** `unter` `soll_cross` 2→3 (= Übereinstimmung mit der
Hand); `mit` bleibt 1 (das dortige Defizit ist ein Join-Effekt, K2).
Die `soll_overlap`-Einträge der t-Wörter (heute 2× `mit`, 2×
`unter`, alle Balken-gegen-Stamm) können sich umklassifizieren —
berichtet, nicht Kriterium.

**Messgrößen und Kill-Kriterien.**
(a) `soll_cross_agree`/`soll_zones_agree` JE WORT über die 10
Dev-Wörter: kein Wort außer den t-Wörtern darf seine
Übereinstimmung verlieren, sonst verworfen.
(b) wordbench `uv run python -m tools.wordbench.run --style
suetterlin --set all`: `word_loss` und `pair_loss` dürfen nicht über
Rausch-Niveau regressieren (> +0,002 auf einer Headline =
verworfen); erwartet ist Bewegung NUR in t-Wörtern.
(c) Das compose-golden-Fixture bricht bauartbedingt (gebundene
t-Geometrie ändert sich) — der Regen (`REGEN_GOLDEN=1`) ist Teil des
PRs und wird hier als deklarierte Re-Baseline geführt; er ist KEIN
Akzeptanzkriterium.
(d) Sichtprüfung der beiden t-Wörter auf der Duell-/Werkbank-Seite
(der Balken darf nicht als abgesetzter Stummel wirken).

**Ergebnis (gemessen nach dem Commit oben).** Die registrierte
Erwartung ist WIDERLEGT — und die Widerlegung ist der Fund. Auf
WORT-Ebene ändert der Überstand die Topologie exakt gar nicht: die
Kreuzungspunkte der komponierten `unter` sind vor und nach K1
byte-nah identisch ((4,72 · 0,28) und (7,70 · 0,26)), `soll_cross`
bleibt 2, die Agree-Zeilen bleiben 7/10 und 6/10. Der Grund: die
t-Kreuzung EXISTIERTE schon immer — der Stift-Weg
Balken-Rücklauf → Schnittpunkt → Join-Haarlinie ist EIN
Pen-down-Zug und durchstößt den Stamm; verbucht war sie nur beim
JOIN (`comp − Σ Buchstaben`), weil der Balken als eigener Strich am
Schnittpunkt endete. K1 verschiebt die Kreuzung in den Buchstaben
(Σ Buchstaben 1→2, die per-Letter-Zelle des gebundenen t wird 1/1
und trägt damit den Duktus-Fingerabdruck selbst; der scheinbare
„Join-Beitrag +1" bei `unter` war eine Fehlbuchung dieser
Balken-Kreuzung, kein d/e-artiger Schleifenbeitrag). Das ECHTE
Defizit (`unter` 2 vs 3, `mit` 1 vs 2) sitzt im STAMM-RETRACE: die
Hand schreibt den t-Stamm hinunter und VERSETZT wieder hinauf
(Abstrich x≈4,60, Aufstrich x≈4,65 — der Auslauf durchsticht ZWEI
Pässe und die Rückkehr kreuzt den Abstrich ein drittes Mal), die
Komposition überbrückt den Rückweg KOLLINEAR auf dem Stamm — für
den Zähler unsichtbar. Kandidat K1b (eigene Vorregistrierung, nicht
Teil dieses Ergebnisses): die generierte Stamm-Rückkehr als
versetzten Pass führen (~0,05 xh, innerhalb der Schwellzug-Breite —
auf der Platte unsichtbar, im Zähler zwei Pässe). Gates: Headline
`bench_loss` 0,110703 → 0,110992 (+0,0003, Kill-Schwelle 0,002),
`pair_loss` byte-gleich 0,165688, bewegt haben sich AUSSCHLIESSLICH
t-Wörter (Seiten +0,00001 · Soldaten +0,0007 · streiten +0,0036 ·
unter +0,0038 · fechten +0,0100); kein Nicht-t-Wort verliert
Übereinstimmung. ENTSCHEIDUNG: BEHALTEN — kein Kill-Kriterium
feuert, die Tinte ist quasi unverändert (der Join beginnt an der
Spitze statt am Schnittpunkt, derselbe Weg), und die
Buchstaben-Attribution stimmt jetzt mit der Hand überein; das
compose-golden-Fixture wurde als deklarierte Re-Baseline
regeneriert. K1b ist der nächste Composer-Kandidat der Welle.

### Welle 1 · B1 `aug15` — Vorregistrierung: Best-of-N über Input-Augmentierungen (InkSight)

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.4; Infrastruktur
`tools/inksight/{augment,ensemble}.py`, Ranker ausschließlich gegen
die gemessene Tinte).

**Hypothese.** Ein einzelner Decode ist ein Zug aus einer auf
Sütterlin instabilen bedingten Verteilung; N deterministische
Augmentierungs-Varianten (Rotation ±2/±4° × Füllgrad — exakt die
InkSight-eigenen Trainings-Augmentierungen) plus ein Tinten-Ranker
(beidseitiges Chamfer gegen `ref_skel`, Kontraktverletzung
disqualifiziert) verbessern die Bahn. Präzedenz: Afonin et al.,
ICDAR 2023 (dieselbe Forschungsgruppe, „more than halving the
character error rate").

**Owner-Direktive (2026-08-15).** Gemessen wird nicht nur der
Gewinner: ALLE Varianten werden einzeln gegen die Handbahn
gebencht. Die ORAKEL-Spalte — die per Hand-dtw beste Variante je
Wort gegen die Wahl des Tinten-Rankers — beziffert, was die
ehrliche Tinten-Auswahl kostet; die Handbahn bleibt Prüfung, die
Tinte das einzige Auswahlsignal.

**Messgrößen und Kill-Kriterien** (Dev-Split, Vergleich gegen die
eingefrorene T0-derender-Zeile `temp/tb-inksight-derender.json`,
dtw-Median 0,0956, 9 gewertete Wörter + `Wer` failed):
(a) Primär: gepaarter dtw_xh-Median Best-of-N vs. T0-derender;
Median-Δ ≥ 0 (keine Verbesserung) = Maßnahme verworfen.
(b) Struktur netto: `cross_missing+spurious` und
`retrace_missing+spurious` dürfen sich in Summe nicht
verschlechtern.
(c) `Wer` (T0: failed an einem Ein-Punkt-Strich): erwartet geheilt,
sobald EIN konformes Ensemble-Mitglied existiert; bleibt es failed,
wird das berichtet, ist aber kein Kill.
(d) Die Orakel-Lücke (Median der gepaarten Differenz
Ranker-Wahl − Hand-Orakel) wird berichtet — eine große Lücke ist
ein Befund über das Auswahlsignal, kein Kill.
(e) Determinismus-Gate: die Identitäts-Variante `rot+0_s100` muss
tokengleich zur T0-Antwort decodieren; weicht sie ab, ist der
LAUF ungültig (nicht die Maßnahme).

**Ergebnis (gemessen nach dem Commit oben).** Der Lauf ist GÜLTIG,
die Maßnahme ist nach ihrer eigenen Regel VERWORFEN — und der Fund
steckt in der Orakel-Spalte, die genau dafür vorregistriert war.

*Gate (e) zuerst:* die Identitäts-Variante `rot+0_s100` decodiert
bei ALLEN zehn Wörtern tokengleich zur eingefrorenen T0-Antwort
(rekonstruierte Token-Sequenz, `n_ink_tokens` 149…441 identisch,
`n_invalid_tokens` überall 0, Strichlisten punktgleich; die
Eingabe-PNGs sind ohnehin byte-identisch zu denen von `prepare.py`).
100/100 Rohantworten geparst, 10 Varianten je Wort, ein
Decoder-Deckel-Treffer (`laden`/`rot+4_s092`, 1023 von 1024 Token =
abgeschnittene Tinte, ohnehin kontraktverletzend).

*Gate (a), die Entscheidung:* gepaarter dtw_xh-Median Best-of-N
gegen T0-derender **+0,0000** (9 gepaarte Wörter; 4 besser, 4
schlechter, 1 unverändert; Vorzeichentest p = 1,0; Median absolut
0,0956 → 0,0960). Δ ≥ 0 heißt laut Vorregistrierung: **verworfen**.
Die Tinten-Zahlen bewegen sich dabei ALLE in die erwartete Richtung
— `aiou` 0,6969 → 0,7057, `chamfer_cand_ref` 0,0430 → 0,0388, die
Ranker-Summe je Wort 0 bis −40 % gegen die Identität. Der Ranker
hat also genau das optimiert, was ihm aufgetragen war; nur ist das
nicht, was dtw misst.

*Gate (b):* Struktur netto NICHT schlechter — auf denselben neun
Wörtern Kreuzungen (missing+spurious) 10 → 6, Retraces 13 → 14,
Summe 23 → 20. Der Zehn-Wort-Block liest 23 → 25, weil `Wer`
überhaupt erst gewertet werden KANN und seine eigenen Defekte
mitbringt; die Like-for-like-Spalte ist die Antwort auf „wurde es
schlechter".

*Gate (c):* `Wer` ist GEHEILT — T0 scheiterte an einem
Ein-Punkt-Strich, Best-of-N liefert eine speicherbare Zeile (dtw
0,1378 über `rot-2_s092`). Von zehn Varianten waren dort genau zwei
kontraktkonform: das Ensemble hat die Heilung mit seinem letzten
Mitglied bezahlt, nicht mit Redundanz.

*Gate (d), der eigentliche Befund — die Orakel-Lücke.* Je Wort
Ranker-Wahl (dtw) · Hand-Orakel (dtw) · T0: `Wer` `rot-2_s092`
0,1378 · dieselbe 0,1378 · failed | `die` `rot+2_s092` 0,0385 ·
`rot+0_s092` 0,0312 · 0,0395 | `laden` `rot+0_s100` 0,0607 ·
dieselbe · 0,0607 | `linken` `rot-2_s100` 0,1081 · dieselbe ·
0,1227 | `mit` `rot-2_s100` 0,0758 · `rot+4_s092` 0,0361 · 0,0421 |
`muß` `rot+4_s100` 0,0886 · `rot+0_s100` 0,0808 · 0,0808 | `und`
`rot+4_s100` 0,3795 · dieselbe · 0,3952 | `unter` `rot-4_s100`
0,3966 · `rot-2_s100` 0,0813 · 0,3898 | `will` `rot+4_s100` 0,0960
· `rot-4_s100` 0,0516 · 0,0956 | `zwei` `rot+4_s100` 0,1129 ·
`rot+2_s100` 0,1069 · 0,1193. Median der gepaarten Differenz
(Ranker − Orakel) **+0,0067 xh**, Treffer in 4 von 10 Wörtern. Und
die Kehrseite derselben Tabelle: das ORAKEL hätte einen gepaarten
Median von **−0,0124** geliefert (7 von 9 Wörtern besser, Median
absolut 0,0808) — Gate (a) also klar bestanden. Die N Antworten
ENTHALTEN die Verbesserung; das Auswahlsignal findet sie nicht.

*Warum nicht — an einem Wort abzulesen.* Bei `unter` stehen vier
kontraktkonforme Varianten zur Wahl; der Tinten-Ranker setzt
`rot-4_s100` (Chamfer-Summe 0,0759) vor `rot-2_s100` (0,0841), also
10 % Abstand im Auswahlmaß — in der Handbahn liegen zwischen beiden
0,3966 gegen 0,0813, ein Faktor 4,9. Bei `mit` dasselbe Muster mit
8 % Chamfer-Abstand und +0,0337 dtw gegen T0 (die größte
Einzelregression des Laufs). Das ist keine Kalibrierfrage: ein
beidseitiges Chamfer gegen das Skelett misst ÜBERDECKUNG und Nähe,
dtw misst Reihenfolge und Korrespondenz. Wo eine Variante die Tinte
gleich gut bedeckt, sie aber in anderer Ordnung durchläuft, ist der
Ranker per Konstruktion blind — und genau diese Wörter (`unter`,
`mit`) sind die Berührungs-/Überlagerungsfälle aus §7.1.

*Zweiter Befund: die Augmentierung kostet Kontraktkonformität.* Nur
`rot+0_s100` und `rot-2_s100` schaffen 9 von 10 Wörtern; die
Füllgrad-Varianten kommen auf 3–4. Nach Disqualifikation bleiben im
Median 4 von 10 Mitgliedern, bei fünf Wörtern ≤ 4 und bei `und`,
`laden`, `Wer` nur 2 — das Ensemble schrumpft ausgerechnet dort, wo
es gebraucht würde. Einziges Wort mit 10/10 gültigen Mitgliedern ist
`die` (kleinster Crop, 154 px). Die Ein-Punkt-Striche sind also kein
`Wer`-Sonderfall, sondern die Reaktion des Modells auf verschobene
Eingaben. Repariert wird nichts (§2.4): eine geflickte Zeile ließe
das Modell besser aussehen, als es ist.

*Kein systematischer Gewinner.* Der Ranker wählt 7× reine Rotation,
2× Füllgrad, 1× die Identität; das Orakel verteilt sich auf ACHT
verschiedene Varianten. Es gibt keine bessere feste Vorverarbeitung,
die man einfach adoptieren könnte — der Gewinn ist wortweise und
steht und fällt mit der Auswahl.

**ENTSCHEIDUNG: VERWORFEN** als Default (Gate (a) feuert; nichts in
`core/`, an der DB oder am Rendering wird berührt — die Maßnahme
lebte ohnehin nur im Messlayer). Behalten wird die INFRASTRUKTUR
(`tools/inksight/{augment,ensemble}.py` inkl. `--per-variant`), denn
sie hat die eigentliche Frage erst messbar gemacht. Der Nachfolger
ist NICHT „mehr Varianten", sondern das Auswahlsignal: ein Ranker,
der Reihenfolge sieht (Soll-Duktus-Struktur statt reiner
Überdeckung), gemessen gegen die hier gemessene Orakel-Lücke von
+0,0067 xh als Zielgröße und −0,0124 als Deckel. `Wer` bleibt als
Nebenergebnis geheilt, ist aber allein keine Adoption wert.

### Welle 1 · A1 `aug15` — Vorregistrierung: der Marken-Nachfit

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(Plan: `../proposals/tintenfolger.md` §7.3; Infrastruktur
`tools/pairlab/marks.py`, opt-in `--mark-refit`, default byte-identisch).

**Hypothese.** Die Marken des Kettenfit-Kandidaten stehen an ihrer
Kompositions-Position statt auf der gemessenen Marken-Tinte
(`mark_pos_err_xh` Median 0,129 gegen 0,046 der prior-freien
Kontrolle; bei muß/und/unter/zwei matcht keine Marke). Ein rigider
Nachfit (reine Translation) jeder Marke auf die vom Körper nicht
beanspruchte Skelett-Tinte, mit Verweigerung bei Ambiguität
(Suchradius 0,6 xh = die Match-Grenze des Lineals, Margin 0,25),
senkt den Ortsfehler, ohne irgendetwas anderes zu bewegen.

**Nachfit-Ziel ist ausschließlich die TINTE** (ref_skel), nie die
authored-Referenz — gemessen wird ausschließlich GEGEN die Hand.

**Messgrößen und Kill-Kriterien** (gepaart über die 10 Dev-Wörter
des eingefrorenen Splits, Vergleich gegen die deklarierte
Post-K1-Kettenbaseline `tb-chain-r1-postk1`):
(a) Primär: `mark_pos_err_xh`-Median fällt; `marks_matched` steigt
oder bleibt (ein VERLORENES Match = verworfen).
(b) Do-no-harm: `dtw_xh` byte-gleich auf Wörtern ohne bewegte Marke
und ohne Netto-Verschlechterung insgesamt; Strukturzähler
(cross/zones/touch/overlap) exakt unverändert — der Nachfit bewegt
nur Marken-Striche; jede Abweichung = verworfen.
(c) `marks_spurious` darf nicht steigen (zwei 1,0 heute).
(d) Verweigerungen werden gezählt und benannt (meta.mark_refit),
nie still übergangen.

**Ergebnis (gemessen nach dem Commit oben, Lauf `tb-a1-marks`
gegen `tb-chain-r1-postk1`).** Die Hypothese ist BESTÄTIGT, mit
einer Einschränkung, die erst der Lauf sichtbar gemacht hat.
Primär: `mark_pos_err_xh` Median **0,1285 → 0,0576** (−55 %; Mittel
0,1217 → 0,0530), und zwar auf JEDEM der vier Wörter, die das Lineal
überhaupt paaren kann — `die` 0,0675 → 0,0560 · `mit` 0,1071 →
0,0194 · `linken` 0,1624 → 0,0592 · `will` 0,1499 → 0,0775.
`marks_matched` bleibt 4/4 (kein Match verloren), `marks_missing` 0,
`marks_spurious` 1 → 1, `marks_ambiguous` 0. Damit schließt A1 rund
86 % des Abstands zur prior-freien Kontrolle (0,046): der Kettenfit
konnte die Markentinte immer lesen, er hat sie nur nie gefragt.
Do-no-harm hält vollständig: die Strukturzähler sind über ALLE zehn
Wörter exakt unverändert (0 abweichende Zellen über
cross/retrace/touch/overlap/soll/lift), `dtw_xh` ist auf 7 von 10
Wörtern byte-gleich, der gepaarte Median-Δ ist 0,0000 und der
Vorzeichentest n=3/pos 2/neg 1 mit p=1,0. Nebenbei verbessern sich
die tintenseitigen Spalten (`aiou` 0,6831 → 0,6884, beide Chamfer-
Mediane −0,0003) — genau das Vorzeichen, das „die Marke sitzt jetzt
auf Tinte" erwarten lässt. Verweigerungen: KEINE. Acht der zehn
Wörter tragen genau eine Marke, alle acht wurden bewegt (Median-
Verschiebung 0,073–0,127 xh, alle weit innerhalb des 0,6-xh-Radius),
`laden` und `Wer` haben gar keine.

**Die Einschränkung, und sie ist der eigentliche Fund.** Das
PRIMÄRMASS ruht auf 4 der 10 Wörter: bei `unter`, `und`, `muß` und
`zwei` steht `marks_uncertain` — die AUTHORED-Referenz enthält dort
gar keinen als Marke klassifizierten Strich (die Hand schreibt den
u-Bogen angebunden, nicht schwebend), also gibt es nichts zu paaren.
Genau diese Wörter zeigen den zweiten Effekt: die Harvest-Regel
`_is_diacritic` (schwebt über der Mittellinie, KEINE Bogenlängen-
Grenze) nimmt den langen u-Bogen als Marke, das Lineal
(`classify_strokes`, Deckel 0,8 xh) zählt ihn als Körper — deshalb
landet seine Verschiebung dort in der Körper-DTW statt in der
Marken-Spalte: `unter` −0,0008 (besser), `und` +0,0010, `muß`
+0,0020. Das ist der gesamte dtw-Effekt des Laufs; er hebt den
Headline-Median um +0,0005 (0,061985 → 0,062474), weil `und` zufällig
auf der Median-Position sitzt. Bei den fünf i-Punkt-Wörtern bleibt
die DTW byte-gleich, weil das Lineal die Marke vor der Körper-DTW
heraustrennt. Kandidat A1b (eigene Vorregistrierung, NICHT Teil
dieses Ergebnisses, weil er nach Sicht der Daten formuliert ist): den
Nachfit auf Striche mit Bogenlänge ≤ `MARK_MAX_ARC_UNITS`
beschränken, also auf genau die Klasse, die „Marke" heißt — der
u-Bogen wäre dann wieder Sache des Körper-Solves.

ENTSCHEIDUNG: **BEHALTEN.** Kein Kill-Kriterium feuert (kein
verlorenes Match, kein zusätzliches `marks_spurious`, Strukturzähler
exakt gleich, keine Netto-dtw-Verschlechterung), und das Primärmaß
mehr als halbiert sich. Der Schalter bleibt vorerst opt-in
(`--mark-refit`, `HarvestOptions.mark_refit`, default AUS): der
Kettenfit-Kandidat ist die eingefrorene Baseline, und ob A1 in die
GESPEICHERTE Bahn wandert, ist ein eigener Autoren-Entscheid — der
Bestätigungssatz (`--split confirm`) ist die Bedingung dafür, weil
vier gepaarte Wörter eine schmale Grundlage für eine Adoption sind.

**Nachmessung `aug19` auf dem 19er-Dev-Satz** (§7.7
Nachkalibrierungs-Protokoll; kein neuer Knopf, dieselbe opt-in
Variante `--mark-refit`, lokale Basis der v0.10/v0.11-Runde):
`mark_pos_err_xh`-Median **0,111 → 0,030 (−73 %)**, ALLE sechs
markentragenden Dev-Wörter verbessern sich (die 0,072 → 0,036 ·
mit 0,106 → 0,019 · linken 0,160 → 0,059 · will 0,150 → 0,078 ·
mit-2 0,116 → 0,023 · die-2 0,055 → 0,019); Körper byte-neutral
(dtw-Δ-Median 0,0000, 10 ties), Marken- und Strukturzähler exakt
unverändert (Galoppierens fehlende i-Marke bleibt fehlend — der
Nachfit repariert Positionen, erfindet keine Striche). Der
Welle-1-Gewinn generalisiert damit auf die 9 neuen Nachfahrungen,
stärker als auf dem 10er-Satz (−55 %). Die Adoptionsbedingung
(Bestätigungssatz) bleibt; die Grundlage ist jetzt 6 statt 4
gepaarte Wörter.

### Welle 1 · K1b `aug15` — Vorregistrierung: der versetzte Stamm-Rückpass des t

Geschrieben und committet VOR der ersten Zahl dieser Maßnahme
(der in K1s Ergebnis benannte Kandidat; Plan
`../proposals/tintenfolger.md` §7.2).

**Hypothese.** Das verbleibende t-Defizit (`unter` `soll_cross` 2
vs. Hand 3 · `soll_zones` 2 vs. 3; `mit` 1 vs. 2 · 1 vs. 2; dazu
`lift_delta` +1 der Kette auf beiden Wörtern) kommt daher, dass die
Komposition zwischen Stammfuß und Deckstrich ABSETZT, wo die Hand
den Stamm mit VERSATZ retraced: Abstrich x≈4,60, Aufstrich x≈4,65,
der Auslauf durchsticht BEIDE Pässe (Kreuzungs-Sites 0,07 xh
auseinander). Ein generierter Rückpass — der Balkenstrich verliert
seinen Lift und wird stattdessen mit einer Brücke Stammfuß →
Balkenstart als Präfix versehen, nach rechts ausgebuchtet um
`BAR_RETRACE_BULGE_UNITS` — stellt Zonen, Kreuzungen und Strichzahl
der Hand wieder her. Vorbild ist der Capital-Retrace
(`cap_retrace`): das Präfix ist generierte Centerline OHNE eigene
Silhouette, die gedruckte Tinte ändert sich nicht (der Versatz
bleibt innerhalb der Schwellzug-Breite).

**Konstante, gemessen statt gewählt.** `BAR_RETRACE_BULGE_UNITS =
0.06`: der Aufstrich der Hand liegt 0,05–0,07 xh rechts des
Abstrichs (unter x≈4,60→4,65; die zwei Kreuzungs-Sites der Hand
liegen 0,07 auseinander und werden vom Zähler als getrennte Sites
geführt — ein kleinerer Versatz würde zu EINER Site verschmelzen).
Nur Basis t; das Präfix wird nur gebaut, wenn der vorige Strich
unterhalb des Balkenstarts endet und horizontal nahe liegt
(Stamm-Geometrie), sonst bleibt der Lift.

**Erwartung.** `soll_cross`: `unter` 2→3, `mit` 1→2 (= Hand);
`soll_zones`: `unter` 2→3, `mit` 1→2 (= Hand);
`soll_cross_agree` 7/10 → 9/10, `soll_zones_agree` 6/10 → 8/10;
Ketten-`lift_delta` auf mit/unter −1 (erst im nächsten
Kettenlauf sichtbar).

**Messgrößen und Kill-Kriterien.**
(a) Die Erwartungs-Zellen oben JE WORT; jedes NICHT-t-Wort, das
eine Übereinstimmung verliert → verworfen. Ein Über-Kreuzen
(`unter` > 3 oder `mit` > 2) → verworfen (Versatz zu groß oder
Präfix kreuzt selbst).
(b) wordbench `--set all`: Headlines nicht > +0,002; Bewegung nur
in t-Wörtern.
(c) compose-golden bricht bauartbedingt → deklarierte Re-Baseline
im selben PR, kein Akzeptanzkriterium.
(d) Die deklarierte Post-K1-Kettenbaseline
(`temp/tb-chain-r1-postk1.json`, Kaskade aus K1) ist der
Vergleichspunkt des nächsten Kettenlaufs; K1b selbst wird zuerst
auf Soll-Ebene abgenommen.

**Ergebnis (gemessen nach dem Commit oben).** Die Erwartung trifft
Zelle für Zelle ein: `soll_cross` `unter` 2→**3** und `mit` 1→**2**
(beide = Hand), `soll_zones` `unter` 2→**3** und `mit` 1→**2**
(beide = Hand), `soll_cross_agree` 7/10 → **9/10**,
`soll_zones_agree` 6/10 → **8/10**; kein Über-Kreuzen, kein
Nicht-t-Wort bewegt. Die per-Letter-Zelle des t wird 2/1 — der
Auslauf durchsticht jetzt Abstrich UND versetzten Aufstrich, wie
die Hand. Unangekündigter Bonus: die 4 `soll_overlap`-Einträge der
t-Wörter (Balken-gegen-Stamm) verschwinden vollständig (Hand hat
dort ebenfalls 0), je eine Berührung bleibt (`mit` 1 vs Hand 2,
`unter` 1 = Hand 1). Verbleibende Abweichler sind die bekannten
Chart-Fälle: `linken` (k zählt im Soll eine Kreuzung mehr als die
Hand schreibt), `Wer` (W-Ansatz-Retrace, Chart-Lücke, Korb) und
`zwei` (z-Retrace, mutmaßlich dieselbe Klasse — bei der
W-Neutracierung mitprüfen). Gates: wordbench `bench_loss` 0,110992
→ 0,110983 (−0,00001), `pair_loss` 0,165688 → 0,165725 (+0,00004,
Schwelle 0,002), bewegt ausschließlich t-Wörter (macht · mit ·
mit-2 · Seiten · Soldaten · fechten · streiten · unter, alle
≤ ±0,0005); compose-golden regeneriert (deklarierte Re-Baseline);
1240 Tests grün. ENTSCHEIDUNG: BEHALTEN. — Nebenbefund, hier
deklariert: die Post-K1-KETTENbaseline `r1` (der Vergleichspunkt
aller folgenden Kettenläufe) unterscheidet sich von `r0` in genau
EINEM Wort: `unter` dtw 0,4389 → 0,4690 (+0,0301) bei einer
erfundenen Kreuzung WENIGER (`cross_spurious` 4→3); die übrigen 9
Wörter sind byte-identisch. Der ohnehin chaotische unter-Fit
reagiert auf die veränderte Initialisierung — die dtw-Zahl der
Kette ist dort schlechter, ihre Topologie besser; der als nächstes
anstehende Kettenlauf (A1) vergleicht gegen r1.

### Welle 2 · P1 `aug15` — Vorregistrierung: die Vorschub-Kalibrierung aus den gemessenen Joins

Geschrieben und committet VOR der ersten Zahl der Maßnahme.
Anlass ist ein Owner-Fund an den K1b-Sichtprüfungs-Overlays: auf
langen Wörtern wandert die Komposition nach hinten sichtbar rechts
von der Specimen-Tinte weg („das Rot muss auf dem Ink liegen").

**Befund (Diagnose-Skripte, Session `aug15`).** (a) Drift-Profil
über die 63 Bench-Wörter — je Slot der best-passende x-Versatz der
komponierten Buchstaben gegen das Specimen-Skelett, ZUSÄTZLICH zur
globalen Registrierung des Lineals: Drift-Median −0,10 xh
(Mittel −0,25), −0,0375 xh je Slot; Vorsicht Arkaden-Aliasing (i/n/m
rasten beim Best-Fit um einen ganzen Bogen, Einzelsprünge ±1 xh sind
Artefakte). (b) Die identitäts-sichere Zahl: die SIGNIERTE
doff-Verteilung über 218 gemessene Joins (pairmeas-Frame, Betrag
durch Vorzeichen ersetzt): Median **+0,05 xh je Join**, 138/218 zu
weit — aber KEIN globaler Faktor, sondern zwei Klassenfehler in
Gegenrichtung: zu WEIT laufen Ausgänge aus Rundkörpern/Schleifen und
Eingänge in e/r (b→e +0,41 · f→e +0,31 · o→r +0,30 · c→h +0,25 n=6 ·
w→e +0,20 · t→e +0,15 · e→r +0,14 n=13 · d→e +0,12); zu ENG laufen
Eingänge in die Arkaden (e→n −0,13 n=12 · u→n −0,23 · i→n −0,24 ·
n→n −0,21 · u→m −0,31) sowie r→e (−0,66 n=3 — Verdacht
Frame-Kaveat des Arm-Fuse, vor jeder Korrektur visuell prüfen).

**Maßnahme in zwei Stufen.**
(i) MECHANISMUS-ATTRIBUTION statt additiver Fudges: die Komposition
bekommt unter `provenance=True` ein report-only Feld, das je
platziertem Glyph benennt, WELCHE Platzierungsregel gefeuert hat
(Fork/Bar-Rise/Arm-Fuse/Girlande/High-Couple …) und ob der
Ink-Clearance-Floor gebunden hat; die 218 signierten Fehler werden
danach gruppiert. Erwartung: die Zu-weit-Klasse korreliert mit
gebundenem Clearance-Floor bzw. einer benennbaren Kopplungsregel,
die Zu-eng-Klasse mit der Girlanden-Kopplung. Sonderfrage: hat K1s
Balken-Tail den t→e-Vorschub über den Ink-Floor verschoben?
(ii) REGEL-FIX der(s) verantwortlichen Mechanismus(se) — Klassen-
regel, kein Pair-Override, Konstanten aus den gemessenen Medianen.

**Messgrößen und Kill-Kriterien.**
(a) Primär: wordbench `word_loss` fällt (trans ist die größte
Komponente); ein Fix, der `word_loss` nicht senkt, wird verworfen.
(b) Die signierte doff-Verteilung: Klassen-Mediane bewegen sich
Richtung 0, der Gesamt-Median |≤ 0,02|; keine Klasse darf das
Vorzeichen ÜBERSCHIESSEN (neuer Betrag > alter Betrag = verworfen).
(c) Struktur-Wächter: `soll_cross_agree`/`soll_zones_agree`
unverändert (Platzierung darf keine Topologie kaufen).
(d) `pair_loss` nicht über +0,002; compose-golden bricht
bauartbedingt → deklarierte Re-Baseline im selben PR.
(e) Stufe (i) ist report-only und muss headline-byte-identisch
sein; zusätzlich wird eine report-only DRIFT-Spalte im Bench
erwogen (eigener, kleiner Schritt — nie Teil eines Loss).
(f) Kill für Stufe (ii): erklärt kein Mechanismus die Mehrheit
seines Klassenfehlers, wird NICHT gefixt, sondern der Befund als
ehrliches Negativ dokumentiert und die Frage an die nächste
Werkzeug-Stufe (H2-Klassen-Statistik) zurückgegeben.

**Stufe (i) gemessen — die Attribution trennt sauber** (Feld
`placement` am Konnektor unter `provenance`, golden/Payload
byte-identisch, 73 Tests grün). Die 218 signierten Fehler nach
entscheidender Regel: `clearance_floor` **n=116** (der
Ink-Clearance-Floor entscheidet die HÄLFTE aller Platzierungen),
median +0,048 — aber gespalten: nach RUNDEM linken Buchstaben
**+0,206 (n=47)**, in ARKADEN (n/m) **−0,182 (n=31)**, in e +0,104
(n=18). Dazu `backward_clearance` **+0,189 (n=19)** (w/v-Bögen),
`bar_rise` **+0,159 (n=6)** (die t-Steiglinie), `align(_floor)`
+0,07 (n=36, mild), `connect_gap` −0,042 (n=26, fein),
`arm_fuse` **−0,507 (n=5)** — wie vorregistriert VOR jeder
Korrektur visuell zu prüfen (Frame-Kaveat-Verdacht). Lesart: der
EINE Floor trägt beide Klassenfehler mit entgegengesetztem
Vorzeichen — die Hand lässt Arkaden MEHR Luft und taucht nach
Rundkörpern ENGER in die Lücke, als die einheitliche Clearance
erlaubt; dazu zwei klar überschießende Spezialregeln (Rückwärts-
Clearance, Balken-Steiglinie). Stufe (ii) kalibriert genau diese
vier Stellen aus den gemessenen Medianen; `arm_fuse` erst nach
Sichtprüfung.

**Stufe (ii) gemessen — Einzelzerlegung, drei adoptiert, eine
ehrlich verworfen.** Vorab die `arm_fuse`-Sichtprüfung: das
Defizit ist REAL (Drift +0,49 und doff −0,66 zeigen in dieselbe
Richtung, das fusionierte e sitzt sichtbar zu nah am r), aber mit
der LÄNGE des r-Arms im Template verschränkt — eine reine
Platzierungskorrektur risse die Berührung auf; bleibt draußen
(eigener Kandidat, mutmaßlich Chart-/Laufform-Stufe). Der
Gesamt-Fix aller vier Kalibrierungen verletzte Gate (a)
(`word_loss` 0,110983 → 0,114252 bei `pair_loss` −0,023) — die
Einzelzerlegung fand die Ursachen: **Bowl-Voll-Tuck** (Clearance
−0,06, erlaubte Überlappung) allein: words +0,0015 / pairs −0,022
— die Überlappung kollidiert im Wortkontext; **gebundener Tuck**
(Clearance 0,0, Berührung statt Überlappung): words −0,0001 /
pairs **−0,018** — hält fast den ganzen Paar-Gewinn ohne
Wort-Kosten → ADOPTIERT. **Arkaden-Luft** (0,32) allein: words
+0,0043, pairs unbewegt → VERWORFEN als ehrliches Negativ (das
per-Dissektion gemessene Defizit −0,18 bleibt stehen und
unerklärt adressiert; Wiedervorlage am Bestätigungssatz).
**Rückwärts-Clearance** 0,30 → 0,11: words −0,0019 / pairs
−0,0013 → ADOPTIERT (die jul-11-Kalibrierung 0,30 war gegen das
Overlay der Vor-Registrierungs-Ära gelesen). **Balken-Steigung**
0,55 → 0,69: ruler-neutral (words +0,00003), doff-wahr →
ADOPTIERT. **Endstand A′+C+D:** `word_loss` 0,110983 →
**0,108991** (Gate a ✓), `pair_loss` 0,165725 → **0,146602**
(größte Paar-Verbesserung der Bench-Historie), `meas_doff`-Median
0,195 → **0,131**; signierte Klassen-Mediane: gesamt +0,050 →
**+0,010** (Ziel |≤0,02| ✓), backward +0,189 → −0,001, bar
+0,159 → −0,040, Bowl-Floor +0,206 → +0,049 — nichts überschießt
(Gate b ✓). Gate (c): `soll_cross_agree` 9/10 unverändert,
`soll_zones_agree` 8/10 → **9/10** — `zwei` gewinnt durch die
kalibrierte w-Platzierung seine zweite Retrace-Zone (= Hand); die
einzigen Rest-Abweichler sind die zwei Chart-Fälle (linken-k,
Wer-W). compose-golden als deklarierte Re-Baseline regeneriert,
1260 Tests grün. Die Werte-Historie der Wordbench-Headline wird in
§6 beim nächsten Release-Schnitt nachgeführt. Ehrliche
per-Wort-Streuung der Median-Kalibrierung, benannt statt
versteckt: `unter` 0,107 → 0,083 und `fechten` 0,222 → 0,173
gewinnen groß, `streiten` verliert einzeln 0,114 → 0,189 — es ist
das einzige Dev-Wort mit ZWEI t-Exits (t→r und t→e), die
Steigungs-Kalibrierung wirkt doppelt und die globale Registrierung
verteilt den Rest übers Wort (longs→t springt von 0,03 auf 0,36,
ohne dass eine adoptierte Regel diesen Join berührt). Die
t-Join-Stichprobe ist dünn (n=6, Spanne +0,15…+0,21) — der
Bestätigungssatz prüft die 0,69 nach.

**Nachtrag P1b `aug15` — der streiten-Fund des Owners korrigiert
die Rückwärts-Klasse.** Die t-Exit-Attribution des Absatzes oben
war FALSCH: die per-Join-Nachmessung an `streiten` selbst zeigt
die t-Joins nach der Kalibrierung fast perfekt (t→r −0,067 ·
t→e −0,040) — der Schuldige ist `longs→t`, denn der
longs-Abschwung exitiert RÜCKWÄRTS und fiel mit in die pauschal
reduzierte Rückwärts-Clearance (−0,156 per Dissektion, und die
globale Registrierung schob das ganze Wort neben die Tinte —
Owner: „gleich der erste Buchstabe liegt nicht übereinander").
Die Klassen-Nachmessung je linkem Buchstaben: w/v (n=12) wollen
die 0,11 (jetzt +0,02, alt +0,21), Versal-W will sie ebenfalls
(per Ruler UND Dissektion), die übrigen Versalien sind
n=1-Singletons mit Ruler-Dissektions-Konflikt und bleiben beim
Ruler-Präferenzwert 0,11 — die benannte AUSNAHME ist `longs`
(`LONGS_BACKWARD_CLEARANCE` 0,30): sein Abschwung-Rücklauf
braucht den alten Raum (die zwei Bench-longs-Wörter splitten ihr
Ruler-Votum ±0,03, die einzige dissezierte longs-Zeile stimmt für
0,30; Wiedervorlage am Bestätigungssatz). Endstand P1b:
`word_loss` 0,108991 → **0,108446**, `pair_loss` unverändert
0,146602, gegen den gemergten P1-Stand bewegt sich EXAKT ein Wort
(`streiten` 0,189 → 0,154), Soll-Agree unverändert 9/10 · 9/10,
compose-golden regeneriert (deklarierte Re-Baseline). Der
Fehlversuch dazwischen — ALLE Nicht-w/v-Rückwärts-Exits auf 0,30
zurück — wurde gemessen und verworfen (words +0,0009, drei Wörter
regressieren): auch eine Korrektur-Klasse kann zu breit
geschnitten sein.

### Welle 2 · P2 `aug15` — Vorregistrierung: die align-Klasse und der Arkaden-Varianz-Befund

Geschrieben und committet VOR der ersten Zahl der Maßnahme; setzt
die Owner-Direktive „die x-Verschiebung ist noch real, weitermachen"
um. Zwei Teile — eine Kalibrierung und ein GESCHLOSSENER Befund.

**(A) Arkaden-Luft — geschlossen als Hand-Varianz, KEIN
Kalibrierfehler.** Die Dissektion verlangt +0,18 Luft vor Arkaden,
das Lineal lehnt jede getestete Dosis ab (0,32: words +0,0037 ·
0,23: +0,0008). Der Mechanismus-Test löst den Widerspruch: unter
Luft wird `wenn` besser (−0,030) und `wenn-2` — DASSELBE Wort,
anderer Beleg — deutlich schlechter (+0,089); die vier
`und`-Belege stimmen gemischt ab; die dissezierten
Arkaden-Deltas streuen MAD 0,096 (p10..p90 −0,13..+0,12) bei
Median −0,004 unter Luft. Die Hand schreibt die Arkaden-Weite von
Beleg zu Beleg ±0,1 xh verschieden — die Komposition kann nur
EINEN Punkt im Band wählen und bleibt am Ruler-Punkt. Keine
Konstante wird geändert; Wiedervorlage ausschließlich mit dem
Bestätigungssatz.

**(B) align-Klasse — die letzte kalibrierbare Vorschub-Masse.**
36 gemessene Joins, Median +0,072, und der Fehler ist
STEIGUNGS-UNABHÄNGIG (klein-rise +0,069 / groß-rise +0,074,
Korrelation −0,28) — also ADDITIV, kein Steigungsproblem wie beim
Balken. Zwei Unter-Mechanismen, je ein Knopf, Einzelzerlegung wie
P1: (i) die reine Durchlauf-Diagonale (`align`, n=19, +0,074) —
ein gemessener Abzug `ALIGN_ADVANCE_TRIM_UNITS = 0.07` auf das
Diagonalen-Ziel; (ii) der gebundene align-Floor (`align_floor`,
n=17, +0,069) — `ALIGN_MIN_CLEARANCE` 0,06 → **0,0**: dieselbe
Berührungs-Semantik wie der adoptierte Bowl-Tuck (Spalten dürfen
sich berühren, nie überlappen).

**Messgrößen und Kill-Kriterien** (identisch zur P1-Familie):
(a) wordbench `word_loss` fällt gegen 0,108446, sonst verworfen —
je Knopf einzeln UND in Kombination gemessen; (b) die
align-Klassen-Mediane bewegen sich Richtung 0 ohne Überschießen;
(c) `pair_loss` nicht > +0,002; (d) `soll_*_agree` unverändert;
(e) compose-golden bricht bauartbedingt → deklarierte Re-Baseline.
Erwartete Ausreißer, vorab benannt: `Z→a` +0,94 und `a→n` −0,645
sind n=1-Extreme und werden von keiner Konstante gejagt.

**Ergebnis (gemessen nach dem Commit oben).** Einzelzerlegung wie
registriert: Knopf (i), der Diagonalen-Trim, wird vom Lineal bei
jeder Dosis abgelehnt (0,07 allein: +0,0020 · 0,035 auf dem Floor:
+0,0011) — dasselbe Beleg-Varianz-Verdikt wie die Arkaden-Luft;
die Konstante bleibt DEKLARIERT-ABER-NEUTRAL (0,0), die
Dissektions-Forderung steht für den Bestätigungssatz im Protokoll.
Knopf (ii), der Berührungs-Floor (`ALIGN_MIN_CLEARANCE` 0,06 →
0,0), BESTEHT: `word_loss` 0,108446 → **0,108091**, `pair_loss`
byte-gleich, `soll_*_agree` unverändert 9/10 · 9/10. Die Streuung:
9 Wörter besser (voran `fechten` 0,173 → **0,144** — sein
f→e-align_floor war der +0,31-Ausreißer; kumuliert seit Beginn der
Vorschub-Runde 0,222 → 0,144), größter Einzelverlierer `Zaum`
+0,022 (der vorab benannte `Z→a`-Ausreißer reagiert auf den
Floor). compose-golden regeneriert (deklarierte Re-Baseline),
1260 Tests grün. ENTSCHEIDUNG: Floor ADOPTIERT, Trim NEUTRAL.
Damit ist die kalibrierbare Vorschub-Masse der 218 gemessenen
Joins abgearbeitet: adoptiert Bowl-Tuck · w/v-Rückwärts ·
longs-Ausnahme · Balken-Steigung · align/nested-Floor; als
Beleg-Varianz geschlossen Arkaden-Luft · Diagonalen-Trim; offen
bleiben die zwei NICHT-Kalibrier-Fälle `arm_fuse`/r-Arm-Länge
(Chart-Frage) und `descender_ride` (n=2, zu dünn).

### Welle 2 · P3 `aug16` — Vorregistrierung: Kopf-Koartikulation als Entry-Klassenregeln

Geschrieben und committet VOR der ersten Zahl der Maßnahme.
Owner-Priorität „zeitnah" (2026-08-15): kontextabhängige
Kopf-/Schwanz-Flexibilität der Buchstaben als nächster
Composer-Baustein nach der Vorschub-Runde.

**Vorstudie (Session `aug15`, 248 Vorkommen / 134 Paare über
words+pairs).** Werkzeug: `pairlab.dissect_occurrence(trace=True)`
über alle Fixture-Vorkommen, mit Zerlegung der M4-Ankerverschiebung
in starren Anteil (Median über die Körperanker), Längs-/Quer-
Residuum an der Template-Tangente und die verschiebungs-invariante
Reichweite des ganzen Anschluss-Strichs; Permutationstests;
Skripte im Session-Scratchpad (`coart.py --against laufform`,
Rohdaten `coart_lauf.json`). Der Befund ist eine ASYMMETRIE:

(a) Der SCHWANZ (linke Seite) ist KEINE Koartikulation: die
Umformung hängt nicht vom Nachfolger ab (p = 0,19–0,55) und ist je
Exit-Klasse eine Konstante mit winzigem MAD (Arkaden +0,079 ±
0,011 · d −0,144 ± 0,010 · Balken −0,053 ± 0,010). Das ist eine
Chart-/Laufform-Frage und AUSSERHALB dieses Eintrags — ebenso der
pauschale +7–10-%-Reichweitenzuwachs des Anschluss-Strichs.
(b) Der KOPF (rechte Seite) IST Koartikulation: nach einem
Hoch-Exit (Balken, d-Schleife, Deckstrich-Bogen, r-Arm) sitzt der
Ankunftspunkt +0,10 xh weiter rechts und +0,10 xh höher, der
Eingangs-Strich ist 0,09–0,15 xh kürzer als nach flachem Exit
(p < 0,0001 in jeder geprüften Population). Die Laufform trägt
davon nur ein Viertel des Betrags und nichts vom Senkrechten
(Δ 0,084 xh, p < 0,00002) — sie KANN es bauartbedingt nicht
tragen, weil sie eine Form je Glyph ist. Deshalb Klassenregeln im
Composer; alle Konstanten LAUFFORM-relativ erhoben (pairlab misst
gegen die Chart-Zeile, komponiert wird die Laufform).

**Die drei vorregistrierten Entry-Regeln** (Median ± MAD in xh;
Basislinie `arkade→arkade` n = 65: Reichweite +0,093 ± 0,017,
cp dx −0,046 ± 0,010, Ankunft y 0,570 ± 0,033). Umsetzungs-
Reihenfolge **K1 → K3 → K2** (K1 = schärfster Effekt, K3 = reine
Höhenregel = billigster Eingriff, K2 = riskantester wegen des
zweimal verworfenen Stub-Trims), je Regel EIN Knopf mit eigener
Leiter, gepaart gemessen, erst adoptieren, dann die nächste:

* **P3-K1 · Balken → Rundkörper** (`BAR_EXIT_BASES` t/f → e/a/o
  …): gemessen cp dx **+0,157 ± 0,002**, cp dy +0,075 ± 0,011,
  Kopfstrich-Reichweite −0,089 ± 0,005 (n = 7: t→e, f→e);
  compose-relativer Ankunftswinkel **+126,1° ± 4,3** — der Zug
  kommt heute praktisch aus der Gegenrichtung an. Regel: nach
  Balken-Exit koppelt der Verbinder TIEFER auf der Anstiegsflanke
  (Soll-Ankunft y ≈ 0,56 statt einheitlich `ENTRY_COUPLE_Y` 0,78)
  und der Entry-Stub verliert ≈ 0,09 Reichweite. Knopf: klassen-
  eigenes `BAR_ENTRY_COUPLE_Y`, Leiter 0,50 / 0,56 / 0,62 / 0,78
  (= aus).
* **P3-K3 · Deckstrich-Bogen → Arkade** (o/b/v/w → n/m/i/r):
  gemessen cp dy **+0,074 ± 0,022** bei cp dx +0,038 ± 0,011 und
  Reichweite −0,001 ± 0,027 (n = 6: o→n, b→i, w→i, o→r),
  Soll-Ankunft y 0,685 gegen Basislinie 0,570. Reine HÖHEN-Regel,
  kein Längeneingriff. Knopf: Anhebung des Arkaden-Ankunftspunkts
  nach Deckstrich-Exit, Leiter +0,00 / +0,07 / +0,11.
* **P3-K2 · Schleifen-Exit → Rundkörper** (d → e/a/o): gemessen
  Kopfseite cp dx +0,080 ± 0,025, cp dy +0,052, Reichweite −0,086
  (n = 8), Soll-Ankunft y 0,628; A-Seite d-Abgangswinkel
  compose-relativ **+48,0° ± 0,8** bei Reichweiten-Wachstum in
  0 von 18 Vorkommen. **Ausdrücklich: der reine d-Stub-Trim ist
  zweimal gemessen-und-verworfen (`jul11`, `jul17`/PR #220) und
  wird NICHT wiederholt** — das neue Signal ist der WINKEL, nicht
  die Länge. Knopf: Drehung des d-Abgangswinkels Richtung
  gemessener Tangente, Leiter +0° (= aus) / +24° / +48°.

**Nicht in dieser Vorregistrierung** (benannt, damit es niemand
hineinliest): (a) `arm_fuse`/r→e — die Formeffekte erklären ≤ 20 %
der −0,51-Lücke, bleibt Platzierung/Armlänge, wie P1 schloss;
(b) der pauschale Reichweitenzuwachs (Chart-/Laufform-Frage);
(c) alle Versal-Paare (n=1-Singletons).

**Messgrößen und Kill-Kriterien** (wie die P1-Familie).
(a) Primär: wordbench `word_loss` UND `pair_loss` (eingefrorenes
Lineal) dürfen nicht steigen; Erwartung ist Verbesserung auf den
Wörtern der jeweiligen Klasse. (b) Die signierte doff-Attribution
der betroffenen Klasse bewegt sich Richtung 0, ohne das Vorzeichen
zu ÜBERSCHIESSEN. (c) Struktur-Wächter: `soll_cross_agree`/
`soll_zones_agree` je Wort unverändert (eine Entry-Regel darf
keine Topologie kaufen). (d) Sichtprüfung der betroffenen Wörter.
(e) Jede Regel bricht deklariert das compose-golden (Entry-
Kopplung ändert komponierte Bahnen): REGEN_GOLDEN=1-Re-Baseline im
selben PR, letter-only bleibt byte-identisch. (f) Kill: eine
Regel, die ihre eigene Klasse verbessert, aber `word_loss`/
`pair_loss` verschlechtert, wird verworfen, nicht nachgestimmt;
ein K2, dessen Winkel-Drehung das Fehlerbild der verworfenen
Stub-Trims reproduziert, widerlegt die Winkel-Hypothese —
ehrliches Negativ mit Datum; keine Adoption allein auf der
Klassen-Metrik.

**Grenzen (aus der Vorstudie übernommen).** Zensur bei ≈ 0,17 xh:
das M4-Trace-Fenster ist Körperbreite ± 0,15 xh, das |cp dx|-
Histogramm bricht genau dort ab — alle Beträge sind UNTERE
Schranken. Konfundierte Köpfe h/d/l (nur ein Kontext) begründen
keine Regel — trennbar sind e (7 Kontexte), i (5), r (4), a (3).
Eine Hand, eine Norm (96 Proben). Kleine Klassen-n (K1 n=7 ·
K3 n=6 · K2 n=8+18) → das Nachkalibrierungs-Protokoll
(tintenfolger.md §7.7) greift, sobald der Bestätigungssatz
nachgefahren ist.

**P3-K1 gemessen `aug16` — verworfen per eigenem Kill, der Fund
ist die Frame-Brücke.** Umsetzung als geteilter Kopplungsindex
(`BAR_ENTRY_COUPLE_Y`; Platzierung und Verbinder lesen denselben
Anker; die Steig-Wächter für den flachen K1-Zug klassenbewusst
gelockert), Feuer-Nachweis exakt in der Klasse und nirgends sonst
(fechten f→e + t→e, streiten/unter/Seiten/Soldaten/scharfen t→e
bzw. f→e; macht/mit mit wortfinalem t byte-identisch; das
compose-golden deckt die Klasse mit keinem seiner Wörter ab und
blieb daher UNGEBROCHEN — die „bricht bauartbedingt"-Erwartung
der Vorregistrierung war falsch herum). Leiter gegen die
P2-Baseline 0,108091: 0,50 feuert nie (e-Anstrich startet über
dem Ziel — die Leiterstufe war leer), 0,56 → 0,108145 · 0,62 →
0,108190 · 0,78 → 0,108120; `pair_loss` byte-identisch (die
Abb.-20-Drills enthalten kein Balken→Rund-Paar), doff-Median
0,130 → 0,132, nicht-monoton je Wort (fechten −0,0059 bei 0,56,
+0,0023 bei 0,62, −0,0041 bei 0,78). Auf JOIN-Ebene stimmen die
Belege GEGENEINANDER: fechtens t→e halbiert sich (0,12 → 0,06),
streitens verschlechtert sich (0,04 → 0,07), unter bevorzugt
0,78 (0,11 → 0,10). Kill (a) feuert (word_loss steigt bei jedem
feuernden Arm, die Klasse verbessert sich nicht kohärent), also
VERWORFEN; `BAR_ENTRY_COUPLE_Y` bleibt DEKLARIERT-ABER-NEUTRAL
(None) für die Bestätigungssatz-Nachkalibrierung (K1 ruht auf
n = 7). Der Fund: die Vorstudien-Konstanten sind im FIT-Frame
kohärent (MAD 0,002!), aber die Brücke in den Composer — der
Kopplungshöhen-Knopf bei gebundener Floor-Platzierung
(`bar_rise_floor` bindet in allen Klassenwörtern) — reproduziert
sie nicht: dieselbe Arkaden-Lektion (Beleg-Varianz am
Ruler-Punkt) eine Klasse weiter, PLUS die neue Hypothese, dass
nicht die KOPPLUNGSHÖHE, sondern die VERBINDERFORM (gekrümmter
Einfall statt gerader Balken-Linie) den +126°-Ankunftsfehler
trägt — das wäre ein anderer Knopf und braucht seine eigene
Vorregistrierung. K3 und K2 werden trotzdem gemessen (andere
Mechanismen), mit entsprechend gedämpfter Erwartung.

**P3-K3 gemessen `aug16` — verworfen am Paar-Gate; der Fund ist
der Wort/Drill-Split.** Vorab die Diagnose: die Klasse koppelt
heute INKONSISTENT — o→r trimmt auf den generischen 0,78-Punkt
(ÜBER dem Soll-Band 0,685), o→n/w→i koppeln am Chart-Fuß
(0,58–0,63, darunter), weil ein Spline-Resampling-Zittern von
0,0004 xh den strengen Monotonie-Wächter von
`_entry_couple_index` abbrechen lässt — der generische O2-Trim
ist für Arkaden-Köpfe still deaktiviert (eigener
Bugfix-Kandidat, nicht in dieser Regel behoben; K3 nutzt einen
jitter-toleranten lokalen Scan, Schwelle 0,02/Sample). Regel
umgesetzt als klassen-einheitliche Kopplung bei Fuß + Lift
(ersetzt beide Fehlstände), Feuer-Nachweis exakt in der Klasse
(von o→n · will w→i · Zorn/Sporn o→r · Drills on/bi/wi),
Kontrollen (kann/wenn/schwer/zwei) byte-identisch, das
compose-golden bricht hier WIRKLICH (wovon/Morgen tragen die
Klasse). Leiter: words 0,108091 → 0,108082 (0,07) → 0,107971
(0,11) — die WÖRTER stimmen erstmals größtenteils GLEICHGERICHTET
für die Regel (von −0,0090 · will −0,0019 · Sporn +0,0002 ·
Zorn +0,0031); aber pairs 0,146602 → 0,147337 (0,07) → 0,147162
(0,11), getragen vom Drill `on` (+0,0172, dazu bi +0,0018,
wi −0,0006). Gate (a) verlangt BEIDE Lineale → VERWORFEN,
`COVER_ARCADE_ENTRY_LIFT` bleibt DEKLARIERT-ABER-NEUTRAL (0,0)
für die Bestätigungssatz-Nachkalibrierung (K3 ruht auf n = 6).
Der Fund: das Wort `von` und der Drill `on` — nach H2-Doktrin
DERSELBE Übergang derselben Hand — stimmen am Ruler
GEGENEINANDER (−0,0090 vs. +0,0172); die Beleg-Varianz-Serie
(Arkaden-Luft · K1 · K3) hat damit ihre dritte Ausprägung:
Wort-Platte vs. Paar-Drill. Offen bleibt der gemessene
o→r-Überstand (0,78 komponiert vs. 0,685 Soll), den Zorn beim
Absenken trotzdem ablehnt.

**P3-K2 gemessen `aug16` — eindeutig verworfen: beide Lineale
monoton gegen die Drehung.** Umsetzung als gedrehter Abgang auf
dem geretteten Chord (`LOOP_ROUND_EXIT_ROT_DEG`; der d→Rund-Zug
ist heute der High-Reversal-gerettete STRAIGHT-Chord — die Kubik
krümmt mit gedrehtem d_out den Start, die Ankunft behält ihren
Chord; der zweimal verworfene Stub-Trim blieb unangetastet).
Feuer-Nachweis exakt in der Klasse (laden/der d→e · das/Soldaten
d→a · Drill do; die d→i still), nur das Verbinder-Item bewegt
sich. Leiter: words 0,108091 → 0,108286 (+24°) → 0,108409
(+48°), pairs 0,146602 → 0,146694 → 0,146764 — BEIDE Lineale
monoton schlechter, ohne Klassen-Split. Kill (a) feuert glatt →
VERWORFEN, Konstante bleibt deklariert-aber-neutral (0,0). Damit
ist die P3-Runde KOMPLETT: alle drei vorregistrierten
Entry-Regeln sind gemessen und ehrlich negativ — die im
FIT-Frame hochkohärenten Kopf-Konstanten der Vorstudie
überleben die Brücke in den Composer an KEINEM der drei
registrierten Knöpfe am aktuellen Ruler-Punkt. Stehend bleiben:
(i) die Verbinderform-Hypothese für den +126°-Balken-Fehler
(eigene Pre-Reg), (ii) der Jitter-Bugfix am O2-Trim (eigene
Pre-Reg, latent für ALLE Arkaden-Köpfe), (iii) die
Nachkalibrierung aller drei Knöpfe am Bestätigungssatz
(Klassen-n 6–8 sind der wahrscheinlichste Grund, warum
Median-Regeln gegen Beleg-Varianz verlieren).

### Wächter als Produktions-Kette `aug16` — Vorregistrierung: die gewachte Bahn wird die gespeicherte

Geschrieben und committet VOR der ersten Zahl der Messung.
Owner-Entscheid der Namensrunde (2026-08-16): „Kette+ sollte
einfach das einzige Kette sein" — fit-erfundene Kreuzungen sind
nie richtig (join-gebildete stecken im Soll-Budget, Hand-vs-
Komposition-Lücken sind Composer-Defekte). Die Duell-Seite zeigt
das schon; DIESER Eintrag misst die PRODUKTIONS-Seite: sollen die
`traced`-`word_instances` (die 53 nicht nachgefahrenen Wörter +
Drills) künftig die STRUKTUR-GEWACHTE Bahn speichern statt der
rohen Kettenfit-Bahn?

**Konfiguration.** Exakt die Ebene, die die Duell-Seite als
„Kette" führt: `follow_word_chain` mit `structure_guard` (Arm ⑨,
Budget aus der eigenen Chain-Initialisierung, Retry-Leiter wie
released) auf der Basis `prox 0.1 · rounds 2 · coverage 0.3`;
Kontroll-Arm die rohe Kette (`rounds 0`, derselbe Codepfad).
Beide über ALLE 63 Wörter des words-Sets (nicht nur die 17
Dev-Fälle — die Produktion speichert alle).

**Bindende Leitplanke (aus §2.2 der Kampagne):** der Tausch darf
NUR `word_record["strokes"]` betreffen — `occurrences`,
`letter_gate`, `instances` und alle Messungen bleiben die des
Kettenfits; `pair_aggregates` sieht Chain-Verbinder ohnehin nie.
Kein DB-Write in diesem Schritt: die Messung läuft offline über
die eingefrorenen Fixtures; der Re-Harvest selbst braucht
Owner-Go + dbsnapshot und `provenance` bleibt `traced`
(`fit_path` würde die gewachte Herkunft tragen).

**Messgrößen.** (a) Auf den 10 authored-Referenzen: `dtw_xh`
gepaart gewacht vs. roh — Arm ⑨ maß Δ exakt 0 auf den Dev-Fällen,
erwartet wird NEUTRALITÄT. (b) Auf ALLEN 63 Wörtern (referenzfrei
messbar): die Strukturzähler v2.1 gegen das je-Wort-SOLL
(`soll_cross`/`soll_zones`-Abstände) — die rohe Kette erfand auf
den Dev-Wörtern ~21 Kreuzungen über ihre eigene Initialisierung
(laden 3→11, unter 3→12); erwartet wird, dass die gewachte Bahn
je Wort näher am Soll liegt und NIRGENDS weiter. (c) `aiou`
gegen die Tintenmaske je Wort (darf nicht fallen — der Wächter
darf Ink-Deckung nicht kaufen, indem er sie opfert). (d) Marken:
`marks_missing/spurious` unverändert. (e) Laufzeit je Wort
(Produktions-Tauglichkeit; die Retry-Leiter kostet).

**Gates und Kill-Kriterien.** Adoptions-Empfehlung nur wenn:
(i) dev-`dtw_xh` gepaart |Median-Δ| ≤ 0,002 und kein Einzelwort
über +0,01; (ii) Struktur-Abstand zum Soll (Kreuzungen + Zonen,
je Wort) gewacht ≤ roh ÜBERALL und irgendwo strikt besser;
(iii) `aiou`-Median fällt nicht (> −0,005); (iv) Marken
unverändert; (v) kein Wort scheitert (failed/skipped) das roh
durchläuft. Kill: EIN Wort mit MEHR Soll-Abstand als roh →
nicht adoptiert (der Wächter-Kontrakt wäre gebrochen — das wäre
ein Bug, kein Tuning-Fall); Laufzeit im Mittel > 5 min/Wort →
Empfehlung nur mit benanntem Budget. Ergebnis wird hier datiert
nachgetragen; die ADOPTION selbst (Re-Harvest, DB) bleibt ein
eigener Schritt hinter Owner-Go.

**Gemessen `aug16` — drei Gates bestehen glänzend, das
Struktur-Gate findet die LÜCKE des einseitigen Wächters.** Beide
Läufe 63/63 ok (roh 87 min · gewacht 5,3 h = 302 s/Wort — HAARE
über dem 5-min-Budget von Gate (e), benannt). (i) dev-`dtw_xh`:
Median-Δ exakt 0,0000, drei Wörter BESSER (unter −0,0300 ·
und −0,0077 · mit −0,0003), keins schlechter — mehr als
Neutralität. (iii) `aiou` fällt NIRGENDS (min-Δ 0,0000, max
+0,1103). (iv) Marken byte-gleich. ABER Gate (ii): 1 Wort näher
am Soll (unter 3→2, eine Zonen-Erfindung weg), 59 gleich,
**3 Wörter WEITER weg** — und alle drei sind Kreuzungs-VERLUSTE
(Sporn cross 3→2 bei Soll 3 · einer 1→0 bei Soll 1 · er-3 1→0
bei Soll 1): der released Wächter deckelt nur ERFINDUNGEN über
das Init-Budget, die Tinten-Anziehung darf aber ungestraft eine
kleine Schleife KOLLABIEREN. Per Kill-Kriterium NICHT adoptiert.
Rettungsweg (benannt nach §7.9-Regel, hier sofort ausgeführt):
**der zweiseitige Wächter** — die K0-Invariante sagt, die
Strukturzahl ist deterministisch aus dem Duktus, also ist das
Init-Budget in BEIDE Richtungen bindend; ein Round, der eine
Init-Kreuzung verliert, wird genauso zurückgewiesen wie einer,
der eine erfindet.

**Vorregistrierter Folge-Arm (zweiseitig), VOR seiner ersten
Zahl:** identische Konfiguration, `structure_guard` prüft
Gleichheit statt Obergrenze (`--structure-guard-two-sided`,
Retry-Leiter unverändert). Erwartung: die drei Verluste
verschwinden (Retry oder Rückfall auf die Vorrunden-Geometrie),
unter behält seinen Gewinn, dev-dtw bleibt im (i)-Band —
plausibel opfert `unter` einen Teil der −0,0300, wo der Gewinn
aus einem Verlust-Round kam. Gates unverändert die von oben;
Kill unverändert: EIN Wort weiter vom Soll als roh → nicht
adoptiert.

**Zweiseitig gemessen `aug16` — erst der Umgebungs-Fund, dann
ein sauberes Pareto-Bild.** Der erste Vergleich (2s gegen die
Nacht-Baseline) zeigte 6 scheinbare Regressionen — die Isolation
entlarvte sie als MESSFEHLER DES AUFBAUS: **der Ketten-Solve ist
über BLAS-Thread-Umgebungen hinweg nicht bit-reproduzierbar**
(dasselbe Wort, derselbe Code, rounds 0: capped-1-job vs.
uncapped-3-jobs ergeben verschiedene Bahnen; an
Struktur-Grenzfällen kippen dann Zähler). Der Revert-Pfad des
Wächters ist dagegen KORREKT (Isolations-Paar rounds-0 vs.
zweiseitig-revertiert byte-identisch). Zwei Konsequenzen,
stehend: Solve-Vergleiche nur noch in IDENTISCHER Umgebung
(`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS` gepinnt), und eine
Produktions-Verdrahtung muss die Thread-Zahl pinnen. Nebenbei
löste der Pin das Laufzeit-Gate (e) vollständig: die
Thread-Übersättigung (3 Worker × ~15 Threads auf 8 Kernen) war
der ganze Kostentreiber — gedeckelt läuft die rohe Kette über
63 Wörter in 2,7 min und der ZWEISEITIGE Wächter in 18,3 min
(≈ 17 s/Wort, weit unter dem 5-min-Budget; einseitig-ungedeckelt
waren es 5,3 h).

Der SAUBERE Vergleich (Kette und 2s-Wächter in identischer
Umgebung, 63/63 ok): Gate (ii) Struktur: **0 besser · 63 gleich ·
0 schlechter** — Gesamt-Soll-Abstand exakt 104 = 104; der
beidseitige Veto friert die Struktur konstruktionsbedingt auf
Init-Niveau ein (auch unters Zonen-REPARATUR aus dem einseitigen
Lauf wird vetiert — der Preis der Symmetrie). Gate (i) dev-dtw:
Median-Δ 0,0000, max-Δ 0,0000, zwei Wörter besser (und −0,0077 ·
mit −0,0003), keins schlechter. Gate (iii) aiou: min-Δ −0,0023
(Sporn, über der −0,005-Schranke), max +0,1199. Gate (iv) Marken
byte-gleich. FORMAL: die Adoptionsbedingung verlangt „irgendwo
strikt besser" auf der Struktur-Achse — die kann ein
beidseitiger Veto NIE erfüllen; der Arm ist damit nach dem
Buchstaben der Vorregistrierung NICHT adoptiert, obwohl er auf
jeder gemessenen Achse gleich-oder-besser ist (nie schlechter:
Struktur eingefroren, Tinte näher, Hand-Abstand nie größer).
LESART: der zweiseitige Wächter ist die SICHERE Produktions-Bahn
(primum non nocere gegenüber der rohen Kette), und die
Entscheidung wird eine Owner-Abwägung statt eines Gate-Automatismus:
(a) zweiseitig adoptieren (sicher, tinten-näher, Struktur =
Kette), (b) rohe Kette behalten, (c) der benannte RETTUNGSWEG
für „strikt besser": der **soll-bewusste K0-Wächter** —
Struktur-Änderung nur zulassen, wenn sie sich dem
Kompositions-Soll NÄHERT (die Richtung, die die
Kreuzungs-Invariante ohnehin vorzeichnet; als „Topologie-Budget
K0" seit aug15 als künftiger Arm benannt). Der wäre eine eigene
Vorregistrierung; bis dahin bleibt die Produktions-Adoption
offen und der Re-Harvest hinter Owner-Go + dbsnapshot.

**Vorregistrierung `aug19` — der soll-bewusste K0-Wächter
(Rettungsweg (c)), VOR seiner ersten Zahl.** EIN Knopf:
`--structure-guard-soll` (`FollowWeights.structure_guard_soll`,
impliziert den Wächter; Basis-Konfiguration unverändert die der
Produktions-Messung: prox 0,1 · rounds 2 · coverage 0,3). Die
Akzeptanzregel wird ein INTERVALL je Klasse: mit B = Zählung am
Chain-Optimum (dem Init der Runden, wie bisher) und S = Zählung
der KOMPONIERTEN Init-Geometrie (die Bahn bei x0 = 0, durch
DENSELBEN Assembler und DIESELBEN v2.1-Zähler wie Budget und
Runden — das Soll ist duktus-deterministisch und hier ohne jede
Zweitimplementierung ablesbar) muss jede Klasse c des
Runden-Ergebnisses in [min(B_c, S_c), max(B_c, S_c)] liegen:
Bewegung nur RICHTUNG Soll, nie darüber hinaus, nie davon weg;
bei B_c = S_c friert die Klasse exakt (der zweiseitige
Spezialfall). Retry-Leiter unverändert.

**Messplan.** Beide Arme über alle 63 Wörter des words-Sets in
EINER gepinnten Umgebung (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1` — die aug16-Lehre): Kontrolle = rounds 0
(die rohe Kette durch denselben Codepfad), Kandidat =
soll-bewusst gewacht; `--candidate-out` beider Läufe, Zahlen
über den tracebench-File-Provider (dev-19) plus eine
referenzfreie Auswertung über alle 63 (Strukturzähler vs.
Soll-Spalten aus `tools.tracebench.soll`, `aiou` gegen
`ref_mask.png`). Die 9 versiegelten authored-Zeilen werden dabei
NICHT als Trace-Referenz gelesen (dev-Gate nur über die 19
Dev-Zeilen; Maske und Soll sind referenzfrei).

**Gates (die der Produktions-Messung, unverändert):**
(i) dev-`dtw_xh` gepaart |Median-Δ| ≤ 0,002, kein Dev-Wort über
+0,01; (ii) Struktur-Abstand zum Soll je Wort
(|cross−soll| + |zones−soll|) gewacht ≤ roh ÜBERALL und irgendwo
strikt besser; (iii) `aiou` je Wort min-Δ > −0,005; (iv) Marken
unverändert; (v) kein Wort scheitert, das roh durchläuft;
Laufzeit-Budget 5 min/Wort (gepinnt erwartet ≈ 20 s). Kill wie
gehabt: EIN Wort weiter vom Soll als roh → nicht adoptiert (das
wäre ein Wächter-Bug). Erwartung: unters Zonen-Reparatur aus dem
einseitigen Lauf kehrt zurück (Init 12 → Richtung Soll), die
drei Kreuzungs-Kollapse (Sporn/einer/er-3) bleiben vetiert,
„irgendwo strikt besser" wird damit erstmals erfüllbar. Besteht
alles, ist die Adoptions-EMPFEHLUNG automatisch erfüllt; der
Re-Harvest selbst bleibt Owner-Go + dbsnapshot.

**Gemessen `aug19` — vier von fünf Gates bestehen (Gate (i)
sogar mit SIEBEN strikten dtw-Gewinnen), die Struktur-Klausel
bleibt formal unerfüllbar — und das Runden-Protokoll benennt
den Mechanismus exakt.** Beide Arme 63/63 ok, identisch
gepinnte Umgebung, gewacht 651 s gesamt (≈ 10,3 s/Wort — weit
im Budget). (i) dev-19 gepaart: Median-Δ 0,0000, KEIN Wort
schlechter, sieben strikt besser (das −0,0123 · und −0,0074 ·
muß-2 −0,0065 · und-3 −0,0041 · will/mit/und-2 klein); der
eigene dev-Median fällt 0,0576 → 0,0494. (iii) `aiou` je Wort
NIE negativ, bis +0,108 (und), dev-Median +0,024; beide
Chamfer-Hälften besser. (iv) Marken byte-gleich 1+1.
(ii) ABER: Gesamt-Soll-Abstand exakt **107 = 107** (0 besser ·
63 gleich · 0 schlechter) — wieder friert die Struktur. Das
`unter`-Protokoll zeigt warum: Runde 1 bewegt overlap 3 → 2
(RICHTUNG Soll 0, im Intervall erlaubt), bündelt das aber im
selben Solve mit touch 3 → 6 (WEG vom Soll 0) — die
runden-ATOMARE Rückweisung (auch nach zwei Halbierungs-Retries)
verwirft die Reparatur mitsamt der Verletzung. Die Soll-Richtung
ist also nicht die Schranke; die ATOMARITÄT ist es. NICHT
adoptiert (nach dem Buchstaben der Klausel), aber als
PRODUKTIONS-KandIDAT dominiert der soll-bewusste Wächter den
zweiseitigen auf jeder gemessenen Achse (nirgends schlechter,
sieben Dev-Wörter strikt tinten-näher, aiou bis +0,11, Struktur
= Kette). Die Owner-Abwägung erweitert sich auf: (a) zweiseitig
· (b) roh · (c′) **soll-bewusst (die beste sichere Bahn dieser
Messreihe)** · (d) der benannte nächste Mechanismus für „strikt
besser": **zonale Rückweisung** — nicht der ganze Round wird
verworfen, sondern nur die Anker-Nachbarschaft der
VERLETZENDEN Zone wird auf die Vorrunden-Geometrie zurückgesetzt
bzw. eingefroren und nachgelöst, sodass eine gebündelte
Soll-Reparatur den Round überlebt (eigene Vorregistrierung,
§7.9-Zeile im selben PR).

### Route „Lotse" `aug16` — Vorregistrierung: Skelett fahren, Duktus als Karte

Geschrieben und committet VOR der ersten Bench-Zahl. Owner-Idee
(2026-08-16, tintenfolger.md §7.8): nicht Buchstabe auflegen und
verformen (Kette), sondern wie die Nullprobe DIREKT auf der
Tinten-Mitte fahren und nur an Entscheidungsstellen den Duktus als
KARTE fragen. Arm ⑨s Fazit („Tinten-Gewinn und Struktur-Erfindung
in DIESER Formulierung untrennbar") benannte genau diese andere
Formulierung als Rettungsweg (§7.9).

**Implementierung** (`tools/inkpilot`, Anzeige-Name „Lotse"):
Karte = die komponierte Bahn in Crop-px (wordlab-Transform auf der
gefitteten Registrierung der Zeile); Wasserweg = der
routeg-Skelettgraph; Ritt = GLOBALE Zuordnung Karten-Sample →
Grat-Punkt (Viterbi über die Sample-Kette: Graph-Fahrkosten +
Karten-Abweichung + Brücken-Zustand), verbunden über kürzeste
Pixelketten-Wege — der Abbiege-Entscheid an jeder Kreuzung fällt
aus der Route der Karte; Kanten dürfen doppelt gefahren werden
(Retrace); wo keine Tinte liegt, überbrückt die Karte; führende und
folgende Brücken ohne Wieder-Aufstieg werden GETRIMMT (komponierte
Luft ist kein Federstrich). Kein #278-Bruch: Ordnung, Richtung und
Marken-Zuweisung kommen vollständig vom Prior. v0-Konstanten
(unkalibriert, deklariert): `SAMPLE_STEP` 0,12 xh · `BOARD_RADIUS`
0,6 xh · `DEVIATION_WEIGHT` 2 · `BRIDGE_EMIT` 2,5×Radius ·
`MAX_RIDE_FACTOR` 8. Laufzeit ~0,1–0,3 s/Wort (kein Solver).
Unit-Tests auf dem synthetischen Kreuz: Gleistreue, Karten-Abbiegen
an der Kreuzung, Luft-Trimm, Lücken-Brücke, Frame-Roundtrip.

**Messgrößen (Dev-Split, gegen die eingefrorene Baseline).**
(a) `dtw_xh` gepaart Lotse vs. Kette (Baseline 0,062 med) — die
Hypothese der Route: Tinten-Mitte + Karten-Ordnung schlägt den
Mess-Fit als NACHFAHRER. (b) Strukturzähler + Soll-Spalten (die
Karte bringt das Soll mit; erfundene Kreuzungen wären
Graph-Artefakte). (c) `marks_missing/spurious` (Marken per Karte
zugewiesen). (d) `aiou` (konstruktionsbedingt hoch — Erwartung ≥
Kette). (e) Brücken-Anteil je Wort als QC-Spalte — viel Brücke
heißt, die KARTE verließ die Tinte: ein Kompositions-Defizit, kein
Lotse-Fehler, report-only ausgewiesen.

**Gates und Kill-Kriterien (relativ, keine publizierten Zahlen).**
Ernst zu nehmen ist die Route, wenn `dtw_xh` gepaart die Kette
schlägt (Median der Differenzen < 0, Sign-Test beschreibend) OHNE
Netto-Verschlechterung bei Kreuzungen und Marken. Kill:
Struktur-Erfindungen über der Kette (Graph-Grate erzeugen
Falsch-Kreuzungen) oder Marken-Verluste → Formulierung zurück ans
Reißbrett, ehrliches Negativ mit Fund. Erwartete Fehlermodi
benannt: der Pixel-Zickzack der 8er-Skelettkette (kostet dtw
wenig, ist der benannte Feinschliff-Kandidat), Doppelpass-Zonen
(das Skelett hat EINE Linie, wo die Hand zwei schrieb — der Ritt
fährt sie zweimal, korrekt per Karte, aber deckungsgleich statt
versetzt), der ß-Kringel in muß.

**v0.1 gemessen `aug16` — Gate verfehlt, aber mit dem stärksten
Einzelwort-Fund der Kampagne.** Dev-Split, 10/10 ok, 22,5 s
Gesamtlauf. `dtw_xh` Median 0,119 gegen Kette 0,062 — die Route
verliert den Median klar (8/10 Wörter schlechter). ABER die
Verteilung erzählt zwei Geschichten: **unter — das
Katastrophen-Wort der Kette (0,4501, der Stapel-Kollaps) — fällt
auf 0,0641 (−0,386)**, muß ebenfalls besser (−0,021), und `aiou`
steigt fast überall (laden 0,686 → 0,801 · will 0,753 → 0,816 —
die Tinten-Mitte hält, was die Nullprobe versprach). Die zwei
Verlust-Mechanismen, beide vorregistriert erwartet, einer davon in
voller Stärke: (1) **`cross_cand = 0 auf JEDEM Wort** — 23
Hand-Kreuzungen fehlen komplett: wo Striche sich kreuzen, teilen
sich die Ritte die SELBEN Skelett-Pixelketten durch den Knoten,
zwei Pässe fallen deckungsgleich zusammen und schneiden sich nie
transversal (stattdessen 12 unechte Retrace-Zonen,
`retrace_arc_ratio` 2,49). (2) `und` bricht aus (+0,294) —
Autopsie: die Geometrie ist praktisch PERFEKT (Chamfer beidseitig
0,031/0,053, besser als die Kette), der dtw-Ausreißer besteht aus
einem 4,15-xh-Deckungs-Doppelritt am d-Stamm (der A5-Fall in
Reinform) plus einem Klassifikations-Kipp: der
skelett-VERKÜRZTE u-Deckbogen des Lotsen (Skelett endet eine
halbe Strichbreite vor der Tintenspitze) fällt unter die
0,8-xh-Marken-Schwelle, der längere der Hand nicht — die
Body-Mengen unterscheiden sich strukturell und das forward-DTW
zahlt den ganzen Umweg. Kill-Kriterium „Struktur-Erfindung"
feuert NICHT (0 unechte Kreuzungen, 0 Marken-Verluste) — aber das
Gate (Kette schlagen ohne Struktur-Netto-Verlust) ist verfehlt:
VERWORFEN als v0.1, Route NICHT geschlossen. Rettungswege
(§7.9-Regel): (i) **der versetzte Doppelpass aus Breiten-Evidenz**
— genau §7-Maßnahme A5: auf mehrfach gefahrenen Kanten die Pässe
um einen Bruchteil der GEMESSENEN lokalen Strichbreite
(`width_map` liegt im Fixture!) senkrecht auseinanderlegen, dann
schneiden sich die Züge transversal wie die Hand; (ii) der
Feinschliff über den Pixel-Zickzack; (iii) die und-Autopsie.

**Vorregistrierter v0.2-Arm (A5, versetzter Doppelpass), VOR
seiner ersten Zahl.** EIN Knopf: `DOUBLE_PASS_OFFSET_FRACTION` —
jeder Ritt-Punkt auf einem Skelett-Pixel, das im WORT insgesamt
mehrfach befahren wird, weicht um diesen Bruchteil der lokalen
EDT-HALBBREITE (`width_map` des Fixtures) NACH RECHTS seiner
Fahrtrichtung aus; gegenläufige Pässe trennen sich dadurch von
selbst auf gegenüberliegende Seiten (die Vorzeichen-Konvention
der Hand), gleichläufige (Overlap-Klasse) bleiben deckungsgleich,
Einfachpässe und Brücken bleiben unberührt (Tinten-Mitte hält).
Leiter 0,0 (= aus) / 0,35 / 0,5. Erwartung: die 23 fehlenden
Kreuzungen kehren mehrheitlich zurück (transversale Schnitte an
den getrennten Pässen), `retrace_arc_ratio` fällt Richtung 1,
`und` verliert seinen Doppelritt-Anteil; `aiou` darf dafür
minimal nachgeben (der Versatz verlässt den Grat um < eine halbe
Strichbreite — per Definition innerhalb der Tinte). Gates wie
v0.1; Zusatz-Kill: sinkt `aiou` im Median um > 0,02, kauft der
Versatz Struktur mit Tinten-Deckung und wird verworfen.

**A5-Arm gemessen `aug16` — verworfen; der Parallel-Versatz ist
der falsche Mechanismus, der richtige heißt Knoten-Sehne.**
Leiter (dev, 10/10 ok): 0,35 → dtw 0,1156 · aiou −0,018 (hält
das Zusatz-Kill knapp) · aber nur **3 von 23 Kreuzungen kehren
zurück** (+2 unechte); 0,5 → 13 fehlend (+6 unechte), aiou
−0,032 → vom eigenen Zusatz-Kill VERWORFEN. Die Erwartung
(„mehrheitlich zurück") verfehlen beide klar, Konstante bleibt
0,0. Der Fund: versetzte Pässe sind getrennte, aber weiterhin
FAST PARALLELE Züge — der Kreuzungs-Detektor verlangt zu Recht
einen echten Schnittwinkel (≥ 15°), und den erzeugt ein
Parallel-Versatz nur an den flachen Zonen-Enden, nicht dort, wo
die Hand kreuzt. Die Hand kreuzt am KNOTEN in echten Winkeln:
zwei Pässe treten aus vier verschiedenen Richtungen durch die
Kreuzungs-Nachbarschaft, das Skelett zwingt beide auf dieselbe
geteilte Schiene und knickt sie um die Ecke. Der präzisere
Rettungsweg (benannt, eigene Messung): **der Knoten-Sehnen-
Schnitt** — wo ein Ritt einen Verzweigungsknoten durchquert,
lokal die SEHNE seines eigenen Eintritts→Austritts fahren statt
der geteilten Knoten-Schiene (die Kreuzung entsteht dann von
selbst, wo sich zwei Sehnen schneiden — die Extrapolations-Idee
der §13a-Landmark-Ziele, hier als Konstruktion statt als
Zielterm).

**Vorregistrierter v0.3-Arm (Knoten-Sehne), VOR seiner ersten
Zahl.** EIN Knopf: `JUNCTION_CHORD_RADIUS_FRACTION` — um jeden
VERZWEIGUNGS-Knoten (≥ 3 einlaufende Kanten) wird eine
Nachbarschaft vom Radius Knopf × lokale EDT-Halbbreite gelegt;
jeder maximale Lauf von Ritt-Punkten innerhalb dieser
Nachbarschaft (eine Knoten-Durchquerung) wird durch die GERADE
SEHNE seiner beiden Randpunkte ersetzt, sofern der Lauf kurz ist
(Bogen < 4 × Radius — ein Zug, der den Knoten nur streift, bleibt
unangetastet). Zwei Pässe aus verschiedenen Richtungspaaren
erzeugen zwei verschiedene Sehnen, die sich in echtem Winkel
schneiden; auch der EINFACH-Pass profitiert (die Sehne begradigt
den Umweg, den die geteilte Skelett-Schiene der Feder andichtet
— die publizierte Junction-Verschiebung um ±Strichbreite).
Leiter 0,0 (= aus) / 1,0 / 1,5. Erwartung: fehlende Kreuzungen
kehren am KNOTEN zurück (nicht an Zonen-Enden wie beim
Parallel-Versatz), dtw fällt auch auf kreuzungsarmen Wörtern
leicht (Umweg-Begradigung); `aiou` gibt in der
Knoten-Nachbarschaft nach — dieselbe Zusatz-Kill-Schranke wie
A5 (Median-Δ > −0,02 verworfen). Übrige Gates wie v0.1.

**v0.3 gemessen `aug16` — verworfen; der Fund lokalisiert die
fehlenden Kreuzungen endgültig.** Leiter (dev, 10/10 ok):
1,0 → dtw 0,1211 · aiou 0,702 (−0,045!) · Kreuzungen 23 → 21
fehlend; 1,5 → dtw 0,1252 · aiou 0,637 (−0,110) · 19 fehlend.
Beide Stufen vom aiou-Zusatz-Kill VERWORFEN, beide Knöpfe bleiben
0,0. Der Fund: nur 2–4 der 23 fehlenden Kreuzungen sitzen an
Punkt-Knoten — die Mehrheit liegt auf **LANGEN geteilten
Schienen** (bis 4 xh: der Schleife-auf-Stamm-Kollaps der
Skelettierung verschmilzt die zwei Pässe der Hand über die ganze
Überlappungsstrecke), und dort erreicht keine lokale
Knoten-Chirurgie sie; die Sehnen kosten dafür ÜBERALL Deckung
(auch Einfach-Pässe durch gekrümmte Knoten werden begradigt, wo
die Feder wirklich kurvte). Damit sind die drei Lotse-Verluste
mechanisch vollständig kartiert und die zwei ehrlichen Wege
benannt (§7.9): (i) **Sub-Strich-Trennung aus Breiten-Evidenz
über ganze Zonen** — wo die gemessene Breite die
Einfachstrich-Breite deutlich übersteigt, liegen zwei Pässe in
der Tinte; ihre Trennung ist ein eigenes Forschungsstück (die
A5-Intuition war über die EVIDENZ richtig und über die GEOMETRIE
falsch); (ii) pragmatisch die **Karten-Vorfahrt in
Doppelpass-Zonen** — der Lotse hält die Karte ohnehin in der
Hand, und die Karte HAT die Kreuzung (das Soll ist
duktus-deterministisch): in Zonen, die die Karte als Doppelpass
ausweist, fährt der Zug die KARTE statt der degenerierten
Schiene — der Brücken-Modus, gezielt eingesetzt. Beides eigene
Vorregistrierungen; v0.1 bleibt der gemessene Stand der Route. Der
unter-Befund steht unabhängig davon: wo der Ketten-Fit
strukturell scheitert, liefert die Karten-Fahrt bereits jetzt
eine um Faktor 7 bessere Bahn — die Fusion („Vier Augen") hat
damit ihr erstes gemessenes Argument.

**Vorregistrierter v0.4-Arm (Karten-Vorfahrt in Doppelpass-Zonen),
VOR seiner ersten Zahl.** Der v0.3-Fund lokalisierte die fehlenden
Kreuzungen auf den LANGEN geteilten Schienen (Skelett verschmilzt
die zwei Pässe der Hand über die ganze Überlappungsstrecke); dort
ist die Schiene DEGENERIERT und die KARTE hat die Wahrheit (das
Struktur-Soll ist duktus-deterministisch, die Komposition schreibt
den Doppelpass mit Kreuzung). EIN Knopf: `MAP_PRIORITY_IN_RETRACE`
(aus/an) — Karten-Samples, die in einer SELBST-Retrace-Zone der
Karte liegen (Zonen via `core.geometry.detect_retrace_pairs` auf
den Karten-Strichen, dem Detektor des eingefrorenen Lineals, hier
nur LESEND auf der Karte), bekommen im Viterbi ausschließlich den
Brücken-Zustand: der Zug fährt dort die Karte selbst, mit ihrer
komponierten Kreuzung und ihrem versetzten Doppelpass; außerhalb
der Zonen ändert sich nichts. Erwartung: die Schienen-Klasse der
fehlenden Kreuzungen kehrt zurück (und der 4-xh-Doppelritt in
`und` verschwindet), `aiou` gibt nur INNERHALB der Zonen nach —
dieselbe Zusatz-Kill-Schranke (Median-Δ > −0,02 verworfen);
übrige Gates wie v0.1. Zusätzliche QC-Spalte: Karten-Anteil je
Wort (Brücken-Bogen/Gesamt-Bogen), report-only.

**Vorregistrierter Zusatz-Arm (Schienen-Auslauf), VOR seiner
ersten Zahl — Owner-Fund an der v0.1-Sichtprüfung (2026-08-16):
„beim d geht die Linie nach der Kreuzung nicht weiter bis zum
Ende".** Diagnose: die KARTE endet dort, wo die Komposition den
gebundenen Schleifen-Abgang an der Kreuzung trimmt (Loop-Exit-
Regel) bzw. wo der komponierte Auslauf generell kürzer reicht als
die Tinte (der +7–10-%-Reichweiten-Befund der P3-Vorstudie) — und
der Lotse fährt nur, wohin die Karte führt; die getintete Spitze
hinter dem letzten Karten-Sample bleibt ungeritten. EIN Knopf:
`TAIL_RUNOUT_MAX_UNITS` — endet ein Ritt-Strich auf einer
Schiene, die ohne Verzweigung in einen Grad-1-ENDPUNKT des
Skeletts ausläuft, und liegt dieser näher als der Knopf (in xh),
fährt der Zug bis zum Schienen-Ende weiter (symmetrisch am
Strich-ANFANG). Leiter 0,0 (= aus) / 0,6 / 1,0. Erwartung: die
d-Spitzen und Wort-Ausläufe schließen (sichtbar + `dtw` an den
betroffenen Wörtern), `aiou` steigt eher (mehr getintete Bahn
gedeckt), keine Struktur-Änderung (ein Grad-1-Auslauf kann weder
kreuzen noch retracen). Kill: verlängert der Auslauf in
Wirklichkeit einen SPORN des Skeletts (unechte Marken/Spitzen —
`marks_spurious` oder `dtw` netto schlechter), wird er verworfen.

**Beide Arme gemessen `aug16` — der Owner-Fund-Arm ADOPTIERT, die
Karten-Vorfahrt ehrliche Null.** (a) Schienen-Auslauf (dev,
10/10 ok): 0,6 → dtw 0,1053 · 1,0 → **dtw 0,1007** (v0.1: 0,1192),
`und` **0,3428 → 0,0874** — die fehlende d-/Auslauf-Spitze WAR der
Ausreißer —, `aiou` 0,747 → 0,765, `marks_spurious` 3 → 1 (der
verlängerte u-Deckbogen springt zurück über die
0,8-xh-Marken-Schwelle: auch der Klassifikations-Kipp der
und-Autopsie heilt), Kreuzungen exakt unverändert (23 fehlend —
wie konstruiert), `retrace_spurious` 12 → 14 (+2, benannt: zwei
verlängerte Enden fallen in Deckungs-Zonen). Gates bestanden →
**ADOPTIERT, `TAIL_RUNOUT_MAX_UNITS` = 1,0.** (b) Karten-Vorfahrt:
dtw 0,1179 · aiou −0,014 · Kreuzungen 22 statt 23 fehlend (+1
unecht) · `und` UNVERÄNDERT — die SELBST-Retraces der Karte sind
in den Dev-Wörtern zu selten (das t mit Stamm-Rückpass kommt nur
in mit/unter/streiten vor, unds Doppelritt entsteht RITT-seitig
an einer Tinten-Schleife, die die Karte nur EINMAL passiert): der
Karten-Trigger war die falsche Zone. VERWORFEN (Erwartung klar
verfehlt), Knopf bleibt False; benannter Nachfolger: dieselbe
Karten-Fahrt, aber in RITT-seitig erkannten Doppelzonen (die
A5-Erkennung, die v0.4-Geometrie — Kombination, eigene Pre-Reg).
Stand der Route damit: dev-dtw 0,101 gegen Kette 0,062 (Lücke
2,0× → 1,6×), `aiou` klar über der Kette, Kreuzungs-Kollaps auf
geteilten Schienen bleibt DER offene Block.

### Route „Lotse" v0.5 `aug16` — Vorregistrierung: Karten-Geometrie in Ritt-Doppelzonen

Geschrieben und committet VOR der ersten Zahl. Die benannte
Kombination aus den zwei verworfenen Armen: die ERKENNUNG des A5
(wo besucht der Ritt dasselbe Skelett-Pixel mehrfach — dort ist
die Schiene degeneriert, das Skelett hat die zwei Hand-Pässe
verschmolzen) mit der GEOMETRIE des v0.4 (dort die Karte fahren,
die den Doppelpass MIT Kreuzung komponiert). EIN Knopf:
`RIDE_DOUBLE_MAP_PRIORITY` (aus/an) — die Sample-Zuweisungen des
Wortes werden in SCHREIB-Reihenfolge durchlaufen; ein Sample,
dessen zugewiesenes Schienen-Pixel im Wort schon einmal besetzt
wurde, fährt statt der Schiene die KARTE (sein eigenes
Karten-Sample, brücken-gleich verbunden) — der ERSTE Pass bleibt
auf der Tinten-Mitte, jeder SPÄTERE fährt die komponierte
Geometrie mit ihrer Kreuzung. Erwartung: die Schienen-Klasse der
23 fehlenden Kreuzungen kehrt substanziell zurück, `und`s
Rest-Doppelritt verschwindet, `retrace_arc_ratio` fällt Richtung
Hand-Niveau; `aiou` gibt nur in den Doppelzonen nach — dieselbe
Zusatz-Kill-Schranke (Median-Δ > −0,02 verworfen). Kill
zusätzlich: erzeugt die Karten-Geometrie in den Zonen UNECHTE
Kreuzungen über das Soll (`cross_spurious` netto > +2), ist die
Karten-Platzierung dort zu schlecht — verworfen, zurück zur
Sub-Strich-Trennung. Basis ist der adoptierte Stand (Auslauf 1,0).

**Gemessen `aug16` — ALLE Gates bestehen, ADOPTIERT.** Dev,
10/10 ok: dtw-Median 0,1007 → **0,0853**; `und` 0,0874 →
**0,0431** — schlägt dort erstmals die KETTE (0,0491); **5 der 23
fehlenden Kreuzungen kehren zurück** (18 fehlend, +1 unecht —
innerhalb der ≤+2-Schranke); `retrace_spurious` 14 → 11,
`retrace_arc_ratio` 2,48 → **1,66** (Richtung Hand, wie
vorregistriert); `aiou` −0,002 (weit innerhalb der Schranke).
`RIDE_DOUBLE_MAP_PRIORITY` = True. Routen-Stand: **0,0853 gegen
Kette 0,0620 (Lücke 1,4×)**, und die Komplementarität ist jetzt
messbar scharf — der Lotse schlägt die Kette auf genau den
STRUKTUR-schweren Wörtern (unter −0,387 · muß −0,129 ·
und −0,006), verliert auf den einfachen (die glatte
Regularisierung der Kette gewinnt, wo nichts kollabiert):
mit +0,042 · will +0,081 · zwei +0,056. Das ORAKEL der Fusion
(je Wort das bessere Verfahren, nur als Decke, kein Ergebnis):
Median **0,0563** — besser als jede Einzelroute, schlechtestes
Wort 0,113 statt 0,450 (Kette) bzw. 0,132 (Lotse). „Vier Augen"
hat damit seine erste bezifferte Decke; der ehrliche
Auswahl-Mechanismus (ohne Referenz!) ist die offene Frage — die
Lehre aus B1 (der ordnungs-blinde Ranker) gilt hier wörtlich.

**Auswähler-Diagnostik `aug16` (explorativ, KEIN Ergebnis —
festgehalten, damit die Sackgassen benannt sind):** drei
referenzfreie Signale auf den 10 Dev-Wörtern geprüft, keines
trennt: (i) Soll-Distanz der Kette (zwei hat 4 und die Kette
gewinnt trotzdem; die drei Lotse-Siege liegen bei 0–1);
(ii) p90-Tinten-Restfehler der Kette (Lotse-Siege bei
0,057–0,068, aber die/zwei gewinnen für die Kette im selben
Band); (iii) Lotse-eigene `retrace_arc_ratio` flaggt zuverlässig
nur die GROSSEN Lotse-Niederlagen (≥ 4 ⇒ Kette, 4/4), die
resultierende Einweg-Regel bleibt aber unter der Kette (Median
0,0746), weil die kleinen Ketten-Siege (Wer/linken/mit,
+0,03–0,04) mitverloren gehen. Struktur des Problems:
asymmetrische Einsätze (Kette gewinnt 7/10 knapp, Lotse 3/10
riesig) — der Auswähler braucht ein Signal für „die Kette
scheitert HIER" mit sehr niedriger Falsch-Positiv-Rate.
Kandidaten für die echte Pre-Reg, wenn der Bestätigungssatz da
ist: fit-interne Flags der Kette (at_bound/Konvergenz je Slot)
und die Kombination arc-ratio-Einweg + Restfehler. Auf n=10 wird
KEINE Regel adoptiert (Dev-Fishing-Verbot).

### Route „Lotse" v0.6 `aug16` — Vorregistrierung: der Feinschliff

Geschrieben und committet VOR der ersten Zahl. Der benannte
Kandidat aus der Duell-Review (Owner: Mikro-Wackler sichtbar,
„wenn der Schreiber der Linie mit fester Stiftdicke nachgeht,
sieht man die Wackler in der dicken Linie"): die 8er-Pixelkette
des Skeletts zickzackt mit ±0,5 px; auf den GLATTEN Wörtern, wo
die Kette heute noch gewinnt, ist das ein flächiger dtw-Beitrag.
EIN Knopf: `SMOOTH_ITERATIONS` — je Iteration das lokale Mittel
x_i ← (x_{i−1} + 2·x_i + x_{i+1}) / 4 über jeden Ritt-Strich,
ENDPUNKTE FIX (der adoptierte Schienen-Auslauf bleibt exakt);
Leiter 0 (= aus) / 2 / 4. Struktur-Wächter als Gate statt als
Code: `cross/retrace/touch/overlap`-Zähler und Marken müssen
byte-gleich bleiben (eine 1-px-Glättung, die eine Kreuzung
unmacht, ist verworfen — Ecken und Retraces sind ECHTE Merkmale,
die Doktrin der Natürlichkeitsmetrik in §5); `aiou`-Median-Δ >
−0,02 = verworfen. Erwartung: dtw fällt breit (auch auf den
Ketten-Siegen), `aiou` ~neutral (die Glättung bleibt binnen
halber Strichbreite).

**Gemessen `aug16` — beide Stufen verworfen; die
Zickzack-Hypothese ist fürs LINEAL widerlegt.** it2 → dtw 0,0860
· aiou −0,022 · Zähler NICHT byte-gleich (cross 18→17 fehlend,
1→0 unecht; retrace 0→1 fehlend); it4 → dtw 0,0869 · aiou −0,029
· retrace 0→3 fehlend. Alle drei Gates verletzt, Konstante bleibt
0. Die Lehre: das 0,02-xh-Arc-Resampling des `dtw_xh` schluckt
den ±0,5-px-Zickzack ohnehin (beide Seiten werden identisch
abgetastet) — die Glättung kauft auf der Messachse NICHTS und
bezahlt mit Tinten-Deckung und Grenzfall-Struktur. Der
Mikro-Wackler ist damit als SICHT-Problem des späteren
NACHSCHREIBERS eingeordnet, nicht als Mess-Problem: der
Feinschliff gehört, wenn überhaupt, an den KONSUMENTEN der Bahn
(Renderer/Editor-Anzeige, eine reine Darstellungsstufe), nie in
den gemessenen Kandidaten. §7.9-Zeile entsprechend.

### O2-Trim-Jitter `aug16` — Vorregistrierung: der Bugfix, der auch verlieren darf

Geschrieben und committet VOR der ersten Zahl. Der K3-Nebenfund
(§14 „Welle 2 · P3"): `_entry_couple_index` bricht seinen
Flanken-Aufstieg bei JEDEM Mini-Rückgang ab (`y[i] < y[i−1]`,
ohne Toleranz) — das Spline-Resampling der komponierten Bahnen
trägt aber ±0,0004-xh-Zittern, und so ist der generische
O2-0,78-Trim für Arkaden-Köpfe (deren Anstriche das Zittern im
ersten Schritt zeigen) STILL DEAKTIVIERT: Hoch-Exits in n/m/i/r
koppeln heute am Chart-Fuß statt am beabsichtigten 0,78-Punkt.
EIN Knopf: `ENTRY_FLANK_DIP_TOL` — der Aufstiegs-Wächter toleriert
Rückgänge bis zu diesem Betrag je Sample (in xh); ein echter
Kopf-Umschwung fällt weit schneller. Leiter 0,0 (= heutiges
Verhalten) / 0,02 (die Schwelle, die der K3-Lokalscan bereits
verwendet). BEIDE Ausgänge sind vorregistriert gültig:
(a) Bench besser oder gleich → Bugfix ADOPTIERT (die beabsichtigte
O2-Semantik gilt wieder); (b) Bench schlechter → der Bug ist
TRAGEND (das Lineal bevorzugt die Fuß-Kopplung, die der Bug
zufällig herstellt — dann ist nicht die Toleranz falsch, sondern
die O2-Zielhöhe für Arkaden-Köpfe, und DAS wird als eigener
Befund verbucht; Konstante bleibt 0, Rethink benannt). Gates:
wordbench `word_loss` + `pair_loss` (eingefroren), `soll_*_agree`
unverändert, Sichtprüfung der bewegten Wörter; compose-golden
bricht, wo Hoch-Exit→Arkade in den golden-Wörtern vorkommt
(wovon o→n! Morgen o→r!) → deklarierte Re-Baseline bei Adoption.

**Gemessen `aug16` — Ausgang (b), und der Bug erweist sich als
ZUFÄLLIGE KLASSENREGEL.** Toleranz 0,02: `word_loss` 0,108091 →
0,108095 (+4e−6, hauchdünn schlechter), `pair_loss` byte-gleich,
genau DREI Wörter bewegen sich — und sie spalten sich exakt
entlang der K3-Ankunfts-Leiter: **von (o→n) −0,0126** (der
reparierte 0,78-Trim ist für o→n ein klarer Gewinn — mehr als
K3s 0,685-Lift je holte), aber **Zorn (o→r) +0,0112** und Sporn
(o→r) +0,0017 (o→r will TIEFER ankommen, wie K3 maß). Der
Jitter-Bug implementiert heute unabsichtlich genau diesen Split
(n-Anstriche zittern im ersten Schritt → Fuß; r-Anstriche nicht →
0,78), und das Lineal bevorzugt ihn netto um Mikrometer.
VERDIKT: Toleranz bleibt 0,0 (per Kriterium (b)); der eigentliche
Befund ist, dass die UNIFORME O2-Zielhöhe für Arkaden-Köpfe falsch
ist und die richtige Struktur eine KLASSENREGEL wäre (n hoch,
r tiefer — von-Gewinn ernten, ohne Zorn zu bezahlen). Die gehört
als eigene Pre-Reg auf den Tisch, ehrlicherweise erst mit dem
Bestätigungssatz (dieselbe n≤8-Vorsicht wie bei P3); bis dahin
trägt der Bug — dokumentiert statt still.

### Re-Baseline `aug17` — der 19er-Dev-Satz: Dev-Erweiterung aktiviert, alle stehenden Routen neu vermessen

**Anlass und Deklaration.** Der Autor hat den kompletten Dev-Satz der
§2.5-Zuordnung nachgefahren (alle 19 Vorkommen `authored`, inkl. der
zwei neuen Wörter **Galoppieren** und **das** und aller
Wiederholungs-Vorkommen; Bestätigung A stand bei 5/20, B bei 4/24 —
beide bleiben versiegelt). Owner-Go in Session (2026-08-17): die
Dev-Erweiterung tritt VOR der Voll-Autorisierung in Kraft
(Aktivierungs-Nachtrag in tintenfolger.md §2.5 — die Zuordnung war
seit 2026-08-16 fixiert und performance-blind, Galoppieren/das nie
gebencht, der Weg Dev → Bestätigung existiert nicht).
`TRACEBENCH_DEV_IDS` führt seither 19 Ids (Wiederholungen splitten
als WORT, §2.5). Zugleich ist dies die deklarierte
**Doppel-Re-Baseline** der Betriebsregeln: die Fixture-Roots wurden
in der Cloud-Session über `fetch_fixtures --set all --verify` neu
gebaut (kein `--only`-Refill möglich — frischer Klon hat keine
Roots; Verify: 12 Kompositionen und alle Template-Zeilen bit-exakt
gegen die deployte API), die Vorher-Zahlen (`aug14`/`aug16`-Stände)
sind mit den heutigen NICHT vergleichbar. Alle Routen laufen mit
gepinnten BLAS-Threads (`OPENBLAS_NUM_THREADS=1`,
`OMP_NUM_THREADS=1`).

**Identitäts-Gate (vor jeder Kandidaten-Zahl): PASS auf 19/19** —
dtw 0, beide Chamfer 0, alle Zähler voll gematcht,
`direction_uncertain` 0 (auch die 9 neuen Nachfahrungen stimmen
überall mit der Duktus-Richtung des Priors überein — Galoppieren
eingeschlossen). Fixture-Qualitätssignale, keine Kandidatenfehler:
`marks_uncertain` 9/19 (der Autor zeichnet Marken teils verbunden
bzw. unter der Diakritika-Schwelle — der Bestätigungs-Brief-Hinweis
„Marken mit eigenem Absetzen" gilt weiter); `soll_cross_agree`
16/19, `soll_zones_agree` 18/19 (Abweichler unten je Wort).

**Die Kette auf dem 19er-Satz** (`--candidate chain --split dev`,
Schritt 0,02, 19/19 gescort, 0 failed, 163 s):

```
dtw_xh_median:   0.057853    aiou_median:              0.6940
dtw_xh_p90:      0.236331    chamfer_cand_ref_median:  0.0380
dtw_xh_worst:    unter 0.4503 chamfer_ref_cand_median: 0.0400
marks_missing:   1  marks_spurious: 1
cross_missing:   15  cross_spurious: 7
retrace_missing: 7   retrace_spurious: 13
retrace_arc_ratio_median: 0.641
touch 13 Hand / 24 Kette · overlap 0 Hand / 8 Kette
lift_delta_total: +7  dtw_reversed_better: 0  max_absorption_max: 93
```

Je Wort (dtw · cross matched/ref+spurious · Auffälligkeit):
unter **0,4503** · 1/3 · der bekannte Stapel-Kollaps, unverändert —
muß **0,2421** / muß-2 **0,2082** / muß-3 **0,2337** · je 1/1 ·
die ß-Retrace-Zone fehlt in ALLEN drei Vorkommen (0/1 gematcht,
r 0,18–0,24): der Defekt ist reproduzierbar klassenhaft, kein
Einzel-Beleg — **Galoppieren 0,2349** · **3/8** (5 verlorene
Kreuzungen, die schwerste Struktur-Zahl des Satzes) · dazu die
fehlende i-Marke (0/1), lift +1, r 1,84 — das 22,7-s-Solve ist auch
der Laufzeit-Ausreißer — das 0,0579 · 3/3**+2** · zwei erfundene
Kreuzungen — die 0,0745/die-2 0,0746 · je +1/+2 erfundene —
laden 0,0746 · 1/3+2 — zwei 0,0761 · 1/3 — will 0,0451 · 1/3 —
mit 0,0426/mit-2 0,0376 · 1/2 bzw. 1/1 — Wer 0,0432 · 3/3 —
und-Familie 0,0280–0,0491 · 1/1 · sauber.

Lesart: Der Median sinkt leicht (0,0620 → 0,0579), weil die
Wiederholungs-Vorkommen mehrheitlich leichte Wörter sind — die
KLAGE wächst trotzdem: die muß-Klasse trägt jetzt dreifach, und
Galoppieren bringt eine neue Fehlerklasse (Versal-Kette + lange
Wortspanne) mit 5 verlorenen Kreuzungen und einem
Berührungs-/Überlagerungs-Aufwuchs (touch 24 vs. 13, overlap 8
vs. 0), den die 10er-Baseline so nicht zeigte.

**Der Lotse auf dem 19er-Satz** (adoptierter Stand: Auslauf 1,0 +
Ritt-Doppelzonen-Kartenfahrt; 19/19 ok, 83 s): dtw-Median
**0,0850** · p90 0,1273 · worst muß-2 0,1466 · aiou **0,7631**
(klar über der Kette 0,6940) · `marks_missing` 0 ·
`cross_missing` **31** (+4 unecht) · `retrace_spurious` 22 ·
touch 41 (Hand 13). Gepaart gegen die Kette: Δ-Median +0,0099,
Sign-Test 10:9 — zahlenmäßig unentschieden, aber die Einsätze
bleiben asymmetrisch, jetzt mit VIER großen Lotse-Siegen statt
drei: **unter −0,387 · muß −0,129 · muß-3 −0,121 · Galoppieren
−0,112 · muß-2 −0,062 · die-2 −0,044**, dagegen 10 kleine bis
mittlere Niederlagen (max. will +0,081). Die muß-Klasse gewinnt
der Lotse GESCHLOSSEN (alle drei Vorkommen ~0,11–0,15 gegen
0,21–0,24) — der Komplementaritäts-Befund der 10er-Runde
generalisiert auf die neuen Belege, statt zu verschwinden.
Diagnose-Spalten: `direction_uncertain` 3 = exakt die drei
muß-Vorkommen (je 1 von 2 geprüften Strichen — der ß-Bereich;
Autopsie-Kandidat, kein Gate-Bruch); `will` trägt r = 14,9
(pathologischer Deckungs-Doppelritt), laden 6,4 · Galoppieren 6,3
· die 4,5. **Die Kreuzungs-Verlustkarte ist vollständig:** JEDES
Wort verliert (31 von 46 Hand-Kreuzungen fehlen), Galoppieren
alle 8, zwei/Wer/will/unter je 3/3 bzw. 0 gematcht — und auch die
join-gebildete die-Kreuzung (soll_letters 0) fällt dem
Schienen-Kollaps zum Opfer. Der offene Block der Route (v0.3-Fund:
lange geteilte Schienen, Schleifen-Kollaps der Skelettierung) ist
damit auf dem größeren Satz DER dominante Verlustmechanismus.

**Die Nullprobe auf dem 19er-Satz** (routeg, 19/19 ok): dtw-Median
0,6189 — alle 19 Wörter schlechter als die Kette (Sign-Test 19:0),
rel. Median **+1092 %**; aiou 0,8290 (wie immer die beste
Tinten-Deckung — Skelett-Mitte), `cross_missing` 27,
`lift_delta` +167. Galoppieren ohne Prior: **1,906**. Der Wert
des Duktus-Priors, auf 19 Wörtern neu beziffert: Faktor ~11 im
Median, am langen Versal-Wort Faktor 8 gegen die Kette bzw. 15
gegen den Lotsen.

**Das Orakel der Fusion, neu beziffert** (je Wort das bessere aus
Kette/Lotse — Decke, kein Ergebnis): Median **0,0491** · p90
0,115 · schlechtestes Wort muß-2 0,1466 (statt 0,450 Kette bzw.
0,147 Lotse). Die Decke liegt weiter unter beiden Einzelrouten;
der referenzfreie Auswähler bleibt die offene Frage (die
`aug16`-Diagnostik gilt: kein Signal trennt auf Dev-n, keine
Regel wird auf dem Dev-Satz adoptiert).

**InkSight T0 auf dem 19er-Satz** (derender-Prompt, CPU 4 Kerne,
median 429 s/Wort — deutlich über den 2–6 min der 8-Kern-Messung;
`to_candidate` unverändert): **14/19 gescort, 5 failed** am
Ein-Punkt-Strich-Kontraktbruch — und zwar die GESAMTE und-Familie
(und, und-3, und-4) plus muß-2 und die-2; die T0-Klasse, die auf
dem 10er-Satz `Wer` traf, wandert mit den Crops (Wer scort
diesmal 0,1033). dtw-Median 0,0951 (10er-Satz: 0,0956 —
konsistent) · p90 0,297 · worst unter 0,390 · aiou 0,6955 ·
`retrace_missing` 18 (r ≈ 0 fast überall) · **lift_delta +47** —
die bekannte Signatur: das Modell setzt ab, statt zurückzufahren.
Kreuzungen weiter vergleichsweise sauber (15 fehlend/2 unecht auf
14 Wörtern). Stärken bleiben komplementär: die muß-Klasse schlägt
die Kette klar (muß 0,081 · muß-3 0,097 gegen 0,242/0,234), die
0,039. **Der B2-Prüffall ist bestätigt, deutlicher als erwartet:
Galoppieren (Crop-Ratio 4,34 > Trainingsfiltergrenze 4,0) kollabiert
flächig** — aiou **0,347** (jedes andere Wort ≥ 0,59), beide
Chamfer ~0,11 (3× Satz-Median), +13 Lifts, cross 2/8, Marken
0/1+1: die Langseiten-Skalierung verschenkt die halbe
y-Token-Auflösung, das Wortbild zersplittert. Die
§7.4-B2-Maßnahme (Tiling auf w/h ≤ 2) hat damit ihren gemessenen
Probestein; Priorität unverändert Welle 2. Diagnose-Spalte:
`direction_uncertain` 3 = wieder exakt die muß-Klasse (wie beim
Lotsen — ein Hinweis auf die ß-Strich-Zerlegung dieser Referenzen,
Autopsie-Kandidat der L2-Restliste). Damit sind ALLE stehenden
Routen auf dem 19er-Dev-Satz vermessen; der Eintrag ist
vollständig.

### Route „Lotse" v0.7 `aug17` — Vorregistrierung: die Zonen-Ausweitung der Kartenfahrt (L1)

Geschrieben und committet VOR der ersten Zahl. Die Autopsie der
Re-Baseline (tintenfolger.md §7.10, Befund 3) lokalisiert die 31
fehlenden Kreuzungen im **Junction-Pinch**: der Viterbi routet
beide Pässe eines Schleifenschlusses über dieselben 1–3
Korridor-Pixel; die adoptierte v0.5-Kartenfahrt triggert dort
korrekt, aber nur auf 1–2 Samples — ein einzelnes
karten-gerittenes Sample macht aus den zwei tangentialen
Y-Zusammenläufen kein transversales X (Instrumentierung `will`:
4 von 173 Samples map-priorisiert, je 1 pro l-Schleifenschluss;
Fenster-Bilder will/die/muß). Neuer MECHANISMUS im Sinne der
§7.9-Leitplanke: nicht der Trigger wird weicher, seine WIRKUNG
wird räumlich ausgeweitet.

**EIN Knopf: `RIDE_DOUBLE_ZONE_MARGIN_UNITS`** — jedes
v0.5-getriggerte Sample weitet die Karten-Vorfahrt auf seine
Nachbar-Samples innerhalb dieses Bogenabstands (in xh, entlang
der Sample-Kette desselben Strichs) aus; der spätere Pass fährt
damit die KARTE durch den ganzen Pinch statt durch 1–2 Punkte,
und das X entsteht mit dem Kreuzungswinkel der komponierten
Karte. Einfachpässe, Brücken und alles außerhalb der geweiteten
Zonen bleiben unberührt; der erste Pass bleibt auf der
Tinten-Mitte. Leiter 0,0 (= aus, heutiges Verhalten) / 0,35 /
0,7.

**Erwartung (benannt, damit ein Negativ lesbar ist):** die
Junction-Pinch-Klasse der 31 fehlenden Kreuzungen kehrt
substanziell zurück — konkret erwartete Rückkehrer: die zwei
l-Schleifen in `will` (4,22/5,28), die d-Schleifen in
die/die-2/das/laden, die z/w-Schlüsse in `zwei`, Anteile der 8
Galoppieren-Kreuzungen und die ß-Stamm-Kreuzung der muß-Klasse
(dann entfällt L2 teilweise); `retrace_spurious` (22) und
`touch_cand` (41) fallen Richtung Hand-Niveau; dtw auf den
Struktur-Wörtern fällt oder hält. `aiou` gibt nur INNERHALB der
geweiteten Zonen nach.

**Gates und Kills (wie v0.1/v0.5):** Kette-Vergleich gepaart
gegen die `aug17`-Baseline; Co-Primär-Gates Marken und
`cross_missing+spurious` ohne Netto-Anstieg gegenüber dem
v0.5-Lotse-Stand (31+4); **Zusatz-Kill `aiou`-Median-Δ < −0,02
gegenüber dem v0.5-Stand (0,7631) = verworfen**; erzeugt die
Karten-Geometrie in den Zonen netto > +2 unechte Kreuzungen über
das Soll, ist die Karten-Platzierung dort zu schlecht —
verworfen, zurück zur Sub-Strich-Trennung (§7.9). Beide
Leiter-Stufen werden gemessen, adoptiert wird höchstens EINE
(die bessere, sofern sie alle Gates besteht).

**Gemessen `aug17` — 0,35 ADOPTIERT (alle Gates bestanden), 0,7
vom aiou-Kill verworfen; die Erwartung traf nur TEILWEISE — der
Fund präzisiert die Schleifen-Klasse endgültig.** Leiter (dev-19,
je 19/19 ok): 0,35 → dtw 0,0858 (v0.5: 0,0850, +0,0008) · aiou
0,7493 (−0,0138, hält) · **cross_missing 31 → 27, Netto-Defekte
35 → 32** · retrace 5+22 → 4+21 · **`retrace_arc_ratio`-Gap
0,285 → 0,044** (Median 0,956 — praktisch Hand-Niveau) · touch
41 → 38, overlap 2 → 1 · p90 +1,1 %. 0,7 → aiou 0,7404
(−0,0227) → Zusatz-Kill. Struktur vor Distanz, alle Wächter im
Rahmen → `RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0,35. ABER: die
Rückkehrer (Wer +2, Galoppieren +1, die-2 +1) sind die
PUNKT-Pinch-Unterklasse — die erwarteten Schleifen-Rückkehrer
(will 2× l, zwei, die, unter, muß-Stamm) blieben ALLE bei 0.
Autopsie-Bild (will, v0.5 vs. m035): der Aufwärts-Pass BOARDET
die verschmolzene Schiene genau auf Kreuzungshöhe — unterhalb
des Schleifenschlusses existiert gar keine Pixel-Wiederbelegung,
die ein Occupancy-Trigger sehen könnte; der Selbstschnitt der
Karte wird beim Aufsteigen durch einen tangentialen Board-Hop
ERSETZT. Ein Occupancy-Mechanismus kann diese Klasse
prinzipiell nicht erreichen — der Rettungsweg ist ein ANDERER
Trigger (unten), keine weichere Schwelle.

### Route „Lotse" v0.8 `aug17` — Vorregistrierung: Karten-Vorfahrt an Karten-Selbstschnitten (L1b)

Geschrieben und committet VOR der ersten Zahl. Der v0.7-Fund:
die Schleifen-Klasse der fehlenden Kreuzungen (will/zwei/die/
unter/muß u. a., der Großteil der verbleibenden 27) entsteht
NICHT durch Doppel-Belegung, sondern durch den Board-Hop — der
Ritt ersetzt den Selbstschnitt der Karte durch ein tangentiales
Aufsteigen auf die verschmolzene Schiene. Die KARTE hat die
Kreuzung (das Soll ist duktus-deterministisch, ihre
Selbstschnitte sind berechenbar); der neue TRIGGER ist darum der
**Karten-Selbstschnitt selbst**: Um jeden Selbstschnittpunkt der
komponierten Karten-Striche bekommen die Karten-Samples BEIDER
beteiligter Pässe innerhalb eines Bogenfensters im Viterbi
ausschließlich den Brücken-Zustand (die v0.4-Geometrie, mit dem
richtigen Auslöser) — beide Züge fahren die Karte durch die
Kreuzung, das X ist das X der Karte, mit ihrem Winkel; außerhalb
der Fenster ändert sich nichts, v0.5 + v0.7 bleiben aktiv.

**EIN Knopf: `MAP_CROSSING_WINDOW_UNITS`** (0,0 = aus). Leiter
0,35 / 0,6. Erwartung: die Schleifen-Klasse kehrt zurück —
konkret will (2× l-Schleife), zwei, die/die-2, unter (bis 3),
die muß-Stamm-Kreuzung (×3) und weitere Galoppieren-Anteile;
`cross_missing` fällt klar unter 27, Ziel-Richtung ≤ 15 (das
Ketten-Niveau). Benanntes Risiko: an Soll-Kreuzungen, die DIESE
Hand nicht schreibt (linken 4 vs 3, mit-2 2 vs 1), zeichnet das
Fenster ein X, das die Hand nicht hat → +spurious dort ist
erwartbar und im Gate enthalten. **Gates:** Marken und
`cross_missing+spurious` ohne Netto-Anstieg gegenüber dem
v0.7-Stand (27+5 = 32); aiou-Median-Δ < −0,02 gegenüber 0,7493 =
verworfen; p90-Wächter ≤ +10 % gegen die Kette wie gehabt;
`dtw_reversed_better` = 0. Kill: bleibt die Schleifen-Klasse
auch mit erzwungener Karten-Fahrt aus (die Karte selbst liegt
dann zu weit von der Tinte), ist der ehrliche Rest die
Sub-Strich-Trennung aus Breiten-Evidenz (§7.9) — und die
Karten-PLATZIERUNG wird als eigener Befund an die
Kompositions-Schiene zurückgegeben.

**Gemessen `aug17` — BEIDE Stufen vom aiou-Kill verworfen; die
Topologie-Hypothese ist zugleich SO STARK bestätigt wie kein
Arm zuvor.** Leiter (dev-19, je 19/19 ok): w0,35 →
**cross_missing 27 → 2, spurious 5 → 2** (Netto-Defekte 32 → 4),
`retrace_spurious` 21 → 3, touch 38 → 20, **dtw-Median 0,0858 →
0,0576** — erstmals unter der Kette (0,0579; gepaart Δ-Median
−0,0075, Sign 11:8), p90 0,1187 gegen Kette 0,2363 — aber aiou
0,7493 → 0,7264 (Δ −0,0229 < −0,02) und Recall-Chamfer 0,0492 →
0,0522: **Kill feuert um 0,003.** w0,6 → gleiche Strukturzahlen
(2+2), aiou 0,6744 (−0,075) → tiefer Kill. Der Sichtbeweis
(will/muß-Fenster): alle drei will-Kreuzungen und die
ß-Stamm-Kreuzung kehren zurück — die Schleifen-Klasse ist
GENAU die vorregistrierte. Diagnose des Kills: die Fenster
fahren die ROHE Karte, und deren lokaler Versatz zur Tinte
(bis ~0,5 xh — die bekannte Platzierungs-Toleranz der
Komposition) verlässt den Tintenkörper; der Wächter tut exakt
seinen Dienst — „Geometrie aus der Tinte" ist in den Fenstern
verletzt. Rettungsweg (benannt, eigene Pre-Reg unten): die
Fenster ans Ink PINNEN — Topologie und Winkel von der Karte,
die Lage von den Board-Punkten der Tinte. §7.9-Zeile im selben
PR.

### Route „Lotse" v0.9 `aug17` — Vorregistrierung: gepinnte Selbstschnitt-Fenster (L1c)

Geschrieben und committet VOR der ersten Zahl. Der v0.8-Befund:
die Selbstschnitt-Fenster liefern die Struktur vollständig
(Netto-Defekte 32 → 4), bezahlen aber mit der ROHEN
Karten-Geometrie — deren lokaler Versatz kostet Tinten-Deckung
(aiou-Kill). v0.9 behält Trigger und Fenster UNVERÄNDERT und
ändert allein die GEOMETRIE der Fenster-Strecke: jeder maximale
Fenster-Lauf wird als Ganzes so verschoben, dass seine Enden auf
den benachbarten BOARD-Punkten der Tinte liegen (linear
interpolierter Versatz zwischen beiden End-Offsets; Läufe an
Strich-Enden nehmen den einen verfügbaren Offset konstant; reine
Karten-Striche bleiben roh). Damit stammen Topologie und
Kreuzungswinkel weiter von der Karte, die LAGE aber von der
Tinte — „Geometrie aus der Tinte, Ordnung aus dem Prior", auf
das Fenster selbst angewandt. Natürliche Brücken (fehlende
Tinte) bleiben unangetastet; die adoptierten v0.5/v0.7-Zonen
ebenso.

**EIN Knopf: dieselbe `MAP_CROSSING_WINDOW_UNITS`-Leiter 0,35 /
0,6, jetzt mit Pinning (`MAP_CROSSING_PIN` fest an, kein eigener
Suchknopf).** Erwartung: Strukturzahlen ~wie v0.8 (2+2 bleibt),
aiou kehrt Richtung v0.7-Niveau zurück (der Versatz war die
einzige benannte Kostenquelle), dtw hält oder fällt weiter.
**Gates unverändert wie v0.8** (Netto-Defekte ≤ 32, aiou-Δ ≥
−0,02 gegen 0,7493, p90 ≤ +10 % gegen Kette, Marken, reversed
= 0). Kill: bleibt aiou auch gepinnt unter der Schranke, liegt
der Versatz nicht in der Karten-LAGE, sondern die Karte ist im
Fenster FORMfremd — dann ist die ehrliche Grenze erreicht und
der Rest gehört der Sub-Strich-Trennung (§7.9).

**Gemessen `aug17` — 0,35 ADOPTIERT (alle Gates bestanden), 0,6
vom aiou-Kill verworfen (−0,039). Die stärkste Zahl der
Kampagne.** Leiter (dev-19, je 19/19 ok): w0,35 gepinnt → dtw
**0,0578** (Ketten-Niveau 0,0579; gepaart gegen die Kette
**Δ-Median −0,0183 = −24 %** — erstmals erfüllt eine Route das
Primär-Kriterium „≥ 20 % Fall") · p90 **0,1179** (Kette 0,2363)
· worst muß-2 0,1473 · `cross_missing` 3, `spurious` 4
(Netto-Defekte 32 → **7**) · `marks_missing` 0 (die Kette
verliert 1 — der Lotse findet Galoppierens i-Punkt per Karte) ·
retrace 5+4 · touch 20 · aiou 0,7351 (Δ −0,0142, hält) ·
reversed 0. Die Wort-Tabelle dreht das Komplementaritäts-Bild:
der Lotse gewinnt jetzt JEDES strukturschwere Wort (unter
−0,376 · Galoppieren −0,147 · muß −0,126 · muß-3 −0,109 ·
muß-2 −0,061 · die-2 −0,041 · die −0,035 · das −0,024 · zwei
−0,018 · laden −0,018) und verliert die glatten nur noch
mikroskopisch (will +0,006 statt +0,081 — die gepinnten
Fenster reparierten auch die Schleifen-GEOMETRIE; Maximum
linken +0,019). Sign-Test 10:9 (beschreibend). w0,6 →
cross_missing 1, aber aiou 0,7106 (−0,0387) → Kill.
`MAP_CROSSING_WINDOW_UNITS` = 0,35, `MAP_CROSSING_PIN` = True.

**Die verbleibenden 7 Defekte sind kartiert und fast
vollständig SOLL-Differenzen, keine Ritt-Fehler:** Galoppieren
2/8 fehlend = exakt die p-Unterlängen-Kreuzungen, die schon der
KOMPOSITION fehlen (kein Fenster ohne Karten-Kreuzung — der
G1-Autorenschritt aus §7.10 ist jetzt der limitierende Faktor
dieses Worts); linken +3 und mit-2 +1 unecht = exakt die
vorbenannten Soll-Kreuzungen, die DIESE Hand nicht schreibt
(Beleg-Varianz, im v0.8-Risiko benannt); unter 1/3 fehlend als
letzter echter Ritt-Rest. Routen-Stand nach der Runde: **der
Lotse steht auf dem 19er-Dev-Satz erstmals GLEICHAUF mit der
Kette im Median, halbiert ihren p90, schlägt sie gepaart um
24 % und trägt die sauberere Struktur** — die
Bestätigungssätze (A, dann B) bleiben der Schlussstein, bevor
daraus eine Adoptionsentscheidung jenseits der
Routen-Konstanten wird.

### Route „Lotse" v0.10 `aug19` — Vorregistrierung: Knoten-Anker-Pinnung der Karten-Läufe (L1d)

Geschrieben und committet VOR der ersten Zahl. Anlass: der
Owner-Sichtbefund an der Duell-Ansicht (2026-08-19) — „beim k wird
der untere Kringel nicht nachgefahren", das W in `Wer` „macht
Quatsch", der r/e-Auslauf in `Galoppieren` fährt eckige Luft-Züge.
Die Kategorien-Autopsie (Instrumentierung: jedes Sample nach
Mechanismus eingefärbt — Schiene · Brücke · Doppelzonen-Ride ·
Fenster) lokalisiert die Exkursionen vollständig in der
KARTEN-Geometrie, in zwei Klassen:

1. **Verschmolzene Fenster-Läufe.** `map_crossing_masks` legt um
   JEDEN Karten-Selbstschnitt ±0,35 xh; wo Selbstschnitte dicht
   stehen, ketten die Fenster zu EINEM Lauf (linken: 4,32 xh am
   k-Komplex aus Kopfschleife + Kringel + Stamm — 71 von 253
   Samples; mit: 2,76 xh am t-Rückpass; Galoppieren: 3,72 und
   2,64 xh; ein Einzel-Fenster wäre 0,96 xh). Die v0.9-Pinnung
   interpoliert NUR zwischen den Lauf-ENDEN — über solche Läufe
   reicht sie die rohe (bis ~0,5 xh versetzte) Karten-Form im
   Innern durch: exakt die „Quatsch"-Züge des Sichtbefunds.
2. **Rohe Doppelzonen-Rides und Brücken.** Die adoptierten
   v0.5/v0.7-Zonen-Rides und die natürlichen Brücken zeichnen die
   Karte weiterhin UNGEPINNT (Wer: 13, Galoppieren: 32
   Zone-Samples) — dieselbe Fehlerklasse, die v0.9 für die
   Fenster bereits behoben hat.

**Anker-Evidenz (vor der Maßnahme gemessen):** jeder
Karten-Selbstschnitt der vier Verlierer-Wörter hat einen
Skelett-VERZWEIGUNGSKNOTEN in ≤ 0,6 xh (Median 0,06–0,19; mit
6/6, linken 16/16, Wer 10/10, Galoppieren 32/32 innerhalb 1,0 xh)
— die Tinte benennt den Ort der Kreuzung selbst, das Fenster muss
ihn nur ansteuern.

**EIN Mechanismus: die verallgemeinerte Pinnung.** Jeder
Karten-Lauf wird über eine Offset-Polylinie mit KNOTEN gepinnt:
die Lauf-Grenzen (benachbarte Board-Punkte — die v0.9-Mathematik,
unverändert) PLUS je Karten-Selbstschnitt im Lauf ein ANKER
(Offset = nächster Verzweigungsknoten − Selbstschnittpunkt,
Suchradius `PIN_KNOT_NODE_RADIUS_UNITS` = 1,0 xh fest, kein
Suchknopf; ohne Knoten in Reichweite entfällt der Anker). Linear
zwischen benachbarten Knoten, konstant jenseits der äußersten;
ein Lauf ganz ohne Knoten bleibt roh (wie v0.9s „Strich ganz aus
Karte"). Beide Pässe eines Selbstschnitts erhalten denselben
Anker — das X der Karte landet konstruktiv auf dem Knoten der
Tinte (die §13a-Extrapolations-Idee als Konstruktion, dieselbe
Verwandtschaft wie beim v0.3-Arm, jetzt ohne dessen
Flächen-Kosten, weil nur KARTEN-Läufe bewegt werden, nie
Schienen-Ritte).

**Leiter (`MAP_RUN_PIN_KNOTS`): "off" (= v0.9) / "windows" (nur
Fenster-Läufe bekommen Knoten-Pinnung) / "all" ("windows" +
dieselbe Knoten-Pinnung für Doppelzonen-Rides und natürliche
Brücken).** Beide Stufen werden gemessen, adoptiert wird
höchstens EINE. Erwartung: linken/mit/mit-2/Wer/Galoppieren
fallen in dtw (die fünf tragen die größten Ketten-Vorsprünge des
v0.9-Stands), `aiou` steigt (weniger Luft), Kreuzungs-ZAHLEN
unverändert (Topologie bleibt die der Karte), Kreuzungs-Ortsfehler
fällt; keine neue Struktur.

**Umgebungs-Deklaration.** Diese Runde läuft lokal (WSL2, BLAS
gepinnt); die aug17-Zahlen stammen aus der Cloud-Session. Neu
gemessene lokale Basis: Kette dtw 0,0576 med (aug17: 0,0579 —
Solver-Umgebungsvarianz, dokumentierte Klasse), Lotse v0.9
0,0578 · aiou 0,7351 · cross 3+4 · marks 0+1 (deterministisch,
BYTE-gleich mit aug17). Alle gepaarten Vergleiche dieser Runde
laufen gegen die LOKALE Kette.

**Gates (wie v0.9):** Marken und `cross_missing+spurious` ohne
Netto-Anstieg gegenüber dem v0.9-Stand (3+4 = 7);
`aiou`-Median-Δ ≥ −0,02 gegen 0,7351; p90 ≤ +10 % gegen die
Kette; `dtw_reversed_better` = 0. Zusatz-Kill: `cross_spurious`
netto > +2 → die Anker greifen den falschen Knoten (das benannte
Risiko der dichten Regionen — Galoppieren p90-Ankerabstand
0,51 xh) → verworfen, Rettungsweg wäre ein kleinerer Suchradius
NUR mit frischer Vorregistrierung.

**Gemessen `aug19` — BEIDE Stufen vom Kreuzungs-Gate verworfen;
der Fund benennt den Degenerierungs-Mechanismus präzise und die
Gewinnseite ist die stärkste Tinten-Deckung der Route.** Leiter
(dev-19, je 19/19 ok): "windows" → Netto-Kreuzungsdefekte 6+3 =
9 (> 7) · aiou 0,7616 (+0,027!) · dtw gepaart gegen Kette
−0,0097 (schlechter als v0.9s −0,0182); "all" → Defekte 5+5 =
10 (> 7) · aiou 0,7616 · gepaart gegen v0.9: 14 von 19 Wörtern
besser (Δ-Median −0,0037, Sign 14:5, p=0,064), beide
Chamfer-Hälften besser, `retrace_arc_ratio`-Gap −0,047,
**Kreuzungs-Ortsfehler-Median 0,116 → 0,083 xh** und die
SPURIOUS-Klasse heilt (linken 3 → 1, mit-2 1 → 0 — wo die Hand
das Soll-X nicht schreibt, hat die Tinte keinen Knoten, und der
Anker degeneriert das Karten-X von selbst: der Mechanismus
arbeitet in beide Richtungen). Der Sichtbefund bestätigt: der
k-Kringel in `linken` wird erstmals nachgefahren, der
V-Spike unter die Grundlinie ist weg. ABER die Anker KOSTEN
Kreuzungen genau dort, wo sie dicht stehen: `mit` verliert eins
der zwei nur 0,07 xh getrennten t-X (auf einen Punkt gezogen →
Detektor-Merge), `zwei` beide z-Unterschleifen-X (0,25 xh
Abstand, gemittelte Offsets → Berührung statt Durchstoß),
`will` das zweite l-X (Punktlandung beider Pässe auf dem Knoten
→ oskulierend statt piercend), und `Galoppieren` fabriziert 4
unechte an Interpolations-Knicken des dichten „ieren"-Clusters.
Diagnose in einem Satz: **das Offset-Feld der Punkt-Knoten
variiert nahe der Kreuzung zu schnell — Scherung und Mittelung
zerstören genau die Transversalität, die der Anker herstellen
soll.** VERWORFEN (beide Stufen), `MAP_RUN_PIN_KNOTS` bleibt
"off". Rettungsweg (benannt, eigene Pre-Reg unten): das
Offset-Feld um jeden Anker lokal KONSTANT machen — reine
Translation erhält jedes X exakt (v0.11); §7.9-Zeile im selben
PR.

### Route „Lotse" v0.11 `aug19` — Vorregistrierung: Plateau-Anker (stückweise-starre Fenster, L1e)

Geschrieben und committet VOR der ersten Zahl. Der v0.10-Fund:
Anker-Offsets als PUNKT-Knoten scheren das Offset-Feld an genau
den Stellen, deren Transversalität sie sichern sollen — eine
Kreuzung überlebt eine lokal REINE TRANSLATION dagegen exakt
(beide Pässe verschieben sich gleich, das X wandert starr mit).
Der neue MECHANISMUS: jedes Anker-Offset wirkt als **Plateau**
konstanter Breite statt als Punkt — `PIN_KNOT_PLATEAU_UNITS` =
0,35 xh beidseitig (= der Fensterradius, deklariert fest, kein
Suchknopf); überlappende Plateaus VERSCHMELZEN zu einem
Intervall mit dem Mittel ihrer Anker-Offsets (der dichte
Cluster wird als Ganzes starr verschoben — beide X bleiben
erhalten, jedes landet ≤ halber Clusterbreite neben seinem
Knoten, weit innerhalb des 0,55-xh-Matchers); zwischen Plateaus
und zu den Lauf-Grenzen wird weiter linear interpoliert — die
Scherung wandert in die kreuzungsfreien Zwischenstrecken.
Mittelung je EINZEL-Index entfällt (sie war die zweite
Degenerierungsquelle).

**Leiter: dieselben zwei Stufen wie v0.10 ("windows" / "all"),
jetzt mit Plateau-Feld.** Gates unverändert (Netto-Defekte ≤ 7,
aiou-Δ ≥ −0,02 gegen 0,7351, p90 ≤ +10 % gegen Kette, Marken,
reversed = 0, `cross_spurious` netto ≤ +2). Erwartung: die
v0.10-Gewinne bleiben (aiou ~0,76, Ortsfehler ~0,083,
Spurious-Heilung, k-Kringel), die vier Verlust-Stellen
(mit-t-Doppel, zwei-z-Doppel, will-l2, Galoppieren-Knicke)
kehren auf den v0.9-Stand zurück. Kill: verliert auch das
Plateau-Feld Kreuzungen in den dichten Clustern, ist die
Anker-Idee an der Dichte-Grenze ehrlich gescheitert und der
Rest gehört der Karten-FORM (Kompositions-Schiene: der
k-Kopfschleifen-Bogen bleibt auch gepinnt formfremd —
eigener Befund unten).

**Gemessen `aug19` — "windows" ADOPTIERT (alle Gates bestanden),
"all" um genau ein Doppel-X verworfen; eine
Semantik-Korrektur unterwegs, beide Messungen berichtet.** Die
Erstmessung implementierte die Verschmelzung LAUF-lokal — kreuzende
Pässe konnten so verschiedene Plateau-Mittel bekommen, und `mit`/
`zwei` verloren weiter je ein echtes X: die deklarierte Semantik
(„der dichte Cluster wird als Ganzes starr verschoben") verlangt
die GLOBALE Fusion über alle beteiligten Pässe (Union-Find über
die Anker-Identitäten). Mit der deklarierten Semantik (dev-19,
je 19/19 ok):

- **"windows": Netto-Kreuzungsdefekte 1+6 = 7 (= v0.9-Stand,
  Gate hält), `cross_missing` 3 → 1** — mit/zwei/will vollständig
  zurück, und **Galoppierens zwei Kompositions-fehlende
  p-Unterlängen-X kehren als einzige ECHTE Struktur-Neuheit der
  Route zurück** (das Plateau-Feld öffnet den Karten-Retrace zur
  Schleife, wie die Tafel sie schreibt — der G1-Autorenschritt
  verliert seinen Rang als limitierender Faktor); Rest-Missing
  ist allein unters letzter Ritt-Rest. Kreuzungs-Ortsfehler-Median
  **0,116 → 0,066 xh (−43 %)** · aiou 0,7434 (+0,0083) · p90
  0,1179 → **0,1129** · marks 0+1 unverändert · rev 0 · gepaart
  gegen v0.9: Δ-Median −0,0018, Sign 13:6. Kosten, ehrlich:
  eigener dtw-Median 0,0578 → 0,0596, gepaart gegen die Kette
  −0,0137 = **−18,0 %** (v0.9: −24 %) — der Präzedenzfall ist
  v0.7 („Struktur vor Distanz"); `retrace_missing` 5 → 6; und die
  Spurious-Klasse wechselt ihren Charakter: 6 statt 4, davon
  linken 3 → 1 GEHEILT, aber 4 der 6 sind **Doppel-X-Duplikate**
  (dieselbe Kreuzung zweimal gezeichnet, weil die gepinnten
  Pässe durch den Knoten doppelt wackeln: Galoppieren 2, mit-2 1,
  will 1) plus ein echtes Erfundenes (Galoppieren u≈13,4).
  `MAP_RUN_PIN_KNOTS` = "windows".
- **"all"**: identische Heilung, aiou sogar 0,7521, aber
  Galoppieren trägt ein viertes Spurious → Netto 8 > 7,
  VERWORFEN um genau dieses eine Doppel-X. Die Zonen-Rides und
  Brücken (der Rest-Kasten in Galoppieren x≈360, die
  Wer-Diagonale) bleiben damit roh — ihr Pinning ist hinter der
  Doppel-X-Frage eingereiht, nicht verworfen.

Sichtbefund zum Owner-Anlass: **der k-Kringel in `linken` wird
nachgefahren**, der V-Spike ist weg; verbleibend fährt die
k-KOPFSCHLEIFE als flacher Bogen durchs Schleifen-Innere — die
KARTE selbst ist dort formfremd (der komponierte k-Bogen liegt
tiefer/schmaler als diese Hand schreibt): ein
Kompositions-/Laufform-Befund, kein Ritt-Fehler, notiert für die
Kompositions-Schiene. Offene Blöcke nach der Runde:
(i) die Doppel-X-Duplikate — der benannte nächste Mechanismus
ist EIN X je Knoten-Cluster (Begradigung der Fenster-Teilbahn je
Pass durch den Knoten), er würde zugleich die "all"-Stufe
freischalten; (ii) die Karten-Form-Klasse (k-Kopfschleife,
W-Ansatz = K3, Autorenschritt). §7.9-Zeilen im selben PR.

### Route „Lotse" v0.12 `aug19` — Vorregistrierung: die Plateau-Sehne (Doppel-X-Begradigung, L1f)

Geschrieben und committet VOR der ersten Zahl. Der v0.11-Rest:
4 der 6 Spurious sind Doppel-X-Duplikate — die gepinnte
Fenster-Teilbahn eines Passes WACKELT durch die
Knoten-Nachbarschaft und schneidet den anderen Pass zweimal
(Kreuzungs-Orte 0,06–0,11 xh auseinander), dazu ein an einem
Interpolations-Knick erfundenes X (Galoppieren u≈13,4). Der neue
MECHANISMUS: **innerhalb jedes (verschmolzenen) Plateau-Intervalls
wird die Teilbahn jedes Passes durch ihre SEHNE ersetzt**
(Interior-Samples linear zwischen den beiden Intervall-Rändern des
eigenen Passes) — zwei Sehnen schneiden sich höchstens EINMAL, das
Doppel-X ist konstruktiv unmöglich. Verwandt mit dem verworfenen
v0.3 (Knoten-Sehne), aber ohne dessen Flächen-Kosten: v0.3
begradigte SCHIENEN-Ritte überall (aiou-Kill −0,045); die
Plateau-Sehne begradigt nur KARTEN-Geometrie, die bereits im
starren Plateau liegt — die Abweichung ist durch die Plateau-Breite
(±0,35 xh) gedeckelt, und Schienen-Ritte bleiben unberührt.

**Leiter: "windows"+Sehne / "all"+Sehne** (EIN Knopf
`PIN_PLATEAU_CHORD` aus/an; die "all"-Wiedervorlage ist der in
§7.9 benannte Rettungsweg — die Zonen-Rides und Brücken werden
erst gepinnt, wenn die Sehne die Doppel-X-Quelle schließt).
**Gates gegen den v0.11-Stand:** Netto-Kreuzungsdefekte ≤ 7 UND
`cross_spurious` ≤ 6 (kein Anstieg); `cross_missing` ≤ 1 (die
geheilte Missing-Klasse darf nicht zurückfallen);
`aiou`-Median-Δ ≥ −0,02 gegen 0,7434; Marken ohne Netto-Anstieg;
p90 ≤ +10 % gegen die Kette; `dtw_reversed_better` = 0.
Erwartung: die 4 Duplikate verschwinden (spurious → ~2), dtw
~neutral, aiou ~neutral (Sehne bleibt im Plateau); bei "all"
zusätzlich der Galoppieren-Rest-Kasten (x≈360) und die
Wer-Diagonale gepinnt, aiou eher steigend. Adoptiert wird
höchstens EINE Stufe (die bessere, sofern alle Gates bestehen).
Kill: kostet die Sehne Missing-Kreuzungen (der Wackel WAR das X)
oder aiou, bleibt v0.11 stehen und die Duplikat-Frage geht als
ehrliches Negativ mit benanntem Rest in §7.9.

**Gemessen `aug19` — BEIDE Stufen verworfen, das benannte Kill
feuert in voller Stärke: der Wackel WAR das X.** Leiter (dev-19,
je 19/19 ok): "windows"+Sehne → `cross_missing` 1 → **8**,
spurious 6 → 1, `retrace_missing` 6 → **12**, dtw auf 16 von 19
Wörtern schlechter (Δ-Median +0,0014, Sign 3:16, p=0,004), aiou
−0,0075; "all"+Sehne → 7 missing / 2 spurious, gleiches Bild. Die
Diagnose ist geometrisch eindeutig: an den Sütterlin-Schleifen-
schlüssen laufen beide Pässe TANGENTIAL durch die Knoten-
Nachbarschaft (die Junction-Pinch-Geometrie) — ihre Sehnen sind
nahe-parallel und schneiden sich GAR NICHT; erst der Wiggle der
Karten-Teilbahn stellt die Transversalität her, und er trägt
Kreuzung UND Duplikat untrennbar. Zugleich zerstören die Sehnen
die Retrace-Zonen im Plateau (12 fehlend). VERWORFEN,
`PIN_PLATEAU_CHORD` bleibt False; v0.11 "windows" bleibt der
adoptierte Stand. Rettungswege (§7.9-Regel, je eigene Pre-Reg):
(i) **Entdrillung statt Begradigung** — Duplikat-PAARE desselben
Pass-Paars (Kreuzungs-Orte < 0,3 xh) topologisch entdrillen, indem
der kleinere Wiggle-Bogen zwischen den beiden Schnittpunkten
EINES Passes gespiegelt wird (entfernt genau ein X, erhält das
andere samt Winkel); (ii) **asymmetrische Sehne** — nur der
SPÄTERE Pass wird begradigt, der frühere behält seine Kurve
(bricht die Parallel-Degenerierung, weil nur eine Seite
linearisiert). Beides bleibt hinter der Feststellung eingereiht,
dass die 4 Duplikate KEINE Topologie-Erfindung sind (das X ist
real, nur doppelt gezählt) — der Leidensdruck ist entsprechend
klein, und die "all"-Wiedervorlage wartet auf den Mechanismus,
der die Duplikate schließt, ohne das X zu kosten.

### L2-Rest-Autopsie `aug19` — die Kollaps-Klasse (unter + muß×3) ist ORDNUNGS-dominiert: der Deckbogen sitzt in der Ketten-Assembly an der falschen Sequenz-Position

Befund, kein Knopf (die in §7.10 L2 und in der `aug17`-Re-Baseline
benannte Rest-Autopsie, ausgeführt und noch am selben Tag um eine
FALSCHE Erst-Attribution korrigiert — beide Fassungen stehen der
Ehrlichkeit halber im Verlauf dieses Branches). Auslöser der
Korrektur: die Owner-Frage „das er von unter ist ja ganz schlecht —
war das schon immer so?" und der Lotse-Widerspruch (0,063 auf
derselben Referenz — ein Referenz-Defekt hätte JEDE Route deckeln
müssen).

**Die Erst-Fassung war doppelt falsch:** (1) das Diagnose-Skript
resampelte NACH der Body-Konkatenation statt je Strich — die
Absetz-Sprünge wurden zu synthetischen Bogen-Zonen (das Lineal
selbst resampelt je Strich, `summary.score_word` →
`resampled_strokes`; die „Rücklauf-Zonen" bis 6,75 xh waren zum
Teil Artefakt); (2) der ü-/u-Deckbogen ist NICHT verbunden
gezeichnet — er ist in allen betroffenen Referenzen ein eigener,
ABGESETZTER Strich (unter: 54 Samples · Bogen 1,10 xh; muß: 59
Samples), liegt damit aber über der 0,8-xh-Marken-Schwelle von
`classify_strokes` und bleibt zu Recht im Body (die bekannte
und-Autopsie-Klasse „Deckbogen über der Marken-Schwelle").

**Der wirkliche Mechanismus — mit Beweis-Messung.** Die
Body-Sequenzen: Hand = [Wort, Deckbogen] (Bogen ZULETZT; dieselbe
Ordnung fährt der Lotse, dessen Karte die komponierte
Engine-Ordnung mit endständigen Marken übernimmt — darum sein
0,063). Der KETTEN-Kandidat assembliert dagegen je RUN
zusammenhängender Slots und emittiert den Deckbogen ZWISCHEN den
Runs: unter = [u..t (12,6 xh) · Bogen (1,0 xh) · e..r (12,8 xh)],
muß-Familie analog [erster Teil · Bogen · Rest]. Das forward-DTW
konkateniert in Schreibreihenfolge (die Ordnung IST die Wahrheit)
und zahlt die Sequenz-Inversion voll — `dtw_max_absorption` 132
(der Singularitäts-Wächter zeigte seit `aug14` exakt hierhin).
Beweis durch die Ordnungs-Permutation (Geometrie byte-identisch,
NUR der Bogen ans Ende sortiert): **unter 0,4503 → 0,0854 ·
muß 0,2419 → 0,1096 · muß-2 0,2084 → 0,0877 · muß-3 0,2339 →
0,0962**; der Permutations-Sweep über ALLE 19 Dev-Wörter findet
außerhalb dieser vier keinen einzigen Ordnungs-Gewinn — die
Klasse ist vollständig und exakt die Kollaps-Klasse der Baseline.
`unter` war seit der ersten Zahl so (aug14: 0,4389 „der bekannte
Kollaps-Probefall"); es war nie primär das sichtbare
er-Gekritzel — das kostet den REST (~0,085, der echte
Berührungs-/Überlagerungs-Stapel bleibt die zweite, kleinere
Baustelle).

**Einordnung.** (a) Die Kollaps-Headline der Kette (59,8 % des
Fehlers, §7.1) ist zu ~2/3 eine ASSEMBLY-Eigenschaft des
Kandidaten, kein Fit- und kein Referenz-Defekt; auch die
gespeicherten `traced`-Produktionszeilen tragen dieselbe
Strichfolge. (b) Benannter Kandidat (eigene Vorregistrierung,
nicht Teil dieses Befunds): **die marken-endständige
Ketten-Assembly** — der Kandidat emittiert abgesetzte
Deckbogen-/Markenstriche NACH allen Runs, in der komponierten
Engine-Ordnung, die Lotse und Hand ohnehin teilen. Erwartung aus
der Permutations-Probe: Kette p90 0,236 → ~0,11, unter −0,36,
muß-Klasse −0,11 bis −0,13; das ist eine Änderung des
EINGEFRORENEN Baseline-Kandidaten und damit eine deklarierte
Re-Baseline (alle gepaarten Routen-Vergleiche verschieben sich —
ehrlich gesagt: der Lotse-Vorsprung auf unter/muß schrumpft
entsprechend, er schlug dort zum Teil ein Assembly-Artefakt).
(c) Die Referenzen sind SAUBER — der Todoist-Entscheid
„muß neu nachfahren" ist gegenstandslos und wird zurückgezogen;
der Brief-Hinweis „Marken mit eigenem Absetzen" bleibt für
KÜNFTIGE Nachfahrungen sinnvoll (kleine Marken unter der
Schwelle profitieren vom Zentroid-Matching). (d) A2 (SDM/DCD)
bleibt für muß/unter zurückgestuft — Stranding/Doppelpass sind
seine Ziele. KEINE Gate- oder Lineal-Änderung aus dieser
Autopsie.

### Kette K-A `aug19` — Vorregistrierung: die marken-endständige Assembly (Owner-Go „weiter optimieren")

Geschrieben und committet VOR der ersten Zahl. Der benannte
Top-Kandidat aus der (korrigierten) L2-Rest-Autopsie:
`assemble_word_strokes` läuft heute JE RUN, und die
Diakritika-Striche eines Runs (der eigene Assembler-Begriff:
alle Samples über `DIACRITIC_MIN_Y` = 1,0) landen dadurch
ZWISCHEN den Runs in der Schreibreihenfolge — Hand und
komponierte Engine-Ordnung schreiben sie am WORTENDE. **EIN
Knopf: `HarvestOptions.marks_last`** (CLI `--marks-last`,
Label `chain+order` — wie `--mark-refit` eine Variante der
Baseline, nie die Baseline selbst): die assemblierten Striche
des Wortes werden stabil partitioniert, Diakritika (der
Assembler-eigene Begriff, auf den Word-Unit-Strichen
angewandt) hinter alle Körper-Striche, Reihenfolge innerhalb
beider Gruppen unverändert. Reine ORDNUNGS-Änderung: kein
Punkt bewegt sich.

**Erwartung (aus der Permutations-Probe der Autopsie):**
unter −0,36 (0,4503 → ~0,085), muß-Familie −0,11 bis −0,13;
alle geometrie-basierten Spalten IDENTISCH (aiou, Chamfer,
Struktur- und Markenzähler — dieselbe Segmentmenge), einzig
`dtw_xh` (und die Lift-Positionsspalten) bewegen sich; kein
anderes Dev-Wort ändert sich über ±0,002 (der Sweep fand
keinen weiteren Ordnungs-Gewinn).

**Gates:** (i) die vier Kollaps-Wörter fallen je um > 0,05;
(ii) KEIN Dev-Wort steigt um > 0,002; (iii) aiou/Chamfer/
Zähler byte-gleich (eine Abweichung wäre ein Bug der
Partition, kein Tuning-Fall — Kill); (iv) `dtw_reversed_better`
= 0. Bestehen alle: ADOPTION als Kette v2 (die erste
Formulierungsänderung der Route) mit datierter Re-Baseline —
deklariert: ALLE gepaarten Routen-Vergleiche rechnen ab dann
gegen die v2-Kette, die alten Zahlen bleiben als
v1-Geschichte lesbar; der PRODUKTIONS-Re-Harvest (DB) bleibt
davon getrennt hinter Owner-Go + dbsnapshot.

**Gemessen `aug19` — ALLE Gates bestehen exakt wie
vorregistriert, ADOPTIERT als Kette v2.** Dev-19, gepaart gegen
die v1-Baseline: **unter 0,4503 → 0,0854 (−0,365) · muß-3
0,2339 → 0,0962 · muß 0,2419 → 0,1096 · muß-2 0,2084 →
0,0877**; die übrigen 15 Wörter Δ exakt 0,0000, und JEDE
Geometrie-Spalte byte-gleich (aiou 0,6929, beide Chamfer,
cross 14+7, marks 1+1, retrace 6+13, touch 25, reversed 0) —
die Partition bewegt keinen Punkt, nur die Reihenfolge.
`HarvestOptions.marks_last` = True ist der v2-Default (False
bleibt als Archäologie-Knopf, das Mess-CLI-Flag entfällt mit
der Adoption).

### Kette K-B `aug19` — Vorregistrierung: die Zacken-Reparatur im Trace

Geschrieben und committet VOR der ersten Zahl. Die Zacken-Klasse
des Owner-Sichtbefunds (Galoppieren: das V in den i-Punkt — EIN
Polylinien-Punkt springt 0,44 xh weg und zurück —, die Nadel am
Kopf des ersten p — drei Punkte, 6–11× der Median-Schrittweite)
ist exakt die §11-Ausreißer-Form, für die der geteilte Detektor
`tools.pairlab.anchors` gebaut und an 17 von 22 Owner-Markierungen
validiert wurde. Die STATISTIK-Schicht repariert sie seit §11e;
der Trace zeigt sie bisher absichtlich roh („inspection layer,
needle and all") — eine Doktrin von VOR der Tintenfolger-Kampagne,
in der der Trace zum PRODUKT wurde. **EIN Knopf:
`HarvestOptions.trace_repair`** (CLI `--trace-repair`, Label
`chain+repair` — das A1-Muster: ändert, was der Trace ZEIGT, nie,
was die Ernte MISST): `repair_stranded_anchors` — DIESELBE
geteilte Funktion, kein Zweitbau; das Kriterium ist skalenfrei
(Schritt-Verhältnisse je Strich) — läuft je assembliertem
Trace-Strich; Läufe konsekutiv geflaggter Punkte werden als ein
Stück auf die Sehne der ungeflaggten Nachbarn interpoliert, nie
auf Tinte gesnappt, Anzahl geloggt (`trace_repaired` im Meta).

**Erwartung:** die beiden Galoppieren-Zacken verschwinden
(sichtbar + dtw dort leicht runter); der i-Punkt-Strich fällt
ohne Ausreißer unter die 0,8-xh-Marken-Schwelle — die fehlende
i-Marke DARF heilen (`marks_missing` 1 → 0); alle übrigen
Dev-Wörter ±0,002; `aiou` ~neutral (Zacken liegen in Luft).
**Gates:** kein Dev-Wort schlechter als +0,002; Struktur- und
Markenzähler ohne Netto-Verlust; `aiou`-Median-Δ > −0,005;
reversed = 0. Kill: kostet die Reparatur irgendwo eine ECHTE
Struktur (ein „Spike", der in Wahrheit ein Kreuzungsschenkel
war), ist der Polylinien-Einsatz des Detektors verworfen und der
Weg zurück die Anker-Ebene (keep_solve-Plumbing, eigene
Pre-Reg). Bestehen alle Gates: Adoption als **Kette v3** (die
Trace-Doktrin-Zeile in `chain_word_strokes` wird im selben
Commit umgeschrieben — der Trace ist seit der Kampagne Produkt,
die Inspektion der rohen Nadel bleibt über
`trace_repair=False` erreichbar).

**Gemessen `aug19` — alle Gates bestehen, ADOPTIERT als Kette
v3; die Zacken trugen fast den ganzen Galoppieren-Rest.**
Dev-19, gepaart gegen v2: **Galoppieren 0,2329 → 0,0401
(−0,193)** — die V-Zacke in den i-Punkt und die p-Nadel waren
sein dominanter Fehler, und wie vorregistriert erhofft fällt
der reparierte i-Punkt-Strich unter die Marken-Schwelle:
**`marks_missing` 1 → 0**, `lift_delta` Galoppieren +1 → 0 —
dazu die-2 −0,026, zwei −0,015; kein Wort über +0,0016 (unter,
im Rahmen des +0,002-Gates). Zähler: `retrace_spurious` 13 → 6
und `touch` 25 → 21 (die Zacken WAREN die unechten Zonen),
Kreuzungen exakt unverändert, `aiou` +0,006,
`max_absorption` 94 → 79. Ehrlich benannt: `retrace_missing`
6 → 7 — die Autopsie (Flag-Positionen + Sichtprüfung) verortet
alle sieben unter-Reparaturen bei u 5,6–6,6 IM er-Gekritzel
(der echte t-Stamm-Retrace bei u 4,7–5,1 bleibt unberührt):
eine ZUFALLS-Korrespondenz von Tangle-Geometrie löst sich, die
Netto-Retrace-Defekte fallen 19 → 13 — das Kill („echte
Struktur") feuert nicht. `trace_repair` = True ist der
v3-Default (False = Nadel-Archäologie), die Doktrin-Zeile in
`chain_word_strokes` ist umgeschrieben.

**Re-Baseline Kette v3 `aug19` (deklariert):** dtw-Median
**0,0491** · p90 **0,0894** · worst **muß 0,1096** · marks 0+1
· aiou 0,6987 · cross 14+7 · retrace 7+6 · touch 21. Gepaarte
Vergleiche gegen v3: **Lotse v0.11 Δ-Median +0,0016 (Sign
12:7)** — nach zwei reinen Trace-Schicht-Fixes führt die KETTE
erstmals auf Median UND p90; der Lotse behält Struktur (7
gegen 21 Netto-Kreuzungsdefekte), aiou (0,743) und
Kreuzungs-Ortsfehler (0,066 gegen 0,083 xh). Tagesbogen der
Route: 0,0576/0,2355 → 0,0491/0,0894, ohne dass sich ein
einziger Fit-Parameter bewegt hat — beide Gewinne lagen in der
KANDIDATEN-SchICHT (Ordnung + Ausreißer), nicht im Solver.

**Re-Baseline Kette v2 `aug19` (deklariert, lokale Umgebung der
Runde):** dtw-Median 0,0576 (unverändert — die Median-Wörter
waren nie betroffen) · **p90 0,2355 → 0,0988** · worst jetzt
**Galoppieren 0,2329** (der echte unter-Rest: 0,0854, das
er-Gekritzel aus dem versetzten Karten-Init) · Struktur- und
Markenspalten identisch zu v1. **Gepaarte Routen-Vergleiche
gegen v2:** Lotse v0.11 Δ-Median **+0,0007** (Sign 10:9,
p=1,0) — der −18-%-Vorsprung der Lotse-Route gegen v1 bestand
zu praktisch 100 % aus dem Assembly-Artefakt; die Routen
stehen jetzt im Median GLEICHAUF, die Kette führt beim p90
(0,0988 gegen 0,1129), der Lotse behält die Struktur (7 gegen
21 Netto-Kreuzungsdefekte), die Marken (0 gegen 1 fehlend),
aiou (0,7434 gegen 0,6929) und den Kreuzungs-Ortsfehler
(0,066 gegen 0,083 xh). Das Fusions-Orakel und die
InkSight-/Nullprobe-Paarungen sind mit ihrer nächsten Messung
gegen v2 neu zu beziffern (lokal nicht neu gerechnet — die
absoluten Wortwerte dieser Routen ändern sich nicht, nur ihre
Deltas). Der PRODUKTIONS-Re-Harvest der `traced`-Zeilen mit
v2-Ordnung bleibt hinter Owner-Go + dbsnapshot (die
Fixture-`traced`-Zeilen tragen bis dahin die v1-Ordnung —
der Bench rechnet den `chain`-Kandidaten ohnehin frisch).

### Route „Lotse" v0.13/v0.14 `aug19` — Vorregistrierung: die Entdrillung, dann die „all"-Stufe (Owner-Go „weiter mit lotse neben ink")

Geschrieben und committet VOR der ersten Zahl. Ziel ist der
letzte Owner-Punkt der Runde: der Lotse fährt in Doppelzonen und
Brücken noch die ROHE Karte („windows" pinnt nur Fenster) — die
G-Kästen, die r-Geraden, der Galoppieren-Kasten, die
Wer-Diagonale. Die „all"-Stufe scheiterte am 19. um genau EIN
Doppel-X; der Blocker sind die Duplikate.

**Autopsie vor dem Mechanismus (Roh-Ereignis-Zählung, proper
segment intersections der Body-Kette, 0,35-xh-Eigenbogen-Floor):**
die Duplikat-Orte sind GEWEBE — mehrere Schnitt-Ereignisse
desselben Pass-Paars in kleinem Fenster: mit-2 trägt DREI
Ereignisse, wo die Hand einmal kreuzt (Orte 5,08/5,14) · will
trägt neben dem echten Schnitt (1,94) drei Gewebe-Ereignisse um
2,2–2,3 · Galoppieren fünf um 8,7–9,1 (Hand 1) und sechs um
13,3–13,5 (Hand 0). Der v0.12-Befund erklärt sich damit
vollständig: die Sehne entfernte ALLE Schnitte einer Stelle —
die Parität verlangt aber PAARWEISES Entfernen (3 → 1 · 5 → 1 ·
6 → 0), das genau die topologisch nötige Kreuzung stehen lässt.

**Der Mechanismus (v0.13, EIN Knopf `UNTWIST_WINDOW_UNITS`,
0 = aus, Leiter 0,5 / 0,8):** Auf den assemblierten
Kandidaten-Strichen werden Schnitt-Ereignis-PAARE gesucht, deren
BEIDE Bogenabstände ≤ Knopf und deren Schnittpunkte ≤ Knopf/2
auseinanderliegen (echte getrennte Kreuzungen wie wills
l-Schleifen liegen weit darüber und bleiben unberührt). Je Paar
wird der Wiggle-Bogen zwischen seinen beiden
Ereignis-Parametern an der Sehne P1→P2 GESPIEGELT — der Bogen
wechselt die Seite, beide Schnitte des Paars verschwinden,
Richtung und Parametrisierung bleiben erhalten, die Geometrie
bleibt in der Wiggle-Amplitude (< Fenster). Iterativ bis kein
Paar mehr feuert (Deckel 8 Durchläufe je Wort), Anzahl geloggt.
*Präzisierung VOR der ersten Bench-Zahl (Synthetik-Fund des
Unit-Tests, im Test gepinnt):* „der Wiggle" ist die Seite mit
der GRÖSSEREN maximalen Sehnen-Abweichung — die ursprüngliche
„kürzere-Bogen"-Heuristik ist degeneriert (die sehnen-nahe
Gegenseite hat Bogenlänge ≈ Sehnenlänge und die Spiegelung
wäre ein No-op); eine Seite ohne messbare Abweichung ist nie
der Wiggle.

**Stufen:** v0.13 = "windows" + Entdrillung; v0.14 = "all" +
Entdrillung (die §7.9-Wiedervorlage: Zonen-Rides und natürliche
Brücken bekommen die Knoten-Plateau-Pinnung der Fenster).
Adoptiert wird höchstens EINE Konfiguration (die beste, die alle
Gates besteht).

**Gates v0.13 (gegen den v0.11-Stand):** `cross_missing` ≤ 1
(NICHTS Echtes verlieren — steigt es, feuert das Kill),
`cross_spurious` fällt netto (Erwartung 6 → ≤ 3), Marken
unverändert, Retrace-Zähler ohne Netto-Anstieg, `aiou`-Median-Δ
≥ −0,02 gegen 0,7434, dtw je Wort ±0,003, p90 ≤ 0,113
(v0.11-Stand), reversed 0. **Gates v0.14 (gegen den
v0.13-Stand):** Netto-Kreuzungsdefekte ≤ v0.13, `aiou` steigt
oder hält (die Zonen verlassen die Luft — fällt aiou, ist die
Pinnung dort falsch verdrahtet), dtw-Median hält (±0,003),
Sichtprüfung der vier Owner-Stellen (G · unter/Galoppieren-r ·
Galoppieren-Kasten x≈360 · Wer-Diagonale) wird dem Ergebnis
beigelegt. Paarungen beschreibend gegen die Kette v3
(0,0491/0,0894). Kill v0.14: erzeugt die Zonen-Pinnung neue
Netto-Defekte, bleibt v0.13 (bzw. v0.11) stehen und der Rest
gehört der Karten-Form-Schiene.

**Gemessen `aug19` — v0.13 bei 0,5 ADOPTIERT; 0,8 vom eigenen
Kill verworfen und der Diskriminator sauber benannt; v0.14 per
Gate verworfen, mit dem stärksten SICHTBEWEIS der Runde.**

*v0.13 (dev-19, je 19/19 ok):* **w0,5** (16 Paare entdrillt) →
`cross_missing` 1 (unverändert), `cross_spurious` 6 → **5**
(wills Duplikat heilt), Marken/Retrace unverändert, `aiou`
−0,0036, dtw je Wort ≤ ±0,0011, p90 0,1129 — ALLE Gates
bestehen, **Netto-Defekte 7 → 6**, `UNTWIST_WINDOW_UNITS` =
0,5. **w0,8** (32 Paare) → spurious 6 → 2, aber
`cross_missing` 1 → **6**: das weite Fenster entdrillt auch
GENUIN nahe ECHTE Paare (mits t-Doppel bei 0,07 xh, unters und
Galoppierens enge X) — vom eigenen Kill verworfen. Der Befund
benennt die Grenze exakt: GEOMETRIE allein kann ein
Gewebe-Duplikat nicht von einem echten engen Doppel
unterscheiden — der ehrliche Diskriminator ist das SOLL (die
Karte weiß, wie viele Kreuzungen in eine Nachbarschaft
gehören: mits Doppel steht im Soll, die Gewebe nicht) →
Rettungsweg **soll-budgetierte Entdrillung**, eigene Pre-Reg
(§7.9-Zeile im selben PR).

*v0.14 („all" + Entdrillung 0,5; 13 Paare):* die
Tinten-Gewinne kommen wie erhofft — `aiou` 0,7398 → **0,7521**,
Precision-Chamfer −0,0021, dtw 8:1 Wörter besser (mit-2/mit
−0,009, muß-2/-3, Galoppieren, Wer), und der SICHTBEWEIS ist
der stärkste der Runde: **das G wird erstmals fast wie von der
Hand geritten** (Oval, Kopfschleife, Stamm, Unterschleife am
Ink — alle Luft-Kästen weg), auch der Galoppieren-Rest-Kasten
und die er-Region legen sich an. ABER die Strukturzähler
kippen in GENAU den zwei schlimmsten Karten-Form-Regionen:
Galoppieren verliert das G-Kopf-X ((1,6·1,67) — die gepinnte,
formfremde G-Karte schließt die Schleife nicht, wo die Tafel
kreuzt) und erfindet eines am p (7,97·0,83) — Netto 6 → 8 >
Gate, VERWORFEN wie vorregistriert („der Rest gehört der
Karten-Form-Schiene", hier wörtlich eingetreten). Konstanten:
`MAP_RUN_PIN_KNOTS` bleibt "windows". Rettungsweg:
**Wiedervorlage von v0.14 NACH den
Karten-Form-Autorenschritten** (G-Chart/Laufform,
p-Unterlängen — exakt die beiden Gate-Brecher; §7.7-Protokoll
misst dann neu) — der Sichtbeweis verdoppelt den Ertrag dieser
Autorenschritte: sie reparieren Komposition UND schalten die
saubere Zonen-Fahrt frei.

### Route „Lotse" v0.15 `aug19` — Vorregistrierung: die soll-budgetierte Entdrillung (L1h)

Geschrieben und committet VOR der ersten Zahl (nach dem
Owner-Merge von #387 und „weiter"; Cherry-pick-Recovery des
Squash-Rennens dokumentiert im Branch). Der v0.13-Fund: das
0,8-Fenster heilt alle Duplikate, tötet aber genuin nahe ECHTE
Paare (mits t-Doppel, 0,07 xh) — Geometrie allein trennt die
Klassen nicht. Der vorregistrierte Diskriminator ist das SOLL:
die KARTE kennt ihre eigenen Selbstschnitte, also weiß der
Kandidat, wie viele Kreuzungen in eine Nachbarschaft gehören
(mits Doppel steht in der Karte, die Gewebe nicht).

**EIN Knopf: `UNTWIST_SOLL_BUDGET`** (False = v0.13-Verhalten;
True = Budget-Regel). Die Regel: ein Ereignis-Paar darf nur
entdrillt werden, wenn die Nachbarschaft danach nicht UNTER ihr
Soll fällt — `n_events_near − 2 ≥ n_soll_near`, mit
`n_events_near` = Kandidaten-Schnitt-Ereignisse und
`n_soll_near` = Karten-Selbstschnitte im festen Radius
`UNTWIST_SOLL_RADIUS_UNITS` = 0,55 xh um den Paar-Mittelpunkt
(der Matcher-Radius des Lineals, als deklarierter Snapshot,
kein Suchknopf). Damit ist mits Doppel konstruktiv geschützt
(3 − 2 < 2), während die Gewebe (Soll 0–1, Ereignisse 3–6)
paarweise fallen.

**Leiter: Budget an × Fenster {0,5 · 0,8}** — die Hypothese ist,
dass das weite Fenster ERST mit dem Budget sicher wird und dann
auch mit-2s und Galoppierens Rest-Duplikate erreicht. Gates
gegen den v0.13-Stand (missing 1 · spurious 5 · Netto 6):
`cross_missing` ≤ 1 (steigt es, hat auch das Budget ein echtes
Paar nicht geschützt — Kill, Rettungsweg wäre Matching gegen
die Soll-POSITIONEN statt Zählungen); `cross_spurious` fällt
netto (Erwartung ≤ 3); Marken unverändert; Retrace ohne
Netto-Anstieg; `aiou`-Median-Δ ≥ −0,02 gegen 0,7398; dtw je
Wort ±0,003; p90 ≤ 0,113; reversed 0. Adoptiert wird höchstens
EINE Stufe.
