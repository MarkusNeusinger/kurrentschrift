# Glossar — Fachbegriffe und Repo-Redewendungen

> **Status (2026-09-04): lebend.** Nachschlagewerk über die Begriffe, die
> in `docs/`, in Issues/PRs und in der Admin-Oberfläche vorkommen — über
> 300 Einträge, rund 57 000 Token.
>
> **Diese Datei liest man nicht am Stück.** Sie ist die
> **Nachschlage-Instanz**: Einstieg ist der alphabetische
> [Schnellindex](#schnellindex-alphabetisch), der jeden Begriff seinem
> Themenblock zuordnet (**§1** Schrift · **§2** Architektur & Datenmodell
> · **§3** Mess- und Fit-Vokabular · **§4** Metriken & Benchmarks · **§5**
> Werkbank & Prozess · **§6** Extern/Forschung · **§7** Öffentliche
> Seiten). Für den Einstieg in eine Sitzung steht seit 2026-09-04 die
> Kurzfassung [`kurzglossar.md`](kurzglossar.md) auf der Pflichtlektüre —
> 77 Begriffe, je ein bis zwei Sätze, jeder mit dem Sprung hierher; sie
> ersetzt dieses Glossar nicht, sie ersetzt nur das Am-Stück-Lesen.
>
> **Was ein Eintrag verspricht.** Einen allgemeinverständlichen Teil ohne
> Vorkenntnisse und, wo es etwas zu verankern gibt, den Modul-, Formel-
> oder Konstantennamen zum Weitergraben. Kein API-Verzeichnis: aufgenommen
> ist, was ein Leser in Prosa, Issue oder UI antrifft.
>
> **Nachzieh-Pflicht: jedes Doc und jeder PR, der einen neuen Fachbegriff
> oder eine neue Kennzahl prägt, legt im selben Zug einen Eintrag hier an**
> — Themenblock **und** Schnellindex (Regel auch in `CLAUDE.md`
> § „Working guardrails“, `.github/copilot-instructions.md` und den Skills
> `/write-docs` + `/open-pr`). Erreicht der Begriff danach Code, die
> Agenten-Dateien oder PR-Beschreibungen, folgt der Kurzeintrag im
> Kurzglossar (Schwelle und Ausschlüsse stehen in dessen Kopf).

Dieses Projekt hat über die Läufe hinweg eine eigene Sprache entwickelt —
teils Paläografie („Schwellzug“, „Duktus“), teils Architektur („Laufform“,
„Bibliothekseinheit“), teils Hausmaße aus einzelnen Messrunden
(„gen_chamfer“, „Bézier-Handle-Floor“, „degenerierte Solves“). Wer neu
dazukommt — Mensch oder KI — trifft diese Wörter im Fließtext, ohne dass
sie dort noch einmal erklärt werden.

**Wie dieses Glossar gedacht ist:** jeder Eintrag hat einen
allgemeinverständlichen Teil (keine Vorkenntnisse nötig) und, wo es etwas
zu verankern gibt, einen technischen Nachsatz mit dem Formel-, Modul- oder
Konstantennamen. Der Nachsatz ist bewusst *Anker-Vokabular*: einen Eintrag
in einen beliebigen KI-Chat kopiert, hat man genug Stichworte, um
tiefer zu graben („Erklär mir Tikhonov-Regularisierung“, „Was ist eine
Chamfer-Distanz“), ohne dass dieses Repo die halbe Numerik-Vorlesung
mitliefern muss.

**Was es nicht ist:** keine API-Referenz und keine Vollzählung aller
Bezeichner. Aufgenommen ist, was ein Leser in Prosa, Issue oder UI
antrifft und nicht raten können soll.

---

## Schnellindex (alphabetisch)

Die Ziffer nennt den Themenblock unten: **§1** Schrift & Paläografie ·
**§2** Architektur & Datenmodell · **§3** Mess- und Fit-Vokabular ·
**§4** Metriken & Benchmarks · **§5** Werkbank & Prozess ·
**§6** Extern/Forschung · **§7** Öffentliche Seiten.

- **A** — `add_header`-Vererbungsfalle §2 · Anker · Sample · Schritt §4 · Abdeckungsmatrix §4 · abgeschnittener Anstrich §4 · Absetzen §1 · Absprung (Lotse) §4 · Arm-Datei (humanbench) §4 · Abstandsprofil (Werkbank) §5 · Aggregat §2 · AIoU §6 · Allograph §1 · Analysis-by-Synthesis §2 · Anker §2 · Anker im leeren Papier §4 · Anstrich/Auslauf §1 · Auftragskorb §5 · Auftragskorb-Protokoll §5 · Ausbau-Quote (→ Bestandsbericht) §5 · Ausgangsschrift §1 · Ausreißer §4 · Austritts-Trim (`exit_trim`) §2
- **B** — Bandzugfeder §1 · Bbox §2 · Beleg (Eigenhand) §5 · bench_loss §4 · Bereich daneben §4 · Berührung (Struktur-Zähler) §4 · Bestandsbericht §5 · Bestätigung A/B (→ Referenzsatz) §4 · Bewertungsdurchgang §4 · Bézier-Handle-Floor §3 · Biasing §6 · Bibliothekseinheit §2 · bindend §5 · blinde Wiederholung §4 · Bogen (Eigenhand) §5 · Bogen-Kappe §4 · bogengleich §3 · Bot-Site (`bot_fetch`) §2 · Bowl-Exit-Tuck §2
- **C** — CER §6 · Chamfer-Distanz §4 · Changelog-Fragment §5 · Chart §2 · Chor (geplant) §4 · Chronik (tracebench) §4 · Cusp-Connector §3
- **D** — dconn §4 · Deckung §3 · Deckungslücke §3 · Doppel-X-Duplikat §4 · Duell-Ansicht §4 · Duell-Namen §4 · degenerierte Solves §3 · Degeneriewächter §3 · d_end (verworfen) §4 · Dice §4 · Dissektion §2 · doff §4 · DTW §6 · dtw_xh §4 · Duktus §1 · Duktus-Prior §1 · Durchstoß-Kriterium §4
- **E** — Echtheitsfrage §4 · EDT §3 · Eigenhand-Buchführung §5 · Eigenhand-Erfassung §5 · Einrichtungs-Wizard §5 · Endblende (Laufform) §2 · Entdrillung §4 · Entwurfsnetz des Wizards §5 · Ernte §2 · Erstbeleg-Quote (→ Bestandsbericht) §5 · extrapoliertes Landmark-Ziel §3
- **F** — Fassung (Eigenhand) §5 · Federprobe §7 · Federtypen §1 · Federwinkel §1 · Fehler-Taxonomie §4 · Fehlerschicht (`apiErrorText`) §5 · Feinschliff (geplant) §4 · Fenster-Versatz §4 · FID §6 · Fixture-Wurzel §4 · Form-Abstand (Laufform) §2 · Frame-Gate (`frame_stale`) §4 · Fremdtinte §3 · Frozen-Reference-Regel §4 · Fuge §1 · Fußwende §2
- **G** — G1-/G2-Stetigkeit §6 · gefüllte Ringe §4 · gen_chamfer §4 · grid_step_crop_px §4 · Gewackel §4 · Girlande §2 · Glätte-Sensor §2 · Gleichzug §1 · Gleichzug-Audit §4 · glyph_key §2 · Gradientenzerlegung §4 · Grundstrich/Haarstrich §1 · Grundtafel §7 · gut (`G`) §4 · Gute-Fortsetzung §4
- **H** — H0–H5 §5 · Hand §2 · HTG §6 · HTR §6 · Huber-Kappung §3 · humanbench §4 · HWD §6
- **I** — IndexNow §2 · Ink gap §3 · Instance §2 · Isochronie §6 · Iterationsdeckel §3
- **J** — Junction-Pinch §4 · Junction-Verschiebung §3
- **K** — k0-Protokoll §4 · Karten-Abdrift §4 · Karten-Soll-Vollständigkeit §4 · Kettenfit §3 · Kill-Kriterium §3 · klassenbewusste Korrespondenz §3 · Klassenregel §2 · Knick am Rand §4 · komplett daneben §4 · Komposition §2 · Konnektor §2 · Kopf-Gate (Laufform) §2 · Kopplungshöhe §1 · Kopplungs-Stub §3 · Korb-Notiz §5 · Korrespondenz-Kappe §3 · Kreuzungs-Landmarke §3 · Kringel-Exit §2 · Kurzglossar §5
- **L** — Labs §4 · Landmarken-Term §3 · Laufform §2 · Laufform-Lücke §2 · Laufform-Topologie-Wächter §3 · Lineal-Soll-Budget §4 · Lotse (Arbeitstitel) §4 · laufform_dev_xh §4 · L-BFGS-B §6 · LDTW §6 · lebend §5 · Lese-Budget §5 · like-for-like Gate §3 · Lesart §1 · Lesart prüfen §7 · Lese-Quiz §7 · Lesefalle §1 · Lesetafel §7 · Ligatur §1 · Lineatur §1 · loss §4
- **M** — M1–M4 (Kettenfit-Kennzahlen) §3 · M0–M7 (MVP-Meilensteine) §5 · M4-Fit §3 · MAD §4 · Marke §4 · Marken-Claim-Trennung §3 · Marken-endständige Assembly §4 · matched arc §3 · MDN §6 · meas §4 · Messboden §4 · Messjournal §5 · Mindestbelegung (Eigenhand) §5
- **N** — Nachbarbindung §4 · Nachfahr-Stand §5 · Naht §3 · Naht-Anteil §3 · Naht-Winkel (`seam_deg`) §4 · Natürlichkeitsmetrik §4 · Nullprobe §4
- **O** — Offenbacher §1 · Open-Core-Moat §2 · Origin-Geheimnis §2 · Ortsmarker §4 · Ortsprüfung §4 · Override §2
- **P** — Paar-Aggregat §2 · Paar-Editor §5 · paariger Blindvergleich §4 · pair_loss §4 · Passmarken §5 · Plateau-Anker §4 · Platzierungsschranke §3 · Prerender-Pfad (Crawler) §2 · Prior-Landerichtung §2 · Priming §6 · Provenance §2 · Provenienz-Stempel §4 · Prüfstein §4
- **Q** — Quelle §2
- **R** — R1–R5 §5 · Radierer §5 · Rastersuchlauf §3 · Ratsche (Ratschen-Budget) §3 · Re-Baseline §4 · Rechteck-Reparatur §5 · Referenzsatz (nachgefahren) §4 · Registrierung §2 · Regel-Fix vor Override §5 · Render-Kontext §2 · Report-Only-Woche §2 · Report-Spalte §4 · reproduced §5 · Reservierungs-Veto §4 (→ Lineal-Soll-Budget) · Residualprofil §4 · resolution §5 · Restart-Klasse (`CAP_RESTART_BASES`) §2 · Retrace §1 · Retrace-Guard §3 · Retrace-Segment §4 · Rettungsweg §5 · Route G §4 · Rückgabe an Autor §5 · Rückhaltemenge §4
- **S** — Same-Hand-Disziplin §4 · Schienen-Auslauf §3 · Schräglage §1 · Schreib-Karte §2 · Schreibtafel §7 · Schriftkunde (Seite) §7 · Schnittband §5 · Schnittmarken §5 · Schwellzug §1 · Score §4 · Segment-Attribution §4 · Sehnen-Schwelle §3 · Sektion §2 · Shaping §2 · Sieb-Disziplin (→ Siebung) §5 · Siebung §5 · Sigma-Lognormal §6 · Skelett §3 · Slant-Spalte §4 · Slot §2 · Specimen §2 · Spike-Verhältnis §4 · Spitzfeder §1 · Spline-Basis-Median §2 · Sprung-Gate (Laufform) §2 · `stage` (work_items) §5 · Stamm-Rückpass §2 · Stand-Block §5 · Status-Vokabular §5 · Stehendes Setup §5 · Streifen (Eigenhand) §5 · Streifenkartei §5 · Streifenplan §5 · Stiftmarke §5 · St-Ligatur §1 · Stub §3 · Stufen-Doktrin §5 · Style §2 · Sütterlin §1
- **T** — Tafel §2 · tail_adapt/head_adapt §3 · tail_stub_delta §3 · Template §2 · Tikhonov-Regularisierung §3 · Tintenabstand §4 · Tinten-Evidenz-Maske §3 · Tintenfolger §3 · Tintenlücke §3 · Tinten-Zuweisung per Strecke §3 · Topologie-Reparatur §3 · Topologie-Wächter §3 · tracebench §4 · Trajektorien-Recovery §6 · Trefferfläche (`hitArea`) §5 · Triage-Pflicht §5 · Typo-Boden §5
- **U** — Unantastbare Lineatur §7 · Unvollständige Wortprobe §5
- **Ü** — Übergang §2 · Übergangs-Generator §2 · Übergangsraum §5 · Überlappungsterm §3 · Übungsblatt §7 · understanding §5
- **V** — Variante §2 · Vereinfachungs-Gate §5 · Verfahrensseite §4 · Vier Augen (geplant) §4 · Vereinigungsfenster §3 · Verlässlichkeitsschranke §4 · Verworfen §5 · Vorkommensschranke §2 · Vorlage §2 · Vorregistrierung §4 · Vorschub-Kalibrierung §2 · Vorschrift §1
- **W** — W1–W6 §5 · Warp §3 · Werkbank §5 · wordbench/glyphbench/pairlab/chainbench §4 · work_items §5 · Wort-Ausschnitt (Eigenhand) §5 · Wort-Editor §5 · Wortrunde (humanbench) §4 · Wort-Trace §2 · Wortvorrat §5 · Wurzel-Digest (`root_digest`) §4
- **X** — x-Höhe (`xh`) §1
- **Z** — Zeichenbreiten-Mittel (`AVG_ADVANCE_UNITS`) §7 · Zeilen-Gate (Laufform) §2 · Zeilenmarke §7 · Zelle einsetzen §5 · zirkuläres Kriterium §4 · zonale Rückweisung (`zonal`) §3 · „Zug um Zug“ §7 · Zwei Stillen (Leerzustands-Regel) §5 · Zwei-Drittel-Gesetz §6 · Zögling (geplant) §4

---

## §1 Schrift und Paläografie

**Duktus** *(ductus)* — die Art, wie ein Buchstabe *geschrieben* wird:
Reihenfolge der Striche, Richtung, wo die Feder abgesetzt wird. Nicht die
fertige Form auf dem Papier, sondern der Weg dorthin. Zwei Buchstaben
können identisch aussehen und einen völlig verschiedenen Duktus haben.
*Technisch:* deutsche Fließtext-Schreibung mit k (Duden), Code-Identifier
bleibt `ductus` → sprachregelung.md §2 · allgemein.md §3

**Duktus-Prior** — die zentrale Idee des Projekts: Weil aus einem Foto
nicht ablesbar ist, welcher Ast einer Kreuzung zu welchem Strich gehört
und was zuerst geschrieben wurde, gibt man dieses Wissen *vorher* vor —
als von Hand autorisierten Duktus je Buchstabe. „Prior“ ist der
statistische Begriff für Vorwissen, das man in eine Schätzung einbringt.
→ architektur.md §2

**Allograph** — zwei verschiedene Schreibformen desselben Buchstabens, die
beide korrekt sind, aber an verschiedenen Stellen stehen. Prominentestes
Beispiel: das lange ſ (im Wortinneren) und das runde s (am Wortende) sind
*verschiedene* Buchstabenformen mit verschiedenem Duktus, nicht dasselbe s
mit anderem Anschluss. Im Repo sind Allographe daher getrennte Glyphen
(`longs` vs. `s`), nicht Varianten. → architektur.md §3 ·
orthographie-regeln.md §1

**Lesart** — ein echtes Wort, das ein gelesenes Wort in der deutschen
Schreibschrift ebenso gut sein könnte: gleiche Länge, jeder abweichende
Buchstabe ein dokumentierter Verwechsler (Lesefalle) des gelesenen. Die
Lesart-Seite (`/lesen/vergleichen`) bietet sie zur Vermutung des Lesers
an, gereiht nach der Summe der Verwechsler-Abstände (ein dokumentiertes
Paar = 1), Bankwörter vor Wörterbuch. Kein Buchstabentausch ohne Wort
dahinter (Autor, 2026-08-30). Im Repo: `core/lesarten` (Schlüssel
`lesart_key` = jeder Buchstabe durch seine Verwechsler-Klasse ersetzt,
`rank_readings`), Tabelle `lesart_forms`, `GET /lesarten?text=`.

**Lesefalle** — ein Buchstabenpaar, das sich in der deutschen
Schreibschrift so ähnelt, dass Leseanfänger es regelmäßig vertauschen,
und das ein benennbares Merkmal trennt — meist ein einziges: n und u
nur der u-Bogen, e und n die Enge der Züge, i und j die Unterlänge; bei
ſ und f sind es zwei: oben die Schleife des f gegen die Spitze des ſ,
dann der Querstrich, den nur das f hat;
dazu die Positionsregel des runden s (Silben-/Wortende) und die
Versalien-Cluster L/K/R, N/M, B/V, für die der Katalog kein einzelnes
Merkmal nennt. Im Repo: der Katalog `app/src/sections/quiz/lesefallen.ts`
(Sätze in `locales/de/quiz.ts`, `play.rules`), aus dem das Lese-Quiz nach
einem Fehlgriff die Regel zeigt — gezeigte Form gegen geratenen
Buchstaben, richtungsbewusst, und für Paare ohne dokumentiertes Merkmal
bewusst keine Erklärung. Die Schriftkunde-Seite führt dieselben Fallen
unter „Buchstaben-Besonderheiten“. → orthographie-regeln.md §1/§3 ·
vision.md Ziel 4

**Ligatur** — eine auf der Lehrtafel *als eigene Einheit gelehrte*
Buchstabenverbindung. Der geschlossene Satz im Projekt: `ch` · `ck` · `tz`
· `ſt` · `St` · `qu` · `ß`. Sie werden als eigene Glyphen mit eigenem Duktus
gespeichert („enumerieren, nicht generieren“) — im Gegensatz zu beliebigen
Buchstabenpaaren, deren Verbindung erzeugt wird. Fehlt der Canonical eines
Clusters, zerfällt der Slot beim Shaping in seine Einzelbuchstaben
(Rückfall, `ch` · `ck` · `tz` · `ſt` · `St` · `qu`); `ß` bleibt davon
ausgenommen und ATOMAR — sein ſs/ſz-Zerfall ist selbst eine
Allographen-Frage, und ein naiver Split schriebe mitten im Wort ſſ.
→ architektur.md §4 · write-api.md „Pipeline“ · „St-Ligatur“

**St-Ligatur** — das eine GROSS-Cluster des geschlossenen Ligatur-Satzes
(Korb #9, 2026-08-30): die 1922er Sütterlin-Vorlage schreibt das große S
ohne Absetzen in das kleine t weiter, während andere Groß-Paare (`Sc` …)
das S absetzen und an der Grundlinie neu ansetzen. Glyph-Key `St`; erkannt
wird exakt großes S vor kleinem t (`STEIN`/`sT` zerfallen nie, eine Fuge
dazwischen blockiert das Cluster). Bis der Autor die Tafel-Form im Wizard
nachgefahren hat, greift der Ligatur-Zerfall: der Slot schreibt sich als
S + t mit generiertem Übergang, exakt wie vor der Aufnahme in den Satz.
`core/shaping.py` (`_LIGATURES`) · TS-Zwilling `app/src/domain/glyphs.ts`
(`COMB`). → „Ligatur“ · architektur.md §4

**Fuge** *(morpheme boundary)* — die Nahtstelle in einem zusammengesetzten
Wort (Donners·tag, Aus·flug). Sie ist orthographisch relevant, weil dort
das runde s steht, obwohl es mitten im Wort sitzt. Da die volle Regel noch
nicht implementiert ist, gibt es einen manuellen Marker: ein `|` im
Eingabetext erzwingt das Schluss-s und verhindert, dass eine Ligatur über
die Fuge greift (`Donners|tag`).
*Technisch:* `core/shaping.py::FUGE`, Zwilling `app/src/domain/shaping.ts`
→ orthographie-regeln.md §1.2

**Lineatur** — das Liniensystem im Schulheft. Vier Linien mit deutschen
Namen, die im Repo (Code-Kommentare, UI, Docs) durchgängig gelten:
**Oberlinie · Mittellinie · Grundlinie · Unterlinie**; die drei Räume
dazwischen heißen **Oberlänge · Mittellänge · Unterlänge**. Das
Verhältnis der drei Zonen ist ein Schriftmerkmal (Sütterlin 1:1:1,
Offenbacher 2:3:2, Kurrent 2:1:2). → allgemein.md §1

**Vorschrift** — auf einem Übungsblatt die vorgeschriebene Musterzeile, die
der Lernende in den Leerzeilen darunter nachschreibt. Auf der Seite: der
Übungstext des Übungsblatts (`/schreiben/uebungsblatt`), zeilenweise in der
nachgeschriebenen Vorlage gesetzt — komponiert wie in der Federprobe
(`GET /write/word`), auf die Zeilen der gewählten Lineatur gelegt
(Mittelband = x-Höhe), darunter auf Wunsch eine graue Kopie zum Nachspuren
und Leerzeilen zum Nachschreiben; was nicht auf das Blatt passt, wird
benannt statt gezeichnet. *Technisch:*
`app/src/lib/uebungstext.ts` (`placeText`), Browser-Hälfte
`sections/worksheet/useWorksheetText.ts`.

**x-Höhe (`xh`)** — die Höhe der Mittellänge, also eines Buchstabens ohne
Ober- und Unterlänge (klassisch: die Höhe des x). Sie ist die
**Maßeinheit des ganzen Projekts**: Anker, Abstände, Toleranzen und fast
alle Kennzahlen stehen in x-Höhen, nicht in Pixeln — nur so sind
verschieden große Scans vergleichbar. „0,19 xh“ heißt: 19 % der
Mittellängenhöhe.

**Schräglage** *(slant)* — wie schräg die Schrift steht. **Messkonvention
im ganzen Repo: Winkel des Abstrichs zur Grundlinie, 90° = senkrecht.**
Sütterlin steht senkrecht (90°), Kurrent um 1900 bei 60–70°, die
Loth-Tafel von 1866 gemessen bei ~50°. Feld `slant_deg`. → allgemein.md §2

**Schwellzug** *(pressure-driven stroke-width modulation)* — das An- und
Abschwellen der Strichbreite bei der elastischen **Spitzfeder**: Druck
spreizt die Federzinken, der Abstrich wird dick, der Aufstrich bleibt
haarfein. Charakteristisch für Kurrent.

**Gleichzug** — das Gegenteil: gleichbleibende Strichstärke ohne
Druckwechsel, geschrieben mit einer Redis-/Gleichzugfeder.
Charakteristisch für Sütterlin — Ludwig Sütterlin wählte sie bewusst,
damit Kinder nicht auch noch Druck dosieren müssen.

**Grundstrich · Haarstrich** — Grundstrich (= Abstrich, abwärts) ist der
breite Hauptstrich, Haarstrich (= Aufstrich, aufwärts) die feine Linie.
Bei der Spitzfeder ist das ein Druck-, bei der Bandzugfeder ein
Richtungsunterschied. → allgemein.md §3

**Absetzen** *(pen lift)* — die Feder vom Papier abheben. Ein Buchstabe
kann aus mehreren Zügen bestehen (das u hat zwei Abstriche mit einem
Absetzen dazwischen); die Engine darf über ein Absetzen **nie** eine Linie
ziehen.
*Technisch:* flacher `raw_path` mit `pen_up`-Markern + `stroke_starts` in
`trace_meta`; Kanonisierung, Diagnose und Fit behandeln jeden Zug einzeln.

**Anstrich · Auslauf** — der kleine Zustrich, mit dem ein Buchstabe
*beginnt* (Anstrich), und der Ausläufer, mit dem er *endet* (Auslauf). Im
verbundenen Wort werden sie nicht gespeichert, sondern vom Composer aus
dem Slot-Kontext gesetzt — am Wortanfang bleibt der Anstrich stehen, in
der Wortmitte geht er im erzeugten Übergang auf. → architektur.md §3/§4

**Retrace** *(Rückzug)* — die Feder fährt auf derselben Linie zurück, die
sie gerade gezogen hat (typisch beim langen ſ, beim t, beim f). Für die
Bildanalyse ein Problemfall: zwei Striche liegen als eine Tintenspur
übereinander. → qualitaetsmetrik.md §5

**Kopplungshöhe** *(coupling)* — auf welcher Höhe ein Buchstabe an seinen
Nachbarn andockt: unten an der Grundlinie oder oben im Mittelband. Eine
Eigenschaft des Buchstabens, aber sie steht in der **Klassenregel**, nicht im
Template: `core/compose.py::HIGH_COUPLE_BASES` koppelt Rundkörper
(e/a/o/c/d/g/q) oben am Scheitel, Arkadenbuchstaben (n/m/i/u) unten über die
Grundlinien-Girlande. Das früher pro Glyph autorierte Feld
`entry/exit.coupling` wurde von nichts gelesen und ist entfernt.
→ architektur.md §3

**Federtypen** — **Spitzfeder** (elastisch, Breite kommt aus dem Druck →
Schwellzug, Kurrent) · **Bandzugfeder / Breitkantfeder** (breite,
schräg gehaltene Schneide, Breite kommt aus der *Richtung*, Offenbacher) ·
**Redisfeder / Gleichzugfeder** (runder Schreibkopf, Breite konstant,
Sütterlin). Im Code entscheidet der `width_resolver` des Stils, welches
Modell beim Rendern gilt. → federmodelle.md §1

**Federwinkel** *(nib angle, `alpha`)* — der Winkel, in dem die Schneide
einer Bandzugfeder zur Schreiblinie steht. Bei der Offenbacher lehrt Koch
konstante 15° — daraus folgt das ganze Breitengesetz der Schrift.
*Technisch:* `w(φ) = W·|sin(φ−α)| + t·|cos(φ−α)|` in
`core/widths.py::BroadNib`; `alpha` ist die gelehrte Konstante und wird
nie pro Quelle gefittet. → federmodelle.md §2

**Ausgangsschrift** — die an der Schule gelehrte Norm-Schreibschrift. Das
Projekt kennt drei: **Kurrent** (bis ~1900 gebräuchlich, schräg,
Spitzfeder) · **Sütterlin** (1911, senkrecht, Gleichzug, 1:1:1) ·
**Offenbacher** (Rudolf Koch 1927, Bandzugfeder, 2:3:2). Achtung
Begriffsfalle: „Sütterlin“ wird umgangssprachlich für *jede* alte deutsche
Schreibschrift benutzt. → schriftkunde/allgemein.md §5

---

## §2 Architektur und Datenmodell

**Analysis-by-Synthesis** — die Grundmethode: Statt aus dem Bild eine Form
*herauszulesen*, wird eine bekannte Form so lange an das Bild *angepasst*,
bis sie passt. Das Bild liefert Geometrie und Strichbreite, das
Duktus-Modell liefert Strichreihenfolge und Kreuzungsauflösung.
→ architektur.md §2

**Bibliothekseinheit** — der Schlüssel, unter dem eine kanonische Form
liegt: **`(style, glyph, variant)`**. Also: welche Schriftfamilie, welche
Glyphe, welche gelehrte Formvariante. Die Wortposition gehört seit dem
Positions-Rückbau (Redesign R2, Migration `0017`) **nicht** dazu — sie ist
Render-Kontext, keine eigene Zeile. → architektur.md §3

**Style** *(Grundvorlage / Schriftfamilie)* — Kurrent · Sütterlin ·
Offenbacher. Trägt die Voreinstellungen der Schrift: `width_resolver`,
`default_slant_deg`, `default_style_ratio`. Tabelle `styles`.

**Hand** — **ein Schreiber**. Die zentrale Trennlinie der Statistik: über
Hände wird **nie** gemittelt. Eine gerenderte Schrift hängt immer an genau
einer Hand; fremde Hände sind Vergleichsmaterial, nie Vorbild. Tabelle
`hands`, Referenzhand des Projekts: `suetterlin-1922-norm`.
→ handmodell-stufenplan.md §2/§5

**Quelle** *(source)* / **Vorlage** — die Herkunft der Bytes: eine
Lehrtafel (`kind: chart`) oder ein Manuskript. Im Admin heißt sie
„Vorlage“, und **alles im Admin gehört zu genau einer gewählten Vorlage**
— deshalb ist die Vorlagen-Auswahl der Eingangsschritt. Tabelle `sources`.

**Tafel · Chart · Chart-Zelle** — die gedruckte Buchstabentafel eines
Lehrbuchs (Loth 1866, Sütterlin-Leitfaden 1922, Koch 1928, Petzendorfer
1889) und die einzelne Zelle darin, aus der ein Buchstabe geschnitten
wird. „Chart-Zeile“/„Tafel-Form“ = die aus der Zelle autorisierte
Grundform (Variante 0), im Gegensatz zur gemessenen Laufform.

**Bbox** — die Zuschnitt-Konfiguration einer Chart-Zelle: Rechteck,
Radierer-Striche, gemalte Tinte, Lineatur-Kalibrierung, eingesetzte
Spender-Zellen (`patches`), Anzahl der Anker, `locked`. Tabelle `bboxes`.
*Technisch:* `core/chart.py` ist das Lade- und Zuschnitt-Modul —
`crop_with_mask` komponiert den freihändigen Radierer (`mask_strokes`),
die eingesetzten Spender-Zellen (`patches`) und den manuellen
Tinte-Pinsel (`ink_strokes`) in den Ausschnitt.

**Template** — die kanonische Form einer Glyphe: **Anker** (die Stützpunkte
der Mittellinie), `half_widths` (das gemessene Breitenprofil),
`raw_path` (der von Hand gezeichnete Stylus-Pfad), `entry`/`exit`/`advance`.
Tabelle `templates`.

**Anker** *(anchors)* — die Stützpunkte, aus denen die Mittellinie eines
Buchstabens besteht (Voreinstellung ~120 pro Glyphe). Fast alle Messungen
des Projekts sind „pro Anker“ — Median pro Anker, MAD pro Anker,
Auslenkung pro Anker.

**Variante** *(variant)* — eine zweite, **von der Norm ebenfalls
sanktionierte** Form desselben Buchstabens (auf Lehrtafeln als „A = A“
notiert). Kein Fehler und keine Abweichung, sondern eine eigene
Template-Zeile. Reserviert: **Variante 100 = Laufform**.

**Laufform** — die aus echten Wortvorkommen *gemessene* Form eines
Buchstabens, wie er im fließenden Wort wirklich aussieht (breiter,
geneigter, verformter als die isolierte Tafelform). Sie liegt als
Template-Variante 100 und wird nur in fließenden Läufen benutzt.
*Technisch:* `LAUFFORM_VARIANT = 100` (`core/database/models.py`),
Composer-Zugriff über `laufform_by_key`; entsteht als **Ableitung** aus
den Aggregaten via `POST /hands/{id}/aggregates/apply-laufform`.
→ handmodell-stufenplan.md H1

**Laufform-Lücke** — der Zustand eines Glyphen OHNE gespeicherte
Laufform-Variante: die Komposition setzt die rohe Chart-Form ein, und
die Schicht, die per Architektur die Hand-Breite trägt, schweigt.
Stand `aug19`: 15 der 34 Fixture-Glyphen der Sütterlin-1922-Root
(alle Versalien, dazu ae · b · f · k · s · ue · v) — der `aug19`
diagnostizierte Haupt-Anteil der „Karten-Form-Decke" der Lotse-Route
(G-Kopf, W-Apexe, k-Kringel liegen alle in der Lücke). *Technisch:*
Glyph ohne `variant=100`-Zeile; Lücken-Schluss-Arm LF1 →
messjournal.md §14 („Laufform LF1")

**Endblende (Laufform)** — die Chart-Rückblendung an den FREIEN
STRICHENDEN einer Laufform-Zeile: über ein Bogen-Fenster W vom
Strichende blendet die Zeile zur Chart-Geometrie zurück, starr am
Fensterrand angehängt (eine rein verschobene Laufform bleibt
Fixpunkt). Zwei Modi: `full` (LF5, der ganze Rest) und `transverse`
(LF6, nur der Quer-Anteil zur Chart-Endrichtung — der Längs-Anteil ist
die Ausdehnung der Hand). Anlass: die gefitteten Endanker driften zur
Nachbar-Tinte (t-Anker 0 zum Kringel, K-Endanker auf den Anstrich des
u), und die Grammatik liest ihre Tangenten genau dort. **Beide Modi
am Wort-Lineal verworfen (`aug29`):** bei gut belegten Buchstaben sind
die Laufform-Enden die Hand, nicht Drift. *Technisch:*
`core/laufform.py::blend_stroke_ends`, Knopf `LAUFFORM_END_WINDOW`
(0 = aus), Stempel `trace_meta.laufform.end_window`/`end_mode`;
Kandidaten-Karten: `tools/laufform/endblend.py` → messjournal.md
§14 („Laufform LF5"/„LF6"), Rettungswege tintenfolger.md §7.9

**Prior-Landerichtung** — die Regel-Idee (Übergänge J1, `aug29`),
dass die Grammatik B's LANDErichtung (Klassen-Entscheidung
Align/Flanke/Sameslant/Ritt, Steigung der Pass-through-Linie) am
ersten Zug der CHART-Zeile misst, wenn ein Slot seine Laufform
rendert — die Geometrie bleibt Laufform, nur die Richtung kommt vom
Duktus-Prior. Gemessen (a) grün (−0,0010), aber die Zielstelle (n→t)
unverändert, weil die Kopplung das t nicht erreicht
(`ALIGN_MAX_ENTRY_Y`, Haken-Segment im Kandidaten-Scan) — nicht
adoptiert, wird in J2 („Anstrich-Verlängerung in den Schaft")
mitgemessen. → messjournal.md §14 („Übergänge J1"/„J2")

**Kopf-Gate (Laufform)** — die dritte Prüfung des Zeilen-Gates (§14
LF9, `aug29`): der KOPF einer Laufform-Zeile — die Landerichtung ihres
ersten Zugs über dasselbe Bogenfenster, mit dem die Übergangs-Grammatik
landet (`TANGENT_WINDOW_UNITS`), gemessen auf der GERENDERTEN
Mittellinie (die Anker-Polylinie liest die dichten, eingerollten
Kapitalen-Köpfe bis 33° falsch) — darf die Richtung der Tafelzeile um
höchstens `LAUFFORM_HEAD_DEVIATION_MAX` = 15° verlassen, kein Override.
τ ist aus der Doktrin abgeleitet, nicht aus den Daten: das halbe
Align-Band (25–55°) der Grammatik — ein Kopf, der weiter abdreht,
ändert die Übergangsklasse, die die Grammatik an der Landung
entscheidet (J1-Befund), und widerspricht dem, was die Kanonisierung
verspricht („the tangents stay": die Zeile trägt die Eintrittstangente
der Tafel als Metadatum). Gefunden am Korb-#7-t: Anker 0 der n=4-Zeile
liegt RECHTS von Anker 1, der Kopf startet mit 104° gegen 37° Tafel —
der Rückwärts-Schlenker im Wort, den das Sprung-Gate nicht sieht (t
2,11 < 2,95). Auf der Root vom 29.08.: t 46°, E 48°, K 41°, f 28°, v
27°, k 17° über τ (alle am 29.08. in Prod gelöscht), m mit 14,9° die
knappste vertraute Zeile darunter.
*Technisch:* `core/laufform.py` (`head_deviation`, `head_gate`),
Skip-Grund `head_deviation` mit `head_deviation`/`head_max`,
Inventar-Spalte `head°` → messjournal.md §14 („Laufform LF9")

**Glätte-Sensor** — die Kennzahl, die das Zittern einer Laufform-Zeile
zum ersten Mal benennt (§14 LF11, `sep02`): wie oft die GERENDERTE
Mittellinie ihre Krümmung umkehrt, je x-Höhe Bogenlänge. Jeder Zug wird
auf 0,02-xh-Schritte resampelt (ein Drittel des Nib-Radius), der
Drehwinkel je Schritt gebildet und jeder Vorzeichenwechsel gezählt, bei
dem mindestens eine der beiden Drehungen über 3° liegt — das trennt die
Zacke vom Rundungsrauschen. Federabsätze zählen nie, wie beim
Sprung-Gate. Der Sensor musste gebaut werden, weil KEIN eingefrorenes
Lineal die Größe sieht: Wort-Bench und Tintenfolger resampeln den
Zickzack weg, bevor sie werten — die Zeilen der Root zackten mit 6,9
gegen 0,2 der Tafel, ohne dass eine Zahl je darauf reagiert hätte.
Berichtsspalte, kein Gate. *Technisch:* `core/laufform.py`
(`zigzag_rate`, `smoothness_gap`, `ZIGZAG_STEP_UNITS`,
`ZIGZAG_TURN_MIN_DEG`), Inventar-Spalte `zig` →
messjournal.md §14 („Laufform LF11")

**Spline-Basis-Median** — die glatte Zwillingsform des Per-Anker-Medians
(§14 LF11, `sep02`): statt jeden der 120 Anker einzeln zu medianisieren
— wobei nichts im Modell Nachbarn koppelt und das Eigenrauschen des
Schätzers als Zickzack in die geschriebene Zeile durchschlägt — wird
jedes Vorkommen je Zug per kleinster Quadrate auf eine geklammerte
kubische B-Spline projiziert, der Median über die KONTROLLPUNKTE
genommen und an den Ankerparametern der Tafel zurück ausgewertet.
Gemeinsamer Parameter ist die Bogenlänge der TAFELZEILE (damit alle
Vorkommen auf dieselbe Basis projizieren), die Ecken des Duktus-Priors
werden Knoten der Vielfachheit 3 (damit eine Ecke Ecke bleibt), und ein
Zug ohne Platz für die Basis behält den Per-Anker-Median und sagt es.
Ein Knopf: der Knotenabstand Δs; gemessen auf {0,08 · 0,16 · 0,32} xh,
bestanden hat 0,16. *Technisch:*
`core/aggregate.py::spline_basis_median`, Kandidaten-Karten trocken über
`tools/laufform/smoothrow.py`; `aggregate_instances` bleibt bis zu einer
Adoption beim Per-Anker-Median → messjournal.md §14 („Laufform LF11")

**Form-Abstand (Laufform)** — der vierte, GEMESSENE und (Stand
`sep01`) NICHT adoptierte Sensor der Zeilen-Gate-Familie (§14 LF10):
wie weit eine Laufform-Zeile die Bahn ihrer Tafelzeile verlässt, je
Anker in Nib-Radien der Tafel. Beide Zeilen werden mit dem Sample-Plan
der Tafel gerendert; je Anker der kürzeste Abstand zur gerenderten
Mittellinie DESSELBEN Zugs der Gegenseite, in beide Richtungen getrennt
(Zeile→Tafel, Tafel→Zeile — kein symmetrisches Mittel); Gate-Größe das
schlechtere p90 der beiden Richtungen (`form_p90`), Median und Maximum
als Empfindlichkeitsprüfungen, dazu der index-weise Abstand
|Zeile_i − Tafel_i| (er trägt den Längs-Anteil, den LF5/LF6 als Breite
der Hand bestätigt haben; der Linien-Abstand ist gegen Gleiten entlang
des Zugs blind, absichtlich). Gebaut für die Form-Drift OHNE Sprung
(v, E, P, k), die das Sprung-Gate durchlässt. Gemessen `sep01` auf dem
Neuexport: τ_form = 1,40 (w — die enger sitzende Schlussschleife, Breite
der Hand), die Referenzzeile P liegt mit 1,01 darunter — der Sensor
misst Geometrie treu, die Abweichung des P liegt im Band der vertrauten
Zeilen; was das Auge an P liest, ist kein Abstandsbetrag. Bleibt
Berichts-Spalte der Bestandsaufnahme, kein Schreibpfad liest sie.
*Technisch:* `core/laufform.py::form_distance`, Inventar-Spalten
`form`/`f-med`/`f-max` + τ_form, `--laufform DATEI.json` für
Kandidaten-Zeilen → messjournal.md §14 („Laufform LF10"),
tintenfolger.md §7.9

**Zeilen-Gate (Laufform)** — die drei Prüfungen, die eine
Laufform-Zeile bestehen muss, bevor sie in den Schreibweg kommt (§14
LF7/LF8/LF9, `aug29`), auf BEIDEN Schreibpfaden (manueller `PUT
…/laufform` wie `apply-laufform`): (1) der **Boden**
`LAUFFORM_MIN_OCCURRENCES` (n ≥ 3), nur durch die ausdrückliche
Autor-Aussage `?min_occurrences=N` in der Anfrage zu senken; (2) das
**Sprung-Gate**: die Sprung-Ratio der Zeile (`anchor_spike_ratio`,
„Anker im leeren Papier" — derselbe Detektor wie am Ernte-Gate, dort
auf dem Einzelfit) darf `LAUFFORM_SPIKE_RATIO_MAX` = 2,95 nicht
übersteigen, kein Override; (3) das **Kopf-Gate** (eigener Eintrag):
der Kopf der Zeile darf die Landerichtung der Tafel um höchstens 15°
verlassen. Doktrin-Satz dazu: ein Wort-Gewinn am
Pixel-Lineal ist KEIN Aufnahmekriterium für eine Zeile — so kam das
n=1-K in den Schreibweg. Vorher gemessen und verworfen: die
Natürlichkeits-Lücke N(Chart) − N(Zeile) über die §5-Terme (LF7 — sie
verfehlt das K, weil der Anker-Median-Jitter der vertrauten Zeilen den
Glätte-Term stärker trifft als große Wellen); sie bleibt Berichts-Spalte
der Bestandsaufnahme (`tools/laufform/inventory.py`). τ ist
datengetrieben: Maximum der vertrauten Zeilen (n ≥ 3) auf der Root,
aufgerundet — nie von Hand gesetzt. *Technisch:* `core/laufform.py`
(`anchor_spike_ratio`, `spike_gate`, `row_naturalness`), Skip-Grund
`anchor_spike` mit `spike_ratio`/`spike_max` → messjournal.md §14
(„Laufform LF7"/„LF8")

**Schreib-Karte** — die Laufform-Kandidaten-Karte in GENAU der
Gestalt, die ein DB-Write erzeugen würde: die zu schreibenden Zeilen
über der eingefrorenen Root, mit den Autor-Ausschlüssen (`aug26`:
h behält seine Zeile, W bekommt keine, G/h-Chart-Fallback heißt
„keine Zeile"), gemessen auf allen Gates, bevor eine Zeile die DB
sieht. Der Begriff trennt „die Karte, die gemessen wurde" (LF3b
`aug19`, nicht mehr auf der Platte) von „der Karte, die geschrieben
wird" — eine neu gerechnete Karte ist nicht automatisch die
freigegebene. *Technisch:* gepatchte Fixture-Root
(`templates_laufform.json` ersetzt, sonst byte-gleich) + Payload
`{glyph_key: {anchors, n_occurrences}}` für `PUT
…/templates/{key}/laufform` → messjournal.md §14 („Laufform
LF3b-W")

**Instance** *(Vorkommen / occurrence)* — **ein** beobachtetes Auftreten
einer Glyphe auf einer Vorlage, samt seinem Fit-Ergebnis. Die Rohdaten der
Statistik: viele Instanzen ergeben ein Aggregat. Tabelle `instances`;
Schwestern: `pair_instances` (ein sezierter Übergang) und `word_instances`
(ein nachgefahrenes ganzes Wort). Vorkommen wirken **nie** direkt auf das
Rendering.

**Aggregat** — die verdichtete Statistik **einer Hand** je
`(glyph_key, variant)`: Median-Anker (= die Laufform-Quelle), MAD-Hülle,
gepoolte Kennzahlen, `n_instances`. Tabelle `aggregates`, Rechenkern
`core/aggregate.py`, Neuaufbau über `POST /hands/{id}/aggregates/rebuild`.

**Vorkommensschranke** *(`LAUFFORM_MIN_OCCURRENCES` = 3)* — die Mindestzahl
an Vorkommen, aus denen ein Median in den **Schreibpfad** übernommen werden
darf. Keine Geschmacksgrenze, sondern die Stelle, ab der der Median
überhaupt arbeitet: bei n = 2 ist er das *Mittel* der beiden, ein einzelner
ausgerissener Fit-Anker landet also mit halber Amplitude in der
geschriebenen Form — genau so bekam das Sütterlin-`S` seinen Zacken oben
rechts. `apply-laufform` erzwingt die Schranke serverseitig (Skip-Grund
`below_min_occurrences`, absenkbar über `?min_occurrences=`); das *Sehen*
eines dünnen Medians bleibt erlaubt, dafür steht die Aggregat-Schranke
`min_n` getrennt daneben (Standard 1, Issue #273). Doktrin wie beim
**Auftragskorb-Protokoll**: eine Regel, die die API *durchsetzt*, statt sie
einem Client zu glauben. Spiegel im SPA: `LOW_N` in `laufformPreview.ts`.

**Paar-Aggregat** *(pair_aggregates)* — dasselbe eine Ebene höher, je
`(hand, left_key, right_key)`: Median-Versatz und per-Punkt-Median der
gemessenen Verbindungslinien plus gepoolte QC. **Bewusst ohne
Apply-Schritt** — die Paar-Statistik ist rein lesend, das Rendering rührt
sie nicht an. `kind` wird dabei **gepoolt**: ein Wort-Join (Abb. 19) und
ein Paar-Drill (Abb. 20) landen in EINER Aggregat-Zeile, weil beide
derselbe Übergang derselben Hand sind; das Wort-/Paar-Platten-Histogramm
bleibt in der gepoolten QC stehen, damit die Mischung sichtbar ist.
Migration `0023`. → handmodell-stufenplan.md H2

**glyph_key** — der Schlüssel einer Glyphe als bare Basis: `a`, `longs`,
`ch`. Seit Redesign R2 ohne Positions-Suffix (früher `a-medial`).

**Slot** — eine Position im komponierten Wort. Das Shaping wandelt Text in
eine geordnete Liste von Slots (je ein `glyph_key` plus Render-Kontext);
Vorkommen, Segment-Bewertungen und Übergänge werden über
`(specimen_id, slot)` zugeordnet.

**Shaping** — Text → geordnete Glyph-Schlüssel: Lang-s-/Rund-s-Regel,
Fugen-Marker, Ligatur-Erkennung, Positionszuweisung, Ziffern und
Satzzeichen als nicht verbindende Glyphen — dazu der **Ligatur-Zerfall**
als Rückfall, wenn der Canonical eines Clusters fehlt: die
Teilbuchstaben erben die Wortposition des Clusters (erster `initial`,
letzter `final`, dazwischen medial), `ß` bleibt atomar
(`core/shaping.py::decompose_ligature_slot` — nur noch Python, der
TS-Zwilling hat seinen Zerfall mit dem serverseitigen Compose-Umzug
abgegeben). Das Shaping existiert **zweimal** —
`core/shaping.py` (maßgeblich) und `app/src/domain/shaping.ts` (nur noch
fürs Quiz); ein gemeinsames Fixture hält beide synchron.

**Komposition** *(compose)* — Slots → fertiges Wort: Buchstaben auf die
Grundlinie setzen, Abstände wählen, Übergänge erzeugen, Diakritika
zurückstellen. `core/compose.py` ist die **einzige** Kompositionsquelle,
gepinnt durch das goldene Paritäts-Fixture `tests/fixtures/compose_golden.json.gz`.

**Übergang · Konnektor** *(connector)* — der Verbindungsstrich zwischen
zwei Buchstaben. Doktrin: **„Übergänge sind Konsequenz, keine Daten“** —
sie werden aus `exit`-Tangente des linken und `entry`-Tangente des rechten
Buchstabens *erzeugt*, nicht gesammelt. Sonst bräuchte man eine
Bigramm-Datenbank für alle ~900 Buchstabenkombinationen.
→ architektur.md §4

**Übergangs-Generator (§4-Generator)** — die erzeugende Logik dahinter:
eine kubische Bézierkurve zwischen Austritt und Eintritt, mit
Klassenregeln für die Sonderfälle. Er ist und bleibt der **Default**.
*Technisch:* `CONNECT_SAMPLES = 24` Stützpunkte, Guards für hohe Exits,
Bogen-Exits, rückwärts zeigende Exits.

**Klassenregel** — eine Regel, die für eine ganze *Klasse* von Übergängen
gilt (alle d-Schleifen-Exits, alle Deckstrich-Bögen, alle r-Arme). Das
Leitprinzip der Optimierung: **eine Klassenregel hebt viele Paare, ein
Override repariert eine Stelle.** Die Klassen sind im Code als
Buchstabenmengen ausbuchstabiert, und diese Konstanten sind die Quelle —
die Liste hier ist ihr Inhaltsverzeichnis (`core/compose.py`, Stand
2026-09-02: 14 positive Mengen plus eine Ausschlussmenge):

| Klasse | Konstante | gilt für |
|---|---|---|
| Bowl-Exit-Tuck | `BOWL_EXIT_TUCK_BASES` | b · c · d · o |
| Arkaden-Eintritt | `ARCADE_ENTRY_BASES` | m · n |
| hohe Kopplung | `HIGH_COUPLE_BASES` | e · a · o · c · d · g · q · ae · oe |
| Oberlängen-Neigung | `ASCENDER_LEAN_BASES` | d |
| Schleifen-Exit | `LOOP_EXIT_BASES` | d · s |
| Kringel-Exit | `KRINGEL_EXIT_BASES` | b · o · B |
| Arm-Fusion | `ARM_FUSE_BASES` | die hohe Kopplung + r · i |
| gleichschräge Kopplung | `SAMESLANT_COUPLE_BASES` | n · m · i · u |
| Unterlängen-Ritt | `DESCENDER_RIDE_BASES` | c · t |
| Bar-Exit | `BAR_EXIT_BASES` | t · f |
| Deckbogen-Austritt | `COVER_ARCADE_EXIT_BASES` | o · b · v · w |
| Deckbogen-Eintritt | `COVER_ARCADE_ENTRY_BASES` | n · m · i · r |
| Schleife in Rundform | `LOOP_ROUND_ENTRY_BASES` | e · a · o |
| Restart-Klasse | `CAP_RESTART_BASES` | S · O · K · P |
| Austritts-Trim (opt-in) | `EXIT_TRIM_EXCLUDED_BASES` *(Ausschluss)* | alle Basen AUSSER Schleifen-, Kringel- und Bar-Exit |

Dazu die Klassen ohne eigene Buchstabenmenge, weil ihre Bedingung
geometrisch ist: Girlande · Gabel-Join · Cusp-Connector ·
Kapital-Übergabe · Arkaden-Diagonale.

**Restart-Klasse** *(`CAP_RESTART_BASES`)* — die Versalien, deren
Verbinder mit einem vorangestellten **Rückzug** beginnt: die Feder fährt
den eigenen Bogen zurück und setzt an der Grundlinie an wie zu einem
frischen Anstrich, statt vom Duktus-Ende aus weiterzulaufen. Tafelform
für S · O · K · P. Wer in der Klasse steckt, ist eine gemessene
Aussage über die Vorlage, keine Vereinfachung: das **B** hat sie
`aug30` verlassen, weil sein autorisierter Duktus auf Mittellinienhöhe
in einem steigenden Abgang endet — der Retrace lief diese Fortsetzung
sinnlos zurück (Korb #8). Die Naht-Winkel-Spalte zählt Verbinder dieser
Klasse aus und meldet sie getrennt, weil ihr „Abgang“ eine gewollte
180°-Kehre ist.
*Technisch:* `core/compose.py::CAP_RESTART_BASES`, `cap_retrace` in
`compose_word` → messjournal.md §14 „Übergänge Korb-Runde `aug30`“

**Vorschub-Kalibrierung** *(advance calibration)* — die Runde, in der
die Abstände zwischen zwei Buchstaben nicht mehr geraten, sondern aus
den **gemessenen** Joins der Platte nachgezogen wurden: 218 sezierte
Übergänge der Worttafel liefern je Klasse, wie weit die Hand vorschiebt,
und die Klassenregeln bekommen diese Werte statt gewählter Konstanten.
Adoptiert wurden vier Stücke (Bowl-Tuck · w/v-Rückwärts ·
longs-Ausnahme · Balken-Steigung) plus der align/nested-Floor der
Folgerunde; die „Arkaden-Luft“ fiel als Beleg-Varianz durch. Die Runde
ist der Grund, warum das Wort-Lineal von 0,110983 auf 0,108091 fiel —
der größte Einzelsprung der Kompositions-Arbeit.
*Technisch:* `core/compose.py` (Welle 2, PR #361/#363) →
messjournal.md §14 „Welle 2 · P1“ und „Welle 2 · P2“

**Girlande** — die tief durchhängende Verbindung, die von einem Exit in
den nächsten Arkaden-Eintritt (n, m, i, u) fällt — das rhythmische
Grundmuster der verbundenen Schrift.
*Technisch:* `GARLAND_*` in `core/compose.py`.

**Kringel-Exit** — die Klassenregel für Buchstaben, deren Bogen in der
kleinen Schluss-Schleife (dem Kringel) endet und deren Chartzelle daraus
noch einen steigenden Koppel-Stub herausschlägt (b, o) — Tafelform wie
t's langer Balken. Im gebundenen Kontext wird der Stub am Self-Crossing
der Schleife (dem Knoten, ~0,77 xh) gekappt — Mittellinie UND Silhouette —
und der Übergang verlässt den Kringel nahezu eben; ein Knoten-Abgang
zählt dabei **nicht** als r-Arm (keine Arm-Fusion). Wortfinal bleibt die
Chartform vollständig. Anlass: Korb #5 („Säbel" b→e — der Generator
setzte über dem Kringel einen zweiten Scheitel, den die Platte nie
schreibt).
*Technisch:* `KRINGEL_EXIT_BASES` + `_last_ink_crossing` in
`core/compose.py`.

**Austritts-Trim** *(`exit_trim`)* — die A-seitige Spiegelregel zum
`entry_trim`: der Sägezahn-Austritt von e/n/m/u/i behält in der Chartzelle
einen **Abschluss-Flick** (die letzten 0,05 xh drehen beim `e` von 45° auf
9° ab, beim `i` sogar nach unten), während der Composer seine
Austrittsrichtung über 0,12 xh liest und den Verbinder daran ausrichtet —
die Tinte am Saum läuft dadurch 13–42° flacher als der abgehende Strich
(Audit-Befund 19 vom 2026-09-02, sichtbar am **Naht-Winkel**). Die Regel
schneidet den Stummel von der Spitze her bis zu der Stelle zurück, an der
die Gerade zum **unveränderten** Kopplungspunkt die eigene Laufrichtung
des Stummels fortsetzt, und zeichnet den Übergang als eben diese Gerade —
Mittellinie UND Silhouette, Boden der Suche ist die **Fußwende**
(das letzte lokale y-Minimum des Zuges; der Buchstabenkörper wird nie
angeschnitten). Anders als Schleifen-, Kringel- und Balken-Exit greift sie
NACH der Platzierung, damit die Spationierung als experimentelle Kontrolle
unberührt bleibt. **Status: opt-in, Standard aus, nicht adoptiert** —
`seam_dep` der Klasse geht von +12,52° auf −1,39° und das Wort-Lineal ist
leicht dafür, aber `dconn` gegen die dissezierten Hand-Verbindungen fällt
nur in 20 % (artefaktbereinigt 51 %) der Joins; Gate (b) rot
(messjournal.md §14 „Übergänge J4/J4b").
*Technisch:* `EXIT_TRIM_WINDOW`, `EXIT_TRIM_TOL_DEG`,
`EXIT_TRIM_MIN_KINK_DEG`, `_exit_trim_index`, `_cut_exit_stub` in
`core/compose.py`; Bench-Schalter `--exit-trim`.

**Fußwende** — das letzte lokale y-Minimum eines Zuges: die Stelle, an der
die Feder ihren Abstrich beendet und in den Austritts-Stummel hochdreht.
Strukturelle Untergrenze des **Austritts-Trims** — weiter zurück wird nie
geschnitten, sonst verlöre der Buchstabe seinen Körper statt seiner
Tafelform.
*Technisch:* `_foot_turn_index` in `core/compose.py` (nicht zu verwechseln
mit `_loop_return_foot`, dem Schleifenfuß des Schleifen-Exits).

**Bowl-Exit-Tuck** — die klassenbewusste Clearance nach einem
geschlossenen Rundkörper-Ausgang (b/c/d/o): die Hand rückt den
Folgebuchstaben an den Kessel heran (gemessen +0,20 xh Überschuss der
einheitlichen Clearance über 218 sezierte Joins, b +0,42 · o +0,30 ·
c +0,25 · d +0,12), die Klassen-Clearance erlaubt deshalb BERÜHRUNG
der Tintenspalten (0,0) — bewusst nicht die volle gemessene
Überlappung (−0,06), die im Wortkontext kollidierte (Welle 2 · P1,
`aug15`: der gebundene Tuck hält −0,018 `pair_loss` bei neutralen
Wörtern). Schwester-Befund, ehrlich NICHT adoptiert: die
Arkaden-Luft (n/m brauchen laut Dissektion +0,18 mehr Raum, die
Wordbench widerspricht).
*Technisch:* `BOWL_EXIT_TUCK_BASES`/`BOWL_EXIT_CLEARANCE` in
`core/compose.py`; Messung messjournal.md §14 „Welle 2 · P1".

**Stamm-Rückpass (versetzt)** — die generierte Brücke, mit der die
Komposition den t-Deckstrich OHNE Absetzen anschließt (Welle 1 · K1b,
`aug15`): vom Stammfuß zurück hinauf zum Balkenstart, um 0,06 xh nach
rechts ausgebuchtet, damit die Strukturzähler ZWEI Pässe sehen — wie
die Hand, deren Aufstrich 0,05–0,07 xh rechts des Abstrichs liegt.
Nur Mittellinie, keine Silhouette (das `cap_retrace`-Muster); auf dem
outline-gestützten Render-Pfad bleibt die gedruckte Tinte dadurch
unverändert. Der Balkenstrich verliert seinen Lift; der Auslauf
durchsticht Abstrich UND Rückpass, womit `unter`/`mit` ihre
Hand-Zählungen erreichen.
*Technisch:* `BAR_RETRACE_BULGE_UNITS` (+ `_MAX_DX`/`_MIN_RISE`) in
`core/compose.py`; Messung messjournal.md §14 „Welle 1 · K1b".

**Override** *(Paar-Override, `glyph_pairs`)* — eine für genau *ein*
Buchstabenpaar hinterlegte, wörtlich übernommene Verbindung, die den
Generator für dieses Paar ersetzt. Bewusst die **sparsame Ausnahme**: nur
`approved`-Zeilen erreichen den Composer, links-nach-rechts-Vorrang, und
der Regel-Fix geht immer vor. Migration `0018` (Redesign R3).

**Provenance** *(Herkunft einer Zeile)* — woher eine gespeicherte
Geometrie stammt: `harvested` (vom Ernte-Werkzeug aus einer Vorlage
gezogen) · `authored` (vom Menschen von Hand gezeichnet/nachgefahren) ·
`traced` (von der Engine automatisch nachgefahren). Wichtige Regel: eine
`authored`-Zeile wird von einer neuen Ernte **nie** überschrieben.

**Specimen** — eine konkrete Wort- oder Paar-Probe auf einer Vorlage, mit
der gemessen wird. Für Sütterlin: die 63 Wörter der Abb. 19, die 33
Buchstabenpaare der Abb. 20 und — als eigenes Kontext-Set, andere Hand! —
die 106 Wörter der Abb. 22. Vermessen im committeten Sidecar
`data/sources/suetterlin-1922/words.json` (Rechteck + aus der Tinte
gemessene Grund-/Mittellinie je Zeile).

**Registrierung** *(registration)* — das Aufeinanderlegen von gemessenem
Ausschnitt und gerechneter Geometrie: Skala aus der gemessenen Lineatur,
Translation begrenzt gewählt. Bewusst **begrenzt**, damit sich ein
Experiment nicht durch Verschieben besser rechnen kann.

**Render-Kontext** *(render context)* — alles, was ein Render einer Quelle
auflöst, **bevor** es zeichnet: Stil, Lineatur-Verhältnis, Schräglage,
`width_resolver`, der quellen-gepoolte Gleichzug-Nib und die gepoolte
Feder. Seit dem Nib-Präzisions-Umbau als eigener admin-gegateter Read
verfügbar — `GET /sources/{id}/render-context`, unrundet, wo die
öffentlichen `/write`-Payloads dieselben Zahlen auf vier Dezimalen gerundet
tragen. Sein einziger Zweck: ein serviertes Payload **bit-genau** offline
reproduzieren zu können (der Fixture-Nachbau, `fetch_fixtures.py`); das
Manifest-Feld `nib_precision` (`"exact"` · `"4dp-readback"` · `"none"`)
sagt, welche Nib-Quelle ein Fixture-Root bekam, und das Verify-Gate zieht
seine Toleranz daraus. Sein Laufform-Zwilling `laufform_precision`
(`"stored"` · `"reconstructed"`) sagt, ob der Root die gespeicherten
Variante-100-Zeilen wortwörtlich trägt (Einzeltemplate-GET mit
`?variant=`, Issue #311) oder den Aggregat-Nachbau, auf den ein älteres
Deployment erkennbar zurückfällt. → write-api.md

**Ernte** *(harvest)* — der Lauf, der aus den eingefrorenen Vorlagen
Messergebnisse macht und sie als **Entwürfe** über die admin-gegatete API
schreibt: `tools/laufform/harvest.py` (Buchstaben-Vorkommen + Laufformen +
Wortspuren), `tools/pairlab/harvest.py` (Paar-Overrides + `pair_instances`).
Ohne `--apply` entsteht nur ein Report — die Freigabe bleibt Menschensache.

**Sektion · Dissektion** — das Auseinandernehmen eines echten Vorkommens
in seine Bestandteile: beide Buchstaben unabhängig eingepasst, der echte
Verbindungszug aus dem Skelett verfolgt, Platzierungsfehler von Formfehler
getrennt. Werkzeug: `tools/pairlab`.

**Wort-Trace** — die nachgefahrene Schreibspur eines ganzen Specimen-Worts
im Registrierungs-Rahmen dieses Worts, plus Slot-Labels. Zusammen mit dem
Ausschnitt die vollständige „Lern-Schablone“. Tabelle `word_instances`.

**Open-Core-Moat** — die bewusste Trennung: **Code ist MIT, die gelernten
Daten sind es nicht.** Autorisierte Duktus-Templates, Laufformen und
Vorkommens-Statistik (= der DB-Inhalt) sind außerhalb der Lizenz
reserviert. Technisch durchgesetzt: Bench-Fixtures gitignored,
Ernte-Artefakte nie committet, und seit 2026-08-28 JEDER API-Read, der
den Bestand trägt, admin-gegatet — Templates, Vorkommen, Bboxen,
Paar-Overrides, Hände, Statistik-Schicht, Eigenhand; die Trennlinie
öffentlich/reserviert hält `tests/test_api_public_surface.py` für jede
GET-Route fest. Die Crawler-Politik der Seite ist davon unabhängig offen
(`ai-train=yes`): Der Moat ist die Datenbank, nicht die Webseite.
→ quellen-und-rechte.md §5, crawler-richtlinie.md §2

**Origin-Geheimnis** — der gemeinsame Wert zwischen dem Cloudflare-Edge und
dem API-Dienst, der die direkte `*.run.app`-Adresse zumacht. Beide
Cloud-Run-Dienste stehen mit `ingress=all` im Netz (kein Load Balancer — er
kostete mehr im Monat als das Projekt), die API antwortete also auf zwei
Adressen: über Cloudflare und daran vorbei. Alles, was am Edge durchgesetzt
wird — Rate-Limiting-Regel, WAF, Cache —, war damit über eine URL umgehbar.
Eine **Transform-Rule** stempelt seit 2026-09-02 den Header
`X-Origin-Secret` auf jeden Request, den Cloudflare für
`api.kurrentschrift.ink` weiterreicht; alles ohne ihn bekommt **403** —
vor dem Limiter, vor `require_admin`, vor jeder DB-Abfrage. Es ist
**keine Authentifizierung**: der Header sagt „durch die Vordertür", nicht
wer da kommt. **Eine Ausnahme, gemessen beim Rollout:** ein
Worker-Subrequest an einen Host DERSELBEN Zone läuft an den Transform-Rules
vorbei, deshalb stempelt der Apex-Worker vor dem Admin-Weg selbst
(`infra/cloudflare/`). Ohne gesetzte `ORIGIN_SECRET`-Env ist die Prüfung aus,
und genau das ist der Rollback (Env entfernen **und** die neue Revision
promoten); ausgenommen bleiben `/health` (der Deploy-Smoke probt die
`run.app`-Tag-URL) und `/seo-proxy/…` (Crawler-Pfad). `/health`
meldet als `origin_gate` das Urteil für den fragenden Request (`off` ·
`off-seen` · `ok` · `missing` · `mismatch`, nie den Wert); `off-seen` heißt
„Header kommt an, Prüfung noch aus" und ist das Messmittel, mit dem jeder Weg
in den Dienst bestätigt wird, bevor scharf geschaltet wird — es ist der
Grund, warum der Worker-Befund vor und nicht nach dem Scharfschalten auffiel.
*Technisch:* `api/origin_gate.py`, `core/config.py::origin_secret`,
`infra/cloudflare/kurrentschrift-api-proxy.js`.
→ frontend-stack.md §5, quellen-und-rechte.md §5

**Report-Only-Woche** — die Woche, in der eine neue
Content-Security-Policy als `Content-Security-Policy-Report-Only`
ausgeliefert wird: Sie **blockiert nichts**, sondern lässt den Browser jede
Quelle melden, die sie verboten hätte. Danach wird sie scharf geschaltet,
indem der Header-Name um `-Report-Only` gekürzt wird — eine Zeile.
Der Umweg ist kein Zögern, sondern die Antwort auf eine Asymmetrie: Eine zu
enge Policy fällt auf der öffentlichen Seite sofort auf, in der **Werkbank**
aber erst dem Autor — und die kann kein automatischer Durchgang öffnen, weil
sie hinter Cloudflare Access liegt. Die Woche ist nur so viel wert wie die
Meldungen, die sie erzeugt: Ziel der Meldung ist `POST /csp-report` auf dem
API-Host, der zählt und loggt und **nichts** schreibt; jede gemeldete
Verletzung ist ein Befund, der vor dem Scharfschalten in die Policy gehört
(oder abgestellt wird). Gemeldet wird per `report-uri`, und **nur** so: Die
naheliegende Fassung deklariert daneben `report-to` (Reporting-API) — und
genau das ließ Chromium im Durchgang vom 2026-09-02 `report-uri` ignorieren
und dann gar nichts liefern. *Technisch:*
`app/security-headers.conf`, `api/routers/csp.py`,
`tests/test_csp_policy.py`. → frontend-stack.md §6

**`add_header`-Vererbungsfalle** — nginx vererbt Antwort-Header **nicht über
Ebenen hinweg**: Sobald ein `location`-Block einen eigenen `add_header` setzt
(und sei es nur ein `Cache-Control`), fallen sämtliche auf Server-Ebene
gesetzten Header für diesen Block still weg. Kein Fehler, keine Warnung —
nur eine URL, die als einzige ohne CSP und ohne `nosniff` ausgeliefert wird.
Deshalb stehen die Header dieses Projekts in einer eigenen Datei, die im
Server-Block **und** in jedem `location` mit eigenem `add_header` per
`include` gezogen wird; wer irgendwo einen `add_header` ergänzt, ergänzt die
`include`-Zeile daneben. *Technisch:* `app/security-headers.conf`,
`app/nginx.conf`; gehalten von
`tests/test_csp_policy.py::test_every_nginx_location_with_its_own_header_reincludes_the_snippet`.
→ frontend-stack.md §6

**Prerender-Pfad (Crawler)** — Crawler und KI-Agenten (kein JavaScript)
bekommen je öffentliche Route eine zur Build-Zeit aus dem Locale-Katalog
gerenderte HTML-Seite statt der leeren SPA-Hülle; Menschen bekommen
unter derselben URL die App. Erkannt am User-Agent (`$is_bot`-Map in
`app/nginx.conf`, wortgleich mit anyplot), bedient vom API-Host
(`/seo-proxy/{route}` liest `app/prerender/*.html`). Jede Seite trägt
Head (Canonical, OG, JSON-LD), den Text in DOM-Reihenfolge, die
Site-Nav, Stand (Sitemap-`lastmod`) und den Rechtehinweis in-band; erste
Zeile ist der Marker `<!-- kurrentschrift.ink prerender -->`. Löste am
2026-08-28 den *Markdown-Spiegel* der Schriftkunde (`/schriftkunde.md`,
2026-08-27, eine Seite) ab. *Technisch:* `app/src/lib/seo/prerender.ts`
(Renderer) + `app/scripts/build-prerender.mjs` (prebuild) +
`api/routers/seo.py`; Wächter `prerender.test.ts`,
`tests/test_api_seo_proxy.py` und täglich
`.github/workflows/bot-serving-check.yml`. → frontend-stack.md §6,
crawler-richtlinie.md §3

**IndexNow** — das freie, offene Push-Protokoll von Bing und Yandex
(mitgenutzt von Seznam, Naver, Yep): Statt auf den nächsten Crawl zu
warten, meldet die Seite geänderte URLs per POST an `api.indexnow.org`;
Google nimmt nicht teil und liest weiter die Sitemap. Der Nachweis, dass
die Meldung vom Host stammt, ist eine öffentliche Schlüsseldatei
`app/public/kurrentschrift-indexnow-….txt` (nginx liefert sie wie die
anderen Maschinendateien direkt aus). Gemeldet wird bei jedem Push auf
`main`, der `app/**` berührt — dieselben Pfade wie der Cloud-Build-Trigger
`deploy-app` — die komplette Sitemap (zehn URLs), weil bei zehn Seiten die
Sitemap die natürliche Einheit ist. Seit 2026-09-02, auf Empfehlung der
Bing Webmaster Tools. *Technisch:*
`.github/workflows/indexnow-submit.yml`. → crawler-richtlinie.md §3

**Bot-Site (`bot_fetch`)** — die zweite Plausible-Site
`bots.kurrentschrift.ink`, auf der die Seitenabrufe von Crawlern und
KI-Assistenten landen — nie auf der Besucher-Site, weil jedes
Plausible-Event einen „Besucher" erzeugt und die menschlichen Zahlen
sonst aufblähen würde (anyplots Befund: ~40 % zu viel). Ein Event
`bot_fetch` je Abruf auf dem Prerender-Pfad, serverseitig aus der
API-Middleware, mit den Eigenschaften `assistant` (Anbieter: claude,
chatgpt, gemini, google …), `kind` (**warum** abgerufen wurde —
`user_directed` = ein Mensch hat seinen Assistenten gebeten, die Seite
zu öffnen, also ein Leser; `index`, `search`, `training`, `inspection` =
Maschinen bauen einen Korpus), `path` und `status` (der Abruf wird
aufgezeichnet, nicht der erfolgreiche Lesevorgang — eine 404 ist ein
Signal, kein Seitenaufruf). Dazu seit 2026-08-28 das Event
`asset_fetch` für die Einzel-Abrufe der API — Buchstabe oder Wort als
SVG/JSON, Tafel-Ausschnitt — mit `asset`, `source` und `key`
(glyph_key bzw. angefragter Text): welche Buchstaben und Wörter
Assistenten zeigen wollten. Drei Fallen, die die Events schweigend
verschwinden lassen: ein Bot-User-Agent (→ Events laufen unter dem
neutralen `kurrentschrift-server/1.0`, die Identität steckt in den
Props), eine Hosting-IP als Besucher — Plausible verwirft
Google-Cloud-Adressen, und genau die ist auf dem Crawler-Pfad
`cf-connecting-ip` (→ nginx reicht den Crawler in `X-Forwarded-For`
durch, `visitor_ip` nimmt die ERSTE gültige weitergeleitete Adresse) —
und der Edge-Cache (→ `/seo-proxy` antwortet `no-store`, sonst zählt
nur der erste Abruf). Taxonomie `AI_AGENTS` wortgleich mit
anyplot. *Technisch:* `api/analytics.py`, `api/request_context.py`, die
Middleware `record_bot_fetch` in `api/main.py`; aktiv nur in Produktion
(`BOT_ANALYTICS` überschreibt). → frontend-stack.md §6,
crawler-richtlinie.md §3

---

## §3 Mess- und Fit-Vokabular

**M4-Fit** — die elastische Anpassung eines Templates an echte Tinte:
Das kanonische Template wird auf das Skelett eines Vorkommens *gewarpt*,
wobei Strichstruktur und Ecken erhalten bleiben. Heißt so nach dem
Meilenstein M4 der MVP-Roadmap, in dem die Routine entstand — **nicht** zu
verwechseln mit der Kettenfit-Kennzahl M4 (unten).
*Technisch:* `core/fit.py::fit_template_to_instance` /
`fit_glyph_to_crop`, Tikhonov-regularisiert, L-BFGS-B mit analytischem
Gradienten.

**Tikhonov-Regularisierung** — der mathematische Trick, der einen Fit
davon abhält, sich beliebig zu verbiegen: zur Datenanpassung wird ein
Strafterm addiert, der große Abweichungen von der Ausgangsform bestraft.
Der Fit „darf sich anschmiegen, aber nicht verwandeln“. (Anderswo:
Ridge-Regression, L2-Regularisierung.)
*Technisch:* `REFINE_LAMBDA_REG` in `core/fit.py`.

**Skelett** *(skeleton)* — die auf ein Pixel Breite ausgedünnte Mittellinie
der Tinte (`skimage.skeletonize`). Zusammen mit der **EDT**
(*euclidean distance transform*, `distance_transform_edt`), die an jedem
Punkt den Abstand zum nächsten weißen Pixel = die halbe Strichbreite
liefert, sind das die beiden Kanäle, aus denen jede Messung kommt.

**Deckung** *(coverage)* — die Gegenrichtung des Fits: Nicht nur „liegt
mein Template auf Tinte?“ (das ist die Geometrie-Richtung), sondern „ist
jede Tinte von meinem Template erklärt?“. Ohne Deckungsterm kann ein Fit
sich auf einen Teilstrich zurückziehen und dort perfekt sitzen.
*Technisch:* Energien `e_geo` (Template → Skelett), `e_cov` (Skelett →
Template) und `e_wid` (Breiten); Konvergenz-Schwellen
`core/fit.py::CONVERGED_GEO_RMSE_UNITS` (0,08 xh) und
`CONVERGED_COVERAGE_RMSE_UNITS` (0,10 xh); Punktbudget
`MAX_COVERAGE_POINTS` (300 pro Glyphe).

**Deckungslücke** — der **Abzug**, den die Sütterlin-Natürlichkeitsmetrik
aus dem Deckungs-Gate bildet: `components.coverage = 1 − gate`. Höher =
schlechter, genau umgekehrt zur → Deckung und zum `gate` selbst.
**Wichtig für die Deutung:** Das Gate ist ein Produkt aus drei Faktoren
(`gate = dice · q_chamfer · q_geo`), die Lücke also ein
**zusammengesetzter** Abzug aus Überlappung (Dice), Randabstand
(Chamfer) und Mittellinien-Lage (Geo-RMSE) — **nicht** allein der Anteil
verfehlter Tinte. Ein hoher Wert sagt „das Tor ist zu", nicht welcher
der drei Faktoren es zugezogen hat; dafür stehen die Einzelmaße im
Diagnose-Block. Der eigene Name
(Autor-Entscheid 2026-09-03) löst eine Falle in der Werkbank auf: Im
Diagnose-Block standen „Deckung (IoU): 0.105“, „Deckungs-Gate: 0.01“ und
„Deckung 0.99“ drei Zeilen auseinander — dieselbe Größe einmal positiv
und einmal als Abzug, unter einem Wort; die 0.99 las sich wie eine
hervorragende Deckung und war der maximal mögliche Abzug. Seither heißt
**nur der Abzug** „Deckungslücke“; „Deckung (IoU)“ und „Deckungs-Gate“
behalten ihr Wort, weil sie die positive Richtung messen. Die Kurzform
auf den Buchstabenkarten trägt zusätzlich das Präfix „Abzüge:“, damit die
Zahlenreihe auch ohne die Balkenlegende ihre Richtung nennt.
*Technisch:* `core/quality_suetterlin.py` (`gate` → `components.coverage`);
Beschriftung `app/src/locales/de/wizard.ts` (`optimize.cat.coverage`),
Kurzform `app/src/sections/admin/quality/scoreParts.tsx`
(`ScoreBreakdownInline`). → qualitaetsmetrik.md §5

**Warp** — das elastische Verbiegen einer Form beim Fit (im Gegensatz zum
bloßen Verschieben). Merksatz aus der Ernte: **„shapes, not placements“**
— gespeichert werden zentrierte *Formen*; wo ein Buchstabe stand, ist ein
eigener, unregularisierter Parameterblock und darf nicht als Formfehler
bestraft werden.

**Rastersuchlauf · Platzierungsschranke** — vor dem elastischen Fit wird
ein Buchstabe durch eine begrenzte Gittersuche grob auf die Tinte
geschoben (±0,6 xh horizontal, ±0,20 xh vertikal:
`FIT_DX_UNITS`/`FIT_DY_UNITS` in `tools/pairlab/analyze.py`). Landet das
Optimum *auf* dem Rand dieses Fensters (`at_bound`), ist das ein
Warnzeichen: die richtige Stelle lag vermutlich außerhalb.

**Kettenfit** *(chain fit)* — die Idee, **Buchstabe → Verbinder →
Buchstabe als EINE durchlaufende Feder** zu fitten statt als zwei
unabhängige Buchstaben plus nachträglich zerlegten Verbindungsstrich.
Motiv: Wo zwei Buchstaben sich berühren, liefert die nachträgliche
Zerlegung *gar nichts* — genau dort, wo verbundene Schrift am
verbundensten ist. Stufe A (Paar-Maßstab) ist gebaut und gemessen; Stufe B
(Wort-Maßstab) ist freigegeben. **Reine Messschicht, ändert kein
Rendering.** Auf der Duell-Seite trägt seit 2026-08-16 die GEWACHTE
Variante (Struktur-Wächter, Arm ⑨) das Label **Kette** — Owner-
Entscheid: fit-erfundene Kreuzungen sind nie richtig (→ Duell-Namen).
*Technisch:* `tools/pairlab/chain.py` + `chainbench.py`
→ uebergaenge-befund.md §5c · Issue #278

**Tintenfolger** *(ink follower)* — die geplante Verfeinerungsstufe ÜBER
dem Kettenfit: der Kettenfit liefert Topologie, Strichfolge und
Kreuzungsauflösung als Initialisierung, dann wird die Form-Regularisierung
Richtung Vorlage GELÖST (der Tikhonov-Term wird im Rebuild zum
Proximal-Term relativ zum Chain-Optimum, kein Chart-Prior mehr) und die
Bahn dicht auf das gemessene Skelett gezogen — „Geometrie ganz aus der
Tinte, Ordnung ganz aus dem Prior“. Maßstab ist der nachgefahrene
**Referenzsatz** (§4), nie das eigene Residual. Kein neues System, kein
GPU, kein Fremdmodell; Ausgabe ist eine Wortbahn (Inspektionsschicht),
nie eine Messung. *Technisch:* `tools/pairlab/follow.py`
(`follow_word_chain`/`follow_case`, Gewichte PROVISORISCH bis zur
§14-Arm-Kalibrierung) → proposals/tintenfolger.md ·
bildsynthese-und-stiftbahn.md §6

**Fremdtinte** *(foreign ink)* — Tinte im Wort-Crop, die das Wort nie
geschrieben hat und die die eingefrorene Binarisierung trotzdem behält:
Papierflecken, **Durchschein** der Rückseite (Galoppieren: sechs
Fragmente, halb so dunkel wie die Schrift), Reste der Nachbarzeile.
Für den Kettenfit/Folger ist jede solche Komponente zugleich Zugfeld-
Magnet und Coverage-Ziel — die Nadeln „ins Papier" (zwei w-Fuß,
Galoppieren) enden messbar darauf. Gemessener Fund (2026-08-20, 90
Nicht-Haupt-Komponenten der 63 Fixtures): FLÄCHE trennt Fremdtinte nicht
von echten Marken, DUNKELHEIT trennt vollständig (rel 0,74–0,92 gegen
0,01–0,38). Nicht zu verwechseln mit der **eigenen Marke** als Magnet
(die-2: der i-Punkt zieht die Körperbahn) — dunkel, echt, und vom
Darkness-Filter bewusst behalten. *Technisch:*
`tools/pairlab/ink_evidence.py` → messjournal.md §14 „Kette K-C"

**Tinten-Evidenz-Maske** *(ink-evidence mask, Kette K-C)* — die Maßnahme
gegen Fremdtinte: vor Seed-Fenstern und Solve wird jede Nicht-Haupt-
Komponente der Maske, deren Median-Grau näher am Papier als an der
Haupttinte liegt (`paper_fraction` 0,5 = Mitte der gemessenen Lücke, kein
Knopf), aus `skel` und `width_map` des Falls gelöscht; die größte
Komponente ist das Wort und bleibt immer. Aus — oder nichts zu droppen —
heißt derselbe `WordCase` (Identität), darum sind Wörter ohne Fremdtinte
byte-identisch. Ändert NUR, was den Fit zieht; das Bench-Lineal
(`ref_mask`, AIoU, Zähler) bleibt eingefroren — die Torpfosten stehen.
Nach dem aug20-Sechs-Gates-Pass und dem Autor-Go als **Kette v4**
adoptiert (`aug21`): `FollowWeights.ink_evidence` und
`HarvestOptions.ink_evidence` sind seither DEFAULT an (auch im
`chain`-Provider des Tracebench); Archäologie-Pfad `--no-ink-evidence`
bzw. `ink_evidence=False` = der Vor-v4-Stand, byte-identisch.
Drop-Liste je Wort in `meta.ink_evidence`. *Technisch:*
`tools/pairlab/ink_evidence.py`, Einsatz in `follow_derived` und
`harvest.chain_word_strokes` → messjournal.md §14 „Kette K-C"
(Messung) + „Kette v4" (Re-Baseline)

**Tinten-Zuweisung per Strecke** *(per-stroke ink assignment, Kette
K-E)* — der Autor-Ansatz nach K-C: nicht WELCHE Tinte zieht, sondern
WEN sie ziehen darf. Heute sehen alle Samples eines Ketten-Runs EIN
Distanzfeld und EINEN Coverage-Topf — jede Tinte zieht das nächste
Sample, egal zu welcher Strecke (Strich) es gehört; so zieht in
die-2 der eigene i-Punkt die d-Schleife (die V-Nadel), und dasselbe
plattgezogen ist der Verdacht hinter den verbliebenen unechten
Retrace-Zonen an kleinen Kringeln. Stufe 1 = Marken-Claim-Trennung
(eindeutige Zuweisung per Duktus); Stufe 2 = Kringel (braucht den
Duktus-Prior als Verbrauchs-Zuordnung: jeder Tinten-Punkt wird von
genau einer Strecke verbraucht), nur bei haltender Stufe 1.
*Gemessen `aug21` (K-E1 + Ein-Faktor-Konversion K-E2): beide per
aiou-Gate verworfen* — die benannten Ziele heilen (die-2s V-Nadel
weg), aber vier diffuse Körper-Deckungs-Risse hängen an denselben
Kanälen wie die Heilung; Stufe 2 nicht eröffnet, Wege §7.9
(humanbench · Distanzfeld-NUR-Claim). *Technisch:*
`tools/pairlab/chain.py` (Feld-Aufbau in
`fit_word_chain`/`_prepare_fields`) → messjournal.md §14
„Kette K-E"/„Kette K-E2", tintenfolger.md §7.3 A9/K-E

**Marken-Claim-Trennung** *(mark-claim separation, K-E Stufe 1)* —
die eindeutige Hälfte der Tinten-Zuweisung per Strecke: eine
Marken-Strecke (Strich eines Buchstaben-Segments, dessen Init das
Assembler-Kriterium `diacritic_stroke_units` erfüllt — i-Punkt,
u-Bogen; der t-Querbalken nicht) CLAIMT die dunkle
Nicht-Haupt-Komponente im 0,6-xh-Marken-Radius des Lineals. Ein
Claim schaltet beide Zug-Kanäle um: die Komponente verlässt Feld und
Coverage-Topf der Körper-Samples, die Marken-Samples lesen
ausschließlich ihre Komponente. Ohne Claim ändert sich nichts —
Marken ohne Tinte suchen wie heute, Körper-Bruchstücke bleiben
Körper-Evidenz. EIN Knopf `mark_claim` (`--mark-claim`), nach den
`aug21`-Messungen (K-E1 · K-E2) declared-off geblieben — verworfen
per aiou-Gate bei spektakulärer die-2-Heilung; der Code trägt die
K-E2-Form (Breitenfelder ungeteilt). *Technisch:*
`tools/pairlab/chain.py`, Knopf in `FollowWeights`/`HarvestOptions`
→ messjournal.md §14 „Kette K-E"/„Kette K-E2"

**Topologie-Wächter** *(structure guard)* — Arm ⑨ des Tintenfolgers:
eine Runden-AKZEPTANZREGEL statt einer Kraft. Vor der ersten Runde
wird das Struktur-Budget der Initialisierung gemessen (die
v2.1-Klassenzählung Kreuzungen · Retrace-Zonen · Berührungen ·
Überlagerungen, mit den Zählern des Lineals auf der assemblierten
Bahn); eine gelöste Runde wird nur akzeptiert, wenn keine Klassenzahl
ihr Budget übersteigt — sonst wird sie mit halbierten Reisebudgets neu
gelöst (höchstens zweimal) und danach auf die Vorrunden-Geometrie
zurückgewiesen (`structure_rejected`). Trennt die Distanz-Gewinne des
Form-Release von seinen Struktur-Erfindungen, statt beide gemeinsam am
Veto scheitern zu lassen; der Owner-Satz dahinter: Kringel, Kreuzungen
und Retraces sind duktus-fix. *Technisch:*
`tools/pairlab/follow.py::structure_class_counts` +
`FollowWeights.structure_guard` (default False = byte-identisch),
`STRUCTURE_GUARD_MAX_RETRIES` → messjournal.md §14 (Arm ⑨).
Nicht zu verwechseln mit dem **Laufform-Topologie-Wächter** (unten) —
gleicher Geist (Duktus-Topologie ist unantastbar), andere Schicht.

**zonale Rückweisung** *(`zonal`, K0-Z)* — die Reparatur des
Topologie-Wächters an seiner teuersten Eigenschaft: er verwirft eine
Runde **atomar**. Eine Runde bündelt aber oft eine erlaubte
Soll-Reparatur mit einer verbotenen Erfindung, und beim Voll-Revert
fällt die Reparatur mit. Die zonale Rückweisung lokalisiert stattdessen
die Verletzungen (Positions-Diff gegen die Vorrunde), pinnt die Anker im
Radius **0,55 xh** um jede und löst EINMAL nach — der Rest der Runde
bleibt. `guard_outcome` protokolliert je Wort, was passierte
(`accept` · `zonal` · `revert-init`), und genau daran ist die Wirkung
belegt: 26 der 31 bewegten Wörter waren unter dem alten Wächter ein
Runde-1-Rollback auf den Init. Radius 0 reproduziert das alte
Verhalten byte-identisch. *Technisch:*
`tools/pairlab/follow.py`, `--structure-guard-zone <xh>`,
`FollowWeights.structure_guard_zone_units` (Default 0,55 seit Kette v5)
→ messjournal.md §14 „Kette K0-Z `aug20`“ und „Kette v5 `aug26`“

**Ratsche** *(Ratschen-Budget, `structure_guard_ratchet`, K0-Z-R)* —
die zweite Reparatur derselben Schicht: das Struktur-Budget des
Wächters bleibt nicht auf dem Stand der Initialisierung stehen, sondern
**zieht nach jeder akzeptierten Runde Richtung Soll nach** — wie eine
Ratsche, die nur in eine Richtung greift. Ohne sie darf eine Runde eine
Klassenzahl beliebig oft wieder verschlechtern, solange sie unter dem
alten Init-Budget bleibt; mit ihr ist jeder erreichte Struktur-Gewinn
die neue Obergrenze. Zusammen mit der zonalen Rückweisung und dem
Kompositions-Soll bildet sie den Wächter-Stack, der seit Kette v5
(`aug26`) der Default ist. *Technisch:*
`tools/pairlab/follow.py`, `--no-structure-guard-ratchet` schaltet sie
ab → messjournal.md §14 „Kette K0-Z-R `aug20`“ und „Kette K0-S
`aug21`“

**Schienen-Auslauf** *(tail runout)* — die erste adoptierte Konstante
der Route Lotse und ein Owner-Fund, kein geplanter Arm: am ENDE eines
Wortes hört die Tinte auf, aber die Karte läuft weiter; ohne Deckel
folgt der Ritt der Karte ins Leere und schleppt einen Schwanz hinter
sich her. Der Auslauf begrenzt, wie weit der Ritt nach dem letzten
Tinten-Sample noch der Karte folgen darf. Adoptiert bei **1,0** —
er allein senkte den dtw-Median der Route von 0,119 auf 0,101 und ein
Einzelwort von 0,343 auf 0,087. *Technisch:*
`tools/inkpilot/pilot.py::TAIL_RUNOUT_MAX_UNITS` →
messjournal.md §14 „Route Lotse `aug16`“, Ledger:
verfahren-lotse.md

**Laufform-Topologie-Wächter** *(LF2)* — die Schichtungs-Regel auf der
Laufform-Ebene: eine Laufform-Zeile, die eine GEZÄHLTE Chart-Kreuzung
ihres Glyphen löscht, überschreibt den Duktus-Prior statt ihn zu
weiten und wird nicht komponiert (Fallback rohe Chart-Form). Der
`aug19`-Sweep fand genau zwei gespeicherte Verlierer (h: 2 → 0 in
jedem Slot · p: 1 → 0) und der LF1-Lauf einen frischen (G-Draft) —
der rohe Anker-Median bügelt Schleifenschlüsse glatt
(„Median-Verengung": der Annäherungs-Spalt der Schenkel schrumpft,
und der v2.1-Retrace-Filter kippt das tangentiale X). Als
Voll-Entfernung gemessen und verworfen (Tinten-Preis, Marken-Kipp);
als WRITE-PATH-Prinzip bleibt er stehen. → messjournal.md §14
(„Laufform LF2"), Nachfolger: Topologie-Reparatur (LF3)

**Topologie-Reparatur** *(Chart-Rückblendung, LF3)* — die Konversion
des Laufform-Topologie-Wächters von Filter zu Konstruktion: verliert
eine Laufform-Form (gespeicherte Zeile oder Lücken-Draft) eine
gezählte Chart-Kreuzung, blenden die Anker im festen 0,5-xh-Fenster
um die verlorene Kreuzung minimal zur Chart-Geometrie zurück —
`t` per Bisektion als kleinstes t ∈ [0, 1], das die Zählung
wiederherstellt (linearer Falloff, deterministisch); scheitert auch
t = 1, fällt das Glyph auf die Chart-Form zurück. Breite bleibt
Laufform, Topologie bleibt Chart. → messjournal.md §14
(„Laufform LF3")

**Junction-Verschiebung** *(junction displacement)* — der dokumentierte
Fehler des Skelett-Branch-Points als Kreuzungs-Marke: Thinning
verschiebt ihn um bis zu die lokale Strichbreite (±2–4 px bei xh ≈ 30)
und spaltet eine echte Kreuzung oft in ZWEI Y-Junctions, deren Brücke
1,2–1,7 Strichbreiten lang ist (auf den Dev-Wörtern gemessen). Ein Term,
der eine Bahn-Kreuzung auf den rohen Branch-Point zieht, zieht sie
deshalb an die falsche Stelle. → das extrapolierte Landmark-Ziel.

**extrapoliertes Landmark-Ziel** — die Korrektur der
Junction-Verschiebung im Tintenfolger: Um den Branch-Point werden die
einlaufenden Skelett-Äste GEODÄTISCH verfolgt (Dijkstra auf dem
Skelett, Junction-Cluster absorbiert, Konfluenzen blockiert statt
verschweißt — die euklidische Annulus-Variante verschweißt auf
kursiver Tinte die Schenkel), der junction-verzerrte Kern (2×
Halbbreite) ausgeschlossen, je Ast eine TLS-Richtung gefittet, Äste
per Gute-Fortsetzung gepaart (Krümmungs-basierte Toleranz) und der
Schnittpunkt der Fortsetzungen als Ziel genommen — mit isotroper
Unsicherheit ≈ lokale Halbbreite als 1/σ²-Gewicht (Pre-Whitening des
bestehenden Operators, kein neuer Term). Verweigert ehrlich:
Touch-Points (2 Schenkel) und T-Junctions (3) sind BY DESIGN keine
Kreuzungsziele — auf den Dev-Wörtern sind das 12 von 21
Korrespondenzen (→ die Korrespondenz-Kappe), die Kappe jedes
Landmark-Effekts, solange die Korrespondenz nicht klassenbewusst wird.
*Technisch:* `tools/pairlab/follow.py::extrapolated_targets`
→ messjournal.md §14 (Arm ⑥)

**Korrespondenz-Kappe** — der Befund, der die Arme ⑤/⑥ des
Tintenfolgers überragt: 12 der 21 Landmark-Korrespondenzen der
Dev-Wörter zeigen auf Tinte, die GAR KEINE Kreuzung trägt (5
Touch-Points, 7 T-Junctions) — die BAHN kreuzt sich dort, die Tinte
berührt sich nur. Solange die Korrespondenz diese Klassen nicht kennt,
zieht jeder Landmark-Zug an der Hälfte der Ziele in eine Struktur, die
es nicht gibt; das deckelt jeden möglichen Effekt des Terms, wie stark
er auch gewichtet wird. → die klassenbewusste Korrespondenz.
*Technisch:* messjournal.md §14 (Arme ⑤+⑥, `aug14`)

**klassenbewusste Korrespondenz** — die vorregistrierte Antwort auf die
Korrespondenz-Kappe (Arm ⑥b): die Landmark-Korrespondenz kennt die
KLASSE ihres Tinten-Ziels. Zeilen, deren Verfeinerungsgrund eine
By-Design-Nichtkreuzung der Tinte ist (`touch_point` · `t_junction`),
bekommen Gewicht 0 über das bestehende Pre-Whitening (√w skaliert
Operator-Zeile UND Ziel — die Zeile zieht nichts und kostet nichts),
statt weiter am rohen Branch-Point zu ziehen; die 1/σ²-Gewichte der
überlebenden Zeilen renormieren auf Mittel 1. Die Walk-Fehlschläge
(`few_branches` · `no_continuation_pair` · …) bleiben Ziele — dort KANN
die Tinte eine Kreuzung tragen. Folger-seitig; `chain.py` und die
eingefrorene `landmarks.py` bleiben unberührt. *Technisch:*
`tools/pairlab/follow.py::classed_targets` (Modus
`extrapolated_classed`), `LANDMARK_NONCROSSING_REASONS`
→ messjournal.md §14 (Arm ⑥b)

**Retrace-Guard** — die Ausnahme im Tintenfolger, die dessen blinden
Fleck deckt: Über doppelt beschriebener Tinte belohnen BEIDE Datenterme
den Kollaps zweier Pässe auf eine Linie (Reverse-Coverage ist von einem
Pass befriedigt, der Ridge-Pull von beiden auf dem Grat), und das
Einzige, was sie unterscheidet, ist der Form-Prior — den die Stufe
gerade löst. Der Guard erkennt Retrace-Zonen deshalb auf der
INIT-Bahn (derselbe Detektor wie der tracebench-Zähler) und lässt die
betroffenen Anker ihr VOLLES Chain-λ behalten, als per-Anker-
Reg-Gewicht statt als Bound — nur so koexistiert λ_prox = 0 (die erste
Sprosse von Arm ①) mit stehendem Guard. `--no-retrace-guard` existiert,
um den Guard selbst zu MESSEN, nie als Betriebsmodus. *Technisch:*
`tools/pairlab/follow.py::apply_retrace_guard` →
proposals/tintenfolger.md §3

**Iterationsdeckel** *(iteration cap)* — die Obergrenze, wie viele
Optimierungsschritte ein Fit machen darf, bevor er abgebrochen wird. Klingt
nach einer Sicherheitsleine, ist aber eine stille Falle: Wird der Deckel
erreicht, *meldet* der Optimierer trotzdem ein Ergebnis — nur ist es eine
Momentaufnahme eines noch laufenden Abstiegs, kein konvergiertes Resultat.
Solche Zwischenstände fallen durch das Konvergenz-Gate, ihr Vorkommen wird
verworfen, und **wo genau der Abbruch landet, verschiebt sich mit dem
Startwert** — daher waren Ernten über eine Init-Änderung hinweg nicht
reproduzierbar. Lehre: Ein Fit-Ergebnis ist erst dann eines, wenn man weiß,
*warum* der Solver aufgehört hat.
Merkregel: Ein Deckel, der überhaupt bindet, ist der falsche Knopf — der
Solver hört ohnehin bei seinem eigenen Kriterium auf, also kostet ein hoher
Deckel nur dort etwas, wo er gebraucht wird.
*Technisch:* der Kettenfit hat mit `CHAIN_MAX_ITER` (Default 8100) ein
EIGENES Budget statt `core.fit.DEFAULT_MAX_ITER` (300) — 300 ist ein
Pro-Glyph-Budget, eine Wortkette trägt ~820 freie Parameter. Gemessen
(Median 1211 Iterationen, p90 2518, Maximum 4215): bei 300 war der Deckel in
91 % der Solves der bindende Stopp, bei 2700 in 10 %, bei 8100 in keinem —
für +5 % Rechenzeit, ohne dass sich ein einziges Gate-Urteil ändert.
`fit_meta["hit_iteration_cap"]` und die Spalte im `--diag-csv` machen den
Zustand lesbar; `KS_CHAIN_MAX_ITER` sweept ihn.

**Überlappungsterm** *(overlap term, Exklusivität)* — der Energieterm des
Kettenfits, der die physikalische Aussage kodiert: **eine Feder schreibt
denselben Zug nicht zweimal.** Nötig wurde er durch einen Befund der
Runde 2: Das Objektiv prüfte die *Vereinigung* aller Segmente gegen die
*Vereinigung* der Tinte und war für die **Zuordnung** blind — ein Buchstabe,
der die Tinte des Verbinders schluckt, und ein Verbinder, der den
Buchstabenstrich nachfährt, sahen beide nach guter Deckung aus. Die
Beckensonde bewies: die gestapelte Lösung war in *jedem* Term billiger
(5/5 Fälle). Der Term bestraft Sample-Paare **verschiedener** Segmente, die
näher beieinander liegen als ein Haarstrich breit ist; ausgenommen sind nur
die Nahtbänder benachbarter Segmente (die gemessene Stub-Zone, in der die
Hand wirklich Tinte teilt) — Buchstabe-auf-Buchstabe ist nie ausgenommen.
Wirkung, gemessen im vorregistrierten A/B: die vier Grenzfall-Flags des
Konnektor-Wächters heilen mechanisch (der Naht-Anteil verschwindet aus der
Lösung selbst), +4 Vorkommen, null neue Flags.
*Technisch:* `tools/pairlab/chain.py` — `CHAIN_OVERLAP_RADIUS_UNITS` (0,15),
`CHAIN_OVERLAP_SEAM_EXEMPT_UNITS` (0,4, aus der Init-Geometrie, damit der
Gradient exakt bleibt), `CHAIN_OVERLAP_WEIGHT` (0,2, per Sweep + A/B;
`KS_CHAIN_OVERLAP_WEIGHT` überschreibt). Paarmenge pro Evaluation per
KD-Baum, stückweise konstant in den Parametern — dieselbe f.ü.-exakte
Behandlung wie die Deckungszuordnung.

**Kreuzungs-Landmarke** *(crossing landmark)* — eine **Selbstkreuzung** der
Buchstaben-Ankerlinie, die als *Ortsmarke der Struktur* taugt: zwei
Sehnen, die sich unter mindestens 15° schneiden und (innerhalb desselben
Federzugs) mindestens 0,35 xh Bogenlänge auseinander liegen. 26 der 34
eingefrorenen v0-Zeilen tragen zusammen 43 solcher Landmarken. Der Sinn:
Ein Buchstabe hat eine feste Struktur (Kringel, Kreuzung, Schale in fester
Reihenfolge), und was je Vorkommen und je Übergang wandert, ist deren
**Lage** — beim Sütterlin-`d` sitzt die Tinten-Kreuzung mit
Folgebuchstaben 0,243 xh tiefer als am Wortende.
*Technisch:* `tools/pairlab/landmarks.py` — `landmark_crossings`
(`LANDMARK_MIN_ANGLE_DEG`, `LANDMARK_MIN_ARC_SEPARATION_UNITS`,
`LANDMARK_MERGE_RADIUS_UNITS`); ausdrücklich nicht
`core.geometry.detect_crossing_passages`, das dieselbe Erscheinung für die
**Breiten**-Kontaminationsliste vermisst und keinen Schnittpunkt liefert
→ qualitaetsmetrik.md §13a

**Landmarken-Term** *(landmark correspondence term)* — der Energieterm, der
eine solche Landmarke auf ihr **Tinten-Gegenstück** zieht: den nächsten
Verzweigungspunkt des Skeletts (ein Skelettpixel mit ≥ 3 Nachbarn im
8er-Umfeld, benachbarte zu einem Schwerpunkt verschmolzen). Er ist der
erste **Daten**-Term dieser Zielfunktion — *dieser Punkt gehört auf jenen
Punkt* — und damit kein fünfter Anlauf der vier verworfenen Terme (§7
Biegeenergie, §8 Scharnier, §10 Eckanker, §11d Nachbarbindung), die alle
einen **Stellvertreter** (Krümmung, Abstand, Steifigkeit) auf einer
zuordnungsblinden Zielfunktion bepreisten. Linearisiert wie jeder andere
Operator der Kette: Sehnenpaar und Sehnenparameter werden am Startzustand
**eingefroren**, die gefittete Kreuzung ist dann der Mittelwert der beiden
Zweigpunkte und damit linear in vier Ankern (exakter Gradient). Eine
Zuordnung, die nicht entscheidbar ist, wird **verworfen statt geraten**
(kein Kandidat im Radius, oder der zweitnächste liegt innerhalb der
Eindeutigkeitsmarge).
*Technisch:* `tools/pairlab/chain.py` — `CHAIN_LANDMARK_WEIGHT`
(**Standard 0,0**, byte-identisch; `KS_CHAIN_LANDMARK_WEIGHT`),
`CHAIN_LANDMARK_TARGET_RADIUS_UNITS` (0,55), …`_MARGIN_UNITS` (0,25),
Energie `e_landmark`, Gradientenanteil `landmark`; Sonde
`tools/pairlab/landmarklab.py` (Skalen-Kalibrierung + Wirkungsmessung)

**Naht** *(seam)* — die Stelle, an der im Kettenfit ein Buchstabe endet und
der Verbinder beginnt. Kunstgriff: Sie ist **kein Strafterm, sondern ein
geteilter Ankerindex** — der letzte Anker des Buchstabens und der erste
des Verbinders *sind dieselben Parameter*. Damit gilt Stetigkeit per
Konstruktion, und die Schnittstelle sitzt überall am gleichen Index statt
an einer pro Vorkommen verschiedenen Tintenlücke.
**Naht-Anteil (seam tail/head share)** = wie viel Bogenlänge des
Buchstabenendes der Verbinder für sich beansprucht; muss im gemessenen
Band von 0,2–0,4 xh bleiben, sonst ist die Segmentierung eine Eigenschaft
des Lösers statt der Hand.

**Vereinigungsfenster vs. buchstabenlokales Fenster** — *woran* gemessen
wird. Das buchstabenlokale Fenster ist der x-Bereich eines Buchstabens
plus Rand (`TRACE_WINDOW_MARGIN` 0,15 xh); das Vereinigungsfenster ist die
Vereinigung beider Buchstabenfenster **mit geschlossenem Loch dazwischen**
— es enthält also die Verbinder-Tinte. Der Kettenfit *rechnet* im
Vereinigungsfenster (das ist sein Zweck), wird aber *benotet* im
buchstabenlokalen (das ist der Maßstab, den der unabhängige Fit schon
immer hatte).

**like-for-like Gate** *(„gleichnamig messen“)* — die Forderung, zwei
Verfahren am **selben** Maßstab zu beurteilen. Konkreter Anlass: Stufe A
verglich eine Kette, die gegen Verbinder-Tinte benotet wurde, mit einer
Basislinie, die diese Tinte nie sah — der Rückstand war teilweise ein
Benotungsartefakt. Erst gleichnamig gemessen wird eine Zahl belastbar.

**matched arc · bogengleich** — dasselbe Prinzip für Formvergleiche: Zwei
Kurven dürfen nur auf dem **gemeinsamen Bogen** verglichen werden. Der
Kettenverbinder besitzt konstruktionsbedingt die Stub-Zonen, der aus der
Tinte gelesene beginnt erst an der Tintenlücke — schneidet man beide auf
dasselbe x-Intervall, schrumpfte der Abstand um rund drei Viertel
(0,046 → 0,011 xh). „Ein Teil der Distanz ist definitorisch, nicht
Formfehler.“

**Ink gap · Tintenlücke** — der tintenfreie Spalt zwischen den
Tintensäulen zweier Buchstaben. Historisch das Kriterium, wo ein
Buchstabe aufhört und der Verbinder anfängt — mit der bekannten Schwäche:
bei Berührung ist es **undefiniert** (Median-Lücke 0,251 xh, aber in
38 von 248 Vorkommen gar keine).
*Technisch:* `tools/pairlab/analyze.py::_ink_extent_x` / `_real_join`.

**Stub · Kopplungs-Stub** — die kurzen An- und Absatzstriche, die auf der
Lehrtafel an jeder isolierten Buchstabenzelle stehen (Entry-Stub:
Anstrich von halber Höhe; Exit-Stub: Grundlinienfuß nach oben). Im
verbundenen Wort existieren sie **nicht** — die echte Feder verlässt die
Form am letzten Strukturpunkt. Wer über die Stub-Spitzen hinweg verbindet,
baut ein „Shelf“ ins Wortbild. Gemessene Ersatzlänge 0,2–0,4 xh je Seite.
→ uebergaenge-befund.md §5

**tail_adapt · head_adapt** — wie weit die *echte* Feder die Glyphe selbst
für den Übergang umschreibt: die Bogenlänge (in xh) ab der Verbindung, über
die der letzte Strich von A bzw. der erste Strich von B von der
Template-Form abweicht (Schwelle 0,12 xh). Die Zahl beantwortet die Frage
„ist der Fehler im Verbinder oder schon im Buchstabenende?“.

**tail_stub_delta** — die Kennzahl des zugehörigen Kill-Kriteriums: wächst
dieser Wert unter einem neuen Verfahren systematisch, zieht das Verfahren
die Buchstaben-Auslauf-Enden mit — dann ist die gemeinsame Optimierung
das Problem statt die Lösung. (Gemessen wurde das Gegenteil: −0,006 xh.)

**Huber-Kappung** — ein robustes Fehlermaß: kleine Abweichungen zählen
quadratisch, große nur noch linear. Wirkung: ein Tintenklecks oder eine
fremde Spur im Messfenster kann den Fit nicht mehr beliebig ziehen.
*Technisch:* `CHAIN_COVERAGE_CAP_UNITS = 0.30` xh in `tools/pairlab/chain.py`.

**Bézier-Handle-Floor** — ein konkreter Bug-Fund, der zur stehenden
Redewendung wurde. Der Verbinder-Generator berechnet die Länge seiner
Bézier-*Griffe* (die Kontrollpunkt-Hebel, die die Kurvenform bestimmen) als
`handle = max(0.05, min(0.4·Sehne, 0.5·Δx))` — mit einer **Untergrenze von
0,05 xh**. Diese Untergrenze („floor“) ist im Rendering harmlos. Sitzen
zwei Buchstaben aber fast aufeinander, überschreibt sie den eigenen
Entwurfswert `0,4·Sehne`: die Kubik greift weiter aus, als die Sehne lang
ist, und **kehrt um**.
*Technisch:* `tools/pairlab/analyze.py::_generate_connector`
→ uebergaenge-befund.md §5c „Nachtrag: degenerierte Solves“

**Cusp-Connector** — das Ergebnis dieses Handle-Floors: ein Verbinder, der
in einer **Spitzkehre** (engl. *cusp* — eine Stelle, an der eine Kurve
umkehrt statt weiterzulaufen) zusammenfällt. Alle 24 Stützpunkte liegen
dann in ~0,05 xh Bogenlänge, benachbarte Punkte 8·10⁻⁵ xh auseinander.
Als *Bild* egal, als *Startwert für einen Optimierer* fatal (siehe
degenerierte Solves).

**degenerierte Solves** — Optimierungsläufe, die formal durchlaufen, aber
das Falsche optimieren. Konkret: Der Glättungsterm skaliert mit `1/ds²`
(ds = Ankerabstand); bei einem Cusp-Connector geht der Verbinder-Block
damit rund **10⁷-fach steifer** in die Hesse-Matrix ein als bei einem
normalen Übergang. Ergebnis: 24 von 248 Vorkommen verbrauchten ihr ganzes
Iterationsbudget auf das Geraderichten des Verbinders — **die Buchstaben
bewegten sich überhaupt nicht**. Sichtbar wurde es erst, als der Bench die
Abbruchmeldung des Optimierers wirklich exportierte (er hatte bis dahin
einen Schlüssel gelesen, den niemand schrieb).
Reparatur: `chain.regularise_connector_anchors` — eine
**Diskretisierungs**-Korrektur, keine Form-Korrektur.

**Sehnen-Schwelle** *(chord threshold)* — die Grenze, unterhalb derer ein
Verbinder neu diskretisiert wird: `CHAIN_CONNECTOR_MIN_SPAN_UNITS = 0.20`
xh. Sie liegt in einem messbar **leeren Band** — alle 24 betroffenen
Vorkommen hatten eine Sehne ≤ 0,187 xh, alle 224 gesunden ≥ 0,205 xh. Ein
sauberer Diskriminator, kein getunter Schwellwert.

**Degeneriewächter** *(connector QC)* — die nachgelagerte Prüfung, ob ein
gefitteter Ketten-Verbinder plausibel eine Schreibbewegung ist, statt quer
durch beide Buchstaben zu laufen (der zweite Degenerationstyp: formal
konvergiert, QC grün, aber eine lange gerade Diagonale). Vier reine
Geometrie-Signale — Naht-Anteil, Vorwärts-Verhältnis (`net_dx / arc`),
Bogen-zu-Lücke, Geradheit×Länge — hinter einer Mindest-Sehne, kalibriert
an den 11 bekannten Drill-Fällen (11/11 erkannt, ein nachweisbarer
Fehlalarm auf 179 belabelbaren Wortzeilen). Solange dieser Wächter nicht
auf beiden Sets fehlalarmfrei sitzt, bleibt `pair_aggregates` für
Ketten-Verbinder gesperrt.
*Technisch:* `tools/pairlab/connector_qc.py::connector_degenerate`,
Spalte `chain_conn_degenerate` im chainbench-Report.

**Kill-Kriterium** — ein *vorab* festgelegtes Ergebnis, bei dem ein
Vorhaben abgebrochen wird. Für Stufe A des Kettenfits waren es drei:
wachsende `tail_stub_delta`, Divergenz auf den Versalien und eine
Naht, die aus dem gemessenen Band läuft. Keines schlug an. Der Zweck ist
Disziplin: Man legt die Abbruchbedingung fest, **bevor** man die Zahlen
sieht.

**M1 · M2 · M3 · M4 (die vier Kettenfit-Kennzahlen)** — die Stufe-A-Prüfung
von Issue #278. Sie tragen dieselben Buchstaben wie die MVP-Meilensteine
(§5) und wie der „M4-Fit“, meinen aber etwas anderes — im Zweifel den
Kontext prüfen.

- **M1 — Konvergenz.** *Frage:* Konvergiert der Kettenfit pro Buchstabe
  mindestens so oft wie zwei unabhängige Fits? *Berechnung:* Anteil der
  Buchstabensegmente, die beide Konvergenz-Tore von `core/fit.py`
  bestehen, gemessen im buchstabenlokalen Fenster (like-for-like).
  *Stand:* Basislinie 0,746 · Kette **0,754** über 248 Vorkommen —
  **erfüllt**, nachdem die degenerierten Solves repariert waren (vorher
  0,690). Untergrenze für Stufe B: 0,754.
- **M2 — heute unmessbare Übergänge.** *Frage:* Wie viele Verbindungen,
  bei denen die heutige Zerlegung *nichts* liefert (weil die Buchstaben
  sich berühren), macht die Kette messbar? *Berechnung:* Anteil der
  Vorkommen mit leerem `_real_join`, für die die Kette einen
  konvergierten, mit Tinte belegten Verbinder liefert. *Stand:* **33 von
  38 = 87 % — erfüllt.** Das ist das stärkste Einzelargument des Verfahrens.
- **M3 — Verbinderform.** *Frage:* Liegt der Ketten-Verbinder so nah an
  dem aus der Tinte gelesenen Zug wie der erzeugte? *Berechnung:* `dconn`
  (§4) zwischen den beiden Mittellinien, **bogengleich** beschnitten.
  *Stand:* erzeugt 0,028 xh · Kette 0,040 xh (n = 193) — wörtlich
  **verfehlt**, aber nur noch um 0,011 statt 0,046 xh, und der Rest sitzt
  in **einer** Klasse: dem Schleifen-Exit (d, ſ) mit +0,17 xh. Deshalb
  bleibt der Bann, dass Ketten-Verbinder nicht in `pair_aggregates`
  fließen dürfen — `gen_chamfer` lebt davon, unkontaminiert zu sein.
- **M4 — Buchstabenform gegen das Rauschen.** *Frage:* Verbiegt die Kette
  die Buchstaben stärker, als die Hand ohnehin streut? *Berechnung:*
  mittlere Ankerabweichung Kette ↔ unabhängiger Trace, verglichen mit dem
  **MAD-Boden** aus den H1-Aggregaten derselben Hand. *Stand:* 0,0269 xh
  gegen einen Boden von 0,0112 xh — knapp **verfehlt**, aber ohne
  Verzerrungssignal: gegenüber der Chart-Zeile verformt die Kette
  *weniger* (0,0140 vs. 0,0170 xh). Sie verbiegt die Buchstaben nicht
  stärker, sie stellt sie anders hin.

---

## §4 Metriken und Benchmarks

**Score · loss · `bench_loss`** — Ein **Score** geht von 0 bis 100 (100 =
perfekt), **`loss = 1 − score/100`** ist dieselbe Information in der
Loop-Konvention „kleiner ist besser“. **`bench_loss`** ist der
*Mittelwert* der Einzel-Losses über alle Fixtures — bewusst Mittelwert
statt Median, damit eine einzelne verschlechterte Glyphe die Kopfzahl
sichtbar bewegt. Ein Absturz zählt als 1,0. → qualitaetsmetrik.md §1

**`pair_loss`** — dieselbe Kopfzahl für das getrennte Set der isolierten
Buchstabenpaare (Abb. 20). Wörter und Paare bekommen eigene Headlines und
werden **nie** gemittelt. Der aktuelle Stand steht bewusst **nicht hier**:
eine Zahl in zwei Docs veraltet in einem davon (dieser Satz nannte bis
2026-09-02 noch den Lauf `aug02`). Er wohnt im Status-Blockquote von
qualitaetsmetrik.md, seine Historie samt Fixture-Wurzeln im
Headline-Ledger am Kopf von §14. → qualitaetsmetrik.md §6 ·
messjournal.md §14

**Chamfer-Distanz** — ein Standardmaß für „wie weit sind zwei Formen
auseinander“: für jeden Punkt der einen Form der Abstand zum nächsten
Punkt der anderen, gemittelt. Symmetrisch (beide Richtungen) oder
gerichtet („Vorwärts-Chamfer“). Kommt in fast jeder Kennzahl dieses
Projekts vor.

**Dice** — das Flächenmaß daneben: doppelte Überlappung geteilt durch die
Summe beider Flächen (1 = deckungsgleich). Beantwortet „sieht es aus wie
der Ausschnitt“, während Chamfer „liegt die Kante auf der Kante“ misst.

**Tintenabstand** *(`ink_max` / `ink_mean`)* — Abstand der gefitteten
Mittellinie zur **gemessenen Tinte** (Skelett der Platte), in x-Höhen.
Das Bodenwahrheitsmaß eines Fits, und zwar **in beide Richtungen**: das
Maximum bepreist den Fehler (ein Stück Linie im leeren Papier), der
Mittelwert bepreist, ob eine Verbesserung des Maximums damit erkauft
wurde, dass die ganze Kette von der Tinte wegwandert. Beide zusammen sind
die Pflichtprüfung für jeden Regularisierer am M4-Fit — **Formmaße allein
genügen nie** (siehe **Anker im leeren Papier**).
→ qualitaetsmetrik.md §7

**Anker im leeren Papier** — die benannte Fehlerform des M4-Fits: ein
*einzelner* Anker verlässt den Strich und kehrt im nächsten Schritt
zurück. Physikalisch unmöglich — eine Feder schreibt Bögen und Geraden —,
für die Zielfunktion aber unsichtbar, weil dort alles Mittelwerte sind.
Ein solcher Anker vergiftet über den Vorkommens-Median die Laufform.
Gegenmittel in drei Stufen: die **Vorkommensschranke** verhindert, dass
ein einzelner ihn in den Schreibpfad trägt; das **Spike-Gate**
(`anchor_spike`) verwirft die unbrauchbare Messung an der Quelle; und seit
`aug11` wird der Ausflug in ANGENOMMENEN Vorkommen **repariert** —
Interpolation der Nachbarn im eigenen Federzug, protokolliert in
`measurements.repaired_anchors`, das Gate urteilt weiter über die
unreparierte Geometrie. Vier Fit-Terme dagegen (Biegeenergie, Scharnier,
Eckanker-Stützung, **Nachbarbindung**) wurden gemessen und **verworfen**.
→ qualitaetsmetrik.md §7, §8, §11d, §11e

**Spike-Verhältnis** *(`anchor_spike_ratio`, Gate `anchor_spike`)* — die
Kennzahl hinter dem **Anker im leeren Papier**: größter Schritt zwischen
benachbarten Ankern, gemessen am Median-Schritt **seines eigenen
Strichs**, maximiert über die Striche. Absetzer zählen nie (eine
Strichgrenze ist die Hand, die neu ansetzt). Je Strich statt gepoolt,
weil ein langer Körperstrich sonst den Nenner aufbläht und einen Zacken
im kurzen Umlautstrich verdeckt. Ab `MAX_ANCHOR_SPIKE_RATIO` = 8,0
verwirft die Ernte das Vorkommen — nicht als Reparatur, sondern als
Aussage: eine Kette mit einer Unstetigkeit hat die Hand nie gemessen.
→ qualitaetsmetrik.md §8

**`gen_chamfer`** — **die Auditzahl „gemessen vs. komponiert“.** Abstand
zwischen dem *erzeugten* Übergang und dem an derselben Stelle aus der
Vorlage *gemessenen*. Sie sagt, wo und wie weit der Generator danebenliegt
— und ist damit die Grundlage jeder Entscheidung über eine Klassenregel.
Genau deshalb darf sie nie von Geometrie gespeist werden, die selbst vom
Generator abstammt (Prior-Kontamination).

**`doff`** — *Platzierung*: der **horizontale** Versatz zwischen
komponierter und gemessener Verbindung, abgelesen im **Körper-Rahmen**
(vom Ende der letzten Nicht-Diakritikum-Spur des linken Glyphs zum Anfang
der ersten des rechten). Nur x, weil die y-Komponente der Messung
konstruktionsbedingt keine Vorlagen-Information trägt. Nulllinie: Wörter
0,135 · Paare 0,192 xh.

**`dconn`** — *Form*: mittlerer punktweiser Abstand der beiden
Verbindungs-Mittellinien, beide bogenlängen-gleichmäßig auf
`core.aggregate.PAIR_CONNECTOR_POINTS` (24) resampelt und auf ihren
eigenen ersten Punkt gelegt. **Start-aligniert, also translationsfrei** —
die Platzierung ist allein Sache von `doff`. Kein kalibrierter
Absolutabstand, sondern ein monotones Signal: gleiche Verbindung, kleinere
Zahl = näher an der Vorlage.

**Anker · Sample · Schritt** — die drei Sorten Punkt, die im Fit alle wie
Punkte aussehen und ständig verwechselt werden. **Anker** sind die
Stützpunkte der Spline, also die Freiheitsgrade des Fits (120 je Buchstabe,
`templates.anchors`). **Samples** liegen auf der Spline zwischen ihnen — und
NUR dort liest die Zielfunktion die Tinte ab (~180 je Buchstabe); kein Anker
wird je selbst befragt. **Schritt** ist der Abstand zweier benachbarter Anker,
worauf `anchor_spike_ratio` misst. Ein Anker wirkt also nur mittelbar, über
die ein bis zwei Samples in seiner Umgebung; wer die Rückstellkraft am
Ankerort misst, beziffert eine Kraft, die in der Rechnung nicht vorkommt —
was einmal eine Fehldiagnose gekostet hat. Achtung auch beim Zeichnen:
`fitted_polyline_px` ist die SAMPLE-Reihe, nicht die Ankerreihe.

**Nachbarbindung** *(`core.fit.DEFAULT_SMOOTH_WEIGHT`,
`chain.CHAIN_LETTER_BIND_WEIGHT`)* — der Fit-Term gegen den **Anker im leeren
Papier**: die zweite Differenz der **Verschiebungen** je Federzug. Eine
Verschiebung des ganzen Strichs kostet exakt nichts, ein einzelner Anker, der
seine Nachbarn verlässt, quadratisch. Das unterscheidet ihn von den beiden
verworfenen Vorläufern: der **Biegeterm** (§7) nahm die zweite Differenz der
ANKER und bepreiste damit die Krümmung, aus der eine Schrift besteht; das
**Scharnier** (§8) bepreiste den Abstand („ein Sprung auf nahe Tinte ist immer
noch ein Sprung"). Existiert zweimal, weil es zwei Fit-Pfade gibt — im
Einzelbuchstaben-Fit und in den BUCHSTABENBLÖCKEN der Kette, wo alle
gespeicherten Vorkommen herkommen; nicht zu verwechseln mit
`CHAIN_CONNECTOR_SMOOTH_WEIGHT`, der die ANKER eines frei erfundenen Verbinders
glättet. **Gemessen und verworfen** (§11d): der Term wirkt — gestrandete Anker
−58 %, Spike-Verhältnis −45 % — und verschiebt trotzdem 18 % **mehr** Anker aus
der Tinte heraus, weil ein gebremster Anker seine Nachbarn mitnimmt. Aus einem
Anker im leeren Papier werden drei. Beide Gewichte bleiben auf 0.
→ qualitaetsmetrik.md §7, §8, §11a, §11d

**Zirkuläres Kriterium** — der Fehlschluss, einen Eingriff an einer Kennzahl zu
messen, die er selbst bestraft. Zweimal gemessen dokumentiert: die
**Nachbarbindung** senkt `anchor_spike_ratio` per Konstruktion, und weil das
Ernte-Gate denselben Grund führt, sah ihr Mehr-Ertrag (209 → 218 angenommene
Vorkommen, McNemar p = 0,021) wie ein Produktgewinn aus — **jeder** Gewinn war
ein zuvor mit `anchor_spike` abgelehntes Vorkommen, während die echte
Konvergenz schlechter wurde. Gegenmittel und Pflicht jeder Vorregistrierung:
ein Kriterium, das **weder in der Zielfunktion noch im Gate** steht (hier der
Abstand des gespeicherten Ankers zur Tinte). → qualitaetsmetrik.md §11b, §11d

**Gradientenzerlegung** *(`chain.gradient_decomposition`, `tools/pairlab/gradlab.py`)*
— die Diagnose, die vor jedem neuen Fit-Term steht: die Kraft **je Term und
je Anker** am gefundenen Optimum. Ein Optimum ist ein Punkt, an dem sich die
Kräfte aufheben; welcher Term einen Defekt festhält, ist damit eine
**Messfrage**, keine Vermutung. Bauregel — und der Grund für den Namen:
die Terme werden einzeln gerechnet und ihre **Summe gegen den echten
Gradienten geprüft** (`GRADIENT_SUM_RTOL`), sonst beschreibt die Diagnostik
eine andere Zielfunktion als die, der der Löser gefolgt ist. Gelesen wird
immer gegen eine **Kontrollpopulation** (dieselben Terme an den unauffälligen
Ankern derselben Lösung): ein Term, der am Defekt genauso stark zieht wie
überall, erklärt ihn nicht. → qualitaetsmetrik.md §11
*Technisch:* `core/fit.py::_sampling_operator`,
`core/template.py::build_sample_plan` → vom-scan-zum-schreiben.md Schritt 4

**`d_end`** *(verworfen)* — Abstand des Kettenendes eines gefitteten
Buchstabens zur nächsten Tinte, in x-Höhen; gedacht als „Nahtstellen-Kennzahl"
für die Fehlerart `E` („Knick nur am Rand"). Sie hat ihr vorregistriertes
Bestätigungskriterium auf der Rückhaltemenge **bestanden** (AUC 0,764,
p = 0,012) und wird trotzdem **nicht geführt**: gegen die anderen Fehlerarten
trennt sie auf Zufallsniveau (`E` gegen `W`/`B` 0,539), ist also nicht
nahtspezifisch, und sie bleibt hinter dem längst berechneten `peak` zurück
(0,888 für „irgendein Mangel" gegen „gut"). Der Eintrag steht hier, weil der
Name in §9/§10 vorkommt und weil „bestätigt, aber unbrauchbar" die Lehre der
Runde ist. *Technisch:* qualitaetsmetrik.md §10

**`meas`** *(Report-Spalte)* — die Zeile, die `doff` und `dconn` je
komponierter Verbindung im Wordbench-Report ausweist, plus Blockmediane
und `meas_excluded`. Ausgeschlossen (gezählt, nie stillschweigend): Zeilen,
deren Dissektion die Ernte selbst verworfen hat (`fit_ok`), und
Verbindungen, die aus einem freigegebenen Override gerendert wurden — ein
Override misst gegen sein eigenes Quell-Specimen konstruktionsbedingt ~0.
*Technisch:* `tools/wordbench/pairmeas.py`

**Report-Spalte** — eine Zahl, die **nie in den Loss eingeht**. Bauweise
im Repo streng festgelegt: eigener try/except, angehängt *nach* dem
stabilen Block, und der **Headline-Nachweis ist Pflicht** — ein Lauf vor
und nach der Einführung muss bis zur letzten Stelle identisch sein. Die
Linie dieser Spalten: Slant (R5) → Gleichzug (`jul30`) → `meas` (`aug02`)
→ Naht-Winkel (`sep02`).

**Slant-Spalte** — Report-Spalte, die die gemessene Schräglage der Vorlage
gegen die der komponierten Zeile stellt (90° = senkrecht), aus dem
Spaltenprofil. `tools/wordbench/slant.py`.

**Gleichzug-Audit** — Report-Spalten für zwei physikalische Invarianten
einer Gleichzug-Schrift: **(a) EIN FLUSS** — aufeinanderfolgende
Pen-down-Elemente müssen Ende-an-Anfang schließen (eine Lücke heißt: der
Stift ist gesprungen); **(b) EINE STRICHBREITE** — zwei fast parallele
Pfadstücke in einem bestimmten Abstandsband lesen sich als doppelt breiter
Strich („Doppelung“). Exaktes Nachfahren (Retrace) und transversales
Kreuzen sind erlaubt. `tools/wordbench/gleichzug.py`.

**Naht-Winkel** *(`seam_deg`)* — wie stark die Feder an der **Naht**
abknickt, also dort, wo ein generierter Verbinder den Buchstaben verlässt
(`dep`, Abgang) und den nächsten erreicht (`arr`, Ankunft). Gemessen wird
die Richtungsdifferenz **Abgehend minus Ankommend in Schreibrichtung**, in
Grad, positiv = die Feder dreht gegen den Uhrzeigersinn; das Fenster ist
mit 0,05 xh Bogenlänge bewusst *kleiner* als die 0,12 xh, auf die der
Composer seine Verbinder-Tangenten ausrichtet — auf dem Fenster der
Konstruktion selbst gemessen wäre der Restknick per Definition null. Auf
der eingefrorenen 1922er Worttafel geht der Verbinder im Median **+11,87°**
steiler ab, als der Buchstabe zuletzt lief, und kommt **−3,26°** flacher
an (Prüfung 2026-09-02, 206 von 214 Joins). Ausgeschlossen und gezählt:
Verbinder mit vorangestelltem Versal-Rückzug (deren „Abgang“ ist eine
gewollte 180°-Kehre). Echte Kehren (ſ/w/r/v) bleiben drin — Duktus, kein
Defekt. Report-Spalte, nie Teil des Loss.
*Technisch:* `tools/wordbench/seam.py::seam_angles`, `SEAM_WINDOW`;
Blockzeilen `seam_dep_median` / `seam_arr_median` (vorzeichenbehaftet) und
`seam_*_abs_median`. → tools/wordbench/README.md

**Natürlichkeitsmetrik (Sütterlin)** — die zweite, *referenzfreie* Metrik:
Weil Sütterlin einen pixeligen Scan mit konstanter Strichbreite hat, wäre
Pixeltreue das falsche Ziel. Stattdessen `score = 100 · Tor^0,5 ·
Natürlichkeit` — die **Deckung ist nur das Tor** (eine glatte Glyphe am
falschen Ort kann nicht hoch scoren), entschieden wird über fünf Terme am
gerenderten Verlauf: Glätte · Vertikalität · Eckenschärfe · Kollinearität
· Rückzug-Treue. **Zwei Metriken, eine pro Schrift** — ein kombinierter
`bench_loss` über Schwellzug und Gleichzug wäre bedeutungslos.
`core/quality_suetterlin.py` → qualitaetsmetrik.md §5

**Messboden** — die Erkenntnis, dass 100 nicht erreichbar ist: runde
Federkappen gegen eckige Balkenenden, ±0,5 px Binarisierungs-Unsicherheit
an jeder Kante eines Drucks von 1866. Praktisch heißt das: **hohe 80er /
niedrige 90er ≈ im Rahmen der Messbarkeit perfekt.**

**Frozen-Reference-Regel** — die Torpfosten stehen fest. Eingefroren sind
Maske, Skelett, EDT, die geshapten Slots, die Template-Zeilen, der
gepoolte Nib und (seit `aug02`) `pair_instances.json`. Ein Experiment kann
die Metrik nicht dadurch „verbessern“, dass es die Binarisierung
verschiebt oder das Ziel neu exportiert. Während eines
Optimierungs-Loops sind zusätzlich Metrik-Module und Tests eingefroren:
geändert wird der Composer, nie das Lineal.

**Re-Baseline** — der bewusste, menschlich entschiedene Neu-Export dieser
Referenzen. **Zahlen über eine Re-Baseline hinweg sind nicht
vergleichbar** und werden im Journal ausdrücklich als solche markiert.

**Wurzel-Digest** *(`root_digest`)* — der Fingerabdruck einer
Fixture-Wurzel, damit man einer Kennzahl ansieht, **worauf** sie gemessen
wurde: SHA-256 über die *sortierte* Liste aus (relativem Pfad, Größe,
SHA-256 der Bytes) aller Dateien der Wurzel. Deterministisch (die
Sortierung ist die einzige Reihenfolge), blind für DATEISYSTEM-Zeitstempel
und Rechte (eine kopierte Wurzel behält ihre Identität), empfindlich schon
gegen ein einzelnes gekipptes Byte oder eine bloß hinzugefügte Datei.
**Der Digest identifiziert damit einen EXPORT, nicht einen DB-Stand**
(Befund `sep02`, §14 „Laufform LF11 — humanbench-Wortrunde"): das
`exported_at` im `manifest.json` ist Inhalt und geht mit ein, also
bekommen zwei Exporte derselben unveränderten Daten verschiedene Digests
und messen trotzdem identisch. Zu zitieren ist der Digest der Wurzel, auf
der wirklich gemessen wurde; ein Neu-Export verlangt einen neuen Digest,
ohne dass sich eine Zahl bewegt. Weil die
Wurzeln gitignored sind, hinterlässt ein Neu-Export sonst keine Spur — die
Prüfung vom 2026-09-02 fand ein Zahlenpaar, dessen Grundlage niemand mehr
rekonstruieren konnte (die **undeklarierte Re-Baseline**). Hausregel:
**jede genannte Headline nennt `exported_at` + die ersten 12 Hex daneben**;
`--expect-root <Präfix>` macht die erwartete Grundlage zur Vorbedingung und
bricht *vor* dem Messen ab.
*Technisch:* `tools/wordbench/run.py::root_digest`, Kopfzeilen `root:` /
`digest=`, volle Digests im `--json`-Report unter `roots`; im selben Zug
prüft der Messlauf das `page_sha256` des Manifests gegen die Tafel-Bytes.
→ tools/wordbench/README.md

**MAD** *(median absolute deviation)* — die robuste Streuung: Median der
absoluten Abweichungen vom Median. Anders als die Standardabweichung
verzieht ein einzelner Ausreißer sie nicht. Im Projekt die Streuungsangabe
schlechthin (MAD-Hülle je Anker, MAD-Whisker am Versatz). Hausregel:
**bei fehlender MAD wird kein „± 0,00“ gedruckt** — und bei n = 1 gibt es
keine.

**`laufform_dev_xh`** *(der Prüfstein)* — die Antwort auf „ist das, was die
Engine schreibt, noch das, was die Statistik sagt?“: der Abstand zwischen
dem aus den Vorkommen rekonstruierten Median und der aktuell gespeicherten
Laufform-Zeile. 0 = aktuell; ein Wert > 0 = veraltet. Wird auch schon beim
reinen *Lesen* der Aggregate mitgeliefert, damit die Frage ohne einen
Neuaufbau beantwortbar ist. `core/aggregate.py::laufform_deviation`

**Prüfstein** — allgemein: eine Bedingung, an der eine ganze Stufe geprüft
wird und die bindend über alle Stufen gilt (z. B. „nie über Hände mitteln“,
„Duktus bleibt Prior“, „Same-Hand-Headline unangetastet“).
→ handmodell-stufenplan.md §5

**Same-Hand-Disziplin** — Kopfzahlen werden nur gegen Vorlagen **derselben
Hand** gebildet. Die Abb.-22-Schülerschrift ist ein anderer Schreiber und
läuft als eigenes Set mit eigener Zahl, nie in der Headline. Fremde Hände
sind Kontext, nie Maßstab.

**Segment-Attribution** — die Zerlegung eines Wort-Losses auf seine Teile:
welcher Buchstabe und welcher Übergang trägt wie viel. Erst damit ist ein
Score handlungsfähig („der zweite n-Bogen kostet 0,11“ statt „das Wort ist
0,19“). `core/word_metric.py::score_word_segments`

**glyphbench · wordbench · pairlab · chainbench · glyphlab · wordlab** —
die Werkzeugfamilie. **Benches** *messen* (glyphbench: einzelne Buchstaben
gegen eingefrorene Referenzen; wordbench: komponierte Wörter und Paare
gegen echte Wortproben; chainbench: die beiden Fit-Pfade gegeneinander).
**Labs** *zeigen*: matplotlib-Overlays, aus denen man sieht, **warum** eine
Zahl schlecht ist (glyphlab: die Ableitung eines Buchstabens; wordlab: ein
komponiertes Wort über seiner Vorlage mit Penalty-Callouts; pairlab: die
Sektion eines Übergangs). Daneben steht als dritte Gattung **humanbench**,
das nicht rechnet, sondern *fragt*: es baut den blinden
**Bewertungsdurchgang** und wertet dessen Urteile aus. Merksatz aus den
Läufen: **die Skizzen des Autors waren das Messinstrument, der Bench der
Regressionswächter.** → werkzeuge.md

**Fixture-Wurzel** — das eingefrorene Eingabepaket eines Bench-Sets
(Crops, Masken, Skelette, Slots, Template-Zeilen, Laufform-Zeilen,
`pair_instances.json`, `word_instances.json`). Gitignored
(Open-Core-Moat), neu erzeugbar über
`tools/wordbench/export_fixtures.py` (DB-Pfad) oder `fetch_fixtures.py`
(API-Pfad, für Sitzungen ohne DB-Zugang).

**Referenzsatz (nachgefahren)** — die manuell per S-Pen nachgefahrenen
Wortbahnen (`word_instances`, Provenienz `authored`), an denen jeder
automatische Wortbahn-Kandidat gemessen wird. Der **Entwicklungssatz**
(Tuning) sind heute die 10 am 2026-08-13 nachgefahrenen Abb.-19-Wörter
(die · laden · linken · mit · muß · und · unter · Wer · will · zwei),
committete Konstante; jedes SPÄTER nachgefahrene Wort ist per Definition
**Rückhaltemenge** (Bestätigungssatz). Die tragende Invariante: Bewegung
gibt es nur BLIND und vorregistriert in Richtung Entwicklungssatz, nie
zurück — ein Wort, auf dem je getunt oder dessen Zahl je gelesen wurde,
kann nie wieder Prüfmaterial werden. Seit der **Split-Neuziehung**
(tintenfolger.md §2.5, vorregistriert 2026-08-16) ist die Rückhaltemenge
zweigeteilt: **Bestätigung A** (offen für vorregistrierte
Bestätigungsmessungen) und **Bestätigung B** (VERSIEGELT, öffnet erst
für die großen Adoptionsentscheidungen); der Entwicklungssatz wächst bei
Vollausbau der 63 Wörter deklariert um Galoppieren + das (12 Wörter /
19 Vorkommen). Ein Kandidat kann nie sein eigener Maßstab sein: die
`traced`-Ernte-Fits sind Ausgaben des Kandidaten, nicht seine Wahrheit.
*Technisch:* `word_instances.json` je Fixture-Wurzel;
`tools/tracebench/sets.py::TRACEBENCH_DEV_IDS`
→ proposals/tintenfolger.md §1 + §2.5

**Frame-Gate (`frame_stale`)** — der Maschinencheck, dass die
Registrierung einer gespeicherten Wortbahn noch die eingefrorene
Rect/Lineatur beschreibt, über deren Crop sie gezeichnet wird:
`|baseline_row+ty − (baseline_y−y0)| ≤ 4 px` (der vertikale Suchbereich
des Score-Gitters) und `|xh_px − (baseline_y−midband_y)| ≤ 0,51 px`
(halbes Pixel über ganzzahliger Lineatur). Fehlschlag STEMPELT die Zeile
(`frame_stale` mit Grund), droppt sie nie — Konsumenten zählen-und-
schließen-aus. Generalisiert die #334/#336-Fehlerklasse (Rect unter
gespeicherter Bahn editiert); beim `--only`-Refill prüft es gegen die
eingefrorenen `word.json` der Wurzel, beim Voll-Export gegen das Sidecar.
*Technisch:* `tools/wordbench/export_fixtures.py::_frame_stale_reason`

**tracebench** — der dritte Bench neben glyphbench (Buchstabe) und
wordbench (komponiertes Wort): er misst WORTBAHN-Kandidaten (Kettenfit,
Tintenfolger, InkSight, später Fusion) gegen den nachgefahrenen
Referenzsatz — Punktdistanz (`dtw_xh`), papertreues AIoU gegen die
Tintenmaske, Richtungs-Chamfer, Fehlerzähler an Kreuzungen/Marken/
Retraces. Ein Kandidat ist wörtlich eine `word_instances`-Zeile; die
Kriterien sind vorregistriert (messjournal.md §14), ein
Strukturdefekt vetot jeden Distanzgewinn. *Technisch:* die Mess-Module
`tools/tracebench/{metric,frames,counters,sets}.py` (Stufe B); Harness +
Provider folgen als Stufe C → proposals/tintenfolger.md §2

**k0-Protokoll** — die referenzfreie 63er-Auswertung der Ketten-Arme
(seit K0-Z `aug20`), das Gegenstück zum dev-19-Scoring: je Wort der
**Soll-Abstand** |Kreuzungen − Kompositions-Soll| + |Retrace-Zonen −
Zonen-Soll| (Soll aus `ductus_soll`, seit K0-S die EINE Soll-Pipeline
mit dem Wächter) plus `aiou` gegen die eingefrorene Maske; gepaart
über eine Basis mit Strich-Identitäts-Klassen (welche Zeilen sich
zwischen zwei Kandidaten überhaupt bewegten — verglichen werden die
geparsten Strichzüge, nicht die Datei-Bytes; in den §14-Einträgen
bis `aug21` „byte-identisch“ genannt — die Grundlage der
Identitäts- und Konstruktions-Vorhersage-Gates). Die stehende
aiou-Verlierer-Schwelle je Wort ist −0,003 (Messrauschen). Bis
`aug21` je Runde als Scratch-Skript neu gebaut, seither
`tools/tracebench/k0eval.py`. *Technisch:* Zähler aus
`tools/tracebench/counters.py`, Soll aus `soll.py` →
messjournal.md §14 „Kette K0-Z" (Erstform), werkzeuge.md
(Mess-Liturgie)

**`dtw_xh`** — die Headline-Distanz des tracebench: unconstrained DTW
(euklidisch, in xh, symmetric-1-Schritte, beide Enden verankert, kein
Band), normalisiert durch die Länge T des optimalen Warping-Pfads (die
LDTW-Normalisierung, §6), beide Bahnen vorher arc-length-uniform
resampelt. **Nur vorwärts** — die Richtung ist Duktus-Wahrheit, ein
rückwärts besser passender Kandidat ist ein Duktus-Fehler
(Report-Spalte `dtw_reversed_better`, nie verrechnet). Eigener Name,
bewusst nicht „LDTW": Resampling + xh-Einheit machen die Zahl mit
publizierten Werten unvergleichbar. QC-Begleiter `dtw_max_absorption`
(max. Punkte einer Seite auf EIN Sample der anderen — der
Singularitäts-Wächter). *Technisch:* `tools/tracebench/metric.py::dtw`

**Marke** *(mark)* — die Strichklasse, die der tracebench VOR dem
Body-Vergleich herauslöst und separat zählt: ein nicht-erster Strich,
der komplett über `DIACRITIC_MIN_Y` (= 1 xh) schwebt und die
**Bogen-Kappe** nicht überschreitet — i-Punkt/-Strich, Umlautzeichen
und der u-Deckstrich. Letzterer erst seit `aug26`: bis dahin machte
ihn die Kappe zum Body, entgegen dieser Aufzählung und entgegen der
Erwartungstabelle `MARKS_PER_KEY` (→ **Bogen-Kappe**).
Der t-Querstrich kreuzt das Mittelband und bleibt Body (ihn zählt der
Kreuzungszähler). Gematcht per Zentroid mit Refusal; **fehlende Marken
sind Co-Primär-Gate**, mit gutem Body-`dtw_xh` nicht rückkaufbar — der
verschluckte i-Punkt ist der dokumentierte Fehlermodus des ganzen
Felds, den keine publizierte Metrik erfasst. *Technisch:*
`tools/tracebench/frames.py::classify_strokes`/`match_marks`

**Bogen-Kappe** *(arc cap)* — die dritte Bedingung der Marken-Klasse
(`MARK_MAX_ARC_UNITS`): ein schwebender Strich zählt nur bis zu dieser
Bogenlänge als **Marke**, darüber als Body. Sie hält aus der
Marken-Klasse heraus, was nur zufällig in der Oberlänge bleibt — ein
abgesetztes Versalien-Ornament, eine Oberlängenschleife, ein
Fit-Defekt, dessen Bahn die Tinte verlässt: solche Striche würden sonst
zur Marke erklärt und verschwänden damit aus dem Primärmaß.
Steht seit `aug26` bei **1,5 xh**, davor bei 0,8 — und 0,8 lag
INNERHALB der Marken-Population statt zwischen Marke und Body: auf der
eingefrorenen Referenz enden Punkte und Umlaute bei 0,652 xh, die
u-Bögen beginnen bei 1,039 xh. Die Höhe ist aus dem Breitenmodell
begründet (ein Kleinbuchstabe ist eine x-Höhe breit, ein Diakritikum
steht über EINEM Buchstaben), nicht aus der Verteilung; **angehoben und
nicht gestrichen**, weil die Kappe sonst ihren eigentlichen Zweck
verlöre. `--mark-arc-cap` reproduziert jeden alten Wert. *Technisch:*
`tools/tracebench/frames.py`. Der Marken-Nachfit hat seit `aug26` eine
EIGENE Kappe (`tools/pairlab/marks.py::MARK_MAX_INK_ARC_UNITS`, 1,6) —
früher davon abgeleitet, entkoppelt, damit eine Lineal-Änderung nicht
still die Kandidatenseite mitbewegt.
→ messjournal.md §14 „Lineal L-U"

**Retrace-Segment** — zweimal beschriebene Tinte als GEZÄHLTE Zone:
zusammenhängende antiparallele Sample-Paare (Detektor
`core.geometry.detect_retrace_pairs`, prox 0,15 xh, ≥ 3 Samples auf
gemeinsamem 0,02-xh-Raster), wobei Hin- und Rückschenkel EINER
Aus-und-zurück-Bewegung zu einer Zone fusionieren (über die
Partner-Indizes des Detektors — sonst verweigert das Zentroid-Matching
eine Bahn gegen sich selbst, und das authored-Identitäts-Gate schlüge
auf jedem Deckstrich-Wort an). Seit den Struktur-Zählern v2
(messjournal §14 `aug16`) zählt ein Pass nur als Retrace, wenn
sein Partner BOGEN-NAH liegt (Lücke ≤ 1,0 xh) und der Pass keine
Spitzen-Graze ist (Arc ≥ 0,30 xh); ferne Antiparallel-Nähe ist eine
→ Berührung, ein Partner im anderen Strich eine Überlagerung.
Robusteste Vergleichszahl ist das Bogen-Verhältnis
`retrace_arc_ratio`, die Zonen-Counts sind die Ortsdiagnose.
*Technisch:* `tools/tracebench/counters.py::count_retraces`

**Junction-Pinch** — der `aug17` benannte Verlustmechanismus der
Lotse-Route an Schleifenschlüssen: Der Viterbi-Ritt routet beide
Pässe eines Selbstschnitts über dieselben 1–3 Korridor-Pixel des
Skelett-Knotens; statt eines transversalen X entstehen zwei
tangentiale Y-Zusammenläufe, die das Durchstoß-Kriterium zu Recht
nicht zählt. Zwei Unterklassen mit verschiedenen Heilmitteln: der
PUNKT-Pinch (der spätere Pass belegt Korridor-Pixel erneut —
erreichbar über die Zonen-Ausweitung der Kartenfahrt, v0.7) und die
SCHLEIFEN-Klasse (der Aufwärts-Pass boardet die verschmolzene
Schiene genau auf Kreuzungshöhe, es gibt keine Wiederbelegung —
erreichbar nur über Karten-Vorfahrt an Karten-Selbstschnitten,
v0.8/v0.9). *Technisch:* `tools/inkpilot/pilot.py`
(`RIDE_DOUBLE_ZONE_MARGIN_UNITS`, `MAP_CROSSING_WINDOW_UNITS`,
`MAP_CROSSING_PIN`) → messjournal.md §14 „Lotse v0.7–v0.9",
proposals/tintenfolger.md §7.10

**Absprung** *(Lotse)* — ein maximaler Lauf von mindestens zwei
Punkten der Lotse-Bahn, die AUSSERHALB des Tintenkörpers liegen.
Der Körper ist die Vereinigung der Scheiben mit Radius
`width_map[p]` um jedes Skelettpixel `p`; in der
Medialachsen-Näherung ist der Abstand davon `slack = edt −
width_map[nächstes]`, negativ in der Tinte, positiv daneben, gemessen
in x-Höhen. Weil der Ritt das Skelett per Konstruktion fährt, ist
jeder Absprung von einem benannten Mechanismus gesetzt. Die
`sep04`-Forensik misst auf dev-19: `bridge_no_rail` kommt in 7 958
emittierten Punkten **kein einziges Mal** vor, der Schienen-Auslauf
liegt in 201 Punkten nie daneben, der gewöhnliche Ritt in 2 von
6 872 — was danebenliegt, ist **Karten-Vorfahrt**, und die
Ritt-Doppelzone in 49,5 % ihrer Punkte. Zwei Klassen tragen ihn:
Karten-Abdrift und Fenster-Versatz (beide unten). *Technisch:*
`tools/inkpilot/forensics.py` (`ink_slack_field`, `jump_events`,
`traced_pilot_word`, `blame`) → messjournal.md §14 „Lotse
Absprung-Forensik `sep04`"

**Karten-Abdrift** — die `sep04` benannte GEERBTE Absprung-Klasse der
Lotse-Route: In einer Ritt-Doppelzone gilt Karten-Vorfahrt
(`RIDE_DOUBLE_MAP_PRIORITY` seit v0.5, ausgeweitet um
`RIDE_DOUBLE_ZONE_MARGIN_UNITS` seit v0.7), und weil
`MAP_RUN_PIN_KNOTS` seit v0.16 auf „bridges" steht, wird der Lauf
NICHT an die Tinte zurückgepinnt — der Folger reicht die komponierte
Karte wörtlich durch. Messbar daran, dass der Überschuss des Stifts
über die Karte im Median exakt **+0,0000** ist: der Lotse fügt nichts
hinzu. Die Klasse trägt die tiefsten (bis 0,269 xh) und längsten
(Bogen bis 0,84 xh) Absprünge und sitzt zu 9 von 11 an einem
Skelettknoten vom Grad ≥ 3. **Ihre Ursache liegt in der
PLATZIERUNG der Komposition, nicht im Folger** — der Lotse macht sie
nur sichtbar; die Rettungswege stehen darum bei den Platzierungs-Armen
(§7.9). *Technisch:* `tools/inkpilot/pilot.py`
(`RIDE_DOUBLE_MAP_PRIORITY`, `RIDE_DOUBLE_ZONE_MARGIN_UNITS`,
`_assemble_ride`s `map_mask`) → messjournal.md §14 „Lotse
Absprung-Forensik `sep04`", proposals/tintenfolger.md §7.9

**Fenster-Versatz** — die `sep04` benannte SELBST GEMACHTE
Absprung-Klasse der Lotse-Route und der einzige Mechanismus, mit dem
die Route die Tinte aus eigenem Antrieb verlässt: In einem gepinnten
Kreuzungs-Fenster wird die Kandidatenmenge des Viterbi auf den
Karten-Zustand allein reduziert (`states[k] = [(None, 0.0)]`), und
`_pin_map_runs`/`_pin_forced_runs` verschieben den Lauf danach STARR,
bis seine Enden die Bord-Punkte treffen — der Bauch des Laufs wird
dabei mit hinausgetragen. In 11 von 15 Ereignissen lag die Karte
selbst auf der Tinte; Median-Überschuss über die Karte **+0,0928 xh**,
maximal +0,2146. Zweischneidig und darum lange unsichtbar: in 12
weiteren Fenstern zieht dieselbe Pinnung um −0,0165 xh ZURÜCK zur
Tinte, sodass die Summe unauffällig bleibt und die v0.9/v0.11-Gates
bestanden wurden. Benannte Konversionen: formtreue statt starrer
Pinnung, und `map_slack_xh` als Nie-schlechter-als-die-Karte-Budget.
*Technisch:* `tools/inkpilot/pilot.py` (`MAP_CROSSING_WINDOW_UNITS`,
`MAP_CROSSING_PIN`, `_pin_map_runs`, `_pin_forced_runs`) →
messjournal.md §14 „Lotse Absprung-Forensik `sep04`",
proposals/tintenfolger.md §7.9

**Plateau-Anker** — der `aug19` adoptierte Pinnungs-Mechanismus der
Lotse-Route (v0.11, L1e): Jeder Karten-Selbstschnitt in einem
Fenster-Lauf erhält einen ANKER (Offset = nächster
Skelett-Verzweigungsknoten − Schnittpunkt, Suchradius 1,0 xh), und
das Offset wirkt als starres PLATEAU von ±0,35 xh statt als
Punkt-Knoten — eine Kreuzung überlebt eine lokal konstante
Verschiebung exakt (beide Pässe verschieben sich gleich, das X
wandert starr auf den Tinten-Knoten), während Punkt-Knoten das
Offset-Feld an genau der Kreuzung scheren, die sie sichern sollen
(das gemessene v0.10-Negativ: Merge/Oskulation in dichten Clustern).
Plateaus, die sich entlang IRGENDEINES beteiligten Passes
überlappen, verschmelzen GLOBAL (Union-Find über die
Anker-Identitäten) zu einem Cluster mit einem gemeinsamen
Mittel-Offset — der dichte Cluster verschiebt sich als Ganzes.
*Technisch:* `tools/inkpilot/pilot.py` (`MAP_RUN_PIN_KNOTS`,
`PIN_KNOT_PLATEAU_UNITS`, `map_crossing_knots`, `_pin_map_runs`) →
messjournal.md §14 „Lotse v0.10/v0.11 `aug19`"

**Marken-endständige Assembly** — die `aug19` als **Kette v2**
adoptierte Formulierungsänderung (K-A): der Ketten-Kandidat emittiert
die Diakritika-Striche eines Wortes (Assembler-Kriterium: alle
Samples über `DIACRITIC_MIN_Y`) NACH allen Körper-Strichen, in der
komponierten Engine-Ordnung, die auch die Hand schreibt — die
v1-Assembly setzte sie je RUN zwischen die Läufe, und das
ordnungstreue forward-DTW zahlte die Sequenz-Inversion als die
gesamte unter/muß-Kollaps-Klasse (unter 0,4503 → 0,0854 bei
byte-identischer Geometrie; Kette-p90 0,236 → 0,099). Eine reine
ORDNUNGS-Änderung der Strichliste; ihre Adoption war die erste
datierte Re-Baseline eines Duell-Kandidaten (alle gepaarten
Vergleiche rechnen seither gegen v2). *Technisch:*
`tools/laufform/harvest.py` (`HarvestOptions.marks_last`,
`chain_word_strokes`), `tools/pairlab/trace.py::
diacritic_stroke_units` → messjournal.md §14 „Kette K-A `aug19`"

**Entdrillung** *(untwist)* — der `aug19` adoptierte
Lotse-Mechanismus (v0.13, `UNTWIST_WINDOW_UNITS` = 0,5) gegen die
GEWEBE-Form der Doppel-X-Duplikate: Die Duplikat-Orte tragen mehrere
Roh-Schnitt-Ereignisse desselben Pass-Paars in kleinem Fenster
(3/5/6 Ereignisse, wo die Hand 1/1/0-mal kreuzt), Entfernen muss
darum PAARWEISE geschehen, damit die Parität die topologisch nötige
Kreuzung stehen lässt (die v0.12-Sehne entfernte alle und das X
mit). Je Ereignis-Paar wird der Wiggle-Bogen (die Seite mit der
größeren Sehnen-Abweichung) an der Sehne der beiden Schnittpunkte
GESPIEGELT — richtungserhaltend, lokal, geloggt. Gemessene Grenzen:
Geometrie allein trennt ein Gewebe nicht von einem echten ENGEN
Doppel (mits t-Paar, 0,07 xh — das 0,8-Fenster tötete es), und die
Paar-Entfernung ist PARITÄT-BLIND — die `aug20`-Autopsie zeigt sie
am Galoppieren-G-Kopf das echte X mitsamt seinem Duplikat fressen
(2 → 0, wo die Hand 1 schreibt); der benannte Diskriminator ist das
Lineal-Soll-Budget (eigener Eintrag). *Technisch:*
`tools/inkpilot/pilot.py::untwist_strokes` → messjournal.md §14
„Lotse v0.13/v0.14 `aug19`", „G-Kopf-Ritt-Autopsie `aug20`"

**Lineal-Soll-Budget** *(ruler-soll budget)* — die `aug20`-Korrektur
der soll-budgetierten Entdrillung (v0.15/v0.16): Ein Entdrillungs-Paar
darf nur fallen, wo die Ereignis-Nachbarschaft danach nicht unter ihr
Karten-Soll rutscht — und das Soll zählt der GEFRORENE
Kreuzungs-Detektor des Lineals selbst (`crossing_points` auf der
xh-skalierten Karte: Durchstoß-Kriterium, Arc-Floor, Merge) statt
roher Segment-Schnitte. Die Autopsie fand die rohe Zählung jeden
Karten-Schnitt ~doppelt listen (will: 10 roh gegen 4 gezählt) — exakt
wills falsches v0.15-Veto; mit Lineal-Zählung löst sich das Veto, das
G-Kopf-Veto feuert korrekt, mits echtes t-Doppel bleibt geschützt.
Gehört zur v0.16-Leiter der selektiven Pinn-Stufen (`bridges` ·
`zones`; bridges ∪ zones = all). Seit v0.17 arbeitet das Veto als
**Reservierungs-Veto**: das Soll wird je Entdrillungs-Pass
eins-zu-eins auf die Ereignisse gematcht, reservierte Ereignisse
sind unpaarbar — jede ZÄHL-Variante (Radius wie Delta) fällt in
dichten Clustern als Commons-Problem (unters 12 Events über
1 Soll: jede Einzelentfernung findet einen Ersatz-Matcher, die
Kaskade räumt die Stelle trotzdem leer). *Technisch:*
`tools/inkpilot/pilot.py::map_self_intersections` (Soll-Quelle),
`::pin_run_mask` (Stufen), `UNTWIST_SOLL_BUDGET` ·
`UNTWIST_SOLL_MATCHING` →
messjournal.md §14 „Lotse v0.16/v0.17 `aug20`"

**Karten-Soll-Vollständigkeit** — die `aug20` gestellte Frage
nach den Kreuzungen, die die Karte GAR NICHT führt (Wächter
können nur schützen, was das Soll kennt) — **noch am selben Tag
GEMESSEN beantwortet: die Karte ist vollständig.** Die
Platzierungskarte auf der ROHEN komponierten Karte matcht
**41 von 41** Hand-X des Dev-Satzes (Ortsfehler median
0,159 xh); die vermeintliche Lücke (unters t-Stamm-Doppel:
Abstieg + 0,07-xh-versetzter Rückpass, der K1b-Befund) war die
0,12-xh-ABTASTUNG von Soll-Quelle und Ritt-Bahn — eine
Auflösungs-Grenze (v0.18), keine Kompositions-Lücke. Was
karten-seitig bleibt, sind Soll-X ohne Hand-Partner (mit-2,
linken: die Karte kreuzt, wo DIESE Hand nicht kreuzt) —
Beleg-Varianz, kein Fehler. *Technisch:* messjournal.md §14
„Karten-Soll-Autopsie"/„t-Stamm-Ritt-Autopsie `aug20`",
tintenfolger.md §7.9

**Doppel-X-Duplikat** — die seit Lotse v0.11 dominante
Rest-Spurious-Klasse des Kreuzungszählers (4 der 6 Zählungen):
Dieselbe Hand-Kreuzung wird vom Kandidaten ZWEIMAL gezeichnet, weil
die gepinnten Fenster-Pässe doppelt durch die Knoten-Nachbarschaft
wackeln — zwei nah beieinanderliegende Kreuzungs-ORTE, von denen
einer matcht und der andere als unecht zählt. Kein
Topologie-Erfindungs-Fehler (das X ist real, nur doppelt); benannter
nächster Mechanismus: EIN X je Knoten-Cluster (Begradigung der
Fenster-Teilbahn je Pass durch den Knoten). *Technisch:*
messjournal.md §14 „Lotse v0.11 `aug19`",
proposals/tintenfolger.md §7.9

**Durchstoß-Kriterium** *(pierce test)* — die v2-Definition der
gezählten Schleifenkreuzung (Owner-Spezifikation aus dem manuellen
Audit): Eine Kreuzung existiert nur, wo eine Linie die andere
DURCHBRICHT — eindeutig auf einer Seite herein, auf der anderen
heraus, beidseitig geprüft. Formal: TLS-Gerade durch das
±0,25-xh-Fenster jedes Passes; die Fensterenden des anderen Passes
müssen auf entgegengesetzten Seiten liegen, beide ≥ 0,05 xh
(≈ halbe Strichbreite) heraus. Ersetzt die 15°-Winkel-Schwelle: eine
Retrace-Ablösung ist keine Kreuzung, wie spitz ihr Winkel auch sei,
und ein flacher Schleifen-Schluss ist eine, wie flach er auch sei
(impliziter Konditionierungs-Boden arcsin(0,05/0,25) ≈ 11,5° — darunter
beantwortet die Tinte die Frage selbst nicht). Seit v2.1 zusätzlich
RETRACE-INTERN verweigert: Ein Ring, dessen beide Chords einander
Antiparallel-Partner des Retrace-Detektors sind, ist der beiläufige
Selbstschnitt eines Hin-und-zurück-mit-Ablösung, keine
Struktur-Kreuzung; für antiparallel-benachbarte Paare liegt der
effektive Boden damit bei der Detektor-Toleranz 25°. Gezählt werden
Kreuzungs-ORTE, nicht -Ereignisse. *Technisch:*
`tools/tracebench/counters.py::_pierces`, Konstanten
`PIERCE_WINDOW_UNITS`/`PIERCE_MARGIN_UNITS`/`CROSS_PARTNER_NEAR_UNITS`
→ messjournal.md §14 (Struktur-Zähler v2 + Nachtrag v2.1)

**Berührung (Struktur-Zähler)** *(touch)* — Vorbeischreiben statt
Retrace: zwei Passagen derselben Bahn laufen nahe und entgegengesetzt
(der Retrace-Detektor flaggt sie), aber zwischen ihnen liegt entlang
des Wegs mehr als 1,0 xh — die Feder kam später wieder vorbei, sie
fuhr nicht zurück. Eigene gezählte und berichtete Klasse neben
Retrace und Überlagerung (Partner im anderen Strich), nie Teil eines
Loss; auf der Duell-Seite gepunktet gezeichnet. Die v1-„erfundenen
Retraces" der Kette waren überwiegend erfundene Berührungen — die
Komposition schreibt Buchstaben zu eng aneinander vorbei.
*Technisch:* `tools/tracebench/counters.py::structure_zones`,
`RETRACE_MAX_PARTNER_GAP_UNITS`
→ messjournal.md §14 (Struktur-Zähler v2)

**Duell-Ansicht** — die Sichtbarmachung des Tintenfolger-Duells: ein
selbst-enthaltenes HTML, das je Wort ALLE Bahn-Kandidaten als
schaltbare Ebenen über dem echten Crop zeigt, die Hand-Nachfahrung
immer als grüne Referenz, plus die Schreib-Animation — ein Play-Knopf
animiert alle sichtbaren Bahnen synchron in Schreibreihenfolge
(`stroke-dashoffset`, konstante Stiftgeschwindigkeit in xh, Absetzen
als echte Lücke). Finale Form UND Entstehung, nebeneinander statt als
Zahlenzeile. *Technisch:* `tools/tracebench/view.py`
→ proposals/tintenfolger.md §4c

**Residualprofil** — die Kurve unter jedem Wort der Duell-Ansicht, die
je Verfahren zeigt, WO die Kopfzahl `dtw_xh` herkommt: x = Bogenlänge
entlang der Hand-Nachfahrung (nur Tinte, Absetzer als gestrichelte
Marker), y = Abstand der Kandidaten-Bahn in x-Höhen. Kein naives
Punkt-n-gegen-Punkt-n bei gleicher Punktzahl (das verschöbe nach der
ersten Extraschleife alles Folgende zum Phantomfehler), sondern der
per-Sample-Abstand ENTLANG der optimalen DTW-Zuordnung, die auch die
Kopfzahl mittelt — deshalb ist der Mittelwert über alle
Zuordnungspaare exakt `dtw_xh`, und das Profil kann der Zahl nie
widersprechen. Flach nahe 0 = sauber, Berge = daneben; Marken bleiben
wie in der Kopfzahl außen vor; die Anzeige-Dezimierung behält je
Fenster das SCHLECHTESTE Sample (ein Ausreißer kann nicht
weggeglättet werden), und Hover setzt eine Sonde an die entsprechende
Wortstelle. *Technisch:* `tools/tracebench/view.py::residual_values`
(über den Warping-Pfad `metric.DtwResult.pairs` — Anzeige-Zugang zur
Zuordnung, zahlenneutral) → reference/messjournal.md §14

**Chronik (tracebench)** — die create-only Rundenhistorie des Duells:
jeder Optimierungs-/Mess-Lauf wird als zeitgestempeltes Verzeichnis
NEBEN dem privaten Archiv-Klon abgelegt (Artefakte + Duell-HTML +
INDEX-Zeile), nach der dbsnapshot-Disziplin — nie löschen, nie
überschreiben, leere Snapshots verweigert, nichts davon im Repo
(Bahndaten sind gelernter Datensatz, Open-Core-Regel). So bleibt der
Fortschritt über die Folger-Runden browsebar; die spätere öffentliche
Methoden-Seite bedient sich HIER, als bewusste
Produkt-Flächen-Entscheidung. *Technisch:*
`tools/tracebench/chronik.py` (`KS_CHRONIK_ROOT` ·
`$KURRENTSCHRIFT_ARCHIVE`-Nachbar) → proposals/tintenfolger.md §4c

**Route G** *(prior-free control)* — der Kontrollkandidat des
Tintenfolger-Duells: gewinnt eine Schreibreihenfolge AUS DER TINTE
ALLEIN — Skelett → Segmentgraph → Greedy-Traversierung per
Gute-Fortsetzung — und macht damit erstmals messbar, was der
Duktus-Prior wirklich kauft (die Differenz zu Kettenfit/Folger auf
denselben 10 Dev-Wörtern). Ausdrücklich KEIN Konkurrent: Schlägt der
Kettenfit ihn nicht klar, ist das ein Befund erster Güte. Er trifft
genau drei Entscheidungen — linkester Endpunkt als Startpunkt, ein
Skalarprodukt am Knoten, Absetzen bei Sackgasse — und lehnt jeden
gelernten Anteil ab (auch den Startpunkt-Prior des Referenz-Codes, der
auf Unterschriften gefittet ist). Der publizierte MATLAB-Code (Diaz et
al. 2022, MIT) läuft hier nicht und ist deshalb die *Spezifikation*, nicht
die Abhängigkeit. *Technisch:* `tools/routeg` (`graph.py` baut,
`recover.py` läuft, `to_candidate.py` rahmt um; Kandidaten-Label
`routeg-graph`, nie `routeg-wor`). *Anzeige-Name auf der Duell-Seite
seit 2026-08-16:* **Nullprobe** (→ Duell-Namen).
→ proposals/tintenfolger.md §4b, messjournal.md §14

**Duell-Namen** *(display names of the tracing duel)* — die lesbaren
Verfahrensnamen der Duell-Seite und der späteren öffentlichen
Methoden-Seite (Owner-Entscheid 2026-08-16), je ↔ technischer Name:
**Hand** (die eigene S-Pen-Nachfahrung, die Referenz) · **Kette** (der
Kettenfit MIT Struktur-Wächter — seit dem Entscheid die EINZIGE Kette:
fit-erfundene Kreuzungen sind nie richtig, join-gebildete stecken im
Soll-Budget; seit Kette v5 `aug26` ist der ganze Wächter-Stack —
Kompositions-Soll, Ratsche, Zone 0,55 — der Default von
`pairlab.follow`, ein Lauf ohne Flags IST die Kette; der Folger OHNE
Wächter heißt **Kette-frei** und ist ein Diagnose-Arm, nie Duell-
Kandidat, weil er Tinte deckt, indem er Struktur zerstört) · **InkSight** (Small-p, derender-Prompt; der text-Prompt
war Diagnose und ist von der Seite genommen) · **Nullprobe** (die
prior-freie Kontrolle, technisch Route G/`tools/routeg` — die Probe
ohne Wirkstoff). Geplant: **Zögling** (eigenes Trajektorien-Modell auf
Engine-Paaren, Route B2) · **Vier Augen** (Fusion beider Routen) ·
**Feinschliff** (Natürlichkeitsfilter als zweite Stufe) · **Chor**
(ordnungs-bewusste Auswahl unter Varianten) · **Lotse** (Arbeitstitel:
Skelett direkt fahren, Duktus als Karte an Abzweigungen). Technische
Namen bleiben in Code und datierten §14-Einträgen unverändert — dieser
Eintrag ist die Übersetzungstabelle. *Technisch:* Label-Marker in
`tools/tracebench/view.py` (`CHAIN_MARKERS`/`CONTROL_MARKERS`)
→ proposals/tintenfolger.md §7.8

**Wächter-Ausgang** *(guard outcome)* — was der Struktur-Wächter mit
EINEM Wort getan hat, aus den Runden-Protokollen des Folgers gelesen
und seit `aug26` eine Spalte des k0-Protokolls: `clean` (jede Runde
im ersten Anlauf angenommen) · `halved` (angenommen nach halbiertem
`max_delta`) · `zonal` (angenommen erst nach der zonalen Neu-Lösung
mit gepinnten Ankern) · `revert-r<n>` (spätere Runde verworfen, das
Wort behält Runde n) · `revert-init` (Runde 1 verworfen — das Wort
behält den Ketten-Init und wurde GAR NICHT gefolgt). Die Stufen der
v5-Autopsie: gegen den rundenatomaren Soll-Wächter waren 26 von 31
bewegten Wörtern `revert-init`, v5 macht daraus `zonal`. Daneben der
**Stack-Sensor**: `k0eval` liest die Wächter-Flags beider Dateien und
warnt bei Abweichung — zweimal in zwei Tagen wurde sonst gegen den
falschen Folger gemessen. *Technisch:*
`tools/tracebench/k0eval.py::guard_outcome`/`guard_stack`
→ messjournal.md §14 „Kette v5"

**Verfahrensseite** — die Register-Seite eines Duell-Verfahrens unter
`docs/reference/` (`verfahren-kette.md` · `verfahren-lotse.md` ·
`verfahren-inksight.md` · `verfahren-nullprobe.md`): Steckbrief
(Anzeige-Name, Code-Heimat, aktuell adoptierte Konstanten) plus
Versions-/Arm-Ledger mit Verdikt und §14-Anker. Die Konvention (eine
Versionsnummer je vorregistriertem Arm; Stand = Menge der adoptierten
Mechanismen; keine rückwirkende Umnummerierung; die Nullprobe bewusst
unversioniert) steht in der Übersicht. Register, keine zweite
Wahrheit: jede Zahl dort ist ein datiertes Zitat, der Beleg wohnt in
messjournal.md §14. *Technisch:*
`docs/reference/verfahren.md` (Übersicht + Konvention),
Nachzieh-Pflicht in docs/dokument-status.md
→ reference/verfahren.md

**Gute-Fortsetzung** *(good continuation)* — die Gestalt-Regel, mit der
ein prior-freies Verfahren an einer Kreuzung entscheidet, welcher Ast
weiterläuft: der, dessen Richtung die einlaufende am besten fortsetzt.
In Route G ein einziges Skalarprodukt über ein 5-Punkt-Fenster; im
Referenzverfahren eine gewichtete Summe `π_ij` aus Außenwinkeln,
Innenwinkeln und Krümmung plus Dijkstra durch den Cluster. Die
Kreuzung ist in JEDER zitierten Arbeit der benannte harte Fall — die
Regel ist das Beste, was ohne Duktus-Wissen zu haben ist, und ihre
Lücke gegenüber dem Prior ist genau das, was Route G beziffert.
*Technisch:* `tools/routeg/recover.py::_walk` (`DIRECTION_WINDOW`)
→ proposals/tintenfolger.md §4b

**grid_step_crop_px** — der Präzisionsboden einer InkSight-Bahn: das
Modell quantisiert seine Ausgabe auf ein 225-Stufen-Gitter über dem auf
Langseite 224 skalierten, weiß gepaddeten Eingabebild, also beträgt ein
Gitterschritt `max(Langseite/224, 1)` Crop-Pixel — bei unseren 154–310 px
breiten Wort-Crops bis ~1,4 px. Die Spalte wird je Wort mitreportet,
damit dieser Anteil des gemessenen Fehlers nie stillschweigend dem
Kandidaten zugerechnet wird. *Technisch:*
`tools/inksight/prepare.py` (`frames.json`) → proposals/tintenfolger.md §4

**Bewertungsdurchgang** *(labelling round)* — eine Runde, in der ein Mensch
gefittete Buchstaben **blind** beurteilt: je Bildschirm ein Ausschnitt der
Vorlage mit der gezeichneten Mittellinie darüber, dazu eine Kategorie der
**Fehler-Taxonomie**, ein **Ortsmarker** und, wenn er mag, ein freier Satz.
Anlass ist die Lücke zwischen Geometrie und Wahrnehmung: `geo_rmse`,
`cov_rmse_local` und `anchor_spike_ratio` messen Abstände, keine davon
misst, ob eine Abweichung *stört*. Der Durchgang beantwortet genau eine
Frage — **welche Fehlerart sieht welche Kennzahl überhaupt?** — und liefert
ausdrücklich keine Schwellwerte, keinen Detektor und keine Note „wie gut
sind die Fits“.
*Technisch:* `tools/humanbench` (`build.py` baut, `page.py` rendert,
`analyse.py` rechnet in der vorregistrierten Reihenfolge)
→ menschliche-bewertung.md

**Gefüllte Ringe** — der Anzeigefehler, den die Vorbereitung der ersten
humanbench-WORT-Runde (`sep02`) zutage förderte, und seither eine Konstruktionsregel
(`menschliche-bewertung.md` §3.6b): die Silhouette eines Federzugs ist
ein Außenring PLUS die Ringe seiner Binnenflächen, und die Urteilsseite
füllte jeden Ring einzeln statt die Gruppe als EINEN Pfad mit
`fill-rule: evenodd`. Folge: jede Schleife läuft zu (das `Z` von „Zorn"
als massiver Tropfen). Tückisch ist nicht die Hässlichkeit, sondern die
RICHTUNG des Schadens — zugefüllt sehen beide Arme genau an den
Merkmalen gleich aus, über die geurteilt werden soll (Schleifenweite,
Binnenraum, Bogenrundung), also antwortet der Beurteiler ehrlich „kein
Unterschied". Ein Anzeigefehler dieser Art rauscht nicht, er **zieht zur
Mitte** und redet jeden Kandidaten klein — vorhergesagt aus dem
Mechanismus; wie groß der Effekt ist, hat noch keine Runde sauber
gemessen (dazu bräuchte es dieselben Bilder unter beiden Fassungen).
Behoben in PR #492. Ob der Fehler außerdem Urteile erreicht hat, ist
offen: der Bestand sagt nein (die Payloads tragen das erst mit #492
eingeführte Format), das Sitzungsprotokoll der LF11-Runde sagt, die
ersten 27 Bildschirme seien noch auf der alten Anzeige gelaufen — eine
vorher geöffnete Browser-Seite erklärt beides und hinterlässt keine
Datei (§14 „Laufform LF11 — humanbench-Wortrunde").
Regel daraus: vor der ersten Runde eine Form mit Binnenfläche
gegenprüfen — und falls eine Anzeige doch mitten in einer Runde repariert
wird, teilt das die Runde: die Grenze liegt im Zeitstempel, die
bereinigte Menge wird nach demselben Auswerteplan gezählt (Wiederholungen
stimmen nie mit) und trägt unter sechs vollständigen Paaren keinen
Adoptionsanspruch; berichtet werden beide Lesarten.
→ menschliche-bewertung.md §3.6b, messjournal.md §14 („Laufform
LF11 — humanbench-Wortrunde")

**Fehler-Taxonomie** — die sechs Kategorien, in denen ein
Bewertungsdurchgang urteilt, plus ein Modifikator. Sie sind die
Schnittstelle zwischen Auge und Zahl — jede spätere Kennzahl wird gegen sie
gebaut —, deshalb steht ihre operative Definition ausführlich in der
Methodendoku und nicht nur als Knopfbeschriftung im Code. `G` und `K`
beantworten die Frage **allein**, die Fehlerarten **addieren sich**, `U`
kombiniert mit allem. Beurteilt wird die Mittellinie gegen die Tinte
**ihres eigenen** Buchstabens; die Strichbreite kommt nicht vor.

- **`G` — gut.** Keine Stelle, die man markieren würde. Zugleich die
  billigste Probe darauf, dass die Regel verstanden wurde: `G` darf in der
  Auswertung **nie** zusammen mit einer Fehlerart auftauchen — wer zögert,
  setzt die Fehlerart plus `U`.
- **`A` — Ausreißer.** *Eine* Stelle springt aus der Kette, die
  unmittelbaren Nachbarn sitzen richtig; der Fehler ist ein **Punkt** (mit
  dem Daumen abgedeckt, ist der Buchstabe in Ordnung). Das menschliche
  Gegenstück zum **Anker im leeren Papier**.
- **`W` — Gewackel.** Die Linie folgt der Tinte im Groben, zittert aber um
  ihren Sollverlauf, oder eine Rundung läuft als Vieleck statt als Bogen.
  Kein einzelner Übeltäter, sondern **Unruhe**. Trägt bis auf Weiteres auch
  die eckig gelaufene kleine Schleife („der Kringel ist eher ein Quadrat als
  ein Kreis“), für die eine eigene Kategorie `R` vorgesehen ist.
- **`B` — Bereich daneben.** Ein **zusammenhängendes Stück** der Kette liegt
  neben seiner Tinte, für sich glatt und plausibel, nur am falschen Ort.
  Gegen `A` die Ausdehnung, gegen `W` die Glätte, gegen `K` der Rest des
  Buchstabens.
- **`E` — Knick am Rand.** Die Beanstandung sitzt **ausschließlich** im
  ersten oder letzten Stück der Ankerkette; definierend ist der **Ort, nicht
  die Form**. Dahinter steckt überwiegend ein **abgeschnittener Anstrich**:
  der Fit beginnt zu spät, das erste Stück Tinte bleibt unbedeckt, der Knick
  ist nur dessen sichtbarer Rest. Eine andere Krankheit als ein Ausreißer
  mittendrin — dort ist Tinte da und der Fit verlässt sie trotzdem.
- **`K` — komplett daneben.** Kein Schweregrad, sondern ein **Ausschluss**:
  der Fit gehört nicht zu diesem Buchstaben, es gibt nichts zu markieren.
  Solche Vorkommen fliegen aus der Bewertung *aller* anderen Kategorien —
  ein Totalausfall wäre sonst überall ein Positiv und höbe jede AUC, ohne
  dass eine Kennzahl irgendetwas Spezifisches gesehen hätte.
- **`U` — unsicher** *(Modifikator)*: Das Urteil steht, der Beurteiler steht
  nicht dafür ein. Gerechnet wird zweimal, mit und ohne — weichen die
  Zahlen auseinander, ist das ein Befund über die Kategorie, nicht über die
  Kennzahl.

*Technisch:* `tools/humanbench/page.py::CATEGORIES`
→ menschliche-bewertung.md §2 · qualitaetsmetrik.md §9

**Vorregistrierung** *(pre-registration)* — der Auswerteplan wird
geschrieben, **bevor** die Zahlen da sind: Reihenfolge der Auswertung,
Ausschlüsse, Mindestbesetzung, die Auflösung, die die Daten überhaupt
tragen, falsifizierbare Erwartungen und was ein Ergebnis auslösen darf.
Ohne ihn passt man die Auswertung hinterher an die Daten an — bei sechs
Kategorien und acht Kennzahlen findet sich immer eine Zelle, die etwas
zeigt, und niemand weiß hinterher, ob sie gesucht oder gefunden war.
Bindend wird der Plan erst durch seinen Zusatz: **Was nicht im Plan steht,
ist eine nachträgliche Idee und wird als solche gekennzeichnet** — mit
Datum und Anlass, als eigener Nachtrag, ohne eine vorregistrierte
Auswertung zu ersetzen. Ein Nachtrag *nach* den Labels ist keine
Vorregistrierung mehr, sondern eine Hypothese für die nächste Runde.
Dieselbe Disziplin wie das **Kill-Kriterium** (§3) und das vorregistrierte
A/B vor jeder rendernden Änderung. → menschliche-bewertung.md §4

**Verlässlichkeitsschranke · blinde Wiederholung** *(test–retest)* — ein
Teil der Bildschirme zeigt ein bereits beurteiltes Vorkommen ein zweites
Mal, ohne es als Wiederholung kenntlich zu machen. Aus der
Selbst-Übereinstimmung folgt die Obergrenze dessen, was eine Kennzahl je
erreichen kann: Wer sich in einer Kategorie nur in 6 von 12 Fällen selbst
bestätigt, für den kommt auch ein *perfekter* Detektor nicht wesentlich
darüber hinaus — und der Satz „unsere Kennzahl ist blind für X“ wäre
**unfalsifizierbar**. Deshalb wird jede AUC mit dieser Schranke berichtet,
und unter einer vorher genannten Übereinstimmung wird für die Kategorie
*keine* Blindheit behauptet. Gemessene Lehre: zufällig gezogene
Wiederholungen messen **seltene** Kategorien nicht — bei 10 % Prävalenz
enthalten 12 Paare je etwa ein Ja, die Übereinstimmung kommt fast ganz aus
Einigkeit über die Neins. Wiederholungen sind nach Kategorie zu schichten.
*Technisch:* `tools/humanbench/build.py::pick_repeats` mit
`REPEAT_MIN_GLYPH_COUNT`/`REPEAT_JITTER`, Auswertung
`analyse.py::reliability` → menschliche-bewertung.md §3.2

**Abdeckungsmatrix** *(coverage matrix)* — die Kopf-Ausgabe eines
Bewertungsdurchgangs: je **Kategorie × Kennzahl** eine AUC gegen „Kategorie
gesetzt / nicht gesetzt“ (AUC = die Wahrscheinlichkeit, dass die Kennzahl
ein zufälliges Vorkommen *mit* der Fehlerart höher bewertet als eines
*ohne*; 0,5 = blind, 1,0 = perfekte Trennung), `K` ausgeschlossen und je
Zeile mit ihrer **Verlässlichkeitsschranke** daneben. Sie wird **grob**
gelesen — „sichtbar überhaupt?“, also deutlich über ~0,7 —, nie fein: bei
10–15 Positiven je Kategorie liegt der Standardfehler bei ≈ 0,09, ein
Unterschied von 0,04 ist auf solchen Daten nicht auflösbar und wird nicht
neu verhandelt.
*Technisch:* `tools/humanbench/analyse.py::coverage_matrix`,
Standardfehler nach Hanley-McNeil → menschliche-bewertung.md §1

**Rückhaltemenge** *(hold-out)* — der Teil der Stichprobe, der bewusst
**ungelabelt** bleibt (`reserve.json`, durch dieselbe Austeilung
bandbalanciert wie der gelabelte Teil). Regel: **entwickeln auf dem
gelabelten Satz, bestätigen auf der Rückhaltemenge.** Eine Kennzahl, die
gebaut wird, um zu sehen, was dieser Durchgang gefunden hat, wäre sonst auf
denselben Labels abgestimmt *und* bestätigt — also gar nicht bestätigt;
ohne den zweiten Durchgang gilt sie als unbestätigt und darf keine
Entscheidung tragen. *Technisch:* `tools/humanbench/build.py`, `--n-label`
→ menschliche-bewertung.md §3.3

**Provenienz-Stempel** *(`provenance.json`)* — was der Builder ungefragt
neben jede Runde schreibt: Runde, Modus, Bauzeit, Quelle, Saat, Bänder,
Zoom, Rand, Wiederholungsregeln, **Code-Commit und -Branch**, die
verwendeten Eingaben und alle Zählungen. Grund: Ein Urteil gilt gegen
**einen** Stand des Fits. Ändert sich der Algorithmus — und genau das ist
der Zweck der Übung —, werden die Urteile nicht wertlos, sondern zum
**Vorher-Zustand**; aber nur, wenn festgehalten ist, worauf sie sich
bezogen haben. Fehlt der Stempel, ist die zweite Runde keine Fortsetzung,
sondern eine neue, unvergleichbare Messung — und die erste damit verloren.
Aus demselben Grund ist das Instrument ein **Werkzeug im Repo** und kein
Skript je Runde. Nicht zu verwechseln mit der **Provenance** einer
gespeicherten Geometrie (§2): Jene sagt, wer eine Zeile gezeichnet hat,
dieser, gegen welchen Stand geurteilt wurde.
*Technisch:* `tools/humanbench/build.py::provenance`
→ menschliche-bewertung.md §7

**paariger Blindvergleich** *(paired comparison)* — der
Vorher/Nachher-Durchgang: dasselbe Vorkommen **zweimal gerechnet**,
nebeneinander auf **einem** Ausschnitt, eine einzige Frage — „welche Linie
folgt der Tinte besser?“ — und drei gleichwertige Antworten: links ·
rechts · **kein Unterschied erkennbar** (das ist ein Ergebnis, keine
Ausrede — der Streit liegt dann unter der Sichtbarkeit). Er tritt an die
Stelle eines zweiten Kategorien-Durchgangs, weil „gut“ kein absoluter
Maßstab ist: Zwischen zwei Sitzungen verschiebt sich die Latte um einen
unbekannten Betrag, und nach Runde eins weiß der Beurteiler, wonach er
sucht. Die Seitenzuordnung steht ausschließlich im Schlüssel, die Seiten
werden je Bildschirm aus der Saat gezogen, Wiederholungen werden
**gespiegelt** gezeigt. Er misst die **Richtung** („ist es besser
geworden?“) auf denselben Vorkommen — nicht die Prävalenz je Fehlerart und
keine Fehlerrate. *Technisch:* `tools/humanbench/build.py::build_paired`
→ menschliche-bewertung.md §8

**Echtheitsfrage** *(authenticity question)* — die zweite der beiden Fragen,
die ein **paariger Blindvergleich** stellen kann: **„welche sieht echter
geschrieben aus?“** statt „welche Linie folgt der Tinte besser?“. Sie löst die
Genauigkeitsfrage ab, sobald beide Linien gleich gut auf der Tinte liegen —
dann misst jene nichts mehr (zwei genaue Linien sind beide genau). Gefragt
wird nach dem Schriftbild, nicht nach der Nähe zur Vorlage; die beiden können
einander sogar zuwiderlaufen, weil eine Linie, die jeden Skelett-Zacken
mitnimmt, genauer ist und weniger geschrieben aussieht. Weil sie etwas anderes
misst, sind ihre Runden mit denen der Genauigkeitsfrage **nicht vergleichbar**
— das Instrument trägt die gestellte Frage deshalb in die Kopfzeile des
Ergebnistextes (`ECHTHEIT/n` gegen `VERGLEICH/n`), damit ein Text auch ohne
seinen Plan zuzuordnen bleibt. *Technisch:*
`tools/humanbench/page.py::QUESTIONS` (`--question ink | authentic`),
Auswertung `analyse.py::analyse_paired`
→ menschliche-bewertung.md §8, §8a

**Wortrunde** *(word round)* — der dritte Modus des Bewertungsdurchgangs und
der einzige, der die drei sichtbarsten Defekte des Geschriebenen überhaupt
zeigt: den **Anker-Median-Zickzack** einer Laufform-Zeile, den **zu dünnen
Strich** und den **Knick an der Naht**. Jedes eingefrorene Lineal ist für sie
blind (das Resampling schluckt den Zickzack, keine Kennzahl trägt die Breite,
der Knick sitzt unter dem Messfenster) und der Kategorien-Durchgang ebenfalls,
weil er einen *Buchstaben* zeigt und eine *Mittellinie* zeichnet. Die
Wortrunde zeigt stattdessen ein ganzes Specimen-Wort mit **zwei Kompositionen
als Tinte** darüber — gefüllte Silhouetten und Verbinder-Kapseln ihrer eigenen
Breite — und stellt die **Echtheitsfrage**. Vorregistriert entschieden wird
sie bei **≥ 60 % Kandidat unter den entschiedenen Bildschirmen und ≤ 25 % „kein
Unterschied“ über alle**, und nur, wenn die gespiegelten Wiederholungen zeigen,
dass nicht nach Position geantwortet wurde. *Technisch:*
`tools/humanbench/build.py --word-arms` (`build_word`), Erzeuger
`tools/humanbench/wordarm.py`, Auswertung `analyse.py::analyse_paired` mit
`ADOPT_CANDIDATE_SHARE`/`ADOPT_MAX_TIE_SHARE`
→ menschliche-bewertung.md §8a

**Arm-Datei** *(arm file)* — die Eingabe einer **Wortrunde**: je Seite eine
JSON-Datei mit einer Komposition je Fixture-Wort — Registrierung plus
`strokes` (Punkte in x-Höhen, y nach oben von der Grundlinie, mit
Strichbreite) und `fills` (Silhouetten) —, also wörtlich das, was
`compose_word` liefert. Der Builder komponiert **nichts** selbst: ein
Instrument, das seinen eigenen Kandidaten rechnete, könnte von dem Lineal
wegdriften, das ihn bestätigen soll. Zwei Größen daraus wandern in den
Schlüssel: der **`arm_gap`** (wie weit die beiden Arme auf diesem Wort
auseinanderlaufen, symmetrisch, in x-Höhen — die Schwere-Achse, an der die
Bänder geschnitten werden) und die **Verdachtsklasse** (`--strata`, die
deklarierte Fehlerklasse eines Wortes, über die die Wiederholungen ausgeteilt
werden). *Technisch:* Vertrag im Kopf von `tools/humanbench/build.py`,
Referenz-Erzeuger `tools/humanbench/wordarm.py`, Prüfsumme je Arm im
Provenienz-Stempel → menschliche-bewertung.md §8a

**Ortsmarker · Ortsprüfung** — der eine Punkt, den der Beurteiler je Bild in
den Ausschnitt klickt (die auffälligste Stelle, nicht alle), und die
Auswertung darüber. Sein Wert liegt darin, dass er **unabhängig von der
eigenen Rechnung** ist: Eine Ortsaussage, die aus dem selbst berechneten
Maximum stammt, ist zirkulär und belegt nichts — daran ist die frühere Zahl
„die Gate-Ablehnungen sitzen an Strichgrenzen“ zerbrochen. Zwei vorab
festgelegte Auswerteregeln: **ein fehlender Marker ist kein Datum** (nicht
markiert heißt „nicht markiert“, nie „dort ist kein Fehler“; die
**Markerquote** wird mitberichtet, denn sinkt sie über die Sequenz, ist das
Ermüdung und keine Aussage über die Bilder), und **Bilder mit mehreren
Kategorien zählen nur in die Gesamtfrage**, weil bei einem Punkt nicht
entscheidbar ist, welcher Fehlerart er gilt.
*Technisch:* `tools/humanbench/analyse.py::place_check`; die Koordinaten
stehen im Panel-Pixelrahmen und werden über den Schlüssel auf Ankerindex
bzw. Strichgrenze zurückgerechnet → menschliche-bewertung.md §3.7

---

## §5 Werkbank und Prozess

**Werkbank** — die Admin-Oberfläche als **eine** Arbeitsfläche statt
fragmentierter Tabs. Seit dem Redesign „aus einem Guss“ (2026-08) ist der
ganze Admin die Werkbank: eine **Vorlagen-Auswahl** und darunter drei
Ansichten — **Buchstaben · Übergänge · Wörter** —, jede nach dem Muster
Übersicht ⇄ Detail, mit dem Subjekt in der URL, sodass jeder Quersprung
ein normaler Link ist. **Jede Ebene nimmt frei eingetippte Ziele an:** eine
Kombination oder ein Wort, das keine Vorlage je geschrieben hat, muss
trotzdem richtig aussehen und bemängelbar sein.
→ optimierungs-werkbank.md

**Stufen-Doktrin** — die bindende Rollenverteilung, wer welche Stufe
liefert. Grundregel: **Manuell hinzufügen nur, wo Ground Truth entsteht,
die das System nicht selbst herleiten kann. Alles Generierte wird
bemängelt.** Also: Tafel-Duktus und das Nachfahren eines misslungenen
Worts sind Menschenarbeit; Laufform, Übergangs-Grammatik und Komposition
sind Algorithmus-Territorium und werden reklamiert, nicht von Hand
gepatcht. Begründung: **„Ein Mangel schärft die Regel für alle Wörter, ein
manueller Eingriff repariert genau eine Stelle.“** → optimierungs-werkbank.md §3

**Abstandsprofil (Werkbank)** — die Kurve unter einer Wort-Karte der
Werkbank (`/admin/woerter`, Detail): je Punkt der gespeicherten
Nachfahrung der NÄCHSTE Abstand zur Engine-Komposition, in x-Höhen,
über der Bogenlänge der Nachfahrung — flach nahe 0 = deckungsgleich,
Berge = daneben; Hover setzt eine Sonde an die Stelle im
Platten-Ausschnitt. Ein **Anzeige-Maß der Werkbank**, bewusst NICHT
das Residualprofil der Duell-Seite (→ §4): Nachfahrung und Komposition
segmentieren ihre Striche verschieden (generierte Verbinder,
aufgeschobene Marken), eine Schreibreihenfolge-Zuordnung (DTW) würde
dort Segmentierung als Fehler melden — deshalb nächster Abstand statt
Zuordnung, und deshalb nie mit `dtw_xh` zu verwechseln. Eine Richtung
(Nachfahrung → Engine): überschüssige Engine-Tinte zeigt die
Overlay-Ansicht, nicht diese Kurve. *Technisch:*
`app/src/sections/admin/words/distanceProfile.ts` +
`DistanceProfileChart.tsx` → proposals/optimierungs-werkbank.md

**Auftragskorb** *(`work_items`)* — statt Screenshots eine Tabelle: Der
Autor markiert in der Werkbank einen Buchstaben, ein Paar oder ein Wort
(⚑) und legt daraus einen Auftrag ab — Ebene, Ziel-Schlüssel, wo gesehen,
freie Notiz. Mehr ist von der Mensch-Seite nicht gefordert; die Ebene heißt
**„wo gesehen“, nicht „wo verursacht“**. Migration `0020`/`0022`.

**Korb-Notiz** *(`work_items.kind = "note"`)* — die vierte, zielfreie Ebene
des Auftragskorbs: eine allgemeine Kleinigkeit ohne Buchstabe, Paar oder
Wort — eine Admin-UI-Falte, ein schiefes Wort in der Oberfläche —, für die
sich ein GitHub-Issue nicht lohnt. Ihr ganzer Inhalt ist der Notiztext (das
einzige Pflichtfeld), angelegt direkt im Korb statt über ⚑, das immer etwas
Bestimmtes markiert. Läuft dasselbe Protokoll, nur ohne Pflicht-`stage`:
das Stufen-Vokabular benennt Stufen des Schreibwegs. →
optimierungs-werkbank.md §5

**Auftragskorb-Protokoll** — der Rest ist Protokoll, und die API
**erzwingt** es (`check_transition`, 422 bei unvollständigem Abschluss):

- **`understanding`** — die Beschwerde in eigenen Worten zurückgespiegelt,
  **bevor** irgendetwas geändert wird. Drei Sätze: was ich als Beschwerde
  verstehe · was ich beim Nachprüfen gesehen habe · welche Stufe ich zuerst
  verdächtige.
- **`reproduced`** — `yes`/`partly`/`no`: ist die Beschwerde überhaupt
  aufgetreten? („Nachprüfen, nicht nacherzählen.“)
- **`stage`** — die *diagnostizierte* Stufe aus einem geschlossenen
  Vokabular: `chart_ductus` · `laufform` · `join_rule` · `composition` ·
  `pair_override` · `word_trace` · `not_reproducible`. Ein geschlossenes
  Vokabular macht aus dem Archiv eine Abfrage statt einer Lesearbeit.
- **`resolution`** — Stufe, Änderung, PR, Messstand. Querverweis-Regel: die
  `resolution` nennt die PR, die PR-Beschreibung nennt `Korb #<id>`.

**Triage-Pflicht · Regel-Fix vor Override** — die Reihenfolge, in der ein
Auftrag geprüft wird: Tafel-Duktus falsch? → Laufform/Fit? → Klassenregel?
→ Platzierung? → **erst zuletzt** ein Paar-Override. Ein Override ohne
vorherige Regel-Prüfung ist ein Doktrin-Verstoß.

**Rückgabe an Autor** *(`returned`)* — der ehrliche Ausgang, wenn die
Triage eine **Ground-Truth-Lücke** ergibt (der Tafel-Duktus ist falsch,
der Fit ist ohne manuelles Nachfahren unmöglich). Statt `done` wird
`returned` gesetzt, und die `resolution` nennt den konkret benötigten
manuellen Schritt. Die Zeile bleibt im Korb sichtbar — **sie wartet auf den
Autor, nicht auf den Algorithmus.**

**Einrichtungs-Wizard** — die einzige Bearbeitungsfläche für den
Tafel-Duktus, in Schritten: **Ausschluss** (Radierer · Tinte-Pinsel ·
„Lücken füllen“ · „Zelle einsetzen“) → **Lineatur** (inkl. Schräglagen-
Linien) → **Weg** (den Duktus als Stiftzüge aufnehmen; jedes Absetzen
beginnt einen neuen Zug, „Anpassen“ erlaubt Warp-Ziehen zum Ausbügeln) →
**Übersicht/Freigabe**.

**Radierer · Tinte · Lücken füllen · Zelle einsetzen** — die vier
Ausschluss-Werkzeuge über einer Chart-Zelle: freihändig Tinte *entfernen* ·
freihändig Tinte *hinzufügen* · kleine Sprenkel automatisch schließen
(farbcodiert in der Maskenvorschau, damit sichtbar ist, was verschluckt
wurde) · Tinte aus einer *anderen* Zelle derselben Tafel einkopieren
(`bboxes.patches` — so entsteht ein ü aus u-Basis + ä-Umlaut, obwohl es
keine eigene ü-Zelle gibt).
*Technisch:* Alle drei Tinten-Eingriffe komponiert
`core/chart.py::crop_with_mask` **vor** der Binarisierung in den
Ausschnitt — sie ändern also, was die Maske überhaupt sieht;
`crop_mask_to_png_bytes` rendert daraus die binarisierte Vorschau
(„Maske zeigen“) mit farbcodierter Auto-Füllung.

**Wort-Editor · Paar-Editor** — die beiden manuellen Ground-Truth-Flächen:
der Wort-Editor lässt ein misslungenes automatisches Nachfahren von Hand
über dem Ausschnitt neu ziehen (→ `authored`, wird von keiner Neu-Ernte
überschrieben); der Paar-Editor zeichnet einen Verbinder für genau ein Paar
und gibt ihn frei (→ `glyph_pairs`, die sparsame Ausnahme).

**Nachfahr-Stand** *(`traceStatusOf`, `shell/model.ts`)* — der dreiwertige
Stand einer Wortprobe im manuellen Nachfahr-Durchgang, hinter dem
Status-Filter der Wörter-Übersicht (Alle · Offen · Nachgefahren ·
Unvollständig): **nachgefahren** = eine gespeicherte `authored`-Bahn
liegt vor (ein automatischer Fit zählt **nicht** — er ist genau das, was
der Durchgang ersetzt) · **unvollständig** = die Probe ist als
angeschnitten markiert, das Nachfahren geht also nie · **offen** = alles
übrige, und damit die Arbeitsliste. „Offen" ist der Filter, den es
gibt, damit „was fehlt noch?" eine Auswahl ist und keine Scrollarbeit.

**Unvollständige Wortprobe** *(`incomplete`, words.json)* — eine
Wortprobe, deren EIGENE Tinte angeschnitten ist: der i-Punkt fehlt, der
letzte Buchstabe läuft aus dem Rechteck. Sie lässt sich nicht von Hand
nachfahren und ist darum weder Arbeit noch Versäumnis — markiert mit
`"incomplete": true` (Grund im `note` daneben) an ihrer Zeile im
committeten Sidecar `data/sources/<id>/words.json`, fällt sie aus der
Arbeitsliste **und** aus dem Nenner des Nachfahr-Zählers heraus und wird
als eigene Zahl ausgewiesen. **Beleg bleibt sie**: der heile Teil ist
weiter messbar. Nicht zu verwechseln mit **Fremdtinte** (§3) — die
stammt aus einer Nachbarzeile und wird per `exclude` weiß gemalt; hier
fehlt Tinte des Wortes selbst. **Die Marke ist das zweite Mittel, nicht
das erste** (Autor, 2026-08-31): schneidet nur das RECHTECK die Tinte
ab, wird das Rechteck repariert (→ Rechteck-Reparatur) — angeschnittene
Wörter bringen nichts, und das eingefrorene Fixture ist ein Grund für
ein angekündigtes Re-Baseline, keiner, den Mangel stehen zu lassen.
`incomplete` bleibt für das, was kein Rechteck einfangen kann: Tinte,
die auf der Platte selbst endet.

**Rechteck-Reparatur** *(`tools/wordbench/repair_boxes.py`)* — das
Nachziehen einer Wortproben-Kante, die die eigene Tinte anschneidet.
Gemessen wird auf der ROHEN binarisierten Platte, weil der
Standardschnitt auf der despeckelten misst und ein dünner i-Strich
unter dieser Schwelle liegt. Was eigene Tinte ist, entscheidet die
**Lineatur der Zeile**: außerhalb ±1,35 xh liegt die Nachbarzeile,
Interpunktion hängt ganz unter der Mittellinie und kommt nie herein,
blasser Durchschlag fällt am Schwärze-Vergleich aus. Über 2 x-Höhen
Wachstum wird gemeldet statt angewandt (Rückfallebene, bewusst locker:
bei einer x-Höhe verweigerte sie `regieren`, dessen letztes `n` wirklich
angeschnitten war). Die `exclude`-Boxen wandern mit — neu eingeschlossene
Fremdtinte bekommt eine, eine die nur noch eigene Tinte verdeckt fällt
weg. Zwei weitere Dinge wandern mit: die CROP-lokalen
Registrierungen gespeicherter Bahnen (`shift_registrations.py`, reiner
Ursprungs-Versatz, kein Nachfahren — die verschobene Zeile bekommt den
Ursprung, auf den sie sich bezieht, als `rect_origin` mitgestempelt, sonst
ist ein Lauf auf der x-Achse nicht wiederholbar) und die Fixture-Roots
(Re-Export + datierter §15-Eintrag).

**H0–H5 · R1–R5 · W1–W6 · M0–M7** — die vier Nummerierungen der
Arbeitspläne, bewusst getrennt gehalten:
**H** = Handmodell-Stufenplan (H0 Bench-Anschluss der Laufformen · H1
Vorkommen + Aggregate · H2 Paar-Statistik · H3 Konstanten → Hand-Parameter
· H4 zweite historische Hand · H5 die eigene Hand; H0–H2 ausgeliefert).
**R** = Schreibsystem-Redesign (R1 Paar-Matrix · R2 Positions-Rückbau ·
R3 geerntete Paar-Overrides · R4 Platzierungsrest · R5 Schräglage; alle
umgesetzt).
**W** = Werkbank (W1 Backend · W2 Seite · W3 Wort-Editor · W4 Protokoll ·
W5 Stufen-Einsicht · W6 Nachfahr-Stand; alle umgesetzt).
**M** = MVP-Roadmap (M0 Toolchain … **M4 Fit-Routine** … M7 abgespeckte
Animation) — daher „M4-Fit“. Nicht zu verwechseln mit den vier
Kettenfit-Kennzahlen M1–M4 (§3).

**Vereinfachungs-Gate** — die Regel aus H3: Ein Parameter darf nur dann aus
dem Code in die Statistik wandern, wenn (a) die Bench sich nicht
verschlechtert **und** (b) netto Code entfällt oder ein Sonderfall
verschwindet. Antwort auf die Sorge „das ganze wird immer besser, aber der
Code auch immer komplexer“: **Vereinfachung ist ein Gate, kein
Nebeneffekt.**

**Verworfen** — Abschnitte mit dieser Überschrift sind **geschlossene**
Entscheidungen mitsamt Begründung. Sie werden beim Überarbeiten eines Docs
nicht geschwächt oder gelöscht; neue Argumente gehen nach
`docs/proposals/`. Der Zweck: dieselbe Sackgasse nicht zweimal laufen.

**Rettungsweg** *(conversion path)* — die beim VERWERFEN einer Maßnahme
benannte Idee, die sie doch noch ins Ziel bringen könnte (Owner-Direktive
2026-08-16). Jeder §14-Ergebnis-Eintrag eines ehrlichen Negativs schließt
mit seinen Rettungswegen (oder explizit „keiner benannt"); die zentrale
stehende Liste ist proposals/tintenfolger.md §7.9. Ein Rettungsweg ist immer ein
NEUER Mechanismus, neue Evidenz (Bestätigungssatz) oder ein neuer Sensor
(z. B. der blinde Menschvergleich als Tie-Breaker) mit frischer
Vorregistrierung — nie derselbe Knopf mit weicheren Gates. Verhältnis zu
„Verworfen": das Verdikt bleibt geschlossen; der Rettungsweg ist die
separat vorregistrierte NÄCHSTE Hypothese, nicht seine Wiedereröffnung.
→ proposals/tintenfolger.md §7.9 · messjournal.md §14

**Status-Vokabular der Docs** — jedes Doc trägt unter der Überschrift einen
Status mit absolutem Datum: **bindend** (entschieden) · **lebend**
(beschreibt den Ist-Stand und trägt eine benannte Nachzieh-Pflicht) ·
**teil-umgesetzt** · **umgesetzt-historisch** · **offen** ·
**Befund-Journal** (datierte Momentaufnahme, wird nie fortgeschrieben, nur
abgelöst) · **statisch** (quellenbelegtes Nachschlagematerial). Ab rund
10 000 Token wird der Kopf zum **Stand-Block**: bis zu 40 datierte Zeilen,
die sagen, was gilt, was offen ist und wo der Rest steht — jeder Satz mit
dem Anker seiner Quelle.
→ docs/dokument-status.md

**Messjournal** *(measurement journal)* — die Datei
[`messjournal.md`](messjournal.md), seit 2026-09-04 die Heimat von §14, dem
Kampagnen-Journal: 81 datierte Abschnitte, je einer pro Mess-Runde, mit
Vorregistrierung, gemessenen Zahlen und Verdikt. Vorher stand die Sektion in
`qualitaetsmetrik.md` und machte dort zwei Drittel der Datei aus, sodass jede
Frage nach einer Metrik-REGEL das ganze Journal mitlud; der Umzug ist Wort für
Wort und lässt Überschriften wie Anker unangetastet, weshalb die Nummer **§14**
als Zitierschlüssel bleibt (rund 350 Zitate im Repo). Einstieg ist das
**Register** im Kopf: eine Zeile je Abschnitt mit Datum, Route, Typ · Verdikt
und Befund — erst der Sprung aus dem Register lädt einen Abschnitt. Ein
abgeschlossener Arm zieht in
[`messjournal-archiv.md`](messjournal-archiv.md) (Verdikt gebucht ·
Rettungswege eingetragen · ≥ 4 Wochen unberührt), behält dabei seinen Anker,
und seine Registerzeile bekommt nur den Dateinamen vor das `#`-Fragment.
*Technisch:* `tools/docs_register` (`JOURNAL`, `ARCHIVE_PAGE`, `METRIC`),
CI-Job „Docs-Register“. → messjournal.md · qualitaetsmetrik.md

**Kurzglossar** *(short glossary)* — die Datei
[`kurzglossar.md`](kurzglossar.md) (seit 2026-09-04): 77 Begriffe zu je ein
bis zwei Sätzen, je mit dem Sprung in den Themenblock dieses Glossars.
Ausgewählt in zwei nachvollziehbaren Schritten: **gezählt** — ein
Eintragstitel wird Kandidat, wenn er mit Wortgrenzen in mindestens zwei von
drei Quellen vorkommt (Code in `core/`, `api/`, `tools/`, `alembic/`,
`app/src/`; die Agenten-Dateien; die letzten 40 gemergten PR-Beschreibungen)
— das ergab 92 Kandidaten —, und daraus **ausgeschlossen** entlang dreier
benannter Klassen: Wortfalle (der Treffer stammt aus gewöhnlicher Prosa),
schon abgedeckt (der Inhalt steht dort unter einem anderen Eintrag) und
Ein-Arm-Etikett (ein Messname, den genau ein §14-Abschnitt benutzt). Die
Klassen mit ihren Titeln stehen im Kopf des Kurzglossars; 77 bleiben. Grund:
dieses Glossar kostet über 56 000 Token und stand damit als Pflichtlektüre
in `CLAUDE.md`; die Kurzfassung ist die Pflichtlektüre, das volle Glossar
bleibt die Nachschlage-Instanz und behält seinen Schnellindex.
→ kurzglossar.md · glossar.md

**Lese-Budget** *(reading budget)* — die Obergrenze dessen, was eine Sitzung
laden muss, **bevor** sie mit der eigentlichen Aufgabe anfängt: die
Pflichtlektüre aus `CLAUDE.md` und jeder dort benannte Lesepfad haben je eine
Zahl, gemessen am 2026-09-04 plus 10 % Luft. Das Gate dazu ist
`uv run python -m tools.docs_budget check` (CI-Job „Docs-Budget“); es liest
die Pflichtliste **aus `CLAUDE.md`**, statt sie abzuschreiben, also hebt ein
neuer Listenpunkt die gemessene Summe und fällt auf. Gezählt wird ohne
Tokenizer, mit einem eigenen deterministischen **Proxy** (Wortstücke, lange
Komposita geteilt, mal einem Kalibrierungsfaktor) — die Budgets stehen in
Proxy-Einheiten, damit Gleiches mit Gleichem verglichen wird; der Abgleich
gegen `tiktoken` `o200k_base` steht im Modul-Docstring. Ein Budget wird
bewusst gehoben, mit Begründung im PR, nie stillschweigend. Dasselbe Gate
prüft Stand-Blöcke, die eine Zeile je Datei in der Karte und jeden Anker.
*Technisch:* `tools/docs_budget` (`BUDGETS`, `PATHS`, `proxy_tokens`).
→ werkzeuge.md § docs_budget · docs/index.md

**Stand-Block** *(standing block)* — der erweiterte Status-Blockquote eines
großen Docs (ab rund 10 000 Token): bis zu 40 datierte Zeilen, die sagen,
**was gilt**, **was offen ist** und **wo der Rest steht** — jeder
zusammenfassende Satz mit dem Anker seines Abschnitts. Er ist das, was eine
KI-Sitzung liest, statt die Datei zu laden; Muster sind
`proposals/tintenfolger.md` und `reference/qualitaetsmetrik.md`. Nicht zu
verwechseln mit dem gewöhnlichen Status-Kopf, den jedes Doc trägt.
→ docs/dokument-status.md · `/write-docs`

**Changelog-Fragment** *(`changelog.d/<slug>.md`)* — der Changelog-Beitrag
einer PR als EIGENE Datei statt als Bullet unter `[Unreleased]` der
geteilten `CHANGELOG.md` (seit 2026-08-30). Format = das der CHANGELOG
selbst (`### Category` über fett betitelten englischen Bullets), damit der
Release-Schnitt (`tools.changelog release`) die Fragmente unverändert unter
die neue Versionsüberschrift faltet — neueste zuerst je Kategorie, nach dem
Commit, der sie anlegte — und sie danach löscht. Grund: die eine geteilte
Stelle war der Ort, an dem jeder Geschwister-Merge die anderen PRs in den
Konflikt schickte (Audit-Serie 2026-08-29/30); der Union-Merge-Treiber
heilte nur den lokalen Rebase, GitHubs eigene Mergebarkeitsprüfung
ignoriert ihn. Der CI-Job „Changelog (fragment)" verlangt je PR ein
Fragment (Ausnahmen: reine `data/`-PRs, Label `skip-changelog`, PRs von
Dependabot) und weist direkt in `[Unreleased]` HINZUGEFÜGTE Bullets ab —
hinzugefügt, nicht bloß verändert: ein Bullet wird über seinen fetten Titel
identifiziert (seit 2026-09-04), also darf der Wortlaut eines dort schon
stehenden Eintrags korrigiert werden, und nur ein NEUER Titel (oder eine
weitere Kopie eines vorhandenen) ist ein hinzugefügtes Bullet. Ebenfalls
abgewiesen: der unausgefüllte Platzhalter `(#NNN)` — die PR-Nummer bleibt
optional, der Platzhalter nicht. *Technisch:*
`tools/changelog/__init__.py` — `parse_entries` (ein Parser für Fragmente
und `[Unreleased]`), `bullet_title`/`_added_bullets` (die Titel-Identität),
`check_placeholder`, `check_pr` (die PR-Regel), `plan_release`/`apply_release`
(der Schnitt); CI-Job `changelog` in `.github/workflows/ci.yml`.
→ werkzeuge.md § Der Changelog-Schnitt · `changelog.d/README.md`

**Fehlerschicht (`apiErrorText`)** — die deutsche Antwort der Werkbank
auf einen fehlgeschlagenen API-Aufruf: aus dem HTTP-Status wird **ein
Satz, der den nächsten Schritt nennt** („Diese Glyphe ist gesperrt — erst
in der Tafel entsperren"), und die englische Rohzeile des Servers bleibt
darunter in einem zugeklappten `<details>` („Technische Meldung") stehen.
Beides zusammen ist der Punkt: Vorher renderten alle achtzehn Admin-Stellen
`String(err)` wörtlich, also stand „Error: 423 Locked: glyph 'longs' is
locked; pass force=true to overwrite" mitten in deutscher Oberfläche und
sagte nichts darüber, was zu tun ist; bloßes Übersetzen hätte die einzige
Diagnose weggeworfen, die es gibt. **Der Satz antwortet, das Detail
beweist.** Der Rückgabewert trägt zusätzlich den `status`, damit
Aufrufer einen Sonderfall (404 = „noch nicht angelegt", kein Fehler) am
Typ erkennen statt die Meldung nach „404" zu durchsuchen.
Der **Name** ist englisch, die **Ausgabe** deutsch — sprachregelung.md §1
verlangt englische Bezeichner, und §3 verwirft deutsche Identifier
ausdrücklich auch für deutsche Fachbegriffe („Begriff gehört in den
Kommentar, nicht in den Bezeichner"). Der Begriff steht also hier im
Glossar, nicht im Code.
*Technisch:* `app/src/sections/admin/shell/apiErrorText.ts` +
`ErrorText.tsx`; die Sätze in `app/src/locales/de/admin.ts` (`admin.errors`).
Liegt bewusst unter `sections/admin/` und nicht bei `lib/api/`: der
Katalog darf das öffentliche Bundle nicht erreichen (`no-restricted-imports`).

**Entwurfsnetz des Wizards** — die Rettungskopie des gezeichneten Wegs.
Der Weg ist der **einzige** Zustand des Einrichten-Wizards, der nicht
live committet wird (Ausschluss, Tinte, Lineatur und Schräglage schreiben
sofort), und zugleich der Schritt, an dem Handarbeit Ground Truth erzeugt
(→ Stufen-Doktrin). Deshalb zwei Schichten: Escape, Backdrop-Klick und
„Schließen" laufen alle über **eine** Rückfrage, die benennt, was
verloren ginge und was nicht; und selbst das bewusste „Verwerfen" legt
die Striche unter `kurrentschrift.wizard.<sourceId>.<glyphKey>` in den
`sessionStorage`, sodass das nächste Öffnen sie zum Wiederherstellen
anbietet statt sie stillschweigend zurückzumalen.
*Technisch:* `useWizard.ts` (`dirty`, `discardAndClose`, `draft`),
`SetupWizard.tsx` (`requestClose`).

**Zwei Stillen (Leerzustands-Regel)** — ein Leerzustand muss die Ursache
nennen, die tatsächlich vorliegt, nicht die nächstbeste. Konkret in der
Werkbank: `no-occurrences` („Noch keine Vorkommen geerntet") gegen
`no-hand` („Keine Hand an den Vorkommen hinterlegt"). Die Hand wird **aus**
den Vorkommen abgeleitet — gibt es keine, kann keine eine Hand nennen,
und der Hand-Satz benennt eine Ursache, die es noch gar nicht geben kann;
genau das stand vor 2026-09 auf jeder Karte einer frisch geseedeten
Vorlage. Dieselbe Regel gilt eine Ebene höher schon für die Aggregate
(„kein Neuaufbau" vs. „unter der Mindest-Vorkommenszahl").
*Technisch:* `StatsStatus` in `LensStats.tsx`, abgeleitet in
`WorkbenchData.tsx::statsContextOf` und `pairMeasurement.ts::aggregateLayerState`.

**Typo-Boden** — die bindende Untergrenze der Schriftgrößen des öffentlichen
Auftritts: Fließtext ≥ 19 px, Caption ≥ 14 px, ohne Ad-hoc-Größen (design-system.md
§9). „Boden" statt „Richtwert", weil er MESSBAR ist: `app/scripts/type-floor.mjs`
fährt alle öffentlichen Routen in einem echten Browser an, liest die *berechnete*
Schriftgröße jedes Elements mit eigenem Text und schlägt unter 14 px fehl. Genau
eine Ausnahme ist sanktioniert, der 13-px-`overline` der Typo-Leiter (§3). Der
Boden wurde am 02.09.2026 an 17 Stellen unterschritten — durchweg
MUI-`size="small"`-Vorgaben und Ad-hoc-`fontSize`-Werte, keine Absicht; deshalb
sitzt die Korrektur im Theme und die Kontrolle im Skript.
→ concepts/design-system.md §9 · `app/scripts/type-floor.mjs`

**Trefferfläche** *(`hitArea`)* — die unsichtbare Vergrößerung eines
Bedienelements auf das 44-px-Touch-Ziel, ohne seine Optik anzufassen: ein
zentriertes `::after` mit `max(100%, 44px)` in beiden Kanten
(`app/src/styles/hitArea.ts`). Sie ist die Antwort auf den Konflikt zwischen
Plattformempfehlung (Apple HIG 44 pt, Material 48 dp) und einem Entwurf, dessen
kleine Marken — das Wiederholen-↻ über der Tinte, das Kurrent-i des `InfoHint`,
das leise „beenden" — absichtlich leise sind: **eine unsichtbare Trefferfläche
statt einer kleineren Wahrheit.** WCAG 2.2 SC 2.5.8 (24 × 24 px) hielt die Seite
schon vorher über die Abstandsausnahme; die 44-px-Regel geht bewusst darüber
hinaus und ist seit dem **Entscheid des Autors vom 03.09.2026 bindend**
(design-system.md §9.3, bis dahin als Vorschlag notiert). Nachgeprüft wird sie
nicht an der berechneten Größe, sondern an der echten Trefferfläche:
`npm run touch-targets` fragt per `elementFromPoint` in 22 px Abstand vom
Mittelpunkt nach — das fängt den stillen Bruch, bei dem ein `overflow: hidden`
das Pseudo-Element beschneidet und das Ziel bei unveränderter Zeichnung
zurückschrumpft.
→ concepts/design-system.md §9.3 · `app/src/styles/hitArea.ts` ·
`app/scripts/touch-targets.mjs`

### Eigenhand-Erfassung

**Eigenhand-Erfassung** — die Werkzeugkette, mit der der Autor seine
eigene Hand als Trainingsdaten erfasst: Wortvorrat → Streifenplan →
Bogen drucken → mit echter Feder schreiben → einlesen → Siebung →
Fassungen in der Streifenkartei → Bestandsbericht → nächster Bogen.
*Technisch:* `tools/eigenhand/`, Datenwurzel `data/samples/own-hand/`
(gitignored, Archiv via `tools/eigenhand/snapshot.py`).
→ proposals/eigenhand-erfassung.md

**Wortvorrat** — der committete, kuratierte, in Wellen wachsende Bestand
ECHTER Wörter der Eigenhand-Erfassung (alt und modern, hauptsächlich
Deutsch, Englisch getaggt); Kurationsschichten per Tag (`mvp9` ·
`bench-abb19` · `quizbank` · `rare-join` · `haeufig` · `english`).
Trainingsdaten, kein Mess-Satz — keine Bench-Kopfzahl liest daraus.
*Technisch:* `tools/eigenhand/corpus.py::pool_entries`.
→ proposals/eigenhand-erfassung.md §4

**Streifen (Eigenhand)** — die stabile Inhaltseinheit der
Eigenhand-Erfassung: eine feste Wortgruppe, die genau eine Bogenzeile
füllt. Einmal vergeben, nie umnummeriert (append-never); Aufnahmen sind
Fassungen. *Technisch:* IDs `S0037`; Wächter
`tools/eigenhand/pool.py::verify_immutable`.
→ proposals/eigenhand-erfassung.md §4

**Streifenplan** — das committete, append-only Verzeichnis
Streifen → Wörter, deterministisch gebaut (Phase A gewichtetes
Set-Cover für die Startdeckung, Phase B defizitgetriebener Ausbau mit
Wiederholungs-Dämpfung `REPEAT_DAMPING`). Seit Format 2 trägt er neben
den Streifen die Tabelle `forms` (Wort → Fugen-Form), damit auch ein
Leser ohne die Kurationsquelle richtig formen kann — der Server tut
genau das. *Technisch:* `core/eigenhand/streifen.json`, Builder
`tools/eigenhand/pool.py`, Leser `core/eigenhand/plan.py`.
→ proposals/eigenhand-erfassung.md §4

**Fassung** — EINE konkrete Aufnahme eines Streifens (eine gesiebte
Bogenzeile). Status `angenommen` · `verworfen` (nur Kartei-Protokoll,
keine Datei) · `zurueckgezogen` (explizit per `redo --retire`; ASCII, wie
alle drei Werte — `core/eigenhand/ids.py::STATUSES`, und die API nimmt
kein zweites Schreibweise-Paar an);
Neuaufnahme ERGÄNZT, sie ersetzt nicht. Nur angenommene Fassungen
zählen als Trainingsmaterial. *Technisch:*
`fassungen/S0037/F02/{streifen.png, meta.json}`; der PNG ist
selbst-zuordenbar (gedruckte Streifen-ID + Wortlabels im Ausschnitt).
→ proposals/eigenhand-erfassung.md §6–§7

**Bogen** — ein gedrucktes A4-Blatt der Eigenhand-Erfassung: dynamische
Zusammenstellung offener Streifen mit Wortkästen samt Lineatur,
Klartext-Labels, Streifen-IDs am Rand und Passmarken; derselbe Streifen
darf mehrfach daraufstehen (Versuche, `--repeat`). Jeder Bogen schreibt
neben sein PDF die `layout.json` — den einzigen Geometrie-Vertrag des
Importers (Registrierung statt Erkennung). *Technisch:* IDs `B0012`;
komponiert in `core/eigenhand/bogen.py::compose_sheet` (Auswahl, Layout,
PDF), abgelegt entweder lokal durch `tools/eigenhand/sheet.py` oder als
Zeile `eigenhand_sheets` durch `POST /eigenhand/sheets`.
→ proposals/eigenhand-erfassung.md §5, §7.1

**Passmarken** — die vier gedruckten schwarzen 8-mm-Eckquadrate eines
Bogens, links oben mit 3-mm-Lochung (Donut) zur Orientierung: darüber
entzerrt der Import Scan wie Handyfoto (Homographie) und erkennt
gedrehte Aufnahmen. *Technisch:* `tools/eigenhand/fiducial.py`
(scikit-image, bewusst ohne OpenCV).
→ proposals/eigenhand-erfassung.md §6

**Schnittband** — das Rechteck, zu dem eine Bogenzeile geschnitten wird:
feste Spalten (x = 12 … 197 mm) plus feste Polster über der Oberlinie und
unter der Klartext-Zeile. Für jede Zeile eines Stils identisch (Sütterlin
185 × 29 mm; Kurrent und Offenbacher 185 × 28 mm, weil `CUT_MIN_HEIGHT_MM`
ihren flacheren Zeilen mehr Polster über und unter der Lineatur gibt),
unabhängig von der Wortzahl — deshalb haben am Ende ALLE Streifen EINER
Schrift dieselbe Höhe und Breite. Die Streifen-ID sitzt im oberen
Polster, also auf dem Streifen (Zuordenbarkeit); die Stiftmarke bleibt
draußen. Der Import schneidet digital am selben Rechteck, damit
Papierstreifen und `streifen.png` dasselbe Objekt sind. *Technisch:*
`core/eigenhand/geometry.py::cut_box`/`cut_size_mm`, je Zeile in
`layout.json` unter `cut_mm`.
→ proposals/eigenhand-erfassung.md §5

**Schnittmarken** — die kurzen Striche in den Blatträndern, die zeigen, wo
geschnitten wird: je Zeile vier auf Höhe der Querschnitte (links und
rechts), dazu die beiden Längsschnitte in den Lücken ZWISCHEN den
Streifen. Nie innerhalb des Schnittbands — gedruckte Tinte auf dem
Streifen wäre Tinte in den Trainingsdaten — und nie am Blattkopf, wo eine
Haarlinie auf dem Scan in eine Passmarke verlaufen und deren Schwerpunkt
verziehen könnte. *Technisch:*
`core/eigenhand/geometry.py::cut_ticks`/`page_cut_ticks`.
→ proposals/eigenhand-erfassung.md §5

**Stiftmarke** — das eine gedruckte Kästchen am rechten Rand JEDER
Bogenzeile (5 mm, ab x = 199 mm, im Kopf einmal mit „ok“ beschriftet —
außerhalb des Schreibfelds, in Reichweite der Hand am Zeilenende). Der
Schreiber hakt direkt nach dem Schreiben ab, ob die Zeile taugt; der
Import liest die Marke aus dem entzerrten Bild und belegt die Siebung
damit vor. Anders als die QC-Flags DARF sie vorbelegen: sie ist ein
Menschenurteil im besten Moment, nicht eine Maschinenvermutung —
überschreibbar bleibt sie trotzdem. Die Regel (Autor, 2026-08-26, löst
das „leer = verworfen" vom 23.08. ab): **Haken oder Kreuz = angenommen;
ohne Haken zählt die Zeile nicht** — sie bleibt unbeurteilt, der
Streifen steht wieder in der Warteschlange; `verworfen` mit Grund ist
eine ausdrückliche Wahl auf der Siebungsseite, keine Vorgabe.
`apply --haken` verbucht die Haken direkt. *Technisch:*
`core/eigenhand/geometry.py::mark_box`,
`tools/eigenhand/ingest.py::read_pen_mark`, je Zeile in `layout.json`
unter `mark_mm`. → proposals/eigenhand-erfassung.md §5–§6

**Siebung** — der Annehmen/Verwerfen-Schritt je Bogenzeile auf einer
selbstständigen Offline-HTML-Seite (humanbench-Muster: data-URIs,
Resume, uid-verschlüsseltes Ergebnis). Regel ist die **Sieb-Disziplin**
(aus mvp-roadmap M2): verworfen wird nur nach Schreibqualität
(verschrieben, verrutscht) — nie wegen Verbindungsenge; Ausfälle müssen
zufällig sein, nicht selektiv; best-of über Mehrfach-Versuche desselben
Streifens ist erlaubt. *Technisch:* `tools/eigenhand/page.py` →
`apply.py`.
→ proposals/eigenhand-erfassung.md §6

**Streifenkartei** *(kurz: Kartei)* — das lokale Manifest einer Hand und
ihre EINZIGE Zustandsquelle: Bögen, Fassungen, Schreibsitzungen
(Datum · Feder · Tinte · Papier · Gerät), Redo-Liste. Streifen-Zustände
(`geplant` · `unterwegs` · `belegt`) werden ABGELEITET, nie gespeichert;
`unterwegs` ist reine Anzeige — die Druck-Warteschlange beginnt immer
vorn im Plan minus `belegt` (Autor-Entscheid 2026-08-26, proposals
§7), ein Stapel setzt sie seitenweise fort und wird EIN PDF.
Nie committet, nie von Hand editiert. *Technisch:*
`data/samples/own-hand/<hand>/kartei.json`,
`tools/eigenhand/kartei.py::strip_state`.
→ proposals/eigenhand-erfassung.md §7

**Übergangsraum** — die Soll-Grundgesamtheit der Eigenhand-Erfassung:
alle GEFORMTEN glyph_key-Übergänge und Glyph-Positionen, die in echtem
Wortschatz vorkommen, korpusfrequenz-gewichtet; berechnet aus
Konsultationskorpora (Klasse 2). Die Gewichtstabelle wird nie
committet (Frequenzlisten-Doktrin, quiz-wortbank.md §4); seit dem
Autor-Entscheid 2026-08-25 liegt sie neben der lokalen Kopie als EINE
Zeile in der privaten, geteilten DB (`eigenhand_uebergangsraum`,
Migration `0026`, Push `tools.eigenhand.universe --push`) — als
vollständiges Soll-Universum (Korpus-Items ∪ Pool-Items zu 0) samt
Provenienz, damit Werkbank und Terminal dieselben Quoten und dieselbe
gewichtete Druck-Warteschlange rechnen. Item-Notation `l>e`
(Übergang) und `e@medial` (Glyph-Position). Bewusst nicht „Abdeckung“
genannt — der Begriff gehört der Humanbench-Abdeckungsmatrix (§4).
*Technisch:* `tools/eigenhand/universe.py`,
`core/eigenhand/coverage.py` (`soll_from_weights` = die eine
Ziel-Ableitung beider Seiten), `GET|PUT /eigenhand/uebergangsraum`.
→ proposals/eigenhand-erfassung.md §4, §7.1

**Mindestbelegung (Eigenhand)** — die harte Untergrenze des
Streifenplans: JEDE Glyphe — Buchstabe, Ligatur, Ziffer, Zeichen — wird
mindestens dreimal eingeplant, unabhängig von ihrer Textfrequenz
(Owner-Regel 2026-08-23: „sowas wie q nur 1× darf nicht sein“). Eine
Garantie, keine Präferenz: Phase A2 des Builders hebt jede unterbelegte
Glyphe auf, bevor der frequenzgetriebene Ausbau beginnt, und meldet
namentlich, wenn die Wellenkapazität nicht reicht. Nicht zu verwechseln
mit dem gewichteten Aufbauziel (→ Bestandsbericht), das je nach Frequenz
zwischen 3 und 20 liegt. *Technisch:*
`tools/eigenhand/pool.py::GLYPH_MIN_PLANNED`, Prüfzeile am Ende jedes
`tools.eigenhand.progression`-Laufs.
→ proposals/eigenhand-erfassung.md §4

**Beleg (Eigenhand)** — ein Vorkommen eines Übergangsraum-Items in den
angenommenen Fassungen einer Hand; die Zähleinheit des
Bestandsberichts. → proposals/eigenhand-erfassung.md §7

**Bestandsbericht** — der Soll/Ist-Bericht der Eigenhand-Erfassung je
Glyph-Position und Übergang, mit zwei Kopfzahlen: **Erstbeleg-Quote**
(Anteil Items mit ≥1 Beleg) und **Ausbau-Quote** (Σ min(Ist, Soll)/
Σ Soll), beide ungewichtet UND übergangsraum-gewichtet (die gewichtete
Zahl ist die ehrliche Kopfzeile). Dazu der Druckvorschlag — dieselbe
Warteschlange, die `sheet.py --next` druckt: Redo > nie belegt >
Wiederholung nach gewichtetem Soll-Gewinn. Zweistufiges Soll: die
Erstbeleg-Stufe (≥1 Beleg je Item — sie misst die Erstbeleg-Quote und
treibt Phase A des Streifenplans) und das Aufbauziel
`clamp(3 + 17·√(w/wmax), 3, 20)` (`coverage.target_for_weight`,
Untergrenze 3 — es misst die Ausbau-Quote).
*Technisch:* `core/eigenhand/bestand.py` (die Rechnung),
`tools/eigenhand/report.py` (Terminal), `GET /eigenhand/bestand/{hand}`
+ `/admin/eigenhand` (Werkbank — mit Quoten, sobald die Gewichte per
`universe --push` in der DB liegen), `tools/eigenhand/pool.py::soll_model`
über `coverage.soll_from_weights`.
→ proposals/eigenhand-erfassung.md §7

**Eigenhand-Buchführung** — die Hälfte der Streifenkartei, die in der
GETEILTEN Datenbank liegt: welche Bögen gedruckt sind (mit ihrem Layout)
und welche Streifen wie oft angenommen wurden (`eigenhand_sheets` ·
`eigenhand_fassungen`, Migration `0024`, Owner-Entscheidung 2026-08-23).
Die Zahlen brauchen keine Pixel — die Wörter folgen aus Streifen-ID plus
committetem Plan. Seit `0025` liegen die Streifenbilder trotzdem
daneben (`eigenhand_strips`, Owner 2026-08-24), damit die Werkbank einen
geschriebenen Streifen zeigen kann wie einen Tafel-Crop: eigene Tabelle,
PNG-Spalte überall deferred, admin-gesichert, `private, no-store`, nie im
Repository — der Master bleibt das private Archiv. Nahtstelle ist die
Kartei-FORM: lokal `kartei.json`, serverseitig
`EigenhandRepository.kartei` — dahinter rechnet dieselbe Schicht. Seit
`0026` liegt auch das Soll daneben: die Übergangsraum-Gewichte als EINE
hand-unabhängige Zeile (`eigenhand_uebergangsraum`, Autor 2026-08-25,
Push `universe --push`), damit Quoten und gewichtete Warteschlange auf
beiden Seiten dieselben sind.
*Technisch:* `core/database/models.py`, `api/routers/eigenhand.py`,
hoch/runter mit `tools/eigenhand/sync.py` ↔ `pull.py`
(Bilder nur auf `--mit-streifen`).
→ proposals/eigenhand-erfassung.md §7.1, §7.2

**Stehendes Setup** — Feder, Tinte, Papier und Aufnahmegerät einer Hand,
EINMAL erklärt statt bei jedem Import getippt (`eigenhand_hands`,
Migration `0025`). Begründung ist photometrisch, nicht ergonomisch:
diese vier sind Parameter der ganzen Kampagne — wechseln sie mittendrin,
zerfällt das Korpus in Kohorten, die man auf Strichbreite und Schwärzung
nicht mehr vergleichen kann. `ingest` liest sie als Vorgabe aus einem
lokalen Zwischenspeicher; die EFFEKTIVEN Werte stehen zusätzlich an jeder
Fassung (bewusst denormalisiert — ein echter Wechsel soll als Bruch in
den Daten sichtbar sein, nicht rekonstruiert werden müssen). Reihenfolge:
vor der ersten Sitzung erklären, sonst bleiben die Felder der davor
eingelesenen Fassungen leer. *Technisch:* `tools/eigenhand/setup.py`
(CLI, lokaler Cache `setup.json`), `GET|PUT /eigenhand/setups/{hand}`,
Panel „Stehendes Setup“ in `/admin/eigenhand`.
→ proposals/eigenhand-erfassung.md §7.2

**Wort-Ausschnitt (Eigenhand)** — ein einzelnes Wort, aus einem
gespeicherten Streifen HERAUSGERECHNET statt zusätzlich abgelegt: der
Streifen merkt sich seinen Crop-Anfang in Millimetern
(`crop_origin_mm`), das `layout.json` des Bogens sagt, wo die Wortkiste
sitzt, und die Pixelbreite über der Schnittband-Breite gibt den Maßstab.
Senkrecht bleibt der Ausschnitt auf VOLLER Streifenhöhe — Ober- und
Unterlängen sind das Interessante an einem Wort. Dieselbe Überlegung wie
beim Tafel-Crop-Endpunkt, nur in mm statt in Tafelpixeln.
*Technisch:* `core/eigenhand/crop.py`,
`GET /eigenhand/strips/{hand}/{strip}/{fassung}?wort=…`.
→ proposals/eigenhand-erfassung.md §7.2

---

## §6 Extern — Forschung und Vergleichsmaße

Diese Begriffe stammen aus der Literatur, nicht aus dem Repo. Sie stehen
hier, weil sie in Recherche-Notizen und Issue-Diskussionen als
Vergleichsmaßstab auftauchen — und weil unsere Hausmaße (`gen_chamfer`,
`dconn`) eben *Hausmaße* sind.

**DTW** *(Dynamic Time Warping)* — Standardverfahren, um zwei
unterschiedlich lange Sequenzen (z. B. zwei Stiftbahnen) elastisch
aufeinander abzubilden und ihren Abstand zu messen. Klassiker der
Handschrift-Literatur, für Trajektorienvergleich aber schlecht kalibriert.

**LDTW** *(Length-independent DTW)* — längenunabhängige Variante davon,
eingeführt von PEN-Net (ACCV 2022). Präzise (Primärquelle verbatim
geprüft, `aug14`): **unconstrained DTW geteilt durch die Länge T des
gefundenen optimalen Warping-Pfads** (Eq. 1) — kein Band, kein fester
Schrittvorrat, und der Divisor ist datenabhängig (T ≤ M+N), keine
Konstante. Kleiner ist besser. Es existiert KEINE
Referenz-Implementierung (das PEN-Net-Repo enthält nur Trainingscode);
publizierte Werte hängen an [0,64)-Koordinatenboxen und
CASIA-Einzelzeichen und sind mit unseren Wort-Zahlen nicht
vergleichbar. Unsere Headline **`dtw_xh`** (§4) übernimmt genau diese
T-Normalisierung, resampelt aber beide Seiten arc-length-uniform und
misst in xh — deshalb der eigene Name.

**AIoU** *(Adaptive Intersection over Union)* — das zweite Maß aus
derselben Arbeit. Präzise (Primärquelle verbatim geprüft, `aug14`): die
Referenz ist NICHT eine Ground-Truth-Bahn, sondern die
**OTSU-binarisierte Tintenmaske des Bildes**; nur die VORHERSAGE wird
1 px gerastert und per 3×3-Dilatation iterativ verbreitert, bis die IoU
maximal ist — `AIoU = max_k IoU(G, dilate^k(P))`. „Adaptiv" heißt: an
die argmax-Dilatationsstufe, nicht an eine gemessene Breite; genau das
eliminiert den Einfluss der Strichbreite. Größer ist besser;
auflösungsabhängig (Raster immer mitnennen). Publizierte
Größenordnungen: 0,45–0,55 (PEN-Net, isolierte CASIA-Zeichen), ~0,75
(Diffusions-Rekonstruktion 2026, ebenfalls Zeichen-Ebene) — beide NIE
als Zielwerte für verbundene Wörter importieren. Der tracebench (§4)
implementiert die Spalte papertreu gegen die eingefrorene `ref_mask.png`
— was sie nebenbei auf alle Wörter ohne Nachfahrung ausdehnt; eine
Wordbench-Variante (komponierte Maske statt Bahn) bleibt ein eigenes,
anderes Maß.

**HTG** *(Handwritten Text Generation)* — der Literatur-Sammelbegriff für
Modelle, die Handschrift als **Bild** synthetisieren (Offline-Synthese):
GANs wie ScrabbleGAN, Transformer wie HWT/VATr, Diffusionsmodelle wie
DiffusionPen und One-DM. Gegenstück zur Online-Synthese nach Graves, die
Stiftbahnen statt Pixel erzeugt. Für uns relevant als möglicher
Parallelweg (Kurrent-Bilder generieren, dann die Bahn zurückgewinnen) —
Stand der Technik, Datenlage und Prüfsteine in
[`bildsynthese-und-stiftbahn.md`](../research/bildsynthese-und-stiftbahn.md).

**HWD** *(Handwriting Distance)* — perzeptuelle Distanz im Merkmalsraum
eines eigens auf Handschrift-*Stil* trainierten Netzes (BMVC 2023).
Eingeführt, weil **FID** (*Fréchet Inception Distance*, das übliche Maß
für generierte Bilder) für Handschrift schlecht taugt: falsches Backbone,
quadratischer Bildausschnitt, Stichprobengrößen-Bias.

**Sigma-Lognormal / Kinematic Theory** — Réjean Plamondons Modell, das
einen Handschriftzug als Überlagerung lognormaler
Geschwindigkeitsprofile beschreibt — also eine *physiologisch plausible*
Kurvenfamilie. Interessant für uns, weil es **keine Online-Trainingsdaten
braucht** und direkt auf die erzeugten Verbinder zielt: Es sagt nicht nur,
wie schnell, sondern auch **welche Kurvenform** ein Mensch zwischen zwei
Punkten zieht. Daniel Berios Kalligrafie-Synthese ist die ausgebaute
Variante davon.

**Zwei-Drittel-Gesetz** — die schwache, bereits benutzte Version davon:
die Schreibgeschwindigkeit sinkt mit der Krümmung (`v ∝ κ^(−1/3)`), dazu
**Isochronie** — die Dauer eines Zuges wächst deutlich langsamer als seine
Länge (im Repo `Dauer ∝ Länge^0,6`), ein langer Zug wird also einfach
schneller geschrieben. Steckt in
`app/src/lib/strokeTiming.ts` und macht die Schreib-Animation glaubwürdig.
→ animation-rendering.md §1

**G1- / G2-Stetigkeit** — geometrische Stetigkeitsgrade an einer Nahtstelle
zweier Kurven: **G0** = gleicher Punkt, **G1** = zusätzlich gleiche
Tangentenrichtung, **G2** = zusätzlich gleiche Krümmung. Unser
Übergangs-Generator trifft Punkt und Tangente, also **G1**; nichts erzwingt
Krümmungsstetigkeit über die Fuge. Saubere Schreibschrift lebt aber genau
davon — ohne ein Krümmungskriterium bleibt jede Fuge lokal richtig und
global sichtbar. Als benannte offene Naht notiert.

**Trajektorien-Recovery** *(handwriting trajectory recovery)* — das
Forschungsfeld „aus einem Bild die Stiftbahn zurückgewinnen“, in dem der
Kettenfit fachlich zu Hause ist. Verwandt und ausdrücklich **nicht**
gewählt: blindes Skelett-Tracing (löst das Kreuzungsproblem nicht) und
neuronale Bildsynthese (liefert Raster, keine Bahn — also keinen Duktus,
keine Strichfolge, keine Animation, keine Belegbarkeit).

**MDN** *(Mixture Density Network)* — Ausgabeschicht, die statt eines
Punktes eine Mischverteilung vorhersagt (mehrere Gauß-Komponenten samt
Gewichten). Graves 2013 setzt sie auf ein LSTM, um je Zeitschritt die
Verteilung des nächsten Stift-Offsets zu modellieren — die Grundlage der
generativen Handschrift-Synthese. *Technisch:* Parameter μ/σ/ρ/π plus
Stift-ab-Wahrscheinlichkeit; Kontext in
[`graves-handschrift-synthese.md`](../research/graves-handschrift-synthese.md)
und [`kurrent-writer-and-recognizer.md`](../research/kurrent-writer-and-recognizer.md) §1.

**Priming / Biasing** — die zwei Steuerhebel des Graves-Writers:
*Priming* konditioniert den LSTM-Zustand mit echten Trajektorien eines
Zielautors, bevor der neue Text generiert wird (Stil-Imitation);
*Biasing* skaliert zur Laufzeit die Varianz der MDN-Verteilung
(Lesbarkeit ↔ Natürlichkeit). *Technisch:* Mechanik, Grenzen (Style
Collapse, OOV-Alignment) und moderne Nachfolger in
[`graves-handschrift-synthese.md`](../research/graves-handschrift-synthese.md).

**HTR · CER** — *Handwritten Text Recognition* und *Character Error Rate*
(Anteil falscher Zeichen). Der geplante Lesepfad: Transkribus als
Default (CER 5–7 %), das self-hosted Modell `dh-unibe/trocr-kurrent` als
Fallback (CER 2,65 %). → htr-integration.md

**L-BFGS-B** — der benutzte Optimierer: ein quasi-Newton-Verfahren mit
begrenztem Speicher und **Box-Schranken** (daher das B — genau die
Schranken, die die Platzierungsblöcke des Fits brauchen). Steht hier, weil
Abbruchmeldungen dieses Optimierers (`STOP: TOTAL NO. OF ITERATIONS
REACHED LIMIT`) in Befundtexten wörtlich zitiert werden.

---

## §7 Öffentliche Seiten — die Produktnamen

Die Namen, unter denen Besucher die Werkzeuge kennen. Sie stehen hier, weil
sie im Repo bislang nur *benutzt* wurden: „Schreibtafel“, „Lesetafel“ und
„Grundtafel“ meinen drei verschiedene Dinge, und „Tafel · Chart“ (§2) ist
noch einmal ein viertes — die Lehrbuch-Tafel als Datenquelle, nicht die
Seite. Ein Blick hierher spart das Auseinandersortieren (Website-Audit
2026-09-02). Die Texte selbst liegen in `app/src/locales/de/`, eine Datei je
Namensraum; die Seiten sind die Routen aus `app/src/routes/paths.ts`.

**Schriftkunde** *(`/schriftkunde`)* — die belegte Übersichtsseite über
Kurrent, Sütterlin und Offenbacher: Grundbegriffe, die drei
Ausgangsschriften mit ihren Kennwerten, Federn, Tinte und Papier,
Buchstaben-Besonderheiten, Chronologie, Quellen. Jede Angabe stützt sich
auf `docs/schriftkunde/*.md` — das Faktenblatt ist die einzige Quelle für
historische Aussagen auf der Website, nicht das Gedächtnis des Schreibenden.
`locales/de/schriftkunde.ts`, Abschnitts-Anker in
`sections/schriftkunde/sections.ts`.

**Lese-Quiz** *(`/quiz`)* — das Abfragespiel: eine geschriebene Form
(einzelner Buchstabe oder ganzes Wort), vier Antworten, nach einem Fehlgriff
beide Formen nebeneinander. Erklärt wird ein Fehlgriff nur bei den
dokumentierten Verwechslerpaaren (→ Lesefalle §1, `sections/quiz/
lesefallen.ts`) — „no explanation is better than an invented one“. Welche
Auswahlzeilen die Seite überhaupt zeigt, entscheidet `offersChoice`
(`sections/quiz/quizOptions.ts`): eine Zeile mit nur einer verfügbaren
Option ist eine Tatsache, keine Wahl, und erscheint darum weder in der SPA
noch auf der vorgerenderten Crawler-Seite.

**Schreibtafel** *(`/tafel`)* — die Alphabet-Seite: die drei Grundtafeln
nebeneinander zum Vergleichen und Nachschlagen; die Sütterlin schreibt sich
dort Zug um Zug selbst, jeder Buchstabe mit seiner Strichfolge.
`sections/tafel/TafelView.tsx`.

**Grundtafel** — die gemeinfreie Original-Lehrtafel *einer Quelle*
(Loth 1866, Sütterlin 1922, Koch 1928), so wie sie gedruckt wurde — das
Bild, nicht die Nachschrift. Drei davon zeigt die Schreibtafel.
`sections/tafel/useGrundtafeln.ts`; die Quelle dahinter ist die Vorlage
(§2).

**Lesetafel** — das A4-PDF der Schreibtafel: dieselben Formen zum
Ausdrucken und Danebenlegen beim Entziffern. `lib/lesetafel.ts`.

**Lesart prüfen** *(`/lesen/vergleichen`)* — die Hilfe für das eine Wort,
das sich nicht entziffern lässt: Man tippt seine Vermutung ein, die Feder
schreibt sie, daneben stehen die Wörter, die sich von ihr nur in
Verwechslerpaaren unterscheiden (→ Lesart §1, `GET /lesarten`).

**Federprobe** *(`/federprobe`)* — die Schreibfläche für beliebigen Text:
eingetippt, live in Sütterlin geschrieben, mit den generierten Übergängen.
Die öffentliche Kostprobe der Komposition (§2). `sections/scribe/`.

**Übungsblatt** *(`/schreiben/uebungsblatt`)* — das erzeugte PDF mit der
Lineatur der gewählten Ausgangsschrift, wahlweise mit Schräglinien,
Federwinkelmarke und dem eigenen Text als Vorschrift (§1) in den Zeilen.
`sections/worksheet/`.

**Unantastbare Lineatur** — die Doktrin des Übungsblatts für eine
Vorschrift-Zeile, die breiter gerät als die Zeile fasst (Autor-Entscheid
2026-09-02): Sie wird **weder verkleinert noch an einer Wortgrenze
umgebrochen** — beides nähme der Vorschrift genau das, wofür sie da ist,
nämlich exakt zwischen ihren Linien zu stehen. Stattdessen bleibt die Zeile
ungeschrieben, ihr Platz auf dem Blatt bleibt reserviert, sie bekommt ihre
Zeilenmarke, und die Seite sagt es unter dem Textfeld mit Zeilennummer und
Zeichenzahl. Der Gegenentwurf („lieber schief als gar nicht“) ist damit
verworfen. `lib/uebungstext.ts` `placeText`.

**Zeilenmarke** — die rot gestrichelte Bande über dem Mittelband einer Zeile,
die für eine nicht geschriebene Vorschrift-Zeile freigehalten wird, mit deren
Zeilennummer am Seitenrand. Sie erscheint **nur in der Vorschau**: Ein
gedrucktes Übungsblatt trägt keine Warnbänder, es lässt die Zeile einfach
leer. Damit verschwindet nichts still, ohne den Druck zu verunstalten.
`lib/uebungstext.ts` `RowMark` → `sections/worksheet/PreviewSvg.tsx`.

**Zeichenbreiten-Mittel** (`AVG_ADVANCE_UNITS`) — wie breit ein Zeichen im
Mittel läuft, in Template-Einheiten (x-Höhe = 1). Gemessen 2026-09-02 am
Komponisten über `abcdefghijklmnopqrstuvwxyz`: 1,55. Darauf ruht die einzige
Zahl, die das Übungsblatt über die Zeilenlänge verspricht — „bei 6 mm
Mittellänge etwa 18 Zeichen“ statt der früheren pauschalen 60 (das war bloß
die Obergrenze des Eingabefeldes). Es beantwortet „wie viel passt ungefähr“,
nie „diese Zeile passt“: Das Urteil über eine konkrete Zeile fällt an ihrer
eigenen Komposition. `lib/uebungstext.ts` `maxCharsPerLine`.

**„Zug um Zug“** — das Leitmotiv der öffentlichen Texte und zugleich eine
inhaltliche Zusage: Was die Seite zeigt, ist die **Bewegung der Feder** in
ihrer Strichfolge, nicht eine Schriftart mit fertigen Buchstabenbildern.
Wo der Satz steht, muss dahinter eine echte Komposition aus dem Duktus (§1)
stehen — `WrittenGlyph`/`WrittenWord`, nicht der Fallback-Font. In der Prosa
heißt die schreibende Instanz „die Feder“; „Synthese“ bzw.
„Synthese-Engine“ bleibt den Stellen vorbehalten, die das Gezeigte
*kennzeichnen* (Bildunterschriften, Herkunftshinweise).

---

## Querverweise

- [`architektur.md`](../concepts/architektur.md) — §2 Analysis-by-Synthesis,
  §3 Schema, §4 Übergänge, §5 Schwellzug vs. Tinte
- [`allgemein.md`](../schriftkunde/allgemein.md) — die belegten
  paläografischen Grundbegriffe (§1 hier ist deren Kurzfassung)
- [`qualitaetsmetrik.md`](qualitaetsmetrik.md) — alle Metriken im Detail
  samt Baseline-Historie
- [`menschliche-bewertung.md`](menschliche-bewertung.md) — der blinde
  Bewertungsdurchgang: Fehler-Taxonomie, Instrumentregeln, Vorregistrierung
- [`uebergaenge-befund.md`](../proposals/uebergaenge-befund.md) §5/§5c —
  das Übergangs- und Kettenfit-Vokabular in seinem Messkontext
- [`handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md) —
  Laufform, Aggregat, Prüfstein, H0–H5
- [`optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md) —
  Werkbank, Auftragskorb, Stufen-Doktrin
- [`sprachregelung.md`](sprachregelung.md) — warum die Docs deutsch und
  die Bezeichner englisch sind
