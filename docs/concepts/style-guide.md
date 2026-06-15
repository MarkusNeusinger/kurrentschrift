# Style-Guide — kurrentschrift.ink

Visuelle Identität der Endnutzer-Website. Begleitdokument zu
[`vision.md`](vision.md). Hält fest, *welcher* Look gilt und
**warum** — getrennt vom *Was* (Vision) und *Wie* (Architektur).

Die Tokens leben in `app/src/styles/paper.ts` (`const paper = …`) und sind die
**einzige Quelle** der Palette: das globale MUI-Theme (`app/src/theme/`), die
geteilte Papier-Textur (`PaperBackground`) und `PublicHeader` lesen alle von dort.
Die Identität trägt damit über **alle** Seiten — Landing, Quiz, Lineatur und den
Admin-Bereich. Neutral bleiben nur die **Arbeitsflächen** (A4-Vorschau,
Buchstaben-Crops, Chart-Scan), und das erzeugte **PDF bleibt weiß** (siehe §8).

---

## 1. Grundhaltung

- **Eigene Identität, nicht der anyplot/pyplots-Stil.** Für eine
  Schreibschrift-Seite ist das off-white-+-grün-Token-Set zu nüchtern.
  Diese Seite klingt nach **Papier und Tinte um 1900**.
- **Tinte, nicht Font.** Der Look feiert den *Schreibvorgang* (Duktus,
  Schwellzug), nicht eine statische Glyphe — deshalb das schreibende
  Hero-Wort und die Lineatur.
- **Synthese ist als solche erkennbar.** Wir simulieren Schrift, nicht
  Provenienz — Kennzeichnung statt Fälschungs-Optik.
- **Eine Tinte über alle Familien.** Kurrent · Sütterlin · Offenbacher
  unterscheiden sich in der *Form* (Schräglage, Strichstärke,
  Schwellzug), nicht in der Farbe. Keine familienspezifischen Tinten.
- **Eine Identität über alle Seiten.** Die Papier-Textur (Verlauf + Korn
  + Vignette) trägt über Landing, `/schreiben`, `/quiz` **und** den
  Admin-Bereich, damit alles einheitlich wirkt. Neutral bleiben nur die
  Arbeitsflächen (A4-Vorschau, Buchstaben-Crops, Chart-Scan); das
  gedruckte PDF bleibt weiß (§8).

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
| Sepia | `#5e4726` (`sepia`) | Eyebrows, kleine Labels **und** „bald"-Marker — abgesetzte, ältere Tinte. Gegenüber dem früheren `#6f5230` (nur 5.2:1) auf ~6.3:1 vertieft, damit kleine Schrift sich klar vom Papier abhebt (§3-Leitsatz). |
| Sepia blass | `#9a8259` (`sepiaFaint`) | **Nur Lineatur** — dezente Mittellinie/Linien. Für Text zu hell (2.66:1), trägt daher keine Schrift mehr. |
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
  Timeline-Knoten, Karten-Hover-Rahmen, Abschnitts-Initiale (`/impressum`, §3).
- **Viridian niemals als Fließtextfarbe** (Kontrast auf Creme zu schwach).
  Ausnahme nur für **große/fette** Schrift (≥ ~24 px): dort genügt der
  WCAG-Schwellwert 3:1, den `#40826d` mit 3.28:1 erreicht — so getragen von
  der grünen Abschnitts-Initiale (§3). Reines `#40826d` als kleiner Text
  bleibt verboten.

### Periodenpigmente als Semantikfarben (Runde R1, 2026-06)

Die MUI-Semantikfarben (error/warning/info) sind keine Markenfarben,
sondern Funktionssignale — und seit R1 in der **Chromolithographie-Palette
der Schulwandbilder** geerdet statt willkürlich modern. Alle Hexes
*approx* (gealterte Drucke), Ableitungen sind als solche markiert
(`derived for contrast, not a period hex`):

| Rolle | Pigment | Hex | Anmerkung |
|---|---|---|---|
| `error.main` | **Ochsenblut** | `#6b2e2a` | **Gewählt** (7.41:1 auf Creme) — ruhig, „sitzt im Papier". |
| `error.light` | Zinnober | `#e34234` | Füllungen/Ränder; als Text zu hell (2.98:1). |
| `warning.main` | Ocker | `#cc7722` | Ersetzt das alte Amber `#DDCC77` (**1.17:1** — praktisch unsichtbar). Text-Derivat `#a85f17`. |
| `info`/`secondary` | Preußischblau | `#003153` | 9.70:1 auf Creme; Derivat `#2a4a66` für dunkle Flächen. |
| reserviert | Chromgrün · Altgold | `#4a6741` · `#c9a227` | Noch ohne Rolle (success bleibt Viridian). |

Verworfen in R1: **abgedunkelter Zinnober** `#b5301f` als `error.main` —
liest zu sehr als modernes Alarm-Rot; Ochsenblut gewann als papier-
gebundener Fehlerton.

### Tintenzustände (Runde R2/R3, 2026-06)

Deutsche Schultinte war per Reichs-Tintenprüfung (1888, ergänzt 1912)
Eisengallus **blauschwarz** (Pelikan-Katalog 1892: „Schwarze Schultinte",
„Deutsche Reichstinte"): Der Indigo-Provisionalfarbstoff machte Frisches
lesbar, das Eisengallat oxidierte in Wochen nach Fast-Schwarz und
braunte über Jahrzehnte. Tokens (`inkState`, Hexes approx):

- `fresh` `#233044` — frisch geschrieben (blauschwarz)
- `oxidized` `#1c1a17` — Wochen alt
- `aged` = `ink` `#241a10` — das Jahrzehnte-Braun der Seite

**Signature-Animation (R2, angenommen):** Hero-Wort und Quiz-Glyphen
schreiben sich in `fresh` und setteln nach dem letzten Absetzen — der
Hero zur gealterten Seiten-Tinte (Archiv-Fläche), Quiz-Glyphen nur bis
`oxidized` („du schreibst jetzt"). Die Zeitachse ist bewusst gerafft —
**Synthese, als solche erkennbar**; `prefers-reduced-motion` zeigt
sofort den Endzustand. **Ink-Bleed (R3, angenommen):** feTurbulence +
feDisplacementMap nur auf den kleinen Schrift-Flächen (nie ganzseitig)
gibt den Strichen Faserkanten; gemessen kostenlos (61 fps).

### Schulheft-Lineatur (Runden R4/R5, 2026-06)

Gedruckte Schulheft-Lineatur ist **ab 1871** belegt, die **rote
Randleiste ab ~1900** (Schulmuseum Ottweiler); sie hielt den
Korrekturrand des Lehrers frei. Tokens (`schulheft`, Hexes approx):
`rulingBlue #8fa8c4` · `rulingBlueFaded #a8bcd0` · `marginRed #b03a3a`.

- **Worksheet-Modus „Schulheft um 1900" (R4, angenommen):** blaue
  Schreiblinien + zuschaltbare rote Randleiste (Default aus). Die
  Randleiste ist eine **dokumentierte Druck-Rolle**, kein Akzent — die
  §2-Verwerfung von Rot als Markenakzent bleibt unberührt. Das PDF
  druckt die Lineatur-Farben echt; die Seite bleibt weiß (§8).
- **Kurrent-Preset = Artefakt-Maß:** 2:1:2 bei 2,5 mm Mittelband —
  die in einem zeitgenössischen Kurrent-Übungsheft gedruckten
  **5/2,5/5 mm**. Schräglage in traditioneller Notation (Winkel zur
  Grundlinie, 90° = senkrecht): Kurrent um 1900 60–70° (die Loth-Tafel
  1866 selbst misst ~50°, siehe `schriftkunde/kurrent.md`), Offenbacher
  75–80° (Verhältnis **2:3:2**, Breitfeder 15–20°), Sütterlin 90°
  (Gleichzugfeder, Strichbreite winkelunabhängig).
- **Liniensystem-Progression:** Vier Linien (Anfang) · Doppellinie
  (geübt) · Nur Grundlinie (frei) — Zeilenmetrik bleibt identisch.
- **Quiz-Hilfslinien (R5, angenommen):** Grundlinie/Mittellinie im Crop
  in `rulingBlueFaded` statt neutralem Grau; die Crop-Fläche selbst
  bleibt weiß (§8).
- Verworfen in R4: 7/11/15-mm-Schnellwahl-Chips aufs Mittelband — die
  belegten Werte sind **Zeilenabstände einfach linierter Hefte**, keine
  Mittelband-Höhen des Vierliniensystems (Kategorienfehler; der Beleg
  bleibt als Hinweistext).

---

## 3. Typografie

| Rolle | Schrift | Hinweis |
|---|---|---|
| Headline / Display | **Playfair Display** | Didone-/Scotch-Register — der hohe Strichkontrast des Antiqua-Buchdrucks des 19. Jh., **voll lesbar** auch für Leser ohne Altschrift-Kenntnis. Via `@fontsource` (OFL 1.1). Mit Letterpress-Prägung (`letterpress`-Token, R8). |
| Body / UI | **EB Garamond** | Old-Style-Serife; ruhig, soll die Display-Stimme nicht konkurrenzieren. `@fontsource` (OFL 1.1). |
| Schau-Schrift (Script) | **GL-GermanCursive** (`'GLKurrent'`) | Kurrent/Sütterlin-Kursive. **Nur** dekorativ/Showpiece, **nie** UI. Siehe §4. |

```css
--serif:   'EB Garamond', Georgia, 'Times New Roman', serif;
--display: 'Playfair Display', 'EB Garamond', Georgia, serif;
--script:  'GLKurrent', cursive;   /* showpiece only */
```

**Leitsatz (User-Entscheidung, 2026-06):** Bei aller Liebe fürs Alte —
die Schrift muss **lesbar sein für Menschen, die die alten Schriften
nicht beherrschen**. Keine gebrochene Schrift in UI, Headlines oder
Body; historische Formen nur als gekennzeichnetes Schau-Material.

**Größen-Untergrenze (2026-06):** Aus demselben Leitsatz heraus hebt das
Theme (`app/src/theme/typography.ts`) die kleinen Varianten explizit über die
MUI-Defaults — EB Garamond läuft durch seine kleine x-Höhe optisch noch
kleiner: `body1` 17 px, `body2` 15 px, `caption` 13 px. Gilt über **alle**
Seiten (öffentlich **und** Admin), da das Theme die einzige typografische
Quelle ist.

**Offene Alternative:** *Sorts Mill Goudy* (OFL; Revival von Goudy
Oldstyle, **1915** — echtes Periodendesign, wärmer/ruhiger) bleibt als
Display-Kandidat dokumentiert, falls Playfair auf Dauer zu scharf wirkt.

Verworfene Typografie-Kandidaten (Runden R6/R7, 2026-06):

| Kandidat | Warum nicht |
|---|---|
| **Cormorant Garamond** (bisheriges Display) | 1530er-Garalde — elegant, aber zeitlich am wenigsten passend; von Playfair abgelöst. |
| **UnifrakturMaguntia** (Fahrenwaldt 1901) als Quiz-„gedruckt um 1900"-Zeile | Gebaut, live gezeigt, **abgelehnt**: keine gebrochene Schrift auf der Seite — Lesbarkeits-Leitsatz. (Technik-Notiz fürs Archiv: das fontsource-Subset enthält **kein ſ** U+017F; nur Self-Subsetting des Original-TTF trägt das lange s.) |
| **Alte DIN 1451 Mittelschrift** (Preuß. Musterzeichnung 1905) als Admin-Stimme | Übersprungen — konsequent keine weiteren Schriften; EB Garamond trägt auch den Admin. |
| UnifrakturCook · CC Accidenz Commons · Theano Didot | Keine Rolle, die Garamond/Playfair nicht füllen; Accidenz zudem CC-BY-SA statt OFL. |

### Abschnitts-Initialen mit Hover-Reveal (`/impressum`, 2026-06-15)

Die Kategorie-Überschriften der Rechtsseite (`Impressum` · `Datenschutz` ·
`Quellen & Lizenzen` · `Transparenz`) waren als kleine `overline`-Eyebrow
in Sepia gesetzt — schwächer als ihre eigenen Unterabschnitte (invertierte
Hierarchie). Neu (live in Runden 1–3 entschieden):

- **Form:** Wort in Tinte (Playfair 600, 1,5/1,75 rem) auf einer
  Hairline-Schreiblinie (`line`), eröffnet von einer **übergroßen
  Kurrent-Initiale** (GL-GermanCursive) in **Viridian** — die historische
  Rubrizierung (farbiger Abschnitts-Anfang) im Hausgrün statt im erwarteten
  Rot. Die Kategorie dominiert damit klar über die `subTitle`-Unterabschnitte.
- **Hover-Reveal:** Im Ruhezustand die echte Kurrent-Schauschrift; bei
  Hover/Focus blendet die Zierinitiale per Crossfade auf den **normalen
  Antiqua-Buchstaben** über — die Seite, die Kurrent lesen lehrt, übersetzt
  ihre eigenen Initialen. `prefers-reduced-motion` zeigt den Wechsel ohne Blende.
- **Grün = `#40826d` (normales Viridian).** Bewusst **nicht** das dunkle
  `#336152`: Letzteres ist nur ein abgeleiteter Hover-/Kontrastton („derived
  for contrast, not a period hex"); das echte Periodenpigment (Chromoxidhydrat,
  ~1859) **und** das Marken-Grün aus URL/Hero ist `#40826d`. Als große Initiale
  (≥ 2 rem) trägt es: 3.28:1 ≥ 3:1 → Lighthouse-Accessibility 100, color-contrast
  ohne Befund (§2-Ausnahme). Das Wort selbst bleibt Tinte.
- **Lesbarkeit/A11y:** Das `<h2>` trägt `aria-label` mit dem vollen Wort, alle
  sichtbaren Glyphen sind `aria-hidden` — die Zierschrift ist eine rein
  visuelle (Sehende-)Geste, der Screenreader liest immer das Klarwort. Der
  Lesbarkeits-Leitsatz bleibt gewahrt: nur **ein** Buchstabe ist Kurrent, der
  Rest Antiqua, und der Hover liefert die Übersetzung. Dies ist die **eine
  sanktionierte** UI-nahe Verwendung der Schau-Schrift (sonst gilt §4).

Verworfen in diesen Runden: die grüne **Rubrizierung des ganzen Titels** (zu
„langweilig"), die **Viridian-Randleiste** (zu modern), die **tiefe Drop-Cap**
(hängt bei einzeiligen Überschriften durch) und das **dunkle Grün** `#336152`
(kein Periodenton, weicht vom Marken-Grün ab).

---

## 4. Schrift-Asset: GL-GermanCursive

- Quelle: **Gutenberg-Labo / GL-GermanCursive** (kupferplatten-artige
  Sütterlin/Kurrent-Mischkursive).
- Lizenz: **frei** — „Unlimited permission … use, copy, distribute, with
  or without modification, commercially and noncommercially. AS IS." →
  Eintrag in `THIRD_PARTY_NOTICES.md` analog zu EB Garamond.
- Format: TTF → **WOFF2** (24 KB) konvertiert; liegt in
  `src/assets/fonts/gl-germancursive.woff2`, `@font-face` via
  `<GlobalStyles>` in `PaperBackground.tsx` (geteilte Papier-Schicht —
  Identität überall, §8).
- Zeichenumfang geprüft: enthält langes **ſ** (U+017F), **ß** und alle
  Umlaute — kein Tofu bei deutschem Text.
- Abgrenzung: ist ein **Font**, nicht der Duktus-Renderer. Genau die
  Lücke, die die echte Synthese später füllt — im Mockup nur Platzhalter
  für die Optik.
- **Sanktionierte UI-nahe Ausnahme:** als dekorative **Abschnitts-Initiale**
  mit Hover-Reveal auf `/impressum` (§3). Legitim, weil nur **ein** Buchstabe
  Kurrent ist, der Hover die Antiqua-Form zeigt und `aria-label` das Klarwort
  trägt — sonst bleibt es bei „Showpiece, nie UI".

---

## 5. Papier-Textur & Tiefe

Hintergrund nie als Flächenfarbe, sondern als Atmosphäre:

- **Warmer Radial-Verlauf** `hi → bg → lo` (Lichtpunkt oben).
- **Korn** — seit R9 (2026-06) ein **vorgebackener 128-px-PNG-Tile**
  (~9 KB, deterministisch, Seed 1866) statt des Live-`feTurbulence`
  unter `mix-blend-mode: multiply`: Der Live-Filter samt viewport-großer
  Blend-Ebene kostete gemessen **~18 fps beim Scrollen** (43 fps mit Live-Filter,
  Kontrolle ohne Korn 61 fps, mit gebackenem Tile 60 fps). Die Multiply-Mathematik steckt als
  Schwarz-mit-Alpha im Tile (`alpha = a·(1−g)`) — der Look ist
  identisch, die Blend-Ebene entfällt.
- **Letterpress (R8, angenommen)** — Display-Headlines tragen eine
  1-px-Lichtkante unten (`letterpress`-Token, aus `hi` abgeleitet):
  gepresste Type fängt das Licht des Papiers. Multiply-Compositing von
  Loth-Crops (R8b) ist **aufgeschoben**, bis eine dekorative Crop-Fläche
  existiert (Quiz/Diagnose sind Arbeitsflächen, §8).
- **Vignette** — `box-shadow: inset 0 0 200px rgba(60,40,20,.26)`.
- Alle Overlays fixiert und nicht-interaktiv (`pointer-events: none`,
  `z-index: 0`), Inhalt liegt auf `z-index: 1`.

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

## 8. Architektur-Regel: Identität überall, Arbeitsflächen neutral

Ursprünglich war der Look auf die Landing beschränkt und die Tool-Seiten
blieben weiß. Das wurde **bewusst aufgehoben** — die Identität soll alles
einheitlich tragen. Die neue Regel:

- **Chrome trägt Papier.** Die Papier-Textur (`PaperBackground`) + das
  warme MUI-Theme (cremefarbener Grund, Eisengallus-Tinte als Text, EB
  Garamond, Viridian-Akzent) gelten auf **allen** Seiten: Landing,
  `/schreiben`, `/quiz` und dem Admin-Bereich (Sidebar, Leiste, Wizard).
- **Arbeitsflächen bleiben neutral.** Genau die Flächen, die einen ruhigen
  Hintergrund brauchen, malen ihren eigenen Grund über die Textur:
  - die **A4-Vorschau** im Lineatur-Tool (weiß),
  - die **Buchstaben-Crops** im Quiz und in der Diagnose (weiß),
  - der **Chart-Scan** und die **Wizard-Leinwand** im Admin (dunkles `#111`
    für Kontrast zur Vorlage).
- **Das gedruckte PDF bleibt weiß.** Die Textur ist reines Bildschirm-Atmo;
  die Vorlage zum Ausdrucken trägt keinerlei Papier-Effekt.
- Gemeinsamer Header (`PublicHeader`, Tone `paper`) trägt die Marke auf den
  öffentlichen Seiten; der Admin nutzt seine eigene Sidebar/Leiste.
- Tools werden **nicht** in die Landing inline-eingebaut (eigene Apps,
  eigener Viewport); höchstens ein read-only Live-Teaser (z. B.
  `PreviewSvg`).

---

## 9. Token-Referenz (copy-paste)

```ts
// Single source of the palette — read by theme/, PaperBackground and PublicHeader.
const paper = {
  bg: '#e7dabf',
  hi: '#f1e8d4',
  lo: '#d8c7a3',
  ink: '#241a10',        // iron-gall ink, aged — primary writing/body
  inkSoft: '#473420',
  sepia: '#5e4726',      // eyebrows, small labels, "bald" markers — deepened for legibility (~6.3:1)
  sepiaFaint: '#9a8259', // ruling/Mittellinie tint ONLY — too light for text (2.66:1)
  viridian: '#40826d',   // the single accent (chromium-oxide green)
  line: '#b6a079',
};

// Periodengeerdete Erweiterungen (R1–R5; Hexes approx, siehe §2/§2a)
const inkState  = { fresh: '#233044', oxidized: '#1c1a17', aged: paper.ink };
const schulheft = { rulingBlue: '#8fa8c4', rulingBlueFaded: '#a8bcd0', marginRed: '#b03a3a' };
const pigment   = { vermilion: '#e34234', oxblood: '#6b2e2a', ochre: '#cc7722',
                    prussianBlue: '#003153', chromeGreen: '#4a6741', oldGold: '#c9a227' };

const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";
const display  = "'Playfair Display', 'EB Garamond', Georgia, 'Times New Roman', serif";
const script   = "'GLKurrent', cursive"; // showpiece only
const letterpress = `0 1px 0 ${paper.hi}59`; // Deboss der Display-Headlines
```

---

## 10. Komponenten-Muster

- **Live-Feature** → echter `RouterLink` mit CTA (`Übungsblatt erstellen →`).
- **Geplantes Feature** → „bald"-Marker (`sepia`, kursiv), **kein**
  toter Button. Konsistent mit dem bestehenden „bald" im Quiz/Setup.
  (Früher `sepiaFaint` — auf `sepia` angehoben, weil `sepiaFaint` mit
  2.66:1 als Text durchfällt; `sepiaFaint` trägt jetzt nur noch Lineatur.)
- **CTA primär** → Tinte-Button bzw. Viridian-Text; sparsam einsetzen.
- Eyebrows: Viridian-Punkt + Kleinbuchstaben-Domain `kurrentschrift.ink`.

---

## 11. Lizenzen / Attribution

| Asset | Lizenz | Ablage |
|---|---|---|
| Code | MIT | Repo |
| Kanonische Glyph-Daten | Public Domain / CC0 | Open-Data-Paket (Roadmap) |
| EB Garamond | SIL OFL 1.1 | `@fontsource`, `THIRD_PARTY_NOTICES.md` |
| Playfair Display | SIL OFL 1.1 | `@fontsource`, `THIRD_PARTY_NOTICES.md`, Lizenztext unter `app/public/fonts/` |
| GL-GermanCursive | frei (Gutenberg-Labo) | `src/assets/fonts/`, `THIRD_PARTY_NOTICES.md` |

---

## 12. Sprachton der Website-Prosa (2026-06-12)

**Leitgedanke: Die Website spricht im Ton der Briefe, die sie lesen
lehrt.** Was in Kurrent überliefert ist, sind vor allem Briefe — die
Prosa der Seite übernimmt deren Register: das gebildete
Alltags-/Briefdeutsch um 1900. Warm, fließend, ein leicht
altmodischer Satzrhythmus; die Du-Anrede bleibt. Erste Umsetzung:
`/impressum`, danach Landing, Quiz und Lineatur-Vorlage
(`app/src/locales/de/*.ts` — die Strings sind die einzige Textquelle,
der Ton lebt also vollständig in den Locale-Dateien).

Regeln:

- **Patina in den Rahmen, nicht in die Fakten.** Einstiege, Übergänge
  und Schlusszeilen tragen den Ton; rechtlich oder funktional
  relevante Angaben (Datenschutz-Fakten, Fristen, Namen, Zahlen)
  bleiben nüchtern und eindeutig. Das sprachliche Pendant zum
  Lesbarkeits-Leitsatz der Typografie (§3): Verständlichkeit vor
  Epoche.
- **Funktionale UI-Labels bleiben knapp und modern** („Quiz starten",
  „Als PDF herunterladen", Formularfelder, Chips). Der Ton lebt in
  Fließtexten, Hinweisen und Überschriften-Prosa.
- **Alte Wörter gern, wo sie passen und heute noch tragen:**
  Liebhaberei · unbehelligt · tilgen · Setzkasten · Fibel · tadellos ·
  vorschreiben („Zug um Zug vorgeschrieben" — die Lehrtafel *ist* eine
  Vorschrift) · „ein paar Zeilen" · „ich freue mich über Post" ·
  „nach Belieben" · „auf Wunsch". Datums-/Schlusszeilen nach Briefart:
  „Visp, im Juni 2026" statt „Stand: 06/2026".
- **Fachbegriffe behalten ihren Namen** (Cookies, PDF, Open Source,
  Schwellzug, Lineatur) — keine Scherzverdeutschungen.

Beispiele (Stand 2026-06, `app/src/locales/de/impressum.ts`):

| Neutral-modern | Briefton |
|---|---|
| „Diese Website kommt ohne Cookies aus." | „Wer diese Seiten besucht, bleibt unbehelligt: kein Konto, keine Cookies, kein Verzeichnis der Besucher." |
| „Wir erfassen nur anonyme Seitenaufrufe." | „Gezählt wird nur, was sich ohne Namen zählen lässt: Seitenaufrufe, nicht Personen." |
| „Stand: Juni 2026" | „Visp, im Juni 2026" |

**Verworfen** (live ausprobiert am 2026-06-12, als Gesamtregister
abgelehnt — „ich würde ja auch keine Seite in Notar-Deutsch
schreiben"):

| Variante | Warum verworfen |
|---|---|
| Kanzlei-/Beamtendeutsch („Der Unterzeichnete …", „Verantwortlich zeichnet", „Zuschriften erbeten an", „Gegeben zu Visp", „hiermit wird zur Kenntnis gebracht") | Damalige *Amts*sprache ist nicht das Register der Seite — Briefe sind es. |
| Alte Orthographie („daß") | Liest sich heute wie ein Tippfehler — kollidiert mit dem Lesbarkeits-Leitsatz. |
| Scherzverdeutschung von Fachbegriffen (Cookies als „Süßgebäck") | Teil der verworfenen Kanzlei-Fassung; Rechtsseite muss belastbar bleiben, der Gag nutzt sich ab. |

---

## Quick Do / Don't

- ✅ Tinte fürs Schreiben, Viridian nur als Akzent.
- ✅ Script-Font nur als Showpiece (Ausnahme: dekorative Abschnitts-Initiale
  mit Hover-Reveal, §3/§4), `prefers-reduced-motion` ehren.
- ✅ Eine Tinte über alle drei Familien.
- ✅ Papier-Textur trägt überall; nur Arbeitsflächen (A4, Crops, Chart) und das PDF bleiben neutral/weiß.
- ✅ Prosa im Briefton um 1900 (§12); UI-Labels und Fakten nüchtern.
- ❌ Kein Reinweiß als Seitengrund, kein Reinschwarz als Tinte.
- ❌ Viridian nicht als Fließtext.
- ❌ Keine toten „coming soon"-Buttons — „bald"-Marker stattdessen.
- ❌ Kein Kanzleideutsch, keine alte Orthographie („daß") in der Prosa (§12).
