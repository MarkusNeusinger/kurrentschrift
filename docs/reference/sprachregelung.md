# Sprachregelung (Docs / Code / README)

> **Status (2026-08-18): bindend.** Festgelegte Sprachregeln mit eigener
> Verworfen-Liste (§3) — Änderung nur über eine neue Entscheidung, kein
> Code-Tracking. Neu per Owner-Entscheid 2026-08-18: §4 macht den Google
> developer documentation style guide zum Referenz-Fallback für die
> englischen Artefakte, mit benannten Haus-Abweichungen.

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
| **Forschungsnotizen in `docs/research/`** | Englisch zulässig (im Kopf als EN markiert) | Recherche-Material, das englischsprachige Quellen/Modelle zitiert (z. B. `kurrent-writer-and-recognizer.md`); entschiedene Konzepte wandern auf Deutsch nach `concepts/` |
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
{"glyph": "ſt", "variant": 0}   # value = the char; key = English
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

## 4. Englischer Stil: Google-Guide als Referenz-Fallback

**Owner-Entscheid 2026-08-18.** Für alle **englischen Artefakte** —
README, CHANGELOG, `docs/contributing.md`, die `tools/*/README.md`, die
Skills unter `.claude/skills/`,
`CLAUDE.md`/`.github/copilot-instructions.md`, Commit-/PR-Prosa und
englisch markierte `docs/research/`-Notizen — gilt der
[Google developer documentation style guide](https://developers.google.com/style)
als **Referenz-Fallback**: Er beantwortet Stilfragen, für die dieses
Dokument und die Repo-Konventionen keine eigene Regel haben. Er ist
Referenz, kein Gesetz — der Guide selbst sagt „break the rules“; wo
eine Hausregel steht, gewinnt sie.

**Der adoptierte Kern** (die Regeln, nach denen neuer englischer Text
geschrieben wird):

- Zweite Person und Imperativ in Anleitungen; Aktiv; Präsens.
- **Sentence case** für Titel und Überschriften (kein Title Case).
- Serial comma.
- **Beschreibende Linktexte** — nie „here“/„this“.
- Zeitlose Formulierungen: kein „currently“, kein Vorab-Ankündigen
  künftiger Features (deckt sich damit, dass die Docs durchweg
  absolute Daten schreiben statt „aktuell“/„zuletzt“).
- Barrierefreie, inklusive Sprache; Alt-Texte für Bilder.
- Im Fließtext „for example“/„that is“ statt `e.g.`/`i.e.`; in
  Klammern, Tabellen und Code-Kommentaren bleibt die Kurzform
  zulässig (die nicht-zu-strikte Mitte).

**Benannte Haus-Abweichungen — sie gewinnen über den Guide:**

1. **ISO-Daten (JJJJ-MM-TT)** statt „August 18, 2026“ — die Docs
   schreiben durchweg absolute ISO-Daten (Status-Köpfe, datierte
   Einträge); das erfüllt das Eindeutigkeits-Ziel des Guides besser
   als sein Prosa-Format.
2. **Gespacte Gedankenstriche ( — )** bleiben Hausstil in allen
   Sprachen; die ungespacte Google-Form wird nicht übernommen.
3. **Narrative Begründungs-READMEs und Warum-Kommentare bleiben.**
   Unsere READMEs und Docs sind Entscheidungs- und Messprotokolle,
   keine aufgabenorientierte Produktdoku — das Genre des Guides. Die
   Begründungs-Kultur (Verworfen-Listen, Vorregistrierungen, ehrliche
   Negative) wird nicht auf Task-Knappheit umgebaut.
4. **Deutsche Fachbegriffe** erscheinen unübersetzt in englischem Text
   (§2 — `Schwellzug`, `Laufform`, Duell-Namen); der Glossar liefert
   die Erklärung.

**Sprachneutrale Mechanik gilt auch für neue deutsche Docs:** sentence
case, beschreibende Linktexte, Alt-Texte, inklusive Sprache, zeitlose
Formulierungen — die Teile des Guides, die keine englische Grammatik
voraussetzen.

**Nur vorwärts wirkend.** Die Regeln gelten für
neuen und ohnehin angefassten Text. Es gibt KEINEN rückwirkenden
Repo-Sweep (gemessen 2026-08-18: allein 1.174 gespacte
Gedankenstriche und 28 `e.g.`/`i.e.` in den englischen Artefakten —
Churn ohne Erkenntnisgewinn), und die CHANGELOG-Historie wird nie
umgeschrieben.

**Verworfen im Rahmen dieser Entscheidung:** (a) strikte Volladoption
inkl. rückwirkendem Sweep — großer Diff, kein Gegenwert, Risiko für
die tragende Doku-Kultur; (b) ungespacte Em-Dashes; (c) Umbau der
narrativen READMEs auf Task-Orientierung; (d) Anwendung auf die
Website — der Entscheid betrifft ausschließlich das Repository, die
öffentliche Seite folgt `design-system.md` und bleibt deutsch (§1).

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) §3 (Schema, englische Keys), §4 (Ligatur-Satz)
- [`naming-und-setup.md`](../concepts/naming-und-setup.md) §1 (Zielgruppe inkl. engl.
  Genealogie), §3 (README = Pitch)
