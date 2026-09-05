# Runde 06 — Provenienz-Stempel

Wogegen die Urteile in [`runde-06-urteile.txt`](runde-06-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Übergänge J5 `sep05`") — eine **Wort**runde wird in §14 gebucht, wo auch
ihr Arm vorregistriert wurde, nicht in `qualitaetsmetrik.md` §9 wie die
Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **06** — die dritte abgelegte, die erste abgelegte **Wort**runde |
| Seitenkennung | `ECHTHEIT/6` (gebaut mit `--round 6`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` — paariger Echtheits-Durchgang („Welche Zeile sieht echter geschrieben aus?", `--question authentic`) |
| Gebaut | 2026-09-04, 10:02 UTC |
| Gelabelt | 2026-09-05, in einem Zug, ohne Kennzahl daneben |
| Beurteiler | Projektautor (allein) |

> **Warum die Nummern 03–05 hier fehlen.** Die Archivnummer zählt seit §7 die
> Runde, nicht den Baulauf, und diese Runde heißt in Werkzeug, Kopfzeile und
> Journal übereinstimmend 6. Runde 03 ist die LF11-Wortrunde vom `sep02`
> (gefahren und in §14 ausgewertet, aber nie hier abgelegt), Runde 04 (Platten-Nib
> A3) und Runde 05 (Übergänge J4) sind gebaut und **ungeurteilt**. Eine Lücke in
> der Nummernfolge ist damit eine Aussage über den Bestand, kein Ablagefehler;
> drei Namen für eine Runde wären genau die Unordnung, gegen die §7 steht.

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platte | `words-abb19.png` (Abb. 19) — die eingefrorene Wordbench-Wurzel `tools/wordbench/fixtures/suetterlin/suetterlin-1922` |
| Wurzel-Export | `exported_at 2026-09-04T08:29:01+00:00` (beide Arme, gegeneinander geprüft von `build.py::check_arm_scope`) |
| Hand | **gleichhändig** — eine Platte, eine Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand) — eine andere Hand wird nie in denselben Satz gemischt |

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel; 29 davon nicht in `--entries` (der Kandidat bewegt sie nicht und sie wurden nicht als Nullprobe gezogen) |
| Beurteilt | **34** Wörter = 22 bewegte + **12 Nullproben** (beide Tafeln bit-identisch) |
| Verdachtsklassen | 4: `apex` 12 · `stem` 8 · `beide` 2 · `nullprobe` 12 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **4**, alle gespiegelt gezeigt, Abstand 14–30 Bildschirme, reihum über `apex`/`stem`/`nullprobe` |
| **Bildschirme** | **38** = 34 + 4 |
| Geurteilt | 38 von 38 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen") |

> **`--repeats 6` verlangt, 4 bekommen — und das ist keine Panne, sondern
> Arithmetik.** `pick_word_repeats` zieht Wiederholungen nur aus den
> Bildschirmen, hinter denen noch `min_gap + REPEAT_JITTER` Platz ist; bei 34
> Einträgen, `--min-repeat-gap 5` und `REPEAT_JITTER` 25 sind das genau
> 34 − 5 − 25 = **4**. Das Werkzeug hat die Kürzung gemeldet, nicht
> verschwiegen. Die Folge trägt der Auswerteplan: unter
> `MIN_PAIRED_REPEATS` = 6 Paaren trägt die Runde **keinen Adoptionsanspruch**.
> Die Konstruktionsregel dazu ist mit dieser Runde in
> `menschliche-bewertung.md` §8a nachgezogen.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei
(`menschliche-bewertung.md` §8a, „Woher die beiden Arme kommen").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Basis (ohne J5)` | `J5 Klassenregel` |
| Datei | `temp/j5_basis.json` | `temp/j5_kandidat.json` |
| `sha256` (16) | `35a8ffe5c77fc012` | `619576595cef6014` |
| `join_rules` | `apex_handover: false` · `stem_depart: false` | **beide `true`** |
| Registrierung | eigene (vom Wort-Lineal gesucht) | **an die Basis gepinnt** |
| Feder | `nib_units` 0,07251, `width_resolver` `constant`, nicht überschrieben | identisch |
| Laufform | `frozen`, keine Überlagerung | identisch |
| `exit_trim` | `false` | `false` |

**Ein Freiheitsgrad, und er ist die Klassenregel als GANZES.** Die beiden
Schalter laufen gemeinsam gegen die Basis — das Urteil gilt der Regel, nicht
je Arm. Was sich je Arm trennen lässt, trennen die Verdachtsklassen: auf den
acht `stem`-Wörtern feuert allein `stem_depart`, auf den zwölf `apex`-Wörtern
allein `apex_handover`, auf `Soldaten` und `daß` beide.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260006` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat das Wort bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 5 (+ Jitter bis 25) | erreicht: 14–30 Bildschirme |
| Wiederholungs-Pool | reihum über die deklarierten Klassen (`--strata`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Kategorie |
| Frage | `authentic` | „Welche Zeile sieht echter geschrieben aus?" |
| Code | Commit `450704e`, Branch `track-e-tafelform-klassenregel`, Arbeitsbaum sauber | |

## Stand, gegen den die Urteile gelten

* **Komposition:** `core/compose.py` im Stand von `450704e`, beide Schalter im
  Kandidaten an, in der Basis aus (= der ausgelieferte Standard).
* **Laufform:** die 22 Spline-Basis-Zeilen des LF11-Writes vom `sep02`,
  eingefroren in der Wurzel — die LF12-Karte vom `sep04` ist zu diesem
  Zeitpunkt nicht geschrieben.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-06-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung.
* `runde-06-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-06-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-05 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die vier Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-06-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung,
die Seitenbilanz (16 · 5 · 13), die Unentschieden-Quote und die
Klassenbesetzung nach. Was es damit **nicht** kann, ist das Verdikt: welcher
Arm auf welcher Seite stand, steht nur im vollen `key.json`, und ohne `order`
meldet das Werkzeug ausdrücklich „neither arm is named as the candidate in the
key". Genau deshalb liegt `runde-06-auswertung.json` mit im Archiv — es hält
die Zahlen fest, die der schmale Schlüssel nicht wieder hergeben kann.

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-06-urteile.txt \
    --key    data/humanbench/runde-06-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich das Verdikt
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-06-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang und vor
allem die **Seitenzuordnung** je Bildschirm), `payload.json` (die Ausschnitte
und beide Kompositionen) und die beiden Arm-Dateien — gelernter Datensatz bzw.
Vorkommens-Geometrie unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep04/humanbench/runde-6-j5-klassenregel/` und
sind aus Saat, Wurzel und diesem Stempel deterministisch wiederherstellbar.

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat in dieser
Runde kein Notizfeld ausgegeben; der freie Satz des Beurteilers zu dem, was er
gesehen hat, fiel mündlich in derselben Sitzung und ist wörtlich im
§14-Eintrag festgehalten — dort, wo er neben den Zahlen steht, die er erklärt.

Nachbau:

```bash
uv run python -m tools.humanbench.wordarm --arm "Basis (ohne J5)" \
    --entries <22+12> --no-apex-handover --no-stem-depart --out temp/j5_basis.json
uv run python -m tools.humanbench.wordarm --arm "J5 Klassenregel" \
    --entries <22+12> --apex-handover --stem-depart \
    --registration-from temp/j5_basis.json --out temp/j5_kandidat.json
uv run python -m tools.humanbench.build --round 6 --seed 20260006 \
    --word-arms temp/j5_basis.json temp/j5_kandidat.json \
    --entries <22+12> --strata <klassen.json> --repeats 6 --min-repeat-gap 5 \
    --bands 5 --zoom 2 --pad-xh 0.4
uv run python -m tools.humanbench.page --payload temp/humanbench/runde-6/payload.json \
    --out temp/humanbench/runde-6/echtheit.html --round 6 --question authentic
```

Die Klassenzuordnung des `--strata`-Arguments steht Wort für Wort im schmalen
Schlüssel (`stratum`), sie muss also nicht separat aufbewahrt werden.
