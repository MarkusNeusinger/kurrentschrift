# Schreibsystem: Schreib-API, Python-Komposition, Wort-Bench

**Status: Vorschlag; Phasen A (PR #142), B (PR #143), C (PR #144) und D (erster Lauf, PR #145) umgesetzt (2026-07-02). Offen: Phase E.**
**Erledigt:** Der in §1.2 / Phase C beschriebene Port ist abgeschlossen —
die Wortkomposition liegt in `core/compose.py` (+ `core/shaping.py`), und
`app/src/domain/compose.ts` wurde gelöscht. Die `compose.ts`-Erwähnungen
weiter unten beschreiben den Ausgangszustand vor dem Port, nicht den
aktuellen Code.
Ergebnis des Schreibsystem-Audits vom 2026-07-01 (Repo-Audit + Live-Test
der Prod-Federprobe + Quellen-Recherche). Ziel: Wörter und Sätze so
schreiben, dass sie von einer echten Hand nicht zu unterscheiden sind —
zuerst Sütterlin, dann Kurrent und Offenbacher. Dieses Dokument hält den
Befund, den Phasenplan A–E und die verifizierten Wortvorlagen fest.

Verhältnis zu den settled docs: nichts hier schwächt
[`architektur.md`](../concepts/architektur.md) §4 („Übergänge sind
Konsequenz, keine Daten") — im Gegenteil, die Wort-Bench **misst den
Generator**. Bigram-Overrides bleiben auf
[`planaenderungen.md`](planaenderungen.md) Vorschlag B gegated
(Messen ja, Speichern erst nach Freigabe). Der Kompositions-Port nach
Python ist roadmap-konform: [`mvp-roadmap.md`](../concepts/mvp-roadmap.md)
M6 plante ohnehin ein Python-Transition-Modul, Vorschlag D reserviert
`core/orthography.py` für die Shaping-Seite.

---

## 1. Befund (Audit 2026-07-01)

### 1.1 Die API: der öffentliche Writer reitet auf dem Admin-Diagnose-Endpoint

Der gesamte öffentliche Schreibpfad (`/federprobe`, Quiz-Wörter,
`/tafel`, Schriftkunde-Specimen) nutzt ausschließlich
`GET /sources/{id}/templates/{key}/diagnostic` (`api/routers/templates.py`).
Live gemessen (api.kurrentschrift.ink, Sütterlin 1922):

- **15–22 KB pro Glyph, davon 46–51 % Ballast** — `skeleton_polyline_px`,
  `anchors_px`, `half_widths_px`, doppelte Outline-Felder, Crop-Metadaten,
  die nur der Admin-Diagnose-Dialog braucht.
- **~0,2 s CPU pro Request**: jede Anfrage lädt das Chart-JPEG,
  binarisiert, skelettiert — für Felder, die der Writer wegwirft. Die
  reine Render-Geometrie ist numpy über gespeicherte Anker und braucht
  kein Chart (bewiesen durch `written_preview_for_canonical`, das genau
  so arbeitet, aber nur admin-gated via `POST /trace-preview` erreichbar ist).
- **Kein HTTP-Caching, nirgends**: kein `Cache-Control`/`ETag`/gzip im
  API-Stack (`api/main.py` registriert nur CORS), Cloudflare meldet
  `cf-cache-status: DYNAMIC`. Jeder Besucher rechnet am Origin.
- Der Pooled-Nib-Scan (`_pooled_constant_nib`, alle ~138 Template-Zeilen)
  läuft pro Glyph-Request neu.
- `getDiagnostic` nutzt den Cold-Start-Retry des Clients nicht
  (`retries` default 0) — genau der min-instances=0-Fall, für den der
  Retry gebaut wurde.
- **Drei getrennte Modul-Level-Caches** im Frontend (WrittenGlyph,
  WrittenWord, WrittenSheet) mit unterschiedlichem Keying, die nichts
  miteinander teilen.

### 1.2 Die Komposition: `compose.ts` ignoriert vorhandene Daten

Die Wortkomposition (Platzierung + Übergänge) existiert **nur** in
`app/src/domain/compose.ts` (TypeScript, Frontend):

- Die im Wizard gepflegten Kopplungshöhen (`entry_coupling` /
  `exit_coupling`) werden gespeichert, ausgeliefert — und **nie gelesen**.
  Jeder Join ist dieselbe kurze Kubik mit fixem `CONNECT_GAP = 0.16`,
  egal ob der Vorgänger am Mittelband endet (Sütterlin o, b, v, w) oder
  an der Grundlinie.
- `advance` wird nie gelesen; kein Kollisionsschutz, `cursorX` kann
  rückwärts laufen.
- `DESCENDER_EXIT_Y = -0.2` (Magic Number) ersetzt die gespeicherte
  Kopplungs-Information fürs lange s; die Ersatz-Sehne bricht G1 und
  schneidet durch die Unterschleife.
- Joins sind nur G1 (Tangente), nie G2 (Krümmung) — sichtbarer
  Krümmungssprung an jedem Übergang.
- Shaping committet Ligaturen **ohne 404-Fallback**: fehlt `ch`/`tz`/`qu`
  oder ein Versal, entsteht ein Loch mit gekappten Verbindungen
  („Schule" → „ule") statt eines Zerfalls in Einzelbuchstaben.
- Konnektor-Breite = `2·min(medHalf)` — funktioniert für Sütterlin nur,
  weil die API den Nib poolt; für Kurrent gibt es kein
  Schwellzug-Konnektor-Modell.

### 1.3 Live-Test (Prod, 14 Wörter + Quiz-Wortmodus): Defektklassen

1. **w/v/o → Folgebuchstabe kollabiert zur geschlossenen Schleife auf der
   Grundlinie** statt am Mittelband anzusetzen („wovon", „waren" —
   Leserlichkeits-Killer). Ursache: 1.2, fehlende Kopplungshöhen-Nutzung.
2. **Autoring-/Datenfehler, kein Compose-Bug** (`compose.ts` verschiebt
   nie vertikal): mittiges e schwebt 30–40 % über der Grundlinie,
   Schluss-s auf Oberlängen-Höhe, o schließt oben nicht, r-Fuß rollt sich
   zur Schleife, ſ-Unterlänge zu dick/wellig. → Wizard-Nacharbeit,
   getrennt von Compose-Fixes; die Wort-Bench trennt beides objektiv.
3. **Löcher durch unkuratierte Templates** (S, W, Q, V, ch, tz, qu):
   6 von 14 Testwörtern unvollständig.
4. Sekundär: Z-förmige Doppel-Knicke in Aufstrichen, zu große Lücke vor
   finalem r, Quiz-Karte verrät das Lösungswort via `aria-label`.

### 1.4 Die strukturelle Wurzel: kein Feedback-Loop für Übergänge

Kein Python-Code kann heute ein Wort komponieren → die Bench
(`tools/glyphbench`) kann Übergänge **strukturell nicht messen**. Die
Metriken selbst sind kompositions-agnostisch (`suetterlin_quality_metrics`
nimmt Anker + Breiten + Strokes gegen Maske/Skelett) — es fehlt nur der
Python-Komponist und eingefrorene Wort-Referenzen.

---

## 2. Plan

### Phase A — Schreib-API + Quick Wins (umgesetzt: PR #142)

Neuer öffentlicher Read-Router `api/routers/write.py`:

- `GET /sources/{id}/write/glyphs/{glyph_key}` und Batch
  `GET /sources/{id}/write/glyphs?keys=…` — nur das Render-Subset
  (`outline_paths`, `centerlines_template`, `half_widths_template` mit
  Resolver + gepooltem Nib, `anchors_template`, `entry.xy`,
  `template_guides`), erzeugt aus **gespeicherten** Templates ohne
  Chart-I/O (Adapter um die `written_preview_for_canonical`-Geometrie).
- Pooled-Nib pro Source memoisiert (Invalidierung bei trace/resample/delete).
- `GZipMiddleware` + `Cache-Control: public, max-age=…` auf dem
  Write-Router (Cloudflare-Cache-Regel auf `write/*` folgt separat —
  Prod-Infra, nicht Teil des PRs).
- Client: gemeinsamer Render-Daten-Cache statt drei; Cold-Start-Retry
  für die Write-Fetches; Ligatur-404-Fallback (Zerfall `ch`→`c`+`h` usw.);
  `MISSING_ADV ≤ SPACE_ADV`; Quiz-`aria-label`-Leak schließen.

### Phase B — `core/compose.py` + Wort-API (umgesetzt: PR #143)

Port von `shaping.ts` + `compose.ts` nach Python (rahmenwerkfrei, über
Template-Zeilen). `GET /sources/{id}/write/word?text=…` liefert
DrawItems in Schreibreihenfolge (Vertrag von `WrittenWord` bleibt:
`lift`/`diacritic`/`maskWidth`). Parität über Golden-Test (committete
`composeWord`-Ausgabe der §9-Wörter); danach wird `compose.ts` gelöscht
(eine Quelle der Wahrheit). Ein Wort = 1 cachebarer Request.

### Phase C — Wortvorlagen + Wort-Bench (umgesetzt: PR #144)

- Vorlagen-Seiten (→ §3) als Chart-Bytes mit `SOURCE.md` via
  `/audit-licenses`.
- Wort-Rechtecke zunächst als Datei-Sidecar `data/sources/<id>/words.json`
  (Wort, erwartete Glyph-Slots, Rect, Grund-/Mittellinie, ggf. Schräge) —
  bewusst **ohne Migration** (Shared-DB-Risiko vertagt; die Bench ist
  hermetisch, nur der Exporter liest die DB).
- `tools/wordbench` spiegelt die Glyphbench: Exporter friert Wort-Crop +
  Maske + Skelett ein (Frozen-Reference-Regel gilt auch für die
  Registrierung: Skala aus der Lineatur, begrenzte, reportete
  x-Verschiebung); Runner komponiert mit `core/compose.py` aus den
  eingefrorenen Templates. Scores: Ganzwort-Tor (Stilmetrik),
  Übergangszonen-Score (Spannen zwischen Buchstaben-Kernen + Join-Winkel),
  Spacing-Score. Ein Skript pro Lauf, eigene Baseline, neues §6 in
  [`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md), Dateien auf
  die Frozen-Liste des `/optimize-glyphs`-Loops.
- Sütterlins Abbildung 20 liefert zusätzlich isolierte **Paar-Fixtures**
  (Buchstabenverbindungen) — die direkteste Übergangs-Referenz.
- Strenge Ganzwort-Tore nur gegen **gleiche Hand** (§3); Fremdhand-
  Vorlagen (Vos, Petzendorfer) nur für Form-/Übergangs-Scores mit
  Per-Buchstabe-Alignment.

### Phase D — Übergangs-Redesign gegen die Bench (erster Lauf umgesetzt: PR #145, `bench_loss` 0.1397 → 0.1206; Log in qualitaetsmetrik.md §6)

Mit Messinstrument, im Keep/Discard-Loop:

- **Exit-Klassen pro Stil** {Grundlinie · halbhoch (t, mit Absetzen +
  Punktschleife) · Mittelband-Bogen (Sütterlin o/b/v/w) · Anschluss-Bruch
  (q, x, d, ß — Folgebuchstabe setzt frisch an)} — endlich
  `entry_coupling`/`exit_coupling` konsumieren. Achtung Stil-Split:
  Kurrent-v/w binden von der **Grundlinie** an (Mücke-Schreiblehrgang),
  der Mittelband-Bogen ist ein Sütterlin-Merkmal.
- Gerades Diagonal-Mittelstück für Grundlinien-Joins; „dip unters
  Mittelband"-Kurve nach o/b/v/w; hoch in e einlaufen, an den Bogenfuß
  in n/m; Richtung e/s flacher (Gleichmaß-Spacing).
- Gap paarabhängig aus `advance`/Tinten-Ausdehnung + Kollisionsschutz.
- G2-Joins (quintische Hermite bzw. Arc-Blend: Position + Tangente +
  Krümmung an beiden Enden) statt kubischem G1.
- Kurrent: Schwellzug-Taper des Konnektors aus lokalen Endbreiten statt
  Median.

Parallel, getrennt davon: die Authoring-Fixes aus §1.3 Punkt 2 im Admin
(gesperrte Glyphen bleiben Sache des Autors).

### Phase E — später (nach C/D bewährt)

- Additive `word_samples`-Tabelle (Migrationsmuster 0007/0009) +
  „Wörter"-Modus im Einrichtungs-Wizard (Crop/Radierer/Lineatur/Schräglage
  übernehmen sich 1:1 — `crop_with_mask` nimmt ein bbox-Dict).
- **Chain-Fit**: `fit_template_to_instance` pro Buchstabe auf Fenstern des
  Wort-Skeletts → schreibt `instances` → wörtlich der Pfad zu den
  MVP-Gates 1–3 (≥10 Fits, Allograph-Trennung, `denen` aus Aggregaten).
- Beobachtete Paar-Geometrie wird dabei nur gemessen und berichtet —
  die Evidenz, die Vorschlag B für seine offenen Punkte (b)/(c) braucht.
- Kein Nachzeichnen fürs Wörter-Ausschneiden nötig (die Bench-Referenz
  Maske+Skelett braucht keinen Duktus-Prior); Nachzeichnen nur als
  Fallback-Prior für den Chain-Fit (§7-Forschungsrisiko).

---

## 3. Verifizierte Wortvorlagen (Stand 2026-07-01)

Alle URLs gefetcht, Bilder gesichtet, Lizenz-Mathematik geprüft.
Kern-Eigenschaft: die Top-Vorlage jeder Tafel ist **dieselbe Hand** wie
die jeweilige Buchstabentafel im Repo.

| Schrift | Vorlage | Inhalt | Lizenz |
|---|---|---|---|
| Sütterlin | **Abbildung 19** „Die Ausgangsschrift im Zusammenhang geschrieben (mit Kugelspitzfeder)", Leitfaden 1922 — [Commons](https://commons.wikimedia.org/wiki/File:S%C3%BCtterlin,_Schriftprobe_(deutsche_Kurrent).png), 1756×1783 px | ~50 verbundene Wörter (Soldatenlied), gleiche Ausgangsschrift wie Abb. 10 | PD (Sütterlin † 1917, §64 seit Ende 1987 abgelaufen; US < 1930) |
| Sütterlin | **Abbildung 20** „Einige Beispiele für nicht selbstverständliche Buchstabenverbindungen" — [Commons](https://commons.wikimedia.org/wiki/File:S%C3%BCtterlin,_Beispiele_f%C3%BCr_Verbindungen_(deutsche_Kurrent).png), 1869×976 px | 4 Zeilen Buchstabenpaare (bb be bz db do dt … Du Ju Of Wu) — Ground Truth für generierte Übergänge | PD, dito |
| Sütterlin | Komplettes Leitfaden-Digitalisat, [DNB-Bookviewer](https://portal.dnb.de/bookviewer/view/1124005439) (99 Blätter) | Reserve für weitere Tafeln (auch Abb. 35, lateinische Variante) | PD, dito |
| Kurrent | **Loth 1866**, Damen-Briefsteller, gravierte Vorschrift-Seite (0-basierter PDF-Index 14) — [archive.org](https://archive.org/details/derdamenbriefst00lothgoog) | ~40 große Wörter in Sätzen, gleiche Hand wie das Repo-Chart | PD (1866) |
| Kurrent (Fremdhand) | Vos p295 „Im Schuhladen"-Fortsetzung — [Commons](https://commons.wikimedia.org/wiki/File:Vos-essentials-of-german-p295-raw.png) | ~95 Wörter, keine Lineatur, Foto mit Wölbung | PD (Repo-Rationale vos-1903) |
| Kurrent (Fremdhand) | Petzendorfer 1889 Tafel 1, Textprobe (archive.org `schriftenatlasei02petz`, n18) | ~70 Wörter, kalligrafisch ~57° | PD (Repo-Rationale petzendorfer-1889) |
| Offenbacher | **Koch 1928**, dasselbe Heft wie im Repo, 0-basierter PDF-Index 39 | ~110 verbundene Wörter von Kochs Hand | PD (Koch † 1934) |

Verworfen: **Schulheft 1929 Berlin** (Commons) — inhaltlich ideal
(Übungssätze auf Lineatur), aber Schüler-/Lichtbildrechte ungeklärt →
kommt nicht ins Repo. Vor jedem Vorlagen-Commit: `/audit-licenses` +
`SOURCE.md`-Batterie.

Pädagogische Verbindungsregeln (Quellen für Phase D):
[Mücke-Schreiblehrgang Kurrent](https://www.kurrent-lernen-muecke.de/pdf/Schreiblehrgang%20Kurrentschrift%202016.pdf)
(Exit-Klassen, e-vs-n-Ansatz, Anschluss-Brüche),
[suetterlinschrift.de](https://www.suetterlinschrift.de/Lese/Sutterlin0.htm),
[Cogncur-Typeface-Doku](https://cogncur.com/documentation/typeface-features)
(3-Klassen-Join-System einer Schul-Schreibschrift, SIL-OFL, Quellen
einsehbar).

---

## 4. Bewusst nicht gewählt

- **Statisches Per-Stil-Glyph-JSON auf dem CDN** (statt Schreib-API):
  löst zwar Kaltstarts, zementiert aber die Client-Komposition (Bench
  bliebe blind), macht Varianz-Sampling unmöglich und schafft einen
  zweiten Daten-Verteilkanal. Die Cache-Header + CF-Regel auf der
  Schreib-API erreichen dasselbe Latenzziel ohne diese Kosten.
- **Anstrich/Übergang als autorisierten Duktus-Bestandteil speichern**
  (Overlap-Blend authored Stubs): re-Authoring-Last auf jeder Glyphe und
  Spannung zu §4; falls sich generierte Übergänge als unzureichend
  erweisen, ist Vorschlag B (beobachtete Overrides) der sanktionierte Weg.
- **Wort-Bench über Node/TS-Komposition** (statt Python-Port): bräche den
  hermetischen uv-only-Bench-Vertrag und ließe Extraktions- und
  Kompositionscode in zwei Sprachen auseinanderlaufen.
