### Added

- **Der Streifen-Editor — the surface the author draws a Bahn on, over his own
  writing.** Opened from a Nachfahr-Zeile, fullscreen with every control above
  the drawing area, and a SECOND, slim editor beside the plate one (author
  decision G) rather than a props seam through it: the tested plate write flow
  is not touched, and what the two genuinely share they now share for real —
  the drawing surface is one component (`shell/TraceCanvas`), the registration
  maths stay the one module both import. Copying the geometry would have let
  the two editors disagree about where a stroke lies, which is the defect that
  looks like nothing on screen. Three things differ from the plate and are the
  reason it is its own surface: the underlay is a BLOB, because the strip crop
  route is admin-gated and `private, no-store` and a bare `<image href>` cannot
  send the admin header (the strip tiles' own loader is reused); the frame is
  the stored Bahn's registration minus the box rectangle, so a Bahn drawn,
  saved, read back and re-seeded lands on the same pixels; and „Speichern &
  weiter" walks to the next box of the list's current order without leaving the
  surface, on the `ETag` the save itself handed back — two boxes of one Fassung
  cost one read.
- **Das Absetzer-Soll beside the Bahn, with a warning when they disagree.**
  The editor shows how many joined runs the script writes this word in and says
  plainly that the target counts BODY runs only — i-Punkt and Umlaut are not in
  it, so one run more can be right and two are a different stroke order.
  Without that number, tracing quietly delivers a new Strichreihenfolge by
  picture, which is the one thing the Duktus-Prior exists to prevent.
- **Die Buchstabengrenzen are shown on the Bahn and can be corrected by hand.**
  The seam between two letters is dragged with the pen and saved as an
  `authored` span through the per-box write; the interface says why it asks —
  a corrected boundary is training material for the Span-Zuordner and survives
  every later re-follow. A boundary nobody touched keeps the follower's own
  provenance, deliberately: stamping it as the author's would freeze a guess as
  ground truth. Boundaries belong to the RUN they sit on: redrawing that run
  gives them up and says so, while Anpassen (which moves points and never their
  count) and a run drawn beside them — what the Absetzer-Soll asks for when a
  mark stroke is missing — leave them standing. The narrow rule is the point:
  the per-box write replaces the entry whole, so a boundary dropped in passing
  is a corrected one deleted for good.
- **The first component test for a re-tracing surface.** No `*.test.tsx`
  referenced the plate editor either, so the suite Q6 (b) promises had to be
  written rather than moved: the seeded Bahn's round trip through the strip
  frame, a saved box advancing on the token the save returned, a dragged
  boundary going out as the author's while an untouched one does not, the
  Absetzer warning firing on a mismatch, and a 412 reaching the author as
  something to act on with his drawing still standing.
- **An unsaved drawing is not thrown away without being asked.** „Schließen"
  and the Escape key both stop at a short confirmation while something is
  drawn. A hand-drawn Bahn exists nowhere else until it is stored — no follower
  run recreates it — which is the whole reason this surface exists.

### Changed

- **A word box states its printed ruling.** `GET` of a strip listing and of a
  Fassung's Bahnen carry `nominal_baseline_row` and `nominal_xh_px` beside
  `rect_px`, from the same `frame_for_box` call. A box whose follower gave up
  carries neither frame nor scale — its Skip-Eintrag has none by construction —
  and that is exactly the box the author draws by hand, so the editor needs a
  frame for it. It is NOMINAL and labelled „Saat" wherever it is used: where
  the writer was asked to write, never where the hand wrote.
- **A gallery tile carries its box's Ampel again.** The tiles lost the „Maske
  geändert" warning when the free-standing chip gave way to the Tintentreue in
  the list; the hand-wide read now reaches the crop tiles too, so a picture
  says what the list says about the same box — one reader for both surfaces
  rather than a second fetch with its own rules.
