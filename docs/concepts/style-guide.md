# Style-Guide — kurrentschrift.ink

Visuelle Identität der Endnutzer-Website. Begleitdokument zu
[`vision.md`](vision.md). Hält fest, *welcher* Look gilt und
**warum** — getrennt vom *Was* (Vision) und *Wie* (Architektur).

Die Tokens leben in `app/src/styles/paper.ts` (`const paper = …`, geteilt von
`LandingPage` und `PublicHeader`), bewusst **nicht** im globalen Theme — die
Landing hat eine eigene Identität, die Tool-Seiten bleiben auf dem ruhigen
Light-Theme (siehe §8).

---

## 1. Grundhaltung

- **Eigene Identität, nicht der anyplot/pyplots-Stil.** Für eine
  Schreibschrift-Seite ist das off-white-+-grün-Token-Set zu nüchtern.
  Diese Seite klingt nach **Papier und Tinte um 1900**.
- **Tinte, nicht Font.** Der Look feiert den *Schreibvorgang* (Ductus,
  Schwellzug), nicht eine statische Glyphe — deshalb das schreibende
  Hero-Wort und die Lineatur.
- **Synthese ist als solche erkennbar.** Wir simulieren Schrift, nicht
  Provenienz — Kennzeichnung statt Fälschungs-Optik.
- **Eine Tinte über alle Familien.** Kurrent · Sütterlin · Offenbacher
  unterscheiden sich in der *Form* (Schräglage, Strichstärke,
  Schwellzug), nicht in der Farbe. Keine familienspezifischen Tinten.
- **Landing expressiv, Tools clean.** Die Papier-Textur lebt auf der
  Landing; auf `/schreiben` und `/quiz` regiert neutrales Weiß (§8).

---

## 2. Farben — und warum

Eisengallustinte auf gealtertem Papier. Dominante warme Töne, **ein**
scharfer Akzent. CSS-Variablen / `paper`-Token in Klammern.

| Rolle | Hex | Begründung |
|---|---|---|
| Papier (Basis) | `#e7dabf` (`bg`) | Gealtertes Creme-/Hadernpapier um 1900: warmes Off-White, kein Reinweiß. |
| Papier hell | `#f1e8d4` (`hi`) | Lichtpunkt oben im Radial-Verlauf — gibt dem Blatt Tiefe. |
| Papier dunkel | `#d8c7a3` (`lo`) | Abfallender Rand des Verlaufs; wirkt wie leicht vergilbte Ränder. |
| **Tinte (primär)** | `#241a10` (`ink`) | **Eisengallustinte**, gealtert: ein warmes Braun-Schwarz, nie reines `#000`. Trägt Headline, Body und das Hero-Wort. |
| Tinte weich | `#473420` (`inkSoft`) | Sekundärtext; wie verdünnte/abgesetzte Tinte. |
| Sepia | `#6f5230` (`sepia`) | Eyebrows, kleine Labels — abgesetzte, ältere Tinte. |
| Sepia blass | `#9a8259` (`sepiaFaint`) | „bald"-Marker, dezente Mittellinie der Lineatur. |
| **Akzent (Viridian)** | `#40826d` (`viridian`) | Siehe unten — der einzige scharfe Akzent. |
| Linie | `#b6a079` (`line`) | Hairlines, Kartenrahmen, Lineatur-Linien. |

### Warum Viridian als Akzent

Historisch war der klassische Akzent **Rot/Ocker** (Rubrizierung mit
Mennige/Zinnober/Eisenoxid). Wir nutzen stattdessen **Grün als eigene
Identität** — und unter den historischen Grüns gewinnt **Viridian**:

- **Viridian** `#40826d` — Chromoxidhydrat, ab ~1859, tiefes kühles
  Blaugrün, **chemisch stabil**. Das „moderne" Grün um 1900. Liest klar
  als Grün, wirkt edel, „sitzt im Papier". → **gewählt.**

Bewusst verworfene Alternativen (Doku, damit die Wahl nachvollziehbar
bleibt):

| Kandidat | Hex | Warum nicht |
|---|---|---|
| Rotes Rubrum | `#8c2f1c` | Historisch korrekt, aber wir wollten grüne Identität statt der erwartbaren Rubrizierung. |
| Gebrannter Ocker | `#a8631f` | Schöner warmer Komplementär — als Fallback gut, aber kein Grün. |
| Smaragd | `#009E73` | Farbton zeitlich plausibel, aber **voll gesättigt wirkt's digital** und ist als **Fließtext zu hell** (Kontrast). Nur als Schau-Wort/Akzent tauglich. |
| Grünspan/Verdigris | `#1f7a6e` | Schönes Manuskript-Grün, aber **papierfressend** (Kupferacetat: Säure + Kupfer-Ionen zersetzen die Zellulose). |
| Grüne Erde | `#6b7a4f` | Sehr dezent — als Akzent fast zu zurückhaltend. |
| Waldgrün | `#1f4d38` | Als Akzent fast so dunkel wie die Tinte → „poppt" kaum. |

### Akzent-Regel

- Tinte (`ink`/`inkSoft`) trägt **Schrift und Body**.
- Viridian nur **sparsam als Akzent**: Marken-Punkt, Link-Hover, CTA,
  Timeline-Knoten, Karten-Hover-Rahmen.
- **Viridian niemals als Fließtextfarbe** (Kontrast auf Creme zu schwach).

---

## 3. Typografie

| Rolle | Schrift | Hinweis |
|---|---|---|
| Headline / Display | **EB Garamond**, *italic* | Old-Style-Serife, zeitstimmig (~1900-Druck). Selbst-gehostet via `@fontsource` (OFL 1.1). |
| Body / UI | EB Garamond / Sans-Stack | Ruhig, soll die Hero-Serife nicht konkurrenzieren. |
| Schau-Schrift (Script) | **GL-GermanCursive** (`'GLKurrent'`) | Kurrent/Sütterlin-Kursive. **Nur** dekorativ/Showpiece, **nie** UI. Siehe §4. |

```css
--serif:   'EB Garamond', Georgia, 'Times New Roman', serif;
--script:  'GLKurrent', cursive;   /* showpiece only */
```

> Im eigenständigen HTML-Mockup kamen Cormorant Garamond (Display) und
> Courier Prime (Code) dazu. Für die echte App bleibe ich bei EB Garamond,
> um deinen vorhandenen `@fontsource`-Stack nicht aufzublähen — Cormorant
> ist eine optionale Aufwertung, falls die Headline mehr Charakter braucht.

---

## 4. Schrift-Asset: GL-GermanCursive

- Quelle: **Gutenberg-Labo / GL-GermanCursive** (kupferplatten-artige
  Sütterlin/Kurrent-Mischkursive).
- Lizenz: **frei** — „Unlimited permission … use, copy, distribute, with
  or without modification, commercially and noncommercially. AS IS." →
  Eintrag in `THIRD_PARTY_NOTICES.md` analog zu EB Garamond.
- Format: TTF → **WOFF2** (24 KB) konvertiert; liegt in
  `src/assets/fonts/gl-germancursive.woff2`, `@font-face` via
  `<GlobalStyles>` in `LandingPage.tsx`.
- Zeichenumfang geprüft: enthält langes **ſ** (U+017F), **ß** und alle
  Umlaute — kein Tofu bei deutschem Text.
- Abgrenzung: ist ein **Font**, nicht der Ductus-Renderer. Genau die
  Lücke, die die echte Synthese später füllt — im Mockup nur Platzhalter
  für die Optik.

---

## 5. Papier-Textur & Tiefe

Hintergrund nie als Flächenfarbe, sondern als Atmosphäre:

- **Warmer Radial-Verlauf** `hi → bg → lo` (Lichtpunkt oben).
- **Korn** — graustufiges SVG-`feTurbulence`, `mix-blend-mode: multiply`,
  `opacity .5`. Feines Papierkorn.
- **Vignette** — `box-shadow: inset 0 0 200px rgba(60,40,20,.26)`.
- Alle drei als fixierte, nicht-interaktive Overlays (`pointer-events:
  none`, `z-index: 0`), Inhalt liegt auf `z-index: 1`.

---

## 6. Bewegung

Der Signature-Moment ist das **Schreiben**:

- **Hero-Wort schreibt sich** — `clip-path: inset(0 100% 0 0) → inset(0)`,
  ~1.9 s `cubic-bezier(.6,.02,.2,1)`. Liest wie Tinte, die die Feder legt.
- **Lineatur-Linien** zeichnen sich gestaffelt vorweg (`transform: scaleX`).
- **Scroll-Reveal** — Abschnitte faden mit leichtem `translateY` ein
  (IntersectionObserver, einmalig).
- **Immer** `@media (prefers-reduced-motion: reduce)` respektieren:
  Endzustand sofort, keine Animation.

```css
@keyframes writeIn  { from { clip-path: inset(0 100% 0 0) } to { clip-path: inset(0 0 0 0) } }
@keyframes drawLine { from { transform: scaleX(0) }        to { transform: scaleX(1) } }
```

---

## 7. Layout

- Editorial, großzügiger Weißraum, **Hairlines** (`line`) statt schwerer
  Trenner.
- Leichte **Asymmetrie/Drehung** fürs Hand-Gefühl (Hero-Script `-2deg`).
- Karten: 1 px `line`-Rahmen, `border-radius: 3px`, dezenter Hover-Lift
  (`translateY(-3px)` + weicher Schatten, Rahmen → Viridian).
- Lineatur als wiederkehrendes Motiv (Bezug zum Lineatur-Tool):
  Ober-/Mittel-/Unterband, Mittellinie in `sepiaFaint`.

---

## 8. Architektur-Regel: Landing vs. Tools

- **Landing (`/`)** = expressives Papier-Tinte-Showcase. One-Pager, der
  die *echten* Tools verlinkt und den Rest ehrlich als „bald" staged.
- **Tool-Seiten (`/schreiben`, `/quiz`)** = **clean/weiß lassen.** Die
  A4-Vorschau und die Buchstaben-Crops brauchen neutralen Hintergrund;
  Papier-Textur würde mit dem Inhalt kämpfen.
- Optionale Brücke: ein schlanker gemeinsamer Header, der die Identität
  dezent trägt, ohne den Tool-Inhalt zu stören.
- Tools werden **nicht** in die Landing inline-eingebaut (eigene Apps,
  eigener Viewport); höchstens ein read-only Live-Teaser (z. B.
  `PreviewSvg`).

---

## 9. Token-Referenz (copy-paste)

```ts
// Local to the landing — own identity, not the global theme.
const paper = {
  bg: '#e7dabf',
  hi: '#f1e8d4',
  lo: '#d8c7a3',
  ink: '#241a10',        // iron-gall ink, aged — primary writing/body
  inkSoft: '#473420',
  sepia: '#6f5230',
  sepiaFaint: '#9a8259',
  viridian: '#40826d',   // the single accent (chromium-oxide green)
  line: '#b6a079',
};

const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";
const script = "'GLKurrent', cursive"; // showpiece only
```

---

## 10. Komponenten-Muster

- **Live-Feature** → echter `RouterLink` mit CTA (`Übungsblatt erstellen →`).
- **Geplantes Feature** → „bald"-Marker (`sepiaFaint`, kursiv), **kein**
  toter Button. Konsistent mit dem bestehenden „bald" im Quiz/Setup.
- **CTA primär** → Tinte-Button bzw. Viridian-Text; sparsam einsetzen.
- Eyebrows: Viridian-Punkt + Kleinbuchstaben-Domain `kurrentschrift.ink`.

---

## 11. Lizenzen / Attribution

| Asset | Lizenz | Ablage |
|---|---|---|
| Code | MIT | Repo |
| Kanonische Glyph-Daten | Public Domain / CC0 | Open-Data-Paket (Roadmap) |
| EB Garamond | SIL OFL 1.1 | `@fontsource`, `THIRD_PARTY_NOTICES.md` |
| GL-GermanCursive | frei (Gutenberg-Labo) | `src/assets/fonts/`, `THIRD_PARTY_NOTICES.md` |

---

## Quick Do / Don't

- ✅ Tinte fürs Schreiben, Viridian nur als Akzent.
- ✅ Script-Font nur als Showpiece, `prefers-reduced-motion` ehren.
- ✅ Eine Tinte über alle drei Familien.
- ❌ Kein Reinweiß-Hintergrund auf der Landing, kein Reinschwarz als Tinte.
- ❌ Viridian nicht als Fließtext.
- ❌ Keine Papier-Textur auf den Tool-Seiten.
- ❌ Keine toten „coming soon"-Buttons — „bald"-Marker stattdessen.
