# Quellen-Recherche: geschriebene Wörter & echte Hände (Juli 2026)

**Stand: 2026-07-31.** Synthese der Recherche-Runde vom 30./31.07.2026
(19-Agenten-Workflow mit unabhängigen Suchkanälen und adversarialen
Lizenz-Checks). Ausgangsfrage: Gibt es weitere **geschriebene**
Wortvorlagen — Schulhefte, Vorschriften, Briefe — die als Vorbild für
die verbundene Schrift dienen können? Ergebnis in Kurzform: Von der
Normhand der `suetterlin-1922` existiert **kein weiteres Material**
(das Mutterbuch ist vollständig gesichtet, siehe Nr. 1); dafür gibt es
mehrere sauber gemeinfreie **fremde Hände** und eine zweite
Kurrent-Norm in drei Progressionsstufen.

**Umsetzungsstand:** Nr. 1 ist committet
([`data/sources/suetterlin-leitfaden-1926/`](../../data/sources/suetterlin-leitfaden-1926/SOURCE.md),
PR #248). Alles Übrige ist per Nutzer-Entscheid **reine
Recherche-Notiz** — keine Commits, keine Anfragen an Institutionen
ohne neuen Entscheid. Rechte-Maßstab für jeden späteren Ingest:
[`quellen-und-rechte.md`](../reference/quellen-und-rechte.md) +
[`datenablage.md`](../reference/datenablage.md) + `/audit-licenses`.

---

## 1. Rangliste der besten Funde

### 1. Sütterlin: *Neuer Leitfaden für den Schreibunterricht*, 5. Aufl. 1926 — SUB Hamburg, Volldigitalisat ✅ committet

**Link:** <https://resolver.sub.uni-hamburg.de/kitodo/PPN1025245350> ·
IIIF: <https://iiif.sub.uni-hamburg.de/object/PPN1025245350/manifest> ·
DDB: `2AHKCSHB6SLPIYKJ2KSHR2HI7DYTVVUP`

**Was drin ist:** Das Mutterbuch unserer vorhandenen Platten — komplett
(112 IIIF-Farbscans, 90 S.). Per Seitenzug verifiziert: S. 53 ist
druckstock-identisch mit unserer `words-abb19`. Der ehrliche Kernbefund
des vollständigen Seiteninventars: Die 1926er enthält **keine
zusätzlichen Norm-Wort-Platten** über die bekannten Abb. 19/20/22
hinaus — der Neuwert ist die **Hände-Galerie** (17 Faksimile-Seiten
echter Handschriften: namentlich bekannte, sicher gemeinfreie
Schreiber — Goethe, Güll ganzer Brief ~100 Wörter, Moltke ~120
Wörter, Bismarck, Thoma, Behrens, Flaischlen, Blüthgen, Varnhagen,
Stöber, Weddigen, Weckherlin 1632, Hans Sachs 1557 — plus drei
anonyme Proben nach §66 UrhG: zwei Kanzlei-Seiten 16. Jh. und die
„Dekorative Handschrift").

**Rechtslage:** COMMITTABLE — doppelt adversarial geprüft. Vorwort im
Scan selbst signiert „Berlin, Ostern 1917. Ludwig Sütterlin.";
Verlagsnotizen 1921/1926 belegen im Buch, dass spätere Auflagen
unverändert sind. §64 abgelaufen 1987, US-PD (vor 1930), PDM 1.0 der
SUB Hamburg + §68 UrhG. Vor Aufnahme einer weiteren 1926er-Platte in
ein Same-Hand-Set ist **pro Abbildung** die Druckidentität mit dem
1922er-Druck zu prüfen (für Abb. 19 erledigt: identisch).

**Genutzt als:** Provenienz-Härtung der bestehenden
`suetterlin-1922`-SOURCE.md + Hände-Galerie als Fremdhand-Material für
Hände-Vergleich/Stilanalyse (architektur.md §12) — **nie**
Same-Hand-Bench-Referenz. Zweitscan als Backup: UB Paderborn, CC BY
4.0 (<https://digital.ub.uni-paderborn.de/ihd/id/7289766>).

### 2. August Berger: *Vorlegeblätter zum Schönschreiben in deutscher Current* (Beck, 1860)

**Link:** <https://archive.org/details/bub_gb_PaxAAAAAcAAJ>

**Was drin ist:** ~20 lithographierte Platten, je eine Lineatur-Zeile
mit ~5 verbundenen Kurrent-Wörtern („edel, oben, ewig, einzig, eisig"
…), geschätzt 80–120 Wörter in einer konsistenten Idealhand, sauberer
Schwellzug, ~50–55°. Das Wort-pro-Zeile-Layout passt direkt auf unser
words.json-Sidecar-Format.

**Rechtslage:** COMMITTABLE (adversarial geprüft). Werk 1860
zweifelsfrei PD; PDM auf dem Google/BUB-Scan; §68-Rationale identisch
zur committeten petzendorfer-1889. Für eine spätere SOURCE.md: kein
gedrucktes Jahr auf dem Titel (1860 = Katalogdatum der 2. Aufl.),
**Lithographie** nicht Stich, der Scan ist nur Heft 1/Erste Stufe.
Nur Plattenseiten committen, nie Googles Deckblatt.

**Nutzbar als:** zweite Kurrent-Wortquelle neben Loth 1866 —
Cross-Hand/Cross-Norm-Wortkorpus + Laufform-Daten (Vorbehalt:
lithographiertes Ideal, nicht Federtinte). Eigenes Set `berger-1860`
mit eigener Kennzahl, nie Headline.

### 3. Die Berger-Familie komplett: *Schulvorschriften* 1850 + *18 Vorlegeblätter* 1866

**Links:** <https://archive.org/details/bub_gb_aEhCAAAAcAAJ> ·
<https://archive.org/details/bub_gb_DgBCAAAAcAAJ>

**Was drin ist:** Die Fortsetzungsstufen derselben Norm: 1850
mehrzeilige, voll verbundene Sprichwort-Platten mit abschließenden
Verbindungsdrills (ck, ſſ, ſt, ßt) — deutlich join-dichter als
Wortzeilen; 1866 sechs Ein-Zeilen-Sprichwörter pro Platte in kleinem
Schriftgrad. Zusammen mit Nr. 2 ein **Drei-Stufen-Join-Korpus einer
Kurrent-Norm**.

**Rechtslage:** gleiche Klasse wie Nr. 2 (PD-old, PDM auf
Google-Scan); formal wurde nur der 1860er-Band adversarial geprüft —
vor einem Commit denselben Prüfpfad in die SOURCE.md schreiben. Beim
1866er den Scan-Kontrast auf feinen Haarlinien vorab prüfen.

### 4. Dressel: *Lebensbeschreibung 1751–1773 / 1773–1778* (Commons, Bezirksamt Charlottenburg-Wilmersdorf)

**Link:** <https://commons.wikimedia.org/wiki/Category:Johann_Christian_Gottfried_Dressel,_Lebensbeschreibung_1751_-_1773>

**Was drin ist:** ~1 165 High-Res-TIFFs, eine einzige geübte
Erwachsenenhand ~1791–1824, ~250 Wörter/Seite — ein sechsstelliges
Wortkorpus **in einer Hand**.

**Rechtslage:** COMMITTABLE (adversarial geprüft; die sauberste große
Fundstelle: Autor † 1824 namentlich belegt, Upload durch die haltende
Institution selbst mit PDM, §72/§68/§71 durchdekliniert). Praktische
Auflage: zig GB — Ingest über das `/data/corpora`-Muster (SOURCE.md +
fetch_corpus.py, Bytes gitignored), nur ausgewählte Specimen-Seiten
nach `/data/sources`.

**Nutzbar als:** Hände-Vergleich/HTR-Flaggschiff für die
Post-MVP-Säulen (§12/§13) und der beste Kandidat für ein
**statistisches Hand-Modell einer echten historischen Hand** (genug
Text für Verteilungen pro Glyphe und pro Paar). Nicht als Referenz für
die 1866/1889er Kurrent-Quellen — andere Ära, andere Letterformen.

### 5. Schönschreibhefte Käthe Erker, 1889–1890 (Freilichtmuseum Roscheider Hof)

**Link:** <https://www.deutsche-digitale-bibliothek.de/item/EXXXFRO3YWWVREA33DF6YH7P46K2P67M> ·
<https://rlp.museum-digital.de/object/137961>

**Was drin ist:** Echte Schülerhand, klassischer Schönschrift-Drill
(eine Zeile seitenfüllend wiederholt), Lehrerzensuren sichtbar — aber
bisher nur 4 Seiten digitalisiert.

**Rechtslage:** der seltene Fall mit **beiden Ebenen sauber**:
Schreiberin identifiziert (Katharina Auguste Sieger geb. Erker,
1876–1942 → PD) **und** CC0 vom Museum. Kein adversarial Check
gelaufen; vor einem Commit die Rechtezeile pro Bild bestätigen.

**Nutzbar als:** Laufform-Daten + Hände-Vergleich mit echter Tinte
statt Litho.

### 6. *Leseübungen für die zarte Jugend* (Wien 1835, Wienbibliothek/Commons)

**Link:** <https://commons.wikimedia.org/wiki/File:Lese%C3%BCbungen_f%C3%BCr_die_zarte_Jugend_27.jpg>
(Serie „Leseübungen für die zarte Jugend 00…", 56 Seiten)

**Was drin ist:** Ganze Seiten fortlaufender verbundener
Kurrent-Lesetext, ~120–150 Wörter/Seite, mehrere tausend Wörter gesamt.

**Rechtslage:** PD-old zweifelsfrei; Wienbibliothek-Repro in der
SOURCE.md zitieren (§72-Vorsicht). Kein adversarial Check, Risiko
gering.

**Nutzbar als:** Cross-Hand-Kontext — reichste PD-Quelle für die
Quiz-Wortbank und ein Join-/Ligatur-Inventar der 1830er-Norm. Als
natürliche Laufform-Evidenz schwach (Stich/Satz: identische
Wiederholformen).

### 7. Henze: *Die Handschriften der deutschen Dichter und Dichterinnen* (1855)

**Link:** <https://books.google.com/books?id=iYa0u8kT-JwC>

**Was drin ist:** 305 Faksimiles **echter** Hände namentlich bekannter
Schriftsteller, je einige verbundene Zeilen + Signatur, mit gedruckten
Lebensdaten direkt daneben — das Todesjahr steht gleich neben jedem
Specimen.

**Rechtslage:** Werk PD; **Google-Scan nutzen, nicht die ÖNB-Bytes**
(deren NoC-NC-Mark kollidiert mit unserer Policy).
Faksimile-Lithografie begrenzt die Strichbreiten-Treue.

**Nutzbar als:** Hände-Vergleich — hunderte distinkte reale Hände
unter einem PD-Dach für die Post-MVP-Stilanalyse. Keine Norm-Referenz.

---

## 2. Klare Absteiger (view-only / LINK-ONLY)

- **Diktatheft 1901 (Auguste Lege)** — inhaltlich der beste Fund echter
  Schülerhand, rechtlich gekippt: PD-Tag nachweislich falsch
  (Schreiberin * 1888, Todesjahr unbekannt), „Erben-Release" ist ein
  einzelner Enkel ohne belegte Alleinerbenstellung, und falls das
  Urheberrecht doch abgelaufen wäre, griffe §71 (Editio princeps, bis
  2046). Verlinken und Fakten auswerten: ja. Bytes committen: nein.
- **Poppe: Schreibvorlagen 1889 (SUB Hamburg)** — trotz
  institutioneller PDM: Autor auf dem Titel namentlich genannt,
  Todesjahr trotz Recherche unauffindbar → der §66-Anonymitätspfad ist
  blockiert; „vermutlich lange tot" reicht nach unseren eigenen Regeln
  nicht. Upgrade über Hamburger Lehrerverzeichnisse/Staatsarchiv
  möglich.
- **Stegemann-Schönschreibhefte, Hildesheim ~1910–12** — inhaltlich
  das beste Echte-Hand-Item der Runde (drei komplette Hefte, eine
  Hand, Lehrerkorrekturen), aber CC BY-NC-ND auf der Digitalisierung +
  Todesjahr der Schülerin unbekannt → doppelt gesperrt.
- **Kochbuch Bertha Mejer 1899 · Poesiealbum Hedwig 1901 · Poesiealbum
  1930–32** — dasselbe Muster: CC-Lizenz deckt nur die Foto-Ebene, die
  Schreiber sind Orphan Works. Das 1930er-Album bleibt als einziger
  Fund echter Sütterlin-Norm-Handschrift immerhin zum Anschauen
  wertvoll.
- **Moderne Sütterlin-Übungsblätter (Commons, 2018)** — moderne
  Imitationshand, Teilbestand mutmaßlich font-gerendert, BY-SA;
  als Handdaten wertlos.
- **BSB-NoC-NC-Items (Ostermayer 1883, G. A. Berger ~1844)** — die
  pauschale NC-Markierung ist post-§68 wohl unwirksam, aber *wie
  ausgewiesen* NC → ohne Projektentscheid zur §68-Frage nicht
  committable.
- **Kurt Hoffmann Arbeitsheft 1938** — CC0 vom Museum, aber nur 2 von
  32 Seiten digitalisiert und Schreiber-Orphan.
- **Marksteine 1902** — Letternsatz-Prachtband, keine Kursive.
- **Nicht gefunden:** ein freies Digitalisat von **Koch: Das
  Schreibbüchlein 1930** — die Offenbacher-Lücke bleibt offen
  (Watch-Item: seit Jan 2026 US-PD, HathiTrust/archive.org
  beobachten). Europeana war maschinell unerreichbar (403),
  DDB-Feldpost-Suchen ergaben nur undigitalisierte Bestände,
  GEI-Digital ist bot-gated (Vorsicht: viele Fibel-Seiten sind
  Satzschrift mit gegossenen Verbindungen).

---

## 3. Einordnung: neue Hände vs. Bench-Headline

Bindend wie gehabt: **Keine neue Hand wandert je in die
Same-Hand-Headline der Wordbench.** Die Headline misst gegen die eine
1922er-Normhand (Abb. 19/20). Alles hier Gefundene ist entweder
(a) *dieselbe Norm aus demselben Buch* — nach Druckverifikation pro
Abbildung als Erweiterung der bestehenden Fixtures zulässig — oder
(b) *fremde Hände/Normen* → eigenes Set mit eigener Kennzahl nach dem
abb22-Muster, bzw. Statistik **je Hand** in `aggregates`
(architektur.md §12) und Fremdhand-Kontext im Vergleich-Tab. Die
Berger-Bände wären also ein Set `berger-1860` mit eigenem Loss, nie
ein Beitrag zur Sütterlin-Zahl. Wie viele Hände als *Vorbild* taugen,
beantwortet der Stufenplan:
[`handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md) —
kurz: pro gerenderter Schrift genau **eine** Hand als Modell, nie ein
Durchschnitt über Hände.

## 4. Mögliche nächste Schritte (festgehalten, nicht beauftragt)

Per Nutzer-Entscheid 2026-07-31 werden diese nur notiert; jede
Umsetzung braucht einen neuen Entscheid.

1. **Berger 1860 als zweite Kurrent-Wortquelle** committen (nur
   Plattenseiten; SOURCE.md mit den drei Korrekturen: Katalogjahr,
   Lithographie, Heft 1), die 1850/1866-Geschwister nach demselben
   Prüfpfad nachziehen.
2. **Dressel per `/data/corpora`-Muster** anbinden (fetch-Skript +
   SOURCE.md, ausgewählte Specimen-Seiten nach `/data/sources`), als
   Basis für ein Hand-Modell einer echten historischen Hand.
3. **Vier Anfragen, die sich lohnen würden** (aufsteigend nach
   Aufwand): Freilichtmuseum Roscheider Hof (Digitalisierung der
   restlichen Erker-Seiten + des Hoffmann-Hefts — die
   wahrscheinlichste komplett saubere Echte-Hand-Quelle);
   Commons-User NobbiP (belastbare CC0/VRT-Freigabe der Erben für das
   Diktatheft 1901); Schulmuseum Hildesheim (Lockerung der
   NC-ND-Lizenz für die Stegemann-Hefte); Klingspor-Museum bzw.
   HathiTrust-Watch (Koch: Das Schreibbüchlein, seit 01/2026 US-PD).
4. **Leseübungen Wien 1835** bei Bedarf als Quiz-/Lesedrill-Quelle
   erschließen (Cross-Hand, kein Laufform-Material).
