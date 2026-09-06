# Runde 05 — Provenienz-Stempel

Wogegen die Urteile in [`runde-05-urteile.txt`](runde-05-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Übergänge J4 `sep06`") — eine **Wort**runde wird in §14 gebucht, wo auch
ihr Arm vorregistriert wurde, nicht in `qualitaetsmetrik.md` §9 wie die
Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **05** — die vierte abgelegte, die zweite abgelegte **Wort**runde |
| Seitenkennung | `ECHTHEIT/5` (gebaut mit `--round 5`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` — paariger Echtheits-Durchgang („Welche Zeile sieht echter geschrieben aus?", `--question authentic`) |
| Gebaut | 2026-09-04, 09:03 UTC |
| Gelabelt | 2026-09-06, in einem Zug, ohne Kennzahl daneben |
| Beurteiler | Projektautor (allein) |

> **Warum die Nummer 04 hier fehlt — und 06 vor 05 abgelegt wurde.** Die
> Archivnummer zählt seit §7 die Runde, nicht den Baulauf, und diese Runde
> heißt in Werkzeug, Kopfzeile und Journal übereinstimmend 5. **Alle drei
> Runden 04, 05 und 06 wurden am 2026-09-04 gebaut** (04 und 05 um 09:03 UTC,
> 06 um 10:02 UTC); geurteilt wurde **06 am 2026-09-05 und 05 am 2026-09-06**,
> Runde **04** (Platten-Nib A3) ist bis heute **ungeurteilt**. Die Ablage folgt
> der Nummer, nicht dem Urteilsdatum — deshalb steht 05 hier nach 06. Runde 03
> ist die LF11-Wortrunde vom `sep02` (gefahren und in §14 ausgewertet, aber nie
> hier abgelegt). Eine Lücke in der Nummernfolge ist damit eine Aussage über
> den Bestand, kein Ablagefehler.

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platte | `words-abb19.png` (Abb. 19) — die eingefrorene Wordbench-Wurzel `tools/wordbench/fixtures/suetterlin/suetterlin-1922` |
| Wurzel-Export | `exported_at 2026-09-02T22:16:06+00:00`, Digest `6cbab9d5c092` (beide Arme, gegeneinander geprüft von `build.py::check_arm_scope`) |
| Hand | **gleichhändig** — eine Platte, eine Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand) — eine andere Hand wird nie in denselben Satz gemischt |

> **Die Wurzel ist die des `sep02`-Standes, nicht die von heute.** Am
> 2026-09-05 hat der LF12-Write 18 Laufform-Zeilen ersetzt und `S` gelöscht;
> seither trägt die Wordbench-Wurzel `eaa195aa7c84…`. Das entwertet diese
> Runde nicht: sie vergleicht zwei Arme auf DIESEN Karten und nicht die
> heutige Wurzel gegen sich selbst (§14 „Laufform LF12 `sep05` —
> geschrieben", Abschnitt „Was das für die gebauten Runden heißt"). Wer die
> Lineal-Zahlen des Arms auf dem heutigen Stand sehen will, findet sie im
> §14-Eintrag dieser Runde — sie sind dort auf der `sep05`-Wurzel neu
> gemessen und ausdrücklich nicht Teil dessen, was der Beurteiler gesehen hat.

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel — **alle** wurden gezeigt (der Kandidat bewegt 60 davon) |
| Beurteilt | **63** Wörter, davon 60 bewegte + **3 Nullproben** (`unberuehrt`, die Regel feuert nicht) |
| Verdachtsklassen | 3: `naht-stark` 31 · `naht-schwach` 29 · `unberuehrt` 3 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **12**, alle gespiegelt gezeigt, Abstand 17–49 Bildschirme, reihum über `naht-stark`/`naht-schwach` |
| **Bildschirme** | **75** = 63 + 12 |
| Geurteilt | 75 von 75 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen"); `reserve.json` der Runde ist leer |

> **Die 12 Wiederholungen liegen über dem Boden, die Nullproben unter
> `MIN_PAIRED_PER_CLASS`.** Anders als in Runde 06 zeigt diese Runde die
> ganze Grundgesamtheit, also greift die Arithmetik aus
> `menschliche-bewertung.md` §8a (`n − min_gap − REPEAT_JITTER` = 63 − 15 − 25
> = 23) nicht als Kürzung: 12 verlangt, 12 platziert, `MIN_PAIRED_REPEATS` = 6
> deutlich genommen. Der Preis liegt woanders: weil die Regel auf 60 von 63
> Wörtern feuert, bleiben für die Kontrollklasse nur **3** Wörter — unter
> `MIN_PAIRED_PER_CLASS` = 8 und damit beschreibend, kein prüfbarer Anteil.
> Das stand so in der Vorregistrierung, bevor eine Zahl vorlag.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei
(`menschliche-bewertung.md` §8a, „Woher die beiden Arme kommen").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Basis (LF11, Chart-Nib)` | `J4 Austritts-Trim` |
| Datei | `temp/runden-sep04/humanbench/arm-basis.json` | `temp/runden-sep04/humanbench/arm-j4.json` |
| `sha256` (16) | `8538513b46fbd10c` | `404abd38fa2ef59b` |
| `exit_trim` | `false` | **`true`** |
| `exit_trim_min_kink_deg` | 0 (nicht verengt) | 0 (nicht verengt) — die J4-Klasse als GANZE, nicht die J4b-Verengung |
| Registrierung | eigene (vom Wort-Lineal gesucht) | **an die Basis gepinnt** |
| Feder | `nib_units` 0,07251, `width_resolver` `constant`, nicht überschrieben | identisch |
| Laufform | `frozen`, keine Überlagerung | identisch |
| `apex_handover` · `stem_depart` | `false` · `false` | identisch |

**Ein Freiheitsgrad, und er ist der Schalter `exit_trim`.** Die Pinnung der
Registrierung ist hier fast wirkungslos und deshalb billig: von 63 Wörtern
bewegt die Regel die beschränkte Suche in 3 überhaupt, gepinnt ist sie in 0 —
womit „Platzierung unangetastet", die experimentelle Kontrolle der
J4-Vorregistrierung, auch auf dem Bildschirm buchstäblich gilt.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260005` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat das Wort bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 15 (+ Jitter bis 25) | erreicht: 17–49 Bildschirme |
| Wiederholungs-Pool | reihum über die deklarierten Klassen (`--strata`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Kategorie |
| Frage | `authentic` | „Welche Zeile sieht echter geschrieben aus?" |
| Code | Commit `18a7087`, Branch `humanbench-a3-a18`, Arbeitsbaum **nicht sauber** (`code_dirty: true`) | |

> **Der unsaubere Arbeitsbaum gehört genannt, und er ist hier folgenlos.** Was
> die Runde zeigt, sind zwei fertige Arm-DATEIEN mit ihren `sha256`; die Seite
> komponiert nichts nach. Der Bau-Commit bestimmt also die Auswahl, die
> Anordnung und die Spiegelung — nicht die Geometrie. Trotzdem steht das
> Flag hier: ein Stempel, der nur die bequemen Felder trägt, ist keiner.

## Stand, gegen den die Urteile gelten

* **Komposition:** `core/compose.py` im Stand vom `sep02`, `exit_trim` in der
  Basis aus (= der zum Urteilszeitpunkt ausgelieferte Standard), im Kandidaten
  an. Die Regel selbst ist seit dem J4-Eintrag vom `sep02` unverändert.
* **Laufform:** die 22 Spline-Basis-Zeilen des LF11-Writes vom `sep02`,
  eingefroren in der Wurzel — die LF12-Karte ist zum Bau-Zeitpunkt noch nicht
  geschrieben.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.
* **Drei Wörter laufen über ihren Ausschnitt hinaus** und werden angeschnitten
  gezeigt (`Soldaten`, `Gaul`, `schießen`). Das trifft beide Seiten gleich —
  ein Befund über die Komposition, kein Fehler der Seite.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-05-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung.
* `runde-05-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-05-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-06 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die drei Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-05-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung,
die Seitenbilanz (17 · 19 · 27), die Unentschieden-Quote und die
Klassenbesetzung nach. Was es damit **nicht** kann, ist das Verdikt: welcher
Arm auf welcher Seite stand, steht nur im vollen `key.json`, und ohne `order`
meldet das Werkzeug ausdrücklich „neither arm is named as the candidate in the
key". Genau deshalb liegt `runde-05-auswertung.json` mit im Archiv — es hält
die Zahlen fest, die der schmale Schlüssel nicht wieder hergeben kann.

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-05-urteile.txt \
    --key    data/humanbench/runde-05-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich das Verdikt
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-05-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang und vor
allem die **Seitenzuordnung** je Bildschirm), `payload.json` (die Ausschnitte
und beide Kompositionen), die beiden Arm-Dateien und die Klassendatei
`strata-r5-j4.json` mit ihren `arm_gap`-Beträgen je Wort — gelernter Datensatz
bzw. Vorkommens-Geometrie unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep04/humanbench/` und sind aus Saat, Wurzel und
diesem Stempel deterministisch wiederherstellbar; die Klassenzuordnung selbst
steht Wort für Wort im schmalen Schlüssel (`stratum`).

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat auch in
dieser Runde kein Notizfeld ausgegeben; ein freier Satz des Beurteilers liegt
nicht vor. Was an dieser Runde erklärungsbedürftig ist — die hohe
Unentschieden-Quote —, ist deshalb aus den Zahlen selbst gelesen und im
§14-Eintrag begründet, nicht aus einer Äußerung.

Nachbau:

```bash
uv run python -m tools.humanbench.wordarm --arm "Basis (LF11, Chart-Nib)" \
    --out temp/runden-sep04/humanbench/arm-basis.json
uv run python -m tools.humanbench.wordarm --arm "J4 Austritts-Trim" --exit-trim \
    --registration-from temp/runden-sep04/humanbench/arm-basis.json \
    --out temp/runden-sep04/humanbench/arm-j4.json
uv run python -m tools.humanbench.build --round 5 --seed 20260005 \
    --word-arms temp/runden-sep04/humanbench/arm-basis.json \
                temp/runden-sep04/humanbench/arm-j4.json \
    --strata temp/runden-sep04/humanbench/strata-r5-j4.json \
    --repeats 12 --min-repeat-gap 15 --bands 5 --zoom 2 --pad-xh 0.4
uv run python -m tools.humanbench.page \
    --payload temp/runden-sep04/humanbench/runde-5-j4-austritts-trim/payload.json \
    --out temp/runden-sep04/humanbench/runde-5-j4-austritts-trim.html \
    --round 5 --question authentic
```
