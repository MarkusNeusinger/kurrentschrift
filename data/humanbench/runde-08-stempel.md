# Runde 08 — Provenienz-Stempel

Wogegen die Urteile in [`runde-08-urteile.txt`](runde-08-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Laufform LF16 `sep08` — Runde 8 geurteilt: die Karte fällt, die `d`-Zeile
trägt") — eine **Wort**runde wird in §14 gebucht, wo auch ihr Arm
vorregistriert wurde, nicht in `qualitaetsmetrik.md` §9 wie die
Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **08** — eine **Wort**runde; abgelegt sind damit 01, 02, 05, 06, 07 und 08 |
| Seitenkennung | `ECHTHEIT/8` (gebaut mit `--round 8`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` — paariger Echtheits-Durchgang („Welche Zeile sieht echter geschrieben aus?", `--question authentic`) |
| Gebaut | 2026-09-07, 20:05 UTC |
| Gelabelt | 2026-09-08, in einem Zug, ohne Kennzahl daneben |
| Beurteiler | Projektautor (allein) |

> **Warum 03 und 04 weiter fehlen.** Die Archivnummer zählt seit §7 die Runde,
> nicht den Baulauf. Runde 03 ist die LF11-Wortrunde vom `sep02` (gefahren und
> in §14 ausgewertet, aber nie hier abgelegt), Runde 04 (Platten-Nib A3) ist
> gebaut und bis heute **ungeurteilt**. Runde 09 (Kette K-E) liegt seit `sep07`
> gebaut und ungeurteilt daneben. Eine Lücke in der Nummernfolge ist damit eine
> Aussage über den Bestand, kein Ablagefehler.

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platte | `words-abb19.png` (Abb. 19) — die eingefrorene Wordbench-Wurzel `tools/wordbench/fixtures/suetterlin/suetterlin-1922` |
| Wurzel-Export | `exported_at 2026-09-05T21:33:12+00:00`, Digest `eaa195aa7c84…` (beide Arme, gegeneinander geprüft von `build.py::check_arm_scope`) |
| Hand | **gleichhändig** — eine Platte, eine Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand) — eine andere Hand wird nie in denselben Satz gemischt |

> **Die Wurzel ist die des `sep05`-Standes, nicht die von heute.** Am
> 2026-09-07 hat der Komma-Ausschluss die Wort-Wurzel neu gebaut; seither
> trägt sie `ccb036a5eb20…` (§14 „Komma-Ausschluss `sep07`"). Das entwertet
> diese Runde nicht: sie vergleicht zwei Karten auf DIESER Wurzel und nicht
> die heutige Wurzel gegen sich selbst. Wer die Zeilen dieser Runde auf dem
> heutigen Stand sehen will, braucht eine frische Ernte auf der neuen Wurzel —
> der §14-Eintrag nennt die Befehle dafür und sagt ausdrücklich, dass sie
> nicht gefahren wurden.

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel — **alle** wurden gezeigt |
| Beurteilt | **63** Wörter, davon 57 bewegte + **6 Nullproben** (beide Tafeln bit-identisch) |
| Verdachtsklassen | 4: `lineal-verlierer` 10 · `zeile-stark` 24 · `zeile-schwach` 23 · `nullprobe` 6 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **12**, alle gespiegelt gezeigt, Abstand 20–47 Bildschirme, reihum über alle vier Klassen |
| **Bildschirme** | **75** = 63 + 12 |
| Geurteilt | 75 von 75 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen"); `reserve.json` der Runde ist leer |

> **Die 12 Wiederholungen liegen über dem Boden, die Nullproben unter
> `MIN_PAIRED_PER_CLASS`.** Wie in Runde 05 zeigt diese Runde die ganze
> Grundgesamtheit, also greift die Kürzungs-Arithmetik aus
> `menschliche-bewertung.md` §8a (`n − min_gap − REPEAT_JITTER` = 63 − 15 − 25
> = 23) nicht: 12 verlangt, 12 platziert, `MIN_PAIRED_REPEATS` = 6 deutlich
> genommen. Die Nullprobenklasse bleibt mit 6 unter `MIN_PAIRED_PER_CLASS` = 8
> und ist damit beschreibend — das stand so in der Vorregistrierung, bevor eine
> Zahl vorlag, und ist per Konstruktion so: mehr Zwei-Buchstaben-Wörter hat die
> Platte nicht.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei
(`menschliche-bewertung.md` §8a, „Woher die beiden Arme kommen").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Bestand` | `Chart-Saat` |
| Datei | `temp/runden-sep07/humanbench/bestand.json` | `temp/runden-sep07/humanbench/chart-saat.json` |
| `sha256` (16) | `9a03f1d0d3b77c66` | `aa235127f3265bc9` |
| Laufform | `frozen` — die Zeilen der Wurzel | **`overlay`** — die 15-Zeilen-Schreibliste `Z a c d e g h l longs m n p r u w` |
| Registrierung | eigene (vom Wort-Lineal gesucht) | **an die Basis gepinnt** |
| Feder | `nib_units` 0,07243258426966293, `width_resolver` `constant`, nicht überschrieben | identisch |
| `exit_trim` | `true` (Produktion seit A37) | identisch |
| `apex_handover` · `stem_depart` | `false` · `false` | identisch |
| `nib_clearance` · `seam_negotiation` | `false` · `false` | identisch |

**Ein Freiheitsgrad, und er ist die Schreibliste als GANZE.** Die 15 Zeilen
laufen gemeinsam gegen die gespeicherten — das Urteil gilt der Karte, nicht
einer Zeile. Was sich je Zeile lesen lässt, liest
[`runde-08-zeilen.json`](runde-08-zeilen.json) hinterher aus, und zwar als
bedingte Lesart über überlappende Wortmengen, nicht als eigener Arm.

Die Karte selbst (`card-K1-write.json`) kommt nicht mit: sie ist die
abgeleitete Laufform-Geometrie und fällt unter den Open-Core-Vorbehalt. Ihre
Herkunft steht im §14-Eintrag „Laufform LF16 `sep07`", Teil 2.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260008` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat das Wort bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 15 (+ Jitter bis 25) | erreicht: 20–47 Bildschirme |
| Wiederholungs-Pool | reihum über die vier deklarierten Klassen (`--strata`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Klasse |
| Frage | `authentic` | „Welche Zeile sieht echter geschrieben aus?" |
| Code | Commit `82c28f7`, Branch `laufform-chart-saat-default`, Arbeitsbaum **nicht sauber** (`code_dirty: true`) | |

> **Der unsaubere Arbeitsbaum gehört genannt, und er ist auch hier folgenlos.**
> Was die Runde zeigt, sind zwei fertige Arm-DATEIEN mit ihren `sha256`; die
> Seite komponiert nichts nach. Der Bau-Commit bestimmt also Auswahl,
> Anordnung und Spiegelung — nicht die Geometrie.

## Stand, gegen den die Urteile gelten

* **Komposition:** `core/compose.py` im Stand von `82c28f7`, `exit_trim` in
  BEIDEN Armen an (= der ausgelieferte Standard seit A37), `apex_handover`
  und `stem_depart` in beiden aus.
* **Laufform:** Basis = die Zeilen der Wurzel, also der LF12-Write vom `sep05`
  (18 Zeilen, `S` gelöscht auf Entscheid A35). Kandidat = dieselbe Komposition
  mit der 15-Zeilen-Schreibliste der chart-gesäten Ernte als Overlay; die vier
  vom Sprung- und Kopf-Gate abgewiesenen Zeilen (`i` `o` `sz` `z`) sind nicht
  dabei.
* **Vier Wörter laufen über ihren Ausschnitt hinaus** und werden angeschnitten
  gezeigt (`schießen`, `Gaul`, `Soldaten`, `Säbel`). Das trifft beide Seiten
  gleich — ein Befund über die Komposition, kein Fehler der Seite.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-08-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung.
* `runde-08-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-08-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-08 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die vier Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.
* `runde-08-zeilen.json` — die Zerlegung je Laufform-Zeile und die
  vorregistrierte Ohne-`Z`-Probe, ebenfalls nur als Zählungen. Sie ist **nicht**
  Ausgabe eines Werkzeugs, sondern in diesem PR gerechnet; ihr
  `reproduction`-Block nennt die sechs Rechenschritte und die **SHA-256 aller
  privaten Eingänge** (voller Schlüssel, Kandidaten-Karte, die beiden
  Wordbench-Berichte), damit die Rechnung gegen genau die Bytes prüfbar ist,
  die sie gelesen hat.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-08-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung,
die Seitenbilanz (14 · 19 · 30), die Unentschieden-Quote und die
Klassenbesetzung nach. Was es damit **nicht** kann, ist das Verdikt: welcher
Arm auf welcher Seite stand, steht nur im vollen `key.json`, und ohne `order`
meldet das Werkzeug ausdrücklich „neither arm is named as the candidate in the
key". Genau deshalb liegt `runde-08-auswertung.json` mit im Archiv — es hält
die Zahlen fest, die der schmale Schlüssel nicht wieder hergeben kann.

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-08-urteile.txt \
    --key    data/humanbench/runde-08-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich das Verdikt
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-08-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

> **Was `runde-08-zeilen.json` zusätzlich preisgibt — und warum das in Ordnung
> ist.** Aus fünfzehn Zeilen-Zählungen über überlappende Wortmengen lässt sich
> für einen Teil der Bildschirme zurückrechnen, welcher Arm dort gewonnen hat
> (am deutlichsten dort, wo eine Zeile 0 Kandidaten-Stimmen trägt). Die
> **Seitenzuordnung** `L`/`R` bleibt trotzdem draußen, und was der volle
> Schlüssel schützt, ist die Geometrie — `arm_gap` je Wort und der daraus
> gezogene Rang. Die Blindheit selbst ist mit dem Urteil verbraucht: eine
> spätere Runde wird neu gebaut, mit neuer Saat und neuer Seitenverteilung.
> §14-Einträge nennen die Richtung kleiner Wortgruppen ohnehin seit `sep05`
> („die 5 Apex-Gewinner gehen 5 : 0 an die Basis"); diese Datei tut dasselbe,
> nur systematisch und nachrechenbar.

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang und die
**Seitenzuordnung** je Bildschirm), `payload.json` (die Ausschnitte und beide
Kompositionen), die beiden Arm-Dateien, die Kandidatenkarte
`card-K1-write.json` und die Klassendatei `klassen-runde-8.json` — gelernter
Datensatz bzw. Vorkommens-Geometrie unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep07/`; die Klassenzuordnung selbst steht Wort
für Wort im schmalen Schlüssel (`stratum`).

> **Was daran wiederherstellbar ist — und was nicht.** Die **Geometrie** ist
> gepinnt: die beiden Arm-Dateien tragen ihre `sha256` oben, und aus Wurzel,
> Nib und den genannten Schaltern komponiert `wordarm` sie erneut. Die
> **Seitenzuordnung** ist es nicht: sie entsteht aus Saat UND Bau-Code, und der
> Bau-Commit `82c28f7` lief mit unsauberem Arbeitsbaum (`code_dirty: true`), so
> dass die genauen Bau-Änderungen nicht festgehalten sind. Wer den vollen
> Schlüssel nicht hat, kann also nicht rekonstruieren, welcher Arm auf welcher
> Seite eines Bildschirms stand — die Zahlen, die davon abhängen, überleben
> deshalb in `runde-08-auswertung.json` und `runde-08-zeilen.json`, und diese
> beiden Dateien sind genau darum committet.

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat auch in
dieser Runde kein Notizfeld ausgegeben; der freie Satz des Beurteilers zu dem,
was er gesehen hat, fiel mündlich in derselben Sitzung und ist wörtlich im
§14-Eintrag festgehalten — dort, wo er neben den Zahlen steht, die er erklärt.

Nachbau:

```bash
uv run python -m tools.humanbench.wordarm --arm Bestand \
    --out temp/runden-sep07/humanbench/bestand.json
uv run python -m tools.humanbench.wordarm --arm Chart-Saat \
    --laufform temp/runden-sep07/fixpunkt/card-K1-write.json \
    --registration-from temp/runden-sep07/humanbench/bestand.json \
    --out temp/runden-sep07/humanbench/chart-saat.json
uv run python -m tools.humanbench.build --round 8 --seed 20260008 \
    --word-arms temp/runden-sep07/humanbench/bestand.json \
                temp/runden-sep07/humanbench/chart-saat.json \
    --strata temp/runden-sep07/humanbench/klassen-runde-8.json \
    --repeats 12 --min-repeat-gap 15 --bands 5 --zoom 2 --pad-xh 0.4 \
    --out temp/runden-sep07/humanbench/runde-8
uv run python -m tools.humanbench.page --question authentic \
    --payload temp/runden-sep07/humanbench/runde-8/payload.json \
    --out temp/runden-sep07/humanbench/runde-8-chart-saat.html --round 8
```

Woher die Kandidatenkarte kommt (chart-gesäte Ernte auf der eingefrorenen
`sep05`-Wurzel, BLAS gepinnt), steht im §14-Eintrag „Laufform LF16 `sep07`".
