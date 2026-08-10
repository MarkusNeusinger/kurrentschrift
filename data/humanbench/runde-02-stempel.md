# Runde 02 — Provenienz-Stempel

Wogegen die Urteile in [`runde-02-urteile.txt`](runde-02-urteile.txt) gefällt
wurden. Ohne diesen Stempel ist eine Runde keine Fortsetzung, sondern eine
neue, unvergleichbare Messung — Begründung in
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md)
§7.

## Runde

| Feld | Wert |
|---|---|
| Runde | **02** — die zweite abgelegte Menschenrunde des Projekts |
| Seitenkennung | `BEFUND/3` (gebaut mit `--round 3`) — **nicht** die Archivnummer, siehe unten |
| Modus | `single` — Kategorien-Durchgang („Was stimmt hier nicht?") |
| Gebaut | 2026-08-09, 15:50 UTC |
| Gelabelt | 2026-08-09, in einem Zug, ohne Kennzahl daneben |
| Beurteiler | Projektautor (allein) |

> **Zwei Nummern, eine Runde.** Der `--round`-Schalter zählt Bauläufe, die
> Archivnummer zählt abgelegte Runden; in dieser Sitzung waren zwei Bauläufe
> nötig (der erste rekonstruierte die Rückhaltemenge), also läuft die
> Seitenkennung der Archivnummer um eins voraus. Dasselbe gilt für Runde 01
> (`BEFUND/2`). **Maßgeblich ist die Archivnummer**; die Seitenkennung steht
> hier, damit ein Ergebnistext seiner Runde zuzuordnen bleibt. Für die nächste
> Runde ist die Regel in §7 nachgetragen: `--round` auf die Archivnummer
> setzen.

## Quelle

| Feld | Wert |
|---|---|
| Quelle | [`data/sources/suetterlin-1922`](../sources/suetterlin-1922/SOURCE.md) — Sütterlin, Ausgangsschrift 1922 |
| `source_id` | `suetterlin-1922` |
| Platten | `words-abb19.png` (Abb. 19, 89 der 95) · `pairs-abb20.png` (Abb. 20, 6 der 95) |
| Hand | **gleichhändig** — beide Platten sind Sütterlins eigene Hand |
| Nicht enthalten | `words-abb22.png` (Abb. 22, Schülerhand nach derselben Norm) — eine andere Hand wird nie in denselben Satz gemischt |
| Vermessene Proben | 59 verschiedene Wort-/Paar-Proben, 27 verschiedene Glyphen |

## Umfang

| Feld | Wert |
|---|---|
| Grundgesamtheit | dieselbe wie Runde 01 — 245 gespeicherte Vorkommen der Quelle |
| Gelabelt | 95 — **exakt die Rückhaltemenge der Runde 01**, nie zuvor gezeigt |
| Neu zurückgehalten | 0 (die Reserve ist mit dieser Runde aufgebraucht) |
| Blinde Wiederholungen | 10 (Glyphen `d` `e` `i` `n` `r`, Abstand 35–55 Positionen) |
| **Bildschirme** | **105** = 95 + 10 |
| Geurteilt | 105 von 105 (kein Abbruch) |

## Bau-Parameter

Aus dem Provenienz-Stempel des Bauwerkzeugs
([`tools/humanbench/build.py`](../../tools/humanbench), Format 2):

| Parameter | Wert | Wofür |
|---|---|---|
| Saat | `20260903` | zieht Mischung, Wiederholungsauswahl und deren Abstands-Jitter |
| Bänder | 5 | Schwere-Schichtung; ausgeteilt wird reihum über die Bänder |
| Zoom | 4× | wie Runde 01, damit die Bilder vergleichbar bleiben |
| Rand | 0,4 x-Höhen | wie Runde 01 |
| Wiederholungs-Mindestabstand | 30 Bildschirme (+ Jitter bis 25) | erreicht: 35–55 Positionen |
| Wiederholungs-Pool | Glyphen mit ≥ 6 Vorkommen, **ohne** das Versal-S | ein einprägsames Bild misst Erinnerung statt Urteil |
| Auswahl | `--only <reserve>` | die Runde besteht ausschließlich aus der Rückhaltemenge; die 150 gelabelten Vorkommen wurden ausgeschlossen |
| Code | Commit `1de7e6b`, Branch `claude/s-buchstabe-darstellung-e9c98b`, Arbeitsbaum sauber | |

## Was sich gegenüber Runde 01 am INSTRUMENT geändert hat

**Das ist der Grund, warum dieser Stempel existiert.** Zwischen den beiden
Runden wurde ein Konstruktionsfehler behoben, und er verschiebt die Zahlen:

* **Runde 01 zeichnete den Buchstaben ohne seinen Federweg.** Die Ernte fittet
  ein ganzes Wort als EINE Kette; die Verbinder liegen in deren
  Verbinder-Segmenten, nicht in den Ankern eines einzelnen Buchstabens. Die
  Seite zeichnete nur diese Anker — jeder verbundene Buchstabe endete auf dem
  Bildschirm in der Luft.
* **Runde 02 zeichnet den gespeicherten Wort-Federweg blass mit.** Der
  beurteilte Buchstabe steht darin, statt frei zu schweben.

Eine Prävalenz aus Runde 01 ist mit einer aus Runde 02 deshalb **nicht ohne
Vorbehalt vergleichbar** — am deutlichsten bei `E` („Knick nur am Rand"),
23,3 % → 7,4 %. Was den Unterschied verursacht hat — das Instrument oder die
Erwartung des Beurteilers, der die Korrektur kannte —, ist aus diesen Zahlen
prinzipiell nicht trennbar (ein verblindeter Zeichnungsvergleich ist
unmöglich: man sieht dem Bild an, ob der Verbinder gezeichnet ist).

## Stand, gegen den die Urteile gelten

* **Fits:** dieselben gespeicherten `instances`-Zeilen wie Runde 01 —
  **kein Fit hat sich zwischen den Runden geändert**. Wer die 61,1 % `G`
  gegen die 47,3 % der Runde 01 hält, vergleicht Zeichnungen, keine Fits.
* **Vorbehalt:** Sind die Vorkommen inzwischen neu geerntet, baut derselbe
  Befehl eine **andere** Runde. Wer Runde 02 exakt nachbauen will, braucht
  denselben Vorkommens-Schnappschuss (`tools/dbsnapshot`, privat).

## Was mitkommt und was nicht

**Mit dabei:** die Urteile (`runde-02-urteile.txt`, einschließlich des
Zählblocks, den die Seite ausgibt — `analyse.py` prüft ihn gegen die
Urteilszeilen und fängt so einen abgeschnittenen Einfügevorgang) und der
**schmale Schlüssel** `runde-02-vorkommen.json` — uid → Glyph, Vorlagenwort,
`slot`, `repeat_of`. Damit sind Verlässlichkeit, Besetzung, Drift und die
Notizen jederzeit nachrechenbar:

```bash
uv run python -m tools.humanbench.analyse \
    --result data/humanbench/runde-02-urteile.txt \
    --key    data/humanbench/runde-02-vorkommen.json
```

Anders als in Runde 01 hat das Bauwerkzeug den schmalen Schlüssel **selbst
geschrieben** (`vorkommen.json`, Format 2), er musste nicht rekonstruiert
werden, und die Anzeige-Ids zählen hier die **Position im Durchgang** — nicht
den Schwere-Rang wie in Runde 01. Verbunden wird trotzdem über
`identity` = (Glyph, Wort, Slot), nie über die Id.

**Nicht dabei:** der volle `key.json` (zusätzlich Schwere und Rang je
Vorkommen), `payload.json` (Crops und Vorkommens-Geometrie) und jede
Kennzahlentabelle je Vorkommen — gelernter Datensatz bzw.
Vorkommens-Statistik unter dem Open-Core-Vorbehalt
([`quellen-und-rechte.md`](../../docs/reference/quellen-und-rechte.md) §5).
Sie bleiben unter `temp/humanbench/runde-3/` und sind aus Saat,
Vorkommens-Schnappschuss und diesem Stempel deterministisch wiederherstellbar.

Nachbau:

```bash
uv run python -m tools.humanbench.build --round 3 --seed 20260903 \
    --bands 5 --repeats 10 --min-repeat-gap 30 --zoom 4 --pad-xh 0.4 \
    --only <reserve.json> --instances <schnappschuss.json>
```
