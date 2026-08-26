# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Every PR adds its entries under `[Unreleased]`; a release moves that section under a new
version heading AND bumps `CITATION.cff` (`version` + `date-released`) and
`pyproject.toml` (`project.version` — `/docs` reads it at runtime) in the same commit.
Code changes are covered here — data-only commits (chart sources,
authored templates) are covered by their `SOURCE.md` provenance records instead.

## [Unreleased]

### Changed

- **Bogen printing: a job always starts at the front of the plan, and a stack
  is ONE PDF.** Author's decision 2026-08-26: the queue is the plan order
  minus the strips that are already belegt — a Bogen that was printed but
  never written holds nothing back (a new print is asked for because the old
  sheet is gone), so `unterwegs` becomes a display state and stops being a
  queue criterion. A stack of N Bögen is one selection for the whole job
  (`core/eigenhand/bogen.py::compose_stack`: the pages continue the queue, no
  strip on two sheets, attempt groups stay on one page, ids minted
  consecutively against a working copy of the Kartei) and comes out as one
  multi-page document (`pdfgen.build_pdf_pages`; the single-page file stays
  byte-identical). `POST /eigenhand/sheets` composes the stack in one go and
  still records every Bogen as its own row; new `GET
  /eigenhand/stacks/{hand}/pdf?sheets=B0007,B0008` re-renders several recorded
  Bögen into one PDF; the Werkbank opens the job as one document (per-Bogen
  buttons stay for reprinting a page); `tools.eigenhand.sheet --sheets N`
  writes `stapel-<first>-<last>.pdf` beside the per-Bogen folders. Doctrine:
  `eigenhand-erfassung.md` §7.

- **Laufform LF3b-W: the write map re-derived and measured as it would be
  written — the 14-row map fails one gate by one crossing, the 13-row map
  without p passes every gate and now waits for the author's go.** The
  aug19 candidate map was gone from disk and its build script never
  committed; the recipe was reconstructed from the session log and rerun
  under the current harvest (ink-evidence mask) and ruler (cap 1.5). All
  seven repair parameters reproduce aug19 to three decimals (p t=0.578).
  Gates re-anchored to fresh bases in one pinned environment: wordbench
  0.108091 → 0.105607 (pair byte-identical, 16 words better / 5 worse, only
  write-glyph words move), Galoppieren's composition soll 6 → 8 = hand,
  Lotse aiou 0.7398 → 0.7484 with spurious 5 → 4 and no losing word — but
  the Kette v5 route loses ONE hand crossing in Galoppieren (missing 13 →
  14) while gaining aiou +0.071 there. The autopsy (with a second opinion)
  puts it in the fit/init layer and the counter's ring rule, not in the
  map: the composition prescribes the lost crossing identically on both
  roots, the chain init draws it at the same place, and the v2.1 ring rule
  drops it on the write root by partner hits (2/11 vs the base's 2/1) —
  and the base for that word is the guard's reverted init. The gate stands
  as pre-registered: no write of the 14-row map. The pre-registered
  rescue — the author's glyph selection — was measured in the same round:
  the 13-row map (E F K P S Z ae b f k s ue v) passes (a)–(d) with the
  Kette stroke-identical to its base; p goes to its own arm with three
  named rescue paths (init guard against the composition soll, stem
  release at the bowl return, ring-rule sensor). `k0eval` gains
  `--fixtures` so a candidate solved on a patched root is scored against
  that root's own soll. **Written on the author's go of 2026-08-26:** archive
  snapshot `2026-08-26T11-13-38Z` first, DB base checked anchor-equal to
  the frozen root, then the 13 rows via `PUT …/templates/{key}/laufform`
  and verified by GET — the Sütterlin-1922 Laufform gap shrinks from 15 to
  2 glyphs (G unrepairable, W excluded); the frozen fixture root stays
  frozen. Details: `qualitaetsmetrik.md` §14 „Laufform LF3b-W",
  `tintenfolger.md` §7.9, glossary „Schreib-Karte".

- **Kette v5: the K0-S stack — composition soll, ratchet, zone 0.55 — is the
  follower's default.** Author's go of 2026-08-25, measured against the
  pre-registered Soll-Stack base in one pinned environment: 63-word soll
  distance 86 → 79 (7 better, 0 worse), aiou over the 31 moved words min
  −0.0004 / median +0.073, zero losers; on the dev-19 ruler dtw median 0.0453
  → 0.0446, p90 0.0896 → 0.0861, aiou 0.7468 → 0.7608, worst per-word dtw
  delta +0.0016. Every K0-S gate holds. The mechanism is visible per word for
  the first time: the round-atomic soll guard reverts 26 of the 31 moved words
  to the chain init in round 1 — they were never followed — and the zonal
  re-solve rescues exactly those. A run with no flags is now the Kette;
  `--no-structure-guard-ratchet --structure-guard-zone 0 --soll-source init`
  reproduces the old Soll-Stack base stroke-identically and
  `--no-structure-guard` the unguarded follower, which is a diagnostic arm and
  never the duel candidate. Thirteen words v5 still reverts to the init are
  named with their rescue paths — preventive terms in the descent, never
  acceptance rules; "fall back to the unguarded result" was examined and
  rejected as the abolition of the guard. Details: `qualitaetsmetrik.md` §14
  „Kette v5".

- **`k0eval` refuses to let a base and an arm from different stacks pass as a
  pair unnoticed.** The first v5 measurement paired the arm against the
  follower WITHOUT the structure guard and read three gates as violated — 36
  aiou losers that were the base's own structure destruction (init 86 → free
  125 soll points), not the arm's cost; the L-U "Kette" row of the day before
  carried the same base. `k0eval` now reads the follower flags off both files,
  prints both stacks before the first number, warns loudly with the differing
  flags, and names each word's guard outcome (`clean / halved / zonal /
  revert-r1 / revert-init`) so the tier autopsy that took an hour by hand is
  one column. The L-U row is corrected in place; its finding is unchanged.

- **The frozen ruler's arc cap moves 0.8 → 1.5 xh: the u-Bogen is a mark
  (L-U, measured, adopted).** All six pre-registered gates hold. Identity: the
  pre-change code and the new one at the default produce all 19 dev rows
  byte-identical. Class: exactly the enumerated strokes change — 9 on the
  reference, 5 on the candidate side, every one a u-Bogen. Defect: the
  defective `Zaum` arc (1.966 xh) stays in the body and is still paid for.
  `marks_uncertain` falls 8 → 0 on every route, `marks_ambiguous` and
  `marks_missing` stay 0, and 16 columns that read the full stroke list are
  byte-identical between the two caps — so `aiou`, both chamfer halves,
  crossings, retraces, touch/overlap and the soll columns keep their standing
  numbers comparable.

  The win lands on exactly one route, and the entry says so: **Kette** (the
  duel stack, `--structure-guard-soll`) drops its p90 from 0.2355 to 0.0896
  and its worst word from `unter` 0.4503 to `muß` 0.1108 — `unter` alone goes
  0.4503 → 0.0877, confirming the hand-computed 0.084 of the `aug20` autopsy.
  (The entry's first version measured this row on the follower WITHOUT the
  structure guard; corrected on `aug26`, the finding is unchanged, and the
  unguarded follower stays in the table as a diagnostic arm.) On Lotse, the
  raw chain fit and the Nullprobe
  the change costs a little instead, because only the Kette ever had the
  ordering fault: the others emit diacritics last, drive the skeleton directly,
  or have no stroke order at all, so pulling the u-Bogen out only removes a
  stroke that was aligning fine. What those routes gain is not a better number
  but an honest one — `mark_pos_err_xh` now reports 0.015–0.134 xh that stood
  in no column before. `--mark-arc-cap` reproduces any earlier value, and the
  cap was raised rather than dropped precisely so a defective arc cannot escape
  the primary measure into the mark column. **InkSight is not re-measured** —
  its inference needs an isolated Python-3.11 TF venv — so its numbers stay
  valid, archived and not comparable until that run is caught up.

### Added

- **A cut strip says which hand, which sheet and which day it is from.**
  `S0001` alone did not identify one: a single plan serves all three scripts,
  so that id exists for every hand, and a redo prints it again on a later
  sheet — the attempt suffix only counts within one sheet. A drawer of cut
  slips was therefore resolvable only through the Kartei and the DB, which is
  exactly what the drawer case has lost. The same line now carries hand, sheet
  and print date right-aligned at the other end of the Schnittband. Two short
  runs at opposite ends rather than one long one, so the middle of the top pad
  stays clear of an overshooting ascender; and it costs the import nothing,
  because `_printed_mask` already blanks everything above the ascender line,
  which is where the line sits. Tests pin that both ends stay inside the cut
  band, never overlap even for a long hand id, and stay in the masked zone.

### Changed

- **Pre-registered: the u-Bogen becomes a mark in the frozen ruler (L-U).**
  The `aug20` chain autopsy found that 81 % of the `unter` distance is pure
  stroke ORDER — the hand writes the u-Bogen last, the chain in the middle —
  and that the ruler forces it into the body DTW because its arc (1.10 xh)
  exceeds `MARK_MAX_ARC_UNITS` = 0.8. It left the consequence to the author,
  who decided on 2026-08-25 to change the ruler, and after the class census
  refined that to raising the cap rather than dropping it. A descriptive census
  over the frozen root, taken before any route number: exactly nine reference
  strokes change class, all of them u-Bögen, one per word — no capital
  ornament, no ascender loop, no umlaut. The current cap sits INSIDE the mark
  population rather than between mark and body, and on the candidate side it
  misses misclassifying a real umlaut by eleven thousandths (`Sprünge`,
  0.789 xh). The measure raises it to 1.5 xh, derived from the width model — a
  standard lowercase is one x-height wide, so a floating stroke longer than one
  and a half letter widths is no accent — rather than from the observed
  distribution, which keeps a defective candidate arc (`Zaum`, 1.966 xh) in the
  body where it is paid for instead of letting it escape into the mark column.
  Written and committed BEFORE the first number, with six gates, the kill
  criteria, the expected pen-lift side effect and the circularity antidote (the
  ruler's own expectation table has said `"u": 1` all along). Details:
  `docs/reference/qualitaetsmetrik.md` §14 „Lineal L-U".

### Fixed

- **The sheet's legend printed a "?" where the long s belonged.** It read
  "rundes s statt langem ſ" and came off the printer as "statt langem ?":
  WinAnsi has no ſ, and the note saying exactly that sat four lines above the
  legend in the same file, written about the word labels and never applied to
  the legend added later. The one character the sentence exists to explain was
  the one the font cannot draw. Reworded so it needs no special glyph, and the
  substitution can no longer reach paper: the writer still maps an
  unencodable character to "?" — right for a general PDF writer — but
  `render_pdf` now refuses the page instead, checked over the composed sheet so
  it covers the strip ids and word labels from the plan as well as the
  constants. Both halves of the legend are imperative now; the "|" half was a
  gloss that never said the mark is not to be written.

- **The `cfg` stamp is a geometry fingerprint again, not a promise.** It hashed
  a hand-kept list of constants under a comment claiming it covered "EVERY
  constant that moves a printed box" — and it failed the way such lists always
  do: the printable-area pass moved all four Passmarken by 3 mm, pushed every
  row down and shifted the verdict column, and the printed stamp stayed
  `aa9f6a5566` throughout. Two sheets whose registration frame differs by 3 mm
  were indistinguishable by the mark that exists to distinguish them. It now
  hashes the layout minus its provenance block: the layout already carries the
  fiducial centres, every `cut_mm`, `band_mm` and `mark_mm` and every box edge,
  so it can forget nothing — and it no longer reacts to things the sheet does
  not print, such as an advance for a glyph that is not on it.

- **The Bogen prints the rules that cannot be undone, and its own ruler
  check.** Ink colour, colour scan, scan-before-cut and the verdict-box rule
  lived only in `data/samples/own-hand/README.md` — a file nobody has open when
  the pen goes into the ink, and each of them costs a sheet that cannot be
  reprinted. They are two lines above the legend now. The ruler check
  ("Markenmitten 190,0 × 277,0 mm — ohne Skalierung drucken", derived from
  `FIDUCIAL_CENTERS` rather than spelled out) took the place of the machine id,
  which stood in the footer as a second verbatim copy of the header and was
  read by nobody: `ingest` crops the top 14 mm for the misfiling guard, never
  the foot. The footer also stops printing "no-commit" — every sheet printed
  through the deployed API said that, since `.git` is in `.dockerignore` and
  the image has no `git`.

- **The Bogen now fits the printer it is printed on.** Its Passmarken sat
  3 mm from the page edge — closer than any office laser can print: HP
  LaserJets refuse the outer 4.23 mm, consumer devices run 3.4 to 5. The
  cost would not have been an error but a silent skew, because a clipped
  mark is still square and still solid and passes every shape test the
  detector has; only its centroid moves inward. On an HP the four 8 mm
  squares come out at 6.77 mm, each centroid pulled 0.615 mm toward the
  page centre, and the rectification — which maps exactly those centroids
  onto their nominal millimetres — then stretches the sheet by +0.63 % in x
  and +0.44 % in y. Anisotropic, systematic and campaign-wide. The sheet now
  declares the printable area it needs (`PRINT_SAFE_MM` = 6.0) and nothing
  is drawn closer, checked on the composed sheet for all three scripts
  rather than on the constants. The marks go as far out as that allows
  (centres at 10 mm, spans 190 × 277 instead of 196 × 283) because a larger
  registered quad means less angular error per pixel of centroid noise; the
  header, footer and legend move to their own `META_MARGIN_MM` so they keep
  the 4 mm they had off the marks; `TOP_MARGIN_MM` follows the marks down by
  the same 3 mm so the top cut ticks keep their 6.4 mm; and the verdict box
  moves into the right cut-tick lane, which it never meets because the ticks
  mark the Schnittband's corners and it sits in the middle of the row. Seven
  rows still fit, the writing width is still 180 mm, and the golden PDF is
  re-baselined. No sheet had been printed yet, so nothing splits into
  cohorts — and a per-sheet layout means an already-printed one would keep
  its own geometry anyway, which is now pinned by a test.

- **A clipped print is reported instead of quietly absorbed.** Mark size and
  mark spacing come off the same printer, so their ratio is fixed by the
  layout and survives any uniform scaling: `fiducial.check_mark_size` reads
  the size the measured spacing implies and `ingest` names every mark that
  falls materially short. The other failure — a driver's "fit to printable
  area" — is invisible to any measurement taken from the scan, since marks
  and spacing shrink together; that one is a ruler on the paper, and both
  the proposal and the operating README now say so instead of implying the
  import would catch it.

- **The three blockers between the eigenhand chain and the first real
  Bogen.** All of them were invisible to the synthetic smoke test, because
  that test neither crosses Cloudflare nor runs inside the deploy image.
  (1) `tools/eigenhand/apiclient.py` sent no `User-Agent`, so Cloudflare
  answered urllib's default with a 403 (error 1010) in front of the API
  and `setup`, `sync` and `pull` could not reach production at all —
  measured as 403 against 401 with nothing changed but the header; the
  archive client has carried a name since it was written. (2) Neither
  `tools/eigenhand` nor `tools/dbsnapshot` read `.env`, so the archive
  snapshot refused with "no archive" and every admin call with "no admin
  token" unless the environment had been sourced by hand (author,
  2026-08-25: the tools should take it from `.env`, that is where it is);
  both packages now load it on import, and an already-set variable still
  wins. (3) `core/eigenhand/geometry.py` imported the fugen-form table
  from `tools`, which the API image does not ship — every Bogen printed
  from `/admin/eigenhand` ended in a `ModuleNotFoundError` 500, since
  `_guard` only catches `SystemExit`. The table already lives in the
  committed plan's `forms` block, put there for exactly this reason, so it
  is passed in from the caller now; boxes stay byte-identical across all
  120 strips, 13 of which carry a fugen word. `tests/test_imports.py`
  keeps `core/`, `api/` and `alembic/` free of `tools` imports from here
  on, deferred ones included.

- **`redo --retire` no longer bricks a hand's `sync`.** It wrote the
  status as `zurückgezogen` while `core/eigenhand/ids.py`, the Bestand
  count and the API's `Literal` all use ASCII `zurueckgezogen`. Since
  `sync` posts every Fassung of a hand in one request, a single retired
  Fassung turned each later run into a 422 abort — and the Kartei is not
  meant to be edited by hand. The three status values are named constants
  now, the test that pinned the German spelling pins the ASCII one, and
  the glossary and the proposal agree with the code. Also documented, in
  both places a reader looks: `--retire` only touches ACCEPTED Fassungen,
  so a row rejected by mistake cannot be accepted later — that strip has
  to be printed and written again.

### Added

- **The written strips themselves, in the DB and in the workbench.** The
  bookkeeping made the admin view possible; this makes it show the actual
  writing (owner, 2026-08-24: the strips should be visible in the admin
  area like a chart crop, without landing in the repository). Migration
  `0025` adds `eigenhand_strips` — its own table, PNG column deferred
  everywhere, so a Bestand query never drags ~350 KB per Fassung along —
  plus `eigenhand_hands` for a hand's STANDING setup (nib, ink, paper,
  device) and the effective per-row copy of it on `eigenhand_fassungen`.
  The chart's model could not be followed: `sources.chart_path` points at
  committed bytes on disk, which the reserved own-hand dataset can never
  be, so the bytes travel the other way — admin-gated, `private,
  no-store`, never public, never in the repo. Word crops need no storage
  of their own: the strip remembers where its crop started in millimetres,
  the sheet's layout says where each word box sits, and `core/eigenhand/
  crop.py` cuts it out on demand (full strip height, on purpose — the
  ascenders and descenders are the point). `/admin/eigenhand` gained the
  standing setup and a Streifen panel that loads a Fassung on click and
  any word of it with one more.

- **Repo plus archive restore the own-hand tables — as a check, not a
  hope.** The owner's requirement (2026-08-24) after the strips moved into
  the DB: a lost database must be recoverable from the public repo and the
  private archive alone, table contents and strip images. The archive
  stays the master, and `sync --from <archive snapshot>` replays it —
  the SAME push code as the everyday sync, so the restore path cannot rot
  unnoticed. `sync --mit-streifen` (opt-in) carries the images, skipping
  by sha256 what the server already holds, refusing a filed strip whose
  bytes no longer match its Kartei record, and — after pushing everything
  that is there — failing loudly when an accepted Fassung has no filed
  strip at all: on the restore path a silent skip would report success
  while leaving strips out of the DB (Copilot review). `--from` reads the
  archive as one LAYERED tree — the named snapshot plus its siblings,
  newest first — because `snapshot.py` files incrementally and only the
  first snapshot is ever self-contained; reading one directory restored
  one increment and called it done. The standing setup rides along in
  every snapshot now and is pushed when the server has none, so all four
  `eigenhand_*` tables really do come back. `tools/dbsnapshot` takes the
  `eigenhand_*` tables along WITHOUT the blobs plus a `strip_hashes`
  manifest — the mechanical check that DB and archive have not drifted
  apart. Drilled 2026-08-25 against a throwaway PostgreSQL with the
  working copy deleted in between (1 Bogen, 3 Fassungen, 3 strips back;
  hashes identical; a word crop cut from a restored strip; the second run
  wrote nothing), and pinned as a test that runs the whole chain against
  the real API.

- **`tools.eigenhand.setup` — the standing nib/ink/paper, typed once.**
  Ink, paper and nib are photometric parameters of a whole campaign, not
  details of one import: change them mid-campaign and the corpus splits
  into cohorts that cannot be compared on stroke width or darkness. The
  tool writes the server record and caches it next to the local data root,
  so `ingest` defaults to it at a desk with a scanner and no reason to be
  online, and only a deviation has to be typed. Every Fassung still
  records the effective values it was written with — a real change should
  be a visible break in the data, not something to reconstruct.

- **The own-hand Bestand in the workbench, and the Bogen printer with
  it.** The capture chain's bookkeeping moves into the shared DB (owner,
  2026-08-23: the DB may hold which Streifen exist how often — the crop
  is not needed for that), which is what makes an admin view possible at
  all: the counts need no pixels at all, because a strip id plus the
  committed plan already names the words. (The strips themselves followed
  a day later, admin-gated — see the strip entry above; when this landed
  they were still local-only.) Two tables (`eigenhand_sheets`, `eigenhand_fassungen`,
  migration `0024`) hold printed Bögen with their layout and one verdict
  per printed row — no pixels, `png_sha256` names a local file without
  containing it. `/admin/eigenhand` shows what a hand holds: strips
  belegt/unterwegs/geplant, Fassungen, Bögen, and which glyphs and joins
  are written out of how many the plan can produce — capitals, digits and
  signs each in their own class — plus a printer that composes the next
  Bögen and hands back their PDFs. Six admin-gated endpoints under
  `/eigenhand/*`; uploading a scan deliberately stays a local step. What
  the API is handed, it re-checks: an uploaded layout must name the Bogen
  its route names (the PDF is re-rendered from it and a scan registered
  against it — the same check `apply.py` makes locally), its hash is
  derived rather than believed, and every verdict must name a row that was
  actually printed. A Fassung is a Beleg: without that last check a
  verdict for a Bogen nobody printed would have inflated the counts
  (Copilot review).

- **One compute layer for the capture chain, two persistences.** The pure
  half moved from `tools/eigenhand` to `core/eigenhand` — the frozen strip
  plan, the page geometry, the PDF writer, the coverage bookkeeping, the
  Bestand and the Bogen composition — because the API serves it now. The
  seam between server and terminal is the KARTEI SHAPE: `tools/eigenhand`
  reads it as `kartei.json`, `EigenhandRepository.kartei` builds the same
  dict from the two tables, and everything behind it cannot tell them
  apart. So `python -m tools.eigenhand.report` and the admin view cannot
  disagree about one hand, and both print Bögen through the same
  `compose_sheet`. `streifen.json` gained format 2: it now carries the
  shaping form of every planned word whose spelling differs
  (`Amtszeit` → `Amts|zeit`), append-never like the strips, so the plan is
  readable without the curation source. Two new local tools close the
  loop: `sync` pushes the counts up over the admin API (never a DB
  connection, never an image), `pull` fetches a Bogen printed in the
  workbench down to disk so `ingest` can register a scan against it.

- **One guarded helper for every Bogen path, and guards that mean what
  they say.** `--sheet` reaches four Eigenhand CLIs and is interpolated
  into a path in each of them, so it now passes `store.check_sheet_id`
  (plain `B<nnnn>`) and every `<hand>/blaetter/<sheet>/` is built by
  `store.sheet_dir` — the hand id and the sheet id are checked in one
  place instead of four. All three guards in the module match with
  `fullmatch` rather than `match`, because `$` also matches BEFORE a
  trailing newline: `mn-suetterlin\n` passed the hand-id guard until now.
  The sheet id spells its digits `[0-9]` instead of `\d`, which takes
  non-ASCII digits (Copilot review, PR #407).

- **Cyan rulings that a colour scan can drop, and more air for the flat
  scripts.** The guide lines print in pale cyan instead of grey: cyan's
  blue component sits at paper level, so `ingest --channel auto` reads a
  colour capture through its blue channel and the lines are gone rather
  than merely faint (baseline 0.91 in the blue channel, 0.75 as greyscale
  — better than the grey in both capture modes). Black and iron-gall ink
  come through at 0.10/0.14; blue ink lands on the 0.55 threshold, so the
  operator README asks for black or brown. Strips are never shorter than
  28 mm, the surplus split above and below the row block, which gives
  Kurrent 6.2/5.2 mm of padding instead of 4/3 — and the row pitch now
  derives from the strip height plus a fixed 5 mm gap, so the paper
  between two strips is the same for every script. The printed strip id
  and word label moved further from the writing band without the strip
  growing: the three vertical zones were shifted against each other, their
  sum unchanged.

- **Buffer in every box, faint rulings, a printed legend, and stacks of
  sheets.** Five corrections from writing practice (owner, 2026-08-23):
  the packing filled rows to 180.0 of 180 mm, so a word could run out of
  room mid-stroke — it now keeps 15 mm in reserve and `boxes_for_row`
  hands that reserve back to the boxes in proportion to word length, so
  every word gets 10–44 % over its estimate rather than only the last one
  on the line. The advance model was raised with it (a Sütterlin lowercase
  is a full x-height, not 0.85), which re-baked the strip plan — nothing
  had been written yet, so this was the last moment for it. The sheet now
  prints its own faint `CAPTURE_STYLES` ruling theme instead of the app's
  reading theme, every value well above the importer's ink threshold, so a
  printed line can never count as ink; the page is marked identically at
  both ends (a vertical tick above the first strip, mirroring the one
  below the last); the verdict caption moved above the first cut line
  instead of sitting level with the first strip; the label hints `|` and
  `*` are spelled out in a footer legend; and `sheet.py --sheets N` prints
  a whole session's stack in one call, with no strip on two sheets.

- **A cut format for the strips: wider row gaps plus cut marks in the
  margins ("Schnittband" · "Schnittmarken").** Every row now carries a cut
  rectangle of fixed columns and fixed paddings, so the strips of a style
  all come out at one height and one width (Sütterlin 185 × 29 mm) no
  matter how many words a row holds. The row gap grows from 5 mm to 12 mm
  — it has to carry two cut lines now — which puts 5 mm of free paper
  between neighbouring strips and 7 rows on a Sütterlin sheet instead of 9.
  Marks are printed in the page margins only: ink inside the cut rectangle
  would end up in the training data. The vertical cuts are marked in the
  gaps between strips rather than at the page head, where a hairline
  blurring into a Passmarke on a scan would drag its centroid and with it
  every millimetre the importer computes; for the same reason the first row
  starts at y = 22 mm. The strip id moved into the cut rectangle's top pad
  so a cut strip stays attributable on its own, while the verdict box stays
  outside it. `ingest` crops exactly at the cut rectangle, so the paper
  strip and the filed `streifen.png` are the same object.

- **A per-row verdict box on the sheet ("Stiftmarke"), read back at
  import.** Every printed row now carries one 5 mm box in the right
  margin, captioned "ok" once above the first row, so a row can be judged
  with the pen the moment it is written instead of from memory at the
  screen: a cross or check means accepted, an empty box means rejected.
  The column sits at x = 199 mm, clear of the writing area (the frozen
  strips fill its full 180 mm) and clear of the corner fiducials, which
  only occupy the page corners. `ingest` reads the box off the rectified
  page (ink fraction of the inner area, printed outline excluded, a stray
  speck stays below the threshold) and the Siebung page pre-selects the
  verdict, marked with a "Stift auf dem Blatt" chip and overridable at any
  time; a stored click always wins over the seed. One box rather than two
  keeps the sheet to a single pen movement, and a forgotten tick fails
  towards re-writing the strip rather than filing an unreviewed row. This
  is the only input allowed to pre-fill a verdict — it is a human
  judgement, unlike the QC flags, which stay warnings. The mark rides
  along in each Fassung's `meta.json` for the audit trail.

- **Eigenhand coverage progression, a digits-and-punctuation pool layer,
  and strip-plan wave 1.** `tools/eigenhand/progression.py` answers "after
  10, 20, … strips, how often has every glyph and join been planned?" with
  cumulative per-checkpoint counts (bucketed klein · gross · ligatur ·
  ziffer · zeichen), quotas against the shared Soll model and a `--json`
  export for repeatable optimisation loops. Coverage now counts detached
  glyphs (digits, punctuation) as glyph-position items, and the pool gains
  a `zeichen` layer of real-text carriers (years, a date, a price, signs
  at words) plus capital-C and bare-q carriers the progression run
  surfaced as gaps. A hard per-glyph floor (`pool.GLYPH_MIN_PLANNED = 3`,
  phase A2) now guarantees that EVERY glyph — letter, ligature, digit,
  sign — is planned at least three times regardless of its text frequency,
  before the frequency-driven build-out starts; a wave too small to satisfy
  it names the leftovers instead of failing silently, and every
  `progression` run closes with the check line. Wave 1 of the strip plan
  (strips 61–120) ships committed: after 120 planned strips every registry
  glyph — all capitals, all ten digits, all thirteen signs — carries at
  least three planned recordings (666 distinct joins, 99.5 % weighted
  Erstbeleg quota). The PDF writer's
  literal-string escape is now WinAnsi-aware so German quotes, dashes and
  the typographic apostrophe survive onto printed labels.

- **Eigenhand-Erfassung: the complete tool chain for collecting the
  author's own hand as training data** (`tools/eigenhand/`, proposal
  `docs/proposals/eigenhand-erfassung.md`, glossary section
  „Eigenhand-Erfassung"). A curated, wave-growing word pool of real
  words (`corpus.py`, seeded from the §9 MVP words, the 63 Abb.-19
  bench words, the full quiz bank plus hunted rare-join, high-frequency
  German and tagged English layers) is partitioned deterministically
  and append-never into row-sized strips (`pool.py`: weighted set-cover
  start coverage, deficit-driven even build-out, repetition damping —
  breadth before repetition), weighted against the local Übergangsraum
  built from consult-only frequency corpora
  (`data/corpora/frequencywords-2018/`, bytes gitignored, SHA256-pinned
  fetch script; `universe.py`, `gaps.py` for curation candidates).
  `sheet.py` prints A4 Bogen PDFs (dependency-free PDF writer twin of
  `app/src/lib/pdf.ts`; lineature presets pinned against
  `app/src/lib/lineatur.ts`; corner fiducials with an orientation
  donut; per-row strip ids; multi-attempt rows via `--repeat`) plus a
  `layout.json` sidecar as the importer's sole geometry contract.
  `ingest.py` rectifies scanner or phone captures (scikit-image-only
  fiducial detection and homography, 300 DPI working space, QC flags as
  warnings only), `page.py` renders the offline Siebung review page
  (humanbench pattern: data URIs, resume state, uid-keyed result), and
  `apply.py` files ONLY accepted rows as self-attributing strip
  recordings (printed strip id and word labels inside the crop,
  `meta.json` with words, geometry, session and checksums; rejections
  are recorded pixel-free in the Kartei). `kartei.py` keeps the local
  manifest with derived strip states, `report.py` reports Soll/Ist
  (weighted Erstbeleg/Ausbau quotas, print queue by weighted repetition
  gain), `redo.py` queues re-recordings (`--retire` withdraws), and
  `snapshot.py` backs everything up incrementally and create-only into
  the private archive clone (dbsnapshot discipline, shrink refusal).
  Wave 0 of the strip plan (60 strips, 253 distinct words) ships
  committed; five new test files pin the preset port, the PDF bytes,
  the shaped-coverage facts, a synthetic render→distort→rectify round
  trip (±0.5 mm) and the Kartei state machine. Own-hand bytes stay out
  of git by owner decision (open-core reservation) — documented in
  `data/samples/own-hand/SOURCE.md` and reconciled across
  `datenablage.md`, `mvp-roadmap.md` (M1/M2 superseded) and
  `handmodell-stufenplan.md` §H5.

### Fixed

- **`k0eval` refuses an empty scoring set instead of quietly reporting
  0 words.** When `ductus_soll` yields no targets (missing wordlab
  deps, broken fixture cases), the run would have continued into a
  meaningless evaluation — the soll distance is the core metric. The
  guard `scoring_ids` now fails fast with a clear error, pinned by a
  unit test.

### Changed

- **Four durable working rules lifted from the 2026-08-21 campaign
  session's friction into the agent instructions and the PR skill**
  (`CLAUDE.md` + the `.github/copilot-instructions.md` mirror where the
  rule is shared, `.claude/skills/open-pr/SKILL.md`): the recipe for
  restarting a mandated branch after its squash-merge when force-push is
  blocked by the cloud classifier (content-neutral merge of the stale
  remote tip, every conflicted file resolved with `--ours`, marker grep
  and an EMPTY diff against the pre-merge head required before the
  commit — `git add -A` during an unresolved merge committed conflict
  markers once); the heredoc ban now names appending with `>>`
  explicitly (a §14 entry slipped in via `cat >>`); the cloud
  fixture-rebuild note gains the `uv sync --all-extras` prerequisite
  (the verify path imports matplotlib from the `viz` extra and fails on
  a fresh cloud venv); and the open-pr skill documents that a cancelled
  Copilot review run may never deliver — one re-request, then green plus
  zero threads counts as review-clean by absence.

### Added

- **The campaign's measurement liturgy becomes documentation and a
  standing tool: werkzeuge.md learns the tracebench/follow loop, and
  the k0-protocol evaluation ships as `tools/tracebench/k0eval.py`**
  (session retro 2026-08-21, points 2+3). `werkzeuge.md`'s bench
  section — which still called `tools/tracebench` "geplant" — gains
  the standing five-step round liturgy the §14 entries have been
  running since `aug19`: extras + bit-exact fixture fetch first, the
  pinned follower run on the soll-stack convention with
  `--candidate-out`, the dev-19 file-provider scoring with
  `--compare`, the reference-free 63-word k0 protocol, and the
  sensors/Augenschein tools. The k0 evaluation itself — per word the
  soll distance against the composition soll through `ductus_soll`
  (the one soll pipeline since K0-S), `aiou` against the frozen mask,
  paired totals, the standing −0.003 aiou-loser gate and the
  stroke-identity classes every identity gate reads — had been
  re-written as a scratchpad script every round and died with each
  container; `k0eval.py` is the durable form, with the paired
  classification factored into a pure `pair_rows` and pinned by unit
  tests over a `tmp_path` fixture tree. Glossary: the `aug20`-coined
  „k0-Protokoll“ finally gets its entry (themed section +
  Schnellindex).

- **Chain K-D, the ink corridor: closed as objectless after v4 by its
  own pre-registered object test — no implementation, a positive
  finding about the route's state** (§14 `aug21` „Kette K-D"; the
  final item of the author's campaign sequence). The corridor idea
  (a keep-out zone around the extended ink the path may not pierce)
  predates the K-C measurement, and rung 0 — an excursion inventory
  over the existing v4-base and v5-contender candidates, no solve —
  shows the target class is gone: not a single word of the 63 reaches
  0.35 xh of paper excursion on either candidate (set maximum: zum at
  0.33 xh), while the autopsied aug20 needle class sat at 0.5–0.83 xh.
  The root treatment (K-C dropping the foreign-ink magnets from the
  evidence) outran the symptom ban. The decision rule was declared
  before the number; the inventory ships as a standing repo sensor
  (`tools/tracebench/excursions.py` — per word, the candidate path
  resampled at the ruler's step against the K-C-cleaned evidence ink;
  no DB, no solve), and the revival trigger (a future inventory or arm
  showing a new paper-needle class → the barrier with a fresh
  pre-registration and the author's named unter lock-in risk) is
  registered in §7.9.

- **Chain K0-S: the soll-source autopsy vindicates the metric, ONE
  soll pipeline is built, and the K0-Z-R resubmission passes every
  gate — with the old zwei trade inverted** (§14 `aug21` „Kette
  K0-S"; the campaign step after K-E). The daß autopsy settles the
  aug20 two-soll-sources find: both pipelines always shared the bench
  counters, and the divergence was input geometry alone — the guard's
  aug19 soll read the chain INIT (chart anchors + generated
  connectors), which squeezes the d-head loop closure into a
  flattened sliver that the 0.15-xh detector correctly counts as
  retrace + touch, while the canonical composition crosses cleanly
  there. The divergence map (ladder rung 0, no solve) shows it was a
  pattern, not an outlier: 40 of 63 runs diverge, and EVERY d word
  (die, das, der×3, laden, daß, die-2, Feinde) carries the daß
  signature. The measure, one knob (`FollowWeights.soll_source`,
  `--soll-source`, default `init` = byte-identical): `composition`
  feeds the structure guard's soll from `composition_strokes` — the
  item→strokes builder factored out of `ductus_soll` (the metric's
  counting is byte-identical through it), run-restricted so a
  deferred mark can never drag a foreign letter's body into the run.
  Budget stays the init count, round counts stay the candidate count,
  the target comes from the canonical source. Measured on the ladder
  (identity spot 4/4 byte-equal incl. daß): the atomic soll guard on
  the new source reaches soll distance 85 → 80 with zero worse words
  and a near-byte-neutral dev-19; **ratchet + zone 0.55 on the new
  source — the K0-Z-R resubmission — reaches 85 → 77 (7 better, 0
  worse), a moved-words aiou median of +0.059, a dev-19 aiou median
  gain of +0.0216 (the campaign's largest), worst per-word dtw loss
  +0.0014, net crossing defects 22 → 19, marks/retrace unchanged —
  and zwei's aug20 trade (+0.0142 dtw for ink) inverts to −0.0100
  dtw WITH ink gains: its magnets were the foreign ink v4 has been
  dropping since.** Both aug20 tears are thereby measured as
  resolved, not waived; adoption of the winning rung as the Kette v5
  stack awaits the author's go (everything stays declared-off until
  then). Ledger row on the Verfahrensseite, §7.9 rows updated.

- **Chain K-E, per-stroke ink assignment stage 1 (the mark-claim
  separation): implemented, pre-registered, and measured to two honest
  negatives that heal the named target and refute the width hypothesis
  by byte identity** (§14 `aug21` „Kette K-E"/„Kette K-E2"; the
  author's follow-up to K-C — after the foreign ink, the remaining
  magnet is the word's OWN dark mark, die-2's i-dot pulling the d-loop
  into the V needle, and the same effect flattened is the suspect
  behind the 7 remaining spurious retrace zones at small loops). The
  mechanism, one intervention point in `fit_word_chain`'s field build:
  a composed mark stroke (the assembler's own diacritic criterion)
  claims its dark non-main component within the ruler's 0.6-xh mark
  radius (`MARK_CLAIM_RADIUS_UNITS`, mirrored and test-pinned), and a
  claim moves the component out of the body's distance field and
  coverage pot while the claiming stroke's samples read exclusively
  their component (`_ChainProblem.field_of_sample`/`mark_fields`,
  carried through every re-linearised round; exact analytic gradient
  pinned by finite differences; claim list in the run meta so a silent
  claim cannot happen). One knob `mark_claim` (`--mark-claim`,
  `FollowWeights` + `HarvestOptions`), declared-off. Measured on the
  63-word soll stack in one pinned environment: identity and the
  construction prediction hold exactly (26 claim-free words
  byte-identical; 37 firing claims — i-dots, u-bows, umlaut pairs);
  **die-2 heals on every axis (soll distance 4 → 1, dtw −0.0281, the
  V needle visibly gone)**, die −0.016, net crossing defects 22 → 18,
  spurious retraces 7 → 6, the dev-19 median exactly held — but the
  aiou gate tears at four diffuse losers (auch, schießen, Einen,
  muß-2; −0.013 to −0.027), whose per-pixel autopsy shows BODY
  coverage lost across the whole word width: a basin redistribution,
  not a mark effect. The one-factor conversion **K-E2** (width fields
  stay unsplit — width is a measurement target, not an attractor)
  refutes the width suspicion cleanly: 55/63 candidates byte-identical
  to K-E1, among them two of the four losers, so the driver is the
  distance-field/coverage redistribution itself — gain and loss of
  this formulation are inseparable, the arm-⑨ pattern one layer down.
  Family closed per its own pre-registration; stage 2 (the loops)
  stays unopened per the author's condition; standing rescue paths in
  `tintenfolger.md` §7.9 (the pre-registered humanbench tie-breaker
  case in pure form · a distance-field-only claim · bow-claim
  sharpening). Glossary: „Tinten-Zuweisung per Strecke",
  „Marken-Claim-Trennung"; ledger rows on the Verfahrensseite.

- **Chain K-C: the ink-evidence mask — pre-registered from the author's
  "Flecken" find and measured to a pass on all six gates** (§14 `aug20`
  evening/night; soll distance 107 → **86** over 63 words with 11 better
  and 0 worse, ZERO aiou losers and gains up to +0.099, dev-19 dtw
  median 0.0494 → **0.0453** and aiou median 0.717 → 0.747, worst
  per-word dtw loss +0.0002, Galoppieren 0.233 → 0.038, zwei 0.073 →
  0.056, spurious retrace zones 13 → 7, the 40 words without foreign
  ink byte-identical as predicted, hand-claim check 0 hits; stays
  declared-off until the author's go). The author read the K0-Z-R
  duel page and asked whether paper specks pull the follower off the
  letters; a four-word autopsy plus a code map confirmed it for three of
  the four complaints with numbers (zwei: both w needles terminate
  inside a faint 27/36-px blob, the ratchet's tip INSIDE it;
  Galoppieren: show-through of the sheet's reverse, three of four
  excursions end on a fragment and one point of the i-dot stroke costs
  75 % of the word's dtw and the mark gate; die-2: the attractor is the
  word's OWN i-dot) and found something else for the fourth (unter: no
  foreign ink — the composed e is twice the hand's width, the seed error
  exceeds the anchor budget, and 81 % of the headline is u-bow stroke
  ORDER bookkeeping). The fit sees every component of the frozen mask
  as attractor and coverage target; over all 63 fixtures AREA does not
  separate real marks from foreign ink, DARKNESS does completely (gap
  0.38–0.74). New `tools/pairlab/ink_evidence.py` drops paper-grey
  non-main components from the case's `skel`/`width_map` at ONE point
  per route (after `derive_word`, before the grid fits), identity when
  off or when nothing is foreign; `FollowWeights.ink_evidence`
  (`--ink-evidence`) and `HarvestOptions.ink_evidence`, both
  declared-off; the bench's own mask stays frozen. Glossary:
  „Fremdtinte", „Tinten-Evidenz-Maske"; plan rows A7/K-C and the
  author's corridor idea A8/K-D in `tintenfolger.md` §7.3. The zwei
  fixture's hand trace was refilled (`--only word-instances`) after the
  author added the forgotten i-dot.
- **Chain K0-Z and K0-Z-R: the zonal rejection and the ratchet budget,
  measured to two honest negatives that carry the route's strongest
  numbers — and a two-soll-sources find** (§14 `aug20` night,
  pre-registered arms). The zonal rejection localises a structure-guard
  violation (one-to-one position diff of the class points through the
  same assembler and counters as the budget), pins the free anchors
  around it to the previous geometry, and re-solves the round once —
  saving a bundled repair instead of rejecting it whole. Zone 0 is
  byte-identical to the aug19 run; zone 1.0 rescues 59 of 79 previously
  discarded rounds with the largest ink gain the chain has seen (aiou
  up to +0.154, soll distance 107 → 102, dev dtw median 0.0494 →
  0.0472, dev-19 fully green). The ratchet (budget snaps to every
  accepted round's counts) plus zone 0.55 reaches soll 107 → **99**
  with ZERO per-word aiou losers — and still fails one gate: daß 2 → 3,
  whose autopsy finds the real root one layer down: the guard's soll
  (`structure_zones` on the composed init: 2 retrace zones) and the
  metric's soll (`ductus_soll`: 1) DIVERGE on the same composition —
  the day's "two rulers" pattern again, now on the chain. Both arms
  stay declared-off (`--structure-guard-zone`,
  `--structure-guard-ratchet`); standing rescue: the soll-source
  autopsy, then re-submission with ONE pipeline for budget, guard soll,
  round counts and metric. The evaluation also re-hit the documented
  aug19 gotcha (follow rows carry registration at top level) — caught
  and corrected before any verdict.

- **The operating-point smoothing candidate falls to the window fine
  ladder — the map/sampling family is exhausted** (§14 `aug20` night,
  second Nachtrag). The fine window ladder {0.02, 0.03, 0.04, 0.06} at
  the adopted 0.12 step shows the sub-0.06 windows kernel-quantized to
  one identical rung (a 3-point box kernel on the 0.02-xh grid), and NO
  window without a loser: the 3-point-kernel rung wins Wer
  and makes unter's t-stem X appear but pays at Galoppieren (+1
  spurious, new retrace defects) and mit; 0.06 wins mit (aiou +0.0967)
  but flips Wer (+0.0309). The effects jump non-linearly between rungs —
  Viterbi decision tipping points, not systematics; per-word optima
  would be fishing. Day verdict closed: the route sits in a sensitive
  optimum at its operating point, and the remaining campaign arms move
  to other layers (chain K0 zonal rejection, InkSight, the zone stage's
  p-osculation mechanics).

- **The smoothing probes close the resolution family: the final coupling
  is the Viterbi's decision granularity** (§14 `aug20` night). The
  announced rescue — an along-path box smoother at counter scale before
  sampling (`smooth_map_strokes`, endpoint-exact, declared off) — was
  built and probed with the full ruler on five words: the fine-step
  drift persists unchanged on the smoothed map (Wer +0.033, window width
  irrelevant), so the coupling is neither economy (v0.19 made it
  invariant) nor emission nor map geometry but the decision granularity
  itself — more samples mean more switching points and different paths.
  The resolution family (v0.18, v0.19, smoothing) is measured out and
  closed: 0.12 stays the operating point, unter's second t-stem crossing
  the standing resolution limit, with no further ladder attempt without
  a fundamentally different solver. Side finding, recorded as its own
  future candidate: smoothing AT the operating point shows mixed, partly
  large effects (mit aiou +0.0967 and dtw −0.0275, muß-2's retrace
  defects heal, unter's t-stem X appears · Wer +0.0309 dtw, Galoppieren
  trades one crossing) — its own pre-registration with a window ladder
  if taken up. §7.9 row updated.

- **Lotse v0.19: the ride economy becomes step-invariant (proven
  byte-neutral), and the resolution ladder's second rejection names the
  final coupling** (§14 `aug20`, pre-registered). The re-denomination —
  per-sample emissions scaled by `step/0.12`, `MAX_RIDE_UNITS` = 0.96
  and `RIDE_DOUBLE_MIN_GAP_UNITS` = 0.48 in xh instead of steps/samples
  — reproduces the v0.17 candidate rows byte-identically on both roots
  (rung 0), so it stays as a neutral foundation that makes future step
  arms measurable at all. The re-submitted ladder rungs {0.06, 0.04}
  fail their geometry gates again with the drift redistributed, not
  removed (Wer +0.031, muß-2 +0.022, new retrace defects): the remaining
  step dependence is the EMISSION fineness itself — finer bridge runs
  emit the map's composition micro-structure along with the wanted
  topology, so structure gain and geometry loss hang on the same
  resolution. 0.12 stays the operating point, unter's second t-stem
  crossing the documented resolution limit. Standing rescue: smooth the
  map at counter scale BEFORE fine sampling (an along-path smoother
  keeps pass offsets like the 0.06-xh t double but eats intra-pass
  wiggle); §7.9 row updated.

- **The t-stem ride autopsy dissolves the completeness gap into a
  RESOLUTION limit, and the v0.18 resolution ladder closes as an honest
  negative with the route's best structure number in hand** (§14 `aug20`,
  pre-registered). The raw composition carries unter's t-stem double
  everywhere — the placement map on the RAW map matches **41 of 41** hand
  crossings (median 0.159 xh), so the composer is innocent: the "gap" is
  `SAMPLE_STEP_UNITS` = 0.12 being coarser than a 0.06-xh crossing pair,
  in the budget's soll and the ride path alike. The pre-registered ladder
  {0.06, 0.04} confirmed the structure thesis exactly (net 5 → **3**,
  unter's last missing heals, a Galoppieren weave falls) but failed its
  geometry gates: the ride economy is sample-denominated
  (`RIDE_DOUBLE_MIN_GAP` counts samples, `BRIDGE_EMIT_FACTOR` prices per
  sample), so halving the step re-prices every bridge and the muß family
  drifts up to +0.035 dtw; 0.04 drifts further — economy, not
  convergence. The fine-emission rescue (decide at 0.12, emit the raw
  map) died in probes: the raw map carries composition micro-structure
  the 0.12 smoothing silently hid (32 spurious on Galoppieren) — the
  smoothing is part of the filter. Standing rescue: step-invariant
  rescaling of the ride economy, then re-submit the ladder; §7.9 rows
  updated, the Karten-Soll-Vollständigkeit glossary entry corrected.

- **The map-soll autopsy dissolves the placement ceiling into a soll
  COMPLETENESS gap, and Lotse v0.17 adopts the reservation veto** (§14
  `aug20`, pre-registered). The placement map over dev-19 matches 40 of
  41 hand crossings against the composed map's ruler soll (median error
  0.150 xh; map-blind only the second X of unter's t-stem double) — the
  evening's "p crosses at v 0.85" turns out to be artifacts of the raw
  double-count enumeration, and the p osculation is a map near-touch,
  not a placement error. The 0.8-window kill at unter dissolves into a commons problem
  of every per-pair COUNT veto (12 events over 1 soll: each single
  removal finds a substitute matcher, the cascade still empties the
  site); the viable semantics is RESERVATION — the ruler soll matched
  one-to-one to the events once per pass, matched events unpairable
  (unit-test pinned). v0.17 measured on both roots: counter-identical
  per word, every gate PASS → adopted per the pre-declared parity rule
  (`UNTWIST_SOLL_MATCHING="reserve"`); the untwist now needs fewer
  mirrors (Galoppieren 15 → 11). Even with reservation the 0.8 window
  stays dead: the second X of unter's t-stem double is a crossing the
  map does not carry (the hand crosses the stem with the descent AND
  the 0.07-xh offset repass — the K1b finding — while the composed bar
  crosses once) — the common denominator of every remaining blocker,
  converted into the named composer arm "Karten-Soll-Vollständigkeit"
  (glossary entry; §7.9 row updated).

- **The G head ride autopsy resolves the v0.14 tear, and Lotse v0.16
  adopts the "bridges" pin stage with the ruler-soll budget** (§14
  `aug20`, pre-registered before the first dev-19 number). The autopsy
  found the tear one layer lower than every prior hypothesis: BEFORE the
  untwist, the "all" stage keeps the Galoppieren G head crossing and
  rides visibly cleanest — the parity-blind pairwise untwist then
  removes the real X together with its weave duplicate (2 → 0 where the
  hand writes 1; "windows" survived only by parity luck, 3 → 1). The
  v0.15 budget failure dissolves the same way: the raw segment
  enumeration lists every map crossing ~twice (will: 10 raw vs 4
  counted), which is exactly will's false veto — with the frozen
  crossing detector itself as the soll source (pierce filter, arc
  floor, merge) the veto arithmetic comes out right at every probed
  site. The pre-registered four-rung ladder then adopted
  `MAP_RUN_PIN_KNOTS="bridges"` + `UNTWIST_SOLL_BUDGET=True`:
  structure counter-identical to the v0.13 base at every site on both
  the LF3b candidate map and the frozen root, no losing word, p90
  0.1129 → 0.1122, chamfer 0.0410 → 0.0404, four words gain
  −0.0035..−0.0059 dtw and up to +0.0117 aiou, mit's retrace zone
  heals. The zones/all rungs fail their net gate by exactly the one
  Galoppieren p osculation (+1 spurious, placement family) while the
  budget keeps the G head X — their re-submission waits behind the
  K1 p placement arm; the 0.8 untwist window stays rejected with
  mechanism (unter loses all three X because the map does not know
  its crossing places — fourth confirmation of the placement
  ceiling). New glossary entry: Lineal-Soll-Budget.

- **The Laufform night: all three owner-flagged map-form sites (G, W, p)
  resolve into ONE layer, and the topology repair becomes the first
  adopted Laufform arm** (pre-registered §14 `aug19` arms LF1/LF2/LF3/
  LF3b, all measured dry — no DB writes). Two code autopsies first
  overturned both late-evening mechanisms: the W→e join does not balloon
  (the composed W simply sits ~0.4 xh left of the hand's apexes — the W
  Laufform gap), and p is no composer class case — the STORED p Laufform
  lost its pierce to the anchor median (the chart form keeps it; the
  v2.1 retrace filter then rightly drops the tangential X). The ruler
  sweep found exactly two stored rows that delete counted chart
  crossings (h: 2→0 in every slot, p: 1→0) and the LF1 run added a
  fresh third instance (the n=3 G draft) — the plain per-anchor median
  systematically flattens loop closures. LF1 (gap-filling drafts for
  the 15 glyphs without a running form, one knob: evidence floor
  min-n {3,1}) and LF2 (guard = compose the chart form instead of a
  topology-losing row) were honestly rejected on their own gates; LF3b
  repairs the topology instead: anchors blend locally back to chart in
  a 0.5-xh window around the lost crossing, with the smallest t (found
  by bisection) that restores the COMPOSITION-level counted crossing.
  LF3b passed every gate: Galoppieren's composition soll reaches 8 =
  hand agreement (p repaired at t=0.578), marks unchanged, Lotse aiou
  0.7398 → 0.7484, dtw median 0.0585 → 0.0573, net defects 5,
  wordbench 0.108091 → 0.107105 with pair_loss byte-identical — the
  candidate map for the standing v0.14 re-submission. Glossary gains
  Laufform-Lücke, Laufform-Topologie-Wächter and Topologie-Reparatur;
  werkzeuge.md documents the wordbench `--laufform`/`--no-laufform`
  overlay flags. Any DB write of the candidate rows stays behind
  dbsnapshot + an explicit owner go.

- **The v0.14 "all" re-submission on the repaired map refutes the
  map-form hypothesis for that rung** (pre-registered §14 `aug19`,
  redeeming the standing §7.9 rescue rows). On the topology-clean
  candidate map the "all" pinning again wins ink (aiou 0.7484 → 0.7521,
  p90 −0.001, five words' dtw −0.004..−0.009, not a single dtw loser)
  and again breaks structure at the SAME Galoppieren site (net 7 > 5) —
  so the G-head break is a property of the ride through the dense
  G junction complex, not of the map form. Named rescue paths: an
  instrumented G-head ride autopsy under "all", then a selective
  pinning rung (bridges and zone rides separated) as its own
  pre-registered mechanism.

- **Lotse v0.10/v0.11: junction-anchored pinning of the map runs —
  v0.11 "windows" adopted, the k curl is finally traced** (pre-registered
  §14 `aug19`, arms L1d/L1e; owner's visual find: the k's lower curl
  untraced, the capital W riding air, angular runs at r/e). The autopsy
  localized the excursions in MERGED crossing windows (up to 4.3 xh in
  one run at linken's k) whose v0.9 end-only pinning passes the raw,
  locally offset map form through their middle, plus the still-raw
  double-zone rides and bridges. v0.10 (anchors as point knots: offset =
  nearest skeleton branch node minus map self-intersection) was
  measured-and-rejected — a point field shears at exactly the crossings
  it anchors (merge/osculation in dense clusters). v0.11 makes each
  anchor a rigid PLATEAU (0.35 xh) with GLOBAL cluster fusion
  (union-find across passes), so dense clusters translate as a whole
  and every X survives. Adopted "windows" on dev-19: net crossing
  defects 7 (= v0.9) with `cross_missing` healed 3 → 1 — Galoppieren's
  two p-loop crossings return although the composition itself lacks
  them —, crossing position error median 0.116 → 0.066 xh (−43 %),
  aiou +0.008, p90 0.118 → 0.113; honest costs: own dtw median
  0.0578 → 0.0596, paired-vs-chain −24 % → −18 %, and the residual
  spurious class is now dominated by double-drawn X duplicates (4 of
  6, named next mechanism). The "all" rung (zone rides + bridges
  pinned too) failed its gate by exactly one duplicate X and stays a
  named rescue path. New glossary terms: Plateau-Anker,
  Doppel-X-Duplikat.

- **Lotse v0.12 "Plateau-Sehne" measured and rejected — the wiggle WAS
  the crossing** (pre-registered §14 `aug19`, arm L1f). Replacing each
  pass's sub-path inside a fused plateau by its chord was meant to make
  the double-X duplicate constructively impossible; instead it killed
  the missing class (1 → 8) and the retrace zones, because at loop
  closures both passes run tangentially and their chords are parallel —
  only the map's wiggle carries the transversality. Both rungs rejected
  by their own kill criterion; rescue paths (untwisting the smaller
  wiggle arc, asymmetric chord) named in the standing §7.9 table.

- **A1 mark refit re-measured on the 19-row dev set: mark position
  error −73 %** (§7.7 recalibration protocol; no new knob, the same
  opt-in `--mark-refit` variant). Median 0.111 → 0.030 xh, all six
  mark-carrying dev words improve, body and structure byte-neutral —
  the wave-1 win (−55 % on 10 words) generalizes to the 9 new
  tracings. Adoption into the stored chain stays gated on the
  confirmation set, now with 6 instead of 4 paired words.

- **Lotse v0.15 (soll-budgeted untwisting): built, measured, honest
  negative — the third independent confirmation of the map-form
  ceiling** (pre-registered §14 "Lotse v0.15 aug19"). The budget
  rule (never untwist a neighbourhood below the map's own
  self-intersection count, fixed 0.55-xh matcher-radius snapshot)
  inherits exactly the map placement errors v0.14 measured: at
  unter's displaced e→r map the real pair dies despite the budget,
  and the radius count lumps will's neighbouring REAL crossing into
  the weave's neighbourhood and falsely vetoes its healed fix. Both
  rungs rejected by their gates; v0.13 (geometry-only, 0.5) stays
  the adopted state, the declared knob and its unit test remain.
  The remaining three duplicates and the "all" rung now explicitly
  wait for the map-form author steps, after which v0.14 and a
  position-matched soll guidance are to be re-measured together.

- **Lotse v0.13 "Entdrillung" adopted; v0.14 (the "all" rung)
  measured with the round's strongest visual proof and rejected by
  its gate** (pre-registered §14 "Lotse v0.13/v0.14 aug19", owner go
  "weiter mit lotse neben ink"). The duplicate autopsy shows every
  duplicate site is a WEAVE (3/5/6 raw intersection events where the
  hand crosses 1/1/0 times), so removal must be pairwise — the
  untwist mirrors the wiggle arc (larger chord deviation; precision
  pinned by a unit test) across the pair's chord, direction
  preserved. Adopted at 0.5: net crossing defects 7 → 6, will's
  duplicate heals; 0.8 killed by its own gate — geometry alone
  cannot tell a weave from a genuinely close REAL pair (mit's t
  double at 0.07 xh), naming the soll-budgeted discriminator as the
  next mechanism. v0.14 (zones and bridges pinned, plus untwist)
  delivers the ink gains (aiou +0.012, 8:1 words better, the
  capital G ridden almost hand-like for the first time — the air
  boxes gone) but flips structure in exactly the two worst map-form
  regions (the G head crossing dies on the form-alien composed G,
  the p invents one): rejected as pre-registered, to be re-measured
  after the map-form author steps, which now pay double. New
  glossary term: Entdrillung.

- **Kette v3: the trace-level spike repair, adopted with a dated
  re-baseline** (pre-registered §14 "Kette K-B aug19"). The §11
  outlier class the owner spotted (the V into the i-dot, the needle
  on the first p — single points jumping 3×+ the stroke's median
  step and back) is repaired on the assembled trace strokes with the
  very detector the statistics layer has used since §11e
  (`tools.pairlab.anchors`; scale-free, runs chorded between
  unflagged neighbours, never snapped to ink, logged) — the A1
  pattern: changes what the trace shows, never what the harvest
  measures. Measured: Galoppieren 0.233 → 0.040 (the spikes carried
  almost its whole residual), the missing i-mark heals (the repaired
  dot falls back under the 0.8-xh mark threshold), retrace-spurious
  13 → 6, touch 25 → 21, no word beyond +0.0016; the one lost
  retrace match is autopsied as a coincidental correspondence inside
  unter's tangle. Chain v3 baseline: dev median 0.0491, p90 0.0894,
  worst muß 0.110, marks 0 — after two pure candidate-layer fixes
  the chain leads the Lotse on median and p90 without a single
  solver parameter moving; the old needle-and-all inspection view
  stays reachable via `trace_repair=False`.

- **Kette v2: the marks-last assembly, adopted with a dated
  re-baseline** (pre-registered §14 "Kette K-A aug19", owner go
  "weiter optimieren"). `HarvestOptions.marks_last` (default True)
  emits a word's diacritic strokes after all body strokes in the
  composed engine order the hand shares; the v1 per-run assembly
  interleaved them between the runs. Measured exactly as
  pre-registered: the four collapse words fall (unter 0.4503 →
  0.0854, muß family −0.12 to −0.14), every other word and every
  geometry column byte-identical — a pure order change. The chain's
  dev p90 drops 0.236 → 0.099 and its worst word is now Galoppieren;
  paired against v2 the Lotse's −18 % advantage disappears entirely
  (Δ-median +0.0007, sign 10:9) — the routes now tie on median, the
  chain leads on p90, the Lotse keeps structure, marks, aiou and
  crossing position. The production re-harvest of the stored traced
  rows stays behind owner go + dbsnapshot. New glossary term:
  Marken-endständige Assembly.

- **The chain's collapse class (unter 0.450, muß ×3 ~0.22) is an
  ORDER artifact of the candidate assembly — proven by permutation**
  (§14 "L2-Rest-Autopsie", corrected same-day after an owner
  question exposed a wrong first attribution). The lifted u/ü top
  bow sits above the 0.8-xh mark threshold and stays in the body;
  the hand (and the engine's composed order, which the Lotse rides)
  writes it LAST, while the chain assembly emits it BETWEEN the
  slot runs. Re-ordering only that stroke — geometry byte-identical
  — drops unter 0.4503 → 0.0854 and the muß family 0.21–0.24 →
  0.088–0.110; a permutation sweep over all 19 dev words finds no
  other order gain. Named top candidate for the Kette:
  marks-last assembly (own pre-registration; changes the frozen
  baseline, hence a declared re-baseline — the Lotse's wins on
  those words partly beat this artifact). The references are clean;
  the earlier "re-trace muß" decision task is withdrawn.

- **The soll-aware K0 guard (`--structure-guard-soll`): built,
  pre-registered and measured over all 63 words** — the named rescue
  path (c) of the production-chain question. Acceptance becomes an
  interval per structure class between the chain optimum's count and
  the composed init's count (x0 through the same assembler and
  counters): movement only toward the soll. Measured against the raw
  chain in one pinned environment: four of five gates pass — seven
  dev words strictly ink-closer (das −0.012, und −0.007, muß-2
  −0.007; dev median 0.0576 → 0.0494), aiou never negative (up to
  +0.11), marks byte-equal, 63/63 ok at ~10 s/word — but the
  structure axis freezes again (soll distance 107 = 107), and the
  round protocol proves why: the round-ATOMIC rejection discards a
  bundled soll-ward repair together with its violation (unter:
  overlap 3 → 2 allowed, touch 3 → 6 forbidden, one solve). Formally
  not adopted; as a production candidate it dominates the two-sided
  guard on every measured axis. Named next mechanism: zonal
  rejection (freeze only the violating zone's anchors), own
  pre-registration.

- **Duel view: a "Feinschliff (nur Anzeige)" toggle** smooths the
  CANDIDATE traces for the eye ((1, 2, 1)/4, endpoints fixed, three
  iterations) — the display-stage consequence of the v0.6 verdict (the
  ruler never sees the pixel zigzag, so smoothing belongs to the
  consumer, never into the measured candidate). The hand reference,
  the mark dots and every number stay raw; the toggle is off by
  default and the page bytes stay deterministic.

- **Werkbank word cards: an Abstandsprofil under each word — where the
  composition sits beside the author's line**
  (`app/src/sections/admin/words/distanceProfile.ts` +
  `DistanceProfileChart.tsx`, wired into `WordSpineCard`). For every
  point along the stored trace the curve plots the nearest distance to
  the engine composition's centerlines, in x-heights over the trace's
  ink arc — flat near zero reads congruent, a mountain reads
  off-track, pen lifts appear as dashed markers, and hovering the
  curve pins a probe onto the matching spot of the specimen face. A
  display measure by design, not the duel page's DTW residual: trace
  and composition segment their strokes differently (generated
  connectors, deferred diacritics), so a writing-order pairing would
  report segmentation as error — the caption says so outright, and
  the extra-engine-ink direction stays the overlay's job. Pure
  computation module with vitest coverage; new term "Abstandsprofil
  (Werkbank)" added to the glossary.

- **Duel page: a residual profile per word — where the headline number
  comes from** (`tools/tracebench/view.py`). Below each word's numbers
  table the page now plots, per candidate method, the distance to the
  hand re-tracing along the hand's body arc (in x-heights) — flat near
  zero reads clean, a mountain reads off-track. The profile follows
  the optimal DTW pairing the headline `dtw_xh` averages over — never
  a same-point-count subtraction, which would turn everything after
  the first extra loop into a phantom error — so the curve's mean over
  the pairing IS `dtw_xh` and the chart can never disagree with the
  number it explains. Pen lifts of the hand appear as dashed markers,
  marks stay held out exactly as in the headline, the legend
  checkboxes toggle curve and trace together, display decimation
  keeps each window's WORST sample so a spike cannot be smoothed
  away, and hovering the chart pins an orange probe onto the
  matching spot of the hand's trace in the word image. To feed the
  chart, `metric.DtwResult` now also carries the optimal warping
  path (`pairs`) — display-grade access to the alignment in the
  `classified_pass_points` tradition; every measured value is
  untouched (pinned by the existing metric tests). New term
  "Residualprofil" added to the glossary.

- **English style anchored: the Google developer documentation style
  guide becomes the reference fallback for the repository's English
  artifacts** (`sprachregelung.md` §4, owner decision 2026-08-18;
  repository only — the public site is out of scope). The adopted
  core: second person and imperative in instructions, active voice,
  present tense, sentence-case headings, serial comma, descriptive
  link text, timeless wording, inclusive language, alt text, and
  "for example"/"that is" over `e.g.`/`i.e.` in running prose (short
  forms stay fine in parentheses, tables and code comments). Named
  house rules win over the guide: ISO dates, spaced dashes ( — ), the
  narrative rationale style of READMEs and why-comments, untranslated
  German domain terms. Language-neutral mechanics apply to new German
  docs too. Forward-only — no retroactive restyle sweep (measured:
  1,174 spaced dashes and 28 Latin abbreviations in the English
  artifacts alone), and the changelog history is never rewritten.
  Anchored in the `/write-docs` and `/open-pr` skills, in `CLAUDE.md`
  and in `.github/copilot-instructions.md`.

- **Method pages: one register page per tracing-duel route, with a
  shared versioning convention** (`docs/reference/verfahren.md` plus
  `verfahren-kette.md` · `verfahren-lotse.md` · `verfahren-inksight.md`
  · `verfahren-nullprobe.md`; owner request 2026-08-18). Each page carries the method's profile (display
  name, code home, currently adopted constants) and a dated
  version/arm ledger with verdicts and §14 anchors — a register, never
  a second source of truth: every number is a dated quote, the
  evidence lives in qualitaetsmetrik.md §14. The convention: one
  version number per pre-registered arm (the Lotse practice,
  v0.1–v0.9); a method's state is the set of its adopted mechanisms;
  no retroactive renumbering — the chain keeps its historical arm
  names (①–⑨, A1 …), starts at v1 today and only bumps on an adopted
  formulation change; the Nullprobe is deliberately unversioned (a
  control that learns is no control). Indexed in `docs/index.md`
  (tree, quick links, Dokument-Status trigger), new glossary entry
  "Verfahrensseite", pointer in tintenfolger.md §7.8; the stale
  `tintenfolger.md` line missing from the index tree was added along
  the way.
- **The 19-row dev split is live, with a dated re-baseline of every
  standing route** (tintenfolger.md §2.5 activation addendum, owner go
  2026-08-17). The author traced the complete dev assignment (all 19
  occurrences, Galoppieren and das included), so `TRACEBENCH_DEV_IDS`
  now carries the pre-registered §2.5 dev side; the confirmation seal
  on sets A and B is untouched. §14 "Re-Baseline aug17" records the
  new state: identity gate PASS 19/19, chain dtw median 0.0579 (worst
  unter 0.450; the muß class now weighs three-fold at 0.21–0.24, and
  Galoppieren arrives at 0.235 with 5 lost crossings), Lotse 0.0850,
  Nullprobe +1092 % (what the ductus prior buys, re-measured), fusion
  oracle ceiling 0.0491. The wordbench headlines are byte-identical
  (0.108091 / 0.146602), so the ruler change is purely the split
  extension. Findings and the measure plan: tintenfolger.md §7.10;
  the p-descender question (the plate crosses where the template
  retraces) went to the author as a Todoist task.
- **Lotse v0.7 and v0.9 adopted, v0.8 honestly rejected — the
  junction-pinch campaign** (`tools/inkpilot/pilot.py`, all three §14
  pre-registered before their first numbers). v0.7 widens the adopted
  ride-double trigger's effect into a zone
  (`RIDE_DOUBLE_ZONE_MARGIN_UNITS` = 0.35): crossing defects 35 → 32,
  retrace-arc gap 0.285 → 0.044 — and the honest miss that the loop
  class is unreachable by ANY occupancy trigger (the up-pass boards
  the merged rail at crossing height). v0.8 (map right-of-way around
  the map's own self-intersections) proves the topology completely —
  net crossing defects 32 → 4, dtw median under the chain for the
  first time — but rides the raw composed map and pays with ink
  coverage: both rungs rejected by the pre-registered aiou kill,
  rescue path named (§7.9). v0.9 keeps the windows and PINS them onto
  the ink's boarding points (topology and angle from the map, position
  from the ink): all gates pass at window 0.35 — dev-19 dtw median
  0.0578 (level with the chain, paired Δ-median −24 % — the first
  route ever to meet the §14 primary criterion), p90 halved, net
  crossing defects down to 7, and those 7 are mapped to soll-vs-hand
  disagreements rather than ride failures. The confirmation sets
  remain the keystone before any adoption beyond route constants.
  New glossary entry: Junction-Pinch.

- **The dev/confirmation split re-draw, pre-registered before any number
  exists** (`docs/proposals/tintenfolger.md` §2.5, owner decision
  2026-08-16). Once all 63 words are hand-traced, the trace bench's
  split moves from "the ten first-traced words" to a stratified,
  performance-blind key over letter classes: dev stays minimal (the ten
  burned words + Galoppieren + das — the only two additions needed for
  every writing-mechanics class to appear at least twice), and the
  held-out material is split into an open confirmation half (A, 19
  words) and a SEALED half (B, 19 words) that only opens for the major
  adoption decisions — staged reveal against confirmation wear-out.
  The seal is in force immediately; the dev extension and the
  `TRACEBENCH_DEV_IDS` change take effect at 63/63 as a declared ruler
  change with a dated re-baseline of every standing route. Repeats of
  one word never cross the split boundary; movement is only ever blind
  and pre-registered toward dev, never back. The 33 Abb.-20 pair
  drills stay outside the word split (the K3 word/drill lesson) and
  get their own blind two-way split drawn now, while no drill was ever
  traced or benched: 18 open (for pre-registered word/drill diagnoses
  and future drill tuning) and 15 sealed, keyed by the left letter's
  exit class; the glossary entry "Referenzsatz" carries the revised
  invariant.

- **The word editor gets an adjust mode, and the Wörter view a review
  stack of the hand-authored traces** (Werkbank W3). „Anpassen" — the
  wizard's Weg mechanism ported to the word editor — drags the drawn
  line locally with a smoothstep falloff (radius slider in x-heights,
  falloff ring under the pointer), so one tablet wobble no longer costs
  a whole redraw; strokes are never split, merged, reordered or
  reversed and points only move (the trace bench measures pen-lift
  structure and writing order — pinned by unit tests on
  `warpTraceStrokes`). Saving one of the ten frozen dev-split words now
  asks once explicitly („Trotzdem speichern") — that save changes the
  frozen ruler's reference and owes a dated §14 re-baseline. The new
  „Nachgefahren" tab stacks every `authored` trace over its specimen
  crop (or bare on white — wobbles read best on the naked line), badges
  dev-split membership and client-side frame staleness (the fixture
  exporter's own gate tolerances), and jumps straight into the editor;
  a save now refetches the trace list (`refreshWordTraces`), so the
  evidence views show the stored state instead of the load-time
  snapshot. A `frame_stale` row heals on open: the editor re-expresses
  the strokes through the stale frame into the sample's current one
  (same place on the crop pixels) and the save stores the fresh
  registration — so the badge's remedy really is re-tracing, instead
  of the save echoing the stale frame back forever. Gesture handling
  is hardened against mid-drag mode flips (a stray toolbar graze can
  no longer weld pen samples onto a stored stroke — the move handler
  branches on the live gesture, never on the mode).

### Changed

- **Chain v4: the ink-evidence mask is now the default on the follower,
  the harvest and the tracebench chain provider — the author's go on the
  measured K-C pass, with a dated re-baseline** (§14 „Kette v4 `aug21`").
  `FollowWeights.ink_evidence` and `HarvestOptions.ink_evidence` flip to
  True; the CLI grows `--no-ink-evidence` (the `retrace_guard` negation
  pattern) and `chain_provider` an `ink_evidence` kwarg, both as the
  byte-identical pre-v4 archaeology path — no algorithm code moves, and
  the frozen bench mask still grades against ALL ink. Re-measured from
  scratch in a second pinned environment (fixtures re-fetched bit-exact,
  BLAS pinned, both arms paired): the pre-flip chain provider reproduces
  the declared v3 baseline exactly (dtw median 0.049135, p90 0.0891,
  worst muß 0.1097); the full-63 archaeology run is byte-identical to
  the pre-flip default; 23 words drop 44 components — exactly the aug20
  count — with all 40 drop-free words byte-identical. The flip itself:
  soll distance 103 → **85** (11 better / 1 worse), dev-19 dtw median
  0.0491 → **0.0448**, aiou median 0.7161 → **0.7481**, spurious
  retrace zones 13 → 7, the Galoppieren i-dot heals (marks missing
  1 → 0), worst per-word dev loss +0.0004 (die-2, whose magnet is the
  word's OWN mark — the named successor is the mark-claim separation).
  Honestly named environment variance vs aug20: base soll 103 vs 107,
  die-2 soll −1 there / +1 here, streiten aiou −0.0075 here. Declared
  re-baseline v4: chain provider dev-19 dtw median 0.0491 · p90 0.0891
  · worst muß 0.1097 · aiou 0.7021; follower soll-stack dtw median
  0.0448 · aiou 0.7481 · 63-word soll distance 85. Route pairings
  (Lotse, InkSight, Nullprobe) re-quantify against v4 at their next
  measurement; the production re-harvest of stored `traced` rows stays
  behind owner-go + dbsnapshot. Docs: §14 entry, verfahren-kette.md
  (v4 + ledger row), glossary „Tinten-Evidenz-Maske" updated,
  tintenfolger.md §7.3 K-C marked adopted.

- **The agent instructions went on a diet — details moved into the docs
  they belong to** (`CLAUDE.md` 82 → ~24 KB, `.github/copilot-instructions.md`
  mirrored): the "Repository state" prose dump became a compact per-directory
  map with invariants + doc pointers, the self-verification section became a
  routing table, and the 23 facts that lived ONLY in the instructions
  (frontend routes/deploy details, glossary-grade idioms, write-API
  semantics, licensing footnotes …) were moved into their owning docs
  (`frontend-stack.md`, `glossar.md`, `werkzeuge.md`, `write-api.md`,
  `qualitaetsmetrik.md`, `quellen-und-rechte.md`, `architektur.md`,
  `datenablage.md`) so nothing was dropped — the instructions now say where
  things live and which rules bind, the docs say what is true.

### Added

- **Durable working rules lifted from machine-local session memory into
  the repo instructions** (`CLAUDE.md` guardrails + the
  `.github/copilot-instructions.md` mirror), so cloud/web sessions — which never
  see the local memory directory — inherit them: the rescue-path duty for
  rejected measures, the squash-merge race recovery (fresh branch +
  cherry-pick, wait for "green and review-clean"), Opus for delegated
  agents (Claude-side only), BLAS thread pinning for solver measurement
  runs, no AI-development disclosure on the public site, and legibility
  over period authenticity in UI.

- **The O2-trim jitter, pre-registered with both outcomes valid — and
  the bug turns out to be an accidental class rule** (`core/compose.py`
  `ENTRY_FLANK_DIP_TOL`, kept at 0.0; §14 „O2-Trim-Jitter"). The K3
  side find made testable: a tolerance of 0.02 xh on the rising-flank
  walk restores the intended 0.78 trim for arcade heads whose spline
  lead-ins jitter in the first step. Measured: word_loss +4e−6 (a
  wash), pair_loss byte-identical, and exactly THREE words move —
  splitting precisely along K3's arrival ladder: von (o→n) −0.0126
  (the restored trim is a clear win there), Zorn/Sporn (o→r) +0.0112
  and +0.0017 (o→r wants to arrive lower, as K3 measured). Today's
  strict guard accidentally implements exactly that class split
  (n lead-ins jitter, r lead-ins do not), and the frozen ruler prefers
  it by micrometres — so per the pre-registered criterion the bug
  stays, documented instead of silent, and the real finding is that
  the UNIFORM O2 target height for arcade heads is wrong: a proper
  class rule (n high, r lower) goes on the table as its own
  pre-registration once the confirmation set exists.

- **Lotse v0.5 adopted: map geometry in ride-side double zones — the
  first crossings return, and the fusion ceiling gets its number**
  (`tools/inkpilot`, §14 „Route Lotse v0.5"). The combination of the
  two parked arms — A5's detection (which rail pixels does the word
  ride twice) with v0.4's geometry (ride the composed map there, it
  carries the crossing): the first pass keeps the ink's mid-line,
  every later pass takes the map. All pre-registered gates pass: dev
  dtw median 0.101 → 0.085, `und` 0.087 → 0.043 (now beating the
  chain there), 5 of 23 missing crossings return (+1 spurious, within
  bounds), retrace arc ratio 2.48 → 1.66, aiou −0.002. Route standing
  0.085 vs the chain's 0.062 (gap 1.4×) with sharp complementarity —
  the Lotse wins exactly the structure-heavy words (unter −0.387,
  muß −0.129), the chain the smooth ones. The per-word oracle fusion
  („Vier Augen" ceiling, not a result) now measures 0.056 — better
  than either route alone; the honest reference-free selector remains
  the open question, with B1's order-blind-ranker lesson applying
  verbatim.

- **Lotse arms round two: the rail run-out (owner find) adopted, three
  others honestly parked** (`tools/inkpilot`, §14 arms). The owner's
  review find — "the d line stops at the crossing" — turned into the
  pre-registered rail run-out: a ride ending on a rail that runs
  unbranched into a degree-1 skeleton endpoint within 1 xh continues
  to the rail's end (the composed map undershoots inked tips via the
  loop-exit trim and the +7–10% reach gap; the ink does not). Adopted
  at 1.0: dev dtw median 0.119 → 0.101, the `und` outlier 0.343 →
  0.087, aiou up, spurious marks halved, structure untouched by
  construction. The junction chord (v0.3) and the map right-of-way
  (v0.4) measured and rejected by their own gates — the missing
  crossings live on LONG shared rails the skeleton merges over the
  whole overlap, which neither node surgery nor map-side retrace
  zones reach; named successors: sub-stroke separation from width
  evidence, and map geometry in ride-side double zones. Route
  standing: dev dtw 0.101 vs the chain's 0.062 (gap 2.0× → 1.6×),
  aiou clearly above the chain.

- **The Lotse route (owner idea): ride the skeleton mid-ink, ask the
  ductus like a map — built, pre-registered, first honest numbers**
  (`tools/inkpilot` + §14 „Route Lotse" + a pinned viewer colour).
  Geometry comes entirely from the measured skeleton (the routeg
  graph), order and every junction decision from the composed word
  acting as the map: a global Viterbi assignment of map samples to
  ridge points (graph ride cost + map deviation + a bridge state),
  connected by shortest pixel-chain walks; leading/trailing bridges
  over blank paper are trimmed. ~0.1 s per word, six unit tests on a
  synthetic cross. First measurement (dev split): the gate is missed
  (dtw median 0.119 vs the chain's 0.062; hand crossings collapse to
  zero because double passes share the same skeleton rails through a
  junction and never intersect transversally) — but `unter`, the
  chain's catastrophe word, falls 0.450 → 0.064 and aiou rises almost
  everywhere. Named rescue paths: the width-evidence offset double
  pass (plan measure A5, the fixture's `width_map`), the smoothing
  stage, and the `und` autopsy; the route stays open.

- **The guarded chain measured as the production trace — pre-registered
  over all 63 words, with a two-sided guard built as the executed
  rescue path** (`tools/pairlab/follow.py` `--structure-guard-two-sided`
  + `qualitaetsmetrik.md` §14 „Wächter als Produktions-Kette"). The
  released one-sided guard passes three gates outright (never worse on
  the 10 authored references and better on three of them, ink coverage
  never falls, marks byte-identical) but loses one soll-required
  crossing on three words — it caps structure INVENTIONS while the ink
  pull may collapse a small loop unpunished. The two-sided guard
  (init counts binding in BOTH directions per the K0 invariant) then
  measured as a clean Pareto picture: structure frozen at the chain's
  level on all 63 words, dtw never worse and better on two, aiou up to
  +0.12 — formally NOT auto-adopted because a both-ways veto can never
  satisfy the „strictly better somewhere" leg; the adoption is now an
  owner decision, with the soll-aware K0 guard named as the next
  rescue path. Two standing findings en route: the chain solve is not
  bit-reproducible across BLAS thread environments (solve comparisons
  and any production wiring must pin `OPENBLAS_NUM_THREADS`), and
  pinning the threads collapsed the runtime gate entirely (raw chain
  63 words: 87 min → 2.7 min; two-sided guard: ≈17 s/word).

- **The rescue-path register: every honest negative names its way back
  into the game** (owner directive 2026-08-16, after the P3 0/3 round):
  `docs/proposals/tintenfolger.md` §7.9 collects, per rejected measure, the finding or
  measured ceiling, the named conversion path and its trigger (B1's
  proven −0.0124 oracle → the order-aware „Chor" selector; K1's real
  +126° arrival error → the connector-FORM hypothesis; K3's jitter
  side-find → the O2-trim bugfix candidate; arm 9 → the „Lotse" route;
  the cross-cutting one: kills decided by net deltas the ruler barely
  registers get a pre-registered humanbench word round as tie-breaker).
  Standing rule recorded there and in the new glossary entry
  „Rettungsweg": every rejected §14 entry closes with its rescue paths
  (or an explicit „none named"), and a rescue path is always a NEW
  mechanism, new evidence or new sensor with a fresh pre-registration —
  never the same knob re-run with softer gates.
- **Wave 2, P3: head coarticulation as entry class rules — all three
  measured, all three honest negatives** (`core/compose.py` +
  `qualitaetsmetrik.md` §14 „Welle 2 · P3"; owner priority). The
  pre-study (248 dissected occurrences, Laufform-relative) proved the
  asymmetry — tails are per-class constants, heads are real
  coarticulation after high exits (p < 0.0001) — and three
  pre-registered entry rules mapped it into the composer: K1 the low
  bar→round couple (`BAR_ENTRY_COUPLE_Y`, shared placement/connector
  index), K3 the unified cover-bow→arcade couple lift
  (`COVER_ARCADE_ENTRY_LIFT`, replacing today's inconsistent
  foot-vs-0.78 coupling), K2 the rotated d→round departure on the
  rescued chord (`LOOP_ROUND_EXIT_ROT_DEG`, never the twice-rejected
  stub trim). Every ladder was measured and killed by its own
  pre-registered gate: K1's class words vote in opposite directions,
  K3 wins the words but loses the drills of the SAME joins (von
  −0.009 vs. drill `on` +0.017 — the word/drill split is the find),
  K2 loses both rulers monotonically. All three knobs ship
  DECLARED-BUT-NEUTRAL for the confirmation-set re-calibration;
  rendering stays byte-identical. Side find: a 0.0004-xh spline
  resampling jitter silently disables the generic 0.78 entry trim
  for arcade heads (own bugfix candidate) (#366).

### Fixed

- **The fluent body widening is alive on `/write` again — production now
  renders what the bench has been measuring all along** (#289). The
  round-letter body widening (`core/pipeline.py` `FLUENT_BODY_PITCH`,
  the deliberate jul08 overlay decision) keys on the template row's
  `glyph` field, and both production row builders — the write router's
  and the labs' live-DB mirror — hand-rolled that dict without it, so
  every `/write/glyphs` + `/write/word` render composed with pinched
  e/a/u/o bodies while the wordbench fixtures (whose rows carry
  `glyph`) measured with the widening on. One shared builder
  (`core.database.models.template_render_row`) now feeds both paths, a
  parity test pins the fixture exporter's row to that exact shape plus
  bookkeeping (`tests/test_render_row.py`), an HTTP regression test
  holds the widening on the Gleichzug path, and the fixture-rebuild
  gate (`tools/wordbench/fetch_fixtures.py`) compares full rows
  instead of stripping `glyph` — its `--verify` therefore needs a
  deployed API at or after this fix. Bench numbers are untouched by
  construction (the fixtures already carried the field); only the
  served geometry moves, toward what the frozen rulers measured.

## [0.26.0] — 2026-08-15 — Optimization plan + wave 1 + advance round + viewer polish

### Added

- **Wave 1, B1: best-of-N InkSight ensembling — rejected by its own
  gate; the selection signal is the finding**
  (`tools/inksight/{augment,ensemble}.py` + a back-compatible
  `--manifest` decode mode; pre-registered and measured in
  `qualitaetsmetrik.md` §14 „Welle 1 · B1"). Ten deterministic
  augmentation variants per word (InkSight's own training
  augmentations), decoded on CPU (100 decodes), ranked exclusively
  against the MEASURED ink (symmetric skeleton chamfer — never the
  authored reference), every variant additionally benched against
  the hand per the owner's oracle directive. The determinism gate
  passed token-identically on all ten identity decodes. The primary
  gate FIRES: the ink-ranked winner ties the plain decode exactly
  (paired median +0.000, p = 1.0) — but the ORACLE column proves a
  paired −0.0124 median (better on 7 of 9 words) sits inside the
  same N answers: the coverage-based ranker is blind to traversal
  ORDER (on `unter` two variants sit 10 % apart in the selection
  metric and factor 4.9 apart in dtw). Side results: `Wer` is
  healed (T0's contract failure), structure is net cleaner
  like-for-like, and augmentation costs contract conformance
  (median 4 of 10 variants survive per word). The infrastructure
  stays; the named successor is an order-aware selection signal
  with the measured +0.0067 gap as target and −0.0124 as ceiling (#364).

- **Wave 2, P2: the align floor becomes the bounded touch; the
  arcade air is closed as hand variance** (`core/compose.py`,
  continuing the owner's directive that the x-drift is still real
  and the work must continue). The measured align-class error (+0.072 median over 36
  dissected joins) is rise-INDEPENDENT, so the two registered knobs
  were an additive diagonal trim and the align/nested clearance
  floor. The single-knob sweep adopted the FLOOR
  (`ALIGN_MIN_CLEARANCE` 0.06 → 0.0 — columns may touch, never
  overlap, the bowl-tuck semantics): `word_loss` 0.108446 →
  **0.108091**, `fechten` 0.173 → **0.144** (its f→e align_floor
  was the +0.31 outlier; cumulative 0.222 → 0.144 over the advance
  round), `pair_loss` and soll agreement unchanged. The diagonal
  TRIM is declared-but-neutral (rejected by the ruler at every
  dose) — and the §14 entry closes the ARCADE AIR with a mechanism
  exhibit instead of a constant: under air the same word votes both
  ways per specimen (wenn −0.030 vs wenn-2 +0.089; dissected spread
  MAD 0.096), so the hand's own arcade variance, not a calibration
  error, carries that class; revisit only with the confirmation
  set. compose-golden regenerated as the declared re-baseline (#363).

- **Wave 2, P1b: the backward-clearance class gets its named longs
  exception** (`core/compose.py`, owner find on the streiten
  overlay: the word's FIRST letter sat beside the ink). The P1
  per-join re-measurement on streiten itself acquitted the t-exits
  (−0.07/−0.04 after calibration) and convicted `longs→t`: the
  longs descender exits BACKWARD and fell into the uniformly
  reduced backward clearance (−0.156 per dissection; the global
  registration then pushed the whole word off the ink). Re-split by
  left letter: w/v (n=12) and capital W want the re-calibrated
  0.11; `longs` keeps `LONGS_BACKWARD_CLEARANCE` = 0.30 as the
  named exception (its dissected row sides with 0.30; the two bench
  longs-words split their ruler vote — confirmation-set item).
  `word_loss` 0.108991 → **0.108446**, `pair_loss` unchanged,
  exactly ONE word moves vs. merged P1 (streiten 0.189 → 0.154),
  soll agreement unchanged; the in-between attempt (restoring ALL
  non-w/v backward exits to 0.30) was measured and rejected — a
  correction class can be cut too wide, too. compose-golden
  regenerated as the declared re-baseline; §14 records the
  corrected attribution in a dated addendum (#362).

- **Wave 2, P1: the advance calibration from the measured joins —
  the red now sits on the ink** (`core/compose.py`; owner find on
  the K1b overlays: the composition drifted progressively right of
  the specimen ink on long words). Diagnosis chain, all
  pre-registered in `qualitaetsmetrik.md` §14 („Welle 2 · P1"): a
  per-slot drift profile over the 63 bench words (median −0.0375 xh
  per letter too wide), then the SIGNED per-join advance error over
  the 218 dissected joins of the hand (median +0.05, two class
  errors in opposite directions), then report-only placement-rule
  provenance on every generated connector — the one uniform
  ink-clearance floor carried both classes. Adopted after a
  single-knob decomposition sweep: the BOUNDED bowl-exit tuck
  (b/c/d/o clearance 0.0 — columns may touch, never overlap; the
  full measured tuck collided in word context and was rejected),
  the backward w/v clearance 0.30 → 0.11 (the jul-11 value was
  calibrated against the pre-registration-fix overlay), and the
  bar rise slope 0.55 → 0.69. Honest negative kept on record: the
  measured arcade-entry air (n/m, −0.18 per dissection) regresses
  the word bench and is not adopted; the r→e arm-fuse deficit is
  real but entangled with the r-arm template length. Results:
  `word_loss` 0.110983 → **0.108991**, `pair_loss` 0.165725 →
  **0.146602** (the largest pair improvement in the bench's
  history), `meas_doff` median 0.195 → **0.131**, signed overall
  median +0.050 → +0.010, and `zwei` gains its second retrace zone
  (`soll_zones_agree` 8/10 → 9/10). compose-golden regenerated as
  the declared re-baseline. Glossary gains „Bowl-Exit-Tuck" (#361).

- **Wave 1, A1: the opt-in mark refit halves the chain candidate's
  mark position error** (`tools/pairlab/marks.py`, wired as
  `HarvestOptions.mark_refit` → `tools.tracebench.run --mark-refit`,
  default off with a proven byte-identical baseline): after the body
  solve, each diacritic mark is rigidly translated onto the skeleton
  ink the body did not claim — assignment via the shared
  `nearest_unique_point` with refusal on ambiguity (search radius
  0.6 xh = the ruler's own match limit), contested clusters leave
  both marks untouched, and every verdict is reported in
  `meta.mark_refit`. Pre-registered and measured in
  `qualitaetsmetrik.md` §14 („Welle 1 · A1"): `mark_pos_err_xh`
  median 0.1285 → 0.0576 (−55 %, all four pairable words improve,
  closing ~86 % of the gap to the prior-free control), structure
  counters exactly unchanged across all ten words, zero refusals,
  `marks_spurious` unchanged — KEPT, opt-in; whether the refit ever
  enters STORED traces is a separate author decision gated on the
  confirmation set. Side find recorded as candidate A1b: the harvest
  and the ruler classify a long u-bow differently (no arc cap vs.
  0.8 xh), so four reference words carry no matchable mark at all (#360).

- **Wave 1, K1b: the t writes its crossbar without a pen lift — the
  offset stem-return pass** (`core/compose.py`,
  `BAR_RETRACE_BULGE_UNITS` = 0.06 xh measured from the hand's
  descent/ascent offset): the bar stroke is prefixed with a generated
  bridge from the previous stroke's foot up to the bar start —
  centerline only, no silhouette (the cap_retrace pattern), bulged
  right so the counters see a second pass — and loses its lift.
  Pre-registered and measured in `qualitaetsmetrik.md` §14 („Welle 1
  · K1b"): the expectation lands cell for cell — `unter` reaches
  3 crossings/3 retrace zones and `mit` 2/2 (both = the hand),
  `soll_cross_agree` 7/10 → 9/10, `soll_zones_agree` 6/10 → 8/10, and
  the four bar-against-stem `soll_overlap` entries disappear (the
  hand has none). Remaining disagreements are the known chart cases
  (linken-k, Wer-W, zwei-z). Gates: wordbench headlines within
  ±0.00004, only t-words moved, compose-golden regenerated as a
  declared re-baseline. The entry also declares the post-K1 chain
  baseline `r1` (cascade of K1 into the fit): only `unter` differs
  from `r0` (+0.0301 dtw at one invented crossing fewer) (#359).

- **Wave 1, K1: the bound t-bar keeps a measured overrun past its stem
  crossing** (`core/compose.py`, `BAR_CROSS_OVERRUN_UNITS` = 0.2 xh,
  measured on the authored references of `mit` and `unter`; the join
  launches from the bar tip while the next letter's placement stays
  anchored to the STEM). Pre-registered and measured in
  `qualitaetsmetrik.md` §14 „Welle 1 · K1": the registered expectation
  was REFUTED and the refutation is the find — at word level the
  composed pen path always pierced the stem (the crossing was
  bookkept as a join contribution), so K1 moves the ductus-fixed
  crossing into the letter itself (the bound t's per-letter cell
  becomes 1/1, matching the hand) without changing word topology. The
  REAL t deficit sits in the stem retrace: the hand descends and
  re-ascends the stem as two offset passes, the composition bridges
  the return collinearly — invisible to the counters; K1b (an offset
  generated return pass) is named as the next candidate. Gates:
  `bench_loss` +0.0003 (kill threshold 0.002), `pair_loss`
  byte-identical, only t-words moved; the compose-golden fixture is
  regenerated as a declared re-baseline (#358).

- **The per-method optimization plan for the word-tracing campaign**
  (doc-only, `docs/proposals/tintenfolger.md` §7): built from a
  per-word × per-method defect matrix over all duel artifacts plus a
  source-verified research round (four parallel agents). Names the
  measured levers — two words carry 59.8 % of the chain fit's dtw,
  the touch class breaks 6 of 7 guard rejections, i-dots sit worse
  than the prior-free control's — and lays out candidate experiments
  per method in four waves: composition topology (cut-with-overrun,
  pass-through coupling; the W onset is a chart-ductus gap for the
  author, not a composer rule), route-A reformulations (separate
  mark refit, SDM/density-aware data term, explicit crossing
  variables, barrier-instead-of-veto, two-pass retrace evidence,
  GNC schedule), raw-InkSight levers (best-of-N ensembling, tiling
  to aspect ≤ 2, cheap A/Bs, learned-init + classical refine,
  prior-driven retrace recovery), the own small trajectory model,
  and fusion. Every measure requires its own pre-registered §14
  entry before the first number. §14 (Arm ⑨) gains a dated
  correction: the "9 invented touches" belong to the chain fit, not
  the composition (measured: the composition prescribes 2 touches,
  both w-internal, and 4 t-bar overlaps) (#357).

### Changed

- **Duel-method display names decided and propagated** (owner decision
  2026-08-16): the readable method family is Hand · Kette · InkSight ·
  Nullprobe (planned: Zögling · Vier Augen · Feinschliff · Chor ·
  Lotse as working title). The structure-guarded chain run is THE
  „Kette" (fit-invented crossings are never right — join-formed ones
  live in the Soll budget, hand-vs-composition gaps are composer
  defects to fix at the source), the duel page carries ONE InkSight
  (the text-prompt variant was diagnosis and leaves the page), and
  the prior-free control is the „Nullprobe". The translation table
  lives in the new glossary entry „Duell-Namen"
  (+ `tintenfolger.md` §7.8 incl. the new owner-proposed „Lotse"
  route sketch: ride the skeleton mid-ink, ask the ductus like a map
  at junctions); technical names (Kettenfit, Route G, `routeg-graph`)
  stay unchanged in code and dated §14 entries, with display-name
  pointers added to `tools/routeg` and `tools/pairlab/follow.py` (#365).

### Fixed

- **Duel viewer: the writing animation, the control's visibility, and
  two lay legends** (`tools/tracebench/view.py`, all from the owner's
  page review): the write-on animation now dashes in REAL geometric
  units via `getTotalLength` instead of the normalised unit
  pathLength — the old combination with `non-scaling-stroke`
  mis-rendered in some engines as ink writing on the left while
  erasing on the right until the final state snapped in; the
  prior-free control gets a pinned high-chroma cyan (the order-based
  palette had handed it the brown that vanished against the sepia
  plate); a „Die Verfahren in einem Satz" explainer names per layer
  what each method uses (human hand · ductus library + ink · learned
  open model without ductus · pure image processing), and a column
  legend explains dtw_xh/aiou/cross/retrace in lay terms — including
  the honest note that none of today's columns punishes micro-wobble
  smoothness. The regenerated page is republished to the same
  artifact URL (#365).

## [0.25.0] — 2026-08-15 — Trace editor rebuild + the tracing duel: tracebench stages, routes A/B/G, arms, structure counters

### Added

- **Route G: the prior-free control of the Tintenfolger duel**
  (`tools/routeg`, `docs/proposals/tintenfolger.md` §4b) — a third
  candidate that recovers a writing order from the ink ALONE: frozen
  skeleton → segment graph (adjacent branch pixels merged into one node,
  the paper's crossing „cluster") → greedy traversal by good
  continuation, converted into a `tools/tracebench` candidate through the
  harvest's own `_px_to_word_units`. Its role is control, not
  competitor: the distance between it and the chain fit on the same ten
  words is the first measured number for what the ductus prior buys.
  Measurement only — no DB, no API, no `core/`, no rendering.

  **The reference implementation is not what runs here, and the reason is
  documented rather than papered over.**
  <https://github.com/gioelecrispo/wor> (Diaz et al. 2022) carries a real
  MIT licence, so the licence is not the blocker — the runtime is: 234
  MATLAB `.m` files needing MATLAB 2016a+ with the Image Processing
  Toolbox, no PyPI package, no Octave path, an unlicensed
  `SalernoSkeletonization.jar` in the tree, and no commit since
  2022-10-06. Neither MATLAB nor Octave exists here or in CI, so a
  `wor()` number would be reproducible by nobody running this repo's
  gates. The control is therefore a deliberate MINIMAL own reduction —
  three decisions, each named beside the reference's richer one it
  replaces — and it explicitly declines the reference's learned
  start-point prior (a 2-D Gaussian fitted on SigComp2009 SIGNATURES),
  because a control that borrows a learned table is not prior-free.
  `prepare.py` still writes exactly `wor()`'s documented input format, so
  only stage 2 would have to be swapped by anyone holding a MATLAB
  licence.

  Measured on the frozen dev split: `aiou_median` 0.833 — *higher* than
  the hand references score against themselves — while `dtw_xh_median`
  is 0.820 and the structure gates collapse (15 crossings missing, 15
  retraces missing, +90 pen lifts). Riding the ink is not writing it,
  which is exactly what a control is for (#354).

- **The duel page shows the DETECTED structures, so the eye can audit the
  detector against the ink** (`tools/tracebench/view.py::structure_marks`,
  owner request after the t carried three „retrace" zones): every layer
  gains rings at the frozen crossing detector's points and translucent
  bands along its retrace passes — dashed when the pass is an OVERLAP of
  two pen strokes (the Sütterlin t crossbar riding the entry connector
  and the exit stroke, which is what those extra zones turned out to be)
  rather than an out-and-back retrace of one stroke. The distinction is
  drawn from the stroke indices the frozen `detect_retrace_pairs`
  already returns; the counters themselves are untouched, no reported
  number changes, and a „Struktur" toggle hides the markers. The numbers
  table states every layer's OWN detected counts (crossings, merged
  retrace zones — the hand reference included) plus two muted
  ductus-target rows per word: the sum over the ISOLATED letters (hover
  shows the budget letter by letter) and the whole composition with its
  generated connectors, whose difference is the joins' contribution. The
  hint text explains the reading (#349).

- **Arm ⑥b: the class-aware landmark correspondence**
  (`tools/pairlab/follow.py::classed_targets`, target mode
  `extrapolated_classed`) — the pre-registered answer to the
  correspondence cap (12 of the dev words' 21 landmark correspondences
  aim at ink that carries NO crossing at all): a row whose refinement
  reason is a by-design non-crossing of the ink (`touch_point` ·
  `t_junction`, `LANDMARK_NONCROSSING_REASONS`) gets weight 0 through
  the existing pre-whitening — the row neither pulls nor costs anything
  — while the surviving rows' `1/σ²` weights re-normalise to mean 1 over
  the survivors; the walk failures keep their raw target, because there
  the ink CAN carry a crossing the refinement merely failed to find. The
  calibration pass now reads all three modes
  (`LANDMARK_CALIBRATION_MODES`), so the arm's rung comes from a parity
  measured with the class rule ON (§11c). `chain.py` and the frozen
  `landmarks.py` are untouched, and at `landmark == 0` every solve stays
  byte-identical. Pre-registration, measurement and verdict in
  `docs/reference/qualitaetsmetrik.md` §14 (Arm ⑥b); glossary gains
  „Korrespondenz-Kappe" and „klassenbewusste Korrespondenz" (#348).

- **Arm ⑥ groundwork: the ink follower's landmark term can aim at the
  EXTRAPOLATED junction crossing instead of the raw skeleton branch
  point** (`tools/pairlab/follow.py`, `docs/proposals/tintenfolger.md`
  §3). Thinning displaces a branch point by up to the local stroke width
  — more than the anchor spacing the term exists to correct — so
  `extrapolated_targets` walks the skeleton around each assigned branch
  point, drops the junction-distorted core (one stroke width), fits one
  straight line per „gute Fortsetzung" branch pair and intersects them;
  the local half-width rides along as an isotropic uncertainty and
  enters as a per-target `1/σ²` weight (mean 1, so the term keeps the
  scale a weight is calibrated at) by pre-whitening the chain operator's
  rows — no change to `chain.py`, gradient still exactly analytic. Every
  step refuses rather than guesses, a refusal keeps the raw point and the
  reason is reported next to the correspondence's own drop reasons, and
  the reasons separate what the INK cannot support (`touch_point` ·
  `t_junction` · `ill_conditioned`) from what this refinement failed to
  find (`no_junction` · `few_branches` · `no_continuation_pair` ·
  `far_from_branch`) — only the second kind is ever worth chasing.
  `--landmark-targets
  extrapolated|extrapolated_uniform|raw` selects the formulation (the
  raw arm is the A/B control, the uniform one separates target from
  weighting), and `--landmark-calibrate` reads `e_geo / e_landmark` at a
  follower optimum with the term forced INERT, so the arm's rungs come
  from measured ratios rather than by analogy (§11c). NO weight is
  adopted: the default stays 0.0, at which the whole block is skipped
  and every solve is byte-identical (pinned) (#346).
- **…and it now fires on real ink: the junction walk follows the
  SKELETON and swallows the junction cluster** (`tools/pairlab/follow.py`).
  Measured on the 10 hand-traced dev words, the first form of the walk
  refined nothing at all — 21 of 21 targets stayed raw (16
  `no_continuation_pair`, 5 `few_branches`), and a wider window made it
  worse rather than better. Two mechanisms, both measured on the real
  skeletons at xh ≈ 30 px: (1) the walk labelled connected components of
  a EUCLIDEAN annulus, and on cursive ink two limbs of one junction
  reconnect inside it — its components reached 19–49 px where a 1-px arc
  across the 6–9 px annulus is 13 px at most, so limbs were welded into
  one branch with a meaningless direction; (2) thinning splits one
  shallow crossing into TWO Y-junctions bridged by a short segment (the
  partner sits 9.4–13.2 px away where the ink is 6.4–8.4 px wide), and a
  core stopping before the bridge walks a real X as a T, which three
  limbs can never repair. The walk is now geodesic along the ink
  (`_arc_field`), limbs keep their identity from the core boundary
  outward and a confluence is blocked rather than merged, and the core
  grows into a junction cluster (`FOLLOW_LANDMARK_CLUSTER_WIDTHS = 4.0`
  half-widths, the measured bridge bound with headroom).
  `FOLLOW_LANDMARK_CONTINUATION_TOL_DEG` goes 30° → 35°, from a
  measurement rather than by loosening: a genuine continuation's chord
  deviation is the CURVATURE its limbs turn through over the walk span,
  `(s0+s1)/R`, which reproduces the observed deviations to a median 3.8°
  (n = 6 pairs whose limbs fit one circle to < 1 px) and bounds them at
  34° for this geometry — at 30° four of the eight resolvable crossings
  were refused by 0.8–1.5°, and the result is flat from 35° to 45°.
  Refinement rate on the dev words 0/21 → 8/21, which is 8 of the 9
  targets whose junction has four or more limbs at all; the other 12 are
  `touch_point` (5) or `t_junction` (7), i.e. ink with no crossing to
  extrapolate. Still no weight adopted — the default stays 0.0 (#346).

- **Route B T0 measured: raw InkSight Small-p on the dev words**
  (doc-only — the pipeline shipped in #340; results in
  `qualitaetsmetrik.md` §14 „Route B T0" and the tool README). Raw,
  unadapted, CPU: `derender` lands at dtw 0.0956 median — 1.5× the
  chain fit and 8.6× ahead of the prior-free control — with CLEANER
  crossings than the chain (1 invented ring) but most retraces lost
  (+20 pen lifts): exactly the class the ductus prior owns. Against
  the paper's ablation, the word-conditioned `text` prompt is WORSE
  than plain `derender` on this out-of-distribution script, and the
  `r+d` prompt (43 min/word on CPU) was cut after one diagnostic data
  point — it reads the Sütterlin „Wer" as „Olomi". T0 is the
  documented OOD baseline; the next route-B step remains an own small
  trajectory model on engine pairs (#356).

- **Arm ⑨: the topology guard — a round-level acceptance rule for the
  ink follower** (`tools/pairlab/follow.py`, pre-registered in
  `qualitaetsmetrik.md` §14 `aug16`): before the first round the
  initialisation's own v2.1 structure class counts (crossings, retrace
  zones, touches, overlaps — measured by the bench's own
  `tools.tracebench.counters` on the assembled trace) become the
  budget; a solved round that exceeds any class is re-solved with
  halved travel bounds (at most `STRUCTURE_GUARD_MAX_RETRIES` = 2
  times) and otherwise rejected back to the previous geometry
  (`structure_rejected`, ending the loop). No new objective term — the
  guard decides acceptance, the solver is untouched.
  `FollowWeights.structure_guard` defaults to False (byte-identical,
  pinned); `--structure-guard` enables it per arm, and every guarded
  round records budget, counts and retries. Glossary gains
  „Topologie-Wächter". Measured verdict in §14 (Arm ⑨): the guard's
  contract holds perfectly on every rung — the first released follower
  to pass the structure gate — but both pre-registered kill criteria
  fire: dtw against the chain is exactly null (6–8 of 10 words
  byte-identical, p = 1.0) because 13 of ~21 rounds exhaust their
  retries. The release's ink gains and its structure inventions are
  NOT separable — moving toward the ink IS the inventing. Route-A
  conclusion: the chain fit already sits at the structure-safe optimum
  of this formulation; the next levers are composer-side (placement,
  joins) and route B. The guard stays in the repo as the first tool
  that keeps a follower run guaranteed structure-clean (#355).

- **The bench report carries the ductus target beside every word**
  (`tools/tracebench/soll.py`, the owner's standing test as a report
  column family): `SollRow`/`ductus_soll` moved out of the duel viewer
  into a shared module, and `tools/tracebench/run.py` attaches per row
  the composition's expected structure (`soll_cross`, `soll_zones`,
  `soll_touch`, `soll_overlap` plus the letters-sum
  `soll_cross_letters`/`soll_zones_letters`) and prints the agreement
  lines `soll_cross_agree`/`soll_zones_agree` (hand == composition per
  word). Report-only — no scored number reads these fields, and a
  fixture root without composition data degrades to a warning. First
  reading on the dev words: crossings agree 7/10, zones 6/10, with the
  disagreements exactly the named composer findings (the t
  under-crossing, the W retrace, the join-formed loops) (#353).

- **The duel viewer and the round chronik (`tools/tracebench/view.py` +
  `chronik.py`) — the methods beside each other AND beside the author's
  own pen, kept per round.** The bench says which tracing is closer; it
  cannot show WHAT differs, and it says nothing at all about the half of
  the question the owner asked on 2026-08-14 — see the methods next to
  one another and next to the hand re-tracing, both as the finished
  trace over the plate and as HOW it is written. `view.py` builds one
  self-contained HTML page in the `tools/fitview` discipline (data:-URI
  crops, inline CSS/JS, no fonts, no CDN, no network, pinned by a test
  that refuses any `http(s)://` in the artifact): per word the crop at
  2×, an SVG overlay in crop-pixel coordinates with one `<g>` per method
  plus one for the hand reference (green — the Werkbank's own
  trace-over-ink colour; chain red, follower blue, everything else from
  a fixed palette), per-method toggles, and the per-word numbers of an
  attached `--json` report (`dtw_xh`, `aiou`, cross matched/spurious,
  retrace ratio) beside each. The writing-order animation follows the
  MVP doctrine of `docs/reference/animation-rendering.md` §1 —
  `stroke-dasharray`/`stroke-dashoffset` on `pathLength=1`, every
  visible method started in sync, each stroke's duration proportional to
  its arc length at a constant pen speed measured in x-heights per
  second, every pen lift a real pause and a real gap, marks (via
  `frames.classify_strokes`) drawn thinner. The geometry is never
  re-derived: both sides travel `BenchFrame.trace_to_bench` →
  `bench_to_crop_px`, exactly as the scorer reads them, and candidates
  arrive through the existing file-provider contract, so a file in
  another frame is refused rather than drawn. No clock is read inside
  the build (`--title` injects the stamp) and label order never comes
  from a set, so identical inputs produce identical bytes — asserted
  across two interpreters with different `PYTHONHASHSEED`.
  `chronik.py snapshot --label … --files …` then files a round's
  artifacts into `<root>/<UTC-stamp>-<label>/` with one `INDEX.md` line,
  under the `tools/dbsnapshot` discipline: create-only (an existing
  round is never opened, renamed or removed, and there is no delete
  path), every source verified to exist and carry bytes BEFORE the
  directory is created, and a root that must lie outside the working
  tree — `--root` / `KS_CHRONIK_ROOT`, else the `tracebench-chronik`
  sibling of the `KURRENTSCHRIFT_ARCHIVE` clone, never a silent
  `temp/` that the next `git clean -xfd` takes away. So the comparisons
  of every optimisation round persist, and the good ones can later seed
  a public method explainer. Measurement and display only: no DB, no
  API, no `core/`, no rendering, and nothing filed inside the
  repository (#344).
- **The ink follower (`tools/pairlab/follow.py`) — route A of the
  Tintenfolger plan, with every shipping weight declared PROVISIONAL.**
  A re-linearising restart on the chain fit, exactly as
  `docs/proposals/tintenfolger.md` §3 formulates it and nothing more:
  solve 1 is the harvest's own `fit_word_chain`, then each round rebuilds
  the problem from `respec_from_solution` and solves it again from zero,
  stopping as soon as a round moves no anchor by more than
  `FOLLOW_ROUND_EPS_UNITS`. What that buys is the three things the chain
  freezes at its INITIAL anchors — the chord parameterisation, the
  landmark correspondence, the overlap seam exemptions — re-frozen at the
  found optimum, where the fit worked hardest; what it CHANGES is the
  meaning of one term: with the chain optimum as the initial geometry the
  Tikhonov term prices displacement from THAT rather than from the chart
  form, i.e. a proximal/trust-region term instead of a form prior. That
  change of meaning is the whole of v1; the change of value is the §14
  arm ① ladder, and until it is measured `FOLLOW_PROX_WEIGHT` stays at
  the chain's own λ — no default here is calibrated, and
  `FollowWeights.provisional` stamps that into every artefact the tool
  writes. The retrace guard is realised as PER-ANCHOR Tikhonov weights
  (the objective already carried `reg_w`): anchors a retrace zone of the
  init path spans keep the full chain λ while everything else is released
  to λ_prox, with the scaling in `reg_w` rather than in `lambda_reg` so
  that λ_prox = 0 stays expressible with the guard standing. Zones are
  detected with `core.geometry.detect_retrace_pairs` at 0.15 xh, the
  trace bench's own rule, mirrored rather than imported — the ruler must
  not be imported into what it grades. `follow_case` mirrors
  `harvest.chain_word_strokes` by USING it: the per-slot grid windows,
  the chainable runs, the welded pen path, the wire caps and the stored
  record shape are the harvest's own (a test asserts the whole word trace
  is byte-identical to the harvest's at `rounds=0`), and the follower
  replaces exactly one thing in that pipeline — the fit each run uses.
  The CLI writes a `tools/tracebench` file-provider candidate
  (`--candidate-out`, the mandatory `"frame": "word_registration"`, a
  word without a pen path excluded AND counted rather than written as an
  empty candidate) and sweeps one weight per run (`--sweep prox=…`).
  Strictly additive: `KS_FOLLOW_*` never moves a `CHAIN_*` (pinned by a
  test), no chain solve changes, the harvest gets no follower path, and
  nothing here touches the DB, the API, `core/` or rendering (#343).
- **The tracebench harness (`tools/tracebench/run.py`) — stage C of the
  Tintenfolger plan, the ruler put to work.** `uv run python -m
  tools.tracebench.run [--candidate chain|authored|traced|file] [--split
  dev|confirm|all]` scores an automatic word tracing against the
  hand-made one and prints the columns
  `docs/reference/qualitaetsmetrik.md` §14 pre-registered — one stable
  line per word, then the block, then (with `--compare`) the paired
  deltas whose sign test is IMPORTED from `tools.pairlab.chainbench`
  rather than restated. `reference.py` turns the frozen
  `word_instances.json` plus each entry's `word.json` into bench frames,
  stored rows and lazily read ink masks, with the `pairmeas` doctrine on
  the losses: a `frame_stale` row and a row without a frozen entry are
  excluded AND counted by reason, never silently dropped. `candidates.py`
  makes a candidate literally a `word_instances` row — validated against
  the wire caps the write endpoint enforces, so a trace the product could
  never store is caught rather than praised — behind four providers:
  `chain` runs the HARVEST's own code path (the trace half of
  `_harvest_case_chain` was lifted into the public
  `harvest.chain_word_strokes` and is asserted byte-identical to what the
  harvest stores; a baseline that is a reimplementation stops being the
  baseline the moment the two drift), `authored` doubles as the identity
  gate, `traced` reads the stored harvest rows, and `file` demands the
  literal `"frame": "word_registration"` so a trace in an unstated frame
  is refused instead of measured as a catastrophic error. Three rules
  the CLI ENFORCES rather than trusts: the startup assertion that all ten
  frozen development words are present as `authored`, non-`frame_stale`
  rows (a ruler that lost a word reports a better number for the rest),
  the refusal of `--split confirm` under five words, and the identity
  gate — `authored` against itself must land on dtw = 0, chamfer = 0 and
  every counter matched, and a FAIL exits non-zero because from there on
  no candidate number means anything. Beside them a report-only
  direction audit of the reference set (per body stroke, endpoint
  concordance against the candidate) — a backwards human trace is a
  fixture-quality signal, not a model error, which a forward-only DTW
  could not otherwise tell apart. Measurement only: no DB, no API, no
  `core/` change, no rendering.

  **The identity gate earned its keep on its first real run**: it FAILED
  on unter/mit/linken because the crossing matcher's refusal margin
  refused two TRUE crossings closer than 0.20 xh even at distance zero —
  a trace against itself. Repaired inside §14's pre-registered
  free-fix window: structure populations (crossings, retrace zones) are
  now matched one-to-one by ascending distance under the radius cap
  (`frames.match_points_one_to_one`); the refusal margin stays with the
  marks, whose single-query frame it was built for. After the fix the
  gate passes exactly (dtw 0, chamfer 0, all counters matched,
  `direction_uncertain` 0 across all ten hand traces).

  **The first baseline is committed to §14 and freezes the ruler**: the
  chain fit against the hand scores `dtw_xh` median 0.062 xh (p90 0.262)
  — but the complaint sits in STRUCTURE, exactly as pre-registered: 19
  invented crossings, 21 invented retrace zones, retrace-arc ratio 1.51
  (the chain re-inks 51 % more than the author), with `unter` (0.439,
  max_absorption 132 — the known collapse case) and `muß` (0.242, two
  lost crossings) carrying the tail. A one-time step sweep
  (0.02/0.03/0.05) pins 0.02: `dtw_xh` moves only +5 % across it, the
  retrace-arc measure is genuinely step-bound. Four reference words are
  flagged `marks_uncertain` (the author drew the i-stroke/u-bow
  connected) — a fixture-quality note for the confirmation set, not a
  candidate error (#341).
- **`tools/inksight` — the isolated InkSight pipeline (Tintenfolger route
  B, T0).** Three stages split at a process boundary so no dependency
  crosses: `prepare.py` (repo env) turns frozen wordbench crops into
  224×224 white-padded model inputs plus a `frames.json` recording the
  affine per word, `run_inksight.py` (isolated Python-3.11 venv, the only
  file importing TensorFlow) asks the released Small-p checkpoint all
  three prompts per crop — `Derender the ink.` · `Recognize and
  derender.` · `Derender the ink: <word>`, the last one fed with the word
  we already know — and decodes its `<ink_token_N>` answer, and
  `to_candidate.py` (repo env) inverts the affine and converts to the
  stored `word_instances` trace frame through the SAME
  `_px_to_word_units` the harvest and the follower use, emitting one
  tracebench candidate file per prompt. Measurement only: the derendered
  geometry never reaches `core/`, the database or rendering, and is never
  a ductus source. Two honesty rules are wired in rather than documented
  away — the XLA flags InkSight's own `utils/tensorflow.py` sets are
  replicated before the first TensorFlow import (without them TF ≥ 2.18
  silently decodes DIFFERENT ink), and the 225-level token grid's
  resolution floor is reported per word (`grid_step_crop_px`, 1.00–1.38
  crop px on the dev set) beside the raw ink-token count that exposes a
  truncated decode. Strokes are emitted exactly as the model produced
  them: the only judgement applied is the wire contract, and a row that
  violates it is stamped `failed` with a reason instead of being cleaned
  up. Weights (Apache 2.0, 518 MB) are downloaded per the README recipe
  and stay untracked, like the venv and every run artefact (#340).
- **The tracebench ruler (`tools/tracebench`) — stage B of the
  Tintenfolger plan.** The measurement modules an automatic word tracing
  is graded with, defined by `docs/proposals/tintenfolger.md` §2 and
  built before any candidate exists, so the criteria cannot be chosen
  after seeing a result. `metric.py` carries the distances and imports
  NOTHING of this project (numpy and scipy only, pinned by parsing its
  own imports — a ruler must not be movable by the engine it grades):
  `dtw` is the `dtw_xh` headline, unconstrained, Euclidean, forward only
  (writing direction is ductus truth) and normalised by the length of
  the OPTIMAL warping path, so the number is a distance in x-heights
  that neither the word's length nor the sampling density moves;
  `aiou` is the paper-faithful Adaptive IoU against the ink MASK (1-px
  rasterisation, never bridging a pen lift, 3×3 dilation to the IoU
  peak), which keeps the width channel out of the geometry number and
  extends the column to specimens nobody traced; `chamfer` reports both
  directions unaveraged, because a missing i-dot inflates exactly one of
  them. `frames.py` builds the comparison frame from the frozen
  `word.json` alone (crop pixels re-expressed in x-heights) and sends
  every path through its OWN registration to get there — two rows whose
  stored labels share no digit land on identical bench points — and adds
  the stroke bookkeeping the distance cannot do: marks split off the
  body (`DIACRITIC_MIN_Y` + arc cap), lifts compared as positions rather
  than as cost, and one shared refusal contract
  (`ref/cand/matched/missing/spurious/ambiguous/pos_err_xh`) over
  `landmarks.nearest_unique_point`. `counters.py` puts that contract on
  the hard places — loop crossings and retrace zones, detected on BOTH
  sides at one common discretisation with the existing detectors at
  their own thresholds — so a lost structure is reported as a structure
  defect instead of dissolving into a small distance. `sets.py` freezes
  the ten hand-traced development words as an append-never constant.
  Measurement only: no DB, no API, no `core/` change, no rendering, and
  no numbers yet — harness, candidate providers and the first baseline
  table arrive with stage C (#339).
- **The frozen word-trace artifact (`word_instances.json`) — tracebench
  stage A.** The wordbench fixture exporter and its API twin freeze the
  stored word traces of each set alongside the measured joins: every
  `word_instances` row travels (the 10 hand-`authored` re-tracings that
  form the Tintenfolger reference set, plus the harvest's `traced` chain
  fits as context), lean-projected to the frame keys
  (`registration_px` + `xh_px` + `fit_path`) so both provenances keep
  the same shape. A machine **frame gate** generalises the #334/#336
  failure class: a row whose registration no longer matches the frozen
  rect/lineature it will be drawn over is stamped `frame_stale` with a
  readable reason — never dropped — and an `--only` refill gates against
  the root's own frozen `word.json` entries (its live debut stamped
  exactly the four rows re-registered by #334/#336 when refilled into
  the pre-#336 roots). `--only` grows `word-instances` and `instances`
  (both artifacts in one pass), shared verbatim between exporter and
  fetcher; the fetcher reads the already-public
  `GET /sources/{id}/word-instances`. The plan the artifact serves —
  reference set, tracebench ruler, the chain-fit-refinement route vs.
  the InkSight route, pre-registered criteria — lives in the new
  `docs/proposals/tintenfolger.md` (indexed in `docs/index.md`);
  `docs/research/bildsynthese-und-stiftbahn.md` gains the 2026-08-14
  addendum (reference set begun; the Small-p fine-tune assumption
  corrected: no training code exists or is coming, so route B re-scopes
  to a small own model on engine pairs) (#337).

- **`docs/research/` — a home for the idea-feeding literature.** New docs
  layer for external research notes that never follow the code, so the
  folder taxonomy answers "is this a plan, a protocol or a paper summary?"
  at a glance: `kurrent-writer-and-recognizer.md` moves there from
  `proposals/` (which is now purely implementation proposals and their
  protocols), joined by the new `graves-handschrift-synthese.md` — a
  54-source literature report on handwriting synthesis (Graves-2013
  mechanics, priming/biasing, the physical plotter pipeline, the
  GAN/Transformer/tokenisation successors), editorially cleaned from its
  deep-research export (25 base64 formula images replaced by text
  notation, flattened footnote digits turned into readable source
  references). The index, the write-docs skill, `sprachregelung.md` §1
  and the copilot docs tree all carry the new layer; two glossary §6
  entries (MDN, Priming/Biasing) anchor the terms the report brings in (#329).

### Changed

- **Structure counters v2 — a dated re-baseline of the trace bench's
  crossing and retrace counts** (`tools/tracebench/counters.py`,
  pre-registered in `qualitaetsmetrik.md` §14 `aug16` from the owner's
  manual audit of the dev words, every constant measured on the named
  examples). A crossing now exists only where one line PIERCES the
  other — clearly in on one side and out on the other, both ways
  (`_pierces`, window 0.25 xh, margin 0.05 xh ≈ half a stroke width) —
  which retires the 15-degree angle threshold: a retrace release is no
  crossing however sharp, a piercing loop closure is one however
  shallow. A retrace requires its partner ARC-NEAR (gap ≤ 1.0 xh) and a
  real pass (≥ 0.30 xh): anti-parallel proximity with a long way in
  between is a **touch** (writing past each other), a partner in
  another pen stroke an **overlap**, a diverging cusp nothing — touch
  and overlap are counted and reported (`touch_ref/cand`,
  `overlap_ref/cand`), never part of a loss. The owner's verdicts are
  pinned as tests, the identity gate still passes exactly, and
  dtw/aiou/chamfer/marks are untouched (the v2 baseline's dtw is
  byte-identical to v1). New v2 chain baseline: invented crossings
  19 → 13 (6 were tangential artifacts), invented retrace zones
  21 → 5 — the rest reclassifies into 9 invented touches (letters
  composed too close) and 6 overlaps; hand counts move onto the ductus
  budgets (Wer 5 → 3, muß 3 → 1). The duel page draws the three zone
  classes distinctly (solid/dashed/dotted); glossary gains
  „Durchstoß-Kriterium" and „Berührung (Struktur-Zähler)". v1 numbers
  of the aug14 baseline and arms 1/5/6/6b stay archived and are not
  comparable to v2. **v2.1 amendment** (the owner's second audit pass):
  a ring whose two chords are each other's anti-parallel partners is
  the incidental self-crossing of one out-and-back-with-release —
  retrace-internal, suppressed (`CROSS_PARTNER_NEAR_UNITS`); exactly
  the disputed rings fall (unter-t, mit-t, zwei-w, linken-k-exit)
  while a retrace through FOREIGN ink keeps its rings. Crossing SITES
  are counted, not events. The duel page's numbers table gains
  Berührungen/Überlagerungen columns for every layer and both Soll
  rows. v2.1 chain baseline: invented rings 4, invented zones 5,
  invented touches 9, overlaps 6 — most of the stack-word „inventions"
  were the chain's own overlapping strokes crossing incidentally (#351).

- **Follower arms 5 and 6 recorded in the quality-metric §14** (doc-only):
  the overlap term is acquitted of the §13 brake hypothesis (switching it
  off is mildly better, the structure veto vs the baseline remains), and
  the landmark arm — after the geodesic-walk repair made extrapolation
  fire on real ink — measures null at the middle rung and pointwise
  significantly worse at full parity. The finding that outranks both
  arms: 12 of 21 landmark correspondences point at ink with no crossing
  (touch points, T-junctions) — the correspondence cap; the next
  pre-registered hypothesis is class-aware correspondence, not more
  weight. No default adopted (#347).

- **Follower arm 1 result recorded in the quality-metric §14** (doc-only):
  the pre-registered lambda ladder ran paired against the frozen `aug14`
  baseline — every rung fails the co-primary structure gate, so the
  naked form-release formulation is rejected by its own veto while the
  ink pull itself is validated (AIoU +0.10 on every rung). One named
  protocol deviation (decade ladder with realized ratios instead of the
  ill-defined percent-of-e_geo dialing at a restart) is recorded in the
  entry. No default adopted; `FOLLOW_*` stays provisional; next
  pre-registered steps are the structural data-term arms (#345).

- **The word-trace assembly moved to `tools/pairlab/trace.py`, and the chain fit
  gained three additive handles for a re-linearising restart — all four changes
  proven inert.** `assemble_word_strokes` and its helpers left
  `tools/laufform/harvest.py` bodily unchanged (a pure move, asserted
  line-for-line) because the coming ink-follower
  (`tools/pairlab/follow.py`, `docs/proposals/tintenfolger.md` §3) needs the same
  assembler and `tools.pairlab` importing `tools.laufform` would be an import
  cycle — the harvest already imports `pairlab.chain`, `pairlab.anchors` and
  `pairlab.connector_qc`; the same one-shared-module resolution
  `tools/pairlab/anchors.py` took, with the harvest re-exporting every name so
  no caller or test changes. In `chain.py`: `respec_from_solution` rebuilds the
  segment specs with the SOLVED anchors as their initial ones (everything else
  verbatim), so a second `build_chain_problem` freezes the chord
  parameterisation, the landmark correspondence and the overlap exemptions at
  the first solve's optimum instead of at the composed start — measured on the
  synthetic ink pair, that staleness is ~0.06 xh of sample displacement after
  0.2 xh of injected placement error; `_ChainProblem.skel` carries the
  band-restricted skeleton the fields were built from, for consumers only and
  never read by the objective (pinned by a test that nulls it and re-evaluates);
  and `build_chain_problem` takes `max_anchor_delta` / `connector_max_delta`,
  which at their default None are exactly today's module constants. The slot
  BLOCK bounds stay unparameterised on purpose — they are an asymmetric x/y pair
  rather than one cap, and a restart's placement budget is its own decision. A
  chain solve is bit-identical to the pre-change module on both the toy and the
  rasterised-ink problem, so nothing here re-baselines the harvest (#338).

- **Declared wordbench re-baseline `aug14`** (full fixture re-export, the
  first since `jul31`): the frozen reference crops now carry the
  #334/#336 rect corrections (detached i-marks that lay fully outside
  their rects), and the roots catch up to the `aug07` write round.
  Headline against the documented `aug07` state: words 0.110392 →
  **0.110703**, pairs 0.165678 → **0.165688** — composition untouched;
  the movement sits in the corrected references (`haben`/`ein`/`einen`/
  `zwei` improve, `regieren` honestly worsens because its i-stroke is
  finally part of the reference the composition must cover). Documented
  as a dated section in `docs/reference/qualitaetsmetrik.md` §6 (#337).

- **Research note on the image-first parallel track: offline handwriting
  generation for Kurrent and the way back to a pen path.** New
  `docs/research/bildsynthese-und-stiftbahn.md` surveys the current
  offline-HTG landscape (GAN · transformer · diffusion families, with
  DiffusionPen/One-DM as fine-tuning favourites and Emuru's
  synthetic-font pretraining recipe adapted to the project's own engine
  as the data-scarcity answer), the licensing-triaged training-data
  situation for Kurrent word images (CC-BY line datasets, the
  Sütterlin-era gap, papers linked rather than committed), the
  offline-to-online trajectory-recovery state of the art (InkSight,
  TRACE, the geometric route — and the repo's own chain fit as the
  prior-guided competitor, with the traced `word_instances` as the only
  existing online Kurrent ground truth and hence the evaluation bench),
  and a cheap-to-expensive test ladder T0–T4 ending in a plotted
  postcard A/B against the current engine. Indexed in `docs/index.md`;
  the external umbrella term HTG gets its glossary entry in §6 (#330).
- **A zoom slider in the word trace editor, so a word can be re-traced at
  natural writing size on a tablet.** The W3 editor
  (`WordTraceEditorDialog`) gains a 1–8× size slider: the crop scales
  inside a scrollable container, fingers pan the zoomed view
  (`touch-action: pan-x pan-y`) while pen and mouse draw — touch
  pointers are ignored by the stroke handlers, which doubles as palm
  rejection — and the drawn trace keeps a constant on-screen thickness
  (stroke width divided by zoom), so zooming in reveals the ink instead
  of a fatter overlay. Groundwork for hand-tracing the `authored`
  reference set the research note's ink-follower benchmark needs (#330).
- **The word trace editor rebuilt around actually writing on a tablet.**
  First real S-Pen session feedback: the dialog is now fullscreen, every
  control (save/close, size slider, undo/clear/reset, stored-trace
  toggle, stroke count) moved into the header ABOVE the drawing surface
  — while writing, the hand rests exactly where footer controls used to
  sit and a graze there interrupted the stroke — the canvas owns the
  whole remaining viewport, the long intro text moved behind an
  `InfoHint`, and the size slider now also SHRINKS (0.25–8× in 0.25
  steps, shrunk words centred), because on a tablet the crop at dialog
  width can be larger than natural writing size (#331).
- **Trace editor: shrink floor lowered to 0.1× and the drawn line made a
  true 2-CSS-pixel hairline.** Fullscreen made the 1× baseline much
  larger than the old dialog width, so natural writing size on a tablet
  can sit below the former 0.25× floor (now 0.1–2× in 0.05 steps —
  capped at 2× because tablet use showed higher zoom unused while
  packing so many steps into the slider that it was hard to set
  precisely) — and
  the zoom-compensated stroke width, constant relative to the container,
  drew a line far fatter than the shrunk ink it traced; both overlay
  paths now use `vector-effect: non-scaling-stroke` with fixed pixel
  widths, so the trace stays a hairline at every zoom. The canvas also
  drops `touch-action: pan-x pan-y` for `none` with hand-rolled finger
  panning: Chromium treats the pen as a pannable pointer, so the browser
  recognised a short pen stroke as a scroll gesture, fired
  `pointercancel` and broke the drawn line off mid-stroke (#332).
- **Word-sample crops actually reach the browser after a sidecar fix.**
  The #334 rect corrections never arrived on the tablet: the sample
  metadata URL carried a hard-coded `?v=2` and the crop PNGs no version
  at all, so the edge cache kept serving the old data for days. Both
  URLs now share a bumped `WORD_SAMPLES_V` (v=3) and accept the
  admin-wide reload stamp (`t=`), the words overview re-fetches the
  metadata on „Neu laden", and stale-metadata/fresh-crop mismatches
  (which squashed the taller crops) are gone. Alongside, a second
  sidecar audit for DETACHED marks fully outside their rect — invisible
  to the #334 edge audit — widened three more rects (the i-Striche of
  `zwei` and `regieren`, the i-dot of the Abb.-22 `in`); the two stored
  rows were re-registered through the admin PUT in the same action, the
  hand-authored `zwei` trace with its strokes untouched (#336).
- **Trace editor: text selection and the context menu are suppressed.**
  An S-Pen long-press mid-stroke selected the hint text (native
  selection handles + copy toolbar) or opened the browser context menu.
  The fullscreen dialog's paper now carries `user-select: none` and
  swallows `contextmenu`; buttons and slider are unaffected, the
  `InfoHint` popover renders in a portal and stays selectable. A shrunk
  word is additionally centred in BOTH axes of the canvas area, so the
  writing zone sits mid-screen instead of directly under the header
  controls the pen hand kept grazing (#335).
- **Trace editor: panning is an explicit mode, fingers are fully inert
  while writing.** Even hand-rolled finger panning fought the writing
  hand — resting fingers and palm shoved the view around mid-stroke. A
  Schreiben/Verschieben toggle (the wizard's Zeichnen/Anpassen pattern)
  replaces the gesture: in draw mode touch input does nothing at all,
  in pan mode any pointer — pen, mouse or finger — drags the view (#333).
- **The words overview shows which specimens are already hand-traced.**
  Every card whose stored trace is provenance `authored` carries a
  filled "von Hand" chip and the toolbar counts the tab's progress
  ("0/63 von Hand nachgefahren") — the glanceable state for working
  through the manual reference set, fed from the shared workbench rows
  at no extra request (#331).

- **The crossing landmark as a DATA term in the chain fit — inert by default,
  with its energy scale calibrated before any weight is proposed.** New pure
  module `tools/pairlab/landmarks.py` finds a ductus polyline's proper
  self-intersections (chord pair plus both chord parameters, half-open so a
  crossing on an anchor is counted once, never bridging a pen lift) and
  classifies the well-conditioned ones as landmarks (≥ 15°, ≥ 0.35 xh arc
  separation, co-located duplicates merged — this reproduces
  `qualitaetsmetrik.md` §13a's census exactly: 43 landmarks over 26 of the 34
  frozen v0 rows). Beside it the ink side: skeleton branch points (≥ 3
  8-neighbours, adjacent ones collapsed to their centroid) and an explicit
  refusal to assign an ambiguous one. `tools/pairlab/chain.py` gains the
  correspondence term over those pairs — linearised the way every other
  operator of `_ChainProblem` is (chord pair and parameters frozen at the
  initial anchors, so the fitted crossing is the average of the two branch
  points and hence LINEAR in four plan anchors, with an exact gradient),
  weight `CHAIN_LANDMARK_WEIGHT` / `KS_CHAIN_LANDMARK_WEIGHT` **default 0.0**
  and byte-identical there (value and gradient bit-for-bit the term's absence,
  pinned by a test), `landmark` added to `GRADIENT_TERMS` so
  `gradient_decomposition`'s sum check covers it. Why this is not a fifth
  attempt after §7/§8/§10/§11d: those four priced a PROXY (curvature,
  distance, stiffness) on an assignment-blind objective, and this states a
  correspondence — *this point belongs on that point*. `tools/pairlab/landmarklab.py`
  is the probe: `--calibrate` reads `e_geo / e_landmark` at BASELINE optima
  only (§11c's lesson — a ladder chosen by analogy put the bind term at 0.2 %
  of this objective's energy scale and produced an empty experiment), then the
  effect run reports the fitted crossing height per occurrence against the ink
  target, pooled by joined vs. word-final, with its costs and with the
  structure-or-slide column that says whether a weight moved the structure or
  just translated the letter. Measurement only: no DB, no API, no `core/`, no
  rendering, and no default weight is proposed from a 14-occurrence
  single-glyph development set (#328).

- **Docs drift pass, with the layer taxonomy sharpened to match
  reality.** The index's layer shorthand no longer claims every
  `reference/` doc is lebend-or-bindend (HTR/animation/style-analysis
  carry the status of their planned build-out), `concepts/` is described
  as the design core it actually is, the proposals index is grouped by
  status word so plan and protocol separate at a glance, and
  `optimierungs-werkbank.md` is re-labelled `bindend` — its §3–§5
  doctrine is API-enforced and read before every basket run; „umgesetzt"
  was not in the closed status vocabulary. Stale claims fixed in the same
  pass: the last `position`-keyed tuples in `architektur.md` §3/§12 and
  `styleanalyse.md` (the schema key is `(glyph_key, variant)` since
  R2/migration `0021`), architektur §16's pre-redesign admin routes, the
  metric doc's stale `aug02` headline (actual: words 0,110392 · pairs
  0,165678, re-baseline `aug07`), style-guide §9's drifted token copy
  (now a pointer to design-system §2), `werkzeuge.md` missing
  `dbsnapshot`, `fitview` and the pairlab entry scripts,
  `datenablage.md` not knowing the committed `data/humanbench/` tree,
  `naming-und-setup.md` §3 missing `/data` + `/tools`, the
  `mvp-roadmap.md` head now declaring the retired `/mvp/` folder
  historical wholesale, and the audit-licenses skill's dead base64
  exclude (its target was deleted in #209) with the stale
  woff2-duplicate baseline note (#329).

### Fixed

- **The duel page's resting trace no longer loses its tail**
  (`tools/tracebench/view.py`, owner report: the hand trace of „unter"
  ended at the t on the page while the admin editor showed it complete —
  the trace DATA was complete, x 9..269 of a 274 px crop). Cause: the
  static `stroke-dasharray="1"` + `pathLength="1"` +
  `vector-effect="non-scaling-stroke"` combination mis-scales the dash in
  some engines and swallows the end of the longest paths. The resting
  markup now carries no dash at all; the dash is applied by the JS only
  while the writing animation runs and removed again in the final state (#350).

## [0.24.0] — 2026-08-11 — Class rules, floors, human judgement pass, stranded-anchor repair

### Added

- **The hold-out round is judged, and it retires the metric it was meant to
  confirm.** 95 occurrences the judge had never seen plus 10 blind repeats,
  all 105 rated with the corrected sheet against unchanged fits. `d_end` — the
  distance from a letter's chain end to the nearest ink — passed the criterion
  that was fixed before the number existed (AUC 0.764, exact one-sided
  p = 0.012) and is dropped anyway, on two checks nobody had pre-registered:
  it does not separate `E` from the other defect classes (0.539, chance), so
  it was never seam-specific and the name was the claim; and the plain `peak`
  we already compute beats it (0.888 for „any defect" against „good"). The
  development figure also picked the judged end from the human's click, which
  no acceptance criterion can use — the confirmed variant takes the worse of
  the two ends under one rule for every screen. `B` („a whole stretch beside
  the ink") turns out to be a `d` problem rather than a fit problem: a rigid
  shift removes 0 % of its residual, and 5 of the 7 `d` occurrences carry it
  while every other frequent glyph sits at 0–2. The prevalence shift
  (`E` 23.3 % → 7.4 %) is recorded as *consistent with* the instrument fix and
  explicitly not as proof — the judge knew the prediction and a drawing cannot
  be blinded — while the opposite artifact is measured and left open: the
  faint pen path may mask real seam defects (good-screen `d_end` p90
  0.047 → 0.067, p = 0.08). Findings in `qualitaetsmetrik.md` §10, judgements
  and slim key under `data/humanbench/runde-02-*`, `d_end` in the glossary as
  a rejected metric (#320).

- **The location question §9 left open is settled — against the hypothesis,
  and that closes the last repair path for the outlier class.** §9 withdrew
  „22 of 23 gate rejections sit at corner anchors" as circular (it came from
  the maximum of our own detector) and required a non-circular analysis before
  anything is built there. The 35 human markers of the hold-out round, scored
  against the landmarks the template itself carries, look like a hit: 42.9 %
  in a landmark neighbourhood against 23.0 % by chance, p = 0.007. The control
  removes it entirely — drop the chain ENDS from the landmark set, where `E`
  („kink only at the edge") sits by definition, and 12.9 % remain against
  18.4 % expected, p = 0.85. The only location structure in the markers is a
  tautology; nothing concentrates at corner anchors or internal pen lifts. The
  strong form of the §8 conjecture is therefore no longer merely unsupported
  but measured away at any size that would have justified an intervention, so
  the bending term, the hinge and now the corner-anchor sample support are all
  out, and the harvest gate stays a fallback that discards rather than repairs.
  A fourth attempt needs a new diagnosis, not a new objective term. `W`
  („wobble") is a different matter and remains untried: both rejected terms
  aimed at the single jump, not at the unsteady line (#320).

- **`tools/dbsnapshot` — an archive of the hand-made data, and a restore drill
  that proves it works.** Two tables in the database cannot be recomputed from
  anything: `bboxes` (the crop, eraser, ink and donor work) and
  `templates.raw_path` (the stylus-drawn ductus). Everything else falls back
  out of those plus the committed chart bytes. Cloud SQL's own backups are
  instance-wide, keep seven days and cannot be read without restoring an
  instance; this project's failure mode is slower — a bad apply or re-harvest
  noticed weeks later — so `fetch.py` files a readable, diffable snapshot into
  a private repository outside the GCP project. Append-only by construction: a
  new timestamped directory per run, no overwrite, no delete path at all, and a
  run that would file fewer rows than the previous one fails instead, because
  an archive that quietly shrinks looks exactly like a full one in a directory
  listing. Every call is a GET, through the existing GET-only client, so the
  tool cannot mutate the deployed system even by accident. `restore.py` is the
  half that makes the archive more than a guess — an archive nobody has ever
  restored is a hope — and it is built for drills: the target URL is required
  and never read from the environment, a URL equal to `DATABASE_URL` is
  refused, an occupied target needs `--replace` and nothing is written without
  `--apply`. Templates are archived per STYLE rather than per source, since the
  unique key is `(style_id, glyph_key, variant)` and reading them per source
  duplicates every row of a two-source style. The manifest states the gaps it
  knows rather than hiding them (#317).
- **`tools/humanbench` — the blind judgement pass over the fits, as a package
  rather than a scratchpad script.** The automated benches score what a metric
  can already see; this one produces the other half — the author works through
  a sample of stored fits by eye, so a metric can be checked against human
  judgement instead of against itself. `build.py` draws a round and writes its
  payload, key, held-out reserve and provenance stamp: the sample is stratified
  by severity WITH a seeded shuffle inside the bands (without it a prefix is
  not a sample), carries blind repeats as the reliability bound, pads crops
  proportionally and draws pen lifts as lifts — each safeguard sitting next to
  the failure it was added for, because a safeguard without its failure is the
  first thing a later edit removes as noise. `page.py` renders one
  self-contained HTML page from that payload — crops as `data:` URIs, style and
  script inline, no font, no CDN, no network — and the mode follows the payload
  rather than a flag: one panel per screen is the category pass, two are the
  paired before/after comparison, whose side assignment exists only in the key,
  so the fix's own author cannot read the answer off the page. Nothing in the
  package writes anywhere: `page.py` and `analyse.py` see neither DB nor API,
  and `build.py` reads occurrences from files or, absent those, GET-only over
  the deployed read API. The method — taxonomy, construction rules, the
  pre-registered analysis plan — is `docs/reference/menschliche-bewertung.md`
  (indexed in `docs/index.md` and `reference/werkzeuge.md`); the findings of a
  round belong to `qualitaetsmetrik.md`. Payload and key are occurrence
  geometry and stay under `temp/humanbench/runde-<n>/`
  (`quellen-und-rechte.md` §5); what is committed is the human half alone,
  under `data/humanbench/` — the round's judgement text plus its provenance
  stamp and a `SOURCE.md`, with the `.gitignore` boundary drawn as an allowlist
  (`*.md` and `*-urteile.txt`) so a later round's payload cannot follow them in (#317).
- **`tools/humanbench/analyse.py` — the labelling pass's evaluation, in the
  order the plan fixed before the labels existed.** `page.py` collects the
  judgement and `build.py` decides what is judged; the third piece parses the
  emitted result text (`<uid>:<codes>[#x,y][@Ns][ "note"]`, category codes read
  straight from `page.CATEGORIES` so parser and instrument cannot drift) and
  runs the six pre-registered steps: test-retest reliability from the blind
  repeats, occupancy, gate validation, the coverage matrix (AUC ± Hanley-McNeil
  SE per category × metric), the place check over the clicked markers and
  drift over the sequence. The point is the ORDER: an evaluation written after
  seeing the labels can always be reordered until it says something, so it is
  code rather than a scratchpad script, and the second round re-runs the same
  analysis instead of a new one. Three rules from the plan are enforced rather
  than trusted — an unset marker is dropped instead of counted as „nothing
  wrong there", a screen carrying two findings drops out of the per-category
  place check because its one point cannot be attributed, and „komplett
  daneben" is excluded from every other category's numbers. A category below
  `MIN_POSITIVES = 8` gets the words „too few" instead of a number, and a
  per-category test-retest agreement built on fewer than three positive pairs
  is flagged as agreement about the negatives — which is exactly what the first
  round's 12/12 for `A` and `B` were. Reproduces the published round-2 numbers
  exactly (79 of 150 flagged, gate precision 11/11 against „any finding" and
  8/11 against the `A` labels, `spike` AUC 0.86 ± 0.06 for `A`, `cov` 0.84 ±
  0.05 for `W`, 20 of 20 single-labelled `E` markers at a stroke boundary). No
  DB, no API: the per-occurrence metrics arrive as a file the caller supplies,
  which is what keeps the learned geometry out of the repo
  (`quellen-und-rechte.md` §5) (#317).
- **`docs/reference/menschliche-bewertung.md` — the method behind the blind
  judgement pass, so a repetition is a rebuild rather than a replanning.** The
  project's numbers measure geometry; the pass measures which kind of defect
  any of them can see at all, and it deliberately yields no thresholds and no
  training set. The doc carries the six-category defect taxonomy with an
  operative definition, a recognition cue and a demarcation against its
  neighbour for each — three rounds of sharpening, and the most durable result
  of the exercise — plus every construction rule of the instrument next to the
  failure it was added for: the stratified sample WITH the shuffle inside the
  bands (without it a prefix is not a sample and the cleanest cases, where the
  false positives live, are unreachable), the blind repeats as the reliability
  bound (without them a low AUC cannot be told from label noise and „our metric
  is blind to this" is unfalsifiable), the held-out reserve, the proportional
  crop pad, the cartographic casing, pen lifts drawn as lifts, and one marker
  per screen with the rule that a missing marker is not a datum. Then the
  pre-registration (why the analysis plan is written before the labels, what it
  must fix, and that later additions are marked as such), a round as a
  step-by-step command sequence, what is kept and what is not and why (the
  judgements are committed — the author's own statement, unreproducible; key
  and per-occurrence metrics are not, and are rebuildable from seed and
  snapshot like the bench fixtures), the provenance stamp and why it is
  mandatory, why a second category pass cannot prove an improvement, and the
  known limits. Indexed in `docs/index.md` (quick links, tree, Reference
  section and the living-document table); the findings themselves belong to
  `qualitaetsmetrik.md` (#317).
- **`qualitaetsmetrik.md` §9 — the first round's findings: which defect any of
  our numbers actually sees.** 162 screens, 150 occurrences plus 12 blind
  repeats, judged against an analysis plan written before the labels existed.
  Roughly half the stored fits are clean. The largest defect class is not the
  one the shipped gate was built for: 23 % is a truncated stroke END —
  overwhelmingly a stroke start, the entry stroke the fit never reaches — and
  no metric sees it, because `cov_rmse_local` measures coverage in a window
  derived from the fit itself, so a fit that starts too late defines its own
  error away (AUC 0.54 against that class, and 0.26 among the flawed
  occurrences, where those cases look BETTER than the rest). The shipped
  `anchor_spike_ratio ≥ 8.0` gate rejected 11 occurrences and not one of them
  had been called good. The pre-registered prediction that „wobble" would be
  invisible to every metric is falsified — `cov_rmse` reaches 0.84 for it, and
  survives every artefact check — which narrows the standing claim „our metrics
  do not see what bothers a reader" to the outlier class alone. Two earlier
  statements are withdrawn: „22 of 23 gate rejections sit at corner anchors"
  was circular (it came from the detector's own maximum), and the human markers
  refute it no better than they support it at n = 6. Also settles the
  aggregation question the occurrence floor left open: local defect and
  globally failed fit are two populations, not one scale (1.7 % of anchors
  flagged for a good occurrence against 58–68 % for an unusable one, with a
  clean gap), which is what justifies treating them with different instruments (#317).

- **What a second judgement round would otherwise have had to rediscover.** A
  completeness pass over the retired scratchpad scripts, asking not „is this
  good" but „what is missing before a repetition is genuinely cheaper than the
  first time". Four gaps closed in the instrument itself: `build.py` now writes
  the **slim key** (`vorkommen.json`) that gets archived beside the judgements,
  so the archive is a copy of the key that was judged against rather than a
  second artefact hand-cut months later — and it carries the `slot`, without
  which two occurrences of one letter in one word cannot be told apart (round 1
  had three such words, and its hand-cut key dropped the field). `--only`
  restricts a round to the occurrences a reserve or key file names, applied
  BEFORE the severity ranking, which is what the pre-registered rule „develop on
  the labelled set, confirm on the reserve" needs in order to be runnable at
  all. The builder now warns, by name, about glyphs whose pen lifts it could not
  resolve: that read is admin-gated, so an unauthenticated round silently draws
  every multi-stroke letter bridged and manufactures its own findings. And the
  stamp records the two repeat rules that are constants rather than flags
  (`repeat_min_glyph_count`, `repeat_jitter`), the glyph and specimen coverage
  the first round's stamp had to count by hand, the instance rows that were not
  eligible BROKEN DOWN BY REASON (a filter nobody counted looks exactly like no
  filter, and only the tally tells „the harvest changed" from „the filter did")
  and `code_dirty` — a commit only says which code built a round if the tree
  was clean. `analyse.py` gains
  `--union W,B`, the one pre-registered analysis step that had no
  implementation: two categories the round shows to be inseparable are scored as
  one column, so confusability costs resolution instead of destroying the
  statement. Asked for, never default. Documented alongside: the contract of the
  `--rows`/`--spots` files (what each default metric column meant in round 1) —
  with the honest note that NOTHING in the repo produces them yet, so the
  coverage matrix, the gate validation and the place check of a category round
  still need that fourth module written; that the category-stratified repeats
  the method doc calls for are watched by the analyser but not yet buildable;
  and that the per-judgement seconds changed meaning after round 1 and are not
  comparable across rounds. First tests for `build.py`'s sampling half
  (`tests/test_humanbench_build.py`), two of which grade a safeguard against the
  failure it was added for rather than against a snapshot (#317).

- **The pair focus shows its drill plate like a word: green trace, red engine
  ink, one registration.** Every Abb.-20 drill is auto-traced into
  `word_instances` since the harvest, but the Übergänge view only offered the
  plain crop tile — the traced line and the system's answer met the specimen
  only two clicks away, in the Wörter detail. `/admin/uebergaenge?l=&r=` now
  carries a full-width „Platten-Beleg (nachgefahren)" panel wherever a traced
  drill of exactly that pair exists (matched by shaping the sample's word, the
  same rule the pair cards use): the same `WordSpineCard` the Wörter view
  draws — the green Nachfahrung and the translucent engine ink both on the
  row's measured registration, the engine's own face beside at the same scale
  — with both layers ON by default and the Wörter detail's layer toggles
  (`LayerDot` extracted to `shell/` for both views), a „Bewerten" score
  action, and a jump into the word detail. An override save resets the card
  through the existing `pairTick` (fresh composition via the render cache's
  `bust`, stale score dropped); a pair without a drill plate shows no panel (#307).

- **The Übergänge view shows the measured joins as ink, not as chips.** The
  occurrence panel of `/admin/uebergaenge` listed every dissected join by
  specimen id and `gen_chamfer` — it said where a join was measured and never
  what it looks like, which is the one thing a join is judged on. A
  `pair_instance` carries no pixel box (its geometry lives in the glyph_pairs
  frame, relative to the left glyph's exit), but it names the specimen and the
  left glyph's slot, and the letter occurrences of the same plate carry those
  slots as page-pixel boxes: the new pure `model.ts::joinCropBoxOf` unions the
  two into the join's own crop box, and the tile from the Buchstaben view
  (extracted as the generic `CropThumb`) draws it. Slot and glyph key must
  both match — where the two harvests disagree about a word's slotting, the
  chip row stays rather than showing the wrong ink (#306).

### Changed

- **The stranded anchor is now REPAIRED at harvest — the accepted alternative
  to the four rejected objective terms.** `tools/pairlab/anchors.py` holds the
  shared detector (both neighbouring steps ≥ 3× the median step of the own
  pen-stroke — the shape of the author-marked defect, 16/17 hit rate) and the
  repair: a flagged anchor is replaced by the linear interpolation of its
  nearest unflagged stroke neighbours, never snapping to ink (§8 showed why: at
  a crossing the nearest ink is the wrong stroke) and never crossing a pen
  lift. Both harvest storage paths apply it AFTER the gate, only to ACCEPTED
  occurrences: the gate keeps judging the unrepaired geometry (a repair is a
  near-rejection, never a pass), the stored `anchor_spike_ratio` stays the
  unrepaired number, and `measurements.repaired_anchors` lists what was
  touched — absence means untouched, pinned byte-identical by the golden
  test. The word trace deliberately stays unrepaired (the inspection layer
  shows what the fit actually did). The owner's explicit trade (2026-08-10)
  is recorded at the module: an interpolated anchor slightly off the ink is
  the lesser defect; the peak that poisons the per-anchor Laufform median is
  the one that must go. This removes exactly the judged defects — every
  author-marked peak sat in an accepted fit, so no yield or threshold moves (#327).

- **`tools/fitview` — the before/after page for the judged occurrences.**
  Re-runs the live chain fit on precisely the humanbench screens the owner
  marked (default: category `A`, both rounds, blind repeats merged), and
  renders each occurrence in the SAME frame the judgement used (window pad and
  4× zoom replicated from `humanbench/build.py`): left the unrepaired anchor
  polyline, right the repaired one, repaired indices circled, the owner's
  clicked marker as a cross. One self-contained HTML file, minutes per round
  instead of hours — the small-subset human loop the owner asked for (#327).

- **`tools/pairlab/peaklab.py` — the same loop over a NAMED working set.** The
  sibling of `tools/fitview`: instead of the judged screens it fits a small
  named set of words (default the five whose outliers the author marked plus
  three he passed as clean, so a round can tell „the peaks are gone" from
  „everything got flattened"), reports the lone excursions per letter
  occurrence with the spike ratio before and after, and with `--png` draws the
  fitted anchor chain over the specimen ink with every excursion circled —
  `--compare` puts the fitted and the repaired chain side by side in one
  window, so a shift is never a zoom. Four minutes per round instead of three
  hours; detector and repair are the shared ones from `tools/pairlab/anchors.py`,
  so what it shows is what the harvest does. Measurement only: no DB, no API,
  nothing renders (#327).

- **Per-term, per-anchor gradient decomposition of the chain fit — the
  diagnosis that has to come before the term.** An optimum is a point where
  the forces cancel, so „what holds the stranded anchor out there" is a
  measurement, not a guess, and until it is made a new term is a hopeful
  edit. `_ChainProblem.gradient_terms` splits the objective into its seven
  weighted forces (`geo` · `crop` · `width` · `coverage` · `overlap` ·
  `smooth` · `reg`) and reads each one per free anchor. `crop` is split off
  `e_geo` because the out-of-crop pull is a different statement about a
  sample than the distance field is.
  The build rule of the method is wired in as an assertion rather than
  trusted: every term is folded through the SAME chain rule and the SAME
  parameter packing the objective uses (`_fold_samples`/`_fold_plan`/`_pack`,
  now one code path instead of two), and `gradient_decomposition` re-adds the
  split and raises unless it reproduces the gradient L-BFGS-B actually
  followed. Measured on a real solve, the split misses it by 2.7e-14
  relative. A decomposition that does not reproduce the gradient describes a
  different objective, which is precisely the failure mode that would make
  the diagnostic drift away from the thing it diagnoses.
  `sample_slice_of_anchor` supplies the reading the earlier measurement got
  wrong: the field at the SAMPLES between an anchor's two neighbours. The
  objective never queries an anchor's own position, so a restoring force
  measured there quantifies something the optimiser cannot feel.
  `fit_word_chain(keep_solve=True)` hands back the solved problem and its
  argmin — off by default, because the problem holds the whole field stack (#322).

- **`tools/pairlab/gradlab.py` — the sweep that runs it over the harvest's own
  solves.** Same cases, same grid windows, same chain fits as
  `tools.laufform.harvest`, so the optimum it inspects is the optimum the
  stored occurrences came from. Per anchor it reports every term's force, the
  field at that anchor's sample window, and its displacement against its
  neighbours; the stranding detector is the shape the author's markings
  actually have (both neighbouring steps at least 3x the median step of their
  own pen-stroke, never across a lift). Every other letter anchor of the same
  solves is carried as a CONTROL population — a term that pulls as hard at a
  healthy anchor as at a stranded one explains nothing, and without that
  column the numbers would invite exactly that conclusion. Measurement only:
  no DB, no API, no rendering, nothing in `core/` (#322).

- **The neighbour-binding term: measured and REJECTED (`qualitaetsmetrik.md`
  §11b–§11d).** The pre-registered A/B, its criteria committed before any of
  its numbers existed. Run 1 failed on a ladder that turned out never to have
  switched the term on — at its top rung the weighted binding contributed
  4.9e-6 against a geometry term of 2.2e-3, 450× smaller, because the ladder
  was taken by analogy to `core.fit`'s constant and the operator being the same
  does not make the objective's energy scale the same. Named as the
  pre-registration's flaw rather than quietly patched, and re-registered with a
  ladder calibrated on baseline-only solves.
  Run 2, calibrated: **the term works and is still wrong.** Stranded anchors
  98 → 41, spike ratio 2.90 → 1.59 — and the share of stored anchors sitting
  off the ink RISES 18 %, where a 25 % fall was required. Smoothing the second
  difference of the displacements stops one anchor from making its excursion
  alone, so it takes its neighbours along: one anchor in blank paper becomes
  three, which is the worse failure for a per-anchor median. Cost bounds break
  on the lowest rung too.
  The apparent yield gain is fully circular and is the reason the criterion was
  chosen: accepted occurrences rise 209 → 218 with McNemar significant in the
  term's favour (p = 0.021), and **every** flip up to weight 1.0 was an
  occurrence the harvest had rejected for `anchor_spike` — the statistic the
  term suppresses by construction — while genuine convergence got worse
  (`not_converged_local` 21 → 31). Measured on §11's original criteria the term
  would have passed brilliantly on every rung.
  That closes the fourth repair path for the single-anchor outlier, after the
  bending term (§7), the hinge (§8) and the corner-anchor diagnosis (§10). What
  is left is not a fifth term but the cause §11a named: the coverage term's
  blindness to which segment owns a skeleton point. The hold-out (Abb. 20) was
  deliberately NOT spent — the protocol confirms only a weight that passed
  development, and spending a reserve on a refuted hypothesis burns it for the
  next one (#326).

- **The answer the decomposition was built for, and the term moved to where
  the defect lives (`qualitaetsmetrik.md` §11a).** 96 chain solves, 41 280
  letter anchors, at the optima the stored occurrences came from; 128 stranded
  anchors in 82 of 344 occurrences across 27 glyphs, so this is a property of
  the model and not of a glyph. The sum check held everywhere (worst 1.7e-13).
  **The coverage term is the driver**: 32.4× its control strength at a
  stranded anchor, aligned with the displacement to a cosine of −0.996, and
  decoupled from the distance field (`coverage` vs `geo` 0.912 → 0.554). Two
  of §11's four candidates die here. The width term is *weaker* at stranded
  anchors (0.9×). And the Tikhonov pull, which looked like a finding at 8.5×,
  is force/displacement 4.167e-3 stranded against 4.166e-3 control — the same
  spring stretched further, identical to four figures. Without the control
  population that number would have been read as an explanation.
  §11 had asked which counter-force *holds* the anchor out; measured, the
  question is the wrong way round. Nothing holds it — the data terms push it
  there and Tikhonov is the only restraint. The field reading at the samples
  (the one §11 marked as owed, because no anchor is ever queried) says why
  that is cheap: 0.1849 xh of anchor travel — ~5.7 px — costs 0.6 px of extra
  distance to ink at the samples. The spline absorbs the excursion.
  `CHAIN_LETTER_BIND_WEIGHT` now carries the term on the chain path's LETTER
  blocks, in the displacement form: second difference of the per-anchor
  deltas inside a letter's own pen-stroke, never across a lift, never across
  a segment, never on the anchors (which would be §7's rejected bending
  term). Default 0.0 and verified byte-identical on a real solve — every
  number of the pre-term run reproduces exactly — so the A/B's baseline arm
  is an identity rather than a re-derivation.
  Stated in the same place rather than left implicit: this term is a
  stiffness answer to an attribution problem. The measurement says the driver
  is the coverage term's blindness to which segment owns a skeleton point —
  the same blindness the overlap term was introduced for, one level down. The
  A/B measures a brake, not a cause, and a passing criterion must not be read
  as „the stranding is understood" (#322).

- **The autopsy of the `d` chart form (`qualitaetsmetrik.md` §12).** §10 had
  narrowed the human „Bereich daneben" verdict to one glyph and named the
  autopsy as the next step; this is it, over all 18 `d` screens, the 14
  stored occurrences they map onto 1:1, and the chart row itself. The
  deviation is neither a translation (the best one removes 0.6 %, an
  independent confirmation of §10's 0 % measured against the ink instead of
  the chart form) nor affine (a full scale+rotation+shear map reaches 10.6 %,
  and explains as much in the clean rows as in the flagged ones): ~89 % is
  non-affine, and it sits in ONE stretch of ductus — the ascender loop's
  closing run and the exit, anchors ≈ 90–119. The bowl is untouched. The
  human's own markers, projected back onto the drawn line, land at anchors
  92–118 in 8 of 10 flagged screens — the same stretch, from an unrelated
  measurement.
  The sharp part is geometric and label-free: **all 10 `d`s with a following
  letter shorten the exit run (−17 % to −33 %), all 4 word-final ones leave
  it alone.** So the exit defect is join-conditional, and the fix is NOT
  „move the Laufform's exit left" — variant 100 already carries the median
  correction, but as one averaged form over two populations that differ
  systematically, which no single Laufform can be. That is a model question
  (variant split, or the run-out belongs to the join generator) and is left
  open rather than guessed. The chart row scores 85.82, rank 46 of 62: the
  authoring metric is faithful to the chart cell, and the chart cell is not
  the running form (#322).

- **A neighbour-binding term in the fit objective — shipped inert, for a
  pre-registered A/B.** The single anchor that runs into blank paper is not
  stuck in a dead spot: measured at the 49 detected cases, the smoothed
  distance field pulls at `|∇d|` 0.898 of full strength and none of them sits
  on a ridge where the gradient would vanish. The anchor was driven there and
  nothing held it back — it is displaced 0.208 template units from the chart
  form while its own four neighbours sit at 0.047. The objective had no term
  for that: geometry, width, coverage and an ABSOLUTE Tikhonov pull per
  anchor, but nothing on the difference between neighbours.
  `_second_difference_operator` prices exactly that — the second difference of
  the DISPLACEMENTS, per pen-stroke, never spanning a lift. Which is neither
  the bending term of §7 (second difference of the ANCHORS, so it prices the
  real curvature a script lives on) nor the hinge of §8 (which prices
  distance, and „a jump onto nearby ink is still a jump"): an affine
  deformation of a stroke — what fitting a template to a hand IS — costs
  exactly zero, a lone anchor leaving its neighbours costs quadratically.
  `smooth_weight` defaults to **0.0**, so the objective is byte-identical
  until the A/B fixes a weight; a test pins that. The analytic gradient is
  checked against finite differences, because a wrong jacobian would not
  raise — L-BFGS-B would just converge elsewhere and the A/B would measure the
  bug instead of the idea. Corrected on a second reading: a **translation** is
  exactly free, a stretch or shear is NOT — the residual is
  `(A − I)·(second difference of the anchors)`, so it costs wherever the chart
  form is curved, which is where a genuine slant adaptation lives. The first
  test asserted „affine is free" by displacing the anchors linearly in the
  INDEX, a weaker statement that hid the gap; both halves are pinned now, and
  the docstring states the prior's real cost instead of overselling it (#321).

- **The three kinds of point are written down** (`vom-scan-zum-schreiben.md`
  step 4, glossary): **anchors** are the spline's control points and the fit's
  degrees of freedom (120), **samples** lie between them and are the ONLY
  place the objective reads the ink (~180), **steps** are anchor-to-anchor
  distances and what `anchor_spike_ratio` measures (119). An anchor therefore
  acts only indirectly, through the one or two samples around it — measuring a
  restoring force AT an anchor quantifies a force the optimiser never sees,
  which is exactly the mistake that produced a wrong dead-spot diagnosis. Also
  noted: `fitted_polyline_px` is the SAMPLE row, not the anchor row (#321).

- **`analyse.py` reads the page's tally block instead of choking on it, and
  uses it as a completeness probe.** The judgement sheet prints its own
  per-category count under the verdict lines, so the natural copy-paste
  carries them — and the parser rejected the whole file at the first one. It
  now parses those lines and checks each against the verdicts: a truncated or
  reassembled paste fails with the mismatch named, rather than quietly
  producing a prevalence table over whatever survived the clipboard (#320).

- **„Which codes are modifiers" is derived from the category table instead of
  naming `U` by hand** (`analyse.py`), so a verdict's size counts the findings a
  judge actually ticked and a later modifier cannot silently inflate it. The
  generalisation outlived what prompted it: a „could be better" tick, added so
  that `G` — „nothing I can name is wrong", which is not „as good as it gets" —
  could carry the author's reservation instead of swallowing it, and removed
  again before any round was judged with it. On every screen that already
  carries a defect the answer is foregone (the harvest holds such fits out
  anyway), so the tick would only have said something on the `G` screens, and
  next to each companion category it would have meant something else — a label
  set is worth less with an ambiguous column than without it. The ceiling
  question goes back to the one instrument that has a reference point, the
  paired comparison; `menschliche-bewertung.md` §2 records the attempt and why
  it was dropped (#319).

- **Recorded a rejected experiment: a curvature regulariser on the M4 fit
  (`qualitaetsmetrik.md` §7).** Chasing the capital S's spike one layer down
  found its real cause — the two `S` occurrences are written almost
  identically, and the difference is a single anchor the FIT parked in blank
  paper, 12 px from the nearest ink and 9.3× the median step off its neighbour,
  while 119 of 120 anchors sit on the line. Nothing in the objective can see a
  lone outlier (`e_geo` is a mean over samples, the Tikhonov energy a mean over
  anchors, `MAX_ANCHOR_DELTA` far too loose). A second-difference penalty on
  the deformation field fixed the defect convincingly on every SHAPE measure —
  spike median 3.29 → 1.25, occurrences above 8× 39 → 0, better in 245/245 and
  worse in none, the aggregate median 41 % less faceted — but on ground truth,
  the fitted centerline's distance to the measured ink, the mean got WORSE in
  241 of 245 occurrences. A global tax to stop a local crime: it does remove
  the needle (worst-case distance 0.61 → 0.45 xh) but drags the whole chain off
  the stroke to do it. Reverted, with the lesson written down — shape-regularity
  measures (spike, cross-occurrence agreement) all improve for any term that
  pulls toward the prior, so they can never adjudicate alone; the next attempt
  should be a targeted one-sided hinge on an anchor's ink distance, which costs
  exactly zero for anchors that sit on ink (#315).

- **Pre-approved the Claude Code Remote scheduling tools for repo sessions**
  (new committed `.claude/settings.json`): `send_later` and the trigger
  CRUD/list/fire tools no longer raise a permission prompt — cloud sessions
  schedule their own PR check-ins constantly, and the container is ephemeral,
  so the committed project settings are the only place the grant persists.
  Only the scheduling family is allowed; every other Remote tool (session
  creation, archiving) still prompts (#314).
- **Documented the `aug07` write round and its new wordbench baseline**
  (`qualitaetsmetrik.md`): 23 letter resamples under the sharpened
  verticalisation tolerance (`oe` and `U` deliberately held back),
  `apply-laufform` on all 20 stored variant-100 keys, 96 word traces re-harvested with the
  restart-capital pen lift. Headline words 0.110392 / pairs 0.165678 — the
  pair regression sits in the dz/dk drills, whose resampled d now carries its
  chart cell's gently curved back (chart truth over drill similarity). The
  open verification finding — the fixture Laufform layer is rebuilt locally
  and one run sits on the tolerance knife edge — is issue #311 (#312).
- **Sharpened the verticalisation pair: gently curved capital flanks stay
  round (Korb #5, the S bowl).** The derivation's downstroke straightening
  and the Sütterlin metric's vertical-run detector share one new constant
  `core.geometry.VERTICAL_STRAIGHT_TOL = 0.035` (was three silent copies of
  0.10): a run must bow at most 3.5 % of its chord to count as a Gleichzug
  downstroke — calibrated over all 61 authored letters (real stems ≤ 3.0 %,
  oval capital flanks ≥ 3.6 %). The S bowl (and O/A/M/… flanks) keeps its
  even curvature instead of being pressed flat with fillet corners; a
  deliberate metric re-baseline documented in `qualitaetsmetrik.md` §6
  (`aug07`): glyph bench 0.183765 → 0.175550, every ink-anchored component
  better, honest loser Y (+0.115, collinearity on its de-straightened
  crossing). Stored templates change only via re-derive (`resample`) (#310).
- **Word-trace harvest lifts the pen after a restart capital (Korb #5,
  „Säbel" S→ä).** `assemble_word_strokes` no longer welds the composed
  connector's retrace prefix into the pen run after an S/O/B/K/P capital:
  the run ends at the capital's ductus end and the trace's next stroke
  starts at the connector's Grundlinie turn — the fresh Ansatz the plates
  show. New `restart_slots` parameter fed from `CAP_RESTART_BASES`; stored
  traces change only on a re-harvest (#310).

- **Kringel-exit class rule: b and o depart for the join at the bow's
  closing loop, not at the chart cell's rising coupling stub (Korb #5,
  „Säbel").** In bound context the stub after the Kringel's self-crossing
  is cut — centerline and silhouette, like the t-bar — so the join leaves
  the knot near-level instead of cresting a second time above the bow; a
  knot departure is excluded from arm fusion (it is no covering arm), and
  word-final b/o keep the full chart form. As a fallback for bow exits
  without a detectable knot, a closing bow coupling a round body's top now
  departs on the falling chord (the arm grammar's shallow-join precedent)
  instead of the level clamp. Wordbench words 0.114448 → 0.110605, pairs
  0.164343 → 0.162783 (same fixtures, A/B); biggest movers Zorn −0.113,
  von −0.048, Soldaten −0.034, Säbel −0.008. Golden compose fixture
  re-baselined; new unit tests pin the cut, the word-final keep, the
  low-crossing guard and the base gate (#309).

- **The rule work's duplicated computations now agree by construction — a
  byte-exact structural cleanup of `core/compose.py` and its neighbours.**
  The placement stage and the connector drawer used to re-derive the same
  anchors independently and only agreed as long as two code sites stayed in
  sync: the fork/bar coupling index, the fork height clamp, the sawtooth
  pass-through slope, the arm-fusion apex gate and B's landing tangent are
  now computed ONCE (shared helpers `_fork_height`/`_align_slope`/
  `_arm_fuse_apex`, plus `fork_couple_idx`/`land_deg` passed into
  `_connector_centerline`), so the solved distance and the drawn join can no
  longer diverge. The untyped 12-key `prev` dict — the whole inter-slot
  interface — became the `_PrevGlyph` dataclass with the three exit→join
  handshakes (`exit_line`/`stem_launch`/`cap_retrace`) as named fields. Silent
  numeric ties turned into imports or named constants: the composer's
  `TANGENT_WINDOW` and the derivation's `CORNER_WINDOW_UNITS` now both read
  `geometry.TANGENT_WINDOW_UNITS` (the comment-only "matches the
  corner-detection window" tie, shared via the core-import-free tangent
  module so composition stays clear of the pipeline stack; the frozen
  metric's same-named constant deliberately remains a mirror by value — the
  ruler must not follow an experiment), the silhouette simplify tolerance is
  `template.SILHOUETTE_SIMPLIFY_TOL` (was `0.002` restated in three places),
  the medial-axis snap cap is `extract.medial_snap_cap_px` (was
  `max(3.0, 0.25·unit_px)` inline in both fit and pipeline), and the
  erase-corridor/broad-nib-mask/Bézier-handle-floor factors got names. Three
  inline quadratic Bézier evaluators collapsed into `_sample_quad_bezier`.
  Deliberately NOT unified: `CONNECT_SAMPLES` vs.
  `aggregate.PAIR_CONNECTOR_POINTS` (a segment count and a resample point
  count that merely share the value 24 — an import would fake a coupling),
  the arm classification's two predicates (they differ in a float round-trip;
  unifying would change edge behaviour) and `_key_base` (identity since R2,
  but its removal rests on registry reasoning, not mechanical proof — own
  follow-up). Verified byte-exact end to end: regenerated golden fixture
  decompressed byte-identical, a full-precision compose dump over all pen
  kinds/provenance/laufform/override variants byte-identical, the wordbench
  words+pairs report identical to the last digit, glyphbench unchanged on
  both scripts, 780 tests green (#308).

- **Deleting a task in the Auftragskorb asks first.** The bin icon on a
  work-item row was a single click on a hard DELETE with no undo anywhere in
  the basket. That is the wrong bargain for a CLOSED item in particular: its
  handling protocol — the session's restatement, the diagnosed stage, the
  resolution — is precisely the symptom → diagnosis → change archive the §5
  protocol exists to accumulate, and one stray tap on a phone emptied it. The
  icon now opens a confirmation naming the row, and an erledigter Auftrag adds
  the warning that its record is history plus the pointer to the „erledigte
  anzeigen" toggle, which hides rather than destroys (#306).

- **ESLint 9 → 10, with the one plugin that blocks it pinned rather than
  dropped.** Dependabot's bump (#235) could not land on its own: `npm ci` died
  in the ERESOLVE check because `eslint-plugin-jsx-a11y` still declares a peer
  range that stops at ESLint 9, and 6.10.2 is its newest release — there is no
  version to bump to. An `overrides` entry in `app/package.json` pins that peer
  to ours instead; the plugin runs fine on 10, verified by its rules still
  firing (`jsx-a11y/no-autofocus` on a canary), and `eslint.config.js` carries
  the note plus the condition for removing the override again. `@eslint/js`
  moves to 10 with it. The new recommended set brought exactly one finding:
  `no-useless-assignment` on a `let caption = null` in `SchriftkundeView` whose
  every branch assigns before use — the dead initialiser is gone, which also
  drops a `| null` the type never needed. Lint is back to 0 errors and the same
  59 known warnings (#304).

### Removed

- **„Kopplung Anfang/Ende" is gone from the wizard — the field was read by
  nothing.** The Weg step let a letter's entry/exit coupling height be
  authored per glyph (Grundlinie · Mittellinie · Oberlinie · Unterlinie); it
  travelled from `bboxes.guides` through `canonical_from_path` into
  `templates.entry.coupling` / `exit_pt.coupling` and was carried onto every
  M4 fit — and there the trail ended. `core/compose.py` decides the coupling
  height by class rule (`HIGH_COUPLE_BASES`: round bodies e/a/o/c/d/g/q couple
  high at the apex, arcade letters n/m/i/u low through the baseline garland,
  measured on Abb. 19/20/22) and never once read the stored label, so the
  control promised an effect it did not have. Removed end to end: the two
  dropdowns and their locale strings, the wizard state, the `GuideConfig`
  fields, the pipeline stamp, the fit carry-over, and `CouplingPointOut` →
  `EndPointOut` (point + tangent). No migration and no data rewrite — stored
  `guides` JSON keeps its keys (`extra="ignore"` makes an older client's
  payload valid, and one of the 77 authored bboxes carries a non-default value
  nothing ever consumed), and rows authored earlier keep their `coupling` key,
  which is now simply ignored on read. `architektur.md` §3 and the glossary
  said the coupling height lives in the template; both now record that the
  class rule owns it (#306).

### Fixed

- **The judgement sheet showed a letter without the pen path it was fitted
  inside — and that cost the first round its headline finding.** The harvest
  fits a whole word as ONE chain, so the connectors belong to the chain's
  connector segments and are absent from a letter's own anchors. Round 1 drew
  only those anchors, every joined letter ended in mid-air on screen, and 23 %
  of the round was filed as „the entry stroke is missing" — correctly, for what
  was on screen. Re-measured: the ink beyond the letter sits 0.25 xh from the
  drawn line but **0.02 xh from the stored pen path** (24 of 26 covered), so
  the fit had it all along. `build.py` now fetches the word traces and draws
  them faintly beneath the judged line, and warns when they are missing.
  The tempting conclusion — „then the labels were an artefact" — is refuted by
  its own control group: the GOOD screens carry the same undrawn connector ink
  and MORE of it (0.50 xh vs 0.25), and the same judge did not flag it there.
  What the labels actually caught is the SEAM between letter and connector,
  where the stored pen path itself deviates from the ink (0.105 xh against
  0.047 on good screens, AUC 0.84) — so „a kink at the edge" was literally
  right, and no per-letter metric can see it because every such window ends at
  the letter. `qualitaetsmetrik.md` §9 carries the correction, the withdrawn
  reading and the two failed metric attempts that followed from it; prevalence
  without `E` is 39 % rather than 53 % (#318).

- **Three self-checks and a persistence asymmetry in `tools/humanbench`.** The
  realised repeat gaps were measured at insertion time, but a repeat spliced in
  between an earlier pair pushes it further apart — so „gaps 40-65 positions"
  described a sequence nobody was shown; they are now read off the finished
  order. In the paired mode the severity band a repeat was drawn from came from
  the full old snapshot's rank while the bands were cut over the MATCHED rows
  only, so every occurrence the new snapshot lost pushed repeats towards the
  last band; the ranks are re-stamped after matching, and the prefix check is
  graded against the population that was actually banded. And the round-1 page
  stored `{at, seen, notes, stamps, picks}` while its `restore()` read `spots` —
  a field nothing ever wrote, so one reload would have dropped every marker
  placed so far, silently, and the markers are the only part of the judgement
  independent of our own numbers. The current page persists them; the symmetry
  is now pinned by a test in both directions, and round 1's stamp says the
  markers are plausible but not proven complete (#317).
- **The harvest rejects the „Anker im leeren Papier" occurrence
  (`qualitaetsmetrik.md` §8).** A fit that parks one anchor in blank paper — the
  Sütterlin capital S in „Sprünge" sits 12 px from the nearest ink at 9.3× the
  median step, while 119 of its 120 anchors lie on the line — is not a
  measurement of the hand, so the occurrence is now declined rather than
  medianed into a Laufform. New `anchor_spike_ratio`: the largest step between
  neighbouring anchors against the median step OF ITS OWN stroke, maximised
  over the strokes. Per stroke rather than pooled because a long body stroke
  otherwise inflates the denominator and hides a needle in a short umlaut one
  (`ue` in „Zügel" scores 7.21 pooled, 10.61 against its own stroke); pen lifts
  never count, or every multi-stroke glyph would be rejected for writing its own
  ductus. Gate `anchor_spike` at `MAX_ANCHOR_SPIKE_RATIO = 8.0` on **both**
  harvest paths, calibrated on the 245 stored occurrences (median 2.68, p90
  7.28, max 32.9): 23 rejected (9.4 %), and not one glyph drops below
  `LAUFFORM_MIN_OCCURRENCES` — though `S`, `s` and `ue` each go 2 → 1, all three
  already below that floor. On the accepted set the worst distance of a fitted
  centerline to the measured ink falls from 0.613 to 0.258 x-heights and its p90
  from 0.194 to 0.149. It catches DISCONTINUITIES and only those: a smooth
  deviation spread over many anchors passes untouched, and the 0.258 xh that
  remains says such residuals exist (#316).
- **…and it sits on the path that actually produced the data.** The first
  version of the gate lived only in `_harvest_case_slots`, while all 245 stored
  occurrences come from `_harvest_case_chain` (`fit_path == "chain"`, 245 of
  245) — it would have rejected exactly nothing in production, with a green test
  suite, because every new test pinned the slot path. Found by adversarially
  injecting the needle into the chain path and getting `['ok','ok','ok']` back.
  The check is now a step in the chain path's `letter_gate` cascade, after
  `anchor_count` (the ratio of a mis-shaped array says nothing) and before the
  connector reason (this is the letter's own chain, not a neighbour's damage),
  and it excludes the letter from the STATISTICS layer only — the trace keeps
  it, so a gated letter stays visible to the admin.
  `test_the_chain_path_rejects_an_anchor_in_blank_paper` holds the hole shut (#316).
- **Where the spikes sit — a claim since withdrawn as circular.** Reviewing the
  gate put 22 of the 23 rejected occurrences (96 %) at a corner anchor or a
  stroke boundary, with five of the seven rejected `e` occurrences spiking at
  the *same* anchor 43, and read that as one instrument defect rather than 23
  broken measurements. The location, however, came from the detector's own
  maximum, so it could not have said anything else. §9's human markers are the
  independent test and they do not reproduce it: not one of the six
  single-labelled outlier markers sits at a stroke boundary, and the click
  matches the measured maximum in only 45 % of cases overall. The finding is
  therefore **unsupported rather than disproven** (at n = 6 the markers refute
  nothing either), and any repair aimed at that anchor class needs a
  non-circular location analysis first. Recorded in §8 with the per-glyph
  table and corrected in §9; the gate stays as the backstop either way (#317).

- **`apply-laufform` enforces the occurrence floor the dialog alone could not
  hold — the capital S's spike.** The Sütterlin `S` is written from a
  variant-100 row derived from exactly TWO occurrences (`trace_meta.laufform.
  n_occurrences = 2`), and at n = 2 `np.median` returns the mean of the two: a
  fit blow-up in the `Sprünge` occurrence — anchor 113 sitting 0.357 units from
  its twin where the neighbours sit 0.01–0.03 apart, at an unremarkable 1.261 px
  per-glyph RMSE — landed in the written form at half amplitude as a visible
  spike off the top right, with the whole bowl 3.3× more faceted than the chart
  row (mean turn 13.0° vs. 4.0°). The caution lived only in the SPA dialog's
  proposed selection (`LOW_N = 3`), and a re-apply names the keys that ALREADY
  have a Laufform row — so a key that once earned one from a word harvest kept
  being re-derived from however thin an aggregate it had since acquired.
  `POST …/aggregates/apply-laufform` now carries the floor itself
  (`core.aggregate.LAUFFORM_MIN_OCCURRENCES = 3`, where the median starts being
  able to outvote one bad anchor): a thinner aggregate is reported as
  `below_min_occurrences` with its count and left alone, however it was named,
  and `?min_occurrences=` lowers it for the human who means it — the same
  enforce-don't-trust doctrine as the `work_items` protocol. The dialog keeps
  proposing and keeps every row tickable; a deliberate tick now travels as the
  lowered floor instead of as a check nobody ran (#315).
- **Wordbench fixture Laufform layer is byte-true to the stored rows (issue
  #311).** The admin single-template GET takes a `variant` query parameter, so
  the stored variant-100 (Laufform) rows are readable at all — and
  `fetch_fixtures` now freezes them VERBATIM (manifest `laufform_precision:
  "stored"`) instead of reconstructing them locally from the hand's aggregates,
  where a chart resample between apply and fetch (or a run on the
  `VERTICAL_STRAIGHT_TOL` knife edge) turned wire-level noise into a discrete
  render flip. Same transported-not-recomputed philosophy as the
  `render-context` nib read; a deployment predating the parameter is detected
  per response (it serves the variant-0 row, which says so) and falls back to
  the reconstruction (`"reconstructed"`). The `--verify` gate also cache-busts
  every one of its own `/write` reads now — the `aug04` CDN gotcha could make
  it "verify" the edge cache's pre-write-round state. Knife-edge caution
  documented at the shared constant in `core/geometry.py` (#313).

- **The d→i join stops digging a valley, and the d's crossing keeps its ink**
  (Korb #4, the „die" complaint). Two class rules in the composer, no
  overrides: (1) a HIGH reversal exit — the trimmed loop exit of d/round-s
  falling from its crossing (~1.15 xh) onto the next letter's rising flank —
  no longer takes the baseline garland; the rescue had already declared its
  chord truthful, and the garland dug a valley to ~0.5 xh below it followed
  by a long level run into the entry (the complaint's „waagrechter
  Verbindungsstrich" — the near-horizontal connector stroke). The taut cubic
  now falls straight onto the flank, as
  the two measured d→i dissections show. (2) `erase_silhouette_piece` gained
  a `keep` parameter — the centerline the stroke STILL writes — and cuts the
  eraser capsule back around it: the d's loop-return stub crosses its own
  stem, and erasing the stub used to bite the stem's ink at the crossing (the
  reported white gap). All three trim sites (loop stub, t-bar, entry stub)
  pass their kept line; ink is only ever spared, never added. Wordbench:
  words 0.114563 → 0.114448, pairs 0.164880 → 0.164343 (both sets improve;
  `die` 0.077 → 0.068, its d→i transition 0.096 → 0.070), report columns
  `meas_dconn_median` 0.127 → 0.124 / 0.217 → 0.206, pair Gleichzug
  doublings 8 → 6. Golden compose fixture deliberately re-baselined (#305).

## [0.23.0] — 2026-08-05 — The word-scale chain fit era

### Added

- **The chain objective learned the one thing a pen always knew: a stroke is
  not written twice.** The grid-seed A/B's follow-up (the basin probe) proved
  the placement collapse is a property of the objective — on all five probed
  collapsing cases the stacked solution scores lower on EVERY term, coverage
  included, because the objective checks the union of the segments against the
  union of the ink and is blind to attribution, and the collapse converts
  Tikhonov-taxed anchor deformation into free block translation. The new
  `e_overlap` term prices that physics directly: sample pairs of different
  segments within 0.15 xh (inside one drawn hairline) pay a quadratic hinge,
  with the measured 0.2–0.4 xh seam stub zone exempt for adjacent segments
  (init-geometry mask, so the analytic gradient stays exact) and letter-letter
  stacking never exempt. Calibrated by a pre-registered sweep and a
  three-config A/B over the frozen fixtures: at the chosen weight **0.2** the
  term heals exactly the four joins the ink adjudication had named as the
  guard's marginal fires — mechanically, the seam retrace disappears from the
  solve itself (`streiten|0` seam share 1.178 → 0.136 xh), so
  `connector_degenerate` stops firing without any threshold moving. Accepted
  occurrences 241 → 245 (`longs` 3 → 6), zero new flags, `at_bound` 1 → 0,
  geo_rmse p50 +0.003 px; weight 1.0 is the measured over-strong regime and
  was rejected. The interleaved pair-drill stacks stay knowingly open — their
  centerlines sit beyond the radius, and whether that interleaving is
  legitimate tucking (the hand demonstrably tucks `k` under a `d` crossbar) or
  collapse needs ground truth, not a bigger radius. The FD gradient test runs
  on an overlapping, paying configuration; weight 0 is regression-tested
  byte-identical to the old objective. Findings in
  `docs/proposals/uebergaenge-befund.md` §5c, the term in the glossary
  (Überlappungsterm) (#300).

- **The chain can start its letters where their own ink says they are — and
  measuring that settled what the placement collapse actually is.**
  `fit_word_chain` gained an optional `slot_shift_init` (harvest flag
  `--chain-seed grid`): each letter's translation block starts at the grid
  placement the harvest has always computed for its coverage window, instead
  of at the composed layout. The objective is untouched — only the basin the
  descent enters changes — and the A/B over the frozen fixtures ran with
  pre-registered criteria. Outcome, reported straight: **8 flagged joins are
  genuinely healed** (collapsed gaps reopen, backward connectors run forward
  again — e.g. `Silber|4` gap 0 → 0.060 xh, forward −0.919 → +0.323) and 7
  more letters converge, but 4 other joins derail, the gate cascade reshuffles
  and the net yield is **exactly zero**, so the default stays `composed`. The
  decisive follow-up measurement: letters beside still-flagged connectors
  travel 1.8× further beyond their seed than clean ones, and **all 11**
  still-collapsed joins started from a healthy seed — the solves walk from the
  right start INTO the collapse. The placement collapse is therefore a
  property of the objective (overlapping letters both earn coverage credit for
  the same ink, so stacking is cheap), not of the initialisation — which
  redirects the next round at the objective itself. Knob, seed columns in the
  diag CSV, and three unit tests stay as measurement infrastructure; details
  in `docs/proposals/uebergaenge-befund.md` §5c (#300).

- **The Auftragskorb takes general notes — a fourth, target-less kind.** Not
  every small thing is a letter, a join or a word: an admin-UI wrinkle or a
  wording slip belongs to no glyph and does not earn a GitHub issue, so until
  now it had nowhere to go while the admin was on the move. `work_items` gained
  `kind: "note"`, whose whole content is the note text (the one field it
  requires, no target columns, no `specimen_ref`), and the Korb drawer gained a
  „Notiz anlegen" field above the list — the drawer is the surface that is
  already open, and ⚑ by definition always marks something specific. In the
  basket a note leads with its own first line instead of the word „Notiz", so a
  column of them reads as what was noticed. The handling protocol is unchanged
  except for one field: a note closes on its `resolution` alone, because every
  stage in the §3 vocabulary names a stage of the *writing* path and has
  nothing true to say about a UI wrinkle (`stage` stays allowed where it
  applies). No migration — `work_items.kind` was always a plain string (#301).

- **The word overlays are switchable one layer at a time, and the words
  overview reloads like the letters grid.** Three inks over one crop — plate,
  trace, engine — is a lot, and which pair actually answers the question
  (ink↔trace, ink↔engine, trace↔engine) changes with the question. Two toggle
  buttons above the cards, each carrying the swatch its layer draws with, turn
  the trace and the engine on and off independently, and the face caption names
  exactly what is drawn. The overview now opens on the plain side-by-side
  (crop | wie geschrieben) instead of the overlay, with the Überlagern switch
  one click away, and the two faces shrink together rather than wrapping the
  written word under the crop. It also gained the letters grid's „Neu laden":
  because `/write/word` answers with `s-maxage=86400`, the button moves the
  admin-wide bust stamp through `fetchRenderWord` into the request itself, so
  the words really recompose after a template, Laufform or override change
  instead of being served the old composition by the CDN (#298).

- **The word harvest can fit whole words as one pen chain (`--path chain`,
  report-only).** `tools/laufform/harvest.py` gained the Stage-B integration
  of issue #278: after the existing per-slot grid fits (which keep supplying
  each letter's local window and the fallback diagnosis), every maximal run of
  joined slots is fitted as ONE `fit_word_chain` chain, letters pass a
  five-gate cascade (like-for-like coverage · geo RMSE · placement bound ·
  anchor count · a degenerate adjacent connector rejects the letter too —
  seam parameters are shared), and the word records are welded WITH their
  connectors for the first time — a `traced` row is finally "the word as
  written", closing the dead `authored` branch. Plus `--jobs` (ProcessPool
  over cases, order-independent medians), `--sets words,pairs` (the pair
  drills flow through the same code path), `--diag-csv` (34 columns incl.
  per-join connector signals), `--max-cases`. The old path stays the default
  and byte-identical (`--path slot`, pinned by a golden test); `--apply` is
  refused outside `--path slot --sets words` so the chain path stays
  report-only until its measurement round passes. 24 new unit tests (#294).
- **Four faces per letter in the Buchstaben overview, and a grid that can sort
  itself worst-first.** Original (the chart crop) · Tafel-Form (the authored
  chart ductus, variant 0) · Laufform (the derived running form, variant 100) ·
  „Median & Vorkommen" (the H1 aggregate: the per-anchor median with the
  occurrence chains thin behind it, the MAD circles, and the Laufform actually
  in use drawn dashed against it) — the source, the two forms the engine can
  write from it and the statistics they came from, in one row per letter,
  where the overview used to show chart against written and nothing else. Every
  face has an honest empty state instead of a blank box: „noch keine Laufform"
  where none was derived, and for the sketch a hint that distinguishes loading
  from no hand, from an unavailable admin read, from genuinely no aggregate.
  Overlay mode still collapses the first two faces into the red silhouette
  overlay, and the faces are `flex: 1 1 150px`, so they break to 2 × 2 on a
  phone. The new sort toggle (Alphabet · „Schlechteste zuerst") turns the
  alphabet into a work list. The sketch itself moved out of
  `shell/LensStats.tsx` into `shell/AggregateSketch.tsx` plus the pure
  `shell/sketchGeometry.ts`, so the miniature in the grid is the same drawing
  as the one in the statistics block, only shorter (#293).
- **The key numbers under each of them — occurrences, mean fit residual, the
  stored score and where its points went — and the whole alphabet's scores in
  one read.** New `GET /sources/{id}/templates/quality` (admin-gated like the
  raw template row per quellen-und-rechte.md §5, uncached, and declared above
  `GET /{glyph_key}` so FastAPI cannot swallow the literal path as a glyph key)
  serves `templates.trace_meta["quality"]` for every row of the style, extracted
  in SQL by the new `TemplateRepository.list_quality` rather than dragging the
  dense `pixel_anchors`/`half_widths_px` arrays along with it: 0.145 s for all
  80 rows, against 0.44 s for a SINGLE glyph through the recomputing per-glyph
  `/quality`. What it serves is the score at AUTHORING time — the number the
  derivation stamped onto the row, not a re-score with today's metric code —
  which the chip tooltip says, and only variant 0 is read, because a Laufform
  row inherits the chart row's `trace_meta` and its stamped score is therefore
  a copy, never a verdict on the median geometry. The rest of the grid is as
  cheap: the render payloads come from two batch requests (`renderCache`'s
  `fetchRenderGlyphs` gained `variant` and `bust`, which is what makes a
  Laufform batch possible at all), the statistics from the shared workbench
  context, and the expensive per-glyph `/diagnostic` is now fetched only for
  the overlay mode that needs its outline geometry — the grid used to fire one
  per card, some thirty per visit. Score colour, the score chip and the
  per-category breakdown moved out of the wizard into
  `sections/admin/quality/scoreParts.tsx` and are now shared by the wizard
  preview, the overview and the Diagnose modal, which gained the breakdown it
  had never shown although its payload always carried it (#293).
- **A connector degeneracy guard (`tools/pairlab/connector_qc.py`) — the QC
  the loop-exit fix showed was missing.** On the Abb.-20 pair drills the chain
  connector silently degenerates in 11 of 23 occurrences (a long straight
  diagonal through both letters, every convergence gate green). Four pure
  geometry signals behind a minimum-chord gate — seam share, forward ratio
  (`net_dx / arc`), arc-vs-gap, straightness×length — calibrated in-sample
  against the 11 known-bad rows: 11/11 flagged, one demonstrable false
  positive across 179 labelable word rows (raw flag rate 4.2%, chosen for
  recall since the guard's job is keeping contaminated joins out of the
  `gen_chamfer` audit; the stricter setting is one `dataclasses.replace`
  away and documented). Reported as a `chain_conn_degenerate` column and a
  worst-first block in the chainbench; the precondition before any chain
  connector may feed `pair_aggregates`, and gate 5 of the coming word
  harvest (a flagged connector rejects its adjacent letters too — seam
  parameters are shared) (#292).
- **`GET /sources/{id}/render-context` — the resolved render context of a
  source at full precision, admin-gated.** Everything a render resolves before
  it draws (lineature, width resolver, the source-pooled Gleichzug nib and the
  pooled pen), unrounded, where the public `/write` payloads carry the same
  numbers rounded to the four decimals the renderer draws at. It exists for the
  one job that needs to reproduce a served payload bit-for-bit offline: the
  fixture rebuild without Cloud SQL access (`tools/wordbench/fetch_fixtures.py`)
  used to recover the pooled nib by reading a rounded half width back off
  `/write/glyphs`, and that ≤5e-5 xh error flipped knife-edge ink-clearance
  decisions into up to ~0.02 xh of glyph-placement jitter. The fetcher now asks
  for the exact value first and falls back to the readback on an API that
  predates the endpoint, records which it got as the manifest's
  `nib_precision`, and tightens its own acceptance gate accordingly — a root
  frozen with the exact nib must compose bit-for-bit against `/write/word`
  instead of within the old jitter allowance. Admin-gated like the raw template
  read (quellen-und-rechte.md §5): the pool spans every authored template of
  the source, including variant rows no endpoint serves. The payload rounding
  itself stays at four decimals — it is part of the frozen render contract, and
  a fifth decimal would cost ~7 % payload size for nothing the exact scalar
  does not already fix (#288).
- **A glossary of the project's own vocabulary — `docs/reference/glossar.md`.**
  The docs, issues and admin UI have grown a private language across the
  optimisation rounds: palaeography (Duktus, Schwellzug, Anstrich/Auslauf),
  architecture (Bibliothekseinheit, Laufform, Prüfstein, open-core moat),
  measurement (Kettenfit, Naht, like-for-like Gate, matched arc,
  Bézier-Handle-Floor, Cusp-Connector, degenerierte Solves) and house metrics
  (`gen_chamfer`, `doff`, `dconn`, `bench_loss`/`pair_loss`, MAD hull) — none of
  it explained where a newcomer meets it. Around 115 entries in six themed sections
  with an alphabetical quick index: each one a plain-language explanation that
  assumes nothing, plus, where it helps, the formula name and the module or
  constant it lives in (`core/fit.py::CONVERGED_GEO_RMSE_UNITS`), deliberately
  enough anchor vocabulary that pasting an entry into any AI chat lets the
  reader dig further. Includes the four Stage-A chain metrics **M1–M4** with
  what each asks, how it is computed and where it stands — plus an explicit
  warning that M1–M4 (chain), M0–M7 (MVP milestones, hence "M4-Fit") and H/R/W
  numbering are four independent schemes — and a research section (AIoU, LDTW,
  DTW, HWD, Sigma-Lognormal, G1/G2 continuity) that places the house metrics
  against the published state of the art (#286).
- **A standing upkeep rule so the vocabulary cannot outrun the glossary.** Any
  doc or PR that coins a new Fachbegriff, metric, named failure mode or repo
  idiom adds its entry in the same change — recorded in `CLAUDE.md` §
  „Working guardrails", mirrored into `.github/copilot-instructions.md`, spelled
  out with the entry format in the `/write-docs` skill and enforced at PR time
  as a gate in `/open-pr` (#286).
- **The two preconditions Stage A put in front of issue #278's Stage B are
  measured, and they do not both fall the same way.** Stage A compared the chain
  fit against the independent one under two silently different rules, and said
  so; `chainbench` now removes both differences and re-measures. **M1** grades a
  chain letter in its own letter-local coverage window — the window the
  independent M4 trace was always graded in — while the fit keeps seeing the
  whole pair window, since owning the connector's ink is the chain's entire
  point; the report carries the union gate, the like-for-like gate and, as the
  symmetric alternative, the baseline re-graded on the union window. **M3**
  clips generated, chained and ink-read connector to one common arc (the
  specimen's ink gap intersected with each curve's own x-span) before applying
  the unchanged pairmeas formula, because the chain connector owns the two stub
  zones the ink-read one does not have. The verdict changes accordingly:
  three quarters of M3's Stage-A gap was definitional (chain 0.086 → 0.040 xh
  against a bar of 0.034 → 0.028) and what remains sits in a single exit class,
  while M1's shortfall survives the like-for-like comparison (0.665 → 0.690
  against an unmoved 0.746) and is therefore a real property of the coupled
  problem rather than a grading artifact. Written up in
  `docs/proposals/uebergaenge-befund.md` §5c: the conditional go becomes a go,
  with the M1 deficit carried into Stage B as a named floor and the
  `pair_aggregates` ban kept for the loop-exit class. The fit itself is
  untouched — M2, M4 and all three kill criteria reproduce number for number (#284).
- **`pairlab` can fit a letter join the way it was written — as one continuous
  pen path — and Stage A of issue #278 measured whether that is worth doing.**
  `tools/pairlab/chain.py` fits `letter → connector → letter` as ONE problem:
  both chart rows (never the composed Laufform geometry) plus the generated
  connector, whose interior points are free anchors with no form
  regularisation, with the two seams tied by *shared anchor indices* rather
  than a continuity penalty — so the letter/connector boundary stops depending
  on whether the letters happen to touch on this specimen, which is exactly
  where today's ink-gap dissection returns nothing. Placement stays a separate
  unregularised per-slot translation block, the coverage window closes the hole
  between the letters, and the coverage distance is Huber-capped so foreign ink
  has bounded leverage. `tools/pairlab/chainbench.py` runs the chain and
  today's independent fit over the same 248 frozen occurrences and reports the
  four Stage-A metrics plus the kill-criterion signals. The verdict is mixed
  and written up honestly in `docs/proposals/uebergaenge-befund.md` §5c: no
  kill criterion fires, 87 % of the joins that are unmeasurable today become
  measurable, and the chain deforms letters less than the independent fit — but
  convergence and connector shape do not pass as specified, so Stage B is a
  *conditional* go with two named preconditions. Measurement only: nothing here
  touches the DB, the API, `core/` or rendering (#283).
- **The word-bench fixtures can be rebuilt from the deployed API, not only from
  Cloud SQL.** `tools/wordbench/fetch_fixtures.py` is a read-only sibling of
  `export_fixtures.py` that produces byte-compatible fixture roots over HTTP,
  reusing the exporter's pure pieces and replacing only the DB block — so a
  session without Cloud SQL egress (a cloud session, a fresh checkout) can
  still run the word bench, pairlab and chainbench. GETs only, `ADMIN_TOKEN`
  from the environment and never echoed, with a `--verify` gate that composes
  the rebuilt cases locally and compares them against `/write/word` (#283).
- **The Laufform can be adopted from the admin — deliberately, with the
  difference visible first and a confirmation in front of it.** `apply-laufform`
  is the one step of the whole hand model that changes what the engine writes,
  and until now it existed only as a curl call (#270). It gets a surface that
  matches that weight rather than hiding it: at the foot of the Buchstaben view,
  in its own set-apart block, a dialog that warns this leaves the measuring half
  of the system, previews per glyph what would change (occurrences, distance to
  the Laufform in use, „neu" for a first write, „unverändert" at distance 0),
  requires an explicit confirmation, and afterwards reports what was written and
  what was skipped and why. It stays hand-wide because the endpoint is — a UI
  implying per-glyph choice would lie about what the button does (#277).
- **Every letter says whether the form the engine writes is still the form the
  statistics say.** A chip („Laufform aktuell" · „Laufform veraltet · Abstand
  0,05" · „noch keine Laufform"), and in the median sketch the currently
  rendered running form drawn dashed against the median that would replace it —
  the difference is there to look at before anything is overwritten (#277).
- **`GET /hands/{hand_id}/aggregates` carries the freshness pair per row:**
  `laufform_anchors` (the rendered variant-100 form) and `laufform_dev_xh` (its
  distance to the median). The Prüfstein used to exist only as a by-product of
  a rebuild or an apply, so answering "is this stale?" required doing something
  first. Null wherever the comparison is meaningless: a non-base variant, no
  stored running form, a differing anchor count (#277).
- **The letter statistics draw every occurrence behind the median.** The MAD
  circles gave the spread as a number; the bundle of thin occurrence chains
  gives it as a shape — ten forms hugging the median and one outlier read very
  differently from an evenly scattered set, and that is the question ("are the
  occurrences alike at all?") the layer exists to answer. Same reading as the
  pair sketch already had, in the same frame (occurrence anchors are stored
  centered, exactly like the median) (#276).
- **`GET /write/glyphs` takes a `variant` parameter.** Default 0 is the
  authored chart ductus every public surface writes with; `100` renders the
  derived Laufform, which is what lets the Buchstaben view show the two side by
  side. A glyph without a row for the asked variant lands in `missing` exactly
  like an unknown key, so asking for the Laufform of a letter that never got
  one is an empty answer rather than a silent fallback to the chart form (#276).

- **End-to-end overview doc `docs/concepts/vom-scan-zum-schreiben.md`: how the
  writing system emerges from a chart, the specimen plates and the author's
  tracing.** The pipeline was documented stage by stage — schema in
  `architektur.md`, ruler in `qualitaetsmetrik.md`, occurrence and statistics
  layers in the Handmodell plan, doctrine in the Werkbank proposal — but
  nowhere as one narrative, so the shape of the whole (what is input, what is
  derived, what actually renders) had to be reassembled from six documents
  every time. The new doc walks the six steps once in plain German prose, each
  with a tight `Fachlich:` / `Im Admin:` / `Wer macht was:` triple, and then
  answers the three questions the stage-by-stage docs leave implicit: which
  artefacts are on the writing path at all (`templates` + approved
  `glyph_pairs` as data, shaping/compose/pen models as rules — everything else
  measures and never writes), why there is no context-forked `a`-before-`b`
  template (occurrence anchors are stored centered, so the letter median is the
  context-free body while transitions are their own per-pair measurement
  objects — with the honest limit named: body reshaping smears into the letter
  median, visible as fat exit-side MAD circles), and what goes stale (the
  Laufform is a materialised snapshot behind explicit manual steps; generated
  transitions read the current form's exit/entry at every compose and follow
  automatically, approved overrides deliberately do not). Closes with the six
  known gaps as of 2026-08-02 and a mapping list into the detail docs. Every
  route, endpoint, table and constant it names is verified against the repo (#275).
- **Lifecycle status headers on every doc under `docs/`, a living-docs table
  with named update triggers, and a `write-docs` duty that keeps them true.**
  The docs tree had grown past thirty files in which a settled decision, an
  already-shipped proposal and a pure sketch looked exactly alike — a reader
  (human or agent) had to reconstruct from PR archaeology whether
  `htr-integration.md` describes running code (it does not) or whether the
  Handmodell stages were still ahead (H0–H2 shipped in v0.22.0). Each doc now
  opens with one blockquote directly under its H1, dated absolutely and drawn
  from a deliberately small vocabulary — `bindend`, `lebend`,
  `teil-umgesetzt`, `umgesetzt-historisch`, `offen`, `Befund-Journal`,
  `statisch` — that states what is built, with PR and migration evidence, and
  what is still future. `docs/index.md` gains a "Dokument-Status" section
  explaining the vocabulary plus a table of the living documents with the
  concrete files whose change obliges an update (for example: `write-api.md`
  follows every `/write/*` route, `core/shaping.py` and `core/compose.py`;
  `werkzeuge.md` follows every entry script under `tools/`), and three
  section-wise obligations for docs that are only partly implemented
  (`animation-rendering.md` §1/§3, `styleanalyse.md` layers 1–2,
  `quellen-und-rechte.md` §5). The proposals list carries each stage's status
  as a short tag, so a shipped stage can no longer read as open work. The
  `write-docs` skill gets the matching duty: implementing part of a proposal
  updates its header and its index tag in the SAME PR as the code, a new
  proposal starts at `offen`, and a doc that turns `lebend` is added to the
  trigger table. The audit that produced the headers also found stale claims,
  all fixed in this pass rather than merely flagged: the Laufform rows live on
  `variant=100` (not `1`), `werkzeuge.md` was missing both harvest tools and
  the wordbench report modules, the `sprachregelung.md` schema example still
  carried the `position` key removed by migration `0017`,
  `qualitaetsmetrik.md` still headlined a July run, `quellen-und-rechte.md` §5
  did not name the admin-gated aggregate reads, `offenbacher.md` claimed the
  Koch 1928 chart was unseeded (it has rendered on the public Tafel since
  migration `0008`), `architektur.md` §4 still called the pair-override layer
  a staging proposal, `design-system.md` was missing `PaperCardLink`, and the
  animation width-resolver table listed no `broad_nib` (#275).

### Changed

- **The connector guard was suspected of eating the chain's yield; it turns out
  to be reporting a real defect, and the defect is the chain's.** 46 of the
  chain harvest's rejections failed only `connector_degenerate` — a gate the
  per-letter path does not have — which looked like an over-strict guard on a
  population (the Abb. 20 pair drills) it was never calibrated for. Two
  independent studies of those 46 rows say otherwise, and the decision came
  from an external label nobody had used: the MEASURED ink connectors already
  in the fixtures' `pair_instances.json` (232 of 248 joins have a twin,
  including all 38 flagged). Chain-vs-ink `dconn` is **0.403** on flagged joins
  against **0.093** on clean ones, AUC 0.900. The decisive evidence uses no
  shape distance at all: on flagged rows the ink's own join travels +0.280 xh
  forward against +0.283 on clean rows — identical — while the chain's fitted
  ink gap collapses from 0.229 to 0.012 xh, 17 of 38 at exactly zero. The
  specimen says those letters do not touch; the chain stacked them and the
  connector had to run backwards to arrive. Mechanism, measured two ways: by
  join it is the left glyph's exit height (high-exit classes flag at 40 % on
  word plates and 16/16 on the pair drills, everything else at 8–10 %, and the
  drills simply over-represent that class), by solve it is run length (2.6 % at
  run ≤ 4 against 14.0 % at run ≥ 5, p = 0.0074, flat across the whole
  iteration-budget ladder so not solver noise). No threshold was moved: every
  relaxation was costed against the ink and each one admits genuinely derailed
  joins, while the guard's measurable weakness is **recall**, not precision (16
  stub connectors with a negative forward ratio deliver 25 accepted slots today
  purely because their chord is short). `connector_qc.py`'s docstring is
  corrected instead: its "two signals never fire" claim holds for the
  chainbench corpus but **not** for the harvest, because the two harnesses feed
  the same connectors against different ink edges — every number in that
  docstring is a chainbench-frame statement and is now labelled as one. Two
  known measurement defects (the overlap double-count, the seam height-band
  mismatch) are recorded with their measured effect of **zero freed slots**, so
  the next round does not re-derive them. Full finding in
  `docs/proposals/uebergaenge-befund.md` §5c (#299).

- **The word chain has its own iteration budget, and it is no longer the thing
  that stops the solve.** The chain borrowed `core.fit.DEFAULT_MAX_ITER` — a
  per-GLYPH budget on a per-glyph problem, while a three-slot word chain
  carries roughly 820 free parameters. Measured over the frozen words+pairs
  fixtures (96 solves, 344 slot rows), **300 iterations was the binding stop in
  91 % of solves**: not tight but far below the median a converging chain
  actually needs (1211 iterations, p25 680, p90 2518). A capped solve is still
  descending, so it fails the convergence gate and its occurrence is dropped —
  and where the truncation lands moves with the initialisation, which is why
  the harvest was not reproducible across the exact-nib change.
  `tools/pairlab/chain.py` now owns `CHAIN_MAX_ITER`, default **8100**, at
  which **no solve is truncated at all** (longest observed: 4215 iterations).
  A budget that binds is the wrong kind of knob — L-BFGS-B stops at its own
  criteria, so a high ceiling costs nothing for solves that already converged
  and only the hard tail pays: 2700 → 8100 buys "nothing is cut off" for
  **+5 % CPU**. It is also demonstrably harmless rather than presumed so —
  305 of the 344 slot rows are bit-identical to the 2700 run, the 39 that move
  belong exclusively to the ten formerly-capped specimens, that movement is
  settling noise (median +0.0010 px, 22 rows worse against 17 better), and all
  344 gate verdicts are unchanged. `core.fit` is deliberately untouched, so
  measuring the chain can never re-tune the production M4 fit behind the
  wizard, `/fit` and `/diagnostic`; `KS_CHAIN_MAX_ITER` re-runs the sweep.
  Effect against the old 300: accepted occurrences 232 → 241,
  `not_converged_local` 47 → 35, `geo_rmse` median 1.063 → 1.027 px.
  `fit_meta` and the harvest's `--diag-csv` gained `iterations`, `max_iter`
  and `hit_iteration_cap` so that state is read rather than inferred.
  Measurement only: no DB, no rendering, no request path. Details in
  `docs/proposals/uebergaenge-befund.md` §5c (#299).

- **A word card is two faces now, like a letter tile.** One frame held the
  plate crop, the green trace and — overlapping both — the red engine ink, which
  is three answers to two different questions in one picture. Left is now the
  MEASUREMENT (plate ink + the traced pen path + the clickable letter boxes and
  join dots; the engine joins it translucently only when the Überlagern switch
  is on), right is what the engine writes on its own. Both faces are drawn at
  the same px-per-unit on the same baseline row, so „trifft der Fit das Wort?"
  and „was macht das System daraus?" are two glances instead of one untangling,
  and a width or slant difference is a difference rather than a rendering
  artefact (#297).

- **The first Stage-B chain harvest is written, and the running forms are now
  derived from whole-word pen paths.** Until now every occurrence in the
  statistics layer came from fitting one letter at a time; the chain fit
  (`tools/pairlab/chain.py`) solves letter–connector–letter as a single pen
  path, and its first full harvest replaced the layer wholesale: **232
  occurrences** (up from 218, and for the first time including letters read off
  the Abb. 20 pair drills) and **77 word traces** (up from 58) that carry their
  connector strokes instead of the letters alone. Rebuilding the hand's
  aggregates over them yields 35 keys, of which **15 running forms were
  applied** — `a d e g h i l m n r u w` refreshed, and `S`, `sz` (ß) and `z`
  given a running form for the very first time. `t`, `o`, `c` and `b` were deliberately
  withheld and are reported as excluded; `t`'s stored running form is
  consequently, and correctly, stale until its sample recovers. The wordbench
  headline moves from **0.116886 to 0.115623** on the words (the pairs give up
  0.001013, the same trade the July running-form round documented: the pair
  drills are written close to the chart). Documented as a dated re-baseline in
  `docs/reference/qualitaetsmetrik.md` §6, together with the second effect that
  fell in the same window — fixtures built from the exact pooled nib rather
  than the four-decimal readback, which confirms the previously documented
  headline was right and the export was what had drifted (#295).
- **The admin header is the public header.** The workbench sat under a 48 px
  strip of Garamond-13 buttons while every public page carried the 67 px bar
  with the wordmark and the Playfair nav — two houses in one product, and the
  shabbier one was where the actual work happens. The shared chrome now lives
  in `components/HeaderBar/HeaderBar.tsx`: the sticky, blurred, hairlined bar
  with an optional content-width cap, the `•kurrentschrift.ink` wordmark with
  its viridian dot and italic TLD, and the Playfair nav link with the animated
  viridian underline and `aria-current`. `components/PublicHeader` and
  `sections/admin/shell/AdminHeader` are both written on top of it; the public
  bar is visually unchanged, and the admin bar keeps exactly the differences it
  has reasons for — full-bleed instead of capped, because the workbench needs
  the width; `zIndex` 1100, so the Korb drawer (1200) and the LetterPicker
  popover (1300) still sit above it; and its two extra slots, the Vorlage chip
  (now a link back to the Vorlagen-Auswahl) and the Korb ⚑ badge. Its nav lost
  the `overflowX: auto` that grew a scrollbar around the hover underline
  sitting four pixels below the links (#293).
- **The admin follows the public type system instead of its own hard-coded
  sizes.** `/admin` opens with `PageContainer` + `PageHeader` (eyebrow
  „Werkbank", Playfair title, `Prose` intro) over a three-column card grid
  whose cards name the plate and not only the script; `shell/Panel.tsx`'s
  `ViewHeader` gained an `eyebrow` (the three views pass their area) and
  replaced its hard-coded `fontFamily: display, fontSize: 24` with
  `variant="h4"` plus the design-system heading rule — size from the ladder,
  face and weight in `sx`; panel titles became `h2` elements; the occurrence
  caption left 10 px for the 14 px caption floor. The workbench is the surface
  this project is used from most and should not read as the draft version of
  its own design system (#293).
- **The Petzendorfer 1889 chart is hidden from the Vorlagen-Auswahl — hidden,
  not removed.** Two cards both labelled „Kurrent" make the one choice the
  whole admin hangs off ambiguous, and the second cannot be authored against
  yet: it was seeded ahead of time for the digits row Loth 1866 lacks, written
  by a different hand at ~57° against Loth's ~50°. The new
  `CONFIG.hiddenSourceIds` filters it out in the two places in
  `context/AdminContext.tsx` that can produce a selection — the source list
  itself and the persisted choice read back from localStorage, because a stored
  hidden id would strand the admin on a Vorlage with no card to switch away
  from. Nothing is deleted: no migration, no DB change, the row, its chart
  bytes and every API route stay exactly as they are, and taking the id out of
  the list brings the card back (#293).
- **The admin is one workbench in three views instead of five pages with tabs
  and a permanent letter sidebar.** Entering `/admin` now asks the one question
  everything below depends on — which Vorlage — because every letter, join and
  word belongs to exactly one source and its hand; the chosen script is named
  in the header and one click goes back to switch it. Under it sit exactly
  three views, each following the same overview ⇄ detail pattern:
  **`/admin/buchstaben`** carries a letter's whole life in one column (the
  chart cell with the Einrichtungs-Wizard, the Diagnose modal and the
  collapsible chart editor, the Tafel-Form beside the derived Laufform, every
  harvested occurrence as a crop cut-out, the H1 statistics with its median
  sketch, and chips onward to the letter's joins and words);
  **`/admin/uebergaenge`** puts the generated join first, the H2 „Gemessen vs.
  komponiert" measurement beside it and the pair editor last, in the order the
  stage doctrine triages; **`/admin/woerter`** writes any text, breaks it into
  the letters and joins it consists of (each a jump into the other two views)
  and shows the traced specimen with its clickable occurrence overlay wherever
  a plate of this hand wrote the same word. This completes the absorption of
  `/admin/vergleich`, `/admin/paare` and `/admin/belege` into the Werkbank that
  `optimierungs-werkbank.md` §2/§6 announced — the tools themselves are
  unchanged and simply lost their own routes; the old paths stay as redirects
  so bookmarks and work-item links keep working (#276).
- **Every level of the admin now accepts freely typed targets, not only what a
  plate happens to contain.** Any two-letter combination and any word can be
  typed, written by the engine and complained about — most combinations were
  never written by hand anywhere, they still have to look right, and until now
  there was nowhere in the admin to look at one. A filed `work_item` for such a
  target carries no specimen reference and says so, rather than inventing one (#276).
- **One shared data layer and one header above the three views.** The
  occurrence reads and the per-hand statistics load once for the whole
  workbench (`sections/admin/shell/WorkbenchData.tsx`), so walking letter →
  join → word costs no refetch; the Auftragskorb moved into a header drawer, so
  ⚑ works from wherever the complaint arose. The subject of each view lives in
  the query string (`shell/focus.ts`, pure and unit-tested), which makes every
  cross-jump a plain link, the back button an inspection history and a reload
  land where the work was. The desktop/mobile split is gone with the sidebar:
  one layout serves both, and the letter grid became an on-demand picker (#276).

### Fixed

- **Deleting an item in the Auftragskorb only took effect after a reload.** The
  panel removed the row optimistically and announced the change to the shell in
  the same breath — but that announcement bumps the shared `refreshKey` the
  panel itself re-reads on, so the re-read raced the `DELETE` and usually won:
  the server's pre-delete rows came back and put the row on screen again, where
  it sat until the next reload. The basket now reports a mutation only after
  the server confirmed it, for the delete and for the „missverstanden" rejection
  alike; a failed call still restores exactly the one row locally and announces
  nothing, because the server state never moved (#301).

- **Generated Übergänge were drawn mirrored below the baseline.** The two SVG
  path helpers disagreed on the y sign — `ringsToPathD` keeps y by default,
  `polylineToPathD` always negated it — so any surface drawing both kinds of
  item under one y-flipping `<g>` got the letters (rings) right side up and the
  generated connectors (polylines) flipped a second time. They left the word
  and reappeared as loose strokes under it, in the word cards, the specimen
  comparison overlay and the pair editor's live preview and its own
  pointer-drawn connector. Verified in the browser before and after: the
  connectors of `muß` sat at y [−0.73, −0.48] and [−0.70, −0.40] against a
  payload of [+0.48, +0.73] and [+0.40, +0.70], an exact sign flip, and the pair
  editor showed letters at y [0, 1.01] beside a connector at [−0.74, −0.49].
  `polylineToPathD` now takes the same explicit `flipY` its ring twin has; the
  asymmetric defaults stay (the public "as written" surfaces rely on them) and a
  unit test states the rule so the trap cannot be re-entered silently (#297).

- **The engine ink was drawn in the wrong place on every word card.** The
  overlay that projects a composed word onto its specimen pixels pinned the
  composition's left edge to the crop's left edge — a convention, not a
  measurement. Over the 63 Sütterlin word rows that put the engine a median
  **8.9 px (~0.3 xh) left** of the ink it was supposed to be compared against,
  so every composition read worse than it is and the deviation an admin saw was
  mostly registration error. The trace and the composition live in the identical
  frame (baseline = 0, 1 unit = x-height), so the row's own measured
  registration places both: the median left-edge error drops to **1.1 px**, and
  what remains at the right edge is the real width difference — the thing worth
  looking at. Extracted as the shared, unit-tested
  `shell/model.ts::traceFrameOf`/`traceMatrix` and applied to the word cards
  AND the specimen overview list; the left-edge pin survives only as the
  fallback for a sample no harvest ever traced (#297).

- **The gate decides what becomes a measurement, not what the trace shows.** The
  chain harvest wrote word traces that broke into disconnected fragments:
  `tools/laufform/harvest.py` assembled the pen path out of the letters its gate
  cascade had ACCEPTED, so a letter that merely wobbled took itself and the
  connectors on either side out of the drawing — `Einen` (E-i-n-e-n) was one
  chain solve over all five slots and came out as three pieces because slots 2
  and 4 failed `not_converged_local`. Two layers, two questions: `instances` is
  the statistics layer and stays gated exactly as before (a wobbly letter must
  not pollute a Laufform median), while `word_instances` is the inspection layer
  and now carries the WHOLE solved run — every letter segment and every
  connector the chain produced. Only a slot the chain could not fit at all (no
  template, no window, `chain_failed`) stays out, because it has no geometry;
  a trace that splits for that reason is honest. The per-slot verdicts stay
  readable beside the geometry, and the two sets are two explicit fields rather
  than one overloaded key: `measurements.traced_slots` is what is drawn,
  `fitted_slots`/`unfitted_slots` keep meaning "accepted as an occurrence", with
  `gates`, `converged_local` and `geo_rmse_px_by_slot` unchanged. Measured over
  the frozen words + pairs fixtures: 27 of the 77 previously written records
  still hold more than one body stroke, down from 32, and every remaining split
  is a genuine pen lift (the `E`/`P` ornaments, the u-Bogen, `t`'s crossbar,
  `ß`, the ä/ü umlauts) or a chain that really did stop — no split is caused by
  a gate any more. 19 further specimens gain a trace at all, having had every
  letter rejected and therefore been dropped whole. The occurrence layer is
  byte-identical across the change (232 rows, the same Laufform drafts), and the
  longer welded runs stay inside the wire caps (longest stroke 2277 of 4096
  points, `Galoppieren`; at most 4 of 128 strokes), with the downsampling guard
  in `cap_word_strokes` reporting rather than 422-ing if they ever do not (#296).
- **A glyph with two coincident anchors returned a 500 — and took the whole
  batch with it.** `core/template.py::sample_polyline` builds its spline
  parameter from the cumulative chord length, and a zero-length chord leaves
  that parameter flat, on which `CubicSpline` raises "`x` must be strictly
  increasing sequence". Not a theoretical input: anchors are stored rounded to
  four decimals, so the apex of a short out-and-back stroke can round its two
  samples onto the same point — the Sütterlin `period` does exactly that — and
  that one key failed the whole 60-key render batch the new letter overview
  asks for. The repeat is dropped before splining (a zero-length chord carries
  no geometry, only the same position twice); a path without one keeps every
  anchor and every sample byte-identical, which the compose golden fixture
  confirms. Two unit tests in `tests/test_template.py` (#293).
- **Occurrence thumbnails cut into the letter.** The crop left a fixed 4 crop px
  of air around the stored occurrence box, but that box comes from the M4 fit
  and hugs the centerline, so the ink runs past it on every side. The margin
  scales with the box now (`max(7, 0.18 · √(w·h))`) and the thumbnail row grew
  from 64 to 80 px (#293).
- **pairlab measured the loop-exit join class against a reference that was not
  there, and on an arc that was not matched.** `analyze._real_join` read the
  specimen's own joining stroke only inside `JOIN_BAND_Y`'s 0.8 xh ceiling — the
  composer's clearance band, not a statement about where joins live — while a
  loop exit departs at y ≈ 1.04–1.13 xh and runs level at ≈ 0.9–1.0 xh: the
  tracker saw 4 of 18 gap columns, every `d→*` occurrence fell back to the
  straight exit→entry chord, and the clipped seed latched onto the ink below the
  join (a following descender in `b→p`, empty space in `o→r`). The band ceiling
  now follows the exit, which needs no new constant and leaves every pair whose
  exit sits inside the band bit-identical. On top of that
  `chainbench.dconn_matched_arc` clipped all three curves to one x-interval,
  which is an arc match only while a curve is single-valued in x — a loop-exit
  chain connector owns the near-vertical descent off the loop and the plunge
  into the next letter, so its clipped piece carried 1.69× the reference's arc
  at the same x-span and `dconn` compared physically different positions; the
  reference now defines the stretch and the other curves are trimmed to it.
  Together this turns M3's last open class from `gen 0.058 → chain 0.228` into
  `0.074 → 0.050` (on the word plates alone `0.081 → 0.034`) and the pooled
  paired delta from +0.008 (p 3e-5) into +0.002 (p 0.48); M1, M4 and the kill
  criteria come out field-for-field identical because `chain.py` never reads
  `_real_join`. See `docs/proposals/uebergaenge-befund.md` §5c, Nachtrag
  „loop-exit" — which also records why the `pair_aggregates` ban stays anyway (#290).
- **The pair-chain fit no longer stalls on letters that are composed on top of
  each other.** `analyze._generate_connector` emits its full Bézier subdivision
  whatever room the placement leaves and floors its handle at 0.05 xh, so where
  two letters touch or overlap the cubic doubles back into a cusp carrying two
  dozen anchors inside ~0.05 xh of arc. `chain._second_difference_operator`
  scales as 1/ds², which put the connector's smoothness block into the Hessian
  ~10⁷ times stiffer than on a normal join: `e_smooth(x0)` 5.2e6 against 53.7,
  `f(x0)` 51.9 against 0.026, and 24 of the 248 Stage-A occurrences — every
  `c→h`, `r→e`, `m→u`, `n→e` — burned their whole iteration budget unbending
  that connector while `e_geo`, `e_cov` and `e_wid` never moved from their
  starting values at all. `chain.regularise_connector_anchors` now
  re-discretises a connector whose chord is below
  `CHAIN_CONNECTOR_MIN_SPAN_UNITS`: the same curve, resampled by arc length to
  the anchor count that chord can carry (endpoints exact, so the shared seam
  anchors survive, and nothing above the threshold is touched). The affected
  occurrences go from 4 to 20 of 24 converged on the letter-local gate (#285).
- **`chainbench` exported an optimizer status key `chain.py` never writes.** The
  row read `fit_meta["status"]` while the fit writes `"message"`, so
  `chain_status_msg` was the empty string on every row and the L-BFGS-B
  termination reason — the one column that identifies a stalled solve — was
  invisible. The termination message, `optimizer_success`, the iteration and
  evaluation counts and the per-term energies at `x0` against `x*` are now all
  exported, with an explicit flag for a non-finite initial energy (which `_r`
  would otherwise round into an indistinguishable `None`) (#285).
- **The registered overlay of engine ink over the specimen pixels is back — and
  now also sits on the word evidence card.** The redesign had left it wired to
  a hardcoded `false`, so the sharpest error-finding view in the project was
  dead code while the surrounding copy still promised it. It returns as a
  switch (on by default) in the Wörter overview, and the traced-word card now
  draws the composed word in the same registered frame as the specimen and the
  trace — original ink, hand trace and engine output in one picture (#276).
- **A failed occurrence load is now visible instead of spinning forever.** The
  shared data layer set its error flag but kept the lists at `null`, so
  `loading` never ended and every occurrence panel sat on a spinner that could
  not resolve; the state is now ended by the error and reported as one quiet
  line per block (#276).
- **Filed tasks in the Auftragskorb link to their subject.** The basket named
  what was wrong and offered no way to it, although the three views are one
  link away for exactly those keys — a letter/pair/word row now navigates and
  closes the drawer (#276).
- **German singulars:** „1 Beleg" and „1 Vorlage" instead of „1 Belege" /
  „1 Vorlagen" (#276).

## [0.22.0] — 2026-08-02 — Hand model statistics: aggregates + gemessen vs. komponiert

### Added

- **Wordbench "gemessen vs. komponiert" columns (Handmodell H2): every composed
  letter join is now reported against the specimen's own dissected one.** The
  pair layer already knew what the writer did at each join — `pair_instances`
  holds one dissection per adjacent joined pair of the very specimens the bench
  scores — but the bench never looked at it, so a worse word said only *that*
  it got worse. `tools/wordbench/pairmeas.py` puts the two side by side per
  join: `doff`, the HORIZONTAL placement delta read in the frame the harvest
  measured in — the two letters' body endpoints (left glyph's last
  non-diacritic stroke end, right glyph's first non-diacritic stroke start)
  against the measured `geometry.offset`'s x — and `dconn`, the mean pointwise
  distance between the two connector centerlines, arc-length-resampled to the
  same 24 points the pair aggregation uses and then each shifted onto its own
  first sample, i.e. a translation-free shape-and-sweep distance. The frame is
  the whole point: the composer's coupling anchors sit up to ~2 xh away from
  the body endpoints after a capital ornament or a trimmed lead-in, so
  comparing them against a body-frame measurement reports an artifact rather
  than an error (`Of` read 2.06 that way, now 0.07). The measured offset's y is
  excluded by construction — the harvest cancels the relative vertical fit
  shift, so it is the composed body Δy at harvest time and would measure the
  composer against itself. The run prints `meas n=<matched>/<joins> doff=…
  dconn=…` on every scored row (zeros included, `-` where nothing matched) and
  appends `meas_matched`/`meas_excluded`/`meas_doff_median`/`meas_dconn_median`
  after the stable headline block, `pair_`-prefixed for the pairs set. Two
  kinds of join stay out of the medians and are counted instead: a dissection
  the harvest's own QC rejected (`fit_ok`, the gate the pair-aggregate rebuild
  applies too — 11 of 199 word rows, 3 of 33 pair rows), and a join rendered
  from an approved override, which IS a harvested centerline and would score
  ~0 against its own source. `compose_word(..., provenance=True)` additionally
  states each join's coupling endpoints `exit`/`entry` in word coordinates (the
  Endstrich has no `entry`) — not readable off the emitted centerline, kept for
  overlay diagnostics, deliberately not used by `doff`. The measured joins
  freeze as a new per-set fixture artifact `pair_instances.json`
  (`export_fixtures.py`, written atomically, with `--only pair-instances` to
  fill it into existing fixture roots without re-freezing — and thereby
  re-baselining — crops, masks, slots or templates); a corrupt or unreadable
  one costs the columns and one warning line, never the run. Report-only in the
  strict sense, like the slant column and the Gleichzug audit before it:
  computed under its own guard so a crash cannot move the number (and says so
  once per run), matched by `(kind, specimen_id, from_slot)` plus agreeing base
  keys so a shifted slot counts unmatched rather than comparing the wrong
  transition, and verified byte-identical — `bench_loss` 0.116886 and
  `pair_loss` 0.164506 to the last digit before and after, every per-entry loss
  unchanged. Null line: words 188/214 matched, doff median 0.135 · dconn median
  0.115; pairs 30/34, 0.192 · 0.217. The public `/write/word` payload and the
  compose golden fixture are untouched (provenance stays off by default) (#268).
- **"Gemessen vs. komponiert" on the Vergleich page's pair cards (Handmodell
  H2, read surface).** The Verbindungen tab showed a specimen beside the
  composed pair and left the verdict entirely to the eye, while the occurrence
  and aggregate layers already knew how far the generator sits from the measured
  median for exactly that join. Each pair card now carries a compact "Gemessen"
  chip row between header and body: the occurrence count (the aggregate's
  `n_instances`, falling back to the matched `pair_instances` OF THAT SAME HAND
  so a card keeps a number without the admin-gated layer, and a second hand
  harvested on the source can never inflate a number the tooltip credits to one
  writer) and the `gen_chamfer` mean — the audit number this layer exists for —
  with the fuller pooled QC in the tooltip (chamfer max, harvest chamfer, fit
  residual, offset ± MAD, ink-gap share, plate-kind histogram, the named hand),
  plus a "Fit unsicher" chip when THIS specimen's own occurrence carries
  `fit_ok: false`. A card without a median says WHICH of the four reasons
  applies, in the Werkbank's own wording — still loading, no hand on the
  occurrences, never rebuilt, or not loadable — so "keine Messung" is left to
  the one case it describes (the hand's aggregates are there, this join is not
  among them). Both lists load once per source rather than per card — the public
  pair occurrences, and the pair aggregates of the hand DERIVED from those rows
  (modal non-null `hand_id`, never a constant), reused as-is when the tab is
  left and re-entered; a failing admin read degrades to the occurrence numbers
  behind one quiet notice instead of emptying the tab. Deliberately numbers
  only: the median-connector sketch stays in the Werkbank's pair lens, and a
  registered overlay of measured connector on composed pair is not attempted
  (different frames — a false superposition would read as evidence). Scoped to
  the Verbindungen tab; the Fremdhand tab stays view-only and unmeasured, and
  the numbers are matched by the same base-key pair the pair-editor deep link
  uses, so a card's readout and its "Im Paar-Editor öffnen" can never describe
  two different joins. Frontend-only, no API change (#267).
- **Werkbank "Stufen-Einsicht" (W5): the hand-model statistics layers are now
  visible inside the context lenses.** Both aggregate layers existed and had no
  reader — H1 medians and H2 pair medians were numbers only a rebuild response
  ever printed, while the surface where a complaint is made showed the chart
  form and the raw occurrences with the whole condensation step invisible
  between them. The letter lens now draws the stored aggregate between the two:
  the per-anchor median as an anchor chain with per-anchor MAD circles over the
  baseline/midband hairlines („Aggregat-Median (Laufform-Quelle)"), plus the
  pooled layer-1 numbers (occurrences, specimens, fit RMSE ⌀/max, x-height,
  position histogram). The pair lens gains „Gemessen vs. komponiert": every
  loaded occurrence connector thin, the median connector bold on top and the
  median offset as a dot with its MAD whisker — occurrences, median and hull all
  share the one left-exit frame, so the sketch needs no registration, and a
  `/write/word` overlay is deliberately not attempted (different frame; the
  comparison stays side-by-side) — beside the pooled dissection QC with
  `gen_chamfer` as the audit number. The hand is derived from the loaded rows
  (the modal non-null `hand_id`, never a constant: the Werkbank shows exactly
  one source and therefore one hand) and is NAMED in every block's header, with
  a quiet warning when the occurrences do not all name the same one — one
  hand's medians over another hand's occurrences must never happen silently.
  The two layers load and refetch independently (own state, own error flag), so
  a failing pair read never mutes the letter block and a rebuild leaves the
  other lens — and its own result caption — untouched; the admin-gated reads sit
  outside the spine's load, so a 401 or an empty statistics table degrades to a
  quiet caption and leaves the spine and both lenses fully usable. Each block
  carries a quiet per-layer rebuild button — that recomputes statistics and
  touches no rendering, which is also why `apply-laufform` has no button here:
  it writes Laufform rows, and this surface displays generated stages rather
  than editing them (optimierungs-werkbank.md §3/§7). The sketches stay honest
  about their own material: occurrences the rebuild skipped as `fit_bad` are
  left out of the pair sketch and its bounds (and counted in the caption)
  instead of squashing the median they never fed, an absent MAD prints no „±"
  clause, and an aggregate missing for the selected key reads differently from a
  hand that was never rebuilt at all (#266).
- **Pair aggregates (Handmodell H2): the statistics layer over the observed
  letter joins.** `pair_instances` has held every dissected join since H1/H2,
  but nothing condensed them — the pair level had occurrences and no medians.
  Migration `0023` adds the additive `pair_aggregates` table, the pair twin of
  `aggregates`, keyed `(hand_id, left_key, right_key)`, and the admin-gated
  `GET /hands/{hand_id}/pair-aggregates` + `POST …/rebuild?min_n=1` fill it
  from a hand's occurrences across all sources. The math lives in the pure
  `core/aggregate.py::aggregate_pair_instances`: the placement offset condenses
  to a per-axis median, the connector centerlines are resampled to 24
  arc-length-uniform points (`_resample_polyline` — differently-sampled traces
  of one stroke only line up over arc length) and reduced to a per-point
  median, both with a MAD hull, alongside pooled dissection QC (`gen_chamfer`
  as the „gemessen vs. komponiert" audit number, ink-gap share, the
  word-plate/pair-drill histogram, distinct specimens). `kind` is pooled — an
  Abb.-19 word join and an Abb.-20 pair drill are the same hand writing the
  same transition — and `min_n` defaults to 1 rather than the glyph layer's 4,
  because pairs are sparse (87 occurrences over 45 pairs on the 1922 plates)
  and one clean dissection is still the only measured truth about that
  transition; `n_instances` rides along so consumers can weigh it. Deliberately
  without an `apply` counterpart: the pair statistics are read-only by design —
  `glyph_pairs` stays the sparse verbatim override, the §4 join generator stays
  the default, and nothing here reaches the writing path (#265).
- **Auftragskorb protocol (Werkbank W4): a filed task now has to be understood
  before it can be worked, and diagnosed before it can be closed.** A
  `work_items` row used to carry only the admin's note and a free-text
  resolution — the handling doctrine
  (`docs/proposals/optimierungs-werkbank.md` §5) lived purely in prose, and a
  bare `PATCH {status: "done"}` closed anything. Migration `0022` adds
  `understanding` · `reproduced` · `stage` · `acked_at` · `closed_at`
  (additive, nullable) and the status vocabulary grows to `open` → `ack` →
  `done`, plus `returned` for the hand-back the doctrine used to express as a
  string prefix. The API enforces the transitions in the pure, unit-tested
  `check_transition`: acking requires the session's own restatement of the task
  and whether it could reproduce the complaint, closing requires that
  restatement plus a `stage` from the fixed §3 vocabulary (`chart_ductus` ·
  `laufform` · `join_rule` · `composition` · `pair_override` · `word_trace` ·
  `not_reproducible`) and a non-empty `resolution` — anything less is a 422
  naming the missing field. Acking is deliberately its own call: a protocol
  field may not travel on a status-less PATCH, and closing needs the
  restatement to be *stored*, so it cannot be produced at the same moment as
  the result. What accumulates is the point: a searchable archive of symptom →
  verified reproduction → diagnosed stage → change → measured effect, instead
  of a wall of „erledigt" (#264).
- **A source-free work-item queue, so a session can find its own tasks.**
  Reading the basket used to require knowing a `source_id` first, which sent a
  session guessing `/work-items`, collecting a bare `{"detail":"Not Found"}`
  and grepping the router source for valid ids. The queue is now reachable
  without any prior knowledge: `GET /work-items[?status=&source_id=]`,
  `GET/PATCH /work-items/{item_id}`, with each row carrying its own
  `source_id` back and an unknown `source_id` answering 404 instead of a
  quietly empty list. The source-scoped routes stay for the SPA. Round start is
  wired up too — `/prime` lists the open items, and the new `/work-basket`
  skill runs the protocol end to end (reproduce → restate → triage → rule-fix
  before override → measure → close) (#264).
- **Word editor (Werkbank W3): every stored word occurrence can now be
  re-traced by hand.** Each card on `/admin/belege` opens the new
  `WordTraceEditorDialog` — the specimen crop as underlay with the row's own
  registration frame drawn on it (Grundlinie + Mittellinie), the stored trace as
  the starting point, and pointer/S-Pen capture in which every pen lift
  (Absetzen) starts a new stroke, exactly like the wizard's Weg step. Per-stroke
  undo, clear and reset-to-stored; saving writes the path as an `authored`
  `word_instance` through the existing batch endpoint with a SINGLE item and
  without `replace`, so the server's overwrite protection re-traces exactly that
  occurrence and leaves every other row — and every other authored trace —
  untouched. Slot labels are preserved and the registration (`registration_px`,
  `xh_px`) is carried over so the row stays displayable, while the replaced
  path's automatic fit QC is dropped instead of ranking a hand-fixed word by
  dead numbers. The crop↔trace mapping moved into the pure, unit-tested
  `sections/admin/belege/registration.ts` shared by the list and the editor, and
  the frontend API layer grew `putWordInstances` + `getHand` (the occurrence's
  writer is echoed back as read, so saving a trace cannot wipe the hand's
  era/note). Authored traces are ground truth for statistics and training, never
  a rendering patch (optimierungs-werkbank.md §3/§6) (#261).
- **Aggregates rebuild (Handmodell H1): the statistics layer finally gets
  filled.** `aggregates` has existed since migration `0004` and never held a
  row; the admin-gated `GET /hands/{hand_id}/aggregates` and
  `POST …/aggregates/rebuild?min_n=4` now condense a hand's stored `instances`
  into one aggregate per `(glyph_key, variant)` — the per-anchor elementwise
  median (which IS the running form, because occurrence anchors are stored
  centered: "shapes, not placements"), the per-anchor spread as a median
  absolute deviation hull, the pooled layer-1 statistics (fit RMSE, x-height,
  position histogram, distinct specimens) and `n_instances`. The median math
  lives in the new pure `core/aggregate.py` (no DB imports — the API image
  ships no `tools/`, same rationale as `core/word_metric.py`). The rebuild
  response reports the H1 Prüfstein per key: `laufform_dev_xh`, the mean anchor
  distance between the recomputed median and the stored Laufform (template
  variant 100). Reads are admin-gated too — an aggregate is learned geometry,
  not public product surface (quellen-und-rechte.md §5) — and nothing here
  touches rendering. Migration `0021` re-keys the table to
  `(hand_id, glyph_key, variant)` following the R2 position removal (drop +
  recreate: the table was empty) (#259).
- **The Laufform row is now DERIVED from the aggregate (Handmodell H1
  complete).** `POST /hands/{hand_id}/aggregates/apply-laufform` (admin-gated)
  writes the hand's stored aggregates into the style's running-form templates
  (variant 100): the per-anchor median becomes the anchors — occurrence anchors
  are stored centered, so the median already sits in the chart row's frame —
  while widths, stroke topology and entry/exit/advance keep coming from the
  chart template, through the very `build_laufform_canonical` helper the manual
  `PUT …/templates/{key}/laufform` uses. With that the variant-100 row stops
  being the harvest's end product and becomes a derivation from the persisted
  occurrences, and a following rebuild reports the H1 Prüfstein
  `laufform_dev_xh` as 0. It reads the STORED aggregates and never recomputes
  them: writing templates affects rendering, so promoting a statistic into a
  rendered form stays a deliberate, separate step from the rebuild. Only
  base-variant aggregates feed it (a variant-100 occurrence would let the row
  derive from itself); keys without a chart template or with a deviating anchor
  count are reported as skipped with their reason, never guessed at. The
  response reports the pre-write distance per key, so the answer shows what the
  apply actually changed (#260).

### Fixed

- **The `X-Admin-Token` break-glass path could never authenticate against the
  deployed API.** The `ADMIN_TOKEN` secret version had been created with a
  trailing newline; Cloud Run injects secret bytes verbatim, so
  `settings.admin_token` carried that newline while an HTTP header physically
  cannot transport one — `secrets.compare_digest` in `api/auth.py` therefore
  rejected *every* possible token value with 401, and no amount of re-copying
  the token could fix it. `core/config.py` now strips surrounding whitespace
  from all four Secret-Manager-backed settings (`database_url`,
  `cf_access_team_domain`, `cf_access_aud`, `admin_token`) and maps a
  whitespace-only value to `None`, so the admin gate still fails closed with 503
  when nothing is configured instead of comparing against an empty string. The
  malformed secret version was replaced in Secret Manager as well; the new
  `tests/test_config.py` pins both the stripping and the outage itself.
  `docs/reference/frontend-stack.md` now documents the two rules this cost us:
  a self-set `X-Admin-Token` only ever reaches Cloud Run via
  `api.kurrentschrift.ink` (the apex `/api/*` 302s at the Cloudflare Access edge
  first), and Secret Manager versions must be created with `printf '%s'`, never
  `echo` — with the byte-count diagnosis, because command substitution hides the
  newline and makes a fingerprint comparison report a false match (#262, #263).

## [0.21.0] — 2026-08-01 — Optimierungs-Werkbank + open-core moat

### Added

- **The Optimierungs-Werkbank page (`/admin/werkbank`, stage W2): word spine,
  switching context lens, Auftragskorb.** One admin surface where the three
  occurrence layers finally meet, per the doctrine in
  `docs/proposals/optimierungs-werkbank.md` §2. The left column is the word
  spine — every stored trace over its specimen crop, worst first — now with an
  interactive overlay: a dashed box per fitted letter and a dot on every join
  between two adjacent letters. Clicking one switches the right column's lens:
  a LETTER shows its chart form plus every stored occurrence as a cut-out
  thumbnail (worst residual first, click to jump back into that word) and
  offers the wizard jump; a JOIN lists its dissected occurrences with the
  generated connector's distance from the plate ink and opens the pair editor
  for exactly that pair. ⚑ (or shift-click) files the element into the
  Auftragskorb — the `work_items` backend from W1 — where a letter first has to
  pass the one pre-sort question §4 puts on the human ("does it look wrong on
  its own too?"): yes routes to the wizard and files nothing, no files the
  complaint. `WordSampleOut` gained the specimen's page `rect` so page-pixel
  occurrence boxes can be placed inside a crop; the existing pages
  (Vergleich · Paare · Belege) stay untouched until the Werkbank absorbs them (#255).

### Changed

- **The Auftragskorb card shows what a session understood, and lets the admin
  say it got it wrong.** `KorbPanel` groups by protocol state — handed back on
  top (those wait on the author), then the queue, then what is in work, with
  the archive behind the existing toggle — and renders the session's
  restatement as its own block with chips for „nachvollzogen" and the
  diagnosed stage. An acked item carries a `missverstanden` button: one click
  opens a correction field and puts the row back to `open` with the correction
  appended to the note, while the rejected restatement stays on the record. The
  round is deliberately NOT blocking — a session acks and keeps working; the
  veto exists so a misunderstanding costs one click instead of a whole round.
- **The word bench now composes with the frozen Laufform variants — the
  measurement stand catches up to production (handmodell plan H0).** The
  fixture export freezes the `LAUFFORM_VARIANT` template rows (median running
  forms) as `templates_laufform.json` next to `templates.json`, the runner
  passes them into `compose_word` exactly like `/write/word` does
  (`--no-laufform` keeps a chart-only diagnostic run), and `tools/wordlab`
  (fixture and live path) composes identically so its overlays show what the
  bench scores. Documented re-baseline in `qualitaetsmetrik.md` §6: words
  0.1208 → 0.1169, pairs flat at 0.1645 — decomposed into the export shift
  (five words + one pair newly scorable through the authored capitals) and
  the Laufform effect proper (−0.0053 on words) (#256).
- **Open-core moat hardened: the learned dataset is no longer publicly
  exfiltrable.** The README has always reserved the authored data (ductus
  templates, running forms, statistics) outside the MIT grant; now the
  technical side matches: `GET /sources/{id}/templates/{glyph_key}` — the
  full authored row incl. the raw stylus path, used by no public surface —
  is admin-gated (the public list keeps serving geometry-free summaries),
  the design-sync preview data file that embedded real diagnostic payloads
  is untracked (local-only, regenerate against the local API), and
  `quellen-und-rechte.md` §5 documents the whole enforcement picture: bench
  fixtures stay gitignored, `/write` payloads remain deliberate product
  surface under the README reservation + crawler policy, the compose-golden
  parity fixture (11 rendered words, no templates) is the accepted known
  exception with a follow-up to regenerate it from synthetic templates, and
  a public dataset only ever ships as a deliberate goal-7 release (#254).
- **The Optimierungs-Werkbank direction and its binding stage/role doctrine,
  documented.** `docs/proposals/optimierungs-werkbank.md` records the
  2026-07-31 decisions (ONE admin workbench page — word spine + letter/pair
  context lenses + Auftragskorb; the Korb as a `work_items` table the AI reads
  per API) and, centrally, the doctrine that prevents misunderstandings on
  both sides of a fix task: manual input only where it creates ground truth
  (chart ductus, word re-tracing where the auto-fit fails, pair overrides as
  last resort), everything generated gets flagged rather than hand-patched, a
  Korb entry names where the problem was SEEN while the stage triage (chart →
  Laufform/fit → class rule → placement → override) is the AI's duty, with a
  fixed `resolution` format and a "Rückgabe an Autor" path for ground-truth
  gaps. Indexed in `docs/index.md`; CLAUDE.md and the Copilot twin point to it
  as mandatory reading before working off a work item (#253).
- **The Auftragskorb: filed optimization tasks instead of screenshots
  (Werkbank stage W1).** The admin's channel into a working session gets a
  backend: the new additive `work_items` table (migration `0020`) holds one
  row per marked element — `kind` names the level (`letter` | `pair` |
  `word`), the key columns name the element, `specimen_kind`/`specimen_id`
  name the words.json sample the issue was seen in (same namespace semantics
  as the occurrence rows), and `note` carries the observation. A working
  session lists the open items at round start, works them off and closes each
  with status `done` plus a `resolution` note (what changed, PR reference).
  All of it runs over the new admin-gated
  `GET/POST /sources/{id}/work-items` + `PATCH/DELETE …/{item_id}` — unlike
  the occurrence reads even the list is gated, because these are internal work
  notes, not measurement or public content. Filing validates that the target
  is actually workable (a letter item needs its glyph_key, a pair both sides,
  a word its text or specimen) and that the keys are registry glyphs. Nothing
  here affects rendering (#252).

### Fixed

- **Werkbank: the context lens and Auftragskorb now stay beside the word being
  inspected.** The sticky positioning sat on the lens card, whose parent column
  is content-sized — no room to travel, so clicking far down the word spine
  showed the lens only after scrolling back to the top. The whole right column
  now sticks against the tall spine track (scrolling internally when taller
  than the viewport; single-column layouts stay in flow) (#257).

## [0.20.0] — 2026-07-31 — Hand model: occurrence layer + Belege

### Changed

- **Admin Belege page (`/admin/belege`) — the stored word traces, browsable.**
  Every word-occurrence trace of the active source rendered over its specimen
  crop (public `GET /word-instances` joined with the word-samples metadata,
  registered via the row's stored registration), sorted worst-first: unfitted
  letters weigh heaviest, mean fit RMSE breaks ties — the error-finding surface
  over the new occurrence layer and the designated entry point for the coming
  word editor (manual `authored` re-tracing). Cards carry provenance
  (traced/authored), fitted-count, unfitted-letter and RMSE chips (per-letter
  values in the tooltip) plus a word filter; a sidebar icon links the page (#251).
- **Occurrence persistence: every clean specimen fit becomes a database row
  (hand-model plan H1/H2).** Per the decision to store occurrences, not just
  medians: the laufform harvest now persists each clean per-occurrence M4 fit
  as an `instances` row (centered shape anchors; placement, specimen/slot
  context, neighbours and RMSE in `measurements`) and the pairlab harvest can
  persist EVERY dissected letter join as a row in the new additive
  `pair_instances` table (migration `0019` — geometry in the `glyph_pairs`
  frame plus dissection QC, unique per `(source, kind, specimen, slot)` since
  the word plates and the Abb.-20 drills are separate id namespaces). The
  word level completes the training template: `word_instances` stores one
  traced word per specimen sample — slot labels plus the fitted letter
  strokes as a pen path in the word's registration frame, pairing with the
  specimen crop the word-samples endpoints already serve. Word traces carry
  provenance `traced`/`authored`: an authored row (the future manual admin
  trace — the training-set growth loop) is never overwritten or replace-wiped
  by a re-harvest, and `DELETE` spares it unless explicitly included. All
  three flow through new admin-gated batch endpoints
  (`PUT /sources/{id}/instances` + `/pair-instances` + `/word-instances`,
  public reads alongside) that get-or-create the writer's `hands` row — the
  first real inhabitants of the statistics layer defined in migration 0004.
  Occurrence rows never affect rendering; the composer path is untouched (#250).
- **The staged hand-model plan and the July specimen-source research, documented.**
  `docs/proposals/handmodell-stufenplan.md` consolidates the Laufform round into
  a staged proposal (H0–H5): confirm the role model (chart cell = ductus prior,
  the written words of exactly ONE hand = form model, foreign hands = context,
  never averaged), then fill the schema's empty statistics layer — persist the
  per-occurrence M4 fits into `instances`/`hands` instead of discarding them
  after the median, add per-pair join statistics for observed pairs, move
  measurable hand constants from `core/compose.py` into per-hand aggregates
  behind a simplification gate, prove hand-genericity on a second historical
  hand, and finish on the user's own hand ("any text, in my own hand" — vision
  goal 6, "in meiner Hand, aber jeden Text").
  `docs/notes/quellen-recherche-2026-07.md` preserves the source-research round
  (ranked committable finds, rejected items with license reasoning, possible
  archive requests recorded but not commissioned); `docs/index.md` indexes both
  and syncs the stale R3–R5 status line (#249).

## [0.19.0] — 2026-07-31 — Laufformen: the running hand's letterforms

### Added

- **Laufform variants: median running forms as a reserved templates
  variant.** The doctrine split settled with the author: the chart cell is the ductus prior
  (stroke order, crossings), the written specimen words are the form model.
  A new admin endpoint `PUT/DELETE /sources/{id}/templates/{key}/laufform`
  stores a per-letter median running form (validated one-to-one against the
  chart row's anchor topology; entry/exit/advance ride their end anchors),
  and `/write/word` renders it for glyphs in a flowing run (≥ 3, the
  ascender-lean gate) — solo payloads, the Tafel and short drills stay
  chart-true, and the per-letter width factor stays as fallback for letters
  without a stored form. `tools/laufform/harvest.py` derives the medians
  from the frozen word fixtures (M4 fit per occurrence, clean-fit guards)
  and writes drafts through the admin API. The experiment run measured
  words bench 0.1208 → 0.1136 with the median shapes; the headline moves
  only once the rows are written and the fixtures re-exported (documented
  re-baseline). Without variant rows every composition stays
  byte-identical (golden fixture untouched) (#246, #247).

### Changed

- **Capital handover: the join leaves the capital's WORKING exit, never its
  ornament.** Prompted by the user spotting that Soldaten's S→o kept a high
  covering line where the 1922 plate restarts at the baseline; measuring all
  22 joined capital→lowercase plate occurrences confirmed no capital ever
  hands over high. Crest and low-ending capitals (S/O/B/K/P) now depart at
  their last low body pass (local minimum at/below 0.55 x-heights) with the
  ornament fully drawn and retraced over its own ink; descender-loop
  capitals (G/Z) already took the fork join; mid enders (E/F/W/I/D) keep
  their true exit. The round-body top coupling is suppressed after any
  capital (contradicted by every plate case — round bodies are met on their
  rising flank with the lead-in intact), capital joins never garland (they
  rise monotonically on the plates) and get the plates' wider clearance.
  Words bench 0.121625 → 0.120793, pairs 0.169987 → **0.165297**, and the
  words Gleichzug audit is **completely clean for the first time** (0
  gaps, 0 doublings; pairs keep 6 in the parked d→descender class).
  Seiten 0.101 → 0.068, Silber 0.120 → 0.098, Säbel 0.165 → 0.115. Golden
  re-pinned (qualitaetsmetrik.md §6 „Kapital-Runde jul31") (#245).
- **Running-form width (Laufform): bound letters render at their measured
  running width.** M4-fitting all 257 letter occurrences of the specimen
  words onto the plates shows the running hand writes most letters 3–11%
  wider than their chart cells (e/r/h/l/ſ up to +11%) — the plates get
  their word width from wider letters with tighter gaps, the composer so
  far from chart-narrow letters with wider gaps (the root of the
  "stretched" impression). The target-based fluent body widening already
  covers the round bodies (its jul08 targets match the new medians
  independently); the new `LAUFFORM_SX` rule scales the remaining letters
  (i/l/h/n/r/w/ſ wider, t/d slightly narrower) in bound context only —
  solitary glyphs and the Tafel stay chart-true, like the ascender lean.
  Words bench 0.130253 → **0.121625** (largest single improvement since
  the garland round; 28 words improve, e.g. Gewehr −0.060, Einen −0.048),
  pairs 0.169987, Gleichzug zero line unchanged, gap-rhythm spread
  0.197 → 0.186. Golden re-pinned (qualitaetsmetrik.md §6
  „Laufform-Runde jul31") (#244).

### Fixed

- **Laufform rows move to reserved variant 100 — variant 1 belongs to the
  authored chart-form variants.** The live check after the first Laufform
  write-up found the collision: authored "A = A" teaching-chart variants
  already occupy variants 1..n (Sütterlin Q and ü carry 1+2), so
  `/write/word` had started rendering those authored alternatives as
  running forms in flowing words, and the Laufform upsert for `i` silently
  overwrote a pre-existing authored variant-1 row (its content needs a
  backup restore or re-authoring; Q/ü were untouched). The Laufform
  endpoint, the `/write/word` fetch and the harvest tool now use the
  reserved `LAUFFORM_VARIANT` (100), the 13 derived rows were migrated
  there and the 12 freshly-created variant-1 rows removed, and a
  regression test pins that an authored variant-1 row is never picked up
  as a running form (#247).

## [0.18.0] — 2026-07-31 — One-flow writing: six connection classes + Gleichzug audit

### Changed

- **A Gleichzug audit as wordbench report columns — the one-flow, one-width
  invariant made measurable.** A Sütterlin word is written in one flow (pen
  lifts only for diacritics) with a line that is always one nib wide; the new
  `tools/wordbench/gleichzug.py` detects the two violations on the composed
  centerline path alone — flow gaps (the pen teleports between items) and
  parallel doublings (two near-parallel stretches at a perpendicular offset
  between the retrace epsilon and ~1.35× the nib read as a double-width
  stroke, which a one-width nib cannot write). Retraces, transversal
  crossings and near-parallel pairs inside ONE letter (authored letterform)
  are classified out via the compose provenance tags. Report-only like the
  slant column (`flow gaps=… dbl=…` per entry, `gleichzug_*` totals per
  block), verified headline-neutral to the last byte; unit-tested. Current
  zero line after the join round: 0 gaps everywhere; after calibrating the
  doubling band against the user-approved renders (fully-merged runs below
  half a nib and short junction lobes are pen-authentic — the lower band
  edge scales with the nib, minimum event arc 0.25, parallel threshold 22°)
  the doubling worklist is 3 words / 17 pairs, concentrated in three known
  classes (capital joins, d into descenders, ſ into hanging bowls). The
  wordbench fixtures were also
  re-exported after the author completed the letter set — words 58/63
  scorable (only the five ß words remain), pairs 32/33, abb22 106/106; the
  new headlines (words 0.131392, pairs 0.182982) are a documented
  re-baseline, not comparable to the jul08-fixture numbers
  (qualitaetsmetrik.md §6) (#240, #241).
- **Fork joins for the long-s and the t/f bar — the two plate-measured
  stem-launch classes.** After a long-s the rising connector no longer
  climbs 0.08 x-heights BESIDE the stem (a sustained parallel track the
  plates never write — the Gleichzug audit's ſ shortlist): it rejoins the
  stem, retraces it to a fork at ~0.4 of the coupling height and swings
  out on a straight diagonal into a high coupling; hanging bowls place on
  the 45° line from the fork while c/t keep their calibrated run-down
  placement (overlay-verified plate-exact) and couple mid-flank. For t/f
  the second specimen measurement (all 8 joined occurrences) showed the
  plates end t's crossbar AT the stem (right of it: no ink — the long
  chart bar is table form) and leave the STEM on a shallow 16–27° rise
  into the next letter's apex: in bound context the rendered bar is cut
  at its own last ink crossing (word-final keeps the chart form) and the
  join is one straight rise, with placement on that line. Also fixes a
  latent shared-payload mutation (the stub/bar cuts edited cached stroke
  lists in place — a word-final t after any bound t lost its bar and
  Endstrich in cached-payload runs like the wordbench). Words bench
  0.130439 → 0.130253, pairs 0.174158 → 0.170674, Gleichzug doublings
  3 → 1 (words) / 17 → 9 (pairs); golden re-pinned
  (qualitaetsmetrik.md §6 „Gabel-Runde jul30") (#243).
- **Height-aware join kerning — ink at different heights may overlap columns
  like on the teaching plates.** The specimen gap measurement (every letter
  of all 58 Abb.-19 words re-fit independently onto its plate) showed the
  composed rhythm, not the total width, is what reads as stretched: the
  overall width ratio is 0.96 and the join-advance median ±0.00, but
  high-exit classes sat 0.13–0.36 x-heights wider than the plate (t/f bar,
  c/b/l/o arcs — the plate even slides the next letter's body under the
  t-bar) while baseline diagonals already matched. Joined placement now
  judges clearance per y-bin (the nine fusion-guard bins) between A's
  rightmost and B's leftmost band ink — bins where only one side has ink
  impose nothing, which is exactly the plates' tuck-under; the covering-arm
  exemption (r/p) collapses into it as a special case and backward bow exits
  (w/v) keep the scalar clearance. Words bench 0.131392 → 0.130439, pairs
  0.182982 → 0.174158, Gleichzug zero line unchanged (3/17), per-class
  advance error halved (c→h −0.26 → −0.13, b→e −0.28 → −0.14, l to 0.00);
  compose golden fixture deliberately re-pinned. The t/f bar class needs a
  fork join (retrace the own stroke, then fall) — measured on the plates for
  both the bar and the ſ ascent — and follows as its own round
  (qualitaetsmetrik.md §6 „Dehn-Runde Stufe 1") (#242).
- **A sketch-driven join round: six Sütterlin connection classes rebuilt
  toward "one flow, one nib width".** An annotated feedback loop (the user
  marking defects directly on rendered words) rebuilt the generated
  Übergänge in `core/compose.py`, each as a letter-CLASS rule, never a
  bigram: (1) a descender-loop exit (ſ) returns THROUGH the baseline and
  rides the next Anstrich letter's lead-in line up from the Grundlinie
  (class `{c, t}`; hanging bowls keep their direct coupling); (2) the
  Deckstrich arm (r/p) is classified exhaustively in the bow band — no
  crest-roll above the arm (the double-wave), and the covering arm no
  longer kerns the next letter away (arm-exempt clearance with a
  height-aware knob guard); (3) the arm FUSES onto the next letter's
  lead-in crest apex (round bodies + r + i, `ARM_FUSE_GAP` 0.02) — the bow
  rolls over in one motion, no parallel double-stroke; (4) same-slant
  sawtooth diagonals (e→n, i→n, …) couple as ONE straight through-line
  arriving high on the flank, placement untouched; (5) a bound loop-return
  letter (d, round s) no longer writes the chart cell's finishing stub at
  all — the return crosses the stem and continues in one motion into the
  next letter (word-final keeps the complete chart form plus a new
  level-launch late-rise loop finial); this supersedes the twice-rejected
  O3 stub trim, which fails only with a tip-anchored connector
  (qualitaetsmetrik.md §6); (6) every generated stroke now overlaps its
  neighbours' ink by `CONNECT_OVERLAP` under the round cap, closing the
  hairline white cracks at item handoffs. Wordbench: words
  0.123703 → 0.122287, pairs 0.191805 → 0.183317; compose golden re-pinned
  deliberately per stage (#239).

## [0.17.0] — 2026-07-28 — Fast public writes + crawler policy

### Changed

- **A written-down crawler policy — AI retrieval welcome, AI training declined.**
  Cloudflare answered every AI user agent with a hard `403` across the whole
  zone, `llms.txt` and `api.kurrentschrift.ink` included, so the file written
  for AI agents was unreachable to every agent it was written for — and
  user-directed fetches (`Claude-User`, `ChatGPT-User`, i.e. a human asking
  their assistant to open the page) were blocked along with the scrapers.
  `app/public/robots.txt` now carries the whole policy itself — the content
  signals incl. `ai-train=no` as the express reservation of rights under
  Art. 4 EU-DSM, the welcomed retrieval/citation agents, the declined training
  collectors — so it holds with Cloudflare's managed block turned off. The new
  `docs/reference/crawler-richtlinie.md` records the measurement, the decision,
  the dashboard steps that lift the block and the rejected alternatives;
  lifting it at the edge is a Cloudflare action, not a repo change (#232).
- **The SPA lint gate now enforces the React Compiler rules
  (`eslint-plugin-react-hooks` 5 → 7).** v7 folds the stabilised React Compiler
  rule set into `recommended`: 16 rules where v5 shipped two, of which **11 are
  enforced at error** — previously only `rules-of-hooks` was. Ten of the newly
  adopted error-level rules (`purity`, `immutability`,
  `preserve-manual-memoization`, `static-components`, `error-boundaries`,
  `set-state-in-render`, `globals`, `use-memo`, `config`, `gating`) are already
  clean on the tree, so the gate gets strictly stronger at no cost. The two
  that are not — `react-hooks/refs` (the latest-ref `ref.current = prop` write
  during render, 4 sites) and `react-hooks/set-state-in-effect` (the "reset
  transient state when the input prop changes" effects, 21 sites) — are
  configured as warnings rather than switched off, because clearing them is a
  behavioural refactor of `WrittenGlyph`/`WrittenWord`, the diagnostics dialogs
  and the admin compare views, tracked with every site listed in issue #227.
  `npm run lint` therefore
  reports 0 errors / 45 warnings (20 pre-existing `react-refresh` + the 25
  above); tests, build and `npm ci` are unaffected (#190).
- **Ruff no longer formats the Markdown docs.** Ruff 0.16 extends `ruff format`
  to Python code blocks inside Markdown, which reflows the illustrative
  snippets under `docs/` and in the tool READMEs — schema sketches,
  pseudo-code and column-aligned trailing comments whose alignment is the
  point. `*.md` therefore joins `[tool.ruff] exclude`; the formatter's scope
  stays the 128 Python files it always covered. Unblocks the ruff
  0.15.20 → 0.16.0 bump (#226).
- **Public `/write` endpoints: p95 latency ~1100 ms → ~100 ms (rendered
  geometry byte-identical).** A cProfile of a realistic workload (real
  120-anchor Sütterlin templates, mixed words up to the 160-char cap, gzip
  on) showed 74 % of request CPU re-rendering the SAME glyph payloads per
  request, dominated by per-segment Python-loop shapely buffers plus
  `union_all`, with FastAPI's `jsonable_encoder` walk and level-9 gzip on
  top. Four independent, output-preserving fixes: (1) `api/rendering.py`
  memoises `render_payload_for_template` per
  `(style, glyph_key, template id+updated_at, resolver, ratio, nib, pen)`
  with the same TTL + invalidation discipline as the pooled-nib cache
  (admin template writes clear the style's entries; callers copy before
  annotating — the shared payloads are never mutated, pinned by the golden
  parity fixture); (2) `core/template.py` builds the capsule/chisel
  silhouette geometries with shapely 2.x vectorized array calls instead of
  93k Python-level `buffer()` calls — bit-identical output verified against
  the previous implementation on all fixture glyphs plus randomized
  degenerate inputs (capsule 1.6×, chisel 3.5× faster); (3) the three write
  endpoints serialize straight through `orjson` (new runtime dependency),
  bypassing the `jsonable_encoder` walk over ~100k floats per response, and
  the write-path template fetches defer the unused `raw_path`/`measurements`
  JSONB columns (~100 KB per glyph off every request); (4) `GZipMiddleware`
  drops from the implicit compresslevel 9 to 6 (~3× faster on the large
  geometry bodies for ~1 % more bytes). In-process benchmark, 84 mixed
  requests: `/write/word` p95 1116 → 100 ms (max 217 ms), the 23-key
  `/write/glyphs` batch p95 1031 → 26 ms (#225).

### Fixed

- **Eraser mask correctly applies to inserted donor cells ("Patches").**
  Previously, when placing a second cell (Zelle einsetzen) into a crop via the
  admin wizard, the eraser tool (Ausschluss/Radierer) could not remove its ink
  because patches were composited *after* the eraser ran. The crop pipeline now
  composites patches before the eraser, matching the frontend's visual layering
  and allowing the eraser to clean up unwanted ink from donor cells (#238).
- **Robust `_rasterize_strokes` against malformed payloads.**
  The `core/chart.py` rasterizer now uses `isinstance` checks and `try...except` 
  blocks when parsing `mask_strokes` and `ink_strokes`. A malformed JSON row in 
  the database (e.g. flat integers instead of coordinate pairs) will now be 
  safely skipped instead of crashing the pipeline with a 500 error (#238).
- **Wizard gestures stranded by their own save — the eraser that kept
  painting and the Grundlinie that blocked the Weg.** Handing the preview
  over only once the commit lands (above) clears the gesture by identity,
  but nothing ended the POINTER's turn at pen-up: every pointer-move during
  the ~round trip replaced that same state with a new object, so the identity
  clear found a stranger and skipped. The gesture then lived forever — the
  red Ausschluss draft kept growing on plain hover moves and only vanished on
  the next press, and a leaked Grundlinie/Mittellinie drag survived the step
  change and swallowed every pointer sample on the Weg step (`if (calibDrag)`
  returns ahead of the trace branch), so the ductus could not be drawn at all
  and the stale value was committed on the next click. `WizardCanvas` now
  separates the two lifetimes explicitly (`gestureUtils.ts`): a pointer
  **grip** claimed at pen-down and released at the top of pointer-up, before
  the commit is awaited — so the preview still waits for its write while no
  sample can rewrite it. The grip also makes one pointer own the canvas (a
  palm resting beside the S-Pen no longer hijacks a stroke, and only the
  owning pointer's release commits), adds a `buttons === 0` backstop that
  finishes a gesture whose pointer-up never arrived, and a step change is now
  a hard gesture boundary (#231).
- **Admin writes answered with the state from *before* the write.** Every
  repository `upsert` writes through a Core insert-on-conflict the ORM session
  cannot see, then re-selects the row — and a plain re-select returns the
  instance already in the session's identity map, unrefreshed. Since the
  handlers load the row first (the bbox PUT's coalesce lookup, the `/trace`
  identity guard), every response carried the pre-write values. The setup
  wizard builds each next edit on the last response, so it re-sent a
  one-edit-old bbox: guide drags snapped back to their old position before
  jumping forward a round trip later, and every second eraser/ink stroke was
  silently dropped — erased neighbour ink reappeared as the crop "jumped back
  and forth". The three upserts (bbox, template, glyph pair) now re-select with
  `populate_existing` (#230).
- **Wizard gestures no longer snap back for the duration of their save.** The
  in-flight drag/stroke preview (Grundlinie, Mittellinie, Schräglage, donor
  cell, eraser and ink brush) was cleared *before* the PUT resolved, so the
  guide line or stroke rendered from the still-unsaved bbox for one round trip.
  The preview now hands over to the stored value only once the commit lands,
  cleared by gesture identity so a gesture started during the save survives (#230).

## [0.16.0] — 2026-07-20 — Writing-system redesign: one form per glyph + pair overrides

### Added

- **Admin pair matrix (`/admin/paare`, redesign R1).** Every two-letter
  combination of a chosen letter (capitals only on the left), composed
  server-side via the cacheable `/write/word` and rendered lazily per
  IntersectionObserver — an unnatural join is visible directly instead of
  hiding inside a longer word (#213).
- **Word-specimen comparison on `/admin/vergleich` (redesign R1b, stage 1).**
  The page now has tabs — Buchstaben (the existing per-letter view) plus
  Wörter/Verbindungen/Andere Hand: every connected-writing specimen from the
  source's `words.json` sidecar next to the same word written by the engine,
  side-by-side or with the engine ink overlaid on the specimen pixels,
  registered exactly over the sidecar lineature (baseline/midband → scale);
  unauthored letters surface as `missing` chips, the other-hand plate
  (Abb. 22) is labeled as view-only context (#213).
- **Public word-sample reads.** New `word_samples` router:
  `GET /sources/{id}/word-samples` (metadata with crop-local lineature) and
  `GET /sources/{id}/word-samples/{sample_id}/crop` (grayscale PNG, exclude
  rects painted paper-white), backed by `core/chart.py::load_word_samples` +
  `word_sample_crop_to_png_bytes` over the committed sidecar — public like
  the bbox crops (`<img>` cannot send the admin header), cached, covered by
  a new HTTP test suite (#213).
- **Writing-system redesign proposal (`docs/proposals/schreibsystem-redesign.md`).**
  Records the accepted direction from the 2026-07-17 review: one authored
  form per glyph with the position triplication removed (R2), an admin
  pair-matrix view over `/write/word` (R1), sparse *harvested* pair
  overrides with capital-joins first as the concrete form of proposal B
  (R3), placement-residual + O3 re-evaluation (R4), and a new measured
  slant finding — the specimen hand's d-ascender loop leans ~4–5° right
  of the upright chart cell while medians match (R5). Cross-referenced
  from `docs/index.md` and `planaenderungen.md` (proposals B and D) (#212).

### Changed

- **Straight-fit flank coupling for sawtooth letter pairs (the "ne" kink).**
  Between two mid-band diagonals whose entry foot sits at/below the previous
  exit (n→e and friends), no spacing can make the generated connector
  collinear — the taut cubic ran visibly flatter than both ink flanks (n→e
  chord −7° between 41°/39° tangents on the golden payloads), the kink the
  connected-writing review kept flagging. `core/compose.py` now solves the
  PAIR DISTANCE together with the coupling point, in two stages. Fusion
  (`_fused_flank_placement`): the join continues the stroke direction
  itself — the pair is pushed together until the line through the exit at
  the FULL mean ink tangent meets the rising lead-in flank, the connector
  degenerates to a short collinear piece and the stub below the coupling
  point is absorbed by the join (the O2 trim mechanism, silhouette
  included); since fusing stroke ends overlap in x by design, legitimacy is
  judged by a new height-aware per-y-bin clearance guard
  (`_fused_clearance_ok`) instead of the column ink floor. Fallback
  (`_flank_couple_steepest`): a rejected fusion places at the stub-relaxed
  column floor and couples the steepest reachable straight line instead of
  dipping below both flanks; connectors whose crossing already lies inside
  the couple-able window (a→n, g→e) degenerate to the exact straight middle
  piece at unchanged placement. On the golden payloads n→e goes from a −7°
  dipping cubic to a 39.9° straight between 41.2°/40.9° flanks — seam kinks
  −1.3°/+1.0°, one continuous diagonal. Guarded to the sawtooth class: both
  tangents inside `ALIGN_TAN_DEG`, coupling below `ALIGN_MAX_ENTRY_Y`, entry
  drop bounded by `FLANK_COUPLE_MAX_DROP` so the nested-fall letters (t's
  bar, f's flag) keep their bench-confirmed authentic S-join. Golden fixture
  deliberately re-pinned; the wordbench headline still needs a re-measure in
  a DB-connected session (qualitaetsmetrik.md §6) (#221).
- **Harvest importer for glyph-pair overrides (redesign R3 Erstbefüllung).**
  `tools/pairlab/harvest.py` dissects every adjacent joined pair in the frozen
  Abb.-20 pair fixtures (independent rigid fits + M4 ductus traces) and derives
  the `PairGeometry` the composer replays verbatim: placement offset from the
  rigid fits, connector centerline from the specimen's own joining stroke,
  baseline-locked so the stored path meets the composed entry
  (`connector[-1] == offset`). One best occurrence per pair with QC (fit
  residuals, gap ink, harvested vs generated chamfer); `--apply` PUTs
  unapproved `harvested` drafts through the admin API's validation and
  `--approve left:right` flags measured winners in the same upsert. The word
  bench gains `--overrides <harvest.json>` — an override run is its own
  measurement, never the headline; with only the four capital pairs B:i, I:n,
  D:u, O:f overridden, `pair_loss` falls 0.1918 → 0.1864 on the frozen
  fixtures (#220).
- **Slant report column in the word bench (redesign R5, stage 1).**
  `tools/wordbench/slant.py` implements the shear-search estimator from the
  redesign findings (−30°…+30° in 0.25° steps, maximum sum of squared column
  profile; 90° = upright, < 90 = right-leaning). Every scored row reports
  `slant <specimen>/<composed>` plus per-block medians; report-only —
  headlines and per-word losses verified byte-identical. On the frozen
  references it reproduces the d-loop finding: das 86.2°, der 87.2°,
  die 88.0° against a rigid ~90° engine (#220).
- **Composer placement: nested-fall class rule (redesign R4).** With the
  global advance bias gone, the pairlab residuals are class-shaped: rising
  mid-band exits whose neighbour enters below them (t's bar, f's flag, c's
  hook — no sawtooth pass-through possible) composed up to 0.34 xh too wide
  because their far-right ink pinned the clearance floor. On the plates the
  next letter nests under that ink: the ink floor now relaxes to
  `ALIGN_MIN_CLEARANCE` for exactly this class. Words bench 0.1185 → 0.1178,
  pairs unchanged. Re-evaluated and again rejected in the same loop: the
  ligature-remnant tuck and the O3 A-side d-stub trim — the latter with a
  sharpened diagnosis (the trimmed stub retraces the loop's crossing stretch,
  which carries real specimen ink; both headlines regress) (#220).
- **Bound d leans its ascender loop like the school hand (redesign R5,
  stage 2).** The measured d-Oberlängen-Schleife leans 4–5° right in
  connected writing while the chart cell stands upright. A bound d in a
  joined run of ≥ 3 letters now shears its above-midband part 4.5° right at
  render time — centerlines, silhouette rings and every downstream
  measurement consistently; the stored template stays the chart measurement,
  a solitary d and the isolated two-letter drills (measured upright) render
  chart-true. Bench-neutral within ruler noise; decided by the slant
  measurement and the das/der overlays. Extending the class to b/h/k was
  checked and not adopted (no measured lean). The compose golden fixture is
  deliberately re-pinned for this intentional output change (#220).
- **Pair cards link into the pair editor with the specimen as underlay.**
  Closing the redesign's R1b→R3 circle: every letter-pair card in the
  `/admin/vergleich` Verbindungen tab gets an "Im Paar-Editor öffnen" action
  that opens the pair editor for exactly that join, with the Abb.-20 specimen
  crop rendered as a semi-transparent, lineature-registered underlay in the
  drawing scene (baseline on y = 0, scale from the sidecar lineature; a
  "Vorlage unterlegen" toggle hides it) — the connector is drawn over the
  real pen's path instead of from memory. Saving an override invalidates
  that card's cached score; pairs that don't shape to exactly two slots
  offer no link. The shared `pairKeysOf` helper moved to its own module (#219).
- **Specimen scores in the admin word comparison (redesign R1b, stage 2).**
  New admin-gated endpoint `GET /sources/{id}/word-samples/{sample_id}/score`:
  it runs the frozen wordbench ruler on the same composition `/write/word`
  serves (shared `compose_word_payload`, approved pair overrides included)
  and returns loss/components plus per-letter/per-join segment attribution
  from compose provenance; a specimen with a missing template scores
  `failed`/1.0 (the bench crash rule). The `/admin/vergleich` word and pair
  tabs gain a "Scores berechnen & sortieren" action that fetches each card's
  score sequentially, shows a colour-coded loss chip (tooltip: the three
  worst segments) and sorts worst-first; the other-hand tab is deliberately
  never scored. To serve the metric from the API image (which ships no
  `tools/`), the ruler moved to `core/word_metric.py` — together with the
  exporter's specimen-reference pipeline and a per-sample skeleton cache —
  while `tools/wordbench/metric.py` remains as a re-export shim, so the
  bench's frozen import path and behaviour are unchanged (#217).
- **Pair editor + override badges (redesign R3, stage 2).** Clicking a cell
  in `/admin/paare` opens the new `PairEditorDialog`: both letters rendered
  at an adjustable coupling offset (right entry relative to left exit), the
  connector drawn directly with the pointer/stylus, an approval checkbox and
  a cache-busted live `/write/word` preview. Freehand saves are stored as
  `authored`; approving an untouched harvested row keeps its provenance and
  specimen citation. Matrix cells show green (approved) / orange (draft)
  override badges; ligature-folding cells (ch, ck, …) have no join and stay
  non-clickable. New client endpoints for `/pairs` CRUD (#216).
- **Glyph-pair override layer (redesign R3, stage 1).** New `glyph_pairs`
  table (migration `0018`): sparse per-pair overrides over the §4 join
  generator, carrying a connector centerline + placement offset relative to
  the left glyph's exit, with `provenance` (harvested/authored), a specimen
  reference and an `approved` gate. `core/compose.py` renders an approved
  override verbatim for exactly its adjacent pair (left-to-right precedence);
  with no override the generator path stays byte-identical (golden-pinned).
  `GET /sources/{id}/write/word` fetches the approved rows in one query;
  new public reads + admin-gated writes under `/sources/{id}/pairs/…` with
  registry-key and geometry validation. The harvest importer and the pair
  editor follow as the next slices (#215).
- **Position removal (redesign R2).** One authored form per glyph:
  glyph_keys lose their `-initial/-medial/-final` suffix (`a-medial` → `a`;
  the s-allographs untangle to `longs` — historically `s-medial` — and `s`),
  the admin fan-out/split machinery is gone, `templates.position` and
  `bboxes.split` are dropped and the identity constraint becomes
  `(style_id, glyph, variant)` (migration `0017`, which collapses sibling
  rows — a genuinely differing sibling survives as an extra `variant`, bbox
  locks are OR-merged). The word position stays per-slot render context in
  `core/shaping.py`/`shaping.ts`. Render output is unchanged: the compose
  golden fixture stays byte-identical in geometry (only key names moved).
  `architektur.md` §3 updated in the same change (#214).

## [0.15.0] — 2026-07-17 — Full-repo audit: hardening, tests, deploy gating

### Added

- **"Einen alten Brief entziffern" section on /schriftkunde.** A method-only
  five-step decipherment guide (anchors first, stock formulas, chart
  side-by-side, the classic f/ſ–n/u–e/n traps, skip-and-return) with a
  pointer to the Schreibtafel — the practical how-to the page's own intro
  audience was missing (#211).
- **Quiz provenance caption.** The quiz setup now names its source like the
  Tafel and Federprobe do ("Nachgebildet aus der gemeinfreien
  Sütterlin-Ausgangsschrift von 1922.") (#211).
- **Structured data + meta polish.** Static `WebSite`/`Person` JSON-LD in
  `index.html`, a `twitter:image:alt`, and `<lastmod>` on every sitemap entry (#211).
- **`docs/reference/werkzeuge.md`.** Human-facing entry point for
  glyphlab/wordlab/pairlab (exact CLI, `--live` read-only pulls, `temp/`
  output) with pointers to the bench and quizgen docs; indexed in
  `docs/index.md` (#211).
- **Admin `useInView` hook.** `/admin/vergleich` gates each card's heavy
  diagnostic fetch behind an IntersectionObserver and lazy-loads crop images
  instead of firing ~30 JSON requests on mount (#211).
- **HTTP tests for the admin compute endpoints + the untested public reads.**
  New `tests/test_api_compute_endpoints.py` (15 tests): `/trace-preview`
  (pressure raw/refined + the constant-style compute-once branch, dry-run
  proof), the full `/resample` 409/404/409/423 ladder incl. the legacy
  no-raw_path row, `/diagnostic` 404s + payload, `/quality` 409 without
  pixel meta + a real stored/candidate score, `/fit` 404, both chart image
  endpoints (PNG magic + cache headers), the single-glyph `/write` read,
  `/write/word` input bounds + the ligature-decompose fallback over HTTP,
  the new bbox geometry 422s, and the styles/sources/hands get-by-id 404s.
  `api/routers` coverage: templates 41→57 %, chart 47→84 %, write 61→67 % (#208).
- **Pooled nib/pen memoisation unit tests.** `tests/test_rendering_pool.py`
  pins the TTL cache the admin-trace→public-render coherence hangs on
  (hit, expiry, explicit invalidation, no-scan for constant styles) with a
  fake repository and a frozen clock — `api/rendering.py` 68→90 % (#208).
- **Guard against silent lab-test skip rot.** The glyphlab/wordlab/pairlab
  suites skip in CI on gitignored fixtures by design, so a renamed export
  dir would disable them forever without anyone noticing;
  `tests/test_lab_fixture_wiring.py` pins the consumers' fixture dirs to
  the exporters' output dirs and the shared manifest name (#208).
- **Vitest suite for the glyph lock/split helpers.** `domain/glyphs.test.ts`
  (10 tests) pins `siblingKeys` (incl. the s/ſ allograph overrides),
  `isLetterSplit`'s `.some` contract and `quizKeysFromLocked` (lock-as-one
  collapse, canonical-preferring representative, split units, punctuation
  exclusion, allograph separation) (#208).
- **Own-code deprecations now fail the test suite.** The deprecated
  `HTTP_422_UNPROCESSABLE_ENTITY` starlette constant (9 accumulated
  warnings) is renamed to `HTTP_422_UNPROCESSABLE_CONTENT` across the
  routers, and `filterwarnings` turns DeprecationWarnings raised from
  `api`/`core`/`tools` code into errors — third-party warnings stay
  warnings (#208).
- **`/verify-migrations` skill + a hardened CI migrations job.** The CI job now
  runs the full sequence — `alembic upgrade head`, `alembic check`
  (model↔migration autogenerate drift) and a `downgrade -1`/`upgrade head`
  roundtrip — against its throwaway Postgres 16; the new skill runs the exact
  same sequence locally (Docker or the container's unprivileged Postgres), so
  the shared Cloud SQL DB never sees an untested revision. This closes the
  Alembic entry in CLAUDE.md's "known gaps without a loop" (#204).
- **Post-deploy prod smoke.** `api/cloudbuild.yaml` ends with a smoke step
  against the freshly deployed revision: `/health`, `/styles` non-empty,
  `/write/word?text=lesen` returns items, and an uncredentialed write answers
  401 (fail-closed gate proven live) — a bad image that still answers /health
  can no longer ship silently (#204).
- **Frontend coverage reporting.** `npm run test -- --coverage`
  (`@vitest/coverage-v8`) uploads to Codecov under a new `frontend` flag
  (informational patch status to start); `app/` is no longer ignored in
  `codecov.yml`, so SPA regressions become visible to the patch gate (#204).
- **`REGEN_SHAPING=1` regen path for the shaping-twin fixture.** Mirrors the
  compose-golden pattern: a legitimate shaping change regenerates
  `tests/fixtures/shaping_cases.json` from the Python source of truth instead
  of hand-editing JSON that two suites assert (#204).
- **Pre-commit config.** `ruff-check` + `ruff-format` hooks (same versions CI
  pins), so format-only red CI runs stop happening; ESLint stays CI-only (#204).
- **`docs/reference/write-api.md`.** The shipped public render endpoints
  (`/write/glyphs` + `/write/word`) graduate from the proposal into a proper
  reference doc (pipeline, wire format, cache semantics, render-cache
  consumption), indexed in `docs/index.md` (#204).

### Changed

- **CORS is now environment-scoped.** Production allows only the
  `kurrentschrift.ink` origins; the localhost/LAN developer conveniences no
  longer apply to prod (where `allow_credentials` rides the CF Access
  cookie). An env override remains available (#211).
- **Template writes commit before invalidating the pooled-nib cache**, so a
  concurrent public read can no longer repopulate the 600 s TTL cache from
  pre-write state (#211).
- **Ligatures require both characters lowercase** in the shaping twins
  (Python + TS): `sT` / `McHale` no longer swallow capitals into
  `longst`/`ch` ligatures; pinned by new shared fixture cases (#211).
- **Wizard stroke capture stores relative timestamps.** Points now carry
  `performance.now() - traceEpoch` instead of a `t=0` first point followed
  by raw epoch values — saved traces become usable for the post-MVP
  velocity/style analysis (#211).
- **Quiz play/results panels use semantic headings and the type ladder.**
  Section titles are real `h2`/`h3`s in ladder variants (Playfair-600 rule);
  ad-hoc pixel sizes are mapped to the nearest rung, deliberate display
  figures are marked as such (#211).
- **Public copy audit fixes.** The Gleichzugfeder paragraph no longer calls
  the *pen* a school script; the 1915 timeline entry drops the four-year
  hedge; the Schriftkunde lead anakoluth is split; the Tafel intro says
  "Schreibvorlagen" instead of claiming "die drei Ausgangsschriften"; the
  hero caption is honest about being type, not the engine; the quiz SEO line
  no longer overclaims; the Federprobe page finally carries its own name as
  the h1; "kuratiert" jargon is replaced; the worksheet uses the DIN/Süß
  terms (Ober-/Mittel-/Unterlänge, "Mittellänge (Schreibhöhe)") instead of
  Band/x-Höhe (#211).
- **Impressum wording made defensible.** EU data-centre claim now names
  Google/Cloudflare as US providers certified under the EU-US Data Privacy
  Framework; the rights paragraph is reconciled with the 30-day server logs;
  date bumped to July 2026 (#211).
- **Quiz gloss corrections.** "Groschen" (era-scoped: 10-Pfennig piece only
  in the Kaiserreich) and "Witwe" (precise definition) fixed in the
  generator, the regenerated word bank, the bundled fallback bank, and
  in place via migration `0016_quiz_gloss_fixes` (#211).
- **The quiz is named "Lese-Quiz" in the UI too.** The six "Buchstaben-Quiz"
  strings (page title, hub/landing/Schriftkunde cards, SEO title) and the
  letters-only SEO/landing descriptions now match the shipped scope
  (letters + whole words), consistent with the docs rename below (#211).
- **Docs sync.** copilot-instructions' schema section now states both
  template unique constraints (the `(style_id, glyph_key, variant)` one
  shipped in 0015) instead of calling `glyph_key` UI-only;
  `write-api.md` documents the single-glyph read; the letter quiz is renamed
  to the shipped reading quiz (letters + words) across README/docs/guides;
  the two agent guides agree on read-first and language rules; implemented
  proposals are annotated in `docs/index.md`; README explains the
  Sütterlin-first validation order and lists `tools/`/`tests/` (#211).
- **Cloud Run request timeout lowered to 60 s** (from 600) — nothing
  legitimate runs ten minutes (#211).
- **Deploys go no-traffic → smoke → promote.** `api/cloudbuild.yaml` used to
  route 100 % of traffic and only then smoke — a bad revision served users
  until the build went red. The deploy now carries `--no-traffic` +
  `--tag=candidate` + a deterministic `--revision-suffix`, the smoke suite
  probes the candidate's tag URL (and asserts the tag still points at this
  build's revision), and a final `update-traffic --to-revisions` step promotes
  exactly the smoked revision — never a concurrent build's unsmoked one (#210).
- **The Tafel boots from the slim bbox read.** `BboxStatusOut` gains the six
  layout scalars (`x0/x1/y0/y1/baseline_y` + flags) the sheet layout needs,
  and `useGrundtafeln` switches from the full `BboxOut` list — the same
  multi-MB mask/ink/patch JSONB payload the quiz was weaned off in the last
  audit round — to `GET /bboxes/status`. The three chart scans (~1.4 MB of
  JPEG, two below the fold) now load lazily like the other public images (#210).
- **One version source for the API.** `api/main.py` read `0.2.0` while
  pyproject said `0.1.0` and the last release was 0.13.0; `/docs` now reads
  `project.version` from the shipped `pyproject.toml` (bumped to 0.13.0), and
  the release note covers the bump (#210).
- **pre-commit runs ruff through uv.** The mirror-based hooks pinned their own
  `rev` that Dependabot never bumps — pre-commit-green/CI-red was weeks away;
  the hooks are now `repo: local` `uv run --extra dev ruff …`, so uv.lock is
  the single ruff version source (#210).
- **Palette rgba literals replaced with `alpha(token, …)`.** The quiz panels
  and the Tafel sheet baked `paper.viridian`/`pigment.vermilion`/`paper.line`
  into rgba strings a palette retune would silently miss — `PublicHeader`'s
  bar background had in fact already drifted from a pre-retune `paper.bg`
  (rgb 231,221,193 vs the token's 231,218,191); all derive from the tokens now (#210).
- **Docs drift pass from the audit.** `animation-rendering.md` §1 now
  describes the SHIPPED engine — WAAPI via `useStrokeReveal`/`el.animate`
  with two-thirds-law keyframes and isochrony from `lib/strokeTiming`, not
  the "CSS keyframes, constant speed" it claimed — and its §3 sketch uses the
  real `width_resolver == "constant"` property and the `/write` payload path;
  the `/open-pr` skill learns CI's third job (migrations) and the
  `/verify-migrations` precondition; `CITATION.cff` catches up to release
  0.13.0/2026-07-09 and the CHANGELOG header makes the bump part of every
  release; `quiz-wortbank.md` states the real 75/25 modern/historic ratio
  (was 60/40); `docs/index.md` names the full library tuple
  `(style, glyph, position, variant)` and a current status line;
  `frontend-stack.md`'s route map stops claiming a live-written hero;
  `design-system.md`'s colour table gains the shipped `paper.viridianText`
  token + its usage rule; `planaenderungen.md` Vorschlag D gets a status
  note (core/shaping.py is the shipped precursor; the `glyphs` table is
  `templates` since 0004); `[Unreleased]` regrouped to one heading per
  category (#209).
- **CI frontend job on Node 22** (20 reached EOL 2026-04-30); `app` engines
  field now requires `>=22` (#204).
- **Docs and agent-surface refresh from the audit.** `.claude/commands/prime.md`
  rewritten from the current repo layout (it described the pre-library-schema
  world: `glyphs.py` router, `constants.ts`, `state.tsx`); `verify-api` skill
  aligned with reality (admin-gated `/fit`+`/quality`, four seeded sources,
  `/write/*` + `/quiz-words` + `/bboxes/status` in the sweep); `verify-core`
  drops stale test counts; `verify-frontend` drops the obsolete favicon-404
  gotcha and describes the render-cache quiz boot; `write-docs` matches the
  real `docs/index.md` structure (notes/ IS indexed, `schriftkunde/` exists);
  CLAUDE.md corrections (hero is font-first with an open engine seam,
  koch-1928 is a live seeded source, migration 0008 listed, known-gaps
  updated) mirrored to `.github/copilot-instructions.md` (CI = three jobs);
  `naming-und-setup.md` §1 reflects the Sütterlin pivot; `docs/index.md`
  prose sections list style-guide/design-system/federmodelle/qualitaetsmetrik;
  `frontend-stack.md` names `HeroWritten` and clarifies "keine eigene
  Komponenten-Bibliothek"; `animation-rendering.md` §1 describes the
  render-cache data path; `contributing.md` names the full live feature set;
  `sprachregelung.md` documents the EN-proposals exception (#204).
- **Public copy pass from the content audit.** /schriftkunde's intro no longer
  switches to Sie-form on an otherwise du-form site; German closing quotes are
  typographic („…“) everywhere; the hub/SEO texts stop promising trace-along
  words the worksheet generator doesn't produce and stop overclaiming the
  Tafel ("jeder Buchstabe, wie ihn die Feder schreibt" → only the Sütterlin is
  engine-written); the landing quiz card stops calling the Sütterlin-only quiz
  "Kurrent-Buchstaben" (and fixes "weist" → "zeigt"); quiz feedback "Super
  Übereinstimmung" → "Richtig gelesen."; quiz/tafel availability notes use the
  same wording (freigegeben instead of admin-jargon "kalibriert und gesperrt");
  the worksheet tool is consistently named "Übungsblatt" and the presets
  "Ausgangsschrift"; fact fixes against docs/schriftkunde: Sütterlin school
  introduction 1915 (Prussia) / ~1930 elsewhere instead of "1920er Jahre" and
  "Schulschrift von 1911", the Swiss phase-out 1890–1930 instead of "um 1900",
  the ß note now attributes the ſ+s reading to the Antiqua tradition, the
  1915/1918 timeline entry carries the divergent-sources caveat, and Kurrent is
  "die alte Alltagsschrift, ohne einheitliche Norm" instead of "die ältere
  Norm"; grammar fixes ("Das Schreiben lernte man …", "niederschrieben");
  the static `<title>`/description in `index.html` now match the SEO catalogue
  (full home title for no-JS crawlers, description trimmed to ~155 chars) (#202).
- **`/fit` and `/quality` are admin-gated; the crop endpoint leaves the event
  loop.** Both diagnostics cost seconds of pure CPU per call and back
  admin-only workflows, so they now require the admin credential like the
  writes (the SPA already sends it on every request); `GET /crop` runs its
  chart decode + binarisation in the threadpool like the other CPU-bound
  endpoints instead of freezing concurrent public requests (#201).
- **Admin locale namespaces left the public bundle.** The `admin`/`wizard`
  message catalogs moved from the shared locales barrel into a new
  `@/locales/admin` superset barrel imported only by admin code — ~24 kB of
  admin-only German strings no longer ship to every visitor (locales chunk
  51.7 → 45.5 kB gzip) (#201).
- **Boot states keep the navigation, and the cold-start copy speaks German,
  not ops.** The quiz and Tafel cold-start/loading/error states render inside
  the public layout (header + footer stay usable through the ~47 s worst
  case), and the boot message now says the server is waking up instead of
  "Cold Start" (#201).
- **Accessibility polish on the public pages.** The quiz verdict line is an
  `aria-live` region and focus moves to "Weiter" after a wrong answer (the
  disabled answer buttons used to drop focus on `<body>`); landing cards and
  header nav links gained visible `:focus-visible` outlines; the Federprobe
  disclaimer switched from the too-light `sepiaFaint` to readable `sepia`; the
  404 page sets its own title (#201).
- **Portable JSON column type.** Model columns now declare
  `JSON().with_variant(JSONB, "postgresql")` — identical behaviour on
  Postgres, creatable on SQLite for the new API test harness; migrations keep
  their own explicit JSONB types (#201).
- **Docs refreshed to current reality.** The agent guides
  (`copilot-instructions`, `CLAUDE.md`) now describe the live two-service
  Cloud Run deployment, the CI-gated Vitest suite and the full UI inventory
  (`inkReveal`, `InfoHint`, `tafel/`, `impressum/`, `/admin/vergleich`);
  `frontend-stack.md` §2/§7 carry the real route map (three areas, hubs,
  `/federprobe`, `/tafel`) with planned P1+ routes split out; the README's
  "what you can use today" covers Schriftkunde, Tafel and Federprobe;
  `style-guide.md` §3 states the 19/17/14 px type floor;
  `sprachregelung.md` documents the English `contributing.md` exception;
  `mvp-roadmap`/`architektur` §16/`qualitaetsmetrik`/`docs/index` status
  lines corrected (#201).
- **Deduped shared geometry/payload helpers and decomposed the oversized `core/`
  functions (no behaviour change).** The two canonical derivations now share one
  `_assemble_canonical_payload` (+ `_serialize_raw_path`) in `core/pipeline.py`
  instead of ~45 near-verbatim lines each — the pixel→template normalisation,
  entry/exit tangents, raw-path pen-lift serialization and the wire dict live
  once; the per-script differences (`method`, the Sütterlin `nib_radius_px`/
  `smooth`/`vertical` keys and the snap/refine notes) ride in one `method` string
  plus an `extra_trace_meta` dict. `bilinear` moved from `core/fit.py` to
  `core/geometry.py`, so `core/quality.py` and `core/quality_suetterlin.py` sample
  the shared field without importing the heavy `fit` module; `suetterlin`'s
  `_unit_tangents` now reuses `geometry.unit_tangents` and `compose`'s `_median`
  reuses `statistics.median`. The multi-closure giants are stage-extracted into
  named module-level helpers: `compose_word`'s pen/Endstrich/connector geometry
  became `_apply_pen`/`_endstrike_centerline`/`_connector_centerline`, and
  `fit_template_to_instance`'s objective/energy closures became an `_InstanceFit`
  dataclass mirroring the existing `_RefineRound` idiom. The compose golden fixture
  stays byte-identical and the full core suite is unchanged (#200).
- **Unified the "as written" ink-reveal across the three surfaces into a shared
  primitive.** `WrittenGlyph`, `WrittenWord` and `WrittenSheet` each
  reimplemented the identical SVG reveal technique (y-negated centerline paths,
  the `feTurbulence`/`feDisplacementMap` ink-bleed filter, the swept
  `stroke-dashoffset` mask, the iron-gall settle, the faint baseline/midband
  guides, the replay button). That lives once now in
  `app/src/components/inkReveal` (`InkBleedFilter` · `RevealMask` · `InkGuides` ·
  `ReplayButton` · `inkGroupSx` settle helper); the y-negating polyline path
  moved to `lib/svg.ts` (`polylineToPathD`, replacing the three per-file
  `pathD`/`lineD` copies); and the timing magic numbers moved to
  `lib/strokeTiming.ts` as named, justified defaults plus one shared
  `sequenceReveal` cursor walk — reconciling the drifted pen-lift pause (was
  110/130/150 ms across siblings → one `PEN_PAUSE_MS = 130`). The three surfaces
  are now thin consumers. No SVG/filter/timing behaviour change beyond that pause
  reconciliation (#199).
- **Folded `WrittenWord`'s private `/write/word` cache into `renderCache.ts`.**
  The composed-word FIFO cache lived in a second module-level `Map` inside
  `WrittenWord` with its own key scheme, undermining the "ONE shared render
  cache" invariant. It is now `fetchRenderWord` alongside the glyph cache
  (same key helper, same cold-start retry, same evict-on-error) — no private
  render cache remains outside `renderCache.ts` (#199).
- **Trimmed `app/src/domain/shaping.ts` to the quiz-gating subset.** With word
  composition living server-side (`core/compose.py`), the TS shaper only needs the
  `text → glyph_keys` mapping the quiz word-bank gating consumes (`shapeText` +
  `glyphKeysOf`). Dropped the now-dead exports `decomposeLigatureSlot` and
  `stripFugen`, and made `shapeWord`/`FUGE` module-private; the header note now
  states the reduced scope and points at the shared fixture that keeps the mapping
  in sync with `core/shaping.py`. No runtime behaviour change (the quiz imports are
  untouched) (#198).
- **API helper consolidation (no behaviour change).** Collapsed copy-pasted `api/`
  boilerplate onto single sources of truth: `resolve_render_context(source, db)` in
  `api/rendering.py` now resolves the style + source-pooled nib/pen for every write and
  template render path, so the "constant nib if constant else None" branch lives in one
  place; `Bbox.to_pipeline_dict()` is the ONE crop-affecting serializer consumed by the
  crop preview, the trace/resample/diagnostic derivation and the bbox read response (a
  new crop-affecting field can no longer be added to one and dropped from the others);
  `put_bbox` loads the stored row once and coalesces the optional fields via one
  `_coalesce` helper; `CACHE_CONTROL` moved to a shared `api/http.py`; the `n_anchors`
  bound is one `NAnchors` annotated type and `QuizWordOut.era` is a
  `Literal["modern", "historic"]`; `GET /styles` fetches all sources in one query and
  groups in Python (no more per-style N+1, chart `.exists()` memoised); and the router
  `HTTPException`s use named `status.*` constants. Response shapes are unchanged (#197).

### Removed

- **Orphaned design artifacts in `docs/reference/`.** The pre-design-system
  landing mockup `kurrentschrift-landing.html` (Google-Fonts era, referenced
  by nothing) and the duplicate `gl-germancursive.woff2` (the live copy is
  `app/src/assets/fonts/`) are gone (#209).
- **Unused runtime dependencies `cairosvg` and `python-multipart`.** Neither is
  referenced anywhere in the codebase; both (plus cairosvg's native transitive
  chain) leave the Cloud Run image (#201).

### Fixed

- **Cross-source render-cache poisoning.** `WrittenGlyph` seeded admin
  payloads from the runtime-switched active source under the *public*
  source's cache keys, so after a source switch in the admin, `/quiz` and
  `/tafel` could serve the wrong script in the same SPA session. The
  component now takes a `sourceId` prop used for peek/seed/fetch alike,
  threaded from all three admin surfaces (#211).
- **Quiz word bank no longer degrades silently on cold start.** The boot
  read now retries like its siblings instead of falling back to the small
  bundled bank for the whole session after one failed fetch (#211).
- **Out-of-chart bboxes are rejected (422)** instead of storing a box that
  later 500s the public `/crop` with a zero-size crop (#211).
- **DELETE /templates and /bboxes return 404 for nonexistent rows** instead
  of a false 204 on a typo'd glyph key (#211).
- **Error details no longer leak internals.** The public chart 404 hid the
  absolute container path and the style-resolution 500 its referential
  detail; specifics now go to the server log (#211).
- **`/hands` responses carry the shared Cache-Control** like styles/sources (#211).
- **`/fit` query params are bounded**; `require_db`'s 503 distinguishes
  "not configured" from "initialisation failed" (#211).
- **Quiz results word render falls back to plain type on error** instead of
  spinning forever after a cache eviction + failed refetch (#211).
- **`/diagnostic` is admin-gated like its compute siblings.** The 3-column
  diagnostic re-runs the image pipeline (chart decode + binarise +
  skeletonise, ~0.2 s CPU) per request; `/fit` and `/quality` were gated for
  exactly that reason but `/diagnostic` stayed public and uncached on the
  max-instances=1 service. Only admin surfaces consume it — the public
  renderer reads the cached `/write` payloads. The admin-gate HTTP test
  matrix now includes it (#207).
- **Structural uniqueness for `glyph_key`.** Every template read — including
  the public `/write` endpoints — keys on `glyph_key` via
  `scalar_one_or_none()`, so two rows sharing `(style, glyph_key, variant)`
  would turn every read into a 500; the API's 409 backstops are
  read-then-write and bypassable out of band. Migration 0015 adds the unique
  constraint (mirrored in the model), making the backstops UX instead of the
  only defense (#207).
- **Bbox saves reject degenerate rectangles.** `PUT /bboxes/{key}` accepted
  inverted or negative rectangles (`x1 <= x0`, `y1 <= y0`), which stored fine
  and then 500ed the public crop/derivation paths on an empty crop; the
  handler now 422s with a clear message, alongside the existing
  baseline/midband check (#207).
- **Cross-source pen-pool invalidation.** A style can pool from several chart
  sources (Kurrent: loth-1866 + petzendorfer-1889); a trace/resample/delete
  issued through source A that touches a template whose provenance is B left
  B's pooled nib/pen stale for the 10-minute TTL. Template writes now clear
  the whole style's pools (they are tiny), with a unit test pinning it (#207).
- **Cache-Control on the remaining public reads.** `GET /bboxes/status` (the
  quiz boot) and the crop PNGs (quiz prompt fallback; the wizard busts via
  its version param) now carry the shared public cache header; `GET
  /templates` deliberately stays uncached — the admin sidebar reads the same
  list and needs a fresh `has_data` right after a trace, and the code now
  says so (#207).
- **Fact-checked public copy, with the fact sheets updated to match.** A
  research pass with primary sources settled the audit's content findings:
  the Schriftkunde chronology note claimed the Swiss cantons dropped Kurrent
  "um 1900" while the geography section of the same page (correctly, per the
  cited ZB Zürich source) says 1890–1930 — the note now matches. The 1941
  passage attributes the "foreigners can't read it" justification precisely
  (Lammers, Chef der Reichskanzlei, forwarding note of 13 Jan 1941) and the
  fact sheets now name Bormann's party-office circular (3 Jan), Lammers'
  forwarding (13 Jan) and the Reich education ministry's school decree
  (1 Sept) with sources. The Gleichzugfeder blurb no longer claims Sütterlin
  "setzte sich in den 1920er Jahren durch" (Prussia from 1915, most Länder
  only around 1930). The Sütterlin-never-in-Switzerland claim is now backed
  by a direct ZB Zürich quote in the fact sheet, and the Swiss 1890–1930
  range gained an academic reference (Boser/Hofmann 2019) (#206).
- **Quiz gloss for "Gulden": silver, not gold.** The 19th-century South
  German Gulden was a silver coin (only the name derives from the medieval
  gold "guldin"); the generator source, `quiz_words.json` and — via new
  migration 0014 — the already-seeded DB row now read "alte Silbermünze
  (süddeutsche Währung)" (#206).
- **Impressum/llms.txt no longer overclaim synthesis.** "Alle gezeigten
  Schriftzüge sind … kein historisches Original" contradicted the
  Schreibtafel's genuine public-domain scans and the Koch 1928 original on
  /schriftkunde; both texts now distinguish synthesized forms (marked as
  such) from the PD originals shown with provenance. The privacy section's
  "keine personenbezogenen Daten" now carves out the 30-day server logs the
  same page already discloses (IPs are personal data) (#206).
- **Copy polish across the public pages.** Landing no longer claims all
  three scripts are engine-written ("die Sütterlin schreibt hier schon");
  the Federprobe card invites a word *or short sentence* (the input takes
  48 chars); "↻ noch einmal schreiben" matches the other replay labels;
  the worksheet intro gains its missing article; the written-glyph aria
  label says "alte Schreibschrift" instead of naming Kurrent while the
  engine writes Sütterlin; trailing ellipses uniformly get their narrow
  space; the Schwellzug explainer no longer has the *pen* swelling; the
  show-script font is consistently "GL-GermanCursive"; the sources intro
  points readers to the GitHub fact sheets (#206).
- **Straight-quote pairing spans the whole text, not one word.** The shaping
  twins (`core/shaping.py` + `app/src/domain/shaping.ts`) reset the
  low/high quote parity per whitespace-split word, so a multi-word quote —
  `"Guten Tag"` in the Federprobe — rendered two opening „ quotes. The parity
  now threads through `shape_text`/`shapeText`; the shared fixture gained the
  multi-word case and was regenerated via `REGEN_SHAPING=1` (#205).
- **Quiz word prompt no longer spins forever on a failed compose.** The word
  branch of the question card passed no `onError` to `WrittenWord`, so a
  compose request that died mid-cold-start (the render cache's retry budget is
  much shorter than the boot loads') left an infinite `CircularProgress`. The
  prompt now offers the same retry affordance as the Federprobe — a plain-type
  fallback would hand the solution to the learner, so it retries instead; the
  post-answer comparison forms fall back to plain type (#205).
- **Quiz keyboard focus survives a correct answer.** Focus moved to "Weiter"
  only on a wrong pick; on a correct one every answer button disables and focus
  fell to `<body>` — reduced-motion users got a "Weiter" button that never
  received focus, everyone else lost their tab position each auto-advance. The
  advance control now receives focus on every verdict, and after the advance
  focus returns to the answer grid (#205).
- **`quiz_words.created_at` is NOT NULL like every other `created_at`.**
  Migration 0010 forgot `nullable=False` (0004 declares it on all other
  tables) while the model implies NOT NULL — the very first `alembic check`
  run caught the drift; migration 0013 tightens the column (safe: it carries
  `server_default=now()`) (#204).
- **Slim public reads for the heavy list payloads.** New
  `GET /sources/{id}/bboxes/status` returns only the availability flags
  (glyph_key, locked, split) and `TemplateRepository.list_summaries()` feeds
  the template list from a column-select — the admin sidebar and the public
  quiz no longer decode multi-MB of `raw_path`/`anchors`/mask/ink/patch JSONB
  for six scalar fields. The quiz left the pinned AdminProvider entirely: a
  new `useQuizSource` hook boots from source + template summaries + status
  flags (same cold-start retry), so `/quiz` stops downloading the full
  crop-editing bbox payload (#202).
- **jsx-a11y lint gate.** `eslint-plugin-jsx-a11y` (recommended rules) now runs
  in the frontend lint, so the mechanical accessibility slips on the SVG-heavy
  custom surfaces get caught before review (#202).
- **`PaperCardLink` + `PaperCardCta`.** The public "paper card that is a link"
  (hover/focus lift, viridian border, focus ring, CTA underline sweep) that
  LandingView, HubView and the Schriftkunde try-cards each copy-pasted is now
  one shared component — contrast and focus fixes land once (#202).
- **Authorized admin-write and Cloudflare-Access test suites.** New
  `tests/test_api_admin_writes.py` exercises the gated handlers with a CORRECT
  token: bbox PUT/GET roundtrip incl. the coalesce contract (omitted
  `locked`/`n_anchors` preserve stored values), the full `/trace` pipeline
  against the on-disk synthetic chart (persisted template, list `has_data`,
  bbox anchor-count sync), the 423 lock + `force` override, and DELETE
  semantics for bboxes and templates. New `tests/test_api_auth.py` covers the
  JWT branch that actually gates prod: listed email → authorized, unlisted →
  hard 403 (no token fallback), unverifiable JWT → break-glass token path, plus
  unit tests of `_verify_cf_access_jwt` (lowercasing, PyJWTError → None,
  missing email claim, unconfigured). The shared ASGI harness moved from
  `test_api_http.py` into `tests/api_harness.py` + a conftest `api` fixture so
  all three API suites reuse it (#202).
- **HTTP-level API test suite + an Alembic migration check in CI.** New
  `tests/test_api_http.py` runs the FastAPI app under pytest against an
  in-memory aiosqlite session (dependency-overridden `get_db`, no
  Postgres/network): the admin gate (401 on missing/wrong token, fail-closed
  503 when unconfigured) is asserted for every write endpoint incl. the newly
  gated `/fit` + `/quality`, plus Cache-Control on the public reads and
  `/write/glyphs` + `/write/word` end-to-end with synthetically seeded
  templates. A new `migrations` CI job runs `alembic upgrade head` (schema +
  seeds) against a throwaway Postgres 16 service on every PR, so a broken
  revision can no longer reach the shared Cloud SQL instance. Vitest gains
  `renderCache.test.ts` (request batching, in-flight dedupe, cache hits,
  missing-as-null, error eviction, cold-start retry) (#201).
- **Brand icons + social preview image.** `favicon.ico` (multi-size),
  `apple-touch-icon.png` and a 1200×630 `og.png` — the viridian Kurrent K on
  the paper gradient, rendered from the bundled GLKurrent face — wired into
  `index.html` with a `summary_large_image` twitter card; link previews and
  browser tabs stop being generic (#201).
- **Shareable Federprobe.** The typed text syncs to a `?text=` URL parameter
  (debounced, history-friendly) with a "Link kopieren" button and a character
  counter on the input — the page's output is now deep-linkable (#201).
- **"Jetzt ausprobieren" cross-links on `/schriftkunde`.** The primer closes
  with hub-style cards into the quiz, the Schreibtafel and the Federprobe
  instead of dead-ending after the chronology (#201).
- **Chart image LRU cache + Cache-Control on stable reads.** Decoded chart
  grayscale arrays are cached per resolved path (read-only, max 4 entries), so
  repeated crops/diagnostics/fits stop re-decoding the same immutable PD scan;
  `/styles` and `/sources` responses now carry the shared cache policy and the
  chart image caches for a day (#201).
- **Direct unit tests for the pure-math core modules + a mechanical shaping twin
  guard.** New `tests/test_geometry.py` and `tests/test_widths.py` pin the
  deterministic numeric helpers in `core/geometry.py` (tangents, arc length,
  curvature, straightness residual, TLS line fit, vertical-run/crossing/retrace
  detectors) and `core/widths.py` (the `BroadNib` law + vectors, per-stroke
  tangents, every `resolve_half_widths` branch) with known inputs/outputs, so the
  upcoming core-dedup refactor has a behavioural net; `_locally_straight_mask`
  gains direct coverage in `tests/test_quality_components.py`. The
  `core/shaping.py` ↔ `app/src/domain/shaping.ts` twin is now enforced by a shared
  fixture (`tests/fixtures/shaping_cases.json`, generated from the Python source of
  truth) asserted by both `tests/test_tri_script.py` and a new Vitest test
  (`app/src/domain/shaping.test.ts`) — mutating one shaping without the other fails
  CI. Wires a `test` script + `vitest` into `app/` and a Vitest step into the
  frontend CI job (build-only before) (#198).
- **WCAG AA contrast for viridian text and the quiz answered state.** New
  `paper.viridianText` (#2e6152 — derived for contrast, not a period hex;
  5.15:1 on the paper ground vs 3.28:1 for the accent #40826d) is used
  wherever viridian is body-size text: card CTAs, the hub/landing links, the
  quiz score and verdict, the Scribe copy confirmation, Tafel chip/provenance
  links, prose-link hovers. `quiz.resolvedText` darkened to #6e5c42 (5.5:1 on
  the answered button face, was 3.61:1). The accent #40826d stays for large
  display, initials, borders, fills and focus rings (#202).
- **Contiguous heading outline on every public page.** Card titles now carry
  explicit heading components (hub cards `h2` under the page `h1`; landing,
  Schriftkunde and Tafel cards `h3` under their `h2` section headings), and
  MUI's default subtitle→`<h6>` mapping is overridden to `<p>` at the theme
  level — definition-row terms and timeline years no longer appear as phantom
  section headings to screen readers (#202).
- **The nav marks the current area.** PublicHeader links carry
  `aria-current="page"` plus a visible active state (ink colour + full
  viridian underline) for the area whose page is open (#202).
- **`/trace` can no longer cross-link template rows.** The template upsert
  conflicts on `(style, glyph, position, variant)` while reads go by
  `glyph_key`, so a client bug pairing a wrong URL key with a payload identity
  could conflict-update another row and rewrite its `glyph_key` — reads then
  silently 404 on the shared prod DB. `POST /trace` now derives the expected
  key from the shared registry (`core.shaping.expected_glyph_key`, the Python
  twin of `glyphs.ts`; `{base}-{position}` convention as fallback) and rejects
  a mismatch with 422 (#202).
- **DB engine init race closed.** The lazy `asyncio.Lock` getter in
  `core/database/connection.py` was itself check-then-set, so two first
  requests could each mint their own lock, both enter `init_db()`, and the
  loser's engine (and Cloud SQL connector) leaked without `dispose()`. The
  lock is now created at import; the dead `_sync_init_lock` is gone (#202).
- **No more raw English error strings on public pages.** `/quiz` and `/tafel`
  showed `String(e)` (e.g. "TypeError: Failed to fetch") as the BootStatus
  detail under a German title; both now show a fixed German sentence
  (`common.boot.sourceUnreachableDetail`) and log the exception to the console (#202).
- **A late word-compose rejection can no longer evict a fresh cache entry.**
  `fetchRenderWord`'s error eviction now checks entry identity before deleting
  (like the glyph cache): after a FIFO eviction + re-fetch under the same key,
  the old promise's rejection used to delete the new, valid entry (#202).
- **The nav's current-area marker covers the standalone tool routes.** /quiz
  and /tafel light up Lesen, /federprobe lights up Schreiben (they keep their
  stable top-level URLs and are not nested under the hubs); only the exactly
  matching page uses `aria-current="page"`, area membership uses `"true"` (#202).
- **CHANGELOG `[Unreleased]` consolidated to one heading per category.**
  Successive PR insertions had produced duplicate Added/Changed/Fixed headings
  with bullets filed under the wrong category; regrouped per Keep-a-Changelog (#202).
- **The Cloud SQL connector fallback is now truly async.** The
  `INSTANCE_CONNECTION_NAME` path built a *sync* pg8000 engine and handed it to
  `async_sessionmaker(..., class_=AsyncSession)` — the first session would have
  raised `ArgumentError` and `close_db` would have crashed on `await
  engine.dispose()`; it now uses the native async Cloud SQL Connector with an
  asyncpg `async_creator`. A failing lazy `init_db()` in the session dependency
  is also caught and surfaces as the clean 503 instead of an unhandled 500 (#201).
- **Wizard brush commits can no longer overwrite each other.** All bbox writes
  are serialized through one queue and compute their payload from the
  then-current bbox at write time — two quick eraser/ink strokes (S-Pen taps
  faster than the PUT round-trip) used to both build on the same stale state,
  silently dropping the first stroke. Bbox saves also stopped echoing a stale
  `n_anchors` back, which used to revert the server-side sync with the derived
  canonical (`_sync_bbox_anchor_count`); and the canvas renders committed
  strokes/patches/saved-trace through memoised layers, so a 240 Hz pen gesture
  only re-renders the in-flight stroke (#201).
- **Federprobe and Schreibtafel fail loudly instead of silently.** A failed
  compose fetch on `/federprobe` now shows an error message with a retry button
  instead of an endless spinner, and a failed letter batch on the Tafel shows a
  notice + retry instead of silently rendering an empty ruled sheet (#201).
- **Mask preview halves its binarisation work.** The "Maske zeigen" preview
  derives the filled mask from the already-thresholded raw mask via
  `fill_small_holes` instead of running the adaptive threshold twice
  (identical output) (#201).

## [0.14.0] — 2026-07-13 — Specimen-true joins + compose calibration

### Changed

- **Pairlab-calibrated placement (O1).** `core/compose.py` places letters with two
  measured corrections: a HIGH exit is treated as a coupling-stub tip, not the pen's
  true departure — the next letter tucks back under it proportionally to the exit
  height (`TUCK_RATE`·(exit − 0.6)⁺; the d-class needed −0.33 xh) — and a BACKWARD
  exit tangent (the w/v bow) gets `BACKWARD_INK_CLEARANCE` 0.30 instead of 0.14 (the
  join must clear the whole bow; w joins measured +0.23 xh too tight). Re-measured
  against the pairlab independent fits over all 48 scorable specimen words: joins
  needing ≥ 0.25 xh correction drop from 31 to 21 of 146 (d-class −0.33 → −0.07,
  w-class +0.23 → +0.08 median) (#179).
- **Coupling anchors for high-exit joins (O2, B side).** After a Deckstrich bow,
  d-loop or r-arm exit (≥ 0.7 xh) the generated connector no longer bridges to the
  next letter's entry-stub foot ("shelf") but falls onto the RISING flank of its
  first downstroke at y 0.78, and the chart cell's stub piece below the anchor is
  removed from the centerline and the filled silhouette (new
  `core/template.py::erase_silhouette_piece`). Word-initial stubs stay — they are
  the Anstrich; low arcade joins are untouched (the standard diagonal is generically
  right per the pairlab findings) (#179).
- **Level Auslauf for high word-final exits.** A word ending on a high forward exit
  (the r-arm) now runs a short level finishing stroke (0.25 xh) like the plates,
  instead of stopping dead at the arm end — `der`/`der-2` carried the bench's
  largest width penalties for the missing stroke. Words ending low keep their
  rising Endstrich (#179).
- **Word bench headline** 0.1253 → 0.1183 (−5.6 %) over the frozen `jul08`
  references; `pair_loss` (report-only) 0.199 → 0.195. Loop protocol, keeps,
  discards (incl. the measured-but-rejected A-side d-stub trim) in
  `docs/reference/qualitaetsmetrik.md` §6, Lauf `jul11`; the compose golden fixture
  is deliberately re-pinned (#179).
- **Doc & instruction-sync hygiene.** Re-aligned `.github/copilot-instructions.md`
  with `CLAUDE.md`: corrected the stale "no tests exist yet", "ruff/ESLint when
  configured" and "no automated AI workflows configured" claims (a pytest suite,
  ruff, and `.github/workflows/ci.yml` all exist); fixed the dead `app/src/constants.ts`
  and `app/src/components/wizard/SetupWizard.tsx` paths to `app/src/domain/glyphs.ts`
  and `app/src/sections/admin/setup-wizard/`; added `quiz_words` to the schema table;
  and added the missing Working Guardrails section. Removed the stale references to the
  deleted `app/src/domain/compose.ts` in `app/src/domain/shaping.ts`,
  `app/src/sections/scribe/ScribeView.tsx` and the `schreibsystem-und-wortbench.md` proposal. Added the `kurrent-writer-and-recognizer.md`
  proposal and `docs/notes/` to `docs/index.md` (#186).

### Fixed

- **Third wordbench set: the Abb. 22 Schülerschrift plate (cross-hand reference).** The
  1922 Leitfaden's only other connected Ausgangsschrift specimen — a pupil's hand
  (Bruno Krüger, 3rd school year, Breitkantfeder, 106 words of Hoffmann von
  Fallersleben's "Hab' Dank, du lieber Wind!") — is now measured like Abb. 19
  (`words-abb22.png` + 106 sidecar entries, boxes proposed, line-QC'd and hand-corrected).
  Sidecar entries carry a new optional `set` field; `export_fixtures`/`run`/`wordlab`
  accept custom set names, so the plate freezes into its own sibling fixture root
  (`suetterlin-1922-abb22`, `--set abb22`) and its cross-writer numbers are never averaged
  into the same-hand headlines. Provenance + PD rationale in the source's `SOURCE.md` (#188).
- **ESLint gate for the SPA.** Added a flat `app/eslint.config.js` (JS +
  typescript-eslint recommended + `react-hooks`, react-refresh as warnings),
  a `npm run lint` script, and an ESLint step to the CI frontend job — the
  `react-hooks/exhaustive-deps` suppressions in the tree are now enforced
  instead of inert. Fixed the findings this surfaced: `prefer-const` in
  `TafelView.tsx`, a missing hook dep in `RederiveAllDialog.tsx`, and added
  the missing justification to a `WrittenWord.tsx` suppression; kept the
  `_`-prefix unused-args convention and allowed intentional non-breaking
  spaces in UI strings. Updated `.github/copilot-instructions.md` to record
  that ESLint is now configured (#187).
- **`tools/pairlab` — independent-fit dissection of letter joins.** For every real
  occurrence of a letter pair in the Abb.-19/Abb.-20 specimens it re-fits each letter
  INDEPENDENTLY onto the frozen skeleton (bounded translation grid), regenerates the
  production connector between the two placements (same constants/guards as
  `core/compose.py`), tracks the specimen's own connecting stroke through the
  inter-letter gap, and measures tail/head adaptation profiles — how far into each
  glyph the real pen departs from the template before the join. Separates the three
  entangled failure modes (connector shape · placement · glyph-end adaptation) the
  word bench cannot tell apart. Additionally it TRACES the real pair along the known
  ductus: the M4 fit (`core/fit.py`) warps both templates onto the specimen ink, so
  every occurrence yields its ground-truth target — true coupling heights/tangents
  per join class and the stub-trim signal (fitted endpoint vs. tracked departure).
  Overlay + deviation-profile PNGs per occurrence, JSON aggregation, unit-tested
  pure geometry core (`tests/test_pairlab.py`) (#178).
- **Transition findings 2026-07-11** (`docs/proposals/uebergaenge-befund.md`): the
  pairlab survey over 87 occurrences / 45 pairs. Placement is the largest single
  error (39/87 need ≥ 0.25 xh correction); the standard diagonal join is generically
  right once letters sit correctly (f→e/t→e's bench penalty was placement); high
  exits (d loop, o/b/v/w Deckstrich bows, the r arm) systematically REPLACE both
  coupling stubs (0.2–0.4 xh per side) with one diagonal into the next letter's
  first-downstroke apex — confirming the stub hypothesis class-wise, not per pair.
  Solution options O1–O3 (placement first, coupling anchors, gated pair overrides)
  with cross-references from `qualitaetsmetrik.md` §6 and Vorschlag B (#178).
- **Connectors follow the school hand's join grammar.** The jul09/10 join audit (all
  generated Übergänge ranked with seam-kink angles against the Abb. 19/20/22 specimens)
  adds the plates' entry-class join grammar on top of the jul11 coupling composer:
  arcade entries (n m i u …) that must lose height now couple low through a baseline
  garland that merges tangentially onto their lead-in line (bi/on originals), the r-arm
  sets off with its authentic Absatz corner before a deep garland, clamped bow exits
  roll G1 over the crest instead of cornering (the b→e "extra Zacken"), sawtooth pairs
  (e→n family) pull onto one continuous diagonal instead of leaving a mid-height shelf,
  and the low-exit word-final Endstrich is a two-tangent quadratic that flattens like the
  plates (short flick after descender exits) while high forward exits keep the jul11 level
  Auslauf. Round bodies after a high exit stay on the jul11 rising-flank coupling anchor
  (O2), which subsumes the garland there. Measured standalone against the pre-jul11 base
  the grammar scored words 0.1253 → 0.1241 / pairs 0.1992 → 0.1927; the combined headline
  on top of jul11 was not re-measured in the merge environment (the wordbench needs the
  shared DB), but both composer unit-suites (`test_compose_coupling`, `test_compose_joins`)
  pass and the compose golden fixture is deliberately re-pinned (#188).

## [0.13.0] — 2026-07-09 — Tri-script pen foundation + human writing kinematics

### Added

- **`llms.txt` for agentic browsing.** The site now serves a spec-compliant `/llms.txt`
  (H1, summary, linked sections: the three public areas, legal, GitHub, the open read
  API's OpenAPI docs) so AI agents get a crawlable map instead of the SPA's index.html
  fallback — fixes the Chrome "agentic browsing" audit error (#174).
- **The public repository is linked.** Every public page's footer now carries a GitHub
  link next to the Impressum link (on phones the row wraps onto its own line), and the
  Impressum's "Quellen & Lizenzen" no longer announces the repository as planned but links
  it directly. A "Weitere Projekte" block (mirroring the anyplot legal page) lists
  anyplot.ai and cite-citadel after the operator disclaimer — deliberately in the
  Impressum and not in the footer (#172).
- **Petzendorfer 1889 seeded as a separate Kurrent source** (migration 0012): the only PD
  Kurrent chart with a digits row — the Kurrent digit templates' authoring source. A
  deliberately separate hand (~57° calligraphic Kurrent), never merged into loth-1866
  (#171).
- **Broad-nib pen model — the Offenbacher Bandzugfeder writes for real.** `core/widths.py`
  gains the `BroadNib` model (`w(φ) = W·|sin(φ−α)| + t·|cos(φ−α)|` at Koch's constant 15°
  edge angle, primary source *Die Offenbacher Schrift*, 1928) and
  `core/template.py::chisel_union_rings` sweeps the W×t nib rectangle along the centerline,
  so chisel ends fall out naturally — never round caps. The writing path regenerates widths
  from the model (warp-invariant, inks generated connectors, repairs scan noise); the stored
  measurement is untouched and keeps serving the diagnostic. `api/rendering.py::pooled_pen`
  calibrates the nib per source from the pooled measured profiles (#170).
- **Digits and punctuation as detached glyphs.** `0–9` and `. , ; : ! ? ' „ “ - – ( ) §`
  are real glyphs with `joins: false` in both shaping twins (`core/shaping.py`,
  `app/src/domain/{glyphs,shaping}.ts`): written without any Übergang, placed by whole-ink
  clearance, pen lift into them, Endstrich + diacritic flush before them. ASCII `-` maps to
  the historical double-stroke hyphen; straight `"` pairs low-then-high by occurrence
  parity. The admin sidebar gains Ziffern/Satzzeichen groups; digits are quizzable,
  punctuation is not; unauthored marks surface in the Federprobe "noch nicht kuratiert"
  note instead of failing silently (#170).
- **Pen-aware composition.** `compose_word(…, pen=…)`: `pressure` (Kurrent Spitzfeder) caps
  generated strokes at the source's pooled hairline — pressure never travels between
  letters; `broad_nib` ships connectors as swept-nib rings (the client already fills rings,
  zero client changes). `pen=None` stays byte-identical: golden fixture, wordbench 0.125337
  and both glyph benches (Sütterlin 0.1865, Kurrent 0.1251) reproduce their baselines
  (#170).
- **Design doc `docs/concepts/federmodelle.md`** — three pens, one render path: the
  Bandzugfeder law + chisel sweep, Spitzfeder hairline rules and the planned synthesis
  model/naturalness metric, the digits/punctuation glyph space, per-script authoring
  sources, and the rejected alternatives (#170).
- **`tools/glyphbench --style offenbacher`** routes through the pressure derivation and the
  Schwellzug pixel metric (honest for extraction quality — it scores the measured profile)
  until a dedicated width-direction naturalness metric is calibrated (#170).

### Changed

- **The handwriting reveal follows human kinematics.** `lib/strokeTiming` applies the
  two-thirds power law (the pen visibly slows in curves — non-linear dashoffset keyframes
  per stroke) and isochrony (stroke durations grow sublinearly with length) to
  `WrittenWord` and `WrittenGlyph`, replacing the constant-speed sweep
  (docs/concepts/federmodelle.md §5) (#171).
- **The Schreibtafel writes with the same hand.** `WrittenSheet` (the `/tafel` alphabet
  rows) now runs through the shared kinematic reveal (strokeTiming + the WAAPI hook)
  instead of its own linear keyframes — the most glyph-dense writing surface no longer
  sweeps at machine-constant speed; cascade stagger, tap-replay and the ink settle are
  unchanged (#173).

### Fixed

- **Trailing punctuation no longer steals the round Schluss-s.** Positions are assigned per
  run of same joins-class, so `"Haus,"` keeps `s-final` (previously the comma made the s
  read as medial → long-ſ) (#170).

## [0.12.0] — 2026-07-08 — Word bench full coverage + compose loop

### Added

- **All 63 Abb.-19 words + 33 Abb.-20 letter pairs annotated**; the word bench scores pairs
  separately with their own `pair_loss` headline (#163).
- **Word diagnostics layer**: `tools/wordlab` overlays a composed word on its specimen with
  per-connector penalty callouts; compose provenance + segment metric (#166).
- **Word-final Endstrich**: the composer generates the finishing upswing of the school hand
  (words bench 0.1284 → 0.1240) (#168).

### Changed

- **Fluent body widening**: the chart-pinched round letters (e/a/u/o) open to the connected
  hand's measured pitch at render time (#169).

## [0.11.0] — 2026-07-04 — Repo goes public

### Added

- **Community files + public README** with hero image and live-first structure (#151, #162);
  Codecov coverage reporting for the backend (#161).

### Changed

- Dependency refresh across Python, npm and Actions via grouped Dependabot PRs (#152–#160).

## [0.10.0] — 2026-07-03 — Server-side word composition + word bench

### Added

- **Public write API** (`/write/glyphs`, `/write/word`) with a shared render cache — whole
  words compose server-side in one cacheable request (#142, #143).
- **The word bench**: frozen same-hand word specimens (Sütterlin Abb. 19) scored against the
  composer, `tools/wordbench` (#144); first transition-redesign loop against it (#145).
- **Quiz word mode + "Tinte & Vergleich" redesign** (#139), an expanded ~500-word reading
  bank with runtime distractor draw (#148, #149, #150).

### Changed

- Sütterlin diacritics defer to the end of the word; connectors join on rendered-centerline
  tangents (#136, #137); public reads route via the open `api.` subdomain (#140).

## [0.9.0] — 2026-06-26 — Public redesign: three areas + Schreibtafel

### Added

- **The word-composition engine**: glyphs connect into live-written words (#112).
- **Public Schreibtafel** with written-letter playback and all three Grundtafeln (#114, #123,
  #127–#130); the `/lehrbuch` primer, later renamed and expanded to `/schriftkunde` (#116–#118).
- **ü/ö/Ü/Ö authored from two chart pieces** (crop patches) in the admin (#135).

### Changed

- **Public redesign**: width/typo/surface foundation, three-area nav + hubs, single-column
  written-word hero, unified PageHeader, SEO baseline (#120, #122, #124–#126, #131).

## [0.8.0] — 2026-06-21 — Sütterlin naturalness metric

### Added

- **The Gleichzug naturalness metric** (`core/quality_suetterlin.py`) with bench + glyphlab
  tooling (#96) and two deliberate re-baselines (#97, #106).
- Admin wizard: per-category score breakdown in Optimieren, the Weg "Anpassen" nudge tool
  (#101, #102); a decluttered admin with one action hub (#111, #113).

### Changed

- Sütterlin ductus tuning: through-stem straightening, Spitze-tip retrace collapse then
  taper (#103–#105); `/quality` scores with the style's own metric (#98).

## [0.7.0] — 2026-06-17 — Sütterlin writes (Gleichzug derivation)

### Added

- **Skeleton-locked Gleichzug derivation** for Sütterlin (#83) with edge-following in merged
  double-stroke regions (#92), smooth strokes + the source-pooled nib (#93), corner-aware
  verticalization + the glyphlab inspection tool (#95).
- Wizard ink brush + per-glyph speck auto-fill + mask preview (#80); admin glyph comparison
  view (#82); InfoHint affordance + legibility pass (#89).

### Changed

- Quiz UX rounds: written/crop toggle, steady prompt, compact setup, crop-overlay reveal
  (#84–#88).

## [0.6.0] — 2026-06-12 — Glyph quality pipeline + the Sütterlin pivot

### Added

- **Image-space quality metric + the hermetic glyph bench** (#63), corner knots + template
  refinement (#64), the `/optimize-glyphs` experiment-loop skill (#65), admin quality
  feedback + re-derive flows (#66, #68–#70, #73, #74).
- **Medial-axis snap + crossing-width resolution** for the drawn ductus (#61).
- `/impressum` with period letter-register copy (#75).

### Changed

- **Pivot to Sütterlin as the active public script**: PD 1922 chart seeded, width resolver
  activated, runtime source switcher (#77–#79); experiment run pressure-cone prior + refine
  tuning, bench 0.1339 → 0.1251 (#71, documented in the new Qualitätsmetrik reference #72).

## [0.5.0] — 2026-06-10 — Paper & ink identity (style rounds R1–R9)

### Added

- **The period visual identity**: pigment palette, ink settle + fibre-wicked edges, Schulheft
  ruling, exercise-book blue guides, letterpress deboss + Playfair Display, static paper
  grain (#47–#53, decisions recorded in the style guide #54).
- The self-verification skill family + working guardrails (#55); Schriftkunde docs + PD
  chart sources with corrected slant geometry (#57, #58).

### Changed

- **App restructure**: components/layouts/sections/hooks refolder, lazy routes, typed API
  layer, German locales namespaces, split quiz/chart/wizard modules (#33, #34, #38–#46);
  quiz letters render "as written" via the ductus (#32).

## [0.4.0] — 2026-06-08 — Library schema + setup wizard

### Added

- **The library schema** (styles/templates/instances) with German lineature terms and the
  step-by-step setup wizard as the admin's single editing surface (#25, #26).
- **Multi-stroke ductus capture** — pen lifts no longer bridge strokes (#29); per-line slant,
  box move/resize/lock, zoom + pan, mobile fixes (#22–#24, #27, #28, #30).

## [0.3.0] — 2026-06-04 — Public site v1: landing, quiz, worksheet

### Added

- **Public letter-recognition quiz** (`/quiz`) with end-screen stats (#12, #13, #15);
  the Lineatur worksheet generator (#11); the serif landing with ductus timeline, rebuilt
  in the "paper & ink" identity (#9, #19–#21).
- **M4 fit routine** + editor fit overlay (#8); CI pipeline (ruff + pytest) (#14); alembic
  migrations run on deploy (#18).

## [0.2.0] — 2026-05-29 — Deployed: Cloud Run + Cloudflare Access

### Added

- **Cloud Run + Cloudflare Access deploy bootstrap** (#5) with operational status notes
  (#6); Plausible analytics routed off the Access-gated apex.
- Vision + architecture docs restructured holistically (#1–#4).

## [0.1.0] — 2026-05-22 — MVP kernel: ductus extraction

### Added

- **Two-channel ink extraction** (width = pressure via skeleton + distance transform,
  darkness = ink) on the PD Loth 1866 Kurrent chart (M0).
- **Canonical ductus templates** for the §9 core glyphs with editable bboxes, exclude
  regions and a chart annotator (M3 Phase A).
- **The admin**: web UI for canonical extraction, from CLI tooling (v1) to real UI with
  2:1:2 calibration + resample (v2) to `/core` + Postgres + Alembic + SVG diagnostic (v3).
- The founding design docs (analysis-by-synthesis architecture, MVP gates, naming/licensing)
  and the first PD source.
