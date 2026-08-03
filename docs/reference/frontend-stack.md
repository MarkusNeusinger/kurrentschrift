# Frontend-Stack

> **Status (2026-08-03): lebend.** Ist-Stand von Stack, Routen, i18n-Soll,
> Deploy und Admin-Gate; jede Änderung an `app/package.json`,
> `app/src/routes/paths.ts`, den Cloudbuild-/nginx-Dateien oder `api/auth.py`
> zieht hier nach.
> Am 2026-08-03 gegen den Code geprüft und deckungsgleich (Admin-Routen nach
> dem Redesign „aus einem Guss": `/admin` Vorlagen-Auswahl + die drei
> Ansichten Buchstaben · Übergänge · Wörter; Admin-Token-Regeln, PR #263).

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
| **`react-helmet-async`** | geplant (P1) | SEO-Meta-Tags pro Route (Title, Description, Open Graph). Noch nicht installiert. |
| **`react-i18next`** | geplant (P1) | Internationalisierung DE/EN. Noch nicht installiert (siehe i18n unten). |
| **TypeScript** | 6.x | Typsicherheit. |
| **`vite-plugin-compression2`** | geplant (P1) | Gzip + Brotli-Pre-Compression. Noch nicht installiert. |

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

### Öffentliche Routen (kein Auth) — Ist-Stand

So liegen die Routen heute im Code (`app/src/routes/paths.ts` +
`routes/sections/public.tsx`; die IA mit den drei Bereichen und den zwei
Hub-Seiten ist in [`design-system.md`](../concepts/design-system.md) §6
festgelegt). Die Pfade sind **ohne** Sprachpräfix notiert; im Ziel-Design
(P1, siehe i18n unten) wandern sie unter `/de/…` (Default) bzw. `/en/…` —
die englischen Slug-Varianten werden mit dem `locales/en/`-Bundle
definiert (P1-Arbeit).

| Pfad | Inhalt | Bereich |
|---|---|---|
| `/` | Landing (der Hero schreibt das Markenwort font-first: GLKurrent + Clip-Path-Reveal, Engine-Naht offen — §7) | Einstieg |
| `/schriftkunde` | Überblick der deutschen Schreibschriften (der umbenannte frühere `/lehrbuch`) | Schriftkunde |
| `/lesen` | Hub → Quiz, Tafel | Lesen |
| `/quiz` | Lese-Quiz (Buchstaben + ganze Wörter) | Lesen |
| `/tafel` | Schreibtafel (Vorlage) | Lesen |
| `/schreiben` | Hub → Übungsblatt, Federprobe | Schreiben |
| `/schreiben/uebungsblatt` | Übungsblatt-Generator (Lineatur-Konfigurator, PDF) | Schreiben |
| `/federprobe` | Live-Schreiber (Sütterlin-Synthese mit generierten Übergängen) | Schreiben |
| `/impressum` | Impressum, Datenschutz, Quellen | Footer |
| `/lehrbuch` | Redirect → `/schriftkunde` (alter Name) | — |

### Geplante öffentliche Routen (P1+)

Noch nicht gebaut — Ziel-Routen aus der Vision, kommen mit den
Post-MVP-Phasen (architektur.md §10):

| Pfad | Inhalt | Vision-Bezug | Status |
|---|---|---|---|
| `/lernen` | Einstieg (Geschichte, Alphabet-Tafel, Lese-Regeln) | §1 | geplant (P1+) |
| `/animation` | Animierte Buchstaben-Tafel | §3 | geplant |
| `/lesen-ueben` | Beliebiger Text → Kurrent-Rendering | §4 | geplant (P2) |
| `/lese-hilfe` | Upload historischer Brief → HTR-Job | §5 | geplant (P1) |
| `/lese-lupe/:job` | Lese-Lupe für transkribierten Brief | §5 | geplant (P1+) |
| `/stil-analyse` | Upload Schrift-Probe → Statistik-Report | §6 | geplant (P3) |
| `/vergleich` | Hände vergleichen mit Heatmaps | §6 | geplant (P4) |
| `/open-data` | Daten-Export-Seite mit DOI-Verweis | §7 | zurückgestellt (Open-Core, architektur.md §17) |
| `/glossar` | Erklärungen (Rund-s, Ligaturen, Schwellzug…) | §1, §5 | geplant |

### Admin-Routen (hinter Auth)

| Pfad | Inhalt | Status |
|---|---|---|
| `/admin` | **Einstieg: die Vorlagen-Auswahl.** Alles darunter gehört zu genau einer Quelle und ihrer Hand, also steht die Wahl am Anfang statt in einem Menü; die aktive Vorlage steht danach im Header und führt mit einem Klick hierher zurück (`sections/admin/shell/StartView.tsx`) | existiert |
| `/admin/buchstaben[?g=<key>]` | **Buchstaben.** Ohne `g` die Alphabet-Übersicht (Chart-Crop vs. „wie geschrieben", ehemals `/admin/vergleich`-Tab), mit `g` der einzelne Buchstabe mit allen Werkzeugen: Tafel-Ausschnitt + Einrichtungs-Wizard + Diagnose + aufklappbarem Chart-Editor (ehemals `/admin/chart`), Tafel-Form neben Laufform, die Vorkommen aus den Wörtern, die H1-Statistik und die Absprünge zu Übergängen/Wörtern (`sections/admin/letters/`) | existiert |
| `/admin/uebergaenge[?l=<key>&r=<key>]` | **Übergänge.** Ohne Paar die Matrix aller Zweierkombinationen (ehemals `/admin/paare`) plus ein Freitextfeld für JEDE Kombination, mit Paar die komponierte Verbindung, die H2-Statistik „gemessen vs. komponiert", die dissezierten Vorkommen und — als letztes Mittel — der Paar-Editor (`sections/admin/joins/`) | existiert |
| `/admin/woerter[?w=<text>&s=<specimen>]` | **Wörter.** Ohne `w` die Wortproben-Liste mit Scores (ehemals `/admin/vergleich`-Tabs Wörter/Andere Hand), mit `w` ein beliebiger Text: wie die Engine ihn schreibt, woraus er besteht (Buchstaben + Übergänge als Absprünge) und — wo eine Platte ihn enthält — die nachgefahrene Spur mit Vorkommens-Overlay, Score und Wort-Editor (ehemals `/admin/belege` + `/admin/werkbank`-Rückgrat; `sections/admin/words/`) | existiert |
| `/admin/sources` | Source-Verwaltung | post-MVP |
| `/admin/jobs` | HTR-Job-Monitor (Quote-Übersicht) | post-MVP |

**Admin-Redesign 2026-08 (aus einem Guss):** Die fünf Seiten mit ihren
Tabs und der Dauer-Sidebar sind zu **drei Ansichten über einer Vorlage**
zusammengezogen — damit ist das in
[`optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md) §2/§6
angekündigte Aufgehen von Vergleich, Paar-Matrix und Belegen in der
Werkbank vollzogen. Jede Ansicht folgt demselben Muster **Übersicht ⇄
Detail**; das Subjekt steht in der Query (`sections/admin/shell/focus.ts`),
damit jeder Quer-Absprung ein normaler Link ist, der Zurück-Knopf die
Inspektionsgeschichte läuft und ein Reload dort landet, wo gearbeitet
wurde. Header (drei Bereiche + Vorlage + Auftragskorb) und die geteilte
Datenschicht (`shell/WorkbenchData.tsx`) liegen ÜBER dem Outlet, also
kostet der Weg Buchstabe → Übergang → Wort keinen neuen Ladevorgang.
Die alten Pfade (`/admin/chart` · `/vergleich` · `/paare` · `/belege` ·
`/werkbank` · `/edit/:glyphKey`) bleiben als Redirects bestehen, damit
Lesezeichen und Notizen weiter tragen.

---

## 3. i18n

**Status: Ziel-Design für P1, noch nicht eingebaut.** Ist-Stand:
`react-i18next` ist nicht installiert; alle deutschen UI-Strings liegen
als Pre-i18n-TS-Namespaces unter `app/src/locales/de/`, das Routing kennt
keine Sprachpräfixe. Der Rest dieses Abschnitts beschreibt das Soll.

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

- **MVP (DE only, Ist-Stand):** alle Strings nur in `locales/de/` (als
  TS-Namespaces, noch ohne i18n-Library); keine Sprachpräfixe im Routing.
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

### Implementiert dazu: X-Admin-Token-Fallback + Fail-Closed

`api/auth.py:require_admin` akzeptiert neben dem CF-Access-JWT einen
`X-Admin-Token`-Header als Shared-Secret-Fallback (lokale Entwicklung /
CI / Break-Glass): `ADMIN_TOKEN` im API-Env, das passende
`VITE_ADMIN_TOKEN` im SPA-Env. Ist keiner der beiden Pfade konfiguriert,
beantwortet das Gate jeden geschützten Request mit **503** — ein
fehlkonfiguriertes Prod-Deploy schlägt geschlossen fehl statt offen.

**Gegen die deployte API: nur über `api.kurrentschrift.ink`.** Die
Apex-Route `kurrentschrift.ink/api/*` liegt hinter Cloudflare Access und
antwortet schon an der Edge mit 302 auf den Login — der `X-Admin-Token`
erreicht Cloud Run dort nie. Das ist das Spiegelbild der Regel für
öffentliche Reads (`CONFIG.publicApiBase`): die offene Subdomain ist der
einzige Weg, auf dem ein selbst gesetzter Header ankommt. Verifiziert am
2026-08-01 — `GET /sources/<id>/work-items` mit `X-Admin-Token` gegen
`https://api.kurrentschrift.ink` antwortet auf allen vier Sources mit 200.

**Fallstrick Zeilenumbruch.** Cloud Run injiziert Secret-Manager-Werte
byteweise als Env-Var. Eine mit `echo` angelegte Version trägt ein
abschließendes `\n`, das ein HTTP-Header nicht transportieren kann —
`secrets.compare_digest` lehnt dann *jeden* Tokenwert mit 401 ab. Genau
das war von der Anlage des Secrets (2026-05-27) bis 2026-08-01 der Fall:
der Break-Glass-Pfad war unbenutzbar, ohne dass es auffiel, weil der
Browser-Admin über den JWT-Zweig läuft. Diagnose ist die Byte-Differenz,
nicht der Wert:

```bash
gcloud secrets versions access latest --secret=ADMIN_TOKEN --project=kurrentschrift | wc -c
```

gegen die Länge desselben Werts in `$(…)` — die Kommando-Substitution
schluckt den Umbruch, ein naiver Fingerprint-Vergleich meldet also
fälschlich „identisch", während Prod weiter 401 sagt. Neue Versionen
darum immer mit `printf '%s'` anlegen; `core/config.py` strippt seit
PR #262 zusätzlich alle vier Secret-gestützten Settings und mappt
Whitespace-only auf `None`, damit das Gate weiter fail-closed bleibt.
Cloud Run löst `latest` beim **Instanz-Start** auf — eine neue
Secret-Version wirkt also erst mit dem nächsten Kaltstart oder Deploy,
und häufiges Polling hält die Instanz warm und verhindert genau das.

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
- Geplant (P1, noch nicht in `vite.config.ts`):
  - Manual-Chunks wie anyplot — `mui-icons` separat (large, oft gecached),
    `mui` (MUI + Emotion), `vendor` (React + Router).
  - Gzip + Brotli pre-compressed via `vite-plugin-compression2`.

### Deploy auf Cloud Run

**Zwei Services**, live seit 2026-05:

- **`kurrentschrift-api`** — FastAPI (`api/Dockerfile`);
  `api/cloudbuild.yaml` fährt vor dem Rollout einen
  Alembic-Migrate-Job (`kurrentschrift-migrate`).
- **`kurrentschrift-app`** — statisches Vite-Build hinter
  nginx-unprivileged (`app/Dockerfile` + `app/cloudbuild.yaml`).
- **CI/CD:** Cloud Build, je ein Trigger pro Service (deploy-api /
  deploy-app), deployt aus `main`.
- **Region:** europe-west4 — niedrige Latenz für deutschsprachige
  Hauptzielgruppe.
- **Min instances:** 0 (Cold-Start akzeptabel für eine Lern-Webseite).
- **Memory:** API 1 Gi (für FastAPI + WeasyPrint + ggf. TrOCR später
  2–4 Gi), App 512 Mi.

### Reverse-Proxy / Routing

- `/api/*` → der Cloudflare-Worker vor dem App-Service leitet auf
  `api.kurrentschrift.ink` (FastAPI) um; nginx im App-Container kennt
  kein `/api` (siehe Kopfkommentar `app/nginx.conf`).
- `/admin/*` → React-SPA (Auth-Gate am Edge via Cloudflare Access, §5).
- alles andere → React-SPA mit Fallback `index.html` (nginx).

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
- `sections/landing/` — `LandingView` + `HeroWritten` (GLKurrent-Schreib-
  Animation, Font-first mit offener Engine-Naht) + `Reveal` (Scroll-Reveal).
- `sections/schriftkunde/` — der `/schriftkunde`-Überblick (Grundbegriffe,
  drei Ausgangsschriften mit Specimen, Federn, Tinte, Chronologie).
- `sections/hub/` — `HubView` (die `/lesen`- und `/schreiben`-Bereichs-Hubs).
- `sections/worksheet/` — `WorksheetView` + `ConfigPanel` + `PreviewSvg`
  (Lineatur-Konfigurator, `/schreiben/uebungsblatt`).
- `sections/scribe/` — der `/federprobe`-Live-Schreiber (Text →
  serverseitig komponiertes Wort, `WrittenWord`).
- `sections/tafel/` — die `/tafel`-Schreibtafel (Vorlage-Zeilen „wie
  geschrieben").
- `sections/quiz/` — `QuizView` + `useQuizEngine` (gesamte Quiz-Logik ohne
  JSX) + Setup/Play/Results-Panels + `QuestionVisual`.
- `sections/impressum/` — Impressum/Datenschutz/Quellen als Dokumentspalte.
- `sections/admin/chart/` — `ChartView` (Pointer-Routing) + `useChartViewport`
  (Zoom/Pan/Pinch) + `useBboxEditing` (Bbox-Commits, Lock) +
  `BboxOverlay`/`ChartToolbar` + pure `bboxGeometry`.
- `sections/admin/setup-wizard/` — `SetupWizard` (Dialog-Shell) + `useWizard`
  (State + Server-Mutationen) + `useCropView` (Crop-Viewport) + `WizardCanvas`
  + `steps/{Mask,Lineatur,Slant,Trace,Overview}Step`. Einzige Autoren-Fläche.
- `sections/admin/diagnostics/` — `DiagnosticDialog` (3-Spalten + M4-Fit),
  `DiagnosticView`/`FitView`.
- `sections/admin/shell/` — die Werkbank-Hülle, die alle drei Ansichten
  teilen: `AdminHeader` (drei Bereiche + Vorlagen-Chip + Korb-Badge),
  `StartView` (`/admin`, die Vorlagen-Auswahl), `LetterPicker`
  (Buchstaben-Grid aus `domain/glyphs.ts` — als Popover statt als
  Dauer-Sidebar), `WorkbenchData` (die EINE geteilte Datenschicht:
  Vorkommen je Quelle + die admin-gesicherten Statistik-Schichten je Hand,
  über dem Outlet montiert), `KorbContext` (⚑ von überall, Korb als
  Drawer) + `KorbPanel`/`MarkDialog`, `LensStats` (H1/H2-Blöcke),
  `OccurrenceThumb`, `Panel`/`ViewHeader` (die geteilten Layout-Bausteine)
  und die puren, getesteten `focus.ts` (Subjekt ⇄ URL) + `model.ts`.
- `sections/admin/letters/` — `LetterView` (`/admin/buchstaben`): Übersicht
  über `compare/GlyphComparison`, im Detail Tafel-Ausschnitt, Tafel-Form
  neben Laufform, Vorkommen, H1-Statistik, Absprünge.
- `sections/admin/joins/` — `JoinView` (`/admin/uebergaenge`): Matrix +
  Freitext-Kombination, komponierte Verbindung, H2-Statistik, Vorkommen,
  Paar-Editor.
- `sections/admin/words/` — `WordView` (`/admin/woerter`): Freitext-Wort,
  „woraus es besteht", Belege je Specimen über `WordSpineCard`.
- `sections/admin/chart/`, `setup-wizard/`, `diagnostics/`, `compare/`,
  `pairs/`, `belege/` bleiben die WERKZEUGE, die diese drei Ansichten
  einsetzen (Chart-Editor, Wizard, Diagnose, Vergleichsraster,
  Paar-Editor, Wort-Editor + die pure `registration.ts`) — sie haben seit
  dem Redesign keine eigene Route mehr.
- `components/` — `PaperBackground` (Papier-Atmosphäre), `PublicHeader`
  (3-Bereiche-Nav), `PublicFooter`, `PageContainer` (eine Inhaltsspalte,
  drei Breiten 760/1152/1280), `Prose` (Lesemaß ~66 Zeichen), `PageHeader`
  (einheitlicher Seitenkopf: Bereichs-Eyebrow + Playfair-Titel + Intro),
  `CategoryHeading` (Abschnittstitel mit Viridian-Kurrent-Initiale),
  `InfoHint` (Kurrent-„i"-Popover, die eine Info-Affordanz app-weit),
  `inkReveal/` (geteilte „wie geschrieben"-Primitiven: Silhouette,
  maskiert von einer gesweepten Centerline + Ink-Bleed/Settle),
  `WrittenGlyph` (ein Glyph als Duktus-Animation), `WrittenWord` (ganzes
  Wort/Zeile, serverseitig komponiert via `GET /write/word`), `BootStatus`
  (Boot/Fehler-Screens). Vollinventar mit Kern-APIs:
  [`design-system.md`](../concepts/design-system.md) §7.

### Neu (kommt mit Phasen P1–P5)

Bereits gebaut (siehe oben): Landing (`sections/landing/`),
Schriftkunde (`sections/schriftkunde/`), die Bereichs-Hubs
(`sections/hub/`), Lineatur-Konfigurator (`sections/worksheet/`,
`/schreiben/uebungsblatt`), Federprobe (`sections/scribe/`), Schreibtafel
(`sections/tafel/`), Lese-Quiz (`sections/quiz/`). Neue Features
kommen als je eine
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

- **Keine eigene Komponenten-Bibliothek.** MUI 9 deckt unsere
  UI-Bedürfnisse. Custom-Komponenten nur dort, wo es unvermeidbar ist
  (Animation, Lineatur, Heatmap). Die verbindliche Bauvorschrift
  (Tokens, Typo-Leiter, Flächen) ist
  [`design-system.md`](../concepts/design-system.md) — das ist ein
  Regelwerk ÜBER MUI, keine eigene Bibliothek.
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
