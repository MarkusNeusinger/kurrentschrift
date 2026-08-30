# Vom Scan zum Schreibsystem — der Datenfluss im Überblick

> **Status (2026-08-03): lebend.** Die Überblicks-Erzählung des Datenflusses;
> jede neue Stufe, neue Admin-Fläche oder geschlossene Lücke zieht sie nach —
> insbesondere die Lücken-Liste am Ende, wenn eines der dort verlinkten
> Issues (#270–#274) schließt.

Die eine durchgehende Erzählung: wie aus drei äußeren Zuflüssen — einer
gemeinfreien **Buchstabentafel**, den **geschriebenen Wortproben** derselben
Hand und dem **Nachfahren des Autors** — ein System wird, das beliebigen Text
selbständig schreibt. Wer macht dabei was (Mensch vs. Algorithmus), wo ist
jede Stufe im Admin sichtbar, und was davon gehört zum fertigen System — was
nur zum Trainingsgerüst drumherum.

> **Dies ist eine Übersicht, kein Nachschlagewerk.** Jeder Abschnitt nennt am
> Ende das Dokument, in dem die Details stehen; die Sammelliste steht unter
> [„Wo die Details stehen"](#wo-die-details-stehen).

---

## Das Grundprinzip

Ein Scan weiß, wie ein Buchstabe *aussieht* — aber nicht, wie er *geschrieben*
wird. Aus einem Standbild ist nicht ablesbar, welcher Strich zuerst kam,
welcher Ast an einer Kreuzung zu welchem Zug gehört und wo die Feder abgesetzt
hat. Genau dieses fehlende Stück liefert der Autor: **einmal pro Buchstabe**
fährt er den Weg nach — Strichreihenfolge, Richtung, Absetzpunkte. Alles
Weitere — verbinden, vermessen, verdichten — macht der Algorithmus.

Das ist die Architekturentscheidung **Analysis-by-Synthesis mit Duktus-Prior**
([`architektur.md`](architektur.md) §2): Das Bild liefert Geometrie und
Tintenbreite, das Duktus-Modell liefert Strichreihenfolge und die Auflösung
der Kreuzungen. Deshalb ist die manuelle Arbeit klein und einmalig, statt bei
jedem neuen Wort erneut anzufallen.

Drei Zuflüsse, sechs Schritte:

```
Tafel (PD-Scan) ──► Schritt 1: Bibliothek ──► Schritt 2: Schreiben  ← das fertige System
                          ▲                          │
Nachfahren (Mensch) ──────┘                          ▼
                                          Schritt 3: Maßstab (Messlatte)
Wortproben (PD-Platten) ─────────────────►         │
                                                    ▼
                                          Schritt 4: Ernte (Vorkommen)
                                                    ▼
                                          Schritt 5: Statistik je Hand
                                                    │  (genau ein Rückkanal:
                                                    ▼   apply-laufform)
                                          Schritt 6: Reklamieren → Diagnose → Messen
```

---

## Schritt 1 — Eine Tafel wird zur Buchstaben-Bibliothek

Die Lehrtafel einer gemeinfreien Vorlage zeigt jeden Buchstaben einmal sauber.
Der Autor zieht um jede Zelle einen Rahmen, putzt den Ausschnitt (fremde Tinte
vom Nachbarn wegradieren, Lücken im Strich zutinten), legt Grund- und
Mittellinie sowie die Schräglage fest — und fährt dann mit dem Stift den Weg
nach, den die Feder genommen hat. Jedes Absetzen beginnt einen neuen Zug.
Danach wird der Buchstabe freigegeben und gesperrt.

**Fachlich:** Die Crop-Konfiguration liegt je `(source, glyph_key)` in
`bboxes` — Rechteck, `mask_strokes` (Radierer), `ink_strokes` (Tintenpinsel),
`fill_holes_max_area` (Fleck-Autofüllung), `patches` (aus einer anderen
Tafelzelle kopierte Spenderregion, etwa der ä-Umlaut über einem u für ü),
`baseline_y`/`midband_y`, `guides`, `n_anchors`, `locked`. Der Ausschnitt wird
adaptiv binarisiert (`core/extract.py::binarize_adaptive`, Fleckfüllung
`fill_small_holes`); `skeletonize` liefert die Centerline, die
`distance_transform_edt` die halbe Strichbreite an jedem Punkt — der
**Schwellzug-Kanal**, bewusst getrennt von der Schwärze (§5). Der gezeichnete
Weg landet als `raw_path` mit `pen_up`-Markern und `stroke_starts` in
`trace_meta`; `core/pipeline.py::canonical_from_path` löst damit die Kreuzungen
auf, zieht die Anker auf die Tinte (Medial-Axis-Snap) und resampelt kanonisch →
eine `templates`-Zeile mit `anchors`, `half_widths`, `entry`/`exit`-Tangenten
und `advance`. Die Kopplungshöhe steht NICHT dabei — die entscheidet der
Komponist per Klassenregel (`core/compose.py::HIGH_COUPLE_BASES`,
architektur.md §3).

**Im Admin:** Einrichtungs-Wizard über `/admin/buchstaben?g=<key>` in vier Schritten —
**Ausschluss** (Radierer · Tinte · Lücken füllen · Zelle einsetzen · „Maske
zeigen") → **Lineatur** (Grund-/Mittellinie, und in derselben Fläche die
Schräglinien) → **Weg** (Zeichnen/Anpassen) → **Übersicht** mit Freigabe und
Sperre. Dazu das Diagnose-Modal (Ausschnitt · Skelett + Anker · kanonische
Form · M4-Fit, aus `…/templates/{glyph_key}/diagnostic` + `/fit`) und der Tab
die Übersicht von `/admin/buchstaben` (jeder Buchstabe als Tafel-Ausschnitt
vs. „wie geschrieben") und, im Detail, die Tafel-Form neben der Laufform.

**Wer macht was:** Mensch — Rahmen, Putzen, Lineatur/Schräglage und vor allem
der Weg (Strichfolge, Absetzpunkte: Autorenwissen, nicht ableitbar).
Algorithmus — Binarisierung, Skelett, Breitenmessung, Kreuzungsauflösung,
Anker-Snap, kanonisches Resampling.

> Details: [`architektur.md`](architektur.md) §2 · §3 · §5.

---

## Schritt 2 — Aus der Bibliothek schreibt das System

Ab hier ist nichts mehr manuell. Ein Text kommt herein, wird in Buchstaben der
Bibliothek zerlegt, diese werden auf der Grundlinie platziert — und die
Verbindungsstriche dazwischen werden **erzeugt**, aus dem Auslauf des linken
und dem Anstrich des rechten Buchstabens. Deshalb genügt ein autorisiertes
Alphabet: schon 30 Kleinbuchstaben ergäben 900 Paare, die niemand einzeln
zeichnen will. Dieser Schritt **ist** das fertige System — alles Folgende misst
und verbessert ihn, ersetzt ihn aber nicht.

**Fachlich:** `core/shaping.py` bildet Text auf geordnete `glyph_keys` ab —
langes ſ vs. Schluss-s nach der historischen Regel samt manuellem Fugen-Marker
`|` (`Donners|tag`), der geschlossene Ligatur-Satz `ch · ck · tz · ſt · St ·
qu · ß` (St als das eine Groß-Cluster, architektur.md §4)
als eigene Primärglyphen (enumerieren, nicht generieren), Ziffern und
Satzzeichen als echte Glyphen mit `joins: false`; die Wort-Position ist reiner
Render-Kontext und wird je Lauf gleicher `joins`-Klasse zugewiesen.
`core/compose.py` platziert auf der Grundlinie, erzeugt die Übergänge aus den
`entry`/`exit`-Tangenten (Klassen-Grammatik: Girlande, Absatz, Gabel-Joins,
Bar-Exits, Kapital-Übergabe), stellt Diakritika zurück und hält für nicht
verbindende Glyphen Tinten-Freiraum. Zwei Sonderwege: eine **freigegebene**
`glyph_pairs`-Zeile wird für genau ihr Nachbarpaar verbatim gerendert
(`pair_overrides`), und in fließenden Läufen (ab `ASCENDER_LEAN_MIN_RUN` = 3
verbundenen Slots) zieht der Composer die Laufform-Zeile heran
(`LAUFFORM_VARIANT` = 100, `laufform_by_key`). Die Federmodelle in
`core/widths.py` entscheiden über die Strichbreite: `pressure` (Kurrent,
gemessener Schwellzug), `constant` (Sütterlin-Gleichzug), `broad_nib`
(Offenbacher, aus dem Federmodell regeneriert); kalibriert je Quelle über
`api/rendering.py::pooled_pen`.

**Sichtbar:** öffentlich `/federprobe` (beliebiger Text live geschrieben),
`/tafel` und `/schreiben/uebungsblatt` — alle über
`GET /sources/{id}/write/glyphs` bzw. `GET /sources/{id}/write/word?text=…`.
Im Admin zeigt `/admin/uebergaenge` systematisch **jede** Zweierkombination
eines Buchstabens, serverseitig komponiert, mit Badge für vorhandene Overrides;
ein Klick öffnet die Verbindung samt Messung und — als letztes Mittel — dem
Paar-Editor. Kombinationen, die keine Platte je geschrieben hat, lassen sich
dort eintippen: geschrieben werden muss auch, was nie jemand geschrieben hat.

**Wer macht was:** vollständig Algorithmus. Der Mensch greift hier nur als
Ausnahme ein — der gezeichnete Paar-Override, ausdrücklich letztes Mittel.

> Details: [`architektur.md`](architektur.md) §4 ·
> [`federmodelle.md`](federmodelle.md) ·
> [`write-api.md`](../reference/write-api.md).

---

## Schritt 3 — Geschriebene Wörter werden zum Maßstab

Woher weiß das System, ob sein Wort gut ist? Aus den Platten derselben Hand,
auf denen dieselben Wörter wirklich geschrieben stehen. Der Autor hat sie
**einmal** vermessen: pro Wort ein Rechteck und die aus der Tinte abgelesene
Grund- und Mittellinie (die Tafeln tragen keine gedruckte Lineatur). Seitdem
läuft das automatisch — jedes komponierte Wort wird gegen die Originalpixel
gescort.

**Fachlich:** Die Vermessung liegt als Sidecar `words.json` neben den Platten
(`data/sources/suetterlin-1922/`): alle 63 Wörter der Abbildung 19 und alle 33
Buchstabenverbindungen der Abbildung 20, Boxen von
`tools/wordbench/propose_boxes.py` vorgeschlagen und Zeile für Zeile visuell
verifiziert; die Abb.-22-Schülerschrift (106 Wörter, andere Hand) ist ein
eigenes Cross-Hand-Set und geht nie in dieselbe Kennzahl ein. Das Lineal ist
**eingefroren**: `core/word_metric.py` (Import-Shim
`tools/wordbench/metric.py`) mit
`loss = 0,45·Übergang + 0,35·Deckung + 0,20·Breite`, dazu die
Segment-Attribution pro Buchstabe und pro Verbindung. Während eines
Optimierungs-Laufs wird der Composer geändert, nie die Messlatte. Report-only
und ausdrücklich **nicht** Teil des Loss: die Schräglagen-Spalte
(`tools/wordbench/slant.py`), das Gleichzug-Audit (`gleichzug.py`) und die
Spalte `meas` (`pairmeas.py`, gemessene vs. komponierte Verbindung).

**Im Admin:** die Wortproben-Übersicht von `/admin/woerter` —
jede Probe neben demselben Wort aus `/write/word`, wahlweise als Overlay über
den Specimen-Pixeln. „Scores berechnen & sortieren" holt je Karte den
admin-gesicherten
`GET /sources/{id}/word-samples/{sample_id}/score` und sortiert schlechteste
zuerst: das ist die Arbeitsliste. Die Umschaltung **Andere Hand** ist reiner
Kontext — nie Referenz, nie gescort. Die Verbindungs-Platten (Abb. 20) mit
ihren „Gemessen"-Chips sitzen dort, wo sie hingehören: in `/admin/uebergaenge`.

**Wer macht was:** Mensch — die einmalige Vermessung (und ihre visuelle
Verifikation). Algorithmus — jeder Score seitdem.

> Details: [`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6.

---

### Drei Sorten Punkt, die alle wie Punkte aussehen

Vorgezogen, weil ab hier alles davon handelt und die Verwechslung schon eine
Fehldiagnose gekostet hat (`qualitaetsmetrik.md` §10):

| Begriff | Was es ist | Wie viele |
|---|---|---|
| **Anker** | Stützpunkte der Spline. Die **Freiheitsgrade** des Fits — was der Optimierer verschieben darf, und was als Buchstabenform gespeichert wird. | 120 je Buchstabe |
| **Sample** | Punkte **auf** der Spline zwischen den Ankern. Nur hier liest die Zielfunktion die Tinte ab: Abstand, Breite, Deckung. Kein Anker wird je selbst befragt. | ~180 je Buchstabe |
| **Schritt** | Abstand **zweier benachbarter Anker**. Worauf `anchor_spike_ratio` misst: ein Schritt, der weit über dem Median seines Federzugs liegt, ist der „Anker im leeren Papier". | 119 je Buchstabe |

Die Reihenfolge ist: Anker bewegen → Spline neu abtasten → Samples lesen die
Tinte → Kraft zurück auf die Anker. **Ein Anker wirkt also nur mittelbar**, über
die ein bis zwei Samples in seiner Umgebung, und was am Anker selbst steht,
sieht der Optimierer nie. Wer die Rückstellkraft am Ankerort misst, beziffert
eine Kraft, die es in der Rechnung nicht gibt.

Dieselben drei Sorten heißen an drei Orten verschieden: als Zahl in der
Datenbank sind die Anker `templates.anchors` bzw. `instances.anchors`, im Fit
sind sie die Parameter `deltas`, und im gezeichneten Überlagern sind es die
Punkte der `fitted_polyline_px` — das ist aber die **Sample**-Reihe, nicht die
Ankerreihe. Ein Werkzeug, das beides für dasselbe hält, misst Unsinn.

## Schritt 4 — Die Ernte: das System vermisst jedes Vorkommen

Bis hier lautet die Frage „wie ähnlich ist mein Wort dem Original?". Jetzt
dreht sie sich um: „**wie hat die Hand jeden einzelnen Buchstaben und jeden
Übergang tatsächlich geschrieben?**" Dafür wird jedes Vorkommen auf den Platten
einzeln vermessen und als eigene Zeile abgelegt — nicht nur der Mittelwert.

**Fachlich:** Der M4-Fit (`core/fit.py::fit_template_to_instance`) warpt das
Buchstaben-Template regularisiert auf jedes Vorkommen; was die Gates besteht
(konvergiert, kleiner Restfehler, nicht am Rand), wird zur `instances`-Zeile:
gefittete Anker **zentriert** abgelegt („Formen, nicht Platzierungen"), dazu
`measurements` mit Restfehler, Wort-Id und Slot sowie den Nachbar-Keys
(`prev_key`/`next_key`). Jeder Verbindungsstrich wird zusätzlich herausseziert
→ `pair_instances`: Connector-Geometrie im Rahmen des linken Auslaufs,
Platzierungs-Offset und Dissektions-QC, darunter `gen_chamfer` als Audit-Zahl
„gemessen vs. komponiert". Ganze Wörter liegen als `word_instances` mit
Slot-Labels und Schreibpfad im Registrierungs-Rahmen des Worts, Provenienz
`traced` (aus der Ernte) oder `authored` (vom Admin manuell nachgefahren) —
eine Neu-Ernte überschreibt eine `authored`-Spur nie. Geerntet wird mit
`tools/laufform/harvest.py` und `tools/pairlab/harvest.py --store-occurrences`,
geschrieben über die admin-gesicherten Batch-`PUT`s
(`/sources/{id}/instances` · `/pair-instances` · `/word-instances`). **Am
Rendering ändert dieser Schritt nichts.**

**Im Admin:** `/admin/woerter?w=<text>` zeigt zu einem Wort jedes gespeicherte
Vorkommen über seinem Platten-Ausschnitt — mit einer gestrichelten Box je
gefittetem Buchstaben und einem Punkt auf jedem Übergang, beides anklickbar
(Box → Buchstaben-Ansicht, Punkt → Übergangs-Ansicht). „Nachfahren" öffnet den
Wort-Editor (`WordTraceEditorDialog`), in dem der Admin dort nachzieht, wo der
Auto-Fit scheitert; die Übersicht derselben Ansicht listet alle Proben,
schlechteste zuerst (ungefittete Buchstaben, dann mittlerer Fit-Restfehler).

**Wer macht was:** Algorithmus — Fit, Dissektion, automatische Nachfahrung.
Mensch — nur die roten Fälle: das manuelle Nachfahren (`authored`), das Ground
Truth erzeugt, nicht das Rendering flickt.

> Details: [`handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md)
> H1/H2 · [`architektur.md`](architektur.md) §3.

---

## Schritt 5 — Statistik je Hand: aus vielen Messungen ein Modell

Aus allen Vorkommen eines Buchstabens wird der Median gebildet: die
**Laufform** — wie diese Hand den Buchstaben im laufenden Wort formt, im
Unterschied zur isolierten Tafelzelle (gemessen 3–11 % breiter bei leicht
gestauchter Höhe; Stand 2026-08, 220 saubere Fits aus 257 Vorkommen). Dazu die
Streuung pro Anker. Dasselbe für jedes Buchstaben**paar**: mittlerer Versatz
und mittlere Verbindungsform. Diese Statistik ist zunächst **nur zum Ansehen**.
Genau **ein** bewusster Schritt hebt sie ins Schreibsystem.

**Fachlich:** Rechenkern ist das reine `core/aggregate.py`
(`aggregate_instances` · `aggregate_pair_instances`). Ergebnis: `aggregates` je
`(hand_id, glyph_key, variant)` — Per-Anker-Median, MAD-Hülle, gepoolte
Schicht-1-Statistik (Migration `0021`) — und `pair_aggregates` je
`(hand_id, left_key, right_key)` — Median-Offset, bogenlängen-nachgesampelter
Median-Connector, MAD-Hüllen, gepoolte Dissektions-QC (Migration `0023`). Die
Endpunkte sind vollständig admin-gesichert:
`GET/POST /hands/{hand_id}/aggregates[/rebuild]` (`min_n` 4) und
`GET/POST /hands/{hand_id}/pair-aggregates[/rebuild]` (`min_n` 1, weil Paare
dünn belegt sind). Ein Rebuild ändert **nichts** am Rendering. Der Prüfstein
`laufform_dev_xh` meldet je Glyphe den Abstand zwischen rekonstruiertem Median
und gespeicherter Laufform-Zeile. Der eine Rückkanal ist
`POST /hands/{hand_id}/aggregates/apply-laufform`: er schreibt die
**gespeicherten** Aggregate (nie eine Neuberechnung) als Template-Variante 100
— Median-Anker als Geometrie, Breiten, Strich-Topologie und
entry/exit/advance weiter aus der Tafelzeile, über denselben Helfer
`build_laufform_canonical`, den auch der manuelle
`PUT …/templates/{key}/laufform` benutzt. Für Paare gibt es bewusst **kein**
Apply-Gegenstück: `glyph_pairs` bleibt der sparsame verbatim-Override, der
§4-Generator bleibt Default, die Paar-Statistik ist sein Audit.

**Im Admin:** die Statistik-Blöcke der beiden Ansichten (Stufen-Einsicht W5,
`shell/LensStats.tsx`) — in `/admin/buchstaben` zeichnet „Statistik der Hand"
den Aggregat-Median als Ankerkette mit MAD-Kreisen über Grund- und Mittellinie
(die Laufform-Quelle) plus die gepoolten Zahlen; in `/admin/uebergaenge` zeigt
„Gemessen vs. komponiert" jede Vorkommens-Verbindung dünn, den Median-Connector
kräftig darüber und den Median-Versatz als Punkt mit MAD-Whisker. Je Schicht
ein leiser Neuaufbau-Knopf; dazu die „Gemessen"-Chips auf den Karten der
Verbindungs-Platten.

**Der Rückkanal hat seit 2026-08 eine Oberfläche** — und zwar eine, die sich
von den Inspektionsflächen abhebt, statt sich unter sie zu mischen. In
`/admin/buchstaben` sagt ein Chip je Buchstabe, ob die geschriebene Laufform
noch der gespeicherten Statistik entspricht („Laufform aktuell" ·
„Laufform veraltet · Abstand 0,05" · „noch keine Laufform"), und die
Median-Skizze zeichnet die **aktuell geschriebene** Laufform gestrichelt rot
gegen den Median, der sie ersetzen würde — der Unterschied ist damit
anzusehen, bevor irgendetwas passiert. Die Zahl dahinter kommt neuerdings aus
einem gewöhnlichen Read: `GET /hands/{id}/aggregates` liefert je Zeile
`laufform_anchors` und `laufform_dev_xh`, vorher war der Prüfstein nur als
Nebenprodukt eines Neuaufbaus oder eines Apply zu bekommen (man musste also
etwas *tun*, um zu erfahren, ob man etwas tun sollte). Das Überschreiben selbst
sitzt am Fuß der Ansicht in einem eigenen, gestrichelt umrandeten Block und
verlangt eine **Bestätigung**, die vorher auflistet, was sich ändert: je
Buchstabe Vorkommenszahl und Abstand, „neu" für eine erstmals geschriebene
Laufform, „unverändert" für Abstand 0 — danach der Bericht, was geschrieben und
was übersprungen wurde. Die Doktrin bleibt gewahrt: nicht weil der Griff
versteckt ist, sondern weil er sich als das ausweist, was er ist.

**Wer macht was:** Algorithmus — Median, Streuung, Prüfstein. Mensch — der
Beschluss, wann `apply-laufform` läuft.

> Details: [`handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md)
> H1/H2 · [`architektur.md`](architektur.md) §6 · §12.

---

## Schritt 6 — Die Schleife: reklamieren, diagnostizieren, messen

Was am Ende noch falsch aussieht, wird **bemängelt**, nicht von Hand
korrigiert. Der Admin markiert in der Werkbank einen Buchstaben, einen Übergang
oder ein Wort und legt ihn als Auftrag in den Korb — mit Notiz, statt mit
Screenshot. Eine Arbeitssitzung (Mensch oder KI) arbeitet die Aufträge nach
festem Protokoll ab.

**Fachlich:** Der Korb ist die Tabelle `work_items` (Migration `0020`,
Protokollspalten `0022`), vollständig admin-gesichert. `⚑` oder Umschalt-Klick
legt eine Zeile an; bei einem **Buchstaben** stellt der Dialog zuerst die
Vorsortier-Frage „Sieht der Buchstabe einzeln (in der Tafel-Ansicht daneben)
auch falsch aus?" — ja springt in den Wizard und legt nichts ab, nein reicht
die Beschwerde ein. Die Sitzung muss die Beschwerde **nachprüfen und
zurückspiegeln**, bevor sie etwas ändert (`status: ack` mit `understanding` +
`reproduced`), dann entlang der Stufen triagieren — Tafel-Duktus →
Laufform/Fit → Klassenregel → Platzierung → **erst zuletzt** Override — und
kann nur mit diagnostizierter `stage` (`chart_ductus` · `laufform` ·
`join_rule` · `composition` · `pair_override` · `word_trace` ·
`not_reproducible`) und `resolution` abschließen; unvollständig heißt 422
(`check_transition` in `api/routers/work_items.py`). Fehlt Ground Truth, geht
die Zeile als `returned` an den Autor zurück. Ob eine Änderung bleibt,
entscheidet das eingefrorene Lineal aus Schritt 3.

**Im Admin:** der Auftragskorb liegt seit dem Redesign im Header-Drawer, also
über allen drei Ansichten; ⚑ gibt es entsprechend in jeder von ihnen — auch für
eine frei eingetippte Kombination oder ein frei eingetipptes Wort, das gar
keinen Vorlagenbezug hat (die Zeile sagt das dann, statt einen zu erfinden).
Der „missverstanden"-Knopf legt eine falsch verstandene Zeile mit Korrektur
zurück auf `open`; quellenfrei lesbar ist der Korb über
`GET /work-items?status=open`. Den Ablauf führt das Skill
`.claude/skills/work-basket/`.

**Wer macht was:** Mensch — reklamieren (wo es weh tut, nicht wo es verursacht
ist) und die Ground-Truth-Rückläufer. Algorithmus/Sitzung — Reproduktion,
Triage, Regel-Fix, Messung, Archiv-Zeile.

**Doktrin:** manuell hinzufügen nur, wo Ground Truth entsteht (Tafel-Duktus,
Wort-Nachfahrung); alles Generierte — Laufform, Übergangs-Grammatik,
Komposition — wird **bemängelt**, nie von Hand nachgebessert. Ein Mangel
schärft die Regel für alle Wörter, ein manueller Eingriff repariert genau eine
Stelle.

> Details: [`optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md)
> §3–§5.

---

## Finales System vs. Trainingsgerüst

Die nützlichste Unterscheidung im ganzen Datenfluss — weil sie beantwortet,
was ausfallen dürfte, ohne dass ein einziges Wort anders geschrieben würde.

**Auf dem Schreibpfad liegen nur:**

| Art | Artefakt |
|---|---|
| Daten | `templates` — Tafel-Duktus (Variante 0/…) **und** Laufform (Variante 100) |
| Daten | `glyph_pairs`, aber nur die **freigegebenen** Zeilen |
| Regeln (Code) | `core/shaping.py` · `core/compose.py` · `core/widths.py` (Federmodelle) |
| Auslieferung | `/write/glyphs` · `/write/word` und die SPA-Renderer darüber |

**Alles Übrige misst, prüft oder merkt sich — und schreibt nie:**
die drei Vorkommens-Tabellen (`instances` · `pair_instances` ·
`word_instances`), beide Aggregat-Tabellen (`aggregates` · `pair_aggregates`)
außer im Moment des `apply-laufform`, das Sidecar `words.json` samt
word-samples-Endpunkten, Wort- und Glyph-Bench mitsamt eingefrorenen Fixtures,
die Inspektions-Labs (`tools/glyphlab` · `tools/wordlab` · `tools/pairlab`),
die Ernte-Werkzeuge und der Auftragskorb `work_items`.

> **Merksatz:** Was die Live-DB an `templates` + `glyph_pairs` hält, schreibt;
> alles andere misst.

---

## Warum es kein „a vor b" gibt (Kern + Übergang)

Eine naheliegende Sorge: Wenn ein `a` vor `b` anders aussieht als vor `c` —
verschmiert der eine Median über alle `a` dann nicht genau diesen Unterschied?

**Die Antwort ist zweiteilig, weil das Modell zweiteilig ist.** Die
Vorkommens-Anker werden **zentriert** gespeichert („Formen, nicht
Platzierungen"), der Buchstaben-Median ist also der kontextfreie **Körper**.
Der Übergang ist gar nicht Teil davon, sondern ein eigenes Messobjekt **pro
Paar**: `a`→`b` und `a`→`c` bekommen je eine eigene `pair_aggregates`-Zeile und
werden nie miteinander verrechnet. Der kontextabhängige Teil ist also sehr wohl
kontextabhängig modelliert — er sitzt nur nicht im Buchstaben.

**Wo die Sorge trotzdem berechtigt ist:** wenn die Hand den **Körper selbst**
je nach Nachfolger umformt (den Auslauf früher hochzieht, den Bogen strafft).
Das schluckt der Buchstaben-Median heute — sichtbar als fette MAD-Kreise an den
auslaufseitigen Ankern der Werkbank-Linse und als erhöhte `gen_chamfer`/`doff`
in der Paar-Schicht. Das Ausmaß dieser Umformung *misst* `tools/pairlab`
bereits (`tail_adapt`/`head_adapt`, Koppelhöhe), gespeichert wird es nicht.

**Eskalationsleiter, wenn eine Regel ein Paar nicht trägt:** zuerst die
Klassenregel in `core/compose.py` schärfen (hebt alle Paare derselben Klasse);
**erst zuletzt** ein verbatim-Override für genau dieses Paar. Was es
ausdrücklich **nicht** gibt, ist eine Kontext-Gabelung des Buchstabens (ein
eigenes `a`-vor-`b`-Template): Die Bigramm-Datenbank ist in
[`architektur.md`](architektur.md) §2 verworfen — kombinatorisch unmöglich und
unnötig, weil der Duktus den Übergang erzeugt. Der geschlossene Ligatur-Satz
(§4) ist die enumerierte, endliche Ausnahme, keine Hintertür.

**Die Tür für später steht offen:** Jede `instances`-Zeile trägt ihre
Nachbar-Keys (`prev_key`/`next_key`) mit. Klassenbedingte Mediane („`a` vor
Unterlängen") wären daraus ableitbar, ohne eine Zeile neu zu ernten — H3-Gebiet
des Stufenplans, bewusst unentschieden.

---

## Aktualität: was gespeichert ist, veraltet — was generiert wird, nicht

Die Laufform ist ein **materialisierter Schnappschuss** am Ende einer Kette aus
lauter ausdrücklichen Handgriffen: Tafel-Duktus → Ernte → Rebuild → Apply.
Ändert sich etwas weiter oben, ist der Schnappschuss veraltet:

- Ein neu getuschter Tafel-Duktus entwertet nicht nur die Laufform, sondern
  schon die Fits, die auf dem alten Template beruhten.
- Neue oder korrigierte Wort-Spuren wirken erst nach einer erneuten Ernte.
- Ein Rebuild ohne Apply zeigt sich als von Null verschiedener
  `laufform_dev_xh` — die Statistik ist weiter, die gerenderte Zeile nicht.

**Generierte Übergänge veralten dagegen nicht.** Sie lesen bei **jeder**
Komposition den `exit`/`entry` der *aktuell gerenderten* Form — ändert sich die
Laufform, folgen sie automatisch. Genau das ist der Grund, warum Regeln
Overrides vorzuziehen sind.

**Die eine Ausnahme:** Ein freigegebener Paar-Override ist eingefrorene
verbatim-Geometrie. Er wandert mit der Platzierung mit, seine **Form** folgt
einer späteren Laufform-Änderung aber nicht — ein Override, der zu einer alten
Form gezeichnet wurde, bleibt alt.

Marker für Veraltung gibt es heute **nirgends** — weder eine Anzeige noch eine
Prüfung.

> **Kurzformel:** Gespeichert und pflegebedürftig sind Chart-Duktus, Laufform
> (Variante 100) und Overrides; live und wartungsfrei ist alles Generierte.

---

## Bekannte Lücken (Stand 2026-08-03)

- ~~**`apply-laufform` hat nirgends eine Oberfläche**~~ — **geschlossen
  (2026-08)**: Freigabe-Block mit Bestätigungsdialog in `/admin/buchstaben`,
  Frische-Chip und Differenz-Skizze je Buchstabe, `laufform_dev_xh` +
  `laufform_anchors` auf `GET /hands/{id}/aggregates`
  ([#270](https://github.com/MarkusNeusinger/kurrentschrift/issues/270)).
  Offen bleibt aus derselben Ausgabe die **Paar-Seite** der Hand-Übersicht: die
  `pair_aggregates` haben keine Tabelle, nur die Linse je Übergang.
- **Die Ernte ist aus dem Admin nicht auslösbar** — `tools/laufform/harvest.py`
  und `tools/pairlab/harvest.py` laufen nur auf der Kommandozeile
  ([#272](https://github.com/MarkusNeusinger/kurrentschrift/issues/272)).
- **Die Hand-Übersicht ist halb da** — der Bestätigungsdialog listet alle
  Buchstaben-Aggregate mit `n` und Abstand zur Laufform, aber nur im Moment der
  Übernahme und ohne die Paar-Schicht; eine dauerhaft abrufbare Tabelle über
  beide Schichten (Abdeckung, Streuung) fehlt weiter
  ([#270](https://github.com/MarkusNeusinger/kurrentschrift/issues/270)).
- **`min_n` = 4 schließt die Versalien praktisch aus** — Großbuchstaben kommen
  auf den Platten zu selten vor, um die Schwelle zu erreichen, und bekommen
  daher keine Laufform
  ([#273](https://github.com/MarkusNeusinger/kurrentschrift/issues/273)).
- **Koppelhöhe und `tail_adapt` werden nicht persistiert** — `tools/pairlab`
  misst, wie stark die Hand den Buchstabenkörper für den Übergang umformt, aber
  keine Tabelle hält das Ergebnis
  ([#274](https://github.com/MarkusNeusinger/kurrentschrift/issues/274)).
- **Veraltung ist nur für die Laufform sichtbar** — dort sagt es der
  Frische-Chip je Buchstabe (2026-08,
  [#270](https://github.com/MarkusNeusinger/kurrentschrift/issues/270)). Für
  Fits, die auf einem inzwischen neu getuschten Tafel-Duktus beruhen, und für
  eingefrorene Paar-Overrides
  ([#271](https://github.com/MarkusNeusinger/kurrentschrift/issues/271)) gibt
  es weiter keinen Marker und keine Prüfung.

---

## Wo die Details stehen

| Thema | Dokument |
|---|---|
| Duktus-Prior, verworfene Alternativen, Bigramm-Absage | [`architektur.md`](architektur.md) §2 |
| Bibliothekseinheit, Schema, Tabellen | [`architektur.md`](architektur.md) §3 |
| Übergänge als Konsequenz, Ligatur-Ausnahme | [`architektur.md`](architektur.md) §4 |
| Dreistufige Qualitätspipeline | [`architektur.md`](architektur.md) §6 |
| Federmodelle, Ziffern/Satzzeichen | [`federmodelle.md`](federmodelle.md) |
| Wort-Bench, eingefrorenes Lineal, Baselines | [`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §6 |
| Vorkommen, Aggregate, Stufen H0–H5 | [`handmodell-stufenplan.md`](../proposals/handmodell-stufenplan.md) |
| Stufen-Doktrin, Auftragskorb-Protokoll | [`optimierungs-werkbank.md`](../proposals/optimierungs-werkbank.md) |
| Öffentliche Render-Endpunkte | [`write-api.md`](../reference/write-api.md) |
| Ernte-Werkzeuge, Benches, Inspektions-Labs | [`werkzeuge.md`](../reference/werkzeuge.md) |
