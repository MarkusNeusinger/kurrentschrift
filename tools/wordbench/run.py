"""Run the word bench: compose every fixture word with CURRENT code, score frozen.

Hermetic and deterministic — no DB, no HTTP: templates + slots + scoring
references come from the fixture snapshot (tools/wordbench/export_fixtures.py).
The code under test per run is COMPOSITION + RENDERING (core/compose.py +
core/pipeline.render_payload_for_template). Shaping is deliberately NOT under
test: the slots are frozen at export, so a core/shaping.py change moves the
numbers only after an explicit re-export (= a re-baseline). Composition
mirrors production: the frozen Laufform variants (templates_laufform.json)
are passed as ``laufform_by_key`` exactly like ``/write/word`` does —
``--no-laufform`` runs chart-only as a diagnostic decomposition. ONE script per
run, like the glyph bench: Kurrent and Sütterlin words are never averaged —
and neither are words and pairs: ``--set`` selects the fixture set, and the
pairs of Abb. 20 report their own ``pair_loss`` headline. Entries frozen as
``scorable: false`` (a needed template is not authored yet) are skipped and
reported by name — an authoring gap is not a composition failure; a crash of
an authored entry still counts 1.0.

Every run states WHICH BASE it measured before it measures anything: two header
lines per fixture root (``root: <name> exported_at=…`` and ``digest=<12 hex>``,
from the shared ``tools/wordbench/roots.py`` that the trace tools use too), the
manifest's own ``page_sha256`` re-checked against the committed page bytes, and
``--expect-root`` to make the expected base a precondition rather than a hope.
The roots are gitignored, so a silent re-export used to be invisible — an
undeclared re-baseline is exactly what the audit of 2026-09-02 could no longer
trace.

Usage:
    uv run python -m tools.wordbench.run [--style suetterlin]
        [--set words|pairs|<custom set like abb22>|all] [--words unter,das]
        [--artifacts DIR] [--json report.json] [--compare old.json]
        [--laufform draft.json | --no-laufform] [--expect-root <digest-prefix>]

    ``--laufform`` composes with CANDIDATE running forms instead of the frozen
    ones — the Laufform twin of ``--overrides``, and under the same discipline
    (qualitaetsmetrik.md §6): an overlay run is its OWN number, never the
    headline, because the frozen fixtures are what the headline is defined on.

    ``--set all`` covers ONLY the canonical same-hand sets (words + pairs);
    a custom cross-hand set must be named explicitly so it can never mix
    into the same-hand headlines.

Output contract (parsed by the experiment loop — keep the words block stable):

    word unter           loss 0.312345  trans 0.301 cover 0.322 width 0.310  (tx=12, ty=-1)
    ---
    bench_loss:      0.298765
    worst_word:      haben 0.412345
    words_scored:    15
    words_skipped:   0
    words_failed:    0
    --- components (mean penalty, lower better) ---
    comp_transition: 0.301234
    comp_coverage:   0.288888
    comp_width:      0.150000

The pairs block (``--set pairs``/``all``) mirrors it with ``pair_loss:``,
``worst_pair:``, ``pairs_scored/skipped/failed`` and ``pair_comp_*`` lines.

Report-only columns are appended AFTER that stable block and never enter the
loss: ``slant`` (R5), the Gleichzug audit (jul30) and — when the fixture set
carries ``pair_instances.json`` — ``meas`` (handmodell H2): the composed joins
against the specimen's own dissected ones — ``doff`` the horizontal placement
delta in the harvest's body frame, ``dconn`` the start-aligned connector-shape
distance (tools/wordbench/pairmeas.py) — per row as
``meas n=<matched>/<joins> doff=… dconn=…`` and as ``meas_matched`` +
``meas_excluded`` (QC-rejected dissections / override-rendered joins) +
``meas_doff_median``/``meas_dconn_median`` in the block — and ``seam``
(tools/wordbench/seam.py): the turn angle at each end of a generated
connector, ``dep``/``arr`` per row and pooled ``seam_dep_median`` /
``seam_arr_median`` / ``seam_*_abs_median`` in the block.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from core.compose import _key_base, compose_word
from core.pipeline import render_payload_for_template
from core.shaping import GlyphSlot
from tools.wordbench.gleichzug import audit_composed
from tools.wordbench.metric import score_word
from tools.wordbench.pairmeas import compare_joins, load_measured, rows_for_entry
from tools.wordbench.roots import add_expect_root_argument, announce_roots, check_compared_roots
from tools.wordbench.seam import seam_angles
from tools.wordbench.slant import composed_raster, slant_deg


FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]
STYLES = ("suetterlin", "kurrent", "offenbacher")
# Provenance stamped into a Laufform row DERIVED from a --laufform draft, where
# the frozen rows carry the apply-step's (or the fetcher's). Nothing in the
# render path reads it; it keeps an artifact traceable to its overlay run.
LAUFFORM_OVERLAY_META = {"derived_from": "laufform-overlay", "via": "wordbench.run"}


def page_hash_problems(manifest: dict, repo_root: Path = REPO_ROOT) -> list[str]:
    """Re-check a manifest's ``page_sha256`` against the committed page bytes.

    The export already records the hash of every specimen page a set was frozen
    from; until now only the rebuild path (fetch_fixtures) ever compared it, so
    a measuring run happily scored fixtures whose plate had moved underneath
    them. Returns one human-readable line per problem (missing file, changed
    bytes) and an empty list when the manifest carries no hashes at all — an
    older export keeps running unchanged.
    """
    problems: list[str] = []
    source_id = manifest.get("source_id")
    for page, expected in sorted((manifest.get("page_sha256") or {}).items()):
        path = repo_root / "data" / "sources" / str(source_id) / page
        if not path.is_file():
            problems.append(f"{page}: missing at {path}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            problems.append(f"{page}: manifest {expected[:12]} vs file {actual[:12]}")
    return problems


def _overlay(word_dir: Path, word_meta: dict, composed: dict, report: dict, out_path: Path) -> None:
    """Crop background, specimen skeleton in blue, composed centerlines in red
    (connectors bright, glyph bodies dark, diacritics orange) at the fitted
    registration — the metric is a proxy, the overlay is the truth."""
    crop = Image.open(word_dir / "crop.png").convert("RGB")
    skel = np.load(word_dir / "ref_skel.npz")["skel"]
    px = np.array(crop)  # writable copy
    px[skel] = (90, 140, 220)
    img = Image.fromarray(px)
    d = ImageDraw.Draw(img)
    reg = report.get("registration")
    if reg:
        xh, tx, ty = reg["xh_px"], reg["tx"], reg["ty"]
        baseline_row = word_meta["baseline_y"] - word_meta["rect"][1]
        for it in composed["items"]:
            pts = [(x * xh + tx, baseline_row - y * xh + ty) for x, y in it["centerline"]]
            if "rings" in it:
                color = (230, 140, 30) if it.get("diacritic") else (150, 30, 40)
            else:
                color = (235, 40, 40)
            d.line(pts, fill=color, width=2, joint="curve")
    img.save(out_path)


def _slot_overrides(slots: list[GlyphSlot], by_base: dict[tuple[str, str], dict]) -> dict[tuple[str, str], dict]:
    """Map base-keyed pair overrides onto this word's RAW slot keys.

    The composer looks overrides up by the slots' own keys; a harvest file is
    keyed by bare glyph bases (post-R2 registry keys), while frozen fixture
    slots may still carry position suffixes — so the mapping happens per word."""
    out: dict[tuple[str, str], dict] = {}
    for s0, s1 in zip(slots, slots[1:], strict=False):
        if s0.space or s1.space or not s0.key or not s1.key or not (s0.joins and s1.joins):
            continue
        geometry = by_base.get((_key_base(s0.key, s0.position), _key_base(s1.key, s1.position)))
        if geometry is not None:
            out[(s0.key, s1.key)] = geometry
    return out


def load_laufform_payload(path) -> dict[str, dict]:
    """Read and shape-check a ``--laufform`` file: an object mapping glyph_key -> draft/row.

    A malformed file fails fast with a named SystemExit instead of a traceback —
    this is a CLI surface, not a library path.
    """
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"--laufform {path}: {exc}") from None
    if not isinstance(payload, dict) or not all(isinstance(v, dict) for v in payload.values()):
        raise SystemExit(f"--laufform {path}: expected an object mapping glyph_key -> draft/row")
    return payload


def overlay_laufform_rows(
    frozen: dict[str, dict], payload: dict[str, dict], templates: dict[str, dict]
) -> dict[str, dict]:
    """The frozen Laufform rows with every key the ``--laufform`` file states replaced.

    OVERLAY, not replacement: a candidate file usually carries the handful of
    glyphs an experiment moved, and every other letter must keep composing
    exactly as the headline does — otherwise the run measures the absence of
    the other running forms rather than the candidate.

    Two payload shapes are accepted, because the drafts come from two places:

    * ``{glyph_key: {"anchors": [...], "n_occurrences": N}}`` — a harvest/median
      DRAFT. The full fixture row is derived from THIS root's chart row through
      ``fetch_fixtures.laufform_row_from_payload`` — i.e. through
      ``api.routers.templates.build_laufform_canonical``, the one derivation the
      write path uses — so widths, stroke topology and the entry/exit/advance
      shift are identical to a stored variant-100 row by construction.
    * ``{glyph_key: {row…}}`` — a full fixture row (``anchors`` + ``trace_meta``),
      taken VERBATIM: something already derived it, re-deriving would overwrite
      its widths with the chart row's.

    Skipped, never guessed: a key this fixture root has no chart row for (the
    set simply never composes that glyph) and an anchor count that disagrees
    with the chart row — the same guard the apply endpoint and
    ``fetch_fixtures.laufform_rows_from_aggregates`` apply, named per key.
    """
    if not payload:
        return frozen
    # Deferred: pulls in the API package (build_laufform_canonical), which the
    # flag-free bench path has no business importing.
    from tools.wordbench.fetch_fixtures import laufform_row_from_payload

    rows = dict(frozen)
    for key, value in payload.items():
        chart = templates.get(key)
        if chart is None:
            continue
        anchors = value.get("anchors")
        if not anchors:
            print(f"  skip laufform {key}: no anchors in the overlay file")
            continue
        if len(anchors) != len(chart["anchors"]):
            print(f"  skip laufform {key}: {len(anchors)} overlay anchors vs {len(chart['anchors'])} on the chart row")
            continue
        if "trace_meta" in value:
            rows[key] = value
            continue
        meta = dict(LAUFFORM_OVERLAY_META)
        if value.get("n_occurrences") is not None:
            meta["n_occurrences"] = value["n_occurrences"]
        rows[key] = laufform_row_from_payload(chart, anchors, meta)
    return rows


def _print_block(reports: list[dict], skipped: list[dict], kind: str) -> None:
    """One headline block per fixture set. The words block is the experiment
    loop's stable contract; the pairs block mirrors it under its own names."""
    loss_label, worst_label, noun, comp_prefix = (
        ("bench_loss", "worst_word", "words", "comp")
        if kind == "word"
        else ("pair_loss", "worst_pair", "pairs", "pair_comp")
    )
    scored = [r for r in reports if not r["failed"]]
    losses = [r["loss"] for r in reports]
    headline = float(np.mean(losses)) if losses else 1.0
    worst = max(reports, key=lambda r: r["loss"]) if reports else None
    print("---")
    print(f"{loss_label}:      {headline:.6f}")
    if worst:
        print(f"{worst_label}:      {worst['id']} {worst['loss']:.6f}")
    print(f"{noun}_scored:    {len(scored)}")
    print(f"{noun}_skipped:   {len(skipped)}")
    print(f"{noun}_failed:    {len(reports) - len(scored)}")
    if skipped:
        print(f"{noun}_skipped_ids: {','.join(s['id'] for s in skipped)}")
    if scored:
        print("--- components (mean penalty, lower better) ---")
        for comp, label in (("transition", "transition"), ("coverage", "coverage"), ("width", "width")):
            print(f"{comp_prefix}_{label}: {float(np.mean([r[comp] for r in scored])):.6f}")
        # Report-only slant medians (90 = upright, < 90 = right-leaning) —
        # appended after the stable component block, never a headline.
        slant_prefix = "" if kind == "word" else "pair_"
        for slant_key in ("slant_spec", "slant_comp"):
            values = [r[slant_key] for r in scored if r.get(slant_key) is not None]
            if values:
                print(f"{slant_prefix}{slant_key}_median: {float(np.median(values)):.2f}")
        # Gleichzug audit totals (report-only): flow gaps + doubling events
        # over all scored entries — the one-flow, one-width invariant.
        audits = [r["gleichzug"] for r in scored if r.get("gleichzug")]
        if audits:
            gaps_total = sum(len(a["gaps"]) for a in audits)
            dbl_total = sum(len(a["doublings"]) for a in audits)
            print(f"{slant_prefix}gleichzug_gaps: {gaps_total}")
            print(f"{slant_prefix}gleichzug_doublings: {dbl_total}")
        # Measured-vs-composed join medians (report-only, handmodell H2): how
        # far the generated placement/connector sits from the specimen's own
        # dissected join. Absent when the fixture set has no
        # pair_instances.json — an older export keeps running unchanged.
        meas = [r["pairmeas"] for r in scored if r.get("pairmeas")]
        if meas:
            matched = sum(m["n_matched"] for m in meas)
            total = sum(m["n_joins"] for m in meas)
            print(f"{slant_prefix}meas_matched: {matched}/{total}")
            # What the comparison deliberately left out: dissections the
            # harvest's own QC rejected, and joins rendered from an approved
            # override (an override IS a harvested centerline).
            excluded_fit = sum(m.get("excluded_fit", 0) for m in meas)
            excluded_override = sum(m.get("excluded_override", 0) for m in meas)
            print(f"{slant_prefix}meas_excluded: fit={excluded_fit} override={excluded_override}")
            for label in ("doff", "dconn"):
                values = [m[f"{label}_mean"] for m in meas if m[f"{label}_mean"] is not None]
                if values:
                    print(f"{slant_prefix}meas_{label}_median: {float(np.median(values)):.3f}")
        # Seam turn angles (report-only): how far the generated connector
        # departs from / arrives at the letter it joins. POOLED over every
        # matched join of the block rather than averaged per entry — a word
        # with one join must not weigh as much as a word with six.
        seams = [r["seam"] for r in scored if r.get("seam")]
        if seams:
            matched = sum(s["n_matched"] for s in seams)
            total = sum(s["n_joins"] for s in seams)
            print(f"{slant_prefix}seam_matched: {matched}/{total}")
            # Excluded, counted rather than averaged: a connector item with a
            # capital's ornament retrace prefixed to it (see seam.py).
            print(f"{slant_prefix}seam_excluded: retrace={sum(s['excluded_retrace'] for s in seams)}")
            for label, key in (("dep", "dep_deg"), ("arr", "arr_deg")):
                values = [j[key] for s in seams for j in s["joins"]]
                if values:
                    print(f"{slant_prefix}seam_{label}_median: {float(np.median(values)):+.2f}")
                    print(f"{slant_prefix}seam_{label}_abs_median: {float(np.median(np.abs(values))):.2f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--style", default="suetterlin", choices=STYLES)
    parser.add_argument(
        "--set",
        dest="which",
        default="words",
        help="fixture set to run (words | pairs | a custom set name | all). 'all' covers ONLY the "
        "canonical same-hand sets (words + pairs) — a custom cross-hand set like abb22 must be "
        "named explicitly so it can never mix into the same-hand headlines.",
    )
    parser.add_argument("--fixtures", type=Path, default=FIXTURES, help="fixture root (default: the frozen set)")
    add_expect_root_argument(parser)
    parser.add_argument("--words", help="comma-separated id/word filter")
    parser.add_argument("--artifacts", type=Path, help="write overlay PNGs here")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--compare", type=Path, help="previous --json report to diff against")
    parser.add_argument(
        "--overrides",
        type=Path,
        help="pair-override file (tools/pairlab/harvest.py --out format) composed into every word; "
        "an override run is a SEPARATE measurement, never comparable to the override-free headline",
    )
    # The two ways to leave the frozen running forms — never both at once: one
    # drops them, the other substitutes candidates, and a run that did both
    # would report a number nobody could attribute.
    laufform_group = parser.add_mutually_exclusive_group()
    laufform_group.add_argument(
        "--no-laufform",
        action="store_true",
        help="compose chart-only, ignoring the frozen Laufform variants (templates_laufform.json) — "
        "a diagnostic decomposition run; the headline mirrors production and composes WITH them",
    )
    laufform_group.add_argument(
        "--laufform",
        type=Path,
        help="candidate Laufform file overlaid onto the frozen variants (harvest draft "
        "{glyph_key: {anchors, n_occurrences}} or full fixture rows); keys it does not name keep "
        "their frozen row — an overlay run is a SEPARATE measurement, never comparable to the headline",
    )
    parser.add_argument(
        "--exit-trim",
        action="store_true",
        help="compose with the opt-in exit-side collinearity rule (core.compose EXIT_TRIM_WINDOW, "
        'pre-registered under the heading "Übergänge J4" in messjournal.md §14): a sawtooth '
        "exit's chart stub is cut back to where the "
        "straight to the unchanged coupling point continues the letter's own direction — a CANDIDATE "
        "arm, its own measurement, never the headline",
    )
    parser.add_argument(
        "--exit-trim-min-kink",
        type=float,
        default=0.0,
        metavar="DEG",
        help="narrow --exit-trim to the joins whose departure kinks by AT LEAST DEG (the post-hoc "
        "J4b arm; core.compose EXIT_TRIM_MIN_KINK_DEG, 0 = the full pre-registered J4 class)",
    )
    parser.add_argument(
        "--apex-handover",
        action="store_true",
        help="compose with the opt-in apex handover (core.compose APEX_HANDOVER_MIN_RISE, pre-registered "
        'under the heading "Übergänge J5" in messjournal.md §14): a long unlooped lead-in hands the join '
        "over at its apex — a CANDIDATE arm, its own measurement, never the headline",
    )
    parser.add_argument(
        "--stem-depart",
        action="store_true",
        help="compose with the opt-in d stem departure (core.compose STEM_DEPART_BASES, same J5 entry): "
        "the join rides the d's stem down to the measured departure height — the other arm of that "
        "ladder, likewise its own measurement",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    # A narrowing knob that is silently ignored is the worst kind: the run
    # would report the BASELINE under the name of a candidate arm. Same
    # doctrine as --expect-root — a number must never lie about its origin.
    if args.exit_trim_min_kink and not args.exit_trim:
        parser.error("--exit-trim-min-kink narrows --exit-trim; pass --exit-trim too (or drop it)")
    if args.exit_trim_min_kink < 0:
        parser.error("--exit-trim-min-kink is a kink in degrees and cannot be negative")

    overrides_by_base: dict[tuple[str, str], dict] = {}
    if args.overrides:
        for entry in json.loads(args.overrides.read_text()):
            overrides_by_base[(entry["left_key"], entry["right_key"])] = entry["geometry"]
        print(f"overrides: {len(overrides_by_base)} pairs from {args.overrides}")

    laufform_payload: dict[str, dict] = {}
    if args.laufform:
        laufform_payload = load_laufform_payload(args.laufform)
        print(f"laufform: {len(laufform_payload)} rows from {args.laufform} (own number - never the headline)")
    if args.exit_trim:
        # The header is provenance: it names the arm the run actually measured,
        # so a narrowed run never files itself under the full class's name.
        narrowed = f" min_kink={args.exit_trim_min_kink:g}deg" if args.exit_trim_min_kink else ""
        arm = "J4b" if args.exit_trim_min_kink else "J4"
        print(f"exit_trim: on{narrowed} (candidate arm {arm} - own number, never the headline)")
    if args.apex_handover or args.stem_depart:
        # Same provenance duty: a rung of the J5 ladder must never file itself
        # under the baseline's name.
        on = [n for n, v in (("apex_handover", args.apex_handover), ("stem_depart", args.stem_depart)) if v]
        print(f"J5: {' + '.join(on)} on (candidate arm - own number, never the headline)")

    t0 = time.perf_counter()
    style_root = args.fixtures / args.style
    # 'all' aggregates reports across the selected manifests, so it must stay
    # scoped to the canonical SAME-HAND sets — a custom cross-hand set (abb22)
    # would otherwise silently join the words headline.
    wanted = ("words", "pairs") if args.which == "all" else (args.which,)
    selected: list[tuple[Path, dict]] = []
    for manifest_path in sorted(style_root.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("set", "words") in wanted:
            selected.append((manifest_path.parent, manifest))
    if not selected:
        raise SystemExit(f"no {args.which} fixtures under {style_root} — run tools/wordbench/export_fixtures first")

    # WHICH BASE this run measures — stated, checked and only then scored.
    # Everything here happens before the first composition so a run can never
    # produce a number against fixtures it was not asked for.
    root_meta = announce_roots([root for root, _ in selected], args.expect_root)
    # A baseline from ANOTHER export turns `--compare` into a comparison of
    # exports rather than of code, which is the one thing the frozen-reference
    # rule forbids (qualitaetsmetrik.md §2). Checked before the first
    # composition, so a run that cannot be paired never produces the numbers.
    compare_payload = None
    if args.compare:
        try:
            compare_payload = json.loads(args.compare.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"--compare {args.compare}: {exc}") from None
        check_compared_roots(f"--compare {args.compare}", compare_payload, root_meta)
    page_problems = [f"{root.name}: {p}" for root, manifest in selected for p in page_hash_problems(manifest)]
    if page_problems:
        raise SystemExit("specimen pages do not match the manifest's page_sha256:\n  " + "\n  ".join(page_problems))

    word_filter = set(args.words.split(",")) if args.words else None
    reports: list[dict] = []
    skipped: list[dict] = []
    # Entries whose meas guard fired — reported ONCE per run below, so a
    # systematic schema failure never reads like "this set has no artifact".
    pairmeas_failures: list[tuple[str, str]] = []
    # Same doctrine for the seam sensor: one run-level line, never per entry.
    seam_failures: list[tuple[str, str]] = []
    for root, manifest in selected:
        templates = json.loads((root / "templates.json").read_text())
        # The frozen Laufform variants (median running forms): production
        # composes with them per flowing run, so the headline does too. An
        # older fixture export without the file runs chart-only, unchanged.
        laufform_path = root / "templates_laufform.json"
        laufform_rows: dict[str, dict] = (
            json.loads(laufform_path.read_text()) if laufform_path.exists() and not args.no_laufform else {}
        )
        # The candidate overlay replaces exactly the keys it names — before the
        # cached accessors below bind it, so both see one dict.
        laufform_rows = overlay_laufform_rows(laufform_rows, laufform_payload, templates)
        nib = manifest.get("constant_nib_units")
        resolver = manifest.get("width_resolver") or "pressure"
        style_ratio = manifest.get("style_ratio") or [1, 1, 1]

        payload_cache: dict[str, dict | None] = {}
        laufform_cache: dict[str, dict | None] = {}

        def payload_for(
            key: str,
            cache: dict = payload_cache,
            rows: dict = templates,
            ratio: list = style_ratio,
            width_resolver: str = resolver,
            nib_units: float | None = nib,
        ) -> dict | None:
            if key not in cache:
                row = rows.get(key)
                cache[key] = render_payload_for_template(row, ratio, width_resolver, nib_units) if row else None
            return cache[key]

        def laufform_for(
            key: str,
            cache: dict = laufform_cache,
            rows: dict = laufform_rows,
            ratio: list = style_ratio,
            width_resolver: str = resolver,
            nib_units: float | None = nib,
        ) -> dict | None:
            if key not in cache:
                row = rows.get(key)
                cache[key] = render_payload_for_template(row, ratio, width_resolver, nib_units) if row else None
            return cache[key]

        if laufform_rows:
            print(f"laufform: {len(laufform_rows)} variant rows from {laufform_path.parent.name}")
        # The frozen MEASURED joins of this set (handmodell H2) — the reference
        # for the report-only meas columns. None for a fixture set exported
        # before the artifact existed: the columns are then simply absent.
        measured_artifact = load_measured(root)

        for entry in manifest["words"]:
            entry_id = entry.get("id", entry["word"])
            kind = entry.get("kind", "word")
            if word_filter and entry_id not in word_filter and entry["word"] not in word_filter:
                continue
            if not entry.get("scorable", not entry.get("missing_at_export")):
                skipped.append({"id": entry_id, "kind": kind, "missing": entry.get("missing_at_export", [])})
                continue
            word_dir = root / entry_id
            word_meta = json.loads((word_dir / "word.json").read_text())
            skel = np.load(word_dir / "ref_skel.npz")["skel"]
            slots = [GlyphSlot(**s) for s in word_meta["slots"]]
            try:
                # provenance=True only tags items with slot/pair attribution
                # (needed by the Gleichzug audit's letterform classification);
                # the scoring reads none of those keys — headline unchanged.
                laufform_by_key = {s.key: lf for s in slots if s.key and (lf := laufform_for(s.key)) is not None}
                composed = compose_word(
                    slots,
                    {s.key: payload_for(s.key) for s in slots if s.key},
                    provenance=True,
                    pair_overrides=_slot_overrides(slots, overrides_by_base) or None,
                    laufform_by_key=laufform_by_key or None,
                    exit_trim=args.exit_trim,
                    exit_trim_min_kink_deg=args.exit_trim_min_kink,
                    apex_handover=args.apex_handover,
                    stem_depart=args.stem_depart,
                )
                report = score_word(
                    composed,
                    {
                        "rect": word_meta["rect"],
                        "baseline_y": word_meta["baseline_y"],
                        "midband_y": word_meta["midband_y"],
                    },
                    skel,
                    nib,
                )
                # Slant is a REPORT column (redesign R5), never part of the loss:
                # specimen vs composed, both measured on the same crop grid.
                report["slant_spec"] = slant_deg(skel)
                report["slant_comp"] = slant_deg(
                    composed_raster(composed, report["registration"], word_meta, skel.shape)
                )
            except Exception as exc:  # a crash counts 1.0 — one regressed word always moves the number
                composed = None
                report = {"loss": 1.0, "failed": True, "error": f"{type(exc).__name__}: {exc}", "missing": []}
            # Gleichzug audit — REPORT columns like slant, never the loss, and
            # under its OWN guard: an audit crash must never move the headline.
            if composed is not None:
                try:
                    report["gleichzug"] = audit_composed(composed)
                except Exception as exc:
                    report["gleichzug_error"] = f"{type(exc).__name__}: {exc}"
            # "gemessen vs. komponiert" (handmodell H2) — the same doctrine:
            # REPORT columns under their OWN guard, never the loss.
            if composed is not None and measured_artifact is not None:
                try:
                    report["pairmeas"] = compare_joins(
                        composed, slots, rows_for_entry(measured_artifact, kind, entry_id)
                    )
                except Exception as exc:
                    report["pairmeas_error"] = f"{type(exc).__name__}: {exc}"
                    pairmeas_failures.append((entry_id, report["pairmeas_error"]))
            # Seam angles (the connector's turn against the letters it joins) —
            # same doctrine again: REPORT columns under their OWN guard, needing
            # no frozen artifact because the composition carries the geometry.
            if composed is not None:
                try:
                    report["seam"] = seam_angles(composed, slots)
                except Exception as exc:
                    report["seam_error"] = f"{type(exc).__name__}: {exc}"
                    seam_failures.append((entry_id, report["seam_error"]))
            report["id"] = entry_id
            report["word"] = entry["word"]
            report["kind"] = kind
            report["source_id"] = manifest["source_id"]
            reports.append(report)
            if args.artifacts and composed is not None:
                args.artifacts.mkdir(parents=True, exist_ok=True)
                _overlay(word_dir, word_meta, composed, report, args.artifacts / f"{entry_id}.png")

    if pairmeas_failures:
        entry_id, error = pairmeas_failures[0]
        print(f"warning: meas columns failed on {len(pairmeas_failures)} entries (first {entry_id}: {error})")
    if seam_failures:
        entry_id, error = seam_failures[0]
        print(f"warning: seam columns failed on {len(seam_failures)} entries (first {entry_id}: {error})")

    for r in sorted(reports, key=lambda r: r["id"]):
        if r["failed"]:
            reason = r.get("error") or f"missing {r.get('missing')}"
            print(f"word {r['id']:<15} loss {r['loss']:.6f}  FAILED ({reason})")
        else:
            reg = r["registration"]
            spec = r.get("slant_spec")
            comp = r.get("slant_comp")
            slant = f"  slant {spec:.1f}/{comp:.1f}" if spec is not None and comp is not None else ""
            # Stable report column: printed on every scored entry, zeros
            # included — parsers must not have to infer a missing column.
            audit = r.get("gleichzug")
            flow = f"  flow gaps={len(audit['gaps'])} dbl={len(audit['doublings'])}" if audit else ""
            # Measured-vs-composed joins: printed whenever the fixture set
            # carries the artifact, zeros included — a parser must not have to
            # infer a missing column. '-' where no join matched a measurement;
            # all-dash when this entry's guard fired (the run-level warning
            # names the error), so the per-row column set stays stable.
            pm = r.get("pairmeas")
            meas = ""
            if pm:
                doff = f"{pm['doff_mean']:.3f}" if pm["doff_mean"] is not None else "-"
                dconn = f"{pm['dconn_mean']:.3f}" if pm["dconn_mean"] is not None else "-"
                meas = f"  meas n={pm['n_matched']}/{pm['n_joins']} doff={doff} dconn={dconn}"
            elif "pairmeas_error" in r:
                meas = "  meas n=-/- doff=- dconn=-"
            # Seam turn angles at the two ends of every generated connector,
            # SIGNED medians over this entry's joins (degrees, + = the pen
            # turns counter-clockwise at the seam). Stable column like the
            # ones above: printed on every scored entry, '-' where nothing
            # matched, all-dash when this entry's guard fired.
            sm = r.get("seam")
            seam = ""
            if sm:
                dep = f"{sm['dep_median']:+.1f}" if sm["dep_median"] is not None else "-"
                arr = f"{sm['arr_median']:+.1f}" if sm["arr_median"] is not None else "-"
                seam = f"  seam n={sm['n_matched']}/{sm['n_joins']} dep={dep} arr={arr}"
            elif "seam_error" in r:
                seam = "  seam n=-/- dep=- arr=-"
            print(
                f"word {r['id']:<15} loss {r['loss']:.6f}  "
                f"trans {r['transition']:.3f} cover {r['coverage']:.3f} width {r['width']:.3f}  "
                f"(tx={reg['tx']:.0f}, ty={reg['ty']:.0f}){slant}{flow}{meas}{seam}"
            )

    # The FULL digests go into the report (the header prints 12 hex to stay
    # readable) — a stored report must be enough to re-check its own base.
    result: dict = {"style": args.style, "set": args.which, "roots": root_meta}
    if args.overrides:
        result["overrides"] = str(args.overrides)
    if args.laufform:
        result["laufform"] = str(args.laufform)
    if args.no_laufform:
        result["laufform"] = False
    if args.exit_trim:
        # One key, one type: the flag stays a bool and the narrowing angle gets
        # its own numeric key, so a reader never has to type-check the arm.
        result["exit_trim"] = True
        if args.exit_trim_min_kink:
            result["exit_trim_min_kink_deg"] = args.exit_trim_min_kink
    if args.apex_handover:
        result["apex_handover"] = True
    if args.stem_depart:
        result["stem_depart"] = True
    for kind in ("word", "pair"):
        kind_reports = [r for r in reports if r["kind"] == kind]
        kind_skipped = [s for s in skipped if s["kind"] == kind]
        if not kind_reports and not kind_skipped:
            continue
        _print_block(kind_reports, kind_skipped, kind)
        headline = float(np.mean([r["loss"] for r in kind_reports])) if kind_reports else 1.0
        result["bench_loss" if kind == "word" else "pair_loss"] = headline
    print(f"runtime_s:       {time.perf_counter() - t0:.1f}")

    if args.json:
        result["words"] = reports
        result["skipped"] = skipped
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1))
    if compare_payload is not None:
        old = compare_payload
        old_by_id = {w.get("id", w["word"]): w for w in old["words"]}
        for label in ("bench_loss", "pair_loss"):
            if label in old and label in result:
                print(f"--- compare vs {args.compare} (Δ{label}, negative = better) ---")
                print(f"{label}: {old[label]:.6f} -> {result[label]:.6f}  Δ {result[label] - old[label]:+.6f}")
        for r in sorted(reports, key=lambda r: r["loss"] - old_by_id.get(r["id"], {}).get("loss", r["loss"])):
            o = old_by_id.get(r["id"])
            if o:
                print(f"  {r['id']:<15} {o['loss']:.4f} -> {r['loss']:.4f}  Δ {r['loss'] - o['loss']:+.4f}")


if __name__ == "__main__":
    main()
