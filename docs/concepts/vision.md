# Vision der Website

Begleitdokument zu [`architektur.md`](architektur.md) und
[`naming-und-setup.md`](naming-und-setup.md). Hält fest, *was* die
Endnutzer-Website unter [kurrentschrift.ink](https://kurrentschrift.ink)
sein soll — getrennt vom *Wie* (Architektur) und vom *Wann* (MVP-Roadmap).

---

## Pitch (für Landing-Page-Aufmacher)

Die Kurrentschrift ist im Web stehengeblieben. Wer sie heute lesen oder
schreiben lernen will, klickt sich durch statische GIF-Tabellen aus den
frühen 2000ern, lädt PDF-Übungsblätter herunter und tippt seinen Namen
in einen TrueType-Generator, der wie Maschinenschrift aussieht.

Diese Seite ist der Gegenentwurf: ein moderner Zugang zur deutschen
Kurrent — **Synthese in echter Hand** statt Font, **Statistik über die
eigene Schrift** statt pauschaler Tipps, **Werkzeug** statt Lehrbuch.

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
   Nicht „leere Lineatur zum selber Beschreiben" (das gibt es schon
   woanders), sondern **inhaltsbewusste Vorlagen**.

3. **Lesen üben.** Beliebiger heutiger Text — eine Zeitungsmeldung,
   ein eigenes Memo — gerendert in einer trainierten Kurrent-Hand,
   damit Üben nicht am Nachschub historischer Beispiele scheitert.

4. **Eigene Schrift analysieren.** Handschriftliche Probe hochladen,
   Statistik zurückbekommen: Glyphen-Verteilung, Übergangswinkel,
   Schräglagen-Verteilung, Schwellzug-Profile. Zwei Anschluss-Pfade:
   - **Optimieren** — wo weicht die eigene Hand stark von der Norm ab?
     Wo ist sie inkonsistent? Konkretes statt allgemeines Feedback.
   - **Neuer Stil als Basis** — aus genug eigenen Proben einen Hand-Stil
     extrahieren und damit weitere Texte synthetisieren. „In meiner
     Hand, aber jeden Text."

5. **Lesen historischer Texte (Lese-Hilfe).** Transkription über
   bestehende HTR-Modelle (Transkribus & Co. — siehe `architektur.md`
   §1). Kein eigenes Forschungsfeld, aber motivierender Sofort-Nutzen
   und Einstieg für die Genealogie-Zielgruppe.

6. **Hände vergleichen.** Side-by-side mehrerer trainierter Hände
   (Loth 1866 vs. eigene Probe vs. historische Quelle X) — Heatmaps
   für Schräglage, Schwellzug, Glyph-Frequenz. Natürliche Verlängerung
   von Feature 4, sobald mehrere Stile vorliegen; zeigt konkret, *wo*
   sich Hände unterscheiden, nicht nur *dass* sie es tun.

7. **Lese-Lupe.** Bild plus Overlay zur Lese-Hilfe (Feature 5):
   Klick auf einen verwirrenden Buchstaben → strukturierte Erklärung
   („das ist medial ſ, kein f — hier fehlt der Querstrich").
   Verbindet HTR-Output mit den Regel-Erklärungen aus
   [`orthographie-regeln.md`](../reference/orthographie-regeln.md).

8. **Offene Datensätze.** Kanonische Glyph-Daten (Anker, Schwellzug,
   Ductus-Reihenfolge) als zitierbares Open-Data-Paket für die
   Forschungs-Zielgruppe. Heute nirgends öffentlich verfügbar; passt
   zur MIT-Code-Linie und zur PD-Datenlinie (`quellen-und-rechte.md`).

9. **Zweisprachig (DE/EN).** Die Genealogie-Zielgruppe ist überwiegend
   englischsprachig (`naming-und-setup.md` §1). Deutscher Kern zuerst
   (`sprachregelung.md` §1), englische Version oder mindestens
   englische Glossar-Tooltips als nächster Hebel, sobald der deutsche
   Kern steht.

---

## Was die Seite nicht ist (Nicht-Ziele)

- **Kein umfassendes Lehrbuch.** Wer Tiefe sucht, bekommt verlinkte
  Quellen. Inhalt der Seite endet bei dem, was zum sinnvollen Einstieg
  und Üben nötig ist.
- **Kein TrueType-Font-Generator.** Rendering ist ductus-treu mit
  Schwellzug (`architektur.md` §2/§5) — sonst wäre die Seite
  redundant zu kostenlosen Font-Diensten.
- **Keine Datenbank historischer Korrespondenz / kein Archiv.**
  Fokus ist Schrift, nicht Inhalt.
- **Kein Forum / Community-Hub.** Diskussion findet in bestehenden
  Foren (CompGen, ahnenforschung.net) und auf GitHub statt.
- **Keine Bezahl-Transkription auf Auftrag.** Das machen
  entzifferer.de und metascriptum.de; Konkurrenz dort ist nicht das Ziel.

---

## Verhältnis zur bestehenden Landschaft

| Kategorie | Beispiele | Was fehlt heute |
|---|---|---|
| Lern-Seiten | kurrentschrift.net, suetterlinschrift.de, suetterlinstube.de | Modernes Design, mobil/tablet-tauglich, dynamisches Rendering |
| Schrift-Generatoren | ahnenforschung-ledermann, fontmeme | Echte Hand statt TTF-Maschinenschrift |
| Lineatur-Generatoren | paper.click, frickelmeister | Inhaltsbewusste Vorlagen statt leerer Lineatur |
| HTR | Transkribus | Schreib-Synthese fehlt; rein lesend |
| Foren | CompGen, ahnenforschung.net | (kein Anspruch hier) |

Die Lücke liegt **zwischen** den vorhandenen Angeboten: ein modernes
Lern-Werkzeug, das Rendering, Stil-Analyse und Übungsmaterial im selben
Auftritt kombiniert und dabei die echte Tinte-statt-Font-Synthese
mitbringt. Das gibt es heute weder kostenlos noch bezahlt zu kaufen.

---

## Verhältnis zu anderen Docs

- [`architektur.md`](architektur.md) — das *Wie* der Synthese-Pipeline.
- [`mvp-roadmap.md`](mvp-roadmap.md) — der MVP validiert nur die
  Synthese-Pipeline. Die hier beschriebene Website liegt fast komplett
  *nach* dem MVP. Ausnahme: das Lese-Feature (Punkt 5) ist laut
  `architektur.md` §10 ein früher, paralleler Win mit geringem Risiko.
- [`naming-und-setup.md`](naming-und-setup.md) — Reichweite (gotische
  Kursive vor 1900, optional Skandinavien), Lizenz (MIT), Domain
  (`kurrentschrift.ink`).
- [`reference/sprachregelung.md`](../reference/sprachregelung.md) —
  Website v1 deutsch; englische Erweiterung folgt (Feature 9).
- [`reference/orthographie-regeln.md`](../reference/orthographie-regeln.md) —
  Inhalts-Grundlage für Feature 1 (Einstieg) und Feature 7 (Lese-Lupe).
