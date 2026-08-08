# Source: humanbench

- Title:     Menschliche Bewertungsdurchgänge über die gefitteten Vorkommen
             („Befund-Durchgang" — was stimmt hier nicht?)
- Author:    Projektautor (eigene Urteile, im Alleingang gefällt)
- Year:      2026 (Runde 01: erhoben am 2026-08-08)
- License:   Eigenes Urheberrecht des Projektautors. Kein fremdes Werk und
             kein fremder Scan enthalten — die Dateien bestehen aus
             Kategoriekürzeln, einem Bildpunkt je Bildschirm, Sekunden und
             sechs handgeschriebenen Notizsätzen.
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
- Retrieved: 2026-08-08 (Erhebungsdatum Runde 01; „retrieved" = erhoben, die
             Daten entstehen hier statt abgerufen zu werden)

## Worauf sich die Urteile beziehen

Beurteilt wurde je Bildschirm **ein gefittetes Vorkommen**: der Ausschnitt
einer Sütterlin-Schriftplatte mit der darüber gezeichneten, aus dem M4-Fit
stammenden Mittellinie des Buchstabens. Die Frage lautet nicht „ist der
Buchstabe schön", sondern „folgt die berechnete Linie der Tinte" — und wenn
nicht, **auf welche Art** sie danebenliegt.

Die Urteile gelten damit gegen **einen** Stand des Fits. Welcher das war —
Quelle, Vorkommens-Bestand, Saat, Bau-Parameter und Code-Commit — steht je
Runde im zugehörigen Stempel (`runde-<n>-stempel.md`). Ohne ihn wäre eine
zweite Runde keine Fortsetzung, sondern eine neue, unvergleichbare Messung.

Verfahren, Kategorien und Auswerteregeln:
[`docs/reference/menschliche-bewertung.md`](../../docs/reference/menschliche-bewertung.md).
Instrument: [`tools/humanbench`](../../tools/humanbench). Die Befunde einer
Runde stehen nicht hier, sondern in
[`docs/reference/qualitaetsmetrik.md`](../../docs/reference/qualitaetsmetrik.md)
§9.

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

## Was hier nicht liegt

Nicht committet, weil gelernter Datensatz bzw. Vorkommens-Statistik
(`quellen-und-rechte.md` §5) — es bleibt unter `temp/humanbench/runde-<n>/`
und ist git-ignoriert:

- `payload.json` — die Crops und die Vorkommens-Geometrie, die die Seite
  zeichnet.
- `key.json` — die Zuordnung `uid` → Glyph, Wort, Schwere, Rang und, im
  paarigen Modus, die Seitenzuordnung.
- `reserve.json` — die ungelabelte Rückhaltemenge.
- jede daraus abgeleitete Kennzahlentabelle je Vorkommen.

Alles davon ist aus Saat, Vorkommens-Schnappschuss und Stempel
deterministisch wiederherstellbar; der Mensch ist es nicht. Deshalb liegt
genau der Teil hier, der es nicht ist.
