# Vision der Website

> **Status (2026-09-07): bindend.** Ziele, Leitprinzipien und Nicht-Ziele
> stehen fest; die eingebettete Open-Core-Notiz zu Ziel 7 gilt unverändert
> (technisch verschärft mit PR #254). Neu am 2026-09-07: der Abschnitt
> [„Drei Rollen: Tafel · Platte · Eigenhand“](#drei-rollen-tafel--platte--eigenhand)
> — der Autor-Entscheid, dass die **Eigenhand** die ausgelieferte
> Schreibhand der Seite wird, sobald ihr Bestand Alphabet und Übergänge
> deckt, während die Tafeln der historische Prior und die Platten-Wörter
> der Maßstab bleiben. Am 2026-08-27 ohne neue Entscheidung
> nachgezogen: das Schriftfamilien-Leitprinzip spiegelt jetzt den
> Sütterlin-first-Pivot vom 2026-06-12 (`mvp-roadmap.md`), das
> Offene-Daten-Leitprinzip trägt den Ziel-7-Vorbehalt selbst, und Ziel 6
> nennt die Eigenhand-Erfassung als ersten realen Zubringer.
> Der Umsetzungsstand gehört nicht hierher — Reihenfolge in
> [`architektur.md`](architektur.md) §10, Stand in
> [`mvp-roadmap.md`](mvp-roadmap.md), der Erfassungsweg der Eigenhand in
> [`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md).

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
- **Offene Daten — als Ziel, unter Open-Core-Vorbehalt.** Kanonische
  Glyph-Daten unter zitierfähiger Lizenz bleiben das Ziel (Ziel 7); bis
  zu dieser bewussten Veröffentlichung bleibt der *gelernte* Datensatz
  vorbehalten — siehe die Status-Notiz in Ziel 7 und
  [`quellen-und-rechte.md`](../reference/quellen-und-rechte.md) §5.
- **Drei Schriftfamilien zum Start.** Die drei für den Start
  relevantesten Familien sind **Kurrent** (die ältere Norm, Projekt-
  Baseline), **Sütterlin** (aufrecht, gleichmäßige Strichstärke) und die
  **Offenbacher Schrift** (Breitfeder, winkelabhängiger Strichkontrast). Sie
  teilen denselben Render-Kern und Kanon — eine Familie ist im Kern ein
  Varianten-Auswahlvektor + Width-Profile-Resolver über demselben
  Apparat (`architektur.md` §5/§10), kein eigenes Modell. Validiert wird
  der Kern seit dem Sütterlin-first-Pivot (Status 2026-06-12 in
  [`mvp-roadmap.md`](mvp-roadmap.md)) zuerst an der Sütterlin-Vorlage
  von 1922 — Gleichzug und aufrechte Formen vereinfachen
  Kreuzungsauflösung und Renderpfad; Kurrent (Loth 1866, weiterhin die
  geometrische Projekt-Baseline) ist bis dahin geparkt, die Offenbacher
  folgt danach (Scope-Herleitung: `naming-und-setup.md` §1).
- **Zweisprachig.** Deutscher Kern zuerst (`sprachregelung.md` §1),
  englische Erweiterung folgt — die Genealogie-Zielgruppe ist
  überwiegend englischsprachig (`naming-und-setup.md` §1).
- **Synthese ist als solche erkennbar.** Eine in unserer Hand
  gerenderte Seite wird nie als historisches Original ausgegeben:
  explizite Kennzeichnung (Wasserzeichen, Metadaten). Wir simulieren
  Schrift, nicht Provenienz.

---

## Drei Rollen: Tafel · Platte · Eigenhand

**Autor-Entscheid 2026-09-07.** Das Projekt arbeitet mit drei Sorten
Schriftmaterial, und sie haben verschiedene Aufgaben. Bis zu diesem Tag
war das nirgends festgehalten: dieses Doc nannte die Eigenhand nur einen
„Zubringer“ zur Statistik (Ziel 6),
[`eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md) führte
sie als Bestand und Datenquelle, und jede öffentliche Bildunterschrift
sagt, die Feder schreibe „nach der Sütterlin-Ausgangsschrift von 1922“.
Der Entscheid ordnet die drei Rollen und benennt die dritte zum ersten
Mal — **die Eigenhand ist nicht nur Trainingsmaterial, sie wird die
Hand, die die Seite ausliefert.**

In den Worten des Autors:

> „Die Tafeln sind das Historische, bieten die Basis und werden bei der
> Schriftkunde verwendet. Die Sütterlin-Wörter sind zum ersten Optimieren
> des Schreibens und Nachfahrens. Aber die Schrift, die dann geschrieben
> wird — im Header, Quiz … — ist dann meine: die ist zwar nicht so sauber
> oder historisch, aber ich will das Schreiben eh üben, und so kann ich
> beliebig Buchstaben oder Übergänge nachliefern. Ob, wenn die drei
> Schriften passen, doch noch historische Alltagsschriften folgen, ist
> eine Frage für später; die sind dann auch weniger lehrbuchmäßig
> geschrieben, was einiges schwerer macht.“

**(a) Die Tafeln — die historische Formbasis und der Schriftkunde-Beleg.**
Die gemeinfreien Lehrtafeln (Loth 1866, Petzendorfer 1889,
Sütterlin-Ausgangsschrift 1922, Koch 1928) liefern die **Geometrie**, an
die die kanonischen Templates gefittet werden
([`architektur.md`](architektur.md) §2/§3), und sie sind die Belege der
Schriftkunde. Diese Rolle ändert sich nicht: die Tafeln bleiben
gemeinfrei, zitierbar und das Historische an diesem Projekt. Was sie
ausdrücklich NICHT liefern, ist der **Duktus-Prior** — Strichfolge,
Absetzpunkte und Kreuzungsauflösung sind die eigene Arbeit des Autors
ÜBER dieser gemeinfreien Geometrie und bleiben es in jeder der drei
Rollen (`quellen-und-rechte.md` §5; die Tafel liefert die Formen, nicht
die Reihenfolge).

**(b) Die Platten-Wörter (Sütterlin 1922) — Ground Truth und erster
Maßstab.** Die geschriebenen Wortproben der Platte sind das Material,
gegen das Nachfahren und Komposition optimiert werden: der eingefrorene
Referenzsatz der Tintenfolger-Kampagne
([`../proposals/tintenfolger.md`](../proposals/tintenfolger.md)) und die
Fixture-Wurzeln der Benches. Sie sind **Maßstab, nicht Auslieferung** —
Lineale und Fixture-Wurzeln bleiben während eines Laufs eingefroren
([`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md)
§2). Dass die Rolle beim Messen endet, ist keine Abwertung: eine
Bench-Referenz muss unverändert bleiben, und genau deshalb kann sie nicht
zugleich der Ort sein, an dem fehlende Buchstaben nachwachsen.

**(c) Die Eigenhand des Autors — die ausgelieferte Schreibhand.** Sobald
ihr Bestand Alphabet und Übergänge deckt, schreibt die Seite in der Hand
des Autors: Hero, Federprobe, Übungsblatt-Vorschrift — und das Lese-Quiz,
das der Autor selbst nennt, für das aber eine didaktische Unterfrage offen
bleibt (siehe unten). Sie ist „nicht so sauber oder historisch“ wie die
Platte — das ist bewusst in Kauf genommen, weil vier Dinge dafür sprechen:

- **Bekannte Feder statt rekonstruierter.** Das **stehende Setup** einer
  Hand (Feder, Tinte, Papier, Aufnahmegerät) ist einmal erfasst, und
  jede Fassung trägt zusätzlich die EFFEKTIVEN Werte ihrer Sitzung
  ([`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md)
  §7.1) — ein Wechsel mitten in der Kampagne ist in den Daten sichtbar
  statt still. Bei der Platte ist die Feder ein Druckbild, das wir
  rekonstruieren müssen.
- **Auflösung statt Ablese-Boden.** Die Platten-Wortproben stehen bei
  30–35 px je x-Höhe; die Ablesung einer Binnenfläche hat dort einen
  Boden von etwa ±0,015 xh, und die Kringel-Kette vom 2026-09-06/07 hat
  gemessen, dass die Öffnung an einer verschmolzenen engen Schleife
  bereits in der Tinten-Evidenz verloren geht — vor jedem Fit
  ([`../notes/kringel-binnenflaechen-2026-09-06.md`](../notes/kringel-binnenflaechen-2026-09-06.md)).
  Ein eigener Bogen bei ≥ 300 DPI löst nicht das physikalische Problem —
  wo zwei Federzüge wirklich zusammenlaufen, ist auch dort nichts mehr zu
  öffnen. Er nimmt aber beides, was daran unser eigenes ist: den
  Ablese-Boden, und die Wahrscheinlichkeit des Zusammenlaufens selbst,
  weil in bekannter Federbreite auf bekannter Lineatur geschrieben wird
  statt in einem fremden Druck von 30 px.
- **Beliebig nachlieferbar.** Fehlt ein Buchstabe, ein Übergang oder ein
  Versal, wird er geschrieben — der strukturelle Vorteil, den der
  Stufenplan als H5 führt
  ([`../proposals/handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md)).
  Eine historische Platte antwortet auf eine Lücke nicht.
- **Eigenes Urheberrecht.** Die eigene Hand ist die einzige Quelle, deren
  Rechte vollständig beim Autor liegen; sie trägt den Open-Core-Vorbehalt
  ohne Fremdrechte-Frage
  ([`../reference/quellen-und-rechte.md`](../reference/quellen-und-rechte.md)
  §5). Die Bytes bleiben aus demselben Grund gitignored (Autor-Entscheid
  2026-08-22).

**(d) Historische Alltagsschriften — spätere Frage, ausdrücklich offen.**
Ob nach den drei Schriftfamilien noch echte Alltagshände (Briefe,
Kirchenbücher) als eigene Vorlagen dazukommen, ist **nicht entschieden**.
Der Autor benennt selbst, was es schwer macht: sie sind „weniger
lehrbuchmäßig geschrieben“ — kein Kanon je Buchstabe, keine saubere
Lineatur, mehr Varianz je Vorkommen. Diese Frage wird gestellt, wenn die
drei Familien stehen, nicht vorher.

### Verworfen

Zwei Wege, die derselbe Entscheid ausschließt — sie werden nicht neu
verhandelt; neue Argumente gehen nach `docs/proposals/`:

- **Die Platte bleibt dauerhaft die Auslieferungshand.** Sie kann es
  nicht sein, ohne ihre andere Rolle zu verlieren: eine Bench-Referenz
  muss eingefroren bleiben (Rolle b), also ist sie genau der Ort, an dem
  ein fehlender Buchstabe, ein fehlender Übergang oder ein fehlender
  Versal **nie** nachwachsen kann. Dazu kommt der gemessene Ablese-Boden
  ihrer 30–35-px-Ausschnitte (siehe (c)). Was bleibt: die Platte bleibt
  Maßstab und Ground Truth — das ist keine Abstufung, sondern ihre
  Aufgabe.
- **Die Eigenhand bleibt reines Trainingsmaterial.** Das war der Stand
  bis zum 2026-09-07 und verschenkt den einen strukturellen Vorteil, den
  keine historische Quelle hat: beliebiger Nachschub. Der Autor übt das
  Schreiben ohnehin („ich will das Schreiben eh üben“), sodass der
  Nachschub kein zusätzlicher Aufwand ist, sondern derselbe.

**Nicht verworfen, nur aufgeschoben:** historische Alltagsschriften (d)
— das ist eine offene Frage für später, kein abgelehnter Weg.

### Was am Rollenwechsel hängt

Der Wechsel der ausgelieferten Hand ist **noch nicht vollzogen** — er ist
ein späterer, eigener Autor-Entscheid (Bedingungen und Betrieb:
[`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md)
§2). Was er auslöst, steht hier, damit es beim Umschalten nicht neu
gesucht werden muss:

1. **Die öffentlichen Bildunterschriften ändern sich.** Sie nennen heute
   die Platte als das, was schreibt: `scribe.ts` (`about`,
   `disclaimer`), `quiz.ts` (`about`, `setup.sourceNote`),
   `schriftkunde.ts` (`specimen.suetterlinCaption`,
   `lettersSpecimenNote`) und `vergleichen.ts` (`writtenCaption`,
   `pairsNote`, `disclaimer`) — alle unter `app/src/locales/de/`. Sie
   müssten dann sagen, dass eine eigene Hand schreibt, die der
   Ausgangsschrift von 1922 folgt.
2. **Die Herkunfts-Angaben bleiben, werden aber ergänzt.**
   `impressum.ts` (`sources.geometry`) und `schriftkunde.ts`
   (`sourcesRepo`) beschreiben die gemeinfreien Vorlagen, aus denen die
   Buchstabenform stammt — das bleibt für Rolle (a) wahr und braucht den
   Zusatz, dass die ausgelieferte Schrift eine eigene Hand darüber ist.
   `hub.ts` nennt nur die Schrift („in Sütterlin“), nicht die Platte, und
   bliebe unverändert.
3. **Offene Unterfrage: das Leseziel des Quiz.** Der Entscheid nennt das
   Quiz ausdrücklich („im Header, Quiz …“), also wechselt es nach seinem
   Wortlaut mit. Was er nicht beantwortet, ist die didaktische Frage
   dahinter: das Quiz zeigt eine Form nicht zum Anschauen, sondern als
   **Leseaufgabe** — und die Verwechsler, die es lehrt (n/u, e/n, ſ/f),
   sind an der Norm der Ausgangsschrift definiert, während echte
   Dokumente ohnehin nie lehrbuchsauber sind. Ob das Quiz deshalb als
   einzige Fläche bei den 1922er-Formen bleibt, **entscheidet der Autor**
   — dieses Doc setzt dafür keinen Default gegen seinen Wortlaut. Solange
   die Frage offen ist, wechselt das Quiz mit den übrigen Flächen.
4. **Die Lesbarkeits-Leitregel gilt unverändert** (Autoren-Leitsatz
   „Legibility over period authenticity“,
   [`design-system.md`](design-system.md) §9). Eine weniger saubere Hand
   darf die Lesbarkeit der Seite nicht senken: historische Formen bleiben
   markierte Schriftproben auf eigener Fläche, Navigation und Fließtext
   bleiben Antiqua.
5. **Ein Wechsel ist eine erklärte Re-Baseline.** Die Benches messen
   weiter gegen die Platte (Rolle b); eine Kopfzahl liest nie aus dem
   Eigenhand-Material, solange dafür keine eigene Teilmenge eingefroren
   und vorregistriert ist
   ([`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md)
   §4, „Trainingsdaten, kein Mess-Satz“).

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
   Schwellzug-Aufbau live, für jede trainierte Hand (heute die
   Sütterlin-Vorlage von 1922; dazu künftig Loth 1866, die eigene Probe,
   weitere historische Quellen). Direkter Effekt des Duktus-Priors
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
   Schräglagen-Verteilung, Schwellzug-Profile. Der erste reale Zubringer
   zu dieser Statistik ist die interne Eigenhand-Erfassung des Autors
   (gedruckte Bögen, Streifen, Siebung —
   [`../proposals/eigenhand-erfassung.md`](../proposals/eigenhand-erfassung.md));
   seit dem Autor-Entscheid vom 2026-09-07 ist sie zugleich die künftige
   **ausgelieferte Schreibhand** der Seite, nicht nur ein Zubringer
   (siehe [„Drei Rollen“](#drei-rollen-tafel--platte--eigenhand)).
   Der offene Upload-Weg für Nutzende bleibt das Ziel dieses Punkts.
   Drei Anschluss-Pfade:
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

   > **Status (Open-Core, Stand 2026-06):** Zurückgestellt. Das Projekt
   > läuft aktuell **Open-Core** — der Code ist MIT, aber der *gelernte*
   > Datensatz (kuratierte Glyph-Vorlagen, Duktus, Schrift-Statistik)
   > **und die daraus trainierten Lese-Modelle zur Buchstabenerkennung**
   > bleiben vorbehalten (nicht Teil von MIT, Nachnutzung nach
   > Rücksprache). Eine offene Veröffentlichung ist ein mögliches
   > *späteres* Ziel, kein aktuelles.

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
  noch ohne inhaltsbewusste Synthese) und das Lese-Quiz (Buchstaben +
  ganze Wörter, Grundform von Punkt 4) sind aber bereits live — und ist in
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
