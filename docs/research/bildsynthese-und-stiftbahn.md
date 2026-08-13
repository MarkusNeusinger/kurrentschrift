# Bildbasierte Synthese und der Weg zurück zur Stiftbahn

> **Status (2026-08-13): offen.** Recherche-Runde 2026-08-13 zum
> bildbasierten Parallelweg: ein Offline-HTG-Modell (Handschrift-*Bild*-
> Synthese) auf Kurrent/Sütterlin fein-tunen, das generierte Rasterbild per
> Trajektorien-Rückgewinnung in eine Stiftbahn (SVG/Plotter) überführen —
> und dieselbe Rückgewinnungs-Stufe als Aufwertung des heutigen Ansatzes
> prüfen. Nichts davon ist gebaut; §6 trägt die kleinen Prüfsteine T0–T4
> als Bauoption. Die Graves-2013-Mechanik und die Plotter-Pipeline stehen
> im Schwester-Journal
> [`graves-handschrift-synthese.md`](graves-handschrift-synthese.md), das
> Writer→Recognizer-Argument in
> [`kurrent-writer-and-recognizer.md`](kurrent-writer-and-recognizer.md).
> Der Systemkern bleibt die regelbasierte Engine
> ([`../concepts/architektur.md`](../concepts/architektur.md) §2:
> ML-Synthese ist „optionales Spätstadium, nicht der Einstieg") — dieses
> Doc liefert Ideen und Maßstäbe, es ändert keine Entscheidung.

## 1 Die Idee: ein zweiter Weg, parallel zum ersten

Der heutige Weg (nennen wir ihn **Weg A**) ist Analysis-by-Synthesis mit
Duktus-Prior: autorisierte Vorlagen, generierte Übergänge, messbare
Statistik. Er wird langsam besser und ist lesbar — aber er sieht noch
nicht *natürlich* aus. Der hier untersuchte **Weg B** dreht die Pipeline
um und beginnt beim Bild:

1. **Bild-Synthese (Offline-HTG):** ein modernes bildbasiertes
   Generierungsmodell wird auf Kurrent-/Sütterlin-Wortbilder fein-getunt
   und schreibt beliebigen Text als Rasterbild — mit der Natürlichkeit,
   die solche Modelle aus Pixelstatistik lernen.
2. **Rückgewinnung (Offline→Online):** aus dem Rasterbild wird die
   Stiftbahn zurückgewonnen — Strichfolge, Richtung, Absetzen — und als
   Centerline-SVG exportiert, das ein Stift-Plotter physisch schreiben
   kann.
3. **Optional (der Graves-Anschluss):** genügend zurückgewonnene Bahnen
   ergäben erstmals ein Online-Kurrent-Korpus, mit dem sich ein
   Graves-artiges (oder moderneres) Online-Modell trainieren ließe.

Warum Graves 2013 nicht direkt geht, ist in den Schwester-Docs
ausgeführt und wird von dieser Recherche bestätigt und verschärft: Es
existiert **weltweit kein öffentliches Online-Korpus** (Stift-Trajektorien)
für Kurrent oder Sütterlin — IAM-OnDB ist modernes Englisch, IRONOFF
Französisch/Englisch, die CJK-/Indic-Sätze enthalten nichts Deutsches
Historisches. Die einzigen duktus-geordneten Kurrent-Daten, die diese
Recherche überhaupt finden konnte, sind die eigenen: die
S-Pen-Duktus-Vorlagen (`templates.raw_path`) und die nachgefahrenen
Wortproben (`word_instances`). Das ist zugleich die Schwäche des direkten
Graves-Wegs und der Trumpf dieses Repos (§4, §5).

Der Nebeneffekt, der Weg B auch dann interessant macht, wenn die
Synthese-Hälfte scheitert: Die Rückgewinnungs-Stufe ist auf **echte**
Vorlagenscans genauso anwendbar. Funktioniert sie gut genug, entlastet
sie das manuelle Nachfahren (Werkbank W3) — und genau dafür hat das Repo
mit den vorhandenen Nachfahrungen den Maßstab, um „gut genug" zu messen
statt zu glauben.

## 2 Baustein A: Offline-HTG — Stand der Technik (2019–2026)

Drei Modellfamilien, chronologisch: GANs (ScrabbleGAN, GANwriting,
HiGAN+, JokerGAN), Transformer (HWT, VATr/VATr++, autoregressiv Emuru)
und Diffusion (WordStylist, DiffusionPen, One-DM, zeilenweise DiffBrush,
absatzweise Mayr et al.). Einstieg in die Literatur: die kuratierte Liste
`awesome-handwritten-text-generation` und der Survey in *Pattern
Recognition* 2025 (Quellen in §8).

| Modell | Venue/Jahr | Stil-Eingabe | Inhalt-Eingabe | Gewichte offen? |
|---|---|---|---|---|
| ScrabbleGAN | CVPR 2020 | Rauschvektor (kein Ziel-Stil) | Zeichen-„Keys" (Tabelle) | Code MIT, keine Gewichte |
| GANwriting | ECCV 2020 | 15 Referenzwörter | Embedding-Tabelle | Code MIT, keine Gewichte |
| HiGAN+ | ACM TOG 2022 | 1 Referenzbild | Embedding-Tabelle | ja (nur Forschung) |
| HWT | ICCV 2021 | ~15 Referenzwörter | Embedding-Tabelle | ja (MIT) |
| VATr / VATr++ | CVPR 2023 / 2024 | 15 Referenzwörter | **Unifont-Archetypen** (Glyphbilder) | ja |
| WordStylist | ICDAR 2023 | Writer-ID (nur gesehene) | Embedding-Tabelle | Code MIT |
| **DiffusionPen** | ECCV 2024 | 1–5 Referenzbilder, ungesehene Hände | **CANINE** (beliebiges Unicode) | **ja, MIT + HF** |
| **One-DM** | ECCV 2024 | **1** Referenzbild | **Glyphbild** (Unifont-Render) | ja |
| DiffBrush | ICCV 2025 | Referenz-*Zeile* | zeilenweise | ja |
| Emuru | CVPR 2025 | 1 Stil-Zeile + deren Transkription | Text (fontbasiert vortrainiert) | ja (HF) |

Die für Kurrent entscheidenden Befunde:

- **Kurrent ist ein Neue-Schrift-Problem, kein Neuer-Stil-Problem.**
  IAM-vortrainierte Gewichte transferieren Textur, Strichstatistik und
  Backbones — aber jede Buchstabenform-Zuordnung muss neu gelernt werden,
  denn das Kurrent-e, das lange ſ, die Schleifen existieren in IAM nicht.
  Ein Zero-Shot-Versuch mit Stilreferenzen von den 1922-Tafeln wird
  lateinische Formen in Kurrent-Textur liefern (das ist T0 in §6: die
  Lücke dokumentieren, nicht auf ein Wunder hoffen).
- **Der Zeichensatz ist die versteckte Hürde.** Modelle mit
  Embedding-Tabelle (GANwriting, HWT, WordStylist) haben das Alphabet zur
  Trainingszeit eingebacken — ſ, ä/ö/ü/ß nachrüsten heißt Tabellen- und
  Hilfsnetz-Chirurgie. Zwei Auswege existieren: **Glyphbild-Eingabe**
  (VATr/One-DM rendern das Zielzeichen als Bildchen — der Trick für uns:
  statt Unifont-Antiqua ein digitaler Kurrent-Font als Archetyp-Quelle,
  dann arbeitet der Form-Prior *für* statt gegen uns) und
  **zeichenweise Text-Encoder** (DiffusionPen/CANINE: beliebige
  Unicode-Strings, Formen kommen rein aus den Trainingsdaten). ſ und
  rundes s von Anfang an als **verschiedene Inhaltszeichen** kodieren —
  dieselbe Allographen-Trennung, die das Repo ohnehin lebt.
- **Favoriten fürs Fine-Tuning auf 500–5.000 Wortbilder:**
  **DiffusionPen** (MIT-Code + IAM-Gewichte auf Hugging Face, CANINE,
  Few-Shot-Stil, Diffusion trainiert auf kleinen Daten stabiler als
  GANs; Präzedenz: ein unverändertes Retrain auf Ukrainisch/Kyrillisch
  mit 126k Wörtern), dicht gefolgt von **One-DM** (One-Shot-Stil,
  Glyphbild-Eingabe, auf Chinesisch/Japanisch erprobt — also auf fremden
  Glyphinventaren). GAN-Fine-Tuning auf ≤5k Bildern gilt als fragil.
- **Das Emuru-Rezept gegen die Datenknappheit:** Emuru wurde
  ausschließlich auf ~100k **synthetischen Font-Renderings** vortrainiert
  und generalisiert zero-shot auf ungesehene Stile. Übertragen: erst auf
  einem großen synthetischen Kurrent-Korpus vortrainieren, dann auf den
  wenigen echten Crops fein-tunen. Und hier hat das Repo etwas Besseres
  als Fonts: die eigene Engine (§3).
- **Bewertung: HWD + HTR-CER statt FID.** FID ist für Handschrift
  dokumentiert irreführend; der Feldstandard seit 2023/24 ist HWD
  (perzeptuelle Stil-Distanz) plus die CER eines Erkennungsmodells auf
  den generierten Bildern („Rethinking HTG Evaluation", ECCV-W 2024;
  „Quo Vadis HTG for HTR", ICCV-W 2025 — Letzteres vergleicht genau
  unsere Kandidaten VATr++ · DiffusionPen · Emuru für den
  Neue-Sammlung-Fall). HWD und die Trajektorien-Maße DTW/LDTW/AIoU
  stehen im [Glossar §6](../reference/glossar.md).
- **Niemand hat Kurrent-HTG publiziert** (Stand 2026-08). Die nächsten
  Verwandten: das Ukrainisch-Retrain, die
  Historische-Synthese-für-HTR-Linie (OCR-Constrained GANs ICDAR 2021,
  synthetische Zeilen für unterversorgte Bestände) und StylusAI
  (Diffusion für *modernes* Deutsch). Das Feld ist offen — was auch
  heißt: keine fertigen Gewichte, die Kurrent schon können.

## 3 Baustein B: Woher die Trainingsbilder kommen (Daten- und Lizenzlage)

Für das Fine-Tuning braucht Weg B Wortbilder mit Transkription. Die Lage
nach Lizenz-Triage gegen die Repo-Regeln
([`quellen-und-rechte.md`](../reference/quellen-und-rechte.md),
[`datenablage.md`](../reference/datenablage.md)):

- **Brauchbar (CC-BY 4.0, verifiziert):** READ/ICFHR-2016
  *Ratsprotokolle Bozen* (400+ Seiten, 1470–1805), READ
  *Konzilsprotokolle Greifswald* (**8.770 Zeilen**, spätes 18. Jh.),
  Schweizer *Bundesratsprotokolle* (2.426 Zeilen, 1848–1903), dazu
  CC-BY-Teilmengen eines 19.-Jh.-Kurrent-Sets (Zenodo 17252677 — dessen
  bayerische Transkriptions-Teilmenge ist CC-BY-NC-SA und bleibt
  draußen). Alles **Zeilenebene**: Wortbilder entstehen per Forced
  Alignment (kraken und PyLaia liefern Zeichenpositionen frei Haus);
  auf eng verbundener Kurrent mit QC-Pass rechnen.
- **Ausgeschlossen bzw. heikel:** StABS Basel (CC-BY-NC-SA), StAZH-
  Transkriptionen (CC-BY-SA — Copyleft, für uns wie NC-SA zu behandeln;
  die ~100k trainierten Seitenbilder wurden nie publiziert), Bullinger
  (größtes Korpus, ~165k Zeilen, aber ohne saubere Lizenzangabe — vor
  jeder Nutzung anfragen), Dresdner Hofdiarium 1665 (widersprüchliche
  Lizenzfelder). Lebender Aggregator zum Nachprüfen: HTR-United.
- **Die Ära-Lücke:** die permissiven Sätze decken das 16.–19. Jh. Für die
  **Sütterlin-Schulschrift (1911–1941) existiert praktisch kein
  lizenzierter Datensatz** — nur die unveröffentlichten Trainingsdaten
  der Transkribus-Modelle decken sie ab. Für genau die Hand, die die
  öffentliche Seite heute schreibt, müsste Material aus eigenen
  PD-Quellen kommen (die 1922-Tafeln, eigene Fotografien gemeinfreier
  Originale) — dieselbe Beschaffungsstrategie, die das Repo ohnehin
  fährt.
- **Commit-Klasse:** Trainingskorpora sind Klasse 2 der Datenablage —
  `SOURCE.md` + Fetch-/Ableitungs-Skript werden committet, die Bytes
  bleiben gitignored. Auch bei CC-BY ist das der sauberere Weg
  (Attributionspflicht bleibt im `SOURCE.md` dokumentiert). **Die Paper
  selbst werden nur verlinkt, nicht als PDF committet:** die
  arXiv-Standardlizenz erlaubt Dritt-Hosting nicht (nur einzelne Paper
  sind CC-BY), und arXiv-Links sind dauerhaft — die Bibliografie in §8
  folgt daher der Praxis des Graves-Journals.
- **Der eigene Trumpf: die Engine als synthetische Datenquelle.** Die
  Engine rendert heute schon beliebige Wörter als Silhouette **mit
  bekanntem Text und bekannter Stiftbahn**. Das ist exakt das
  Emuru-Rezept, nur besser: statt eines starren Fonts liefert sie
  positionsrichtige Verbindungen, Varianten und (per Degradierung:
  Papier, Rauschen, Strichbreiten-Jitter) beliebig viel
  Vortrainings-Material — und für die Rückgewinnungs-Stufe gleich die
  Ground-Truth-Bahn dazu (§4). Ein auf DB-Inhalten (Vorlagen, Laufformen,
  Wortproben) trainiertes Modell ist allerdings **gelernter Datensatz im
  Sinne der Open-Core-Regel** (quellen-und-rechte.md §5): seine Gewichte
  bleiben wie die Bench-Fixtures außerhalb des Repos.

## 4 Baustein C: Offline→Online — die Rückgewinnung der Stiftbahn

Der Schritt vom generierten Rasterbild zum Plotter-Pfad ist das
klassische Feld der **Trajektorien-Recovery** (Glossar §6). Vorab die
Falle: gewöhnliches Auto-Tracing (potrace, Inkscape-Standard)
vektorisiert die **Umrisslinie** der Tinte — ein Plotter zeichnet damit
Buchstaben-Silhouetten doppelt nach statt zu schreiben. Gebraucht wird
die **Centerline** mit Strichfolge, Richtung und Absetzen;
`autotrace -centerline` liefert zwar Mittellinien, aber als ungeordnete
Polylinien-Suppe mit Sporen und falsch verbundenen Kreuzungsästen, die
erst `vpype` (`linemerge`/`linesort`/`linesimplify`) plottbar macht.

Der Stand der lernenden Verfahren:

- **TRACE** (ICDAR 2021): Zeilenebene, CRNN + soft-DTW gegen IAM-OnDB,
  DTW ≈ 0,024–0,031 (Zeileneinheiten) — gut genug für
  HTR-Datensynthese, lässt aber systematisch i-Punkte, t-Striche und
  Interpunktion aus. **PEN-Net** (ACCV 2022) brachte die heute üblichen
  Maße AIoU/LDTW; 2024–2026 folgen Transformer- und
  **Diffusions-Rekonstruktion** (letztere umarmt, dass die Strichfolge
  aus Pixeln mehrdeutig ist, und *sampelt* Bahnen statt eine zu
  regressieren) — beides bislang auf Zeichenebene (CJK).
- **InkSight** (Google DeepMind + EPFL, TMLR 2025) ist das wichtigste
  Einzelsystem: ein Vision-Language-Modell (ViT + mT5), das Fotos von
  Handschrift zu „digitaler Tinte" **derendert** — geordnete Striche mit
  Absetzen, wortweise. Die **Small-p-Gewichte sind offen (Apache 2.0)**.
  Ehrliche Zahlen aus dem Paper: ~87 % der Ausgaben sind valide
  Nachzeichnungen, aber nur ~67 % menschenähnliche *Bahnen* — auf
  moderner lateinischer Schrift. Kurrent ist out-of-distribution.
  Entscheidend für uns: InkSights eigenes Trainingsrezept ist „echte
  Online-Tinte rendern + degradieren" — **genau die Paare, die unsere
  Engine für Kurrent unbegrenzt erzeugen kann.** Ein
  Kurrent-Fine-Tuning von Small-p ist damit ungewöhnlich gut erreichbar.
- **Geometrisch, ohne Lernen:** Skelett → Segmentgraph →
  Kreuzungs-Cluster per Gute-Fortsetzung auflösen (Diaz et al. 2022,
  Code offen) — der klassische Weg, an dem auch die
  Plotter-Community entlangläuft; **PolyVector Flow** (SIGGRAPH Asia
  2021) ist die stärkste publizierte Antwort auf „welcher Ast läuft
  durch diese Kreuzung weiter", liefert aber ungeordnete Kurven.
- **Die ganze Schleife hat Präzedenz:** Mayr et al. 2020
  („Spatio-Temporal Handwriting Imitation") gehen offline →
  Pseudo-Online → Graves-Priming → Raster und täuschen Menschen im
  Nutzertest. InkSight belegt quantitativ, dass zurückgewonnene Bahnen
  als *Trainingsdaten* taugen (Online-Erkenner rein auf derenderten
  IAM-Bildern: 7,8 % CER). Und der **Cursive Transformer** (2025) zeigt,
  dass schon **~3.500 Wörter** Trajektorien für ein brauchbares
  Online-Generierungsmodell reichen — der Datenbedarf für Schritt 3 aus
  §1 ist also Größenordnung „machbar", nicht „IAM-OnDB nachbauen".

Ehrliche Einschätzung für dichte, verbundene Kurrent: Kreuzungen sind in
jeder zitierten Arbeit *der* benannte harte Fall, und Kurrent ist härter
als alles Getestete — durchgehende Verbindungen, enge Schleifen, starke
Schräglage (fast parallele Kreuzungsäste), Schwellzug-Breiten, die das
Skelett genau an Kreuzungen und Wenden verzerren. Zu erwarten sind die
publizierten Fehlermodi in verstärkter Form: verschluckte Umlaute und
i-Punkte, falsch aufgelöste Schleifenkreuzungen, zu einem Strich
kollabierte Deckstriche. Und grundsätzlich: **jedes gelernte System rät
die Strichfolge** im Prior seiner Trainingsschrift. Eine glatte Bahn kann
historisch falsch sein (Richtung einer e-Schleife), und kein
Literaturmaß bemerkt das — der historisch korrekte Duktus steht in den
Lehrtafeln, nicht in der Tinte. Das ist wörtlich das
Duktus-Prior-Argument, auf dem die Architektur dieses Repos ruht.

Daraus folgt der strukturelle Vorteil von Weg B in *diesem* Repo: Bei
einem generierten Bild ist der Text bekannt, `core/shaping.py` liefert
die erwartete Glyphfolge, und der **Kettenfit** (`tools/pairlab/chain.py`)
ist bereits prior-geführte Trajektorien-Rückgewinnung — er muss die
Strichfolge nicht raten, er kennt sie. Die Rückgewinnung aus §4 hat hier
also zwei konkurrierende Routen: das externe gelernte Modell (InkSight,
ggf. fein-getunt) und der eigene prior-geführte Fit. Welche auf
Kurrent besser ist, ist messbar — denn die nachgefahrenen
`word_instances` sind die einzige existierende Online-Kurrent-Ground-
Truth und damit der natürliche Prüfstand (DTW/LDTW/AIoU gegen die
Nachfahrung, auf denselben Crops).

## 5 Wie Weg B den Weg A aufwertet — auch wenn er „verliert"

- **Automatisches Nachfahren.** Die Rückgewinnungs-Stufe, auf *echte*
  Vorlagenscans angewandt, ist ein Kandidat, das manuelle Nachfahren
  (Werkbank W3) zu entlasten: heute fährt der Admin nach, wo der
  Auto-Fit scheitert — ein auf Engine-Paaren fein-getuntes
  Recovery-Modell könnte diese Lücke verkleinern. Die Engine liefert die
  Trainingspaare, die Nachfahrungen liefern die Validierung; die
  Provenienz-Regel bleibt (`authored` schlägt automatische Ernte).
- **Der Natürlichkeits-Maßstab.** Ein fein-getuntes HTG-Modell ist ein
  unabhängiger Erzeuger „natürlich aussehender" Kurrent. Ein blinder
  Paarvergleich Engine-Wort gegen HTG-Wort mit der vorhandenen
  humanbench-Methodik ([`menschliche-bewertung.md`](../reference/menschliche-bewertung.md))
  beantwortet die Frage, *was genau* am Engine-Bild unnatürlich wirkt —
  kategorisiert, nicht als Bauchgefühl. Selbst ein verlorener Vergleich
  wäre ein Befund, der die Composer-Arbeit priorisiert.
- **Die Plotter-Kontrolle.** Nüchtern festgehalten: Weg A ist heute
  schon plotter-fähig — die Engine erzeugt Centerlines mit Strichfolge
  und Absetzen, der Export nach SVG/vpype ist reine Formatarbeit, ganz
  ohne ML. Weg B muss den Umweg über Pixel erst rechtfertigen; die
  Postkarte aus beiden Wegen nebeneinander (T4) ist der direkte A/B auf
  Papier.

## 6 Kleine Prüfsteine (T0–T4)

Billig → teuer, jede Stufe mit Messgröße und Abbruchkriterium; keine
Stufe setzt den Erfolg der vorigen voraus, aber jede macht die nächste
informierter. Durchgängig gilt der Guardrail „messen statt glauben":
vorregistrierter A/B gegen gemessene Tinte, ein ehrliches negatives
Ergebnis ist ein gültiges Ergebnis.

- **T0 — Nullkosten-Baselines (Stunden, keine eigene GPU nötig).**
  (a) One-DM/DiffusionPen mit publizierten IAM-Gewichten, 1–5
  Stilreferenzen von den 1922-Tafeln, Testwörter aus §9 der Architektur
  (`lesen`, `das`, `denen`): dokumentiert die Neue-Schrift-Lücke mit
  Bildern statt Vermutung. (b) InkSight Small-p auf drei Eingaben —
  echte Wortproben-Crops, Engine-Render, ein modernes Vergleichswort —
  gemessen per DTW/LDTW/AIoU gegen die `word_instances`-Nachfahrung
  desselben Wortes. *Erkenntnis:* wie groß die Lücke wirklich ist, und
  ob InkSight schon auf sauberen Engine-Rendern scheitert (dann ist
  Fine-Tuning Pflicht, nicht Option).
- **T1 — Synthetisches Pretraining aus der eigenen Engine (Tage, 1 GPU
  ≥ 24 GB).** Korpus: einige zehntausend Engine-Wörter (Wortliste aus
  der Quiz-Wortbank), Silhouetten degradiert (Papier, Rauschen, Blur,
  Breiten-Jitter). DiffusionPen von den IAM-Gewichten darauf fein-tunen;
  ſ/s als getrennte Zeichen. Richter: CER von Transkribus „German
  Kurrent" (CER 5,4 % auf echtem Material, als Obergrenze des
  Erwartbaren) plus ein selbst gehosteter Zweitrichter (TrOCR-/
  kraken-Fine-Tune auf den CC-BY-Sets), damit der Generator nicht die
  Eigenheiten *eines* Erkenners lernt; dazu HWD gegen echte Crops.
  *Abbruch:* lernt das Modell nicht einmal die Formen seiner eigenen
  sauberen Trainingsbilder, ist die Familie falsch gewählt.
- **T2 — Fine-Tuning auf echtem Material (Tage bis Wochen).**
  CC-BY-Zeilen (Konzilsprotokolle + Bundesratsprotokolle) per
  kraken-Alignment zu Wort-Crops schneiden, die eigenen 63
  Abb.-19-Wortproben (und, als eigene Auswertungsschiene, die 106
  Abb.-22-Wörter des zweiten Schreibers) dazu; Ära-Vorbehalt explizit
  im Ergebnis führen (18./19.-Jh.-Kurrent ≠ Sütterlin 1922). Messung wie
  T1, zusätzlich der blinde Paarvergleich gegen Engine-Ausgaben nach
  humanbench-Verfahren. *Erkenntnis:* das erste Kurrent-HTG überhaupt —
  und die Antwort, ob es *natürlicher* wirkt als Weg A.
- **T3 — Rückgewinnung im Duell (Tage).** Auf denselben Wörtern —
  generierte aus T1/T2 **und** echte Vorlagen-Crops — zwei Routen:
  (A) der eigene prior-geführte Kettenfit, (B) InkSight (erst roh, dann
  auf Engine-Paaren fein-getunt). Maßstab: die Nachfahrungen
  (`word_instances`), Maße DTW/LDTW/AIoU plus gezielte Fehlerzählung an
  den bekannten harten Stellen (Schleifenkreuzungen, i-Punkte/Umlaute,
  Deckstriche). *Abbruch für Weg B als Ganzes:* wenn keine Route auf
  generierten Bildern plottbare Bahnen ohne handische Reparatur liefert.
- **T4 — Die Postkarte (Stunden).** Ein kurzer Text, zwei Karten:
  einmal Weg B (bestes T2-Bild → beste T3-Bahn → vpype → Plotter),
  einmal Weg A (Engine-Centerlines → SVG → vpype → Plotter, der heute
  schon mögliche Pfad). Nebeneinander fotografieren; das ist der
  A/B-Test, um den es der Postkarten-Idee eigentlich geht.

Reihenfolge-Empfehlung: T0 sofort (kostet fast nichts und erdet alle
Erwartungen), T4/Weg-A-Hälfte ebenfalls früh (sie hängt an keinem
ML-Schritt), T1→T2→T3 danach in dieser Folge.

### Nachtrag 2026-08-13: der vorgezogene Kleinstschritt — ein Tintenfolger

Aus der Diskussion zur Runde, als Richtung festgehalten: Für unseren
Fall ist das Literaturproblem überdimensioniert. Wir müssen keine
fremde, krakelige Handschrift lesen, sondern eine sauber geschriebene
Ausgangsschrift, deren Text **und** Duktus bekannt sind — und
Kreuzungen, der benannte harte Fall des ganzen Feldes (§4), sind bei
uns keine Rätsel, weil der Duktus-Prior sagt, welcher Ast wie
weiterläuft. Statt gleich ein fremdes Gesamtsystem zu übernehmen, werden
die optimalen Stücke für genau diesen einfachen Fall zusammengesetzt,
und der kleinste sinnvolle Schritt ist keiner der ML-Prüfsteine,
sondern ein **Tintenfolger** aus vorhandenen Teilen: der Kettenfit
liefert Topologie, Strichfolge und Kreuzungsauflösung als
Initialisierung; darauf folgt eine Verfeinerungsstufe, die die
Form-Regularisierung Richtung Vorlage löst und die dicht abgetastete
Bahn auf das gemessene Skelett der Wortprobe zieht — Geometrie ganz aus
der Tinte, Ordnung ganz aus dem Prior. Maßstab sind die manuellen
Nachfahrungen der Abb.-19-Wörter (Punktabstände per DTW/LDTW,
Fehlerzählung an Schleifenkreuzungen, i-Punkten/Umlauten,
Deckstrichen); „der Tinte perfekt folgen" ist erreicht, wenn der
automatische Folger im blinden Paarvergleich (humanbench-Methode) vom
manuellen Nachfahren nicht mehr unterscheidbar ist. Kein GPU-Training,
kein Fremdmodell — und jeder Fortschritt zahlt doppelt: sofort als
automatisches Nachfahren (§5) und später als fertige Route A des
Rückgewinnungs-Duells T3.

## 7 Risiken und Grenzen

- **Datenknappheit in der Ziel-Ära.** Für Sütterlin 1911–1941 gibt es
  kein lizenziertes Fremdkorpus; T2 trainiert überwiegend auf
  18./19.-Jh.-Kurrent. Das Ergebnis ist dann ein Kurrent-Generator —
  für die 1922er Hand bleibt Few-Shot-Stilübertragung plus eigenes
  Material.
- **Lizenz-Hygiene.** NC-SA-Teilmengen bleiben komplett draußen;
  SA-Copyleft wird gemieden; Richter-Modelle *benutzen* ist unkritisch,
  sie weiterverteilen nicht. Auf fremden Daten trainierte eigene
  Gewichte werden nicht veröffentlicht; auf DB-Inhalten trainierte
  Gewichte fallen unter die Open-Core-Reservierung (§3).
- **Der Domain Gap.** Ein auf Engine-Rendern vortrainiertes Modell kann
  die Engine-Ästhetik lernen statt Natürlichkeit; deshalb T2 mit echtem
  Material und der blinde Menschvergleich als Sensor, den keine Metrik
  ersetzt.
- **Die unsichtbare Strichfolge.** Kein Bild-Maß und kein DTW bemerkt
  einen historisch falschen Duktus, solange die Bahn glatt ist. Für
  alles, was Animation oder Belegbarkeit braucht, bleibt der
  autorisierte Duktus-Prior die Wahrheit; Weg-B-Bahnen sind
  Plotter-Material, keine Duktus-Quelle.
- **Aufwand.** T1/T2 brauchen eine ≥-24-GB-GPU über Tage (Miete genügt);
  Diffusions-Sampling ist langsam (DDIM hilft). Das ist bewusst
  Offline-Messaufwand — CPU/GPU-Zeit ist laut Guardrail kein Grund,
  eine Ecke abzukürzen.
- **Verhältnis zur Architektur.** Dieses Doc ändert keine Entscheidung:
  Analysis-by-Synthesis mit Duktus-Prior bleibt der Systemkern
  (architektur.md §2), die `research/`-Schicht folgt dem Code nie. Sollte
  ein Prüfstein einen Kurswechsel nahelegen, ist der Weg dorthin ein
  neues Proposal mit Verworfen-Abschnitt — nicht dieses Journal.

## 8 Quellen

**Einstieg und Überblick:**
[awesome-handwritten-text-generation](https://github.com/koninik/awesome-handwritten-text-generation) ·
[Survey Handwriting Synthesis 2019–2024, Pattern Recognition 2025](https://www.sciencedirect.com/science/article/pii/S0031320325000172)

**Offline-HTG:**
ScrabbleGAN [arXiv:2003.10557](https://arxiv.org/abs/2003.10557) ([Code](https://github.com/amzn/convolutional-handwriting-gan)) ·
GANwriting [arXiv:2003.02567](https://arxiv.org/abs/2003.02567) ·
HiGAN+ [ACM TOG 2022](https://dl.acm.org/doi/10.1145/3550070) ([Code](https://github.com/ganji15/HiGANplus)) ·
HWT [arXiv:2104.03964](https://arxiv.org/abs/2104.03964) ([Code+Gewichte](https://github.com/ankanbhunia/Handwriting-Transformers)) ·
VATr [arXiv:2303.15269](https://arxiv.org/abs/2303.15269) ([Code](https://github.com/aimagelab/VATr)) ·
VATr++ [arXiv:2402.10798](https://arxiv.org/abs/2402.10798) ([Code](https://github.com/EDM-Research/VATr-pp)) ·
WordStylist [arXiv:2303.16576](https://arxiv.org/abs/2303.16576) ([Code](https://github.com/koninik/WordStylist)) ·
DiffusionPen [arXiv:2409.06065](https://arxiv.org/abs/2409.06065) ([Code](https://github.com/koninik/DiffusionPen) · [Gewichte](https://huggingface.co/konnik/DiffusionPen)) ·
One-DM [arXiv:2409.04004](https://arxiv.org/abs/2409.04004) ([Code+Gewichte](https://github.com/dailenson/One-DM)) ·
DiffBrush [arXiv:2508.03256](https://arxiv.org/abs/2508.03256) ·
Absatz-LDM [arXiv:2409.00786](https://arxiv.org/abs/2409.00786) ·
Emuru [arXiv:2503.17074](https://arxiv.org/abs/2503.17074) ([Gewichte](https://huggingface.co/blowing-up-groundhogs/emuru)) ·
Semi-Supervised-Adaption [arXiv:2412.15853](https://arxiv.org/abs/2412.15853) ·
Ukrainisch-Retrain [arXiv:2605.27487](https://arxiv.org/abs/2605.27487) ·
StylusAI [arXiv:2407.15608](https://arxiv.org/abs/2407.15608) ·
OCR-Constrained GANs [arXiv:2103.08236](https://arxiv.org/abs/2103.08236)

**Bewertung:**
HWD [arXiv:2310.20316](https://arxiv.org/abs/2310.20316) ([Code](https://github.com/aimagelab/HWD)) ·
Rethinking HTG Evaluation [arXiv:2409.02683](https://arxiv.org/abs/2409.02683) ·
Quo Vadis HTG for HTR [arXiv:2508.09936](https://arxiv.org/abs/2508.09936)

**Offline→Online:**
Bhunia et al. [arXiv:1801.07211](https://arxiv.org/abs/1801.07211) ·
TRACE [arXiv:2105.11559](https://arxiv.org/abs/2105.11559) ·
PEN-Net/AIoU/LDTW [arXiv:2210.15879](https://arxiv.org/abs/2210.15879) ·
Diffusions-Rekonstruktion [arXiv:2607.03422](https://arxiv.org/abs/2607.03422) ·
Writing Order Recovery [arXiv:2406.03194](https://arxiv.org/abs/2406.03194) ([Code](https://github.com/gioelecrispo/wor)) ·
PolyVector Flow [ACM TOG](https://dl.acm.org/doi/10.1145/3478513.3480529) ·
InkSight [arXiv:2402.05804](https://arxiv.org/abs/2402.05804) ([Code+Gewichte](https://github.com/google-research/inksight)) ·
Spatio-Temporal Handwriting Imitation [arXiv:2003.10593](https://arxiv.org/abs/2003.10593) ([Code](https://github.com/M4rt1nM4yr/spatio-temporal_handwriting_imitation)) ·
Cursive Transformer [arXiv:2504.00051](https://arxiv.org/abs/2504.00051) ·
General Virtual Sketching [SIGGRAPH 2021](https://markmohr.github.io/virtual_sketching/) ·
vpype [github.com/abey79/vpype](https://github.com/abey79/vpype)

**Daten und Richter:**
READ/ICFHR 2016 Ratsprotokolle [Zenodo 1164045](https://zenodo.org/records/1164045) ·
Konzilsprotokolle Greifswald [Zenodo 215383](https://zenodo.org/records/215383) ·
Bundesratsprotokolle [Zenodo 4746341](https://zenodo.org/records/4746341) ·
19.-Jh.-Kurrent (gemischte Lizenz) [Zenodo 17252677](https://zenodo.org/records/17252677) ·
Bullinger [github.com/pstroe/bullinger-htr](https://github.com/pstroe/bullinger-htr) ·
HTR-United-Katalog [htr-united.github.io](https://htr-united.github.io/catalog.html) ·
Transkribus German Kurrent [Modellseite](https://www.transkribus.org/models/german-kurrent-and-sutterlin-17th-20th-century) ·
TrOCR-Kurrent (Bern) [huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII](https://huggingface.co/dh-unibe/trocr-kurrent-XVI-XVII) ·
kraken German Handwriting [Zenodo 7933463](https://zenodo.org/records/7933463)
