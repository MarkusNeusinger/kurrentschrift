# Glossar — Fachbegriffe und Repo-Redewendungen

> **Status (2026-08-12): lebend.** Nachschlagewerk über die Begriffe, die
> in `docs/`, in Issues/PRs und in der Admin-Oberfläche vorkommen.
> Nachzieh-Pflicht: **jedes Doc und jeder PR, der einen neuen Fachbegriff
> oder eine neue Kennzahl prägt, legt im selben Zug einen Eintrag hier an**
> (Regel auch in `CLAUDE.md` § „Working guardrails“, `.github/copilot-instructions.md`
> und den Skills `/write-docs` + `/open-pr`).

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
**§6** Extern/Forschung.

- **A** — Anker · Sample · Schritt §4 · Abdeckungsmatrix §4 · abgeschnittener Anstrich §4 · Absetzen §1 · Aggregat §2 · AIoU §6 · Allograph §1 · Analysis-by-Synthesis §2 · Anker §2 · Anker im leeren Papier §4 · Anstrich/Auslauf §1 · Auftragskorb §5 · Auftragskorb-Protokoll §5 · Ausgangsschrift §1 · Ausreißer §4
- **B** — Bandzugfeder §1 · Bbox §2 · bench_loss §4 · Bereich daneben §4 · Berührung (Struktur-Zähler) §4 · Bestätigung A/B (→ Referenzsatz) §4 · Bewertungsdurchgang §4 · Bézier-Handle-Floor §3 · Biasing §6 · Bibliothekseinheit §2 · bindend §5 · blinde Wiederholung §4 · bogengleich §3 · Bowl-Exit-Tuck §2
- **C** — CER §6 · Chamfer-Distanz §4 · Chart §2 · Chor (geplant) §4 · Chronik (tracebench) §4 · Cusp-Connector §3
- **D** — dconn §4 · Deckung §3 · Doppel-X-Duplikat §4 · Duell-Ansicht §4 · Duell-Namen §4 · degenerierte Solves §3 · Degeneriewächter §3 · d_end (verworfen) §4 · Dice §4 · Dissektion §2 · doff §4 · DTW §6 · dtw_xh §4 · Duktus §1 · Duktus-Prior §1 · Durchstoß-Kriterium §4
- **E** — EDT §3 · Einrichtungs-Wizard §5 · Ernte §2 · extrapoliertes Landmark-Ziel §3
- **F** — Federtypen §1 · Federwinkel §1 · Fehler-Taxonomie §4 · Feinschliff (geplant) §4 · FID §6 · Fixture-Wurzel §4 · Frame-Gate (`frame_stale`) §4 · Frozen-Reference-Regel §4 · Fuge §1
- **G** — G1-/G2-Stetigkeit §6 · gen_chamfer §4 · grid_step_crop_px §4 · Gewackel §4 · Girlande §2 · Gleichzug §1 · Gleichzug-Audit §4 · glyph_key §2 · Gradientenzerlegung §4 · Grundstrich/Haarstrich §1 · gut (`G`) §4 · Gute-Fortsetzung §4
- **H** — H0–H5 §5 · Hand §2 · HTG §6 · HTR §6 · Huber-Kappung §3 · humanbench §4 · HWD §6
- **I** — Ink gap §3 · Instance §2 · Isochronie §6 · Iterationsdeckel §3
- **J** — Junction-Pinch §4 · Junction-Verschiebung §3
- **K** — Kettenfit §3 · Kill-Kriterium §3 · klassenbewusste Korrespondenz §3 · Klassenregel §2 · Knick am Rand §4 · komplett daneben §4 · Komposition §2 · Konnektor §2 · Kopplungshöhe §1 · Kopplungs-Stub §3 · Korb-Notiz §5 · Korrespondenz-Kappe §3 · Kreuzungs-Landmarke §3 · Kringel-Exit §2
- **L** — Labs §4 · Landmarken-Term §3 · Laufform §2 · Lotse (Arbeitstitel) §4 · laufform_dev_xh §4 · L-BFGS-B §6 · LDTW §6 · lebend §5 · like-for-like Gate §3 · Ligatur §1 · Lineatur §1 · loss §4
- **M** — M1–M4 (Kettenfit-Kennzahlen) §3 · M0–M7 (MVP-Meilensteine) §5 · M4-Fit §3 · MAD §4 · Marke §4 · matched arc §3 · MDN §6 · meas §4 · Messboden §4
- **N** — Nachbarbindung §4 · Naht §3 · Naht-Anteil §3 · Natürlichkeitsmetrik §4 · Nullprobe §4
- **O** — Offenbacher §1 · Open-Core-Moat §2 · Ortsmarker §4 · Ortsprüfung §4 · Override §2
- **P** — Paar-Aggregat §2 · Paar-Editor §5 · paariger Blindvergleich §4 · pair_loss §4 · Plateau-Anker §4 · Platzierungsschranke §3 · Priming §6 · Provenance §2 · Provenienz-Stempel §4 · Prüfstein §4
- **Q** — Quelle §2
- **R** — R1–R5 §5 · Radierer §5 · Rastersuchlauf §3 · Re-Baseline §4 · Referenzsatz (nachgefahren) §4 · Registrierung §2 · Regel-Fix vor Override §5 · Render-Kontext §2 · Report-Spalte §4 · reproduced §5 · resolution §5 · Retrace §1 · Retrace-Guard §3 · Retrace-Segment §4 · Rettungsweg §5 · Route G §4 · Rückgabe an Autor §5 · Rückhaltemenge §4
- **S** — Same-Hand-Disziplin §4 · Schräglage §1 · Schwellzug §1 · Score §4 · Segment-Attribution §4 · Sehnen-Schwelle §3 · Sektion §2 · Shaping §2 · Sigma-Lognormal §6 · Skelett §3 · Slant-Spalte §4 · Slot §2 · Specimen §2 · Spike-Verhältnis §4 · Spitzfeder §1 · `stage` (work_items) §5 · Stamm-Rückpass §2 · Status-Vokabular §5 · Stub §3 · Stufen-Doktrin §5 · Style §2 · Sütterlin §1
- **T** — Tafel §2 · tail_adapt/head_adapt §3 · tail_stub_delta §3 · Template §2 · Tikhonov-Regularisierung §3 · Tintenabstand §4 · Tintenfolger §3 · Tintenlücke §3 · Topologie-Wächter §3 · tracebench §4 · Trajektorien-Recovery §6 · Triage-Pflicht §5
- **Ü** — Übergang §2 · Übergangs-Generator §2 · Überlappungsterm §3 · understanding §5
- **V** — Variante §2 · Vereinfachungs-Gate §5 · Verfahrensseite §4 · Vier Augen (geplant) §4 · Vereinigungsfenster §3 · Verlässlichkeitsschranke §4 · Verworfen §5 · Vorkommensschranke §2 · Vorlage §2 · Vorregistrierung §4
- **W** — W1–W5 §5 · Warp §3 · Werkbank §5 · wordbench/glyphbench/pairlab/chainbench §4 · work_items §5 · Wort-Editor §5 · Wort-Trace §2
- **X** — x-Höhe (`xh`) §1
- **Z** — Zelle einsetzen §5 · zirkuläres Kriterium §4 · Zwei-Drittel-Gesetz §6 · Zögling (geplant) §4

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

**Ligatur** — eine auf der Lehrtafel *als eigene Einheit gelehrte*
Buchstabenverbindung. Der geschlossene Satz im Projekt: `ch` · `ck` · `tz`
· `ſt` · `qu` · `ß`. Sie werden als eigene Glyphen mit eigenem Duktus
gespeichert („enumerieren, nicht generieren“) — im Gegensatz zu beliebigen
Buchstabenpaaren, deren Verbindung erzeugt wird. Fehlt der Canonical eines
Clusters, zerfällt der Slot beim Shaping in seine Einzelbuchstaben
(Rückfall, `ch` · `ck` · `tz` · `ſt` · `qu`); `ß` bleibt davon
ausgenommen und ATOMAR — sein ſs/ſz-Zerfall ist selbst eine
Allographen-Frage, und ein naiver Split schriebe mitten im Wort ſſ.
→ architektur.md §4 · write-api.md „Pipeline“

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
(`core/shaping.py::decompose_ligature_slot`, TS-Zwilling
`decomposeLigatureSlot`). Existiert **zweimal** —
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
Override repariert eine Stelle.** Benannte Klassen im Code: Girlande ·
Gabel-Join · Bar-Exit · Kringel-Exit · Kapital-Übergabe · Arkaden-Diagonale.

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
`core/compose.py`; Messung qualitaetsmetrik.md §14 „Welle 2 · P1".

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
`core/compose.py`; Messung qualitaetsmetrik.md §14 „Welle 1 · K1b".

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
Ernte-Artefakte nie committet, der rohe Einzel-Template-Read und die ganze
Statistik-Schicht admin-gegatet. → quellen-und-rechte.md §5

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
`STRUCTURE_GUARD_MAX_RETRIES` → qualitaetsmetrik.md §14 (Arm ⑨)

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
→ qualitaetsmetrik.md §14 (Arm ⑥)

**Korrespondenz-Kappe** — der Befund, der die Arme ⑤/⑥ des
Tintenfolgers überragt: 12 der 21 Landmark-Korrespondenzen der
Dev-Wörter zeigen auf Tinte, die GAR KEINE Kreuzung trägt (5
Touch-Points, 7 T-Junctions) — die BAHN kreuzt sich dort, die Tinte
berührt sich nur. Solange die Korrespondenz diese Klassen nicht kennt,
zieht jeder Landmark-Zug an der Hälfte der Ziele in eine Struktur, die
es nicht gibt; das deckelt jeden möglichen Effekt des Terms, wie stark
er auch gewichtet wird. → die klassenbewusste Korrespondenz.
*Technisch:* qualitaetsmetrik.md §14 (Arme ⑤+⑥, `aug14`)

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
→ qualitaetsmetrik.md §14 (Arm ⑥b)

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
werden **nie** gemittelt. Aktueller Stand: Wörter 0,116886 · Paare
0,164506 (Lauf `aug02`).

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
Linie dieser Spalten: Slant (R5) → Gleichzug (`jul30`) → `meas` (`aug02`).

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
Kriterien sind vorregistriert (qualitaetsmetrik.md §14), ein
Strukturdefekt vetot jeden Distanzgewinn. *Technisch:* die Mess-Module
`tools/tracebench/{metric,frames,counters,sets}.py` (Stufe B); Harness +
Provider folgen als Stufe C → proposals/tintenfolger.md §2

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
der komplett über `DIACRITIC_MIN_Y` (= 1 xh) schwebt und höchstens
0,8 xh Bogenlänge hat — i-Punkt/-Strich, Umlautzeichen, u-Deckstrich.
Der t-Querstrich kreuzt das Mittelband und bleibt Body (ihn zählt der
Kreuzungszähler). Gematcht per Zentroid mit Refusal; **fehlende Marken
sind Co-Primär-Gate**, mit gutem Body-`dtw_xh` nicht rückkaufbar — der
verschluckte i-Punkt ist der dokumentierte Fehlermodus des ganzen
Felds, den keine publizierte Metrik erfasst. *Technisch:*
`tools/tracebench/frames.py::classify_strokes`/`match_marks`

**Retrace-Segment** — zweimal beschriebene Tinte als GEZÄHLTE Zone:
zusammenhängende antiparallele Sample-Paare (Detektor
`core.geometry.detect_retrace_pairs`, prox 0,15 xh, ≥ 3 Samples auf
gemeinsamem 0,02-xh-Raster), wobei Hin- und Rückschenkel EINER
Aus-und-zurück-Bewegung zu einer Zone fusionieren (über die
Partner-Indizes des Detektors — sonst verweigert das Zentroid-Matching
eine Bahn gegen sich selbst, und das authored-Identitäts-Gate schlüge
auf jedem Deckstrich-Wort an). Seit den Struktur-Zählern v2
(qualitaetsmetrik §14 `aug16`) zählt ein Pass nur als Retrace, wenn
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
`MAP_CROSSING_PIN`) → qualitaetsmetrik.md §14 „Lotse v0.7–v0.9",
proposals/tintenfolger.md §7.10

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
qualitaetsmetrik.md §14 „Lotse v0.10/v0.11 `aug19`"

**Doppel-X-Duplikat** — die seit Lotse v0.11 dominante
Rest-Spurious-Klasse des Kreuzungszählers (4 der 6 Zählungen):
Dieselbe Hand-Kreuzung wird vom Kandidaten ZWEIMAL gezeichnet, weil
die gepinnten Fenster-Pässe doppelt durch die Knoten-Nachbarschaft
wackeln — zwei nah beieinanderliegende Kreuzungs-ORTE, von denen
einer matcht und der andere als unecht zählt. Kein
Topologie-Erfindungs-Fehler (das X ist real, nur doppelt); benannter
nächster Mechanismus: EIN X je Knoten-Cluster (Begradigung der
Fenster-Teilbahn je Pass durch den Knoten). *Technisch:*
qualitaetsmetrik.md §14 „Lotse v0.11 `aug19`",
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
→ qualitaetsmetrik.md §14 (Struktur-Zähler v2 + Nachtrag v2.1)

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
→ qualitaetsmetrik.md §14 (Struktur-Zähler v2)

**Duell-Ansicht** — die Sichtbarmachung des Tintenfolger-Duells: ein
selbst-enthaltenes HTML, das je Wort ALLE Bahn-Kandidaten als
schaltbare Ebenen über dem echten Crop zeigt, die Hand-Nachfahrung
immer als grüne Referenz, plus die Schreib-Animation — ein Play-Knopf
animiert alle sichtbaren Bahnen synchron in Schreibreihenfolge
(`stroke-dashoffset`, konstante Stiftgeschwindigkeit in xh, Absetzen
als echte Lücke). Finale Form UND Entstehung, nebeneinander statt als
Zahlenzeile. *Technisch:* `tools/tracebench/view.py`
→ proposals/tintenfolger.md §4c

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
→ proposals/tintenfolger.md §4b, qualitaetsmetrik.md §14

**Duell-Namen** *(display names of the tracing duel)* — die lesbaren
Verfahrensnamen der Duell-Seite und der späteren öffentlichen
Methoden-Seite (Owner-Entscheid 2026-08-16), je ↔ technischer Name:
**Hand** (die eigene S-Pen-Nachfahrung, die Referenz) · **Kette** (der
Kettenfit MIT Struktur-Wächter — seit dem Entscheid die EINZIGE Kette:
fit-erfundene Kreuzungen sind nie richtig, join-gebildete stecken im
Soll-Budget) · **InkSight** (Small-p, derender-Prompt; der text-Prompt
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

**Verfahrensseite** — die Register-Seite eines Duell-Verfahrens unter
`docs/reference/` (`verfahren-kette.md` · `verfahren-lotse.md` ·
`verfahren-inksight.md` · `verfahren-nullprobe.md`): Steckbrief
(Anzeige-Name, Code-Heimat, aktuell adoptierte Konstanten) plus
Versions-/Arm-Ledger mit Verdikt und §14-Anker. Die Konvention (eine
Versionsnummer je vorregistriertem Arm; Stand = Menge der adoptierten
Mechanismen; keine rückwirkende Umnummerierung; die Nullprobe bewusst
unversioniert) steht in der Übersicht. Register, keine zweite
Wahrheit: jede Zahl dort ist ein datiertes Zitat, der Beleg wohnt in
qualitaetsmetrik.md §14. *Technisch:*
`docs/reference/verfahren.md` (Übersicht + Konvention),
Nachzieh-Pflicht in docs/index.md § „Dokument-Status“
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

**H0–H5 · R1–R5 · W1–W5 · M0–M7** — die vier Nummerierungen der
Arbeitspläne, bewusst getrennt gehalten:
**H** = Handmodell-Stufenplan (H0 Bench-Anschluss der Laufformen · H1
Vorkommen + Aggregate · H2 Paar-Statistik · H3 Konstanten → Hand-Parameter
· H4 zweite historische Hand · H5 die eigene Hand; H0–H2 ausgeliefert).
**R** = Schreibsystem-Redesign (R1 Paar-Matrix · R2 Positions-Rückbau ·
R3 geerntete Paar-Overrides · R4 Platzierungsrest · R5 Schräglage; alle
umgesetzt).
**W** = Werkbank (W1 Backend · W2 Seite · W3 Wort-Editor · W4 Protokoll ·
W5 Stufen-Einsicht; alle umgesetzt).
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
→ proposals/tintenfolger.md §7.9 · qualitaetsmetrik.md §14

**Status-Vokabular der Docs** — jedes Doc trägt unter der Überschrift einen
Status mit absolutem Datum: **bindend** (entschieden) · **lebend**
(beschreibt den Ist-Stand und trägt eine benannte Nachzieh-Pflicht) ·
**teil-umgesetzt** · **umgesetzt-historisch** · **offen** ·
**Befund-Journal** (datierte Momentaufnahme, wird nie fortgeschrieben, nur
abgelöst) · **statisch** (quellenbelegtes Nachschlagematerial).
→ docs/index.md § Dokument-Status

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
