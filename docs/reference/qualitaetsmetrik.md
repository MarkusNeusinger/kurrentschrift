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
