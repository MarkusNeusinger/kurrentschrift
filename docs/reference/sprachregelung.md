# Sprachregelung (Docs / Code / README)

> **Status (2026-09-20): bindend.** Festgelegte Sprachregeln mit eigener
> Verworfen-Liste (§3) — Änderung nur über eine neue Entscheidung, kein
> Code-Tracking. Per Owner-Entscheid 2026-08-18: §4 macht den Google
> developer documentation style guide zum Referenz-Fallback für die
> englischen Artefakte, mit benannten Haus-Abweichungen. Neu per
> Autor-Entscheid 2026-09-20: §5 erlaubt deutsche Fachbegriffe **ohne
> etablierte englische Entsprechung** als Bezeichner und löst damit den
> dritten Verworfen-Punkt in §3 ab; Kommentare und docstrings bleiben
> englisch, ausnahmslos. Die Ausnahme gilt **je Begriff, nie je Modul**;
> der übrige deutsche Namensbestand ist Altbestand (§5.3).

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
| **Code — docstrings und Kommentare** | **Englisch, ohne Ausnahme** | Sie erklären, sie benennen nicht; die Erklärung muss für jeden Leser funktionieren |
| **Code — Bezeichner** (Variablen, Funktionen, Klassen, Konstanten, Module) | Englisch, **außer** bei deutschen Fachbegriffen ohne etablierte englische Entsprechung (**§5**) | Konsistent mit Schema (§3 Referenz); fachliche Eigennamen sind ohnehin international — und wo es keinen etablierten Begriff gibt, ist eine erfundene Übersetzung schlechter als das Wort selbst |
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
- Deutscher Fachbegriff, für den es einen **etablierten englischen
  Begriff gibt** → **englischer Identifier, Begriff einmal im Kommentar
  erklären**:
  - `Schwellzug` → `width_profile` / `stroke_width`
    (`# Schwellzug: pressure-driven stroke-width modulation`)
- Deutscher Fachbegriff **ohne** etablierte englische Entsprechung → der
  deutsche Begriff darf der Bezeichner sein (**§5**, Autor-Entscheid
  2026-09-20). Der Test und die Beispiele beider Seiten stehen dort.
- **Schriftzeichen sind Daten, nicht Code.** Die Werte der Ligatur- und
  Allograph-Einheiten bleiben das Zeichen selbst; nur die Schlüssel sind
  englisch:

```python
{"glyph": "ſt", "variant": 0}   # value = the char; key = English
```

  Betrifft den geschlossenen Ligatur-Satz (`ch`, `ck`, `tz`, `ſt`, `St`,
  `qu`, `ß`, §4 Referenz) und das `ſ`-Allograph (§3 Referenz). Kein
  Sprachbruch.

---

## 3. Verworfen (damit nicht erneut diskutiert)

- **„Docs pauschal Deutsch"** inkl. README — Überkorrektur. Schneidet
  genau die Leute ab, die „Kurrent" als unübersetzten Fachterminus
  suchen (englischsprachige Genealogie als Kernzielgruppe). README wird
  daher explizit aus dem „Docs = Deutsch"-Bucket herausgenommen.
- **„Alles Englisch wie bei anyplot"** — ignoriert, dass Domäne und
  v1-Website deutsch sind; interne Argumentation über eine deutsche
  Schrift in Englisch zu führen ist Reibung ohne Gegenwert.
- ~~**Deutsche Code-Identifier für deutsche Fachbegriffe** — bricht die
  Schema-Linie aus §3 der Referenz; Begriff gehört in den Kommentar,
  nicht in den Bezeichner.~~ **Abgelöst durch den Autor-Entscheid
  2026-09-20 (§5)**, und zwar nur für Fachbegriffe **ohne** etablierte
  englische Entsprechung. Wo es einen etablierten Begriff gibt, gilt er
  unverändert weiter; seine Begründung ist der Grund, warum §5 die
  Ausnahme so eng zuschneidet.

---

## 4. Englischer Stil: Google-Guide als Referenz-Fallback

**Owner-Entscheid 2026-08-18.** Für alle **englischen Artefakte** —
README, CHANGELOG samt `changelog.d/*.md`, `docs/contributing.md`, die `tools/*/README.md`, die
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

## 5. Deutsche Fachbegriffe als Bezeichner (Stand 2026-09-20)

**Autor-Entscheid 2026-09-20.** Ein deutscher Fachbegriff **ohne
etablierte englische Entsprechung DARF ein Bezeichner sein** — Klasse,
Funktion, Feld, Konstante, Modul. **Kommentare und docstrings bleiben
englisch, ausnahmslos**, ebenso Commit-Messages und PR-Prosa (§1).

**Der Test ist eine Frage:** *Gibt es einen etablierten englischen
Begriff, den ein Leser dieser Domäne wiedererkennt?*

- **Ja → englischer Bezeichner.** Der deutsche Begriff gehört dann in
  den Kommentar, nicht in den Namen.
- **Nein → der deutsche Begriff darf stehen bleiben.** Eine für den
  Anlass erfundene Übersetzung ist schlechter als das Wort selbst, und
  sie zwingt Code und Docs dazu, dieselbe Sache verschieden zu benennen.

### 5.1 Ja — es gibt einen etablierten Begriff

| Fachbegriff | Bezeichner | Anker |
|---|---|---|
| Schwellzug | `stroke_width`, `width_profile_tv` | `core/compose.py`, `core/quality.py` |
| Schräglage | `slant_deg` | `core/database/models.py` |
| Fehlerschicht | `apiErrorText` | `app/src/sections/admin/shell/apiErrorText.ts` |

Hier gilt die frühere Form **unverändert** weiter: englischer Identifier
plus **ein** erklärender Kommentar —
`width_profile  # Schwellzug: pressure-driven stroke-width modulation`.
„Stroke width“, „slant“ und „error text“ sind etabliert; sie wegzuwerfen
wäre Verlust, kein Gewinn.

### 5.2 Nein — es gibt keinen

Die Liste ist **kurz, und das ist Absicht**: Glossar-Stichwort, dort keine
englische Entsprechung in Klammern, und ein Leser der Domäne erkennt den
Begriff unter einem englischen Namen nicht wieder.

| Fachbegriff | Bezeichner | Anker |
|---|---|---|
| Befund | das Modul selbst, `class Befund`, `def befund`, `befunde_of_strip`, `befund_index`, `BEFUND_FORMAT` | `core/eigenhand/befund.py` |
| Tintentreue | das Modul selbst, `class Tintentreue`, `def tintentreue`, `TINTENTREUE_FORMAT` | `core/eigenhand/tintentreue.py` |
| Laufform | das Modul selbst, `LAUFFORM_VARIANT`, `LAUFFORM_END_WINDOW`, `laufform_by_key` | `core/laufform.py`, `core/compose.py`, `core/aggregate.py` |

**Befund** ist der Fall, an dem der Entscheid hängt: `verdict` ist die
schlechtere Übersetzung. Ein Befund ist das gemessene Blatt samt dem EINEN
Grund und dem Vorschlag — kein Urteil, denn der Haken auf dem Papier
bleibt der Status.

### 5.3 Der übrige deutsche Namensbestand ist Altbestand, kein Beleg

In genau denselben Modulen stehen weitere deutsche Namen, die §5.2
**nicht** deckt — für sie gibt es sehr wohl einen etablierten englischen
Begriff, und das Repo belegt ihn meist selbst:

| Deutscher Name | Entsprechung | Beleg im Repo |
|---|---|---|
| `deckung` | coverage | [`glossar.md`](glossar.md) führt das Stichwort als **Deckung** *(coverage)* |
| `duktus` | ductus | §2 schreibt `ductus` vor; `core/` benutzt sonst durchweg `ductus` |
| `kringel` | loop | dasselbe Modul heißt die Sache `_loops`, `loop_expectation`, `LOOP_*` |
| `unstetigkeit` | discontinuity | `core/continuity.py` trägt für die Größe den englischen Modulnamen |
| `vorschlag`, `grund`, `guete`, `lesbarkeit`, `rang`, `abgeloest_von`, `VORSCHLAEGE`, `GRUND_*`, `Schwellen`, `schwellen_of`, `Kastenzaehler`, `zaehler`, `Rohzahlen`, `Sensorwert`, `sensoren_of`, `STUFEN`, `SENSOR_*` | suggestion, reason, quality, legibility, rank, superseded by, thresholds, box counter, raw numbers, sensor value, sensors, levels | Alltagswörter mit eindeutiger Entsprechung |

Sie **bleiben stehen**, aber aus einem anderen Grund: die Sprachregelung
wirkt vorwärts und kommt nie als Umbenennungs-Sweep zurück (§4, §5.4).
Sie sind **kein Präzedenzfall** — wer NEU benennt, stellt die Frage aus §5
neu, und ein etablierter englischer Begriff gewinnt auch dann, wenn direkt
daneben ein deutscher Altname steht. **Die Ausnahme ist begriffs-, nicht
modulweit:** `core/eigenhand/befund.py` steht nicht als Ganzes unter §5.2,
nur „Befund" selbst tut es.

### 5.4 Was das ersetzt, und was bleibt

Dieser Abschnitt **ersetzt** die frühere Lesart „englischer Identifier +
erklärender Kommentar“ **nur** für die Fachbegriffe aus §5.2. Für Wörter
mit etablierter Entsprechung bleibt sie die Regel (§5.1, §2); der
Altbestand aus §5.3 ist nicht gedeckt, nur nicht zurückgebaut. Der dritte
Verworfen-Punkt in §3 ist damit abgelöst und bleibt als Historie stehen.

**Warum jetzt.** Die Regel stand als „ohne Ausnahme“, während gemergter
Code seit `core/laufform.py` (#443) und `core/eigenhand/befund.py` das
Gegenteil praktizierte — ein stehender Widerspruch, kein Einzelfall.
Copilot meldete ihn auf #638 als Finding, und jedes weitere Modul der
Eigenhand-Kette hätte dasselbe erzeugt. Die drei Begriffe stehen zudem
bereits im Glossar und in entschiedenen Docs — ein englischer Bezeichner
ließe Code und Docs dieselbe Sache verschieden benennen.

**Die Grenze.** Der Entscheid betrifft **Bezeichner**, sonst nichts:

- Schema-**Schlüssel** in gespeicherten Payloads bleiben englisch (§2).
- Die **Werte** der `GRUND_*`-Konstanten sind deutsche Anzeigetexte
  (`GRUND_NICHTS = "nichts fällt auf"`) — das ist der Datenfall aus §2,
  kein Bezeichner.
- Ein deutscher Bezeichner ohne Glossar-Eintrag ist keiner: wer einen
  Begriff so benennt, trägt ihn im selben PR in
  [`glossar.md`](glossar.md) nach.
- Die Ausnahme gilt **je Begriff, nie je Modul** (§5.3); Altbestand ist
  kein Argument für einen weiteren deutschen Namen.
- Eine **Umbenennung in beide Richtungen** ist kein Aufräum-Sweep. Der
  Entscheid wirkt vorwärts (§4); bestehende Namen bleiben, wie sie sind.

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) §3 (Schema, englische Keys), §4 (Ligatur-Satz)
- [`naming-und-setup.md`](../concepts/naming-und-setup.md) §1 (Zielgruppe inkl. engl.
  Genealogie), §3 (README = Pitch)
