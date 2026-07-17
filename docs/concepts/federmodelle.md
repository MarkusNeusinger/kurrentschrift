# Federmodelle — drei Schriften, drei Federn, ein Renderpfad

Stand: 2026-07-08. Dieses Dokument hält die Entscheidungen fest, mit denen
das System alle drei Grundvorlagen (Kurrent · Sütterlin · Offenbacher)
**schreiben** kann: dieselbe Bibliothek, derselbe Composer, dieselbe
Animation — nur die Feder ist pro Stil eine andere. Es ergänzt
[`architektur.md`](architektur.md) §5 (Width-Profile-Resolver) und §11
(Animation) um die konkreten Federmodelle und den Glyphraum für Ziffern
und Satzzeichen.

Leitgedanke (unverändert §5): **Das gespeicherte `half_widths`-Profil
bleibt immer die Messung.** Die Feder wird zur Renderzeit aufgelöst
(`styles.width_resolver` → `core/widths.py`), nie beim Ableiten.

---

## 1. Die drei Federn

| Stil | Feder | `width_resolver` | Breitenquelle beim Schreiben |
|---|---|---|---|
| Sütterlin | Redisfeder (Kugelspitze) | `constant` | EIN Quellen-Nib (gepoolter Median, `pooled_constant_nib`) |
| Kurrent | Spitzfeder | `pressure` | Die Messung selbst (der Schwellzug IST das Profil); **generierte** Striche = Haarstrich |
| Offenbacher | Bandzugfeder | `broad_nib` | **Regeneriert** aus dem Federmodell `BroadNib` (Richtung → Breite) |

Träger im Code: `core/widths.py` (`BroadNib`, `PenStyle`,
`resolve_half_widths`), `core/template.py::chisel_union_rings` (der
Meißel-Sweep), `core/compose.py::apply_pen` (generierte Striche),
`api/rendering.py::pooled_pen` (Kalibrierung pro Quelle, memoisiert wie
der Gleichzug-Nib).

---

## 2. Bandzugfeder (Offenbacher)

Primärquelle: Rudolf Koch, *Die Offenbacher Schrift* (Heintze &
Blanckertz, 1928; PD, Koch † 1934). Kernaussagen (S. 6–12):

- Die breite Stahlfeder wird **ohne allen Druck** geführt; die Spitzfeder
  ist ausdrücklich verboten. Koch verwirft den Schwellzug explizit.
- Die Schneide bildet einen **konstanten Winkel von 15° zur
  Waagerechten**; Grundstriche stehen bei 78–80° zur Grundlinie,
  Lineatur 2:3:2 (mittenbetont).
- Kalibrierpunkt: der Aufstrich ist **≈ ¼ des Abstrichs** (S. 11); der
  flachere 7-Stamm ist „merklich dünner“ (S. 20) — Breite ist reine
  Richtungsfunktion.

### Breitengesetz

Die Feder ist ein Rechteck W × t (Breite × Kantenstärke) unter festem
Winkel `alpha`. Effektive Strichbreite senkrecht zur Laufrichtung `phi`
(Stützbreite des Rechtecks, exakt für den Minkowski-Sweep):

```
w_perp(phi) = W * |sin(phi - alpha)| + t * |cos(phi - alpha)|
```

METAFONTs `penrazor` ist der t=0-Idealfall; t ist die physische Kante,
die nie eine Nullbreite schreibt. Winkelkonvention: Grad, gegen den
Uhrzeigersinn ab +x, im Template-Raum (y nach oben, Grundlinie 0) — die
Schräglage steckt bereits in den gemessenen Ankern, `alpha` ist also
absolut im Template-Raum wohldefiniert.

Kochs ¼-Regel fällt aus dem Gesetz heraus: bei `alpha = 15°` schreibt
der Aufstrich (~29°) `|sin(14°)| ≈ 0,24` der Vollbreite, der Abstrich
(~79°) `|sin(64°)| ≈ 0,90` — Verhältnis ≈ ¼. Der Test
`tests/test_tri_script.py::test_broad_nib_koch_quarter_upstroke` pinnt das.

### Silhouette (Meißel-Sweep)

Für die feste Feder sind die beiden Konturseiten **Translationen der
Centerline um den konstanten Halbfeder-Vektor** `h = (W/2)(cos α, sin α)`
— keine Normalen-Offsets. Implementiert als Vereinigung der konvexen
Hüllen des an beiden Segmentenden gestempelten Rechtecks
(`chisel_union_rings`, Shapely-Union wie die Kapsel-Union): Meißelkanten
an Strichenden fallen gratis heraus (die gestempelte Federkante IST die
Kappe — **nie runde Kappen für `broad_nib`**), Schleifen und
Richtungsumkehr löst die Union auf. Payload-Kontrakt (Rings + evenodd)
unverändert.

### Messung vs. Modell

Beim **Schreiben wird regeneriert**, die Messung dient nur der
**Kalibrierung** pro Quelle (`pooled_pen`: W = 2·P95, t = 2·P10 der
gepoolten Mess-Halbbreiten; `alpha` bleibt die gelehrte Konstante 15°
und wird nie pro Request gefittet). Gründe:

1. Warp-Invarianz: jede Pfadtransformation (Fluent-Weitung,
   Schräglagen-Normalisierung, M4-Fit) ändert Tangenten — gemessene
   Breiten wären danach physikalisch falsch, das Modell rechnet sie aus
   den *neuen* Tangenten nach.
2. Generierte Übergänge haben gar keine Messung.
3. Konsistenz: eine Feder pro Quelle (Spiegel der `pooled_constant_nib`-
   Entscheidung), Binarisierungs-/Kreuzungsrauschen fällt weg.

Die **Diagnose** (Admin, Wizard-Vorschau, Bench) vergleicht weiterhin
die Messung gegen die Chart-Tinte — dort würde das Modell
Extraktionsfehler verdecken. `resolve_half_widths` regeneriert nur, wenn
die Geometrie mitgegeben wird; ohne `points` fällt `broad_nib` auf die
Messung zurück (der bisherige Stub-Pfad, jetzt dokumentiertes Verhalten).

### Verworfen

- **Gemessene Breiten direkt rendern** (der alte Stub): bricht bei jedem
  Pfad-Warp, kann Übergänge nicht einfärben, konserviert Scan-Artefakte.
- **Runde Kappen/Kapseln für Breitfeder-Striche**: physikalisch falsch —
  das Strichende einer Bandzugfeder ist die gestempelte Kante.
- **`alpha` pro Quelle fitten**: eine grobe Regression auf dem
  Koch-Chart streut ±10° (Kreuzungs-/Lineaturkontamination); der
  gelehrte Winkel ist die verlässlichere Konstante. Ein Fit auf sauberen
  Langstrichen bleibt als Authoring-Diagnose denkbar (Proposal-Stoff).

---

## 3. Spitzfeder (Kurrent)

Physik: Druck spreizt die Zinken — Breite ist Druck-, nicht
Richtungsfunktion; aber Druck ist nur auf **Grundstrichen (abwärts)**
möglich, Aufstriche und Verbindungen sind **Haarstriche** (eine
aufwärts geschobene Spitzfeder gräbt sich ein). Konsequenzen:

- **Glyphen**: die Messung bleibt der Renderer (`pressure` = Identität,
  unverändert) — der gemessene Schwellzug ist das Authentischste, was
  wir haben.
- **Generierte Striche** (Übergänge, Endstrich): werden auf den
  gepoolten Haarstrich der Quelle gekappt (`PenStyle.hairline_half` =
  P10 der gepoolten Mess-Halbbreiten, `apply_pen` in `core/compose.py`).
  Vorher erbten sie die Median-Breite der Nachbarglyphen — auf
  Schwellzug-Profilen viel zu fett.
- **Synthese-Modell** (post-MVP, Anschluss an §5 „richtungsabhängiger
  Breiten-Prior“ und §12): Breite aus signierter Richtung
  `a = max(0, -t̂·d̂)` (d̂ = Abstrichrichtung entlang der Schräglage),
  `w = h_hair + (h_max - h_hair)·a^p` mit p ≈ 2, Anschwell-/Abschwell-
  Rampen (L_attack < L_release), Umkehr-Guard `w ≤ 0,8/κ`. Gebraucht
  für: Retrace-Trennung (§5 „Sonderfall Retrace“), Reparatur
  verblasster Tinte, Fremdquellen-Glyphen. Kalibrierung h_hair = P10,
  h_max = P95 der Quelle. Symmetrische Modelle (METAFONT-Ellipse)
  scheiden aus: sie schattieren Auf- wie Abstrich gleich.
- **Natürlichkeitsmetrik Kurrent** (Vorschlag, noch NICHT gebaut —
  Kalibrierung braucht eigene Disziplin nach
  [`qualitaetsmetrik.md`](../reference/qualitaetsmetrik.md)):
  (1) Spearman-Korrelation Breite↔Abwärtsanteil ≥ ~0,5, (2)
  Haarstrich-Boden auf Aufstrichen, (3) Kontrast median(Schatten)/
  median(Haarstrich) in [2, 8] (Zinkenphysik ≈ max 6×), (4)
  Schwellglattheit |dw/ds| begrenzt + Unimodalität pro Schattensegment,
  (5) Schattenlage im Schräglagen-Korridor (±30°), (6) Umkehr-Release
  w·κ ≤ 0,8. Bis dahin bleibt der Kurrent-Bench die Pixel-Metrik §1–§4
  (Baseline 0,1251 — reproduziert am 2026-07-08).

---

## 4. Ziffern und Satzzeichen

### Glyphraum

Ziffern `0–9` und Satzzeichen sind **eigene Glyphen mit `joins: false`**
(„detached“): sie rendern, aber kein Übergang läuft je hinein oder
heraus — auf allen drei Tafeln stehen sie unverbunden. Registry-Basen
(ascii-sicher, `{base}-{position}`-Keys wie Buchstaben):

```
0…9 · period · comma · semicolon · colon · exclam · question ·
apostrophe · quote-low („) · quote-high (“) · hyphen · dash ·
paren-open · paren-close · section
```

Träger: `core/shaping.py` (`_DIGITS`/`_PUNCT`) und die TS-Zwillinge
`app/src/domain/glyphs.ts` (Gruppen `digit`/`punct`) +
`app/src/domain/shaping.ts` — **im Gleichschritt halten** (bestehende
Regel). Aliasse: `’`→`apostrophe`, `”`→`quote-high`, `‐ ‑`→`hyphen`,
`—`→`dash`. Das gerade `"` wird über die Vorkommens-Parität im Wort
aufgelöst: erstes `"` → `quote-low`, zweites → `quote-high` — so öffnet
auch `("Ja")` korrekt tief.

Konventionen aus den Primärtafeln:

- **Bindestrich = schräger Doppelstrich ⸗** (U+2E17; 1889 handschriftlich
  belegt, auf der Koch-Tafel gelehrt): ASCII `-` mappt auf DIESE Glyphe.
  Gedankenstrich `–` ist ein eigenes, langes Template (beidseitig
  gespatiiert — das Spatium tippt der Nutzer, kein Shaping-Fall).
- **Anführungszeichen**: Paare schräger Doppelstriche, öffnend tief auf
  der Grundlinie („), schließend hoch an der Oberlinie (“).
- Ziffernhöhen sind **Template-Daten, kein Code**: Sütterlin lining
  ~1,5 Einheiten aufrecht; Offenbacher springend (3 4 5 7 9 unter die
  Grundlinie); Kurrent 1889 halbspringend (7 9). Sütterlin-7 ohne,
  Koch-7 mit Querstrich — reine Template-Sache.
- Satzzeichen sind **nicht quizbar** (`quizKeysFromLocked` filtert
  `punct`); Ziffern sind es — Zahlenlesen ist eine echte Übung.

### Shaping (Positionen pro Lauf)

Positionen werden **pro Lauf gleicher joins-Klasse** vergeben: das
Komma in „Haus,“ stiehlt dem s nicht mehr die Endposition — das
**Schluss-s bleibt rund** (behobener Altfehler; vorher las `Haus,` das
s als medial → Lang-ſ). Ein Ziffernblock „1922“ löst
initial/medial/final intern auf; seit dem Positions-Rückbau (Redesign R2)
trägt ohnehin jede Glyphe genau EINEN Basis-Key — die Position ist reiner
Slot-Kontext.

### Composer

Ein detached-Slot wirkt wie eine Wortgrenze: der Buchstabenlauf davor
bekommt **Endstrich + Diakritika-Flush**, dann wird die Glyphe rein
über Tintenabstand platziert (`NONJOIN_CLEARANCE`, satzzeichen-eng,
ziffern-gleichmäßig; zwischen zwei detached-Glyphen gewinnt der
kleinere Abstand), erster Strich mit `lift: true`. Der Abstand misst
die **ganze** Tinte (nicht das Join-Band — ein Komma hängt unter der
Grundlinie, ein Anführungszeichen über der Mittellinie). Diakritika-
Deferral gilt für detached-Glyphen nie (der zweite Strich eines „“
darf nicht ans Wortende wandern). Buchstaben-only-Eingaben bleiben
**byte-identisch** (Golden-Fixture unverändert grün).

### Quellenlage fürs Authoring

| Schrift | Ziffern | Satzzeichen |
|---|---|---|
| Sütterlin | auf der aktiven Tafel (Ziffernzeile unten) | auf der aktiven Tafel (Zeile 5 rechts) |
| Offenbacher | auf der aktiven Koch-Tafel (Zeile 3) | ebd. (inkl. ⸗ – § und Klammern) |
| Kurrent | **nicht auf Loth 1866** — Petzendorfer 1889 (im Repo, PD) hat eine Ziffernzeile; als **eigene Source** seeden (~57° vs. Loth ~50°, fremde Hand — nie in die Loth-Hand mogeln) | **keine isolierte PD-Vorlage**; nur In-Gebrauch-Instanzen (Petzendorfer-Textkasten, Vos 1903). Optionen: Ausschnitt-Authoring aus den Textproben oder eigene Hand |

### Verworfen

- **Eigene Position `isolated`** für Ziffern/Satzzeichen: bricht die
  uniforme Fan-out-/Lock-/Sidebar-Maschinerie für einen rein kosmetischen
  Unterschied; die drei Positions-Keys tragen identische Formen.
- **Ziffern per exit→entry anbinden**: alle drei Primärtafeln zeigen
  Ziffern und Zeichen unverbunden; Anstriche verbinden nie.
- **Petzendorfer-Ziffern in die Loth-Quelle patchen**: fremde Hand,
  andere Schräglage — Provenienz bleibt pro Source sauber getrennt.

---

## 5. Animation („wie von Zauberhand“)

Der Masken-Sweep (§11, `animation-rendering.md`) trägt alle drei Federn:

- Der Client füllt `rings` und strokt nur ringlose Items — Breitfeder-
  Übergänge kommen deshalb als **Rings am Konnektor-Item** an, null
  Client-Änderung.
- Breitfeder-Deckung: Tinte liegt **asymmetrisch** um die Centerline
  (±Halbfeder-Vektor); die runde Maskenfront deckt sie ab, solange
  `mask_width ≥ Federbreite + Rand` — der Composer setzt für
  `broad_nib`-Items `mask_width ≥ 1,15·W`. Kosmetische Grenze: die
  sichtbare Front ist rund statt Meißelkante — erst der Canvas-Stroker
  (§11 post-MVP) behebt das; fürs finale Bild ist der Sweep exakt.
- Timing-Realismus (Folgearbeit, rein Frontend): Zwei-Drittel-Gesetz
  `v ∝ κ^(-1/3)` als Zeitgewichte `w_i = Δs_i·(1 + κ_i·r_ref)^(1/3)`,
  Strichdauer sublinear `T ∝ L^β` (β ≈ 0,5), 80–200 ms Absetzpausen —
  als WAAPI-Keyframes mit Offset-Arrays auf dem bestehenden
  dashoffset-Pfad, kein Renderer-Umbau.

---

## 6. Offene Punkte / Folgearbeiten

1. **Authoring-Backlog**: Sütterlin S–Z/ß/Ligaturen + Ziffern/Zeichen
   (alles auf der aktiven Tafel); Offenbacher Alphabet ab c + Ziffern/
   Zeichen; Kurrent-Restalphabet ab Loth. Reihenfolge: Sütterlin-Ziffern
   zuerst (öffentlich sichtbarster Gewinn).
2. **Petzendorfer-1889-Source** für Kurrent-Ziffern seeden (Migration
   nach 0006/0008-Vorbild) — erst bei Authoring-Bedarf.
3. **Offenbacher-Natürlichkeitsmetrik** (w(φ)-Fit, Winkelkonsistenz)
   nach genug authored Templates; bis dahin läuft der Bench über die
   Pixel-Metrik (`STYLE_TO_RESOLVER` kennt `offenbacher` bereits).
4. **Wordbench-Referenzen** Kurrent/Offenbacher: Loth S. 14 bzw.
   Koch-Heft „grüßen“-Proben + Schultafel-Fotos (PDF-Index 19–20,
   38–39; §66-UrhG-Prüfung vor Commit) — eigene words.json-Sidecars.
5. **Wizard-Vorschau** (`written_preview_for_canonical`) zeigt für
   `broad_nib` noch die Messbreiten; auf Modellbreiten umstellen, sobald
   das Authoring Offenbacher erreicht.
6. **Kurrent-Synthese-Modell + Metrik** (Abschnitt 3) als eigener,
   kalibrierter Schritt.
