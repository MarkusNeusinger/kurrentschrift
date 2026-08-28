# Crawler-Richtlinie — Suchmaschinen und KI-Agenten

> **Status (2026-08-28): lebend.** Politik-Quelle zu `app/public/robots.txt`
> (die Datei verweist im Kopf hierher), `llms.txt` und der `robots.txt`
> des API-Hosts (`api/routers/seo.py`); jede Änderung an diesen Dateien
> oder an der Cloudflare-Durchsetzung zieht hier nach. Am 2026-08-28 ist
> die Politik von „Abruf ja, Training nein" auf **offen** umgestellt
> worden — Entscheid und Begründung in [§2](#2--entscheidung), die alte
> Politik steht unter [Verworfen](#verworfen) mit ihrer Rückkehrbedingung.
> Zwei Teile altern anders: §1 ist eine Messung vom 2026-07-25, §4
> beschreibt Dashboard-Schritte, deren Vollzug im Repo nicht nachprüfbar
> ist.

**Kurzfassung:** Die Seite ist für **alle** offen — Suchmaschinen,
KI-Abruf, Zitat **und** Training (`Content-Signal:
search=yes,ai-input=yes,ai-train=yes`). Einzige Ausnahme ist `Bytespider`,
aus Bandbreiten-, nicht aus Prinzipgründen. Der Open-Core-Vorbehalt gilt
unverändert — er liegt aber nicht in der `robots.txt`, sondern am
Auth-Gate der API: Was reserviert ist (Duktus-Templates, Vorkommen,
Bboxen, Paar-Overrides, Hände, Eigenhand-Streifen), gibt die API ohne
Admin-Zugang nicht heraus ([§3](#3--was-im-repo-steht)).

## 1 · Befund (2026-07-25)

Die Messung, aus der die erste Politik hervorging — gemessen gegen die
Live-Zone:

| Anfrage | Ergebnis |
|---|---|
| `ClaudeBot`, `Claude-User`, `Claude-SearchBot` auf `/` | **403** „Your request was blocked.“ (Cloudflare) |
| `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot` auf `/` | **403** |
| Dieselben UAs auf `/llms.txt` | **403** |
| Dieselben UAs auf `api.kurrentschrift.ink` | **403** (die Zone ist vollständig erfasst) |
| `Googlebot` auf `/` und `/llms.txt` | 200 |

Zwei Dinge daran waren nicht beabsichtigt:

1. **`llms.txt` war für sein eigenes Publikum unerreichbar.** Die Datei
   ist genau für Agenten geschrieben — und genau die bekamen 403.
2. **Es trifft nutzergesteuerte Abrufe.** `Claude-User` und
   `ChatGPT-User` feuern, wenn ein *Mensch* seinem Assistenten sagt
   „schau dir kurrentschrift.ink an“. Das sind Besucher mit Werkzeug,
   keine Scraper.

Zusätzlich blockte die Zone `api.kurrentschrift.ink` mit — die in
`llms.txt` beworbene offene Lese-API war für Agenten tot.

Ursache: Cloudflares **AI Crawl Control**. Sie stellt der ausgelieferten
`robots.txt` einen verwalteten Block voran (`Disallow: /` für ClaudeBot,
GPTBot, CCBot, Google-Extended, Amazonbot, Applebot-Extended, Bytespider,
meta-externalagent) **und** beantwortet dieselben UAs an der Kante mit
403. Die Datei im Repo wurde dadurch überstimmt.

## 2 · Entscheidung

**Entscheid (2026-08-28, ersetzt den vom 2026-07-25):** alles offen.
Abruf, Zitat, Suchindexierung und Modelltraining sind jedem Betreiber
erlaubt.

| Gruppe | Agenten | Politik |
|---|---|---|
| Alles | Suchmaschinen, KI-Assistenten, ihre Index- und Trainings-Crawler, Social- und Link-Vorschauen | **erlaubt** |
| Bandbreiten-Ausnahme | `Bytespider` | abgelehnt |
| App-Interna | `/admin` für alle Agenten | abgelehnt |

Begründung:

- **Der Moat ist die Datenbank, nicht die Webseite.** Was das README
  vorbehält — die autorierten Duktus-Templates, Laufformen, Vorkommen,
  Bboxen, Paar-Overrides, Hände, die Eigenhand-Streifen — liegt in der DB
  und ist über die API nur mit Admin-Zugang lesbar; seit 2026-08-28
  lückenlos, denn `tests/test_api_public_surface.py` klassifiziert jede
  GET-Route als öffentlich oder reserviert und erzwingt für reservierte
  den 401 ([`quellen-und-rechte.md`](quellen-und-rechte.md) §5). Der
  Seitentext (Schriftkunde, Hubs, Impressum) und der MIT-Code sind zum
  Gelesen- und Weiterverwendetwerden da; ein Trainings-Verbot auf
  HTML-Text schützte nichts, was das Auth-Gate nicht ohnehin schützt —
  kostete aber Reichweite.
- **`Google-Extended` ist ein Alles-oder-nichts-Token.** Es steuert
  Gemini-*Grounding und Training zusammen* (gegen Googles
  Crawler-Dokumentation geprüft, es gibt keine feinere Stellschraube).
  Es abzulehnen hielt kurrentschrift.ink aus Gemini-Antworten komplett
  heraus — das Gegenteil dessen, was eine Seite will, deren Publikum
  (Familienforschung, Unterricht, Archivarbeit) seine Frage zunehmend
  einem Assistenten stellt. `Applebot-Extended` ist ein reines
  Trainings-Token (Abruf und Siri-Antworten laufen über `Applebot`) und
  fällt mit der Öffnung ebenfalls.
- **Gleichlauf mit anyplot.** Das Schwesterprojekt hat denselben Schritt
  am 2026-08-18 gemacht (dort `docs/reference/seo.md`, „AI crawler
  policy"). Politik und Dateiform sind bewusst deckungsgleich, damit eine
  Änderung auf der einen Seite 1:1 auf die andere kopiert werden kann —
  dasselbe gilt für die Crawler-Liste, sobald der Prerender-Pfad (§3)
  steht.

`Bytespider` ist die eine Ausnahme und operativ, nicht prinzipiell
begründet: dokumentiert als robots.txt-ignorierend und weit aggressiver,
als eine kleine Seite sinnvoll bedienen kann. Die Gruppe nennt die
Absicht; Cloudflare setzt sie durch. Ändert sich das Verhalten, kann die
Gruppe fallen.

**Die eine abweichende Zeile liegt auf dem API-Host.**
`api.kurrentschrift.ink/robots.txt` (`api/routers/seo.py`) erlaubt alles
— `Allow: /`, keine `Disallow`-Zeile, denn reservierte Daten sind durch
Auth gesperrt, nicht durch robots; eine robots-Sperre hielte nur die
spec-treuen Assistenten von `/docs` und `/openapi.json` fern (die
Lehre aus anyplots AI-Access-Audit vom 2026-08-19) — trägt aber
`ai-train=no`: Die komponierte Geometrie der öffentlichen
`/write`-Endpunkte ist aus dem vorbehaltenen Bestand abgeleitet,
Produkt-Oberfläche zum Abrufen und Zitieren, kein Trainingsmaterial.

## 3 · Was im Repo steht

`app/public/robots.txt` trägt die Richtlinie **vollständig selbst**:
Content-Signals, die eine abgelehnte Gruppe, die `*`-Gruppe. Das ist
Absicht — so gilt sie auch dann, wenn Cloudflares verwalteter Block
abgeschaltet wird (mit ihm verschwindet sonst auch die
Content-Signal-Zeile). Die Datei ist damit die Quelle der Wahrheit, das
Dashboard nur die Durchsetzung.

Drei Details der Datei sind Absicht und sollten beim Bearbeiten nicht
„aufgeräumt“ werden:

- Die `Content-Signal`-Zeile steht in **jeder** Gruppe, auch in der
  ablehnenden. Ein Crawler liest nur die Gruppe, die auf ihn passt — ein
  einmal unter `User-agent: *` erklärtes Signal erreichte keinen
  namentlich genannten Agenten.
- Die **namentliche Gruppe steht vor** der `*`-Gruppe. Ein
  spezifikationstreuer Crawler wählt unabhängig von der Reihenfolge die
  spezifischste Gruppe; einfachere Parser nehmen die erste passende — mit
  dem Wildcard oben läsen sie `Allow: /` und kämen bei der ablehnenden
  Gruppe nie an.
- Innerhalb einer Gruppe steht **`Disallow:` vor `Allow: /`**. Dieselbe
  Logik: Bei umgekehrter Reihenfolge lässt ein First-Match-Parser `/admin`
  durch (nachgestellt mit Pythons `urllib.robotparser`, der genau so
  arbeitet), während ein Longest-Match-Parser richtig sperrt.

Die Content-Signal-Zeile kennt genau drei Token — `search`, `ai-input`,
`ai-train` (je `yes`/`no`); ein weiteres Token wie das früher mitgeführte
`use=reference` ist ungültig und kann einen strengen Parser die ganze
Zeile verwerfen lassen (gegen contentsignals.org geprüft, 2026-08-27).

`api/routers/seo.py` liefert die `robots.txt` des API-Hosts (§2, letzter
Absatz). Der technische Vorbehalt selbst — welche Reads öffentlich sind
und welche den Admin-Zugang verlangen — steht mit vollständiger Liste in
[`quellen-und-rechte.md`](quellen-und-rechte.md) §5 und wird durch
`tests/test_api_public_surface.py` festgehalten.

`app/public/llms.txt` bleibt die inhaltliche Oberfläche für Agenten —
der Wegweiser, nicht der Text. Den Text bekommen sie seit 2026-08-28 über
den **Prerender-Pfad** nach anyplots Muster: Die `$is_bot`-Map in
`app/nginx.conf` (wortgleich mit anyplot — Suchmaschinen, KI-Crawler,
nutzergesteuerte Fetcher, Social-/Messenger-Vorschauen; eine Änderung
wird in beiden Dateien im selben Zug gemacht) schickt einen gemappten UA
an `api.kurrentschrift.ink/seo-proxy/{route}`, wo die zur Build-Zeit aus
dem Locale-Katalog gerenderte Seite der Route liegt (`app/prerender/`,
Details in [`frontend-stack.md`](frontend-stack.md) §6); Menschen
bekommen unter derselben URL die SPA. Die Map entscheidet nur, WAS ein
Agent bekommt, nie OB er darf — das bleibt `robots.txt` plus Cloudflare
(§2, §4); ein nicht gemappter Agent ist damit nicht abgelehnt, er sieht
nur die Hülle. Der Markdown-Spiegel der Schriftkunde (2026-08-27, eine
Seite als `/schriftkunde.md`) war der Vorläufer und ist in diesem Pfad
aufgegangen. Weil der Pfad für Menschen unsichtbar ist, prüft ihn
`.github/workflows/bot-serving-check.yml` täglich gegen den
Cloud-Run-Origin — anyplots Alarm, der dort vier stille Wochen mit 502
für jeden Crawler beendet hat.

**Auffindbarkeit (2026-08-28):** Ein Sitzungsprotokoll eines Assistenten
vom selben Tag hat gezeigt, dass die ganze Kette an der ersten Stufe
scheitern kann: Die Fetch-Werkzeuge der Assistenten erlauben häufig nur
URLs, die zuvor **im Text einer abgerufenen Seite oder eines
Suchergebnisses standen** — eine selbst zusammengesetzte URL, ein mit
`…` abgekürzter Pfad im README oder die bloße `/llms.txt`-Konvention
genügen nicht, und die API steht in keinem Suchindex. Deshalb steht die
vollständige Beispiel-URL des Wort-Renders
(`…/write/word.svg?text=lesen`, samt dem Hinweis, dass `text` frei ist)
ausgeschrieben im Prerender-Text von `/federprobe` und `/schriftkunde`
(`apiExampleLine` in `prerender.ts`; `/tafel` trägt die vollständige
Rezeptliste), `llms.txt` ist per Voll-URL aus dem Footer jeder
**Prerender**-Seite verlinkt, und beide `robots.txt` (Site und API-Host)
nennen sie neben der `Sitemap:`-Zeile. Im SPA-Footer, den Menschen
sehen, steht der Link bewusst **nicht** (Entscheid 2026-08-28): Die
Datei ist für Agenten, nicht für Besucher — und die erreichen sie
vollständig über den Prerender-Pfad, denn genau die gemappten Agenten
sind ihr Publikum. Festgehalten von
`prerender.test.ts`, `seoCoverage.test.ts` und `test_api_http.py`; ob
die Prüfung der Werkzeuge auf die exakte URL oder auf Host+Pfad geht,
ist offen — darum steht der Frei-Parameter-Hinweis direkt neben dem
Beispiel.

Ein zweites Protokoll (Grok, ebenfalls 2026-08-28) hat die verbleibende
Stufe gezeigt: Ein Agent, dessen User-Agent **nicht in der
`$is_bot`-Map** steht, bekommt die leere App-Hülle („insufficient
relevant content") — und damit war auch die beste Prerender-Fassung
unsichtbar. Antwort darauf, in Wirkungsreihenfolge: (1) Die **Hülle
selbst** (`app/index.html`) trägt jetzt auf jeder Route einen
`<link rel="alternate" type="text/plain" href="/llms.txt">` im Head und
einen `<noscript>`-Block mit der Voll-URL der llms.txt, der
ausgeschriebenen Beispiel-URL des Wort-Renders samt
Frei-Parameter-Hinweis und den API-Doku-Links — unsichtbar in der
gerenderten App, aber im ersten Response jedes Clients (versteckter
indexierbarer Text jenseits von `<noscript>` wurde verworfen:
Cloaking-Risiko). (2) Geratene Pfade antworten statt 404 mit
Weiterleitung auf die kanonische Datei: `/.well-known/llms.txt` auf der
Site (nginx, 302) und `/llms.txt` auf dem API-Host
(`api/routers/seo.py`, 302). (3) `robots.txt` nennt llms.txt und
OpenAPI zusätzlich in zwei knappen Zeilen **ganz oben**, für Leser, die
nur den Dateianfang ernst nehmen. Die UA-Map hatte `~*grok` zu diesem
Zeitpunkt bereits; ein Sitemap-Eintrag für llms.txt wurde verworfen
(die Sitemap listet exakt die öffentlichen Seiten, von
`seoCoverage.test.ts` festgehalten). Gepinnt von `seoCoverage.test.ts`
(Hülle) und `test_api_http.py`/`test_api_public_surface.py`
(API-Redirect).

Und weil die Abrufe dort sichtbar sind, werden sie dort gezählt: Jeder
`/seo-proxy`-Abruf eines bekannten Agenten landet als Event `bot_fetch`
auf der **zweiten Plausible-Site `bots.kurrentschrift.ink`** — nie auf
der Besucher-Site — mit Anbieter (`assistant`), Grund (`kind`:
`user_directed` ist ein Mensch, der seinen Assistenten bat, die Seite zu
öffnen; `index`/`search`/`training` sind Korpus-Bau), Pfad und Status
(Glossar „Bot-Site", [`frontend-stack.md`](frontend-stack.md) §6). Das
ist die Messung zur Politik: ob die Öffnung (§2) Leser bringt, steht
in `kind=user_directed`, nicht in der Besucherstatistik.

## 4 · Was in Cloudflare zu tun ist

Zone `kurrentschrift.ink` → **AI Crawl Control** (bei älteren Konten:
Security → Bots → „AI Scrapers and Crawlers“). Ziel ist der Stand, den
anyplot am 2026-08-18 für seine Zone verifiziert hat:

1. **Alle Kategorien auf Allow** — *AI Search*, *AI Assistant* **und**
   *AI Crawler* (Training). Der pauschale Block wird aufgehoben. Wo nur
   eine Ein/Aus-Option existiert: ausschalten.
2. **An der Kante blockiert bleiben nur:** `Bytespider`, `TikTok Spider`
   (beide ByteDance — der erste dokumentiert robots.txt-ignorierend, der
   zweite teilt den Betreiber), `Anchor Browser`, `Novellum AI Crawl`,
   `Timpibot` (für die drei letzten existiert keine Herstellerdoku ihres
   Crawl-Verhaltens; Regeltreue ist unverifiziert, nicht widerlegt —
   neu bewerten, wenn sich das ändert).
3. **Verwaltete `robots.txt` abschalten** — die Repo-Datei enthält die
   Content-Signals bereits, und zwei Quellen für dieselbe Aussage
   driften garantiert auseinander. Die Live-Datei muss byte-identisch
   mit der Repo-Datei sein.
4. Prüfen, dass `api.kurrentschrift.ink` mit erfasst ist: Die Regel
   greift zonenweit; die öffentliche Lese-API soll für die erlaubten
   Agenten erreichbar sein (alles Reservierte ist ohnehin durch
   `require_admin` geschützt).

Die Kante kann strenger sein als die Datei und beantwortet blockierte
Agenten mit 403, egal was in `robots.txt` steht — **eine in der
`robots.txt` erteilte Erlaubnis, die das Dashboard weiter blockt, ist
eine veröffentlichte Unwahrheit.** Beides in Deckung halten.

Danach prüfen:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -A "Mozilla/5.0 (compatible; GPTBot/1.4; +https://openai.com/gptbot)" \
  https://kurrentschrift.ink/                               # erwartet 200
curl -s -o /dev/null -w '%{http_code}\n' \
  -A "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)" \
  https://kurrentschrift.ink/llms.txt                       # erwartet 200
curl -s -o /dev/null -w '%{http_code}\n' \
  -A "Mozilla/5.0 (compatible; Bytespider)" \
  https://kurrentschrift.ink/                               # erwartet 403
curl -s https://kurrentschrift.ink/robots.txt | diff - app/public/robots.txt   # ohne verwalteten Block: leer
curl -s https://api.kurrentschrift.ink/robots.txt          # Allow: / + ai-train=no
```

## Verworfen

- **Alles blocken (Status quo bis 2026-07-25).** Kostet die
  Auffindbarkeit im wachsenden Antwort-Kanal und trifft nutzergesteuerte
  Abrufe eigener Besucher.
- **Abruf ja, Training nein (Politik vom 2026-07-25 bis 2026-08-28).**
  Namentliche Erlaubnisgruppe (ClaudeBot, Claude-User, Claude-SearchBot,
  OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User), abgelehnte
  Trainings-Sammler (GPTBot, CCBot, Bytespider, Amazonbot,
  meta-externalagent) und Opt-out-Token (Google-Extended,
  Applebot-Extended), überall `ai-train=no` als ausdrücklicher
  Nutzungsvorbehalt nach Art. 4 DSM-Richtlinie 2019/790 bzw. § 44b UrhG.
  Verworfen am 2026-08-28 aus den Gründen in §2: Der Vorbehalt schützte
  auf HTML-Text nichts, was das Auth-Gate der API nicht ohnehin schützt,
  und das Alles-oder-nichts-Token `Google-Extended` hielt die Seite aus
  Gemini-Antworten heraus. **Rückkehrbedingung:** Sollte je Seitentext
  selbst zum reservierten Bestand werden (etwa ein eigenes Lehrwerk auf
  der Seite), kommt die Gruppe samt der Vorbehaltsformel zurück — dann
  aber mit `Google-Extended` weiterhin erlaubt, weil sein Preis (kein
  Gemini-Grounding) den Nutzen des Trainings-Vorbehalts übersteigt.
- **Nur `robots.txt` im Repo pflegen und den verwalteten Block anlassen.**
  Wurde genau deshalb aufgegeben: Die ausgelieferte Datei sagte das
  Gegenteil der Repo-Datei, und der 403 hätte ohnehin gewonnen.
- **`Allow`-Zeilen für die KI-Agenten hinter dem verwalteten Block.**
  Zwei widersprüchliche Gruppen für denselben UA in einer Datei; das
  Ergebnis hängt an der Merge-Regel des jeweiligen Crawlers. Die
  Richtlinie wird stattdessen an einer Stelle erklärt (§3) und an einer
  Stelle durchgesetzt (§4).
- **Die API per robots.txt sperren, um den Bestand zu schützen.** Eine
  robots-Zeile hält nur die spec-treuen Assistenten fern — genau die
  Clients, die `llms.txt` zu `/docs` und `/openapi.json` einlädt — und
  keinen Sammler, der den Bestand wollte. Der Schutz ist das Auth-Gate;
  robots.txt auf dem API-Host erklärt nur den Trainings-Vorbehalt für die
  `/write`-Renders.
