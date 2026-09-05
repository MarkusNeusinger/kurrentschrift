# Source: humanbench

- Title:     Menschliche Bewertungsdurchgänge über die gefitteten Vorkommen
             („Befund-Durchgang" — was stimmt hier nicht?) und über zwei
             Kompositionen desselben Wortes („Echtheits-Durchgang" — welche
             sieht echter geschrieben aus?)
- Author:    Projektautor (eigene Urteile, im Alleingang gefällt)
- Year:      2026 (Runde 01: erhoben am 2026-08-08 · Runde 02: 2026-08-09 ·
             Runde 06: 2026-09-05)
- License:   Eigenes Urheberrecht des Projektautors. Kein fremdes Werk und
             kein fremder Scan enthalten — die Dateien bestehen aus
             Kategoriekürzeln bzw. Seitenwahlen, einem Bildpunkt je Bildschirm,
             Sekunden und sechs handgeschriebenen Notizsätzen.
- License-Rationale: Klasse 1 nach `docs/reference/datenablage.md` §1
             (committierbar wie `/data/samples/own-hand`): eigene Aussage des
             Autors, keine Reproduktion einer geschützten Vorlage. Die
             beurteilten Bilder stammen aus `data/sources/suetterlin-1922`
             (PD-old-70, siehe dort) — hier liegen sie nicht, auch nicht als
             Ausschnitt.
             **Abgrenzung zum Open-Core-Vorbehalt** (`quellen-und-rechte.md`
             §5): die Urteile sind KEIN gelernter Datensatz. Sie enthalten
             weder Anker, noch Vorkommens-Geometrie, noch Kennzahlen je
             Vorkommen. Was ein Kürzel *meint*, steht erst im Schlüssel
             (`key.json`), und der bleibt außerhalb des Repos.
- Retrieved: 2026-08-08 (Runde 01) · 2026-08-09 (Runde 02) · 2026-09-05
             (Runde 06) — „retrieved" = erhoben, die Daten entstehen hier
             statt abgerufen zu werden

## Worauf sich die Urteile beziehen

**Runden 01 und 02 (Kategorien-Modus).** Beurteilt wurde je Bildschirm **ein
gefittetes Vorkommen**: der Ausschnitt einer Sütterlin-Schriftplatte mit der
darüber gezeichneten, aus dem M4-Fit stammenden Mittellinie des Buchstabens.
Die Frage lautet nicht „ist der Buchstabe schön", sondern „folgt die berechnete
Linie der Tinte" — und wenn nicht, **auf welche Art** sie danebenliegt.

**Runde 06 (Wortmodus, Echtheitsfrage).** Beurteilt wurde je Bildschirm **ein
Wort in zwei Kompositionen** — Basis und Kandidat, nebeneinander in EINEM
Ausschnitt, als gefüllte Tinte statt als Mittellinie —, mit einer einzigen
Frage: „Welche Zeile sieht echter geschrieben aus?" und drei gleichwertigen
Antworten (links · rechts · kein Unterschied erkennbar). Welche Seite welcher
Arm war, steht ausschließlich im Schlüssel, und der bleibt draußen.
**Eine Wortrunde ist mit den Buchstabenrunden nicht vergleichbar** — andere
Frage, andere Darstellung, anderes Objekt (`menschliche-bewertung.md` §8a).

Die Urteile gelten damit gegen **einen** Stand — des Fits (01/02) bzw. der
Komposition (06). Welcher das war — Quelle, Bestand bzw. Fixture-Wurzel, Saat,
Bau-Parameter, Arm-Prüfsummen und Code-Commit — steht je Runde im zugehörigen
Stempel (`runde-<nn>-stempel.md`). Ohne ihn wäre eine zweite Runde keine
Fortsetzung, sondern eine neue, unvergleichbare Messung.

Verfahren, Kategorien und Auswerteregeln:
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md).
Instrument: [`tools/humanbench`](../../tools/humanbench). Die Befunde einer
Runde stehen nicht hier, sondern in
[`docs/reference/qualitaetsmetrik.md`](../../docs/reference/qualitaetsmetrik.md)
§9 (Kategorien-Runden) bzw. in
[`docs/reference/messjournal.md`](../../docs/reference/messjournal.md) §14
(Wortrunden — dort, wo ihr Arm vorregistriert wurde).

## Zweck

Alle Kennzahlen des Projekts messen Geometrie; keine misst Wahrnehmung. Die
Urteile sind die **Referenz gegen die Wahrnehmung**: gegen sie wird gemessen,
welche Fehlerart eine Kennzahl überhaupt sieht (Abdeckungsmatrix) und ob ein
ausgeliefertes Ernte-Gate Vorkommen wegwirft, die ein Mensch behalten hätte.

Sie werden aufbewahrt, weil sie als einziges Stück dieser Kette **nicht
reproduzierbar** sind: Payload, Schlüssel und Kennzahlen entstehen aus Saat,
Vorkommens-Schnappschuss und Stempel jederzeit neu, das Urteil eines Menschen
an einem bestimmten Tag nicht. Nach einer Änderung am Fit werden sie nicht
wertlos, sondern zum **Vorher-Zustand**.

## runde-01-urteile.txt — 162 Zeilen Urteil, 4,0 KB

- Origin:    Ausgabetext der Befund-Seite (`tools/humanbench/page.py`,
             Modus `single`), unverändert übernommen — Zeile für Zeile so,
             wie die Seite sie am 2026-08-08 ausgegeben hat.
- Processing: keine. Kein Sortieren, kein Nachbessern, keine Korrektur der
             Tippfehler in den Notizen (sie sind Teil der Aussage).
- Stempel:   [`runde-01-stempel.md`](runde-01-stempel.md)
- Format:    Kopfzeile `BEFUND/2 geprueft=<n> von <n>`, danach je Bildschirm
             eine Zeile `<uid>:<Kategorien>[#x,y][@Sekunden][ "Notiz"]`.
  - `uid` — `S…` ein Erstauftritt, `R…` eine blinde Wiederholung eines
    früheren Bildschirms. Welcher es war, sagt allein der Schlüssel; die
    Wiederholungen messen die Verlässlichkeit des Beurteilers gegen sich
    selbst.
  - `Kategorien` — Teilmenge von `G A W B E K U`, immer in dieser festen
    Reihenfolge: **G** gut · **A** einzelner Ausreißer · **W** Gewackel ·
    **B** Bereich daneben · **E** Knick nur am Rand · **K** komplett daneben
    (nicht bewertbar) · **U** unsicher (Zusatz zu jeder Wahl). `G` und `K`
    beantworten die Frage allein, die mittlere Reihe addiert sich.
  - `#x,y` — freiwillig geklickter Marker: **die eine** Stelle, die zuerst
    auffiel, in Bildpunkten des gezeigten Bildschirms (4-fach vergrößerter
    Ausschnitt). Ein fehlender Marker ist **kein** Datum — „nicht markiert"
    heißt nicht „dort kein Fehler".
  - `@Sekunden` — Abstand zum vorherigen Weiterklick; erlaubt, Ermüdung und
    Drift zu messen statt sie wegzuannehmen. Der Ausreißer `@1320s` ist eine
    Pause, kein Nachdenken.
  - `"Notiz"` — freier Text des Autors, wörtlich.
- Note:      Die Zeilenreihenfolge ist die **Vorlage-Reihenfolge** der Seite,
             nicht die Schwere: die Bildschirme wurden gestreut über fünf
             Schwere-Bänder ausgeteilt und innerhalb jedes Bandes gesaatet
             gemischt, damit auch ein abgebrochener Durchgang eine
             repräsentative Stichprobe ist. Ohne den Schlüssel ist aus dieser
             Datei kein Vorkommen identifizierbar — das ist beabsichtigt.

## runde-01-vorkommen.json — der schmale Schlüssel, 162 Einträge

- Origin:    aus dem vollen `key.json` der Runde herausgeschnitten (seit der
             Werkzeug-Fassung schreibt `tools/humanbench/build.py` ihn selbst
             als `vorkommen.json`).
- Inhalt:    je Bildschirm `uid` → `glyph`, `word`, `slot`, `repeat_of`. Sonst
             nichts: keine Anker, keine Schwere, kein Rang, keine Kennzahl.
- Zweck:     ohne ihn ist `S026:AW#81,76` eine bedeutungslose Zeichenkette.
             Welcher Buchstabe in welchem Wort einer gemeinfreien Tafel steht,
             ist keine gelernte Geometrie (Abgrenzung oben). Der `slot` gehört
             dazu, weil die rundenübergreifende Identität (Glyph, Wort, Slot)
             ist und drei der Wörter ihren Buchstaben zweimal enthalten; die
             erste Fassung ließ ihn weg, die Nachtragung ist im Stempel
             beschrieben und gegen den vollen Schlüssel geprüft.

## runde-02-urteile.txt — 105 Zeilen Urteil plus Zählblock, 2,5 KB

- Origin:    Ausgabetext derselben Seite, unverändert übernommen, wie die
             Seite ihn am 2026-08-09 ausgegeben hat.
- Processing: keine.
- Stempel:   [`runde-02-stempel.md`](runde-02-stempel.md)
- Format:    wie Runde 01, mit zwei Unterschieden: die Kopfzeile lautet
             `BEFUND/3` (die Seitenkennung zählt Bauläufe, nicht Archivrunden
             — die Auflösung steht im Stempel), und unter den Urteilszeilen
             steht der **Zählblock** der Seite (`Gut: 64` …). Er ist mit
             abgelegt, weil `analyse.py` ihn gegen die Urteilszeilen prüft:
             ein abgeschnittener Einfügevorgang scheitert damit, statt eine
             Besetzungstabelle über den Rest zu rechnen.
- Note:      Diese Runde ist **die Rückhaltemenge der Runde 01** — 95 nie
             gezeigte Vorkommen plus 10 blinde Wiederholungen. Kein Fit hat
             sich zwischen den Runden geändert, wohl aber die Zeichnung (der
             Federweg wird jetzt mitgezeichnet); Prävalenzen der beiden Runden
             sind deshalb nur mit dem Vorbehalt im Stempel vergleichbar.

## runde-02-vorkommen.json — der schmale Schlüssel, 105 Einträge

- Origin:    von `tools/humanbench/build.py` selbst geschrieben (Format 2),
             nicht rekonstruiert.
- Inhalt:    wie Runde 01 — `uid` → `glyph`, `word`, `slot`, `repeat_of`.
- Achtung:   Die Anzeige-Ids zählen hier die **Position im Durchgang**, in
             Runde 01 den **Schwere-Rang**. Verbunden wird über
             `identity` = (Glyph, Wort, Slot), nie über die Id.

## runde-06-urteile.txt — 38 Zeilen Urteil, 0,4 KB

- Origin:    Ausgabetext der Echtheits-Seite (`tools/humanbench/page.py`,
             Modus `word`, `--question authentic`), unverändert übernommen,
             wie die Seite ihn am 2026-09-05 ausgegeben hat.
- Processing: keine.
- Stempel:   [`runde-06-stempel.md`](runde-06-stempel.md)
- Format:    Kopfzeile `ECHTHEIT/6 geprueft=38 von 38`, danach je Bildschirm
             eine Zeile `<uid>:<L|R|N>[@Sekunden]`.
  - `L`/`R` — die gewählte **Seite**, nicht der Arm. Welcher Arm dort stand,
    sagt allein der Schlüssel; ohne ihn ist die Datei zur Adoptionsfrage
    stumm, und das ist Absicht.
  - `N` — „kein Unterschied erkennbar". Ein Ergebnis, keine Ausrede: in
    dieser Runde ist es auf den zwölf Nullproben die einzige richtige
    Antwort.
  - `R…` — eine blinde, **gespiegelte** Wiederholung eines früheren
    Bildschirms; sie misst den Beurteiler gegen sich selbst und stimmt beim
    Verdikt nie mit.
  - `@Sekunden` — Abstand zum vorherigen Weiterklick, für Ermüdung und Drift.
- Note:      Keine Notizzeilen — die Seite hat in dieser Runde kein Notizfeld
             ausgegeben. Der freie Satz des Beurteilers fiel mündlich und
             steht wörtlich im §14-Eintrag des Journals, neben den Zahlen,
             die er erklärt.

## runde-06-vorkommen.json — der schmale Schlüssel, 38 Einträge

- Origin:    von `tools/humanbench/build.py` selbst geschrieben (Format 3),
             nicht rekonstruiert.
- Inhalt:    `uid` → `entry` (Fixture-Eintrag), `text` (Worttext), `stratum`
             (**Verdachtsklasse**: `apex` · `stem` · `beide` · `nullprobe`),
             `repeat_of`. Sonst nichts: keine Registrierung, keine Strichzüge,
             keine `arm_gap`, kein Rang — und **keine Seitenzuordnung**.
- Zweck:     die Klasse gehört dazu, weil die klassenweise Lesart des Verdikts
             zum vorregistrierten Auswerteplan gehört und sonst den vollen
             Schlüssel bräuchte; sie ist zugleich die einzige Aufbewahrung der
             `--strata`-Zuordnung dieser Runde.

## runde-06-auswertung.json — die Auswertung des Werkzeugs, 2,3 KB

- Origin:    `tools/humanbench/analyse.py --json`, gerechnet am 2026-09-05 aus
             dem Ergebnistext und dem vollen Schlüssel.
- Inhalt:    Verlässlichkeit (Paare, Arm-/Seiten-Übereinstimmung),
             Seitenbilanz, Verdikt gegen die vorher gesetzten Schranken, die
             vier Klassen und die Drift-Blöcke — Zählungen und Anteile.
             Keine Geometrie, kein Vorkommen, kein Wort.
- Warum hier: §6 der Methodendoku zählt „der Auswerteplan und die Auswertung"
             zum Aufzubewahrenden. Für die Kategorien-Runden 01/02 erfüllt das
             `qualitaetsmetrik.md` §9 im Fließtext; eine Wortrunde bucht ihre
             Zahlen in `messjournal.md` §14, und die Werkzeug-Ausgabe daneben
             macht nachprüfbar, welche Zahl aus dem Werkzeug kam und welche
             aus der Auslegung.
- Nachbau:   `uv run python -m tools.humanbench.analyse --result
             data/humanbench/runde-06-urteile.txt --key <key.json> --json …`
             reproduziert sie byte-gleich.

## Warum die Nummern 03–05 hier fehlen

Die Archivnummer zählt die **Runde**, und Runde 06 heißt in Werkzeug,
Kopfzeile und Journal übereinstimmend 6. Runde 03 ist die LF11-Wortrunde vom
2026-09-02 — gefahren und in `messjournal.md` §14 ausgewertet, aber nie hier
abgelegt; Runde 04 (Platten-Nib) und Runde 05 (Übergänge J4) sind gebaut und
**ungeurteilt**. Die Lücke ist damit eine Aussage über den Bestand, kein
Ablagefehler.

## Was hier nicht liegt

Nicht committet, weil gelernter Datensatz bzw. Vorkommens-Statistik
(`quellen-und-rechte.md` §5) — es bleibt unter `temp/humanbench/runde-<n>/`
bzw. `temp/runden-sep04/humanbench/runde-6-j5-klassenregel/` und ist
git-ignoriert:

- `payload.json` — die Crops und die Vorkommens-Geometrie, die die Seite
  zeichnet; im Wortmodus zusätzlich **beide Kompositionen** je Wort.
- `key.json` — die Zuordnung `uid` → Glyph, Wort, Schwere, Rang und, im
  paarigen Modus wie im Wortmodus, die **Seitenzuordnung**.
- die beiden Arm-Dateien einer Wortrunde (Strichzüge und Silhouetten je Wort);
  ihre `sha256` stehen im Stempel, damit die Runde trotzdem auf genau die
  Bytes zeigt, die sie gezeigt hat.
- `reserve.json` — die ungelabelte Rückhaltemenge.
- jede daraus abgeleitete Kennzahlentabelle je Vorkommen.

Alles davon ist aus Saat, Vorkommens-Schnappschuss und Stempel
deterministisch wiederherstellbar; der Mensch ist es nicht. Deshalb liegt
genau der Teil hier, der es nicht ist.
