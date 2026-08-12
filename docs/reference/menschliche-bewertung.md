# Menschliche Bewertung — der blinde Urteilsdurchgang über die Fits

> **Status (2026-08-09): lebend.** Beschreibt das Instrument
> ([`tools/humanbench`](../../tools/humanbench)) und das Verfahren eines
> Bewertungsdurchgangs — die Methode, nicht die Ergebnisse. Nachzuziehen bei
> jeder Änderung am Instrument (Kategorien, Stichproben- und
> Wiederholungsregeln, Darstellung, neue Modi in
> `tools/humanbench/build.py` bzw. `page.py`) und bei jeder Runde, deren
> Aufbau von dem hier beschriebenen abweicht.

Diese Datei existiert, damit eine Wiederholung ein **Nachbau** ist und keine
Neuplanung. Jede Regel hier hat eine Runde gekostet; sie steht mit ihrer
Begründung da, weil eine Regel ohne ihren Fehlerfall das Erste ist, was eine
spätere Überarbeitung als Ballast entfernt.

Die **Befunde** eines Durchgangs gehören nicht hierher, sondern in
[`qualitaetsmetrik.md`](qualitaetsmetrik.md) §9 — dort stehen die Metriken,
gegen die die Urteile gehalten werden. Hier steht nur, wie die Urteile
zustande kommen.

---

## 1. Wozu ein Mensch urteilt

Alle Kennzahlen des Projekts messen **Geometrie**: `geo_rmse` und
`cov_rmse_local` messen Abstände zwischen Kurven, `anchor_spike_ratio` misst
einen Schritt gegen seine Nachbarn, `gen_chamfer` misst eine Punktwolke gegen
eine andere. Keine davon misst **Wahrnehmung**. Ob eine Abweichung stört, ob
sie als Fehler gelesen wird oder als Eigenart der Hand, ist eine Frage, die
nur ein Mensch beantworten kann.

Der Durchgang beantwortet deshalb genau eine Frage:

> **Welche Fehlerart sieht welche Kennzahl überhaupt?**

Ausgabe ist eine **Abdeckungsmatrix**: je Kategorie × je Kennzahl eine AUC
gegen „Kategorie gesetzt / nicht gesetzt“ (AUC = die Wahrscheinlichkeit, dass
die Kennzahl ein zufälliges Vorkommen *mit* der Fehlerart höher bewertet als
eines *ohne*; 0,5 = blind, 1,0 = perfekte Trennung), und daneben, in derselben
Zeile, die Schranke, die die Verlässlichkeit des Labels selbst setzt (§3).

Ein zweiter Ertrag fällt kostenlos an und ist oft der
entscheidungsrelevanteste: die **Validierung eines bereits ausgelieferten
Gates** gegen die menschlichen Urteile — wirft es Vorkommen weg, die ein
Mensch behalten würde, oder behält es welche, die er verworfen hätte?

### Was er ausdrücklich NICHT liefert

* **Keine Schwellwerte.** Bei 10–15 Positiven je Kategorie liegt der
  Standardfehler einer AUC bei ≈ 0,09. Zwei Kennzahlen, die sich um 0,04
  unterscheiden, sind auf diesen Daten nicht unterscheidbar; die Frage lautet
  „sichtbar überhaupt?“ (deutlich über ~0,7), nicht „welcher Schnitt ist
  optimal?“.
* **Keinen Trainingsdatensatz.** Ein auf 150 Bildern gebauter Detektor wäre
  auf genau den Labels bestätigt, aus denen er stammt. Dagegen steht die
  Rückhaltemenge (§3), und selbst mit ihr bleibt die Stichprobe klein.
* **Keine Skala „wie gut sind die Fits“.** Gemessen wird die *Sichtbarkeit von
  Fehlerarten*, nicht eine Gesamtnote. Prävalenzen aus einer Runde gelten für
  den Satz, aus dem sie gezogen wurden (§9).

---

## 2. Die Fehler-Taxonomie

Die sechs Kategorien plus ein Modifikator. Sie haben drei Runden Nachschärfen
gekostet und sind das haltbarste Ergebnis des Verfahrens: Sie sind die
Schnittstelle zwischen Auge und Zahl, und jede spätere Kennzahl wird gegen sie
gebaut. Im Code liegen sie in `tools/humanbench/page.py::CATEGORIES`
(Kürzel, Taste, Beschriftung, Art).

Drei Arten bestimmen das Verhalten: `solo` beantwortet die Frage allein
(eine Auswahl löscht die Fehlerarten), `finding` **addiert sich** (mehrere
Fehlerarten pro Bild sind erlaubt und häufig), `modifier` kombiniert mit
allem, auch mit einer Solo-Wahl.

**Was beurteilt wird:** die gezeichnete **Mittellinie** gegen die Tinte
**ihres eigenen** Buchstabens. Nachbartinte im Fenster ist normal und wird
ignoriert. Die Strichbreite (Schwellzug, `half_widths`) wird nicht dargestellt
und daher nicht beurteilt (§9).

| Kürzel | Taste | Beschriftung | Art |
|---|---|---|---|
| `G` | 1 | Gut | solo |
| `A` | 2 | Einzelner Ausreißer | finding |
| `W` | 3 | Gewackel | finding |
| `B` | 4 | Bereich daneben | finding |
| `E` | 5 | Knick nur am Rand | finding |
| `K` | 6 | Komplett daneben — nicht bewertbar | solo |
| `U` | 7 | Unsicher | modifier |

### `G` — Gut

**Definition:** Die Linie folgt der Tinte über die ganze Kette; es gibt keine
Stelle, die man markieren würde.
**Erkennungsmerkmal:** Kein Abschnitt der Linie liegt sichtbar neben dem
Strich, auf dem er liegen soll.
**Abgrenzung:** `G` ist solo — sobald eine Fehlerart zutrifft, ist `G` falsch.
Wer zögert, setzt die Fehlerart **plus `U`**, nicht `G`. Daraus folgt die
billigste Probe darauf, dass die Regel verstanden wurde: In der Auswertung
darf `G` **nie** gemeinsam mit einer Fehlerart auftauchen.

**Wo die Messlatte liegt — und wo nicht** (Kalibrierung des Autors, 2026-08-09):
`G` heißt **„der Buchstabe ist sauber zu erkennen"**, nicht „schreibperfekt".
Das ist die Latte der aktuellen Stufe: erst muss ALLES auf dieses Niveau, als
Basis. Eine `G`-Quote ist deshalb eine Aussage über *Lesbarkeit*, nicht über
Schreibqualität — „47 % gut" bedeutet „47 % sauber erkennbar" und darf nie als
„47 % fertig" zitiert werden.

Ein Versuch, diese Einschränkung als Modifikator festhaltbar zu machen
(erst „ginge besser", dann „nicht als Laufform-Vorlage"), ist **verworfen**:
Bei jedem Bild mit einem Mangel ist die Antwort ohnehin gesetzt — die Ernte
hält solche Fits längst heraus —, das Merkmal trägt also nur auf den
`G`-Bildern etwas und bedeutet je nach Begleitkategorie etwas anderes. Ein
zweideutig gesetztes Label kostet mehr, als eine fehlende Spalte einbringt.
Die Deckenfrage bleibt damit dort, wo sie hingehört: beim paarigen Vergleich
(§8), wo es einen Bezugspunkt gibt.

### `A` — Einzelner Ausreißer

**Definition:** Genau eine Stelle springt aus der Kette heraus. Ein Anker
(oder zwei, drei) steht neben der Tinte, während seine unmittelbaren Nachbarn
korrekt sitzen; die Linie macht dort eine Zacke, einen Haken oder eine kleine
Schlaufe.
**Erkennungsmerkmal:** Der Fehler ist ein **Punkt**. Deckt man ihn mit dem
Daumen ab, ist der Buchstabe in Ordnung.
**Abgrenzung:** gegen `W` die **Anzahl** (eine Stelle vs. durchgehende
Unruhe), gegen `B` die **Ausdehnung** (Punkt vs. ganzer Abschnitt), gegen `E`
der **Ort** (mitten im Strich vs. im allerersten/letzten Stück).

### `W` — Gewackel

**Definition:** Die Linie folgt der Tinte im Groben, zittert aber um ihren
Sollverlauf — mehrere kleine Ausschläge nach beiden Seiten über eine längere
Strecke; oder eine Rundung läuft als Vieleck statt als Bogen.
**Erkennungsmerkmal:** Kein einzelner Übeltäter, sondern **Unruhe**; die Linie
ist „haarig“ statt glatt.
**Abgrenzung:** gegen `A` (dort *eine* Stelle), gegen `B` (dort ein Abschnitt,
der für sich glatt ist und nur am falschen Ort sitzt).
**Bekannte Unschärfe:** `W` trug im ersten Durchgang zwei verschiedene Dinge —
das Zittern und die **eckig gelaufene kleine Schleife** („der Kringel ist eher
ein Quadrat als ein Kreis“). Beide gehören getrennt, weil sie verschiedene
Ursachen haben; dafür ist eine eigene Kategorie `R` („rund → eckig“)
vorgesehen. Solange sie nicht existiert, gehört die eckige Schleife nach `W`.

### `B` — Bereich daneben

**Definition:** Ein **zusammenhängendes Stück** der Kette liegt neben seiner
Tinte: ein Bogen ist abgeschnitten, ein Abstrich läuft parallel neben dem
Strich, eine Schleife sitzt zu hoch. Die Form dieses Stücks ist für sich
plausibel, sie sitzt nur am falschen Ort.
**Erkennungsmerkmal:** Über mehrere Anker hinweg bleibt ein Stück Tinte
unbedeckt **und** liegt ein Stück Linie auf leerem Papier.
**Abgrenzung:** gegen `A` die Ausdehnung, gegen `W` die **Glätte** (`B`
wackelt nicht, es sitzt daneben), gegen `K` der **Rest** (bei `B` stimmt der
übrige Buchstabe).

### `E` — Knick nur am Rand

**Definition:** Die Beanstandung sitzt **ausschließlich** im allerersten oder
allerletzten Stück der Ankerkette; dazwischen ist nichts zu bemängeln.
**Erkennungsmerkmal:** Der Fehler **berührt ein Kettenende**. Typisch: der Fit
beginnt zu spät oder endet zu früh, das erste bzw. letzte Stück Tinte bleibt
unbedeckt, und ein kurzer Knick ist der sichtbare Rest davon.
**Abgrenzung:** Definierend ist der **Ort, nicht die Form** — ein gleich
aussehender Knick mitten im Strich ist `A` oder `W`, nie `E`.
**Warum eine eigene Kategorie:** Am Kettenende läuft die Vorlage über die
Tinte hinaus (oder die Tinte über die Vorlage), es ist also womöglich gar
nichts mehr da, woran zu fitten wäre. Das ist eine andere Ursache als ein
Ausreißer mittendrin, wo Tinte existiert und der Fit sie trotzdem verlässt.
Wären beide eine Kategorie, mittelte die Auswertung zwei Krankheiten zu einer
Zahl.

### `K` — Komplett daneben, nicht bewertbar

**Definition:** Der Fit gehört nicht zu diesem Buchstaben — als Ganzes
verschoben, auf dem Nachbarn gelandet, oder so entstellt, dass sich die Frage
nach der Fehlerart nicht mehr stellt.
**Erkennungsmerkmal:** Es gibt nichts zu markieren, weil nichts stimmt.
**Abgrenzung:** gegen `B` — dort stimmt der Rest des Buchstabens.
**Sonderstellung:** `K` ist **kein Schweregrad, sondern ein Ausschluss**.
Solche Vorkommen fliegen aus der Bewertung aller anderen Kategorien: Ein
Totalausfall wäre sonst in jeder Kategorie ein Positiv und höbe jede AUC,
ohne dass irgendeine Kennzahl irgendetwas Spezifisches gesehen hätte.

### `U` — Unsicher (Modifikator)

**Definition:** Das Urteil steht, aber der Beurteiler steht nicht dafür ein.
Kombinierbar mit jeder Wahl, auch mit `G` und `K`.
**Zweck:** Das Zögern soll nicht als Kategorie-Rauschen enden. In der
Auswertung wird **zweimal gerechnet**, einmal mit und einmal ohne die
`U`-Urteile; weichen die Zahlen auseinander, ist das ein Befund über die
Kategorie, nicht über die Kennzahl.

### Der Marker

Zusätzlich zur Kategorie markiert der Beurteiler **eine** Stelle im Bild — die
auffälligste, nicht alle. Ein Klick woanders verschiebt sie, ein Klick auf sie
löscht sie. Die Auswerteregeln dazu stehen in §3, weil sie
Konstruktionsentscheidungen sind und keine Kategorienfrage.

---

## 3. Die Konstruktionsregeln des Instruments

Jede Regel mit ihrer Begründung. Wer eine davon fallen lässt, misst etwas
anderes als die vorige Runde — dann ist der Vergleich hin, auch wenn die
Zahlen weiter vergleichbar aussehen.

### 3.1 Geschichtete Stichprobe — **mit Mischen innerhalb der Bänder**

Die Vorkommen werden nach Schwere sortiert (Abstand des Fits zur eigenen
Tinte), in `--bands` Bänder geschnitten und **reihum** aus den Bändern
ausgeteilt (`build.py::stratify`). Damit deckt **jeder Präfix** der Sequenz
die ganze Bandbreite ab — nötig, weil ein Beurteiler, der vorzeitig abbricht,
trotzdem eine repräsentative Stichprobe hinterlassen muss.

Reihum allein reicht **nicht**. Im ersten Entwurf blieb die Reihenfolge
*innerhalb* eines Bandes nach Schwere sortiert, und ein 150er-Präfix erreichte
die Ränge 0–215 von 245: die saubersten Fälle waren **unerreichbar**. Genau
dort leben aber die Fehlalarme jeder Kennzahl — ohne sie kann man einen
Detektor nicht von einem unterscheiden, der alles für einen Fehler hält. Das
Mischen innerhalb des Bandes ist gesät (`--seed`), die Runde bleibt also exakt
reproduzierbar.

Der Builder druckt die Gegenprobe („prefix check — first 100 span ranks …“);
sie ist zu lesen, **bevor** eine Seite gebaut wird.

### 3.2 Blinde Wiederholungen als Verlässlichkeitsschranke

Ein Teil der Bildschirme zeigt ein bereits gezeigtes Vorkommen ein zweites Mal
(`build.py::pick_repeats`). Ohne sie ist eine niedrige AUC nicht von
**Labelrauschen** zu unterscheiden: Stimmt der Beurteiler mit sich selbst in
einer Kategorie nur in 6 von 12 Fällen überein, kommt auch ein *perfekter*
Detektor für sie nicht wesentlich darüber hinaus — und die Aussage „unsere
Kennzahl ist blind für X“ wäre **unfalsifizierbar**. Deshalb wird jede AUC mit
dieser Schranke berichtet, und unterhalb einer vorher festgelegten
Übereinstimmung wird für die Kategorie *keine* Blindheit behauptet.

Drei Bedingungen, jede damit die Wiederholung **neu beurteilt** und nicht
erinnert wird:

* nur aus Glyphen mit mindestens `REPEAT_MIN_GLYPH_COUNT` Vorkommen — ein
  Buchstabe, der nur einmal auftaucht, ist für sich einprägsam;
* nie aus `--repeat-exclude` (voreingestellt das große `S`, der bekannt
  kaputte Buchstabe des Projekts: ihn zu wiederholen misst Erinnerung, nicht
  Urteil);
* mindestens `--min-repeat-gap` Bildschirme später, plus Zufallsversatz
  (`REPEAT_JITTER`), damit die Wiederholungen kein Rhythmus sind, den man zu
  antizipieren beginnt.

Die tatsächlich erreichten Abstände werden berichtet, und wenn zu wenige
Wiederholungen platziert werden konnten, warnt der Builder laut — eine Runde,
die still ohne sie läuft, liefert Zahlen ohne Schranke, und genau so wird aus
einem Rauschartefakt ein „Befund“.

**Lehre aus der ersten Runde:** Zufällig gezogene Wiederholungen messen die
Verlässlichkeit **seltener** Kategorien nicht. Bei 10 % Prävalenz enthalten 12
Paare je etwa ein Ja; die Übereinstimmung kommt dann fast ganz aus Einigkeit
über die Neins und sagt über die Kategorie nichts. Wiederholungen sind deshalb
**nach Kategorie zu schichten** (mindestens drei positive Paare je Kategorie,
gezielt aus den bekannten Fällen der Vorrunde), was mehr Wiederholungen
braucht als die voreingestellten 12.

> **Offen — das Werkzeug kann diese Lehre noch nicht ausführen.**
> `build.py::pick_repeats` zieht nach Häufigkeit und Band, nicht nach
> Kategorie; die Labels der Vorrunde gehen gar nicht erst hinein. Die
> Auswertung *überwacht* die Regel bereits
> (`analyse.py::MIN_REPEAT_POSITIVES` = 3 warnt je Kategorie, deren
> Wiederholungspaare sie nie getragen haben) — sie greift also erst, wenn die
> Stunden schon ausgegeben sind. Wer den nächsten **Kategorien**-Durchgang
> fährt, baut die Schichtung vorher ein (Vorrunden-Urteile + schmaler
> Schlüssel als Eingabe, Auswahl deckend über die Kategorien), sonst
> wiederholt die Runde exakt die Messung, die beim ersten Mal nichts ergeben
> hat. Für den **paarigen** Durchgang (§8) ist das nicht nötig: dort misst
> die Wiederholung die Seitenneigung, nicht eine Kategorie.

### 3.3 Rückhaltemenge

`--n-label` bestimmt, wie viele Vorkommen beurteilt werden; der Rest wandert
als **Reserve** nach `reserve.json` und wird **nicht gelabelt**. Sie ist durch
die Austeilung bandbalanciert und damit ein brauchbarer Bestätigungssatz.

Grund: Eine Kennzahl, die gebaut wird, um zu sehen, was dieser Durchgang
gefunden hat, wäre sonst auf denselben Labels abgestimmt **und** bestätigt —
also gar nicht bestätigt. Regel: **entwickeln auf dem gelabelten Satz,
bestätigen auf der Reserve.** Ohne diesen zweiten Durchgang gilt eine neue
Kennzahl als unbestätigt und darf keine Entscheidung tragen.

Der Bestätigungsdurchgang wird nicht neu gewürfelt, sondern **auf genau diese
Vorkommen eingeschränkt**: `--only <reserve.json>` (auch der schmale
Schlüssel einer Runde tut es) beschränkt die Grundgesamtheit auf die dort
genannten Identitäten, und zwar **vor** der Schwere-Sortierung — die Bänder
werden also über den Satz geschnitten, der wirklich beurteilt wird, statt über
einen mit Löchern in den Rängen. Ohne dieses Flag zieht ein zweiter Bau mit
neuer Saat eine frische Mischung aus gelabelten **und** zurückgehaltenen
Vorkommen, und die Rückhaltemenge ist als Bestätigungssatz verbraucht.

### 3.4 Proportionaler Rand um den Ausschnitt

Der Ausschnitt folgt der gezeichneten Linie und wird um einen Anteil der
**x-Höhe** gepolstert (`--pad-xh`, `build.py::crop_window`), nicht um eine
feste Pixelzahl. Ein fester Rand (im ersten Entwurf 8 px) versteckt den Beleg
genau dort, wo er gebraucht wird: Die schlimmsten Abweichungen reichen an eine
Drittel-x-Höhe, die Tinte, auf der die Linie hätte liegen sollen, kann also
außerhalb des Bildes liegen. Der Beurteiler würde dann gefragt, was der Fit
verfehlt hat, und bekäme weder den Fehlgriff noch das Ziel zu sehen.

Nebenwirkung, die deshalb im Kopftext der Seite steht: Bei völlig
danebenliegenden Fits folgt der Ausschnitt dem **Fit** — der Buchstabe kann
angeschnitten sein.

### 3.5 Kartografisches Casing

Linie und Marker bekommen einen hellen Saum (die kartografische Technik, eine
Signatur mit Kontrastsaum auf jedem Untergrund lesbar zu halten). In fast
schwarzer Tinte ist eine dunkle Linie unsichtbar; ohne Saum sähe man nur die
Stellen, an denen die Linie die Tinte **verlässt**, und jedes Wackel-Urteil
wäre heimlich ein Urteil über das Verlassen der Tinte.

### 3.6 Absetzer werden als Absetzer gezeichnet

Die Polylinie wird an jedem Federheber getrennt
(`build.py::polyline_strokes`). Ein Absetzen ist keine Linie: überbrückt
gezeichnet, zeigt die Seite einen Strich, den die Hand nie gemacht hat. Der
Beurteiler meldete dann völlig zu Recht einen Fehler, den der Fit gar nicht
hat — das Instrument produzierte seine eigenen Befunde.

Die Absetz-Indizes kommen aus den Vorlagen, und deren Einzelabruf ist
**admin-gegatet**: ohne `ADMIN_TOKEN` löst der Bau *keinen einzigen* auf und
zeichnet jeden mehrstrichigen Buchstaben überbrückt — lautlos, denn eine
einstrichige Glyphe sieht genauso aus. Der Builder zählt deshalb die Glyphen
ohne Absetz-Angabe und **warnt namentlich**; diese Warnung ist ein Abbruch
und keine Randnotiz.

### 3.6a Der Buchstabe wird IN seinem Federweg gezeigt

Die teuerste Regel des Dokuments, weil sie erst nach Runde 1 dazukam und deren
Hauptbefund gekostet hat.

Die Ernte fittet ein ganzes Wort als **eine Kette**
(`harvest.py::_harvest_case_chain`, „one solve per run of joined slots"); die
Verbindungsstücke gehören zu deren Connector-Segmenten und stehen **nicht** in
den Ankern eines Buchstabens. Runde 1 zeichnete nur diese Anker. Jeder
verbundene Buchstabe endete dadurch auf dem Bildschirm in der Luft, obwohl der
Fit weiterlief — und der Beurteiler meldete, korrekt für das Gezeigte, bei 23 %
der Bilder einen fehlenden Anstrich. Nachgemessen liegt die Tinte jenseits des
Buchstabens 0,25 xh von der gezeichneten Linie, aber 0,02 xh vom gespeicherten
Federweg.

`build.py::word_trace_context` holt deshalb die Wort-Traces und
`context_strokes` legt sie **unter** die Urteilslinie: dünn, grau, gestrichelt,
ohne Casing — sichtbar als Zusammenhang, niemals verwechselbar mit der Linie,
über die geurteilt wird. Fehlen die Traces, warnt der Bau ausdrücklich.

Die Lehre ist allgemeiner als der Fall: **was gezeigt wird, muss deckungsgleich
sein mit dem, worüber geurteilt werden soll.** Zeigt das Blatt weniger als der
Fit enthält, erzeugt der Durchgang Befunde über die Zeichnung und nennt sie
Befunde über das Modell.

Und die Gegenprobe gehört dazu: die naheliegende Folgerung „dann waren die
Meldungen ein Artefakt" ist ihrerseits falsch. Dieselbe ungezeichnete Tinte
liegt auf den als **gut** gelabelten Bildern, dort sogar weiter weg. Was die
Meldungen wirklich trafen, war die **Naht** zwischen Buchstabe und Verbindung.
Eine These, die einen Befund wegerklärt, muss auch erklären, warum sie die
Nicht-Befunde nicht wegerklärt.

### 3.7 Ein Marker je Bild — und ein fehlender Marker ist kein Datum

Der Marker ist der einzige Teil des Urteils, der **unabhängig von der eigenen
Rechnung** ist: Eine Ortsaussage, die aus dem selbst berechneten Maximum
stammt, ist zirkulär und belegt nichts. Gerade deshalb ist er streng
auszuwerten. Zwei Regeln, vorab festgelegt:

* **Nicht markiert heißt „nicht markiert“** — nie „dort ist kein Fehler“.
  Ungesetzte Marker werden weggelassen, nie als Negativbeleg gezählt. Die
  **Markerquote wird mitberichtet**: sinkt sie über die Sequenz, ist das
  Ermüdung des Beurteilers und keine Aussage über die Bilder.
* **Bei mehreren gesetzten Kategorien** ist nicht entscheidbar, welcher von
  ihnen der eine Punkt gilt. Solche Bilder zählen nur in die Gesamtfrage
  („liegt der Punkt an einer Strichgrenze?“), nie in die Ortsprüfung *je
  Kategorie* — und deren Fallzahl gehört vor das Ergebnis, denn sie kann zu
  klein sein. (Ein Tastendruck, der den Marker einer Kategorie zuordnet,
  rettet diese Bilder; er ist für die nächste Runde vorgesehen.)

Die Koordinaten stehen im Panel-Pixelrahmen (gezoomte Crop-Pixel) und werden
in der Auswertung über den Schlüssel auf Ankerindex bzw. Strichgrenze
zurückgerechnet.

### 3.8 Nichts Identifizierendes im Payload

Glyph, Vorlagenwort, Slot, Schweregrad, Schnappschuss stehen im `key.json` —
**nie** im Payload. Die Seite zeichnet Geometrie und sonst nichts, also kann
sie die Antwort auch im Quelltext nicht verraten. Im paarigen Modus (§8) ist
das die Voraussetzung überhaupt; im Kategorien-Modus ist es die Zusicherung,
dass der bekannte Problembuchstabe nicht strenger beurteilt wird als der Rest.

### 3.9 Zeitnahme je Urteil

Die Seite misst die Zeit pro Bild, und die Uhr läuft **nur bei sichtbarer
Seite**. Ermüdung und Drift werden damit gemessen statt wegangenommen; eine
Kaffeepause mitten im Bild darf nicht als langsames Urteil in die Statistik
gehen.

**Nicht rundenübergreifend vergleichbar:** Runde 01 maß etwas anderes — den
Abstand zwischen zwei Weiterklicks, Pausen eingeschlossen (daher dort der
Ausreißer `@1320s`). Die Sekunden einer Runde sind gegen die einer anderen
also nur zu halten, wenn beide dieselbe Uhr benutzt haben; die Drift
*innerhalb* einer Runde bleibt in beiden Fassungen aussagekräftig.

### 3.10 Wiederaufnahme

Der Zustand wird nach jedem Schritt gespeichert und beim Laden
wiederhergestellt, geschlüsselt über einen Fingerabdruck des Payloads (eine
andere Runde setzt also nie auf altem Zustand auf). Der gesamte Aufwand des
Instruments ist menschliche Geduld; sie an einen Tab-Absturz bei Bild 130 zu
verlieren, ist der teuerste denkbare Fehler.

Daraus folgt eine Regel, die eine Runde gekostet hat: **alles, woraus der
Ergebnistext gebaut wird, muss gespeichert werden.** Die Seite der Runde 01
schrieb `{at, seen, notes, stamps, picks}` und *las* beim Laden `spots` —
ein Feld, das nie jemand geschrieben hatte. Ein einziges Neuladen hätte damit
sämtliche bis dahin gesetzten Ortsmarker verworfen, still, und ausgerechnet
die Marker sind der einzige von unserer eigenen Rechnung unabhängige Teil des
Urteils. Die Asymmetrie ist unsichtbar, solange der Tab offen bleibt — also
genau dann, wenn niemand hinschaut. Sie ist heute festgenagelt
(`tests/test_humanbench_page.py`: jedes Zustandsfeld muss in *beiden*
Richtungen vorkommen).

---

## 4. Die Vorregistrierung

**Der Auswerteplan wird geschrieben, bevor die Labels da sind.** Sonst passt
man hinterher die Auswertung an die Daten an — bei sechs Kategorien und acht
Kennzahlen findet sich immer eine Zelle, die etwas zeigt, und man weiß
hinterher nicht mehr, ob man sie gesucht oder gefunden hat.

Der Plan muss festlegen:

1. **Die Reihenfolge der Auswertung, Verlässlichkeit zuerst.** Sie ist
   Vorbedingung, nicht Beiwerk: Liegt die Selbst-Übereinstimmung einer
   Kategorie unter der vorher genannten Schranke, wird für sie **keine**
   Blindheit behauptet — dann ist das Label unscharf, nicht die Kennzahl.
2. **Die Ausschlüsse.** `K` fliegt aus der Bewertung aller anderen Kategorien;
   `U`-markierte Urteile werden zweimal gerechnet (mit und ohne).
3. **Die Mindestbesetzung.** Eine Kategorie mit weniger als der vorher
   genannten Zahl Positiver bekommt **„zu wenig Daten“** statt einer Zahl. Die
   erwarteten Besetzungen gehören mit in den Plan, damit eine dünne Zelle
   später nicht als Befund verkauft wird.
4. **Die Auflösung, die die Daten tragen.** Der Standardfehler der AUC bei der
   erwarteten Besetzung, ausdrücklich mit der Folge: Unterschiede darunter
   werden **nicht** neu verhandelt.
5. **Die falsifizierbaren Erwartungen.** Je Kategorie, welche Kennzahl sie
   sehen sollte und welche nicht. Ohne sie ist jedes Ergebnis bestätigend —
   und die interessanteste Zeile des ersten Durchgangs war eine
   **falsifizierte** Erwartung.
6. **Was ein Ergebnis auslösen darf.** Welche Zahl welchen Auftrag
   rechtfertigt, und die Auflage dazu: Eine neue Kennzahl wird auf dem
   gelabelten Satz entwickelt und auf der **Reserve** bestätigt; eine
   Änderung, die das Gerenderte betrifft, braucht zusätzlich ein A/B gegen die
   gemessene Tinte und die Freigabe des Autors.

Und die Regel, die den Plan überhaupt bindend macht:

> **Was nicht im Plan steht, ist eine nachträgliche Idee und wird als solche
> gekennzeichnet** — mit Datum und Anlass, als eigener Nachtrag, und ohne eine
> vorregistrierte Auswertung zu ersetzen.

Ein Nachtrag zwischen Planschluss und Labels ist zulässig (der erste Durchgang
hat genau einen), solange er als „NACH Planschluss, VOR den Labels“
ausgewiesen ist und seine eigene Erwartung mitbringt, an der er scheitern
kann. Ein Nachtrag *nach* den Labels ist keine Vorregistrierung mehr, sondern
eine Hypothese für die nächste Runde.

Der Plan gehört zur Runde und wird mit den Urteilen aufbewahrt (§6).

---

## 5. Ablauf einer Runde

### Schritt 0 — Frage und Plan

Festlegen, was die Runde beantworten soll: ein **Kategorien-Durchgang**
(`single`, „was stimmt hier nicht?“) oder ein **paariger Vergleich**
(`paired`, §8). Beim paarigen gehört die **Frage selbst** in die Festlegung —
„welche Linie folgt der Tinte besser?“ solange es eindeutige Fehler gibt,
„welche sieht echter geschrieben aus?“ erst danach; die beiden messen
Verschiedenes und ihre Runden sind nicht vergleichbar (§8). Dann den
Auswerteplan schreiben (§4). Der Plan darf nach dem Bauen entstehen — nie nach
dem Labeln.

### Schritt 1 — Bauen

```bash
uv run python -m tools.humanbench.build --round 2 --n-label 150 --repeats 12
```

Voreinstellung ist der Kategorien-Durchgang. Die Vorkommen kommen aus
`--instances <datei>` oder, ohne Datei, über die deployte Lese-API; die
Absetz-Indizes aus `--starts <datei>` oder aus den (admin-gegateten)
Vorlagen-Rows. Ein paariger Vergleich bringt seine beiden Schnappschüsse
selbst mit:

```bash
uv run python -m tools.humanbench.build --round 3 \
    --paired temp/fits-alt.json temp/fits-neu.json
```

Ein Bestätigungsdurchgang über die Rückhaltemenge einer früheren Runde
schränkt zusätzlich ein (§3.3):

```bash
uv run python -m tools.humanbench.build --round 4 \
    --only temp/humanbench/runde-2/reserve.json
```

Geschrieben wird nach `temp/humanbench/runde-<n>/`:

| Datei | Inhalt | archivierbar |
|---|---|---|
| `payload.json` | was die Seite zeichnet — Crop-Bild + Polylinien, sonst nichts | nein |
| `key.json` | was sie nicht wissen darf — Glyph, Wort, Slot, Schwere, Rang, im paarigen Modus die Seitenzuordnung | nein |
| `vorkommen.json` | der **schmale Schlüssel**: uid → Glyph, Wort, Slot, `repeat_of` — was ein Kürzel *meint*, ohne jede Messung | **ja** |
| `reserve.json` | die Rückhaltemenge (§3.3), ungelabelt | nein |
| `provenance.json` | der Stempel (§7) | **ja** |

Der schmale Schlüssel wird vom Builder geschrieben und nicht je Runde von
Hand herausgeschnitten: Das Archiv soll eine **Kopie** des Schlüssels sein,
gegen den geurteilt wurde, nicht ein zweites, Monate später zusammengestelltes
Artefakt. Der `slot` steht mit drin, weil er der dritte Teil der Identität ist
— ohne ihn sind zwei Vorkommen desselben Buchstabens im selben Wort nicht
auseinanderzuhalten (Runde 01 hatte drei solche Paare).

Ein bereits gefülltes Rundenverzeichnis wird **nicht** überschrieben (`--force`
erzwingt es): Eine Runde wird einmal geschrieben, sonst weiß hinterher niemand
mehr, gegen welchen Payload die Urteile gefallen sind.

Die Ausgabe des Laufs ist zu **lesen**, bevor es weitergeht: die Rangspanne
der ersten 100 Bildschirme (die Präfix-Prüfung aus §3.1), Anzahl und Abstände
der Wiederholungen, und die Warnung, falls zu wenige platziert werden konnten.

### Schritt 2 — Seite rendern

```bash
uv run python -m tools.humanbench.page \
    --payload temp/humanbench/runde-2/payload.json \
    --out temp/humanbench/runde-2/befund.html --round 2
```

Der Modus folgt dem Payload, nicht einem Flag: ein Panel je Bild ergibt den
Kategorien-Durchgang, zwei den paarigen Vergleich. Die Seite ist in sich
geschlossen — Crops als `data:`-URIs, Stil und Skript inline, kein Font, kein
CDN, kein Netzzugriff.

### Schritt 3 — Veröffentlichen

Als privates Artifact oder als Datei; entscheidend ist nur, dass die Seite auf
dem Gerät erreichbar ist, auf dem geurteilt wird — sie läuft auf dem Telefon
und ohne Verbindung. Grenze: 16 MB inklusive der eingebetteten Crops (die
Seite warnt ab 15 MB); Stellschrauben sind `--zoom` und `--n-label`.

### Schritt 4 — Labeln

In einem Zug, ohne Rücksprache, ohne eine Kennzahl daneben. Je Bild: die
Kategorie(n) über die Tasten 1–7, optional der Marker, optional eine
Freitextnotiz. Die Notizen sind nicht Zierat: Eine Handvoll freier Sätze hat
im ersten Durchgang mehr zur Diagnose beigetragen als manche Kategorie, weil
Prosa sagen kann, wofür es keinen Knopf gibt.

Am Ende „Aufhören und Ergebnis zeigen“: Die Seite gibt einen Textblock aus.
Dieser Text **ist** das Ergebnis der Runde und wird aufgehoben.

```
BEFUND/2 geprueft=162 von 162
S144:G@78s
S050:E#52,102@25s
S122:WE#49,195@55s "der buchstabe fängt zu spät an …"
```

Je Zeile `<uid>:<Kategorien>[#x,y][@Sekunden][ "Notiz"]`. Die Kategorien
stehen immer in derselben festen Reihenfolge (`G A W B E K U`), Marker und
Zeit fehlen, wenn nichts gesetzt bzw. gemessen wurde. `S…` ist ein
Erstauftritt, `R…` eine blinde Wiederholung. Im paarigen Modus steht statt der
Kategorien `L` / `R` / `N`.

### Schritt 5 — Auswerten

Der Ergebnistext wird über den `uid` mit `key.json` verbunden — **nie** über
die Reihenfolge. Über Runden hinweg verbindet **nicht** der `uid` (der ist die
Position in *dieser* Runde), sondern `key.identity`: Glyph, Vorlagenwort,
Slot.

Gerechnet wird strikt in der Reihenfolge des vorregistrierten Plans, und die
Verlässlichkeit zuerst (§4) — das erledigt `tools/humanbench/analyse.py`:

```bash
uv run python -m tools.humanbench.analyse \
    --result temp/humanbench/runde-2/urteile.txt \
    --key temp/humanbench/runde-2/key.json \
    --rows temp/humanbench/runde-2/rows.json \
    [--spots temp/humanbench/runde-2/spots.json] \
    [--gate 'spike>=8.0:A'] [--union W,B] [--drop-unsure] [--json auswertung.json]
```

Die Reihenfolge steckt im Werkzeug, nicht im Kopf des Auswertenden: Eine
Auswertung, die nach dem Blick auf die Labels geschrieben wird, lässt sich so
lange umsortieren, bis sie etwas sagt. `--rows` liefert der Aufrufer als Datei
(eine Kennzahlen-Zeile je `uid`) — so bleibt die gelernte Geometrie außerhalb
des Repos (§6); `--drop-unsure` rechnet die zweite, `U`-freie Fassung, die der
Plan verlangt, und `--union W,B` legt zwei Kategorien zusammen, die der
Durchgang als nicht trennbar ausgewiesen hat (§9, der vorregistrierte
Rückfall — Verwechselbarkeit kostet dann Auflösung statt die Aussage zu
zerstören). Beides wird **verlangt, nie voreingestellt**: eine Zusammenlegung,
die von selbst passiert, wäre eine andere Auswertung als die geplante.

#### Die beiden Kennzahlen-Dateien

Ohne sie laufen Verlässlichkeit, Besetzung, Drift und die Notizen vollständig,
Schritt 3 und 4 fallen aus und Schritt 5 schrumpft auf die Markerquote — das
Werkzeug sagt jeweils, was es weglassen musste. Beide sind
**Vorkommens-Statistik** und bleiben unter `temp/` (§6).

`--rows`: eine Zeile je `uid`, Zahlenfelder frei benennbar (`--metrics`), die
Voreinstellung ist die Spaltenfolge der Runde 01:

| Feld | Was in Runde 01 darunter stand |
|---|---|
| `peak` | größter Abstand eines gefitteten Ankers zum nächsten Skelettpixel, in x-Höhen („Spitze → Tinte") |
| `med` · `p90` | Median bzw. 90. Perzentil derselben Abstände |
| `off10` · `off20` | Anteil der Anker weiter als 0,10 bzw. 0,20 x-Höhen von der Tinte |
| `geo` | `geo_rmse_px` des Fits (`core/fit.py`), aus `instances.measurements` |
| `cov` | `cov_rmse_local_px` desselben Fits |
| `spike` | `anchor_spike_ratio` (`tools/laufform/harvest.py`), die Kennzahl des ausgelieferten Ernte-Gates |

Boolesche Felder werden **nicht** als AUC gerechnet, sondern als zwei Quoten
(„Anteil der Kategorie, der die Marke trägt, gegen den Anteil aller anderen");
so war die Erwartung zu `E` formuliert (`at_edge` = das Maximum sitzt in den
ersten oder letzten drei Ankern).

`--spots`: je markiertem Bildschirm die Rückrechnung des Bildpunkts auf die
Ankerkette — `idx` (getroffener Anker), `rel` (Position in der Kette, 0…1),
`edge_dist` (Anker bis zur nächsten Strichgrenze), `argmax_idx` (wo *unsere*
Kennzahl ihr Maximum hat).

> **Offen — beide Dateien erzeugt heute kein Werkzeug.** In Runde 01 entstanden
> sie in Wegwerf-Skripten, die es nicht mehr gibt. Alles Nötige liegt beim
> Builder (Abstandsfeld, gefittete Punkte, Absetz-Indizes, die gespeicherten
> Fit-Kennzahlen), der Marker steht in der Ergebniszeile — wer den nächsten
> Kategorien-Durchgang auswerten will, schreibt diesen Schritt also **einmal**
> als vierten Baustein neben `build`/`page`/`analyse`, statt ihn erneut
> wegzuwerfen.

### Schritt 6 — Aufbewahren

Urteile, Plan, Auswertung und Stempel sichern (§6), die Befunde nach
[`qualitaetsmetrik.md`](qualitaetsmetrik.md) §9 schreiben.

---

## 6. Was aufbewahrt wird — und was nicht

**Committet wird:**

* **der Ergebnistext** — die Urteile selbst. Sie sind die eigene Aussage des
  Autors an einem bestimmten Tag, **unersetzlich** und nicht neu zu rechnen;
  und sie entstehen in einem Container, der am nächsten Tag weg ist. Sie
  enthalten keine Geometrie: ein Kürzel, ein Bildpunkt, Sekunden, Prosa.
* **der schmale Schlüssel** (`vorkommen.json`, vom Builder geschrieben) — uid
  → Glyph, Vorlagenwort, Slot, `repeat_of`. Ohne ihn wäre eine Zeile wie
  `S026:AW#81,76` eine bedeutungslose Zeichenkette; welcher Buchstabe in
  welchem Wort einer gemeinfreien Tafel steht, ist keine gelernte Geometrie.
* **der Auswerteplan und die Auswertung** — Methode und Zahlen.
* **der Stempel** (`provenance.json`) — Parameter und Zählungen, keine
  Geometrie.
* **diese Methodendoku**; die Befunde in `qualitaetsmetrik.md` §9.

**Nicht committet** (bleibt unter `temp/`, git-ignoriert):

* `payload.json` (Crops **und** Vorkommens-Geometrie), `key.json` (zusätzlich
  Schwere und Rang), `reserve.json` und jede Kennzahlentabelle je Vorkommen
  (`rows.json`, `spots.json`). Das ist gelernter Datensatz und
  Vorkommens-Statistik und fällt unter den Open-Core-Vorbehalt
  ([`quellen-und-rechte.md`](quellen-und-rechte.md) §5).

**Und der Grund, warum das nichts kostet:** Schlüssel und Payload sind aus
Saat, Instanz-Schnappschuss und Stempel **deterministisch wiederherstellbar** —
genau wie die eingefrorenen Bench-Fixtures, die aus demselben Grund nicht im
Repo liegen. Reproduzierbar ist alles außer dem Menschen; deshalb wird genau
der Teil aufgehoben, der es nicht ist.

Ein Vorbehalt gehört dazu: Die Wiederherstellung ist nur so gut wie der
Stempel und der Fit-Stand, auf den er zeigt. Sind die Vorkommen inzwischen neu
geerntet, baut derselbe Befehl eine **andere** Runde. Wer eine Runde exakt
reproduzierbar halten will, hebt den Instanz-Schnappschuss auf — privat, nicht
im Repo (`tools/dbsnapshot`).

---

## 7. Der Provenienz-Stempel

`provenance.json` schreibt der Builder ungefragt mit: Runde, Modus, Bauzeit,
Quelle und `source_id`, Saat, Bänder, Zoom, Rand, Wiederholungsregeln,
**Code-Commit und -Branch**, die verwendeten Eingaben (Dateien bzw. API) und
alle Zählungen (Vorkommen, Bildschirme, gelabelt, zurückgehalten, im paarigen
Modus auch die nicht zuordenbaren, dazu Glyphen- und Probenzahl des Satzes und
— nach Grund aufgeschlüsselt — die **nicht in Frage kommenden** Zeilen: ohne
Anker, Probe nicht vermessen, abgeleitete Variante, nicht in `--only`). Die
Grundgesamtheit einer Runde ist ein gefilterter Satz, und ein Filter, den
niemand gezählt hat, sieht aus wie gar keiner: nur mit dieser Aufschlüsselung
ist später „die Ernte hat sich geändert" von „der Filter hat sich geändert" zu
unterscheiden.

Drei Felder sind leicht zu übersehen und tragen den Nachbau: die beiden
Wiederholungsregeln, die **Konstanten statt Flags** sind
(`repeat_min_glyph_count`, `repeat_jitter` — eine Änderung daran verschiebt
lautlos, welche Bildschirme sich wiederholen), und `code_dirty`. Ein Commit
sagt nur dann, welcher Code die Runde gebaut hat, wenn der Baum sauber war;
stand `code_dirty` auf `true`, ist der Commit ein Anhaltspunkt und kein
Nachweis.

**Warum er zwingend ist:** Ein Urteil gilt gegen **einen** Stand des Fits.
Ändert sich der Algorithmus — und genau das ist der Zweck der Übung —, werden
die Urteile nicht wertlos: Sie werden zum **Vorher-Zustand**. Aber nur, wenn
festgehalten ist, worauf sie sich bezogen haben: welcher Commit die Fits
gerechnet hat, aus welchem Schnappschuss die Vorkommen stammen, welche Saat
die Reihenfolge gezogen hat, wie breit der Rand war. Fehlt das, ist eine
zweite Runde keine Fortsetzung, sondern eine neue, unvergleichbare Messung —
und die erste ist damit verloren.

Das ist auch der Grund, warum das Instrument ein **Werkzeug im Repo** ist und
kein Skript je Runde: Eine von Hand zusammengestellte zweite Runde wäre ein
anderes Instrument, dessen Zahlen man nicht gegen die erste halten dürfte.

Stempel und Ergebnistext gehören zusammen aufbewahrt.

### Eine Runde, eine Nummer

Die Archivnummer unter `data/humanbench/runde-<nn>-*` ist **maßgeblich** und
zählt die abgelegten Runden. `--round` setzt bloß die Kopfzeile des
Ergebnistextes und wurde bisher zweimal danebengesetzt — Runde 01 trägt
`BEFUND/2`, Runde 02 trägt `BEFUND/3`, weil der Schalter Bauläufe mitzählte
statt Runden. Beides steht im jeweiligen Stempel, aufgelöst statt
stillschweigend geduldet; die Regel für die nächste Runde ist: **`--round` auf
die Archivnummer setzen**, damit Dateiname und Kopfzeile dieselbe Runde meinen.
Drei Zählungen für zwei Runden sind genau die Art Unordnung, gegen die dieser
Abschnitt existiert.

---

## 8. Der paarige Folgedurchgang

### Warum ein zweiter Kategorien-Durchgang die Verbesserung nicht belegen kann

* **Maßstabsdrift zwischen Sitzungen.** „Gut“ ist kein absoluter Maßstab.
  Zwischen zwei Sitzungen verschiebt sich die Latte, und niemand kann sagen,
  um wie viel. Eine gesunkene Fehlerquote ist dann von einem milder gewordenen
  Beurteiler nicht zu trennen.
* **Nach Runde eins weiß der Beurteiler, wonach er sucht.** Er hat die
  Kategorien mitentwickelt, kennt die Symptome, ist der Autor des Fixes und
  hat eine Erwartung. Kein Blindheitsanspruch überlebt das.

Ein zweiter Kategorien-Durchgang bleibt trotzdem sinnvoll — aber für andere
Fragen: frische **Prävalenzen** von einem Satz, den der Beurteiler nie gesehen
hat (die Reserve), und die regelkonforme **Bestätigung** einer neuen Kennzahl
(§3.3). Nicht als Beleg dafür, dass etwas besser geworden ist.

### Die Frage des Vergleichs ändert sich mit der Qualität

Nicht nebensächlich, sondern die Entscheidung, die eine paarige Runde brauchbar
oder wertlos macht (Vorgabe des Autors, 2026-08-09):

**Solange es eindeutige Fehler gibt**, ist der Kategorien-Durchgang das
richtige Werkzeug und die paarige Frage lautet **„welche Linie folgt der Tinte
besser?"** — eine Genauigkeitsfrage, und Genauigkeit ist genau das, was ein
Ausreißer oder ein Bereich daneben verletzt.

**Wenn beide Linien gleich gut auf der Tinte liegen**, misst diese Frage nichts
mehr: zwei genaue Linien sind beide genau. Dann verschiebt sich das Kriterium
auf **„welche sieht echter geschrieben aus?"** — nicht Nähe zur Tinte, sondern
ob es nach Hand aussieht. Das ist eine andere Eigenschaft, sie kann der
Genauigkeit sogar zuwiderlaufen (eine Linie, die jeden Skelett-Zacken
mitnimmt, ist genauer und sieht weniger geschrieben aus), und sie ist der
eigentliche Maßstab des Projekts.

Praktisch: Der Wortlaut steckt in `page.py::CHOICES` („Links folgt besser").
Wer eine paarige Runde auf der Echtheitsfrage fahren will, ändert ihn dort —
und schreibt in den Auswerteplan, welche der beiden Fragen gestellt wurde.
Eine Runde, deren Frage nicht im Plan steht, ist hinterher nicht zuzuordnen;
zwei Runden mit verschiedenen Fragen sind nicht vergleichbar.

Die Reihenfolge ist damit vorgegeben und nicht umkehrbar: **erst die
eindeutigen Fehler weg** (Kategorien), **dann die Echtheit** (paarig). Ein
Echtheitsvergleich über Vorkommen, von denen eines noch einen Ausreißer hat,
misst den Ausreißer.

### Wie der Vergleich stattdessen aussieht

Dasselbe Vorkommen, **zweimal gerechnet**, nebeneinander auf **einem**
Ausschnitt, mit einer einzigen Frage: „Welche Linie folgt der Tinte besser?“
Drei gleichwertige Antworten — links / rechts / **kein Unterschied erkennbar**
(letzteres ist ein Ergebnis, keine Ausrede: der Streit liegt dann unter der
Sichtbarkeit). Eigenschaften, jede aus ihrem Grund:

* **Die Seite verrät nirgends, welche Seite welche Rechnung zeigt** — auch
  nicht im Quelltext. Die Zuordnung steht ausschließlich im Schlüssel.
* **Die Seitenverteilung wird je Bildschirm aus der Saat gezogen.** Ein
  Beurteiler, der still die linke Seite bevorzugt, verteilt diese Neigung dann
  gleichmäßig über beide Schnappschüsse, statt sie einem zu schenken.
* **Ein gemeinsames Bild für beide Panels.** Eigene Ausschnitte hätten
  unterschiedliche Maße und einen anderen Blick auf die Nachbartinte — ein
  Hinweis, der nichts mit den Fits zu tun hat und den man in einem Dutzend
  Bildschirmen lernt.
* **Wiederholungen werden gespiegelt gezeigt.** Die identische Ansicht ließe
  sich mit „links habe ich beim letzten Mal genommen“ beantworten; gespiegelt
  muss neu über die Tinte geurteilt werden, und eine systematische
  Seitenneigung erscheint als Uneinigkeit, statt sich in der
  Übereinstimmungsrate zu verstecken.
* **Die Bänder laufen über den ALTEN Fit**, damit ein Band dasselbe bedeutet
  wie in der Vorrunde und die beiden Runden vergleichbar bleiben.
* **Vorkommen, die nur ein Schnappschuss hat, werden verworfen und gezählt.**
  Eine Änderung, die still aufhört, einen Fit zu liefern, ist ein Ergebnis —
  sie darf nicht in einer kürzeren Runde verschwinden, die trotzdem
  vollständig aussieht.

**Was er misst und was nicht:** die **Richtung** („ist es besser geworden?“)
auf denselben Vorkommen — nicht die Prävalenz je Fehlerart und keine
Fehlerrate. Wer beides will, braucht beide Blöcke: die Reserve als
Kategorien-Durchgang mit den alten Fits, und die gelabelten Vorkommen paarig.

---

## 9. Bekannte Grenzen

* **Die gelabelten Vorkommen sind die Überlebenden.** Sie stammen aus den
  gespeicherten Fits, also aus dem, was die Ernte behalten hat: Was nie
  geerntet wurde oder was ein Gate abgelehnt hat, ist nicht darunter. Eine an
  diesem Satz kalibrierte Kennzahl gilt für frisch Geerntetes **nur unter
  Vorbehalt** — dort ist die Verteilung breiter, und die schlimmsten Fälle
  fehlen hier konstruktionsbedingt. (Deshalb ist die Gate-Validierung aus §1
  eine Aussage über *behaltene* Vorkommen, nicht über verworfene.)
* **Die Breite wird nicht beurteilt.** Dargestellt ist die Mittellinie; der
  Schwellzug (`half_widths`) kommt nicht vor. Eine Runde, die ihn mitfragen
  will, muss ihn als **zweite** Darstellung zeigen und mit eigener Kategorie
  fragen, ohne das Centerline-Urteil zu verändern — sonst ist die
  Vergleichbarkeit mit der Vorrunde dahin.
* **Ein Buchstabe je Bild, nie ein ganzes Wort.** Fehler, die dem Wort gehören
  (Registrierung, x-Höhe), erscheinen als Häufung von Einzelurteilen und
  müssen erschlossen werden. Ein Wort-Übersichtsbildschirm mit eigener
  Kategorie macht diese Signatur direkt sichtbar.
* **Ein einziger Beurteiler.** Gemessen ist die Übereinstimmung des Autors
  **mit sich selbst**. Übereinstimmung zwischen Personen ist nicht gemessen,
  und die Kategorien sind nie an einem Fremden erprobt worden — der Grund,
  warum die operativen Definitionen in §2 so ausführlich ausfallen.
* **Die Kategorien sind nicht disjunkt.** Fehlerarten treten gemeinsam auf.
  Zeigen Wiederholungen oder Ko-Vorkommen, dass zwei nicht trennbar sind,
  werden sie als **Vereinigung** ausgewertet (`analyse.py --union W,B`, eine
  eigene Spalte neben den Einzelkategorien): Verwechselbarkeit kostet dann
  Auflösung, statt die Aussage zu zerstören. In Runde 01 war der Rückfall
  nicht nötig — `W ∩ B` lag bei 20 % der Vereinigung und die Wiederholungen
  waren einig —, er gehört aber zum Plan und nicht ans Ermessen der Auswertung.
* **Gemessen wird Sichtbarkeit, nicht Wichtigkeit.** Eine Fehlerart, die der
  Beurteiler zuverlässig erkennt, muss nicht die sein, die das geschriebene
  Wort verdirbt. Was ein Befund auslösen darf, entscheidet der Plan (§4) —
  nicht die Größe einer Kategorie.

---

## Querverweise

- [`qualitaetsmetrik.md`](qualitaetsmetrik.md) — die automatischen Metriken,
  gegen die die Urteile gehalten werden; die Befunde eines Durchgangs gehören
  dorthin (§9), die Methode hierher
- [`werkzeuge.md`](werkzeuge.md) — Einstieg in die Dev-Tools unter `tools/`
- [`quellen-und-rechte.md`](quellen-und-rechte.md) §5 — der
  Open-Core-Vorbehalt, aus dem §6 folgt
- [`glossar.md`](glossar.md) — Fachbegriffe und Kennzahlen
- [`../proposals/optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md)
  — Stufen- und Rollen-Doktrin: wo ein menschliches Urteil Grundwahrheit
  schafft und wo Generiertes nur markiert, nie von Hand geflickt wird
