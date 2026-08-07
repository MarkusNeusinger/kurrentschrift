# Qualitätsmetrik & Glyph-Bench

> **Status (2026-08-03): lebend.** Fortlaufend gepflegte Messlatte und
> Baseline-Journal — jeder Bench-Lauf und jedes bewusste Re-Baseline
> schreibt hier einen datierten Abschnitt fort; aktuelle Headlines:
> Wörter 0,116886 · Paare 0,164506 (Lauf `aug02`, PR #268).
> Die Verworfen-Listen (§4, §5, §6) bleiben geschlossen.

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

### Kalibrierung

Über die 245 gespeicherten Vorkommen — die **alle** aus dem Ketten-Pfad
stammen (`fit_path == "chain"`, 245 von 245), Kalibrierungs- und
Anwendungspopulation sind also dieselbe: Median 2,68 · p75 3,86 ·
p90 7,28 · p99 23,29 · max 32,9.

Bei **8,0** werden 23 Vorkommen (9,4 %) verworfen und **kein einziger**
Buchstabe fällt unter `LAUFFORM_MIN_OCCURRENCES` = 3 (auch nicht unter
die `--min-n`-Vorgabe 4 der Ernte selbst). Bei 6,0 fiele „g" darunter —
deshalb liegt die Schwelle hier und nicht tiefer.

Wirkung auf die akzeptierte Menge, gemessen als Abstand der gefitteten
Mittellinie zur echten Tinte: schlechtester Wert **0,613 → 0,258** x-Höhen,
p90 **0,194 → 0,149**. Das Gate leistet damit das meiste von dem, was ein
Fit-Regularisierer leisten sollte — ohne den Fit anzufassen.

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
