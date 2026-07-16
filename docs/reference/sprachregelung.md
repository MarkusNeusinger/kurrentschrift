# Sprachregelung (Docs / Code / README)

Begleitdokument zu [`architektur.md`](../concepts/architektur.md) und
[`naming-und-setup.md`](../concepts/naming-und-setup.md). Hält fest, *welche* Sprache wo gilt
und *warum* — inklusive der bewusst verworfenen pauschalen Lösung, damit
die Begründung nicht erneut aufgerollt werden muss.

---

## 0. Leitprinzip

Sprache folgt dem **Publikum des jeweiligen Artefakts**, nicht dem Projekt
pauschal. Anders als bei `anyplot.ai` (generisches Tool, keine
sprachgebundene Domäne, daher durchgängig Englisch) ist hier die Domäne
selbst deutsch (Kurrent, deutschsprachiger Raum) und die Website startet
auf Deutsch. Das ist kein Bruch zur anyplot-Linie, sondern dieselbe Regel
— anders angewendet, weil das Publikum ein anderes ist.

---

## 1. Finale Festlegung

| Artefakt | Sprache | Begründung |
|---|---|---|
| **Interne Docs** (Referenz, Naming-Setup, dieses Dokument) | Deutsch | Für den Autor geschrieben; argumentieren über eine deutsche Domäne |
| **`docs/contributing.md`** | **Englisch** (dokumentierte Ausnahme) | Wird vom README für das externe Publikum verlinkt — das Contributing-Publikum ist das README-Publikum (inkl. englischsprachiger Genealogie), nicht der Autor; in `docs/index.md` als „(EN)" markiert |
| **Forschungsnotizen in `docs/proposals/`** | Englisch zulässig (im Kopf als EN markiert) | Recherche-Material, das englischsprachige Quellen/Modelle zitiert (z. B. `kurrent-writer-and-recognizer.md`); entschiedene Konzepte wandern auf Deutsch nach `concepts/` |
| **README** | **Englisch** (zuerst), ggf. zweisprachig | Pitch, kein internes Doku — Hauptzielgruppe schließt englischsprachige Genealogie ein |
| **GitHub-Description** | Englisch | Internationale/SEO-Zielgruppe, Abgrenzung vom `kurrent-io`-Namespace |
| **Website (v1)** | Deutsch | Erste Zielgruppe deutschsprachig; spätere i18n nicht ausgeschlossen |
| **Code** (Variablen, Funktionen, docstrings, Kommentare) | **Englisch, ohne Ausnahme** | Konsistent mit Schema (§3 Referenz); fachliche Eigennamen sind ohnehin international |
| **Commit-Messages** | Englisch | Teil des Codes, öffentlich lesbar |

---

## 2. Behandlung der Fachbegriffe im Code

- International ohnehin englisch/lateinisch → unverändert übernehmen:
  `ductus`, `kurrent`, `allograph`, `glyph`, `position`, `variant`,
  `canonical`.
  - Achtung Schreibweisen-Split: Der Code-Identifier bleibt `ductus`
    (lateinisch/englisch, paläographischer Fachterminus), aber im
    **deutschen Fließtext** (Docs, UI) gilt die Duden-Schreibung
    **Duktus** ([duden.de/rechtschreibung/Duktus](https://www.duden.de/rechtschreibung/Duktus)).
- Deutsche Fachbegriffe ohne etablierte Übersetzung → **englischer
  Identifier, Begriff einmal im Kommentar erklären**:
  - `Schwellzug` → `width_profile` / `stroke_width`
    (`# Schwellzug: pressure-driven stroke-width modulation`)
- **Schriftzeichen sind Daten, nicht Code.** Die Werte der Ligatur- und
  Allograph-Einheiten bleiben das Zeichen selbst; nur die Schlüssel sind
  englisch:

```python
{"glyph": "ſt", "position": "medial", "variant": 0}   # value = the char; key = English
```

  Betrifft den geschlossenen Ligatur-Satz (`ch`, `ck`, `tz`, `ſt`, `qu`,
  `ß`, §4 Referenz) und das `ſ`-Allograph (§3 Referenz). Kein Sprachbruch.

---

## 3. Verworfen (damit nicht erneut diskutiert)

- **„Docs pauschal Deutsch"** inkl. README — Überkorrektur. Schneidet
  genau die Leute ab, die „Kurrent" als unübersetzten Fachterminus
  suchen (englischsprachige Genealogie als Kernzielgruppe). README wird
  daher explizit aus dem „Docs = Deutsch"-Bucket herausgenommen.
- **„Alles Englisch wie bei anyplot"** — ignoriert, dass Domäne und
  v1-Website deutsch sind; interne Argumentation über eine deutsche
  Schrift in Englisch zu führen ist Reibung ohne Gegenwert.
- **Deutsche Code-Identifier für deutsche Fachbegriffe** — bricht die
  Schema-Linie aus §3 der Referenz; Begriff gehört in den Kommentar,
  nicht in den Bezeichner.

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) §3 (Schema, englische Keys), §4 (Ligatur-Satz)
- [`naming-und-setup.md`](../concepts/naming-und-setup.md) §1 (Zielgruppe inkl. engl.
  Genealogie), §3 (README = Pitch)
