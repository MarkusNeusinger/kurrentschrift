# Design-System — kurrentschrift.ink

> **Was dieses Dokument ist:** die *verbindliche, aktuelle* Bauvorschrift der
> öffentlichen Website — Tokens, Typo-Skala, Breiten, Flächen, Navigation,
> Komponenten, Bewegung, Lesbarkeit. Es beschreibt den **Ist-Zustand des Codes**
> (eine Stellschraube pro Regel), nicht die Entscheidungs­geschichte.
>
> **Begründung & Historie** (warum Viridian, R1–R9, Pigment-Recherche) stehen im
> [Style-Guide](style-guide.md). **Claude-Design-Spiegelung** (die gesyncten
> Marken­komponenten) steht in [`.design-sync/conventions.md`](../../.design-sync/conventions.md).
> Diese drei müssen synchron bleiben — ändert sich hier eine Zahl, dort nachziehen.
>
> Quelle der Wahrheit im Code: `app/src/styles/paper.ts` (Palette + Font-Tokens),
> `app/src/theme/typography.ts` (Typo-Skala), `app/src/components/PageContainer`
> (Breiten), `app/src/components/Prose` (Lesemaß).

---

## 1. Leitstern

Gut lesbar zuerst, Anmutung „um 1900" mit Anspielungen, Bedienung modern. Fokus
**Papier & Tinte**. Jede Gestaltungsregel ordnet sich der **Lesbarkeits-Leitregel**
(§9) unter: gebrochene und Schreibschrift erscheinen nur als markiertes Specimen,
nie als Lesetext.

---

## 2. Farb-Token

Einzige Palettenquelle: `app/src/styles/paper.ts`. Hex nur hier referenzieren,
im Code immer über das Token (`paper.viridian`, nie `'#40826d'`).

| Token | Hex | Rolle |
|---|---|---|
| `paper.bg` | `#e7dabf` | Seiten-Hintergrund (Papier-Grundton, über `PaperBackground`) |
| `paper.hi` | `#f1e8d4` | aufgehelltes Papier — **Karten-/Panelfläche** (das einzige „heller als Grund") |
| `paper.lo` | `#d8c7a3` | abgedunkeltes Papier — Vertiefungen, Trennzonen |
| `paper.ink` | `#241a10` | Tinte — Überschriften, starker Text |
| `paper.inkSoft` | `#473420` | weiche Tinte — Fließtext |
| `paper.sepia` | `#5e4726` | Sepia — sekundärer Text, In-Prosa-Links (Ruhezustand) |
| `paper.sepiaFaint` | `#9a8259` | blasses Sepia — Captions, Metazeilen |
| `paper.viridian` | `#40826d` | **der einzige Akzent** — CTAs, Hover, Initialen, aktive Zustände |
| `paper.viridianText` | `#2e6152` | Viridian in Textgröße — für Kontrast abgeleitet (5.15:1 auf dem Papiergrund, WCAG AA), kein Periodenton; Karten-CTAs, Links, Quiz-Score/-Verdikt |
| `paper.line` | `#b6a079` | Haarlinie — Rahmen, Trenner, Tabellen-Borders |

**Akzent-Regel:** Viridian ist sparsam und bedeutungstragend (Aktion/Aktiv/Akzent).
Sobald Viridian als Fließtext-großer Text auftritt, gilt `paper.viridianText`
(der Akzent `#40826d` erreicht auf dem Papiergrund nur 3.28:1); `#40826d`
bleibt für Display-Größen, Initialen, Rahmen, Füllungen und Fokus-Ringe.
Niemals als Fläche, nie zwei konkurrierende Akzentfarben. Semantik (Erfolg/Fehler im
Quiz) nutzt Periodenpigmente — siehe [Style-Guide §2](style-guide.md).

Font-Tokens (ebenfalls `styles/paper.ts`): `garamond` (EB Garamond, Body/UI &
Theme-Default), `display` (Playfair Display, Display-Überschriften), `script`
(GL-GermanCursive/„GLKurrent", Kurrent-Specimen), `suetterlin` (HJZ-Sütterlin-Font,
Specimen-Fallback), `letterpress` (ein `textShadow`-String für Tiefdruck-Anmutung).

---

## 3. Typo-Skala

Eine einzige Skala im Theme (`app/src/theme/typography.ts`) — **keine Ad-hoc-Größen,
keine per-Seite-`clamp()`**. Auf **19 px Basis** kalibriert: EB Garamonds niedrige
x-Höhe liest klein, darum sitzt der Body auf 19 px und die ganze Leiter zieht
proportional mit (Style-Guide §3 „Lesbarkeit vor Epoche").

| Variant | Größe | ≈ px @19 | Gewicht | Zeile | Einsatz |
|---|---|---|---|---|---|
| `h1` | `clamp(2.4rem, 1.7rem + 2.8vw, 3.1rem)` | 38–50 | 400 | 1.12 | Seitentitel |
| `h2` | `clamp(2.05rem, 1.5rem + 2.2vw, 2.6rem)` | 33–42 | 400 | 1.16 | große Abschnitte |
| `h3` | `clamp(1.75rem, 1.4rem + 1.5vw, 2.15rem)` | 28–34 | 400 | 1.2 | Unterabschnitt, Karten-Titel |
| `h4` | `clamp(1.5rem, 1.25rem + 1vw, 1.85rem)` | 24–30 | 400 | 1.25 | Specimen-/Tool-Karten-Titel |
| `h5` | `1.45rem` | 23 | 500 | 1.3 | kleine Überschrift |
| `h6` | `1.25rem` | 20 | 500 | 1.4 | Label-Überschrift, Sub-Heads |
| `body1` | `1.1875rem` | **19** | 400 | 1.6 | Fließtext (Default) |
| `body2` | `1.0625rem` | 17 | 400 | 1.6 | Sekundärtext, dichte Tabellen |
| `subtitle1` | `1.1875rem` | 19 | 400 | 1.5 | hervorgehobener Vorspann |
| `subtitle2` | `1.0625rem` | 17 | 400 | 1.5 | kleines Display-Label |
| `caption` | `0.875rem` | 14 | 400 | 1.55 | Captions, Quellenzeilen (Boden ~14 px) |
| `overline` | `0.8125rem` | 13 | 500 | — | Eyebrow (`letterSpacing 0.12em`) |

**Größe kommt vom `variant`, Charakter lokal.** Display-Überschriften (Playfair)
opten lokal ein — der Variant liefert nur die Größe:

```tsx
// Kanonisches Seitentitel-Muster (Playfair-Titel):
<Typography component="h1" variant="h1"
  sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress }}>
  {t.title}
</Typography>
```

**Gewichts-Regel:** Eine **Playfair-Überschrift (`fontFamily: display`) trägt
`fontWeight: 600`** — der Display-Schnitt will den schwereren Strich. Garamond-
Überschriften nehmen das Theme-Gewicht (h1–h4 = 400, h5/h6 = 500). Wer also `display`
setzt, setzt auch `fontWeight: 600`; wer ein Garamond-Heading auf einen `variant`
mit abweichendem Gewicht mappt, hält das **Original-Gewicht** explizit in `sx`
(z. B. `variant="h6"` + `fontWeight: 400`, wenn die Vorlage 400 war).

Regeln beim Bauen:
- Ad-hoc `fontSize`/`clamp` auf einer Überschrift → **nächstgelegener `variant`**, das
  `fontSize` löschen. **Die Schrift-FACE bleibt** (war es `display`/`letterpress`/
  `italic`/ein bestimmtes Gewicht, in `sx` behalten — ein `variant` darf Face/Gewicht/
  Stil nie still verändern).
- Lokale Stil-Konstanten (`prose`, `subTitle`): nur noch Farbe/Abstand/Zeile tragen,
  Größe + Family kommen aus dem Variant (vgl. `ImpressumView` `prose` → `{ color, lineHeight, mb }`).

**Seitenkopf — einheitlich.** Jede öffentliche Seite (außer dem Landing-Hero) trägt
ihren Titel in **Playfair** (`fontFamily: display`, `fontWeight: 600`), Größe aus
`variant="h1"` — über den gemeinsamen **`PageHeader`** (§7). **Ein** Titel-Schnitt für
alle; der frühere Tool-vs-Inhalt-Split (Tool-Seiten kursives Garamond) ist aufgehoben.
Darüber sitzt ein einheitliches **Bereichs-Eyebrow** (Overline auf 42-px-Haarlinie,
Garamond-versal-sepia, z. B. `LESEN` / `SCHREIBEN` / `SCHRIFTKUNDE`); die Bereichs-Hubs
lassen es weg (Titel = Bereich). Darunter optional ein Intro im Lesemaß (`Prose`). So
sind Schrift, Eyebrow-Stil und linke Kante auf allen Seiten gleich — eine Stellschraube
(`PageHeader`) statt pro-Seite-Köpfe.

---

## 4. Breiten-System

Eine zentrale Komponente statt sieben driftender `<Container>`: `PageContainer`
(`app/src/components/PageContainer`). Drei kalibrierte Stufen:

| Token | px | Einsatz |
|---|---|---|
| `narrow` | 760 | fokussierte Spaltenbreite (~Lesemaß) — heute als **Deckel**: das Quiz kappt seine Panels in einem `text`-Container auf `maxWidth: 760`, damit der Titel linksbündig mit den anderen Seiten sitzt |
| `text` | 1152 | die meisten Inhalts- & Tool-Seiten (Schriftkunde, Impressum, Scribe, Tafel, Hubs, Quiz) |
| `wide` | 1280 | Landing, Übungsblatt, Header & Footer |

```tsx
<PageContainer width="text" sx={{ pt: { xs: 4, md: 6 } }}>
```

`PageContainer` setzt `maxWidth`, `mx:auto`, responsives `px:{xs:2.5,sm:4,md:6}` und
liegt über den Papier-Overlays (`position:relative; zIndex:1`). Die Seite gibt nur
ihr **oberes** `pt` (und Sonder-`sx`) dazu — **kein eigenes `pb`/`py`** auf dem
äußeren Container. **`PublicHeader`/`PublicFooter`** spannen die Leiste voll,
begrenzen ihren Inhalt aber auf `PAGE_WIDTHS.wide`.

**Footer-Abstand (eine Stellschraube).** Den Abstand von Seiteninhalt zum Footer
besitzt **allein der `PublicFooter`** über sein `mt:{xs:8,md:11}`. Setzt eine Seite
zusätzlich `pb`/`py` auf ihren äußeren `PageContainer`, addiert sich beides und der
Abstand driftet von Seite zu Seite. Regel: äußerer Container nur `pt`, der Footer
trägt den Rest — so ist der Abstand überall gleich.

**Lesemaß.** Fließtext kappt zusätzlich auf ~66 Zeichen (Bringhurst) über `Prose`
(`app/src/components/Prose`), Default `measure='47rem'`, **`align='left'`** (durchgehende
linke Kante mit den vollbreiten Karten/Specimen). Nur *laufender* Mehrsatz-Text wird
gewrappt; strukturierte Inhalte (Karten-Grids, Specimen, Tabellen, Bild-/Chart-Panels,
Button-Reihen, Quiz-Auswahl, Übungsblatt-Konfiguration) bleiben vollbreit.

```tsx
<Prose align="left">
  <Typography variant="body1" sx={{ color: paper.inkSoft }}>{lead}</Typography>
</Prose>
```

**Dokumentseiten** (rein juristisch/textlich, z. B. `/impressum`) sind eine Ausnahme:
die *ganze* Seite ist **eine** linksbündige Dokumentspalte (Prosa **und** die kleinen
strukturierten Blöcke wie Porträt+Kontakt oder die Hosting-Tabelle) in einem
gemeinsamen Maß (`<Box sx={{ maxWidth: '48rem' }}>`). Hier wird **nicht** `Prose`
verwendet (das wrappt nur laufende Absätze) — die kleinen Blöcke würden vollbreit
verloren wirken, im Maß bleiben sie als Dokument zusammen.

---

## 5. Flächen-System

Erweitert [Style-Guide §8](style-guide.md) zur harten Regel:

- **Identität = Papier.** Der `PaperBackground` (Grundton + Korn + Vignette) trägt
  jede Seite. Nichts überlagert ihn mit einem durchscheinenden Weiß-Wash.
- **Karte/Panel = `paper.hi`** (solide). Durchscheinende Weiß-Washes
  (`rgba(255,255,255,0.18/0.45)`) sind verboten — sie wirken als „ausgewaschenes Creme".
  Eine Karte ist `paper.hi` + `1px solid paper.line`.
- **Arbeitsfläche = neutral.** Flächen, die einen **Chart-Ausschnitt, einen Scan,
  ein Glyphen-Crop oder ein A4-Blatt** rahmen, sind **weiß `#fff`** (Quiz-`QuestionVisual`,
  Tafel-Chart & Written-Glyph-Karten, Übungsblatt-A4). Der Admin-Canvas/Chart bleibt
  **dunkel `#111`**.
- **Ausnahme Blend-Specimen:** Ein Scan, der per `mixBlendMode:'multiply'` seinen
  weißen Grund auf das Papier fallen lässt (Offenbacher-Specimen), wird **nicht**
  geweißt — das bräche den Blend.
- Dekorative Textkarten (z. B. Tafel-Provenienz) bleiben `paper.hi`, nicht weiß.

Merksatz: **Identität trägt Papier, Lesetext liegt im Maß, ein Original liegt auf Weiß.**

---

## 6. Navigation / Informationsarchitektur

Drei Bereiche in der Top-Nav statt fünf Einzel-Links (`PublicHeader`):

```
Schriftkunde   ·   Lesen   ·   Schreiben
(Referenz)        (/lesen)     (/schreiben)
```

**Lesen** und **Schreiben** sind kleine **Hub-Übersichtsseiten** (kein Dropdown,
`sections/hub/HubView`), die je zwei Werkzeuge als Karten bündeln. Das löst die alte
Unklarheit „gehört die Tafel zu Lesen oder Schreiben?".

| Pfad | Seite | Bereich |
|---|---|---|
| `/` | Landing | Einstieg |
| `/schriftkunde` | Überblick der deutschen Schreibschriften | Schriftkunde |
| `/lesen` | Hub → Quiz, Tafel | Lesen |
| `/quiz` | Buchstaben-Quiz | Lesen |
| `/tafel` | Schreibtafel (Vorlage) | Lesen |
| `/schreiben` | Hub → Übungsblatt, Federprobe | Schreiben |
| `/schreiben/uebungsblatt` | Übungsblatt-Generator (PDF) | Schreiben |
| `/federprobe` | Live-Schreiber (Sütterlin-Synthese) | Schreiben |
| `/impressum` | Impressum, Datenschutz, Quellen | Footer |

Routen in `app/src/routes/paths.ts` + `routes/sections/public.tsx`. `/lehrbuch`
leitet weiter auf `/schriftkunde` (alter Name). Der Admin liegt unverändert hinter
`/admin/*` (5 Klicks auf die Wortmarke).

---

## 7. Komponenten-Inventar

| Komponente | Zweck | Kern-API / Hinweis |
|---|---|---|
| `PaperBackground` | Papier-Identität (Grund, Korn, Vignette) | umschließt jede öffentliche Seite (via `PublicLayout`) |
| `PublicLayout` | Chrome: Background + Header + `<main>` + optional Footer | `sx` für `<main>` |
| `PublicHeader` | sticky Markenleiste + 3-Bereiche-Nav | `tone='paper'\|'plain'`; 5 Taps → Admin |
| `PublicFooter` | geteilter Footer (Links, Impressum) | Breite `wide` |
| `PageContainer` | eine Inhaltsspalte, 3 Breiten | `width='narrow'\|'text'\|'wide'\|number`, `component`, `sx` |
| `Prose` | Lesemaß ~66 Zeichen | `align='left'\|'center'`, `measure='47rem'` |
| `PageHeader` | einheitlicher **Seitenkopf**: Bereichs-Eyebrow + Playfair-Titel + Intro | `eyebrow?`, `title`, `children` (Intro im `Prose`-Maß); jede öffentliche Seite außer Landing-Hero |
| `CategoryHeading` | **Abschnitts**titel mit Viridian-Kurrent-Initiale auf Haarlinie | innerhalb einer Seite (`/schriftkunde`, `/impressum`, `/tafel`, `/landing`) |
| `InfoHint` | grünes Kurrent-„(i)" + Popover („Mehr dazu") | app-weit, Detail eine Geste entfernt |
| `HubView` | Hub-Layout (Titel + Lead + Karten-Grid) | `title`, `lead`, `cards[{title,body,cta,to}]` |
| `HeroWritten` | einspaltiger Landing-Hero: Markenwort wird von einer Feder geschrieben | GLKurrent-Wort (Specimen) hinter `<HeroWord>` als Engine-Swap-Naht (Font jetzt, Engine später) |
| `WrittenGlyph` | ein Glyph „wie geschrieben" (Ductus-Playback) | weiße Arbeitsfläche |
| `WrittenWord` | ganzes Wort/Zeile aus Per-Glyph-Diagnostik + Übergängen | Engine-Pfad; Font-Specimen ist Fallback |
| `BootStatus` | Vollseiten-Boot-/Cold-Start-Zustand | Quiz, Admin |

---

## 8. Bewegung

Knapp und sinnstiftend (Style-Guide §6, Detailalgorithmen
[`reference/animation-rendering.md`](../reference/animation-rendering.md)):

- **Schreib-Reveal (Engine):** `stroke-dashoffset` auf der Mittellinie zeichnet den
  Ductus in Schreibrichtung (Tafel, Quiz, Federprobe).
- **Schreib-Reveal (Hero):** das GLKurrent-Markenwort wird per `clip-path`-Wisch
  links→rechts freigelegt, eine wandernde Federspitze (SVG) reitet auf der Kante,
  danach zieht sich ein Viridian-Flourish — `HeroWritten`.
- **Ink-Settle:** der gezeichnete Strich „setzt sich" (Eisengallus-Anmutung) leicht nach.
- **Hover:** Haarlinien-Unterstrich zieht sich in Viridian; Karten heben sich 2 px mit
  weichem Schatten; Übergänge 0.25–0.3 s.
- **`prefers-reduced-motion`:** immer ein fertiger Endzustand statt Animation.

---

## 9. Lesbarkeits-Leitregel (bindend)

Keine gebrochene Schrift und keine Schreibschrift als **Lesetext** — nicht in UI,
Überschriften oder Fließtext. Historische Formen (Kurrent/Sütterlin/Fraktur) erscheinen
**ausschließlich als markiertes Specimen** (eigene Fläche, als Beispiel gekennzeichnet).
Untergrenzen: Body ≥ 19 px, Caption ≥ 14 px. Kontrast: Tinte/Sepia auf Papier, nie
blass auf blass. Diese Regel hat Vorrang vor jeder Epochen-Anmutung.

---

## 10. Pflege & Sync

- Ändert sich eine Zahl/Token hier → `app/src/styles/paper.ts`, `theme/typography.ts`,
  `components/PageContainer`, `components/Prose`, `components/PageHeader` (Seitenkopf) bzw.
  `components/PublicFooter` (Footer-`mt` = der eine Abstand, §4) nachziehen (und umgekehrt).
- [Style-Guide](style-guide.md) trägt die *Begründung/Historie*, dieses Dokument den
  *Ist-Zustand*. [`.design-sync/conventions.md`](../../.design-sync/conventions.md)
  spiegelt die Marke nach Claude Design — bei Marken-Komponenten dort prüfen.
- `CLAUDE.md` ↔ `.github/copilot-instructions.md` bleiben synchron (Projektregel).
