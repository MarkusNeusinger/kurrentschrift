# kurrentschrift.ink — paper & ink

A small brand design system: the "paper & ink" identity of kurrentschrift.ink
(a tool for reading old German handwriting). Six React components, shipped from
the real app, on `window.KurrentschriftDS`. Build designs that look like aged
paper written in iron-gall ink — warm, legible, one quiet green accent.

## Setup — wrap every design

Components read the MUI theme and (header/footer) a router from context. Wrap
the whole design in **`AppProviders`** (ThemeProvider + CssBaseline + an
in-memory router). Without it, the header/footer render blank and colors fall
back to MUI defaults.

```jsx
<AppProviders>
  <PaperBackground minHeight="100dvh">
    <PublicHeader tone="paper" />
    {/* your page content */}
    <PublicFooter />
  </PaperBackground>
</AppProviders>
```

## Components

- **PaperBackground** — the page ground (warm gradient + grain + vignette). Put
  almost everything inside it. `minHeight`, `sx` props.
- **PublicHeader** — sticky identity bar (brand wordmark + Schreiben/Lesen nav). `tone="paper"|"plain"`.
- **PublicFooter** — minimal legal footer (hairline + Impressum link). Render inside PaperBackground.
- **BootStatus** — full-page loading/error screen. `variant="loading"|"error"`, `shell="plain"|"paper"`.
- **InfoHint** — the one info affordance: a Kurrent "i" that reveals detail in a popover on click. `title`, `children`.
- **WrittenGlyph** — a canonical glyph rendered "as written" (data-driven; backend payload).

## Palette (exact hexes — use these for your own layout glue)

| Token | Hex | Use |
|---|---|---|
| paper bg | `#e7dabf` | page ground (never pure white) |
| paper hi / lo | `#f1e8d4` / `#d8c7a3` | gradient ends, raised/recessed |
| ink | `#241a10` | primary text / "writing" (never pure black) |
| inkSoft | `#473420` | secondary text |
| sepia | `#5e4726` | small labels, "bald" markers (AA on paper) |
| **viridian** | `#40826d` | **the single accent** — links, the brand dot, hover. NEVER body text. |
| line | `#b6a079` | hairlines, borders |

Semantic pigments for status/marks (sparingly): vermilion `#e34234`, prussianBlue `#003153`, ochre `#cc7722`, oldGold `#c9a227`.

## Typography (these `@font-face` families ship in styles.css)

- Body: **`'EB Garamond', Georgia, serif`**.
- Display / headlines / brand wordmark: **`'Playfair Display', 'EB Garamond', serif`**.
- **`'GLKurrent', cursive`** — showpiece ONLY (the brand "i", decorative initials). Never set readable text in it.

**Binding legibility rule:** UI, headlines and body are always set in the
legible Antiqua faces above. Historic broken/cursive script appears ONLY as a
marked specimen (a WrittenGlyph, a single ornamental initial) — never as text
the reader must actually read. Honor `prefers-reduced-motion`.

## Patterns & don'ts

- Live feature → a real link/CTA ("Übungsblatt erstellen →"). Planned feature → a
  sepia italic "bald" marker, **never a dead "coming soon" button**.
- Eyebrow / brand mark = viridian dot + lowercase domain `kurrentschrift.ink`.
- Paper texture carries everywhere; only true work surfaces (an A4 sheet, an
  image crop, the chart scan) and the PDF stay neutral/white.
- Prose tone: warm ~1900 letter-German for running copy; functional labels and
  facts stay plain and modern. No officialese, no archaic spelling ("daß").
- ❌ no pure white ground, ❌ no pure black ink, ❌ viridian as body text.

## Where the truth lives

Read each component's `<Name>.prompt.md` for its API + examples, and
`styles.css` (+ `fonts/`) for the shipped tokens/faces. The full brand
rationale is in `guidelines/style-guide.md`.
