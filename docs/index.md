# Documentation

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(siehe [`reference/sprachregelung.md`](reference/sprachregelung.md) zur
Begründung). Stand: in-progress MVP — Admin-UI läuft, Canonical-
Extraktion funktioniert, Per-Instanz-Fit und Aggregation sind die
nächsten Meilensteine.

---

## Quick Links

| Ich will… | Gehe zu |
|---|---|
| Wissen, was die Endnutzer-Website sein soll | [Vision der Website](concepts/vision.md) |
| Den Architekturkern verstehen | [Architektur-Referenz](concepts/architektur.md) |
| Wissen, wie der MVP konkret zerlegt ist | [MVP-Roadmap](concepts/mvp-roadmap.md) |
| Wissen, warum Name/Domain/Lizenz so gewählt sind | [Naming und OSS-Setup](concepts/naming-und-setup.md) |
| HTR-Pfad (Transkribus + TrOCR) nachschlagen | [HTR-Integration](reference/htr-integration.md) |
| Animation-Render-Algorithmus nachschlagen | [Animation-Rendering](reference/animation-rendering.md) |
| Stil-Analyse-Pipeline nachschlagen | [Stil-Analyse](reference/styleanalyse.md) |
| Frontend-Stack & Deploy nachschlagen | [Frontend-Stack](reference/frontend-stack.md) |
| Sprache für Code, Docs, README nachschlagen | [Sprachregelung](reference/sprachregelung.md) |
| Wissen, was ins öffentliche Repo darf | [Quellen- und Rechte-Policy](reference/quellen-und-rechte.md) |
| Den `/data`-Baum verstehen | [Datenablage](reference/datenablage.md) |
| Lese-Regeln (Rund-s, Ligaturen, …) nachschlagen | [Orthographie-Regeln](reference/orthographie-regeln.md) |
| Offene Vorschläge für Konzept-Änderungen sehen | [Planänderungen](proposals/planaenderungen.md) |

---

## Documentation Structure

```
docs/
├── index.md                      # You are here
├── concepts/                     # Architektur, Philosophie, getroffene Entscheidungen
│   ├── vision.md                 # Was die Endnutzer-Website sein soll (Pitch + Zielgruppe + 10 Ziele/Nicht-Ziele)
│   ├── architektur.md            # §1–§17: Analysis-by-Synthesis, Schema, MVP, Animation, HTR, Lese-Lupe, Print, Frontend, Open-Data
│   ├── mvp-roadmap.md            # Operative Zerlegung des MVP (§8) in Schritt 0 + M0–M7
│   └── naming-und-setup.md       # Repo-Name, Domain, Lizenz, Verzeichnis-Split, Frontend-Stack, Hosting
├── reference/                    # Policy- und Technik-Dokumente mit Begründung
│   ├── sprachregelung.md         # Deutsch/Englisch pro Artefakt
│   ├── quellen-und-rechte.md     # Was darf rein, was nicht; PD/CC/NC-SA
│   ├── datenablage.md            # `/data`-Baum, SOURCE.md, Commit-Klassen
│   ├── orthographie-regeln.md    # Lese-Regeln (Rund-s wortintern, Ligaturen, Mischschrift, …)
│   ├── htr-integration.md        # Transkribus-API + TrOCR-Fallback, PAGE-XML, Free-Tier
│   ├── animation-rendering.md    # stroke-dashoffset (MVP), Canvas-2D-Stroker (post-MVP), WAAPI
│   ├── styleanalyse.md           # Per-Hand-Aggregation, Hinge-Features, Heatmap-Layouts
│   └── frontend-stack.md         # React+Vite+MUI Build, Deploy auf Cloud Run, i18n, Auth-Routen
└── proposals/                    # Vorgeschlagene Konzept-Änderungen, noch nicht freigegeben
    └── planaenderungen.md        # Staging: §2/§4 Bigramme, §6.1 Positions-Statistik, M4+ core/orthography.py
```

`docs/notes/` enthält zusätzlich Recherchematerial, das nicht zum
Designkern gehört (z. B. Stift-Recherche).

---

## Concepts

Architektur und Entscheidungen mit ihrer Begründung — was bewusst gewählt
und was bewusst verworfen wurde.

- **[Vision der Website](concepts/vision.md)** — was die Endnutzer-Website
  unter `kurrentschrift.ink` sein soll: Pitch, Zielgruppe, zehn Ziele
  (Einstieg, Schreiben üben, animierte Buchstaben, Lesen üben, eigene
  Schrift analysieren, Lese-Hilfe, Hände vergleichen, Lese-Lupe, offene
  Datensätze, DE/EN), Nicht-Ziele, Verhältnis zur bestehenden Landschaft
- **[Architektur-Referenz](concepts/architektur.md)** — §1–§17:
  Analysis-by-Synthesis, Ductus-Prior, Library-Einheit
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
- **[Orthographie-Regeln](reference/orthographie-regeln.md)** — Rund-s
  wortintern an Morphemgrenzen, Ligatur-Satz, Lesefallen, Mischschrift,
  ältere Buchstabenformen
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

---

## Proposals

Vorgeschlagene Änderungen an den Konzept-Dokumenten, noch nicht freigegeben.

- **[Planänderungen](proposals/planaenderungen.md)** — vier offene
  Vorschläge: §3 `position` als Lehrtafel-Rolle präzisieren; §2/§4
  systematische Bigramm-Extraktion aus Beispieltext; §3/§6.1
  Positions-Verteilung datengetrieben; M4+-Modul `core/orthography.py`

---

## Mitmachen

- **[Contributing Guide](contributing.md)** — was aktuell hilfreich ist und was noch zu früh ist

---

## Weitere Ressourcen

- **[README](../README.md)** — Projekt-Pitch (Englisch, öffentlich)
- **[CITATION.cff](../CITATION.cff)** — Zitations-Metadaten
- **[CLAUDE.md](../CLAUDE.md)** — Hinweise für Claude Code
