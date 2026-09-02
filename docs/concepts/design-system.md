# Design-System — kurrentschrift.ink

> **Status (2026-08-03): lebend.** Beschreibt den Ist-Zustand des
> Frontends und ist am 2026-08-03 gegen den Code geprüft
> (Tokens, 19-px-Leiter samt Gewichten, Breiten 760/1152/1280, Kopfleiste,
> Routenliste).
> **Mitziehen bei jeder Änderung an `app/src/styles/paper.ts`,
> `theme/typography.ts`,
> `components/PageContainer|Prose|PageHeader|HeaderBar|PublicHeader|PublicFooter`,
> an der Werkbank-Kopfleiste (`sections/admin/shell/AdminHeader`) oder
> an der öffentlichen Routen-/Bereichsstruktur** — sonst driftet die
> Bauvorschrift von dem, was ausgeliefert wird.

> **Was dieses Dokument ist:** die *verbindliche, aktuelle* Bauvorschrift der
> öffentlichen Website — Tokens, Typo-Skala, Breiten, Flächen, Navigation,
> Komponenten, Bewegung, Lesbarkeit. Es beschreibt den **Ist-Zustand des Codes**
> (eine Stellschraube pro Regel), nicht die Entscheidungs­geschichte.
>
> **Geltungsbereich Admin:** Die **Typo-Skala (§3, samt Überschriften-Regel) und
> die Kopfleiste (§7 `HeaderBar`)** gelten auch für die Werkbank unter
> `/admin/*`; ebenso der Caption-Boden von 14 px (§9). Die Werkbank trägt
> dieselbe Marke und darf beim Betreten nicht wie eine zweite Anwendung wirken.
> Ihr **Arbeits-Layout** bleibt eigen: die drei Ansichten laufen vollbreit
> (§4, „Werkbank — vollbreit").
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

**Schrift-Auslieferung (seit 2026-08-27):** Alle `@font-face`-Regeln stehen früh
in `app/index.html` gegen selbst gehostete Dateien unter `app/public/fonts/`
(wörtliche Kopien der @fontsource-v5.3.0-Builds, Subsets latin + latin-ext),
NICHT im Bundle — zwei Above-the-fold-Schnitte (Playfair 600 und Garamond 400,
jeweils latin) sind per `<link rel="preload">` vorgeladen, damit sie nicht auf
den Entry-Chunk warten (mehr Preloads verlieren den Fast-3G-A/B). latin-ext trägt seine `unicode-range` und lädt
erst, wenn ein ſ o. Ä. auftaucht. Ausgeliefert werden nur latin/latin-ext: ein
Zeichen außerhalb beider Ranges (z. B. `↻`, `→`, künftig Griechisch/Kyrillisch)
fällt auf die Serif-Fallbacks zurück — bewusster Zuschnitt für eine
deutschsprachige Seite. Ein neuer Schnitt braucht eine Datei in `public/fonts/`
plus eine Regel in `index.html`; ein `@fontsource`-Import bringt ihn nicht mehr
mit (Mechanik und Update-Pfad: `frontend-stack.md` §6 „Schrift-Auslieferung").

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
| `subtitle2` | `1.0625rem` | 17 | 500 | 1.5 | kleines Display-Label, Panel-Titel der Werkbank |
| `caption` | `0.875rem` | 14 | 400 | 1.55 | Captions, Quellenzeilen (Boden ~14 px) |
| `overline` | `0.8125rem` | 13 | 500 | — | Eyebrow (`letterSpacing 0.12em`) |

Bei `subtitle2` kommt die **500** aus dem MUI-Default: `theme/typography.ts` setzt
dort nur `fontSize`/`lineHeight`. (Diese Tabelle nannte bis 2026-08-03 eine 400 —
Drift; maßgeblich ist der Code, korrigiert wurde das Dokument.)

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

**Werkbank-Köpfe.** Im Admin gilt dieselbe Regel eine Stufe kleiner. Der Ansichtskopf
(`ViewHeader` in `sections/admin/shell/Panel.tsx`) trägt Bereichs-Eyebrow + Titel in
**Playfair** (`fontFamily: display`, `fontWeight: 600`), Größe aus **`variant="h4"`** —
eine Ansicht sitzt unter einer Chrome-Leiste, nicht auf einer Landing-Seite. Panel-Titel
sind `variant="subtitle2"` in Garamond (`component="h2"`), damit kein Display-Schnitt mit
den Specimen-Glyphen konkurriert, die die Panels füllen. **Ein hartes `fontSize` auf einem
Playfair-Titel ist auch im Admin verboten** — Größe aus der Leiter, Face/Gewicht/
`letterpress` in `sx`. Die **Vorlagen-Auswahl** (`shell/StartView`) ist die eine
Admin-Seite, die wie eine öffentliche gesetzt ist: `PageContainer` + `PageHeader`
(reine Wahl, keine Arbeitsfläche).

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

`PageContainer` setzt `maxWidth`, `mx:auto`, ein responsives Innenmaß von 20/32/48 px und
liegt über den Papier-Overlays (`position:relative; zIndex:1`). Die Seite gibt nur
ihr **oberes** `pt` (und Sonder-`sx`) dazu — **kein eigenes `pb`/`py`** auf dem
äußeren Container. **`PublicHeader`/`PublicFooter`** spannen die Leiste voll,
begrenzen ihren Inhalt aber auf `PAGE_WIDTHS.wide`.

**Footer-Abstand (eine Stellschraube).** Den Abstand von Seiteninhalt zum Footer
besitzt **allein der `PublicFooter`** über sein `mt:{xs:8,md:11}`. Setzt eine Seite
zusätzlich `pb`/`py` auf ihren äußeren `PageContainer`, addiert sich beides und der
Abstand driftet von Seite zu Seite. Regel: äußerer Container nur `pt`, der Footer
trägt den Rest — so ist der Abstand überall gleich.

**Das Innenmaß schließt die Safe-Area ein.** `index.html` fährt
`viewport-fit=cover`, die Seite reicht auf Geräten mit Aussparung also bis unter
Notch und Home-Indikator. Darum steht das Gutter als
`max(20px, env(safe-area-inset-left))` (analog rechts, je Stufe) und der
`PublicFooter` als `calc(24px + env(safe-area-inset-bottom))`: das entworfene Maß
gilt überall, das Geräte-Inset gewinnt nur dort, wo es größer ist. Wer das
Innenmaß ändert, hält die `max()`-Form — sonst kommt die Kompensation lautlos
wieder abhanden.

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

**Werkbank — vollbreit (Ausnahme).** Die drei Ansichten unter `/admin/*`
(Buchstaben · Übergänge · Wörter) benutzen **kein** `PageContainer`: sie laufen
**vollbreit** und tragen ihr eigenes Innenmaß (`p:{xs:2,md:3}`); die Kopfleiste
setzt dazu `maxWidth='none'` (§7 `AdminHeader`). Grund: Chart-Ausschnitte,
Buchstabenraster und Paar-Matrizen sind Arbeitsflächen, die die Breite **brauchen** —
ein 1280er Deckel schneidet dort Evidenz weg, statt Lesbarkeit zu schützen, und
Fließtext, den das Maß schützen müsste, gibt es hier nicht (Intros kappen bei ~47 rem).
Die **Vorlagen-Auswahl** (`/admin`) ist die Ausnahme der Ausnahme und sitzt im
`PageContainer` wie eine öffentliche Seite.

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
| `/lesen` | Hub → Quiz, Tafel, Lesart prüfen | Lesen |
| `/quiz` | Lese-Quiz (Buchstaben + ganze Wörter) | Lesen |
| `/tafel` | Schreibtafel (Vorlage) | Lesen |
| `/lesen/vergleichen` | Lesart prüfen (Vermutung geschrieben + Lesarten mit vertauschten Verwechslern + Verwechsler-Paare) | Lesen |
| `/schreiben` | Hub → Übungsblatt, Federprobe | Schreiben |
| `/schreiben/uebungsblatt` | Übungsblatt-Generator (PDF) | Schreiben |
| `/federprobe` | Live-Schreiber (Sütterlin-Synthese) | Schreiben |
| `/impressum` | Impressum, Datenschutz, Quellen | Footer |

Routen in `app/src/routes/paths.ts` + `routes/sections/public.tsx`. `/lehrbuch`
leitet weiter auf `/schriftkunde` (alter Name). Der Admin liegt unverändert hinter
`/admin/*` (5 Klicks auf die Wortmarke) und trägt **dieselbe Leiste** mit seinen
eigenen drei Bereichen (Buchstaben · Übergänge · Wörter) — §7 `HeaderBar`.

---

## 7. Komponenten-Inventar

| Komponente | Zweck | Kern-API / Hinweis |
|---|---|---|
| `PaperBackground` | Papier-Identität (Grund, Korn, Vignette) | umschließt jede öffentliche Seite (via `PublicLayout`) |
| `PublicLayout` | Chrome: Background + Header + `<main>` + optional Footer | `sx` für `<main>` |
| `HeaderBar` | DIE Kopf-Chrome (sticky, `blur(6px)`, Haarlinie) + Geschwister-Exporte `Wordmark` (•kurrentschrift.ink, Viridian-Punkt, kursive TLD) und `HeaderNavLink` (Playfair-Link, Viridian-Unterstrich, `aria-current`) | `maxWidth` (Default `wide`, `'none'` = vollbreit), `zIndex`, `contentSx`; **eine** Leiste für öffentliche Seiten **und** Werkbank |
| `PublicHeader` | sticky Markenleiste + 3-Bereiche-Nav | auf `HeaderBar` gebaut, Inhalt auf `wide`; nur noch `sx` (die `tone`-Variante hatte keinen Aufrufer und ist entfallen); 5 Taps → Admin |
| `AdminHeader` | dieselbe Leiste für die Werkbank (`sections/admin/shell`) | **vollbreit** (`maxWidth='none'`, §4), `zIndex 1100` (unter Korb-Drawer 1200 und LetterPicker-Popover 1300) + **zwei Zusatz-Slots**: Vorlagen-Chip (→ `/admin`) und Auftragskorb-⚑ mit Badge |
| `PublicFooter` | geteilter Footer (Links, Impressum) | Breite `wide` |
| `PageContainer` | eine Inhaltsspalte, 3 Breiten | `width='narrow'\|'text'\|'wide'\|number`, `component`, `sx` |
| `Prose` | Lesemaß ~66 Zeichen | `align='left'\|'center'`, `measure='47rem'` |
| `PageHeader` | einheitlicher **Seitenkopf**: Bereichs-Eyebrow + Playfair-Titel + Intro | `eyebrow?`, `title`, `children` (Intro im `Prose`-Maß); jede öffentliche Seite außer Landing-Hero |
| `CategoryHeading` | **Abschnitts**titel mit Viridian-Kurrent-Initiale auf Haarlinie | innerhalb einer Seite (`/schriftkunde`, `/impressum`, `/tafel`, `/landing`) |
| `InfoHint` | grünes Kurrent-„(i)" + Popover („Mehr dazu") | app-weit, Detail eine Geste entfernt |
| `PaperCardLink` | DIE Papier-Karte, die ein Link ist: Hover/Fokus heben sie an, Rand wird viridian | `to`, `sx`; Geschwister-Export `PaperCardCta` (Haarlinie wischt bei Karten-Hover/-Fokus ein) — genutzt von Landing, Hubs, `/schriftkunde` |
| `HubView` | Hub-Layout (Titel + Lead + Karten-Grid) | `title`, `lead`, `cards[{title,body,cta,to}]` |
| `HeroWritten` | einspaltiger Landing-Hero: Markenwort wird von der Engine geschrieben | Engine-first (`WrittenWord`, seit 2026-08-27); die Engine bekommt beliebig lange (Geduld-Zeile nach ~3 s, Autor-Entscheid 2026-08-27) — GLKurrent-Wort (Specimen) mit Wisch + Federspitze nur bei echtem Scheitern (Fetch-Fehler, fehlende Glyphen), Caption wechselt mit dem Modus |
| `WrittenGlyph` | ein Glyph „wie geschrieben" (Ductus-Playback) | weiße Arbeitsfläche; `showReplay=false` für kleine Specimens mit eigener Replay-Geste |
| `SpecimenStrip` | Buchstaben „wie geschrieben" als **markiertes Specimen** (§9): eigene Haarlinien-Fläche in `paper.hi`, Antiqua-Beschriftung darunter, Klick schreibt neu | `specimens[{key,label}]`, `payloads` (EIN Batch je Seite über `useSpecimenPayloads`), `height`; montiert erst in Sichtweite, zieht sich zurück, wenn nichts schreibbar ist — Schriftkunde-Besonderheiten, Lesart-Verwechsler |
| `WrittenWord` | ganzes Wort/Zeile aus Per-Glyph-Diagnostik + Übergängen | Engine-Pfad; Font-Specimen ist Fallback |
| `BootStatus` | Vollseiten-Boot-/Cold-Start-Zustand | Quiz, Admin |
| `BackToTop` | schwebende Rückkehr an den Seitenanfang, erscheint ab zwei Bildschirmen Scrollweg | nur auf den langen Inhaltsseiten (`/schriftkunde` ≈ 20 Handy-Bildschirme, `/impressum`, `/lesen/vergleichen`); 44 × 44, Papierfläche mit Haarlinie (§5), `prefers-reduced-motion` springt statt zu gleiten |

---

## 8. Bewegung

Knapp und sinnstiftend (Style-Guide §6, Detailalgorithmen
[`reference/animation-rendering.md`](../reference/animation-rendering.md)):

- **Schreib-Reveal (Engine):** `stroke-dashoffset` auf der Mittellinie zeichnet den
  Ductus in Schreibrichtung (Tafel, Quiz, Federprobe).
- **Schreib-Reveal (Hero):** das Markenwort schreibt die Synthese-Engine Zug um
  Zug (`WrittenWord`), danach zieht sich ein Viridian-Flourish, dessen Einsatz
  am tatsächlichen Schreibende hängt (`onResolved.writeEndMs`). Ein kaltes
  Backend heißt WARTEN, nicht ausweichen (Autor-Entscheid 2026-08-27): die
  reservierte Wortfläche bleibt stehen, nach ~3 s erscheint eine leise
  Geduld-Zeile. Nur echtes Scheitern (Fetch-Fehler nach den Retries, fehlende
  Glyphen) fällt auf das GLKurrent-Markenwort zurück — `clip-path`-Wisch
  links→rechts, wandernde Federspitze (SVG) auf der Kante — `HeroWritten`;
  `index.html` wärmt die Komposition auf `/` vor.
- **Ink-Settle:** der gezeichnete Strich „setzt sich" (Eisengallus-Anmutung) leicht nach.
- **Hover:** Haarlinien-Unterstrich zieht sich in Viridian; Karten heben sich 2 px mit
  weichem Schatten; Übergänge 0.25–0.3 s.
- **`prefers-reduced-motion`:** immer ein fertiger Endzustand statt Animation.

---

## 9. Lesbarkeits-Leitregel (bindend)

Keine gebrochene Schrift und keine Schreibschrift als **Lesetext** — nicht in UI,
Überschriften oder Fließtext. Historische Formen (Kurrent/Sütterlin/Fraktur) erscheinen
**ausschließlich als markiertes Specimen** (eigene Fläche, als Beispiel gekennzeichnet).
Untergrenzen: Body ≥ 19 px, Caption ≥ 14 px — **auch in der Werkbank** (eine
Beleg-Kachel beschriftet mit `variant="caption"`, nicht mit 10 px). Kontrast:
Tinte/Sepia auf Papier, nie blass auf blass. Diese Regel hat Vorrang vor jeder
Epochen-Anmutung.

**Messbar statt behauptet.** Der Typo-Boden hat ein eincheckbares Gitter:
`node app/scripts/type-floor.mjs` fährt alle öffentlichen Routen in einem echten
Browser an, liest die *berechnete* Schriftgröße jedes Elements mit eigenem Text
und schlägt unter 14 px fehl (der 13-px-`overline` ist als Teil der Leiter aus
§3 ausgenommen). Nach jeder Typo- oder Theme-Änderung laufen lassen; das Skript
ist der Mobil-Schritt von `/verify-frontend`.

### 9.1 Fokus (bindend)

**Jedes fokussierbare Element trägt einen sichtbaren Ring:** 2 px `viridian`,
`outline-offset` 2–3 px. Er liegt EINMAL im Theme
(`theme/components.ts` → `MuiButtonBase` + `MuiChip` + `MuiLink`) und trifft damit
Button, IconButton, ToggleButton, Chip, jedes eigene `ButtonBase` und jeden Link.
Drei Flächen haben keine MUI-Basis und tragen darum ihre eigene Regel:
`PaperCardLink` und `HeaderNavLink` denselben Ring, die SVG-Zellen der
Schreibtafel stattdessen eine eingefärbte Zellenfläche (`WrittenSheet.tsx`) —
ein Ring um ein SVG-`<g>` säße dort falsch. Auch MUI-Textfelder bleiben
ausgenommen: sie zeigen Fokus über ihren eigenen Rahmen (2 px `viridian`).
Hintergrund: MUIs `ButtonBase` setzt selbst `outline: 0` — ohne die Theme-Regel
ist eine fokussierte Schaltfläche von ihren Nachbarn nicht zu unterscheiden (das
Quiz war so per Tastatur unbedienbar, Audit 2026-09-02). Lighthouse sieht diesen
Fehler nicht (`focusable-controls` ist dort *manual*): Der Nachweis ist ein
Tastatur-Durchgang, kein Score.

### 9.2 Links (bindend)

**Ein Link im Fließtext ist ohne Farbsehen erkennbar:** durchgehend unterstrichen
(`MuiLink.defaultProps.underline = 'always'`), in `paper.viridianText` (5,15:1
auf dem Papiergrund), die Unterstreichung als Haarlinie derselben Farbe. Farbe
allein reicht nicht — gegen die Prosa stand sie bei 1,35:1, und eine Unterstreichung
erst bei `:hover` gibt es für Tastatur und Finger gar nicht (WCAG 1.4.1).
Die Regel wohnt im Theme; die drei Prosa-Seiten haben ihre eigenen `proseLink`-Konstanten
dafür abgegeben. **Ausnahme: Chrome, die als Chrome liest** — Kopfleiste und Fußzeile
setzen weiter `textDecoration: 'none'` in ihrem `sx` (ihre Trennung vom Text kommt
aus der Position, nicht aus der Auszeichnung). Gefüllte CTAs sind keine Links im
Sinne dieser Regel; für sie gilt: Label ≥ 600 oder Fläche auf `viridianText`.

### 9.3 Trefferflächen (bindend — Entscheid des Autors, 2026-09-03)

**Interaktive Ziele messen ≥ 44 px in der kleineren Kante** (Apple HIG 44 pt,
Material 48 dp); Ausnahme sind Links im Fließtext. Wo die Optik ein kleineres
Element verlangt, trägt es eine unsichtbare Trefferfläche statt einer kleineren
Wahrheit — `hitArea()` aus `app/src/styles/hitArea.ts` (ein zentriertes
`::after` mit `max(100%, 44px)`; die Optik bleibt unverändert).

Die Regel geht über WCAG hinaus: SC 2.5.8 (24 × 24 px) hielt die Seite schon
vorher über die Abstandsausnahme, hier gilt die Plattformempfehlung. Sie war bis
zum 03.09.2026 als Vorschlag notiert und ist seit dem Entscheid des Autors
bindend.

Angewandt auf `ReplayButton`, `InfoHint`, die Quiz-Nebenknöpfe („beenden",
„Einstellungen ändern"), das Detail-Schließen der Tafel, die Federprobe-Chips und
„Link kopieren"; die Umschaltgruppen wachsen unter `sm` per Theme auf
`minHeight: 44`.

**Wo Nachbarn dicht stehen, wächst das Element statt seiner Trefferfläche.** Die
drei Bereichslinks der Kopfleiste sind der Fall: auf dem Handy bricht die Leiste
in zwei Zeilen, deren Textmitten 28 px auseinanderliegen — zwei unsichtbare
44er-Flächen hätten sich um 16 px überlappt, und ein Tipp auf „Lesen" wäre auf
„Schriftkunde" gelandet. `HeaderNavLink` bekommt darum echtes Innenmaß
(`minHeight`/`minWidth` 44, `px`), womit die Zeilen auseinanderrücken; die
Haarlinie sitzt seither an einem inneren `span`, damit sie weiter am Wort klebt
statt am Polster. Die Leiste wächst dadurch auf schmalen Geräten von 82 auf
121 px, auf `sm+` bleibt sie unverändert. Faustregel: Überlagerung nur dort, wo
das Element allein steht.

**Offen — Autor-Entscheid: die Zellen der Schreibtafel.** Die geschriebene Tafel
setzt das Alphabet als SVG-Zellen, die ihre Zeile lückenlos kacheln (bei 390 px
gemessen: 41–98 px breit, Lücke 0, Höhe 73 px). Die schmalsten reißen den Boden
in der Breite. Beide Auswege kosten etwas: eine unsichtbare Fläche griffe in den
Nachbarbuchstaben und nähme ihm den Tipp, eine Verbreiterung baut das
Nachschlage-Raster um, dessentwegen die Seite existiert. WCAG 2.2 SC 2.5.8 ist
mit 41 × 73 px deutlich erfüllt. Bis zur Entscheidung stehen die Zellen als
benannte Ausnahme in `touch-targets.mjs` — sichtbar gezählt, nicht stillschweigend
übersprungen.

**Messbar statt behauptet**, wie der Typo-Boden: `npm run touch-targets`
(`app/scripts/touch-targets.mjs`) fährt **alle** öffentlichen Routen an und misst
**jedes** interaktive Element — 217 sind es heute. Ausgenommen ist genau die eine
Ausnahme der Regel, und zwar an dem Merkmal, das §9.2 ihr gibt: ein `<a>` mit
Unterstreichung ist ein Fließtext-Link (84 Stück); Chrome, das nur wie ein Link
aussieht, setzt `textDecoration: none` und wird mitgemessen. Eine gepflegte
Liste stand vorher hier und war die falsche Form — sie bestand, während die
Lesart-Chips und die Tafel-Schrittknöpfe den Boden rissen.

Geprüft wird die echte Trefferfläche statt einer berechneten Größe: für jede
Achse, auf der ein Element kleiner als 44 px GEZEICHNET ist, fragt das Skript per
`document.elementFromPoint` an der Kante des 44er-Quadrats nach, und dort muss
das Element selbst antworten. Das fängt den einen stillen Weg, auf dem die Regel
bricht: ein `overflow: hidden` beschneidet das Pseudo-Element, die Zeichnung
bleibt gleich und das Ziel schrumpft unbemerkt zurück. Achsen, auf denen die Box
schon ≥ 44 px ist, werden nicht geprüft — dort trägt die Hilfe nichts, und die
Trefferfläche eines Nachbarn dürfte den Punkt zu Recht gewinnen.
Kein Gate in der CI: das Skript braucht die laufende Seite samt erreichbarer API.

**Die Zeilenteilung zählt mit.** Wo umbrechende Elemente eine unsichtbare
Trefferfläche tragen, muss der ZEILENABSTAND sie fassen, sonst greift die untere
Zeile über die obere und nimmt ihr die Tipps (gemessen an den Federprobe-Chips:
28 px Chip + 12 px Lücke = 40 px Rasterhöhe, die untere Reihe gewann). Regel:
`rowGap` so wählen, dass Elementhöhe + Lücke ≥ 44 px.

---

## 10. Pflege & Sync

- Ändert sich eine Zahl/Token hier → `app/src/styles/paper.ts`, `theme/typography.ts`,
  `components/PageContainer`, `components/Prose`, `components/PageHeader` (Seitenkopf),
  `components/HeaderBar` (die eine Kopfleiste, §7) bzw.
  `components/PublicFooter` (Footer-`mt` = der eine Abstand, §4) nachziehen (und umgekehrt).
- Die drei Bedienbarkeits-Regeln aus §9 wohnen an genau einer Stelle:
  `theme/components.ts` (Fokusring, Link-Auszeichnung, Typo-Boden der
  MUI-`small`-Größen, `minHeight` der Umschaltgruppen unter `sm`) und
  `styles/hitArea.ts` (Trefferfläche). Eine neue Ausnahme gehört dorthin, nicht
  an die Aufrufstelle. Gegenprobe: `npm run type-floor` (§9) und
  `npm run touch-targets` (§9.3) — beide gegen die laufende Seite — plus ein
  Tastatur-Durchgang für den Fokusring (§9.1), den kein Skript ersetzt.
  Ein neues Bedienelement muss nirgends nachgetragen werden — der Sweep findet
  jedes von selbst; nur eine begründete Ausnahme gehört benannt in
  `app/scripts/touch-targets.mjs`.
- **Der Admin ist mitgemeint**, wo §3 (Typo) und §7 (`HeaderBar`) es sagen: eine Änderung
  an Leiter oder Kopfleiste wird an **beiden** Leisten (`PublicHeader` +
  `sections/admin/shell/AdminHeader`) und an den Werkbank-Köpfen (`shell/Panel.tsx`,
  `shell/StartView.tsx`) geprüft. Das Arbeits-Layout der drei Ansichten ist davon
  ausgenommen (§4 „Werkbank — vollbreit").
- [Style-Guide](style-guide.md) trägt die *Begründung/Historie*, dieses Dokument den
  *Ist-Zustand*. [`.design-sync/conventions.md`](../../.design-sync/conventions.md)
  spiegelt die Marke nach Claude Design — bei Marken-Komponenten dort prüfen.
- `CLAUDE.md` ↔ `.github/copilot-instructions.md` bleiben synchron (Projektregel).
