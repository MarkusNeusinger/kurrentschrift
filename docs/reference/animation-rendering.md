# Animation-Rendering

Technische Spezifikation der animierten Buchstaben-Tafel aus Vision §3.
Ergänzt [`architektur.md`](../concepts/architektur.md) §11 (und §5 für den
Width-Profile-Resolver).

**Kernprinzip:** Die Animation ist *direkter Effekt des Duktus-Priors*
([`architektur.md`](../concepts/architektur.md) §2). Sie zeigt nicht nur das
fertige Bild, sondern auch *wie es entsteht* — Schreibreihenfolge,
Ansatzpunkte, Schwellzug-Aufbau live.

**Wichtig — verworfener Ansatz:** Standard-SVG-Animations-Bibliotheken
(Vivus.js, GSAP DrawSVG-Plugin, `stroke-dashoffset`-Tricks auf statischen
Pfaden) animieren einen **fixbreiten** Pfad. Sie passen *nicht* zum
generativen Schwellzug-Modell mit variabler Strichbreite über Zeit. Wir
brauchen einen eigenen Renderer.

---

## 1. MVP-Stand: Silhouetten-Reveal per Masken-Sweep (`WrittenGlyph`)

**Scope (Gate 4 in [`architektur.md`](../concepts/architektur.md) §8):**
Ein Glyph spielt mit korrekter Schreibreihenfolge ab. Implementiert als
`app/src/components/WrittenGlyph/WrittenGlyph.tsx` (Quiz-Prompt und die
„Fertig geschrieben"-Stufe im Admin-Diagnose-Dialog; der Landing-Hero
schreibt Stand heute noch den GLKurrent-Font per Clip-Path und wechselt
erst nach der Wort-Komposition aus Templates auf diesen Renderer). Der
gelieferte Stand geht über das Gate-4-Minimum (konstante Breite auf der
Centerline) hinaus: enthüllt wird die gefüllte **Schwellzug-Silhouette**.

### Algorithmus (implementiert)

1. `WrittenGlyph` bezieht das Render-Payload über den geteilten
   Render-Cache (`app/src/lib/api/renderCache.ts`), der pro Wort/Tafel
   gebündelt `GET /sources/{source_id}/write/glyphs?keys=…` abruft
   (`/diagnostic` bleibt dem Admin-Dialog vorbehalten). Das Payload
   liefert pro Pen-Stroke die gefüllte Schwellzug-Silhouette — bevorzugt `outline_paths`
   (Kapsel-Union als Ringlisten: Außenkontur + Löcher, gerendert als ein
   Pfad mit `fill-rule: evenodd`, damit Schleifenaugen offen bleiben;
   Fallback: die älteren `outline_polygons`) — und die zugehörige
   `centerlines_template` (das geordnete Rückgrat jedes
   Polygons in Schreibreihenfolge, Template-Raum; `core/pipeline.py`).
   **Nicht** `skeleton_polyline_px` verwenden — das ist eine Pixel-Wolke
   aus `np.where(skel)` in Row-Major-Reihenfolge, also unsortiert entlang
   des Strichs.
2. Frontend füllt die Polygone und maskiert sie mit einem breit
   gestrichelten Pfad, der entlang der jeweiligen Centerline gesweept
   wird.
3. Der Masken-Pfad nutzt `pathLength={1}` + `stroke-dasharray: 1`; ein
   animierter `stroke-dashoffset` von `1` auf `0` lässt die Tinte entlang
   des realen Schreibwegs erscheinen.
4. Animation als **CSS-Keyframes** (Emotion), nicht WAAPI. Pro Teilstrich
   ist die Dauer proportional zur Pfadlänge (die Feder bewegt sich mit
   konstanter Geschwindigkeit), sequenziert über `animation-delay`; nach
   dem Schreibende folgt der „Eisengallus-Settle" (Tintenfarbe frisch →
   oxidiert).
5. **Mehrstrich-Duktus (Absetzen):** jeder Pen-Stroke ist ein eigenes
   Polygon mit eigener Centerline (`trace_meta.stroke_starts`, gespeist
   aus den `pen_up`-Markern im `raw_path`). Die Striche spielen
   *nacheinander*, eine Stiftabhebung bleibt eine echte Lücke (kein Pfad
   über die Lücke) — so entsteht z.B. das *u* als erster Abstrich →
   zweiter Abstrich, nicht in einem Zug.

### Code-Skizze

```typescript
// app/src/components/WrittenGlyph/WrittenGlyph.tsx (Auszug)
// Maske: gestrichelter Pfad mit pathLength=1 — Offset 1 versteckt, 0 zeichnet.
const reveal = keyframes`from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; }`;
// pro Centerline i im <mask>:
//   animation: `${reveal} ${dur_i}ms linear ${delay_i}ms forwards`
```

### UI-Controls (Ist-Stand)

- **Replay-Button** startet den Schreibvorgang neu.
- **`prefers-reduced-motion`** wird respektiert: ohne Animation steht die
  fertige Silhouette sofort da.
- Die volle Control-Leiste (Play/Pause/Reverse, Speed-Slider, Loop-Toggle)
  bleibt der animierten Tafel (`/animation`, P1) vorbehalten.

### Was MVP nicht macht

- **Kein zeitvariabler Schwellzug-Aufbau.** Die Silhouette trägt zwar das
  volle Schwellzug-Profil (variable Breite), wird aber als fertige Form
  enthüllt — der generative Strichaufbau, bei dem die Breite mit dem Druck
  über die Zeit *entsteht*, kommt im post-MVP-Renderer (§2).
- **Keine Ligatur-Animation.** Ligaturen (`ch`, `ck`, `ſt`, `tz`, `qu`, `ß`)
  kommen mit der Erweiterung des Alphabets.

---

## 2. Post-MVP: voller Canvas-2D-Stroker

**Scope:** Schwellzug-Animation für beliebige Glyphen mit beliebigen Hand-
Stilen.

### Render-Paradigma

Das Duktus-Template ist ein **generatives Kalligraphie-Modell** —
Centerline + zeitvariables Width-Profile. Klassisches Pfad-Rendering passt
nicht; korrekte Vorgehensweise:

**Pro Frame `t`:**

1. Centerline bis Parameter `t` abtasten (Bezier oder Catmull-Rom durch
   `anchors`).
2. An jedem Abtastpunkt: lokale Tangente + halbe Strichbreite aus
   `half_widths` interpolieren (Width-Profile-Resolver, siehe §3 dieses
   Docs).
3. Links + rechts der Centerline je eine Offset-Kurve berechnen
   (Senkrechte zur Tangente, Distanz = halbe Strichbreite).
4. Polygon aus Links-Kurve + reversed(Rechts-Kurve) zusammenbauen
   (geschlossener Pfad).
5. Als Canvas-Polygon füllen *oder* als SVG-`<path>` `fill="black"` rendern.

### Library-Optionen

| Option | Vor | Contra |
|---|---|---|
| **Eigener Canvas-2D-Stroker** | Klein (~5 KB), volle Kontrolle, ~60 fps, Offscreen-Canvas möglich | Eigene Stroking-Mathematik (Offset-Kurven, Mitre/Round-Joins, Tangentenbehandlung an Übergängen) |
| **CanvasKit (Skia-WASM)** | `SkPaint::getFillPath()` wandelt gestrickten Pfad in gefüllten; produktionsreife Anti-Aliasing-Qualität | ~2–6 MB WASM-Payload; Build-/Deploy-Komplexität |
| **Variable Fonts** | Hardware-beschleunigt, Standard-CSS | Kein Duktus/Schreibreihenfolge; Animation von `font-variation-settings` zwingt Rasterizer in jedem Frame → Frame-Drops |

**Default-Wahl:** eigener Canvas-2D-Stroker im Frontend. CanvasKit als
optionales Feature-Flag, wenn maximale Treue gewünscht ist.

### Choreographie via WAAPI

- **WAAPI** (Web Animations API) für Timeline-Steuerung.
- **SMIL** wird abgeraten (Chromium-Deprecation-Intent, MDN-Empfehlung,
  Spec-Empfehlung WAAPI/CSS).
- CSS-Animationen reichen nur für triviale Fälle.

```typescript
class GlyphAnimation {
  controller = new AbortController();
  playSequence(strokes: StrokeData[], speed = 1.0): Promise<void> {
    // Pro Stroke: erst Centerline-Animation, dann nächster Stroke.
    // AbortController erlaubt Pause/Restart.
  }
}
```

### Performance-Ziele

- 60 fps bei einem animierten Glyph.
- 30 fps bei einem Wort von 5–7 Glyphen, gemeinsam animiert (z.B. für
  „Wort entsteht in echter Hand"-Demo).
- Offscreen-Canvas + Web Worker, wenn nötig.

---

## 3. Width-Profile-Resolver pro Schriftfamilie

Das **gleiche Library-Schema** ([`architektur.md`](../concepts/architektur.md)
§3) trägt zwei Render-Modi. Die Stil-Eigenschaft `styles.width_resolver`
entscheidet (§5):

| Schriftfamilie | Width-Profile-Resolver | Begründung |
|---|---|---|
| **Kurrent** (vor 1900) | Druckabhängiger Schwellzug — `half_widths` wird voll genutzt. | Spitzfeder; variable Strichbreite ist Wesensmerkmal. |
| **Sütterlin** (ab 1911) | Konstant — `half_widths` wird auf den Mittelwert pro Source projiziert. | Redisfeder; konstante Strichbreite ist Designziel. |
| **Andere** | Erweiterbar (Federtyp-spezifisch). | Skandinavien / Offenbacher / Volksschrift haben jeweils eigene Federn. |

### Implementierung

```python
# core/width_profile.py (kommt mit P4-Implementation)
def resolve_widths(glyph: Glyph, source: Source) -> list[float]:
    if source.width_profile_mode == "konstant":
        return [statistics.mean(glyph.half_widths)] * len(glyph.half_widths)
    return glyph.half_widths  # Default: voller Schwellzug
```

Frontend bekommt das aufgelöste `half_widths`-Array über den existierenden
`/diagnostic`-Endpoint (Backend führt die Auflösung durch).

---

## 4. UX-Vorlage (nicht Engine): AnimCJK / Hanzi Writer

[Hanzi Writer](https://hanziwriter.org/) und
[AnimCJK](https://github.com/parsimonhi/animCJK) animieren chinesische
Schriftzeichen. Wir übernehmen ihr UX-Modell:

- **Watch-Modus:** der Charakter spielt automatisch ab.
- **Quiz-Modus:** Nutzer zeichnet einen Stroke; das System matched ihn gegen
  den Soll-Stroke und gibt Feedback (`onCorrectStroke`, `onMistake`).
- **Stroke-Outline-Modus:** zeigt nur die Centerline als Hinweis, Nutzer
  füllt den Bauch selbst.

**Render-Engine — Einordnung:** Hanzi Writer strickt fixbreite Pfade —
das übernehmen wir nicht. AnimCJKs Mask-Trick (vorgerenderte SVG-Outlines,
per Maske enthüllt) ist dagegen genau die bewusst gewählte
MVP-Zwischenstufe in `WrittenGlyph` (§1). Was wir *nicht* übernehmen, ist
der Mask-Trick als **finale** Render-Engine: den zeitvariablen
Schwellzug-Aufbau kann er nicht, dafür kommt der Post-MVP-Stroker (§2).

---

## 5. Server-seitiges Vor-Rendering (sekundärer Pfad)

Für **Thumbnails**, **Open-Graph-Vorschauen** und **Offline-Export** ist
ein server-seitiger MP4/WebM-Export sinnvoll:

- Im Backend per Headless-Canvas (z.B. `node-canvas` oder Skia-Python) Frames
  rendern.
- Frames zu MP4 zusammenfügen via FFmpeg.
- MP4 ist ~25–50× kleiner als GIF bei gleicher Qualität.

**Nicht im MVP-Scope.** Primärpfad bleibt Client-Rendering im Browser.

---

## 6. Beziehung zu §12 (Stil-Analyse)

Die Animation kann *unterschiedliche Hände* abspielen. Sobald mehrere
Sources mit gefitteten Templates vorliegen (P3–P4 der Roadmap), zeigt die
gleiche Glyphe in jeder Hand ihre eigene Animation:

- Gleiche Centerline-Topologie (norm-gleicher Duktus).
- Unterschiedliche `anchors`/`half_widths` (Hand-spezifisch).
- Unterschiedlicher Width-Profile-Resolver (falls verschiedene Schriftfamilien).

→ Side-by-Side-Animation-Vergleich als Hand-Vergleichs-Feature (Vision §6,
Hände-vergleichen-Pfad).

---

## 7. Quellen

- [Animate Calligraphy with SVG](https://css-tricks.com/animate-calligraphy-with-svg/)
- [How to Get Handwriting Animation With Irregular SVG Strokes](https://css-tricks.com/how-to-get-handwriting-animation-with-irregular-svg-strokes/)
- [How to Animate SVG: CSS, SMIL, WAAPI, and GSAP Compared](https://svg.dog/learn/how-to-animate-svg/)
- [Intent to deprecate: SMIL (Chromium)](https://groups.google.com/a/chromium.org/g/blink-dev/c/5o0yiO440LM/m/YGEJBsjUAwAJ)
- [MDN Web Animations API Concepts](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Web_Animations_API_Concepts)
- [animCJK GitHub](https://github.com/parsimonhi/animCJK)
- [Make Me a Hanzi](https://www.skishore.me/makemeahanzi/)
- [Hanzi Writer](https://hanziwriter.org/) /
  [GitHub](https://github.com/chanind/hanzi-writer)
- [GSAP DrawSVGPlugin](https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/) (für
  Vergleich, nicht verwendet)
- [SVG Line Drawing Animation Solutions 2025 — portalzine.de](https://portalzine.de/svg-line-drawing-animation-solutions-vivus-js-alternatives-modern-approaches/)
- [CanvasKit — Skia + WebAssembly](https://skia.org/docs/user/modules/canvaskit/)
- [Variable Fonts (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_fonts/Variable_fonts_guide)
- [Sütterlin (Wikipedia)](https://en.wikipedia.org/wiki/S%C3%BCtterlin)
- [Kurrent (Wikipedia)](https://en.wikipedia.org/wiki/Kurrent)
