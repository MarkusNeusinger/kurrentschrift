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

**Der Streifenplan** (`tools/eigenhand/streifen.json`, committet) ist der
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

**Trainingsdaten, kein Mess-Satz.** Der Wortvorrat und der Streifenplan
wachsen; KEINE Bench-Kopfzahl liest je aus ihnen. Sollte je eine Messung
über Eigenhand-Material gewünscht sein, wird dafür eine Teilmenge
separat eingefroren und vorregistriert (Frozen-Reference-Doktrin,
qualitaetsmetrik.md).

## 5 Bogen

Ein Bogen ist ein A4-Blatt aus offenen Streifen: Kopf („Sütterlin ·
Bogen 12“ + Maschinen-ID `mn-suetterlin-B0012` + Datum), vier
**Passmarken** (8×8-mm-Quadrate, Zentren 7/203 × 7/290 mm; links oben mit
3-mm-Lochung als Orientierungs-Donut), je Zeile die Streifen-ID und pro
Wort ein **Kasten mit Lineatur** — Bandlinien nur im Kastenbereich, die
Gassen bleiben tintenfrei (16 mm zwischen den Zeilen: 4 mm
Beschriftungszone + 12 mm Abstand). Presets aus
`app/src/lib/lineatur.ts` portiert und per Test gepinnt (Sütterlin 1:1:1
bei 6 mm x-Höhe senkrecht; Offenbacher 2:3:2/5 mm/77°; Kurrent
2:1:2/2,5 mm/65° mit Schräglagen-Hilfslinien im Kasten). Sütterlin-Pitch
34 mm → **Default 7 Zeilen** (`--rows` konfigurierbar). Kastenbreite =
8 mm Vorlauf + Σ advance(glyph_key) in
x-Höhen (`geometry.py::ADVANCE_XH`, Startwerte; **Kalibrier-Schleife**:
nach dem ersten beschriebenen Blatt werden die Konstanten gegen die
gemessenen Tintenbreiten nachgezogen).

**Schnittband und Schnittmarken (Owner, 2026-08-23):** jede Zeile hat ein
**Schnittband** — das Rechteck, zu dem der Streifen geschnitten wird.
Feste Spalten (x = 12 … 197 mm) und feste Polster (4 mm über der
Oberlinie, 3 mm unter der Klartext-Zeile), also **für jede Zeile eines
Stils dieselbe Höhe und dieselbe Breite** (Sütterlin: 185 × 29 mm),
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
aus demselben Grund beginnt die erste Zeile bei y = 22 mm). Die
Streifen-ID steht im oberen Polster INNERHALB des Schnittbands, damit
ein geschnittener Streifen für sich zuordenbar bleibt (§7); die
Stiftmarke steht bewusst außerhalb.

Der Import schneidet digital genau am Schnittband (`layout.json`-Feld
`cut_mm`): Papierstreifen und `streifen.png` sind damit dasselbe
Rechteck, und jede abgelegte Fassung eines Stils hat identische
Pixelmaße.

**Stiftmarke je Zeile:** rechts neben dem Schreibfeld trägt jede Zeile
EIN 5-mm-Kästchen (Spalte ab x = 202 mm, jenseits des Schnittbands,
einmalig im Kopf mit „ok“ beschriftet). Dort ist die Hand am Zeilenende
ohnehin, und die Passmarken
belegen nur die Seitenecken — die Spalte kostet also keine Schreibbreite
(die eingefrorenen Streifen füllen die 180 mm voll aus). Die Regel ist
bewusst binär (Owner, 2026-08-23): **Kreuz oder Haken drin = ok, leer =
nicht ok.** Ein Kästchen statt zweier hält den Bogen bei einer einzigen
Stiftbewegung; der Preis ist, dass eine vergessene Marke als „nicht ok“
liest — die harmlose Richtung, denn der Streifen wandert dann nur zurück
in die Druck-Warteschlange, statt ungeprüft abgelegt zu werden.

Klartext-Labels stehen in normaler Latin-Type unter den Kästen
(Leitsatz Lesbarkeit; WinAnsi hat ohnehin kein ſ). Als Schreib-Hinweis
zeigt das Label die Fugen-Form, wo eine existiert (`Amts*|zeit`, `*` =
erzwungenes Schluss-s) — der eine Fall, in dem das Shaping von den
einmal gelernten Standardregeln abweicht; `--no-hints` schaltet ab.

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

**Neuaufnahme ergänzt** (Owner-Entscheidung): `redo.py S0037 S0055`
stellt Streifen wieder in die Warteschlange; alte angenommene Fassungen
bleiben Trainingsmaterial, sofern nicht ausdrücklich `--retire`
(Status `zurückgezogen`, Datei bleibt, zählt nicht mehr). Ein
Redo-Eintrag erlischt mit der nächsten angenommenen Fassung.

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
- **Admin-SPA/API-Import** (Owner, 2026-08-22): lokale Werkzeuge unter
  `tools/` genügen; kein Upload-Pfad, kein Deployment, Scans bleiben
  lokal. Die Werkbank-Doktrin bleibt unberührt.
- **Streifen-Scans ins Repo committen** (Owner, 2026-08-22): siehe §8 —
  Open-Core-Reservat statt Klasse-1-Commit.
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

| Phase | Inhalt | Stand 2026-08-22 |
|---|---|---|
| 1 | Wortvorrat, Übergangsraum, Streifenplan (`corpus` · `coverage` · `universe` · `gaps` · `pool`) | umgesetzt; Wave 0 committet |
| 2 | Blattgenerator (`geometry` · `pdfgen` · `sheet` · `rasterize`) | umgesetzt; Beispiel-Bogen erzeugt |
| 3 | Einlesen + Siebung (`fiducial` · `ingest` · `page` · `apply` · `kartei`) | umgesetzt; synthetischer E2E-Rauchtest grün |
| 4 | Bericht, Redo, Archiv (`report` · `redo` · `snapshot`) + Ablage-Skelett | umgesetzt |
| 5 | Ernte-Anschluss, Kurrent/Offenbacher-Betrieb, optionaler Bogen-Code | aufgeschoben (§9) |

Dazu je Schreibsitzung wiederkehrend: Kalibrier-Schleife der
advance-Tabelle, `gaps`-Kuration neuer Selten-Join-Wörter, neue Wellen.

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
5. **Kein DB-Schreibpfad** in der ganzen Werkzeugkette; die Ernte (Phase 5)
   läuft, wenn sie kommt, über die Admin-API wie heute.
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
