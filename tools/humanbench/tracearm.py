"""tracearm — one arm of a humanbench word round from a FOLLOWED word trace.

    uv run python -m tools.humanbench.tracearm --arm Basis \\
        --candidate temp/runden-sep07/base-cand.json --out temp/basis.json
    uv run python -m tools.humanbench.tracearm --arm K-E2 \\
        --candidate temp/runden-sep07/ke2-cand.json --out temp/ke2.json

The sibling of :mod:`tools.humanbench.wordarm` for the rounds whose candidate is
a TRACE and not a composition. ``wordarm`` composes a word and draws it as ink;
this module takes a trace somebody else followed — the ink-follower's own
``--candidate-out``, or any other `tools.tracebench` file-provider candidate —
and draws it as the judged CENTERLINE over the specimen at full strength, which
is the display the letter rounds 01/02 were judged in
(`docs/reference/menschliche-bewertung.md` §3.5, §8).

Two arms of this kind therefore ask §8's ACCURACY question („welche Linie folgt
der Tinte besser?"), not §8a's authenticity question: a follower arm changes
where the pen path runs over the plate's own ink, and there is no composed
stroke weight to judge. The page picks the display from the arm itself — a panel
with neither ``fills`` nor per-stroke widths keeps the cartographic casing and
leaves the crop unfaded — so nothing here has to be switched on.

The module composes NOTHING and measures nothing. It is a frame translation and
a join, for the same reason ``wordarm``'s docstring gives: an instrument that
computed its own candidate could drift away from the ruler that has to confirm
it. What it does have to get right is the frame, and that is a restatement of
`tools.tracebench.frames.BenchFrame.trace_to_bench` in the arm file's own terms:

* a stored trace is ``px = u·xh_px + tx`` and ``py = (baseline_row + ty) − v·xh_px``
  with ``baseline_row`` from the ROW's registration;
* an arm word is ``px = x·xh + tx`` and ``py = (entry baseline_row + ty) − y·xh``
  with the baseline row of the FIXTURE entry.

So the two ``ty`` differ by exactly the two baseline rows, and that difference is
the only arithmetic in this file. Getting it wrong is not silent: the trace then
misses the specimen by whole x-heights instead of the hundredths it lands within
when the frame is right.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.humanbench.build import DEFAULT_FIXTURES, DEFAULT_STYLE, REPO_ROOT, WORD_ARM_FORMAT, load_fixture_words
from tools.humanbench.wordarm import DEFAULT_SOURCE_ID, load_json, pin_registration
from tools.tracebench.candidates import CANDIDATE_FRAME, STATUS_OK


def entry_baseline_rows(root: Path) -> dict[str, float]:
    """Fixture entry id → the crop row of its baseline, from the frozen `word.json`.

    Read from the entry and from nothing else, the way `BenchFrame.from_entry`
    does: the frame of a specimen must not depend on any trace, or a re-followed
    candidate could move the ground it is judged against.
    """
    rows: dict[str, float] = {}
    for entry in load_fixture_words(root):
        meta = load_json(root / entry["id"] / "word.json")
        rows[entry["id"]] = float(meta["baseline_y"]) - float(meta["rect"][1])
    return rows


def trace_words(candidate: dict, baselines: dict[str, float]) -> tuple[dict[str, dict], list[str]]:
    """Candidate rows → the arm file's ``words`` block, plus what was skipped.

    A row is skipped and NAMED when it did not trace, when its specimen is not a
    scorable entry of this root, or when it carries no registration to translate.
    Silence would shorten the round and still look complete — the same rule the
    builder applies to a word only one arm draws.

    The registration is read the way ``candidates.file_provider`` reads it —
    ``row["measurements"]`` first, the row's top level as the fallback — because
    both shapes are the contract, not a preference: the ink-follower writes the
    flat one and `tools/inkpilot` the nested one. Reading only the flat one would
    drop every inkpilot row as „no xh_px" while the file itself is valid.
    """
    words: dict[str, dict] = {}
    skipped: list[str] = []
    for row in candidate.get("rows") or []:
        entry_id = str(row.get("specimen_id"))
        if row.get("status", STATUS_OK) != STATUS_OK or not row.get("strokes"):
            skipped.append(f"{entry_id} ({row.get('status') or 'no strokes'})")
            continue
        if entry_id not in baselines:
            skipped.append(f"{entry_id} (not a scorable entry of this root)")
            continue
        measurements = row.get("measurements") or {}
        registration = measurements.get("registration_px", row.get("registration_px")) or {}
        xh_px = measurements.get("xh_px", row.get("xh_px"))
        if not xh_px:
            skipped.append(f"{entry_id} (no xh_px)")
            continue
        # The row's own baseline row folded into `ty`, so the arm sits where the
        # bench frame puts the trace — see the module docstring.
        row_baseline = float(registration.get("baseline_row", baselines[entry_id]))
        ty = row_baseline + float(registration.get("ty") or 0.0) - baselines[entry_id]
        words[entry_id] = {
            "registration": {"xh_px": float(xh_px), "tx": float(registration.get("tx") or 0.0), "ty": ty},
            # No width and no fills: this arm IS a centerline, and the page
            # draws an unweighted stroke cased over the unfaded crop.
            "strokes": [{"points": [[float(p[0]), float(p[1])] for p in stroke]} for stroke in row["strokes"]],
        }
    return words, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.humanbench.tracearm",
        description="Turn a tracebench file-provider candidate into one arm of a humanbench word round.",
    )
    parser.add_argument(
        "--arm", required=True, help="the arm's name; it appears in the KEY and the stamp, never on the page"
    )
    parser.add_argument("--candidate", required=True, type=Path, help="a tracebench file-provider candidate")
    parser.add_argument("--out", required=True, type=Path, help="arm file to write")
    parser.add_argument("--fixtures", default=DEFAULT_FIXTURES, help=f"fixture root [{DEFAULT_FIXTURES}]")
    parser.add_argument("--style", default=DEFAULT_STYLE, help=f"fixture style directory [{DEFAULT_STYLE}]")
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID, help=f"fixture set directory [{DEFAULT_SOURCE_ID}]")
    parser.add_argument("--entries", default=None, help="comma-separated fixture entry ids to keep")
    parser.add_argument(
        "--registration-from",
        type=Path,
        default=None,
        help="take that arm's registration word by word, for a mechanism that does not move the placement",
    )
    parser.add_argument("--stamp", default=None, help="build timestamp [the system clock]")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fixtures = Path(args.fixtures) if Path(args.fixtures).is_absolute() else REPO_ROOT / args.fixtures
    root = fixtures / args.style / args.source_id
    candidate = load_json(args.candidate)
    # The frame literal is the candidate contract's own precondition: a trace in
    # crop pixels or a model's grid would be drawn as a catastrophic miss rather
    # than refused (tools/tracebench/candidates.py).
    if candidate.get("frame") != CANDIDATE_FRAME:
        raise SystemExit(f"{args.candidate}: frame is {candidate.get('frame')!r}, not {CANDIDATE_FRAME!r}")

    baselines = entry_baseline_rows(root)
    words, skipped = trace_words(candidate, baselines)
    if args.entries:
        keep = {e.strip() for e in args.entries.split(",") if e.strip()}
        words = {k: v for k, v in words.items() if k in keep}
    if not words:
        raise SystemExit(f"{args.candidate}: no row of this candidate draws a word of {root.name}")

    settings: dict[str, Any] = {
        "producer": "trace",
        "candidate": str(args.candidate),
        # Whatever the follower said about itself — label, weights, the excluded
        # rows. Carried verbatim so the round's stamp names the run that drew it.
        "candidate_label": candidate.get("label"),
        "candidate_tool": candidate.get("tool"),
        "candidate_weights": candidate.get("weights"),
        "candidate_excluded": candidate.get("excluded") or [],
        "exported_at": load_json(root / "manifest.json").get("exported_at"),
        "failed": skipped,
    }
    if args.registration_from:
        reference = load_json(args.registration_from).get("words") or {}
        missing = pin_registration(words, reference)
        settings["registration"] = f"pinned to {args.registration_from}"
        if missing:
            print(f"WARNING: {len(missing)} word(s) had no pinned registration and keep their own: {missing[:8]}")
    else:
        settings["registration"] = "own (the followed row's)"

    payload = {
        "format": WORD_ARM_FORMAT,
        "arm": args.arm,
        "style": args.style,
        "source_id": args.source_id,
        "fixture_root": str(root.relative_to(REPO_ROOT)) if root.is_relative_to(REPO_ROOT) else str(root),
        "tool": "tools.humanbench.tracearm",
        "built_at": args.stamp or datetime.now(UTC).isoformat(timespec="seconds"),
        "settings": settings,
        "words": words,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"arm {args.arm}: {len(words)} traced words from {root.name} → {args.out}")
    print(f"  candidate {candidate.get('label')!r} · registration {settings['registration']}")
    if skipped:
        print(f"  WARNING: {len(skipped)} row(s) skipped: {', '.join(skipped[:8])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
