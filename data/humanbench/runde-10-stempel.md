# Runde 10 — Provenienz-Stempel

Wogegen die Urteile in [`runde-10-urteile.txt`](runde-10-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Laufform LF17 `sep10` — Runde 10 geurteilt, die `d`-Zeile geschrieben (A44)
und das Wort-Lineal neu gebaselined") — eine **Wort**runde wird in §14
gebucht, wo auch ihr Arm vorregistriert wurde, nicht in `qualitaetsmetrik.md`
§9 wie die Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **10** — abgelegt sind damit 01, 02, 05, 06, 07, 08, 09 und 10 |
| Seitenkennung | `ECHTHEIT/10` (gebaut mit `--round 10`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` mit Kompositions-Armen — paariger Durchgang auf der **Echtheitsfrage** („Welche Zeile sieht echter geschrieben aus?", `question: authentic`), wie die Runden 05–08 und anders als die BAHN-Runde 09 |
| Gebaut | 2026-09-09, 21:29 UTC |
| Gelabelt | 2026-09-10, in einem Zug, 48 Bildschirme, **177 s** über alle Bildschirme (Median 3 s) |
| Beurteiler | Projektautor (allein) |

> **Was diese Runde von Runde 08 unterscheidet — EIN Freiheitsgrad statt
> fünfzehn.** Runde 08 verglich die ganze 15-Zeilen-Schreibliste der
> chart-gesäten Ernte gegen den Bestand; ihre Zerlegung je Zeile war deshalb
> eine BEDINGTE Lesart. Hier bewegt der Kandidat genau eine Laufform-Zeile
> (`d`), die übrigen zwanzig stehen auf beiden Seiten still. Was die Runde
> misst, ist damit exakt der Freiheitsgrad, den ein Write installieren würde.

> **Die geurteilte Zeile ist byte-identisch mit der aus Runde 08.** Die frische
> Ernte auf der Produktionswurzel gibt sie Anker für Anker gleich (0,000000 an
> jedem der 120 Anker gegen `card-K1-write.json` der `eaa195aa7c84…`-Wurzel),
> und der `words`-Block der Basis-Arm-Datei ist ebenfalls byte-gleich mit dem
> der Runde 08. Nachrechenbar statt zufällig: der Komma-Ausschluss vom `sep07`
> nahm `Gewehr`, `Zügel` und `streiten` Tinte weg, und keines dieser Wörter
> zieht ein `d`. Belege im §14-Eintrag „Laufform LF17 `sep09`", Teil 2.

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platte | `words-abb19.png` (Abb. 19) — die eingefrorene Wordbench-Wurzel `tools/wordbench/fixtures/suetterlin/suetterlin-1922` |
| Wurzel-Export | `exported_at 2026-09-07T20:07:03+00:00`, Digest `ccb036a5eb20…` (beide Arme, gegeneinander geprüft von `build.py::check_arm_scope`) |
| Hand | **gleichhändig** — eine Platte, eine Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand) — eine andere Hand wird nie in denselben Satz gemischt |

> **Diese Wurzel ist die des `sep07`-Standes und damit die der Vorregistrierung**
> — die Produktionswurzel nach dem Komma-Ausschluss (§14 „Komma-Ausschluss
> `sep07`"). Der Write, den die Runde ausgelöst hat, hat sie danach ersetzt
> (`a4eb48420ccb…`, `exported_at` 2026-09-10T20:44:33+00:00); das entwertet die
> Runde nicht: sie vergleicht zwei Tafeln auf DIESEN Ausschnitten und nicht die
> heutige Wurzel gegen sich selbst. Die Lineal-Zahlen der Arme stehen im
> §14-Eintrag der Vorregistrierung auf der Wurzel, auf der sie gemessen wurden,
> und sind ausdrücklich nicht Teil dessen, was der Beurteiler gesehen hat.

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel; der Kandidat bewegt **14** davon (die Wörter, die die `d`-Zeile ziehen), 49 sind bit-identisch |
| Beurteilt | **40** Wörter = 14 bewegte + **26 Nullproben**; die übrigen 23 bit-identischen Wörter wurden vorab weggelassen (`counts.dropped.not_in_entries` = 23) |
| Verdachtsklassen | 3: `d-rein` 10 · `d-und` 4 · `nullprobe` 26 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **8**, alle gespiegelt gezeigt, Abstand 17–33 Bildschirme, reihum über `d-rein`/`d-und`/`nullprobe`; **4 davon liegen auf bewegten Wörtern** (`laden` `die-2` `und` `und-3`) |
| **Bildschirme** | **48** = 40 + 8 |
| Geurteilt | 48 von 48 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen"); `reserve.json` der Runde ist leer |

> **Warum 26 Nullproben — vorregistriert, und die Rechnung steht offen im
> Plan.** Der Wiederholungstopf ist `n − min_gap − REPEAT_JITTER`; bei
> `--min-repeat-gap 5` und vierzehn bewegten Wörtern braucht es **mindestens 22**
> Nullproben, damit überhaupt sechs blinde Wiederholungen möglich sind. Genommen
> wurden 26 — vier mehr, damit der Topf die acht Paare mit Marge trägt —,
> gezogen mit der vorab benannten Saat 20260910 aus den 49 Wörtern ohne
> `d`-Zeile. **Daraus folgt ein struktureller Unentschieden-Boden von 26/40 =
> 65,0 %**, und der steht seit der Vorregistrierung fest: die 25-%-Tie-Schranke
> über ALLE Bildschirme ist per Konstruktion gerissen, die Runde entscheidet
> über die Klasse `d-rein`. `d-und` liegt mit n = 4 unter
> `MIN_PAIRED_PER_CLASS` = 8 und wird darum beschreibend berichtet, nicht als
> Quote gelesen; seine vier Mitglieder standen vor der Messung fest.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei
(`menschliche-bewertung.md` §8a, „Woher die beiden Arme kommen").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Bestand` | `d-Zeile` |
| Datei | `temp/runden-sep09/humanbench/bestand.json` | `temp/runden-sep09/humanbench/d-zeile.json` |
| `sha256` (16) | `57328d5f5fe17f18` | `7a740549377ffbd5` |
| Laufform | `frozen` — die 21 Zeilen der Wurzel | **`overlay`** — dieselben Zeilen plus die frisch geerntete `d`-Zeile (`laufform_overlay_keys: ["d"]`) |
| Registrierung | eigene (vom Wort-Lineal gesucht) | **an die Basis gepinnt** — beurteilt wird die Form, nicht eine Verschiebung |
| Feder | `nib_units` 0,07243258426966293, `width_resolver` `constant`, nicht überschrieben | identisch |
| `exit_trim` | `true` (Produktion seit A37) | identisch |
| `apex_handover` · `stem_depart` | `false` · `false` | identisch |
| `nib_clearance` · `seam_negotiation` | `false` · `false` | identisch |

**Ein Freiheitsgrad, und er ist die eine Zeile.** Die `d`-Zeile stammt aus der
chart-gesäten Ernte der Produktionswurzel (n = 11 Vorkommen, 120 Anker) und
nimmt alle drei Gates des Schreibwegs — Boden 3 ✓, Sprung 2,28 ≤ 2,95, Kopf
2,1° ≤ 15°. Die Karte selbst (`karte-d.json`) kommt nicht mit: sie ist
abgeleitete Laufform-Geometrie und fällt unter den Open-Core-Vorbehalt. Ihre
Herkunft steht im §14-Eintrag „Laufform LF17 `sep09`", Teil 2.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat (Runde) | `20260010` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Saat (Nullproben) | `20260910` | zieht die 26 Nullproben aus den 49 Wörtern ohne `d`-Zeile; vor dem Bau benannt |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat das Wort bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 5 (+ Jitter bis 25) | erreicht: 17–33 Bildschirme |
| Wiederholungs-Konstanten | `repeat_min_glyph_count` 6 · `repeat_jitter` 25 · `repeat_exclude` leer | Konstanten statt Flags — eine Änderung daran verschiebt lautlos, welche Bildschirme sich wiederholen (§7) |
| Wiederholungs-Pool | reihum über die drei deklarierten Klassen (`--strata temp/runden-sep09/humanbench/klassen-runde-10.json`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Klasse |
| Frage | `authentic` | „Welche Zeile sieht echter geschrieben aus?", Kopfzeile `ECHTHEIT` |
| Code | Commit `88730eb`, Branch `laufform-d-row-arm`, Arbeitsbaum **sauber** (`code_dirty: false`) | |

> **Der Arbeitsbaum war diesmal sauber**, anders als in den Runden 05, 07, 08
> und 09. Damit ist der Bau-Commit nicht bloß ein Anhaltspunkt, sondern ein
> Nachweis: Auswahl, Anordnung und Spiegelung hängen an `20260010`, den beiden
> Arm-Dateien und diesem Commit. Maßgeblich bleiben trotzdem die beiden
> `sha256` oben — sie identifizieren die Bytes, die der Beurteiler gesehen hat.

> **Drei Wörter laufen über ihren Ausschnitt hinaus** und werden angeschnitten
> gezeigt (`Soldaten`, `Säbel`, `schießen`). Das trifft beide Seiten gleich —
> ein Befund über die Komposition, kein Fehler der Seite.

## Stand, gegen den die Urteile gelten

* **Komposition:** `core/compose.py` im Stand von `88730eb`, `exit_trim` in
  BEIDEN Armen an (= der ausgelieferte Standard seit Autor-Entscheid A37 vom
  `sep06`), `apex_handover` und `stem_depart` in beiden aus.
* **Laufform:** Basis = die 21 Zeilen der Wurzel, also der LF12-Write vom
  `sep05` (18 Zeilen neu abgeleitet, `S` gelöscht auf Entscheid A35).
  Kandidat = dieselbe Komposition mit der einen frisch geernteten `d`-Zeile als
  Overlay. Die chart-gesäte 15-Zeilen-Karte der Runde 8 ist am `sep08`
  beurteilt und **verworfen** (§14 „Laufform LF16 `sep08`"), also nie
  geschrieben worden.
* **Was das Urteil ausgelöst hat:** Autor-Entscheid **A44** vom 2026-09-10 —
  die `d`-Zeile ist am selben Abend als Variante 100 auf `suetterlin-1922`
  geschrieben worden (Snapshot davor `2026-09-10T20-40-19Z`, danach
  `2026-09-10T20-40-47Z`, Readback worst |Δ| 0,000000). Der Bestand, gegen den
  hier geurteilt wurde, ist damit Geschichte; die Runde bleibt seine Messung.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-10-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung.
* `runde-10-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-10-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-10 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die drei Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-10-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung
(48 von 48), die Seitenbilanz (6 · 8 · 26), die Unentschieden-Quote (65,0 %),
die drei Klassen und die Drift-Blöcke nach. Zwei Dinge kann er nicht: die
**Spiegelung** (er meldet „0 of 8 repeats were shown mirrored", weil das Feld
nur im vollen Schlüssel steht) und die **Seitenzuordnung** — ohne `order`
meldet das Werkzeug ausdrücklich „neither arm is named as the candidate in the
key". Hier kostet das das Verdikt selbst: aus dem schmalen Schlüssel ist
ablesbar, dass `d-rein` zehnmal und `d-und` viermal entschieden wurde, aber
nicht, **für wen**. Genau dafür liegt `runde-10-auswertung.json` mit im Archiv.

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen, Drift
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-10-urteile.txt \
    --key    data/humanbench/runde-10-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich Spiegelung und Armnamen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-10-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

Der zweite Befehl reproduziert `runde-10-auswertung.json` **byte-gleich**
(geprüft am 2026-09-10).

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang, Spiegelung
und vor allem die **Seitenzuordnung** je Bildschirm), `payload.json` (die
Ausschnitte und beide Kompositionen), die beiden Arm-Dateien, die
Kandidaten-Karte `karte-d.json` und die Klassendatei `klassen-runde-10.json`
mit ihren `arm_gap`-Beträgen je Wort — gelernter Datensatz bzw.
Vorkommens-Geometrie unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep09/`; die Klassenzuordnung selbst steht Wort
für Wort im schmalen Schlüssel (`stratum`).

**Keine `runde-10-zeilen.json`.** Runde 08 brauchte eine Zerlegung je
Kartenzeile, weil dort fünfzehn Zeilen zugleich liefen. Hier ist die Zerlegung
die Runde: eine Zeile, drei vorab geschnittene Klassen, und die Klassenzahlen
stehen bereits in der Auswertung.

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat auch in
dieser Runde kein Notizfeld ausgegeben; anders als in den Runden 07, 08 und 09
ist diesmal **kein** freier Satz des Beurteilers gefallen — die Runde wurde
kommentarlos durchgeklickt.

Nachbau:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python -m tools.laufform.harvest \
    --path chain --sets words --min-n 1 --jobs 4 --expect-root ccb036a5eb20 \
    --out temp/runden-sep09/ernte/E1-drafts.json \
    --occ-out temp/runden-sep09/ernte/E1-occ.json \
    --word-out temp/runden-sep09/ernte/E1-words.json
uv run python -m tools.laufform.smoothrow \
    --occurrences temp/runden-sep09/ernte/E1-occ.json \
    --knots 0 --floor 3 --out temp/runden-sep09/ernte/karte-E1.json
PYTHONPATH=. uv run python temp/runden-sep09/ernte/dzeile.py   # → karte-d.json
uv run python -m tools.humanbench.wordarm --arm Bestand \
    --out temp/runden-sep09/humanbench/bestand.json
uv run python -m tools.humanbench.wordarm --arm d-Zeile \
    --laufform temp/runden-sep09/ernte/karte-d.json \
    --registration-from temp/runden-sep09/humanbench/bestand.json \
    --out temp/runden-sep09/humanbench/d-zeile.json
uv run python -m tools.humanbench.build --round 10 \
    --word-arms temp/runden-sep09/humanbench/bestand.json \
                temp/runden-sep09/humanbench/d-zeile.json \
    --strata temp/runden-sep09/humanbench/klassen-runde-10.json \
    --entries "$(cat temp/runden-sep09/humanbench/eintraege-runde-10.txt)" \
    --repeats 8 --min-repeat-gap 5 --out temp/runden-sep09/humanbench/runde-10
uv run python -m tools.humanbench.page --question authentic \
    --payload temp/runden-sep09/humanbench/runde-10/payload.json \
    --out temp/runden-sep09/humanbench/runde-10-d-zeile.html --round 10
```
