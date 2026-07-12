# Übergangs-Befund 2026-07-11 — unabhängige Paar-Sektion (pairlab)

**Status:** O1 und O2 (B-Seite) sind umgesetzt — Compose-Loop `jul11`,
[`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6 (Wort-Headline
0,1253 → 0,1183; Joins mit ≥ 0,25 xh Soll-Korrektur 31 → 21). Der
A-seitige d-Stub-Trim wurde gemessen und VERWORFEN (Deckung besser,
Übergangs-Komponente bestraft die Spannen-Ausdehnung konstruktionsbedingt —
Details ebd.); O3 bleibt vertagt. Werkzeug:
`tools/pairlab` (Diagnostik). Bezieht sich auf
[`architektur.md`](../concepts/architektur.md) §4 („Übergänge sind
Konsequenz, keine Daten") und die offene Diskussion in
[`planaenderungen.md`](planaenderungen.md) Vorschlag B; Vorgeschichte in
[`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6 (Läufe `jul02`,
`jul08` inkl. Verworfen-Einträge E4/E6).

## 1. Fragestellung

Trotz des Übergangs-Redesigns (`jul02`) und des Endstrich-Laufs (`jul08`)
sind einzelne Sütterlin-Verbindungen sichtbar falsch. Die Nutzer-These: es
genügt womöglich **nicht**, zwischen dem letzten Punkt von Buchstabe A und
dem ersten Punkt von Buchstabe B einen Verbindungsstrich zu generieren —
schon das **letzte/erste Stück der Glyphen selbst** müsste sich für einen
sauberen Übergang anpassen. Zu klären:

1. Wo genau liegt der Fehler — Konnektor-Form, Platzierung oder
   Glyphen-Enden?
2. Ist das **generisch** lösbar (Regeln/Klassen) oder braucht es
   **pro Paar** hinterlegte Formen (viel Autoring-Arbeit, Spannung zu §4)?

## 2. Methode: die Platzierung aus der Messung herausnehmen

Die Wort-Bench bewertet den Übergang **an der komponierten Platzierung** —
ein schiefer Konnektor und ein falsch platzierter Buchstabe sind dort
untrennbar vermischt. Genau daran ist der E4-Lauf (`jul08`, Stub-Trim +
Diagonal-Platzierung, verworfen) gescheitert: der Eingriff an den Stubs
wurde durch das gleichzeitig veränderte Platzierungsmodell unmessbar.

`tools/pairlab` (neu) entfernt den Störfaktor: für jedes **echte Vorkommen**
eines Buchstabenpaars in den Abb.-19-Wörtern und Abb.-20-Paaren wird

1. das Wort mit dem Produktions-Composer komponiert (Provenance an),
2. **jeder Buchstabe unabhängig optimal eingepasst** (begrenzte
   Translations-Gittersuche seiner eigenen Körper-Centerlines gegen das
   eingefrorene Proben-Skelett, ±0,6 xh horizontal / ±0,2 xh vertikal),
3. der Produktions-Konnektor **zwischen den unabhängig platzierten
   Buchstaben neu generiert** (identische Konstanten/Guards wie
   `core/compose.py`) und sein Chamfer zur Probe gemessen,
4. der **echte Verbindungszug** der Probe extrahiert (Skelett-Verfolgung
   durch die Lücke zwischen den Tintenspalten) und
5. das **Anpassungs-Profil** gemessen: Abweichung des letzten Strichs von A
   bzw. des ersten Strichs von B von der Probe als Funktion der Bogenlänge
   ab dem Join — `tail_adapt`/`head_adapt` = Bogenlänge (xh), über die die
   echte Feder von der Template-Form abweicht (Schwelle 0,12 xh).

87 Vorkommen über 45 Paare vermessen (alle scorbaren Treffer der gefragten
Paare; Reproduktion s. §7). Overlays: `temp/pairlab_*.png`.

## 3. Befund 1 — die Platzierung ist der größte Einzelfehler

Median der nötigen horizontalen Korrektur (max. der beiden Buchstaben eines
Paars): **0,19 xh**; P75 0,36 xh, P90 0,52 xh. **39 von 87 Vorkommen
brauchen ≥ 0,25 xh Korrektur** — der Fehler akkumuliert entlang langer
Wörter (Advance-/Clearance-Modell), z. B. `Galoppieren` −0,52 xh am r.
Ein formal perfekter Konnektor landet dann trotzdem auf falscher Tinte:
ein Großteil der „sehr falschen" Übergänge im Live-Bild ist ein
Platzierungs-, kein Formfehler.

## 4. Befund 2 — die Standard-Diagonale ist generisch richtig

Für die Brot-und-Butter-Verbindungen liegt der neu generierte Konnektor
**nach** unabhängiger Platzierung praktisch auf der Probe (Chamfer ≤ 0,07,
Anpassung 0):

`e→r` 0.028 · `e→i` 0.040 · `e→n` 0.062 · `n→e` 0.042 · `n→n` 0.062 ·
`u→n` 0.043 · `i→e` 0.035 · `t→e` 0.032 · `f→e` 0.024 · `g→e` 0.014 ·
`h→a` 0.041 · `z→w` 0.031 · `w→e` 0.068 · `longs→a` 0.063 · `b→z`/`v→x`/`r→z` ≤ 0.054

Auch die Tangenten stimmen: generiert +36…+44°, Probe 33…53°. Die im
`jul08`-Loop als systematisch schlecht gemessenen `f→e`/`t→e` (0.220/0.204
an komponierter Platzierung) sind hier unauffällig — ihr Bench-Penalty war
Platzierung (t/f-Vorkommen brauchen ±0,3…0,6 xh Korrektur), nicht
Übergangs-Form. **§4 hält für diese Klasse:** exit/entry + Tangenten
erzeugen den richtigen Übergang.

## 5. Befund 3 — die Stubs: bei Hoch-Exits schreibt die Feder die
## Glyphen-Enden um (These bestätigt, aber klassenweise)

Die schlechten Paare gruppieren sich fast vollständig nach der
**Exit-Klasse des ERSTEN Buchstabens** — und die Abweichung sitzt in den
**Kopplungs-Stubs** der Chart-Zellen (Entry-Stub: Anstrich von halber Höhe
zum Bogenscheitel; Exit-Stub: Grundlinien-Fuß auf halbe Höhe), nicht im
Buchstabenkörper:

| Klasse (A-Exit) | Paare (gen-Chamfer) | tail_adapt | head_adapt |
|---|---|---|---|
| **d-Schleife** (hoher Schleifen-Exit) | d→e 0.170, d→p 0.200, d→z 0.162, d→f 0.140, d→x/d→o 0.11, d→s/d→t/d→k 0.06–0.09 | **0,17–0,31 konstant über ALLE d-Paare** | 0–0,43 (e 0,36, p 0,31) |
| **Deckstrich-Bogen** (o, b, v, w) | o→n 0.119, b→i 0.187, b→s 0.113, b→p 0.095, v→s 0.185, v→p 0.129, w→i 0.087 | b→i 0,22, w→i 0,21, sonst ~0 | 0,14–0,31 (n nach o 0,30) |
| **r-Arm** (Deckstrich auf x-Höhe) | r→e 0.115, r→x 0.119, r→p 0.107 | ~0 (der Arm ist echte Tinte) | **0,23–0,29** |
| **Versalien** | B→i 0.258, I→n 0.249, D→u 0.195, O→f 0.129 | 0,15–0,36 | 0–0,45 |
| Langes ſ → Unterlängen-Folge | longs→g 0.208 | 0 | 0,37 |

Geometrie des echten Zuges (Overlays `d→e` ×4, `o→n` ×2, `b→i`): die Feder
verlässt die Form **am letzten Strukturpunkt** (d: Schleifenkreuzung ~0,8 xh;
o/b/v/w: Bogenende; r: Armende) und fällt in **einer** Diagonale direkt in
den **Scheitel des ersten Abstrichs** des Folgebuchstabens. Beide Stubs —
A-Exit-Stub und B-Entry-Stub — existieren auf der Tafel **nicht**; unser
Konnektor überbrückt stattdessen die Stub-Spitzen (das „Shelf" aus dem
E4-Befund, hier erstmals platzierungsbereinigt und pro Paar quantifiziert:
Stub-Ersatzlänge 0,2–0,4 xh je Seite). Deutlichster Winkel-Beleg `b→i`:
generierter Abgang **+44°** (steigende Bogen-Tangente, trotz Launch-Clamp),
echter Zug **−60°** (fallend).

Sekundärbefund (Autoring, nicht Compose): die r-Form weicht mittig 0,1–0,2 xh
von der fließenden Probe ab (Profile `r→e`), passend zum offenen
buchstabenspezifischen Verdacht aus `jul08` Runde 2/3.

## 5b. Duktus-Trace: das echte Paar nachgefahren (Nachtrag, gleicher Tag)

Auf Nutzer-Vorschlag fährt pairlab die echten Paare jetzt zusätzlich **entlang
des bekannten Duktus nach**: der M4-Fit (`core/fit.py`,
`fit_template_to_instance` — Stroke-Struktur + Ecken bleiben erhalten,
Tikhonov-regularisiert) warpt beide Templates auf die Tinte der Probe
(buchstabenlokales Skelett-Fenster). Das gefittete Paar + der verfolgte
Verbindungszug IST der kontinuierliche **Soll-Pfad** des Vorkommens — die
perfekte Zielvorgabe für den Generator (violett in den Overlays; `fit
exit/entry` in Caption/JSON; `--no-trace` schaltet ab).

Abgelesene Soll-Kopplungen (gefittete Endpunkt-Geometrie, xh / Grad):

| Klasse | Soll-Abgang (A) | Soll-Ankunft (B) |
|---|---|---|
| Arkaden-Diagonale (e→n/e→r/u→n/n→e) | y 0,43–0,68 @ +29…+44° | y 0,47–0,67 @ +31…+52° |
| Deckstrich/Arm (r→e, o→n) | **y 0,81–0,87 @ +2…+13° (eben!)** | **y 0,60–0,72 = Scheitel**, nicht Stub-Fuß |
| Schleifen-Exit (d→e, b→i) | Fit-Endpunkt y 1,2–1,5 auf der Flanke — der Stub hat keine eigene Tinte (Trim-Signal); echter Abgang laut Zugverfolgung y ≈ 0,8 fallend | y 0,60–0,72 = Scheitel |

Lesart der beiden Kennwerte: bei braven Diagonalen stimmen Fit-Endpunkt und
Zugverfolgungs-Abgang überein; klafft dazwischen eine Lücke (d, b), wurde der
Exit-Stub vom Fit in die Schleifenflanke absorbiert — genau das ist die zu
trimmende Strecke. Die O2-Kopplungsanker sind damit nicht mehr Schätzwerte,
sondern **pro Klasse gemessen**; und für einen späteren Vorschlag-B-Import
liefert derselbe Fit die geernteten Paar-Geometrien gleich mit.

## 6. Beantwortung der Kernfrage + Lösungsoptionen

**Generisch lösbar — als Klassenregel, nicht pro Paar.** Die Abweichungen
erklären sich durch wenige Exit-Klassen × eine Entry-Regel („kopple am
Scheitel des ersten Abstrichs"); kein Kleinbuchstaben-Paar verhält sich
idiosynkratisch (deckt sich mit der Vorschlag-B-Residualtabelle vom
2026-07-08). Nur die Versal-Verbindungen (post-MVP-Scope) sind Kandidaten
für echte Paar-/Verkettungsformen.

Empfohlene Reihenfolge:

1. **O1 — Platzierung zuerst** *(umgesetzt, Lauf `jul11`: Hoch-Exit-Tuck
   + Rückwärts-Exit-Clearance)*: das Advance-/
   Clearance-Modell gegen die gemessenen Ist-Abstände der Tafel kalibrieren
   (pairlab liefert die Soll-Verschiebungen pro Vorkommen). Erst danach ist
   jeder Form-Eingriff sauber messbar — die E4-Lektion.
2. **O2 — Kopplungsanker statt Stub-Spitzen** *(B-Seite umgesetzt, Lauf
   `jul11`: Anker auf der steigenden Flanke bei y 0,78 + Entry-Stub-Trim,
   dazu der Level-Auslauf am Wortende; der A-seitige d-Trim wurde gemessen
   und auf der eingefrorenen Metrik verworfen — s. Statuskopf)*
   (generisch, klassenbasiert):
   pro Template zur Renderzeit zwei ableitbare Ankerpunkte bestimmen —
   B-seitig der Scheitel des ersten Abstrichs (erstes lokales y-Maximum
   innerhalb ~0,5 xh Bogenlänge), A-seitig der letzte Strukturpunkt
   (Schleifenkreuzung/Bogenende statt Stub-Spitze). Ist der A-Exit hoch
   (≥ ~0,7 xh: d-Schleife, Deckstrich-Bögen, r-Arm), wird der Übergang
   **Anker→Anker** generiert und die Stub-Stücke im **gebundenen** Kontext
   weggelassen (gemessene Ersatzlänge 0,2–0,4 xh). Die Soll-Werte pro Klasse
   liegen seit dem Duktus-Trace (§5b) gemessen vor: Deckstrich-Klasse eben
   (+2…+13°) bei y ≈ 0,85 abgehen, am Scheitel y ≈ 0,6–0,7 ankommen.
   Wortanfangs-Stubs bleiben — sie SIND der Anstrich (E2-Erkenntnis). Nur
   Renderpfad, Template bleibt Chart-Messung (Prinzip wie
   `FLUENT_BODY_PITCH`); Absicherung über den Wort-Bench-Loop, `pair_loss`
   als Report.
3. **O3 — Paar-Overrides (Vorschlag B) vertagen:** nach O1+O2 neu messen;
   nach heutiger Evidenz für Kleinbuchstaben unnötig. Erst mit der
   Versal-Phase wieder prüfen (B→i/I→n/D→u sind die stärksten Kandidaten
   für echte gefittete Paare). Die Provenance-Naht in `core/compose.py`
   bleibt der Hook.

Nicht wieder anfassen (Verworfen-Einträge bleiben bindend): pauschaler
`CONNECT_GAP`, Ganzhöhen-Clearance, uniformer Wortanfangs-Anstrich (E2),
Level-Join-Begradigung (E6). O2 ist **nicht** E4: E4 trimte blind auf halbe
Höhe und änderte gleichzeitig die Platzierung; O2 koppelt an gemessenen
Strukturpunkten und setzt die separat gelöste Platzierung (O1) voraus.

## 7. Reproduktion

```bash
# einmalig: Fixtures einfrieren (DB nötig)
uv run python -m tools.wordbench.export_fixtures --set all

# Beispiele dieses Befunds
uv run --extra viz python -m tools.pairlab re de on bi --json temp/pairs.json
uv run --extra viz python -m tools.pairlab longs,g d,e --max-occ 4
```

Werkzeug-Doku: `tools/pairlab/README.md`. Die Zahlen dieses Dokuments:
87 Vorkommen, Batches als JSON unter `temp/pairlab_batch*.json`
(gitignored, reproduzierbar mit obigen Kommandos).
