# Runde 07 — Provenienz-Stempel

Wogegen die Urteile in [`runde-07-urteile.txt`](runde-07-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Übergänge J6 `sep08`") — eine **Wort**runde wird in §14 gebucht, wo auch
ihr Arm vorregistriert wurde, nicht in `qualitaetsmetrik.md` §9 wie die
Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **07** — die fünfte abgelegte, die dritte abgelegte **Wort**runde |
| Seitenkennung | `ECHTHEIT/7` (gebaut mit `--round 7`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` — paariger Echtheits-Durchgang („Welche Zeile sieht echter geschrieben aus?", `--question authentic`) |
| Gebaut | 2026-09-06, 23:41 UTC |
| Gelabelt | 2026-09-08, in einem Zug, ohne Kennzahl daneben (544 s über 75 Bildschirme) |
| Beurteiler | Projektautor (allein) |

> **Was zwischen 06 und 07 fehlt, und was daneben noch offen ist.** Die
> Archivnummer zählt seit §7 die Runde, nicht den Baulauf, und diese Runde
> heißt in Werkzeug, Kopfzeile und Journal übereinstimmend 7. Runde 03 ist die
> LF11-Wortrunde vom `sep02` (gefahren und in §14 ausgewertet, aber nie hier
> abgelegt), Runde **04** (Platten-Nib A3) ist bis heute ungeurteilt. Gebaut
> und ungeurteilt sind am Ablagetag außerdem Runde **08** (Chart-Saat, §14
> „Laufform LF16 `sep07`") und Runde **09** (K-E, eine BAHN-Runde auf der
> Genauigkeitsfrage, also `VERGLEICH/9`). Eine Lücke in der Nummernfolge ist
> damit eine Aussage über den Bestand, kein Ablagefehler.

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
> 2026-09-07 hat der Komma-Ausschluss (Autor-Entscheid A3) vier
> Referenz-Ausschnitte von Fremdtinte befreit und beide Wurzeln neu gebaut;
> seither trägt `suetterlin-1922` `ccb036a5eb20…` und die Wort-Headline steht
> bei 0,108153. Das entwertet diese Runde nicht: sie vergleicht zwei Arme auf
> DIESEN Ausschnitten und nicht die heutige Wurzel gegen sich selbst. Die
> Lineal-Zahlen des Arms stehen im §14-Eintrag der Vorregistrierung
> („Übergänge J6 `sep06` — gemessen") auf der Wurzel, auf der er gemessen
> wurde, und sind ausdrücklich nicht Teil dessen, was der Beurteiler gesehen
> hat.

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel — **alle** wurden gezeigt (der Kandidat bewegt 57 davon) |
| Beurteilt | **63** Wörter, davon 57 bewegte + **6 Nullproben** (Δ ≤ 0,005 xh, praktisch dasselbe Bild) |
| Verdachtsklassen | 3: `naht-stark` 29 · `naht-schwach` 28 · `nullprobe` 6 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **12**, alle gespiegelt gezeigt, Abstand 16–48 Bildschirme, reihum über `naht-stark`/`naht-schwach`/`nullprobe` |
| **Bildschirme** | **75** = 63 + 12 |
| Geurteilt | 75 von 75 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen"); `reserve.json` der Runde ist leer |

> **Die Wiederholungen liegen über dem Boden, die Nullproben unter
> `MIN_PAIRED_PER_CLASS`.** Wie in Runde 05 zeigt diese Runde die ganze
> Grundgesamtheit, also greift die Arithmetik aus
> `menschliche-bewertung.md` §8a (`n − min_gap − REPEAT_JITTER` = 63 − 15 − 25
> = 23) nicht als Kürzung: 12 verlangt, 12 platziert, `MIN_PAIRED_REPEATS` = 6
> deutlich genommen. Die Kontrollklasse ist mit **6** dagegen kleiner als
> `MIN_PAIRED_PER_CLASS` = 8 und damit beschreibend, kein prüfbarer Anteil —
> mehr gab die Wurzel nicht her, weil die Regel auf 57 von 63 Wörtern feuert.
> Das stand so in der Vorregistrierung, bevor eine Zahl vorlag.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei
(`menschliche-bewertung.md` §8a, „Woher die beiden Arme kommen").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Basis (Produktion, A37)` | `J6 Nahtverhandlung` |
| Datei | `temp/runden-sep06/humanbench/arm-basis.json` | `temp/runden-sep06/humanbench/arm-j6.json` |
| `sha256` (16) | `b3dc5874f34633f9` | `3085b95655542b3e` |
| `seam_negotiation` | `false` | **`true`** |
| `seam_negotiation_max_jump_deg` | — | **45,0** (die vorregistrierte Kehren-Schranke) |
| `exit_trim` | `true` | `true` — in BEIDEN Armen, seit Autor-Entscheid A37 der Produktions-Default |
| `apex_handover` · `stem_depart` | `false` · `false` | identisch |
| Registrierung | eigene (vom Wort-Lineal gesucht) | **an die Basis gepinnt** |
| Feder | `nib_units` 0,07243, `width_resolver` `constant`, nicht überschrieben, `nib_clearance` aus | identisch |
| Laufform | `frozen`, keine Überlagerung | identisch |

**Ein Freiheitsgrad, und er ist der Schalter `seam_negotiation`.** Die Basis
ist nicht ein Stand von vorgestern, sondern die **ausgelieferte Produktion**:
der Austritts-Trim ist seit A37 (2026-09-06) Default und in beiden Armen an.
Die Pinnung der Registrierung ist hier die experimentelle Kontrolle des Arms
selbst — der Nahtpunkt ist sein Drehpunkt, es soll sich also keine
Platzierung bewegen, und auf dem Bildschirm tut es das dann auch nicht.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260007` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat das Wort bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 15 (+ Jitter bis 25) | erreicht: 16–48 Bildschirme |
| Wiederholungs-Konstanten | `repeat_min_glyph_count` 6 · `repeat_jitter` 25 · `repeat_exclude` leer | Konstanten statt Flags — eine Änderung daran verschiebt lautlos, welche Bildschirme sich wiederholen (§7) |
| Wiederholungs-Pool | reihum über die deklarierten Klassen (`--strata`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Kategorie |
| Frage | `authentic` | „Welche Zeile sieht echter geschrieben aus?" |
| Code | Commit `e581a34`, Branch `uebergaenge-j6-nahtverhandlung`, Arbeitsbaum **nicht sauber** (`code_dirty: true`) | |

> **Der unsaubere Arbeitsbaum gehört genannt, und er ist hier folgenlos** —
> dieselbe Lage wie in Runde 05. Was die Runde zeigt, sind zwei fertige
> Arm-DATEIEN mit ihren `sha256`; die Seite komponiert nichts nach. Der
> Bau-Commit bestimmt also die Auswahl, die Anordnung und die Spiegelung —
> nicht die Geometrie. Trotzdem steht das Flag hier: ein Stempel, der nur die
> bequemen Felder trägt, ist keiner.

## Stand, gegen den die Urteile gelten

* **Komposition:** `core/compose.py` im Stand von `e581a34`,
  `seam_negotiation` im Kandidaten an, in der Basis aus (= der zum
  Urteilszeitpunkt ausgelieferte Standard). Die Regel selbst ist seit dem
  J6-Eintrag vom `sep06` unverändert.
* **Laufform:** die 21 Zeilen des LF12-Writes vom `sep05`, eingefroren in der
  Wurzel — die chart-gesäte LF16-Karte ist zum Urteilszeitpunkt weder
  geschrieben noch beurteilt.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.
* **Drei Wörter laufen über ihren Ausschnitt hinaus** und werden angeschnitten
  gezeigt (`schießen`, `Soldaten`, `Säbel`). Das trifft beide Seiten gleich —
  ein Befund über die Komposition, kein Fehler der Seite.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-07-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung.
* `runde-07-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-07-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-08 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die drei Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-07-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung
(75 von 75), die Seitenbilanz (9 · 14 · 40), die Unentschieden-Quote (63,5 %)
und die Klassenbesetzung (29 · 28 · 6 mit 19 · 4 · 0 entschiedenen) nach. Was
es damit **nicht** kann, ist das Verdikt: welcher Arm auf welcher Seite stand,
steht nur im vollen `key.json`, und ohne `order` meldet das Werkzeug
ausdrücklich „neither arm is named as the candidate in the key" — die
Verlässlichkeitszeile liest sich dann als „same arm 12/12", weil ohne
Seitenzuordnung jedes Paar denselben (leeren) Arm nennt. Genau deshalb liegt
`runde-07-auswertung.json` mit im Archiv: es hält die Zahlen fest, die der
schmale Schlüssel nicht wieder hergeben kann (10/12 gleicher Arm, Basis 14 :
Kandidat 9).

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-07-urteile.txt \
    --key    data/humanbench/runde-07-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich das Verdikt
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-07-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang und vor
allem die **Seitenzuordnung** je Bildschirm), `payload.json` (die Ausschnitte
und beide Kompositionen), die beiden Arm-Dateien und die Klassendatei
`strata-r7-j6.json` mit ihren `arm_gap`-Beträgen je Wort — gelernter Datensatz
bzw. Vorkommens-Geometrie unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep06/humanbench/` und sind aus Saat, Wurzel
und diesem Stempel deterministisch wiederherstellbar; die Klassenzuordnung
selbst steht Wort für Wort im schmalen Schlüssel (`stratum`).

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat auch in
dieser Runde kein Notizfeld ausgegeben; der freie Satz des Beurteilers fiel
mündlich in derselben Sitzung und ist wörtlich im §14-Eintrag festgehalten —
dort, wo er neben den Zahlen steht, die er erklärt.

Nachbau:

```bash
uv run python -m tools.humanbench.wordarm --arm "Basis (Produktion, A37)" \
    --out temp/runden-sep06/humanbench/arm-basis.json
uv run python -m tools.humanbench.wordarm --arm "J6 Nahtverhandlung" \
    --seam-negotiation \
    --registration-from temp/runden-sep06/humanbench/arm-basis.json \
    --out temp/runden-sep06/humanbench/arm-j6.json
uv run python -m tools.humanbench.build --round 7 --seed 20260007 \
    --word-arms temp/runden-sep06/humanbench/arm-basis.json \
                temp/runden-sep06/humanbench/arm-j6.json \
    --strata temp/runden-sep06/humanbench/strata-r7-j6.json \
    --out temp/runden-sep06/humanbench/runde-7-nahtverhandlung
uv run python -m tools.humanbench.page \
    --payload temp/runden-sep06/humanbench/runde-7-nahtverhandlung/payload.json \
    --out temp/runden-sep06/humanbench/runde-7-nahtverhandlung.html \
    --round 7 --question authentic
```
