# Eigenhand-Erfassung: Wortvorrat, Streifen, Bögen

> **Status (2026-08-23): teil-umgesetzt.** Die Werkzeugkette der Phasen 1–4
> (`tools/eigenhand/`: Wortvorrat + Streifenplan · Bogen-Druck · Einlesen +
> Siebung · Kartei/Bericht/Archiv) ist mit diesem Proposal im selben PR
> gebaut und getestet (`tests/test_eigenhand_*.py`); Welle 0 und Welle 1
> des Streifenplans sind committet (Streifen 1–120: Buchstaben, Ziffern,
> Zeichen, Mindestbelegung ≥3 je Glyphe). Zukunft ist Phase 5 (§9:
> Anschluss an Fit/Ernte) sowie die ersten echten Schreibsitzungen samt
> Kalibrier-Schleife der Kastenbreiten (§5).

## 1 Anlass

Der Autor will seine eigene Hand als Trainingsdaten erfassen — zuerst
Sütterlin, dann Offenbacher und Kurrent, mit echter Feder (für Kurrent
sind Federwinkel und Druck strichdickenrelevant; Tablet-Erfassung dafür
verworfen, §10). Der Stufenplan führt das als **H5 „Die eigene Hand“**
(handmodell-stufenplan.md): eigene `hands`-Zeile → Fits → Aggregate →
„meine Version“ als drittes wählbares Modell, mit dem strukturellen
Vorteil **beliebig viel Nachschub**. Die nie durchgeführten Milestones
M1/M2 (mvp-roadmap.md) lieferten die einzigen konkreten Alt-Zahlen
(≥300 DPI, Soll je Glyph-Position, Sieb-Disziplin) — dieses Proposal löst
beide ab und verzahnt sie (§12).

Vier Anforderungen des Autors formen das System (Sitzung 2026-08-22):

1. **Hilfslinien**, damit die Schrift sauber und gleichmäßig wird.
2. **Kein Ganzseiten-Risiko**: nie ein ganzes Blatt wegen zwei
   misslungener Wörter wiederholen — Annahme/Verwurf je Zeile.
3. Ein **fester, wachsender Wortvorrat aus echten Wörtern** (alt UND
   modern, hauptsächlich Deutsch, Englisch getaggt dazu), der schnell
   alle Buchstaben und Übergänge deckt und danach häufige wie seltene
   Verbindungen gleichmäßig ausbaut — Wörter wiederholen sich dabei so
   wenig wie möglich („irgendwann nahezu alle wichtigen Wörter mal
   geschrieben“); sehr häufige Wörter dürfen sich wiederholen, und
   welche Streifen öfter geschrieben werden sollten, macht die
   Druck-Warteschlange sichtbar (§7).
4. **Abgelegt werden nur die relevanten Streifen** — der Bogen wird als
   Ganzes gescannt, aber nur angenommene Zeilen bekommen Dateien, und
   jeder abgelegte Streifen ist für sich zuordenbar (§6).

## 2 Zielbild: die Schleife

    Wortvorrat ──pool──▶ Streifenplan (committet, append-never)
                              │
                       sheet ─▶ Bogen (PDF + layout.json) ─▶ schreiben
                              │                                │
                       report ◀── Kartei ◀── apply ◀── Siebung ◀── ingest ◀── Scan/Foto
                              │
                       snapshot ─▶ privates Archiv (create-only)

Jedes Werkzeug ist ein eigener CLI-Einstieg unter `tools/eigenhand/`
(humanbench-Muster); Betrieb: `data/samples/own-hand/README.md`. Alles ist
Mess-/Autorenschicht — kein Werkzeug schreibt die Datenbank.

## 3 Begriffe

Neu geprägt und im Glossar verankert (glossar.md, Abschnitt „Eigenhand“):
**Wortvorrat** · **Streifen** · **Streifenplan** · **Fassung** ·
**Bogen** · **Passmarken** · **Siebung** · **Streifenkartei** ·
**Übergangsraum** · **Bestandsbericht** (mit **Erstbeleg-Quote** und
**Ausbau-Quote**) · **Beleg**. Bewusst NICHT verwendet: „Abdeckung“
(gehört der Humanbench-Abdeckungsmatrix) und „Ernte“ (gehört dem
automatischen Messlauf).

## 4 Wortvorrat und Übergangsraum

**Nur echte Wörter, keine Fantasiekombinationen.** Vier Kurations-Schichten
in `tools/eigenhand/corpus.py`, per Tag nachvollziehbar: die §9-MVP-Wörter
(`mvp9`), die 63 Abb.-19-Benchwörter (`bench-abb19`, zugleich spätere
H5-Brücke zur historischen Hand), die komplette Quiz-Wortbank (`quizbank`,
mechanisch übernommen samt era/fugen/Glossen) und gezielt gejagte
Selten-Join-Wörter (`rare-join`: Komposita, Lehnwörter, Englisch) plus
zwei Nachschichten aus dem ersten `gaps`-Lauf (`haeufig`:
Hochfrequenz-Funktionswörter, die eine Lese-Quiz-Kuration systematisch
auslässt — du, jetzt, schon, über, hätte, wäre, müssen …; `english`:
Alltags-Englisch für das Zeitungs-Ziel, alles `lang: en` und filterbar;
`zeichen`: Ziffern und Interpunktion im echten Textgebrauch —
Jahreszahlen, ein Datum, ein Preis, Zeichen am Wort — als abgesetzte
Glyphen mit Positions-Soll, ohne Übergänge). Die Plan-Sicht „wie oft ist
jede Glyphe nach N Streifen dran“ liefert
`tools/eigenhand/progression.py` (Checkpoints alle 10 Streifen, `--json`
für Auswertungen).

**Der Übergangsraum ist das Soll-Universum:** alle geformten
glyph_key-Übergänge und Glyph-Positionen, die in echtem Wortschatz
vorkommen, korpusfrequenz-gewichtet. Gerechnet wird IMMER auf geformtem
Material (`core/shaping.py`): `Buch` trägt `u>ch` und kein `c>h`, `Fuß`
keinerlei s-Übergang, Ziffern/Interpunktion (`joins: false`) tragen
nichts. Quelle sind Konsultationskorpora unter
`data/corpora/frequencywords-2018/` (Klasse 2: Bytes gitignored, nur
SOURCE.md + Fetch-Skript committet; Rauschgate `MIN_COUNT` gegen den
Untertitel-Junk-Schwanz). Die Gewichtstabelle bleibt LOKAL
(quiz-wortbank.md §4: Frequenzlisten nie committen); Versal-Übergänge
betreten den Raum über die kuratierten Poolwörter, weil die Korpora
kleingeschrieben sind. Messstand 2026-08-22: 1090 Korpus-Items (987
Übergänge); ∪ Pool-Items 1265.

**Warum gezielte Jagd nötig ist:** die 495-Wörter-Quiz-Bank deckt nur
14 der 34 seltenen Abb.-20-Drill-Übergänge — natürliche Wortlisten
verfehlen den seltenen Schwanz systematisch. Drill-Übergänge OHNE echtes
Trägerwort bleiben bewusst außerhalb des Solls (Ziel ist echter Text;
§10 „Fantasiesilben-Drills“).

**Der Streifenplan** (`core/eigenhand/streifen.json`, committet) ist der
deterministisch gebaute, **append-never** Output: `pool.py build` wählt in
Phase A per gewichtetem Set-Cover die Startdeckung (maximale
Abdeckungsgeschwindigkeit — die ersten Bögen tragen fast das ganze
erreichbare Soll), hebt in **Phase A2** jede Glyphe auf die
**Mindestbelegung** (`GLYPH_MIN_PLANNED = 3`, Owner-Regel 2026-08-23:
„sowas wie q nur 1× darf nicht sein“) — eine Garantie, keine Präferenz,
frequenzunabhängig, mit benannter Meldung, falls die Wellenkapazität
nicht reicht —, und baut in Phase B defizitgetrieben gleichmäßig aus,
häufig UND selten; gepackt wird nach geschätzter physischer Breite gegen
das breiteste Preset (Sütterlin), sodass ein Streifen in jede Schrift
passt. **Breite vor Wiederholung:** ein bereits geplantes Wort wird je
bisheriger Einplanung mit `REPEAT_DAMPING = 0.3` gedämpft — es kommt nur
wieder, wenn kein neues Wort vergleichbaren Nutzen bringt; dominante
Hochfrequenz-Wörter setzen sich trotzdem durch. Wachstum in **Wellen**
(`--wave` implizit über den Dateizustand): neue Streifen werden
angehängt, bestehende sind unantastbar (Wächter `verify_immutable`).
Welle 0: 60 Streifen, 253 distinkte Wörter, 726/1265 Items mit geplantem
Erstbeleg. Welle 1 (Streifen 61–120) bringt Ziffern, Zeichen und die
Mindestbelegung: nach 120 geplanten Streifen trägt JEDE Registerglyphe
mindestens drei Belege, 666 verschiedene Übergänge sind geplant.

**Format 2: der Plan trägt seine Schreibformen selbst.** Seit die
Bestands- und Druckrechnung auch serverseitig läuft (§7.1), führt
`streifen.json` neben `strips` eine Tabelle `forms` — Wort → Fugen-Form,
wo beide auseinanderfallen (`Amtszeit` → `Amts|zeit`). Ohne sie könnte
nur ein Leser mit der Kurationsquelle (`tools/eigenhand/corpus.py`)
richtig formen; mit ihr ist der committete Plan allein vollständig. Die
Tabelle ist append-never wie die Streifen: ein einmal eingetragener Wert
wird nie überschrieben, damit eine spätere Kurationsänderung keine
eingefrorene Zeile umformt.

**Trainingsdaten, kein Mess-Satz.** Der Wortvorrat und der Streifenplan
wachsen; KEINE Bench-Kopfzahl liest je aus ihnen. Sollte je eine Messung
über Eigenhand-Material gewünscht sein, wird dafür eine Teilmenge
separat eingefroren und vorregistriert (Frozen-Reference-Doktrin,
qualitaetsmetrik.md).

## 5 Bogen

Ein Bogen ist ein A4-Blatt aus offenen Streifen: Kopf („Sütterlin ·
Bogen 12“ + Maschinen-ID `mn-suetterlin-B0012` + Datum), vier
**Passmarken** (8×8-mm-Quadrate, Zentren 10/200 × 10/287 mm; links oben mit
3-mm-Lochung als Orientierungs-Donut), je Zeile die Streifen-ID und pro
Wort ein **Kasten mit Lineatur** — Bandlinien nur im Kastenbereich, die
Gassen bleiben tintenfrei. Unter dem Schreibband liegt die 5-mm-Zone mit
dem Klartext-Wort, darüber und darunter die Polster des Schnittbands, und
zwischen zwei Streifen exakt `STRIP_GAP_MM` = 5 mm freies Papier — der
Zeilenabstand wird aus Streifenhöhe + Lücke ABGELEITET, nicht gesetzt, und
gilt damit für jede Schrift gleich. Presets aus
`app/src/lib/lineatur.ts` portiert und per Test gepinnt (Sütterlin 1:1:1
bei 6 mm x-Höhe senkrecht; Offenbacher 2:3:2/5 mm/77°; Kurrent
2:1:2/2,5 mm/65° mit Schräglagen-Hilfslinien im Kasten). Sütterlin-Pitch
34 mm → **Default 7 Zeilen** (`--rows` konfigurierbar); die erste Zeile
beginnt bei y = 29 mm, damit die obere Schnittmarke 6,4 mm Abstand zu den
Passmarken hält.

**Der bedruckbare Bereich ist eine Zusage an den Drucker**
(`geometry.py::PRINT_SAFE_MM` = 6 mm, 2026-08-25). Vorher lagen die
Passmarken 3 mm vom Blattrand — enger, als ein Bürolaser drucken kann:
HP-LaserJets verweigern die äußeren 4,23 mm, gängige Geräte liegen
zwischen 3,4 und 5. Der Preis dafür wäre keine Fehlermeldung gewesen,
sondern eine stille Schieflage. Eine beschnittene Passmarke ist immer
noch quadratisch und immer noch massiv, besteht also jeden Formtest des
Detektors; nur ihr Schwerpunkt ist nach innen gewandert. Auf einem HP
kämen die vier 8-mm-Quadrate als 6,77 mm heraus, jeder Schwerpunkt
0,615 mm weiter innen, und die Entzerrung — die genau diese vier
Schwerpunkte auf ihre Soll-Millimeter abbildet — streckt das Blatt dann
um +0,63 % in x und +0,44 % in y. Anisotrop, systematisch und unsichtbar:
jede Strichbreite, jede x-Höhe und jede Schräglage aus so einem Scan
trüge das mit, die ganze Kampagne lang.

Deshalb sitzt jetzt **nichts Gedrucktes näher als 6 mm am Blattrand** (ein
Test prüft das am fertig komponierten Bogen, nicht an den Konstanten).
Die Marken gehen so weit nach außen, wie das erlaubt — Zentren bei
`PRINT_SAFE_MM + 4` = 10 mm —, denn ein größeres registriertes Viereck
heißt weniger Winkelfehler je Pixel Schwerpunktrauschen; die Spannweite
sinkt dabei von 196 × 283 auf 190 × 277 mm. Zwei Dinge folgen mit: Kopf,
Fußzeile und Legende hängen nicht mehr am Schreibrand, sondern an
`META_MARGIN_MM` = 18 mm (bei 15 mm hätten sie 1 mm neben der neuen Marke
gestanden statt der 4 mm, die sie neben der alten hatten), und
`TOP_MARGIN_MM` folgt den Marken um dieselben 3 mm nach unten, damit die
obere Schnittmarke ihren Abstand behält. Sieben Zeilen passen weiter, die
Schreibbreite bleibt 180 mm, und der Stiftkasten rückt auf x = 198,5 mm —
in dieselbe Spalte wie die rechten Schnittmarken, die er nie trifft, weil
sie an den ECKEN des Schnittbands sitzen und er in dessen Mitte (11–13 mm
Abstand).

**Was der Bogen selbst nicht sehen kann.** Ein gleichmäßig skalierter
Druck („An Seite anpassen") schrumpft Marken UND Abstände zusammen; das
Verhältnis bleibt, die Entzerrung rechnet es weg, und keine Kennzahl im
Scan verrät es. Dagegen hilft nur das Lineal auf dem Papier — 190,0 mm
zwischen den Markenzentren waagerecht, 277,0 mm senkrecht. Ein
BESCHNITTENER Druck dagegen ist messbar, weil Markengröße und
Markenabstand vom selben Gerät kommen: `fiducial.check_mark_size` liest
die Größe, die der gemessene Abstand impliziert, und meldet jede Marke,
die deutlich darunter bleibt.

**Kastenbreite mit Puffer überall** (Owner, 2026-08-23: „ich will nicht
das Wort ruinieren, weil ich am Ende nicht mehr hingekommen bin").
Grundbreite = 10 mm Vorlauf + Σ advance(glyph_key) in x-Höhen
(`geometry.py::ADVANCE_XH`, Startwerte; **Kalibrier-Schleife**: nach dem
ersten beschriebenen Blatt werden die Konstanten gegen die gemessenen
Tintenbreiten nachgezogen). Zwei Reserven darüber:

* Die **Packung** hält `PACK_SLACK_MM` = 15 mm der Zeile frei. Der erste
  Plan packte bis 180,0 von 180 mm — bei einer Schätzung, die noch keine
  echte Tinte gesehen hat, ist das keine Reserve, sondern keine.
* `boxes_for_row` gibt diesen Rest an die **Kästen zurück**, verteilt
  proportional zur Wortlänge. Jedes Wort bekommt also Luft (10–44 % über
  der Schätzung), nicht nur das letzte der Zeile; das lange Wort, bei dem
  die Schätzung am meisten danebenliegen kann, bekommt den größten Anteil.

Die Advance-Startwerte wurden am 2026-08-23 angehoben (Standard-Kleinbuchstabe
0,85 → 1,00 x-Höhe): bei 6 mm x-Höhe misst ein rundes senkrechtes `n` mit
Auslauf eher 6 mm als 5,1 — und eine ungeübte Hand schreibt größer, nicht
kleiner. Zu breit kostet ein Wort je Zeile, zu schmal kostet die Zeile.

**Schnittband und Schnittmarken (Owner, 2026-08-23):** jede Zeile hat ein
**Schnittband** — das Rechteck, zu dem der Streifen geschnitten wird.
Feste Spalten (x = 12 … 197 mm) und feste Polster (4 mm über der
Oberlinie, 3 mm unter der Klartext-Zeile), also **für jede Zeile eines
Stils dieselbe Höhe und dieselbe Breite** (Sütterlin 185 × 29 mm, Kurrent
und Offenbacher 185 × 28 mm — `CUT_MIN_HEIGHT_MM` gibt ihren flacheren
Zeilen 6–7 mm Polster statt 4,5/1,5),
unabhängig davon, wie viele Wörter die Zeile trägt. Zwischen zwei
Schnittbändern bleiben 5 mm freies Papier: ein Schnitt, der 2 mm
wandert, verfehlt beide Streifen immer noch.

Markiert wird an den **Rändern**, nie auf dem Streifen — Tinte innerhalb
des Schnittbands landete sonst in den Trainingsdaten. Je Zeile vier
2,5-mm-Striche links und rechts auf Höhe der beiden Querschnitte; die
beiden Längsschnitte sind für alle Zeilen dieselben und werden deshalb
in den Lücken ZWISCHEN den Streifen markiert (nicht am Blattkopf: eine
Haarlinie, die auf dem Scan in eine Passmarke verläuft, zöge deren
Schwerpunkt mit — und damit jeden Millimeter, den der Import rechnet;
aus demselben Grund beginnt die erste Zeile bei y = 29 mm). Die
Streifen-ID steht im oberen Polster INNERHALB des Schnittbands, damit
ein geschnittener Streifen für sich zuordenbar bleibt (§7); die
Stiftmarke steht bewusst außerhalb.

**Der Streifen sagt, woher er stammt** (Autor-Entscheid 2026-08-25). Die
ID allein leistete das nicht: EIN Plan bedient alle drei Stile, `S0001`
existiert also für `mn-suetterlin`, `mn-kurrent` und `mn-offenbacher`
gleichermaßen, und ein Redo druckt sie auf einem späteren Bogen erneut —
der Versuchszähler `(1/3)` zählt nur innerhalb EINES Bogens. Eine
Schublade voller geschnittener Streifen enthielte damit Dutzende optisch
gleich beschrifteter Zettel, deren Zuordnung zu Bogen, Sitzung und
Fassung ausschließlich in der lokalen Kartei und in der DB steht — genau
den beiden Dingen, die der Schubladenfall nicht mehr hat. Deshalb trägt
dieselbe Zeile am ANDEREN Ende, rechtsbündig im Schnittband, Hand, Bogen
und Druckdatum. Zwei kurze Läufe an den Enden statt eines langen: die
Mitte des Polsters bleibt frei, wo eine überschießende Oberlänge sonst
auf 40 mm gedruckten Text im Trainingsbild träfe. Kostenlos für den
Import — `_printed_mask` stellt alles oberhalb der Oberlinie ohnehin
frei, und dort steht die Zeile bereits.

Der Import schneidet digital genau am Schnittband (`layout.json`-Feld
`cut_mm`): Papierstreifen und `streifen.png` sind damit dasselbe
Rechteck, und jede abgelegte Fassung eines Stils hat identische
Pixelmaße.

**Stiftmarke je Zeile:** rechts neben dem Schreibfeld trägt jede Zeile
EIN 5-mm-Kästchen (Spalte ab x = 198,5 mm, jenseits des Schnittbands,
einmalig im Kopf mit „ok“ beschriftet). Dort ist die Hand am Zeilenende
ohnehin, und die Passmarken
belegen nur die Seitenecken — die Spalte kostet also keine Schreibbreite
(die eingefrorenen Streifen füllen die 180 mm voll aus). Die Regel ist
bewusst binär (Owner, 2026-08-23): **Kreuz oder Haken drin = ok, leer =
nicht ok.** Ein Kästchen statt zweier hält den Bogen bei einer einzigen
Stiftbewegung; der Preis ist, dass eine vergessene Marke als „nicht ok“
liest — die harmlose Richtung, denn der Streifen wandert dann nur zurück
in die Druck-Warteschlange, statt ungeprüft abgelegt zu werden.

**Sehr schwache Lineatur** (Owner, 2026-08-23): der Bogen druckt nicht
das `druck`-Thema der App, sondern ein eigenes Erfassungs-Thema
(`geometry.py::CAPTURE_STYLES`) — Grundlinie hellgrau statt fast schwarz,
Ober-/Unterlinie noch heller, das Schräglagengitter fast Papier. Jeder
Linienwert liegt deutlich über der Tintenschwelle des Imports
(`ingest.INK_THRESHOLD`), eine gedruckte Linie kann also nie als Tinte
gezählt werden — auch dann nicht, wenn die Maskierung sie verfehlt. Dunkel
bleibt nur, was der SCHREIBER lesen muss: Labels, Streifen-ID, Kopf,
Stiftkästchen und Schnittmarken; alle liegen außerhalb des Schreibbands
oder werden maskiert.

**Die Lineatur wird in hellem CYAN gedruckt** (Owner, 2026-08-23). Vorher
lag sie im `druck`-Grau der App bei Luminanz 0,10 (Grundlinie) und 0,41
(Mittellinie) — beide UNTER `INK_THRESHOLD` = 0,55, wären also als Tinte
gezählt worden. Ein hellgraues Ersatz-Thema hätte das behoben, aber nur
knapp (+0,10 auf der Grundlinie, die sichtbar bleiben muss); ein Scanner
mit Auto-Kontrast oder ein Foto im Schatten frisst so einen Abstand.

Cyan löst es strukturell statt knapp: der Blau-Anteil einer cyanfarbenen
Linie liegt bei Papierniveau, ein **Farbscan durch den Blau-Kanal gelesen**
verliert die Linien also vollständig — nicht „unter einer Schwelle",
sondern weg. `ingest --channel auto` nimmt bei einer Farbaufnahme den
Blau-Kanal und fällt bei einer Graustufenaufnahme auf Luminanz zurück;
welcher Kanal genommen wurde, steht in `payload.json` unter `scan.channel`.

Gemessen (Rolle: Blau-Kanal / Graustufe): Grundlinie **0,91 / 0,75**,
Mittellinie 0,94 / 0,81, Ober-/Unterlinie 0,96 / 0,86, Schräglagengitter
0,97 / 0,91. Cyan ist damit in BEIDEN Aufnahmearten besser als das Grau —
keine Wette auf den Farbscan.

Die Tinte übersteht den Kanalgriff: Schwarz 0,10 und Eisengallus-Braun
0,14 im Blau-Kanal. **Blaue Tinte liegt mit 0,55 genau auf der Schwelle**
und ist deshalb ausgeschlossen — der Bogen wird mit schwarzer oder brauner
Tinte geschrieben (README „Regeln").

**Was am Fuß des Bogens steht — und warum** (überarbeitet 2026-08-25, nach
dem ersten Probedruck). Die Fußzeile trug bis dahin drei Felder, von denen
zwei nichts leisteten: die Maschinen-ID ein zweites Mal wörtlich (gelesen
wird nur die im KOPF — `ingest` schneidet die oberen 14 mm als
Fehlablage-Wächter) und einen Commit, der auf jedem über die deployte API
gedruckten Bogen leer ist (`.git` steht in `.dockerignore`, `git` ist im
Image nicht installiert). Gleichzeitig stand von den Regeln, die der
Schreiber UNWIEDERBRINGLICH verletzen kann, keine einzige auf dem Papier —
sie standen in `data/samples/own-hand/README.md`, also in einer Datei, die
beim Eintauchen der Feder niemand offen hat. Jetzt drucken zwei Zeilen über
der Legende genau diese drei:

- **Tinte schwarz oder braun, nie blau** — Blau liegt mit 0,55 exakt auf
  `INK_THRESHOLD`; ein blauer Haken liest als leeres Kästchen.
- **In Farbe scannen, mind. 300 dpi** — sonst greift der Kanaltrick nicht.
- **Erst scannen, dann schneiden** — ein geschnittener Streifen trägt keine
  Passmarke mehr, also ist danach KEIN Import mehr möglich, und der Bogen
  lässt sich nicht neu drucken (neue ID, Streifen aus der Warteschlange).
- dazu die Verdikt-Regel: **Kästchen rechts ankreuzen, leer = verworfen.**

Rechts unten steht seither die **Lineal-Probe** („Markenmitten 190,0 ×
277,0 mm — ohne Skalierung drucken"), aus `FIDUCIAL_CENTERS` abgeleitet
statt ausgeschrieben: die einzige Abwehr gegen den skalierten Druck gehört
auf das Blatt, das der Mensch mit dem Lineal in der Hand hält.

**Der `cfg`-Stempel ist jetzt der Geometrie-Fingerabdruck des Blattes.** Er
war vorher ein Hash über eine handgepflegte Konstantenliste unter einem
Kommentar, der versprach, „JEDE Konstante, die einen gedruckten Kasten
bewegt" zu erfassen. Das tat er nicht, und er scheiterte so, wie solche
Listen immer scheitern: der Umzug in den bedruckbaren Bereich verschob alle
vier Passmarken um 3 mm, jede Zeile um 3 mm nach unten und die
Stiftkasten-Spalte — und der gedruckte Stempel blieb durchweg
`aa9f6a5566`. Zwei Bögen, deren Bezugsrahmen sich um 3 mm unterscheidet,
waren an genau der Marke nicht unterscheidbar, die dafür da ist. Gehasht
wird deshalb jetzt das `layout` selbst ohne seinen `provenance`-Block: es
trägt die Passmarken-Zentren, jedes `cut_mm`, `band_mm`, `mark_mm` und jede
Kastenkante, kann also konstruktiv nichts vergessen — und reagiert nicht
mehr auf Dinge, die dieses Blatt gar nicht druckt (eine geänderte Advance
für eine Glyphe, die nicht darauf steht, bewegte vorher den Stempel jedes
Bogens). Kein voller Reproduktionsschlüssel: Farben, Schriftgrößen und der
Legendenwortlaut liegen in Modulkonstanten und stehen nicht im Layout.

Klartext-Labels stehen in normaler Latin-Type unter den Kästen
(Leitsatz Lesbarkeit; WinAnsi hat ohnehin kein ſ). Als Schreib-Hinweis
zeigt das Label die Fugen-Form, wo eine existiert (`Donners*|tag`: `|` =
Wortfuge, `*` = rundes Schluss-s statt langem ſ) — der eine Fall, in dem
das Shaping von den einmal gelernten Standardregeln abweicht;
`--no-hints` schaltet ab. Die beiden Zeichen stehen als **Legende in der
Fußzeile** jedes Bogens, der sie verwendet (Owner fragte 2026-08-23, was
`Donners*|tag` bedeutet — was erklärt werden muss, gehört gedruckt).

**Mehrfach-Zeilen (Versuche):** derselbe Streifen darf mehrfach auf einem
Bogen stehen (`--repeat N` oder explizit `--strips S0037 S0037 …`);
Zeilenbeschriftung dann `S0037 (1/3)`. Bei der Siebung ist jede Teilmenge
annehmbar — best-of ist ausdrücklich erlaubt (§6).

Der PDF-Writer (`pdfgen.py`) ist der dependency-freie Python-Zwilling von
`app/src/lib/pdf.ts` (+ gefüllte Rechtecke für die Passmarken),
deterministisch (Golden-File-Test). Jeder Bogen schreibt neben das PDF
seine **`layout.json`** — den einzigen Geometrie-Vertrag des Importers:
Registrierung statt Erkennung, weil das Blatt seine Geometrie selbst
gedruckt hat. Das §15-Reservat der Architektur (`POST /worksheet`,
WeasyPrint) bleibt unberührt: der Bogen ist ein privates
Autoren-Instrument, nicht das öffentliche Ziel-2-Übungsblatt.

## 6 Einlesen und Siebung

`ingest.py` nimmt Scan ODER Handyfoto (Owner-Entscheidung: beides;
HEIC vorher als JPEG): Passmarken-Detektion rein mit scikit-image
(Otsu + Regionen, Quadranten-Scoring; OpenCV bleibt bewusst draußen,
styleanalyse.md), Orientierung über den Donut (180°-Scan und gedrehtes
Foto landen richtig), Homographie gegen die layout.json-Zentren, Warp in
den mm-Raum bei **300 DPI Arbeitsauflösung** (6 mm x-Höhe ≈ 71 px, der
M1-Boden; Warnung unter ~250 DPI effektiv). Unter vier sicheren Marken:
lauter Abbruch. Danach schneidet der Import jede Zeile aus dem
entzerrten Bild — **digital, millimetergenau, ohne das Blatt zu
zerschneiden**.

Die **Stiftmarke** wird dabei aus den bekannten Kästchen-mm gelesen
(Tintenanteil in der Innenfläche, gedruckter Rahmen ausgespart): Haken
oder Kreuz → `angenommen`, leeres Kästchen → `verworfen`. Ein Fleck
bleibt unter der Schwelle und zählt nicht als Marke; nur ein Bogen ohne
Kästchen-mm (vor Einführung gedruckt) bleibt unentschieden. Sie ist der
EINZIGE Eingang, der die Siebung
vorbelegen darf — weil sie ein Menschenurteil im besten Moment ist
(direkt nach dem Schreiben), nicht eine Maschinenvermutung; die
Review-Seite zeigt sie als Chip „Stift auf dem Blatt“ und lässt sie
jederzeit überschreiben. QC-Flags (`leer` · `beschnitten` · `blass`,
gedruckte Geometrie ±0,4 mm maskiert) sind dagegen WARNUNGEN, nie
Auto-Verdikte. Die **Siebung** läuft auf
EINER selbstständigen HTML-Seite (`page.py`, humanbench-Muster: Crops als
data-URIs, offline, Resume nach jedem Klick, uid-verschlüsseltes
Ergebnis, nie über Reihenfolge gejoint); der Kopf-Crop wird gegen die
erwartete Bogen-ID bestätigt (Fehlablage-Wächter). Auf der Seite steht
die **Sieb-Disziplin** (aus M2 übernommen): verworfen wird nur nach
Schreibqualität (verschrieben, verrutscht) — nie, weil Buchstaben eng am
Nachbarn sitzen; enge Verbindung ist Signal, nicht Müll; Ausfälle müssen
zufällig sein, nicht selektiv. Best-of über Mehrfach-Versuche desselben
Streifens ist davon ausdrücklich unberührt (Auswahl nach Schreibqualität
ist der Zweck der Versuche).

`apply.py` legt aus dem Ergebnis die **Fassungen** an — und zwar nur für
angenommene Zeilen („abgelegt werden nur die relevanten Streifen“):
`fassungen/S0037/F02/{streifen.png, meta.json}`. Der Streifen-PNG ist der
unveränderte Graustufen-Crop (Zwei-Kanal-Doktrin: Binarisierung ist
nachgelagerte Ableitung) und **selbst-zuordenbar**: gedruckte
Streifen-ID und Wortlabels stehen mit im Ausschnitt, die `meta.json`
daneben trägt Wörter, Kasten-Geometrie, Urteil, QC, Schreibsitzung
(Datum · Feder · Tinte · Papier · Gerät), Prüfsummen und Provenienz.
Verworfene Zeilen werden pixelfrei in der Kartei protokolliert (Urteil +
Grund — der Bias-Audit bleibt zählbar); der Ganzseiten-Scan wird nur mit
`--keep-scan` übernommen. `apply` ist idempotent, verweigert
Überschreiben und widersprüchliche Nachurteile.

## 7 Kartei und Bestandsbericht

Die **Streifenkartei** (`kartei.json`, lokal, atomar, nie committet) ist
die einzige Zustandsquelle: Bögen, Fassungen, Sitzungen, Redo-Liste.
Streifen-Zustände werden ABGELEITET, nie gespeichert: `belegt` (≥1
angenommene, nicht zurückgezogene Fassung) · `unterwegs` (öfter gedruckt
als beurteilt) · `geplant` (sonst — auch nach reinem Verwurf).
`unterwegs` ist ein Anzeige-Zustand, KEIN Kriterium der Warteschlange
(Autor-Entscheid 2026-08-26): ein Druckauftrag beginnt immer vorn im
Plan, minus die belegten Streifen — ein gedruckter, aber nie
geschriebener Bogen hält nichts zurück, denn ein neuer Druck wird
gerade deshalb verlangt, weil der alte weg ist; „Bögen im Umlauf" zu
zählen ließe die Warteschlange nur vom Plan wegdriften. Innerhalb EINES
Auftrags setzen die Seiten die Warteschlange fort (kein Streifen auf
zwei Bögen desselben Stapels), und der Stapel kommt als EIN PDF mit
einer Seite je Bogen heraus (`core/eigenhand/bogen.py::compose_stack`).

**Neuaufnahme ergänzt** (Owner-Entscheidung): `redo.py S0037 S0055`
stellt Streifen wieder in die Warteschlange; alte angenommene Fassungen
bleiben Trainingsmaterial, sofern nicht ausdrücklich `--retire`
(Status `zurueckgezogen` — ASCII wie alle Statuswerte, Datei bleibt,
zählt nicht mehr). Ein Redo-Eintrag erlischt mit der nächsten
angenommenen Fassung. `--retire` greift nur an ANGENOMMENE Fassungen:
eine irrtümlich verworfene Zeile lässt sich nicht nachträglich annehmen,
der Streifen muss neu gedruckt und neu geschrieben werden.

Der **Bestandsbericht** (`report.py`) stellt Soll/Ist je Item:
**Erstbeleg-Quote** (Anteil Items mit ≥1 Beleg) und **Ausbau-Quote**
(Σ min(Ist, Soll)/Σ Soll), jeweils ungewichtet UND
übergangsraum-gewichtet — die gewichtete Zahl ist die ehrliche
Kopfzeile, weil der seltene-aber-echte Schwanz sie nur gemäß seiner
Textrelevanz drücken kann. Dazu die größten gewichteten Fehlstellen und
der **Druckvorschlag**: dieselbe Warteschlange, die `sheet.py --next`
druckt — Redo zuerst, dann nie Belegtes in Planreihenfolge, dann
Wiederholungs-Kandidaten **nach gewichtetem Soll-Gewinn einer weiteren
Fassung** (Owner-Wunsch: sichtbar, welche Streifen wegen häufiger
Wörter öfter geschrieben werden sollten). Zweistufiges Soll je Item: die
Erstbeleg-Stufe (≥1 Beleg — sie misst die Erstbeleg-Quote und treibt
Phase A) und das Aufbauziel `clamp(3 + 17·√(w/wmax), 3, 20)`
(`coverage.target_for_weight`, Untergrenze 3 — es misst die
Ausbau-Quote) — Spiegel von M1 („Kern ≥10, Rest ≥3”) und der
Vorkommensschranke (`LAUFFORM_MIN_OCCURRENCES = 3`). Quer dazu steht die
**Mindestbelegung** je GLYPHE (Phase A2, §4): kein Buchstabe, keine
Ziffer, kein Zeichen darf mit weniger als drei geplanten Belegen
dastehen, egal wie selten das Item im Text ist —
`tools.eigenhand.progression` schließt jeden Lauf mit der Zeile, ob sie
erfüllt ist, und nennt sonst die betroffenen Glyphen.

Rauchtest der ganzen Schleife (synthetisch beschriebener Bogen,
perspektivisch verzerrt + 180° gedreht): nach 6 angenommenen Fassungen
lag die gewichtete Erstbeleg-Quote bei 67,8 % — die gewünschte
Abdeckungsgeschwindigkeit der Phase A.

### 7.1 Zweite Persistenz: die Buchführung in der DB

**Owner-Entscheidung 2026-08-23:** „der weg über die db ist doch gut, da
darf drin stehen welche streifen bereits wie oft vorhanden sind … damit
weisst du ja die wörter … und kann auch neue pdf vorlagen generieren zum
ausdrucken, den crop braucht man da ja erstmal garnicht.“ Damit
bekommt die Kartei eine zweite Persistenz — und der Admin-Bereich eine
Ansicht, die auf der deployten Seite echte Zahlen zeigt statt einer
leeren Seite.

Was in die geteilte DB geht (Migration `0024`, zwei Tabellen):

- `eigenhand_sheets` — je gedrucktem Bogen: Hand, Stil, Bogen-ID,
  Druckdatum, die Streifen-Zeilen und das **Layout** (der
  Geometrie-Vertrag). Gespeichert wird das Layout, nicht das PDF: die
  Bytes folgen aus der Geometrie, die Geometrie nicht aus den Bytes.
- `eigenhand_fassungen` — je beurteilter Zeile: Streifen, Fassung, Bogen,
  Zeilenindex, Verdikt, Grund, SHA256 der lokalen Datei. Zwei
  Unique-Constraints tragen die Regeln: eine Fassungs-ID je Streifen, ein
  Verdikt je gedruckter Zeile (dieselbe Idempotenz wie `apply.py`).

Was NICHT hineingeht: Scans, Crops, Streifenbilder. Der reservierte
Datensatz (§8) bleibt lokal; `png_sha256` benennt die Datei, ohne sie zu
enthalten. Aus Streifen-ID plus committetem Plan folgen die Wörter — für
die Statistik braucht es kein einziges Pixel.

**Eine Rechenschicht, zwei Persistenzen.** Der Nahtpunkt ist die
Kartei-FORM: `tools/eigenhand` liest sie als `kartei.json`, die API baut
denselben Dict aus den beiden Tabellen (`EigenhandRepository.kartei`).
Alles dahinter — Druck-Warteschlange, Layout, PDF, Bestand — liegt in
`core/eigenhand` und kann die beiden nicht unterscheiden. Deshalb sind
Terminal und Werkbank per Konstruktion einig über dieselbe Hand.

Ein Unterschied bleibt und ist gewollt: die
**Übergangsraum-Gewichte** stammen aus Konsult-Korpora und bleiben auf
dem Rechner, der sie gebaut hat (§4, quiz-wortbank.md §4). Der Server
zeigt darum keine Quoten und ordnet Wiederholungs-Kandidaten nach
wenigsten Fassungen statt nach gewichtetem Soll-Gewinn. Wollte man das
ändern, wäre es eine eigene Entscheidung über eine abgeleitete
Gewichtstabelle in der DB — nicht ein Nebeneffekt dieser Ansicht.

**Die Schleife mit Admin-Druck.** Werkbank → `Bögen erzeugen` (Auswahl
und Layout wie im Terminal; ein Stapel wird in EINEM Zug ausgewählt,
jeder Bogen als eigene Zeile verbucht und alle zusammen als ein
mehrseitiges PDF ausgegeben, §7) → PDF öffnen und drucken → schreiben → lokal
`tools.eigenhand.pull --sheet B0007` holt Layout und PDF auf die eigene
Platte → `ingest` → Siebung → `apply` → `tools.eigenhand.sync` schiebt
Bögen und Verdikte zurück. Wer im Terminal druckt, schiebt seine Bögen
mit demselben `sync` hoch: beide Seiten münzen ihre IDs aus derselben
Kartei-Sicht, und ein registrierter Bogen nimmt seine ID aus dem
Verkehr. Ein bereits registriertes Layout wird nie überschrieben — ein
abweichendes unter derselben ID ist ein Konflikt (409), weil ein Scan
dagegen registriert sein kann. „Abweichend" heißt: andere Geometrie,
verglichen über die KANONISCHE Form (`bogen.layout_digest`, Schlüssel
sortiert) des gespeicherten wie des hochgeschobenen Layouts — nicht über
die Reihenfolge der Schlüssel, die JSONB beim Zurückgeben ohnehin
umsortiert. Genau daran scheiterte der erste echte Durchlauf am
2026-08-26: `pull` holte das Server-Layout, `sync` hashte es in der
zurückgegebenen Reihenfolge, und der Server hielt denselben Bogen für
einen anderen.

**Was die Schnittstelle nachrechnet, statt es zu glauben** (Copilot-Review
zu PR #407, beides echte Lücken): Ein hochgeschobenes Layout muss DIESEN
Bogen benennen — Hand, Bogen-ID und Stil müssen zur Route passen, die
Zeilen zur Streifenliste —, denn aus ihm wird später das PDF gerendert und
gegen es ein Scan registriert; dieselbe Prüfung macht `apply.py` lokal,
bevor es eine Zeile in eine Hand einsortiert. Und der Layout-Hash wird
serverseitig gebildet, nicht übernommen: an ihm hängen Idempotenz und
Konflikt, ein selbstdeklarierter Wert könnte zwei verschiedene Layouts für
identisch erklären. Ebenso muss jedes Verdikt eine tatsächlich GEDRUCKTE
Zeile benennen (Bogen registriert, Zeilenindex vorhanden, Streifen der
dieser Zeile) — eine Fassung IST ein Beleg, sie macht einen Streifen
`belegt`; ein Verdikt auf einen nie gedruckten Bogen erfände
Trainingsdaten. `sync.py` hält darum die Verdikte eines Bogens zurück, den
es (mangels `layout.json`) nicht registrieren konnte.

### 7.2 Die Streifen selbst — Bilder in der DB

**Owner-Entscheidung 2026-08-24:** „ich glaube auch, dass ich die
Streifen gerne in der Datenbank hätte, damit der Admin-Bereich wie jetzt
bei Sütterlin auch den Crop anzeigen kann, ohne dass sie im Repository
landen.“ Das kehrt den engeren Satz aus §7.1 („was hochgeht, sind Zahlen
— nie ein Streifenbild“) für genau einen Weg um: die DB, nicht das Repo.
Migration `0025` bringt dafür drei Dinge.

- **`eigenhand_hands`** — das STEHENDE Setup einer Hand: Feder, Tinte,
  Papier, Aufnahmegerät. Diese drei sind photometrische Parameter einer
  ganzen Kampagne, keine Detailangabe eines Imports: wechseln sie
  mittendrin, zerfällt das Korpus in Kohorten, die man auf Breite und
  Schwärzung nicht mehr vergleichen kann. Einmal getippt
  (`tools.eigenhand.setup`), lokal zwischengespeichert (`setup.json`),
  von `ingest` als Vorgabe gelesen.
- **Sitzungsspalten auf `eigenhand_fassungen`** — die EFFEKTIVEN Werte je
  Zeile. Bewusst denormalisiert: eine Fassung muss aus sich heraus sagen,
  womit sie geschrieben wurde — ohne Join und ohne die stille Regel „NULL
  heißt wie die Hand“, die genau an dem Tag falsch wird, an dem die Hand
  wechselt. Der Bruch soll in den Daten sichtbar sein, nicht
  rekonstruiert werden müssen.
- **`eigenhand_strips`** — das Streifenbild. Eigene Tabelle, PNG-Spalte
  überall deferred (`defer(EigenhandStrip.png)`), damit kein
  Bestands-Query je ~350 KB pro Fassung mitschleppt — dasselbe Motiv wie
  beim deferred `templates.raw_path` im Render-Pfad.

Das Chart-Vorbild trägt hier nicht: `sources.chart_path` zeigt auf
committete Bytes auf der Platte, was für Loth 1866 (gemeinfrei) geht. Der
reservierte Eigenhand-Datensatz kann das nie sein, also müssen die Bytes
den anderen Weg nehmen — in die DB, admin-gesichert, `private, no-store`,
nie öffentlich. Das ist keine Aufweichung von §8: das REPO bleibt frei von
Streifen, und das Archiv bleibt der Master (§8.1).

**Wort-Crops brauchen keinen eigenen Speicher.** Die Streifenzeile merkt
sich, wo ihr Crop in Millimetern begann (`crop_origin_mm`), das Layout des
Bogens sagt, wo jede Wortkiste sitzt, und `width_px` über der Breite des
Schnittbands liefert den Maßstab. Damit schneidet `core/eigenhand/crop.py`
jedes Wort aus jeder Fassung heraus — dieselbe Überlegung, mit der der
Chart-Endpunkt Glyph-Crops aus einem Tafelbild bedient, nur in mm statt in
Tafelpixeln. Senkrecht bleibt der Crop auf voller Streifenhöhe: das
Interessante an einem Wort ist, wie weit es über die Mittellinie reicht
und unter die Grundlinie.

**Was die Schnittstelle auch hier nachrechnet:** Jedes gespeicherte Bild
muss zu einer Fassung gehören, die auf einer gedruckten Zeile beurteilt
wurde — dieselbe „keine Geisterzeilen“-Regel wie bei den Verdikten, einen
Schritt weiter, denn Pixel ohne Verdikt wären ein Bild, das im Bestand
nirgends vorkommt. Der SHA256 wird gegen die Bytes geprüft statt geglaubt
(er ist die Identität der Datei im Archiv), die deklarierten Maße gegen
das Bild (sie SIND der Maßstab des Crops), und wo die Fassung bereits
einen Hash trägt, müssen beide dieselbe Datei benennen. Dieselben Bytes
noch einmal sind ein No-op, andere Bytes unter derselben ID ein Konflikt —
überschrieben wird nie.

Hochgeschoben wird nur auf Verlangen: `sync --mit-streifen`. Die Bilder
sind der reservierte Datensatz, und der Master bleibt das Archiv.

## 8 Ablage und Archiv

`data/samples/own-hand/` ist komplett gitignored bis auf `SOURCE.md` +
`README.md` — eine **bewusste Abweichung** von datenablage.md §1/§4
(„eigene Hand committierbar“): der Scan-Strom ist unbegrenzt und die
eigene Hand gehört zum reservierten Datensatz (Open-Core,
quellen-und-rechte.md §5). Präzedenz ist der Selektiv-Commit von
`data/humanbench/` und die Korpora-Klasse 2. Die Begründung steht als
License-Rationale in der `SOURCE.md`; `DATA_PROVENANCE.md` führt die
Zeile.

Gesichert wird ins **private Archiv-Repository** — dieselbe Clone
außerhalb des Arbeitsbaums, die die DB-Snapshots hält
(`KURRENTSCHRIFT_ARCHIVE`): `snapshot.py` legt je Lauf ein neues
zeitgestempeltes Verzeichnis an (create-only, nie löschen/umbenennen),
kopiert `kartei.json` + Streifenplan voll und Fassungs-/Bogen-
Verzeichnisse **inkrementell** (Pfad- und SHA256-Abgleich — keine
Duplikate), verifiziert vorher jede Prüfsumme gegen die Kartei und
verweigert schrumpfende Läufe. Damit liegen DB-Snapshots (inkl. der
authored Wort-Traces) und Eigenhand-Streifen im SELBEN Reservat — der
gesamte gelernte Datensatz an einem Ort. Regel: **Snapshot nach jeder
Import-Sitzung** (bis dahin sind die Streifen die einzige Kopie).

### 8.1 Wiederherstellung: Repo + Archiv genügen

**Owner-Vorgabe 2026-08-24:** „wenn die DB weg ist, muss man mit normalem
Repo plus Archiv-Repo die wichtigen Tabelleninhalte sowie die Streifen als
Bilder wieder voll herstellen können.“ Seit §7.2 liegen Streifenbilder in
der DB — also muss diese Zusage nachprüfbar sein und nicht bloß plausibel.

Die Arbeitsteilung dafür ist eindeutig:

- Das **Archiv ist der Master** — und zwar der Archiv-BAUM, nicht ein
  einzelner Schnappschuss. `own-hand/<hand>/<stempel>/` enthält
  `kartei.json` (Bögen, Fassungen, Verdikte, Sitzungen), `setup.json`
  (das stehende Setup, `eigenhand_hands`), je Bogen `layout.json` (den
  Geometrie-Vertrag) und je Fassung `streifen.png` + `meta.json`.
  Zusammen ist das alles, was die vier `eigenhand_*`-Tabellen ausmachen.
  **Wichtig für jeden Leser:** `snapshot.py` legt INKREMENTELL ab — was
  in einem früheren Schnappschuss schon liegt, wird übersprungen. Nur der
  erste ist also vollständig; jeder spätere trägt eine komplette Kartei
  neben bloß seinem Zuwachs. Ein Wiederherstellungsweg, der ein
  Verzeichnis liest, bringt genau diesen Zuwachs zurück und meldet Erfolg
  (in der Review zu PR #410 gefunden). Deshalb liest `--from` die
  Schnappschüsse als EINEN geschichteten Baum, neuester zuerst.
- Das **Repo** liefert den Rest: Streifenplan, Geometrie, Migrationen,
  Werkzeuge.
- Der **DB-Snapshot** (`tools/dbsnapshot`) nimmt die Eigenhand-Tabellen
  ohne die PNG-Spalte mit und schreibt ein `strip_hashes`-Manifest. Er ist
  hier nicht die Quelle, sondern die PRÜFUNG: an ihm sieht man, ob DB und
  Archiv auseinandergelaufen sind, bevor der Tag kommt, an dem es zählt.

Das Rezept — dasselbe `sync`, nur mit anderer Quelle, damit der
Wiederherstellungsweg keine zweite, ungeprüfte Implementierung ist:

```bash
uv run alembic upgrade head                       # leere DB, aktuelles Schema
ADMIN_TOKEN=… uv run python -m tools.eigenhand.sync \
    --hand mn-suetterlin \
    --from $KURRENTSCHRIFT_ARCHIVE/own-hand/mn-suetterlin/<stempel> \
    --mit-streifen
```

`--from` nimmt IRGENDEINEN Schnappschuss der Hand: die Geschwister im
selben Archivverzeichnis kommen automatisch dazu (neuester gewinnt), damit
die Inkrementalität oben keine Lücke reißt. Gelesen werden Kartei, Setup,
Layouts und Fassungen daraus statt aus der Arbeitskopie; alles danach ist
der normale Push (Bögen zuerst, dann Verdikte, dann das Setup, dann die
Bilder). Die Wiederholung ist gefahrlos: gleiche Layouts, gleiche Verdikte
und gleiche Bytes sind No-ops.

Und der Lauf meldet Erfolg nur, wenn er einer ist: fehlt zu einer
angenommenen Fassung die Datei oder zu einem Bogen der Kartei sein
`layout.json`, wird erst alles Vorhandene hochgeschoben und dann mit Namen
abgebrochen. Das stehende Setup wird nur gesetzt, wenn der Server KEINES
hat — eine Wiederherstellung darf eine Feder, die anderswo gewechselt
wurde, nicht mit einer alten Kopie überschreiben.

**Drill 2026-08-25**, gegen ein Wegwerf-PostgreSQL, die Arbeitskopie
zwischendurch gelöscht: 1 Bogen, 3 Fassungen, 3 Streifen wiederhergestellt;
die drei SHA256 stimmen mit den Archivdateien überein, `octet_length(png)
= bytes`; ein Wort-Crop („Galoppieren“, 1016×342 aus 2185×342) ließ sich
aus einem wiederhergestellten Streifen schneiden; der zweite Lauf schrieb
nichts. Ein Befund aus dem Drill: Feder/Tinte/Papier bleiben auf den
Fassungen leer, wenn das stehende Setup ERST NACH dem `ingest` erklärt
wurde — die Reihenfolge ist `setup` vor der ersten Sitzung. Was der Drill
NICHT zeigte, weil er den ersten Schnappschuss benutzte: die
Inkrementalitäts-Lücke oben; sie kam aus der anschließenden Review und ist
seither ein eigener Test. Der Weg ist
zusätzlich als Test festgenagelt (`tests/test_eigenhand_restore.py`, ganze
Kette gegen die echte API).

## 9 Anschluss an die Ernte (Phase 5, aufgeschoben)

Die eigene Hand braucht **kein eigenes Chart**: der Duktus-Prior bleibt
die Stil-Tafel (Stufenplan §5), die Streifen liefern Wort-Vorkommen.
Der spätere Weg ist der bestehende: Fits gegen die Stil-Templates,
automatischer Tintenfolger zuerst (`traced`), manuelles Nachfahren im
Wort-Editor, wo er nicht reicht (`authored`, nie überschrieben) →
`instances`/`word_instances` über die Admin-API → `hands`-Zeile
`mn-suetterlin` → Aggregate → „meine Version“. **Offene Frage, hier nur
benannt:** `sources.chart_path` ist repo-relativ — gitignorte Streifen
kann die deployte API nie ausliefern; die Ernte-Integration braucht
dafür eine eigene Entscheidung (lokale Quelle, private Ablage oder
Selektiv-Commit einzelner Referenz-Streifen). Ebenfalls Phase 5:
Offenbacher/Kurrent sind reine Preset-Konfiguration, aber
Kurrent-Schwellzug-Haarlinien brauchen ≥600 DPI und die
Zwei-Kanal-Behandlung; optional ein maschinenlesbarer Bogen-Code, falls
die menschliche Kopf-Bestätigung je fehleranfällig wird.

## 10 Verworfen

- **Tablet-/S-Pen-Erfassung als Primärweg** (Owner, 2026-08-22): bei
  Kurrent bestimmen Federwinkel und Druck die Strichdicke — das liefert
  nur die echte Feder auf Papier. Die S-Pen-Erfassung bleibt, was sie
  heute ist: Nachfahr-Werkzeug über Crops (W3), nicht Schreib-Ersatz.
- **Admin-SPA/API-Import** (Owner, 2026-08-22) — **teilweise überholt am
  2026-08-23** (§7.1): Der SCAN-Upload bleibt verworfen (ingest braucht
  die Datei auf der Platte, die Siebung ist bereits eine lokale
  HTML-Seite, und die Streifen bleiben im Reservat). Verworfen war
  ursprünglich auch die Ansicht selbst; der Owner hat das umgedreht: die
  BUCHFÜHRUNG (welche Streifen wie oft, welche Bögen gedruckt) liegt in
  der DB, und die Werkbank zeigt den Bestand und erzeugt die Druck-PDFs.
  Was rein muss, damit das ohne Pixel geht, steht in §7.1.
- **Streifen-Scans ins Repo committen** (Owner, 2026-08-22): siehe §8 —
  Open-Core-Reservat statt Klasse-1-Commit. Gilt unverändert; die
  Streifen liegen seit 2026-08-24 in der DB (§7.2) und im Archiv, nie im
  Repo.
- **Ganzseiten-Scans in die DB**: hochgeschoben wird der Streifen, nicht
  die Seite. Der Scan ist Zwischenmaterial (`--keep-scan` legt ihn lokal
  ab), der Streifen ist das Belegstück.
- **Fantasiesilben-Drills im Wortvorrat**: nur echte Wörter; Übergänge
  ohne echtes Trägerwort sind für echten Text irrelevant. (Die
  historischen Abb.-20-Drills bleiben, was sie sind: Mess-Specimen der
  1922-Vorlage, kein Schreibprogramm.)
- **Barcode/QR als Bogen-Identität in v1**: gedruckte Klartext-ID +
  menschliche Bestätigung des Kopf-Crops reicht und braucht keine neue
  Abhängigkeit; maschinenlesbarer Code bleibt Phase-5-Option.
- **Ganzseiten-Scans verpflichtend archivieren**: abgelegt werden nur
  die relevanten Streifen (Owner, 2026-08-22); `--keep-scan` bleibt als
  Option.
- **`POST /worksheet` für die Bögen besetzen**: das §15-Reservat
  (WeasyPrint, öffentliches inhaltsbewusstes Übungsblatt) bleibt
  unangetastet.

## 11 Phasen und Umsetzungsstand

| Phase | Inhalt | Stand 2026-08-23 |
|---|---|---|
| 1 | Wortvorrat, Übergangsraum, Streifenplan (`corpus` · `coverage` · `universe` · `gaps` · `pool`) | umgesetzt; Wave 0+1 committet, Plan-Format 2 |
| 2 | Blattgenerator (`geometry` · `pdfgen` · `bogen` · `sheet` · `rasterize`) | umgesetzt; Beispiel-Bogen erzeugt |
| 3 | Einlesen + Siebung (`fiducial` · `ingest` · `page` · `apply` · `kartei`) | umgesetzt; synthetischer E2E-Rauchtest grün |
| 4 | Bericht, Redo, Archiv (`report` · `redo` · `snapshot`) + Ablage-Skelett | umgesetzt |
| 4a | DB-Buchführung + Werkbank-Ansicht (`0024` · `/eigenhand/*` · `sync` · `pull`) | umgesetzt (§7.1) |
| 4b | Streifen + stehendes Setup in der DB, Wort-Crops, Wiederherstellungsweg (`0025` · `crop` · `setup` · `sync --mit-streifen`/`--from`) | umgesetzt (§7.2, §8.1); Drill 2026-08-25 grün |
| 4c | Die drei Blocker der ersten echten Sitzung (`apiclient`-Kennung · `.env` · `core`↛`tools`) + der bedruckbare Bereich (§5) | umgesetzt 2026-08-25 (siehe unten) |
| 5 | Ernte-Anschluss, Kurrent/Offenbacher-Betrieb, optionaler Bogen-Code | aufgeschoben (§9) |

Dazu je Schreibsitzung wiederkehrend: Kalibrier-Schleife der
advance-Tabelle, `gaps`-Kuration neuer Selten-Join-Wörter, neue Wellen.

**Phase 4c — was der erste Anlauf zum echten Bogen zutage förderte.** Alle
drei Fehler waren im synthetischen Rauchtest unsichtbar, weil dieser weder
über Cloudflare geht noch im Deploy-Abbild läuft:

1. **`tools/eigenhand/apiclient.py` schickte keine `User-Agent`-Kennung.**
   urllibs Vorgabe `Python-urllib/3.x` beantwortet Cloudflare vor der API
   mit 403 (Fehler 1010) — `setup`, `sync` und `pull` konnten die
   Produktion also nie erreichen. Der Archiv-Client
   (`tools/wordbench/fetch_fixtures.py`) trägt seit jeher eine Kennung;
   dieser hier hatte keine geerbt. Gemessen: identische Anfrage, nur die
   Kennung getauscht → 403 gegen 401.
2. **Die Werkzeugfamilie las `.env` nicht.** `ADMIN_TOKEN` und
   `KURRENTSCHRIFT_ARCHIVE` stehen dort, aber kein Modul rief
   `load_dotenv` — also brach der Snapshot mit „no archive" ab und die
   API-Aufrufe mit „no admin token", solange die Umgebung nicht von Hand
   gesourct war. Eine Sicherung, die nur nach einem gemerkten Vorspann
   läuft, ist eine Sicherung, die ausfällt. Jetzt lädt jedes der beiden
   Pakete (`tools/eigenhand`, `tools/dbsnapshot`) die Datei beim Import;
   eine gesetzte Variable gewinnt weiterhin.
3. **`core/eigenhand/geometry.py` importierte `tools`** — die
   Fugen-Formen-Tabelle, verzögert innerhalb der Breitenschätzung. Das
   API-Abbild enthält `core/`, aber nicht `tools/`: jeder im Admin
   gedruckte Bogen endete in `ModuleNotFoundError` → 500, und `_guard`
   fängt nur `SystemExit`. Die Tabelle steht ohnehin schon im
   committeten Plan (`forms`, §4 — genau dafür eingeführt), sie wird jetzt
   von dort durchgereicht; `core` greift nicht mehr nach `tools`, und ein
   Test über `core/`, `api/` und `alembic/` hält das fest. Die Geometrie
   ändert sich nicht: über alle 120 Streifen (13 mit Fugen-Wort) sind die
   Kästen bytegleich.

## 12 Prüfsteine

1. **Statistik bleibt je Hand** — Hand-IDs `mn-<stil>`; nie über Hände
   mitteln (Stufenplan §5).
2. **Trainingsdaten, kein Mess-Satz** — keine Bench-Kopfzahl liest aus
   Wortvorrat/Streifenplan; Messungen über Eigenhand-Material nur mit
   separat eingefrorener, vorregistrierter Teilmenge.
3. **Sieb-Disziplin** — Verwurf nur nach Schreibqualität, nie nach
   Verbindungsenge; Ausfälle zufällig, nicht selektiv; best-of über
   Versuche desselben Streifens ist erlaubt.
4. **Append-never** — Streifen werden nie umnummeriert oder umgeschrieben;
   Wellen hängen an.
5. **Kein DB-Schreibpfad** in der ganzen Werkzeugkette: `sync.py` schiebt
   die Buchführung über die admin-gesicherte HTTP-Schnittstelle hoch, nie
   über eine Verbindung zur Datenbank; die Ernte (Phase 5) läuft ebenso.
   Seit §7.2 gehen auch Streifenbilder diesen Weg — aber nur auf
   ausdrückliches `--mit-streifen`, nur admin-gesichert und nie
   öffentlich; das Repo bleibt frei von ihnen, das Archiv bleibt Master.
6. **Archiv create-only** — Snapshots nach jeder Sitzung, nie aufräumen,
   Schrumpfung ist ein Fehler.
7. **Duktus-Prior bleibt die Tafel** — die eigene Hand liefert Vorkommen
   und Statistik, nie eine neue Strichreihenfolge per Bild.

## 13 Offene Fragen

- Ausliefer-/Ablageweg der Streifen für die Ernte-Integration
  (chart_path-Frage, §9) — Entscheidung vor Phase 5.
- Englisch in Sütterlin ist ahistorisch (Fremdwörter schrieb man
  lateinisch); für das Zeitungs-Ziel bewusst in Kauf genommen,
  `lang: en` bleibt filterbar, falls die Hand es später trennen soll.
- Hinweis-Notation der Labels (`Amts*|zeit`): Geschmackssache,
  `--no-hints` existiert; nach den ersten echten Bögen bewerten.
