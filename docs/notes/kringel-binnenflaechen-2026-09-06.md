# Die Kringel schließen — wo auf dem Weg von der Platte zur Zeile die Binnenfläche verloren geht (2026-09-06)

> **Status (2026-09-06): Befund-Journal.** Diagnose zur Frage des Autors vom
> 2026-09-06 („In den Beispielwörtern mit der dicken Feder sind die freien
> Stellen da … Ziehen die Linien vielleicht eher Richtung Mitte?"), gestellt
> zum Zweitbefund des verworfenen Arms
> [„Ink-Clearance an die Feder `sep05`"](../reference/messjournal.md#ink-clearance-an-die-feder-sep05--gemessen-der-arm-fällt-und-er-sagt-genau-wo-das-problem-nicht-sitzt).
> **Reine Messung: kein Arm, keine Vorregistrierung eines Kandidaten, keine
> Adoption, keine Zeile geschrieben, kein `core/`-Byte bewegt.** Wird nicht
> fortgeschrieben, nur durch eine neue Messrunde abgelöst. Was daraus an
> Kandidaten folgt, steht unten als Rettungswege und ist in
> [`tintenfolger.md` §7.9](../proposals/tintenfolger.md) nachgetragen.

## Kurzfassung

Der Autor hat recht, und die Messung sagt zusätzlich, wo es passiert.

Die Platte hält ihre Binnenflächen offen: an den acht engen Glyphen misst der
größte einbeschriebene Kreis im Loch **0,096–0,188 xh** (Median 0,131), bei
einer Feder-Halbbreite von 0,0968 xh. Unsere komponierten Buchstaben, mit
derselben Feder gestrichen, schließen dieselben Löcher — **−0,004 bis
−0,019 xh**, also Übermaß statt Öffnung. Der Unterschied ist **kein
Federproblem, sondern ein Mittellinien-Problem**: die Schleife unserer
Mittellinie ist um **0,10–0,20 xh im Durchmesser enger** (Median **0,135**)
als die, die die Feder der Platte gezogen haben muss. Pro Seite sind das rund
0,07 xh — zwei Drittel einer Strichbreite. Die Linien ziehen also tatsächlich
Richtung Mitte.

Der Verlust entsteht **nicht an einer Stelle, sondern zweimal**:

1. **Schon in der Tinten-Evidenz.** Das eingefrorene Skelett — die
   Mittelachse, auf der der Lotse reitet und an der sich die Kette misst — ist
   an einer engen Binnenfläche selbst um **0,035–0,104 xh** enger als die
   Bahn, die die Feder gezogen haben muss. Wo zwei Federzüge um ein kleines
   Loch herum VERSCHMELZEN, ist die Mittelachse des verschmolzenen Klumpens
   nicht mehr der Federweg; sie rückt zwischen Loch und Außenkante. Der Ort,
   an dem die Öffnung zuerst verloren geht, liegt damit vor jedem Fit.
2. **Beim Übergang von Vorkommen zu ZEILE.** Die Kette streut um die
   Mittelachse, ohne sie systematisch nach innen zu unterbieten (signierter
   Median über 183 Schleifen **−0,0116 xh**, Betrag |Kette − Skelett| im
   Median **0,0329**, p75 0,0642) — sie fügt dem geerbten Defizit im Median
   nichts hinzu, das die Größenordnung des Problems hätte. Die gespeicherte
   Zeile liegt dagegen **durchweg** unter dem Median ihrer eigenen Vorkommen:
   0,004–0,082 xh bei den sechs Buchstaben mit Laufform-Zeile, bis 0,126 xh
   bei denen, die aus der Chart-Form komponieren.

Die Komposition selbst verliert danach **nichts** (`komponiert − Zeile`
höchstens 0,0008 xh über alle neun Glyphen, in beide Richtungen): die
Buchstabenform, die in der Wortprobe landet, ist die gespeicherte Zeile.

Und die tröstliche Zahl dazu: **bei der heute ausgelieferten Feder
(0,0724326) schließt keine einzige Binnenfläche** — von den 63 Wortproben
verliert **null** ein Loch, das die Platte offen zeigt. Bei 0,097 sind es
**26 der 63**, darunter der Pflicht-Anker `das` (über das `a`).

## Protokoll

Vor der ersten Zahl festgelegt; die beiden nachträglichen Korrekturen sind
unten benannt statt versteckt.

**Eine Größe trägt die ganze Kette: `D0`, die Öffnungsweite der
MITTELLINIEN-Schleife** — der Durchmesser des größten Kreises, der in das
Gebiet passt, das eine geschlossene Mittellinien-Schleife umschließt. Eine
Gleichzug-Feder der Halbbreite `h` malt die Kapsel-Union, also die
Minkowski-Summe mit der Scheibe vom Radius `h`; das Loch der Union ist die
Erosion des Mittellinien-Lochs um `h`, und die sichtbare Binnenfläche ist
deshalb **exakt `D0 − 2h`**. Damit sind Platte, Skelett, Kette und Zeile in
EINER Einheit vergleichbar, unabhängig davon, welche Feder man jeweils
unterstellt. Gemessen wird auf einem Raster von 1200–1600 px je x-Höhe
(Auflösungsboden ≈ 0,0013 xh), Hintergrund 4-verbunden, Kurve 8-verbunden,
Löcher am Bildrand verworfen; die Öffnungsweite ist `2 · max(EDT)` im Loch.
Die Identität wurde vor der Auswertung gegen den direkt gerasterten
Kapsel-Union geprüft: Abweichung **≤ 0,0013 xh** über sieben Chart-Zeilen
(`check_identity.py`), und die Silhouetten-Ringe aus `multi_stroke_silhouettes`
geben dieselben Werte ±0,002.

**Vier Ablesungen je Binnenfläche**, alle auf derselben eingefrorenen Wurzel:

* **Platte** — die Binnenfläche der binarisierten Plattentinte selbst
  (`ref_mask.png`), in Pixeln gemessen und über `xh = baseline_y − midband_y`
  in x-Höhen gebracht. Das ist die Wahrheit, gegen die alles andere antritt.
* **Skelett** — `D0` der Schleife des eingefrorenen Skeletts (`ref_skel.npz`),
  also der Mittelachse, die der Lotse reitet: die 4-verbundene
  `~skel`-Komponente, die das Loch enthält, gegen das Skelett ausgemessen.
* **Kette** — `D0` der Schleife des gespeicherten Kette-v5-Wortfits
  (`word_instances.json`, `fit_path: "chain"`), in dessen eigenem
  `registration_px`-Rahmen auf den Crop gelegt.
* **Komponiert / Zeile** — `D0` der Mittellinie des komponierten Buchstabens,
  einmal so wie die Produktion komponiert (`compose_word` mit
  `laufform_by_key`, Registrierung aus `score_word` — dasselbe Lineal wie im
  Wort-Bench) und einmal chart-only; dazu `D0` der blanken gespeicherten
  Zeilen über `render_payload_for_template`.

**Zuordnung.** Je Wort werden alle komponierten Schleifen und alle
Platten-Binnenflächen gesammelt und EINMAL global greedy nach Abstand
gepaart (Grenze 0,45 xh); die Kette-Schleife hängt sich an dieselbe
Platten-Binnenfläche. Löcher unter 3 px Fläche gelten als Papierkorn,
Mittellinien-Schleifen unter 0,02 xh als Raster-Splitter.

**Der 0,02-Boden gilt NUR für diese Zuordnung, nicht für die
Zeilen-Inventur.** Er hält Zwei-Pixel-Löcher aus der Paarung heraus, die
beim Rastern zweier fast berührender Polylinien entstehen; eine Schleife
darunter kann keiner Platten-Binnenfläche sinnvoll zugeordnet werden. Die
Inventur der gespeicherten Zeilen (`rows.py`) meldet dagegen JEDE Schleife
mit ihrer Weite — und genau daher kommt der `p`-Befund unten: die
Laufform-Zeile trägt am Schaft noch eine Schleife von **0,0095 xh**, und
dass sie unter dem Zuordnungs-Boden liegt, IST die Aussage über sie. Wer den
Rettungsweg R1 baut, darf diesen Boden folglich nicht mitnehmen: ein
Öffnungsweiten-Gate muss eine kollabierte Schleife sehen, nicht wegfiltern.

**Die Feder-Rekonstruktion `D0(Feder) = Platte + 2 · w_pen`** (mit
`w_pen` = 0,0968 xh, dem Median der Skelett-Halbbreite über alle 63 Wörter)
ist die einzige MODELLIERTE Größe dieses Blatts: sie unterstellt das
Kapsel-Modell auch dort, wo die Tinte real verschmolzen ist. Sie steht
mit, weil sie die Frage „wie weit muss die Schleife sein" direkt beantwortet
— sie ist aber ausdrücklich keine Messung, und keine Schlussfolgerung unten
hängt allein an ihr. Der assumptionsfreie Vergleich ist immer
**Platte@0,097 gegen komponiert@0,097**: beides ist dieselbe physikalische
Größe, dieselbe Feder, ein direktes Maß gegen das andere.

**Wurzel und Umgebung.** Frische Fixture-Wurzeln, gebaut am 2026-09-06 über
`fetch_fixtures --set all` gegen `api.kurrentschrift.ink`: `suetterlin-1922`
`exported_at` 2026-09-06T06:25:39+00:00 `root_digest` **`f30b700a2f3d…`**,
`suetterlin-1922-pairs` gleicher Lauf **`135b15ce909f…`**. Sie sind inhaltlich
die `sep05`-Wurzeln des LF12-Writes — der Digest hasht `manifest.json` und
damit den Zeitstempel, kann also nach einem Re-Export nie derselbe sein.
**Der Beleg ist die Headline, nicht der Digest:**
`wordbench.run --set all --expect-root f30b700a2f3d,135b15ce909f` mit
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` gibt **Wörter 0,108444 · Paare
0,148236** — ziffernweise die `sep05`-Zahlen. Der gepoolte Nib der Wurzel ist
0,0724326 (`nib_precision: "exact"`), 21 Laufform-Zeilen, `S` fehlt: alles
wie im LF12-Write-Eintrag deklariert.

**Zwei Korrekturen nach dem ersten Durchlauf**, beide am Schätzer, keine am
Gegenstand: (i) die lokale Halbbreite wurde zuerst als Median der
EDT-Werte über die GANZE Skelett-Schleife gelesen — das ist an einer
Binnenfläche die falsche Statistik, weil die Schleife auch dort entlangläuft,
wo die nächste Hintergrundkante außen liegt; sie wird jetzt als
`(D0_skel − Platte)/2` geführt und als das benannt, was sie ist. (ii) Die
Zuordnung Schleife↔Binnenfläche lief zuerst slotweise in Leserichtung, wodurch
ein früher Slot eine Binnenfläche belegen konnte, die einem späteren gehört
(sichtbar am `k` in `linken`); sie ist jetzt global greedy.

## Die Kette der Zahlen

Mediane über die Vorkommen, alles in x-Höhen. `n` = Vorkommen mit zugeordneter
Platten-Binnenfläche; bei mehreren Schleifen je Buchstabe zählt die ENGSTE
komponierte (das ist die, die zuläuft).

| Glyphe | n | Platte | `D0`(Feder) | `D0` Skelett | `D0` Kette | `D0` komponiert | Zeile Chart | Zeile Laufform |
|---|---|---|---|---|---|---|---|---|
| `a` | 12 | 0,0959 | 0,2895 | 0,1988 | 0,2236 | 0,1856 | 0,1858 | 0,1858 |
| `o` | 5 | 0,1290 | 0,3226 | 0,2499 | 0,1826 | 0,1765 | 0,1846 | 0,1767 |
| `sz` | 4 | 0,1290 | 0,3226 | 0,2183 | 0,2705 | 0,1877 | 0,1907 | 0,1881 |
| `g` | 3 | 0,1333 | 0,3269 | 0,2667 | 0,2377 | 0,1747 | 0,1849 | 0,1744 |
| `r` | 20 | 0,1333 | 0,3269 | 0,2620 | 0,2332 | 0,2087 | 0,1805 | 0,2091 |
| `p` | 4 | 0,4800 | 0,6736 | 0,6384 | 0,5788 | 0,5746 | 0,2556 | 0,5752 |
| `v` | 2 | 0,0968 | 0,2903 | 0,2131 | 0,2111 | 0,1889 | 0,1896 | — |
| `k` | 1 | 0,1875 | 0,3810 | 0,3125 | 0,3108 | 0,1841 | 0,1845 | — |
| `G` | 3 | 0,1333 | 0,3269 | 0,2667 | 0,2718 | 0,1902 | 0,1901 | — |

Dieselben Zeilen als das, was man SIEHT — die Binnenfläche an der
Platten-Feder 0,097 (`D0 − 0,194`; negativ = zugelaufen):

| Glyphe | Platte (gemessen) | Skelett gestrichen | Kette gestrichen | komponiert |
|---|---|---|---|---|
| `a` | **+0,0959** | +0,0048 | +0,0296 | **−0,0084** |
| `o` | **+0,1290** | +0,0559 | −0,0114 | **−0,0175** |
| `sz` | **+0,1290** | +0,0243 | +0,0765 | **−0,0063** |
| `g` | **+0,1333** | +0,0727 | +0,0437 | **−0,0193** |
| `r` | **+0,1333** | +0,0680 | +0,0392 | **+0,0147** |
| `p` | **+0,4800** | +0,4444 | +0,3848 | +0,3806 |
| `v` | **+0,0968** | +0,0191 | +0,0171 | **−0,0051** |
| `k` | **+0,1875** | +0,1185 | +0,1168 | **−0,0099** |
| `G` | **+0,1333** | +0,0727 | +0,0778 | **−0,0038** |

Zwei Sätze, die diese Tabelle trägt und die für die Rettungswege zählen:

* **Die Mittelachse der Platte, mit 0,097 gestrichen, hält JEDE der neun
  Binnenflächen offen** — die engste Lesung ist `a` mit +0,0048 xh, also ein
  Haar, aber offen. „Der Tinte richtig folgen" reicht als Rezept damit
  gerade eben, und es reicht nur, weil die Mittelachse zufällig noch auf der
  richtigen Seite liegt.
* **Die Kette hält sieben der acht engen offen**; nur das `o` fällt (−0,0114).
  Die Schleifengeometrie ist also in der Spur schon da; sie geht erst
  verloren, wenn aus Vorkommen eine Zeile wird.

Und die Zerlegung, Schritt für Schritt (negativ = enger geworden):

| Glyphe | `D0`(Feder) | → Skelett | → Kette | → komponiert | komponiert → Zeile | gesamt |
|---|---|---|---|---|---|---|
| `a` | 0,2895 | −0,0907 | −0,0658 | −0,0380 | +0,0002 | **−0,1039** |
| `o` | 0,3226 | −0,0727 | −0,1400 | −0,0061 | +0,0002 | **−0,1461** |
| `sz` | 0,3226 | −0,1043 | −0,0521 | −0,0828 | +0,0004 | **−0,1349** |
| `g` | 0,3269 | −0,0602 | −0,0892 | −0,0630 | −0,0003 | **−0,1522** |
| `r` | 0,3269 | −0,0648 | −0,0937 | −0,0245 | +0,0004 | **−0,1182** |
| `p` | 0,6736 | −0,0352 | −0,0948 | −0,0042 | +0,0006 | **−0,0990** |
| `v` | 0,2903 | −0,0772 | −0,0792 | −0,0222 | +0,0008 | **−0,1015** |
| `k` | 0,3810 | −0,0685 | −0,0702 | −0,1267 | +0,0004 | **−0,1969** |
| `G` | 0,3269 | −0,0602 | −0,0551 | −0,0816 | −0,0001 | **−0,1367** |

Die Spalten „→ Skelett" und „→ Kette" sind beide gegen die Feder-Rekonstruktion
gerechnet und deshalb nicht additiv; ihr Verhältnis ist die Aussage. Der Rest
(„→ komponiert" gegen die Kette, „komponiert → Zeile") ist reine Messung.

## Die drei Hypothesen

### H1 — „der Kette-Fit sitzt auf Tinte, aber nicht auf der Mittelachse, vom Chart-Prior nach innen gezogen": **so nicht bestätigt**

Über alle 183 zugeordneten Schleifen liegt die Kette im **signierten** Median
**0,0116 xh** unter dem Skelett, in 61 % der Fälle darunter — an `a` (+0,0083)
und `sz` (+0,0358) sogar systematisch DARÜBER. Ein systematischer Prior-Zug
nach innen in der Größenordnung des Problems ist das nicht.

**Der signierte Median ist dabei kein Abstandsmaß, und das gehört daneben:**
der BETRAG |Kette − Skelett| liegt im Median bei **0,0329 xh** (p25 0,0132 ·
p75 0,0642 · p90 0,0976). Die Kette liegt also nicht „auf" der Mittelachse —
sie streut kräftig um sie, nach beiden Seiten, und nur die Summe der
Vorzeichen ist klein. Für die Frage dieses Blatts ist genau das die Aussage:
was die Kette dem geerbten Defizit HINZUFÜGT, ist im Mittel gering, aber je
Vorkommen ist es nicht klein.

Wie viel des Kette-Defizits geerbt ist, je Schleife statt aus Aggregaten
gerechnet (`(D0(Feder) − D0(Skelett)) / (D0(Feder) − D0(Kette))`, nur die 154
Schleifen mit einem Defizit über 0,02 xh): **Median 0,75**, p25 0,50, p75
1,03. **Rund drei Viertel des Kette-Defizits stammen aus der Mittelachse, nicht
aus dem Fit** — mit einer Spanne, die von „die Hälfte" bis „mehr als alles"
(der Fit macht die Schleife dort WEITER als das Skelett) reicht.

Ein kleiner echter Zug nach innen bleibt und ist benennbar: `r` −0,0332, `g`
−0,0307, `p` −0,0278, `G` −0,0256 gegen das Skelett (signiert) — genau die
Glyphen mit großen Schleifen und Kreuzungen. Das ist ein Kandidat, aber kein
Träger der Erklärung.

**Was H1 ersetzt (H0, gemessen):** die Mittelachse ist an einer engen
Binnenfläche selbst nicht der Federweg. `D0`(Skelett) liegt 0,035–0,104 xh
unter der Feder-Rekonstruktion, und die Halbbreite, die der Klumpen um die
Binnenfläche trägt (`(D0_skel − Platte)/2`), ist mit **0,0667 xh** im Median
deutlich schmaler als die Feder selbst (0,0968) — die zwei Federzüge sind dort
verschmolzen, und `skeletonize` gibt die Achse des Klumpens, nicht die zwei
Bahnen. Für den Lotsen ist das eine Aussage über sein Zielobjekt, für die
Kette über ihre Evidenz.

### H2 — „der Per-Anker-Median der Laufform plus Glättung zieht Schleifen zusammen": **in der Richtung bestätigt, im Betrag NICHT isoliert**

Zeile gegen den Median ihrer eigenen Vorkommen (Kette-Schleifen derselben
Buchstaben), jeweils die engste Schleife:

| Glyphe | n | Vorkommen (Median) | Spanne | Zeile | Zeile − Vorkommen | gerenderte Zeile |
|---|---|---|---|---|---|---|
| `a` | 11 | 0,2236 | 0,1767–0,2865 | 0,1858 | **−0,0378** | Laufform |
| `o` | 5 | 0,1826 | 0,1638–0,2921 | 0,1767 | −0,0059 | Laufform |
| `sz` | 4 | 0,2705 | 0,1957–0,3021 | 0,1881 | **−0,0824** | Laufform |
| `g` | 3 | 0,2377 | 0,2007–0,2442 | 0,1744 | **−0,0633** | Laufform |
| `r` | 20 | 0,2332 | 0,1270–0,3500 | 0,2091 | −0,0241 | Laufform |
| `p` | 4 | 0,5788 | 0,5709–0,6239 | 0,5752 | −0,0036 | Laufform |
| `v` | 2 | 0,2111 | 0,2088–0,2134 | 0,1896 | −0,0215 | Chart |
| `k` | 1 | 0,3108 | — | 0,1845 | **−0,1264** | Chart |
| `G` | 3 | 0,2718 | 0,2566–0,3464 | 0,1901 | **−0,0817** | Chart |

Das Vorzeichen ist **neunmal von neun** negativ. **Aber nur sechs davon sind
H2:** `v`, `k` und `G` haben gar keine Laufform-Zeile, dort ist der Vergleich
Chart gegen Vorkommen und gehört zu H3. Die reine H2-Menge ist `a` `o` `sz`
`g` `r` `p` mit **0,004–0,082 xh** (Median −0,031) — nicht die 0,126 des `k`,
das hier nur der Vollständigkeit halber in der Tabelle steht.

**Und der Betrag ist mit diesen Zahlen nicht dem Schätzer zurechenbar.** Was
gemessen wurde, ist „die gespeicherte Zeile ist enger als die Kette-WORTFITS
derselben Vorkommen". Was H2 behauptet, ist „der Schätzer zieht sie zusammen".
Dazwischen liegen zwei Unterschiede, die dieses Blatt nicht ausräumt: die
Wortfits sind nicht der Vorkommens-Stapel, aus dem die Zeilen abgeleitet
wurden (unten unter „Grenzen" ausgeführt), und die Zeilen der Wurzel entstehen
seit LF11 nicht als Per-Anker-Median mit anschließender Glättung, sondern als
**Median über B-Spline-Kontrollpunkte** (`core/aggregate.py::spline_basis_median`)
— ein anderer Schätzer, auch wenn er dieselbe Kontraktionsrichtung hat.

Der Mechanismus, den H2 unterstellt, ist trotzdem der naheliegende und
verlangt keine neue Vermutung: **ein elementweiser Median über Kurven, die
nicht deckungsgleich sind, kontrahiert.** Punkt `i` der Zeile ist der Median
der Punkte `i` aller Vorkommen; sind die Schleifen gegeneinander verdreht oder
verschoben, liegt dieser Punkt weiter innen als jeder einzelne — und die
Projektion auf eine Spline-Basis mildert das nicht, weil eine enge Schleife
die höchste Krümmung der Zeile trägt. **Isolieren würde es ein Versuch, den
dieses Blatt nicht macht und der als R2 vorregistriert gehört:** `D0` messen
am exakten Eingangs-Stapel einer Zeile, an seinem Per-Anker-Median und an
seinem Spline-Basis-Median — drei Zahlen auf denselben Daten, deren Differenz
dann wirklich der Schätzer ist.

**Der schärfste Einzelfall ist ein anderer und gehört genannt:** die
Laufform-Zeile des `p` trägt **überhaupt keinen Kringel mehr**. Ihre
Mittellinien-Schleifen sind 0,5780 und 0,5752 (Bauch und Unterschleife); die
kleine Schleife am Schaft ist auf 0,0095 xh kollabiert und damit bei JEDER
Feder zu — auch bei der heute ausgelieferten. Die Chart-Zeile des `p` hat sie
mit 0,2556 (offen bis 0,0616 xh bei 0,097). In den drei Wörtern mit gebundenem
`p` (`Galoppieren`, `Sporn`, `Sprünge`) rendert die Produktion also schon
heute ein `p` ohne diesen Kringel. Das ist kein Federproblem, sondern ein
Topologie-Verlust in der Ernte.

### H3 — „die Chart-Form selbst ist eng": **bestätigt, und es ist der größte Einzelposten**

| Glyphe | Chart-Zeile | Feder-Rekonstruktion | Abstand | Chart allein bei 0,097 |
|---|---|---|---|---|
| `a` | 0,1858 | 0,2895 | −0,1036 | −0,0082 |
| `o` | 0,1846 | 0,3226 | −0,1379 | −0,0094 |
| `sz` | 0,1907 | 0,3226 | −0,1319 | −0,0033 |
| `g` | 0,1849 | 0,3269 | −0,1420 | −0,0091 |
| `r` | 0,1805 | 0,3269 | −0,1464 | −0,0135 |
| `p` | 0,2556 | 0,6736 | −0,4180 | **+0,0616** |
| `v` | 0,1896 | 0,2903 | −0,1007 | −0,0044 |
| `k` | 0,1845 | 0,3810 | −0,1966 | −0,0095 |
| `G` | 0,1901 | 0,3269 | −0,1368 | −0,0039 |

Am auffälligsten ist nicht die Größe des Abstands, sondern die **Enge der
Streuung**: acht der neun Chart-Schleifen liegen zwischen 0,1805 und 0,1907 —
eine Spanne von 0,010 xh über völlig verschiedene Buchstaben. Bei der
Chart-Feder (0,0725) ergibt das durchweg 0,036–0,046 xh Binnenfläche. Die
Tafelformen tragen also genau so viel Loch, wie die Tafelfeder braucht, und
keinen Millimeter mehr — die Binnenfläche der Chart-Form ist an ihre eigene
Feder kalibriert, nicht an die der Wortplatten. Genau deshalb bricht die
Klasse geschlossen zusammen, sobald die Feder wächst.

Der einzige Ausreißer ist `r`: die Laufform-Zeile trägt dort 0,2091 gegen
0,1805 der Chart-Zeile und überlebt die schwere Feder als einzige (+0,0147).
In 18 der 20 `r`-Vorkommen rendert die Produktion diese Zeile; die zwei
Ausnahmen (`er`, `er-3`, zu kurze Läufe für das Lauf-Gate) fallen mit −0,0137
auf die Chart-Form zurück und laufen zu. Das ist der Befund des
`sep05`-Eintrags („beim `r` überlebt die Zeile, die Chart-Form nicht") auf
diesem Messpfad reproduziert.

## Die Feder

Die Frage war, ob 0,097 überhaupt die Breite AN den Schleifen ist — ein
Gleichzug sollte gleichmäßig sein.

* Über alle 63 Wortproben, alle Skelettpixel (n = 39 155): Median
  **0,0968 xh**, p10 0,0699, p90 0,1202. Die 0,097 der Wortmessung sind damit
  bestätigt; die Streuung von ±25 % ist die eines echten Gleichzugs mit
  Ansätzen, Kreuzungen und Verschmelzungen.
* Der Klumpen um eine Binnenfläche trägt dagegen nur **0,0667 xh** Halbbreite
  (p10 0,0514, p90 0,0851). Das ist **keine dünnere Feder**, sondern die
  Signatur der Verschmelzung: zwischen Loch und Außenkante steht dort weniger
  Tinte, als ein einzelner Federzug dick ist, weil das Loch selbst schon der
  nächste Hintergrund ist.

Für die Auslieferung heißt das: die Federzahl ist richtig gemessen, und der
gemessene Wert allein ist nicht die Ursache der geschlossenen Kringel. Die
Ursache ist der Weg der Mittellinie.

## Blätter

Ein Blatt je Glyphe, alle Ausschnitte im selben Maßstab, jede
Mittellinien-Tafel mit dem 0,097-Strich geisterhaft hinterlegt; Spalten:
Plattentinte (roter Kreis = einbeschriebener Kreis der Binnenfläche) ·
Skelett · Kette-v5-Fit · komponiert · alles übereinander. Sie liegen im
Sitzungs-Scratchpad, nicht im Repo:

```
/tmp/claude-1000/-home-tirao-kurrentschrift/c3b43b9a-1193-40a4-88f4-19828994db5b/scratchpad/kringel/sheets/
  a.png (daß) · o.png (von) · sz.png (muß-3) · g.png (regieren) · r.png (einer)
  p.png (Galoppieren) · v.png (von) · k.png (linken) · G.png (Gewehr)
  _uebersicht-zeilen.png   — alle neun gespeicherten Zeilen, Chart über Laufform
```

Das Blatt `G.png` ist das lehrreichste: die Platte hält drei Binnenflächen
offen, der Kette-Fit hält bei 0,097 alle drei, und die komponierte Chart-Form
verliert die kleine oben ganz und lässt von der Unterschleife einen Schlitz
übrig. `a.png` zeigt den Fall in Reinform — Plattentinte mit sauberem Loch,
komponierte Mittellinie mit demselben Strich vollständig gefüllt.

## Reichweite: 26 der 63 Wortproben

Bei 0,097 verlieren **26 der 63 Wortproben** mindestens eine Binnenfläche,
die die Platte offen zeigt; betroffen sind `a` (12×), `o` (5×), `sz` (4×),
`g` (3×), `G` (3×), `r` (2×, die beiden Chart-Rückfälle), `v` (2×), `k` (1×).
Bei der heute ausgelieferten Feder 0,0724326 sind es **null**.

Der `sep05`-Eintrag nennt 31 Wörter. Der Unterschied ist Messpfad, nicht
Widerspruch: dort wurde je gespeicherter ZEILE gezählt und auf die Wörter
hochgerechnet, hier je tatsächlich zugeordneter Platten-Binnenfläche im
komponierten Wort — Vorkommen ohne Gegenstück auf der Platte zählen hier
nicht mit. In dieselbe Richtung geht, dass die absoluten Öffnungsweiten
dieses Blatts für die Chart-Zeilen um **0,007–0,024 xh** unter denen des
`sep05`-Eintrags liegen (dort `a` 0,0485 gegen hier 0,0410 bei der jeweiligen
Feder). Welcher der beiden Raster näher an der Wahrheit liegt, ist hier NICHT
entschieden; für dieses Blatt zählt, dass alle vier Ablesungen derselben
Kette mit demselben Werkzeug entstanden sind und die Erosions-Identität
gegengeprüft ist. **Die Verdikte des `sep05`-Eintrags sind unverändert:** alle
neun Glyphen schließen bei 0,097, `r` überlebt nur auf der Laufform-Zeile,
`p` steht auf der Zeile schlechter als auf der Chart-Form.

## Rettungswege — vier benannte Kandidaten, hier NICHT gebaut

Jeder ist ein eigener Arm mit eigener Vorregistrierung vor der ersten Zahl;
die Skizze ist je eine Zeile und ausdrücklich kein Gate. Die Reihenfolge ist
die der gemessenen Hebel.

**(R1) Öffnungsweiten-Gate im Laufform-Schätzer.** *Mechanismus:* die
Ableitung einer Zeile prüft, ob die Öffnungsweite ihrer Schleifen unter den
Median der Vorkommen fällt, und weist eine Zeile zurück (oder blendet lokal
auf die Chart-Topologie zurück), die eine Binnenfläche verliert, die ihre
Vorkommen tragen. *Vorregistrierungs-Skizze:* auf der heutigen Wurzel je
Laufform-Zeile `D0` der Zeile gegen den Median der `D0` ihrer Vorkommen
messen; Gate „keine Zeile unter dem Vorkommens-Median minus dem
Auflösungsboden", Nebenbedingung Wörter/Paare nicht schlechter, Golden
byte-gleich. Trägt sofort das `p` (kollabierter Kringel) und die
0,04–0,08-xh-Fälle `a`/`sz`/`g`. Das ist zugleich der bereits im
`sep05`-Eintrag benannte Weg (2), nur mit einer Messgröße statt einer Absicht.

**(R2) Schleifen-treuer Median statt elementweisem.** *Mechanismus:* die
Vorkommen werden vor dem Median je SCHLEIFE ausgerichtet (Prokrustes auf das
umschlossene Gebiet oder Phasen-Ausrichtung entlang der Bogenlänge), sodass
der Median die Form mittelt und nicht Form gegen Lage verrechnet. *Skizze:*
**erst die Zurechnung, die dieses Blatt schuldig bleibt** — je Zeile `D0` am
exakten Eingangs-Stapel ihrer Vorkommen, an dessen Per-Anker-Median und an
dessen Spline-Basis-Median messen, damit die Kontraktion dem Schätzer gehört
statt einer Vergleichsmenge; DANN der Kandidatenschätzer in `tools/laufform`,
gemessen als „`D0` der Zeile − Median des Stapels" über alle 21 Zeilen, Gate
„Median ≥ −Auflösungsboden und keine Zeile schlechter als heute",
Headline-Gates unverändert. Greift die Ursache statt des Symptoms und ist die
Konversion, falls R1 zu viele Zeilen zurückweist.

**(R3) Schleifen-Geometrie aus der Evidenz statt aus der Zeile.** *Mechanismus:*
für Buchstaben mit enger Binnenfläche wird die Schleife nicht aus dem
Anker-Median genommen, sondern aus der Evidenz derselben Vorkommen
rekonstruiert — der Lotse hat den Zugriff auf die Mittelachse bereits, die
Kette hält an sieben von acht engen Stellen die Öffnung. *Skizze:* je
Glyphenschlüssel die Schleifen-Teilstücke der Vorkommen sammeln, gemeinsam
registrieren, die Zeile lokal darauf setzen; Gate „Binnenfläche bei 0,097
> 0 für alle neun" plus Wörter/Paare nicht schlechter. Der teuerste, aber
einzige Weg, der die 0,10–0,20 xh vollständig zurückholen KANN.

**(R4) Mittelachsen-Korrektur an verschmolzenen Stellen (Sensor zuerst).**
*Mechanismus:* dort, wo zwei Federzüge um eine Binnenfläche verschmelzen, ist
die Mittelachse nicht der Federweg; ein Korrekturterm setzt die Zielbahn an
solchen Stellen auf `Lochkante + w_pen` statt auf das Skelett. *Skizze:* erst
als reine Report-Spalte bauen — je Binnenfläche `(D0_skel − Platte)/2` gegen
`w_pen`, das Verhältnis ist der Verschmelzungs-Anzeiger — und an den 202
gemessenen Binnenflächen abnehmen (Nullproben: Stellen ohne Verschmelzung
müssen 1,0 zeigen); erst danach ein Arm für Kette oder Lotse. **Ausdrücklich
nicht:** einen Öffnungs-Bonus in den Fit-Loss schreiben, ohne den Sensor
vorher einzufrieren — das wäre der Knopf statt des Mechanismus.

**Kein Weg, ausdrücklich:** die Feder dünner machen, bis die Löcher wieder
aufgehen. Die 0,097 sind an den Wortplatten gemessen (hier auf 0,0968
bestätigt); sie kleinzurechnen, weil unsere Formen sie nicht vertragen, wäre
genau das Weichspülen, das die Rettungswege-Regel verbietet.

Der bereits stehende Autorenweg des `sep05`-Eintrags — die acht Formen
nachzeichnen bzw. den Eigenhand-Bestand als zweite Quelle nehmen — bleibt
unberührt und ist von R1–R4 unabhängig. Dieses Blatt beziffert nur, wie weit
er gehen müsste: **+0,10 bis +0,20 xh Mittellinien-Öffnungsweite je Schleife**
(Median +0,135), also rund 0,07 xh je Seite.

## Was ich selbst entschieden habe

* **Die Wurzel neu zu bauen statt die vorhandene zu nehmen.** Der lokale
  Bestand war die `sep03`/`sep04`-Wurzel (`6cbab9d5c092`), vor dem
  LF12-Write; der Auftrag nennt `sep05`. Der Re-Export lief in die
  ISOLIERTE Worktree-Kopie (`--out` Vorgabe des Moduls), der eingefrorene
  Bestand der Haupt-Arbeitskopie wurde nicht angefasst. Dass ein Re-Export
  den Digest zwangsläufig ändert (der Zeitstempel wird mitgehasht), ist oben
  als Grenze benannt und über die ziffernweise Headline aufgefangen.
* **`D0` als gemeinsame Einheit** statt neun Tabellen mit je eigener Feder —
  die Erosions-Identität macht sie exakt und wurde vor der Auswertung geprüft.
* **Die Feder-Rekonstruktion mitzuführen, aber keine Aussage allein auf sie zu
  stützen.** Sie beantwortet die Frage des Autors direkt („wie weit müsste die
  Schleife sein"), unterstellt aber ein Modell; jede Schlussfolgerung oben
  steht auch ohne sie, über den Direktvergleich Platte@0,097 gegen
  komponiert@0,097.
* **Die zwei Schätzer-Korrekturen zu benennen statt sie stillschweigend
  einzubauen** — sie sind nach den ersten Zahlen entstanden und deshalb
  offengelegt.
* **`f` nicht mitzumessen.** Der `sep05`-Eintrag führt es als „eingeschnürt",
  nicht als geschlossene Binnenfläche; der Auftrag nennt neun Glyphen. Eine
  Einschnürung ist eine andere Messgröße (Ringzahl, nicht Öffnungsweite) und
  hätte eine eigene Definition gebraucht.

## Grenzen dieser Messung

* **Auflösung der Platte.** Die Wortproben stehen bei 30–35 px je x-Höhe. Eine
  Binnenfläche von 0,096 xh sind rund 3 px; die Ablesung hat dort einen Boden
  von etwa ±0,5 px ≈ ±0,015 xh. Die Richtung des Befunds (0,10–0,20 xh
  Defizit) liegt eine Größenordnung darüber, die einzelne Zeile der Tabelle
  nicht.
* **`k` steht auf n = 1**, `v` auf n = 2, `g`/`G`/`p` auf n = 3–4. Nur `r`
  (20), `a` (12) und `o` (5) tragen eine Verteilung. Die Mediane der kleinen
  Mengen sind Einzelablesungen mit Median-Etikett.
* **H2 ist in der Richtung gemessen, im Betrag nicht.** Zwei Lücken, beide in
  §H2 benannt: die Kette-Schleife stammt aus dem gespeicherten WORT-Fit, nicht
  aus dem Vorkommens-Stapel, aus dem die Laufform-Zeile abgeleitet wurde; und
  der Schätzer der heutigen Zeilen ist seit LF11 der Spline-Basis-Median,
  nicht der Per-Anker-Median mit nachgeschalteter Glättung, den die Hypothese
  benennt. Die Richtung (neun von neun negativ, sechs davon in der reinen
  H2-Menge) trägt das; der Betrag je Glyphe ist eine Schätzung und wird erst
  durch R2 zurechenbar.
* **Der signierte Median ist kein Abstandsmaß.** Wo dieses Blatt „Kette gegen
  Skelett" mit einem Vorzeichen ausweist, steht der Betrag daneben (|Median|
  0,0329 gegen signiert −0,0116) — die eine Zahl sagt „kein systematischer
  Zug nach innen", die andere „aber je Vorkommen liegt sie nicht auf der
  Achse". Für H1 zählen beide, und die Anteilsrechnung (Median 0,75) läuft
  deshalb je Schleife statt über Aggregate.
* **Kein Gate ist gefallen und keines bestanden** — dies ist eine Diagnose.
  Die Zahlen hier begründen Vorregistrierungen, sie ersetzen keine.

## Reproduktion

Die Skripte liegen im Sitzungs-Scratchpad (`…/scratchpad/kringel/`):
`aperture.py` (Öffnungsweite), `check_identity.py` (Abnahme der
Erosions-Identität), `rows.py` (Zeilen), `chain.py` (die Kette je Vorkommen),
`report.py` (Tabellen und Verdikte), `viz.py` (Blätter). Sie lesen
ausschließlich die eingefrorene Wurzel, schreiben nichts ins Repo, in die DB
oder in die Wurzel, und laufen mit
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`.
