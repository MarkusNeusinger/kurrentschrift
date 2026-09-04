# Dokument-Status und Nachzieh-Pflichten

> **Status (2026-09-04): lebend.** Das Lifecycle-Vokabular der Docs und
> die Tabelle, welche Datei bei welcher Code-Änderung nachgezogen wird.
> Stand 2026-09-04 aus [`index.md`](index.md) hierher gezogen, damit die
> Startseite eine Karte bleibt und nicht zugleich das Pflichtenheft ist —
> Wort für Wort dieselbe Tabelle. Nachzieh-Anlass: jedes Doc, dessen
> Status auf `lebend` wechselt (Zeile ergänzen) oder das es verlässt
> (Zeile entfernen), und jede geänderte Nachzieh-Bedingung.

Jedes Doc unter `docs/` trägt seit 2026-08-03 direkt unter der Überschrift
einen Status-Blockquote nach demselben Muster
(`> **Status (JJJJ-MM-TT): <status>.** …`), damit ein Leser ohne Archäologie
sieht, ob er einen Plan, ein Protokoll oder eine Beschreibung des laufenden
Systems vor sich hat. Das Vokabular ist bewusst klein: **bindend** =
entschieden, wird nur durch eine neue Entscheidung geändert (die
Verworfen-Listen bleiben geschlossen); **lebend** = beschreibt den Ist-Stand
des Codes und trägt eine benannte Nachzieh-Pflicht; **teil-umgesetzt** = ein
Teil ist gebaut, der Rest ist ausdrücklich Zukunft (der Kopf sagt, welcher);
**umgesetzt-historisch** = vollständig abgearbeitet oder durch eine andere
Lösung abgelöst, also Entscheidungs- und Messprotokoll statt Arbeitsplan;
**offen** = nichts davon ist gebaut; **Befund-Journal** = datierte
Momentaufnahme, die nie fortgeschrieben, sondern nur durch eine neue Runde
abgelöst wird; **statisch** = quellenbelegtes Nachschlagematerial, das dem
Code nicht folgt. Die `research/`-Notizen folgen dem Code ebenfalls nie
und tragen je nach Natur `offen` (eine Idee mit Bauoption) oder
`Befund-Journal` (eine Literatur-Momentaufnahme). Die neun
`schriftkunde/`-Faktenblätter sind durchweg
statisch und tragen keinen eigenen Kopf — sie führen ihr „Stand:“-Datum
ohnehin in den ersten Zeilen; einzige Ausnahme ist
[`orthographie-regeln.md`](schriftkunde/orthographie-regeln.md), weil dort
Regeln stehen, die noch nicht implementiert sind.

Ein Doc über rund 10 000 Token trägt zusätzlich einen **Stand-Block**: ein
datierter Blockquote von höchstens 40 Zeilen, der sagt, was gilt, was offen
ist und wo der Rest steht — jeder Satz mit dem Anker seiner Quelle. Er ist
die Antwort auf die Frage, die eine KI-Sitzung als erste stellt, ohne dass
sie dafür die ganze Datei laden muss.

## Lebende Dokumente und ihr Nachzieh-Anlass

| Doc | Nachziehen bei |
|---|---|
| [`index.md`](index.md) | jedem neuen, umbenannten oder gelöschten Doc unter `docs/` (eine Kartenzeile je Datei) sowie beim Kopf-Absatz „Stand“, sobald eine Schicht live geht |
| [`dokument-status.md`](dokument-status.md) | jedem Doc, dessen Status auf `lebend` wechselt oder es verlässt, und jeder geänderten Nachzieh-Bedingung |
| [`contributing.md`](contributing.md) | neuer öffentlicher Route in `app/src/routes/paths.ts`, gefallenem MVP-Gate (`architektur.md` §8) oder Öffnung für externe PRs — betrifft Absatz 1 und „Not yet useful“ |
| [`concepts/vom-scan-zum-schreiben.md`](concepts/vom-scan-zum-schreiben.md) | jeder neuen Stufe im Datenfluss, jeder neuen Admin-Fläche und jeder geschlossenen Lücke — insbesondere der Lücken-Liste am Ende, wenn eines der dort verlinkten Issues (#270–#274) schließt |
| [`concepts/design-system.md`](concepts/design-system.md) | Änderungen an `app/src/styles/paper.ts`, `theme/typography.ts`, `components/PageContainer · Prose · PageHeader · HeaderBar · PublicHeader · PublicFooter`, an der Werkbank-Kopfleiste (`sections/admin/shell/AdminHeader`) oder an der öffentlichen Routen-/Bereichsstruktur (`routes/paths.ts`) |
| [`reference/glossar.md`](reference/glossar.md) | jedem Doc und jedem PR, der einen neuen Fachbegriff, eine neue Kennzahl oder eine neue Redewendung prägt — der Eintrag entsteht im selben PR (Regel auch in `CLAUDE.md` § „Working guardrails“, `.github/copilot-instructions.md` und den Skills `/write-docs` + `/open-pr`) |
| [`reference/kurzglossar.md`](reference/kurzglossar.md) | einem Begriff, der neu in Code-Identifiern, `CLAUDE.md`, den Skills oder PR-Beschreibungen auftaucht (Kurzeintrag ergänzen) — oder den keine dieser Quellen mehr nennt (Kurzeintrag entfernen); der volle Eintrag bleibt in `glossar.md` |
| [`reference/write-api.md`](reference/write-api.md) | jeder Änderung an einer `/write/*`-Route (`api/routers/write.py` inkl. `compose_word_payload`), an `core/shaping.py`, `core/compose.py`, `core/pipeline.py::render_payload_for_template`, `api/rendering.py` oder den Cache-Headern in `api/http.py` |
| [`reference/qualitaetsmetrik.md`](reference/qualitaetsmetrik.md) | jeder Änderung an `core/quality.py`, `core/quality_suetterlin.py`, `core/geometry.py`, `core/word_metric.py` und jedem Re-Baseline der eingefrorenen Fixtures; die aktuellen Headlines im Status-Blockquote bleiben hier, das Journal der Läufe steht seit 2026-09-04 in `reference/messjournal.md` |
| [`reference/messjournal.md`](reference/messjournal.md) | jedem Bench-/Loop-/Folger-Lauf, der eine Zahl oder ein Verdikt hervorbringt (neuer datierter §14-Abschnitt, ans Dateiende — §14 ist die einzige Sektion dieser Datei). **Im selben PR:** die Zeile in der Registertabelle am Kopf von §14, eine bewegte Headline zusätzlich ihre Zeile im Headline-Ledger daneben (mit `exported_at` und Digest der Fixture-Wurzel) — erzwungen von `uv run python -m tools.docs_register check` (CI-Job „Docs-Register“) |
| [`reference/messjournal-archiv.md`](reference/messjournal-archiv.md) | jedem Abschnitt, dessen Arm abgeschlossen ist (Verdikt gebucht · Rettungswege eingetragen · ≥ 4 Wochen unberührt): Abschnitt Wort für Wort herüberziehen, Registerzeile im Journal auf `messjournal-archiv.md#anker` umstellen und im selben PR die dateibenannten Zitate (`messjournal.md §14 …`) dieses Abschnitts auf die Archivdatei nachziehen — der Rezept-Grep steht im Kopf des Archivs |
| [`reference/menschliche-bewertung.md`](reference/menschliche-bewertung.md) | jeder Änderung am Instrument `tools/humanbench` (Kategorien in `page.py::CATEGORIES`, Stichproben- und Wiederholungsregeln in `build.py`, Darstellung, neue Modi, CLI) und jeder Runde, deren Aufbau vom beschriebenen Verfahren abweicht — die Befunde selbst gehören nach `reference/messjournal.md` |
| [`reference/frontend-stack.md`](reference/frontend-stack.md) | Stack-Versionen (`app/package.json`), Routenkarte (`app/src/routes/paths.ts`), Build/Deploy (`app/cloudbuild.yaml`, `api/cloudbuild.yaml`, `app/Dockerfile`, `app/nginx.conf`, Cloud-Run-Parameter), Auslieferungs-Header (`app/security-headers.conf`, `api/security_headers.py`, `api/routers/csp.py`), Admin-Gate (`api/auth.py`, `core/config.py`, Cloudflare Access) oder Origin-Gate (`api/origin_gate.py`, `infra/cloudflare/` — der Apex-Worker, an dessen Konfiguration §5 hängt) |
| [`reference/werkzeuge.md`](reference/werkzeuge.md) | jedem neuen, umbenannten oder entfernten Verzeichnis/Einstiegsskript unter `tools/` und jeder geänderten CLI (Flags, Modulpfade, `viz`-Extra, `--live`) |
| [`reference/quiz-wortbank.md`](reference/quiz-wortbank.md) | Änderungen an `tools/quizgen/corpus.py`/`similarity.py`/`build.py` (inkl. Neuberechnung von `quiz_words.json` → Wortzahl und Era-Verteilung im Kopf nachziehen), am TS-Zwilling `app/src/sections/quiz/wordBank.ts`/`useQuizEngine.ts` und bei jeder Re-Seed-Migration nach dem Muster `0011_quiz_words_reseed.py` |
| [`reference/crawler-richtlinie.md`](reference/crawler-richtlinie.md) | jeder Änderung an `app/public/robots.txt` oder `app/public/llms.txt` (Gruppen, Content-Signals, Reihenfolge, `Disallow`-Pfade) und an den AI-Crawl-Control-/Bot-Regeln der Cloudflare-Zone |
| [`reference/verfahren.md`](reference/verfahren.md) samt den vier Verfahrensseiten (`verfahren-kette.md` · `verfahren-lotse.md` · `verfahren-inksight.md` · `verfahren-nullprobe.md`) | jedem §14-Eintrag, der einen Arm oder eine Stufe eines Duell-Verfahrens misst (adoptiert oder verworfen) — Ledger-Zeile im selben PR; bei Adoption zusätzlich „Aktueller Stand“ der betroffenen Seite und die Stand-/„seit“-Spalte der Übersicht. Erzwungen von `tools.docs_register check` (CI-Job „Docs-Register“) |

Drei weitere Dokumente sind **abschnittsweise** pflichtig, obwohl sie als
Ganzes nicht lebend sind:
[`reference/animation-rendering.md`](reference/animation-rendering.md) §1/§3
(bei Änderungen an `WrittenGlyph.tsx`, `useStrokeReveal.ts`,
`strokeTiming.ts`, `core/widths.py`),
[`reference/styleanalyse.md`](reference/styleanalyse.md) Schichten 1–2 (bei
Änderungen an `core/pipeline.py::_measurements`, `core/aggregate.py` oder den
Aggregat-Tabellen) und
[`reference/quellen-und-rechte.md`](reference/quellen-und-rechte.md) §5 (bei
jeder Änderung an Admin-Gates auf Lese-Endpunkten, am Origin-Gate davor
(`api/origin_gate.py`, `infra/cloudflare/`), an den gitignorten
Bench-Fixtures oder an committeten gerenderten Artefakten).
