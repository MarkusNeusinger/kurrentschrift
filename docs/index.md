# Documentation

Interne Design-Docs für das Kurrentschrift-Projekt. Sprache: Deutsch
(siehe [`reference/sprachregelung.md`](reference/sprachregelung.md) zur
Begründung). Stand: pre-MVP, Code existiert noch nicht.

---

## Quick Links

| Ich will… | Gehe zu |
|---|---|
| Den Architekturkern verstehen | [Architektur-Referenz](concepts/architektur.md) |
| Wissen, wie der MVP konkret zerlegt ist | [MVP-Roadmap](concepts/mvp-roadmap.md) |
| Wissen, warum Name/Domain/Lizenz so gewählt sind | [Naming und OSS-Setup](concepts/naming-und-setup.md) |
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
│   ├── architektur.md            # Analysis-by-synthesis, Ductus-Prior, Library-Schema, MVP
│   ├── mvp-roadmap.md            # Operative Zerlegung des MVP (§8) in Schritt 0 + M0–M6
│   └── naming-und-setup.md       # Repo-Name, Domain, Lizenz, Verzeichnis-Split
├── reference/                    # Policy-Dokumente mit Begründung
│   ├── sprachregelung.md         # Deutsch/Englisch pro Artefakt
│   ├── quellen-und-rechte.md     # Was darf rein, was nicht; PD/CC/NC-SA
│   ├── datenablage.md            # `/data`-Baum, SOURCE.md, Commit-Klassen
│   └── orthographie-regeln.md    # Lese-Regeln (Rund-s wortintern, Ligaturen, Mischschrift, …)
└── proposals/                    # Vorgeschlagene Konzept-Änderungen, noch nicht freigegeben
    └── planaenderungen.md        # Staging: §3 Lehrtafel-Rolle, §2/§4 Bigramme, §6.1 Positions-Statistik
```

`docs/notes/` enthält zusätzlich Recherchematerial, das nicht zum
Designkern gehört (z. B. Stift-Recherche).

---

## Concepts

Architektur und Entscheidungen mit ihrer Begründung — was bewusst gewählt
und was bewusst verworfen wurde.

- **[Architektur-Referenz](concepts/architektur.md)** — Analysis-by-Synthesis,
  Ductus-Prior, Library-Einheit `(glyph, position, variant)`, Schwellzug
  vs. Tinte, dreistufige Qualitätspipeline, MVP, Testwörter, Reihenfolge
- **[MVP-Roadmap](concepts/mvp-roadmap.md)** — operative Zerlegung von §8
  in Schritt 0 + M0–M6 mit Validierungs-Gates und Verifikations-Plan
- **[Naming und OSS-Setup](concepts/naming-und-setup.md)** — Name, Domain
  `kurrentschrift.ink`, Monorepo-Layout, MIT-Lizenz, README als Pitch

---

## Reference

Policy-Festlegungen und Konventionen.

- **[Sprachregelung](reference/sprachregelung.md)** — Code immer Englisch,
  interne Docs Deutsch, README Englisch, Website v1 Deutsch
- **[Quellen- und Rechte-Policy](reference/quellen-und-rechte.md)** — Süß
  nie ins Repo, §72 UrhG, gemischte Lizenzen in Korpora, Variante 0 = Loth 1866
- **[Datenablage](reference/datenablage.md)** — `/data`-Baum, drei
  Commit-Klassen, `SOURCE.md`-Pflichtfelder, Verlinkungsregel
- **[Orthographie-Regeln](reference/orthographie-regeln.md)** — Rund-s
  wortintern an Morphemgrenzen, Ligatur-Satz, Lesefallen, Mischschrift,
  ältere Buchstabenformen

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
