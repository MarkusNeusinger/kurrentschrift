# Naming- und OSS-Setup-Entscheidungen

Begleitdokument zu [`architektur.md`](architektur.md). Hält fest, *was* für
Name, Domain, Repo und Lizenz entschieden wurde und *warum* — inklusive
der bewusst verworfenen Alternativen, damit die Begründung später
nachvollziehbar bleibt und nicht erneut aufgerollt werden muss.

---

## 0. Leitprinzip (die Lektion aus pyplots → anyplot)

Der schmerzhafte Rename damals kam daher, dass der erste Name eine
*Datenscheibe* benannt hat, nicht die *Invariante*. Hier ist die
Invariante **nicht „Kurrent 1900"**, sondern die deutsche Schreibschrift
als Schriftfamilie. Der Name sitzt auf dieser Ebene: breit genug für alle
Varianten und eine mögliche Erweiterung, aber nicht so generisch, dass er
nichts mehr aussagt (die Überkorrektur in die andere Richtung).

---

## 1. Reichweite des Konzepts (was der Name abdecken muss/darf)

Die saubere Obergrenze des Ansatzes ist die *neuzeitliche gotische
Kursive* (paläografisch: Kanzleibastarda / gebrochene Kursive).

**Trägt ohne Architekturbruch:**

- Gesamter deutschsprachiger Raum. Deutschland, Österreich und die
  deutschsprachige Schweiz schrieben dieselbe Kurrent — CH/AT brauchen
  *keinen* Scope-Wechsel. (Österreich behielt die traditionelle Kurrent
  auch, als Deutschland auf Sütterlin umstellte.)
- Skandinavien / Baltikum / Tschechien als *optionale* Erweiterung:
  dieselbe paläografische Familie, lokal „Gotisk skrift" genannt, in der
  Literatur selbst als „mit geringen Abwandlungen die deutsche Kurrent"
  beschrieben. Konsistenz-Prior und Allograph-Modell (§7/§3 der
  Referenz) tragen dahin als neuer Varianten-/Stilvektor, nicht als
  neues Modell.

**Fällt explizit raus:**

- England / englischsprachiger Raum: ging früh auf die runde lateinische
  Schreibschrift (English Roundhand / Copperplate). Spitzfeder-Schwellzug
  ja, aber lateinische Buchstabenformen — andere Schriftfamilie, kein
  Kurrent-Allograph-System.
- Japanisch o. Ä.: ausgeschlossen, kein Thema.

**Variantenfächer allein innerhalb Deutschlands über die Zeit**
(deshalb ist „1900" zu eng — es ist nur *eine* Normform-Scheibe):

Kanzleibastarda (frühes 16. Jh.) → Einfluss Nürnberger / sächsische
Schreibschule (17./18. Jh.) → 1714 preußische Normschrift (Hilmar Curas)
→ 19. Jh. Spitzfeder, Schräglage bis ~45° → „klassische" Kurrent um
1800/1900 (**= die Normform des Projekts**) → Sütterlin (1911, eingeführt
ab 1915 in Preußen) → Offenbacher Schrift (1927, Rudolf Koch) → Deutsche
Volksschrift (1935) → 1941 Ende durch den Normalschrifterlass.

**Oberbegriffe** (für SEO / Texte / spätere Multi-Stil-Benennung):
„Kurrent" · „deutsche Schreibschrift" · „deutsche Schrift" / „alte
deutsche Schrift" (umgangssprachlich) · engl. „German cursive" /
„Old German Script" / „German Gothic handwriting".

---

## 2. Die Namens-Kollision (warum nicht das nackte „kurrent")

„Kurrent" ist seit Ende 2024 ein **aktiver Dev-Infrastruktur-Brand**:
Event Store hat sich mit ~12 Mio. USD Funding zu „Kurrent" umbenannt,
betreibt die GitHub-Org `kurrent-io` (KurrentDB), eine `.io`-Domain und
einen Open-Source-MCP-Server.

- Im **Schrift-Kontext** semantisch unkritisch (Eventdatenbank vs.
  historische Handschrift liegen weit auseinander).
- Im **GitHub-/Dev-/SEO-Namespace** belegt es jedoch genau das Feld.
  Ein nacktes `kurrent` als Domain/Org/Repo platziert das Projekt
  dauerhaft im Suchschatten einer VC-finanzierten DB — dieselbe
  Rename-Falle, nur durch Fremdbrand statt Scope. Erklärt auch, warum
  Einwort-`kurrent.TLD` reihenweise vergeben sind.
- Der Zusatz **`-schrift`** trennt sauber: die DB-Firma nutzt „-schrift"
  nie. „Kurrentschrift" ist zudem ein generisches deutsches Substantiv
  und der Eigenname eines Schriftsystems (wie „Fraktur") → markenrechtlich
  die entspannte Variante für einen öffentlichen Repo. *(Hinweis: keine
  Rechtsberatung.)*

---

## 3. Finale Entscheidungen

| Punkt | Entscheidung |
|---|---|
| **Domain** | `kurrentschrift.ink` |
| **Repo-Ort** | persönlicher GitHub-Account (Portfolio-Projekt, wie anyplot.ai) |
| **Repo-Name** | `kurrentschrift` (Monorepo: Code + Website) |
| **Struktur** | `/core` (Python: extractor, template, DB-Models + Repositories) · `/api` (FastAPI-Backend, dünn) · `/app` (React-Admin-/Lese-UI) · `/alembic` (Postgres-Migrationen) |
| **Lizenz** | MIT |
| **README** | = Pitch, nicht Doku; Rohmaterial aus [`architektur.md`](architektur.md) |
| **Erste Demo** | der MVP aus §8 (6-Buchstaben-Kern-Alphabet, sieben Wörter, drei Validierungs-Gates inkl. Render eines neuen Wortes aus aggregierten Stats) |

### Begründung der Kernpunkte

**MIT, nicht AGPL.** Bei einem Portfolio-Projekt ist das Ziel
Anschauen / Forken / Ausprobieren mit minimaler Reibung. AGPL signalisiert
SaaS-Schutzdenken — explizit *nicht* das Ziel hier. Lizenz vor dem ersten
öffentlichen Commit festlegen (rückwirkend nur mit Zustimmung aller
Contributor änderbar).

**Personal-Account, keine Org.** Konsistent mit der Einordnung als Hobby-
/Portfolio-Projekt analog anyplot.ai. (Der frühere Org-Rat galt dem
Skalierungs-/Contributor-Szenario, das hier ausgeschlossen wurde.)

**Monorepo mit sichtbarem Split.** Code + Website teilen das Lese-Modell
(§1 der Referenz), daher ein Repo. Der Lesen-vs-Schreiben-Split bleibt im
Verzeichnisbaum sichtbar, damit ein OSS-Leser sofort Forschungskern (§7)
von gelöster Integration unterscheidet.

**README als Pitch.** Bei einem Portfolio-Repo entscheidet der Leser nach
~30 s README, nicht nach Code. Stärkstes Material ist bereits in der
Referenz: Analysis-by-Synthesis-Kern (§2), die *bewusst verworfenen*
Alternativen, der ehrlich benannte offene Forschungskern (§7). Genau dieses
„ich kenne die Trade-offs und benenne das Ungelöste" demonstriert Tiefe.

**MVP als Demo.** Ein Portfolio-Projekt überzeugt durch *ein sichtbares
funktionierendes Stück*, nicht durch Vollständigkeit. §8 ist klein genug
zum Fertigstellen und visuell genug für ein GIF/Bild in der README. Die
Reihenfolge aus §10 (MVP zuerst) ist damit auch portfolio-strategisch
richtig, nicht nur technisch.

---

## 4. Verworfene Optionen (damit nicht erneut diskutiert)

- **`kurrent.ai` / `kurrent.ink` / Einwort-`kurrent.TLD`** — vergeben
  bzw. im DB-Brand-Sog; jede neue Einwort-Variante ist die nächste Snipe.
- **`kurrent.art`** — `.art` liest sich als Galerie/Portfolio-Showcase,
  verkauft den Engineering-Teil unter (es ist Engine + Lern-Website,
  kein Kunst-Showcase).
- **`ductus.*` als Brand/Org** — valide, kollisionsfrei, schriftneutral;
  nicht gewählt, weil „kurrent" im Namen sichtbar bleiben soll. Bleibt als
  Reserve, falls sich der DB-Namespace-Druck im Dev-Search doch als Problem
  zeigt.
- **GitHub-Org statt Personal-Account** — zurückgezogen, da Hobby-/
  Portfolio-Einordnung.
- **AGPL-3.0** — nur sinnvoll zum Schutz eines gehosteten SaaS-Geschäfts;
  hier kein Ziel.
- **„Entdeutschen" für das Skandinavien-Szenario** — Überkorrektur
  (anyplot-Falle rückwärts). „Kurrent" ist international der unübersetzte
  Fachterminus (wie „Fraktur"/„Sütterlin"); die deutsch-orientierte
  Hauptzielgruppe — u. a. englischsprachige Genealogie — *erwartet* genau
  dieses Wort. Ein deutscher Name ist auch im Gotisk-skrift-Kontext
  fachlich anschlussfähig, nicht parochial.

---

## 5. Quellen (externe Fakten zur Schriftgeschichte & Namenslage)

- Deutsche Kurrentschrift & Sütterlin: de.wikipedia.org/wiki/Deutsche_Kurrentschrift,
  de.wikipedia.org/wiki/Sütterlinschrift, en.wikipedia.org/wiki/Kurrent
- Skandinavien / „Gotisk skrift" / gotische Kursive als Familie:
  familysearch.org (Nordic Handwriting), en.rigsarkivet.dk (Gothic Script),
  en.wikipedia.org/wiki/Blackletter, script.byu.edu (German Gothic Handwriting)
- Offenbacher Schrift / Variantenfächer: kurrentschrift.net,
  werktisch-in-waldkirch.de
- Brand-Kollision „Kurrent" (Event Store): kurrent.io (Rebrand-FAQ),
  github.com/kurrent-io, businesswire.com (Funding-/Rebrand-Meldung 12/2024)
