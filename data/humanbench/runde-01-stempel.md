# Runde 01 — Provenienz-Stempel

Wogegen die Urteile in [`runde-01-urteile.txt`](runde-01-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine zweite Runde keine Fortsetzung, sondern
eine neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7.

## Runde

| Feld | Wert |
|---|---|
| Runde | 01 |
| Modus | `single` — Kategorien-Durchgang („Was stimmt hier nicht?") |
| Gebaut | 2026-08-08 |
| Gelabelt | 2026-08-08, in einem Zug, ohne Kennzahl daneben |
| Beurteiler | Projektautor (allein) |

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platten | `words-abb19.png` (Abb. 19, 133 der 150) · `pairs-abb20.png` (Abb. 20, 17 der 150) |
| Hand | **gleichhändig** — beide Platten sind Sütterlins eigene Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand nach derselben Norm, `words.json`-Set `abb22`) — eine andere Hand wird nie in denselben Satz gemischt |
| Vermessene Proben | 70 verschiedene Wort-/Paar-Proben, 32 verschiedene Glyphen unter den 150 gelabelten Vorkommen |

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | 245 gespeicherte Vorkommen — alle `instances` der Quelle mit Ankern, `variant = 0`, deren `specimen_id` eine vermessene `words.json`-Probe trifft |
| Gelabelt | 150 |
| Zurückgehalten | 95 (ungelabelt, bandweise ausgewogen — der Bestätigungssatz für jede daraus entwickelte Kennzahl) |
| Blinde Wiederholungen | 12 |
| **Bildschirme** | **162** = 150 + 12 |
| Geurteilt | 162 von 162 (kein Abbruch) |

## Bau-Parameter

Abgelesen aus dem Bauskript der Runde (`build_pass2.py`, Arbeitsstand der
Sitzung; seither als [`tools/humanbench/build.py`](../../tools/humanbench)
ins Repo gehoben):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260808` | zieht Mischung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 (Bandgröße 49) | Schwere-Schichtung; ausgeteilt wird reihum über die Bänder |
| Mischung | gesaatet **innerhalb** jedes Bandes | ohne sie bliebe die Reihenfolge im Band schwere-absteigend, und ein abgebrochener Durchgang erreichte die saubersten Fälle nie |
| Zoom | 4× | Vergrößerung des gezeigten Ausschnitts |
| Rand | 0,4 x-Höhen, mindestens 6 px | proportional statt fest, damit die Tinte, auf der die Linie liegen *sollte*, nie am Crop-Rand abgeschnitten ist |
| Wiederholungs-Mindestabstand | 40 Bildschirme (+ Jitter bis 25) | erreicht: 40–65 Positionen |
| Wiederholungs-Pool | Glyphen mit ≥ 6 Vorkommen unter den 150, **ohne** das Versal-S, nur aus den ersten 85 Positionen | ein einprägsames Bild misst Erinnerung statt Urteil; eine Wiederholung braucht Platz hinter sich |
| Schwere-Kennzahl | größter Abstand eines gefitteten Ankers zum nächsten Skelettpixel, in x-Höhen | nur die Band-Einteilung, **kein** Bestandteil der Urteile |
| Präfix-Prüfung | die ersten 100 Bildschirme spannen Rang 0–242 von 0–244 | belegt, dass jeder Präfix der Folge eine repräsentative Stichprobe ist |

## Stand, gegen den die Urteile gelten

* **Fits:** die am 2026-08-08 **gespeicherten** `instances`-Zeilen der Quelle.
  Sie stammen aus Ernten, die **vor** dem Anker-Spike-Gate liefen
  (`tools/laufform/harvest.py::MAX_ANCHOR_SPIKE_RATIO` = 8,0). Genau deshalb
  ist die Gate-Validierung möglich: der beurteilte Satz enthält noch die
  Vorkommen, die das ausgelieferte Gate ablehnt. Das Gate wurde gegen diese
  Urteile *geprüft*, nicht auf sie *angewendet*.
* **Code:** Repo-Stand bei der Ablage — Commit `9db1136`, Branch
  `claude/s-buchstabe-darstellung-e9c98b`. Die Anker selbst hat dieser Commit
  nicht gerechnet; er beschreibt den Stand von Pipeline und Werkzeug, gegen
  den die Runde ausgewertet wurde.
* **Vorbehalt:** Sind die Vorkommen inzwischen neu geerntet, baut derselbe
  Befehl eine **andere** Runde. Wer Runde 01 exakt nachbauen will, braucht
  denselben Vorkommens-Schnappschuss (`tools/dbsnapshot`, privat).

## Was mitkommt und was nicht

**Mit dabei:** die Urteile (`runde-01-urteile.txt`) und der **schmale
Schlüssel** `runde-01-vorkommen.json` — uid → Glyph, Vorlagenwort,
`repeat_of`. Ohne ihn wäre eine Ergebniszeile wie `S026:AW#81,76` eine
bedeutungslose Zeichenkette, und zwei Stunden Menschenarbeit lägen in einer
Form im Repo, die nichts je zurücklesen kann. Welcher Buchstabe in welchem
Wort einer gemeinfreien Tafel steht, ist keine gelernte Geometrie. Damit sind
Verlässlichkeit, Besetzung, Drift und die Notizen jederzeit nachrechenbar:

```bash
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-01-urteile.txt \
    --key    data/humanbench/runde-01-vorkommen.json
```

**Nicht dabei:** der volle `key.json` (zusätzlich Schwere und Rang je
Vorkommen), `payload.json` (Crops und Vorkommens-Geometrie), `reserve.json`
und jede Kennzahlentabelle je Vorkommen. Die bleiben unter
`temp/humanbench/`: gelernter Datensatz bzw. Vorkommens-Statistik unter dem
Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Für die Abdeckungsmatrix und die Ortsprüfung braucht es sie zusätzlich
(`--rows`, `--spots`).

Das kostet wenig: aus Saat, Vorkommens-Schnappschuss und diesem Stempel sind
sie **deterministisch wiederherstellbar** — dieselbe Rolle wie bei den
eingefrorenen Bench-Fixtures, die aus demselben Grund nicht im Repo liegen.
Reproduzierbar ist alles außer dem Menschen; aufgehoben wird deshalb der
Teil, der es nicht ist — und gerade so viel Beiwerk, dass er lesbar bleibt.

Nachbau (die Voreinstellung des Werkzeugs ist `20260000 + Runde`, die Saat
dieser Runde ist es **nicht** — sie muss ausdrücklich gesetzt werden):

```bash
uv run python -m tools.humanbench.build --round 1 --seed 20260808 \
    --n-label 150 --repeats 12 --min-repeat-gap 40 --bands 5 \
    --zoom 4 --pad-xh 0.4 --instances <schnappschuss.json>
```
