# Tinte und Schreibmaterial

Faktenblatt zu Tinte, Feder, Papier und Schulmaterial der Kurrent-Zeit —
und warum unser Extraktions- und Farbmodell so aussieht, wie es
aussieht. Alle historischen Angaben quellenbelegt. Stand: 2026-06-10.

## Eisengallustinte

- **Zusammensetzung:** Eisen(II)-sulfat (Eisenvitriol) + Galläpfel
  (Gallussäure/Gerbstoff) + Wasser + Gummi arabicum als Bindemittel
  ([Wikipedia: Eisengallustinte](https://de.wikipedia.org/wiki/Eisengallustinte)).
- **Farbverlauf:** Frisch geschrieben ist sie **blass** — der
  tiefschwarze Eisen(III)-Gallat-Komplex bildet sich erst beim Trocknen
  durch Luftsauerstoff; damit man beim Schreiben etwas sieht, wurde ein
  blauer Hilfsfarbstoff zugesetzt (daher „blauschwarz"), der später
  verblasst. Gealtert erscheint die Tinte **braun**, mit bräunlichen
  Höfen; zusätzliches Verblassen ist möglich
  ([Kunsthalle Karlsruhe: Glossar](https://www.kunsthalle-karlsruhe.de/glossar/eisengallustinte/)).
- **Status:** wichtigste Tinte von Mittelalter bis ins 20. Jh.,
  urkundenecht
  ([Wikipedia: Eisengallustinte](https://de.wikipedia.org/wiki/Eisengallustinte));
  historische Handschriften sind meist in schwarzer oder brauner Tinte
  geschrieben
  ([adfontes: Tinte und Farben](https://www.adfontes.uzh.ch/tutorium/handschriften-beschreiben/charakterisierung-des-beschreibstoffes/tinte-und-farben)).
- **Tintenfraß:** Aus dem Eisenvitriol entsteht mit Luftfeuchte
  Schwefelsäure, die die Cellulose spaltet — Papier bricht im
  Schriftbereich, Säure-Höfe verschlechtern den Kontrast
  ([Wikipedia: Tintenfraß](https://de.wikipedia.org/wiki/Tintenfra%C3%9F)).
- **Digitalisierung:** Archive machen verblasste Schrift per
  Multispektralfotografie wieder sichtbar; Eisengallustinte dringt tief
  in den Beschreibstoff ein und bleibt nachweisbar
  ([SPK-Magazin](https://www.spkmagazin.de/2024/unsichtbares-sichtbar-machen.html)).

**Projektbezug 1 — zwei Kanäle:** Genau dieses Verhalten (verblasster,
aber ehemals dicker Abstrich) begründet die Architektur-Regel „Breite =
Druck, gemessen an der Maske; Schwärze = Tintenkanal, getrennt"
([architektur.md §5](../concepts/architektur.md)) — aggressive
Binarisierung würde verblasste Schwellzüge als Haarlinien fehllesen.

**Projektbezug 2 — die Repo-Farben:** Die UI-Palette
(`app/src/styles/paper.ts`, [style-guide.md](../concepts/style-guide.md))
modelliert die Eisengallus-Zustände wörtlich: `inkState.fresh #233044`
(frisch geschriebenes Blauschwarz mit sichtbarem Hilfsfarbstoff) →
`inkState.oxidized #1c1a17` (durchoxidiert) → `inkState.aged = paper.ink
#241a10` (jahrzehntealtes Manuskriptbraun — die Stamm-Textfarbe der
Site). Die `WrittenGlyph`-Animation spielt diesen „Eisengallus-Settle"
nach dem Schreibende ab. Dazu kommen `paper.bg #e7dabf` (gealtertes
cremefarbenes Papier), `viridian #40826d` als einziger Akzent sowie die
Schulheft-Töne `rulingBlue #8fa8c4` / `marginRed #b03a3a` (gedruckte
blaue Lineatur ab 1871, rote Randleiste ab ~1900 — style-guide R4).

## Federn

- **Federkiel:** Vogelfedern (v. a. Gänse-Schwungfedern) ersetzten ab dem
  4. Jh. n. Chr. das Schilfrohr; der Kiel musste regelmäßig mit dem
  Federmesser nachgeschnitten werden
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
- **Stahlfeder:** Massenproduktion ab **1822** in England; **1842**
  erste deutsche Federfabrik (Heintze & Blanckertz), im selben Jahr
  schafften die ersten Hamburger Schulen die Federkiele ab
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
- **Spitzfeder vs. Gleichzugfeder:** Die elastische Spitzfeder erzeugt
  den Schwellzug; die Gleichzugfeder (gleichbleibende Strichbreite)
  setzte sich zusammen mit der auf sie abgestimmten Sütterlinschrift in
  den **1920er Jahren** durch
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
  Federtypen im Detail: [allgemein.md §4](allgemein.md).

## Papier

- **Hadernpapier:** Seit dem 14. Jh. wurde europäisches Papier aus
  Lumpen (Hanf, Flachs, Nessel) geschöpft — reißfest und sehr
  alterungsbeständig
  ([Wikipedia: Hadernpapier](https://de.wikipedia.org/wiki/Hadernpapier)).
- **Holzschliffpapier:** Mitte des 19. Jh. (Keller, Patentverkauf 1846);
  das enthaltene **Lignin vergilbt** unter Licht und Sauerstoff
  ([Wikipedia: Holzschliff](https://de.wikipedia.org/wiki/Holzschliff)).
- **Säurefraß:** Ab 1807 machte die Harz-Alaun-Leimung Papier
  säurehaltig; rund 100 Jahre saure Massenproduktion — die Säure spaltet
  die Celluloseketten, Papier wird brüchig
  ([Wikipedia: Papierzerfall](https://de.wikipedia.org/wiki/Papierzerfall);
  Eckjahre dort nicht scharf datiert).

## Schulmaterial

- **Schiefertafel:** Schreiblernen auf Schiefer mit Griffel bis in die
  **1970er Jahre** — leicht korrigierbar, sparte das teurere Papier
  ([Wikipedia: Schiefertafel](https://de.wikipedia.org/wiki/Schiefertafel)).
- **Schönschreibheft:** vier Linien pro Zeile (Vierliniensystem); Beleg
  u. a. ein Sütterlin-Schulheft von 1929
  ([Wikipedia: Schulheft](https://de.wikipedia.org/wiki/Schulheft)).

## Nicht belastbar belegt

Wann genau Schulhefte die Schiefertafel im Schreibunterricht ablösten;
ein Gesamtzeitraum für die flächendeckende Verdrängung des Federkiels
durch die Stahlfeder an deutschen Schulen (belegt nur: Hamburg ab 1842).
