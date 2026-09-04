# Frontend-Stack

> **Status (2026-09-04): lebend.** Ist-Stand von Stack, Routen, i18n-Soll,
> Deploy, Admin-Gate und Crawler-Prerender.
>
> **Was gilt.** React 19 + Vite + MUI + React Router, EINE SPA für
> Endnutzer und Admin ([§1](#1-stack)). Öffentlich sind drei Bereiche
> plus Landing, der Admin ist die Werkbank in drei Ansichten
> ([§2](#2-routenstruktur) — die Routenkarte ist `app/src/routes/paths.ts`,
> nicht diese Liste). Das Admin-Gate ist Cloudflare Access in Prod und
> `ADMIN_TOKEN`/`X-Admin-Token` lokal; davor liegt seit 2026-09-02 das
> **Origin-Geheimnis**, das der Apex-Worker selbst stempelt, weil ein
> Worker-Subrequest die Transform-Rules der eigenen Zone umgeht
> ([§5](#5-auth-für-admin-routen), `infra/cloudflare/`). Gebaut und
> deployt wird auf Cloud Run: **Min-Instanzen API 1 · App 0**, Max je 3 —
> die eine warme API-Instanz seit 2026-08-30, weil ein Kaltstart gemessen
> 9,4 s p50 kostet, und `max=3`, damit ein Deploy die warme Instanz nicht
> ersetzen muss ([§6](#6-build--deploy)). Crawler bekommen vorgerenderte Seiten über den
> `$is_bot`-Pfad der nginx-Config. Was bewusst NICHT gemacht wird, steht
> in [§8](#8-was-wir-nicht-machen).
>
> **Was offen ist.** i18n ist als **Soll** beschrieben
> ([§3](#3-i18n)) — die Website ist v1 deutsch, Englisch folgt; die
> Komponenten-Map ([§7](#7-komponenten-map)) ist eine Beschreibung des
> Codes und veraltet zuerst, wenn eine Komponente umzieht.
>
> **Beschreibungsstände.** Die Detailregeln aus `CLAUDE.md`
> (Vier-Gesichter-Übersicht, Registrierungs-Regel, Kostenbudget,
> Cloud-Session-Betrieb) tragen den Stand **2026-08-16**; die Admin-Routen
> wurden am 2026-08-03 gegen den Code geprüft (PR #263), §5 am 2026-09-02
> beim Rollout korrigiert.
>
> **Nachzieh-Anlass.** Jede Änderung an `app/package.json`,
> `app/src/routes/paths.ts`, den Cloudbuild-/nginx-Dateien,
> `app/security-headers.conf`, `api/security_headers.py`,
> `api/routers/csp.py`, `api/auth.py`, `api/origin_gate.py`,
> `infra/cloudflare/` oder `app/src/lib/seo/prerender.ts`. Für die
> öffentliche Gestaltung ist
> [`design-system.md`](../concepts/design-system.md) die bindende
> Vorschrift, nicht diese Datei.

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

**Test-Abdeckung:** Vitest misst seit 2026-09-02 über die **ganze**
SPA-Quelle (`test.coverage.include: ['src/**/*.{ts,tsx}']` in
`app/vite.config.ts`, in Vitest 4 der Ersatz für das alte `all: true`) —
ohne diesen Block zählt nur, was ein Test zufällig importiert, was 82,7 %
meldete, wo über die ganze Quelle 19,2 % stehen. Eine Zahl, die ihre
eigene Testliste misst, ist schlechter als keine. Die Codecov-Ziele in
`codecov.yml` sind seither feste Böden je Flag statt `auto`.

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
| `/` | Landing (der Hero schreibt das Markenwort engine-first: `WrittenWord` über `/write/word`, die Engine bekommt so lange sie braucht — Owner-Entscheidung 2026-08-27; nur ein echter Fehler fällt auf den GLKurrent-Clip-Path-Wisch zurück — §7) | Einstieg |
| `/schriftkunde` | Überblick der deutschen Schreibschriften (der umbenannte frühere `/lehrbuch`) | Schriftkunde |
| `/lesen` | Hub → Quiz, Tafel | Lesen |
| `/quiz` | Lese-Quiz (Buchstaben + ganze Wörter) | Lesen |
| `/tafel[?g=<key>]` | Schreibtafel (Vorlage); mit `g` der Buchstabe im Detail unter dem Bogen (`sections/tafel/LetterDetail.tsx`, Vision Ziel 3: Strichfolge mit nummerierten Zügen und Stepper „Zug n von m", Ansatz/Auslauf-Ringe, Zug um Zug in zwei Tempi, Verwechsler als `SpecimenStrip`, Sprung in die Federprobe mit einem Bankwort — ein Tipp auf einen Buchstaben des Bogens setzt `g`, teilbar); seit 2026-08-29 mit „Lesetafel als PDF" — alle drei Vorlagen auf A4, im Browser gebaut (`lib/lesetafel.ts` auf `lib/pdf.ts`: die nachgeschriebene Schrift als gefüllte Silhouetten auf Lineatur mit Antiqua-Beschriftung, die anderen als ihre gemeinfreie Originaltafel, per Canvas zu JPEG gerastert und als DCTDecode-XObject eingebettet) | Lesen |
| `/lesen/vergleichen` | Lesart prüfen — eine Vermutung wird geschrieben, daneben die **echten Wörter**, die sich von ihr nur in Verwechslern unterscheiden (`GET /lesarten?text=…`: Verwechsler-Schlüssel + Rang aus `core/lesarten`, Vokabular `lesart_forms` = igerman98 ∪ Wortbank, geladen über `tools.lesarten.sync`; seit 2026-08-30 — davor Buchstabentausch ohne Wort dahinter), und die klassischen Verwechsler-Paare nebeneinander (`?text=` teilbar) | Lesen |
| `/schreiben` | Hub → Übungsblatt, Federprobe | Schreiben |
| `/schreiben/uebungsblatt` | Übungsblatt-Generator (Lineatur-Konfigurator, PDF); seit 2026-08-30 mit Übungstext — die Vorschrift-Zeilen serverseitig komponiert wie in der Federprobe (`/write/word`), im Browser in die Lineatur gesetzt (`lib/uebungstext.ts`) und in Vorschau wie PDF gleich gezeichnet | Schreiben |
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
| `/admin` | **Einstieg: die Vorlagen-Auswahl.** Alles darunter gehört zu genau einer Quelle und ihrer Hand, also steht die Wahl am Anfang statt in einem Menü; die aktive Vorlage steht danach im Header und führt mit einem Klick hierher zurück (`sections/admin/shell/StartView.tsx`). Die Wahl merkt sich der Browser in `localStorage`; Vorgabe ist `CONFIG.sourceId` (`app/src/global-config.ts`) — dieselbe Konstante hat Doppeldienst: Sie ist die Quelle, aus der die ÖFFENTLICHEN Seiten rendern (heute die Sütterlin-Ausgangsschrift 1922), UND die Vorauswahl des Admins | existiert |
| `/admin/buchstaben[?g=<key>]` | **Buchstaben.** Ohne `g` die Alphabet-Übersicht (ehemals `/admin/vergleich`-Tab): je Buchstabe VIER Flächen — Original (Chart-Crop) · Tafel-Form (Variante 0) · Laufform (Variante 100) · „Median & Vorkommen" (die H1-Aggregat-Skizze) — samt Kennzahlen und einem Sortier-Umschalter (Alphabet · Schlechteste zuerst), der das Raster zur Arbeitsliste macht (Details §7), mit `g` der einzelne Buchstabe mit allen Werkzeugen: Tafel-Ausschnitt + Einrichtungs-Wizard + Diagnose + aufklappbarem Chart-Editor (ehemals `/admin/chart`), Tafel-Form neben Laufform, die Vorkommen aus den Wörtern, die H1-Statistik samt Frische-Chip und Differenz-Skizze, die Absprünge zu Übergängen/Wörtern — und am Fuß, bewusst abgesetzt, der **Laufform-Übernahme-Block** mit Bestätigungsdialog (`sections/admin/letters/`, Issue #270) | existiert |
| `/admin/uebergaenge[?l=<key>&r=<key>]` | **Übergänge.** Ohne Paar die Matrix aller Zweierkombinationen (ehemals `/admin/paare`) plus ein Freitextfeld für JEDE Kombination, mit Paar die komponierte Verbindung, die H2-Statistik „gemessen vs. komponiert", die dissezierten Vorkommen und — als letztes Mittel — der Paar-Editor (`sections/admin/joins/`) | existiert |
| `/admin/woerter[?w=<text>&s=<specimen>]` | **Wörter.** Ohne `w` die Wortproben-Liste mit Scores (ehemals `/admin/vergleich`-Tabs Wörter/Andere Hand), mit `w` ein beliebiger Text: wie die Engine ihn schreibt, woraus er besteht (Buchstaben + Übergänge als Absprünge) und — wo eine Platte ihn enthält — die nachgefahrene Spur mit Vorkommens-Overlay, Score und Wort-Editor (ehemals `/admin/belege` + `/admin/werkbank`-Rückgrat; `sections/admin/words/`) | existiert |
| `/admin/eigenhand` | **Eigenhand.** Die einzige Admin-Ansicht, die zu einer HAND gehört statt zu einer Vorlage: Bestand der eigenen Schreibprobe (Streifen belegt/unterwegs/geplant, Fassungen, Bögen; welche Zeichen und Übergänge belegt sind — gemessen an dem, was der Streifenplan hergibt, Groß-/Kleinbuchstaben, Ligaturen, Ziffern und Sonderzeichen getrennt) und der Bogendruck (Stapel erzeugen, PDF öffnen). Dazu das stehende Setup der Hand (Feder · Tinte · Papier · Gerät) und die GESCHRIEBENEN Streifen: jede gespeicherte Fassung auf Klick, samt Ausschnitt je Wort — admin-gesichert, `private, no-store`, nie im Repository. Die Scans bleiben lokal; hochgeladen wird hier nichts (`sections/admin/eigenhand/`, [`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md) §7.1–§7.2) | existiert |
| `/admin/sources` | Source-Verwaltung | post-MVP |
| `/admin/jobs` | HTR-Job-Monitor (Quote-Übersicht) | post-MVP |

**Ausgeblendete Vorlagen.** Die Auswahl bietet nur die Quellen an, die
`CONFIG.hiddenSourceIds` (`app/src/global-config.ts`) nicht ausblendet —
heute `petzendorfer-1889`, das ZWEITE Kurrent-Chart (eine andere Hand mit
~57° gegenüber Loths ~50°), im Voraus eingesät für die Kurrent-Ziffernzeile,
die Loth 1866 fehlt: Solange dieses Autoring nicht beginnt, machen zwei
beide mit „Kurrent" beschriftete Karten die Einstiegswahl nur mehrdeutig.
Das Ausblenden ist eine reine Client-Liste und wird in
`context/AdminContext.tsx` an genau ZWEI Stellen angewandt (der einen
Verengung der Quellenliste und beim Lesen der gemerkten Auswahl, damit eine
gespeicherte ausgeblendete Id den Admin nicht auf einer Vorlage stranden
lässt, von der keine Karte wegführt). Gelöscht wird NICHTS — keine
Migration, keine DB-Änderung; die Zeile, ihre Chart-Bytes und jede
API-Route bleiben genau so, wie sie sind, und die Id aus der Liste zu
nehmen bringt sie zurück.

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

### Titel und H1 (seit 2026-08-29)

Befund des SEO-Audits vom 2026-08-29: alle Titel waren markenintern
(„Lese-Quiz · kurrentschrift.ink", „Schreibtafel · …"), die H1s reine
Projektnamen — kein Titel außer der Startseite trug „Sütterlin",
„Kurrent" oder „alte deutsche Schrift", und die Seite war bei Bing nicht
indexiert. Regel seitdem (`app/src/locales/de/seo.ts`, gepinnt von
`routes/seoCoverage.test.ts`):

- **`<title>`: Suchbegriff vorn, Marke hinten, ≤ 80 Zeichen** — „Sütterlin-
  Quiz: alte deutsche Schrift lesen üben · kurrentschrift.ink". Jeder
  indexierbare Titel nennt Sütterlin, Kurrent, „deutsche Schrift" oder
  „Schreibschrift"; Impressum und die noindex-404 sind ausgenommen.
- **H1 trägt das Suchwort, das Nav-Label bleibt der Kurzname.** Die
  Werkzeug-Seiten haben dafür neben `title` (Kurzname für Nav, Karten,
  Breadcrumbs) ein eigenes `heading` (`quiz.heading`, `tafel.heading`,
  `scribe.heading`; Hubs: `hub.*.heading`, der Kurzname wird ihr Eyebrow).
- **Die Hubs `/lesen` und `/schreiben` tragen je einen erklärenden Absatz**
  (`hub.*.about`: was die Schrift ist, für wen die Werkzeuge sind, Fakten
  aus der Schriftkunde) — vorher 139 bzw. 141 Wörter, zu dünn für einen
  Treffer. Seit dem Website-Audit 2026-09-02 gilt dasselbe für die beiden
  Werkzeug-Seiten: `quiz.about` und `scribe.about` stehen unter der H1, in
  der SPA wie im Prerender (vorher 111 bzw. 129 Wörter Hauptinhalt).
- **`description`: höchstens 155 Zeichen** (`seoCoverage.test.ts`). Google
  schneidet länger mitten im Satz ab, und verloren geht regelmäßig die
  letzte Teilaussage — genau dort steht die Zusage. Das Gate erlaubte bis
  zum Audit 2026-09-02 200 Zeichen; fünf Beschreibungen waren daraufhin auf
  bis zu 190 gewachsen. Dieselben Texte stehen als `og:description` im
  Prerender und (für die Startseite) in `app/index.html` — beim Kürzen
  mitziehen.
- **Was eine Seite verspricht, muss sie halten.** Der Prerender ist kein
  zweiter Textbestand, sondern dieselbe Locale in anderer Form: Wo die SPA
  eine Auswahl verbirgt, weil es sie nicht gibt (`quizOptions.offersChoice`),
  verbirgt die vorgerenderte Seite sie auch — sonst lesen Crawler und
  KI-Antworten ein Angebot, das die Seite nicht hat (Audit 2026-09-02:
  Kurrent, Offenbacher und drei Schwierigkeitsstufen im Quiz-Body). Gepinnt
  von `lib/seo/prerender.test.ts`.
- **`<lastmod>` in `sitemap.xml` ist die „Stand"-Zeile der Crawler-Seite**
  (`prerender.ts` liest sie von dort), nicht bloß Buchhaltung. Wer Copy
  ändert, zieht das Datum der betroffenen Route mit;
  `scripts/check-sitemap-lastmod.mjs` läuft im `npm run prerender` und
  hält jedes Datum gegen die Git-Historie der gerenderten Seite selbst
  (`app/prerender/<seite>.html`) — die Datei IST die Antwort auf „wann hat
  sich diese Seite geändert". Bis 2026-09-03 war der Vergleichsmaßstab eine
  handgepflegte Quellenliste je Seite (`PageSpec.sources`); die driftete in
  beide Richtungen — eine geteilte Datei wie `seo.ts` meldete Seiten stale,
  deren Text sich nicht bewegt hatte, und ein Body, der ein nicht gelistetes
  Modul las, änderte die Seite unbemerkt. Eine Folge ist einzukalkulieren:
  eine Änderung am Seitenrahmen (Nav-Beschriftung, Rechtehinweis) schreibt
  alle zehn Dateien neu und verlangt entsprechend alle zehn Daten — was den
  Crawler-Seiten tatsächlich passiert ist. Bei flacher Klonung (kein `git
  log`) überspringt der Wächter die Historien-Hälfte still, statt zehn
  Fehlalarme zu werfen; die Arbeitsbaum-Hälfte greift weiter.
- **`/seo-proxy` beantwortet HEAD** wie GET ohne Body (vorher 405 — für
  einen Link-Checker eine tote Seite).
- Der Prerender nimmt die Breadcrumb-Bezeichnung des letzten Glieds aus
  dem Nav-Label der Route, nicht mehr aus dem (jetzt langen) Titel.

Nicht Teil davon: `hreflang`/Englisch — kommt mit der englischen Lese-Hälfte
(Website-Audit 8/8). Owner-Schritt daneben: Search Console und Bing
Webmaster Tools anmelden, Sitemap einreichen.

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

### Davor: das Origin-Geheimnis (seit 2026-09-02)

Beide Cloud-Run-Dienste stehen mit `ingress=all` im Netz — es gibt keinen
Load Balancer, und einer würde mehr im Monat kosten als das ganze Projekt. Der
API-Dienst antwortet damit auf ZWEI Adressen: `https://api.kurrentschrift.ink`
(von Cloudflare proxied) und die rohe `*.run.app`-URL (nicht). Alles, was
Cloudflare durchsetzt — die Rate-Limiting-Regel, die WAF, der Cache — war über
die zweite Adresse umgehbar; das Audit vom 2026-09-02 hat genau das gemessen
(die `run.app`-Antwort trug keinen einzigen `cf-`-Header).

Eine **Cloudflare-Transform-Rule** stempelt deshalb auf jeden Request, den sie
für `api.kurrentschrift.ink` weiterreicht, den Header
`X-Origin-Secret: <Geheimnis>`. `api/origin_gate.py` verlangt ihn und antwortet
sonst **403** — vor dem Limiter, vor der Auth, vor jeder Datenbankabfrage. Das
ist **keine Authentifizierung**: der Header sagt „ich kam durch die Vordertür",
nichts darüber, wer da kommt. Wer etwas darf, entscheidet weiterhin
`api/auth.py`.

- **Unset heißt aus.** Ohne `ORIGIN_SECRET` in der Cloud-Run-Env ist die Prüfung
  komplett inaktiv — das ist zugleich der Rollback und der Grund, warum lokale
  Entwicklung und Testsuite sie nie sehen. **Achtung beim Rollback:** eine
  Änderung an Secrets oder Env legt eine NEUE Revision an, und der Dienst hängt
  nach jedem Deploy an einer namentlich festgenagelten Revision
  (`update-traffic --to-revisions=…`, `api/cloudbuild.yaml`) — die neue bekommt
  also erst Verkehr, wenn sie ausdrücklich promotet wird. Scharfschalten und
  Zurücknehmen sind deshalb je ZWEI Befehle: `services update …`, dann
  `services update-traffic --to-revisions=<neue Revision>=100`. Kein neuer
  Build, aber auch kein Selbstläufer.
- **Ausgenommen sind `/health` und `/seo-proxy/…`.** `/health` erreicht der
  Deploy-Smoke auf der `run.app`-Tag-URL der Kandidaten-Revision, die
  definitionsgemäß nie am Edge vorbeikommt — ein Gate davor ließe jeden Deploy
  geschlossen fehlschlagen. `/seo-proxy/…` ist Gürtel-und-Hosenträger: das
  nginx der Website holt die Prerender-Seiten über `api.kurrentschrift.ink`
  (`app/nginx.conf` `@seo_proxy`), kommt also durch den Edge und trägt den
  Header — aber der Preis eines Irrtums wären 403 für jeden Crawler.
- **Der Admin-Weg stempelt selbst — das war der Befund des Rollouts.** Die
  Apex `/api/*` erreicht den Dienst über den Worker
  `kurrentschrift-api-proxy`, und ein **Worker-Subrequest an einen Host
  derselben Zone läuft an den Transform-Rules der Zone vorbei**. Die Regel
  greift also für Browser und Crawler, aber nicht für das `fetch()` aus dem
  Worker heraus: `/api/health` meldete nach dem Anlegen der Regel weiterhin
  `off`. Der Worker setzt den Header deshalb selbst aus einer
  `secret_text`-Bindung `ORIGIN_SECRET` (danach `off-seen`, nach dem
  Scharfschalten `ok`). Quelltext, Einstellungen und Deploy-Weg liegen seit
  2026-09-02 im Repo: [`infra/cloudflare/`](../../infra/cloudflare/README.md) —
  vorher existierte der Worker nur im Dashboard. nginx kennt kein `/api` und
  ruft nichts direkt auf.
- **`/health` meldet das Urteil** für den Request, mit dem es gefragt wurde:
  `origin_gate` = `off` · `off-seen` · `ok` · `missing` · `mismatch` (nie der
  Wert). Damit lässt sich JEDER Weg in den Dienst — `api.`-Host, Apex hinter
  Access, nginx, rohe `run.app` — prüfen, BEVOR das Gate scharf geschaltet
  wird: Transform-Rule anlegen, dann muss jeder Weg, der weiterlaufen soll,
  `off-seen` melden; erst danach die Env setzen. Genau diese Messung hat den
  Worker-Befund oben gefunden, bevor er den Admin lahmlegen konnte — sie ist
  nicht Zierrat, sondern der Grund, warum das Scharfschalten kein Sprung war.
- **Break-Glass braucht jetzt beide Header.** Der dokumentierte Notweg über die
  direkte `run.app`-URL mit `X-Admin-Token` läuft ins 403, solange nicht
  zusätzlich `X-Origin-Secret` mitgeschickt wird — beide Werte liegen im Secret
  Manager, wer den einen holen kann, holt auch den anderen. Wer die Tür ganz
  aufmachen will, entfernt für die Dauer des Notfalls die Env-Variable.

**Gegen die deployte API: nur über `api.kurrentschrift.ink`.** Die
Apex-Route `kurrentschrift.ink/api/*` liegt hinter Cloudflare Access und
antwortet schon an der Edge mit 302 auf den Login — der `X-Admin-Token`
erreicht Cloud Run dort nie. Das ist das Spiegelbild der Regel für
öffentliche Reads (`CONFIG.publicApiBase`): die offene Subdomain ist der
einzige Weg, auf dem ein selbst gesetzter Header ankommt. Verifiziert am
2026-08-01 — `GET /sources/<id>/work-items` mit `X-Admin-Token` gegen
`https://api.kurrentschrift.ink` antwortet auf allen vier Sources mit 200.

**Dritte Umgebung: die claude.ai/code-Cloud-Session.** Dort gibt es keine
`.env` — die Datei ist gitignoriert und liegt nie im Checkout —, und das
Cloud-SQL-Egress-Gate blockiert eine lokal gestartete API. Die **deployte
API ist deshalb der einzige Admin-Pfad**; `ADMIN_TOKEN`, `VITE_ADMIN_TOKEN`
und `API_BASE_URL` (= die api-Subdomain) sind dort als Umgebungsvariablen
konfiguriert. Vorhandensein prüft man am Exit-Code, nicht am Wert:
`printenv ADMIN_TOKEN >/dev/null && echo set` — den Token selbst nie
ausgeben.

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

### Die zweite Tür: das nginx-Gate der Website (2026-09-04, aus ausgeliefert)

`api/origin_gate.py` hat die Tür des API-Dienstes zugemacht und die des
App-Dienstes zugleich als das benannt, was es von seiner Seite aus nicht
schließen konnte. `kurrentschrift-app` steht ebenfalls mit `ingress=all` im
Netz: Auf der rohen `*.run.app`-URL liefert es die ganze Website ohne
Bot-Challenge, ohne WAF und ohne Rate-Limit aus — **und** reicht einen
Crawler-UA über `@seo_proxy` an `https://api.kurrentschrift.ink` weiter, wo der
Edge das API-Geheimnis rechtmäßig stempelt. Das API-Gate kann das nicht sehen:
Der Request, den es bekommt, kam wirklich durch die Vordertür. Jeder solche
Umweg kostet einen Prerender-Read auf der API plus das Crawler-Plausible-Event,
das sie dafür meldet.

`app/origin-gate.conf.template` ist dieselbe Mechanik in nginx — **ein**
Geheimnis, **fünf** Urteile (`off` · `off-seen` · `ok` · `missing` ·
`mismatch`), eine Rollout-Prozedur. Die Datei ist eine Vorlage, weil nginx die
Umgebung nicht lesen kann; das Basis-Image bringt den Entrypoint
`20-envsubst-on-templates.sh` bereits mit, das Geheimnis kommt also als
gewöhnliche Cloud-Run-Env-Variable herein und beim Containerstart läuft nichts
Neues.

- **Aus, bis es jemand anschaltet.** Das Image setzt `ORIGIN_GATE=off`, der
  Dienst deklariert bis heute gar keine Env-Variablen. `ORIGIN_GATE=on` mit
  leerem `ORIGIN_SECRET` schlägt **geschlossen** fehl — die Map-Schlüssel sind
  getaggt, ein vergessenes Geheimnis öffnet also nicht das ganze Internet.
- **`/_health` meldet das Urteil** im Header `X-Origin-Gate`, für den Request,
  mit dem es gefragt wurde (nie den Wert). Es ist der EINZIGE ausgenommene
  Pfad, exakt und ohne Präfix. Damit ist jeder Weg messbar, bevor scharf
  geschaltet wird: Transform-Rule auf `kurrentschrift.ink` erweitern, dann muss
  der Edge-Weg `off-seen` melden und die rohe `run.app`-URL weiter `off`; erst
  danach wird armiert.
- **Zwei Aufrufer kommen legitim am Edge vorbei** und stempeln jetzt selbst:
  der Deploy-Smoke in `app/cloudbuild.yaml` (liest `ORIGIN_SECRET` **im Schritt**
  aus dem Secret Manager, nicht über `availableSecrets`, und fragt `/_health`
  vor jeder Inhaltsprobe) und der tägliche Bot-Wächter
  `.github/workflows/bot-serving-check.yml` (aus dem Repository-Secret
  `ORIGIN_SECRET`; `missing`/`mismatch` sind dort harte Fehler mit einer
  Meldung, die das Secret beim Namen nennt — sonst würde ein scharfes Gate
  ohne Secret 32 rote Crawler-Checks erzeugen und ein Incident aufmachen, der
  „jede Crawler-Seite ist kaputt" behauptet).
- **Der Worker braucht hier nichts.** Anders als im Schwesterprojekt schickt
  `kurrentschrift-api-proxy.js` **jeden** Pfad an `api.kurrentschrift.ink`, und
  die Plausible-Aufrufe (`/js/script.js`, `/pa/event`) laufen über einen
  eigenen Worker direkt zu `plausible.io` — beides erreicht diesen Container
  nie. Das ist eine Eigenschaft des Codes, kein Naturgesetz:
  `tests/test_app_origin_gate.py` schlägt an, sobald ein Zweig einen Pfad an
  den eigenen Origin zurückgibt (dort wäre wieder zu stempeln, weil ein
  Worker-Subrequest in derselben Zone an den Transform-Rules vorbeiläuft).
- **Scharfschalten ist ein Block, kein Flag.** Auch dieser Dienst nagelt
  Verkehr namentlich fest (`app/cloudbuild.yaml` promotet mit
  `--to-revisions=…=100`), ein `services update` allein legt also eine
  armierte Revision an, die nichts ausliefert. Dazu: das Image der
  **ausliefernden** Revision pinnen (nicht die letzte), die Secret-Version als
  **Nummer** setzen (nie `:latest` — Cloud Run löst sie beim Instanz-Start
  auf, sonst gibt es sporadische 403 innerhalb einer Revision) und keinen Lauf
  starten, während ein Cloud Build unterwegs ist. Der vollständige Block, die
  Hostnamen-Tabelle und der Rollback stehen in
  [`infra/cloudflare/README.md`](../../infra/cloudflare/README.md)
  § „The site's own origin".
- **Ein Längen-Deckel auf dem Geheimnis.** nginx kann keinen `map`-Schlüssel
  hashen, der länger ist als ein Bucket; der Schlüssel ist `presented:` plus
  das ganze Geheimnis, die Vorlage setzt deshalb `map_hash_bucket_size 512`.
  Ab grob 500 Zeichen startet nginx nicht mehr — mit ausgeschaltetem Gate
  dagegen einwandfrei, der Fehler erschiene also erst im Moment des
  Scharfschaltens. Gefunden hat ihn der Container-Smoke im Schwesterprojekt;
  hier hält ihn der Job `app-image` in `.github/workflows/ci.yml` gefangen, der
  das echte Image mit einem produktionslangen Geheimnis dreimal fährt (aus,
  scharf, scharf ohne Geheimnis).

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
- **Min instances (Stand 2026-08-30):** API **1**, App **0**. Die frühere
  Annahme „Cold-Start akzeptabel für eine Lern-Webseite" beruhte auf einem
  geschätzten ~3-Sekunden-Start; gemessen sind es bei der API **p50 9 447 ms /
  p95 12 245 ms**, und 60 % aller Stunden sehen gar keine Anfrage, der Dienst
  ist also meist kalt. Rund 279 der 344 Starts in 30 Tagen waren nutzerseitig.
  98 % der Zeit gehen für Containerstart und Python-Import drauf, die Datenbank
  kostet 0,13 s. Die App bleibt bei 0 — sie startet in 170 ms und wäre eine
  warme Instanz nicht wert. Gegenfinanziert durch `anyplot-app`, das mit 99,56 %
  Leerlauf dauerwarm stand (anyplot#10812); netto ~0 €. Die Kostenrechnung
  dahinter: eine Mindestinstanz mit 1 vCPU kostet rund 8,50 €/Monat, weil
  Leerlauf-CPU zu ~10 % des Aktivsatzes abgerechnet wird, Leerlauf-Speicher
  aber zum vollen Satz.
- **Max instances:** API **3**, App 3. Nicht wegen Durchsatz — in 30 Tagen
  liefen ganze 3 Anfragen auf HTTP 429 —, sondern weil `min=1` zusammen mit
  `max=1` ein Deployment zwingt, die einzige Instanz zu **ersetzen**, statt die
  neue daneben warmlaufen zu lassen. Daher kamen die ~73 Deploy-Kaltstarts.
- **Memory:** API **512 Mi** (gemessen 15 % Mittel / 25 % p99 von 1 GiB, also
  ~254 MiB Spitze — 512 Mi lässt doppelte Luft über p99; bei einer Dauerinstanz
  ist die Speicherstufe reine Standmiete), App 512 Mi. Sollte WeasyPrint oder
  später TrOCR mehr brauchen, wird hier wieder erhöht.
- **Datenbank:** Alle Daten liegen in Postgres — DB `kurrentschrift` auf
  der Cloud-SQL-Instanz von anyplot (Zugang über `.env`). **Die lokale
  Entwicklung schreibt DIESELBE Cloud-SQL-DB; eine separate lokale DB gibt
  es nicht.** Jeder Schreibvorgang aus einem Dev-Lauf trifft also die
  geteilten Echtdaten.

### Prerender für Crawler (seit 2026-08-28)

Crawler und KI-Agenten führen kein JavaScript aus; die SPA gäbe ihnen
auf jeder URL die leere Hülle mit dem Startseiten-Titel. Seit 2026-08-28
bekommen sie stattdessen **je Route eine vorgerenderte HTML-Seite** —
nach dem Muster von anyplot, mit derselben Crawler-Liste (Entscheid
des Autors: „identisch halten"). Der Markdown-Spiegel der Schriftkunde
(2026-08-27, `/schriftkunde.md`) war der Vorläufer für eine Seite und
ist in diesem Pfad aufgegangen.

- **Erkennung** in `app/nginx.conf`: die `map $http_user_agent $is_bot`
  ist WORTGLEICH mit `~/projects/anyplot/app/nginx.conf` (Suchmaschinen,
  KI-Crawler, nutzergesteuerte Fetcher, Social-/Messenger-Vorschauen);
  eine Änderung wird in beiden Dateien im selben Zug gemacht. Ein
  gemappter UA landet über `error_page 418 = @seo_proxy` beim API-Host
  (`https://api.kurrentschrift.ink/seo-proxy$request_uri`, TLS-Prüftiefe
  4 — anyplots Vier-Wochen-502 wiederholt sich hier nicht), Menschen
  bekommen `index.html`. `robots.txt`, `llms.txt`, `sitemap.xml` und
  alle statischen Dateien (`og.png`, Favicon …) werden auch für Bots
  DIREKT bedient (`location =` bzw. die Regex-Location auf
  Dateiendungen) — sonst ginge das `og:image` einer Link-Vorschau an den
  Proxy. Trailing Slashes werden relativ auf die kanonische Form
  umgeleitet (`absolute_redirect off`).
- **Inhalt**: `app/src/lib/seo/prerender.ts` rendert aus dem
  Locale-Katalog je öffentliche Route ein vollständiges Dokument — Head
  (Title/Description aus `seo.ts`, Canonical, OG/Twitter, JSON-LD:
  `WebSite` auf der Startseite, `BreadcrumbList` darunter), Body in der
  DOM-Reihenfolge der Seite (eine Regel je View-Komponente; Schriftkunde
  komplett, Landing samt Schriftstatus, Hubs, Impressum; die Werkzeuge
  Quiz/Tafel/Übungsblatt/Federprobe als beschriebene Auswahl mit dem
  Hinweis, dass das Werkzeug selbst im Browser läuft), Site-Nav auf
  jeder Seite, Footer mit Stand (aus dem Sitemap-`lastmod` der Route —
  deterministisch statt `new Date()`) und dem Rechtehinweis in-band
  (offene Politik `ai-train=yes` + Vorbehalt der Schriftdaten). Dazu die
  404-Seite mit `noindex`. Erste Zeile jeder Datei ist der Marker
  `<!-- kurrentschrift.ink prerender -->`, an dem der Bot-Serving-Check
  eine vorgerenderte Seite von der Hülle unterscheidet.
- **Erzeugung**: `npm run prerender` (läuft als `prebuild` vor jedem
  `vite build`; `--experimental-strip-types`, damit auch Node 22.15 den
  `.ts`-Renderer laden kann) schreibt `app/prerender/*.html` — die
  Dateien sind EINGECHECKT, denn das **API-Image** liefert sie aus
  (`api/Dockerfile` kopiert `app/prerender/`, `api/routers/seo.py`
  bedient `/seo-proxy/{route}` als reine Datei-Suche: keine DB, kein
  Template, nichts, das ein Crawler teuer machen kann; Unbekanntes
  bekommt die 404-Seite mit Status 404 — die Hülle antwortete 200).
- **Wächter**: `prerender.test.ts` — jede öffentliche Route hat eine
  Seite; die Inhaltsseiten (Landing, Schriftkunde, Hubs, Impressum)
  spiegeln jedes Locale-Blatt oder benennen es im SKIP; die
  eingecheckten Dateien sind byte-gleich mit einem frischen Render und
  nichts anderes liegt im Verzeichnis; Head, Marker, Nav und
  Rechtehinweis auf jeder Seite. `tests/test_api_seo_proxy.py` pinnt die
  API-Seite (Route → Datei, 404, keine Pfadtricks). Und weil der Pfad
  für Menschen unsichtbar ist: `.github/workflows/bot-serving-check.yml`
  ruft täglich den Cloud-Run-Origin mit Crawler-UAs an (Prerender je
  Route, Bypass der Maschinendateien, `og.png`, Trailing Slash, 404,
  SPA-Kontrolle) — anyplots Alarm, der dort vier stille Wochen beendet
  hat.
- Bewusst NICHT in `sitemap.xml` und ohne eigene URL: die Prerender-
  Seite IST die Route (gleiche URL, gleicher Canonical) — Google
  billigt das ausdrücklich, solange der Inhalt dem entspricht, was
  Menschen sehen.
- **Für Maschinen lesbar, nicht nur für Crawler erreichbar** (seit
  2026-08-28, nach dem Befund eines Assistenten, der die Seiten
  abgerufen hatte): Die drei Schriften tragen ihre **Kennwerte als
  Daten** — im Locale ein typisiertes `data` je Variante (`slantDeg`,
  `lineature`, `pen`, `stroke`, bei Bedarf `penAngleDeg`,
  `lineatureAlt`), im Prerender der Schriftkunde zweimal ausgegeben: als
  JSON-LD (`ItemList` aus `DefinedTerm`s mit `PropertyValue`s) im Head
  UND als sichtbarer `<pre><code class="language-json">`-Block im Body,
  weil die HTML→Markdown-Konverter, mit denen Assistenten Seiten
  abrufen, `<script>` verwerfen und `<pre>` behalten. Jeder Winkelwert
  in der Prosa nennt seine Bezugsgröße selbst („75–80° zur Grundlinie
  (90° = senkrecht)", „Federkante 15–20° zur Schreiblinie — nicht die
  Schräglage"), damit ein Chunk allein nicht Schräglage und
  Federwinkel zusammenwirft; `prerender.test.ts` hält Zahlen und Prosa
  zusammen. Die **Buchstaben selbst** sind über Rezepte abrufbar (Tafel-
  Seite „Buchstaben für Maschinen" + `llms.txt`): Inventar
  (`/templates`), Vorlage als PNG (`/bboxes/{glyph_key}/crop`,
  gemeinfrei), geschriebene Form als SVG (`/write/glyphs/{glyph_key}.svg`
  — neu, [`write-api.md`](write-api.md)), Geometrie und ganzes Wort als
  JSON, das ganze Wort auch als Bild (`/write/word.svg?text=`).

### Bot-Traffic auf einer zweiten Plausible-Site (seit 2026-08-28)

Wer die vorgerenderten Seiten liest, sieht die Besucher-Statistik nie —
kein JavaScript, kein Plausible-Skript. Der Prerender-Pfad ist der eine
Ort, an dem diese Abrufe sichtbar werden, und dort werden sie gezählt:
**serverseitig, auf der zweiten Plausible-Site `bots.kurrentschrift.ink`**
(nach anyplots Vorbild, Glossar „Bot-Site"). Die Middleware
`record_bot_fetch` (`api/main.py`) meldet jeden `/seo-proxy`-Abruf an
`api/analytics.py`, das den User-Agent gegen die mit anyplot wortgleiche
Taxonomie `AI_AGENTS` hält und ein Event `bot_fetch` mit `assistant`,
`kind`, `path` und `status` an Plausibles Events-API schickt —
Fire-and-forget, nie im Antwortpfad. Eine Middleware statt einer
Router-Dependency, weil nur sie den STATUS sieht: Eine 404 wird als 404
aufgezeichnet, nicht als Seitenaufruf.

Drei Dinge lassen die Events schweigend verschwinden — alle drei am
2026-08-28 live nachgestellt:

- **Ein Bot-User-Agent.** Plausible verwirft jedes Event, dessen UA es
  als Bot erkennt — jeden UA auf diesem Pfad. Darum laufen die Events
  unter `kurrentschrift-server/1.0`; die Identität steckt in den Props.
- **Eine Hosting-IP als Besucher.** Probe-Events mit `X-Forwarded-For`
  aus Google-Cloud-Bereichen (`34.90.1.1`, `35.204.1.1`) kamen nie an,
  dieselben Events mit einer Heim- oder GitHub-IP sofort. Auf dem
  Crawler-Pfad (Cloud-Run-App → Cloudflare → API) ist `cf-connecting-ip`
  aber genau die Google-Egress-IP des App-Containers — von zwanzig
  Crawler-Abrufen zählte einer. Darum reicht nginx den Crawler in
  `X-Forwarded-For` durch (`@seo_proxy`, `$proxy_add_x_forwarded_for`),
  und `api/request_context.py::visitor_ip` nimmt die ERSTE gültige
  weitergeleitete Adresse VOR `cf-connecting-ip` (anders als anyplot;
  für direkte Clients hinter Cloudflare sind beide dieselbe Adresse).
- **Der Edge-Cache.** Cloudflare cacht die Antworten des API-Hosts per
  Regel; `/seo-proxy` antwortete `s-maxage=86400` und lieferte
  `cf-cache-status: HIT` — ein gecachter Abruf erreicht die zählende
  Middleware nie. `/seo-proxy` antwortet deshalb `private, no-store`;
  der Crawler bezahlt den API-Roundtrip für eine 8-KB-Datei, das ist
  der Preis der Zählung.

Aktiv ist die Meldung nur in Produktion (`ENVIRONMENT=production`, wie
Cloud Run es setzt); `BOT_ANALYTICS=true|false` überschreibt — ein
Dev-Lauf schreibt nie auf die Live-Bot-Site. Auf der Bot-Site liegen
außerdem ein paar Events mit `assistant=probe` vom 2026-08-28 — die
Nachstellung oben; im Dashboard herausfiltern, nicht wundern.

**Zweites Event `asset_fetch`** (seit 2026-08-28): Was Assistenten
über die API konkret ABRUFEN — einen Buchstaben als Bild
(`/write/glyphs/{key}.svg`) oder JSON, ein Wort als Bild
(`/write/word.svg?text=`) oder JSON, den gemeinfreien Tafel-Ausschnitt
(`/bboxes/{key}/crop`) — meldet dieselbe Middleware mit `asset`
(`glyph_svg` · `glyph_json` · `word_svg` · `word_json` · `crop`),
`source` (Quellen-Id) und `key` (glyph_key bzw. der angefragte Text,
auf 80 Zeichen gekappt) neben `assistant`, `kind`, `status`
(`api/analytics.py::classify_asset`, `track_asset_fetch`). Nur die
Einzel-Routen zählen; Batch-Read und Inventar sind Sache der SPA — und
ein Browser-UA kommt ohnehin nie bis hierher, sodass die Abrufe der
eigenen Besucher (Federprobe, Quiz-Crops) die Bot-Zahlen nicht
verfälschen. Damit lässt sich im Dashboard lesen, welche Buchstaben und
Wörter Assistenten wie oft zeigen wollten — mit einer Einschränkung: Die
JSON-Reads und der Crop bleiben am Edge gecacht (die Tafel, das
Hero-Wort und das Quiz hängen daran), ein Edge-HIT erreicht die
Middleware nicht, ihre Zahl sind also die Cache-MISSES (erster Abruf je
Asset und Edge-TTL). Die SVG-Reads, die nur Assistenten anfragen,
antworten `private, max-age=300` (Browser-Cache, kein Edge) und zählen
jeden Abruf (`api/http.py` `BROWSER_ONLY_CACHE`, Befund 2026-08-28:
drei von vier Assistenten-Abrufen waren Edge-HITs und fehlten).

Auf der Plausible-Seite braucht die Site `bots.kurrentschrift.ink` die
Ziele `bot_fetch` und `asset_fetch` (Custom Events) und die
registrierten Properties `assistant`, `kind`, `path`, `status` sowie
`asset`, `source`, `key` — ohne Registrierung kommen die Events an,
lassen sich aber nicht aufschlüsseln. Die Site hat KEIN
Tracking-Skript und zeigt darum „Setup pending" — erwartet, kein
Fehler. `kind` ist die Eigenschaft, nach der man filtert:
`user_directed` ist ein Leser, alles andere ein Korpus-Bau. Erst nach
`status` filtern, dann lesen.

### Schrift-Auslieferung (seit 2026-08-27)

- Alle `@font-face`-Regeln stehen früh in `app/index.html`; die Dateien
  liegen selbst gehostet unter `app/public/fonts/` (16 wörtliche
  woff2-Kopien aus `@fontsource/{eb-garamond,playfair-display}` v5.3.0,
  Subsets latin + latin-ext, plus die beiden Show-Fonts GLKurrent/
  Suetterlin-TTF). Die `@fontsource`-Pakete sind devDependencies —
  Bezugsquelle und Update-Kanal, kein Laufzeitpfad; `npm run fonts:sync`
  kopiert nach einem `npm update` neu und prüft Byte-Identität
  (Lizenzbedingung: verbatim, nie re-subsetten — `app/THIRD_PARTY_NOTICES.md`).
- Zwei Above-the-fold-Schnitte sind per `<link rel="preload" as="font">`
  vorgeladen (Playfair 600 + Garamond 400, latin) — das einzige
  layoutunabhängige Startsignal, weil `#root` bis zum Entry-Chunk leer
  ist; `crossorigin` ist auch same-origin Pflicht. Die Zahl ist gemessen,
  nicht gesetzt: im Fast-3G-A/B kostete jeder weitere Preload den
  Entry-Chunk mehr, als er brachte.
- Die `/fonts/`-URLs sind UNGEHASHT: nginx cached sie 30 Tage (nicht
  `immutable`); wird je eine Datei wirklich getauscht, muss der DATEINAME
  mitversioniert werden und `index.html` mitziehen. Die gehashten
  `/assets/`-Bundles cachen `immutable`/1 Jahr (`app/nginx.conf`).

### CLS auf `/tafel`: gemessen, und nicht die Schrift (2026-09-03)

Der Website-Audit vom 2026-09-02 hat den Layout-Sprung auf `/tafel` der
nachgeladenen GLKurrent-Initiale zugeschrieben und daraus die offene
`font-display`-Frage abgeleitet. Die Nachmessung in **Produktion** widerlegt
das: der Sprung passiert, **nachdem** die Schrift geladen ist.

Aufbau — echtes Chrome über CDP (nicht headless; seit dem 2026-09-03 steht
Cloudflare Bot Fight Mode vor der Zone, eine Challenge wäre also möglich, die
ausgelieferte Seite wurde je Lauf gegengeprüft), `ignoreCache`, Slow 4G +
4× CPU, je drei Läufe, gemessen mit einem `PerformanceObserver` auf
`layout-shift`:

| Ansicht | CLS | Ursache |
|---|---|---|
| Mobil 390×844 | 0,0948 · 0,0948 · 0,0979 | ein einziger Shift bei ~1,9–2,3 s |
| Desktop 1280×800 | 0,112 · 0,112 · 0,112 | derselbe Shift |

Ursachenanteil, aus den Shift-Quellen und einer Zeitreihe der Dokumenthöhe:

- **Tafelscans: 0.** Sie tragen seit #476 ihr `chart_size` als
  `aspect-ratio` (1633/1869 · 1614/1300 · 2190/1029) und reservieren ihren
  Platz, bevor ein Byte Bild da ist.
- **Geschriebene Initiale (GLKurrent): 0.** `document.fonts.check('40px
  GLKurrent')` ist in JEDEM Lauf schon `true`, bevor der Shift eintritt.
- **Später Aufbau der drei Schrift-Abschnitte: alles.** Bis ~1,4 s ist das
  Dokument 844 px hoch (Kopf + Einleitung), dann springt es in EINEM Schritt
  auf 3132 px (mobil) bzw. 4494 px (Desktop), sobald `/sources` beantwortet
  ist. Die Fußzeile, die bis dahin bei y≈649 im Sichtfeld stand, verlässt es —
  genau dieser eine Shift IST der CLS.

Folge für die offene Entscheidung: `font-display: optional` für die Initiale
würde diese Zahl **nicht** bewegen. Wer den CLS senken will, reserviert die
Höhe der drei Abschnitte (Skelett), solange die Quellen laden — das ist eine
Gestaltungsfrage (eine hohe leere Fläche statt einer kurzen Seite) und keine
Schriftfrage.

#### Das Skelett, gebaut und gegengemessen (2026-09-04)

Genau diese Reservierung steht jetzt: `TafelSkeleton` zeichnet vom ersten Bild
an den eigenen Seitenkopf und die drei Abschnitte in ihrer fertigen Höhe, statt
eine Bildschirmhöhe „lade Vorlage …" zu zeigen. Reserviert wird, was sich sonst
bewegt — die echten Schriftnamen und Feder-Zeilen (feste Texte, also von Anfang
an richtig), ein Kasten in Größe des Status-Chips, die Tafel im eigenen
Seitenverhältnis (`RESERVED_CHART_RATIO` in `useGrundtafeln.ts`, Spiegel von
`sources.chart_size`) und die Herkunftskarte. Die Ratios sind **nur
Reservierung**: `OriginalScan` nimmt sein `aspect-ratio` weiterhin aus der
Antwort, eine ausgetauschte Tafel kostet also einen kleinen Shift, nie ein
falsch geformtes Bild.

Gegengemessen mit demselben Aufbau wie oben (echtes Chrome über CDP, Slow 4G +
4× CPU, Cache aus, je drei Läufe). Beide Stände als lokaler `preview`-Build
gegen `https://api.kurrentschrift.ink` — die Zone hat Bot Fight Mode, und der
Basis-Build reproduziert die Produktionszahl auf zwei Stellen genau (0,0969 vs.
0,0948–0,0979 mobil; 0,1125 vs. 0,112 Desktop), samt identischer Dokumenthöhe
3132/4494 px:

| Ansicht | vorher | nachher | Rest |
|---|---|---|---|
| Mobil 390×844 | 0,0969 · 0,0969 · 0,0969 | 0,0007 · 0,0007 · 0,0007 | Kopfzeilen-Fontswap |
| Desktop 1280×800 | 0,1125 · 0,1125 · 0,1125 | 0,0004 · 0,0004 · 0,0004 | derselbe |

Der Beitrag der Seite selbst ist damit 0: was übrig bleibt, ist der Schriftwechsel
in der Navigation des gemeinsamen Seitenkopfs (0,00073 mobil / 0,00033 Desktop) —
den hatte die alte Seite genauso, er gehört nicht `/tafel`.

Genauigkeit der Reservierung, gemessen als Höhe des reservierten gegen den
fertigen Abschnitt: Kurrent und Offenbacher 0–1 px, Sütterlin 39 px (mobil) bzw.
57 px (Desktop). Diese Differenz ist die Original/Geschrieben-Umschaltung, die es
nur auf der nachgeschriebenen Schrift gibt — welche das ist, weiß erst
`/sources`, und sie liegt auf beiden Ansichten unter der Falzkante, wo eine
Verschiebung nichts kostet. Der Schimmer läuft unter
`prefers-reduced-motion: reduce` gar nicht (`animation={false}`, geprüft: keine
`MuiSkeleton-wave`-Klasse, `animation: none`).

### Sicherheits-Header und Cache-Control (seit 2026-09-02)

Bis zum Audit vom 2026-09-02 lieferte `kurrentschrift.ink` **keinen einzigen**
der sechs üblichen Sicherheits-Header und auch kein `Cache-Control` auf der
SPA-Hülle aus; das Schwesterprojekt trug beides schon. Seither stehen sie in
`app/security-headers.conf` — eine eigene Datei, weil nginx `add_header`
**nicht über Ebenen hinweg vererbt**: Sobald ein `location`-Block einen eigenen
`add_header` setzt, fallen sämtliche geerbten weg. Die Datei wird darum im
Server-Block UND in jedem solchen `location` per `include` gezogen; wer irgendwo
einen `add_header` ergänzt, ergänzt die `include`-Zeile daneben.
`tests/test_csp_policy.py` hält genau das fest.

| Header | Wert | Warum |
|---|---|---|
| `Content-Security-Policy-Report-Only` | siehe unten | Erlaubt-Liste der tatsächlichen Quellen der Seite |
| `Strict-Transport-Security` | `max-age=15552000` | 180 Tage, **ohne** `includeSubDomains`, **ohne** `preload` (Autor-Entscheid 2026-09-02, wie anyplot) |
| `X-Content-Type-Options` | `nosniff` | |
| `X-Frame-Options` | `SAMEORIGIN` | die alte Hälfte von `frame-ancestors` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | |
| `Permissions-Policy` | Geo/Kamera/Mikro/Payment/USB/MIDI/Serial aus | alles Ungenannte behält seine Vorgabe — u. a. `clipboard-write`, das „Link kopieren" braucht. `bluetooth` steht bewusst NICHT drin: Chromium kennt das Token nicht und schreibt dafür „Unrecognized feature" in jede Besucher-Konsole (im Durchgang vom 2026-09-02 gesehen) |

**Die CSP nennt die gemessenen Quellen, nicht die vermuteten.** `script-src`
kommt **ohne** `'unsafe-inline'` aus: Die beiden Inline-Skripte in
`app/index.html` (Hero-Vorwärmer und Plausible-Stub) laufen über ein **Nonce
pro Antwort**, der Plausible-Loader `/js/script.js` und das Vite-Modul sind
`'self'`.

Bis 2026-09-04 standen dort zwei sha256-Hashes, und der Tausch hat einen
gemessenen Grund. Ein Hash gilt für die **Bytes** — und ein *drittes*
Inline-Skript kommt hinzu, das dieses Repository nicht schreibt: Cloudflares
JavaScript Detections spritzt es an der Kante in jede HTML-Antwort ein, mit
Ray-ID und Zeitstempel pro Antwort im Rumpf. Dafür kann es keinen Hash geben,
und eine reine Hash-Policy blockiert genau dieses eine Skript (im
Schwesterprojekt gemessen, anyplot #11213) — auf einer Free-Plan-Zone, auf der
JavaScript Detections bei aktivem Bot Fight Mode nicht einmal abschaltbar ist.

Das Nonce ist Cloudflares eigene Empfehlung: Die Kante liest den
**Response-Header** und stempelt ihr eingespritztes Skript damit — am
2026-09-04 auf anyplot.ai live nachgemessen, inklusive der beiden Skripte, die
Cloudflare in seinem versteckten iframe erzeugt. Erzeugt wird es von nginx als
`$request_id` (16 Zufallsbytes, 32 Hex-Ziffern); `sub_filter` stempelt
dieselbe Variable auf jedes `<script`-Tag der Shell, und
`tests/test_csp_policy.py` lässt die beiden Hälften nicht auseinanderlaufen.
Ein Nebeneffekt, der in `app/nginx.conf` steht: `sub_filter` löscht
`Last-Modified` und `ETag`, deshalb bringt das frühere `no-cache` auf der Shell
kein 304 mehr und der Header heißt jetzt `no-store` — gleiche Bytes, aber die
Zusage, dass kein genonctes Dokument im Cache liegt.

`style-src` behält `'unsafe-inline'`, und zwar nicht mehr mangels Nonce —
nginx kann eines erzeugen, siehe oben —, sondern weil die Theme-Tokens auf
inline-`style`-**Attributen** reiten, die ein Nonce grundsätzlich nicht deckt,
und weil Emotion (MUI) sein Stylesheet zur Laufzeit weiterschreibt.

**Die Report-Only-Woche.** Die Policy geht als
`Content-Security-Policy-Report-Only` live und blockiert damit nichts, sondern
meldet nur — ein Fehler in ihr würde sonst die Werkbank unbenutzbar machen, und
die Werkbank ist genau die Fläche, die kein automatischer Durchgang öffnen kann.
Gemeldet wird an `POST /csp-report` auf dem API-Host (`api/routers/csp.py`):
zählt und loggt, schreibt nichts, kennt beide Wire-Formate (`report-uri` schickt
ein Objekt, die Reporting-API ein Array mit camelCase-Feldern) und ist die
einzige öffentliche Schreiboperation dieser API — als solche in
`tests/test_api_public_surface.py::PUBLIC_WRITES` benannt und begründet. Vom
Rate-Limiter ist sie **nicht** ausgenommen (der weite Eimer ist genau das Netz,
das eine offene POST-Route braucht), vom Origin-Gate ebenfalls nicht: Reports
laufen wie jeder Browser-Aufruf über den Edge, der den Header stempelt.

**Gemeldet wird ausschließlich per `report-uri` — gemessen, nicht vermutet.**
Die naheliegende Fassung deklariert beide Kanäle, `report-uri` für Firefox und
Safari, `report-to` samt `Reporting-Endpoints` für Chromium. Im Browser-Durchgang
vom 2026-09-02 kostete genau das jede Chromium-Meldung: Mit `report-to` in der
Policy ignoriert Chromium `report-uri` (so ist es spezifiziert) und lieferte
dann **gar nichts** — in 200 Sekunden erreichte keine Anfrage den Endpunkt.
Ohne `report-to` kam dieselbe Verletzung in unter einer Sekunde an. Ein Kanal,
der den funktionierenden stilllegt, ohne ihn zu ersetzen, ist schlechter als
keiner; `report-to` kommt zurück, sobald eine Meldung nachweislich über HTTPS
darüber ankommt. Der Endpunkt versteht das Reporting-API-Format trotzdem
schon — dann ändert sich nur der Header.

**Kommt in der Woche nichts an, ist das zuerst zu prüfen** — eine Sonde, die den
Weg eines echten Reports geht:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -X POST \
  -H 'Content-Type: application/csp-report' \
  --data '{"csp-report":{"document-uri":"https://kurrentschrift.ink/","effective-directive":"probe","blocked-uri":"probe"}}' \
  https://api.kurrentschrift.ink/csp-report      # erwartet: 204
```

`403` heißt: Die Cloudflare-Transform-Rule stempelt `X-Origin-Secret` nicht auf
POST-Anfragen (§5). Die Meldungen selbst stehen als `WARNING` im Log der API,
eine Zeile je *verschiedener* Verletzung und danach eine je hundertster
Wiederholung — eine Verletzung, die zehntausendmal feuert, ist ein anderer
Befund als eine, die zweimal feuert, und der mitlaufende Zähler ist die Stelle,
an der man das sieht. Jeder geloggte Wert wird entschärft: Die Felder kommen
aus einer anonymen POST-Anfrage, ein Zeilenumbruch darin würde sonst weitere
Log-Einträge erfinden.

**Scharfschalten ist eine Zeile:** In `app/security-headers.conf` den
Header-Namen `Content-Security-Policy-Report-Only` zu `Content-Security-Policy`
ändern und deployen. `report-uri` bleibt stehen, damit auch danach gemeldet
wird — eine tatsächlich blockierte Quelle will man erst recht erfahren.

**`Cache-Control` auf der Hülle.** `location = /index.html` setzt `no-store`
(seit 2026-09-04; davor `no-cache`). Ohne Header trug die Antwort nur
`Last-Modified`, der Browser cachte die Hülle heuristisch mit ~10 % ihres
Alters und verlangte nach einem Deploy `/assets/`-Hashes, die es nicht mehr
gibt: weiße Seite. Das war der ursprüngliche Anlass.

`no-cache` war danach die bewusst *engere* Wahl gegenüber anyplots `no-store`:
„vor Gebrauch nachfragen", die Kopie bleibt liegen, der gemessene Weg endet in
einem 304 mit null Bytes. Diese Ersparnis gibt es seit dem Nonce nicht mehr —
`sub_filter` schreibt die Hülle pro Antwort um und nginx löscht dabei
`Last-Modified` und `ETag`, sonst könnte ein 304 einen frischen Header über
einen gespeicherten Rumpf mit altem `nonce="…"` legen. Gegengemessen an genau
dieser Konfiguration: kein `Last-Modified` im Kopf, und ein bedingter GET
antwortet 200 mit vollen 17 287 Bytes statt 304. `no-cache` hieß damit „behalte
eine Kopie, die du nie revalidieren kannst, und lade sie trotzdem jedes Mal neu"
— gleiche Bytes wie `no-store`, ohne dessen Zusage. Das ist **nicht** der
Schwesterdatei-Abgleich, vor dem der Kommentar dort gewarnt hat; die Zahlen
stehen als Kommentar daneben.

**Der API-Host hat seine eigenen drei.** `api.kurrentschrift.ink` ist ein
zweiter öffentlicher Host mit eigenen Antworten; `api/security_headers.py`
hängt `nosniff`, `Referrer-Policy` und HSTS an jede von ihnen — auch an die 403
des Origin-Gates und die 429 des Limiters, denn die Middleware sitzt außerhalb
beider. **HSTS muss hier wiederholt werden, gerade WEIL der Apex bewusst ohne
`includeSubDomains` fährt:** Der Header gilt im Browser für den Hostnamen der
Antwort, die ihn trug — der Apex sagt über diesen Host nichts aus, auch nicht
als Geschwister, und dass Cloudflare für beide Namen TLS terminiert, ändert
daran nichts (Copilot-Review, PR #497). `app/nginx.conf` blendet die drei am
Crawler-Proxy per `proxy_hide_header` aus, weil die Seite sie dort selbst setzt.
Eine Antwort erreicht die Middleware nie: Starlette baut
`ServerErrorMiddleware` AUSSERHALB jeder User-Middleware, die 500 einer
unbehandelten Ausnahme ist also schon auf der Leitung. Dafür registriert
`api/main.py` einen `Exception`-Handler — genau die Antwort, die jene
Middleware sendet — und stempelt die Header dort.
Keine CSP dort: `/docs` und `/redoc` laden Swagger UI bzw. ReDoc von
`cdn.jsdelivr.net` und führen Inline-Skripte aus; eine Policy, die streng genug
wäre, um etwas zu taugen, würde die eigene API-Dokumentation zerlegen.

**Keine gemeldete URL wird ganz geloggt.** `/federprobe?text=…` und
`/lesen/vergleichen?text=…` tragen, was der BESUCHER getippt hat — sie sind
zum Teilen gemacht —, und ein Report zitiert `document-uri` wörtlich. Query und
Fragment werden abgeschnitten, bevor irgendetwas geloggt oder gemerkt wird
(`api/routers/csp.py::_path_only`); eine Sicherheitsmaßnahme soll nicht
nebenbei mitschreiben, was Fremde schreiben.

### Reverse-Proxy / Routing

- `/api/*` → der Cloudflare-Worker `kurrentschrift-api-proxy` leitet auf
  `api.kurrentschrift.ink` (FastAPI) um; nginx im App-Container kennt
  kein `/api` (siehe Kopfkommentar `app/nginx.conf`). Weil ein
  Worker-Subrequest die Transform-Rules der eigenen Zone NICHT durchläuft,
  stempelt dieser Worker das Origin-Geheimnis aus §5 selbst — Quelltext und
  Einstellungen: [`infra/cloudflare/`](../../infra/cloudflare/README.md). nginx
  muss nichts mitschicken: sein einziger Ausgang (`@seo_proxy`) geht über
  `api.kurrentschrift.ink` und damit durch den Edge, wo die Regel greift.
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
- `sections/landing/` — `LandingView` + `HeroWritten` (das Markenwort
  engine-first von `WrittenWord` geschrieben, seit 2026-08-27; der
  GLKurrent-Clip-Path-Wisch ist nur noch der Fallback bei echtem Fehler) +
  `Reveal` (Scroll-Reveal; ohne IntersectionObserver und im Druck sofort
  sichtbar).
- `sections/schriftkunde/` — der `/schriftkunde`-Überblick (Grundbegriffe,
  drei Ausgangsschriften mit Specimen, drei Federn, Tinte & Papier,
  Buchstaben-Besonderheiten, Zahlen & Zeichen, Chronologie). Die drei
  Ausgangsschriften stehen bewusst in DREI verschiedenen
  Specimen-Techniken da: Kurrent in der GLKurrent-Schauschrift-Font,
  Sütterlin LIVE von der Engine geschrieben, Offenbacher als
  PD-Specimen unter Nennung seiner Quelle. Seit 2026-08-29 trägt jeder
  Abschnitt eine stabile Sprungmarke (`sections.ts`: `#grundbegriffe`,
  `#buchstaben`, `#entziffern` …, die drei Schrift-Karten `#kurrent` /
  `#suetterlin` / `#offenbacher` — dieselben Ziele, auf die das
  Kennwerte-JSON-LD des Prerenders zeigt) und unter dem Seitenkopf steht
  die Sprungliste „Auf dieser Seite“; die Buchstaben-Besonderheiten
  schreiben die Buchstaben, von denen die Zeile spricht (ſ · s · f, u · n,
  e · n · ä, ſ · z · ß), als `WrittenGlyph`-Streifen live daneben —
  markiertes Specimen auf eigener Fläche mit Antiqua-Beschriftung
  (design-system.md §9), nachgeladen erst in Sichtweite, ausgeblendet
  statt Fehlerkasten, wenn die Engine nicht erreichbar ist. Der Prerender
  setzt dieselben Ids auf seine `<h2>`, dieselbe Liste als `<nav>` und
  nennt die Schriftproben je Zeile nur beim Antiqua-Namen.
- `sections/vergleichen/` — `VergleichenView`, die Lesart-Seite
  (`/lesen/vergleichen`, Website-Audit 2026-08-29, 4/8): die getippte
  Vermutung als `WrittenWord`, darunter die Lesarten aus `lib/lesarten.ts`
  (je Karte genau EIN Buchstabe gegen seinen dokumentierten Verwechsler
  getauscht — n/u, e/n, n/m, i/j, t/l, f/h, ſ/f für ein nicht-finales s,
  Umlaut ↔ Grundbuchstabe, die Versalien-Cluster L/K/R, N/M, B/V —,
  höchstens acht, Klick übernimmt die Lesart), darunter die klassischen
  Verwechsler-Paare als `SpecimenStrip` mit dem unterscheidenden Merkmal.
  Kein HTR: die Person liest, die Engine liefert die Kandidaten
  (Vision Ziel 5, didaktische Hälfte).
- `components/SpecimenStrip/` — Buchstaben „wie geschrieben" als
  markiertes Specimen auf eigener Fläche (design-system.md §9), Antiqua-
  Beschriftung, Klick schreibt neu; die Seite holt die Payloads aller
  Streifen in EINEM Batch (`useSpecimenPayloads`), jeder Streifen montiert
  seine Zellen erst in Sichtweite und zieht sich zurück, wenn nichts
  schreibbar ist. Genutzt von der Schriftkunde (Buchstaben-Besonderheiten)
  und der Lesart-Seite.
- `sections/hub/` — `HubView` (die `/lesen`- und `/schreiben`-Bereichs-Hubs).
- `sections/worksheet/` — `WorksheetView` + `ConfigPanel` + `PreviewSvg`
  (Lineatur-Konfigurator, `/schreiben/uebungsblatt`) + `useWorksheetText`
  (Browser-Hälfte des Übungstexts: eine Komposition je Zeile über den
  geteilten Render-Cache, entprellt, nach Text gemerkt; das Platzieren
  auf die Zeilen ist die reine `lib/uebungstext.ts`).
- `sections/scribe/` — der `/federprobe`-Live-Schreiber (Text →
  serverseitig komponiertes Wort, `WrittenWord`).
- `sections/tafel/` — die `/tafel`-Schreibtafel (Vorlage-Zeilen „wie
  geschrieben") + `useLesetafelPdf` (Browser-Hälfte der druckbaren
  Lesetafel: Render-Payloads im Batch, Originaltafeln per Canvas → JPEG,
  Download). `lib/pdf.ts` ist seit 2026-08-29 ein kleiner
  Dokument-Builder (`PdfDocument` + `ContentStream`: Linien, gefüllte
  Ringe even-odd, Helvetica-Text, JPEG-XObjects; Latin-1-Body, damit die
  xref-Offsets Stringlängen bleiben), auf dem `lineaturePdf` (Übungsblatt)
  und `lib/lesetafel.ts` (Lesetafel: Zeilen-Reflow mit proportionalen
  Breiten wie `WrittenSheet`, Lineatur je Zeile, Seitenumbruch) sitzen —
  clientseitig, weil alle Blätter reine Vektor-/Bild-Inhalte sind — seit
  2026-08-30 auch das inhaltsbewusste Übungsblatt (`lib/uebungstext.ts`,
  `ContentStream.polyline` für die Übergänge); der WeasyPrint-Pfad
  (architektur.md §15) ist damit für das Einzelblatt nicht mehr nötig.
- `sections/quiz/` — `QuizView` + `useQuizEngine` (gesamte Quiz-Logik ohne
  JSX) + Setup/Play/Results-Panels + `QuestionVisual` + `lesefallen.ts`
  (die Regel-Erklärung nach einem Fehlgriff: gezeigte Form gegen geratenen
  Buchstaben, Katalog aus `orthographie-regeln.md`; Sätze in
  `locales/de/quiz.ts` unter `play.rules`).
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
  `AggregateSketch` (die aus `LensStats` herausgelöste
  H1-Aggregat-Zeichnung hinter einem `height`-Prop — die Miniatur im Raster
  ist damit buchstäblich DIESELBE Zeichnung wie die in der Linse) über der
  puren `sketchGeometry.ts` (`isPoint` · `boundsOf` · `pathOf` ·
  `letterSketchAnchors` · `occurrenceChainsOf` · `SKETCH_FRAME`),
  `OccurrenceThumb`, `Panel`/`ViewHeader` (die geteilten Layout-Bausteine)
  und die puren, getesteten `focus.ts` (Subjekt ⇄ URL) + `model.ts`.
- **Registrierungs-Regel für jede „gemessen gegen komponiert"-Zeichnung der
  Werkbank:** SOWOHL die gespeicherte Spur ALS AUCH die Engine-Tinte reiten
  auf der eigenen gemessenen Registrierung der Zeile
  (`measurements.registration_px` + `xh_px`), und zwar über die geteilten,
  unit-getesteten `shell/model.ts::traceFrameOf`/`traceMatrix` — Spur und
  Komposition liegen im identischen Rahmen (Grundlinie = 0, 1 Einheit =
  x-Höhe), es wird also nichts nach Augenmaß ausgerichtet. Die Komposition
  stattdessen an die LINKE CROP-KANTE zu heften setzte sie über die 63
  Sütterlin-Wortzeilen im Median 8,9 px (~0,3 xh) links neben die Tinte und
  ließ damit jede Komposition schlechter aussehen, als sie ist (gemessene
  Registrierung: Median 1,1 px; was an der rechten Kante bleibt, ist der
  echte Breitenunterschied). Die Links-Kanten-Heftung überlebt NUR dort, wo
  es keine nachgefahrene Zeile gibt.
- **Zuschnitt-Regel von `OccurrenceThumb`:** Das gespeicherte
  Vorkommens-Kästchen stammt aus dem M4-Fit und umschließt die
  CENTERLINE — die Tinte läuft also darüber hinaus. Die Luft um den
  Ausschnitt ist deshalb proportional, `max(7, 0.18·√(w·h))` Crop-Pixel
  (der Anteil wird auf dem GEOMETRISCHEN MITTEL genommen, nicht auf der
  langen Seite, weil die gespeicherten Kästchen in beiden Richtungen
  extrem ausfallen), und `THUMB_H` ist 80 statt 64. Ein fester Rand von
  4 px schnitt in den Buchstaben hinein.
- `sections/admin/letters/` — `LetterView` (`/admin/buchstaben`): Übersicht
  über `compare/GlyphComparison` — jeder autorierte Buchstabe als Kachel mit
  VIER Flächen: Original (der Chart-Crop) · Tafel-Form (Variante 0, „wie
  geschrieben") · Laufform (Variante 100) · „Median & Vorkommen" (die
  H1-Aggregat-Skizze: Anker-Median, die Vorkommensketten dünn dahinter,
  MAD-Kreise, die aktuell gerenderte Laufform gestrichelt). Jede Fläche
  trägt einen EHRLICHEN Leerzustand statt einer stillen Lücke („noch keine
  Laufform"; bei der Skizze ein Hinweis, der lädt / keine Hand / kein
  Admin-Read / wirklich kein Aggregat unterscheidet). Die Flächen sind
  `flex: 1 1 150px`, brechen auf dem Telefon also zu 2×2; der
  Überlagerungs-Modus klappt weiterhin die ersten beiden zur
  Rot-Silhouetten-Überlagerung zusammen. Jede Kachel zeigt ihre
  Kennzahlen — Vorkommenszahl, mittleres Fit-Residuum über die
  gespeicherten Vorkommen, den gespeicherten Bildraum-Score und dessen
  Abzüge je Kategorie — plus einen Sortier-Umschalter (Alphabet ·
  Schlechteste zuerst), der das Raster zur Arbeitsliste macht und jede
  Kachel in ihren Buchstaben öffnet. **Das Kostenbudget dieser Übersicht
  ist eine stehende Auflage, kein Zufall:** die Render-Payloads für das
  GANZE Alphabet kommen aus ZWEI Batch-Requests (Variante 0 und Variante
  100 über `/write/glyphs`), die Statistik aus der geteilten
  Werkbank-Datenschicht (gar kein Request), die Scores aus dem EINEN
  admin-gesicherten Batch-Read der Qualität — und das teure
  `/diagnostic` je Glyph, das das Raster früher einmal pro Karte feuerte,
  wird NUR noch für den Überlagerungs-Modus geholt, der seine
  Umriss-Geometrie braucht. Im Detail Tafel-Ausschnitt, Tafel-Form
  neben Laufform, Vorkommen, H1-Statistik, Absprünge — plus
  `LaufformApplyDialog`, die EINE rendernde Aktion des Admins
  (`POST …/aggregates/apply-laufform`): Warnung, Vorschau je Buchstabe
  (Vorkommen · Abstand · „neu"), Bestätigung, danach der Bericht.
- `sections/admin/joins/` — `JoinView` (`/admin/uebergaenge`): Matrix +
  Freitext-Kombination, komponierte Verbindung, H2-Statistik, Vorkommen,
  Paar-Editor.
- `sections/admin/words/` — `WordView` (`/admin/woerter`): Freitext-Wort,
  „woraus es besteht", Belege je Specimen über `WordSpineCard`. Diese Karte
  ist wie eine Buchstaben-Kachel aus ZWEI Flächen gebaut: links die
  MESSUNG (Platten-Crop + die gespeicherte Spur in Grün + je gefittetem
  Buchstaben ein gestricheltes Kästchen und je Übergang ein Punkt, alles
  anklickbar — der Weg in die beiden anderen Ansichten; die Engine-Tinte
  legt sich durchscheinend dazu, wenn der „Überlagern"-Schalter an ist),
  rechts die EIGENE Antwort der Engine für sich allein. Beide werden im
  selben px-pro-Einheit-Maßstab auf derselben Grundlinien-Zeile gezeichnet,
  damit Breite, Schräglage und Rhythmus ohne gedankliches Umskalieren
  vergleichbar sind. Je Karte „Bewerten" (der Admin-`/score`) und
  „Nachfahren" (der Wort-Editor).
- `sections/admin/eigenhand/` — `EigenhandView` (`/admin/eigenhand`): der
  Bestand einer HAND (nicht einer Vorlage) und der Bogendruck. Die Zahlen
  kommen fertig aus `GET /eigenhand/bestand/{hand}` — dieselbe
  Rechenschicht, die das Terminal druckt —, das PDF wird geholt statt
  verlinkt, weil das Admin-Token in der Entwicklung ein HEADER ist, den ein
  `<a href>` nicht mitschickt. Daneben `SetupPanel` (das stehende Setup der
  Hand) und `StripsPanel` (die geschriebenen Streifen): dessen Bilder werden
  aus demselben Grund als Blob geholt und zusätzlich erst auf Klick, weil
  ein Streifen ~350 KB wiegt und zum reservierten Datensatz gehört; die
  Object-URLs werden von Hand wieder freigegeben.
- `sections/admin/chart/`, `setup-wizard/`, `diagnostics/`, `compare/`,
  `pairs/`, `belege/`, `quality/` bleiben die WERKZEUGE, die diese drei
  Ansichten einsetzen (Chart-Editor, Wizard, Diagnose, Vergleichsraster,
  Paar-Editor, Wort-Editor + die pure `registration.ts`, Score-Darstellung)
  — sie haben seit dem Redesign keine eigene Route mehr.
  `quality/scoreParts.tsx` hält `scoreColor`, den Score-Chip und die
  Aufschlüsselung je Kategorie; das liegt AUSSERHALB des Wizards, damit die
  Wizard-Vorschau, das Diagnose-Modal (das die Aufschlüsselung dadurch
  bekam, die es nie zeigte, obwohl sein Payload sie immer trug) und die
  Buchstaben-Übersicht dieselbe Zahl auf dieselbe Weise lesen;
  `setup-wizard/steps/previewParts.tsx` behält nur noch die
  Silhouetten-Überlagerung. Der Tooltip des Chips sagt ausdrücklich, dass
  die gespeicherte Zahl der Score ZUM ZEITPUNKT DES AUTORIERENS ist und
  keine Neubewertung mit der heutigen Metrik.
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
