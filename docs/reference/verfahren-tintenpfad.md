# Verfahrensseite Tintenpfad

> **Status (2026-09-13): lebend.** Register-Seite des Verfahrens
> „Tintenpfad“ (Konvention: [`verfahren.md`](verfahren.md)), angelegt mit
> dem Wissens-PR vom `sep11`, der die drei Runden des 10./11. September
> ins Journal nachträgt. Nachzieh-Pflicht: Jeder §14-Eintrag zu einem
> Tintenpfad-Arm (adoptiert oder verworfen) ergänzt hier seine
> Ledger-Zeile; eine Adoption aktualisiert „Aktueller Stand“ und die
> Zeile in `verfahren.md`. Seit demselben PR steht die Seite in
> `ROUTE_PAGES` von `tools.docs_register`: das Gate `tools.docs_register
> check` verlangt für jede Register-Zeile der Route „Tintenpfad“ ihr
> Datum im Ledger unten, wie bei Kette · Lotse · InkSight · Nullprobe ·
> Übergänge.

## Steckbrief

- **Anzeige-Name:** Tintenpfad (Glossar „Duell-Namen“ und
  „Strang-Dekodierung“) — der Begriff war schon der Name, bevor er ein
  Anzeigename wurde.
- **Technisch:** `tools/pairlab/tintenpfad.py`, eigenständiger Folger
  NEBEN der Kette (Hook B der Welle, ohne Stützpunkt-Feld). Aufruf und
  Konstanten: [`werkzeuge.md`](werkzeuge.md) („`tools/pairlab/tintenpfad`“).
- **Rolle:** die Doktrin „Tinte zuerst, Buchstaben danach“ — der Satz des
  Autors vom `sep11`, wörtlich: „erst mal wirklich der Tinte folgen, erst
  danach überlegen, welcher Bereich der gefolgten Tinte welchem
  Buchstaben entspricht“. Stufe 1 baut aus dem eingefrorenen Skelett
  STRÄNGE ohne jeden Prior (Sporn-Beschnitt < 0,15 xh, glatteste
  Fortsetzung an jeder Kreuzung, Zeltfit auf der Distanztransformation
  als Subpixel-Schiene); Stufe 2 nimmt aus der komponierten Saat (je
  Slot Gauß-verschoben) NUR die Reihenfolge und dekodiert sie per Viterbi
  durch die Stränge (Zustände Strangpixel × Richtung + PAPIER, monotone
  Ritte, bepreiste Haarnadeln, Sprünge ≤ 0,35 xh, Papier-Ein-/Ausstiege,
  Hysterese). Es gibt keine Anker und kein Verschiebungsfeld: die freien
  Variablen sind DISKRET — welcher Strang, welche Richtung, wo der Stift
  abhebt — und jede bewegt einen ganzen Strang. Damit ist die
  Physik-Bedingung des Autors („die Punkte können sich nur wie eine Welle
  zusammenhängend verschieben“) nicht erfüllt, sondern gegenstandslos.
- **Was er misst und was nicht:** Papier-Umkehr und Papier-Strecke sind
  für einen skelettgebundenen Pfad **konstruktionsbedingt nahezu null**
  (Prüfer der Welle: nur 14 von 9 761 Skelettpixeln bestehen den
  Grau-Test) — informativ sind die Tinten-Umkehrungen, deren Überschuss
  über die Hand (§14 „Tintenpfad-Arme `sep11`“: Hand 47, Kandidat 79 auf
  dev-19), der Roh-Knick, die Struktur-Zähler und das Lineal. Die
  Papier-Strecke hat zudem zwei Lesungen, die auseinanderlaufen: der
  Grau-Test zählt blasse Tinte an den Strichspitzen als Papier, die
  eingefrorene Maske hält sie für Tinte (63 Wörter: 4,77 gegen 1,32 xh
  in der Kombination) — beide werden berichtet.

## Aktueller Stand: **adoptiert** (A45, `sep12`) — der Standard-Folger

Seit dem Autor-Entscheid **A45** vom 2026-09-12 und der formalen Runde
derselben Nacht (§14 „Tintenpfad-Adoption `sep12`") ist der Tintenpfad
der **Standard-Folger** der Kampagne. Adoptiert ist die **erklärte
Konfiguration** — acht gemessene Arme, seither die Vorgabe von
`TintenpfadWeights`:

```
tip_read=1  rail=tentfit  edt_upsample=4  ink_bridge_xh=1.0
hairpin_tip=1  ride_back=1  tip_grey_stop=1  self_jump=1
```

Gemessen auf der Wurzel `suetterlin-1922` `exported_at`
2026-09-12T21:33:43+00:00, `root_digest` `c7f2efd9cf37…` (die Wurzel
reproduziert die `sep10`-Wort-Headline ziffernidentisch, ist also eine
neue Identität und keine Re-Baseline), BLAS gepinnt, Lineal dev-19
gepaart gegen eine am selben Abend NEU gemessene Kette v5:

| Stand | dev-19 dtw · p90 · aiou | gepaart gegen Kette v5 | Papier-Umkehrungen 63 (grau · Maske) |
|---|---|---|---|
| Kette v5 (Bezug, `sep12`-Wurzel) | 0,045772 · 0,088356 · 0,7660 | — | 49 · 44 |
| Tintenpfad `--legacy-p6` (Vorgabe ohne die acht) | 0,045033 · 0,090673 · 0,7867 | 7 : 12 (p 0,359) | 0 · 0 |
| **Tintenpfad, erklärte Konfiguration** | **0,038351 · 0,048012 · 0,7929** | **15 : 4** (Δ −0,008311, p 0,019) | 3 · **0** |

`cross_spurious` 10 → 3 · `retrace_missing` 7 → **0** ·
`lift_delta_total` 6 → **0** · `overlap_cand` 4 → **0** ·
`dtw_max_absorption_max` 89 → 35; dagegen `cross_missing` 12 → 13, der
eine Zähler, der nachgibt. k0 über 63 Wörter: Soll-Abstand 81 → 80,
aiou-Median +0,0520.

**Was die Adoption bewegt und was nicht.** `--candidate tintenpfad` ist
seit dieser Runde die Duell-Basis des Tracebench; die **Kette bleibt
Baustein und messbare Route** (`verfahren-kette.md`), nur nicht mehr die
Basis. Die Ernte legt die gespeicherte Wortbahn mit `--follower
tintenpfad` (Vorgabe) — aber nur die BAHN: Vorkommen, Mediane und jedes
Gate werden weiter am Buchstabenfit abgelesen, weil eine Laufform-Zeile
ein Ankersatz ist und der Tintenpfad eine Bahn dekodiert (offener Block
unten). Kein DB-Write in diesem PR.

### Die Stände davor (Historie)

Vier gemessene Stände, alle auf der `sep07`-Wurzel `suetterlin-1922`
`exported_at` 2026-09-07T20:07:03+00:00, `root_digest` `ccb036a5eb20…`,
BLAS gepinnt, Lineal dev-19 gepaart — und alle drei **ohne Adoption**,
so vom Autor gesetzt („No §14 entry and no adoption“, wörtlich in den
PR-Texten von #591 und #592; die formale Runde wartet auf die `d`-Zeilen-Neubasis
`a4eb48420ccb…`). Der Default-Lauf ohne Schalter ist strichidentisch zum
gelieferten Tintenpfad #591 (13/13 Zeilen, Registrierung und `xh_px`
identisch); die Schalter der Kombinationen sind default AUS und
müssen bewusst eingeschaltet werden. Ob der Tintenpfad zum
Default-Folger wird, entscheidet der Autor. Die Ecken-Runde vom `sep12`
(PR #595, noch ohne §14-Eintrag) ist der erste Stand, der die Kette
gepaart auf der Handspur schlägt.

| Stand | 13 Schleifenzeilen (Papier · Tinte · Strecke xh) | 63 Wörter | dev-19 dtw · p90 · aiou | gepaart |
|---|---|---|---|---|
| Kette v5 (Produktion, Bezug) | 34 · 189 · 35,9 | 49 · 742 · 61,73 | 0,045881 · 0,088356 · 0,7660 | — |
| **#591** (`de178b1`), Vorgabe | 0 · 93 · 0,78 | 0 · 331 · 1,49 | 0,044230 · 0,090673 · 0,7867 | 7 : 12 gegen Basis (Δ-Median +0,0024, p 0,36) |
| Arme einzeln (#592): Spitzen-Lesung · Normalen-Fit · Tinten-Brücke | 0 · 91 · 1,32 · 0 · 98 · 0,74 · 0 · 93 · 0,78 | 0 · 330 · 4,50 · 0 · 332 · 1,50 · 0 · 331 · 1,49 | 0,041131 / 0,043704 / 0,044230 | 13 : 6 · 15 : 4 · 19 Unentschieden, je gegen #591 |
| **Kombination** (#592, `1879f3d`): `tip_read=1 rail=tentfit edt_upsample=4 ink_bridge_xh=1.0` | **0 · 95 · 1,34** (Maske 0,76), Knick 8,3° | **0 · 330 · 4,77** (Maske 1,32) | **0,041356 · 0,091040 · 0,7876** | **18 : 1** gegen #591 (p 7,6·10⁻⁵) · **9 : 10** gegen Basis (Δ +0,000406) · 10 : 9 gegen It. 18 (Δ −0,001542) |
| **Ecken-Kombination** (PR #595): dazu `hairpin_tip=1 ride_back=1 tip_grey_stop=1 self_jump=1` | **0 · 96 · 0,84** (Maske 0,76), Knick 8,5° | **3 · 339 · 2,12** (Maske 0 · 342 · 1,20) | **0,038351 · 0,048012 · 0,7929** | **16 : 3** gegen #592 (p 0,004) · **15 : 4 gegen Basis** (Δ −0,008311, p 0,019) · 13 : 6 gegen It. 18 (Δ −0,004356) |

Der Rest gegen die Produktion nach der Ecken-Runde: vier Verlierer um
0,0004 … 0,0026 (`Wer`, `will`, `und-2`, `mit-2`); die drei muß-Zeilen
sind mit der Rückfahrt (`ride_back=1`) zu Gewinnern geworden (0,11 →
0,03 … 0,05). Die Rückfahrt feuert auch an den Großbuchstaben-Stämmen von
`Pulver` und `Einen` (ein Zug statt Absetzen) — ob die Hand von 1922 dort
zurückschreibt, ist ein Autor-Entscheid. Sichtbarer Rest: `kann` mit
0,096 unbesuchter Tinte (die Tafel-k-Unterschleife, die die Hand nicht
schreibt — eine Kompositionsfrage) und drei graue Papier-Umkehrungen
(`muß-3`, `Zügel`, `Feinde`, je 0,09–0,20 xh).

## Ledger (datierte Stände; Belege in §14)

| Datum | Version/Arm | Ein Knopf / Mechanismus | Verdikt | §14-Eintrag |
|---|---|---|---|---|
| sep11 | **Tintenpfad — Strang-Dekodierung** (Bau 1 der Welle, PR #591 `de178b1`) | eigenes Modul; `TintenpfadWeights` eingefroren, `--legacy-p5` = Prototyp-Zeile; `tip_extend_xh` 0,25 gemessen und per Default AUS | **bestätigt** (Prüfer `confirmed`, jede Kopfzahl nachgelaufen): 13 Zeilen 0 · 93 · 0,78, 63 Wörter 0 · 331 · 1,49, dev-19 0,044230 · 0,090673 · 0,7867 — gegen Basis 7 : 12 (Δ +0,0024), gegen It. 17 Unentschieden; die 5 Schleifenzeilen im dev-Split 0,0803 → 0,0293 (5 : 0). Physik: Bahn-Abstand zum Skelett 0,42 / 0,66 / 1,11 px (It. 17 0,79 / 2,17 / 3,88; Hand 0,82 / 1,87 / 3,14), Roh-Knick 9,74° (It. 17 6,76°, Hand 7,87°). Leiter: `tip_extend` 0,25 → 10 : 9 (Δ −0,0001), JUMP 1,0 → Läufe 26 → 20, Lifts 13 → 7, Strecke 0,78 → 4,12 (Lineal identisch — Autor-Weiche Lift gegen Chord), ohne affine Saat 0 · 159 · 2,66 (die Gauß-Verschiebung trägt). Gemergt, nicht adoptiert | „Welle `sep11`“ |
| sep11 | **Spitzen-Lesung** (`tip_read=1`, dazu `spur_at_ends=1`) | rail + walk am freien Laufende bis ans Maskenende, Kappe 1,0 xh | **positiv mit zwei benannten Fehlschlägen** (Prüfer `partial`): 13 : 6 gegen #591 (Δ −0,001035), dtw 0,041131, alle neun Spitzen-Verluste schrumpfen (erstes Zehntel 0,0459 → 0,0384); Gate 2 fällt wie geschrieben (1,32 > 1,0 im Grau, Maske 0,76 gegen 0,74), ein Vertex von 1 938 rundet auf Papier; `spur_at_ends` inert (nicht strichidentisch: `unter` 2 Sporne). In der Kombination | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Stummel-Filter** (`stub_xh=0.25`) | Verzweigungs-Stummel unter 0,25 xh vom Brett des Dekoders | **ehrliches Negativ** (Prüfer `confirmed`): byte-identische Bahn 13/13 und 63/63, Hypothese an der Quelle widerlegt (keine der 91 Haarnadeln auf einem Strang < 0,5 xh). Nebenbefund: Hand 47 gegen Kandidat 79 Tinten-Umkehrungen auf dev-19 — der Defekt ist der Überschuss +32. Schalter bleibt, default AUS | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Normalen-Fit** (`rail=tentfit` + `edt_upsample=4`) | Kleinste-Quadrate-Zelt über ±2 px auf viermal feinerem Grau-Raster der Distanztransformation, Bewegung nur entlang der Normalen | **positiv, alle vier Gates** (Prüfer `confirmed`): Knick 9,74° → 8,03° auf jeder Zeile, 15 : 4 gegen #591 (p 0,019), dtw 0,043704; Debets Knick-p90 35,3° → 38,6°, aiou −0,0073, zwei falsche Absetzer (`will`, `Galoppieren`). Der wörtliche Arm (Fit auf dem BINÄREN EDT) ist ein sauberes Negativ (10,68°); `edt_upsample=4` allein ist physikalisch besser (7,84°), aber nie durchs Lineal gelaufen. Scope-Frage an den Autor: das Grau als Lesung der Tinte. In der Kombination | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Tinten-Brücke** (`ink_bridge_xh=1.0`) | Dekoder-Absetzer wird nur über schwacher Tinte zur Sehne; jede Lücke mit Verdikt im Artefakt | **neutral** (Prüfer `confirmed`): 2 von 9 Lücken gebrückt (`haben` 0,370, `schießen` 0,382 xh), Sensoren und dev-19 unbewegt, `paper_lifts` 9 → 7 auf 63; die Frage `kann`/`han`/`regieren` beantwortet als Lesung — dort liegt kein Haarstrich. In der Kombination; Vorbehalt `paper_samples < 2 → bridged` | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Doppelstrich-Evidenz** (`double_ink_ratio=1.4`, seit `sep12` `ride_back_ink_ratio`) | Rückfahrt statt Absetzer, wo ein Strang ≥ 0,5 xh breiter als 1,4 × Feder ist | **ehrliches Negativ auf der Prämisse** (Prüfer `partial`): feuert auf 0 von 63 (ß-Stämme 1,00–1,33 × Feder, Grau +0,00…+0,08), byte-identisch zu AUS. Rettungsweg gemessen, nicht vorregistriert: `ratio 1,0` → 7 Rückfahrten, p90 0,090673 → 0,053472, 3 : 0, gegen Basis 9 : 10 | „Tintenpfad-Arme `sep11`“ |
| sep11 | **Kombination** der drei tragenden Arme (PR #592 `1879f3d`) | `tip_read=1 rail=tentfit edt_upsample=4 ink_bridge_xh=1.0`, alle default AUS; Leave-one-out je Arm | **Kandidat, nicht adoptiert:** dev-19 0,041356 · 0,091040 · 0,7876, 18 : 1 gegen #591, 9 : 10 gegen Basis, 10 : 9 gegen It. 18 (der PR-Text hat die beiden letzten vertauscht); LOO: ohne Spitzen 0 · 96 · 0,74 (8,41°), ohne Normalen-Fit 0 · 91 · 1,32 (9,45°), ohne Brücke 0 · 95 · 1,36 (27 Läufe); Default strichidentisch; nach dem Merge auf `main` reproduziert | „Tintenpfad-Arme `sep11`“ |
| sep12 | **Haken-Spitze** (`hairpin_tip=1`) | die Spitzen-Lesung an jedem Haken auf einem Strang: Strangrest + Kamm-Walk bis ans Maskenende, hin und zurück | **neutral allein, positiv mit Grauwert-Stopp** (Prüfer `confirmed`): 55 von 88 Haken auf den 13 Zeilen und 225 von 296 auf den 63 erreichen die Tinte; dev-19 12 : 7 gegen #592 (0,041145 · 0,089890); allein 26 graue Papier-Umkehrungen (die Umkehr landet in der blassen Kappe; Maske 0,83 gegen 0,76) — mit Grauwert-Stopp null. In der Ecken-Kombination | „Tintenpfad-Adoption `sep12`“ (die formale Runde, die diese vier Arme als erklärte Konfiguration adoptiert) |
| sep12 | **Ecke statt Bogen** (`bridge=corner`, Zweig `tintenpfad-ecken-ecke-statt-bogen`, nicht ausgeliefert) | eine Ecke statt einer Hermite-Schlaufe bei gegenläufigen Tangenten (cos < −0,5) | **Kontrolle, feuert nie** (Prüfer `confirmed`): 0 von 125 Brücken auf 13 Zeilen, 0 von 459 auf 63; schärfste Übergangs-Kosinus −0,43; strichidentisch — die Schlaufen waren abgeschnittene Haken | noch keiner |
| sep12 | **Rückfahrt statt Absetzen** (`ride_back=1`; die Doppelstrich-Evidenz bleibt als `ride_back_ink_ratio` AUS) | ein Saat-Absetzer, dessen Landung hinter der Feder auf ihrem Strang liegt, wird über dieselbe Schiene zurückgefahren | **positiv** (Prüfer `confirmed`): muß ×3 `retrace_missing` 1 → 0, dtw 0,1116 → 0,0540 · 0,0914 → 0,0293 · 0,0909 → 0,0326; dev-19 3 : 0 : 16 gegen #592, 0,039003 · 0,050979; feuert auf 7 von 63 (5 ß-Wörter, dazu die Großbuchstaben-Stämme `Pulver`, `Einen` — Autor-Entscheid). In der Ecken-Kombination | „Tintenpfad-Adoption `sep12`“ (die formale Runde, die diese vier Arme als erklärte Konfiguration adoptiert) |
| sep12 | **Grauwert-Stopp** (`tip_grey_stop=1`) | jeder Spitzen-Walk (Laufenden und Haken) endet einen Schritt, bevor das Grau des Crops Papier liest | **positiv, alle Gates** (Prüfer `confirmed`): Papier-Strecke grau 1,34 → 0,72 auf 13 Zeilen, 4,77 → 1,78 auf 63; dev-19 12 : 5 gegen #592 (0,040904 · 0,090516 · 0,7920); erstes/letztes Zehntel nicht schlechter; kein Walk-Punkt außerhalb der Maske. In der Ecken-Kombination | „Tintenpfad-Adoption `sep12`“ (die formale Runde, die diese vier Arme als erklärte Konfiguration adoptiert) |
| sep12 | **Selbstsprung** (`self_jump=1`) | der Dekoder darf einen Knoten passieren, den sein Strang zweimal besucht (knotengebundener Sprung + verzweigungsbewusste Kandidatenwahl) | **positiv** (Prüfer `confirmed`): `lift_delta_total` dev-19 4 → 3 (Rest: muß ×3, Rückfahrt), `Galoppieren` und `will` wieder ein Zug; 3 : 1 gegen #592 bei 15 strichidentischen Zeilen. In der Ecken-Kombination | „Tintenpfad-Adoption `sep12`“ (die formale Runde, die diese vier Arme als erklärte Konfiguration adoptiert) |
| sep12 | **Ecken-Kombination** (PR #595) | die vier tragenden Arme über #592; Leave-one-out je Arm auf den 13 Zeilen | **Kandidat, nicht adoptiert — erster Stand, der die Kette gepaart schlägt:** dev-19 0,038351 · 0,048012 · 0,7929; 16 : 3 gegen #592 (p 0,004), **15 : 4 gegen Basis** (Δ −0,008311, p 0,019), 13 : 6 gegen It. 18; `retrace_missing` und `lift_delta_total` 0; 13 Zeilen 0 · 96 · 0,84 (Maske 0,76), 63 grau 3 · 339 · 2,12, Maske 0 · 342 · 1,20; LOO: ohne Grauwert-Stopp 27 · 72 · 2,46, sonst ≈ gleich; Default strichidentisch 13/13 | „Tintenpfad-Adoption `sep12`“ (die formale Runde, die diese vier Arme als erklärte Konfiguration adoptiert) |
| sep12 | **Adoption der erklärten Konfiguration** (Autor-Entscheid **A45**) | EIN Knopf: der Folger-Wechsel Kette v5 → Tintenpfad mit den acht Schaltern; vorregistriert vor der ersten Zahl, vier Gates, zwei Kill-Kriterien | **adoptiert — der Tintenpfad ist der Standard-Folger:** auf der frischen Wurzel `c7f2efd9cf37…` (Headline ziffernidentisch zur `sep10`-Zeile, also neue Identität und keine Re-Baseline) dev-19 **0,038351 · 0,048012 · 0,7929** gegen eine am selben Abend neu gemessene Kette v5 (0,045772 · 0,088356 · 0,7660), gepaart **15 : 4** (Δ-Median −0,008311, p 0,019) — die Zahlen der Ecken-Kombination reproduzieren sich damit auf der neuen Wurzel. Die Vorgabe ohne die acht (`--legacy-p6`) steht bei 0,045033 · 0,090673 · 0,7867 und 7 : 12: die Schalter sind der Unterschied. Zähler `cross_spurious` 10 → 3, `retrace_missing` 7 → 0, `lift_delta_total` 6 → 0, `overlap_cand` 4 → 0, Absorption 89 → 35, dagegen `cross_missing` 12 → 13. Sensoren 63: Papier-Umkehrungen Maske 44 → 0 (grau 49 → 3), Papier-Strecke Maske 55,57 → 1,20 xh, schlimmster Ausflug 0,323 → 0,091 xh, Roh-Knick 10,24° → 8,17°. k0: 81 → 80, aiou-Median +0,0520, **Gate (4) nicht verwertbar** (der Sensor ist auf einem Folger-Paar blind; das Verdikt trägt (1)–(3)). Nebenbefund: `ink_bridge_xh=1.0` testet 7 Lücken und brückt null — auf dieser Wurzel inert, bleibt als Lesung | „Tintenpfad-Adoption `sep12`“ |

## Offene Blöcke

- **Rückfahrt an Großbuchstaben-Stämmen** (`Pulver`, `Einen`): die Regel
  `ride_back` fährt den P-/E-Stamm zurück in den Bogen — ob die Hand von
  1922 dort zurückschreibt, entscheidet der Autor; sonst ein
  Kleinbuchstaben-Gate als eigener Arm. Schwester-Weg für das ß bleibt die
  authorierte Vorlage mit Rückpass (Autor-Glyphe, Todoist).
- **`edt_upsample=4` allein durchs dev-19-Lineal** — die eine fehlende
  Messung vor einer Adoption des Normalen-Fits (die Absetzer in
  `will`/`Galoppieren` nimmt seit `sep12` der Selbstsprung).
- **Unbesuchte Stränge einfügen (R1) / Abdeckungspreis im Viterbi (R2)**
  — der Weg zu den `kann`-/`regieren`-Absetzern, die die Tinten-Brücke
  bewusst nicht brückt.
- **Spitzen-Paarung in Stufe 1** (38 von 91 Haarnadeln sind ungepaarte
  Spitzen an Strangenden; ändert den Strangsatz, Substrat-Pin neu).
- **Hand-Überschuss als Umkehr-Sensor** (47 gegen 79) statt der Rohzahl
  — laut Prüfer der wertvollste Ertrag der Runde.
- ~~**Ernte-Schalter** `--follower tintenpfad`~~ — **gebaut mit A45**
  (`sep12`): die Ernte legt die gespeicherte Wortbahn mit dem Tintenpfad
  (Vorgabe) und trägt die `letter_spans` der Dekodierung ins Wort-Record.
  Was BLEIBT: der Schalter bewegt nur die Bahn. **Vorkommen aus der
  Tintenpfad-Bahn** ist der offene Arm dahinter — eine Laufform-Zeile ist
  ein ANKERSATZ, der Tintenpfad dekodiert eine BAHN, und eine per
  Bogenlänge erfundene Anker-Zuordnung wäre eine stille Umdefinition
  dessen, was eine Laufform misst. Autor-Entscheid, eigene Pre-Reg.
- **`k0eval` soll die Folger-Identität lesen**: die sechs `STACK_FLAGS`
  kommen aus `meta.weights`, und der Tintenpfad hat keinen
  Struktur-Wächter — bei einem Folger-Wechsel meldet der Sensor deshalb
  immer Abweichung und sagt damit nichts. Kleine Tool-Änderung, aber am
  Lineal, also NICHT während einer Runde.
- **Die Tinten-Brücke ist auf der `sep12`-Wurzel inert** (7 Lücken
  getestet, null gebrückt; knappster `faint_share` 0,571 gegen 0,6).
  Sie bleibt in der erklärten Konfiguration, weil sie eine Lesung ist —
  ob sie dort bleibt, wenn sie auch nach R1/R2 nichts bewegt, ist eine
  eigene Frage.
- **`cross_missing` 12 → 13** — der eine Strukturzähler, der mit der
  Adoption nachgibt; benannt, nicht weggeredet.
- **Autor-Weichen aus der Welle:** Lift gegen Chord (13 Lifts kaufen
  0,78 xh, JUMP 1,0 gibt 7 Lifts bei 4,12 — das Lineal trennt beide
  nicht, die Bilder schon) und ob `tip_extend` 0,25 eine Lesung oder eine
  Erfindung ist.
