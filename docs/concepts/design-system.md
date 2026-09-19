# Design-System — kurrentschrift.ink

> **Status (2026-09-19): lebend.** Beschreibt den Ist-Zustand des
> Frontends und ist am 2026-08-03 gegen den Code geprüft
> (Tokens, 19-px-Leiter samt Gewichten, Breiten 760/1152/1280, Kopfleiste,
> Routenliste); am 2026-09-04 um den Tintenboden geschriebener Zeilen
> ergänzt (§9, §7 `WrittenWord`) und um die Postkarten-Federprobe samt
> Schriftgrößen-Leiter (§7.1); am 2026-09-19 um die Ebenen- und Rollen-Token
> samt Strichart-Regel und das `mono`-Token (§2, §7, §10).
> **Mitziehen bei jeder Änderung an `app/src/styles/paper.ts`,
> `theme/typography.ts`,
> `components/PageContainer|Prose|PageHeader|HeaderBar|PublicHeader|PublicFooter`,
> an der Werkbank-Kopfleiste (`sections/admin/shell/AdminHeader`) oder
> an der öffentlichen Routen-/Bereichsstruktur** — sonst driftet die
> Bauvorschrift von dem, was ausgeliefert wird.
>
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

### Ebenen- und Rollen-Token (seit 2026-09-19)

Geschwister-Exporte neben `paper` (wie `pigment`), denn `paper` ist das flache
IDENTITÄTS-Objekt und Arbeitsflächen steigen bewusst aus ihm aus (§5). Eine
**Ebene** liegt über Ausschnitt, Scan oder Skizze und muss darum deckend
gezeichnet gegen weiß UND gegen Platten-Tinte 3 : 1 erreichen (WCAG 1.4.11;
durchscheinend gezeichnet siehe den Absatz danach); eine **Rolle** wird auf Papier
gelesen und misst sich an `paper.hi`/`paper.bg`. Die Zahlen und die
Deuteranopie-Abstände prüft `app/src/styles/paper.test.ts`.

Der Boden gilt für die **deckend gezeichnete Marke** — Legendenstrich, eigene
Fläche, Chip, deckender Zug. Er gilt **nicht** für den durchscheinenden
Vergleichs-Overlay über einem Scan, und das ist die zweite benannte Ausnahme,
kein Versehen: die Engine-Silhouette liegt bei 0,40–0,45 Deckkraft, damit die
Tinte darunter lesbar bleibt — genau dafür ist sie da. Zusammengerechnet ergibt
Zinnober bei 0,42 noch **1,81 : 1 auf weiß und 1,71 : 1 auf der Tinte**
(0,40 → 1,76/1,66; 0,45 → 1,90/1,80). Die Unterscheidung trägt dort **Strichart
plus Legende**, nicht der Kontrastwert. Jede dieser Deckkräfte steht als
benanntes Token in `layerAlpha`, und `paper.test.ts` rechnet die Farbe jeder
einzelnen über weiß und über der Tinte zusammen und prüft sie **namentlich mit
ihrer Zahl** — eine geänderte Deckkraft oder ein geänderter Farbton bewegt also
eine Zusage. *Nachzug:* ob eine höhere Deckkraft oder `mix-blend-mode: multiply`
besser trägt, lässt sich erst an echten Platten-Daten im Produktions-Admin
beurteilen; blind umgestellt wird hier nichts.

| Token | Hex | Bedeutung | Strichart |
|---|---|---|---|
| `layer.trace` | `#1b7abb` | Spur — die nachgefahrene Feder (angehobenes Preußischblau, kein Periodenton) | durchgezogen |
| `layer.path` | `#cc7722` | Pfad — das ferne Ende der Schreibreihenfolge-Rampe (Ocker) | durchgezogen |
| `layer.engine` | `#e34234` | Engine — was der Setzer schreibt (Zinnober) | **gestrichelt** |
| `role.tafel` | `#003153` | Tafel (Preußischblau) | durchgezogen |
| `role.platte` | `#6b2e2a` | Platte (Ochsenblut) | **gestrichelt** |
| `role.eigenhand` | `#a85f17` | Eigenhand (angehobener Ocker, kein Periodenton) | **gepunktet** |

Spur und Pfad teilen die durchgezogene Linie: es ist dieselbe gezeichnete Linie,
und der Pfad bringt eigene Kanäle mit (Rampe, Ansatzpunkt, Pfeilspitzen). Ocker
und Zinnober sind für einen Deuteranopen **eine** Farbe — die eine benannte
Ausnahme, getragen von Strichart und Legende. **Keine Rolle trägt Viridian**: es
ist Akzent, `success` und Fokusring zugleich. Ein aktiver ZUSTAND darf es tragen.

Ein Rollen-Token färbt die **Marke** (Punkt, Rahmen, Strich), nie laufenden Text
— das Etikett daneben bleibt `text.primary`: `role.eigenhand` steht bei 3,99 : 1
auf `paper.hi`, über der Nicht-Text-Schwelle, unter den 4,5 : 1 für Fließtext.
Eine farbige Beschriftung bräuchte erst ein abgeleitetes `roleText`, wie
`paper.viridianText` neben Viridian.

Der **Absetzer** (`absetzer`, Violett `#8a5cd0`, gepunktet) ist KEINE Ebene,
sondern die zweite Marke der Pfad-Ebene: halbe Strichbreite, unter den Zügen,
er verbindet Zugende und nächsten Ansatz. Darum gilt für ihn die Paar-Regel
nicht, wohl aber die Grund-Regel — und eine dritte: seine Farbe darf **keine
sein, durch die die Spur→Pfad-Rampe läuft**. Die läuft durch ein Grau, ein
grauer Absetzer sah also aus wie der mittlere Zug eines dreiteiligen Pfades
(im Browser gemessen, 2026-09-19). Ebenso ist `WERKBANK_COLORS.current`, die
**Laufform-Referenz** auf der Buchstaben-Skizze, keine Ebene: Ocker wie der Pfad,
aber **gepunktet** — die 4:3-Strichelung ist die Signatur der Engine-Ebene und
bleibt ihr. Eine Nicht-Ebene nimmt die freie Strichart, nie eine gelehrte.

Eine Strichart ist Strichmuster **und** Linienende (`StrokeStyle =
{ dash, cap }`, `strokeStyle.solid|dashed|dotted`): „gepunktet" ist ein
Null-Strich unter rundem Ende, denn `[2, 2]` unter dem SVG-Standard `butt`
zeichnet Quadrate — also eine zweite Strichelung statt Punkten. Verbraucher
nehmen darum immer das ganze Token, nie nur das Muster.

**Strichart-Regel (bindend).** Farbe ist nie der einzige Kanal: erkennbar wird
eine Ebene oder Rolle aus **Rollen-Etikett + Position + Strichart**, die Farbe
kommt dazu. Daraus folgt (1) jede Ebene und jede Rolle hat genau eine Strichart,
und die Legende (`LayerDot`, §7) zeigt sie mit; (2) eine FLÄCHE trägt statt der
Strichart ihre Deckkraft; (3) **die Texte zu Ebenen und Rollen nennen keine
Farben** — „erster Zug grün, letzter blau" ist der Satz, mit dem ein
farbfehlsichtiger Leser nichts anfangen kann. Die Texte nennen die Bedeutung
oder die Strichart, die Legende trägt die Farbe. Ausgenommen sind vorerst die
Diagnose- und Wizard-Signalfarben (`overlayColors.ts`, Landmark-Farben,
Wizard-Griffe), wo die Farbe teils die Handlungsanweisung ist („den grünen Punkt
ziehen") — ein benannter Nachzug, kein Freibrief für neue Sätze.

Font-Tokens (ebenfalls `styles/paper.ts`): `garamond` (EB Garamond, Body/UI &
Theme-Default), `display` (Playfair Display, Display-Überschriften), `script`
(GL-GermanCursive/„GLKurrent", Kurrent-Specimen), `suetterlin` (HJZ-Sütterlin-Font,
Specimen-Fallback), `mono` (Befehle, Zahlenkolonnen, Fehlertexte — ein
System-Stack und **bewusst keine ausgelieferte Datei**: ein Mono-Webfont wäre
eine neue Datei, eine `@font-face`-Regel, ein Preload-Posten und eine OFL-Notiz
für eine Handvoll Admin-Flächen), `letterpress` (ein `textShadow`-String für
Tiefdruck-Anmutung).

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
eigenen vier Bereichen (Buchstaben · Übergänge · Wörter · Eigenhand) und der
Scope-Leiste darunter — §7 `HeaderBar`.

---

## 7. Komponenten-Inventar

| Komponente | Zweck | Kern-API / Hinweis |
|---|---|---|
| `PaperBackground` | Papier-Identität (Grund, Korn, Vignette) | umschließt jede öffentliche Seite (via `PublicLayout`) |
| `PublicLayout` | Chrome: Background + Header + `<main>` + optional Footer | `sx` für `<main>` |
| `HeaderBar` | DIE Kopf-Chrome (sticky, `blur(6px)`, Haarlinie) + Geschwister-Exporte `Wordmark` (•kurrentschrift.ink, Viridian-Punkt, kursive TLD) und `HeaderNavLink` (Playfair-Link, Viridian-Unterstrich, `aria-current`) | `maxWidth` (Default `wide`, `'none'` = vollbreit), `zIndex`, `contentSx`, `below` (zweite Zeile INNERHALB des Sticky-Blocks, heute die Scope-Leiste); **eine** Leiste für öffentliche Seiten **und** Werkbank |
| `PublicHeader` | sticky Markenleiste + 3-Bereiche-Nav | auf `HeaderBar` gebaut, Inhalt auf `wide`; nur noch `sx` (die `tone`-Variante hatte keinen Aufrufer und ist entfallen); 5 Taps → Admin |
| `AdminHeader` | dieselbe Leiste für die Werkbank (`sections/admin/shell`) | **vollbreit** (`maxWidth='none'`, §4), `zIndex 1100` (unter Korb-Drawer 1200 und LetterPicker-Popover 1300); Wortmarke · Bereichs-Nav (bei `xs` eine Scroll-Snap-Zeile mit 4 px Unterrand, sonst wüchse ein Scrollbalken für die Hover-Haarlinie) · Auftragskorb-⚑ als blankes Icon mit 44-px-`hitArea` und benanntem `aria-label` (der die Zahl mitführt), und im `below`-Schlitz die `ScopeBar`. **Kein Badge:** MUI setzt dessen Zahl in 12 px, unter dem Boden von §9 (V25) |
| `ScopeBar` | die **Scope-Leiste**: zwei Felder „Vorlage:" und „Hand:", die den Arbeitsbereich zeigen und nie umschalten | beide Felder sind Links (Vorlagen-Auswahl · Eigenhand-Seite), das aktive trägt `aria-current` **und** eine Viridian-Leiste links (Farbe nie allein, §9); der Korb-Zähler steht sichtbar im Vorlagen-Feld, 44 px Trefferhöhe je Feld |
| `PublicFooter` | geteilter Footer (Links, Impressum) | Breite `wide` |
| `PageContainer` | eine Inhaltsspalte, 3 Breiten | `width='narrow'\|'text'\|'wide'\|number`, `component`, `sx` |
| `Prose` | Lesemaß ~66 Zeichen | `align='left'\|'center'`, `measure='47rem'` |
| `PageHeader` | einheitlicher **Seitenkopf**: Bereichs-Eyebrow + Playfair-Titel + Intro | `eyebrow?`, `title`, `children` (Intro im `Prose`-Maß); jede öffentliche Seite außer Landing-Hero |
| `CategoryHeading` | **Abschnitts**titel mit Viridian-Kurrent-Initiale auf Haarlinie | innerhalb einer Seite (`/schriftkunde`, `/impressum`, `/tafel`, `/landing`) |
| `InfoHint` | grünes Kurrent-„(i)" + Popover („Mehr dazu") | app-weit, Detail eine Geste entfernt; in der Werkbank das Gegenstück zum Hover (§9.4) — **höchstens einer je Zeile und Gegenstand**, `label` benennt ihn („Score und Abzüge erklären") |
| `ScoreHelp` (Admin) | die EINE Erklärung einer bewerteten Zeile: Score, „kein Score", „Fit ⌀", Abzugsrichtung, die sechs Kategorien | `quality/scoreParts.tsx`, ohne Props; am Kopf von `ScoreBreakdown` und am Anfang von `ScoreBreakdownInline` — ersetzt bis zu neun Hover je Zeile (§9.4) |
| `useRovingList` (Hook) | macht eine Liste zu EINEM Tab-Stopp (§9.5) | `hooks/useRovingList.ts`, `orientation: 'vertical' \| 'horizontal'`; markiert werden nur Behälter und Zeile (`rowProps(key)`), die Bedienelemente findet der Hook — `ROVING_SKIP` nimmt einen Zeilenkörper aus |
| `SubjectStepper` (Admin) | ‹ Gegenstand › im Detailkopf, plus Alt+Umschalt+←/→ (§9.5) | `shell/SubjectStepper.tsx`: `prev`/`next`/`onStep`/`between`; die Reihenfolge kommt aus `shell/subjectNav.ts`, ihr Name als `note` des `ViewHeader` |
| `PaperCardLink` | DIE Papier-Karte, die ein Link ist: Hover/Fokus heben sie an, Rand wird viridian | `to`, `sx`; Geschwister-Export `PaperCardCta` (Haarlinie wischt bei Karten-Hover/-Fokus ein) — genutzt von Landing, Hubs, `/schriftkunde` |
| `HubView` | Hub-Layout (Titel + Lead + Karten-Grid) | `title`, `lead`, `cards[{title,body,cta,to}]` |
| `HeroWritten` | einspaltiger Landing-Hero: Markenwort wird von der Engine geschrieben | Engine-first (`WrittenWord`, seit 2026-08-27); die Engine bekommt beliebig lange (Geduld-Zeile nach ~3 s, Autor-Entscheid 2026-08-27) — GLKurrent-Wort (Specimen) mit Wisch + Federspitze nur bei echtem Scheitern (Fetch-Fehler, fehlende Glyphen), Caption wechselt mit dem Modus |
| `WrittenGlyph` | ein Glyph „wie geschrieben" (Ductus-Playback) | weiße Arbeitsfläche; `showReplay=false` für kleine Specimens mit eigener Replay-Geste |
| `SpecimenStrip` | Buchstaben „wie geschrieben" als **markiertes Specimen** (§9): eigene Haarlinien-Fläche in `paper.hi`, Antiqua-Beschriftung darunter, Klick schreibt neu | `specimens[{key,label}]`, `payloads` (EIN Batch je Seite über `useSpecimenPayloads`), `height`; montiert erst in Sichtweite, zieht sich zurück, wenn nichts schreibbar ist — Schriftkunde-Besonderheiten, Lesart-Verwechsler |
| `WrittenWord` | ganzes Wort/Zeile aus Per-Glyph-Diagnostik + Übergängen | Engine-Pfad; Font-Specimen ist Fallback. Größe und Zeilenzahl kommen aus der **gemessenen** Rahmenbreite, nie aus der Aufrufer-Konstante `maxWidth` (die bleibt Obergrenze): Unterschreitet der Text den **Tintenboden von 14 px x-Höhe** (§9, `lib/lineWrap.ts`), bricht er an Wortgrenzen um — **jede Zeile eine eigene Komposition und ein eigener durchgehender Federzug**, alle Zeilen in einer x-Höhe und links bündig (Autor-Entscheid 2026-09-04; verworfen: Maßstab-Boden mit Scrollfläche, viewportgekoppelte Zeichengrenze). Ein einzelnes zu breites Wort wird nicht getrennt und bleibt unter dem Boden. Seit 2026-09-04 bricht der Text auch an **getippten** Umbrüchen (`planParagraphs`), und die Federprobe gibt über `targetXHeightPx` eine gewünschte x-Höhe vor (§7.1) |
| `BootStatus` | Vollseiten-Boot-/Cold-Start-Zustand | Quiz, Admin |
| `LayerDot` (Admin) | Legenden-Marke einer Ebene: **Farbe UND Strichart** der Linie, die sie beschriftet — der Schalter ist die Legende | `color`, `style` (ein ganzes `StrokeStyle` aus `layerDash`/`roleDash` — Muster UND Linienende); ein kurzer Strich, kein Punkt, damit „durchgezogen" ein sichtbarer Zustand ist (§2) |
| `TerminalCommand` (Admin) | ein Shell-Befehl, der wirklich getippt oder genommen werden kann | `command`, `lead?`; `mono` + `variant="body2"` (§3, nie ein eigenes `fontSize`), `user-select: all`, Kopierknopf |
| `Uebergabekarte` (Admin) | ein Medienbruch, gezeigt statt versteckt: die zustandsgetriebene Karte für einen Schritt, der am Rechner laufen muss | `karte` (Titel · Warum · Befehl · „Danach hier" · Reihenfolge); Fläche `paper.hi` + Haarlinie (§5), Befehlszeile über `TerminalCommand`, der Reihenfolge-Hinweis als Beschriftung und nie als Tooltip (§9.3). **Unsichtbar, wenn nichts fällig ist** — ohne fällige Karte entfällt der ganze Block samt Überschrift; zeigt nur, was der Server sieht. Abweichend vom Plan (§9.2) steht die Zwillings-Zeile `report --faellig` EINMAL am Fuß des Blocks statt auf jeder Karte: sie druckt die Liste des Servers, und eine im Browser gebaute Karte steht nicht in deren Ausgabe |
| `BackToTop` | schwebende Rückkehr an den Seitenanfang, erscheint ab zwei Bildschirmen Scrollweg | nur auf den langen Inhaltsseiten (`/schriftkunde` ≈ 20 Handy-Bildschirme, `/impressum`, `/lesen/vergleichen`); 44 × 44, Papierfläche mit Haarlinie (§5), `prefers-reduced-motion` springt statt zu gleiten |

### 7.1 Federprobe — Postkarte und Schriftgrößen-Leiter

Autor-Entscheide vom 2026-09-04, umgesetzt in `sections/scribe/ScribeView.tsx`
und `sections/scribe/size.ts`.

**Postkarte statt Wort:** **480 Zeichen** = acht geschriebene Zeilen zu sechzig
— dieselbe Zeilenlänge, die das Übungsblatt druckt (`MAX_LINE_LEN`,
`lib/uebungstext.ts`), und zugleich die harte Obergrenze des Umbruchplaners
(`MAX_CHARS_PER_LINE`), damit keine Anfrage der 160-Zeichen-Grenze der Route
nahekommt. Der Zähler `n/480` zählt getippte Umbrüche mit, weil sie im Feld auch
Zeichen sind.

**Ein getippter Umbruch ist immer ein Umbruch.** Das Feld ist mehrzeilig,
`planParagraphs` teilt ZUERST an den getippten Umbrüchen und bricht dann jeden
Absatz wie bisher um (eine zu lange getippte Zeile bricht also trotzdem). Eine
Leerzeile ist **ein** Absatzabstand; mehrere fallen darauf zusammen, führende
und abschließende entfallen. **Nie geht ein `\n` an die API** — jede Zeile ist
eine eigene `/write/word`-Anfrage, und `core.shaping.shape_text` liest ein `\n`
als gewöhnliches Leerzeichen, schriebe den Umbruch also als Lücke mitten in die
Zeile. Der Teilen-Link trägt Umbrüche als `%0A`.

**Was keine Zeilenplanung retten kann, wird gemeldet statt geschrieben:** ein
Zug ohne Leerzeichen, länger als eine Kompositionsanfrage trägt (160 Zeichen),
bricht an nichts und wird von der Route abgelehnt. Die Federprobe benennt ihn
(`tooLongRun`), statt ihn zu senden oder zu kürzen — dieselbe Regel, mit der das
Übungsblatt eine zu breite Zeile meldet.

**Schriftgröße statt Zoom**, drei Stufen als Umschaltgruppe, Vorgabe `mittel`
(ein eigener Zoom ist **verworfen**: `app/index.html` lässt das Pinch-Zoom des
Browsers unangetastet, kein `user-scalable=no`). Eine Stufe ist eine
**Ziel-x-Höhe in px je Template-Einheit**, nach der `lib/lineWrap` die Zeilen
plant — eine größere Stufe kauft weniger Zeichen je Zeile und bringt mehr
Zeilen, der akzeptierte Preis größerer Schrift.

| Stufe | px je Einheit | = |
|---|---|---|
| `klein` | **20** | 14 · √2 |
| `mittel` | **28** | 14 · 2 (Vorgabe) |
| `groß` | **40** | 14 · 2√2 |

Anker ist der **Tintenboden von 14 px** (§9) — die Größe, bei der eine Zeile
gerade noch lesbar ist, nicht die, bei der sie bequem ist —, und die Leiter
steigt in √2-Schritten darüber, damit jede Stufe eine sichtbare Änderung ist.
`klein` trifft damit genau, was eine volle Desktop-Zeile vorher schrieb
(gemessen 20,8 px je Einheit auf 1440 px), `mittel` liegt 1,4× darüber.

**Der Boden gewinnt, wo der Rahmen die Stufe nicht trägt.** Ein Wort wird nie
getrennt, also kappt der Planer das Ziel auf die x-Höhe, bei der das breiteste
Wort noch passt — nie unter den Boden. Gemessen (464 Zeichen, 2026-09-04): auf
**1440 px** 19 · 32 · 57 Zeilen bei exakt 20 · 28 · 40 px je Einheit; auf
**360 px** (Rahmen 286 px) fallen alle drei Stufen auf **14,1 px** und 49 Zeilen
zusammen — deutsche Wörter von 9–11 Buchstaben lassen dort nicht mehr zu. Das
ist die ehrliche Antwort, nicht ein Fehler; Scrollfläche und Silbentrennung sind
beide verworfen.

Die Wahl **überlebt den Besuch** (`localStorage`, in `try`/`catch`, die Seite
rendert auch ohne) und **reist im Link** (`?size=klein|mittel|gross`), wobei die
**URL den Speicher schlägt**, damit ein geteilter Link das Bild des Absenders
zeigt; ein Link ohne `?size=` lässt die eigene Wahl in Ruhe. Die Stufe gilt
**nur der Federprobe**: `targetXHeightPx` ist ein Prop, ohne das `height` die
Größe bemisst wie zuvor (Tafel, Quiz, Vergleichen, Schriftkunde unverändert).

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

**Der Boden gilt auch für geschriebene Zeilen** („Tintenboden“, seit
2026-09-04): Die **x-Höhe** einer geschriebenen Zeile — eine Template-Einheit,
Grundlinie = 0, Mittelband = 1 — fällt nicht unter dieselben **14 px**.
Geschriebene Formen bekommen mindestens, was die kleinste gesetzte Schrift
bekommt, und brauchen eher mehr: Was ein Sütterlin-u vom n trennt, sitzt
*innerhalb* des Mittelbands und ist ein Bruchteil davon. Statt kleiner zu
setzen, bricht `WrittenWord` den Text um (§7). Belegt: Der Audit vom
2026-09-02 maß auf 360 px einen 29-Zeichen-Satz bei 7,1 px je Einheit.
Er ist zugleich der Anker der Schriftgrößen-Leiter (§7.1).

**Messbar statt behauptet.** Der Typo-Boden hat ein eincheckbares Gitter:
`node app/scripts/type-floor.mjs` fährt alle öffentlichen Routen in einem echten
Browser an, liest die *berechnete* Schriftgröße jedes Elements mit eigenem Text
und schlägt unter 14 px fehl (der 13-px-`overline` ist als Teil der Leiter aus
§3 ausgenommen). `--admin` fährt stattdessen die Werkbank-Routen an — ein
eigener Lauf, weil ohne `VITE_ADMIN_TOKEN` jede Admin-Route der Boot-Fehler ist
und ein Lauf darüber grün meldet, ohne ein Bedienelement gesehen zu haben (die
Messung steht im Skriptkopf). Nach jeder Typo- oder Theme-Änderung laufen
lassen; das Skript ist der Mobil-Schritt von `/verify-frontend`.

### 9.1 Fokus (bindend)

**Jedes fokussierbare Element trägt einen sichtbaren Ring:** 2 px `viridian`,
`outline-offset` 2 px. Der Ring ist ein **exportiertes Token** — `focusRing` aus
`app/src/styles/focusRing.ts`, neben `hitArea` das zweite geteilte
Bedienbarkeits-Token —, das `theme/components.ts` in seine drei Regeln
(`MuiButtonBase` + `MuiChip` + `MuiLink`) hineinreicht und damit Button,
IconButton, ToggleButton, Chip, jedes eigene `ButtonBase` und jeden Link trägt.
Ein selbstgebautes fokussierbares Element — ein nacktes `<button>` mit
`appearance: none`, wie die Deckungs-Zellen der Eigenhand — nimmt `focusRingSx`
aus derselben Datei; **nie einen handgeschriebenen `outline`**, denn genau so
driftet der eine Ring auseinander. Alles, was ein `Box component={RouterLink}`
oder ein `role="button"` auf einem `Box` ist, hat keine MUI-Basis und setzt den
Ring selbst — aus demselben Token: `PaperCardLink`, `HeaderNavLink`, die Felder
der Scope-Leiste, die Wortmarke, die zwei Landing-CTAs, die Zoom-Fläche der
Lesetafel (Durchgang 2026-09-19: drei mit eigenem `outline-offset: 3`, vier ganz
ohne Ring). Die SVG-Zellen der Schreibtafel bekommen stattdessen eine
eingefärbte Zellenfläche (`WrittenSheet.tsx`). MUI-Textfelder bleiben
ausgenommen: sie zeigen Fokus über ihren eigenen Rahmen (2 px `viridian`).
Hintergrund: MUIs `ButtonBase` setzt selbst `outline: 0` — ohne die Theme-Regel
ist eine fokussierte Schaltfläche von ihren Nachbarn nicht zu unterscheiden (das
Quiz war so per Tastatur unbedienbar, Audit 2026-09-02). Lighthouse sieht diesen
Fehler nicht (`focusable-controls` ist dort *manual*): Der Nachweis ist ein
Tastatur-Durchgang mit echten Tab-Anschlägen, kein Score.

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
`minHeight: 44` **und `minWidth: 44`** (die Breite seit 2026-09-04, als
„klein" mit 42,2 px den Sweep reißen ließ; eine Umschaltgruppe ist der
Nachbarschaftsfall unten — ihre Schaltflächen stoßen aneinander, also wächst
das Element statt seiner unsichtbaren Fläche).

**Wo Nachbarn dicht stehen, wächst das Element statt seiner Trefferfläche.** Die
drei Bereichslinks der Kopfleiste sind der Fall: auf dem Handy bricht die Leiste
in zwei Zeilen, deren Textmitten 28 px auseinanderliegen — zwei unsichtbare
44er-Flächen hätten sich um 16 px überlappt, und ein Tipp auf „Lesen" wäre auf
„Schriftkunde" gelandet. `HeaderNavLink` bekommt darum echtes Innenmaß
(`minHeight`/`minWidth` 44, `px`), womit die Zeilen auseinanderrücken; die
Haarlinie sitzt seither an einem inneren `span`, damit sie weiter am Wort klebt
statt am Polster. Die Leiste wächst dadurch auf schmalen Geräten von 82 auf
121 px, auf `sm+` bleibt sie unverändert. Faustregel: Überlagerung nur dort, wo
das Element allein steht — ein Nachbar NIMMT sie wieder weg. Ein `InfoHint`
(26 px gemalt) verliert neben einem Schalter 4 px daneben 5 px je Seite und
liegt still wieder unter dem Boden; dort wird der Platz reserviert.

**Benannte Ausnahme: die schmalen Zellen der Schreibtafel** (Entscheid des
Autors, 2026-09-03 — Audit-Befund 21). Die geschriebene Tafel (`WrittenSheet`)
setzt das Alphabet als SVG-Zellen, die ihre Zeile lückenlos kacheln; die Breite
einer Zelle ist die Ink-Breite ihres Buchstabens plus eine halbe Lücke je Seite
(`cellW = glyphW + gap`), damit die Reihe wie geschriebene Zeile läuft und nicht
wie ein Setzkasten. Damit sind schmale Zeichen auch schmale Zellen: **14 der 62
bleiben unter 44 px in der Breite** — i, l, ſ, t, z, die Versalien I, J, O, Ö,
P, S, T, Z und die Ziffer 0 (bei 390 px gemessen: 32,3–77,2 px breit, Lücke 0,
57,2–64,2 px hoch; auf breiteren Geräten wächst der Maßstab und die Zahl sinkt,
bei 500 px sind es noch zwei).

**Das bleibt so.** Die Zellen sind kein primäres Ziel: die Tafel ist zum
Nachschlagen da, das Antippen spielt den Duktus nur noch einmal ab, und dasselbe
Zeichen ist über die Buchstaben-Detailseite (`/tafel?g=…`) mit vollem Ziel
erreichbar — das Ziel der Handlung bleibt also erreichbar, nur nicht auf diesem
Weg. Beide Auswege kosten mehr, als sie brächten: eine unsichtbare Trefferfläche
griffe in den Nachbarbuchstaben und nähme ihm den Tipp (oben: „Überlagerung nur
dort, wo das Element allein steht"), eine Verbreiterung baut genau das
Nachschlage-Raster um, dessentwegen die Seite existiert. WCAG 2.2 SC 2.5.8 ist
mit mindestens 32 × 57 px deutlich erfüllt.

**Wann die Ausnahme fällt:** sobald die Tafel neu gelegt wird — ein anderes
Zellenmodell, gleichmäßiger Pitch, ein anderer Umbruch. Dann ist die 44-px-Breite
Teil des neuen Entwurfs und nicht mehr nachträglich zu erkaufen. Unabhängig davon
gilt sie nur für die schmale BREITE bei voller Höhe: eine Zelle, die ihre Höhe
verlöre oder unter die 24-px-Linie fiele, meldet der Sweep als echten Verstoß.
Die Zellen stehen als benannte Ausnahme in `touch-targets.mjs` — bei jedem Lauf
sichtbar gezählt, nie stillschweigend übersprungen.

**Messbar statt behauptet**, wie der Typo-Boden: `npm run touch-targets`
(`app/scripts/touch-targets.mjs`) fährt **alle** öffentlichen Routen an und misst
**jedes** interaktive Element — 255 sind es heute, über alle Bildschirmzustände
(das Quiz zählt dreimal: Einrichtung, Runde, Auswertung, weil jeder Zustand
andere Bedienelemente zeigt). Ausgenommen ist genau die eine Ausnahme der Regel,
und sie braucht ZWEI Merkmale: unterstrichen **und** außerhalb von `<nav>`.
Die Unterstreichung allein genügt nicht — die Sprungliste der Schriftkunde ist
ebenfalls unterstrichen, ist aber Navigation und schuldet den Boden (sie trägt
ihn seit 2026-09-03 über `minHeight`, was ihre Zeilen zugleich auseinanderrückt).
Chrome, das nur wie ein Link aussieht, setzt `textDecoration: none` und wird
ohnehin mitgemessen.

Zwei Feinheiten, die das Messen erst ehrlich machen: Ein in ein `<label>`
gewickeltes Bedienelement wird **am Label** gemessen — dort tippt man hin, und
MUIs Switch legt nur einen durchsichtigen `<input>` darüber (deshalb prüft der
Sweep auch keine Deckkraft: unsichtbar heißt nicht unbedienbar, das entscheidet
der Treffertest). Und die benannte Ausnahme der Tafel-Zellen hängt am Merkmal
`rect.cellbg` der Zelle, nicht an „ist eine SVG-Gruppe" — sonst erbte das nächste
zu kleine SVG-Element die Ausnahme, statt aufzufallen.

Eine gepflegte Liste stand hier zuerst und war die falsche Form: sie bestand,
während die Lesart-Chips und die Tafel-Schrittknöpfe den Boden rissen.

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

**Ein Eingabefeld wird am FELD gemessen**, nicht an seinem `<input>`: MUI rendert
ein Select als Combobox-`<div>` plus ein unsichtbares 21-px-`<input>`, das es nur
fürs Absenden gibt. Derselbe Gedanke wie beim `<label>` eine Zeile höher; ein
Feldrahmen unter dem Boden fällt weiterhin durch.

### 9.4 Nicht-Hover (bindend — Vorgabe V25 des Admin-Redesigns)

**Kein entscheidungstragender Zustand lebt nur im Hover.** Ein `Tooltip` ist ein
NAME für ein Bedienelement, dessen sichtbare Beschriftung dasselbe sagt — nie der
einzige Ort eines Zustands, eines Grundes, einer Zahl oder einer Anweisung. Wer
mit Tastatur oder auf dem Tablet arbeitet, hat keinen Hover. Umgekehrt gilt für
den `aria-label`: er ERSETZT, was ein Element zeigt, also nennt er dessen
aktuellen Wert mit („Buchstabe a — anderen wählen").

Die Prüffrage ist mechanisch, nicht ästhetisch — **ist das Kind des Tooltips
fokussierbar?**

| Kind des `Tooltip` | Erreichbar | Erlaubt |
|---|---|---|
| `Button`, `IconButton`, `ToggleButton`, klickbarer `Chip`, Link | Tastatur ✓, Touch ✓ | ja, solange der Inhalt das Element BENENNT |
| nicht klickbarer `Chip`, `Typography`, `Box` | nichts | **nein** — MUI setzt dort kein `tabIndex` |
| `<span>` um ein DEAKTIVIERTES Bedienelement | nichts (deaktiviert nimmt keinen Fokus) | **nein**, wenn es den GRUND trägt |
| natives `title=` | nur Hover | **nein** für Fehlertexte, Rohzahlen, Notizen |

Zwei Auswege, in dieser Reihenfolge:

1. **Sichtbarer Text**, wo er kurz ist — der Grund in die Chip-Beschriftung, eine
   Bildunterschrift unter die Zeile, eine Zeile in die Werkzeugleiste (so steht
   jetzt im Chart-Kopf, WARUM „Einrichten" grau ist).
2. **`InfoHint`**, wo die Erklärung lang ist oder einem Block gilt: ein echter
   Knopf mit Fokusring (§9.1) und 44-px-Fläche (§9.3), der auf Klick öffnet.

**Höchstens EIN `InfoHint` je Zeile und Gegenstand.** Verboten ist der EINE
Gegenstand in N Marken — die Kopfzeile einer Fassung erklärt Herkunft, Saat,
Alterung, Maske und Befund aus einer, die Legende alle sieben Landmarken-Arten
aus einer; zeigt eine Zeile wirklich zwei Gegenstände, trägt sie zwei. Der Fall,
für den die Regel geschrieben ist: die Abzugs-Kategorien der
Buchstaben-Arbeitsliste waren sechs `<Typography tabIndex={0}>` je Zeile —
Tab-Stopps ohne Ring, bis zu 72 je Listenseite, keiner mit dem Finger
erreichbar. Heute: kein einziger tabbarer `span` auf `/admin/buchstaben`.

**Kein selbstgebauter `tabIndex` auf einem nicht-interaktiven Element.** Ein
`tabIndex={0}`, das nur einen Tooltip per Tastatur erreichbar machen soll, ist das
Symptom, nicht die Lösung: ein Stopp, der nichts tut und nichts zeigt. Ein Öffner
ist ein `ButtonBase` (V24), kein `<p role="link">` und kein `<img onClick>`.
Beides — natives `title=` auf einer MUI-Primitive und ein rollenloses
`tabIndex={0}` — hält `sections/admin/nonHover.guard.test.ts` fest.

**Farbe zählt hier mit — und der `aria-label` ist erst die halbe Miete.** Wo ein
Zustand als Farbe gezeichnet wird, trägt das Bedienelement ihn als `aria-label`;
das ist die Hälfte im Barrierefreiheits-Baum, die andere schuldet §2, denn ein
sehender Farbfehlsichtiger liest keinen `aria-label`. Der Punkt im
Buchstabenraster (`shell/LetterPicker.tsx`) war der offene Fall und ist seit
2026-09-19 der Musterfall: **gefüllte Scheibe = Canonical, hohler Ring = nur
Bbox**, gleiche Größe, Farben weiter aus den Token. Form trägt den Zustand, die
Farbe bestätigt ihn nur — bei 8 px ist das der einzige zweite Kanal, der das
Raster nicht umbaut.

**Offene Ausnahme vom Typo-Boden: der Zähler der Deckungs-Zellen** (9,6 px,
`eigenhand/BestandView.tsx`). Ihn zu heben legt ~90 Zellen neu, die der Autor
täglich liest. Erreichbar ist die Zahl trotzdem: der Zähler ist `aria-hidden`,
der volle Satz ist der NAME jeder Zelle. `type-floor.mjs` kennt die Ausnahme
NICHT und meldet sie — absichtlich, denn sie wäre die Entscheidung, die noch
aussteht.

### 9.5 Tastatur (bindend — Vorgabe V24 des Admin-Redesigns)

**Eine lange Liste ist EIN Tab-Stopp** — sonst kostet eine Übersicht mit 63
Zeilen à drei Bedienelementen ~190 Anschläge bis zur Werkzeugleiste darunter.
Sie ist eine **Roving-Liste** (`hooks/useRovingList.ts`): Tab hinein auf die
zuletzt besuchte Zeile (sonst die erste), ↑/↓ zwischen Zeilen, ←/→ zwischen den
Bedienelementen EINER Zeile, `Home`/`End` an die Enden, Tab hinaus. Kein Umlauf.
In einer **umbrechenden** Kachelfläche nur ←/→ und `Home`/`End`: ein Flex-Grid
hat keine feste Spaltenzahl, und ein ↓ über sechs Kacheln bei 1440 px und drei
bei 1024 px wäre schlechter als keins. Enter und Leertaste bleiben unangetastet
(es sind echte Schaltflächen), der Körper einer aufgeklappten Zeile bleibt außen
vor (`data-roving-skip`) und behält seine eigene Tab-Folge. Der Fokus hängt am
Zeilen-SCHLÜSSEL: fällt die Zeile durch Filter oder Seitenwechsel weg, übernimmt
die an ihrer Stelle — nie `<body>`.

**Ein Gegenstand, ein Stepper.** Jedes Detail trägt ‹ › um seinen Gegenstand
(`shell/SubjectStepper.tsx`), mit Namen statt bloßem Pfeil, und dieselbe
Bewegung auf **Alt + Umschalt + ← / →**. Nicht `Alt+←/→`: das IST
Zurück/Vorwärts auf Windows und Linux, und die Verlinkungs-Doktrin des Admins
lebt vom Zurück-Knopf (P1-Q11 b). Der Stepper folgt der **Reihenfolge der
Übersicht, aus der der Leser kam**, Filter und Sortierung eingeschlossen
(P1-Q12 a); weil dieselben Pfeile damit nach einem Filterklick etwas anderes
bedeuten, nennt der Kopf die Reihenfolge sichtbar („Reihenfolge: Schlechteste
zuerst · gefiltert") — ohne veröffentlichte Reihenfolge die Registerfolge, auch
das gesagt. Ein Schritt lässt Listen-Zustand und `h=` stehen.

**Kurztasten feuern nur, wo sie dürfen, und sind abschaltbar.** Nie in `input`,
`textarea`, `select`, `contenteditable` oder einem offenen Dialog — Wizard und
Bahn-Editor besitzen ihre Tasten selbst —, und `preventDefault()` nur, wenn
wirklich geblättert wird. Der Schalter **„Kurztasten"** sitzt am Ende der
Scope-Leiste (P1-Q11 b), Zustand als sichtbares Wort daneben, Kombination als
Beschriftung; die Einstellung lebt in `localStorage` — der einzige Fall, denn
sie gehört dem LESER und darf in keinem Link reisen —, jeder Zugriff in
`try/catch`, Voreinstellung AN. Aus ist NICHTS gebunden, die ‹ ›-Knöpfe arbeiten
weiter. **Roving fällt nicht unter den Schalter**: Struktur, keine Kurztaste.
**Einzelbuchstaben-Kurztasten (`n`/`p`, `j`/`k`) gibt es nicht.**

Nachweis ist ein Durchgang mit **echten** Tastenanschlägen, kein Skript: ein
`element.focus()` löst `:focus-visible` nicht aus (§9.1).

---

## 10. Pflege & Sync

- Ändert sich eine Zahl/Token hier → `app/src/styles/paper.ts`, `theme/typography.ts`,
  `components/PageContainer`, `components/Prose`, `components/PageHeader` (Seitenkopf),
  `components/HeaderBar` (die eine Kopfleiste, §7) bzw.
  `components/PublicFooter` (Footer-`mt` = der eine Abstand, §4) nachziehen (und umgekehrt).
- **Farben stehen in drei Dateien, nicht in einer** — wer ein Token bewegt, sieht
  alle drei an: `styles/paper.ts` (die Quelle), `sections/admin/shell/model.ts`
  (`WERKBANK_COLORS` — welche Ebene welche Aufgabe hat),
  `sections/admin/overlayColors.ts` (Chart-/Wizard-Signalfarben, bewusst außerhalb
  der Papier-Identität). Dazu `tools/tracebench/view.py`, das Hexe spiegeln MUSS,
  weil ein matplotlib-Werkzeug kein SPA-Token importieren kann: die Engine-Farbe
  ist dort dieselbe, die Referenzfarbe absichtlich nicht (Blau gehört in diesen
  Abbildungen dem Folger). Gegenprobe bei jeder Ebenen-/Rollenfarbe:
  `app/src/styles/paper.test.ts` — der Augenschein mit Farbfehlsicht-Simulation
  gehört in `/verify-frontend`.
- Die Bedienbarkeits-Regeln aus §9 wohnen an genau einer Stelle:
  `styles/focusRing.ts` (der eine Ring, §9.1), `styles/hitArea.ts`
  (Trefferfläche, §9.3) und `theme/components.ts`, das beide für seine
  MUI-Regeln einsetzt (Link-Auszeichnung, Typo-Boden der MUI-`small`-Größen,
  `minHeight` der Umschaltgruppen unter `sm`). Eine neue Ausnahme gehört dorthin,
  nicht an die Aufrufstelle. Gegenprobe: `npm run type-floor` (§9) und
  `npm run touch-targets` (§9.3) — beide gegen die laufende Seite, beide mit
  `--admin` zusätzlich gegen die elf Werkbank-Routen — plus ein
  Tastatur-Durchgang für den Fokusring (§9.1), die Nicht-Hover-Regel (§9.4) und
  die Roving-Listen (§9.5), den kein Skript ersetzt.
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
