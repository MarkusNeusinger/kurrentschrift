# Admin-Redesign auf der grünen Wiese 2026-09-17 — Optionen, Szenarien, Rückfragen

> **Status (2026-09-17): offen.** Diskussionsgrundlage auf Wunsch des
> Autors („noch nichts implementieren … ich will das erst mit dir durch
> diskutieren bevor wir umsetzen"). Nichts davon ist gebaut, und dieses Doc
> entscheidet nichts: es hält den Ist-Befund des Admins fest (§3), was
> bereits bindend feststeht (§4), drei Gestaltungs-Optionen mit Information
> und Knöpfen je Fläche (§7–§9), die gemeinsame Spezifikation der
> Eigenhand-Statistik (§6), die Nutzungsszenarien (§11) und den
> Rückfragen-Katalog (§12), den der Autor zuerst beantwortet. Die
> Entscheide werden hier als datierte Autor-Entscheide nachgetragen und die
> gewählte Option bekommt ihren Umsetzungs-Abschnitt; der Status bleibt
> `offen`, bis die erste Umsetzung ausgeliefert ist — erst dann
> `teil-umgesetzt` (Lifecycle nach `dokument-status.md`). Die Doktrin
> bleibt, wo sie ist
> ([`optimierungs-werkbank.md`](optimierungs-werkbank.md) §3–§6/§8,
> [`eigenhand-erfassung.md`](eigenhand-erfassung.md) §2/§7/§12,
> [`handmodell-stufenplan.md`](handmodell-stufenplan.md) §5,
> [`../concepts/vision.md`](../concepts/vision.md) „Drei Rollen"). Wo eine
> Antwort des Katalogs eine bindende Regel bewegen würde, steht das in
> §10.2 als erklärtes Proposal-Update — nicht als stille Abweichung.
> Empfehlung des Panels nach Kritikrunde: **Option A zuerst, die Bausteine
> von C darauf, B punktuell** (§10) — unter dem Vorbehalt von Q1 (wie
> dringend „in meiner Hand geschriebenes" ist). Das Kritik-Protokoll liegt
> als datierte Momentaufnahme in
> [`../notes/admin-redesign-kritik-2026-09-17.md`](../notes/admin-redesign-kritik-2026-09-17.md).

## 1 Anlass

Der Autor, 2026-09-17, vom Handy (Tippfehler belassen):

> bitte teste dich durch den Admin Bereich wie können wir das übersichtlicher
> gestalten insbesondere mit den Wörtern historisch und meinen geschriebenen
> weil wichtig wird die pro Buchstaben und Übergang Statistik aus meinen
> streifen sein folgt der ink gut muss ich manuell Nachfahren fürs Training wie
> sehen Ableitungen und in meiner Hand geschriebenes aus... bitte mache einen
> Plan grüne Wiese wenn wir den Admin Bereich mit allem was wir jetzt wissen
> neu designen wollen wie würde er aussehen welche 8nfo brauchen wir wo auch
> Buttons zu fahre das jetzt mal nach... […] noch nichts implementieren
> erstelle auch einen Rückfragen Katalog ich will das erst mit dir durch
> diskutieren bevor wir umsetzen

Gelesen als sieben Fragen, an denen sich jede Option messen lassen muss:

| # | Frage | Woran der Plan sie beantwortet |
|---|---|---|
| F1 | Wie wird der Admin **übersichtlicher**, vor allem die Trennung und Verbindung von **historischen** Wörtern (Platten-Wortproben der Vorlage: Ground Truth und Maßstab) und **meinen geschriebenen** (Eigenhand-Streifen: Trainingsdaten und künftige Produktionshand)? | §5.1 Ideen 1–4, §7–§9 je Option; Q2, Q3, Q7, Q8 |
| F2 | Welche **Statistik je Buchstabe und je Übergang aus meinen Streifen** — welche Zahlen, wo sichtbar, wie abgeleitet? | §6.1, §6.2; Q11, Q15, Q16 |
| F3 | **Folgt der Ink gut?** — je Streifen/Wort sehen, ob der Tintenpfad der Tinte folgt | §6.3 Tintentreue; Q9, Q10 |
| F4 | **Muss ich manuell nachfahren fürs Training?** — die Arbeitsliste und der Editor dafür | §6.4 (Antwort heute: nein — erst mit Q4); Q12–Q15 |
| F5 | **Wie sehen Ableitungen aus?** — Laufform, Median, Aggregat der eigenen Hand neben Tafel und Platte | §6.5; Q3, Q11, Q19 |
| F6 | **… und in meiner Hand geschriebenes?** — ein beliebiges Wort, wie die Engine es mit meiner Hand schriebe | §6.6; Q1, Q19–Q23 |
| F7 | **Grüne Wiese** — welche Information und welche Knöpfe gehören auf welche Fläche; Optionen mit Warum/Was/Wie; Nutzungsszenarien; Rückfragen | §7–§12 |

Der Plan ist Diskussionsgrundlage. Er entscheidet nichts, er legt Optionen
und die Fragen vor, die nur der Autor beantworten kann (§12). Was danach
gebaut wird, bekommt einen eigenen Umsetzungs-Abschnitt in diesem Doc — und
erst dann PRs.

## 2 Wie dieser Plan entstanden ist

Vier Schritte, in dieser Reihenfolge, damit die Optionen auf dem Ist-Stand
stehen und nicht auf einer Erinnerung daran:

1. **Browser-Rundgang durch den heutigen Admin** (§3). Die Cloud-Sitzung
   hat keinen `ADMIN_TOKEN`, und der Admin bootet gegen die deployte API
   ohne ihn nicht — der Boot-Read `GET /sources/{id}/bboxes` ist
   admin-gegatet, die Ansicht bleibt bei „Quelle nicht erreichbar". Darum
   ein lokaler Wegwerf-Stack: Postgres 16, `alembic upgrade head` (Seeds:
   vier Quellen), API mit lokalem Token, Vite mit `VITE_ADMIN_TOKEN`,
   Playwright gegen das vorinstallierte Chromium bei 1440 und 390 px.
   Geseedet wurden die 63 Sütterlin-Bboxen aus dem öffentlichen
   `bboxes/status`, 32 Glyphen per Trace aus zurückprojizierten öffentlichen
   Render-Payloads (die Skalierung ist geraten, die lokalen Glyphbilder sind
   FALSCH und nur strukturell zu lesen), vier Korb-Einträge, ein
   Eigenhand-Setup und ein gedruckter Bogen. Die 202 Wortproben kommen aus
   dem Repo. **Nicht gesehen:** echte Vorkommen, Aggregate, Laufformen,
   Streifen, Befunde, Pfade, Rückspiegelungen — alles hinter dem Gate der
   deployten API. Wo der Plan über diese Flächen spricht, spricht er aus dem
   Code und den Docs, nicht aus dem Bild.
2. **Bestandsaufnahme durch acht parallele Leser** (Shell · Buchstaben ·
   Übergänge · Wörter · Eigenhand · Daten/API · Doktrin · Autor-Wünsche),
   verdichtet zu einer Ist-Karte, aus der §4 und die Datenlage in §6 stammen.
3. **Entwurfsrunde:** sechs unabhängige Entwürfe aus je einer Perspektive —
   Tag im Leben des Autors · Informationsarchitektur · Statistik und Messung
   · Doktrin und Risiko · UX-Praxis der Annotations- und Kurationswerkzeuge ·
   Produktionshand —, dann drei Richter (der Autor selbst, der
   Doktrin-Wächter, der Ingenieur), dann eine Synthese zu drei Optionen
   (§7–§9) und dem ersten Rückfragen-Katalog.
4. **Kritikrunde:** fünf Gegenleser prüfen die Optionen auf Doktrinbruch
   (23 Befunde), Machbarkeit gegen API, DB und Werkzeuge (17), den Autor am
   ersten Tag mit jeder Option (15), Gestaltung und Geräte (17) und die
   Vollständigkeit des Rückfragen-Katalogs (26); jeder Befund trägt einen
   Beleg, eine Überarbeitung hat alle 98 mit Entscheid protokolliert
   ([`../notes/admin-redesign-kritik-2026-09-17.md`](../notes/admin-redesign-kritik-2026-09-17.md)).
   Zwei Kritiker-Irrtümer wurden zurückgewiesen, der Rest hat den Text
   verändert: sechs Doktrin-Fehllesungen, vier falsche
   EXISTS/DERIVABLE-Angaben, der Katalog von 40 auf 25 Fragen plus 26
   Vorgaben. Was die Kritik gekippt hat, steht in §13.

Die Zahlen aus der deployten API, soweit öffentlich lesbar (2026-09-17):
89 Template-Zeilen der Sütterlin-1922 (63 Keys in Variante 0, dazu
Varianten 1/2 und die Laufform 100), 62 von 63 Bboxen gesperrt, 202
Wortproben (63 Wörter der Bench, Abb.-20-Paare, Abb.-22-Schülerhand).

## 3 Ist-Befund: der Admin heute, Fläche für Fläche

Was hier steht, wurde angeklickt und angesehen; die Bildschirmfotos sind
in der PR #607 als Lese-Seite verlinkt (sie gehören nicht ins Repo).
Kürzel: **(Z)** = zeigt, **(K)** = Knöpfe.

### 3.1 Einstieg `/admin` und Kopfleiste

(Z) „Welche Vorlage?" mit drei Karten (Offenbacher · Kurrent · Sütterlin:
Titel, Quellen-Id, Chips Verhältnis/Schräglage, Haken an der aktiven);
Hinweis, dass die Wahl im Browser gespeichert bleibt. Kopfleiste: Wordmark ·
Vorlagen-Chip · Buchstaben · Übergänge · Wörter · Eigenhand · ⚑ Korb.

**Befund:** Auf `/admin/eigenhand` bleibt der Chip „Sütterlin ·
suetterlin-1922" stehen und das Korb-Badge zählt den Korb der VORLAGE — die
Seite gehört aber einer Hand. Zwei Scopes in einer Leiste, ohne dass die
Leiste es sagt. Der Browser-Tab trägt auf jeder Admin-Seite den
öffentlichen Standardtitel.

### 3.2 Buchstaben

**Übersicht:** (Z) eine Zeile je Buchstabe (63) mit vier Flächen — Original ·
Wie geschrieben · Laufform · Median & Vorkommen —, Kopf mit Glyph, Key,
„n Vorkommen", Score-Chip, Fußzeile „Abzüge: Deckungslücke · Glätte · Ecken
· Senkrechte · Kreuzung · Doppelzug". (K) „Buchstabe wählen" (Raster-
Popover), Umschalter Alphabet / Schlechteste zuerst, Schalter Überlagern,
Neu laden, je Zeile Öffnen. **Seitenhöhe 10 585 px** am Desktop, 18 795 px
am Handy. Kein Status-Filter (gesperrt · ohne Laufform · ohne Vorkommen ·
mit Korb-Auftrag).

**Detail `?g=n`:** (Z) Kopfzeile ‹ n › mit Chips erstellt · gesperrt · n
Vorkommen; Panels in dieser Reihenfolge: Tafel-Ausschnitt · Wie es
geschrieben wird (Tafel-Form V0 neben Laufform V100) · Landmarken (Legende
mit sieben Klassen und Zählern, Kringel-Katalog-Zeile) · Vorkommen in
Wörtern (n) · Statistik der Hand · Übergänge dieses Buchstabens · Wörter mit
diesem Buchstaben · **Laufform übernehmen** (abgesetzt, gestrichelt, am
Fuß). (K) Alle Buchstaben · ⚑ Buchstabe markieren · Einrichten · Diagnose ·
Tafel öffnen ▾ · Landmarken zeigen · Fehlende Marke melden · Alle
Kombinationen ansehen. Dialoge: ⚑ „Auftrag einreichen" mit genau einer
Vorsortierfrage („Sieht der Buchstabe einzeln auch falsch aus?" → Ja:
Wizard / Nein: Auftrag); Diagnose (Original · Skelett & Stützstellen ·
Kanonische Form, darunter „Einpassung an das Original", Knopf „Neu ableiten
& speichern"); Wizard mit vier Schritten (Ausschluss · Lineatur · Weg ·
Übersicht), Schloss-Chip „gesperrt" im Titel.

**Befund:** horizontaler Overflow von 16 px auf ALLEN Detailseiten (doc 1456
> win 1440; 398 > 390) — ein Layoutfehler, kein Designproblem.

### 3.3 Übergänge

**Übersicht:** (Z) Freitext „Kombination eintippen", Buchstaben-Leiste (nur
autorierte Keys), zwei Kartenreihen „a als erster / als zweiter Buchstabe"
mit Mini-Render je Paar. (K) Ansehen, je Karte Öffnen, „Verbindungs-Platten
der Vorlage einblenden". Keine Zelle sagt, ob Vorkommen, Override oder
Korb-Auftrag existieren.

**Detail `?l=e&r=n`:** (Z) Kopf e → n mit Chips generiert · n Vorkommen;
Panels Wie es geschrieben wird (komponiert; Doktrin-Satz „Erst die
Klassenregel schärfen") · Gemessen vs. komponiert · Vorkommen (n) · Wörter
mit diesem Übergang. (K) Alle Kombinationen · ⚑ Übergang markieren ·
Buchstabe e · Buchstabe n · Paar-Editor öffnen. Der Paar-Editor:
Zeichenfläche, Versatz-Regler, Zug löschen, Live-Ergebnis über
`/write/word`, Kästchen „Freigegeben (ersetzt den Generator)", Speichern.
Konsole: 404 auf `/pairs/e/n`, wenn kein Override existiert.

### 3.4 Wörter

**Übersicht:** (Z) Freitext „Wort oder Satz", „Proben filtern", Auswahl
Nachfahren: Alle · Offen · Nachgefahren · Unvollständig, Tabs Wörter ·
Andere Hand · Nachgefahren, Zähler „0/63 von Hand nachgefahren"; je Probe
eine Karte Original · Wie geschrieben. (K) Schreiben · Überlagern · Scores
berechnen & sortieren · Neu laden · je Karte Öffnen. **Seitenhöhe
20 088 px.** Andere Hand: Abb.-22-Karten mit Chip „fehlend: H".

**Detail `?w=unter&s=unter`:** (Z) Kopf mit Wort und Chip „n Belege",
Freitextfeld, Wie es geschrieben wird, Woraus es besteht (Buchstaben- und
Übergangs-Chips als Absprünge), Hinweiszeile „keine nachgefahrene Wortprobe
dieser Hand". (K) Alle Wortproben · ⚑ Wort markieren · Schreiben.

**Befund:** Obwohl die Wortprobe `unter` in der Liste mit Crop steht, zeigt
das Detail ohne `word_instance` weder Crop noch Editor-Einstieg — eine Probe
ohne Spur ist im Detail unsichtbar (lokal beobachtet; in Prod tragen die
Bench-Wörter Spuren, die Regel gilt trotzdem für jede neue Probe).

### 3.5 Eigenhand

EINE Seite, 2 647 px bei leerem Bestand: (Z) Hand-Auswahl · Stehendes Setup
(Feder · Tinte · Papier · Aufnahmegerät · Bezeichnung · Notiz) · Streifen-
Zähler (belegt · unterwegs · geplant · im Plan · angenommen · verworfen ·
gedruckt) mit Chips der nächsten Streifen · Geschriebene Streifen (Galerie
mit Wortsuche) · Zeichen (fünf Buckets Klein · Groß · Ligaturen · Ziffern ·
Sonderzeichen; Zelle = Glyph + Belegzahl) · Übergänge (744 Chips `x › y`) ·
Bogen drucken · Quoten (nur die gewichteten Quoten werden gerendert). (K)
Setup sichern · nach Befund sortieren · Pfad zeigen · Lineatur ausblenden ·
Zoom ¼ ½ 1:1 2× · nur offene zeigen · Bögen erzeugen — und **vier
kopierbare Terminal-Befehle** (`TerminalCommand`) auf der Seite (`setup
--pull`, `sync --mit-streifen`, `pull --sheet`, `universe --push`); `pfad
--apply` steht nur als Fließtext, `redo` · `report` · `progression` · `gaps`
· `snapshot` tauchen im Browser gar nicht auf.

**Befund:** Die Eigenhand kennt Belegzahlen, aber keine Statistik AUS der
Tinte: keinen Fit je Vorkommen, keinen Median je Buchstabe, keinen Median-
Verbinder je Übergang, keine Laufform der eigenen Hand — das ist Phase 5
([`eigenhand-erfassung.md`](eigenhand-erfassung.md) §9) und dort
ausdrücklich aufgeschoben. Kein Nachfahr-Editor für Streifen, keine Vorschau
„in meiner Hand", kein Maß „folgt der Pfad der Tinte?" außer dem Overlay
selbst und den Befund-Chips je Fassung. Konsole: 404 auf
`/eigenhand/setups/{hand}` vor dem ersten Setup.

### 3.6 Auftragskorb

(Z) Drawer „Auftragskorb (n offen)", je Eintrag Titel (Ebene + Ziel,
verlinkt), Notiz, Zeitstempel. (K) Notiz anlegen · Löschen; am Eintrag die
Rückspiegelung mit „missverstanden", wo sie vorliegt. Keine Filter, keine
Sicht auf `ack` / `done` / `returned` in der Liste, keine Bündelung nach
Stufe, keine Sortierung.

### 3.7 Mobil (390 px)

Kopfleiste auf drei Zeilen (Wordmark + Chip · Nav · „Eigenhand" allein in
Zeile drei). Detailseiten als eine lange Spalte; die 744 Übergangs-Chips
werden zu einer sehr langen Wolke. Kein Tablet- oder Stift-Modus — das
Nachfahren mit dem S-Pen läuft im normalen Desktop-Layout.

### 3.8 Die Reibungspunkte, gereiht

1. **Zwei Scopes in einer Leiste** (Vorlage · Hand), ohne dass die Leiste es
   sagt; der Korb der Vorlage hängt über der Hand-Seite.
2. **Übersichten als Endlos-Listen** (10–20 k px) ohne Status-Filter, ohne
   Arbeitsliste — „was fehlt noch?" ist Scrollarbeit, außer beim
   Nachfahr-Filter der Wörter (W6).
3. **Zwei Welten mit zwei Vokabularen:** Wortprobe · Beleg · Vorkommen
   (Platte) gegen Streifen · Fassung · Befund (Eigenhand) — und keine
   Brücke: nirgends steht dasselbe Wort als Platte UND als Streifen UND wie
   die Engine es schreibt.
4. **Statistik nur für die Platten-Hand;** für die Eigenhand fehlt die Kette
   Fit → Vorkommen → Aggregat vollständig (Phase 5).
5. **Medienbrüche** Terminal ⇄ Browser in der Eigenhand-Schleife: sechs
   Wechsel je Bogen (drucken · scannen · `pull` · `ingest` · Siebung ·
   `apply` · `sync` · Browser · `pull --flecken` · `pfad --apply` ·
   `snapshot`), vier davon als kopierbare Befehle auf der Seite.
6. **Kleinigkeiten mit Wirkung:** 16-px-Overflow, rote 404-Konsolenzeilen für
   erwartete Leerzustände, generischer Tab-Titel, ein Detail ohne Spur zeigt
   keinen Beleg.

## 4 Was schon feststeht

Jede Option in §7–§9 hält die folgenden Regeln ein; wo eine Option sie
sichtbarer macht, sagt sie es, wo sie sie bräche, ist sie keine Option.
Die Quelle steht je Zeile, das Zitat ist wörtlich.

### 4.1 Bindende Regeln, die ein Redesign nicht anfasst

| Regel | Quelle | Wörtlich |
|---|---|---|
| Stufen-Doktrin: manuell nur, wo Ground Truth entsteht; Generiertes (Laufform · Übergangs-Grammatik · Komposition · Landmarken) wird nur bemängelt | [`optimierungs-werkbank.md`](optimierungs-werkbank.md) §3 | „Ein Mangel schärft die Regel für alle Wörter, ein manueller Eingriff repariert genau eine Stelle." |
| Entlastungsregel: der Mensch diagnostiziert die Stufe nicht; der ⚑-Dialog stellt genau EINE Vorsortierfrage | ebd. §4 | „Die Korb-Ebene heißt „wo gesehen", nicht „wo verursacht"" |
| Korb-Protokoll API-erzwungen (`check_transition`); Protokollfelder reisen nur mit ihrem Statuswechsel; `ack` vor `done` | ebd. §5, `api/routers/work_items.py` | „keine Bitte, sondern die Bedingung, unter der die Zeile überhaupt geschrieben wird" |
| Triage-Reihenfolge Tafel-Duktus → Laufform → Klassenregel → Platzierung → Override; Regel-Fix vor Override | ebd. §5.2 | „Ein Override ohne vorherige Regel-Prüfung ist ein Doktrin-Verstoß." |
| Die Sperre ist eine Warnung; `force` setzt nur eine Fläche, die vorher ausdrücklich fragt (heute drei) | ebd. §6 (Autor 2026-09-03) | „Ein Knopf, der nebenbei schreibt, bekommt das Flag nicht." |
| Zeilen-Gate der Laufform (n ≥ 3 oder `?min_occurrences`, Sprung-Ratio); ein Wort-Gewinn ist kein Aufnahmekriterium | ebd. §6 (Autor 2026-08-29) | „Ein Wort-Gewinn am Pixel-Lineal ist KEIN Aufnahmekriterium für eine Zeile" |
| `rebuild` ≠ `apply`: Statistik neu rechnen ist Wartung, Laufform übernehmen ist der eine rendernde Griff — bewusst nicht in den Linsen | ebd. §7 W5 | „angeschaut und reklamiert wird hier, gerechnet und übernommen woanders" |
| Statistik je genau EINER Hand; nie über Hände mitteln; Fremdhände nur zur Anschauung | ebd. §6; [`handmodell-stufenplan.md`](handmodell-stufenplan.md) §5; [`../reference/quellen-und-rechte.md`](../reference/quellen-und-rechte.md) §7 | „Fremdhände werden verglichen, nie verrechnet" |
| Manuelle Beiträge (`authored`-Spuren, Overrides) gehen nie in die eingefrorenen Metrik-Referenzen | ebd. §6; [`../reference/qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md) §2 | „die Messlatte bleibt die Platte" |
| Paar-Statistik ist nur Anschauung; kein `apply` für Paare; nur `approved`-Overrides erreichen den Composer | `api/routers/aggregates.py`, `core/database/models.py` | „a median join written back into the writing path would be exactly the bigram database architektur.md §2 rejected" |
| Landmarken: generiert, ein Griff (⚑), Ortsangabe optional, Schwellen sind Mess-Provenienz | [`optimierungs-werkbank.md`](optimierungs-werkbank.md) §8 | „Nichts zu zeigen hieße zu behaupten, der Buchstabe habe keinen Kringel." |
| Jede Ebene nimmt frei eingetippte Ziele an; das Subjekt steht in der URL | ebd. Status-Block; [`../reference/frontend-stack.md`](../reference/frontend-stack.md) §2 | „muss trotzdem richtig aussehen und bemängelbar sein" |
| W3/W6: ein Item ohne `replace`; Züge nie teilen oder umordnen; „unvollständig" ist Daten, nicht Klick; Rechteck-Ecken sind Bench-Fixtures | ebd. §7 | „ein anderes Rechteck wäre ein Re-Baseline des Wort-Benchs" |
| Ehrliche Leerzustände: eine fehlende Messung wird nie als Null gezeigt | [`../reference/frontend-stack.md`](../reference/frontend-stack.md) §7 | „an absent measurement is never printed as a measured zero" |
| Open-Core: jeder Read, der den Bestand trägt, ist admin-gegatet und `private, no-store`; die Trennlinie ist getestet | [`../reference/quellen-und-rechte.md`](../reference/quellen-und-rechte.md) §5; `tests/test_api_public_surface.py` | „Jeder API-Read, der den Bestand trägt, ist admin-gegatet" |
| Eigenhand: Buchführung und Streifen-PNG in der DB, nie im Repo; das Archiv bleibt Master; Streifen-Pfad wird außerhalb gerechnet und öffnet Phase 5 nicht | [`eigenhand-erfassung.md`](eigenhand-erfassung.md) §7.1/§7.2/§7.5/§8 | „eine Ableitung wird oben abgelegt, nicht oben erzeugt" |
| Befund: nichts verwirft automatisch; gemessen wird gespeichert, beurteilt wird abgeleitet; Duktus-Treue schlägt Glätte | ebd. §7.3; `core/eigenhand/befund.py` | „Der Haken bleibt das Urteil." |
| Kein DB-Schreibpfad in `tools/`; `core`/`api`/`alembic` importieren nie `tools` | ebd. §12; `tests/test_imports.py` | „nie über eine Verbindung zur Datenbank" |
| Drei Rollen: Tafel = Formbasis, Platte = Maßstab, Eigenhand = Auslieferung; der Wechsel ist eine erklärte Re-Baseline, kein Nebeneffekt | [`../concepts/vision.md`](../concepts/vision.md) „Drei Rollen" (2026-09-07) | „Sie sind Maßstab, nicht Auslieferung" |
| Design-System auch im Admin: Typo-Leiter, HeaderBar, Caption ≥ 14 px, Fokusring, Trefferflächen ≥ 44 px; Arbeitsflächen weiß, Identität Papier | [`../concepts/design-system.md`](../concepts/design-system.md) | „darf beim Betreten nicht wie eine zweite Anwendung wirken" |
| Sprache: Code Englisch, Docs Deutsch, UI Deutsch nach DIN/Süß | [`../reference/sprachregelung.md`](../reference/sprachregelung.md) §1 | „Englisch, ohne Ausnahme" |
| Archiv-Snapshots: frei anlegen, nie zerstören; der Autor autort im PROD-Admin | `.claude/guardrails.md` (2026-08-08, 2026-07-25) | „create freely, never destroy" |

### 4.2 Verworfen — nie wieder aufmachen

Tablet-/S-Pen-Erfassung als Primärweg der Eigenhand (Federwinkel und Druck
liefert nur die echte Feder, 2026-08-22). Scan-Upload über Admin oder API
(nur die Buchführung wanderte in die DB, 2026-08-23). Streifen-Scans ins
Repo. Flecken beim Einlesen aus dem Crop herausrechnen; den Detektor scharf
stellen statt den Pinsel anzubieten. Den Streifen-Pfad serverseitig rechnen,
in `word_instances` schreiben oder in die Streifen-Liste einbetten. Die
Platte als Auslieferungshand behalten und die Eigenhand nur trainieren
lassen. Gepooltes Mehr-Hand-Vorbild, vollständige Bigram-Datenbank, neue
Stufen vor H0. Flächendeckendes manuelles Paar-Autoring, Freihand als
Erstweg, globaler Slant-Offset. Deutsche Code-Identifier. Und alle
Verworfen-Listen der Metrik bleiben geschlossen.

### 4.3 Die Autor-Entscheide, die den Admin geformt haben

| Datum | Entscheid | Stand |
|---|---|---|
| 2026-07-31 | „nicht immer Screenshot in Paint" — EINE Werkbank und der Korb als `work_items` | umgesetzt (W1–W6, Redesign „aus einem Guss") |
| 2026-07-31 | „In meiner Hand, aber jeden Text" — Vorkommen speichern auf allen drei Ebenen | H0–H2 umgesetzt, H3–H5 offen |
| 2026-08-02 | Issues #270 (Laufform-Apply in der SPA), #271 (veraltete Overrides), #272 (Ernte aus dem Admin), #274 (Kopplungshöhen persistieren) | #270 bis auf die Paarseite geschlossen; #271, #272, #274 offen |
| 2026-08-03 | „`min_n` goes to 1 — better once than never" | teilweise (Apply-Boden 3 bleibt) |
| 2026-08-07 | Manuelle Autorenschritte → Todoist | bindend |
| 2026-08-22 bis 27 | Eigenhand: Wortvorrat, Bögen, Buchführung und Streifen in der DB, Übergangsraum als eine Zeile, Wortsuche als Einstieg, Lineatur ausblendbar | umgesetzt (Phasen 1–4f) |
| 2026-08-29 | Kein Wort-Gewinn als Aufnahmekriterium einer Laufform-Zeile | umgesetzt (Zeilen-Gate) |
| 2026-09-03 | „Die Sperre ist eine Warnung, kein Riegel"; Trefferflächen ≥ 44 px | umgesetzt — außer der `ChartToolbar`, die „Einrichten" bei gesperrter Glyphe noch sperrt |
| 2026-09-07 | Landmarken-Linse; Streifen-Befund („auch nicht perfekte Streifen hochladen"); Fleckenmaske; **Drei Rollen** — die Eigenhand wird die ausgelieferte Hand | umgesetzt (#566, #567, #568); der Umschalt-Akt ist ein eigener späterer Entscheid |
| 2026-09-12 | „auch im admin … den pfad auch sehen"; A45: der Tintenpfad ist der Standard-Folger | umgesetzt (#598, #599) |
| 2026-09-13 | A48: Saat-Korrespondenz als Vorkommens-Quelle ehrlich negativ | Rettungswege offen |

**Die wiederkehrenden Themen** dahinter, aus denen die Leitideen in §5
folgen: (1) sehen, was generiert wurde, statt es zu glauben (Landmarken,
Pfad, Befund, Diagnose); (2) sehen, was noch fehlt, ohne zu scrollen
(Status-Filter, Fehlstellen, Warteschlange); (3) reklamieren statt patchen
(Korb, Klassenregeln); (4) Unfertiges zulassen, mit definierter Schleife
(Befund, `min_n`, Sperre als Warnung); (5) der Weg über die DB
(Buchführung, Streifen, Übergangsraum, Wörterbuch); (6) die eigene Hand als
Ziel — nicht Abstand zur Vorlage, sondern „in meiner Hand, aber jeden Text".

### 4.4 Die Datenlage, auf der jede Option steht

Drei Achsen, zwanzig Tabellen. Je **Stil**: `styles`, `templates` (Schlüssel
`(style, glyph, variant)`; Variante 0 = Tafel, 100 = Laufform),
`glyph_pairs`. Je **Quelle/Vorlage**: `sources`, `bboxes`, `instances`,
`pair_instances`, `word_instances`, `work_items`. Je **Hand**: `hands`
(entsteht nur als get-or-create beim Batch-PUT einer Vorkommensschreibung),
`aggregates`, `pair_aggregates`. Daneben die fünf `eigenhand_*`-Tabellen,
deren `hand` ein freier String ohne Fremdschlüssel auf `hands` ist.

**Für die Eigenhand fehlt heute die ganze Statistik-Kette:** für
`mn-suetterlin` gibt es keine `hands`-Zeile, keine `sources`-Zeile, keine
Vorkommen, keine Aggregate, keine Laufform — weil `sources.chart_path` ein
repo-relativer Pflichtstring ist und gitignorte Streifen das nie sein
können ([`eigenhand-erfassung.md`](eigenhand-erfassung.md) §9/§13:
„Entscheidung vor Phase 5"). Die Ernte (`tools/laufform/harvest.py`,
`tools/pairlab/harvest.py`) läuft nur im Terminal gegen gitignorte Fixtures
und schreibt über die Admin-Batch-PUTs; aus dem Admin ist sie nicht
auslösbar (Issue #272). `/write/*` hängt an `source_id`.

**Welche Zahlen „folgt der Tinte?" heute beantworten:** je Wort
`word_instances.measurements.geo_rmse_px_by_slot`, `fit_path`
(`tintenpfad` | `chain`), `follower` und der Tintenpfad-Block (`runs`,
`paper_lifts`, `jumps`, `hairpins`, `ink_unvisited_share`); je Buchstabe
`instances.measurements.geo_rmse_px`; je Paar `pair_instances.measurements`
(`gen_chamfer`, `harvest_chamfer`, `a_resid`, `b_resid`, `fit_ok`).
Serverseitig der Wordbench-Loss (`/word-samples/{id}/score`) — er misst die
Komposition gegen die Platte, nie die Nachfahrung. Clientseitig das
Abstandsprofil Spur → Engine, ausdrücklich ein Anzeige-Maß. **Nicht** in DB,
API oder SPA: `dtw_xh`, AIoU, LDTW — sie leben nur in
`tools/tracebench/metric.py`. Für die Eigenhand misst der Streifen-Befund
(sechs Felder) Sauberkeit, nicht Pfad-Treue. Böden: `LAUFFORM_MIN_OCCURRENCES
= 3`, `LAUFFORM_SPIKE_RATIO_MAX = 2.95`, Rebuild-`min_n` 4 für Glyphen, 1
für Paare.

## 5 Leitideen, auf die sich das Panel einigt

Was alle sechs Linsen unabhängig voneinander vorschlagen, ist mit hoher
Wahrscheinlichkeit richtig — es folgt aus dem Befund, nicht aus einem
Geschmack. Jede Zeile nennt den Grund. Wo die Kritikrunde einen
„Konsens" als Doktrin-Bewegung entlarvt hat, steht das dabei (Idee 2).

### 5.0 Ein Name je Begriff

Die erste Fassung prägte drei Namen für die Ampel, vier für die
Terminal-Karte und benutzte „Bahn" für die Rollen-Spalte UND die gefolgte
Linie. Ab hier gilt je Begriff genau ein Wort; jeder neue trägt seinen
Glossar-Eintrag (`glossar.md` §5, Vorgabe V3 in §12).

| Begriff | UI-Wort | bedeutet |
|---|---|---|
| **Rolle / Rollen-Spalte** | Tafel · Platte · Eigenhand | die drei Rollen aus `vision.md` als feste Spalten (nie „Bahn", „Fenster", „Stimme") |
| **Bahn** | Bahn | die gefolgte oder nachgefahrene Linie eines Wortes, beidseitig; Herkunfts-Chip „automatisch (Tintenpfad)" / „von Hand" (Q8b) |
| **Streifen-Pfad** | — | Glossar-Name des Datenfelds `eigenhand_strips.pfade`, nie ein UI-Wort |
| **Wortkasten** | Kasten | die Ortsangabe eines Wortes auf dem Streifen (`boxes[]`) |
| **Wortprobe** | Wortprobe | ein geschriebenes Wort, Platte oder Streifen |
| **Beleg** | Beleg | die Zähleinheit des Bestands (angenommene Fassung je Item) — nie ein `word_instances`-Zähler |
| **Tintentreue** | folgt · folgt teils · folgt nicht | die referenzfreie Ampel je Kasten (§6.3); ungemessen = grau mit Grund |
| **Rohzahlen-Chip** | Zahl, kein Urteil | die gespeicherten Sensoren ohne Farbe, ab Phase 0 |
| **Übergabekarte** | — | die zustandsgetriebene Karte für einen lokalen Schritt (Idee 11) |
| **Arbeitsliste** | — | gefilterte, sortierte Übersicht mit Zähler; **Nachfahr-Liste** ist eine davon; **Arbeitsvorrat** die Seite, die sie bündelt (nur Option C) |
| **Bahn-Deckung** | — | Items, bei denen < 3 Kästen eine grüne oder nachgefahrene Bahn tragen; die Mindestbelegung des Bestands bleibt unberührt |
| **Belegleiste** | — | je Buchstabe/Übergang eines Textes die Kästen dieser Hand |
| **Gate-Status** | — | Zeilen-Gate erfüllt? (n · Sprung · Kopf) plus „Zeile fehlt" / „veraltet"; keine Distanzschwelle |
| **Scope-Leiste** | — | die Zeile unter der Kopfleiste, die Vorlage UND Hand benennt (Option A/C) |
| **Ausrüstung** | Ausrüstung | Feder · Tinte · Papier · Gerät (heute „Stehendes Setup"; Q8c) |

Gestrichen: „Tor/Tore 1–7", „Lieferbarkeit" (eine Freigabe-Bedingung, die
`eigenhand-erfassung.md` §2 offen lässt und Q24 dem Autor vorbehält),
„Lokale Schritte", „Wortkiste", „Ertrag", „Hub", „Skip", „Sync" als Label,
„Engine" (die Locale sagt „vom System geschrieben"). Terminal-BEFEHLE
bleiben englisch — sie sind Code.

### 5.1 Die Leitideen

1. **Zwei Scopes, beide sichtbar: Vorlage und Hand.** `source_id` und
   `hand_id` sind getrennte Schlüssel; nur die Kopfleiste verschweigt es
   (§3.8, Punkt 1). Form: Q2. Kopplungsregel als Vorgabe (V19): die aktive
   Hand ist immer eine Hand des Vorlagen-Stils; wechselt die Vorlage den
   Stil, wechselt die Hand auf die zuletzt gewählte Hand dieses Stils oder
   wird leer — nie eine Hand fremden Stils.
2. **Drei Rollen als feste Spalten: Tafel · Platte · Eigenhand.**
   `vision.md` „Drei Rollen" ist die bindende Sprache. **Aber:**
   `optimierungs-werkbank.md` §6 sagt wörtlich „die Werkbank zeigt immer
   genau eine Quelle/Hand". Die Eigenhand auf einer Vorlagen-Fläche zu
   zeigen, bewegt diese Leitplanke — die erste Fassung verkaufte das als
   Konsens. Darum ist es Weichenstellung Q3 mit dem doktrin-konformen
   Standard „strikt eine Hand je Seite"; wird (a) gewählt, steht das
   Proposal-Update in §10.2. Jede Zahl trägt den Namen ihrer Hand; zwei
   Hände sind ein Nebeneinander, nie eine Summe.
3. **Die Brücke zwischen historisch und eigen läuft über Items, nicht über
   Wörter.** Der eingefrorene Streifen-Plan hat 553 Wörter, die Platte 140
   Texte; exakt 24 überschneiden sich (`das`, `und`, `Galoppieren`, `Säbel`,
   `Zügel`, `Soldaten` …). Für 116 von 140 Platten-Wörtern gäbe es keine
   Streifen-Wortprobe, für 529 von 553 Streifen-Wörtern keine Platte. Die
   Brücke ist deshalb die **Belegleiste**: je Buchstabe und Übergang eines
   Textes die Kästen der Hand (`strips?item=`) — in allen Optionen. Ob die
   Referenzwörter (`lesen`, `das`, `denen`, Entwicklungssatz) in den Plan
   gepinnt werden, fragt Q17; das ist ein Repo-Schritt.
4. **Übersichten werden Arbeitslisten — und die kompakte Liste ist die
   Vorgabe.** 10 585 px und 20 088 px Kartenwand (§3.2/§3.4) bleiben sonst
   die erste Erfahrung. Zeile = Glyph/Wort, Chips, Zahlen, KEIN Bild;
   Bilder laden in der aufgeklappten Zeile oder im Detail; Galerie ist der
   Opt-in. Ansicht, Filter, Sortierung und Seite stehen in der URL
   (`?ansicht=liste|galerie&filter=&sort=&seite=`), nicht in localStorage —
   ein Korb-Link auf einem anderen Gerät öffnet sonst wieder die Wand.
5. **„Folgt der Tinte?" liest aus Zahlen, die der Streifen-Pfad HEUTE
   trägt** — `runs · jumps · hairpins · paper_lifts · ink_unvisited_share`
   je Kasten in `pfade[].meta.tintenpfad` (`tools/eigenhand/pfad.py`), die
   „Pfad zeigen" schon lädt. Darum steht in **Phase 0** der
   **Rohzahlen-Chip** je Kasten („Tinte ohne Bahn 21 % · Absetzer 3 ·
   Sprünge 1", Etikett „Zahl, kein Urteil"), die Ampel folgt in Phase 2 an
   derselben Stelle: gemessen wird gezeigt, beurteilt wird später
   (`eigenhand-erfassung.md` §7.3).
6. **Nachfahren auf Streifen ist der Wort-Editor über dem Kasten**, als
   `verfahren: authored` in `eigenhand_strips.pfade`, nie in
   `word_instances` (`eigenhand-erfassung.md` §7.5). **Wann es lohnt:** erst
   mit Q4(a) hat eine nachgefahrene Bahn einen Abnehmer (die Ernte in
   Phase 5 liest sie vor `tintenpfad`); ohne Q4(a) ist es verlorene
   Stifthand. Bis dahin ist die Nachfahr-Liste ein Zähler, keine Aufgabe.
7. **Die Schutzregel „authored wird vom Folger nie ersetzt" fehlt heute auf
   beiden Seiten** (`check_paths` prüft `verfahren` nur als String,
   `_merged` mischt ohne Prüfung). Sie ist Phase 0 (Vorgabe, Zwilling von
   `authored_identities`). Die **Archiv-Regel** dagegen ist eine
   Drei-Werkzeug-Kette (`pull --pfade → snapshot → sync --from`; keines
   kennt `pfade` heute) und bewegt `eigenhand-erfassung.md` §7.5 „der Pfad
   ist ableitbar" — sie gehört zu Q4 und in Phase 2, wo der erste
   nachgefahrene Kasten entsteht.
8. **Ein meta-only Listen-Read je Kasten ist Voraussetzung jeder
   Arbeitsliste** — als Projektion in Python nach `_STRIP_WITHOUT_PNG`
   (`PORTABLE_JSON` ist auf den SQLite-Suiten JSON, keine JSONB-Pfade), ohne
   `strokes` (Vorgabe V5).
9. **Die Eigenhand-Statistik ist zweistufig, an derselben Stelle.** Stufe 1
   bis Phase 5: Belegzahlen, Tintentreue-Verteilung, Ausschnitt-Stapel aus
   `letter_spans` (Bilder), Feder-Halbbreite aus dem Befund. Eine
   Median/MAD-Skizze aus Folger-Bahnen wäre eine zweite Aggregat-Pipeline
   neben H1 (`core/aggregate.py` = Median der FITS) — nur als erklärtes
   Update von `eigenhand-erfassung.md` §7.5 (Q11). Stufe 5 ersetzt Stufe 1
   ohne Umzug.
10. **Frage 6 hängt an zwei Weichen (Q19, Q20).** Verifiziert:
    `apply-laufform` schreibt `(hand.style_id, glyph_key, 100)`; der
    Eigenhand-Apply scheitert heute an `require_hand` (404), überschriebe
    aber mit einer `hands`-Zeile die Platte. Der Guard (Phase 0): Apply nur,
    wenn `hand.id == sources.hand_id` einer Quelle desselben Stils oder der
    Stempel `canonical.derived_from.hand_id` der bestehenden V100-Zeile
    passt; fehlt der Stempel (Altzeilen), ist die Platten-Hand Eignerin. Er
    greift erst mit der Zweithand (V1), kostet aber nichts.
11. **Medienbrüche werden gezeigt, nicht versteckt** — als **Übergabekarte**
    (Titel · Warum mit Doktrin-Grund · Befehl mit Parametern · „Danach hier"
    · Reihenfolge), die verschwindet, sobald der Zustand da ist. Die
    Zwischenablage reicht nicht vom Tablet zum Rechner: der Zwilling ist
    `tools.eigenhand.report --faellig` (Lese-Tool, dieselben Zustandsregeln
    über die API, druckt die fälligen Befehle in Reihenfolge); die Karte
    nennt am Tablet nur diesen Befehl. **Repo-Schritte** (`pool pin`,
    Gewichte) sind Korb-Notizen an die KI-Runde, keine Karte (§10.3).
12. **Kein getesteter Schreibfluss wird umgebaut, nur aufgerufen** (R9,
    Q6); Dialog-Erweiterungen zählen als Umbau. `force` bleibt bei drei
    Flächen; Bestätigung ist nicht `force`.
13. **Phase 0 ist bei allen Optionen dieselbe Liste** (§5.2) — ohne
    Scope-Chips (die kommen nach Q2) und ohne Archiv-Regel (Q4).
14. **Definition of Done jeder Fläche:** jeder neue Read `require_admin` +
    `private, no-store` + RESERVED in `tests/test_api_public_surface.py`;
    jede Arbeitsliste verlinkt nur und löst nie einen Statuswechsel aus;
    Tastatur-Durchgang und Deuteranopie-Simulation je Overlay-Fläche in
    `/verify-frontend`; die pinnende Testdatei steht im PR
    (`test_api_eigenhand.py` für Pfade, `test_api_admin_writes.py` für
    Laufform und `/write/word`).
15. **Ein Name je Begriff** — §5.0.
16. **Der Rollenwechsel bleibt außerhalb des Admins.** Der Admin zeigt die
    zwei doktrinierten Zahlen (Mindestbelegung ≥ 3 je Glyphe, gewichtete
    Erstbeleg-Quote) und den gemessenen Ampel-Anteil, keine Marke, kein
    Schalter (Q24).
17. **Drei Geräte, drei Stufen.** Handy ≤ 600 px (Korb, Ampeln, ⚑ — der
    Auftrag kam vom Handy) · Tablet 600–1200 px hoch und quer (das Gerät,
    an dem der Autor nachfährt; heute kennen nur `SetupWizard` und
    `DiagnosticDialog` den `md`-Bruch) · Schreibtisch ≥ 1200. Rollen-Spalten
    auf dem Tablet = zwei + Tab; Filterzeilen sind EINE scroll-snappende
    Chip-Reihe mit 44-px-Zielen. Stift-Regel je Canvas: Werkzeuge oben,
    `touch-action: none`, Hover = Reichweite, Zwei-Finger = Pan (der
    Wort-Editor hält das schon).
18. **Tastatur.** Listen als Roving-Tabindex (eine Zeile = ein Stopp,
    Pfeile innerhalb); ‹ › im Subjekt-Kopf an Alt+←/→ in allen Optionen;
    Kurztasten nur bei Fokus in der Liste, nie in Eingabefeldern,
    abschaltbar (WCAG 2.1.4); jeder Chip, der öffnet, ist ein `ButtonBase`
    mit Fokusring. Einzelbuchstaben-Kurztasten (`n/p`, `j/k`) sind keine
    Spezifikation mehr.
19. **Farbe und Fläche.** Keine Rolle bekommt Viridian — es ist Akzent,
    `success` und Fokusring zugleich. Rollen-Linien trennt die
    **Strichart** (Tafel durchgezogen · Platte gestrichelt · Eigenhand
    gepunktet) plus Etikett; Farben aus dem Perioden-Set als Tokens
    `paper.role.*`. Die Overlay-Ebenen (#00b37e/#e02030/#2f6fd0 fest
    verdrahtet in sieben Dateien, ein Rot/Grün-Paar) bekommen in Phase 0
    Tokens `paper.layer.*`, farbenblind-sicher, je Ebene eine Strichart,
    Legende mit Text; dazu ein `mono`-Token (17 px). Flächenregel: alles
    mit Scan, Crop, Overlay oder Skizze ist weiß; Text-/Zahlen-Karten
    `paper.hi` mit Haarlinie; Editor-Canvas dunkel. Kein
    entscheidungstragender Zustand lebt nur im Hover — Text oder `InfoHint`
    statt `Tooltip`. `type-floor` und `touch-targets` laufen auch gegen
    Admin-Routen.
20. **Kopfleiste: höchstens vier Bereichs-Links.** `design-system.md` §7
    kennt EINE Leiste für öffentliche Seiten und Werkbank; eine Bottom-Nav
    wäre eine zweite Chrome und braucht einen §7-Nachtrag (V15).

### 5.2 Phase 0 — die eine Liste (alle Optionen, ≈ zwei Wochen)

16-px-Overflow (`minmax(0,1fr)`) · Tab-Titel · erwartete 404 stumm (`GET
/sources/{id}/pairs` und `GET /eigenhand/setups` existieren als Listen) ·
Wort-Detail zeigt die Probe auch ohne `word_instance` · Korb-Drawer mit
Status-Filtern · **Rohzahlen-Chip** je Kasten · **Apply-Guard** (+ `UPDATE
sources.hand_id`: Daten, kein DDL, aber Prod-berührend → Rückfrage; Test
mit gesäter Zweithand) · **authored-Regel** Server (409) + Tool-Merge + Test
· Ebenen- und `mono`-Token · Rollen-Etikett + Position + Strichart als
Darstellungsregel. Realistisch 8–10 Arbeitstage.

**Phasenleiter** (gilt für §6–§12): **0** Reparaturen + Regeln · **1**
Scope + Arbeitslisten · **2** Tintentreue + Nachfahren · **3**
Rollen-Spalten + Statistik Stufe 1 · **4** C-Bausteine auf A (Cockpit,
`?liste=`, Arbeitsvorrat, Korb-Seite) · **5** Produktionshand (Q19/Q20:
Streifen-Quelle, Ernte, Aggregate, Laufform je Hand, Hand-Vorschau).

## 6 Die Eigenhand-Statistik — eine Spezifikation für alle Optionen

Status-Kürzel: **EXISTS** (Feld und Route da) · **DERIVABLE** (aus
vorhandenen Daten ohne Migration; ggf. Tool-Schritt oder Router-Zeile) ·
**MISSING** (Tabelle, Route, Format oder Entscheid fehlt). Jede Zeile wurde
in der Kritikrunde gegen `api/`, `core/`, `alembic/`, `tools/` und
`app/src/lib/api/` geprüft; die Korrekturen der ersten Fassung stehen in
§6.7.

### 6.1 Je Buchstabe

| Zahl | Quelle | Status |
|---|---|---|
| Belege angenommen / geplant; Mindestbelegung ≥ 3 als Ampel | `GET /eigenhand/bestand/{hand}` → `glyphs[bucket].keys[].belege/planned` | EXISTS |
| Kästen mit Bahn, in denen die Glyphe einen `letter_span` hat; davon von Hand | `pfade[].meta.letter_spans` × `verfahren` | DERIVABLE (meta-only Read, §6.7) — für nachgefahrene Bahnen erst nach Q15 |
| Tintentreue-Verteilung der tragenden Kästen | Ampel-Regel über `meta.tintenpfad` | DERIVABLE (Regel MISSING, §6.3) |
| Ausschnitt-Stapel aus Streifen (Bilder) | Span-x-Bereich × `registration_px` × `rect_px` → Client-Clip auf dem Wort-Crop | DERIVABLE |
| Feder-Halbbreite der Hand in xh (Median) | `befund.nib` je Fassung; je Buchstabe über die Fassungen seiner Belege | EXISTS / DERIVABLE |
| Kringel-Zustand je Schleife gegen den Katalog | `befund.kringel` EXISTS; `measure_strip` liefert `woerter[]`, `EigenhandBefundOut` trägt es nicht | DERIVABLE (Router + Schema) |
| Stufe 1 (nur mit Q11a): Breite/Höhe des Spans in xh, Schräglage, Median + MAD | `core/eigenhand/statistik.py` + `GET /eigenhand/statistik/{hand}` | MISSING — Update von `eigenhand-erfassung.md` §7.5 |
| Stufe 5: Median-Anker + MAD-Hülle, `n_instances`, RMSE, `laufform_dev_xh`, Gate-Kaskade | `GET /hands/{hand}/aggregates` (Route EXISTS); keine `hands`-Zeile, keine `instances` für `mn-suetterlin` | MISSING (Phase 5) |
| Zeilen-Gate-Chips (n ≥ 3 · Sprung ≤ 2,95 · Kopf ≤ 15°) | `core/laufform.py::spike_gate/head_gate` EXISTS; `AggregateOut` trägt sie nicht; der Read lädt `chart_by_key` schon | DERIVABLE (Router + Schema) |

Statistik-Einheit ist die Hand — mit Kohorten-Facette und Warn-Chip
„gemischte Federn", weil `EigenhandHand` einen Ausrüstungswechsel
ausdrücklich als unvergleichbare Kohorte führt (`core/database/models.py`);
Q16.

### 6.2 Je Übergang

| Zahl | Quelle | Status |
|---|---|---|
| Belege / geplant je Item `x›y`, gewichtetes Soll, Erstbeleg-/Ausbau-Quote | `bestand.joins.rows`, `bestand.quoten` | EXISTS |
| „in einem Zug": Anteil Kästen ohne `paper_lift` zwischen den Spans | Zug-Grenzen der `strokes` | DERIVABLE |
| Verbinderstück je Kasten: Länge, Winkel, Koppelhöhe | **`letter_spans` enthalten keine Verbinder-Abschnitte** — `spans_of` gibt jedem Verbinder-Sample das Label des nächsten Buchstabens (`tools/pairlab/tintenpfad.py`), also `span[l].last + 1 == span[r].first` | **MISSING** — braucht PFAD_FORMAT 2 mit Roh-Labels oder `connector_spans` je Zug; die ganze Übergangs-Stufe-1 hängt hinter dem Formatwechsel (Phase 3 ← Phase 2) |
| Tintentreue der tragenden Kästen | wie §6.1 | DERIVABLE |
| Stufe 5: Median-Connector + MAD, `offset_center`, `gen_chamfer`/`doff`/`dconn` | `GET /hands/{hand}/pair-aggregates` (Route EXISTS), `pair_instances` der Hand fehlen | MISSING |
| Übersteuerung vorhanden — und für welche Hand | `GET /sources/{id}/pairs` (Liste, EXISTS); `glyph_pairs` ist je `(style_id, left, right, variant)` gekeyt, ohne Hand | EXISTS / Hand-Bezug MISSING (Q23) |

Kein `apply` für Paare: H2 ist lesend (`architektur.md` §2). Die Zahlen
begründen Klassenregel-Aufträge im Korb.

### 6.3 Tintentreue — „folgt der Tinte?"

Je Kasten eine Ampel aus **referenzfreien** Sensoren — ein Streifen hat per
Doktrin keine Referenzspur (`eigenhand-erfassung.md` §12, Prüfstein 2),
also scheiden `dtw_xh`, Chamfer, LDTW aus. Gerechnet wird lokal in
`tools.eigenhand.pfad` beim Folgen (`api`↛`tools`,
`tests/test_imports.py`), abgelegt in `pfade[].meta.tintenpfad`; der Server
leitet beim Lesen ab (`core/eigenhand/tintentreue.py`, reine Funktion,
Schwellen als Konstanten je Hand mit Datum, damit SPA und Bestand dieselbe
Ampel lesen).

| # | Sensor | Herkunft | Status |
|---|---|---|---|
| 1 | `ink_unvisited_share` — Anteil des Tintenskeletts, den die Bahn nie befährt | `meta.tintenpfad` | EXISTS |
| 2 | Absetzer gegen Soll: `paper_lifts` + 1 gegen `body_runs_expected(word)` (`core/eigenhand/befund.py`) plus Markenzüge der Tafel-Zeile | Zähler EXISTS, Soll aus core | DERIVABLE |
| 3 | `jumps`, `hairpins` | `meta.tintenpfad` | EXISTS |
| 4 | Papier-Exkursion: max Abstand Bahn → eigene Tintenmaske in xh | **neu im Tool** — `tools/tracebench/excursions.py` misst gegen die Referenz und ist für Streifen ungeeignet | MISSING (eigene Vorregistrierung; 0,35 xh nur Startwert) |
| 5 | AIoU der gerasterten Bahn gegen die Tintenmaske | `tools/tracebench/metric.py::aiou` (null Projekt-Importe), im Tool ins meta | DERIVABLE; Absolutschwellen neu (`k0eval` kennt nur das Delta-Gate) |
| 6 | Struktur-Soll-Abstand | `ductus_soll` liest Fixture-Fälle, für Streifen nicht anwendbar | offen — Q9 |

Sensor 2 und das Befund-Feld `duktus` messen dasselbe — Körper-Züge gegen
Soll —, einmal auf der Tinte, einmal auf der Bahn. Beschriftung: „Absetzer
(Tinte)" im Befund, „Absetzer (Bahn)" in der Tintentreue; nie zwei Namen für
einen Defekt.

**Regel:** der schlechteste Sensor entscheidet (wie `_summarise` im Befund),
kein gewichtetes Maß. Fassungs-Ampel = schlechtester Kasten;
Buchstaben-/Übergangs-Ampel = Anteile über die tragenden Kästen.

**Startwerte** (vorregistriert, §14-Eintrag im Messjournal vor dem ersten
Streifen): grün = unvisited ≤ 0,05 ∧ Absetzer = Soll ∧ Exkursion ≤ 0,20 xh
∧ AIoU ≥ 0,75; gelb = unvisited ≤ 0,15 ∨ Absetzer ±1 ∨ Exkursion ≤ 0,35 xh
∨ AIoU ≥ 0,65; rot darüber. Anker: 0,096 (`kann`, Tinten-Brücken-Runde),
0,35 xh (K-D-Schließung), 0,7929 (dev-19-AIoU-Median, `sep12`). Alle an
der Platte (30–35 px xh) kalibriert, Streifen liegen bei 300 dpi — Etikett
„vorläufig" bis Q10; nach Q10(b) sind sie an DIESER Hand kalibriert und für
jede weitere Hand neu vorzuregistrieren.

**Zustände:** genau drei GEMESSENE Stufen (folgt · folgt teils · folgt
nicht; Theme `success`/`warning`/`error`, Text als zweiter Träger) und EIN
ungemessener grauer Zustand mit Grund im Text: „noch nicht gefolgt"
(`pfade: null`) · „Folger fand nichts" (`pfade: []`, steht in der
Nachfahr-Liste) · „Maske geändert" (`flecken_n` ≠ Maske) · „übersprungen:
unautoriert <keys> / aufgegeben" (heute KEIN Eintrag — `pfad.py` schreibt
`continue` → PFAD_FORMAT 2 mit Skip-Einträgen) · „Format 1 — unvollständig
gemessen". „von Hand" ist ein **Herkunfts-Chip**, nie eine Ampelfarbe:
nachgefahrene Bahnen misst das Werkzeug beim nächsten Lauf nach (`pfad
--messen`, Sensoren 1/3/4/5 sind referenzfrei) und sie tragen dann dieselbe
Ampel (V21); bis dahin zwei Zähler „k grün (gemessen)" · „j von Hand
(ungemessen)".

**Formatwechsel** PFAD_FORMAT 2 ist ein Lockstep-Deploy: `write_pfade`
antwortet 409 bei Formatdifferenz, der Autor pusht gegen die deployte API.
Zwei Releases: API liest 1 und 2, dann schreibt das Tool 2.

**Absprung:** Chip → Kasten mit Bahn-Overlay (`PathOverlay`, EXISTS);
darunter „Tintenabdeckung entlang der Bahn" (Serverroute aus Bild + Bahn,
MISSING, optional); rot trägt „Nachfahren", gelb „Neu folgen"
(Übergabekarte). Die Ampel liest keine Bench-Zahl und speist keine.

### 6.4 Nachfahr-Triage

**Wann.** Nachfahren auf Streifen hat vor Q4(a) und Phase 5 keinen
Abnehmer: die Ernte läuft gegen Fixtures (Issue #272), `pfad.py` schreibt
nur `verfahren`. Antwort auf Frage 4 heute: **nein**. Ab Phase 5: die roten
Kästen, nach Bahn-Deckung. Mit Q4(a) lohnt es schon vorher, weil die Ernte
das Archivierte später liest.

**Qualifiziert:** jede ANGENOMMENE Fassung ∧ Kasten mit Ampel rot ∨ „Folger
fand nichts". Der Befund-Vorschlag („neu schreiben") ist ein Chip neben dem
Kasten und höchstens ein Sortierschlüssel, nie ein Ausschluss —
`eigenhand-erfassung.md` §7.3 Regel 1 wörtlich: „Nichts verwirft
automatisch. Der Haken bleibt das Urteil"; aus den Trainingsdaten nimmt eine
Fassung nur `redo --retire`. Die Übergabekarte „neu schreiben" steht
PARALLEL zur Nachfahr-Zeile.

**Umgeleitet:** „übersprungen: unautoriert" ist keine Beschwerde über
Generiertes, sondern eine Ground-Truth-Lücke (Stufen-Doktrin: den
Tafel-Duktus liefert der Mensch) → Absprung `/admin/buchstaben?g=<key>` →
Einrichten, in eigener Arbeitsliste „Tafel fehlt" neben der Nachfahr-Liste;
kein Korb-Eintrag (V9). „Maske geändert" → erst `pfad --apply`. Kasten ohne
`rect_px` → „Bogen vor der Schnitt-Geometrie", nie machbar. Gelb wird nicht
nachgefahren (Q12).

**Reihenfolge:** Schwere (rot > Folger fand nichts) → **Bahn-Deckung** (Zahl
der Items des Kastens, bei denen < 3 Kästen eine grüne oder nachgefahrene
Bahn tragen — die Mindestbelegung des Bestands bleibt davon unberührt) →
Übergangsraum-Gewicht → Streifen-Nummer; Q13. Bahn-Deckung braucht
`letter_spans` je Kasten, also auf nachgefahrenen Bahnen Q15.

**Editor:** `WordTraceEditorDialog`, heute an `row: WordInstanceOut`,
`sample`, `sourceId` gebunden UND an `getHand()` gegen `/hands/{id}` —
`mn-suetterlin` hat keine `hands`-Zeile, das Speichern bliebe gesperrt. Der
Adapter braucht Props `hand: {id, resolved}` oder V1, dazu den fehlenden
Wrapper `putEigenhandPfade` (+ `types.ts`). Unterlage `GET
/eigenhand/strips/{hand}/{strip}/{fassung}`, Rahmen aus `registration_px` −
`rect_px`, Saat = gespeicherte Bahn, jeder Absetzer ein Zug. **Prüfstein 7
sichtbar:** die Absetzer-Zahl des Tafel-Duktus (`body_runs_expected` +
Markenzüge) steht als Soll neben der Bahn, Warnung bei Abweichung — sonst
liefert Nachfahren still eine neue Strichreihenfolge per Bild. Keine
Stift-Telemetrie im Format (Verwurf 2026-08-22).

**Speichern:** `PATCH …/pfade/{box}` je Kasten. `eigenhand_strips` hat kein
`updated_at` (nur `created_at`, `erzeugt_am` ist ein Datum) → Content-ETag
(sha256 über `pfade`) im GET, `If-Match` im PATCH, 412 bei Konflikt — ohne
Migration (V20). Der Vollersatz `PUT …/pfade` bleibt dem Tool. Tool-Push
über einen `authored`-Kasten → 409, Überschreiben nur mit ausdrücklichem
Terminal-Flag; keine vierte force-Fläche (Q4). Archiv: Q4, Phase 2.

### 6.5 Ableitungen — „Drei Rollen"

Auf Buchstabe und Übergang EIN Skizzen-Rahmen (`AggregateSketch` EXISTS):
Tafel-Form V0 (EXISTS) · Platten-Laufform V100 + Aggregat-Median mit
MAD-Kreisen (EXISTS, `GET /hands/suetterlin-1922-norm/aggregates`) ·
Eigenhand: Stufe 1 der Ausschnitt-Stapel (Bilder, „n = …"), Stufe 5 der
Aggregat-Median mit Hülle plus die Eigenhand-Laufform (MISSING, Q19/Q20).
**Vorgabe Nebeneinander**, Überlagern nur auf Klick; die Vergleichshand
eingeklappt mit Etikett + n (Q3). Differenzzahlen nur INNERHALB einer Hand
(Median ↔ eigene Laufform); zwischen Händen nur Bilder mit beiden
Etiketten. Keine Whisker unter n = 3, kein ± ohne MAD. Strichart statt
Farbe (§5.1, Idee 19). Die Abb.-22-Schülerhand ist „Kontext, nie Vorbild"
(`handmodell-stufenplan.md` §2): ihre Proben tragen ein eigenes
Rollen-Etikett „andere Hand" und sind aus den Platten-Statistikblöcken
ausgeschlossen (heute nur die `handsMixed`-Warnzeile) — V4.

### 6.6 „In meiner Hand" — Vorschau der Produktionshand

Auf `/admin/woerter?w=<text>` drei Zeilen desselben Textes: Tafel (V0,
Laufform aus) · Platte (V0 + V100 = was die Seite heute schreibt) ·
Eigenhand. MISSING: (a) eine **eigene reservierte Route**
`GET /hands/{hand_id}/write/word` unter `require_admin`, in RESERVED gepinnt
— `/write/word` bleibt parameterfrei, denn der Public-Surface-Test
klassifiziert je ROUTE und ein admin-gegateter Query-Parameter auf einer
öffentlichen Route wäre weder pinnbar noch `private, no-store` (Q22); (b)
`laufform=none` für die Tafel-Zeile; (c) Laufform-Zeilen JE HAND (Q19); (d)
die Laufform-Auswahl in `compose_word_payload` (`repo.get_many(…,
variant=LAUFFORM_VARIANT)`) je Hand — der Payload-Memo ist je Template-Zeile
gekeyt und damit schon hand-sicher (`api/rendering.py`; nur
`_nib_cache`/`_pen_cache` keyen auf `(style, source)`); das reale
Veraltungsrisiko ist die öffentliche `Cache-Control` der `/write`-Antwort am
Rand. Je Slot ein Lücken-Chip „K: Tafel-Rückfall (n = 2)" aus `shaping` ×
Bestand × Aggregat-Keys (DERIVABLE). **Bis dahin ehrlich:** die Zeile
„Eigenhand" zeigt Belegleiste und echte Kästen, nie eine umbeschriftete
Platten-Laufform und keine „Skizze" aus Medianen (`vision.md`).

### 6.7 Was dafür fehlt — konsolidiert, mit Größe

| Stück | Wo | Größe · Phase |
|---|---|---|
| Apply-Guard mit Eigner-Regel + `UPDATE sources.hand_id` (Daten) + Test mit gesäter Zweithand | `api/routers/aggregates.py`, Seed | S · 0 |
| authored-Regel Server (409) + Tool-Merge um `authored` + Test | `write_pfade`, `pfad.py::_merged`, `tests/test_api_eigenhand.py` | S · 0 |
| Rohzahlen-Chip aus geladenem `pfade[].meta` | `StripsPanel` | S · 0 |
| Ebenen-Tokens `paper.layer.*`, Rollen-Tokens, `mono` | `styles/paper.ts`, `design-system.md` §2/§7 | S · 0 |
| Meta-only Read `GET /eigenhand/pfade/{hand}[?nur=offen]` — Python-Projektion, ohne `strokes`, RESERVED | API + `_STRIP_WITHOUT_PNG` | S · 2 |
| PFAD_FORMAT 2: Sensor 4 (neu), 5, Roh-Labels/`connector_spans`, Absetzer-Soll, Skip-Einträge; Lockstep in zwei Releases | `tools/eigenhand/pfad.py`, `core/eigenhand/pfad.py` | M · 2 |
| `core/eigenhand/tintentreue.py` — Ampel-Regel, Konstanten je Hand + Datum; §14-Eintrag; Glossar | core + docs | S · 2 |
| `PATCH …/pfade/{box}` + ETag/`If-Match`; `putEigenhandPfade` + `types.ts` | API + SPA | S · 2 |
| Editor-Adapter (Props-Naht für Hand, Absetzer-Soll) | `WordTraceEditorDialog` | M · 2 (← V1 oder Props) |
| Archiv-Regel für authored-Pfade: `pull --pfade → snapshot → sync --from`, Formatversion, Prüfung nach `eigenhand-erfassung.md` §8.1 | drei Werkzeuge | M · 2 (← Q4) |
| Router-Zeilen: `EigenhandBefundOut.woerter`, `AggregateOut.spike_ratio/head_deviation/gate_ok`, Ausrüstungswerte in `EigenhandStripOut` (Join über die Kartei) | `api/routers/*`, `api/schemas.py` | S · 3 |
| `core/eigenhand/statistik.py` + Read (nur mit Q11a) | core + API | M · 3 |
| `tools.eigenhand.report --faellig` | tools | S · 1 |
| Phase 5/1: Streifen-Quelle (Q20) — `sources.kind='eigenhand'`, `chart_path`-Sentinel (`require_source` prüft ihn nicht), nie Tafel | Migration + `/verify-migrations` + Snapshot | M · 5 |
| Phase 5/2: `instances`-Key `(source_id, specimen_id, slot, variant)` statt Pixel-Ort (`uq_instance_loc`) | Migration | M · 5 |
| Phase 5/3: `tools/eigenhand/ernte.py` — die Ernte ist fixture-gebunden (`iter_fixture_word_cases`, `WordCase` mit templates, laufform, crop, rect, Lineatur) und muss alles aus `/eigenhand/strips/…?box=&lineatur=ohne`, `registration_px` und `/write/glyphs` neu zusammensetzen; authored vor tintenpfad; dann `rebuild` (`_upsert_hand` legt die `hands`-Zeile an) | tools | L (4–6 Wochen) · 5 |
| Exporter-Filter + Test `kind='eigenhand'` nie in Fixture-Wurzeln — an `tools/dbsnapshot/fetch.py` und am Fixture-Builder | tools, tests | S · 5, VOR der ersten Ernte |
| Laufform je Hand (Q19) + Hand-Vorschau-Route, `laufform=none`, Cache-Control, `write-api.md`, Gate-Test | `write.py`, hands, docs | L · 5 |
| `work_items.hand_id` + `hands.kind` (DDL); `specimen_kind='strip'` ist nur Pydantic/TS-Literal (`String(16)` ohne CHECK); `hands.source_id` entfällt — `sources.hand_id` existiert seit `0004` | Migration / Schema | S · 3 (V1, V7) |

**Aufwand mit Kette** (Vermutung, nicht Messung): Phase 0 ≈ 2 Wochen · 1
≈ 2–3 (Split von `EigenhandView` 502 + `StripsPanel` 1073 Zeilen, drei
Übersichten mit URL-Zustand) · 2 ≈ 4–5 (Lockstep-Release, §14, Read,
Adapter, PATCH) · 3 ≈ 2–3 (Übergänge ← Roh-Labels aus 2) · 5 ≈ 8–12 (Q19/Q20
→ Migrationen → `ernte.py` → Aggregate → Vorschau). Gegenprobe: Phasen 1–4
der Eigenhand-Erfassung dauerten drei Wochen (2026-08-22 → 09-12); Phase 5
hat mit `ernte.py` eine größere Fläche. Backend (Phase 5) und SPA (1–3)
berühren sich kaum und können parallel laufen (Q5).

Korrigierte Fehllesungen der ersten Fassung: `/write/word?provenance=1`
gibt es nicht; `EigenhandArchiveOut` hat kein `missing_images` (aus
`png_sha256` gegen `strips` ableitbar); der Render-Memo keyt je
Template-Zeile; `specimen_kind='strip'` ist keine Migration; `strips?item=`
paginiert nicht und leitet je Aufruf die ganze Hand ab — EIN Listen-Read je
Hand im `WorkbenchData`-Cache, Item-Filter im Client; `min_n` der
Rebuild-Route ist 1, der Core-Default 4 wird von keiner Route benutzt.

## 7 Option A — Evolution

**Leitidee.** Nicht neu bauen. Die vier Ansichten und der Korb bleiben und
bekommen, was reine Sicht-Arbeit ist: eine Scope-Leiste, die auf jeder Seite
sagt, ob Vorlage oder Hand das Subjekt ist; kompakte Arbeitslisten als
Vorgabe; Rohzahlen-Chips ab Phase 0, Tintentreue ab Phase 2; die
Nachfahr-Liste als Filter; der Streifen-Editor als Adapter des Dialogs;
in jedem Detail eine Rollen-Spalte Eigenhand — eingeklappt, bis Q3
entschieden ist. Frage 6 wird als beschriftete Leerfläche beantwortet.

**Warum.** Die Schreibflüsse der Werkbank pinnen
`tests/test_api_admin_writes.py` und `/verify-frontend` — jede Fläche, die
sie aufruft, erbt die Tests. Der Scope-Bruch ist ein Beschriftungsfehler.
Kein Nutzen wartet auf eine Migration. Praxis dahinter: Progressive
Enhancement; eine Kontextleiste, die immer sichtbar bleibt (wie in Grafana
oder der GCP-Konsole), statt eines Umschalters.

### 7.1 Was — IA und Routen

Routen unverändert; `/admin/eigenhand?ansicht=bestand|streifen|statistik|drucken`
(V2), überall `?ansicht=liste|galerie&filter=&sort=&seite=`. Scope-Leiste
unter der Kopfleiste: „Vorlage: Sütterlin · suetterlin-1922" · „Hand:
mn-suetterlin", aktives Feld hervorgehoben; sie schaltet NICHT um. Korb
bleibt Vorlagen-Scope; das Badge sagt es sichtbar („⚑ 3 · Vorlage
Sütterlin"), nicht im Hover. ⚑ auf einen Kasten legt `kind=word` +
`specimen_kind='strip'`, `specimen_id='S0041/F02#2'` ab (V7; `note` umginge
das `stage`-Pflichtfeld); `workItemUrl` löst das Muster nach
`?ansicht=streifen&strip=&fassung=&box=` auf.

### 7.2 Flächen

**Scope-Leiste** — Wordmark · Nav (4 Links) · ⚑ | Zeile mit zwei Feldern;
Tablet einzeilig; Handy zwei Zeilen mit Scroll-Snap. Vorlage aus
`AdminContext` (EXISTS), Hand aus `GET /eigenhand/hands` + `/setups`
(Liste, EXISTS), Kopplung Hand↔Stil DERIVABLE. Beide Felder sind Links
(`/admin` · `?ansicht=bestand`), sie schreiben nichts.

**Buchstaben-Übersicht** — Toolbar: Buchstabe wählen · Sortierung
Alphabet/Schlechteste · Filter-Chips gesperrt · ohne Laufform · ohne
Vorkommen · Korb-Auftrag · Umschalter Liste/Galerie. Vorgabe **Liste**: 63
Zeilen auf einen Schirm (Glyph, Güte, Abzüge, Chips), Bilder in der
aufgeklappten Zeile. KEINE Eigenhand-Spalte hier — die Übersicht ist eine
Vorlagen-Arbeitsliste; die Eigenhand-Arbeitsliste liegt unter
`?ansicht=streifen`.

| Information / Knopf | Quelle / Wirkung | Status / schreibt |
|---|---|---|
| Güte, Abzüge, gesperrt, Laufform, Vorkommen n | `WorkbenchData` | EXISTS |
| offene Korb-Aufträge je Buchstabe | `/work-items` nach `glyph_key` | DERIVABLE |
| Filter/Sortierung/Ansicht → URL; Öffnen → Detail | — | nichts |
| Alle neu ableiten … | Bulk-Dialog wie heute (force-Fläche 3) | `POST /templates/{key}/resample` je Glyphe · Rückfrage ja |

**Buchstaben-Detail** — Kopf · Tafel-Ausschnitt (Einrichten · Diagnose ·
Tafel öffnen) · Wie es geschrieben wird · **Rollen-Spalten** Tafel | Platte
(V100 + Median + n, Hand benannt) | Eigenhand (eingeklappt bis Q3: Etikett +
Belege n/m; aufgeklappt: Ausschnitt-Stapel „n = …", drei jüngste Crops,
Chips Belege · nachgefahren · Tintentreue-Anteile; zwei beschriftete
Leerflächen „Aggregat-Median mn-suetterlin — Phase 5" · „Laufform dieser
Hand — Phase 5") · Vorkommen · Statistik der Platten-Hand · Übergänge ·
Wörter · Fuß: Laufform übernehmen. Tablet: zwei Spalten + Tab.

| Information / Knopf | Quelle / Wirkung | Status / schreibt |
|---|---|---|
| Tafel-Form, Laufform, Aggregat + MAD, Gate-Chips | `/templates/{key}`, `/hands/{hand}/aggregates` | EXISTS / DERIVABLE |
| Belege · mit Bahn · von Hand · Ampel-Anteil · Crops | `bestand` + meta-only Read + `strips` (ein Read je Hand) | EXISTS / MISSING (Read) |
| Einrichten (Schloss-Chip, „Trotzdem überschreiben" → `force`) · Diagnose · ⚑ (eine Vorsortierfrage) | unverändert | `POST …/trace` · `…/resample` · `POST work-items` |
| Laufform übernehmen (Fuß) | Dialog unverändert (R9); daneben Übergabekarte `tools.dbsnapshot.fetch` mit Reihenfolge Snapshot → Vorher-Zahl → Übernehmen → Nachher-Zahl; kein Pflichthaken — der Server kann ihn nicht prüfen | `POST …/apply-laufform` · Rückfrage ja |
| Eigenhand-Spalte: Alle Belege / Nachfahren nötig (j) | `?ansicht=streifen&item=&nachfahren=noetig` | nichts |

**Übergänge** — Übersicht: Filter-Chips (mit Übersteuerung · mit Korb · ohne
Vorkommen); je Zelle Zähler statt Farbe (Platte n · Übersteuerung ·
Korb) — Mini-Render nur in der Anker-Ansicht und im Detail. Detail:
unverändert plus Rollen-Spalte Eigenhand (Belege n, Anteil ein Zug, drei
Crops auf den Übergang gezoomt; Verbinder-Maße erst nach dem Formatwechsel;
Leerfläche „pair_aggregates dieser Hand — Phase 5").

Quellen: `/pair-instances`, `GET /sources/{id}/pairs` (Liste, kein
Einzel-404), `/work-items`, `bestand.joins` — EXISTS/DERIVABLE. Knöpfe
unverändert: Paar-Editor → Speichern/Freigegeben (`PUT
/sources/{id}/pairs/{l}/{r}`, die Checkbox ist die bewusste zweite
Handlung, Doktrin-Satz bleibt darüber), ⚑, leiser Neuaufbau.

**Wörter** — Übersicht: Liste als Vorgabe, Korb-Chip je Zeile, Tabs
Wörter · andere Hand (Abb. 22, eigenes Rollen-Etikett) · Nachgefahren.
Detail: System-Schreibung · Platten-Wortprobe (Crop auch OHNE
`word_instance`, Editor-Einstieg) · Woraus es besteht · **Belegleiste** (je
Item die Kästen der Hand, rote Lücke wo keiner) · „In meiner Hand": (a)
Leerfläche „Die Seite schreibt heute mit der Platten-Laufform; eine
Eigenhand-Laufform entsteht mit Phase 5 und Q19" (b) die Kästen desselben
Wortes mit Rohzahlen/Tintentreue (c) sonst „nicht im Plan — ⚑ Pin-Wunsch an
die KI-Runde" (kein Terminal-Befehl: `pool pin` ist ein Repo-Schritt).

Quellen: `/write/word`, `/word-instances`, `/word-samples/{id}/score`,
`strips?item=`/`?wort=` + `…/pfade` (EXISTS); Hand-Vorschau-Route MISSING.
Knöpfe: Nachfahren (Platte) unverändert mit Entwicklungssatz-Warnung (`PUT
/word-instances`); Kasten: Lupe (EXISTS) / Nachfahren (Adapter, `PATCH
…/pfade/{box}` + `If-Match`); ⚑ unverändert.

**Eigenhand** `?ansicht=`. *bestand*: Hand-Auswahl · Ausrüstung · Zähler ·
Zeichen-Buckets (Zelle → Streifen) · Übergänge als Matrix mit Zählern und
Füllmuster (leer · schraffiert · voll) ab `md`, gefilterte Liste „nur
offene, nach Gewicht" darunter · Quoten (gewichtet UND ungewichtet) ·
Übergabekarten in Reihenfolge (pull → ingest → Siebung → apply → sync → pfad
→ snapshot), dazu die eine Zeile `report --faellig`. *streifen*: Wortsuche ·
Item · Sortierung (Befund · Tintentreue · Streifen) · Filter „Nachfahren:
Alle · Nötig · Erledigt · Ohne Bahn" · Zähler „k grün · j von Hand · n
nötig" · je Fassung Befund-Chips + Fleckenpinsel (unverändert), je Kasten
Crop + Overlay + Rohzahlen-Chip/Ampel · Herkunft · „Saat: Tafel-Duktus" ·
„Maske geändert". *statistik*: Stufe-1-Tabellen mit Kopfzeile „aus
Streifen-Bahnen — nicht die H1/H2-Aggregate" (nur mit Q11a; sonst
Belegzahlen + Ampel-Verteilung). *drucken*: Warteschlange, Bögen erzeugen,
PDF, gedruckte Bögen mit Stand.

Quellen: `/eigenhand/*` — alles EXISTS, `zurueckgezogen`, `redo`,
`sheets.last` heute ungezeigt; Sensoren je Kasten in der Liste MISSING
(Phase 2); Ausrüstungswerte je Fassung DERIVABLE (Router-Join). Knöpfe
unverändert: Ausrüstung sichern (`PUT /eigenhand/setups/{hand}`), Bögen
erzeugen (`POST /eigenhand/sheets`), Fleckenpinsel (`PATCH …/flecken`),
Befehl kopieren; neu: Nachfahren je Kasten (`PATCH …/pfade/{box}`,
`authored`), ⚑ Kasten (`kind=word`, `specimen_kind='strip'`). KEIN
annehmen/verwerfen, KEIN Redo-Knopf — der Haken bleibt Urteil, die Kartei
ist die einzige Zustandsquelle.

**Korb (Drawer)**: Filter Status · Ebene · Stufe; Gruppierung nach Stufe;
`returned` oben. Kein menschlicher `done` (422 ohne `stage`/`resolution`);
„missverstanden" bleibt der einzige Rückweg.

### 7.3 Wie — Phasen

| Phase | Inhalt | Größe · hängt an |
|---|---|---|
| 0 | §5.2 | S–M · V1 (Daten-UPDATE mit Rückfrage) |
| 1 Scope + Arbeitslisten | Scope-Leiste (nach Q2), Liste als Vorgabe mit URL-Zustand in drei Übersichten, `?ansicht=`-Split, Übergabekarten-Bauteil, `report --faellig`, Tastatur-Regel | M · Q2 |
| 2 Tintentreue + Nachfahren | PFAD_FORMAT 2 (zwei Releases), `tintentreue.py`, meta-only Read, Filter „Nachfahren", Editor-Adapter, PATCH + ETag, Archiv-Regel, §14-Vorregistrierung | M–L · Q4, Q9, Q10, Q15 |
| 3 Rollen-Spalten + Stufe 1 | Router-Zeilen, Rollen-Spalten in Buchstabe/Übergang/Wort, Belegleiste, Leerflächen Phase 5, `work_items.hand_id`, Glossar | M · Q3, Q11 |
| 5 (außerhalb der Evolution) | Streifen-Quelle, `instances`-Key, `ernte.py`, Exporter-Filter, Aggregate; Laufform je Hand, Hand-Vorschau | L · Q19, Q20 |

### 7.4 Tag 1 nach Phase 0 und die Deltas der Szenarien

**Tag 1:** Scope-Leiste fehlt noch (Q2); aber Overflow weg, Korb-Filter,
Probe ohne Spur sichtbar, und je Kasten der Rohzahlen-Chip — die erste
Antwort auf Frage 3 ohne Weiche. Ab Phase 1 die kompakten Listen.

Die Szenarien S1–S13 stehen einmal in §11; A weicht so ab: S2 —
Nachfahr-Liste ist Filter in `?ansicht=streifen`, Editor im Desktop-Dialog
(Tablet-Vollbild Q14); S4 — Eigenhand nur als Leerfläche + Belegleiste;
S6 — Korb bleibt Vorlagen-Scope, Kasten-Aufträge tragen ihr Specimen; S7
— Eigenhand-Apply abgeblendet (Guard) bis Q19; S9 — Scope-Leiste trägt zwei
Vorlagen je Schrift, Hand fremden Stils wird leer; S12 — 412 aus `If-Match`.

### 7.5 Risiken

Frage 6 bleibt Leerfläche — sagt Q1, F6 sei ein Quartalsziel, läuft Phase
5 parallel ab Phase 1. Der Editor-Adapter hängt an V1 oder einer Props-Naht;
Regressionsrisiko am Platten-Fluss, Gegenmittel `/verify-frontend` auf
beide Flüsse und drei Viewports. `?ansicht=` muss in `paths.ts` und
`frontend-stack.md` §2 stehen. Kein Cockpit, kein ‹ › durch Listen; der
Korb bleibt auf Hand-Seiten ein Vorlagen-Zähler.

### 7.6 Doktrin-Check

Stufen-Doktrin: neue Schreib-Knöpfe nur „Nachfahren" (Streifen, `authored`)
und ⚑. Korb: nur Filter, kein Status. `force`: drei Flächen. Lineale:
Schwellen aus Repo-Konstanten und dev-19; A hält `eigenhand-erfassung.md`
§7.3 bis Q10, danach datierter §14-Eintrag als erklärte Erweiterung.
Statistik je Hand: Eigenhand eingeklappt bis Q3 — mit Q3(a) trägt A das
§10.2-Update. Open Core: neue Reads RESERVED. Haken bleibt Urteil.
Design-System: §5.1, Idee 19.

## 8 Option B — Hand-zentriert

**Leitidee.** Neben dem Subjekt (Buchstabe · Übergang · Wort in der Query)
steht die **Hand** als Arbeitsstelle im Header und in jeder URL
(`h=<hand_id>`); Vorlage und Schrift folgen aus der Hand. Jede Detailfläche
hat dieselben drei **Rollen-Spalten** — die gewählte Hand aufgeklappt mit
Zahlen und Werkzeugen, die andere eingeklappt und beschriftet, nie
verrechnet. Historische Wortproben und Streifen-Wortproben sind zwei
Evidenz-Arten mit einem Vokabular; `/admin/eigenhand` wird die vierte
Ansicht **Hand-Bestand**, die für JEDE Hand Rohmaterial und Schleife zeigt.

**Warum.** Reibung 1 und 3 sind Scope-Fehler: nur mit `h=` in der URL
tragen Korb-, Todoist- und PR-Links die Hand. Und die Eigenhand existiert
in `hands` NICHT — `GET /eigenhand/hands` baut sich aus Zeilen +
`STYLE_IDS`, `GET /hands` ist ein zweites Register: die Arbeitsstelle-Seite
liest zwei Register, die sich nirgends treffen. Nur diese Linse sieht den
Riss.

### 8.1 Was — IA und Routen

Entitäten: Schrift → Vorlage/Tafel (Kurrent hat zwei) → Hand (Platte
`suetterlin-1922-norm`; Eigenhand `mn-<stil>`) → je Hand Wortproben,
Bahnen, Vorkommen (Eigenhand erst Phase 5), Statistik, Laufform (Q19).
`h=` genügt, wenn eine Hand ihre Vorlage kennt: `sources.hand_id` EXISTIERT
(nullable FK seit `0004`, im Seed NULL) — es fehlt nur `hands.kind` und der
Daten-UPDATE (V1), kein `hands.source_id`.

Routen: `/admin` (Arbeitsstelle) · `/admin/buchstaben?h=[&g=]` ·
`/admin/uebergaenge?h=[&l=&r=]` · `/admin/woerter?h=[&w=][&s=|&k=<strip>/<fassung>#<box>]`
· `/admin/hand?h=[&streifen=]` · `/admin/eigenhand` → 302. `focus.ts`-Builder
bekommen `h` als Pflicht-Argument; ohne `h` gilt die letzte Arbeitsstelle,
sonst die Platten-Hand. Header: Wordmark · [Schrift ▾] [Vorlage] [Hand ▾] ·
Nav Buchstaben · Übergänge · Wörter · Hand · ⚑ (Badge je Hand,
`work_items.hand_id`). **Der Hand-Umschalter springt IMMER auf die Übersicht
der neuen Hand** — das Subjekt fällt; ein Umschalter, der unter demselben
Subjekt die andere Hand lüde, ist der in §13 verworfene. Handy: EIN Chip
mit Bottom-Sheet.

**Vokabular (Q8):** Rollen-Etiketten statt „historisch / andere Hand / meine
Hand"; „Wortprobe" beidseitig, „Bahn" mit Herkunfts-Chip, „Vorkommen" für
Fits, „Beleg" allein der Bestand. Heute zählt `traceCount: '{{count}}
Belege'` (`locales/de/admin.ts`) die `word_instances` der Platte — die eine
echte Doppelbelegung.

### 8.2 Flächen

**Arbeitsstelle wählen** `/admin` — je Schrift eine Gruppe: Tafel-Karte(n)
links, Hand-Karten rechts mit Rollen-Etikett und Kennzahlen.

Quellen: `GET /styles`, `/sources`, `/hands`, `/eigenhand/hands`,
`/eigenhand/setups` (EXISTS); „Platten-Hand je Vorlage" ist heute nur aus
`instances` ableitbar, EXISTS erst nach V1; Kennzahlen je Karte aus fünf
Reads oder einem `GET /hands/{id}/summary` (DERIVABLE). Karte →
`/admin/buchstaben?h=`; „Neue Eigenhand" → Ausrüstungs-Skelett (`PUT
/eigenhand/setups/{hand}` EXISTS, `hands`-Zeile MISSING).

**Buchstaben** `?h=[&g=]` — Übersicht: Liste als Vorgabe, Filter wie A +
„Bahn rot", 24er-Seiten. Detail: Rollen-Spalte TAFEL (Ausschnitt, Wizard,
Diagnose, Landmarken) · PLATTE (Vorkommen, Statistik, Übergänge, Wörter) ·
EIGENHAND (Belege-Galerie mit Bahn-Overlay und Tintentreue, Stufe 1/5,
„Nachfahren nötig: k") · Fuß Laufform übernehmen (nur für die Hand, deren
Aggregat übernommen wird).

Rollen Tafel + Platte aus `templates`, `bboxes`, `landmarks`, `instances`,
`aggregates`, `pair-instances`, `word-samples` (EXISTS); Rolle Eigenhand:
Kästen + Bild + Bahn, Crop auf den Span (EXISTS/DERIVABLE), Tintentreue
(§6.3), Stufe 1 (§6.1), Aggregat (Phase 5). Knöpfe wie A; ⚑ trägt
`hand_id` und Specimen/Kasten.

**Übergänge** `?h=[&l=&r=]` — Matrix mit Zählern (Platte n · Übersteuerung
· Eigenhand n als Zahl + Füllmuster, Farbe nur zusätzlich), keine Renders in
Zellen (bei 63 Buchstaben wären es ~4 000 Kompositionen); mobil gefilterte
Liste. Detail: Rollen-Spalten wie §6.2; Verbinder-Maße erst nach dem
Formatwechsel.

**Wörter** `?h=[&w=][&s=|&k=]` — Übersicht mit Hand-Filter, **Vorgabe
„beide Hände"** (die strikte Trennung je `h` gäbe dem Autor genau das nicht,
was er verbinden will); Filter Bahn (Alle · rot · gelb · ohne Bahn · Folger
fand nichts · Maske geändert · von Hand · unvollständig), Sortierung, 24er-
Seiten. Detail = die Brücke: Rolle 1 „Wie das System es schreibt" (Tafel ·
Platte · Eigenhand) + Woraus es besteht + **Belegleiste** · Rolle 2 jede
Platten-Wortprobe (Crop, Bahn, Wortbench-Abstand, Editor) · Rolle 3 jede
Streifen-Wortprobe (Crop ohne Lineatur, Bahn mit Herkunft/Saat, Befund,
Tintentreue mit Zahlen, Lupe, Nachfahren, Flecken, Link „Streifen S0041 im
Hand-Bestand").

Tafel- und Platten-Schreibung über `/write/word` + `laufform=none`
(DERIVABLE), Eigenhand-Schreibung MISSING (Hand-Vorschau-Route + Laufform
je Hand), Belegleiste aus `strips?item=` je Item oder Bündel-Read `GET
/eigenhand/belege/{hand}?text=` (DERIVABLE). Knöpfe wie A; Überlagern nur
innerhalb einer Hand.

**Hand-Bestand** `?h=` — Eigenhand: Stepper der Schleife (Ausrüstung →
Drucken → Schreiben → Einlesen → Hochschieben → Bahnen folgen → Nachfahren
→ Statistik) mit Stand je Schritt („3 Fassungen ohne Bahn") und
Übergabekarten; Streifen · Zeichen & Übergänge · Bögen · Ausrüstung. Platte:
Abbildungen (19 · 20 · 22) mit Wortproben-Zahl, Sidecar-Flags,
Entwicklungssatz-Wörter.

Stepper-Stände (ohne Bild · ohne Bahn · rot · Maske geändert) aus
`archive/{hand}` + meta-only Read, sauberer als ein `GET
/eigenhand/stand/{hand}` (DERIVABLE); „nächster Bogen enthält Buchstabe x"
braucht eine `select_strips`-Vorschau ohne Verbuchung (MISSING). Knöpfe wie
heute; Streifen › Kasten öffnen → `/admin/woerter?h=&w=&k=`.

**Korb**: hand-scoped, Umschalter „alle Hände", Deep-Link `#korb=<id>`;
braucht `work_items.hand_id` (DDL) — `specimen_kind='strip'` ist Schema.

### 8.3 Wie — Phasen

| Phase | Inhalt | Größe · hängt an |
|---|---|---|
| 0 | §5.2 | S–M |
| 1 (B0) Schale und Sprache | Scope-Leiste mit Hand-Umschalter (springt auf Übersicht), `h` in `focus.ts`, `/admin` als Arbeitsstelle-Wahl, Nav „Hand" + Redirect, Rollen-Spalten-Bauteil, Umbenennungen in `admin.ts` (Q8), Listen + Seiten | M · Q2, Q8 |
| 3 (B1) Rollen-Spalten und Brücke, nur Lesen | **Migrationen (zwei):** `hands.kind` + Seed `mn-suetterlin` als Registrierung (V1), `work_items.hand_id`; Rollen-Spalten in drei Details, Wort-Detail mit beiden Evidenz-Arten, Belegleiste, Hand-Bestand mit Stepper, Korb je Hand | M · V1, V7 |
| 2 (B2) Tintentreue und Nachfahren | wie A Phase 2; PATCH + ETag (kein neues `force`) | M–L · Q4, Q9, Q10 |
| 3 (B3) Stufe 1 | Bündel-Reads `/summary`, `/stand`, `/belege?text=`; Skizzen nur mit Q11a | M |
| 5 (B4) | wie A | L · Q19, Q20 |

Zwei Migrationen vor der ersten Ampel — Routine mit Snapshot und
`/verify-migrations` (31 Revisionen, kein Ausfall), aber Nutzen erst nach
B1.

### 8.4 Tag 1 und Deltas

**Tag 1 nach Phase 0** wie A. Nach B0 lernt der Autor drei Dinge, bevor er
Neues sieht: Hand-Achse in der URL, Nav „Hand", Vokabular — und sein
Lesezeichen `/admin/eigenhand` ist ein Redirect. Deltas: S1 — Einstieg über
die Karte „Sütterlin · Eigenhand", Stepper nennt die Fassungen ohne Bahn;
S2 — Filter „Bahn: rot" in der Wörter-Übersicht, ‹ › im Filter; S3 —
Auftrag trägt `hand_id`; S6 — Korb je Hand; S9 — Arbeitsstelle-Seite zeigt
Kurrent mit zwei Tafeln ohne Hand.

### 8.5 Risiken

Migrationslast vor Nutzen. Ein Link ohne `h` landet auf der
localStorage-Hand — Builder erzwingen `h`, Header warnt bei Subjekt-Hand ≠
Arbeitsstelle. Die Vergleichsspalte verführt zur Differenzzahl über Hände.
Die `hands`-Registrierung könnte als „Phase 5 eröffnet" gelesen werden —
Fußnote in `eigenhand-erfassung.md` §9. Umbenennungen brechen Gewohnheit
und Doku-Anker. Belegleiste = n Item-Reads ohne Bündel-Endpunkt. Mobil
konkurrieren Scope-Leiste, Nav und Korb um eine Zeile.

### 8.6 Doktrin-Check

Stufen-Doktrin: Wizard in Rolle Tafel, Wort-Editor in Rolle Platte/Eigenhand
(`authored` = Ground Truth), Paar-Editor hinter dem Doktrin-Satz; Generiertes
nur ⚑. Korb unverändert, ergänzt um `hand_id`. Statistik je Hand: EINE Hand
als Arbeitsstelle, Vergleichsspalte eingeklappt — das ist Q3(a) und trägt
das §10.2-Update. Open Core: neue Reads RESERVED. `force`: drei Flächen —
das Überschreiben einer nachgefahrenen Bahn ist ein Terminal-Flag, keine
UI-Fläche (Q4). Streifen-Bahn bleibt in `pfade`. „Saat: Tafel-Duktus" an
jeder Bahn. Design-System: §5.1, Idee 19; eine URL ohne `h` bleibt gültig.

## 9 Option C — Aufgaben-zentriert

**Leitidee.** Vom Blätterkatalog je Vorlage zum **Cockpit je Tag**: eine
Startfläche „Heute" mit vier Arbeitslisten (neu schreiben · nachfahren ·
Gate-Status · Korb wartet auf dich) und dem Bestandskopf; ein
**Arbeitsvorrat** mit Warteschlangen, aus denen ‹ › das nächste Element lädt
(`?liste=` reist mit); darunter die Subjekt-Flächen in drei Rollen-Spalten;
die Medienbrüche als **Übergabekarten**. Neue Schreibknöpfe nur, wo Ground
Truth entsteht; Generiertes behält genau einen Griff: ⚑.

**Warum.** Der Autor fährt vier Schleifen (drucken → schreiben → scannen →
Befund → das Schwächste neu; folgen → prüfen → nachfahren; markieren →
Rückspiegelung → abnehmen; Wizard/Laufform/Wort-Editor); die Flächen sind
nach Datenobjekt geschnitten — Reibung 2 und 5. Ein Cockpit macht den
nächsten Schritt zum ersten Knopf. Der Autor liest am Tablet, tippt am
Rechner — darum Übergabekarte plus `report --faellig`, und die
Nachfahr-Fläche ist FÜR das Tablet gebaut. Praxis dahinter: die
Arbeitsvorrat-Muster der Annotations-Werkzeuge (Label Studio, Prodigy,
CVAT: Warteschlange, „nächstes Element", Filter, Tastatur) — ohne deren
Statuswechsel per Knopf, weil hier die Kartei und das Korb-Protokoll die
Zustandsquellen bleiben.

### 9.1 Was — IA und Routen

Header: Wordmark · Chip Vorlage · Chip Hand (Popover; auf Eigenhand-Flächen
ist der Vorlage-Chip abgeblendet mit „Saat: Tafel-Duktus") · **Nav mit vier
Links: Heute · Buchstaben · Übergänge · Wörter** — „Arbeit" hängt an Heute,
„Eigenhand" am Hand-Chip (§5.1, Idee 20). Routen: `/admin` (Heute) ·
`/admin/arbeit?liste=korb|nachfahren-platte|nachfahren-eigenhand|neu-schreiben|luecken|gate&filter=`
· `/admin/buchstaben[?g=&hand=&liste=]` · `/admin/uebergaenge[?l=&r=&hand=&liste=]`
· `/admin/woerter[?w=&s=&strip=<S>:<F>:<box>&hand=]` · `/admin/eigenhand`
(Übersicht: Bestand) · `/admin/eigenhand/streifen[?strip=&fassung=&box=]` ·
`/admin/eigenhand/nachfahren` · `/admin/eigenhand/bogen` (Bögen &
Ausrüstung) · `/admin/korb` (Seite; Drawer bleibt). Jede Detailfläche trägt
einen sticky Subjekt-Kopf mit ‹ › entlang der Liste, aus der man kam.
Tablet: zwei Rollen-Spalten + Tab, Split-Pane wird Liste → Detail mit ‹ ›.
Handy: Chips zu einem kombinierten Chip, die Rollen als Tabs, die Matrix als
gefilterte Liste; zweizeilige Leiste mit Scroll-Snap (V15), keine
Bottom-Nav ohne Nachtrag im Design-System §7.

### 9.2 Flächen

**Heute** `/admin` — Arbeitsfläche, vollbreit, `ViewHeader` (Playfair h4);
der Picker wandert in den Vorlagen-Chip (Popover, `PageContainer` bleibt
dort). Zeile 1 Bestandskopf der Eigenhand: die zwei doktrinierten Zahlen
(Mindestbelegung n/63 · gewichtete Erstbeleg-/Ausbau-Quote) und der
gemessene Ampel-Anteil; Kennzahl-Kachel = Zahl in `h3` Garamond 400, Etikett
`caption`, Karte `paper.hi` + Haarlinie; keine „Tore", keine Marke (Q24).
Zeile 2 vier Arbeitslisten-Karten mit Zähler und den ersten drei Einträgen.
Zeile 3 „Am Rechner weiter": Übergabekarten + `report --faellig`. Zeile 4
Letzte Änderungen (7 Tage).

| Information / Knopf | Quelle | Status |
|---|---|---|
| Mindestbelegung, Quoten; neu schreiben (schwächste zuerst) | `bestand.glyphs/quoten`; `strips[].befund` | EXISTS |
| Nachfahr-Liste (rot · Folger fand nichts · Maske · übersprungen) | meta-only Read | MISSING (Phase 2) |
| Gate-Status (Zeile fehlt · Frische „veraltet" · n/Sprung/Kopf) — keine Distanzschwelle, keine Rangfolge nach Gewinn; Filter client-seitig aus `n_instances`/`below_min_occurrences` | `/hands/{hand}/aggregates` | DERIVABLE |
| Korb `returned`/`ack`; Übergabekarten-Trigger (Ausrüstung fehlt · ohne Bild · ohne Bahn · Gewichte leer · Bogen ohne Fassung) | `/work-items`, `setups`, `archive`, meta-only Read, `uebergangsraum`, `sheets` | EXISTS / DERIVABLE |
| Letzte Änderungen (kein Sammel-Endpunkt) | `*.updated_at`, `pfade.erzeugt_am` | MISSING (optional) |
| Chips · Öffnen mit `?liste=` · Befehl kopieren · Karte ausblenden · ⚑ Notiz | Ansicht, localStorage, `POST work-items` | schreibt nur `note` |

Leerzustände: keine Hand → „Noch keine Hand — Ausrüstung anlegen", die
Karte `setup --pull` erst NACH dem Sichern; Aggregate leer → „Diese Hand hat
noch keine Vorkommen", keine Null.

**Arbeitsvorrat** `/admin/arbeit?liste=` — Listen-Tabs mit Zählern,
Filterzeile (Status, Buchstabe, Bogen, Datum, Hand; „Ansicht speichern"),
Split-Pane ab `lg`; Roving-Tabindex, ‹ › an Alt+←/→, Kurztasten nur mit
Fokus in der Liste und abschaltbar. Die Korb-Liste ist die Vollansicht des
Drawers.

Listen: Korb mit Protokollfeldern (EXISTS) · Nachfahren Platte aus
`traceStatusOf`/`badness` (EXISTS) · Nachfahren Eigenhand nach §6.4 mit
Bahn-Deckung (meta-only Read MISSING) · neu schreiben aus `strips[].befund`
· Lücken aus `bestand.queue/redo` (EXISTS). Knöpfe: Liste/Filter/‹ ›/Öffnen
(URL), Nachfahren als Dialog über dem Subjekt (keine Route — R9), ⚑ ·
missverstanden · Löschen wie heute, Lücken › Bögen erzeugen (erst dort),
Mehrfachauswahl → Notiz an alle — kein Batch-Statuswechsel.

**Buchstabe · Übergang · Wort** — Subjekt-Kopf (Titel, Chips, ‹ ›, ⚑) ·
drei Rollen-Spalten (1440) / zwei + Tab (Tablet) / Tabs (Handy): TAFEL
(Ausschnitt, Wizard, Diagnose, Landmarken) · PLATTE (Laufform, Median +
MAD, Vorkommen schlechteste zuerst, Statistik) · EIGENHAND (Belegzahlen,
Ausschnitt-Stapel, Belege-Galerie mit Tintentreue, „Nachfahren nötig: k")
· quer Übergänge/Wörter · Fuß Laufform übernehmen. Übergang: Spalte 1 =
Klassenregel (Provenienz in `compose_word_payload` intern; Name müsste in den
Payload — DERIVABLE), Spalte 3 = Verbinderstücke nach dem Formatwechsel.
Wort: System mit Hand-Umschalter (Tafel · Platte · Eigenhand als Leerzustand
mit Lücken-Chips + „⚑ Pin-Wunsch") · Platte (Ebenen Tinte · Bahn · System;
Wortbench-Abstand; Editor) · Eigenhand (Kästen je Fassung, Ampel mit Zahlen,
„Saat: Tafel-Duktus", Editor) · Belegleiste.

Quellen wie A/B; Wort: Eigenhand-Schreibung MISSING, Lücken je Slot aus
`shaping` × Bestand und Probe ohne Spur aus `word-samples` (DERIVABLE).
Knöpfe: Einrichten · Diagnose · Laufform übernehmen · Paar-Editor ·
Nachfahren (Platte) unverändert; Nachfahren (Kasten) `PATCH …/pfade/{box}`
+ `If-Match`; Flecken; ⚑ mit `specimen_kind='strip'`; „Bahn neu folgen
lassen" als Übergabekarte `pfad --strip S --fassung F --box i`.

**Eigenhand-Übersicht** `/admin/eigenhand` — Hand-Select, Rollen-Chip,
Bestandskopf (zwei Zahlen + Ampel-Anteil, „Nächste Handlung") · Zähler ·
Zeichen-Tafel · Übergangs-Matrix „nur offene" (Zähler + Muster) · größte
gewichtete Fehlstellen · Übergabekarten · Ausrüstung eingeklappt.
*Streifen*: Galerie (Suche, Sortierung Bogen · Befund · Tintentreue · Datum;
Schalter Bahn · Lineatur · roh; Zoom) + Detail je Fassung (Overlay,
Kästen-Tabelle mit Ampel + Zahlen + Herkunft + Nachfahren, Befund-Felder
mit Schwellen, Ausrüstungswerte, `zurueckgezogen` sichtbar). *Nachfahren*:
die Liste nach §6.4 (Filter ohne Bahn · rot · Maske · übersprungen; Zeile =
Crop mit Overlay, Ampel, Grund, Bahn-Deckung, Nachfahren, ggf. „Pfad reicht"
Q12); Editor Vollbild auf dem Tablet, Werkzeuge oben, „Speichern & weiter"
über PATCH je Kasten. *Bogen*: Bögen · Versuche · Erzeugen · PDF · gedruckte
Bögen mit Stand (nur, was der Server sieht) · Ausrüstung · Übergabekarten.

Quellen `/eigenhand/*` (EXISTS); Ampel-Anteil je Glyphe (gemessene Kästen,
von Hand getrennt) MISSING (Read); Befund-Aggregat der Hand, Bahn-Deckung,
Stand je Bogen DERIVABLE; Snapshot-Stand MISSING — der Server weiß nichts
vom Archiv, nur Hinweis. Knöpfe: Bögen · PDF · Ausrüstung · Flecken wie
heute; Nachfahren → Speichern & weiter (`PATCH …/pfade/{box}`); Neu
schreiben als Übergabekarte `redo` (`--retire` getrennt beschriftet); ⚑
Fassung. **KEIN „Aggregate neu rechnen" vor Phase 5** — die Eigenhand hat
keine `hands`-Zeile, der Knopf könnte nur die Platte meinen: ein
Vorlagen-Griff auf einer Hand-Fläche. Laufform ableiten: für die Eigenhand
abgeblendet (Guard) bis Q19.

**Korb** Seite `/admin/korb` + Drawer: Zähler je Status, Filter Ebene/Stufe/
Quelle/Zeitraum, Bündelung nach Ziel, Eintrag mit „Verstanden als",
`reproduced`, Stufe + Resolution (PR-Link), Nachher-Render live neben dem
Platten-Crop (Vorher aus dem PR-Overlay-Link — MISSING als Feld);
Stufen-Statistik client-seitig. „Abnehmen" ist KEIN Status (V10).

**Übergabekarte (Bauteil).** Titel („Bahnen fehlen für 4 Fassungen") ·
Warum mit Doktrin-Grund („der Folger lebt in tools/, das API-Abbild hat ihn
nicht") · Befehl in `mono` mit Parametern + Kopieren · „Danach hier: …" ·
Reihenfolge-Hinweis (Snapshot vor `--apply`) · „Am Rechner: `report
--faellig`". Unsichtbar, wenn nichts fällig ist; zeigt nur, was der Server
SIEHT — lokale Schritte (Snapshot, ingest) kann sie nicht bestätigen. Fläche
`paper.hi` mit Haarlinie; Eintrag im Komponenten-Inventar des
Design-Systems §7.

### 9.3 Wie — Phasen

| Phase | Inhalt | Größe · hängt an |
|---|---|---|
| 0 | §5.2 | S–M |
| 1 (C1) Heute + Arbeitslisten | Cockpit mit Bestandskopf, Befund-Liste, Gate-Status, Korb-returned; Listen mit URL-Zustand; `?liste=` + Subjekt-Kopf; Übergabekarten-Bauteil + `report --faellig`; Virtualisierung nur wo nötig (V14) | M · Q2, Q7 |
| 2 (C2) Tintentreue + Nachfahren | wie A; Streifen-Fläche, Nachfahr-Liste mit Bahn-Deckung, Editor-Dialog tablet-first, PATCH + ETag | M–L · Q4, Q9, Q10, Q13, Q15 |
| 3 (C3) Rollen-Spalten + Matrix | Dreispalten auf Buchstabe/Übergang/Wort; Hand-Umschalter im Render mit Lücken-Chips; Matrix mit Zählern; `work_items.hand_id` | M–L · Q3 |
| 4 (C4/C5) | Arbeitsvorrat vollständig, `/admin/korb`, Sitzungs-Skript | M · C1 |
| 5 | wie A | L · Q19, Q20 |

### 9.4 Tag 1 und Deltas

**Tag 1 nach Phase 0** wie A; nach C1 sieht der Autor „Heute" mit vier
Zählern und den fälligen Übergabekarten, bevor irgendeine Weiche außer Q2/Q7
entschieden ist. Deltas: S1 — Heute: „Neu schreiben: 3 (schwächste S0090
F02, Kringel zu)" → Streifen-Detail → Übergabekarte `redo S0090`; nach der
Runde Bestandskopf 58/63, Karten weg, neue Karte „Bahnen fehlen für 2
Fassungen"; S2 — Nachfahr-Liste mit „Speichern & weiter"; S3 — Arbeit ›
Korb, `returned` erscheint auf Heute als „braucht deine Hand"; S4 —
Hand-Umschalter im Render; S7 — Gate-Status-Karte, Apply nur mit
Snapshot-Karte davor; S8 — die Übergabekarte kann lügen, wenn Kartei und DB
auseinanderziehen (Kartei ist Zustandsquelle); S11 — Letzte Änderungen.

### 9.5 Risiken

Elf Flächen sind ein L-Projekt; ohne Phasen-Schnitt entsteht ein
halbfertiger Zustand neben dem heutigen. Spalte 3 und der Hand-Umschalter
bleiben monatelang Leerzustände. Race Tablet-Editor ↔ `pfad --apply` —
ETag (V20). „Abnehmen" als Client-Filter geht beim Browserwechsel verloren.
Virtualisierung nur ab ~500 Zeilen. Tabletprüfung braucht Access-Cookie und
S-Pen-Events am Gerät (Todoist-Aufgabe).

### 9.6 Doktrin-Check

Stufen-Doktrin: Geometrie schreiben nur Wizard, Wort-/Streifen-Editor,
Paar-Editor, Laufform-Übernahme hinter dem Zeilen-Gate; Arbeitslisten
patchen nichts und lösen nichts aus. Korb: der Mensch setzt nur `open`;
„Abnehmen" ist Notiz/Filter. Haken bleibt Urteil: „Neu schreiben" ist eine
Karte, `--retire` eine getrennt beschriftete zweite; Redo bleibt Kartei.
`force`: drei Flächen. Zeilen-Gate: der Gate-Status zeigt das Gate, kein
neues Kriterium; Reihenfolge Snapshot → Vorher → Übernehmen → Nachher.
Lineale: Bench-Zahl aus dem Terminal; humanbench bleibt außerhalb
(Messjournal §14, kein Korb-Write aus der Messschicht, V11). Statistik je
Hand: Hand-Chip an jeder Zahl; Rollen-Spalten tragen Q3. Open Core: Reads
RESERVED, Hand-Vorschau eigene Route. Tablet-ERFASSUNG bleibt verworfen;
der Streifen-Editor ist Nachfahren über gescannter Tinte. Rollenwechsel:
Zahlen sichtbar, keine Marke.

## 10 Vergleich und Empfehlung

| Kriterium | A Evolution | B Hand-zentriert | C Aufgaben-zentriert |
|---|---|---|---|
| F1 Übersichtlichkeit | Scope-Leiste, Listen als Vorgabe, Rollen-Spalten, Belegleiste | `h=` verlinkbar, ein Vokabular — klarste Disziplin, schwächste Brücke in der Übersicht | Cockpit, ‹ › entlang Listen, Übergabekarten — löst Reibung 2 und 5 am stärksten |
| F2/F3 Statistik, Tintentreue | Rohzahlen Phase 0, Ampel Phase 2 (§6 für alle) | dito, in Rolle 3 | dito + Ampel-Anteil im Bestandskopf |
| F4 Nachfahren | Filter in der Streifen-Ansicht, PATCH | Filter in der Wörter-Übersicht, PATCH | eigene Liste mit Bahn-Deckung, tablet-first |
| F5/F6 | Leerfläche + Belegleiste | dito | Lücken-Chips + Pin-Wunsch |
| Doktrin-Deltas | Q3 (mit a), Q10 | Q3, Q10, Umbenennungen | Q3, Q10 |
| Nutzen der ersten Phase | sofort (Phase 0/1) | erst nach B1 (zwei Migrationen, Routine mit Snapshot) | Phase 1 (Cockpit) |
| Getestete Schreibflüsse | unangetastet | unangetastet (Adapter) | unangetastet (Dialog statt Route) |
| Bis Frage 6 | Phase 5 — gleich bei allen (Q19/Q20), parallel möglich | dito | dito |
| Geräte | drei Stufen, Editor-Vollbild Q14 | Akkordeon-Rollen, ein Scope-Chip | Rollen als Tabs, Nachfahr-Dialog fürs Tablet |
| Kognitive Last | niedrig | mittel (neue Achse, neue Wörter) | niedrig im Alltag, hoch beim Bau |

**Empfehlung.** **A zuerst, C darauf, B punktuell** — unter dem Vorbehalt
von Q1: sagt der Autor, F6 sei ein Quartalsziel, läuft Phase 5 (Backend,
Tool) parallel zu Phase 1–3 (SPA); die beiden berühren sich kaum. Grund: A
beantwortet F1–F5 mit heutigen Daten, fasst keinen getesteten Schreibfluss
an und bringt schon in Phase 0 den Rohzahlen-Chip. Reihenfolge: **Phase 0**
(zwei Wochen, identisch) → **Phasen 1–3** → **Phase 4 = C-Bausteine auf A**
(Heute mit Bestandskopf, `?liste=` + ‹ ›, Übergabekarten + `report
--faellig`, Nachfahr-Liste nach Bahn-Deckung, Nachfahr-Dialog tablet-first,
Korb-Seite). **Aus B gepfropft:** `h=` als optionaler Parameter der
`focus.ts`-Builder, den Korb-/Todoist-Links immer tragen; `hands.kind` +
Registrierung (V1), sobald eine Route sie braucht; Korb je Hand (V7);
Rollen-Etikett + Position + Strichart ab Phase 0; der Stepper als Form der
Übergabekarten-Reihe; NICHT die Umbenennungen und nicht die strikte
Hand-Trennung der Wörter-Übersicht. **Vokabular der C-Bausteine auf A:** das
aus §5.0 — nichts anderes. **Nicht in diesen Plan:** die Freigabe-Maschine
(eigenes Proposal hinter Q19/Q20/Q24), der Editor als eigene Route, die
serverseitige Nachmessung beim Speichern.

### 10.1 Was keine Option anfasst

Die getesteten Schreibflüsse (Wizard · Diagnose · Bulk · Wort-Editor ·
Paar-Editor · Laufform-Übernahme · Korb-Protokoll · Fleckenpinsel ·
Ausrüstung · Bögen · `PUT …/pfade` als Tool-Vollersatz) werden wörtlich
aufgerufen; Dialog-Erweiterungen zählen als Umbau (Q6). Die bindenden
Regeln stehen in §4.1 und gelten unverändert; dazu aus dieser Runde: jede
Browser-Verifikation neuer Schreibflüsse läuft gegen den lokalen
Wegwerf-Stack, nie in Prod (Guardrail, keine Rückfrage); die Messschicht
schreibt keine Korb-Zeilen; das Quiz bleibt bei 1922.

### 10.2 Doktrin-Deltas — was eine Antwort bewegt

| Regel (heute) | Neuer Satz (nur mit dieser Antwort) | Ziel-Doc | Frage |
|---|---|---|---|
| werkbank §6: „die Werkbank zeigt immer genau eine Quelle/Hand" | „genau eine Hand als Subjekt; eine zweite Hand nur eingeklappt, beschriftet, nie verrechnet" | `optimierungs-werkbank.md` §6 | Q3(a) |
| eigenhand §7.5: „der Pfad ist ableitbar" (nicht im Archiv) | „ein nachgefahrener Pfad ist nicht ableitbar und wird wie Bild, Verdikt, Maske archiviert" | `eigenhand-erfassung.md` §7.5/§8.1 | Q4(a) |
| eigenhand §7.3: „keine [Schwelle] an den Streifen des Autors angepasst" | „einmalige, vorregistrierte Kalibrierung je Hand, datiert eingefroren, §14-Eintrag" | `eigenhand-erfassung.md` §7.3 | Q10(b) |
| eigenhand §7.5: „Ansicht auf den Bestand", H1 = Median der Fits | „Stufe 1: Vorstufe aus Bahnen, schreibt nie in `aggregates`, speist nie einen Apply" | `eigenhand-erfassung.md` §7.5 | Q11(a) |
| eigenhand §7.5 Verworfen (Streifen-Pfad in `word_instances`) gegen §9 (Phase 5 → `instances`/`word_instances`) | eine der beiden Stellen wird berichtigt | `eigenhand-erfassung.md` §7.5 oder §9 | Q21 |
| werkbank §6: `force` auf genau drei Flächen | unverändert — das Überschreiben einer nachgefahrenen Bahn ist ein Terminal-Flag | — | Q4 |
| werkbank §5.1: `open` setzt der Mensch | unverändert | — | V11 |

### 10.3 Was im Terminal bleibt — und was ein Repo-Schritt ist

| Schritt | Befehl | Art |
|---|---|---|
| Bogen holen, einlesen, sieben, verbuchen, hochschieben | `pull --sheet` · `ingest` · `page` · `apply --haken` · `sync --mit-streifen` | lokal (Pixel, Passmarken, Haken) — Übergabekarte |
| Bahnen folgen, nachmessen, Grenzen setzen | `pfad --apply` · `--messen` · `--spans` (Q15) | lokal, Snapshot davor — Übergabekarte |
| Archiv | `snapshot` · `pull --pfade` · `sync --from` | lokal, create-only — Karte unbestätigbar |
| Gewichte, Redo | `universe --push` · `redo S00xx [--retire]` | lokal; Haken bleibt Urteil — Übergabekarte |
| Fällige Schritte am Rechner | `report --faellig` | lesend — die eine Zeile jeder Karte |
| **Wort anheften** | `pool pin --word` | **Repo-Schritt**: hängt eine Welle an `core/eigenhand/streifen.json` (Pin S0181), PR + Deploy, erst dann kennt „Bögen erzeugen" das Wort — Korb-Notiz „Pin: <Wort>" |
| **Korpus/Gewichte ändern** | `universe` | Repo-Schritt, wenn der Korpus im Repo liegt — Korb-Notiz |
| Ernte, Aggregate, Laufform | `ernte.py` · `rebuild` · Apply | Phase 5; Apply im Browser, Messung im Terminal |

## 11 Nutzungsszenarien

Einmal erzählt, gegen existierende Ids: Streifen S0001 `Galoppieren`, S0008
`Amtszeit`, S0090 `Säbel`, S0144 `das`, S0181 `Kurrentschrift` (Pin);
Platten-Proben `wenn-2`, `das`, `Galoppieren`, `Säbel`. Die erste Fassung
erzählte vier Szenarien gegen Wörter, die weder im Streifen-Plan noch auf
der Platte existieren — die Kritikrunde hat sie umgeschrieben. Deltas je
Option: §7.4 / §8.4 / §9.4.

**S1 Bogen-Runde.** Bogen geschrieben, lokal `ingest → apply --haken → sync
--mit-streifen`. Streifen-Ansicht, „nach Befund sortieren": S0090/F02 „neu
schreiben · Kringel zu (e) · Rang 2/2" — die Fassung bleibt Beleg und in
der Nachfahr-Liste (Befund-Regel 1). Fleckenpinsel auf einen Druckerpunkt →
`PATCH …/flecken`, Befund neu. Übergabekarte `redo S0090`; Bögen erzeugen →
PDF. Nichts Neues wird geschrieben, was nicht heute schon geschrieben wird.

**S2 Folgt der Tinte?** Lokal `pfad --strip S0008 --apply` (Snapshot
davor). Kasten `Amtszeit`: Rohzahlen „Tinte ohne Bahn 21 % · Absetzer 3 /
Soll 1"; ab Phase 2 Ampel „folgt nicht", Sortierung Tintentreue; Lupe zeigt
den Absprung am t-z-Übergang. „Nachfahren" → Editor über dem Kasten mit
Absetzer-Soll 1 daneben → `PATCH` mit `If-Match` → Herkunft „von Hand",
Ampel grau „ungemessen" bis `pfad --messen`. Ein späteres `pfad --apply`
lässt den Kasten stehen (409-Regel). Dieselbe Stelle in vielen Wörtern: ⚑
`note` — ein §14-Befund fürs Messjournal, kein UI-Fix. Vor Q4(a)/Phase 5:
die Zeile zählt, niemand liest sie.

**S3 Das n wirkt zu flach.** `/admin/woerter?w=wenn&s=wenn-2`: Abstandsprofil
0,11 auf dem zweiten n-Bogen → Chip n → Buchstaben-Detail: V0 solo richtig,
Rollen-Spalten zeigen Platte n = 41 und Eigenhand (eingeklappt) 7 Belege. ⚑
→ Vorsortierfrage „Nein" → Auftrag `kind=letter`, specimen `wenn-2`.
KI-Runde: `ack` mit `understanding`/`reproduced`, `done`, `stage=laufform`,
PR-Link. Drawer, Filter „erledigt", Gruppe „laufform".

**S4 Ein Wort in drei Rollen.** `?w=das`: System (Platten-Laufform) ·
Platten-Wortprobe `das` mit Bahn und Wortbench-Abstand · Eigenhand: Kasten
S0144 mit Bahn, Chip „folgt"; Belegleiste d 9 · a 14 · s 6 · d›a 4 · a›s 3.
Frage 6 ist als fehlend beschriftet, nicht simuliert. `?w=Familienbuch`:
kein Kasten, Belegleiste zeigt F 1 (rot) · ch›b 0 (rot) → „⚑ Pin-Wunsch" →
KI-Runde: Plan-PR, Deploy, dann Bogen.

**S5 Laufform übernehmen (Platte).** Detail-Fuß `d`: Dialog nennt n = 17,
Sprung 1,4 < 2,95, Kopf 6°; daneben die Karte `tools.dbsnapshot.fetch` und
die Reihenfolge Snapshot → Vorher-Zahl (Wordbench lokal, Fixture-Stand) →
Übernehmen → Nachher-Zahl; ein Verlust ist ein Rückroll-Grund über den
Snapshot, ein Gewinn kein Aufnahmekriterium (LF7). Bei n < 3 nur mit
ausdrücklichem `?min_occurrences=`. Eigenhand: abgeblendet, „Laufform je
Hand nicht entschieden" — der Guard lehnt serverseitig ab.

**S6 Korb-Runde bis zur Abnahme.** Am Handy: ⚑ auf `Galoppieren` (Platte),
Notiz „G-Bogen zu eng". KI: `ack` „Verstanden als: Kopplungshöhe G›a",
`reproduced: teilweise`; Triage Tafel → Laufform → Klassenregel; Tafel-
Duktus des G unvollständig → `returned` + Todoist „G im Wizard nachfahren".
Autor am Tablet: „braucht deine Hand" → Wizard → Speichern. KI: `done`,
`stage=chart_ductus`, PR-Link; Nachher-Render neben dem Crop (Vorher-Feld
MISSING); „gesehen" ist ein Client-Filter, kein Status.

**S7 Laufform-Neuableitung nach neuen Streifen (Phase 5).** `sync` →
`ernte.py` (authored vor tintenpfad, Exporter-Filter aktiv) → `rebuild`
für `mn-suetterlin` → Gate-Status → Snapshot → Apply für die EIGENHAND in
ihr Varianten-Band (Q19) → Hand-Vorschau-Route → Wordbench-Nachher lokal →
§14. Öffentlich schreibt die Seite weiter mit der Platte, bis der
Rollenwechsel erklärt ist.

**S8 Schlechter Scan-Tag.** Passmarken nicht erkannt, falsche dpi, Bogen
doppelt, `sync` abgebrochen: die Karte „Fassungen ohne Bild: 6" bleibt
stehen, `zurueckgezogen`-Fassungen sind eine eigene Gruppe (heute
ungezeigt), „neu schreiben" auf allen Fassungen ist ein Chip-Muster, kein
Verwerfen. Was der Server nicht sieht, bestätigt keine Karte — `report
--faellig` am Rechner ist die Wahrheit.

**S9 Zweite Schrift (Kurrent).** Zwei Tafeln, keine Hand `mn-kurrent`, ein
Streifenplan ohne Stil-Schlüssel, ≥ 600 dpi und Zwei-Kanal: Scope-Leiste
„Hand: —", Eigenhand-Flächen im Leerzustand „keine Hand dieses Stils"; kein
Bau in diesem Plan (Q25).

**S10 Rollback eines Apply.** Falsches öffentliches Schriftbild → welcher
Apply war es (kein Änderungsprotokoll, „Letzte Änderungen" MISSING) →
`tools/dbsnapshot`-Restore mit Rückfrage → `invalidate_pooled_style` +
Edge-Cache → §14-Re-Baseline. C's „Letzte Änderungen" wäre der erste
sichtbare Schritt.

**S11 Regression nach einer Korb-PR.** Deep-Link `/schreiben?text=…` →
`/admin/woerter?w=…`; „seit gestern geändert" (MISSING) → ⚑ mit PR-Bezug.

**S12 Zwei Geräte gleichzeitig.** Tablet-Editor speichert Kasten 2 von
S0008/F01, das Terminal fährt `pfad --apply` auf denselben Streifen: das
Tool bekommt 409 (authored) und mischt um den Kasten; ein zweiter Tab mit
altem ETag bekommt 412 und lädt neu — nie ein stiller Verlust (Guardrail
stale tab 2026-07-25).

**S13 Wiederherstellung aus dem Archiv.** DB-Vorfall → `sync --from
<snapshot>`: Bild, Verdikt, Maske kommen zurück; nachgefahrene Bahnen NUR
mit der Archiv-Regel aus Q4(a) — sonst sind sie weg. Restore ist
Prod-berührend: Rückfrage.

## 12 Rückfragen-Katalog

Nach der Kritikrunde von 40 auf 25 Fragen gekürzt: nur Fragen, die allein
der Autor beantworten kann, in drei Stufen nach dem, was sie blockieren
(Phasenleiter §5.2). Engineering-Entscheidungen stehen am Ende als
**Vorgaben** (V1–V26), die ohne Rückfrage gelten und mit einem Wort kippbar
sind. Jede Frage nennt, was stillschweigend gilt, wenn sie NICHT
entschieden wird, und ob eine Antwort eine bindende Regel bewegt — dann
kommt sie nur als erklärtes Proposal-Update in den Bauplan (§10.2).

**Welche Frage beantwortet welche Autor-Frage aus §1:** F1
Übersichtlichkeit → Q2, Q3, Q7, Q8 · F2 Statistik je Buchstabe/Übergang →
Q11, Q15, Q16, Q19, Q20 · F3 „folgt der Ink?" → Q9, Q10 (+ V21, V26) · F4
Nachfahren → Q4, Q12, Q13, Q14, Q15 · F5 Ableitungen → Q3, Q11, Q19 · F6
„in meiner Hand" → Q1, Q19–Q23 · F7 grüne Wiese → Q5, Q6, Q17, Q18, Q24,
Q25.

### 12.1 Stufe I — Weichenstellungen vor Phase 0

**Q1 — Wie dringend ist Frage 6 gegenüber Frage 1–5?** *(blockiert: die
Reihenfolge des ganzen Plans)*
Kontext: Die Empfehlung „A zuerst" hängt an der Annahme, dass „in meiner
Hand geschriebenes" hinter Übersichtlichkeit, Statistik und Nachfahren
warten darf. Phase 5 (Streifen-Quelle, Ernte, Aggregate, Laufform je Hand)
ist Backend- und Tool-Arbeit, Phase 1–3 ist SPA-Arbeit — beides baut die
KI, sie berühren sich kaum.
Optionen: (a) F6 ist ein Quartalsziel → Phase 5 parallel ab Phase 1, sobald
Q19/Q20 entschieden sind; (b) F6 darf hinter Phase 1–3 warten; (c) Reihung
F1–F7 frei angeben.
Empfehlung: (a), wenn der Autor die Produktionshand in diesem Quartal sehen
will — die Aufwandsschätzung (8–12 Wochen, §6.7) ist eine Vermutung mit
Kette, keine Messung.
Ohne Entscheid: (b) — Frage 6 bleibt bis nach Phase 3 eine Leerfläche.

**Q2 — Scope-Modell: wie kommt die Hand in die Kopfleiste?** *(blockiert:
Phase 1)*
Kontext: Der Vorlagen-Chip steht auf `/admin/eigenhand`, das Korb-Badge
zählt die Vorlage (§3.8, Punkt 1). Vorgabe V19 regelt die Kopplung: die
aktive Hand ist immer eine Hand des Vorlagen-Stils.
Optionen: (a) zwei Chips Vorlage + Hand, die Leiste zeigt beide und schaltet
nicht; (b) `h=<hand_id>` in jeder Admin-URL, Vorlage folgt aus der Hand
(braucht `hands.kind` + `sources.hand_id`-Daten, V1); (c) dreiteiliger
Rollen-Chip je Schrift; (d) nur Beschriftung reparieren.
Empfehlung: (a) ab Phase 1, plus `h=` als OPTIONALES Argument der
`focus.ts`-Builder, das Korb- und Todoist-Links immer tragen. Nicht (c):
Kurrent hat zwei Tafeln, die Vorlagenwahl darf nicht verschwinden.
Ohne Entscheid: (d); jeder Link ohne Hand öffnet die localStorage-Hand.

**Q3 — Darf die zweite Hand auf derselben Detailfläche stehen?** *(bewegt
`optimierungs-werkbank.md` §6 „die Werkbank zeigt immer genau eine
Quelle/Hand"; blockiert: Phase 3)*
Kontext: Der Auftrag will „historisch UND meine" nebeneinander; die
Leitplanke sagt eine Hand je Fläche. Alle drei Optionen legen die Eigenhand
als Rollen-Spalte auf Vorlagen-Flächen — das ist keine Layoutfrage, sondern
ein Proposal-Update. Zwei Skizzen nebeneinander verführen zu einer
Differenzzahl.
Optionen: (a) zweite Hand eingeklappt sichtbar (Etikett + n), aufklappbar,
nie verrechnet — §6 wird zu „genau eine Hand als Subjekt; die zweite nur
eingeklappt, beschriftet, nie verrechnet"; (b) strikt eine Hand je Seite,
Wechsel nur über den Chip; (c) beide aufgeklappt als Vorgabe.
Empfehlung: (a) als erklärtes §6-Update; Differenzzahlen nur innerhalb einer
Hand (Median ↔ eigene Laufform), zwischen Händen nur Bilder mit beiden
Etiketten; Nebeneinander als Vorgabe, Überlagern auf Klick.
Ohne Entscheid: (b) — der doktrin-konforme Standard; die Rollen-Spalte
Eigenhand bleibt auf Vorlagen-Flächen zu.

**Q4 — Nachgefahrene Streifen-Bahn: Ground Truth, Archiv, `force`?**
*(bewegt `eigenhand-erfassung.md` §7.5 „der Pfad ist ableitbar";
blockiert: Phase 2)*
Kontext: §7.5 legt den Streifen-Pfad außerhalb von `word_instances` und
hält Pfade für ableitbar — `snapshot.py` und `sync --from` tragen sie
nicht. Ein `authored`-Pfad ist NICHT ableitbar. Die Schutzregel „der Folger
ersetzt `authored` nie" ist Vorgabe (Phase 0, Zwilling von
`authored_identities`); offen ist, was sie schützt und ob es archiviert
wird. Vor Q4(a) und Phase 5 liest kein Verbraucher eine nachgefahrene Bahn.
Optionen: (a) ja: `verfahren: authored` in `eigenhand_strips.pfade`, vom
Folger nie ersetzt (409 + Tool-Merge), im Archiv geführt (`pull --pfade →
snapshot → sync --from`, §7.5 „Wiederherstellung" erweitert), die Ernte
liest ihn vor `tintenpfad`; (b) nur Saat-Korrektur: der Folger läuft danach
noch einmal, gespeichert bleibt sein Pfad; (c) kein Nachfahren auf Streifen
bis Phase 5. Unterpunkt: das Überschreiben einer nachgefahrenen Bahn ist
(i) ein Terminal-Flag, keine UI-Fläche, kein neues `force`; (ii) eine
vierte force-Fläche als erklärter §6-Nachtrag.
Empfehlung: (a) mit (i) — der Zwilling der Platten-Regel; (c) lässt Frage 4
bis Q20 offen. Schreibweg ist Vorgabe V20.
Ohne Entscheid: kein Editor für Streifen; die Archiv-Regel entfällt, Phase 2
baut nur die Ampel.

**Q5 — Welche Reichweite in welcher Reihenfolge?** *(blockiert: alles nach
Phase 0)*
Kontext: A beantwortet F1–F5 mit heutigen Daten ohne Migration; C löst
Reibung 2 und 5 am stärksten; B ist die klarste Scope-Disziplin, aber die
schwächste Brücke in der Übersicht und braucht zwei Migrationen vor der
ersten Ampel. F6 hängt in jeder Option gleich an Q19/Q20.
Optionen: (a) A zuerst (Phase 0 zwei Wochen, Phasen 1–3 je ein Monats-PR),
dann C-Bausteine als Phase 4 auf A, B nur punktuell (`h=` in Links,
`hands`-Registrierung, Korb je Hand, Rollen-Etikett); Phase 5 parallel oder
danach nach Q1; (b) C sofort als Zielbild mit Phasen-Schnitt; (c) B sofort;
(d) nur A.
Empfehlung: (a).
Ohne Entscheid: (d) durch Trägheit — Frage 6 dauerhaft leer.

**Q6 — Ist R9 die Definition of Done?** *(blockiert: Phase 0)*
Kontext: Wizard · Diagnose · Bulk · Wort-Editor · Paar-Editor ·
Laufform-Übernahme · Korb-Protokoll · Fleckenpinsel · Ausrüstung · Bögen sind
von HTTP-Suiten und `/verify-frontend` gepinnt; der Editor-Adapter ist die
Grenze (Props statt Verzweigung). Dialog-Erweiterungen — auch eine Checkbox
im Apply-Dialog — zählen als Umbau.
Optionen: (a) ja, für alle Optionen; Umbau nur mit gesonderter Begründung;
(b) nein, Umbau erlaubt, wenn die Suiten mitgezogen werden.
Empfehlung: (a).
Ohne Entscheid: (b) durch Schleichen.

### 12.2 Stufe II — vor Phase 1–3

**Q7 — Startfläche: Cockpit „Heute" oder die Vorlagen-Wahl? Und der Korb
als Seite?** *(blockiert: Phase 4)*
Kontext: `/admin` ist der Picker — die eine Admin-Seite im Lesemaß
(`design-system.md` §4). Das Cockpit wäre eine vollbreite Arbeitsfläche
(`ViewHeader`, Kennzahl-Kacheln aus der Typo-Leiter); der Picker wanderte in
den Vorlagen-Chip. Der Korb-Drawer bekommt in Phase 0 Filter (V8); eine
Seite macht das Archiv zur Abfrage („welche Stufe verursacht die meisten
Aufträge?", `optimierungs-werkbank.md` §5.1).
Optionen: (a) Heute unter `/admin`, Korb-Seite `/admin/korb` mit Phase 4;
(b) Picker bleibt, Heute unter `/admin/heute`, nur Drawer; (c) Heute als
Block über dem Picker.
Empfehlung: (b) in Phase 1–3, (a) mit Phase 4 — das Cockpit ist erst mit
meta-only Read mehr als vier Zähler.
Ohne Entscheid: Picker bleibt Einstieg, Korb bleibt Drawer.

**Q8 — Vokabular: Etiketten, ein Wort für die Bahn, Anglizismen**
*(blockiert: Phase 1)*
Kontext: Drei Teilfragen. (a) „historisch / andere Hand / meine Hand" oder
die Rollen-Etiketten Tafel · Platte · Eigenhand; „Belege" zählt heute
`word_instances` der Platte (`locales/de/admin.ts`) UND den Bestand — die
eine echte Doppelbelegung. (b) Für die gefolgte oder nachgefahrene Linie
sagt die Eigenhand-Seite „Pfad" (17 Locale-Treffer), die Platte „Bahn" (10)
/ „Spur" / „Nachfahrung"; die Empfehlung „A zuerst, C darauf" importierte
C's „Bahn" durch die Hintertür. (c) Englische Labels in einer deutschen
Werkbank: Override · Loss · Score · Skip · Sync · Setup · Engine · Hub —
Befehle bleiben englisch, Labels nicht.
Optionen: (a) Rollen-Etiketten jetzt, breite Umbenennung nie; (b) EIN
Substantiv „Bahn" beidseitig, Herkunft als Chip „automatisch (Tintenpfad)"
/ „von Hand", „Streifen-Pfad" bleibt Glossar-Name des Felds; (c) je Wort:
Loss → „Wortbench-Abstand", Score → „Güte", Override → „Übersteuerung",
Skip → „übersprungen", Sync → „Hochschieben", Engine → „System", Hub →
„Übersicht", Setup → „Ausrüstung".
Empfehlung: (a) + (b) + (c) vor Phase 1; „Belege" → „n Bahnen" im
Platten-Detail. Kein „der erste PR entscheidet".
Ohne Entscheid: (a); Pfad ⇄ Bahn und die Anglizismen bleiben.

**Q9 — Welche Sensoren zählen in der Tintentreue?** *(blockiert: Phase 2)*
Kontext: `ink_unvisited_share`, `paper_lifts`, `jumps`, `hairpins` liegen im
Pfad-Meta; AIoU rechnet das Tool; die Papier-Exkursion muss NEU gerechnet
werden (`excursions.py` misst gegen die Referenz, die ein Streifen nicht
hat); das Struktur-Soll liest Fixture-Fälle.
Optionen: (a) drei Zahlen aus dem heutigen Meta; (b) fünf: + Exkursion max
gegen die eigene Tintenmaske + AIoU (PFAD_FORMAT 2, Lockstep in zwei
Releases); (c) sechs: + Struktur-Soll, wenn ein Soll-Rechner ohne Fixtures
entsteht. Regel: schlechtester Sensor entscheidet vs. kumulativ.
Empfehlung: (b), „schlechtester Sensor" (wie `_summarise`; ein Strukturdefekt
darf keinen Distanzgewinn kaufen); (c) später.
Ohne Entscheid: (a) — Ampel v1 aus drei Zahlen, ohne Deckungssensor.

**Q10 — Woraus werden die Schwellen vorregistriert — und je an eigenen
Streifen kalibriert?** *(bewegt `eigenhand-erfassung.md` §7.3 „keine an
den Streifen des Autors angepasst"; blockiert: Phase 2)*
Kontext: 0,05/0,15 und 0,7929 sind an der Platte (30–35 px xh) kalibriert,
Streifen liegen bei 300 dpi. Eine Kalibrierung an eigenen Fassungen ist
eine Anpassung an genau diese Streifen; der blinde Beurteiler ist der
Schreiber selbst.
Optionen: (a) Repo-Konstanten und dev-19-Perzentile sofort einfrieren,
Änderung nur als datierter §14-Eintrag; (b) wie (a) als Start, dann EIN
vorregistriertes Verfahren: erste 20–30 Fassungen, 30 Kästen blind
beurteilen (humanbench-Muster), Schwellen einmal justieren, datiert
einfrieren — Proposal-Update §7.3, Konstanten je Hand mit Datum, für jede
weitere Hand neu vorzuregistrieren; (c) Regler in der UI.
Empfehlung: (b) mit dem genannten Preis; nie (c). Bis dahin „vorläufig".
Ohne Entscheid: (a) — Risiko einer leeren oder endlosen Nachfahr-Liste.

**Q11 — Stufe 1 aus Bahnen zeigen, oder nur Belegzahlen bis Phase 5?**
*(bewegt `eigenhand-erfassung.md` §7.5 „Ansicht auf den Bestand", wenn
(a); blockiert: Phase 3)*
Kontext: Eine Median/MAD-Skizze aus Folger-Bahnen wäre eine zweite
Aggregat-Pipeline neben H1 (Median der FITS). Ein Etikett macht die
Abweichung sichtbar, nicht konform. Die Übergangs-Stufe-1 ist ohnehin erst
nach dem Formatwechsel möglich (`letter_spans` kennen keine Verbinder).
Optionen: (a) zeigen, etikettiert „aus Bahnen, n = …", als Proposal-Update
mit dem Satz, dass `statistik.py` nie in `aggregates` schreibt und nie einen
Apply speist; (b) nur Belegzahlen, Tintentreue-Verteilung, Ausschnitt-
Stapel (Bilder), Feder-Halbbreite; (c) nichts bis Phase 5.
Empfehlung: (b) jetzt; (a) nur, wenn der Autor Zahlen vor Phase 5 will.
Ohne Entscheid: (b).

**Q12 — Gibt es „Pfad reicht" (Abnahme eines gelben Auto-Pfads)?**
*(blockiert: Phase 2)*
Kontext: Eine Abnahme (`meta.abgenommen_am`) ist eine zweite Wahrheit neben
der Ampel; ohne sie bleibt gelb gelb, bis nachgefahren oder neu gefolgt.
Optionen: (a) ja, sichtbarer Zustand mit Datum, nie ein Fassungs-Status
(Befund-Regel 1); (b) nein.
Empfehlung: (b) zuerst; (a) nach den ersten 50 Nachfahrungen bewerten.
Ohne Entscheid: (b).

**Q13 — Reihenfolge der Nachfahr-Liste?** *(blockiert: Phase 4)*
Kontext: Bahn-Deckung (Items, bei denen < 3 Kästen eine grüne oder
nachgefahrene Bahn tragen) ist mehr wert als ein zufälliger Kasten; sie
braucht `letter_spans` (Q15). In Phase 2 gilt die einfache Ordnung.
Optionen: (a) Schwere → Bahn-Deckung → Gewicht → Streifen; (b) Schwere →
Streifen; (c) Streifenfolge.
Empfehlung: (a) ab Phase 4, (c) als Umschalter; in Phase 2 (b).
Ohne Entscheid: (b).

**Q14 — Tablet: welche Flächen, welcher Editor, welches Gerät für welchen
Schritt?** *(blockiert: Phase 2)*
Kontext: Der Autor fährt mit dem S-Pen im PROD-Admin nach; der Wort-Editor
ist stift-tauglich (Touch-Pointer ignoriert, `touchAction: 'none'`). Der
Plan kannte zunächst nur 1440 und 390 px — das Tablet (~1024) hatte keinen
Viewport; jetzt gilt die Drei-Stufen-Regel (§5.1, Idee 17).
Optionen: (a) `WordTraceEditorDialog` Vollbild auf dem Tablet, Werkzeuge
oben, „Speichern & weiter" innerhalb `?liste=` (ab Phase 4; in Phase 2 ohne
Liste); (b) eigene Route mit Queue; (c) Stift-Modus-Schalter. Dazu: welche
Schritte am Tablet (lesen, nachfahren, ⚑), welche am Rechner (Wizard,
Terminal, Apply)?
Empfehlung: (a); keine Stift-Telemetrie im Format (Verwurf 2026-08-22);
Tablet-Test am Gerät durch den Autor vor der ersten echten Nutzung
(Todoist-Aufgabe).
Ohne Entscheid: (a) im Desktop-Layout; Geräteteilung wie heute.

**Q15 — Wer setzt Buchstabengrenzen auf nachgefahrenen Bahnen?**
*(blockiert: Phase 2/3)*
Kontext: `letter_spans` schreibt allein der Folger aus `info.meta`
(`tools/eigenhand/pfad.py`); der Editor liefert nur Züge, `check_paths`
prüft `meta` nicht. Ohne Grenzen tragen nachgefahrene Kästen weder Stufe-1-
Statistik noch Bahn-Deckung — das Trainingsziel von Q4 wäre entwertet.
Optionen: (a) der Autor setzt Slot-Marker im Editor; (b) ein Werkzeugschritt
`pfad --spans` legt sie über die nachgefahrene Bahn (Saat-Korrespondenz zur
Tafel-Zeile); (c) gar nicht.
Empfehlung: (b) — der Editor kennt keine Duktus-Semantik.
Ohne Entscheid: (c).

**Q16 — Statistik-Einheit: Hand oder Hand × Ausrüstung?** *(blockiert:
Phase 3)*
Kontext: `EigenhandHand` sagt ausdrücklich, ein Federwechsel „splits the
corpus into cohorts that cannot be compared" (`core/database/models.py`);
jede Fassung trägt Feder/Tinte/Papier/Gerät. §6 rechnet je Hand über alle
Fassungen.
Optionen: (a) Hand, mit Kohorten-Facette als Filter und Warn-Chip „gemischte
Federn"; ein Ausrüstungswechsel ist im Bestand eine sichtbare Zäsur; (b)
strikt je Kohorte; (c) ignorieren.
Empfehlung: (a); ob ein Ausrüstungswechsel die Laufform-Kandidatur
zurücksetzt, entscheidet der Autor am ersten Wechsel.
Ohne Entscheid: (c).

**Q17 — Referenzwörter in den Streifen-Plan pinnen?** *(blockiert: nichts;
Repo-PR)*
Kontext: Plan (553 Wörter) und Platte (140 Texte) überschneiden sich in 24
Wörtern; `lesen`, `denen`, `wenn`, `einen`, `unter` und der Entwicklungssatz
fehlen im Plan. `pool pin` hängt eine Welle an die COMMITTETE Datei (Pin
S0181) — ein Repo-Schritt mit PR und Deploy, kein Terminal-Schritt.
Optionen: (a) MVP-Anker (`lesen`, `das`, `denen`) und Entwicklungssatz als
Pins, ein PR; (b) nur die MVP-Anker; (c) nein — die Brücke läuft über
Items.
Empfehlung: (a), damit die Wort-Brücke wenigstens für die Referenzwörter
trägt.
Ohne Entscheid: (c).

**Q18 — Schreibtakt: wie viele Bögen und Fassungen je Woche?** *(blockiert:
nichts; dimensioniert)*
Kontext: Die Listen (V14), die Kalibriermenge „erste 20–30 Fassungen" (Q10)
und der Abstand der Bogen-Runden hängen an einer Zahl, die nur der Autor
kennt.
Optionen: eine Zahl (Bögen/Woche, Fassungen/Bogen) oder „schwankend".
Empfehlung: eine Zahl nennen; darunter bleibt alles Vermutung.
Ohne Entscheid: Annahme 2 Bögen/Woche, 8 Streifen je Bogen.

### 12.3 Stufe III — vor Phase 5

**Q19 — Wo lebt die Laufform der Eigenhand?** *(blockiert: Phase 5)*
Kontext: `apply-laufform` upsertet `(hand.style_id, glyph_key, 100)` unter
`uq_template_style_key_variant`; heute scheitert der Eigenhand-Apply an
`require_hand` (404), mit `hands`-Zeile überschriebe er die Platte. Der
Guard (V22) steht ab Phase 0. Berührt `write.py` (Zeilenwahl im Router),
`hands.laufform_variant`, `write-api.md` — `compose.py` und die
Golden-Fixture nur unter (d); `/write/glyphs?variant=` akzeptiert 0..999
schon.
Optionen: (a) Varianten-Band je Hand als Daten auf `hands`
(`laufform_variant`: Platte 100, Eigenhand 200); (b) `templates.hand_id`
nullable + Unique-Erweiterung; (c) eigene Tabelle `hand_templates`; (d)
compose liest `aggregates.cluster_center` direkt; (e) eigene `sources`-Zeile
je Hand.
Empfehlung: (a) — kleinste Migration, Default unberührt, passt zu
`architektur.md` §10 „Varianten-Auswahlvektor"; Satz in §3, dass Band ≥ 100
„Laufform je Hand" heißt. Nicht (d): Laufform ist Render-Zustand, Aggregat
Statistik (`optimierungs-werkbank.md` §7 W5).
Ohne Entscheid: Frage 6 bleibt Leerfläche.

**Q20 — Wie werden Streifen zur Quelle der Ernte?** *(blockiert: Phase 5)*
Kontext: `sources.chart_path` ist repo-relativ, gitignorte Streifen können
das nie sein; `instances` hat einen Pixel-Ort-Key, unter dem zwei Streifen
kollidieren. `eigenhand-erfassung.md` §9 sagt: „Die eigene Hand braucht
kein eigenes Chart" — eine `sources`-Zeile ist im Datenmodell die Tafel.
Optionen: (a) `sources.kind='eigenhand'` mit `chart_path`-Sentinel,
ausdrücklich KEINE Tafel: kein Chart, keine Templates, nie in der
Vorlagen-Auswahl, kein Ziel für Wizard/Diagnose; Crop-/Skelett-Routen lesen
`eigenhand_strips`; `instances`-Key wird `(source_id, specimen_id, slot,
variant)`; (b) private lokale Quelle nur für die Ernte; (c) eigene Tabelle
`eigenhand_instances`, `core/aggregate.py` liest beide — trennt die Rollen
im Schema, doktrin-näher, aber zwei Lesewege; (d) Selektiv-Commit
(Autor-Entscheid 2026-08-22 dagegen).
Empfehlung: (a) mit dem Sicherungssatz, Exporter-Filter an
`tools/dbsnapshot/fetch.py` und am Fixture-Builder mit Test VOR der ersten
Ernte; (c), wenn die Rollen-Trennung im Schema wichtiger ist als die
Wiederverwendung der Routen.
Ohne Entscheid: Phase 5 bleibt geschlossen.

**Q21 — Ernte-Ausgabe: `pfade` oder `word_instances` unter der
Eigenhand-Quelle?** *(Doc-Konflikt; blockiert: Phase 5)*
Kontext: `eigenhand-erfassung.md` §7.5 verwirft den Streifen-Pfad in
`word_instances` (eingefrorener Referenzsatz); §9 desselben Docs beschreibt
Phase 5 wörtlich als „`instances`/`word_instances` über die Admin-API →
`hands`-Zeile". Die beiden Stellen widersprechen sich; keine Rückfrage
öffnet Verworfenes, eine muss berichtigt werden.
Optionen: (a) die Ernte liest Bahnen aus `pfade` (authored vor tintenpfad)
und schreibt nur `instances`/`pair_instances`; `word_instances` bleibt
Platte; §9 wird berichtigt; (b) mit Q20(a) und Exporter-Filter auch
`word_instances` unter der Eigenhand-Quelle; §7.5 wird berichtigt.
Empfehlung: (a) bis Phase 5 läuft.
Ohne Entscheid: (a).

**Q22 — Die Hand-Vorschau: Route, Gate, Cache** *(blockiert: Phase 5)*
Kontext: `tests/test_api_public_surface.py` klassifiziert je ROUTE; ein
admin-gegateter Query-Parameter auf der öffentlichen `/write/word` wäre
weder pinnbar noch `private, no-store`. Der Payload-Memo ist je
Template-Zeile schon hand-sicher; das Veraltungsrisiko ist die öffentliche
`Cache-Control` am Rand.
Optionen: (a) eigene reservierte Route `GET /hands/{hand_id}/write/word`
unter `require_admin`, RESERVED gepinnt; `/write/word` bleibt parameterfrei
bis zum erklärten Rollenwechsel, dann Umschaltung über `CONFIG`; (b)
`?hand=` auf der öffentlichen Route mit gezieltem 401-Test; (c) öffentlich
für alle Hände.
Empfehlung: (a); `write-api.md` im selben PR.
Ohne Entscheid: (c) durch Weglassen — ein Open-Core-Leck.

**Q23 — Gelten Paar-Übersteuerungen je Schrift oder je Hand?** *(blockiert:
Phase 5)*
Kontext: `glyph_pairs` ist `(style_id, left, right, variant)` gekeyt; nach
einem Handwechsel schriebe die Eigenhand mit den Platten-Übersteuerungen.
Optionen: (a) `glyph_pairs.hand_id`, bestehende der Platte zuordnen; (b) je
Schrift wie heute.
Empfehlung: (a) vor der ersten Eigenhand-Laufform.
Ohne Entscheid: (b).

**Q24 — Rollenwechsel-Bedingung: Zahlen ohne Marke, oder Marke
vorregistrieren — und das Zielbild jetzt als Doc?** *(blockiert: Phase 5)*
Kontext: `eigenhand-erfassung.md` §2 lässt den Schwellenwert offen;
`vision.md` nennt den Wechsel einen eigenen Autor-Entscheid. Der Admin zeigt
darum die zwei doktrinierten Zahlen und den Ampel-Anteil, keine „Tore". Die
Freigabe-Maschine (Stände create-only, Auslieferungs-Zeiger, Regression je
Hand) ist das stärkste Zielbild, beantwortet aber eine Frage, die der Brief
nicht stellt.
Optionen: (a) Zahlen zeigen, keine Marke; (b) Marke vorregistrieren (z. B.
90 % gewichtet + Top-200-Übergänge + Pflicht-Buckets), „Bedingung erfüllt"
als Hinweis. Unterpunkt: das Zielbild (i) jetzt als eigenes Proposal
entwerfen, kein Code; (ii) erst mit Phase 5; (iii) außerhalb des Admins.
Empfehlung: (a) bis der Autor am ersten vollen Bogen-Satz eine Zahl nennt;
(i), damit Q19/Q22 mit dem Zielbild vor Augen fallen.
Ohne Entscheid: (a), (iii).

**Q25 — Kurrent und Offenbacher jetzt mitdenken?** *(blockiert: nichts)*
Kontext: `styles` kennt drei Schriften, Kurrent hat zwei Tafeln; Phase 5
braucht für Schwellzug ≥ 600 dpi und Zwei-Kanal; der Streifenplan hat keinen
Stil-Schlüssel.
Optionen: (a) das Scope-Modell trägt eine Schrift mit zwei Vorlagen und
mehrere Hände (Q2(a) + V19 tun es), Kurrent-Betrieb bleibt Phase 5; (b)
Sütterlin-only bis zum Rollenwechsel.
Empfehlung: (a) als Randbedingung, kein Bau.
Ohne Entscheid: (b) — späterer Umbau der Scope-Leiste.

### 12.4 Vorgaben, die wir ohne Rückfrage setzen

Jede Zeile ist ein Engineering-Default; der Autor kippt sie mit einem Wort.

- **V1 `hands`-Registrierung.** `UPDATE sources.hand_id` für die Platten-
  Hand (Daten, Prod-berührend → Rückfrage in der Sitzung) in Phase 0;
  `hands.kind` + Seed `mn-suetterlin` als reine Registrierung erst, wenn eine
  Route sie braucht (Phase 3), Fußnote in `eigenhand-erfassung.md` §9 „keine
  Vorkommen". Kein `hands.source_id`.
- **V2 Eigenhand-Unteransichten** als `?ansicht=bestand|streifen|statistik|drucken`
  nach dem `focus.ts`-Muster; Unterrouten erst, wenn die Nachfahr-Liste eine
  eigene Fläche wird (Phase 4).
- **V3 Namen:** Tintentreue (Chip „folgt · folgt teils · folgt nicht"),
  Übergabekarte, Rohzahlen-Chip, Bahn-Deckung, Belegleiste, Gate-Status —
  Glossar-Einträge liegen mit diesem Plan vor (`glossar.md` §5, als geplant
  markiert), Vokabular-Tabelle §5.0.
- **V4 Schülerhand (Abb. 22):** Filter mit eigenem Rollen-Etikett „andere
  Hand", nie innerhalb der Platten-Hand; aus deren Statistikblöcken
  ausgeschlossen. Eigene Hand-Id erst mit V1.
- **V5 Meta-only Read** `GET /eigenhand/pfade/{hand}` als Python-Projektion
  nach `_STRIP_WITHOUT_PNG` (keine JSONB-Pfade — die Suiten laufen auf
  SQLite), RESERVED; eine `pfad_summary`-Spalte nur, wenn Cloud SQL zu
  langsam ist.
- **V6 Redo und Retire bleiben lokal:** Übergabekarte `redo S00xx`,
  `--retire` getrennt beschriftet; kein Verdikt im Browser (Kartei ist die
  einzige Zustandsquelle, Haken bleibt Urteil).
- **V7 Korb-Bezug auf Kästen:** `kind=word` + `specimen_kind='strip'` +
  `specimen_id='S0041/F02#2'` jetzt (Pydantic/TS-Literal, keine Migration);
  `workItemUrl` löst das Muster in `?ansicht=streifen&strip=&fassung=&box=`
  auf; `work_items.hand_id` als Migration in Phase 3. Nie `note` — das
  umginge das `stage`-Pflichtfeld.
- **V8 Korb-Drawer** mit Status-/Ebenen-/Stufen-Filter und Gruppierung ab
  Phase 0; `returned` oben.
- **V9 „übersprungen: unautoriert"** ist eine Ground-Truth-Lücke: Absprung
  in den Wizard und Arbeitsliste „Tafel fehlt", kein Korb-Eintrag.
- **V10 „gesehen"/„abgenommen"** ist Notiz-Ergänzung oder Client-Filter, kein
  Status; erledigte Einträge bleiben hinter „erledigte anzeigen" (so heute).
- **V11 humanbench** legt keine Korb-Zeilen an (Messschicht schreibt nicht;
  `open` setzt der Mensch); der §14-Eintrag bleibt der Ort, die KI-Runde
  darf danach eine `note` mit Verweis anlegen.
- **V12 Kein Todoist-Knopf** im Admin; die KI-Runde legt Aufgaben an
  (Direktive 2026-08-07).
- **V13 Hand-Kennzeichnung:** Viridian nur am aktiven Hand-Chip; Rollen im
  Overlay über Strichart + Etikett, Farben aus dem Perioden-Set als Tokens —
  keine Rolle trägt Viridian.
- **V14 Übersichten:** kompakte Liste als Vorgabe, Galerie Opt-in, 24er-
  Seiten, Zustand in der URL; Virtualisierung erst ab ~500 Zeilen, nie MUI X
  DataGrid.
- **V15 Kopfleiste:** höchstens vier Bereichs-Links; Handy zweizeilig mit
  Scroll-Snap; Bottom-Nav nur mit §7-Nachtrag im Design-System.
- **V16 Migrationen** je Phase gebündelt (ein Schema-PR, Snapshot davor,
  `/verify-migrations`), nie einzeln je Fläche.
- **V17 Verifikation** neuer Schreibflüsse gegen den lokalen Wegwerf-Stack
  (HTTP-Suite auf SQLite + `/verify-frontend` an beiden Editor-Flüssen und
  drei Viewports), nie in Prod — Guardrail, keine Frage. Der Tablet-Test am
  Gerät wird eine Todoist-Aufgabe.
- **V18 Snapshot im Apply-Dialog:** Übergabekarte `tools.dbsnapshot.fetch`
  neben dem Dialog, keine Pflicht-Checkbox (unprüfbar, Umbau); Reihenfolge
  Snapshot → Vorher-Zahl → Übernehmen → Nachher-Zahl.
- **V19 Hand↔Stil-Kopplung:** die aktive Hand ist immer eine Hand des
  Vorlagen-Stils; bei Stilwechsel die zuletzt gewählte Hand dieses Stils
  oder leer.
- **V20 Schreibweg der Bahn:** `PATCH …/pfade/{box}` mit Content-ETag
  (sha256 über `pfade`) und `If-Match`, 412 bei Konflikt — `eigenhand_strips`
  hat kein `updated_at`; der Vollersatz bleibt dem Tool; Tool-Push über
  `authored` → 409.
- **V21 Nachgefahrene Bahnen werden gemessen** (`pfad --messen`, Sensoren
  1/3/4/5 sind referenzfrei); „von Hand" ist ein Herkunfts-Chip, nie eine
  Ampelfarbe; bis dahin zwei Zähler (gemessen / ungemessen).
- **V22 Guard-Eigner-Regel:** Apply nur, wenn `hand.id == sources.hand_id`
  einer Quelle desselben Stils oder der Stempel `canonical.derived_from.hand_id`
  der V100-Zeile passt; fehlt der Stempel, ist die Platten-Hand Eignerin.
- **V23 Overlay-Ebenen** als Tokens `paper.layer.*`, farbenblind-sicher, je
  Ebene eine Strichart, Legende mit Text; Deuteranopie-Simulation im
  Verify-Durchgang; `mono`-Token für Befehle.
- **V24 Tastatur:** Roving-Tabindex in Listen, ‹ › an Alt+←/→, Kurztasten nur
  fokus-gebunden und abschaltbar; Tastatur-Durchgang als DoD je Phase.
- **V25 Hover:** kein entscheidungstragender Zustand nur im Tooltip —
  sichtbarer Text oder `InfoHint`.
- **V26 Rohzahlen-Chip** je Kasten in Phase 0 aus dem geladenen
  `pfade[].meta` — „Zahl, kein Urteil"; die Ampel folgt in Phase 2 an
  derselben Stelle.

**Aus der ersten Fassung gestrichen:** die Frage, ob der Streifen-Pfad des
Folgers in `word_instances` gehört (verworfen in `eigenhand-erfassung.md`
§7.5; der Phase-5-Weg ist Q21), ein Verwurf von Fassungen im Admin
(Kartei bleibt Zustandsquelle), der Verifikationsweg (Guardrail, keine
Frage) und ein reserviertes Druck-Feld im Pfad-Format (die Tür zur
verworfenen Tablet-Erfassung).

## 13 Verworfen in dieser Runde

Was die Entwürfe vorschlugen und die Richter oder die Kritikrunde gekippt
haben — mit dem Grund, damit es nicht in der nächsten Runde wiederkehrt. Das
vollständige Protokoll aller 98 Befunde der fünf Kritiker mit Entscheid und
Begründung steht in
[`../notes/admin-redesign-kritik-2026-09-17.md`](../notes/admin-redesign-kritik-2026-09-17.md).

- **Scan-Upload und serverseitiges Folgen** — waren schon verworfen
  (`eigenhand-erfassung.md` §10, §7.5); zwei Entwürfe hatten sie
  wiederbelebt.
- **Verdikt-, Redo-, Retire-Knöpfe im Browser** — die Kartei ist die einzige
  Zustandsquelle, der Haken bleibt Urteil.
- **Streifen-Pfad des Folgers in `word_instances`** — §7.5 verworfen; der
  Phase-5-Weg ist Q21.
- **Clientseitige „Skizze" der Eigenhand-Mediane** — grenzt an die
  Bildunterschriften-Lüge, die `vision.md` ausschließt.
- **Ampel-Schwellen als Regler in der UI** — Schwellen sind Mess-Provenienz
  (Q10, nie (c)).
- **Bench-Kopfzahlen im Admin** — Lineale bleiben im Terminal.
- **Ein Hand-Umschalter, der unter demselben Subjekt die andere Hand lädt**
  — lüde Statistik-Blöcke mit der falschen Hand; Option B springt darum
  immer auf die Übersicht.
- **Viridian oder eine zweite Akzentfarbe für eine Rolle** — Viridian ist
  Akzent, `success` und Fokusring zugleich; Rollen trennt die Strichart.
- **Der Editor als eigene Route** — Umbau eines getesteten Flusses (R9);
  vorerst Dialog.
- **Die Freigabe-Maschine im Admin-Plan** — das beste Zielbild für den
  Rollenwechsel, aber eine Frage, die der Brief nicht stellt; eigenes
  Proposal hinter Q19/Q20/Q24.
- **Todoist-Schreibzugriff aus der UI** — die KI-Runde legt Aufgaben an
  (Direktive 2026-08-07).
- **Die Pflicht-Checkbox „Archiv-Snapshot liegt vor"** — vom Tablet aus
  nicht wahrheitsgemäß zu setzen, der Server weiß nichts vom Archiv; ein
  Schein-Gate.
- **„Laufform-Kandidaten" mit Distanzschwelle** — ein neues Kriterium ohne
  Repo-Konstante; der Gate-Status zeigt das Zeilen-Gate, nichts anderes.
- **⚑ auf Kästen als `note`** — umginge das `stage`-Pflichtfeld des
  Korb-Protokolls; Kasten-Beschwerden sind `kind=word` mit
  `specimen_kind='strip'`.
- **`hand=` auf der öffentlichen `/write`-Route** — der Public-Surface-Test
  klassifiziert je Route; ein Open-Core-Leck.
- **Ein Druck-Feld im Pfad-Format** — die Tür zur verworfenen
  Tablet-Erfassung.
- **„Tore" und „Lieferbarkeit"** — undefiniert; eine Sieben-Stufen-Skala
  schüfe die Marke, die Q24 dem Autor vorbehält.
- **Einzelbuchstaben-Kurztasten** und **Bottom-Nav ohne Nachtrag im
  Design-System** — Tastatur nur fokus-gebunden; eine Leiste.
- **`pool pin` als Übergabekarte** — ein Repo-Schritt (PR + Deploy), kein
  Terminal-Schritt; als Korb-Notiz an die KI-Runde.
- **Vier Szenarien gegen nicht existierende Wörter** (`lesen`, `unter`,
  `einen`, `Familienbuch` sind weder im Streifen-Plan noch auf der Platte;
  `wenn-19-2` gab es nie) — umgeschrieben gegen echte Ids (§11).
- **Die Wort-Brücke als Konsens** — 24 von 140 Platten-Wörtern treffen den
  Plan; die Brücke läuft über Items (Belegleiste), Q17 fragt nach Pins.

## 14 Nächste Schritte

1. Der Autor liest §12 und beantwortet zuerst die Weichenstellungen.
2. Die Antworten werden als datierte Autor-Entscheide in §4.3 nachgetragen;
   die gewählte Option bekommt ihren Umsetzungs-Abschnitt, die anderen
   wandern nach §13. Der Status bleibt dabei `offen`.
3. Erst dann: Umsetzungs-PRs, jede mit ihrem Verify-Skill und — wo Geometrie
   berührt wird — dem Archiv-Snapshot davor. Mit der ersten ausgelieferten
   Stufe wechselt der Status auf `teil-umgesetzt`, im selben PR wie der Code.
