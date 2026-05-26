# Frontend-Stack

Technische Spezifikation des Endnutzer-Frontends aus Vision §1, §2 (Lineatur-
Konfigurator), §3 (Animation), §4 (Lesen üben), §5 (Stil-Analyse-Upload),
§6 (Lese-Hilfe), §7 (Hände-Vergleich), §8 (Lese-Lupe), §9 (Open-Data) und
§10 (DE/EN). Ergänzt [`architektur.md`](../concepts/architektur.md) §16.

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

**Package Manager:** Yarn (wie anyplot).

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

| Pfad | Inhalt | Vision-Bezug |
|---|---|---|
| `/` | Landing-Page mit Pitch und Quick-Links | §1 |
| `/lernen` | Einstieg (Geschichte, Alphabet-Tafel, Lese-Regeln) | §1 |
| `/animation` | Animierte Buchstaben-Tafel | §3 |
| `/schreiben` | Lineatur-Konfigurator + Übungsblatt-Generator | §2 |
| `/lesen-uben` | Beliebiger Text → Kurrent-Rendering | §4 |
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

- `cd app && yarn build` → statisches `dist/` mit JS-Chunks + Assets.
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

- `App.tsx` — Top-Level mit MUI-Theme, Router-Setup.
- `pages/ChartPage.tsx` — Bbox-Editor (wird zu `/admin/chart`).
- `pages/EditorPage.tsx` — Stylus-Trace + Diagnostic (wird zu
  `/admin/edit/:glyphKey`).
- `components/DiagnosticView.tsx` — 3-Spalten-Diagnostic-Rendering.
- `components/GlyphSidebar.tsx` — Liste der `KNOWN_GLYPHS`.

### Neu (kommt mit Phasen P1–P5)

- `pages/HomePage.tsx` — Landing.
- `pages/LearnPage.tsx` — Einstieg.
- `pages/AnimationPage.tsx` — Animierte Tafel (P1+).
- `pages/WorksheetPage.tsx` — Lineatur-Konfigurator (P2).
- `pages/RenderPage.tsx` — Text → Kurrent (P2).
- `pages/HtrUploadPage.tsx` — Upload + Job-Polling (P1).
- `pages/ReadingMagnifierPage.tsx` — Lese-Lupe (P1+).
- `pages/StyleAnalysisPage.tsx` — Stil-Analyse-Upload (P3).
- `pages/HandComparePage.tsx` — Heatmaps Side-by-Side (P4).
- `pages/OpenDataPage.tsx` — Daten-Export-Seite (P5).
- `components/GlyphAnimation.tsx` — abgespeckte MVP-Animation.
- `components/KurrentRenderer.tsx` — Text → SVG-Render.
- `components/LinearConfigurator.tsx` — Lineatur-Ratio-Wahl.
- `components/HeatmapView.tsx` — D3.js-Heatmap-Komponente.
- `components/IiifViewer.tsx` — Annotorious + OpenSeadragon wrapper.

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
