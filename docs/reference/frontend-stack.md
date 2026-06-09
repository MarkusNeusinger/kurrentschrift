# Frontend-Stack

Technische Spezifikation des Endnutzer-Frontends aus Vision §1 (Einstieg),
§2 (Lineatur-Konfigurator), §3 (Animation), §4 (Lesen üben), §5 (Lese-Hilfe
inkl. Lupe), §6 (Stil-Analyse-Upload + Hände-Vergleich), §7 (Open-Data) und
dem Zweisprachig-Leitprinzip (DE/EN). Ergänzt
[`architektur.md`](../concepts/architektur.md) §16.

**Kernprinzip:** anyplot-Stil — das gleiche Setup wie
`~/projects/anyplot/app/`, das anyplot.ai auf Cloud Run trägt. Eine SPA,
gemeinsam für Endnutzer und Admin, mit Auth-Gate für sensible Routen.

---

## 1. Stack

| Komponente | Version | Zweck |
|---|---|---|
| **React** | 19.x | UI-Framework. Server Components nicht genutzt — wir bleiben Client-Only. |
| **Vite** (mit `@vitejs/plugin-react-swc`) | 8.x | Build-Tool, schneller HMR. |
| **MUI** + **Emotion** | 9.x | Komponenten-Bibliothek. |
| **React Router** | 7.x | Client-Side-Routing. |
| **`react-helmet-async`** | 3.x | SEO-Meta-Tags pro Route (Title, Description, Open Graph). |
| **`react-i18next`** | aktuell | Internationalisierung DE/EN. |
| **TypeScript** | 6.x | Typsicherheit. |
| **`vite-plugin-compression2`** | 2.x | Gzip + Brotli-Pre-Compression. |

**Package Manager:** npm (wie heute im Repo — `app/package-lock.json` ist
checked in; anyplot nutzt yarn, wir bewusst nicht).

**Begründung gegen andere Stacks (Verworfen-Sektion):**

- *Astro mit Islands-Architektur* — wäre für die SEO-Inhaltsseite ein
  besserer Fit, aber das jetzige `/app/` ist schon Vite+React+MUI. Ein
  zweiter Stack wäre Pflegeaufwand. SEO ist mit `react-helmet-async` +
  Googles JS-Rendering tragbar.
- *Next.js* — Vercel-zentriert, Cloud Run möglich aber Reibung. Größerer
  Footprint. Für uns keine RSC-Bedarfsfall.
- *Reine SSG* — Inhalt ist teilweise dynamisch (User-Renders, Stil-Analyse,
  HTR-Job-Status). SSG-only ohne Client-State wäre Brokerei.

---

## 2. Routenstruktur

### Öffentliche Routen (kein Auth)

Die Pfade unten sind **ohne** Sprachpräfix notiert. Im Routing liegen sie
unter `/de/…` (Default) bzw. `/en/…` (siehe i18n unten) — `/lernen` wird
also als `/de/lernen` und `/en/learn` ausgeliefert. Die englischen
Slug-Varianten werden mit dem `locales/en/`-Bundle definiert (P1-Arbeit).

| Pfad | Inhalt | Vision-Bezug |
|---|---|---|
| `/` | Landing-Page mit Pitch und Quick-Links | §1 |
| `/lernen` | Einstieg (Geschichte, Alphabet-Tafel, Lese-Regeln) | §1 |
| `/quiz` | Buchstaben-Quiz (Crop aus der Vorlage → Latein-Buchstabe raten) | §4 |
| `/animation` | Animierte Buchstaben-Tafel | §3 |
| `/schreiben` | Lineatur-Konfigurator + Übungsblatt-Generator | §2 |
| `/lesen-ueben` | Beliebiger Text → Kurrent-Rendering | §4 |
| `/lese-hilfe` | Upload historischer Brief → HTR-Job | §6 |
| `/lese-lupe/:job` | Lese-Lupe für transkribierten Brief | §8 |
| `/stil-analyse` | Upload Schrift-Probe → Statistik-Report | §5 |
| `/vergleich` | Hände vergleichen mit Heatmaps | §7 |
| `/open-data` | Daten-Export-Seite mit DOI-Verweis | §9 |
| `/glossar` | Erklärungen (Rund-s, Ligaturen, Schwellzug…) | §1, §8 |

### Admin-Routen (hinter Auth)

| Pfad | Inhalt | Status |
|---|---|---|
| `/admin/chart` | Bbox-Editor auf Source-Chart (heute `/`) | existiert |
| `/admin/edit/:glyphKey` | Stylus-Trace + 3-Spalten-Diagnostic (heute `/edit/...`) | existiert |
| `/admin/sources` | Source-Verwaltung | post-MVP |
| `/admin/jobs` | HTR-Job-Monitor (Quote-Übersicht) | post-MVP |

**Migration der existierenden Routen:** Beim Implementieren werden die
heutigen `/` und `/edit/:glyphKey` unter `/admin/` verschoben, neue
Endnutzer-Routen kommen nach `/`.

---

## 3. i18n

### Strategie

- **`react-i18next`** als Library.
- **URL-Präfix:** `/de/...` (Deutscher Default) und `/en/...` (Englisch).
  Verwerfen: Cookie-basiert (schlechte UX bei Link-Sharing), Domain-Switch
  (Hosting-Komplexität).
- **Lazy-Loaded Locale-Bundles** pro Sprache — JSON-Dateien unter
  `app/src/locales/{de,en}/...`.

### Konfiguration

```typescript
// app/src/i18n.ts (Skizze)
i18n
  .use(LanguageDetector)
  .use(HttpBackend)  // JSON-Files lazy laden
  .use(initReactI18next)
  .init({
    fallbackLng: 'de',
    supportedLngs: ['de', 'en'],
    detection: { order: ['path', 'htmlTag', 'navigator'] },
    interpolation: { escapeValue: false },
  });
```

### Inhalts-Pflege

- **MVP (DE only):** alle Strings nur in `locales/de/`. Englische Strings
  bewusst leer, Routing leitet alles auf `/de/`.
- **P1+ (EN folgt):** `locales/en/` füllen. Reihenfolge: Lese-Hilfe-UI
  zuerst (Genealogie-Zielgruppe), dann Inhalts-Seiten (Einstieg, Glossar).
- **Hilfetexte und Pitch-Texte** bleiben in den Page-Komponenten als
  Trans-Keys; technische Strings (Button-Labels, Validierungen) kommen in
  ein gemeinsames `common.json`.

---

## 4. SEO-Strategie

### react-helmet-async pro Route

Jede Page-Komponente setzt eigene Meta-Tags:

```tsx
<Helmet>
  <title>Lese-Hilfe — kurrentschrift.ink</title>
  <meta name="description" content="Historische Briefe transkribieren …" />
  <meta property="og:image" content="/og/lesehilfe.png" />
  <link rel="alternate" hreflang="de" href="https://kurrentschrift.ink/de/lese-hilfe" />
  <link rel="alternate" hreflang="en" href="https://kurrentschrift.ink/en/reading-help" />
</Helmet>
```

### Crawler-Verhalten 2026

- **Google:** rendert JavaScript, indexiert SPAs mit aktualisierten
  Meta-Tags zuverlässig. Reichweite für unsere Hauptzielgruppen (Genealogie
  + Lernende) gegeben.
- **Bing, DuckDuckGo, andere:** lesen Meta-Tags ohne JS-Rendering — daher
  ist `react-helmet-async` Pflicht, nicht Kür.
- **Social-Sharing (Open Graph):** wird über `react-helmet-async`
  gleich miterledigt.

### Sitemap

- `public/sitemap.xml` statisch generieren beim Build (Vite-Plugin
  `vite-plugin-sitemap` oder eigenes Script).
- Aufnehmen: alle öffentlichen Routen × beide Sprachen.

### Fallback-Pfad bei Bedarf

Sollte sich später herausstellen, dass SEO-Indexierung doch zu schwach
ist (z.B. niedrige Rankings bei langem Inhalt), Migration möglich auf:

- **vite-ssg** (statische Pre-Renderung der Inhalts-Routen) — kleine
  Migration, gleicher React-Code.
- **Astro mit React-Islands** — größere Migration, eigentliche
  SEO-First-Lösung.

Beide bleiben als Optionen dokumentiert, sind aber kein MVP-Pfad.

---

## 5. Auth für Admin-Routen

### Default: Cloudflare Access vor Cloud Run

Wie anyplot (`anyplot/api/routers/debug.py:require_admin`):

1. Cloudflare Access verifiziert Google-Identity am Edge.
2. Cloudflare leitet Request mit `Cf-Access-Jwt-Assertion`-Header an
   Cloud Run weiter.
3. FastAPI verifiziert das JWT (Issuer, Audience, Email-Allowlist).
4. Bei Erfolg: Endpoint freigegeben.

**Vorteile:**

- Auth-Komplexität an die Edge ausgelagert.
- Keine Cookies, kein Session-Management im Backend.
- Google-Login Out-of-the-Box.

### Alternative: GCP Identity-Aware Proxy (IAP)

Wenn wir Cloudflare gar nicht im Stack haben wollen, ist GCP IAP die
äquivalente Lösung — IAP-Header werden statt CF-Access-Header gelesen.
Funktionsweise identisch.

### Frontend-Seite

- Admin-Routen sind im Router-Tree als geschützt markiert.
- Auf 401/403 zeigt die App eine „Sign-in"-Seite mit Redirect zum
  Auth-Provider.
- Existierende `DebugPage.tsx`-Logik in anyplot als Vorlage.

---

## 6. Build & Deploy

### Build

- `cd app && npm install && npm run build` → statisches `dist/` mit
  JS-Chunks + Assets.
- Manual-Chunks (wie anyplot):
  - `mui-icons` separat (large, oft gecached).
  - `mui` (MUI + Emotion).
  - `vendor` (React + Router).
- Compression: Gzip + Brotli pre-compressed via `vite-plugin-compression2`.

### Deploy auf Cloud Run

- **Ein Container** für FastAPI + statisches Vite-Build:
  ```dockerfile
  FROM python:3.13-slim AS api
  # … FastAPI install
  COPY app/dist /app/static
  CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
  ```
  FastAPI mountet `/app/static` als statisches Verzeichnis (`StaticFiles`).
- **CI/CD:** Cloud Build (`cloudbuild.yaml` als Platzhalter im Repo, muss
  aktiviert werden — wie bei anyplot).
- **Region:** europe-west — niedrige Latenz für deutschsprachige
  Hauptzielgruppe.
- **Min instances:** 0 (Cold-Start akzeptabel für eine Lern-Webseite).
- **Memory:** 1 Gi (für FastAPI + WeasyPrint + ggf. TrOCR später 2–4 Gi).

### Reverse-Proxy / Routing

- `/api/*` → FastAPI-Routes.
- `/admin/*` → React-SPA (mit Auth-Check serverseitig).
- alles andere → React-SPA mit Fallback `index.html`.

---

## 7. Komponenten-Map

### Existierend (im jetzigen `/app/`)

Struktur seit dem Restructure (2026-06): `routes/` (Pfad-Konstanten +
lazy Public/Admin-Sections) · `pages/` (dünne Route-Mounts) · `sections/`
(Feature-Views mit Logik) · `components/` (wiederverwendbar) ·
`layouts/admin/` · `theme/` (Farbwahrheit in `styles/paper.ts`) ·
`lib/api/` (Fetch-Client mit Cold-Start-Retry + typisiertem `ApiError`,
Wire-Typen handsynchron zu `api/schemas.py`) · `domain/glyphs.ts`
(Alphabet-Registry + Lock/Split-Helfer) · `context/AdminContext.tsx` ·
`locales/de/` (alle deutschen UI-Strings als Pre-i18n-Namespaces) ·
`hooks/`.

- `routes/index.tsx` — Router-Assembly (Suspense-Fallback, errorElement);
  `routes/paths.ts` ist die einzige Quelle der URLs.
- `sections/landing/` — `LandingView` + `HeroSpecimen` (GLKurrent-Schreib-
  Animation) + `Reveal` (Scroll-Reveal).
- `sections/worksheet/` — `WorksheetView` + `ConfigPanel` + `PreviewSvg`
  (Lineatur-Konfigurator, `/schreiben`).
- `sections/quiz/` — `QuizView` + `useQuizEngine` (gesamte Quiz-Logik ohne
  JSX) + Setup/Play/Results-Panels + `QuestionVisual`.
- `sections/admin/chart/` — `ChartView` (Pointer-Routing) + `useChartViewport`
  (Zoom/Pan/Pinch) + `useBboxEditing` (Bbox-Commits, Lock-Fan-out) +
  `BboxOverlay`/`ChartToolbar` + pure `bboxGeometry`.
- `sections/admin/setup-wizard/` — `SetupWizard` (Dialog-Shell) + `useWizard`
  (State + Server-Mutationen) + `useCropView` (Crop-Viewport) + `WizardCanvas`
  + `steps/{Mask,Lineatur,Slant,Trace,Overview}Step`. Einzige Autoren-Fläche.
- `sections/admin/diagnostics/` — `DiagnosticDialog` (3-Spalten + M4-Fit),
  `DiagnosticView`/`FitView`.
- `sections/admin/sidebar/GlyphSidebar.tsx` — Buchstaben-Grid aus
  `domain/glyphs.ts`.
- `components/` — `PaperBackground` (Papier-Atmosphäre), `PublicHeader`,
  `WrittenGlyph` (Ductus-Animation), `BootStatus` (Boot/Fehler-Screens).

### Neu (kommt mit Phasen P1–P5)

Bereits gebaut (siehe oben): Landing (`sections/landing/`),
Lineatur-Konfigurator (`sections/worksheet/`, `/schreiben`),
Buchstaben-Quiz (`sections/quiz/`). Neue Features kommen als je eine
`sections/<feature>/`-View + dünner `pages/`-Mount + Eintrag in
`routes/paths.ts`:

- `sections/learn/` — Einstieg (P1+).
- `sections/animation/` — Animierte Tafel (P1+).
- `sections/render/` — Text → Kurrent (P2).
- `sections/htr/` — Upload + Job-Polling (P1) und Lese-Lupe (P1+).
- `sections/style-analysis/` — Stil-Analyse-Upload (P3).
- `sections/hand-compare/` — Heatmaps Side-by-Side (P4).
- `sections/open-data/` — Daten-Export-Seite (P5).
- `components/GlyphAnimation` — abgespeckte MVP-Animation (heute schon
  als `WrittenGlyph` im Quiz).
- `components/KurrentRenderer` — Text → SVG-Render.
- `components/HeatmapView` — D3.js-Heatmap-Komponente.
- `components/IiifViewer` — Annotorious + OpenSeadragon wrapper.

---

## 8. Was wir nicht machen

- **Kein eigenes Design-System.** MUI 9 deckt unsere UI-Bedürfnisse. Custom
  Komponenten nur dort, wo es unvermeidbar ist (Animation, Lineatur,
  Heatmap).
- **Kein State-Management-Framework** (Redux/Zustand/Recoil). React-Context
  + lokaler Component-State reichen für unsere Use-Cases.
- **Keine GraphQL-Schicht.** REST über FastAPI ist genug.
- **Kein Service Worker / PWA-Modus** im MVP. Kann später als progressive
  Erweiterung kommen.

---

## 9. Quellen

- [React 19 Release Notes](https://react.dev/blog/2024/12/05/react-19)
- [Vite Docs](https://vite.dev/)
- [MUI v9](https://mui.com/)
- [React Router 7](https://reactrouter.com/)
- [react-helmet-async](https://github.com/staylor/react-helmet-async)
- [react-i18next](https://react.i18next.com/)
- [Astro vs Next.js 2026 — alexbobes.com](https://alexbobes.com/programming/astro-vs-nextjs/) (Vergleich, nicht verwendet)
- [Cloudflare Access](https://www.cloudflare.com/products/zero-trust/access/)
- [GCP Identity-Aware Proxy](https://cloud.google.com/iap)
- [Cloud Run](https://cloud.google.com/run)
- [anyplot.ai-Repo](https://github.com/MarkusNeusinger/anyplot) (interner
  Maintainer; bewusst gleicher Stack)
