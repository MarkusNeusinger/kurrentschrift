# Dokumentation

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(siehe [`reference/sprachregelung.md`](reference/sprachregelung.md) zur
Begründung). Stand: in-progress MVP — Admin-UI läuft, Canonical-
Extraktion funktioniert, Per-Instanz-Fit und Aggregation sind die
nächsten Meilensteine.

---

## Schnellzugriff

| Ich will… | Gehe zu |
|---|---|
| Wissen, was die Endnutzer-Website sein soll | [Vision der Website](concepts/vision.md) |
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
| Sprache für Code, Docs, README nachschlagen | [Sprachregelung](reference/sprachregelung.md) |
| Wissen, was ins öffentliche Repo darf | [Quellen- und Rechte-Policy](reference/quellen-und-rechte.md) |
| Den `/data`-Baum verstehen | [Datenablage](reference/datenablage.md) |
| Lese-Regeln (Rund-s, Ligaturen, …) nachschlagen | [Orthographie-Regeln](schriftkunde/orthographie-regeln.md) |
| Schriftkunde-Fakten (Lineatur, Schräglage, Federn) nachschlagen | [Schriftkunde](schriftkunde/allgemein.md) |
| Fakten zu Kurrent / Sütterlin / Offenbacher nachschlagen | [Kurrent](schriftkunde/kurrent.md) · [Sütterlin](schriftkunde/suetterlin.md) · [Offenbacher](schriftkunde/offenbacher.md) |
| Offene Vorschläge für Konzept-Änderungen sehen | [Planänderungen](proposals/planaenderungen.md) |
| Schreib-API, Python-Komposition & Wort-Bench-Plan nachschlagen | [Schreibsystem und Wort-Bench](proposals/schreibsystem-und-wortbench.md) |
| Übergangs-Befund (pairlab: Platzierung · Stubs · Klassen) nachschlagen | [Übergangs-Befund](proposals/uebergaenge-befund.md) |

---

## Struktur der Dokumentation

```
docs/
├── index.md                      # You are here
├── contributing.md               # (EN) Was aktuell hilfreich ist und was noch zu früh ist — englisch, vom README verlinkt
├── concepts/                     # Architektur, Philosophie, getroffene Entscheidungen
│   ├── vision.md                 # Was die Endnutzer-Website sein soll (Pitch + Zielgruppe + 7 Ziele in 3 Clustern + Leitprinzipien + Nicht-Ziele)
│   ├── architektur.md            # §1–§17: Analysis-by-Synthesis, Schema, MVP, Animation, HTR, Lese-Lupe, Print, Frontend, Open-Data
│   ├── mvp-roadmap.md            # Operative Zerlegung des MVP (§8) in Schritt 0 + M0–M7
│   ├── style-guide.md            # Visuelle Identität Papier & Tinte: Tokens (styles/paper.ts), Typografie, R1–R9-Entscheidungen
│   ├── design-system.md          # Verbindliche Bauvorschrift: Tokens, Typo-Skala (19px), Breiten (PageContainer), Flächen, IA, Komponenten
│   ├── federmodelle.md           # Drei Federn, ein Renderpfad: Bandzugfeder-Gesetz, Spitzfeder-Haarstriche, Ziffern/Satzzeichen (joins:false)
│   └── naming-und-setup.md       # Repo-Name, Domain, Lizenz, Verzeichnis-Split, Frontend-Stack, Hosting
├── reference/                    # Policy- und Technik-Dokumente mit Begründung
│   ├── sprachregelung.md         # Deutsch/Englisch pro Artefakt
│   ├── quellen-und-rechte.md     # Was darf rein, was nicht; PD/CC/NC-SA
│   ├── datenablage.md            # `/data`-Baum, SOURCE.md, Commit-Klassen
│   ├── htr-integration.md        # Transkribus-API + TrOCR-Fallback, PAGE-XML, Free-Tier
│   ├── animation-rendering.md    # stroke-dashoffset (MVP), Canvas-2D-Stroker (post-MVP), WAAPI
│   ├── styleanalyse.md           # Per-Hand-Aggregation, Hinge-Features, Heatmap-Layouts
│   ├── qualitaetsmetrik.md       # Zwei Metriken (Kurrent-Schwellzug §1–4 · Sütterlin-Natürlichkeit §5), bench/Referenzen, Baseline-Historie, Loop-Erkenntnisse + Verworfen
│   ├── quiz-wortbank.md          # Lese-Quiz-Wortbank: Quellen (Kaeding, Genealogie-Felder), Pin+Runtime-Distraktoren, Fugen-Marker
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
├── proposals/                    # Vorgeschlagene Konzept-Änderungen, noch nicht freigegeben
│   ├── planaenderungen.md        # Staging: §2/§4 Bigramme, §6.1 Positions-Statistik, M4+ core/orthography.py
│   ├── schreibsystem-und-wortbench.md  # Audit 2026-07-01: Schreib-API, core/compose.py-Port, Wort-Bench, Übergangs-Redesign (Phasen A–E)
│   ├── uebergaenge-befund.md     # Befund 2026-07-11: pairlab-Paarsektion — Platzierung dominiert, Stub-Ersatz klassenweise, Optionen O1–O3
│   └── kurrent-writer-and-recognizer.md  # Recherche-Notiz (EN): generativer Writer (Graves 2013) als synthetische Datenquelle → billiger Recognizer
└── notes/                        # Recherchematerial & operative Notizen (nicht Designkern)
    └── stifte-fuer-unterwegs.md  # Stift-/Hardware-Recherche fürs Schreiben unterwegs
```

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
- **[Architektur-Referenz](concepts/architektur.md)** — §1–§17:
  Analysis-by-Synthesis, Duktus-Prior, Library-Einheit
  `(glyph, position, variant)`, Schwellzug vs. Tinte, dreistufige
  Qualitätspipeline, MVP (vier Gates), Testwörter, Reihenfolge, plus
  Animation-Render, Stil-Analyse, HTR-Integration, Lese-Lupe, Print,
  Frontend-Architektur, Open-Data
- **[MVP-Roadmap](concepts/mvp-roadmap.md)** — operative Zerlegung von §8
  in Schritt 0 + M0–M7 mit vier Validierungs-Gates und Verifikations-Plan
- **[Naming und OSS-Setup](concepts/naming-und-setup.md)** — Name, Domain
  `kurrentschrift.ink`, Monorepo-Layout, MIT-Lizenz, Frontend-Stack
  (anyplot-Stil), Hosting (Cloud Run), README als Pitch

---

## Reference

Policy- und Technik-Dokumente.

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

Vorgeschlagene Änderungen an den Konzept-Dokumenten, noch nicht freigegeben.

- **[Planänderungen](proposals/planaenderungen.md)** — drei offene
  Vorschläge: §2/§4 systematische Bigramm-Extraktion aus Beispieltext;
  §3/§6.1 Positions-Verteilung datengetrieben; M4+-Modul
  `core/orthography.py` (Vorschlag A — `position` als Lehrtafel-Rolle —
  ist freigegeben und in `architektur.md` §3 eingearbeitet)
- **[Schreibsystem und Wort-Bench](proposals/schreibsystem-und-wortbench.md)** —
  Audit 2026-07-01: öffentliche Schreib-API (Buchstabe + Wort) statt
  `/diagnostic`-Mitnutzung, Port der Wortkomposition nach
  `core/compose.py`, Wort-Bench gegen verifizierte PD-Wortvorlagen
  (gleiche Hand je Tafel), Übergangs-Redesign mit Exit-Klassen (Phasen A–E)
- **[Übergangs-Befund](proposals/uebergaenge-befund.md)** — Befund
  2026-07-11 aus `tools/pairlab` (unabhängige Paar-Sektion, 87 Vorkommen):
  Platzierung ist der größte Einzelfehler, die Standard-Diagonale ist
  generisch richtig, Hoch-Exits (d-Schleife, Deckstrich-Bögen, r-Arm)
  ersetzen die Kopplungs-Stubs klassenweise — Lösungsoptionen O1–O3
- **[Kurrent: Writer → Recognizer](proposals/kurrent-writer-and-recognizer.md)** —
  Recherche-Notiz (Englisch): warum Graves 2013 (RNN-Handschrift-Synthese)
  der Anker für den generativen Writer ist, und wie derselbe Writer als
  synthetische Datenquelle mit perfektem Ground-Truth einen billigen,
  browser-lauffähigen Recognizer trainiert (ein Forward-Pass statt
  Analysis-by-Synthesis zur Inferenzzeit)

---

## Notes

Recherchematerial und operative Notizen außerhalb des Designkerns.

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
