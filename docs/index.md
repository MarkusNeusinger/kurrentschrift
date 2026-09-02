# Dokumentation

> **Status (2026-08-12): lebend.** Bei jedem neuen, umbenannten oder
> gelöschten Doc unter `docs/` mitzuführen (Schnellzugriff + Baum +
> Abschnittsliste); der Abschnitt „Dokument-Status“ trägt die
> Lifecycle-Aussage je Schicht, damit sie nicht jede Datei einzeln tragen
> muss.
> Schichten in Kurzform: `concepts/` = Designkern — Entscheidungen und die
> Grundsatz-Docs, die daraus folgen (teils bindend, teils lebend) ·
> `reference/` = Nachschlagedokumente, Status je Doc (meist Ist-Stand;
> HTR/Animation/Stil-Analyse tragen den Status ihrer geplanten
> Ausbaustufe) · `schriftkunde/` = statische, quellenbelegte Faktenblätter
> mit eigenem „Stand“-Datum, die dem Code NICHT folgen · `proposals/` =
> Umsetzungs-Vorschläge und ihre Protokolle, Umsetzungsstand im Kopf des
> jeweiligen Docs · `research/` = externe Recherche/Literatur, die Ideen
> liefert und dem Code nie folgt · `notes/` = operative, datierte
> Befund-Journale, die nie fortgeschrieben, nur abgelöst werden.

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(siehe [`reference/sprachregelung.md`](reference/sprachregelung.md) zur
Begründung). Stand: in-progress MVP — Admin-UI und Canonical-Extraktion
laufen, die öffentliche Seite schreibt serverseitig komponierte Wörter
(Federprobe, Tafel, Quiz inkl. Wort-Modus, Schriftkunde, Übungsblätter);
Per-Vorkommen-Fit und die Statistik je Hand sind gebaut (Handmodell H0–H2,
Release v0.22.0) — offen ist H3, die Ablösung der Composer-Konstanten durch
gemessene Hand-Parameter; der H5-Erfassungsweg (eigene Hand) ist vorgezogen
und liest bereits echte Bögen ein
([Eigenhand-Erfassung](proposals/eigenhand-erfassung.md), Phasen 1–4f).

---

## Schnellzugriff

| Ich will… | Gehe zu |
|---|---|
| Wissen, wie aktuell ein Doc ist (bindend · lebend · offen …) | [Dokument-Status](#dokument-status) |
| Einen Fachbegriff oder eine Kennzahl nachschlagen (Duktus, Laufform, `gen_chamfer`, M1–M4 …) | [Glossar](reference/glossar.md) |
| Wissen, was die Endnutzer-Website sein soll | [Vision der Website](concepts/vision.md) |
| Den Weg Scan → Bibliothek → Schreiben → Statistik am Stück verstehen | [Vom Scan zum Schreibsystem](concepts/vom-scan-zum-schreiben.md) |
| Den Architekturkern verstehen | [Architektur-Referenz](concepts/architektur.md) |
| Wissen, wie der MVP konkret zerlegt ist | [MVP-Roadmap](concepts/mvp-roadmap.md) |
| Wissen, warum Name/Domain/Lizenz so gewählt sind | [Naming und OSS-Setup](concepts/naming-und-setup.md) |
| Look & visuelle Identität nachschlagen | [Style-Guide](concepts/style-guide.md) |
| Design-System (Tokens, Typo-Skala, Breiten, Flächen, IA) nachschlagen | [Design-System](concepts/design-system.md) |
| Die drei Federmodelle (Bandzug/Spitz/Redis) & Ziffern/Satzzeichen nachschlagen | [Federmodelle](concepts/federmodelle.md) |
| HTR-Pfad (Transkribus + TrOCR) nachschlagen | [HTR-Integration](reference/htr-integration.md) |
| Animation-Render-Algorithmus nachschlagen | [Animation-Rendering](reference/animation-rendering.md) |
| Stil-Analyse-Pipeline nachschlagen | [Stil-Analyse](reference/styleanalyse.md) |
| Qualitätsmetrik, Glyph-Bench & Loop-Erkenntnisse nachschlagen | [Qualitätsmetrik](reference/qualitaetsmetrik.md) |
| Den blinden Bewertungsdurchgang (Fehler-Taxonomie, Instrument, Vorregistrierung) nachschlagen | [Menschliche Bewertung](reference/menschliche-bewertung.md) |
| Frontend-Stack & Deploy nachschlagen | [Frontend-Stack](reference/frontend-stack.md) |
| Quiz-Wortbank (Quellen, Distraktoren, Fugen-Marker) nachschlagen | [Quiz-Wortbank](reference/quiz-wortbank.md) |
| Öffentliche Render-Endpunkte (`/write/*`) nachschlagen | [Write-API](reference/write-api.md) |
| Dev-Werkzeuge (glyphlab/wordlab/pairlab, Benches, quizgen) nachschlagen | [Werkzeuge](reference/werkzeuge.md) |
| Wissen, welche Crawler/KI-Agenten die Seite lesen dürfen | [Crawler-Richtlinie](reference/crawler-richtlinie.md) |
| Sprache und englischen Stil für Code, Docs, README nachschlagen | [Sprachregelung](reference/sprachregelung.md) |
| Wissen, was ins öffentliche Repo darf | [Quellen- und Rechte-Policy](reference/quellen-und-rechte.md) |
| Den `/data`-Baum verstehen | [Datenablage](reference/datenablage.md) |
| Lese-Regeln (Rund-s, Ligaturen, …) nachschlagen | [Orthographie-Regeln](schriftkunde/orthographie-regeln.md) |
| Schriftkunde-Fakten (Lineatur, Schräglage, Federn) nachschlagen | [Schriftkunde](schriftkunde/allgemein.md) |
| Fakten zu Kurrent / Sütterlin / Offenbacher nachschlagen | [Kurrent](schriftkunde/kurrent.md) · [Sütterlin](schriftkunde/suetterlin.md) · [Offenbacher](schriftkunde/offenbacher.md) |
| Offene Vorschläge für Konzept-Änderungen sehen | [Planänderungen](proposals/planaenderungen.md) |
| Schreib-API, Python-Komposition & Wort-Bench-Plan nachschlagen | [Schreibsystem und Wort-Bench](proposals/schreibsystem-und-wortbench.md) |
| Übergangs-Befund (pairlab: Platzierung · Stubs · Klassen) nachschlagen | [Übergangs-Befund](proposals/uebergaenge-befund.md) |
| Schreibsystem-Redesign (R1–R5: Paar-Matrix, Positions-Rückbau, geerntete Paare, Schräglage) nachschlagen | [Schreibsystem-Redesign](proposals/schreibsystem-redesign.md) |
| Den Handmodell-Stufenplan (Duktus-Prior · Laufformen · Statistik · eigene Hand) nachschlagen | [Handmodell-Stufenplan](proposals/handmodell-stufenplan.md) |
| Die Werkbank-Doktrin (wer liefert welche Stufe · Auftragskorb-Protokoll) nachschlagen | [Optimierungs-Werkbank](proposals/optimierungs-werkbank.md) |
| Den Tintenfolger-Plan (Prüfstand · Referenzsatz · Routen-Duell) nachschlagen | [Tintenfolger](proposals/tintenfolger.md) |
| Die eigene Hand erfassen (Wortvorrat · Bögen · Siebung · Streifenkartei) | [Eigenhand-Erfassung](proposals/eigenhand-erfassung.md) |
| Ein Duell-Verfahren (Kette · Lotse · InkSight · Nullprobe) mit Steckbrief und Versions-Ledger nachschlagen | [Verfahrensseiten](reference/verfahren.md) |
| Ideen-Recherche lesen (Graves-Writer → Recognizer · Synthese-Verfahren · Bildsynthese/Offline-HTG · Plotter-Pipeline) | [Research](#research) |

---

## Struktur der Dokumentation

```
docs/
├── index.md                      # You are here
├── contributing.md               # (EN) Was aktuell hilfreich ist und was noch zu früh ist — englisch, vom README verlinkt
├── concepts/                     # Designkern: Entscheidungen + die Grundsatz-Docs, die daraus folgen
│   ├── vision.md                 # Was die Endnutzer-Website sein soll (Pitch + Zielgruppe + 7 Ziele in 3 Clustern + Leitprinzipien + Nicht-Ziele)
│   ├── vom-scan-zum-schreiben.md # Überblick: Tafel + Wortproben + Nachfahren → Bibliothek → Schreiben → Maßstab → Ernte → Statistik → Schleife; finales System vs. Trainingsgerüst
│   ├── architektur.md            # §1–§17: Analysis-by-Synthesis, Schema, MVP, Animation, HTR, Lese-Lupe, Print, Frontend, Open-Data
│   ├── mvp-roadmap.md            # Operative Zerlegung des MVP (§8) in Schritt 0 + M0–M7
│   ├── style-guide.md            # Visuelle Identität Papier & Tinte: R1–R9-Entscheidungen samt Begründung/Historie (Token-Ist: design-system.md §2)
│   ├── design-system.md          # Verbindliche Bauvorschrift: Tokens, Typo-Skala (19px), Breiten (PageContainer), Flächen, IA, Komponenten
│   ├── federmodelle.md           # Drei Federn, ein Renderpfad: Bandzugfeder-Gesetz, Spitzfeder-Haarstriche, Ziffern/Satzzeichen (joins:false)
│   └── naming-und-setup.md       # Repo-Name, Domain, Lizenz, Verzeichnis-Split, Frontend-Stack, Hosting
├── reference/                    # Policy- und Technik-Dokumente mit Begründung (Status je Doc)
│   ├── glossar.md                # Fachbegriffe & Repo-Redewendungen: Schrift · Architektur · Fit · Metriken · Werkbank · Forschung
│   ├── sprachregelung.md         # Deutsch/Englisch pro Artefakt + englischer Stil (§4: Google-Guide als Referenz-Fallback, Haus-Abweichungen)
│   ├── quellen-und-rechte.md     # Was darf rein, was nicht; PD/CC/NC-SA
│   ├── datenablage.md            # `/data`-Baum, SOURCE.md, Commit-Klassen
│   ├── htr-integration.md        # Transkribus-API + TrOCR-Fallback, PAGE-XML, Free-Tier
│   ├── animation-rendering.md    # stroke-dashoffset (MVP), Canvas-2D-Stroker (post-MVP), WAAPI
│   ├── styleanalyse.md           # Per-Hand-Aggregation, Hinge-Features, Heatmap-Layouts
│   ├── qualitaetsmetrik.md       # Zwei Metriken (Kurrent-Schwellzug §1–4 · Sütterlin-Natürlichkeit §5), bench/Referenzen, Baseline-Historie, Loop-Erkenntnisse + Verworfen; §14 Tintenfolger-Journal mit Eintrags-Register + Headline-Ledger im Kopf
│   ├── menschliche-bewertung.md  # Blinder Urteilsdurchgang über die Fits (tools/humanbench): Fehler-Taxonomie, Instrumentregeln, Vorregistrierung, Aufbewahrung
│   ├── quiz-wortbank.md          # Lese-Quiz-Wortbank: Quellen (Kaeding, Genealogie-Felder), Pin+Runtime-Distraktoren, Fugen-Marker
│   ├── write-api.md              # Öffentliche Render-Endpunkte /write/glyphs + /write/word: Shaping → Komposition → Payload
│   ├── werkzeuge.md              # Dev-Tools unter tools/: Inspektions-Labs + pairlab-Einstiegsskripte, Ernte-Werkzeuge, humanbench/fitview, dbsnapshot, Benches, Duell-Kandidaten (inkpilot · routeg · inksight), quizgen, docs_register
│   ├── verfahren.md              # Verfahrensseiten-Übersicht: Versions-Konvention der Duell-Routen, Register-Regel (Zahlen wohnen in §14)
│   ├── verfahren-kette.md        # Kette: Steckbrief, Stand v5 (K0-S-Wächter-Stack), Arm-Ledger ①–⑨/A1/K-A…K-E2/K0-Z/K0-S/K-D, v6-Anwärter
│   ├── verfahren-lotse.md        # Lotse: Steckbrief, Stand v0.17 (Reservierungs-Veto), Versions-Ledger v0.1–v0.19 + Schienen-Auslauf, offene Blöcke
│   ├── verfahren-inksight.md     # InkSight: Steckbrief, Stand T0 (auf Lineal-Kappe 1,5 unvermessen), Ledger (T0 · B1), stehende Maßnahmen B2–B5
│   ├── verfahren-nullprobe.md    # Nullprobe: Steckbrief, Kontroll-Doktrin (bewusst unversioniert), Mess-Ledger bis L-U aug26
│   ├── crawler-richtlinie.md     # Wer die Seite lesen darf: offen für Suche, KI-Abruf und KI-Training (der Vorbehalt liegt am API-Gate), robots.txt/llms.txt, Cloudflare
│   └── frontend-stack.md         # React+Vite+MUI Build, Deploy auf Cloud Run, i18n, Auth-Routen
├── schriftkunde/                 # Quellengesicherte Fakten zu den Schriften (wächst inkrementell)
│   ├── allgemein.md              # Lineatur, Schräglage, Striche, Federtypen, Chronologie, DACH
│   ├── orthographie-regeln.md    # Lese-Regeln (Rund-s wortintern, Ligaturen, Mischschrift, …)
│   ├── kurrent.md                # Kurrent inkl. Loth-1866-Messung (~50°) vs. um 1900 (60–70°)
│   ├── suetterlin.md             # Sütterlin: 1911, senkrecht, 1:1:1, Gleichzugfeder
│   ├── offenbacher.md            # Offenbacher: Koch 1927, 75–80°, 2:3:2, Bandzugfeder; PD-Quelle 1928
│   ├── zahlen-und-zeichen.md     # Ziffern, Doppelbindestrich, Abkürzungen, ₰/ℳ, genealogische Zeichen
│   ├── tinte-und-material.md     # Eisengallustinte (inkl. Repo-Farben), Federn, Papier, Schulmaterial
│   ├── druckschriften.md         # Fraktur/Schwabacher/Textura vs. Kurrent, Kanzleischrift, Neudörffer
│   ├── lateinische-und-englische-schreibschrift.md  # Abgrenzung Kurrent ↔ lateinische/englische Schreibschrift, Zweischriftigkeit
│   └── digital.md                # Unicode (ſ U+017F, Ligaturen), UNZ/MUFI, Fonts, Transkription
├── proposals/                    # Umsetzungs-Vorschläge und ihre Protokolle (Status je Doc, s. u.)
│   ├── planaenderungen.md        # Staging: §2/§4 Bigramme, §6.1 Positions-Statistik, M4+ core/orthography.py
│   ├── schreibsystem-und-wortbench.md  # Audit 2026-07-01: Schreib-API, core/compose.py-Port, Wort-Bench, Übergangs-Redesign (Phasen A–E)
│   ├── uebergaenge-befund.md     # Befund 2026-07-11: pairlab-Paarsektion — Platzierung dominiert, Stub-Ersatz klassenweise, Optionen O1–O3
│   ├── schreibsystem-redesign.md # Entscheid 2026-07-17: eine Form pro Glyphe (Positions-Rückbau), Paar-Matrix, geerntete Paar-Overrides, Schräglagen-Befund (R1–R5)
│   ├── handmodell-stufenplan.md  # Vorschlag 2026-07-31: Statistik-Schicht füllen (H0–H5) — Instances/Aggregates, Paar-Statistik, Konstanten→Hand-Parameter, eigene Hand
│   ├── optimierungs-werkbank.md  # Entscheid 2026-07-31: EINE Werkbank-Seite + Stufen-/Rollen-Doktrin + work_items-Auftragskorb (W1–W5)
│   ├── tintenfolger.md           # Plan 2026-08-14: Prüfstand (tracebench), nachgefahrener Referenzsatz + Split, Routen-Duell (Kette · Lotse · InkSight · Nullprobe), Optimierungsplan §7, Rettungswege §7.9, offene Arme §7.11
│   └── eigenhand-erfassung.md    # Vorschlag 2026-08-22 (H5-Erfassungsweg): Wortvorrat → Streifenplan → Bögen → Siebung → Streifenkartei/Bestand, DB-Buchführung + Streifen in der DB (§7.1/§7.2)
├── research/                     # Externe Recherche/Literatur — liefert Ideen, folgt dem Code nie
│   ├── bildsynthese-und-stiftbahn.md     # Recherche 2026-08: Offline-HTG auf Kurrent fein-tunen → Trajektorien-Rückgewinnung → Plotter; Datenlage/Lizenzen, Prüfsteine T0–T4
│   ├── graves-handschrift-synthese.md    # Literatur-Report: Graves-2013-Mechanik, Priming/Biasing, Plotter-Pipeline, GAN/Transformer/ScribeTokens, 54 Quellen
│   └── kurrent-writer-and-recognizer.md  # Recherche-Notiz (EN): generativer Writer (Graves 2013) als synthetische Datenquelle → billiger Recognizer
└── notes/                        # Operative, datierte Journale (nicht Designkern)
    ├── audit-2026-09-02-rohbefunde.md  # Vollaudit 2026-09-01/02: Rohberichte der 20 Prüfer (Repo · Website · Werkzeuge · das Geschriebene)
    ├── audit-2026-09-02-synthese.md  # Vollaudit 2026-09-01/02: Rangliste, Parallelplan T1–T14, Fragen an den Autor F1–F11
    ├── quellen-recherche-2026-07.md  # Recherche Juli 2026: geschriebene Wortvorlagen & echte Hände — Rangliste, Absteiger, mögliche Anfragen
    └── stifte-fuer-unterwegs.md  # Stift-/Hardware-Recherche fürs Schreiben unterwegs
```

---

## Dokument-Status

Jedes Doc unter `docs/` trägt seit 2026-08-03 direkt unter der Überschrift
einen Status-Blockquote nach demselben Muster
(`> **Status (JJJJ-MM-TT): <status>.** …`), damit ein Leser ohne Archäologie
sieht, ob er einen Plan, ein Protokoll oder eine Beschreibung des laufenden
Systems vor sich hat. Das Vokabular ist bewusst klein: **bindend** =
entschieden, wird nur durch eine neue Entscheidung geändert (die
Verworfen-Listen bleiben geschlossen); **lebend** = beschreibt den Ist-Stand
des Codes und trägt eine benannte Nachzieh-Pflicht; **teil-umgesetzt** = ein
Teil ist gebaut, der Rest ist ausdrücklich Zukunft (der Kopf sagt, welcher);
**umgesetzt-historisch** = vollständig abgearbeitet oder durch eine andere
Lösung abgelöst, also Entscheidungs- und Messprotokoll statt Arbeitsplan;
**offen** = nichts davon ist gebaut; **Befund-Journal** = datierte
Momentaufnahme, die nie fortgeschrieben, sondern nur durch eine neue Runde
abgelöst wird; **statisch** = quellenbelegtes Nachschlagematerial, das dem
Code nicht folgt. Die `research/`-Notizen folgen dem Code ebenfalls nie
und tragen je nach Natur `offen` (eine Idee mit Bauoption) oder
`Befund-Journal` (eine Literatur-Momentaufnahme). Die neun
`schriftkunde/`-Faktenblätter sind durchweg
statisch und tragen keinen eigenen Kopf — sie führen ihr „Stand:“-Datum
ohnehin in den ersten Zeilen; einzige Ausnahme ist
[`orthographie-regeln.md`](schriftkunde/orthographie-regeln.md), weil dort
Regeln stehen, die noch nicht implementiert sind.

### Lebende Dokumente und ihr Nachzieh-Anlass

| Doc | Nachziehen bei |
|---|---|
| [`index.md`](index.md) | jedem neuen, umbenannten oder gelöschten Doc unter `docs/` (Schnellzugriff + Baum + Abschnittsliste) sowie beim Kopf-Absatz „Stand“, sobald eine Schicht live geht |
| [`contributing.md`](contributing.md) | neuer öffentlicher Route in `app/src/routes/paths.ts`, gefallenem MVP-Gate (`architektur.md` §8) oder Öffnung für externe PRs — betrifft Absatz 1 und „Not yet useful“ |
| [`concepts/vom-scan-zum-schreiben.md`](concepts/vom-scan-zum-schreiben.md) | jeder neuen Stufe im Datenfluss, jeder neuen Admin-Fläche und jeder geschlossenen Lücke — insbesondere der Lücken-Liste am Ende, wenn eines der dort verlinkten Issues (#270–#274) schließt |
| [`concepts/design-system.md`](concepts/design-system.md) | Änderungen an `app/src/styles/paper.ts`, `theme/typography.ts`, `components/PageContainer · Prose · PageHeader · HeaderBar · PublicHeader · PublicFooter`, an der Werkbank-Kopfleiste (`sections/admin/shell/AdminHeader`) oder an der öffentlichen Routen-/Bereichsstruktur (`routes/paths.ts`) |
| [`reference/glossar.md`](reference/glossar.md) | jedem Doc und jedem PR, der einen neuen Fachbegriff, eine neue Kennzahl oder eine neue Redewendung prägt — der Eintrag entsteht im selben PR (Regel auch in `CLAUDE.md` § „Working guardrails“, `.github/copilot-instructions.md` und den Skills `/write-docs` + `/open-pr`) |
| [`reference/write-api.md`](reference/write-api.md) | jeder Änderung an einer `/write/*`-Route (`api/routers/write.py` inkl. `compose_word_payload`), an `core/shaping.py`, `core/compose.py`, `core/pipeline.py::render_payload_for_template`, `api/rendering.py` oder den Cache-Headern in `api/http.py` |
| [`reference/qualitaetsmetrik.md`](reference/qualitaetsmetrik.md) | jeder Änderung an `core/quality.py`, `core/quality_suetterlin.py`, `core/geometry.py`, `core/word_metric.py`, jedem Re-Baseline der eingefrorenen Fixtures und jedem Bench-/Loop-Lauf, der eine Headline bewegt (neuer datierter Abschnitt). **Im selben PR:** der neue §14-Abschnitt bekommt seine Zeile in der Registertabelle am Kopf von §14, eine bewegte Headline ihre Zeile im Headline-Ledger daneben (mit `exported_at` und Digest der Fixture-Wurzel) — erzwungen von `uv run python -m tools.docs_register check` (CI-Job „Docs-Register“) |
| [`reference/menschliche-bewertung.md`](reference/menschliche-bewertung.md) | jeder Änderung am Instrument `tools/humanbench` (Kategorien in `page.py::CATEGORIES`, Stichproben- und Wiederholungsregeln in `build.py`, Darstellung, neue Modi, CLI) und jeder Runde, deren Aufbau vom beschriebenen Verfahren abweicht — die Befunde selbst gehören nach `reference/qualitaetsmetrik.md` |
| [`reference/frontend-stack.md`](reference/frontend-stack.md) | Stack-Versionen (`app/package.json`), Routenkarte (`app/src/routes/paths.ts`), Build/Deploy (`app/cloudbuild.yaml`, `api/cloudbuild.yaml`, `app/Dockerfile`, `app/nginx.conf`, Cloud-Run-Parameter), Auslieferungs-Header (`app/security-headers.conf`, `api/security_headers.py`, `api/routers/csp.py`), Admin-Gate (`api/auth.py`, `core/config.py`, Cloudflare Access) oder Origin-Gate (`api/origin_gate.py`, `infra/cloudflare/` — der Apex-Worker, an dessen Konfiguration §5 hängt) |
| [`reference/werkzeuge.md`](reference/werkzeuge.md) | jedem neuen, umbenannten oder entfernten Verzeichnis/Einstiegsskript unter `tools/` und jeder geänderten CLI (Flags, Modulpfade, `viz`-Extra, `--live`) |
| [`reference/quiz-wortbank.md`](reference/quiz-wortbank.md) | Änderungen an `tools/quizgen/corpus.py`/`similarity.py`/`build.py` (inkl. Neuberechnung von `quiz_words.json` → Wortzahl und Era-Verteilung im Kopf nachziehen), am TS-Zwilling `app/src/sections/quiz/wordBank.ts`/`useQuizEngine.ts` und bei jeder Re-Seed-Migration nach dem Muster `0011_quiz_words_reseed.py` |
| [`reference/crawler-richtlinie.md`](reference/crawler-richtlinie.md) | jeder Änderung an `app/public/robots.txt` oder `app/public/llms.txt` (Gruppen, Content-Signals, Reihenfolge, `Disallow`-Pfade) und an den AI-Crawl-Control-/Bot-Regeln der Cloudflare-Zone |
| [`reference/verfahren.md`](reference/verfahren.md) samt den vier Verfahrensseiten (`verfahren-kette.md` · `verfahren-lotse.md` · `verfahren-inksight.md` · `verfahren-nullprobe.md`) | jedem §14-Eintrag, der einen Arm oder eine Stufe eines Duell-Verfahrens misst (adoptiert oder verworfen) — Ledger-Zeile im selben PR; bei Adoption zusätzlich „Aktueller Stand“ der betroffenen Seite und die Stand-/„seit“-Spalte der Übersicht. Erzwungen von `tools.docs_register check` (CI-Job „Docs-Register“) |

Drei weitere Dokumente sind **abschnittsweise** pflichtig, obwohl sie als
Ganzes nicht lebend sind:
[`reference/animation-rendering.md`](reference/animation-rendering.md) §1/§3
(bei Änderungen an `WrittenGlyph.tsx`, `useStrokeReveal.ts`,
`strokeTiming.ts`, `core/widths.py`),
[`reference/styleanalyse.md`](reference/styleanalyse.md) Schichten 1–2 (bei
Änderungen an `core/pipeline.py::_measurements`, `core/aggregate.py` oder den
Aggregat-Tabellen) und
[`reference/quellen-und-rechte.md`](reference/quellen-und-rechte.md) §5 (bei
jeder Änderung an Admin-Gates auf Lese-Endpunkten, am Origin-Gate davor
(`api/origin_gate.py`, `infra/cloudflare/`), an den gitignorten
Bench-Fixtures oder an committeten gerenderten Artefakten).

---

## Concepts

Architektur und Entscheidungen mit ihrer Begründung — was bewusst gewählt
und was bewusst verworfen wurde.

- **[Vision der Website](concepts/vision.md)** — was die Endnutzer-Website
  unter `kurrentschrift.ink` sein soll: Pitch, Zielgruppe, **Leitprinzipien**,
  **sieben Ziele in drei Clustern** — Schreiben (Einstieg · Schreiben üben ·
  animierte Buchstaben), Lesen (Lesen üben · Lese-Hilfe + Lese-Lupe),
  Forschung (Stil-Analyse + Hände vergleichen · Offene Datensätze) —
  Nicht-Ziele, Verhältnis zur bestehenden Landschaft
- **[Vom Scan zum Schreibsystem](concepts/vom-scan-zum-schreiben.md)** — die
  eine durchgehende Erzählung des Datenflusses: Tafel + Wortproben +
  Nachfahren → Buchstaben-Bibliothek → Schreiben → Maßstab → Ernte →
  Statistik je Hand → Optimierungs-Schleife, dazu „finales System vs.
  Trainingsgerüst", warum es kein „a vor b" gibt, Aktualität des
  Gespeicherten und die bekannten Lücken; Einstieg vor der
  Architektur-Referenz
- **[Architektur-Referenz](concepts/architektur.md)** — §1–§17:
  Analysis-by-Synthesis, Duktus-Prior, Library-Einheit
  `(style, glyph, variant)` (seit dem Positions-Rückbau R2, Migration
  `0017`), Schwellzug vs. Tinte, dreistufige
  Qualitätspipeline, MVP (vier Gates), Testwörter, Reihenfolge, plus
  Animation-Render, Stil-Analyse, HTR-Integration, Lese-Lupe, Print,
  Frontend-Architektur, Open-Data
- **[MVP-Roadmap](concepts/mvp-roadmap.md)** — operative Zerlegung von §8
  in Schritt 0 + M0–M7 mit vier Validierungs-Gates und Verifikations-Plan
- **[Naming und OSS-Setup](concepts/naming-und-setup.md)** — Name, Domain
  `kurrentschrift.ink`, Monorepo-Layout, MIT-Lizenz, Frontend-Stack
  (anyplot-Stil), Hosting (Cloud Run), README als Pitch
- **[Style-Guide](concepts/style-guide.md)** — visuelle Identität
  „Papier & Tinte": R1–R9-Entscheidungen samt Begründung/Historie; den
  Token-Ist-Stand trägt [`design-system.md`](concepts/design-system.md)
  §2 (Quelle im Code: `styles/paper.ts`)
- **[Design-System](concepts/design-system.md)** — die verbindliche
  Bauvorschrift der öffentlichen Seiten: Farb-Tokens, 19-px-Typo-Leiter,
  PageContainer-Breiten (760/1152/1280), Flächenregel, IA, Komponenten
- **[Federmodelle](concepts/federmodelle.md)** — drei Federn, ein
  Renderpfad: Bandzugfeder-Gesetz, Spitzfeder-Haarstriche,
  Ziffern/Satzzeichen (`joins: false`)

---

## Reference

Policy- und Technik-Dokumente.

- **[Glossar](reference/glossar.md)** — Fachbegriffe und Repo-Redewendungen
  in sechs Themenblöcken (Schrift & Paläografie · Architektur &
  Datenmodell · Mess- und Fit-Vokabular · Metriken & Benchmarks ·
  Werkbank & Prozess · Extern/Forschung), je Eintrag eine
  allgemeinverständliche Erklärung plus Anker-Vokabular (Formel, Modul,
  Konstante) zum Weitergraben; alphabetischer Schnellindex oben.
  **Nachzieh-Pflicht: jeder PR, der einen Begriff oder eine Kennzahl
  prägt, legt hier einen Eintrag an**
- **[Sprachregelung](reference/sprachregelung.md)** — Code immer Englisch,
  interne Docs Deutsch, README Englisch, Website v1 Deutsch
- **[Quellen- und Rechte-Policy](reference/quellen-und-rechte.md)** — Süß
  nie ins Repo, §72 UrhG, gemischte Lizenzen in Korpora, Variante 0 = Loth 1866
- **[Datenablage](reference/datenablage.md)** — `/data`-Baum, drei
  Commit-Klassen, `SOURCE.md`-Pflichtfelder, Verlinkungsregel
- **[HTR-Integration](reference/htr-integration.md)** — Transkribus-API
  als Default-Pfad (Free-Tier, ≈0,12 €/Seite, CER 5–7 %), TrOCR
  `dh-unibe/trocr-kurrent` als optionaler Self-Hosted-Fallback (CER 2,65 %),
  PAGE-XML-Repräsentation, FastAPI-Adapter
- **[Animation-Rendering](reference/animation-rendering.md)** —
  MVP-Stand `stroke-dashoffset` auf Centerline; Post-MVP Canvas-2D-Stroker
  mit Offset-Kurven aus Centerline + Width-Profile; Width-Profile-Resolver
  pro Schriftfamilie (Kurrent voller Schwellzug / Sütterlin konstant);
  WAAPI-Choreographie
- **[Stil-Analyse](reference/styleanalyse.md)** — Per-Instanz-Stats
  (existiert), Per-Hand-Aggregation (M5(C)+), Hinge-/Δn-Hinge-Features
  nach Bulacu/Schomaker (optional), Heatmap-Layouts via Observable Plot +
  D3.js
- **[Frontend-Stack](reference/frontend-stack.md)** — React 19 + Vite +
  MUI 9 + React Router 7 + `react-helmet-async` + `react-i18next`,
  Build/Deploy auf Cloud Run, Auth-geschützte Admin-Routen,
  Komponenten-Map
- **[Quiz-Wortbank](reference/quiz-wortbank.md)** — Lese-Quiz-Wortschatz:
  Quellen (Kaeding 1897/98, Grundwortschatz, Genealogie-Felder),
  Distraktor-Modell (ein Pin + Laufzeit-Ziehung nach `similarity`),
  Fugen-Marker-Regeln, Lizenz-Haltung, Erweiterungs-Workflow
- **[Write-API](reference/write-api.md)** — die öffentlichen
  Render-Endpunkte `/write/glyphs` + `/write/word`: Shaping →
  Komposition → Payload, Cache-Verhalten, `missing`-Semantik,
  Render-Cache-Konsum im Frontend
- **[Qualitätsmetrik](reference/qualitaetsmetrik.md)** — zwei Metriken
  (Kurrent-Schwellzug §1–§4 · Sütterlin-Natürlichkeit §5), Frozen-
  Reference-Regel, Baseline-Historie, Loop-Erkenntnisse + Verworfen —
  Pflichtlektüre vor jedem `/optimize-glyphs`-Lauf
- **[Menschliche Bewertung](reference/menschliche-bewertung.md)** — der
  blinde Urteilsdurchgang über die Fits (`tools/humanbench`): die
  sechsteilige Fehler-Taxonomie mit operativen Definitionen, die
  Konstruktionsregeln des Instruments samt ihrer Begründung (geschichtete
  Stichprobe, blinde Wiederholungen, Rückhaltemenge, Marker-Regeln), die
  Vorregistrierung des Auswerteplans, Ablauf einer Runde, Provenienz-Stempel,
  der paarige Vorher/Nachher-Durchgang und die Wortrunde auf der
  Echtheitsfrage (§8a) — die Methode, die Befunde stehen in der
  Qualitätsmetrik
- **[Werkzeuge](reference/werkzeuge.md)** — Einstieg in die Dev-Tools
  unter `tools/`: die Inspektions-Labs glyphlab/wordlab/pairlab
  (matplotlib-Overlays, `--extra viz`, Ausgabe nach `temp/`) samt der
  messenden pairlab-Einstiegsskripte, die beiden Ernte-Werkzeuge, der
  Urteils-Durchgang `tools/humanbench` (build · page · analyse) mit dem
  Betrachter `tools/fitview`, der Archiv-Schnappschuss `tools/dbsnapshot`
  sowie Verweise auf glyphbench/wordbench und quizgen
- **[Verfahrensseiten](reference/verfahren.md)** — das Register der
  Tintenfolger-Routen: je Verfahren ein Steckbrief (Anzeige-Name,
  Code-Heimat, aktuell adoptierte Konstanten) plus Versions-/Arm-Ledger
  mit Verdikt und §14-Anker — [Kette](reference/verfahren-kette.md) ·
  [Lotse](reference/verfahren-lotse.md) ·
  [InkSight](reference/verfahren-inksight.md) ·
  [Nullprobe](reference/verfahren-nullprobe.md); die Zahlen selbst
  wohnen ausschließlich in der Qualitätsmetrik §14
- **[Crawler-Richtlinie](reference/crawler-richtlinie.md)** — wer die
  Seite lesen darf: offen — Suche, KI-Abruf/Zitat und KI-Training erlaubt
  (`ai-train=yes`, Entscheid 2026-08-28; der Open-Core-Vorbehalt liegt am
  Auth-Gate der API, nicht in der robots.txt), `robots.txt` als Quelle der
  Wahrheit, Cloudflare als Durchsetzung + Verworfen (darunter die frühere
  Abruf-ja/Training-nein-Politik)

---

## Schriftkunde

Quellengesicherte Fakten zu den Schriften selbst — ausschließlich aus
frei zugänglichen Quellen, jede Angabe mit Beleg; wächst inkrementell.

- **[Allgemein](schriftkunde/allgemein.md)** — Lineatur/Vierliniensystem,
  Schräglage (Messkonvention zur Grundlinie, 90° = senkrecht), Striche
  (Grund-/Haarstrich, Schwellzug/Gleichzug), Federtypen, Kurzchronologie,
  Österreich/Schweiz/Liechtenstein
- **[Orthographie-Regeln](schriftkunde/orthographie-regeln.md)** — Rund-s
  wortintern an Morphemgrenzen, Ligatur-Satz, Lesefallen, Mischschrift,
  ältere Buchstabenformen
- **[Kurrent](schriftkunde/kurrent.md)** — Geschichte, Schräglagen-Spanne
  inkl. eigener Loth-1866-Messung (~50°) vs. Kurrent um 1900 (60–70°),
  Buchstaben-Besonderheiten (ſ/s, u-Bogen, Ligaturen)
- **[Sütterlin](schriftkunde/suetterlin.md)** — 1911, senkrecht, 1:1:1,
  Gleichzugfeder; Begriffs-Falle „Sütterlin" als Sammelbegriff
- **[Offenbacher](schriftkunde/offenbacher.md)** — Koch 1927, 75–80°,
  2:3:2, Bandzugfeder; gemeinfreie Primärquelle von 1928 auf Commons
- **[Zahlen und Zeichen](schriftkunde/zahlen-und-zeichen.md)** — Ziffern,
  Doppelbindestrich, Abkürzungszeichen (Nasalstrich, ꝛc.), ₰/ℳ/fl.,
  genealogische Zeichen
- **[Tinte und Material](schriftkunde/tinte-und-material.md)** —
  Eisengallustinte (frisch → oxidiert → gealtert, inkl. Bezug zur
  Repo-Palette), Federkiel/Stahlfeder, Papier, Schiefertafel
- **[Druckschriften](schriftkunde/druckschriften.md)** — Fraktur ≠
  Kurrent, „altdeutsche Schrift"-Falle, Schwabacher/Textura,
  Kanzleischrift, Neudörffer
- **[Lateinische/englische Schreibschrift](schriftkunde/lateinische-und-englische-schreibschrift.md)** —
  Abgrenzung der Kurrent zur lateinischen und englischen Schreibschrift
  (Copperplate), Zweischriftigkeit (Deutschsprachige lernten beides)
- **[Digital](schriftkunde/digital.md)** — Unicode-Lage (ſ, ß, Ligaturen
  ohne Codepoints), UNZ 1/MUFI, freie Fonts, Transkriptionspraxis

---

## Proposals

Umsetzungs-Vorschläge und ihre Protokolle. Maßgeblich ist der
Status-Kopf des jeweiligen Dokuments; die Einträge sind hier nach ihrem
Statuswort gruppiert, damit Plan und Protokoll auf einen Blick
auseinanderfallen.

**bindend** — gilt als Doktrin weiter:

- **[Optimierungs-Werkbank](proposals/optimierungs-werkbank.md)** —
  Richtungsentscheid 2026-07-31: EINE Admin-Werkbank statt fragmentierter
  Tabs, plus die **bindende Stufen-/Rollen-Doktrin** — manuell hinzufügen
  nur bei Ground Truth (Tafel-Duktus, Wort-Nachfahrung), alles Generierte
  wird bemängelt — und das `work_items`-Protokoll (Triage-Pflicht der KI,
  Regel-Fix vor Override, `resolution`-Format, Rückgabe an den Autor) —
  *Status: bindend (W1–W5 gebaut, §3–§5 von der API erzwungene Doktrin;
  die Alt-Seiten sind mit dem Admin-Redesign 2026-08 in den drei
  Ansichten Buchstaben · Übergänge · Wörter aufgegangen)*

**teil-umgesetzt** — aktive Pläne mit offenem Rest:

- **[Handmodell-Stufenplan](proposals/handmodell-stufenplan.md)** —
  Vorschlag 2026-07-31: das Rollenmodell (Tafel = Duktus-Prior ·
  Wortproben **einer** Hand = Form-Vorbild · fremde Hände = Kontext)
  bestätigt und die leere Statistik-Schicht in Stufen gefüllt —
  H0 Bench-Anschluss der Laufformen, H1 `instances`/`hands`
  persistieren, H2 Paar-Statistik, H3 Konstanten → Hand-Parameter
  (Vereinfachungs-Gate), H4 zweite historische Hand, H5 eigene Hand —
  *Status: teil-umgesetzt (H0–H2 in v0.22.0 ausgeliefert, H3–H5 offen;
  der H5-Erfassungsweg läuft vorgezogen über die Eigenhand-Erfassung)*
- **[Eigenhand-Erfassung](proposals/eigenhand-erfassung.md)** — Vorschlag
  2026-08-22 (H5-Erfassungsweg): die eigene Hand als Trainingsdaten mit
  echter Feder — kuratierter **Wortvorrat** (nur echte Wörter, alt +
  modern, Englisch getaggt) → deterministischer, append-never
  **Streifenplan** (Set-Cover-Startdeckung, dann gleichmäßiger Ausbau
  häufig UND selten, Breite vor Wiederholung) → gedruckte **Bögen** mit
  Wortkästen, Lineatur und **Passmarken** (Scanner UND Handyfoto) →
  **Siebung** je Zeile (Sieb-Disziplin aus M2) → selbst-zuordenbare
  **Fassungen** in der lokalen **Streifenkartei**, Soll/Ist im
  **Bestandsbericht** (Übergangsraum-gewichtet), Sicherung ins private
  Archiv (create-only, inkrementell); Werkzeuge `tools/eigenhand/` —
  *Status: teil-umgesetzt (Phasen 1–4f gebaut, Phase 5 Ernte-Anschluss
  offen)*
- **[Tintenfolger](proposals/tintenfolger.md)** — Plan 2026-08-14 zum
  §6-Nachtrag des Bildsynthese-Journals: das automatische Nachfahren der
  Wortproben messbar machen und verbessern — eingefrorener
  `authored`-Referenzsatz (10 Wörter, append-never-Split), Prüfstand
  `tools/tracebench` (`dtw_xh` · papertreues AIoU gegen die Tintenmaske ·
  Richtungs-Chamfer · Fehlerzähler an Kreuzungen/Marken/Retraces), Route A
  (Verfeinerungsstufe auf dem Kettenfit: Form-Prior → Proximal-Term) gegen
  Route B (InkSight roh; Fine-Tune als unmöglich verworfen → eigenes
  kleines Modell auf Engine-Paaren) und Route G (die prior-freie
  geometrische Kontrolle `tools/routeg`, Anzeige-Name **Nullprobe**:
  beziffert, was der Duktus-Prior kauft — Referenz-Code ist MATLAB,
  darum eigene Minimalfassung); Anzeige-Namen aller Verfahren im
  Glossar-Eintrag „Duell-Namen" —
  *Status: teil-umgesetzt (Duell komplett gemessen; adoptiert sind Kette
  v5, Lotse v0.17, die Lineal-Stände v2.1/L-U und — auf Autor-Entscheid
  nach der ersten humanbench-Wortrunde — die Laufform LF11 „glatte
  Zeile"; Optimierungsplan §7 in Arbeit, offene Arme in §7.11)*
- **[Planänderungen](proposals/planaenderungen.md)** — vier Vorschläge:
  §2/§4 systematische Bigramm-Extraktion aus Beispieltext; §3/§6.1
  Positions-Verteilung datengetrieben; M4+-Modul `core/orthography.py`
  (Vorschlag A — `position` als Lehrtafel-Rolle — ist freigegeben und in
  `architektur.md` §3 eingearbeitet) — *Status: teil-umgesetzt (nur
  Vorschlag D offen; A durch R2 überholt, B als R3 gebaut, C im
  H1-Aggregat)*

**Befund-Journal** — Messprotokoll, Begründungsquelle der Konstanten:

- **[Übergangs-Befund](proposals/uebergaenge-befund.md)** — Befund
  2026-07-11 aus `tools/pairlab` (unabhängige Paar-Sektion, 87 Vorkommen):
  Platzierung ist der größte Einzelfehler, die Standard-Diagonale ist
  generisch richtig, Hoch-Exits (d-Schleife, Deckstrich-Bögen, r-Arm)
  ersetzen die Kopplungs-Stubs klassenweise — Lösungsoptionen O1–O3;
  **O1 + O2 (B-Seite) umgesetzt** (Compose-Loop `jul11`), der A-seitige
  d-Stub-Trim gemessen und verworfen; §5c trägt Stufe A des Kettenfits
  (Issue #278, 248 Vorkommen) samt Nachmessung der beiden
  Stufe-B-Vorbedingungen nach — *Status: Befund-Journal (Stand 2026-08-03;
  O1/O2 umgesetzt, O3 durch R3 überholt, Stufe B freigegeben mit Auflagen)*

**umgesetzt-historisch** — abgearbeitete Protokolle:

- **[Schreibsystem und Wort-Bench](proposals/schreibsystem-und-wortbench.md)** —
  Audit 2026-07-01: öffentliche Schreib-API (Buchstabe + Wort) statt
  `/diagnostic`-Mitnutzung, Port der Wortkomposition nach
  `core/compose.py`, Wort-Bench gegen verifizierte PD-Wortvorlagen
  (gleiche Hand je Tafel), Übergangs-Redesign mit Exit-Klassen (Phasen A–E)
  — *Status: umgesetzt-historisch (Phasen A–D gebaut, E in anderer Gestalt
  erledigt)*
- **[Schreibsystem-Redesign](proposals/schreibsystem-redesign.md)** —
  Richtungsentscheid 2026-07-17 (angenommen; R1–R5 sind umgesetzt,
  offen ist allein der Live-Import der Ernte-Entwürfe): eine Form
  pro Glyphe mit Positions-Rückbau (R2), Paar-Matrix-Ansicht im Admin
  (R1), sparsame **geerntete** Paar-Overrides mit Versal-Priorität als
  Konkretisierung von Vorschlag B (R3), Platzierungs-Rest + O3-Neubewertung
  (R4) und der neue Schräglagen-Befund (d-Oberschleife lehnt in der
  verbundenen Schrift ~4–5° rechts gegenüber der Chart-Zelle; R5) —
  *Status: umgesetzt-historisch (R1–R5 gebaut; offen allein der Live-Import
  der Ernte-Entwürfe)*

---

## Research

Externe Recherche- und Literatur-Notizen — sie liefern Ideen und
Vergleichsmaßstäbe, folgen dem Code aber nie; Status je Doc (`offen` =
Idee mit Bauoption, `Befund-Journal` = Literatur-Momentaufnahme).

- **[Bildsynthese und Stiftbahn](research/bildsynthese-und-stiftbahn.md)** —
  Recherche-Runde 2026-08-13 zum bildbasierten Parallelweg: den Stand der
  Offline-HTG-Modelle (GAN · Transformer · Diffusion; Favoriten
  DiffusionPen/One-DM, das Emuru-Font-Pretraining-Rezept), die Daten- und
  Lizenzlage für Kurrent-Trainingsbilder (CC-BY-Sätze, die Sütterlin-Ära-
  Lücke), die Offline→Online-Rückgewinnung (InkSight, TRACE, Kettenfit
  als prior-geführte Route; `word_instances` als einzige
  Online-Kurrent-Ground-Truth) und die kleinen Prüfsteine T0–T4 bis zur
  geplotteten Postkarte — *Status: Befund-Journal (Literatur-Momentaufnahme
  vom 2026-08-13 samt Nachtrag 2026-08-14; fortgeschrieben wird sie nicht —
  abgelöst hat sie die Kampagne in `proposals/tintenfolger.md`)*
- **[Kurrent: Writer → Recognizer](research/kurrent-writer-and-recognizer.md)** —
  Recherche-Notiz (Englisch): warum Graves 2013 (RNN-Handschrift-Synthese)
  der Anker für den generativen Writer ist, und wie derselbe Writer als
  synthetische Datenquelle mit perfektem Ground-Truth einen billigen,
  browser-lauffähigen Recognizer trainiert (ein Forward-Pass statt
  Analysis-by-Synthesis zur Inferenzzeit) — *Status: offen (Recherche-Notiz,
  nichts gebaut)*
- **[Graves-Handschrift-Synthese](research/graves-handschrift-synthese.md)** —
  Literatur-Report (KI-Recherche, redaktionell bereinigt): die
  Graves-2013-Mechanik im Detail (MDN, Soft-Window, Priming/Biasing),
  Datenbedarf, das Online/Offline-Dilemma, die Plotter-Pipeline zur
  physischen Postkarte und die moderne Verfahrens-Landschaft
  (ScrabbleGAN/HiGAN · HWT/ScriptViT · ScribeTokens) samt
  54-Quellen-Bibliografie — *Status: Befund-Journal*

---

## Notes

Operative, datierte Journale außerhalb des Designkerns — nie
fortgeschrieben, nur durch eine neue Runde abgelöst.

- **[Vollaudit 2026-09-01/02 — Rohbefunde](notes/audit-2026-09-02-rohbefunde.md)**
  — die Rohberichte der 20 unabhängigen Prüfer (Repo · Doku · Skills · API ·
  core · Werkzeuge · Frontend · Inhalte · Live-Seite · das Geschriebene · CI ·
  Sicherheit · Aufgaben-Rückstand); jeder Befund mit Schwere, Kategorie,
  Aufwand, Beleg und Vorschlag
- **[Vollaudit 2026-09-01/02 — Synthese](notes/audit-2026-09-02-synthese.md)** —
  Gesamtbild und Stärken, 39 gereihte Befunde, Parallelplan T1–T14 und die
  Fragen an den Autor F1–F11; der Vorschlag des Synthese-Prüfers — die
  Entscheidungen stehen nicht dort, sondern in den PRs, die daraus folgen
- **[Quellen-Recherche Juli 2026](notes/quellen-recherche-2026-07.md)** —
  Recherche-Runde 30./31.07.2026 zu geschriebenen Wortvorlagen und
  echten Händen: Rangliste (SUB-Leitfaden ✅ committet, Berger-Reihe,
  Dressel, Erker …), Absteiger mit Rechte-Begründung, festgehaltene
  mögliche Anfragen (nicht beauftragt)
- **[Stifte für unterwegs](notes/stifte-fuer-unterwegs.md)** — Stift-/
  Hardware-Recherche fürs Kurrent-Schreiben unterwegs

---

## Mitmachen

- **[Contributing Guide](contributing.md)** (EN) — was aktuell hilfreich ist und was noch zu früh ist (englisch, weil vom README für das externe Publikum verlinkt — siehe [`sprachregelung.md`](reference/sprachregelung.md) §1)

---

## Weitere Ressourcen

- **[README](../README.md)** — Projekt-Pitch (Englisch, öffentlich)
- **[CITATION.cff](../CITATION.cff)** — Zitations-Metadaten
- **[CLAUDE.md](../CLAUDE.md)** — Hinweise für Claude Code
