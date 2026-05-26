# Vision der Website

Begleitdokument zu [`architektur.md`](architektur.md) und
[`naming-und-setup.md`](naming-und-setup.md). Hält fest, *was* die
Endnutzer-Website unter [kurrentschrift.ink](https://kurrentschrift.ink)
sein soll — getrennt vom *Wie* (Architektur) und vom *Wann* (MVP-Roadmap).

---

## Pitch (für Landing-Page-Aufmacher)

Zur Kurrentschrift gibt es im Web schon einiges Gutes: Alphabet-Tafeln,
PDF-Übungsblätter, Font-Generatoren, HTR-Dienste. Was noch fehlt, ist
ein Auftritt, der ductus-treues Rendering, inhaltsbewusste
Übungsblätter und Stil-Analyse im selben Werkzeug zusammenbringt.

Diese Seite schließt diese Lücke: ein moderner Zugang zur deutschen
Kurrent — **Synthese in echter Hand**, **Statistik über die eigene
Schrift**, **Werkzeug statt Lehrbuch**.

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

## Was die Seite leistet (Ziele)

1. **Einstieg in wenigen Minuten.** Geschichte in zwei Sätzen,
   Alphabet-Tafel, die wichtigsten Lese- und Schreibregeln (Rund-s,
   Ligaturen, Mischschrift, ältere Buchstabenformen — siehe
   [`orthographie-regeln.md`](../reference/orthographie-regeln.md)).
   Für Tiefe: Literatur- und Quellverweise, kein eigenes Lehrbuch.

2. **Schreiben üben.** Generierte Vorlagenblätter mit einstellbarer
   Lineatur — Verhältnis Ober-/Mittel-/Unterband frei wählbar
   (2:1:2 als Standard, 3:2:3, 1:1:1 oder was man je nach Lernstand
   und Stift braucht), beliebiger Eingabetext als Vorlage, druckbar.
   Schwerpunkt: **inhaltsbewusste Vorlagen** — Text und passende
   Lineatur in einem Schritt.

3. **Buchstaben in Aktion (animierte Tafel).** Jeder Buchstabe lässt
   sich animiert abspielen — Schreibreihenfolge, Ansatzpunkte,
   Schwellzug-Aufbau live, für jede trainierte Hand (Loth 1866, eigene
   Probe, historische Quellen). Direkter Effekt des Ductus-Priors
   (`architektur.md` §2): Synthese liefert nicht nur das fertige Bild,
   sondern auch *wie es entsteht*. Ligaturen (`ch`, `ck`, `ſt`, `tz`,
   `qu`, `ß`) als eigene Animationen.

4. **Lesen üben.** Beliebiger heutiger Text — eine Zeitungsmeldung,
   ein eigenes Memo — gerendert in einer trainierten Kurrent-Hand,
   damit Üben nicht am Nachschub historischer Beispiele scheitert.

5. **Eigene Schrift analysieren.** Handschriftliche Probe hochladen,
   Statistik zurückbekommen: Glyphen-Verteilung, Übergangswinkel,
   Schräglagen-Verteilung, Schwellzug-Profile. Zwei Anschluss-Pfade:
   - **Optimieren** — wo weicht die eigene Hand stark von der Norm ab?
     Wo ist sie inkonsistent? Konkretes statt allgemeines Feedback.
   - **Neuer Stil als Basis** — aus genug eigenen Proben einen Hand-Stil
     extrahieren und damit weitere Texte synthetisieren. „In meiner
     Hand, aber jeden Text."

6. **Lesen historischer Texte (Lese-Hilfe).** Transkription über
   bestehende HTR-Modelle (Transkribus & Co. — siehe `architektur.md`
   §1). Kein eigenes Forschungsfeld, aber motivierender Sofort-Nutzen
   und Einstieg für die Genealogie-Zielgruppe.

7. **Hände vergleichen.** Side-by-side mehrerer trainierter Hände
   (Loth 1866 vs. eigene Probe vs. historische Quelle X) — Heatmaps
   für Schräglage, Schwellzug, Glyph-Frequenz. Natürliche Verlängerung
   von Feature 5, sobald mehrere Stile vorliegen; zeigt konkret, *wo*
   sich Hände unterscheiden, nicht nur *dass* sie es tun. Kombiniert
   mit Feature 3 lassen sich Animationen derselben Glyphe in mehreren
   Händen direkt nebeneinander abspielen.

8. **Lese-Lupe.** Bild plus Overlay zur Lese-Hilfe (Feature 6):
   Klick auf einen verwirrenden Buchstaben → strukturierte Erklärung
   („das ist medial ſ, kein f — hier fehlt der Querstrich").
   Verbindet HTR-Output mit den Regel-Erklärungen aus
   [`orthographie-regeln.md`](../reference/orthographie-regeln.md).

9. **Offene Datensätze.** Kanonische Glyph-Daten (Anker, Schwellzug,
   Ductus-Reihenfolge) als zitierbares Open-Data-Paket für die
   Forschungs-Zielgruppe. Heute nirgends öffentlich verfügbar; passt
   zur MIT-Code-Linie und zur PD-Datenlinie (`quellen-und-rechte.md`).

10. **Zweisprachig (DE/EN).** Die Genealogie-Zielgruppe ist überwiegend
    englischsprachig (`naming-und-setup.md` §1). Deutscher Kern zuerst
    (`sprachregelung.md` §1), englische Version oder mindestens
    englische Glossar-Tooltips als nächster Hebel, sobald der deutsche
    Kern steht.

---

## Was die Seite nicht ist (Nicht-Ziele)

- **Kein umfassendes Lehrbuch.** Wer Tiefe sucht, bekommt verlinkte
  Quellen. Inhalt der Seite endet bei dem, was zum sinnvollen Einstieg
  und Üben nötig ist.
- **Kein TrueType-Font-Generator.** Für statische Font-Ausgabe gibt es
  etablierte kostenlose Dienste; unser Fokus ist ductus-treues
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
Diese Seite ersetzt sie nicht, sondern setzt einen Baustein dazu — die
ductus-treue Synthese — und kombiniert ihn mit Übungsmaterial und
Stil-Analyse. Wo wir uns einsortieren:

| Kategorie | Beispiele | Was diese Seite ergänzt |
|---|---|---|
| Lern-Seiten | kurrentschrift.net, suetterlinschrift.de, suetterlinstube.de | Mobil/Tablet-Bedienung und dynamisches Rendering zusätzlich zu statischen Inhalten |
| Schrift-Generatoren | ahnenforschung-ledermann, fontmeme | Hand-Synthese mit Schwellzug als Ergänzung zur Font-Ausgabe |
| Lineatur-Generatoren | paper.click, frickelmeister | Inhaltsbewusste Vorlagen (Text + passende Lineatur in einem Schritt) |
| HTR | Transkribus | Schreib-Synthese als Pendant zur Lese-Hilfe |
| Foren | CompGen, ahnenforschung.net | (eigene Domäne — kein Anspruch hier) |

Die Kombination — Rendering, Stil-Analyse und Übungsmaterial im selben
Auftritt mit echter Tinte-statt-Font-Synthese — gibt es heute so noch
nicht. Genau da soll diese Seite ansetzen.

---

## Verhältnis zu anderen Docs

- [`architektur.md`](architektur.md) — das *Wie* der Synthese-Pipeline.
- [`mvp-roadmap.md`](mvp-roadmap.md) — der MVP validiert nur die
  Synthese-Pipeline (vier Validierungs-Gates inkl. abgespeckter
  Animation). Die hier beschriebene Website liegt fast komplett *nach*
  dem MVP und ist in `architektur.md` §10 als Fünf-Phasen-Plan
  sequenziert: P1 Lesen-Hilfe (Punkt 6) → P2 Lineatur/Print (Punkt 2) →
  P3 Stil-Analyse (Punkt 5) → P4 Hände-Vergleich (Punkt 7) → P5 Open-
  Data (Punkt 9). Animation (Punkt 3) und Frontend/i18n (Punkt 10)
  laufen als Querschnitt parallel zur ersten Phase.
- [`naming-und-setup.md`](naming-und-setup.md) — Reichweite (gotische
  Kursive vor 1900, optional Skandinavien), Lizenz (MIT), Domain
  (`kurrentschrift.ink`).
- [`reference/sprachregelung.md`](../reference/sprachregelung.md) —
  Website v1 deutsch; englische Erweiterung folgt (Feature 10).
- [`reference/orthographie-regeln.md`](../reference/orthographie-regeln.md) —
  Inhalts-Grundlage für Feature 1 (Einstieg) und Feature 8 (Lese-Lupe).
