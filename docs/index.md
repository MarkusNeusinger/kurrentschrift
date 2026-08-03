# Dokumentation

> **Status (2026-08-03): lebend.** Bei jedem neuen, umbenannten oder
> gelöschten Doc unter `docs/` mitzuführen (Schnellzugriff + Baum +
> Abschnittsliste); der Abschnitt „Dokument-Status“ trägt die
> Lifecycle-Aussage je Schicht, damit sie nicht jede Datei einzeln tragen
> muss.
> Schichten in Kurzform: `concepts/` = bindende Entscheide · `reference/` =
> je Doc lebend oder bindend · `schriftkunde/` = statische, quellenbelegte
> Faktenblätter mit eigenem „Stand“-Datum, die dem Code NICHT folgen ·
> `proposals/` = Umsetzungsstand im Kopf des jeweiligen Docs · `notes/` =
> datierte Befund-Journale, die nie fortgeschrieben, nur abgelöst werden.

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(siehe [`reference/sprachregelung.md`](reference/sprachregelung.md) zur
Begründung). Stand: in-progress MVP — Admin-UI und Canonical-Extraktion
laufen, die öffentliche Seite schreibt serverseitig komponierte Wörter
(Federprobe, Tafel, Quiz inkl. Wort-Modus, Schriftkunde, Übungsblätter);
Per-Vorkommen-Fit und die Statistik je Hand sind gebaut (Handmodell H0–H2,
Release v0.22.0) — offen ist H3, die Ablösung der Composer-Konstanten durch
gemessene Hand-Parameter.

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
| Frontend-Stack & Deploy nachschlagen | [Frontend-Stack](reference/frontend-stack.md) |
| Quiz-Wortbank (Quellen, Distraktoren, Fugen-Marker) nachschlagen | [Quiz-Wortbank](reference/quiz-wortbank.md) |
| Öffentliche Render-Endpunkte (`/write/*`) nachschlagen | [Write-API](reference/write-api.md) |
| Dev-Werkzeuge (glyphlab/wordlab/pairlab, Benches, quizgen) nachschlagen | [Werkzeuge](reference/werkzeuge.md) |
| Wissen, welche Crawler/KI-Agenten die Seite lesen dürfen | [Crawler-Richtlinie](reference/crawler-richtlinie.md) |
| Sprache für Code, Docs, README nachschlagen | [Sprachregelung](reference/sprachregelung.md) |
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

---

## Struktur der Dokumentation

```
docs/
├── index.md                      # You are here
├── contributing.md               # (EN) Was aktuell hilfreich ist und was noch zu früh ist — englisch, vom README verlinkt
├── concepts/                     # Architektur, Philosophie, getroffene Entscheidungen
│   ├── vision.md                 # Was die Endnutzer-Website sein soll (Pitch + Zielgruppe + 7 Ziele in 3 Clustern + Leitprinzipien + Nicht-Ziele)
│   ├── vom-scan-zum-schreiben.md # Überblick: Tafel + Wortproben + Nachfahren → Bibliothek → Schreiben → Maßstab → Ernte → Statistik → Schleife; finales System vs. Trainingsgerüst
│   ├── architektur.md            # §1–§17: Analysis-by-Synthesis, Schema, MVP, Animation, HTR, Lese-Lupe, Print, Frontend, Open-Data
│   ├── mvp-roadmap.md            # Operative Zerlegung des MVP (§8) in Schritt 0 + M0–M7
│   ├── style-guide.md            # Visuelle Identität Papier & Tinte: Tokens (styles/paper.ts), Typografie, R1–R9-Entscheidungen
│   ├── design-system.md          # Verbindliche Bauvorschrift: Tokens, Typo-Skala (19px), Breiten (PageContainer), Flächen, IA, Komponenten
│   ├── federmodelle.md           # Drei Federn, ein Renderpfad: Bandzugfeder-Gesetz, Spitzfeder-Haarstriche, Ziffern/Satzzeichen (joins:false)
│   └── naming-und-setup.md       # Repo-Name, Domain, Lizenz, Verzeichnis-Split, Frontend-Stack, Hosting
├── reference/                    # Policy- und Technik-Dokumente mit Begründung
│   ├── glossar.md                # Fachbegriffe & Repo-Redewendungen: Schrift · Architektur · Fit · Metriken · Werkbank · Forschung
│   ├── sprachregelung.md         # Deutsch/Englisch pro Artefakt
│   ├── quellen-und-rechte.md     # Was darf rein, was nicht; PD/CC/NC-SA
│   ├── datenablage.md            # `/data`-Baum, SOURCE.md, Commit-Klassen
│   ├── htr-integration.md        # Transkribus-API + TrOCR-Fallback, PAGE-XML, Free-Tier
│   ├── animation-rendering.md    # stroke-dashoffset (MVP), Canvas-2D-Stroker (post-MVP), WAAPI
│   ├── styleanalyse.md           # Per-Hand-Aggregation, Hinge-Features, Heatmap-Layouts
│   ├── qualitaetsmetrik.md       # Zwei Metriken (Kurrent-Schwellzug §1–4 · Sütterlin-Natürlichkeit §5), bench/Referenzen, Baseline-Historie, Loop-Erkenntnisse + Verworfen
│   ├── quiz-wortbank.md          # Lese-Quiz-Wortbank: Quellen (Kaeding, Genealogie-Felder), Pin+Runtime-Distraktoren, Fugen-Marker
│   ├── write-api.md              # Öffentliche Render-Endpunkte /write/glyphs + /write/word: Shaping → Komposition → Payload
│   ├── werkzeuge.md              # Dev-Tools unter tools/: glyphlab/wordlab/pairlab (Inspektions-Labs), Benches, quizgen
│   ├── crawler-richtlinie.md     # Wer die Seite lesen darf: Suchmaschinen, KI-Abruf vs. KI-Training, robots.txt/llms.txt, Cloudflare
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
├── proposals/                    # Vorgeschlagene Konzept-Änderungen (Umsetzungs-Stand je Eintrag, s. u.)
│   ├── planaenderungen.md        # Staging: §2/§4 Bigramme, §6.1 Positions-Statistik, M4+ core/orthography.py
│   ├── schreibsystem-und-wortbench.md  # Audit 2026-07-01: Schreib-API, core/compose.py-Port, Wort-Bench, Übergangs-Redesign (Phasen A–E)
│   ├── uebergaenge-befund.md     # Befund 2026-07-11: pairlab-Paarsektion — Platzierung dominiert, Stub-Ersatz klassenweise, Optionen O1–O3
│   ├── schreibsystem-redesign.md # Entscheid 2026-07-17: eine Form pro Glyphe (Positions-Rückbau), Paar-Matrix, geerntete Paar-Overrides, Schräglagen-Befund (R1–R5)
│   ├── handmodell-stufenplan.md  # Vorschlag 2026-07-31: Statistik-Schicht füllen (H0–H5) — Instances/Aggregates, Paar-Statistik, Konstanten→Hand-Parameter, eigene Hand
│   ├── optimierungs-werkbank.md  # Entscheid 2026-07-31: EINE Werkbank-Seite + Stufen-/Rollen-Doktrin + work_items-Auftragskorb (W1–W5)
│   └── kurrent-writer-and-recognizer.md  # Recherche-Notiz (EN): generativer Writer (Graves 2013) als synthetische Datenquelle → billiger Recognizer
└── notes/                        # Recherchematerial & operative Notizen (nicht Designkern)
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
Code nicht folgt. Die neun `schriftkunde/`-Faktenblätter sind durchweg
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
| [`concepts/design-system.md`](concepts/design-system.md) | Änderungen an `app/src/styles/paper.ts`, `theme/typography.ts`, `components/PageContainer · Prose · PageHeader · PublicHeader · PublicFooter` oder an der öffentlichen Routen-/Bereichsstruktur (`routes/paths.ts`) |
| [`reference/glossar.md`](reference/glossar.md) | jedem Doc und jedem PR, der einen neuen Fachbegriff, eine neue Kennzahl oder eine neue Redewendung prägt — der Eintrag entsteht im selben PR (Regel auch in `CLAUDE.md` § „Working guardrails“, `.github/copilot-instructions.md` und den Skills `/write-docs` + `/open-pr`) |
| [`reference/write-api.md`](reference/write-api.md) | jeder Änderung an einer `/write/*`-Route (`api/routers/write.py` inkl. `compose_word_payload`), an `core/shaping.py`, `core/compose.py`, `core/pipeline.py::render_payload_for_template`, `api/rendering.py` oder den Cache-Headern in `api/http.py` |
| [`reference/qualitaetsmetrik.md`](reference/qualitaetsmetrik.md) | jeder Änderung an `core/quality.py`, `core/quality_suetterlin.py`, `core/geometry.py`, `core/word_metric.py`, jedem Re-Baseline der eingefrorenen Fixtures und jedem Bench-/Loop-Lauf, der eine Headline bewegt (neuer datierter Abschnitt) |
| [`reference/frontend-stack.md`](reference/frontend-stack.md) | Stack-Versionen (`app/package.json`), Routenkarte (`app/src/routes/paths.ts`), Build/Deploy (`app/cloudbuild.yaml`, `api/cloudbuild.yaml`, `app/Dockerfile`, `app/nginx.conf`, Cloud-Run-Parameter) oder Admin-Gate (`api/auth.py`, `core/config.py`, Cloudflare Access) |
| [`reference/werkzeuge.md`](reference/werkzeuge.md) | jedem neuen, umbenannten oder entfernten Verzeichnis/Einstiegsskript unter `tools/` und jeder geänderten CLI (Flags, Modulpfade, `viz`-Extra, `--live`) |
| [`reference/quiz-wortbank.md`](reference/quiz-wortbank.md) | Änderungen an `tools/quizgen/corpus.py`/`similarity.py`/`build.py` (inkl. Neuberechnung von `quiz_words.json` → Wortzahl und Era-Verteilung im Kopf nachziehen), am TS-Zwilling `app/src/sections/quiz/wordBank.ts`/`useQuizEngine.ts` und bei jeder Re-Seed-Migration nach dem Muster `0011_quiz_words_reseed.py` |
| [`reference/crawler-richtlinie.md`](reference/crawler-richtlinie.md) | jeder Änderung an `app/public/robots.txt` oder `app/public/llms.txt` (Gruppen, Content-Signals, Reihenfolge, `Disallow`-Pfade) und an den AI-Crawl-Control-/Bot-Regeln der Cloudflare-Zone |

Drei weitere Dokumente sind **abschnittsweise** pflichtig, obwohl sie als
Ganzes nicht lebend sind:
[`reference/animation-rendering.md`](reference/animation-rendering.md) §1/§3
(bei Änderungen an `WrittenGlyph.tsx`, `useStrokeReveal.ts`,
`strokeTiming.ts`, `core/widths.py`),
[`reference/styleanalyse.md`](reference/styleanalyse.md) Schichten 1–2 (bei
Änderungen an `core/pipeline.py::_measurements`, `core/aggregate.py` oder den
Aggregat-Tabellen) und
[`reference/quellen-und-rechte.md`](reference/quellen-und-rechte.md) §5 (bei
jeder Änderung an Admin-Gates auf Lese-Endpunkten, an den gitignorten
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
  „Papier & Tinte": Tokens (`styles/paper.ts`), Typografie,
  R1–R9-Entscheidungen samt Begründung/Historie
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
- **[Werkzeuge](reference/werkzeuge.md)** — Einstieg in die Dev-Tools
  unter `tools/`: die Inspektions-Labs glyphlab/wordlab/pairlab
  (matplotlib-Overlays, `--extra viz`, Ausgabe nach `temp/`), Verweise auf
  glyphbench/wordbench und quizgen
- **[Crawler-Richtlinie](reference/crawler-richtlinie.md)** — wer die
  Seite lesen darf: KI-Abruf/Zitat erlaubt, KI-Training abgelehnt
  (`ai-train=no` als Nutzungsvorbehalt), `robots.txt` als Quelle der
  Wahrheit, Cloudflare als Durchsetzung + Verworfen

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

Vorgeschlagene Änderungen an den Konzept-Dokumenten. Der Umsetzungs-Stand
ist je Eintrag unterschiedlich (einige sind inzwischen weitgehend
umgesetzt) — maßgeblich ist der Status-Kopf des jeweiligen Dokuments.

- **[Planänderungen](proposals/planaenderungen.md)** — vier Vorschläge:
  §2/§4 systematische Bigramm-Extraktion aus Beispieltext; §3/§6.1
  Positions-Verteilung datengetrieben; M4+-Modul `core/orthography.py`
  (Vorschlag A — `position` als Lehrtafel-Rolle — ist freigegeben und in
  `architektur.md` §3 eingearbeitet) — *Status: teil-umgesetzt (nur
  Vorschlag D offen; A durch R2 überholt, B als R3 gebaut, C im
  H1-Aggregat)*
- **[Schreibsystem und Wort-Bench](proposals/schreibsystem-und-wortbench.md)** —
  Audit 2026-07-01: öffentliche Schreib-API (Buchstabe + Wort) statt
  `/diagnostic`-Mitnutzung, Port der Wortkomposition nach
  `core/compose.py`, Wort-Bench gegen verifizierte PD-Wortvorlagen
  (gleiche Hand je Tafel), Übergangs-Redesign mit Exit-Klassen (Phasen A–E)
  — *Status: umgesetzt-historisch (Phasen A–D gebaut, E in anderer Gestalt
  erledigt)*
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
- **[Handmodell-Stufenplan](proposals/handmodell-stufenplan.md)** —
  Vorschlag 2026-07-31: das Rollenmodell (Tafel = Duktus-Prior ·
  Wortproben **einer** Hand = Form-Vorbild · fremde Hände = Kontext)
  bestätigt und die leere Statistik-Schicht in Stufen gefüllt —
  H0 Bench-Anschluss der Laufformen, H1 `instances`/`hands`
  persistieren, H2 Paar-Statistik, H3 Konstanten → Hand-Parameter
  (Vereinfachungs-Gate), H4 zweite historische Hand, H5 eigene Hand —
  *Status: teil-umgesetzt (H0–H2 in v0.22.0 ausgeliefert, H3–H5 offen)*
- **[Optimierungs-Werkbank](proposals/optimierungs-werkbank.md)** —
  Richtungsentscheid 2026-07-31: EINE Admin-Werkbank statt fragmentierter
  Tabs, plus die **bindende Stufen-/Rollen-Doktrin** — manuell hinzufügen
  nur bei Ground Truth (Tafel-Duktus, Wort-Nachfahrung), alles Generierte
  wird bemängelt — und das `work_items`-Protokoll (Triage-Pflicht der KI,
  Regel-Fix vor Override, `resolution`-Format, Rückgabe an den Autor) —
  *Status: umgesetzt (W1–W5 gebaut, §3–§5 bindende Doktrin; die Alt-Seiten
  sind mit dem Admin-Redesign 2026-08 in den drei Ansichten Buchstaben ·
  Übergänge · Wörter aufgegangen)*
- **[Kurrent: Writer → Recognizer](proposals/kurrent-writer-and-recognizer.md)** —
  Recherche-Notiz (Englisch): warum Graves 2013 (RNN-Handschrift-Synthese)
  der Anker für den generativen Writer ist, und wie derselbe Writer als
  synthetische Datenquelle mit perfektem Ground-Truth einen billigen,
  browser-lauffähigen Recognizer trainiert (ein Forward-Pass statt
  Analysis-by-Synthesis zur Inferenzzeit) — *Status: offen (Recherche-Notiz,
  nichts gebaut)*

---

## Notes

Recherchematerial und operative Notizen außerhalb des Designkerns.

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
