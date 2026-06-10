# Vision der Website

Begleitdokument zu [`architektur.md`](architektur.md) und
[`naming-und-setup.md`](naming-und-setup.md). Hält fest, *was* die
Endnutzer-Website unter [kurrentschrift.ink](https://kurrentschrift.ink)
sein soll — getrennt vom *Wie* (Architektur) und vom *Wann* (MVP-Roadmap).

---

## Pitch (für Landing-Page-Aufmacher)

Drei Dinge an einem Ort, die es heute nirgends in Kombination gibt:

- **Duktus-treues Rendering mit Schwellzug** — Hand-Synthese statt
  Font, mit Schreibreihenfolge und druckabhängiger Strichstärke.
- **Stil-Analyse der eigenen Schrift** — Statistik über Schräglage,
  Schwellzug, Glyph-Verteilung statt Bauchgefühl.
- **Inhaltsbewusste Übungsblätter** — beliebiger Text mit passender
  Lineatur in einem Schritt.

Die etablierten Angebote (Alphabet-Tafeln, PDF-Übungsblätter,
Font-Generatoren, HTR-Dienste) decken jeweils einen Teil ab.
[kurrentschrift.ink](https://kurrentschrift.ink) bringt sie zusammen
und ergänzt sie um die Synthese in echter Hand.

---

## Zielgruppe

| Gruppe | Was sie sucht |
|---|---|
| Deutschsprachige Lernende | Kurrent zum Selber-Schreiben (Tagebuch, Korrespondenz, Kunst); klarer Einstieg ohne Lehrbuch-Schwere. |
| Englischsprachige Genealog:innen | Lese-Hilfe für Familiendokumente; verstehen, *warum* etwas verwirrend ist, nicht nur *was* dasteht. |
| Forschende / Paläografie-affine | Offene Daten, zitierbare kanonische Glyphen, API für eigene Experimente. |

Reihenfolge ist nicht zufällig: die deutschsprachigen Lernenden sind die
Primärzielgruppe für Inhalte, die Genealogie-Zielgruppe für Lese-Hilfen,
die Forschungs-Zielgruppe für Daten und API. Alle drei teilen denselben
Kern (siehe `architektur.md` §1).

---

## Leitprinzipien

- **Werkzeug statt Lehrbuch.** Die Seite ist das interaktive Pendant
  zur vorhandenen Lehrbuch-Landschaft, nicht ihr Ersatz. Tiefe gibt's
  in den verlinkten Quellen.
- **Synthese statt Font.** Schwellzug, Schreibreihenfolge und
  Allographen sind Erstklassen-Bürger, nicht eine Glyphe pro
  Codepoint (siehe `architektur.md` §2/§5).
- **Offene Daten.** Kanonische Glyph-Daten unter zitierfähiger Lizenz
  (`quellen-und-rechte.md`).
- **Drei Schriftfamilien zum Start.** Die drei für den Start
  relevantesten Familien sind **Kurrent** (die ältere Norm, Projekt-
  Baseline), **Sütterlin** (aufrecht, gleichmäßige Strichstärke) und die
  **Offenbacher Schrift** (Breitfeder, winkelabhängiger Strichkontrast). Sie
  teilen denselben Render-Kern und Kanon — eine Familie ist im Kern ein
  Varianten-Auswahlvektor + Width-Profile-Resolver über demselben
  Apparat (`architektur.md` §5/§10), kein eigenes Modell. Der MVP
  validiert den Kern an Kurrent allein; Sütterlin und Offenbacher sind
  die ersten Erweiterungen danach (Scope-Herleitung:
  `naming-und-setup.md` §1).
- **Zweisprachig.** Deutscher Kern zuerst (`sprachregelung.md` §1),
  englische Erweiterung folgt — die Genealogie-Zielgruppe ist
  überwiegend englischsprachig (`naming-und-setup.md` §1).
- **Synthese ist als solche erkennbar.** Eine in unserer Hand
  gerenderte Seite wird nie als historisches Original ausgegeben:
  explizite Kennzeichnung (Wasserzeichen, Metadaten). Wir simulieren
  Schrift, nicht Provenienz.

---

## Was die Seite leistet (Ziele)

### Schreiben

1. **Einstieg in wenigen Minuten.** Geschichte in zwei Sätzen,
   Alphabet-Tafel, die wichtigsten Lese- und Schreibregeln (Rund-s,
   Ligaturen, Mischschrift, ältere Buchstabenformen — siehe
   [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)).
   Für Tiefe: Literatur- und Quellverweise, kein eigenes Lehrbuch.

2. **Schreiben üben.** Generierte Vorlagenblätter mit einstellbarer
   Lineatur — Verhältnis Ober-/Mittel-/Unterband frei wählbar
   (2:1:2 als Standard, 2:3:2, 1:1:1 oder was man je nach Lernstand
   und Stift braucht), beliebiger Eingabetext als Vorlage, druckbar.
   Schwerpunkt: **inhaltsbewusste Vorlagen** — Text und passende
   Lineatur in einem Schritt.

3. **Buchstaben in Aktion (animierte Tafel).** Jeder Buchstabe lässt
   sich animiert abspielen — Schreibreihenfolge, Ansatzpunkte,
   Schwellzug-Aufbau live, für jede trainierte Hand (Loth 1866, eigene
   Probe, historische Quellen). Direkter Effekt des Duktus-Priors
   (`architektur.md` §2): Synthese liefert nicht nur das fertige Bild,
   sondern auch *wie es entsteht*. Ligaturen (`ch`, `ck`, `ſt`, `tz`,
   `qu`, `ß`) als eigene Animationen.

### Lesen

4. **Lesen üben.** Beliebiger heutiger Text — eine Zeitungsmeldung,
   ein eigenes Memo — gerendert in einer trainierten Kurrent-Hand,
   damit Üben nicht am Nachschub historischer Beispiele scheitert.

   **Lern-/Quiz-Modus.** Gamifiziertes Lesetraining: ein Buchstabe
   wird gezeigt — idealerweise *animiert geschrieben* (Feature 3:
   Schreibreihenfolge sichtbar, nicht nur das fertige Bild) — und die
   Lernende rät, welcher Buchstabe es ist. Falsche Antworten lösen die
   strukturierte Erklärung aus dem Orthographie-Regelwerk aus (wie die
   Lese-Lupe in Feature 5: „das ist medial ſ, kein f — der Querstrich
   fehlt"). **Ausbaustufe: ganze Wörter** statt Einzelbuchstaben (etwa
   die MVP-Wörter `lesen`, `das`), animiert geschrieben und zu
   erraten bzw. zu transkribieren — vom Buchstaben- zum Wort- und
   Satzlesen. Baut vollständig auf vorhandenen Primitiven auf
   (Render-Kern + Animation aus Feature 3, Regeln aus
   [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md)) und
   verlangt keine neue Synthese.

5. **Lese-Hilfe für historische Texte.** Transkription über
   bestehende HTR-Modelle (Transkribus & Co. — `architektur.md` §1).
   Kein eigenes Forschungsfeld, aber motivierender Sofort-Nutzen und
   Einstieg für die Genealogie-Zielgruppe. Erweitert um eine
   **Lese-Lupe**: Bild plus Overlay; Klick auf einen verwirrenden
   Buchstaben → strukturierte Erklärung („das ist medial ſ, kein f —
   hier fehlt der Querstrich") aus
   [`orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md).

### Forschung

6. **Eigene Schrift analysieren.** Handschriftliche Probe hochladen,
   Statistik zurückbekommen: Glyphen-Verteilung, Übergangswinkel,
   Schräglagen-Verteilung, Schwellzug-Profile. Drei Anschluss-Pfade:
   - **Optimieren** — wo weicht die eigene Hand stark von der Norm ab?
     Wo ist sie inkonsistent? Konkretes statt allgemeines Feedback.
   - **Neuer Stil als Basis** — aus genug eigenen Proben einen
     Hand-Stil extrahieren und damit weitere Texte synthetisieren.
     „In meiner Hand, aber jeden Text."
   - **Hände vergleichen** — sobald mehrere Stile vorliegen,
     Side-by-side-Vergleich (Loth 1866 vs. eigene Probe vs.
     historische Quelle X) mit Heatmaps für Schräglage, Schwellzug,
     Glyph-Frequenz. Kombiniert mit Feature 3 lassen sich Animationen
     derselben Glyphe in mehreren Händen direkt nebeneinander
     abspielen.

7. **Offene Datensätze.** Kanonische Glyph-Daten (Anker, Schwellzug,
   Duktus-Reihenfolge) als zitierbares Open-Data-Paket für die
   Forschungs-Zielgruppe. Heute nirgends öffentlich verfügbar; passt
   zur MIT-Code-Linie und zur PD-Datenlinie (`quellen-und-rechte.md`).

---

## Was die Seite nicht ist (Nicht-Ziele)

- **Kein umfassendes Lehrbuch.** Wer Tiefe sucht, bekommt verlinkte
  Quellen. Inhalt der Seite endet bei dem, was zum sinnvollen Einstieg
  und Üben nötig ist.
- **Kein TrueType-Font-Generator.** Für statische Font-Ausgabe gibt es
  etablierte kostenlose Dienste; unser Fokus ist duktus-treues
  Rendering mit Schwellzug (`architektur.md` §2/§5) — eine andere
  Aufgabe.
- **Keine Datenbank historischer Korrespondenz / kein Archiv.**
  Fokus ist Schrift, nicht Inhalt.
- **Kein Forum / Community-Hub.** Diskussion findet gut in bestehenden
  Foren (CompGen, ahnenforschung.net) und auf GitHub statt.
- **Keine Bezahl-Transkription auf Auftrag.** Wer eine fachliche
  Entzifferung historischer Dokumente braucht, ist bei spezialisierten
  Diensten wie entzifferer.de oder metascriptum.de richtig aufgehoben.

---

## Verhältnis zur bestehenden Landschaft

Es gibt eine lebendige Landschaft an Angeboten rund um die Kurrent.
Diese Seite ersetzt sie nicht — sie schließt die offene Stelle: die
Kombination aus duktus-treuer Synthese, Stil-Analyse und
inhaltsbewusster Übung im selben Werkzeug.

| Kategorie | Beispiele | Was diese Seite ergänzt |
|---|---|---|
| Lern-Seiten | kurrentschrift.net, suetterlinschrift.de, suetterlinstube.de | Mobil/Tablet-Bedienung und dynamisches Rendering zusätzlich zu statischen Inhalten |
| Schrift-Generatoren | ahnenforschung-ledermann, fontmeme | Hand-Synthese mit Schwellzug als Ergänzung zur Font-Ausgabe |
| Lineatur-Generatoren | paper.click, frickelmeister | Inhaltsbewusste Vorlagen (Text + passende Lineatur in einem Schritt) |
| HTR | Transkribus | Schreib-Synthese als Pendant zur Lese-Hilfe |
| Foren | CompGen, ahnenforschung.net | (eigene Domäne — kein Anspruch hier) |

Die Dreierkombination — Tinte statt Font, Statistik statt Bauchgefühl,
Lineatur passend zum Text — gibt es heute nirgends. Genau dort setzt
diese Seite an.

---

## Verhältnis zu anderen Docs

- [`architektur.md`](architektur.md) — das *Wie* der Synthese-Pipeline.
- [`style-guide.md`](style-guide.md) — das *Wie es aussieht*: visuelle
  Identität (Papier & Tinte), Tokens, Typografie.
- [`mvp-roadmap.md`](mvp-roadmap.md) — der MVP validiert nur die
  Synthese-Pipeline (vier Validierungs-Gates inkl. abgespeckter
  Animation). Die hier beschriebene Website liegt überwiegend *nach*
  dem MVP — der Lineatur-Generator (`/schreiben`, Teil von Punkt 2,
  noch ohne inhaltsbewusste Synthese) und das Buchstaben-Quiz
  (Grundform von Punkt 4) sind aber bereits live — und ist in
  `architektur.md` §10 als Fünf-Phasen-Plan
  sequenziert: P1 Lese-Hilfe (Punkt 5) → P2 Lineatur/Print (Punkt 2) →
  P3 Stil-Analyse (Punkt 6) → P4 Hände-Vergleich (Anwendung von Punkt 6,
  sobald mehrere Stile vorliegen) → P5 Open-Data (Punkt 7). Animation
  (Punkt 3) und Frontend/i18n (siehe Leitprinzipien — Zweisprachig)
  laufen als Querschnitt parallel zur ersten Phase.
- [`naming-und-setup.md`](naming-und-setup.md) — Reichweite (gotische
  Kursive vor 1900, optional Skandinavien), Lizenz (MIT), Domain
  (`kurrentschrift.ink`).
- [`reference/sprachregelung.md`](../reference/sprachregelung.md) —
  Website v1 deutsch; englische Erweiterung folgt (siehe
  Leitprinzipien).
- [`schriftkunde/orthographie-regeln.md`](../schriftkunde/orthographie-regeln.md) —
  Inhalts-Grundlage für Feature 1 (Einstieg) und Feature 5 (Lese-Lupe).
