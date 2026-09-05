# Dokumentation

> **Status (2026-09-04): lebend.** Die **Karte** über `docs/`. Die
> Invariante: **genau eine Zeile je `.md`-Datei unter `docs/`**, mit ihrer
> Aufgabe und dem Anlass, sie aufzumachen — heute 59 Zeilen für 59
> Dateien, gegen den Dateibaum prüfbar. Mehr steht hier bewusst nicht;
> jede Aussage über ein Doc gehört in dieses Doc, sonst veraltet sie hier
> zuerst. Am 2026-09-04 von ~12 500 auf rund 4 100 Token gekürzt: das
> Lifecycle-Vokabular und die Tabelle der Nachzieh-Pflichten sind nach
> [`dokument-status.md`](dokument-status.md) gezogen, die ausführlichen
> Doc-Beschreibungen, der Verzeichnisbaum und der Schnellzugriff sind
> entfallen — sie sagten dreimal dasselbe.
> Nachzieh-Anlass: jedes neue, umbenannte oder gelöschte Doc unter `docs/`
> bekommt hier seine Zeile, beziehungsweise verliert sie.

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(Begründung in [`reference/sprachregelung.md`](reference/sprachregelung.md)).
Stand: in-progress MVP — Admin-UI und Canonical-Extraktion laufen, die
öffentliche Seite schreibt serverseitig komponierte Wörter (Federprobe,
Tafel, Quiz inkl. Wort-Modus, Schriftkunde, Übungsblätter); Per-Vorkommen-Fit
und Statistik je Hand sind gebaut (Handmodell H0–H2, v0.22.0) — offen ist H3,
die Ablösung der Composer-Konstanten durch gemessene Hand-Parameter; der
H5-Erfassungsweg liest bereits echte Bögen ein.

**Für eine KI-Sitzung:** die Pflichtlektüre und die Lesepfade je Aufgabe
stehen in [`../CLAUDE.md`](../CLAUDE.md) § „Read these before substantive
work“ — von dort führt der kürzeste Weg hierher, nicht umgekehrt.
Fachbegriffe schlägt man in
[`reference/kurzglossar.md`](reference/kurzglossar.md) nach (77 Begriffe,
Kurzfassung) oder im vollen [`reference/glossar.md`](reference/glossar.md).

---

## concepts/ — der Designkern

Entschiedene Architektur und die Grundsatz-Docs, die daraus folgen.

| Doc | Wofür | Wann aufmachen |
|---|---|---|
| [vision.md](concepts/vision.md) | Was die Endnutzer-Website sein soll: Pitch, Zielgruppe, sieben Ziele in drei Clustern, Leitprinzipien, Nicht-Ziele | Bevor man entscheidet, ob ein Feature überhaupt dazugehört |
| [vom-scan-zum-schreiben.md](concepts/vom-scan-zum-schreiben.md) | Der Datenfluss am Stück: Tafel + Wortproben → Bibliothek → Schreiben → Maßstab → Ernte → Statistik → Schleife | Als Einstieg vor der Architektur-Referenz, und wenn unklar ist, welche Stufe ein Problem betrifft |
| [architektur.md](concepts/architektur.md) | §1–§17, bindend: Analysis-by-Synthesis, Schema, Ligatur-Ausnahme, Schwellzug vs. Tinte, MVP-Gates, Post-MVP-Entwürfe | Bei jeder Frage „Glyphe, Variante oder Abweichung?“ — §1 ist der Index über alle Sektionen |
| [mvp-roadmap.md](concepts/mvp-roadmap.md) | Der Ist-Stand des MVP: Schritt 0 + M0–M7 mit vier Validierungs-Gates | Wenn die Frage „ist das schon gebaut?“ lautet — architektur.md §8/§10 sagt nur die Reihenfolge |
| [design-system.md](concepts/design-system.md) | **Bindende** Bauvorschrift der öffentlichen Seiten: Tokens, 19-px-Typo-Leiter, Breiten, Flächenregel, IA, Komponenten | Vor jeder Änderung an öffentlichem Styling |
| [style-guide.md](concepts/style-guide.md) | Die visuelle Identität „Papier & Tinte“ als Entscheidungs-Historie R1–R9 | Wenn man wissen will, **warum** ein Token so aussieht (der Ist-Stand steht im Design-System) |
| [federmodelle.md](concepts/federmodelle.md) | Drei Federn, ein Renderpfad: Bandzugfeder-Gesetz, Spitzfeder-Haarstriche, Ziffern/Satzzeichen | Bei allem, was Strichbreiten erzeugt oder misst |
| [naming-und-setup.md](concepts/naming-und-setup.md) | Name, Domain, MIT-Lizenz, Monorepo-Layout, Stack- und Hosting-Wahl | Bei Fragen zu Repo-Struktur, Lizenz oder Domain |

---

## reference/ — zum Nachschlagen

Policy- und Technik-Dokumente, Status je Doc.

| Doc | Wofür | Wann aufmachen |
|---|---|---|
| [kurzglossar.md](reference/kurzglossar.md) | 77 Begriffe, die in Code, Skills und PRs wirklich vorkommen — je ein bis zwei Sätze | Beim Einstieg in eine Sitzung; für Details führt jeder Eintrag ins volle Glossar |
| [glossar.md](reference/glossar.md) | Das volle Vokabular in sechs Themenblöcken, mit Modul- und Konstanten-Anker; alphabetischer Schnellindex oben | Wenn ein Begriff im Kurzglossar fehlt oder der Anker gebraucht wird. **Ein PR, der einen Begriff prägt, legt hier den Eintrag an** |
| [sprachregelung.md](reference/sprachregelung.md) | Welche Sprache welches Artefakt trägt; §4 der englische Stil-Fallback | Vor dem Schreiben von README, Docs, Commit- oder PR-Text |
| [quellen-und-rechte.md](reference/quellen-und-rechte.md) | Was ins Repo darf: PD/CC/NC-SA, §72 UrhG, §5 die Open-Core-Absicherung | Vor jedem Daten-Commit und bei jeder Frage zu Lizenzen |
| [datenablage.md](reference/datenablage.md) | Der `/data`-Baum, drei Commit-Klassen, `SOURCE.md`-Pflichtfelder | Wenn eine Datei nach `/data` soll |
| [qualitaetsmetrik.md](reference/qualitaetsmetrik.md) | Die **Regeln** der Messlatte: zwei Metriken (eine pro Schrift), Frozen-Reference-Regel, Baseline-Historie, Verworfen-Listen | Vor jedem Bench-Lauf und bei jeder Metrik-Frage |
| [messjournal.md](reference/messjournal.md) | Die **Läufe**: §14, 81 datierte Abschnitte mit Vorregistrierung, Zahlen und Verdikt | Wenn eine Zahl oder ein Verdikt gesucht wird — **über das Register im Kopf**, nie die ganze Datei |
| [messjournal-archiv.md](reference/messjournal-archiv.md) | Abgelegte §14-Abschnitte und die Regel, wann einer hierher zieht | Wenn ein Abschnitt im Journal fehlt, oder beim Ablegen eines fertigen Arms |
| [menschliche-bewertung.md](reference/menschliche-bewertung.md) | Die **Methode** des blinden Urteilsdurchgangs (`tools/humanbench`): Taxonomie, Instrumentregeln, Vorregistrierung | Bevor eine Bewertungsrunde gebaut oder ausgewertet wird (die Befunde stehen im Messjournal) |
| [verfahren.md](reference/verfahren.md) | Die Übersicht der Duell-Routen samt Versions-Konvention und der Regel, dass eine Verfahrensseite Register ist und keine zweite Wahrheit | Bevor man eine der vier Routenseiten liest oder eine Ledger-Zeile schreibt |
| [verfahren-kette.md](reference/verfahren-kette.md) | Kette: Steckbrief, Stand v5 (Wächter-Stack), Arm-Ledger ①–⑨ / K-A…K-E2 / K0-Z / K0-S / K-D | Wenn ein Kette-Arm gemessen, adoptiert oder zitiert wird |
| [verfahren-lotse.md](reference/verfahren-lotse.md) | Lotse: Steckbrief, Stand v0.17 (Reservierungs-Veto), Versions-Ledger v0.1–v0.19, offene Blöcke | Dasselbe für den Lotsen |
| [verfahren-inksight.md](reference/verfahren-inksight.md) | InkSight: Steckbrief, Stand T0, Ledger (T0 · B1), stehende Maßnahmen B2–B5 | Dasselbe für InkSight |
| [verfahren-nullprobe.md](reference/verfahren-nullprobe.md) | Nullprobe: Steckbrief, die Kontroll-Doktrin (bewusst unversioniert), Mess-Ledger | Dasselbe für die prior-freie Kontrolle |
| [werkzeuge.md](reference/werkzeuge.md) | Der Index über `tools/`: Labs, Benches, Ernte, Eigenhand, Snapshot, Changelog-Schnitt | Bevor man ein Werkzeug aufruft oder ein neues anlegt |
| [write-api.md](reference/write-api.md) | Die öffentlichen Render-Endpunkte `/write/glyphs` + `/write/word`: Shaping → Komposition → Payload, Cache, `missing` | Bei jeder Änderung an einer `/write/*`-Route |
| [frontend-stack.md](reference/frontend-stack.md) | Stack, Routenkarte, i18n-Soll, Deploy, Admin- und Origin-Gate, Crawler-Prerender | Bei Build-, Deploy-, Auth- oder Routing-Fragen |
| [crawler-richtlinie.md](reference/crawler-richtlinie.md) | Wer die Seite lesen darf (offen, inkl. KI-Training) und wo der Vorbehalt stattdessen sitzt | Vor jeder Änderung an `robots.txt`, `llms.txt` oder `nginx.conf` |
| [quiz-wortbank.md](reference/quiz-wortbank.md) | Der Lese-Quiz-Wortschatz: Quellen, Distraktor-Modell, Fugen-Marker, Erweiterungs-Workflow | Beim Erweitern oder Neuberechnen der Wortbank |
| [htr-integration.md](reference/htr-integration.md) | Der geplante Lesepfad: Transkribus als Default, TrOCR als Fallback, PAGE-XML | Wenn Volltext-Erkennung gebaut wird |
| [animation-rendering.md](reference/animation-rendering.md) | `stroke-dashoffset` (MVP) und Canvas-2D-Stroker (post-MVP), Width-Profile-Resolver | Bei Änderungen am Animationspfad |
| [styleanalyse.md](reference/styleanalyse.md) | Per-Instanz-, Per-Hand- und Hinge-Feature-Schichten, Heatmap-Layouts | Bei Arbeit an der Statistik-Schicht |

---

## schriftkunde/ — quellenbelegte Fakten

Statische Faktenblätter mit eigenem „Stand“-Datum; sie folgen dem Code
nicht. Aufmachen, wenn eine Behauptung über die Schrift selbst belegt
werden muss.

| Doc | Wofür |
|---|---|
| [allgemein.md](schriftkunde/allgemein.md) | Lineatur, Schräglage (90° = senkrecht), Striche, Federtypen, Chronologie, DACH |
| [orthographie-regeln.md](schriftkunde/orthographie-regeln.md) | Lese-Regeln: Rund-s wortintern, Ligaturen, Mischschrift — teils noch nicht implementiert |
| [kurrent.md](schriftkunde/kurrent.md) | Kurrent: Merkmale und Chronologie, inkl. der gemessenen Loth-1866-Schräglage (~50°) vs. 60–70° um 1900 |
| [suetterlin.md](schriftkunde/suetterlin.md) | Sütterlin: 1911, senkrecht, Zonen 1:1:1, Gleichzugfeder |
| [offenbacher.md](schriftkunde/offenbacher.md) | Offenbacher: Koch 1927, 75–80°, Zonen 2:3:2, Bandzugfeder |
| [zahlen-und-zeichen.md](schriftkunde/zahlen-und-zeichen.md) | Ziffern, Doppelbindestrich, Abkürzungen, ₰/ℳ, genealogische Zeichen |
| [tinte-und-material.md](schriftkunde/tinte-und-material.md) | Eisengallustinte (inkl. Repo-Farben), Federn, Papier, Schulmaterial |
| [druckschriften.md](schriftkunde/druckschriften.md) | Fraktur, Schwabacher, Textura und Kanzleischrift gegen die Kurrent abgegrenzt |
| [lateinische-und-englische-schreibschrift.md](schriftkunde/lateinische-und-englische-schreibschrift.md) | Abgrenzung zur lateinischen und englischen Schreibschrift, Zweischriftigkeit |
| [digital.md](schriftkunde/digital.md) | Unicode-Lage (ſ, ß, Ligaturen ohne Codepoint), UNZ/MUFI, Fonts, Transkription |

---

## proposals/ — Vorschläge und ihre Protokolle

Maßgeblich ist der Status-Kopf des jeweiligen Docs.

| Doc | Wofür | Status |
|---|---|---|
| [optimierungs-werkbank.md](proposals/optimierungs-werkbank.md) | EINE Admin-Werkbank, die **Stufen-/Rollen-Doktrin** und das `work_items`-Protokoll (Triage-Pflicht, Regel-Fix vor Override, Rückgabe an Autor), §6 Sperr-Doktrin | bindend — **Pflichtlektüre vor jedem Korb-Auftrag** |
| [handmodell-stufenplan.md](proposals/handmodell-stufenplan.md) | Die Statistik-Schicht in Stufen H0–H5 füllen | teil-umgesetzt (H0–H2 gebaut) |
| [eigenhand-erfassung.md](proposals/eigenhand-erfassung.md) | Die eigene Hand als Trainingsdaten: Wortvorrat → Streifenplan → Bögen → Siebung → Streifenkartei → Bestand | teil-umgesetzt (Phasen 1–4f) |
| [tintenfolger.md](proposals/tintenfolger.md) | Die Wortbahn-Kampagne: Referenzsatz, Routen-Duell, Optimierungsplan §7, Rettungswege §7.9, offene Arme §7.11 | teil-umgesetzt (Duell gemessen) |
| [planaenderungen.md](proposals/planaenderungen.md) | Staging offener Konzept-Änderungen (Bigramme, Positions-Statistik, `core/orthography.py`) | teil-umgesetzt (nur Vorschlag D offen) |
| [uebergaenge-befund.md](proposals/uebergaenge-befund.md) | Der Paar-Befund von `pairlab`: Platzierung dominiert, Stub-Ersatz klassenweise; §5c Kettenfit Stufe A | Befund-Journal |
| [schreibsystem-und-wortbench.md](proposals/schreibsystem-und-wortbench.md) | Audit 2026-07-01: Schreib-API, `core/compose.py`-Port, Wort-Bench, Übergangs-Redesign | umgesetzt-historisch |
| [schreibsystem-redesign.md](proposals/schreibsystem-redesign.md) | R1–R5: eine Form pro Glyphe (Positions-Rückbau), Paar-Matrix, geerntete Overrides, Schräglagen-Befund | umgesetzt-historisch |

---

## research/ und notes/

`research/` liefert Ideen und folgt dem Code nie; `notes/` sind datierte
Journale, die nur durch eine neue Runde abgelöst werden. Beide sind
Nachschlagequellen, keine Pläne.

| Doc | Wofür |
|---|---|
| [research/bildsynthese-und-stiftbahn.md](research/bildsynthese-und-stiftbahn.md) | Offline-HTG, Trajektorien-Rückgewinnung, Plotter-Pipeline, Daten-/Lizenzlage — abgelöst durch die Tintenfolger-Kampagne |
| [research/graves-handschrift-synthese.md](research/graves-handschrift-synthese.md) | Literatur-Report zur Graves-2013-Mechanik, Priming/Biasing, moderne Verfahren, 54 Quellen |
| [research/kurrent-writer-and-recognizer.md](research/kurrent-writer-and-recognizer.md) | (EN) Generativer Writer als synthetische Datenquelle für einen billigen Recognizer |
| [notes/audit-2026-09-02-synthese.md](notes/audit-2026-09-02-synthese.md) | Vollaudit 2026-09-01/02: 39 gereihte Befunde, Parallelplan T1–T14, Fragen F1–F11, Erledigungsstand |
| [notes/audit-2026-09-02-rohbefunde.md](notes/audit-2026-09-02-rohbefunde.md) | Dieselbe Runde als Rohberichte der 20 Prüfer, jeder Befund mit Beleg |
| [notes/serve-image-importgraph-2026-09-04.md](notes/serve-image-importgraph-2026-09-04.md) | Nachmessung zum Serve-only-Image: was `import api.main` lädt, was die Pakete wiegen, zwei Wege mit ihrem Preis — geändert wurde nichts; Nachtrag `sep05` misst image-förmig nach und teilt den Import nach Modulen auf |
| [notes/quellen-recherche-2026-07.md](notes/quellen-recherche-2026-07.md) | Geschriebene Wortvorlagen und echte Hände: Rangliste, Absteiger, mögliche Anfragen |
| [notes/stifte-fuer-unterwegs.md](notes/stifte-fuer-unterwegs.md) | Stift- und Hardware-Recherche fürs Schreiben unterwegs |

---

## Querschnitt — die Dateien direkt unter `docs/`

| Doc | Wofür | Wann aufmachen |
|---|---|---|
| [index.md](index.md) | Diese Karte | Beim Suchen eines Docs |
| [dokument-status.md](dokument-status.md) | Das Lifecycle-Vokabular (bindend · lebend · offen …), die Stand-Block-Regel und die Tabelle der Nachzieh-Pflichten je Doc | Beim Anlegen oder Umstufen eines Docs, und wenn ein Code-Diff ein Doc mitzieht |
| [contributing.md](contributing.md) | (EN) Was aktuell hilfreich ist und was noch zu früh ist; vom README fürs externe Publikum verlinkt | Wenn eine öffentliche Route oder ein MVP-Gate fällt |

Außerhalb von `docs/`: [README](../README.md) (der öffentliche Pitch,
Englisch) · [CITATION.cff](../CITATION.cff) (Zitations-Metadaten) ·
[CLAUDE.md](../CLAUDE.md) (die Anweisungen für Claude Code, mit der
Pflichtlektüre und den Lesepfaden).
