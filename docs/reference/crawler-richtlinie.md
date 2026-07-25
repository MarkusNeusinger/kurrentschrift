# Crawler-Richtlinie — Suchmaschinen und KI-Agenten

**Status:** Entschieden (2026-07-25). Die Repo-Seite ist umgesetzt; das
Durchsetzen liegt in der Cloudflare-Zone `kurrentschrift.ink` und ist
eine Dashboard-Handlung (siehe [§4](#4--was-in-cloudflare-zu-tun-ist)).

**Kurzfassung:** KI-Agenten, die **abrufen und zitieren**, sind
willkommen; Sammler, die **nur für das Training** einsammeln, sind
abgelehnt. Der Nutzungsvorbehalt für das Training bleibt ausdrücklich
erklärt (`Content-Signal: ai-train=no`).

## 1 · Befund

Gemessen am 2026-07-25 gegen die Live-Zone:

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

| Gruppe | Agenten | Politik |
|---|---|---|
| Abruf · Zitat · nutzergesteuert | `ClaudeBot`, `Claude-User`, `Claude-SearchBot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `Perplexity-User` | **erlaubt** |
| Trainings-Sammler | `GPTBot`, `CCBot`, `Bytespider`, `Amazonbot`, `meta-externalagent` | abgelehnt |
| Opt-out-Token (Anbieter crawlt unter anderem UA) | `Google-Extended`, `Applebot-Extended` | abgelehnt |

Begründung:

- **Auffindbarkeit.** Das Publikum dieser Seite — Familienforschung,
  Schulunterricht, Archivarbeit — fragt seine Frage zunehmend einem
  Assistenten („wie lese ich Sütterlin?“). Wer dort nicht zitiert werden
  kann, existiert für diesen Kanal nicht. Für eine deutschsprachige
  Nische ist das der wachsende Entdeckungsweg, nicht ein Randfall.
- **Der Vorbehalt bleibt bestehen.** `ai-train=no` ist der rechtlich
  tragende Teil (ausdrücklicher Nutzungsvorbehalt nach Art. 4
  DSM-Richtlinie 2019/790 bzw. §44b UrhG) und gilt unabhängig davon, ob
  zusätzlich ein 403 ausgeliefert wird.
- **Die geschützten Daten liegen nicht im HTML.** Die kuratierten
  Schriftdaten (Duktus, Vorlagen, Statistik) kommen aus der API und sind
  gesondert vorbehalten (`README`, `/llms.txt`,
  [`quellen-und-rechte.md`](quellen-und-rechte.md)); die öffentlichen
  Seiten tragen erklärenden Text, dessen Zitierbarkeit erwünscht ist.

`GPTBot` ist der bewusste Grenzfall: Es ist OpenAIs **Trainings**-Crawler
und steht deshalb bei den abgelehnten Gruppen, während ChatGPTs
Abruf-Pfad (`OAI-SearchBot`, `ChatGPT-User`) offen bleibt. Die Rollen der
Anbieter-UAs verschieben sich — vor einer Änderung die aktuelle
Kategorisierung in Cloudflares AI Crawl Control prüfen; diese Liste ist
eine Momentaufnahme, keine dauerhaft gültige Wahrheit.

## 3 · Was im Repo steht

`app/public/robots.txt` trägt die Richtlinie **vollständig selbst**:
Content-Signals, die willkommene Gruppe, die abgelehnten Sammler. Das ist
Absicht — so gilt sie auch dann, wenn Cloudflares verwalteter Block
abgeschaltet wird (mit ihm verschwindet sonst auch die Content-Signal-Zeile).
Die Datei ist damit die Quelle der Wahrheit, das Dashboard nur die
Durchsetzung.

Zwei Details der Datei sind Absicht und sollten beim Bearbeiten nicht
„aufgeräumt“ werden:

- Die `Content-Signal`-Zeile steht in **jeder** Gruppe, auch in den
  ablehnenden. Ein Crawler liest nur die Gruppe, die auf ihn passt — ein
  einmal unter `User-agent: *` erklärter Vorbehalt erreichte keinen
  namentlich genannten Agenten, am wenigsten die Trainings-Sammler, an die
  er sich richtet.
- Die **namentlichen Gruppen stehen vor** der `*`-Gruppe. Ein
  spezifikationstreuer Crawler wählt unabhängig von der Reihenfolge die
  spezifischste Gruppe; einfachere Parser nehmen die erste passende — mit
  dem Wildcard oben läsen die `Allow: /` und kämen bei den ablehnenden
  Gruppen nie an.
- Innerhalb einer Gruppe steht **`Disallow:` vor `Allow: /`**. Dieselbe
  Logik: Bei umgekehrter Reihenfolge lässt ein First-Match-Parser `/admin`
  durch (nachgestellt mit Pythons `urllib.robotparser`, der genau so
  arbeitet), während ein Longest-Match-Parser richtig sperrt.

`app/public/llms.txt` bleibt die inhaltliche Oberfläche für Agenten. Das
ist hier wichtiger als bei einer üblichen Seite: Die SPA liefert ohne
JavaScript nur eine ~5,8 KB große Hülle mit Titel und Description
(kein Prerendering, anders als beim Schwesterprojekt anyplot). Agenten,
die kein JS ausführen, sehen also die Hülle **plus** `llms.txt` — und
nichts sonst. Wenn KI-Sichtbarkeit später mehr wert sein soll als heute,
ist ein Prerender-Pfad (Bot-UA → serverseitig gerendertes HTML) der
nächste Schritt, nicht eine weitere robots.txt-Zeile.

## 4 · Was in Cloudflare zu tun ist

Zone `kurrentschrift.ink` → **AI Crawl Control** (bei älteren Konten:
Security → Bots → „AI Scrapers and Crawlers“):

1. Den pauschalen Block **aufheben** und stattdessen pro Kategorie
   setzen: *AI Search* und *AI Assistant* → **Allow**, *AI Crawler*
   (Training) → **Block**. Wo nur eine Ein/Aus-Option existiert:
   ausschalten und die Erklärung über `robots.txt` (§3) tragen lassen.
2. Verwaltete `robots.txt` **abschalten** — die Repo-Datei enthält die
   Content-Signals bereits, und zwei Quellen für dieselbe Aussage
   driften garantiert auseinander. (Alternative: anlassen und
   akzeptieren, dass die Live-Datei strenger ist als die im Repo.)
3. Prüfen, dass `api.kurrentschrift.ink` mit erfasst ist: Die Regel
   greift zonenweit; die öffentliche Lese-API soll für die erlaubten
   Agenten erreichbar sein (Schreibpfade sind ohnehin durch
   `require_admin` geschützt).

Danach prüfen:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -A "Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)" \
  https://kurrentschrift.ink/llms.txt                       # erwartet 200
curl -s -o /dev/null -w '%{http_code}\n' \
  -A "Mozilla/5.0 (compatible; CCBot/2.0; +https://commoncrawl.org/faq/)" \
  https://kurrentschrift.ink/                               # erwartet 403
curl -s https://kurrentschrift.ink/robots.txt | head -25    # ohne verwalteten Block: die Repo-Datei
```

## Verworfen

- **Alles blocken (Status quo).** Kostet die Auffindbarkeit im
  wachsenden Antwort-Kanal und trifft nutzergesteuerte Abrufe eigener
  Besucher, ohne den Trainingsvorbehalt stärker zu machen, als
  `ai-train=no` es ohnehin tut.
- **Alles freigeben, inklusive Trainings-Sammler.** Widerspräche dem
  Datenvorbehalt für die kuratierten Schriftdaten; `CCBot` &Co. liefern
  keinen Rückverweis, also keinen Gegenwert.
- **Nur `robots.txt` im Repo pflegen und den verwalteten Block anlassen.**
  Wurde genau deshalb aufgegeben: Die ausgelieferte Datei sagte das
  Gegenteil der Repo-Datei, und der 403 hätte ohnehin gewonnen.
- **`Allow`-Zeilen für die KI-Agenten hinter dem verwalteten Block.**
  Zwei widersprüchliche Gruppen für denselben UA in einer Datei; das
  Ergebnis hängt an der Merge-Regel des jeweiligen Crawlers. Die
  Richtlinie wird stattdessen an einer Stelle erklärt (§3) und an einer
  Stelle durchgesetzt (§4).
