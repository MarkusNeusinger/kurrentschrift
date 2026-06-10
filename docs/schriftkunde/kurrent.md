# Deutsche Kurrentschrift

Faktenblatt zur Kurrent — der Projekt-Baseline. Grundbegriffe in
[allgemein.md](allgemein.md); alle Angaben quellenbelegt, Strittiges
markiert. Stand: 2026-06-10.

## Steckbrief

| | |
|---|---|
| Zeitraum | frühes 16. Jh. bis Mitte 20. Jh. (Schulverbot 1941) |
| Lineatur | 2:1:2 (Oberlänge : Mittellänge : Unterlänge)¹ |
| Schräglage | je nach Epoche/Vorlage ~45–75°; um 1900: 60–70° (Süß 2002) |
| Feder | Federkiel/Bandzugfeder, ab dem 19. Jh. Spitzfeder |
| Strichprinzip | Schwellzug (druckabhängig) bei der Spitzfeder |

¹ 2:1:2 nennt nur der Offenbacher-Vergleichsartikel
([Wikipedia: Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift));
der Kurrent-Hauptartikel bestätigt die charakteristisch großen
Ober-/Unterlängen ohne Zahl.

## Geschichte

- Entstanden im **frühen 16. Jahrhundert** aus der Kanzleibastarda, in der
  Tradition der gotischen Kursive (Schlaufen, Unterlängen bei f/ſ,
  Schrägstellung)
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift),
  [adfontes UZH](https://www.adfontes.uzh.ch/tutorium/schriften-lesen/schriftgeschichte/bastarda-und-gotische-kursive)).
- Vom Beginn der Neuzeit bis Mitte des 20. Jahrhunderts die allgemeine
  **Verkehrs- und Geschäftsschrift** des deutschen Sprachraums
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- Es gab **keinen einheitlichen Duktus**: Schulvorschriften unterschieden
  sich regional und zeitlich; parallel liefen deutsche Kanzleischrift,
  lateinische Schrift, Fraktur und Antiqua
  ([Schulmuseum Ottweiler](https://schulmuseum-ottweiler.net/magazin/buchstabentabellen-vorschriften-und-musterbuecher)).
- Ende: Schul-Lehrverbot zum 1. September 1941, siehe
  [allgemein.md §6](allgemein.md).

## Schräglage — Literatur vs. Loth-Tafel

Literaturwerte (alle Winkel zur Grundlinie, 90° = senkrecht):

- 19. Jh., Spitzfeder: „schräger, bis hin zu 45 Grad"
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift);
  Bezugsachse dort ungenannt — bei 45° fallen beide Lesarten zusammen).
- Schulvorschriften: Heinrigs (Preußen 1809) 45°; Bayern 1852 „nicht
  geringer als 75°"
  ([Schulmuseum Ottweiler](https://schulmuseum-ottweiler.net/magazin/buchstabentabellen-vorschriften-und-musterbuecher)).
- Klassische Kurrent im Schriftvergleich: ~70°
  ([Wikipedia: Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift)).
- Kurrent **um 1900**: 60–70°, Lineatur auf 2:1:2 zurückgenommen
  (Süß 2002, S. 7 und Tafel 3 S. 11 — bibliographisch).
- Merkhilfe des Bach-Museums Leipzig für die Strichrichtung:
  „Uhrzeigerstellung 07:05"
  ([bachmuseumleipzig.de](https://www.bachmuseumleipzig.de/de/bach-museum/achtung-geheimschrift)).

**Eigene Messung der Loth-Tafel 1866** (`data/sources/loth-1866/chart.jpg`,
gemessen 2026-06-10, Skelett + Distanztransformation, Orientierung per
lokaler PCA, Methode an Synthetik auf ±2° validiert):

| Messgröße | Wert |
|---|---|
| Dicke Abstriche (Schwellzüge), ganze Tafel | **~50°** |
| m-/n-/i-Zeilen isoliert | 45–48° |
| u-Zeile isoliert | 50–51° |
| Haarstriche (Aufstriche/Verbinder) | ~28° |
| Scan-Verkippung (Horizontalstrukturen) | ±0,25° |

Die Tafel von 1866 fällt damit in die stark geneigte Phase der Mitte des
19. Jahrhunderts — **deutlich flacher als die 60–70° der Kurrent um
1900**. Konsequenz im Projekt: `styles.default_slant_deg` (Kurrent
allgemein) bleibt am Literaturwert 65, die Loth-*Quelle* führt ihren
gemessenen Wert als `sources.slant_deg`-Override (Architektur §3).

## Werkzeug und Strich

- Ursprünglich Federkiel, später auch Bandzugfeder (richtungsabhängige
  Strichstärke); seit dem 19. Jh. die metallene **Spitzfeder**, deren
  druckabhängig an- und abschwellende Linien den **Schwellzug** erzeugen
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).

## Buchstaben-Besonderheiten

- **Langes ſ / rundes s:** ſ steht im Silbenanlaut und -inlaut (auch ſp,
  ſt, ſch, ſſ), rundes s ausschließlich im Silbenauslaut; das Fugen-s in
  Komposita ist rund
  ([Wikipedia: Langes s](https://de.wikipedia.org/wiki/Langes_s)).
  Projektregeln inkl. Morphemgrenzen:
  [orthographie-regeln.md](orthographie-regeln.md).
- **ß** ist historisch eine Ligatur aus langem ſ und z (ſʒ, „Eszett");
  die ſ+s-Deutung gehört zur Antiqua-Tradition
  ([Wikipedia: Langes s](https://de.wikipedia.org/wiki/Langes_s)).
- **e und Umlaute:** das Kurrent-e hat eine eigene, an n erinnernde Form;
  aus dem übergeschriebenen e sind die heutigen Umlautpunkte entstanden
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- **n/u-Verwechslung:** n und u sehen gleich aus; das u erhält zur
  Unterscheidung den **u-Bogen**
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- **Reduplikationsstrich:** ein gerader Strich über n/m verdoppelt den
  Konsonanten (n̄ = nn)
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- **Schleifen:** viele Buchstaben entstehen in einem Federzug; h und z
  haben durchgezogene Schleifen an den Unterbögen
  ([bachmuseumleipzig.de](https://www.bachmuseumleipzig.de/de/bach-museum/achtung-geheimschrift)).
- **Ligaturen:** Der Kurrent-Artikel nennt für die Schreibschrift ch, ck,
  th, ſch, ſt und ß
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift));
  die Zwangsligaturen ch, ck, ſt, **tz** sind primär aus dem Fraktur-
  **Drucksatz** belegt
  ([Wikipedia: Ligatur (Typografie)](https://de.wikipedia.org/wiki/Ligatur_(Typografie))).
  Der geschlossene Projekt-Satz (ch · ck · tz · ſt · qu · ß) ist eine
  Design-Entscheidung, siehe
  [architektur.md §4](../concepts/architektur.md).

## Projektbezug

- **Loth 1866** (`v0-loth-1866`) ist die kanonische Geometrie-Baseline
  (PD, [datenablage.md](../reference/datenablage.md) §4); der
  Duktus-Prior ist eigene Autorenleistung darüber.
- Stand der Suche nach einer gemeinfreien **60–70°-Tafel** (2026-06-10):
  ergebnislos — alle messbaren PD-Tafeln 1866–1903 liegen bei ~45–58°
  (steilster Anker: `petzendorfer-1889`, ~57°). Petzendorfers
  „Schriftenatlas, Neue Folge" (1903–05) wurde am TIB-Volldigitalisat
  komplett geprüft und **enthält keine Kurrent-Tafel** (die
  Schreibschrift-Tafeln 53–63 sind durchweg lateinische Schriften;
  [TIB/Goobi, PDM 1.0](https://goobi.tib.eu/viewer/image/1048764478/1/),
  [DOI 10.14463/GBV:1048764478](https://doi.org/10.14463/GBV:1048764478)).
  Moderne 60–70°-Belege existieren nur als CC-BY-SA
  (Commons-Übungsblätter 2018, als Quelle wegen SA nicht committbar) —
  deren **PD-Linienblätter** messen übrigens 64,9° Schräglinien.
  Kandidat für historische Tiefe statt Steilheit: Tafel 2 des 1889er
  Atlas, „Alte deutsche Kurrentschrift und Kanzleischrift nach
  Baurenfeind, Nürnberg 1716"
  ([SLUB, PDM](https://digital.slub-dresden.de/werkansicht/dlf/764888/17)).
