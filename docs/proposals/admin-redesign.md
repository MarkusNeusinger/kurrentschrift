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
> [`../concepts/vision.md`](../concepts/vision.md) „Drei Rollen"). **Dieser
> Stand ist der erste Schnitt der PR** — §4–§13 werden in derselben PR aus
> der laufenden Entwurfs- und Kritikrunde ergänzt.

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
| F1 | Wie wird der Admin **übersichtlicher**, vor allem die Trennung und Verbindung von **historischen** Wörtern (Platten-Wortproben der Vorlage: Ground Truth und Maßstab) und **meinen geschriebenen** (Eigenhand-Streifen: Trainingsdaten und künftige Produktionshand)? | §5 Leitideen, §7–§9 je Option „Scopes" |
| F2 | Welche **Statistik je Buchstabe und je Übergang aus meinen Streifen** — welche Zahlen, wo sichtbar, wie abgeleitet? | §6 |
| F3 | **Folgt der Ink gut?** — je Streifen/Wort sehen, ob der Tintenpfad der Tinte folgt | §6 |
| F4 | **Muss ich manuell nachfahren fürs Training?** — die Arbeitsliste und der Editor dafür | §6 |
| F5 | **Wie sehen Ableitungen aus?** — Laufform, Median, Aggregat der eigenen Hand neben Tafel und Platte | §6 |
| F6 | **… und in meiner Hand geschriebenes?** — ein beliebiges Wort, wie die Engine es mit meiner Hand schriebe | §6 |
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
4. **Kritikrunde:** Gegenleser prüfen die Optionen auf Doktrinbruch,
   Machbarkeit gegen API und DB, Gestaltung und Geräte, und ob sie die
   sieben Fragen wirklich beantworten; ein Vollständigkeits-Kritiker prüft
   den Katalog. Was die Kritik gekippt hat, steht in §13.

Die Zahlen aus der deployten API, soweit öffentlich lesbar (2026-09-17):
89 Template-Zeilen der Sütterlin-1922 (63 Keys in Variante 0, dazu
Varianten 1/2 und die Laufform 100), 62 von 63 Bboxen gesperrt, 202
Wortproben (63 Wörter der Bench, Abb.-20-Paare, Abb.-22-Schülerhand).

## 3 Ist-Befund: der Admin heute, Fläche für Fläche

Was hier steht, wurde angeklickt und angesehen; die Bildschirmfotos liegen
der PR bei. Kürzel: **(Z)** = zeigt, **(K)** = Knöpfe.

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

*Folgt in dieser PR aus der Entwurfsrunde.*

## 6 Die Eigenhand-Statistik — eine Spezifikation für alle Optionen

*Folgt in dieser PR: Zahlen je Buchstabe und je Übergang, das Maß „folgt
der Tinte?", die Nachfahr-Triage, die Ableitungen, die Vorschau „in meiner
Hand" — je Zahl mit dem Stand EXISTIERT / ABLEITBAR / FEHLT.*

## 7 Option A — Evolution

*Folgt in dieser PR.*

## 8 Option B — Hand-zentriert

*Folgt in dieser PR.*

## 9 Option C — Aufgaben-zentriert

*Folgt in dieser PR.*

## 10 Vergleich und Empfehlung

*Folgt in dieser PR.*

## 11 Nutzungsszenarien

*Folgt in dieser PR.*

## 12 Rückfragen-Katalog

*Folgt in dieser PR.*

## 13 Verworfen in dieser Runde

*Folgt in dieser PR.*

## 14 Nächste Schritte

1. Der Autor liest §12 und beantwortet zuerst die Weichenstellungen.
2. Die Antworten werden als datierte Autor-Entscheide in §4.3 nachgetragen;
   die gewählte Option bekommt ihren Umsetzungs-Abschnitt, die anderen
   wandern nach §13. Der Status bleibt dabei `offen`.
3. Erst dann: Umsetzungs-PRs, jede mit ihrem Verify-Skill und — wo Geometrie
   berührt wird — dem Archiv-Snapshot davor. Mit der ersten ausgelieferten
   Stufe wechselt der Status auf `teil-umgesetzt`, im selben PR wie der Code.
