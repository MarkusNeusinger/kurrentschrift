# Runde 09 — Provenienz-Stempel

Wogegen die Urteile in [`runde-09-urteile.txt`](runde-09-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7. Die Befunde stehen nicht hier, sondern in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(„Kette K-E `sep09` — Runde 9 geurteilt: 44 von 44 „kein Unterschied", und der
Beurteiler nennt die Saat statt des Claims") — eine **Wort**runde wird in §14
gebucht, wo auch
ihr Arm vorregistriert wurde, nicht in `qualitaetsmetrik.md` §9 wie die
Kategorien-Runden 01/02.

## Runde

| Feld | Wert |
|---|---|
| Runde | **09** — die erste **BAHN**runde; abgelegt sind damit 01, 02, 05, 06, 07, 08 und 09 |
| Seitenkennung | `VERGLEICH/9` (gebaut mit `--round 9`) — **gleich** der Archivnummer, wie §7 es seit Runde 02 verlangt |
| Modus | `word` mit **Bahn-Armen** — paariger Durchgang auf der **Genauigkeitsfrage** („Welche Linie folgt der Tinte besser?", `question: ink`), nicht auf der Echtheitsfrage der Runden 05–08 |
| Gebaut | 2026-09-07, 20:33 UTC |
| Gelabelt | 2026-09-09, in einem Zug, ohne Kennzahl daneben (420 s über 54 Bildschirme) |
| Beurteiler | Projektautor (allein) |

> **Warum diese Runde anders zählt.** Beide Arme zeichnen keine komponierte
> Tinte, sondern die **gefolgte Bahn als Mittellinie** über der unverblassten
> Platte — die Anzeige der Buchstabenrunden 01/02. Die Frage ist deshalb die
> Genauigkeitsfrage und nicht die Echtheitsfrage, und sie ist **kein
> Schalter**: `build.py::draws_ink` liest sie an den Armen ab und schreibt sie
> in Umschlag UND Stempel (`menschliche-bewertung.md` §8a, „Ein Arm kann auch
> eine BAHN sein"). **Eine Bahn-Runde ist mit den Kompositions-Wortrunden
> 05–08 nicht vergleichbar** — andere Frage, andere Anzeige, anderer
> Gegenstand.

> **Was weiter fehlt.** Die Archivnummer zählt seit §7 die Runde, nicht den
> Baulauf. Runde 03 ist die LF11-Wortrunde vom `sep02` (gefahren und in §14
> ausgewertet, aber nie hier abgelegt), Runde 04 (Platten-Nib A3) ist gebaut
> und bis heute **ungeurteilt**. Eine Lücke in der Nummernfolge ist damit eine
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
> 2026-09-07 hat der Komma-Ausschluss (Autor-Entscheid A3) vier
> Referenz-Ausschnitte von Fremdtinte befreit und die Wort-Wurzel neu gebaut;
> seither trägt sie `ccb036a5eb20…` (§14 „Komma-Ausschluss `sep07`"). Das
> entwertet diese Runde nicht: sie vergleicht zwei Bahnen auf DIESEN
> Ausschnitten und nicht die heutige Wurzel gegen sich selbst. Die
> Lineal-Zahlen der Arme stehen im §14-Eintrag der Vorregistrierung („Kette
> K-E `sep07`") auf der Wurzel, auf der sie gemessen wurden, und sind
> ausdrücklich nicht Teil dessen, was der Beurteiler gesehen hat.

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 63 Wortproben der Wurzel; der Kandidat bewegt **38** davon, 25 sind strich-identisch |
| Beurteilt | **44** Wörter = 38 bewegte + **6 Nullproben**; die übrigen 19 strich-identischen Wörter wurden vorab weggelassen (`counts.dropped.not_in_entries` = 19) |
| Verdachtsklassen | 5: `bewegt` 26 · `gewinn` 8 · `nullprobe` 6 · `riss` 2 · `ziel` 2 (die Klasse steht je Bildschirm im schmalen Schlüssel) |
| Blinde Wiederholungen | **10**, alle gespiegelt gezeigt, Abstand 7–31 Bildschirme, reihum über `bewegt`/`gewinn`/`nullprobe`/`riss` |
| **Bildschirme** | **54** = 44 + 10 |
| Geurteilt | 54 von 54 (kein Abbruch) |
| Rückhaltemenge | 0 — der Wortmodus kennt keine (`menschliche-bewertung.md` §8a, „Grenzen"); `reserve.json` der Runde ist leer |

> **Warum nur 6 der 25 Nullproben — vorregistriert, nicht nachträglich.** Alle
> 25 hätten einen strukturellen Unentschieden-Anteil von 40 % erzeugt und die
> 25-%-Schranke garantiert gerissen; sechs sind ein Boden von 13,6 % und
> zugleich der kleinste Block, der die zehn Wiederholungen noch trägt
> (`n − min_gap − REPEAT_JITTER` = 44 − 5 − 25 = 14 Kandidaten). Gegriffen
> wurden sie gleichmäßig über die Fixture-Reihenfolge, nicht ausgewählt. Die
> Klassen `ziel` (2) und `riss` (2) liegen unter `MIN_PAIRED_PER_CLASS` = 8
> und bekommen darum keine Klassenquote, sondern werden namentlich berichtet;
> ihre Mitglieder standen vor der Messung fest. Das alles steht so in der
> Vorregistrierung, bevor eine Zahl vorlag.

## Die beiden Arme

Der Modus komponiert nichts selbst; beide Tafeln kommen als Datei — hier aus
[`tracearm.py`](../../tools/humanbench/tracearm.py), das einen gefolgten
Kandidaten in den Rahmen des eingefrorenen Fixture-Eintrags legt
(`menschliche-bewertung.md` §8a, „Ein Arm kann auch eine BAHN sein").

| Feld | Basis | Kandidat |
|---|---|---|
| Name | `Basis` — Produktions-Kette **v5**, ohne jedes Flag | `K-E2` — derselbe Lauf mit `--mark-claim` |
| Kandidatendatei | `temp/runden-sep07/base-cand.json` | `temp/runden-sep07/ke2-cand.json` |
| Arm-Datei | `temp/runden-sep07/base-arm.json` | `temp/runden-sep07/ke2-arm.json` |
| `sha256` (16) | `da007a1dcaa51410` | `f8a31021b07ae2a6` |
| `mark_claim` | `false` | **`true`** |
| Folger | `pairlab.follow`, `soll_source` `composition`, `structure_guard` + Ratsche + Zone 0,55, `max_delta` 0,75, `rounds` 2, `max_iter` 8100 | identisch |
| Registrierung | eigene (die der gefolgten Zeile) | eigene — **beide Arme registrieren auf allen 63 Wörtern identisch**, `--registration-from` war nicht nötig |
| Export der Kandidaten | `exported_at 2026-09-05T21:33:12+00:00` | identisch |

**Ein Freiheitsgrad, und er ist der Knopf `mark_claim`.** Die 44 Felder der
beiden `candidate_weights`-Blöcke unterscheiden sich in genau einem: `false`
gegen `true`. Die Basis ist dabei kein Stand von vorgestern, sondern die
ausgelieferte Produktion — Kette v5 seit `aug26`.

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 3):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260009` | zieht Reihenfolge, Seitenverteilung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | hier über `arm_gap` (wie weit der Kandidat die Bahn bewegt), nicht über Schwere |
| Zoom | 2× | Wortmodus-Vorgabe; bei 4× sprengt eine Runde die 16-MB-Grenze |
| Rand | 0,4 x-Höhen | wie in jeder Runde |
| Wiederholungs-Mindestabstand | 5 (+ Jitter bis 25) | erreicht: 7–31 Bildschirme |
| Wiederholungs-Konstanten | `repeat_min_glyph_count` 6 · `repeat_jitter` 25 · `repeat_exclude` leer | Konstanten statt Flags — eine Änderung daran verschiebt lautlos, welche Bildschirme sich wiederholen (§7) |
| Wiederholungs-Pool | reihum über die deklarierten Klassen (`--strata temp/runden-sep07/klassen.json`) | misst die Seitenneigung, nicht die Verlässlichkeit einer Kategorie |
| Frage | `ink` | „Welche Linie folgt der Tinte besser?", Kopfzeile `VERGLEICH` — an den Armen abgelesen, nicht gesetzt |
| Code | Commit `5df6332`, Branch `runde-9-k-e`, Arbeitsbaum **nicht sauber** (`code_dirty: true`) | |

> **Der unsaubere Arbeitsbaum gehört genannt, und er ist hier folgenlos** —
> dieselbe Lage wie in den Runden 05 und 07. Was die Runde zeigt, sind zwei
> fertige Arm-DATEIEN mit ihren `sha256`; die Seite rechnet nichts nach. Der
> Bau-Commit bestimmt also die Auswahl, die Anordnung und die Spiegelung —
> nicht die Geometrie. Trotzdem steht das Flag hier: ein Stempel, der nur die
> bequemen Felder trägt, ist keiner.

## Stand, gegen den die Urteile gelten

* **Folger:** `tools/pairlab/follow.py` im Stand von `5df6332`, Kette **v5**
  (Kompositions-Soll + Ratsche + Zone 0,55, `aug26`), `mark_claim` im
  Kandidaten an, in der Basis aus (= der zum Urteilszeitpunkt ausgelieferte
  Standard). Die Formulierung selbst ist seit dem K-E2-Eintrag vom `aug21`
  unverändert.
* **Komposition:** `exit_trim` ist seit Autor-Entscheid A37 (`sep06`) Default
  und steckt in beiden Armen gleich — der Folger startet auf ihr.
* **Laufform:** die 21 Zeilen des LF12-Writes vom `sep05`, eingefroren in der
  Wurzel; die chart-gesäte LF16-Karte ist am Urteilstag beurteilt und
  **verworfen** (§14 „Laufform LF16 `sep08`"), also nie geschrieben.
* **Vorbehalt:** Ein Neubau auf einer anderen Fixture-Wurzel ist eine andere
  Runde. `build.py::check_arm_scope` prüft Stil, `source_id`, Wurzel und
  Export-Zeitstempel beider Arme gegeneinander — deshalb steht der
  Export-Zeitstempel oben.

## Was mitkommt und was nicht

**Mit dabei:**

* `runde-09-urteile.txt` — der Ausgabetext der Seite, unverändert. Je
  Bildschirm `<uid>:<L|R|N>[@Sekunden]`: `L`/`R` die gewählte Seite (welcher
  Arm dort stand, sagt allein der Schlüssel), `N` „kein Unterschied
  erkennbar". `R…` ist eine blinde, **gespiegelte** Wiederholung. In dieser
  Runde steht auf allen 54 Zeilen `N`.
* `runde-09-vorkommen.json` — der schmale Schlüssel, vom Bauwerkzeug selbst
  geschrieben: uid → Fixture-Eintrag, Worttext, **Verdachtsklasse**,
  `repeat_of`. Die Klasse gehört dazu, weil die klassenweise Lesart des
  Verdikts zum vorregistrierten Plan gehört und sonst den vollen Schlüssel
  bräuchte.
* `runde-09-auswertung.json` — die Auswertung des Werkzeugs, Zahl für Zahl so,
  wie sie am 2026-09-09 gerechnet wurde (Verlässlichkeit, Seitenbilanz,
  Verdikt gegen die vorregistrierten Schranken, die fünf Klassen, Drift). Sie
  trägt Zählungen und Anteile, keine Geometrie und kein Vorkommen.

**Wie weit der committete Schlüssel trägt — nachgeprüft, nicht behauptet.**
Mit `runde-09-vorkommen.json` rechnet `analyse.py` die Vollständigkeitsprüfung
(54 von 54), die Seitenbilanz (0 · 0 · 44), die Unentschieden-Quote (100 %),
die fünf Klassen und die Drift-Blöcke nach. Zwei Dinge kann er nicht: die
**Spiegelung** (er meldet „0 of 10 repeats were shown mirrored", weil das Feld
nur im vollen Schlüssel steht) und die **Seitenzuordnung** — ohne `order`
meldet das Werkzeug ausdrücklich „neither arm is named as the candidate in the
key". In dieser Runde kostet das kein Verdikt, weil es keinen entschiedenen
Bildschirm gibt; es kostet die Aussage, dass die zehn Wiederholungen
**gespiegelt** gezeigt wurden und trotzdem zehnmal denselben Arm nannten.
Genau dafür liegt `runde-09-auswertung.json` mit im Archiv.

```bash
# mit dem committeten Schlüssel: Bilanz, Ties, Klassen, Drift
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-09-urteile.txt \
    --key    data/humanbench/runde-09-vorkommen.json
# mit dem vollen Schlüssel (außerhalb des Repos): zusätzlich Spiegelung und Armnamen
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-09-urteile.txt \
    --key    <key.json der Runde> --json auswertung.json
```

Der zweite Befehl reproduziert `runde-09-auswertung.json` **byte-gleich**
(geprüft am 2026-09-09).

**Nicht dabei:** der volle `key.json` (zusätzlich `arm_gap`, Rang, Spiegelung
und vor allem die **Seitenzuordnung** je Bildschirm), `payload.json` (die
Ausschnitte und beide Bahnen), die beiden Arm-Dateien, die beiden
Kandidatendateien des Folgers und die Klassendatei `klassen.json` mit ihren
`arm_gap`-Beträgen je Wort — gelernter Datensatz bzw. Vorkommens-Geometrie
unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/runden-sep07/`; die Klassenzuordnung selbst steht Wort
für Wort im schmalen Schlüssel (`stratum`).

> **Wie weit „wiederherstellbar" hier trägt — mit dem `code_dirty` daneben
> gelesen.** Aus Saat, Wurzel und diesem Stempel lässt sich der BAU
> reproduzieren: Auswahl, Reihenfolge, Seitenverteilung und Spiegelung hängen
> allein an `20260009` und an den beiden Arm-Dateien, und `build.py` liest die
> Arme als Bytes. Die ARME selbst sind es nicht in demselben Sinn: sie kommen
> aus zwei Folger-Läufen auf einem Baum, der beim Bau **nicht sauber** war,
> und §7 der Methodendoku sagt dazu, dass ein Commit dann ein Anhaltspunkt ist
> und kein Nachweis. Maßgeblich sind deshalb nicht die Befehle unten, sondern
> die beiden `sha256` oben: sie identifizieren die Bytes, die der Beurteiler
> gesehen hat, und ein Nachbau, der sie nicht trifft, ist eine andere Runde.

**Eine Anmerkung, die nicht im Ergebnistext steht.** Die Seite hat auch in
dieser Runde kein Notizfeld ausgegeben; der freie Satz des Beurteilers fiel
schriftlich in derselben Sitzung und ist wörtlich im §14-Eintrag festgehalten
— dort, wo er neben den Zahlen steht, die er erklärt.

Nachbau:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run python -m tools.pairlab.follow --all --set words --jobs 4 \
    --expect-root eaa195aa --candidate-out temp/runden-sep07/base-cand.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run python -m tools.pairlab.follow --all --set words --jobs 4 --mark-claim \
    --expect-root eaa195aa --candidate-out temp/runden-sep07/ke2-cand.json
uv run python -m tools.humanbench.tracearm --arm Basis \
    --candidate temp/runden-sep07/base-cand.json \
    --out temp/runden-sep07/base-arm.json
uv run python -m tools.humanbench.tracearm --arm K-E2 \
    --candidate temp/runden-sep07/ke2-cand.json \
    --out temp/runden-sep07/ke2-arm.json
uv run python -m tools.humanbench.build --round 9 --seed 20260009 \
    --word-arms temp/runden-sep07/base-arm.json temp/runden-sep07/ke2-arm.json \
    --strata temp/runden-sep07/klassen.json \
    --out temp/runden-sep07/humanbench/runde-9
uv run python -m tools.humanbench.page \
    --payload temp/runden-sep07/humanbench/runde-9/payload.json \
    --out temp/runden-sep07/humanbench/runde-9-k-e.html --round 9
```
