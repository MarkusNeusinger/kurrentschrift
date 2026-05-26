# Stil-Analyse

Technische Spezifikation der Stil-Analyse-Pipeline aus Vision §5 (Eigene
Schrift analysieren) und Vision §7 (Hände vergleichen). Ergänzt
[`architektur.md`](../concepts/architektur.md) §6 (Qualitätspipeline) und
§12 (Stil-Analyse-Pipeline).

---

## 1. Schichten-Modell

### Schicht 1 — Per-Instanz-Stats *(liegt vor)*

Jede gefittete Glyph-Instanz hat statistische Größen direkt im
DB-Schema (`glyphs.measurements` JSONB):

| Feld | Bedeutung | Quelle |
|---|---|---|
| `slant_deg` | Schräglagen-Winkel der Hauptachse | `core/template.py:apply_slant` |
| `mean_half_width_px` | mittlere halbe Strichbreite | `core/pipeline.py` |
| `path_length_px` | Gesamtlänge des Strichs | `core/pipeline.py` |
| `aspect_ratio` | Breite/Höhe-Verhältnis des Crops | `core/pipeline.py` |

**Erweiterungen** (folgen demselben JSONB-Pattern, keine Schema-Migration):

- `curvature_mean`, `curvature_max` — Krümmungs-Statistik entlang des
  Skeletts.
- `entry_tangent_dev`, `exit_tangent_dev` — Abweichung der Anschluss-
  Tangenten von der Norm (für Übergangs-Analyse).
- `cross_count` — Anzahl Selbstüberkreuzungen (Topologie-Indikator).

### Schicht 2 — Per-Hand-Aggregation

Pro Source `s` und pro `(glyph, position, variant)`-Bucket:

- **Cluster-Mittelpunkt** der Kontrollpunkte (Median pro Punkt nach
  Ausreißer-Entfernung — §6 Stufe 1 in
  [`architektur.md`](../concepts/architektur.md)).
- **Abweichungs-Hüllkurve** (MAD pro Kontrollpunkt oder
  Kovarianzmatrix).
- **Mittelwerte** der Schicht-1-Stats.

Resultat: pro Hand eine „Personal Canonical"-Instanz, die als Template für
beliebige neue Wörter dient (Multi-Stil-Konsequenz aus
[`architektur.md`](../concepts/architektur.md) §10).

**M5(C) der MVP-Roadmap** liefert die erste Implementierung für die eigene
Hand. Voller Ausbau zur P3-Phase.

**Speicherung:** entweder als JSONB-Feld auf `sources` (kleiner Footprint)
oder als separate `hand_stats`-Tabelle (besser bei vielen Sources). Detail
bei P3-Implementierung.

### Schicht 3 — Textunabhängige Writer-ID *(optional, post-P4)*

Klassische **Hinge-Features** nach Bulacu/Schomaker. *Textunabhängig*
heißt: zwei Texte derselben Hand werden ähnlich, *ohne* dass dieselben
Wörter darin stehen müssen. Goldstandard für forensische Writer-ID.

#### Hinge-Feature

Für jeden Konturpunkt der Schrift:

1. Zwei Vektoren betrachten — einer zum Konturpunkt `n` Schritte vorher,
   einer zu `n` Schritten danach.
2. Beide Winkel relativ zur Bildachse messen → Tupel `(φ1, φ2)`.
3. Über die gesamte Probe einen 2D-Histogramm `P(φ1, φ2)` bauen.

Dieses Joint-Distribution-Histogramm ist der Hinge-Feature-Vector pro
Hand. Vergleich zweier Hände via χ²-Distanz oder Earth-Mover's-Distance.

#### Δn-Hinge

Rotationsinvariante Variante aus Groningen: statt absoluter Winkel
Winkel*differenzen* speichern. Robust gegen leicht gedrehte Scans.

#### Alternative: ML-Embeddings

EfficientNet-B7 / ResNet-50 + NetVLAD + Triplet Loss erreicht 98–99 % auf
Writer-ID-Benchmarks (AHAWP, Khatt, LAMIS-MSHD). Black-Box, didaktisch
unbrauchbar — daher *nur* als optionale Ähnlichkeits-Engine, nicht als
Feedback-Geber für „Optimieren"-Pfad.

---

## 2. Vision-Anwendungspfade

### „Optimieren" (Vision §5a)

Pro Glyph-Instanz die Abweichung von der Per-Hand-Aggregation (Schicht 2)
visualisieren:

- **Welche Glyphe(n) bist du am inkonsistensten?** — höchste Streuung der
  Kontrollpunkt-Cluster pro `(glyph, position)`.
- **Wo weichst du am stärksten von der Norm (Loth) ab?** — Abstand
  Personal Canonical → Loth Canonical, pro Glyph.
- Konkretes Feedback, keine pauschalen Tipps.

### „Neuer Stil als Basis" (Vision §5b)

Sobald die Per-Hand-Aggregation genug Datenpunkte hat (`≥ 10` Instanzen
pro Glyph-Bucket): die aggregierte Personal Canonical wird selbst zum
Template für die Synthese-Pipeline. „In meiner Hand, aber jeden Text" —
das ist exakt der MVP-Gate-3-Mechanismus (`denen` aus aggregierten Stats),
nur jetzt produktiv für beliebige Wörter.

### „Hände vergleichen" (Vision §7)

Side-by-Side mehrerer Sources mit Heatmaps:

- **Schräglage-Heatmap:** `slant_deg` pro Glyph × Hand → Farbcode.
- **Schwellzug-Heatmap:** `mean_half_width_px` pro Glyph × Hand.
- **Glyph-Frequenz-Heatmap:** (für Beispieltext-Imports) Glyphen-
  Verteilung pro Hand.
- **Hinge-Heatmap:** 2D-Joint-Distribution side-by-side.

Kombiniert mit der Animation aus §11 lassen sich Animationen derselben
Glyphe in mehreren Händen direkt nebeneinander abspielen.

---

## 3. Heatmap-Output

### Observable Plot (Default)

Hochlevel-API auf D3. Wenig Code, gute Defaults für Histogramme,
Box-Plots, Violins, faceted plots. Standard für „Verteilung pro Glyph"-
Reports.

```javascript
// Pseudo-Code für Slant-Verteilung
Plot.plot({
  facet: { data: instances, x: "glyph" },
  marks: [Plot.boxX(instances, { x: "slant_deg", y: "source_id" })],
});
```

### D3.js (Spezial-Layouts)

Maßgeschneiderte 2D-Heatmaps (Hinge-Joint-Distributions als 2D-Histogramm)
und Side-by-Side-Vergleiche „Hand A vs. Hand B" mit Difference-Map. D3
für maximale Layout-Kontrolle.

### ECharts (Alternative)

Performant bei großen Daten, eingebaute Heatmap-Komponente. Größerer
Bundle (~1 MB+), weniger anpassbar bei wissenschaftlichen Sonderformen.
Nicht erste Wahl, aber Option für späteren Performance-Druck.

### Plotly.js

Wissenschaftliche Plots out-of-the-box (Heatmaps, Box-Plots, Violinen),
Hover-Tooltips kostenlos. Großer Footprint (3 MB+), Lizenz für
kommerzielles Hosting prüfen. Nur, wenn Tooltips-Komfort wichtig wird.

**Default-Wahl:** Observable Plot für Standard-Plots, D3.js für die
Heatmap-Side-by-Side-Vergleiche.

---

## 4. Konzeptionelle Vorlage: DigiPal / Archetype

[DigiPal](https://kdl.kcl.ac.uk/projects/digipal/) und
[Archetype](https://zenodo.org/records/5572558) (King's Digital Lab) sind
ein etabliertes Framework für allograph-basierte paläografische Analyse.
Modelliert die Hierarchie:

```
Konkrete Instanz → Allograph → Abstrakter Buchstabe
```

Das ist 1:1 unser Datenmodell
([`architektur.md`](../concepts/architektur.md) §3). **Wir übernehmen es
nicht als Code-Dependency** (Wartungslage 2024+ unklar; Django-Monolith
ist Übernahme-Aufwand), sondern als **konzeptionelle Vorlage**.

---

## 5. Toolchain

### Backend (Python)

- **OpenCV** + **scikit-image** für Vorverarbeitung — `skeletonize`,
  `medial_axis`, `distance_transform_edt` sind schon im Einsatz
  (`core/extract.py`).
- **NumPy** / **SciPy** für statistische Aggregation und Cluster-Analyse
  (Mahalanobis, MAD, KDE).
- **scikit-learn** optional für Cluster-Diagnostik (Silhouette, GMM für
  Multi-Variant-Trennung).
- **PyTorch / HuggingFace** *nur* falls ML-Embeddings hinzukommen — kein
  Default-Pfad.

### Frontend

- **Observable Plot** + **D3.js** als oben beschrieben.
- React-Komponenten als „Stat Cards" pro Glyph-Bucket (Slant, Schwellzug,
  Konsistenz).

---

## 6. Was wir nicht machen

- **Kein Deep-Learning-First-Ansatz.** Per-Instanz-Stats + Per-Hand-
  Aggregation + Hinge-Features sind klassische, erklärbare Methoden. ML
  nur dort, wo es unverzichtbar wird (Hand-Ähnlichkeits-Suche bei vielen
  Hände).
- **Keine Forensik-Behauptungen.** Schreiber-Identifikation als
  forensisches Beweismittel ist nicht das Ziel. Stil-Analyse ist
  *didaktisch* — sie hilft Lernenden, ihre eigene Hand zu sehen.
- **Keine Black-Box-Heatmaps.** Jede Statistik muss zurückführbar sein
  auf konkrete Instanzen — sonst funktioniert „Optimieren" nicht.

---

## 7. Quellen

- [Directional Hinge Features for Writer Identification (Springer)](https://link.springer.com/article/10.1007/s42979-021-00950-9)
- [Writer Identification Using Edge-Based Directional Features (Bulacu/Schomaker)](https://www.academia.edu/452798/Writer_Identification_Using_Edge_Based_Directional_Features)
- [Delta-n Hinge: Rotation-invariant Features (Groningen)](https://research.rug.nl/en/publications/delta-n-hinge-rotation-invariant-features-for-writer-identificati/)
- [Writer Identification using Directional Ink-Trace Width (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0031320311002810)
- [Skeleton Hinge Distribution (Aegean)](https://www.icsd.aegean.gr/publication_files/845140009.pdf)
- [Arabic Handwriting DL Writer ID 2024 (arXiv)](https://arxiv.org/html/2406.00409v1)
- [End-to-End DL Writer ID Arabic (Springer 2023)](https://link.springer.com/article/10.1007/s11042-023-17303-8)
- [Archetype (Zenodo)](https://zenodo.org/records/5572558)
- [DigiPal Wiki](https://github.com/kcl-ddh/digipal/wiki)
- [DigiPal Project](https://kdl.kcl.ac.uk/projects/digipal/)
- [Artificial Paleography (Speculum)](https://www.journals.uchicago.edu/doi/10.1086/694112)
- [Computational Paleography of Medieval Hebrew Scripts (CEUR)](https://ceur-ws.org/Vol-3834/paper42.pdf)
- [scikit-image Skeletonize Docs](https://scikit-image.org/docs/0.13.x/auto_examples/edges/plot_skeleton.html)
- [D3 by Observable](https://d3js.org/)
- [D3 Heatmap Gallery](https://d3-graph-gallery.com/heatmap)
- [Observable Plot](https://observablehq.com/plot/)
- [Plotly Heatmaps JS](https://plotly.com/javascript/heatmaps/)
