# Schriftkunde — Grundbegriffe und Überblick

Nachschlage-Sammlung der wichtigsten Fakten zur deutschen Schreibschrift,
**ausschließlich aus frei zugänglichen Quellen** (jede Angabe trägt ihre
Quelle; Strittiges ist markiert). Die Schwesterdokumente behandeln die
drei Startschriften im Detail: [Kurrent](kurrent.md) ·
[Sütterlin](suetterlin.md) · [Offenbacher](offenbacher.md).

Urheberrechtlich geschützte Lehrbücher (z. B. Süß 2002, siehe
[Quellen- und Rechte-Policy](../reference/quellen-und-rechte.md)) werden
hier nur **bibliographisch** zitiert — kein Material daraus liegt im Repo.

Stand: 2026-06-10. Die Dateien werden nach und nach ergänzt.

---

## 1. Lineatur und Vierliniensystem

- **Lineatur** (von lat. *linea*) ist die Linienvorgabe beim manuellen
  Schreiben, vor allem in Schulheften
  ([Wikipedia: Lineatur](https://de.wikipedia.org/wiki/Lineatur)).
- Das **Vierliniensystem** der Schul-Lineatur benennt die vier Linien als
  **Oberlinie · Mittellinie · Grundlinie (Schreiblinie) · Unterlinie**
  ([Wikipedia: Lineatur](https://de.wikipedia.org/wiki/Lineatur)).
- Es teilt den Schreibraum in drei **Zonen**: **Oberlänge** (Oberlinie bis
  Mittellinie), **Mittellänge** (Mittellinie bis Grundlinie; auch
  Mittelband, Höhenmaß: x-Höhe) und **Unterlänge** (Grundlinie bis
  Unterlinie)
  ([Wikipedia: Lineatur](https://de.wikipedia.org/wiki/Lineatur),
  [Mittellänge](https://de.wikipedia.org/wiki/Mittell%C3%A4nge),
  [Oberlänge](https://de.wikipedia.org/wiki/Oberl%C3%A4nge),
  [Unterlänge](https://de.wikipedia.org/wiki/Unterl%C3%A4nge)).
- Die Satztypografie benennt anders (x-Linie/H-Linie/p-Linie);
  „Oberlinie"/„Unterlinie" sind die Namen der **Schul-Lineatur** — für ein
  Schreiblern-Produkt die richtige Wahl
  ([Wikipedia: Oberlänge](https://de.wikipedia.org/wiki/Oberl%C3%A4nge)).
- Handschrift-Lineaturen sind in **DIN 16552-1** (2005) genormt; übliche
  Zonenverhältnisse sind 1:1:1, 2:3:2, 3:4:3 und 2:1:2
  ([Wikipedia: Lineatur](https://de.wikipedia.org/wiki/Lineatur)).

**Projekt-Sprachgebrauch** (deckungsgleich mit UI und CLAUDE.md): Linien
heißen Grundlinie · Mittellinie · Oberlinie · Unterlinie; Zonen heißen
Oberlänge · Mittellänge · Unterlänge (synonym: Ober-/Mittel-/Unterband).

## 2. Schräglage

- Die **Schräglage** der Zeichen-Hauptachse ist ein konstitutives Merkmal
  von Schreibschriften; „Schriftneigung"/„Neigungswinkel" werden synonym
  bzw. für das Winkelmaß verwendet
  ([Wikipedia: Schreibschrift](https://de.wikipedia.org/wiki/Schreibschrift)).
- **Messkonvention:** Der Winkel wird zwischen Grundstrich (Abstrich) und
  **Grundlinie** gemessen, 90° = senkrecht. Explizit so festgelegt in der
  englischen Wikipedia für Spencerian („52 degrees, measured
  counterclockwise from the baseline",
  [en.wikipedia: Spencerian script](https://en.wikipedia.org/wiki/Spencerian_script));
  die bayerische Schulvorschrift von 1852 („Neigung nicht geringer
  als 75°") setzt dieselbe Achse voraus
  ([Schulmuseum Ottweiler](https://schulmuseum-ottweiler.net/magazin/buchstabentabellen-vorschriften-und-musterbuecher)).
  Viele deutsche Quellen lassen die Bezugsachse ungenannt — repo-weit gilt
  daher ausdrücklich: **`slant_deg` = Winkel zur Grundlinie, 90 =
  senkrecht**.
- Vergleichswerte der Spitzfeder-Kalligrafie: Copperplate ≈ 55°,
  Spencerian 52°
  ([en.wikipedia: Spencerian script](https://en.wikipedia.org/wiki/Spencerian_script),
  [ausfraukesfeder.de](https://ausfraukesfeder.de/spitzfederkalligrafie-stile/)).

## 3. Striche und Strichkontrast

- **Grundstrich** = der breite, abwärts gezogene Hauptstrich (typografisch
  auch **Schattenstrich**); **Haarstrich** = die feine Linie, typografisch
  der Aufstrich
  ([Wikipedia: Strichstärke](https://de.wikipedia.org/wiki/Strichst%C3%A4rke)).
- **Aufstrich** = nach oben geführte Linie, **Abstrich** = nach unten
  geführte (kräftigere) Linie
  ([Wiktionary: Aufstrich](https://de.wiktionary.org/wiki/Aufstrich),
  [Abstrich](https://de.wiktionary.org/wiki/Abstrich)).
- **Schwellzug** = das druckabhängig an- und abschwellende Schriftbild der
  elastischen Spitzfeder: dünne Aufstriche, dicke Abstriche
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder),
  [Englische Schreibschrift](https://de.wikipedia.org/wiki/Englische_Schreibschrift)).
- **Gleichzug** = gleichbleibende Strichstärke ohne Druckwechsel
  ([Wikipedia: Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift)).
- **Absetzen** = Abheben des Schreibgeräts vom Papier („ohne abzusetzen
  schreiben", [Wiktionary: absetzen](https://de.wiktionary.org/wiki/absetzen));
  im Projekt: der Pen-Lift zwischen zwei Strichen eines Duktus.
- **Duktus** (Duden-Schreibung mit k): „charakteristische Art, bestimmte
  Linienführung einer Schrift"
  ([Duden: Duktus](https://www.duden.de/rechtschreibung/Duktus)); im
  engeren paläographischen Sinn — so verwendet das Projekt den Begriff —
  die Strichfolge und -richtung beim Schreiben. Code-Identifier bleibt
  `ductus` ([Sprachregelung §2](../reference/sprachregelung.md)).

## 4. Federtypen

- **Spitzfeder:** elastisch, Strichstärke kommt aus dem **Druck**
  (Schwellzug), nicht aus der Richtung
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
- **Bandzugfeder (Breitfeder):** breite, flache Schreibkante; Strichstärke
  variiert **richtungsabhängig** (Winkel Federkante↔Schreibrichtung),
  Maximum = Federbreite
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
- **Gleichzugfeder / Kugelspitzfeder** (Friedrich Soennecken): kugeliger
  Kopf, gleichbleibende Strichstärke unabhängig von Druck und Richtung
  ([Wikipedia: Schreibfeder](https://de.wikipedia.org/wiki/Schreibfeder)).
- **Redisfeder** (Schnurzugfeder): Plattenfeder mit runder Schreibplatte
  (0,5–5 mm); funktional eine Gleichzugfeder, aber nicht identisch mit der
  Kugelspitzfeder
  ([Wikipedia: Redisfeder](https://de.wikipedia.org/wiki/Redisfeder)).
- **Federwinkel** = Winkel der Federkante zur Schreiblinie (relevant bei
  der Bandzugfeder); davon zu unterscheiden ist der Anstellwinkel des
  Halters zur Schreibfläche
  ([Wikipedia: Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift)
  nennt für die Offenbacher 15–20° zur Grundlinie).

## 5. Die drei Startschriften im Überblick

| | Kurrent (um 1900) | Sütterlin (1911) | Offenbacher (1927) |
|---|---|---|---|
| Schräglage | 60–70° (Süß 2002)¹ | 90° (senkrecht) | 75–80° |
| Lineatur | 2:1:2 | 1:1:1 | 2:3:2 (auch 3:4:3) |
| Feder | Spitzfeder | Gleichzugfeder (Kugelspitz-/Redisfeder) | Bandzugfeder, 15–20° |
| Strichprinzip | Schwellzug (Druck) | Gleichzug | richtungsabhängiger Bandzug |

¹ Wikipedia nennt im Offenbacher-Vergleich ~70° für die klassische
Kurrent; Details und die abweichende Messung der Loth-Tafel 1866 (~50°)
in [kurrent.md](kurrent.md). Übrige Werte:
[Wikipedia: Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift),
[Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift).

## 6. Kurzchronologie

- **13.–16. Jh.:** Gotische Kursive als Gebrauchsschrift; über die
  (Kanzlei-)Bastarda entsteht im **frühen 16. Jh.** die deutsche Kurrent
  ([adfontes UZH](https://www.adfontes.uzh.ch/tutorium/schriften-lesen/schriftgeschichte/bastarda-und-gotische-kursive),
  [Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- **1714:** Preußen führt mit den Vorlagen von Hilmar Curas erstmals eine
  Normschrift für den Schreibunterricht ein
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- **19. Jh.:** Die metallene Spitzfeder macht die Kurrent schräger, „bis
  hin zu 45 Grad"
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift));
  Schulvorschriften streuen stark — Heinrigs (Preußen 1809) 45°, Bayern
  1852 „nicht geringer als 75°"
  ([Schulmuseum Ottweiler](https://schulmuseum-ottweiler.net/magazin/buchstabentabellen-vorschriften-und-musterbuecher)).
- **Um 1900:** Lineatur 2:1:2, Schräglage 60–70° (Süß 2002, S. 7/11 —
  bibliographisch).
- **1911:** Ludwig Sütterlin entwirft im preußischen Auftrag seine
  Ausgangsschriften; Einführung ab 1915
  ([Wikipedia: Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift)).
- **1927:** Rudolf Koch entwirft die Offenbacher Schrift
  ([Wikipedia: Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift)).
- **1935:** Eine modifizierte Sütterlin wird als „Deutsche Volksschrift"
  Bestandteil des Schulunterrichts
  ([Wikipedia: Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift)).
- **1941:** Zwei Vorgänge, oft vermischt: der **Normalschrifterlass vom
  3. Januar 1941** beendet die gebrochenen **Druck**schriften
  („Schwabacher Judenlettern" als absurde Begründung); ein Rundschreiben
  vom **1. September 1941** untersagt das Lehren der Kurrent in der
  Schule, ab Schuljahr 1941/42 gilt die lateinische „Deutsche
  Normalschrift"
  ([Wikipedia: Normalschrifterlass](https://de.wikipedia.org/wiki/Normalschrifterlass),
  [Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift)).
- **Nach 1945:** Ab 1954 in einigen Bundesländern wieder Zusatzschrift,
  ohne dauerhaften Erfolg; Bayern nutzt 1950–1955 die
  Koch-Hermersdorf-Variante der Offenbacher als Zweitschrift
  ([Wikipedia: Normalschrifterlass](https://de.wikipedia.org/wiki/Normalschrifterlass),
  [Offenbacher Schrift](https://de.wikipedia.org/wiki/Offenbacher_Schrift)).

## 7. Österreich · Schweiz · Liechtenstein

Die Kurrent war die Schrift des gesamten deutschen Sprachraums — ihr Ende
verlief aber je Land völlig unterschiedlich.

**Österreich**

- Kurrent war als „Amts- und Protokollschrift" etabliert und wurde **bis
  zum Schuljahr 1938/39 als Erstschrift** der Volksschule gelehrt — die
  traditionelle Kurrent, **nicht** die deutsche Sütterlinschrift
  ([Wikipedia: Ausgangsschrift](https://de.wikipedia.org/wiki/Ausgangsschrift),
  [Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- Eigene Normierungen: älteste gesamtösterreichische Schulschrift 1775
  (Felbiger, unter Maria Theresia), Vereinheitlichung 1832, „Richtformen
  1924" des Stadtschulrats für Wien
  ([Wikipedia: Ausgangsschrift](https://de.wikipedia.org/wiki/Ausgangsschrift)).
- Nach dem „Anschluss" 1938 traf Österreich die reichsweite Abschaffung
  durch die „Deutsche Normalschrift" 1941
  ([Wikipedia: Ausgangsschrift](https://de.wikipedia.org/wiki/Ausgangsschrift)).
- **Comeback als Zweitschrift:** Per Erlass vom 22. Mai 1951 wurde die
  Kurrent als Zweitschrift (Schönschreiben) wieder eingeführt, aber nur
  selten praktiziert; Erstschrift blieb die lateinische Österreichische
  Schulschrift (Neunormierungen 1969 und 1995)
  ([Wikipedia: Ausgangsschrift](https://de.wikipedia.org/wiki/Ausgangsschrift)).
- Die **Steilschrift-Bewegung** der 1890er argumentierte im ganzen
  deutschen Sprachraum schulhygienisch gegen die Schrägschrift (Skoliose,
  Kurzsichtigkeit); in Karlsruhe z. B. 1892 eingeführt und 1906 wieder
  abgeschafft
  ([Stadtarchiv Karlsruhe](https://stadtgeschichte.karlsruhe.de/stadtarchiv/blick-in-die-geschichte/ausgaben/blick-126/blickpunkt-steilschrift)).

**Schweiz**

- Kurrent war nur **bis Anfang des 20. Jahrhunderts** Verkehrs-, Amts-
  und Protokollschrift — deutlich kürzer als in Deutschland/Österreich
  ([Wikipedia: Deutsche Kurrentschrift](https://de.wikipedia.org/wiki/Deutsche_Kurrentschrift)).
- Kein Verbot, sondern **kantonale Schulbeschlüsse zwischen 1890 und
  1930**
  ([Zentralbibliothek Zürich, Arbeitsblatt](https://www.zb.uzh.ch/storage/app/media/ueber-uns/Citizen-Science/Schulzeitreisen/20210621_Keine_Angst_vor_alten_Schriften/Arbeitsblatt.pdf)).
  **Quellen-Spannung:** das Staatsarchiv Graubünden nennt Kurrent dort
  noch „bis in die 1940er Jahre" Schulstoff
  ([gr.ch](https://www.gr.ch/DE/institutionen/verwaltung/ekud/afk/sag/dokumentation/digitaleVitrine/Seiten/DeutscheKurrentschrift.aspx)) —
  nicht aufgelöst.
- Sütterlin war eine preußisch-deutsche Schulschrift; eine Einführung in
  der Schweiz ist in den Standardquellen nicht belegt
  ([Wikipedia: Sütterlinschrift](https://de.wikipedia.org/wiki/S%C3%BCtterlinschrift)).
- Nachfolger: die Hulligerschrift (Basel 1926) wurde 1936 als **Schweizer
  Schulschrift** („Schnüerlischrift") von zehn Kantonen übernommen, 1947
  revidiert; seit 2014 löst die **Basisschrift** sie ab
  ([Wikipedia: Schweizer Schulschrift](https://de.wikipedia.org/wiki/Schweizer_Schulschrift),
  [swissinfo.ch](https://www.swissinfo.ch/ger/kultur/schoen-schreiben-als-relikt-einer-gesellschaftskultur/28325768)).
- Druck-Besonderheit: Schweizer Zeitungen hielten die **Fraktur** länger
  als Deutschland — bis Ende der 1940er Jahre
  ([Wikipedia: Antiqua-Fraktur-Streit](https://de.wikipedia.org/wiki/Antiqua-Fraktur-Streit)).

**Liechtenstein**

- Im Alltag dominierte die Kurrent bis ins 20. Jahrhundert; an den
  Schulen wurde seit dem frühen 20. Jh. daneben die lateinische Schrift
  gelehrt, die u. a. durch den **Zollvertrag mit der Schweiz (1923)** an
  Bedeutung gewann — die **Schulkonferenz beschloss 1935 die komplette
  Umstellung** (also vor dem deutschen Erlass, ohne Verbot); 1962 wurde
  die Schweizer Schulschrift eingeführt
  ([Historisches Lexikon Liechtenstein: Schrift](https://historisches-lexikon.li/Schrift)).

**Nicht belastbar belegt** (bewusst ausgelassen): ein konkreter
österreichischer Steilschrift-Erlass der 1890er; die Schulschrift-Praxis
in Österreich 1938–1941; Südtirol und Luxemburg (für Südtirol ist nur das
Verbot des deutschsprachigen Unterrichts ab 1923 belegt, nicht die
Schriftfrage selbst).

## Literatur (bibliographisch, nicht im Repo)

- Harald Süß: *Deutsche Schreibschrift. Lesen und Schreiben lernen.*
  Augsburg 2002 — Referenz-Lehrbuch; Werte daraus sind im Text als
  „(Süß 2002)" gekennzeichnet.
- Rudolf Koch: *Die Offenbacher Schrift.* Berlin 1928 — gemeinfrei, Scan
  auf [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Rudolf_Koch_Die_Offenbacher_Schrift_1928.pdf).
