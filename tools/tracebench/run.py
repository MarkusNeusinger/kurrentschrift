"""Run the trace bench: score an automatic word tracing against the hand-made one.

Hermetic and deterministic — no DB, no HTTP, no writes: the references, the
crops and the ink masks all come out of the frozen wordbench fixture roots, and
the candidate is either a stored row, a recomputed chain fit or a file.

    uv run python -m tools.tracebench.run [--style suetterlin] [--set words]
        [--split dev|confirm|all] [--words die,mit] [--candidate chain]
        [--candidate-file follow.json] [--label follow-v1] [--jobs 4]
        [--json report.json] [--csv rows.csv] [--compare baseline.json]
        [--resample-step 0.02] [--mark-refit]

Three rules the CLI enforces rather than trusts (qualitaetsmetrik.md §14):

* **The dev split is frozen and append-never.** `TRACEBENCH_DEV_IDS` are the ten
  words the author re-traced on 2026-08-13; every id must be present as an
  `authored`, non-`frame_stale` row or the run dies naming it — a ruler that
  lost a word would report a better number for the rest.
* **`--split confirm` is the held-out reserve**, i.e. every authored word that is
  NOT in the dev set, and it refuses to run under five words: a confirmation on
  three words is theatre. `--split all` prints that a combined number is not a
  held-out number; `--words` prints that a hand-picked selection is not
  pre-registered.
* **`--candidate authored` is the identity gate.** A trace scored against itself
  must land on dtw = 0, chamfer = 0 and every counter matched. `identity gate:
  FAIL` exits non-zero, because from there on no candidate number means anything.

Output contract — one stable line per word, then the block, then (with
`--compare`) the paired deltas. Every scored line carries every column, zeros
included; a failed or skipped word prints its reason instead of a number.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Sequence

from tools.tracebench.candidates import (
    PROVIDER_NAMES,
    STATUS_SKIPPED,
    Candidate,
    Provider,
    authored_provider,
    chain_provider,
    file_provider,
    traced_provider,
)
from tools.tracebench.counters import RESAMPLE_STEP_UNITS
from tools.tracebench.reference import (
    DEFAULT_FIXTURES_DIR,
    EXCLUDED_FRAME_STALE,
    MANIFEST_FILE,
    Reference,
    ReferenceEntry,
    load_reference,
)
from tools.tracebench.sets import TRACEBENCH_DEV_IDS
from tools.tracebench.soll import ductus_soll, soll_row_fields
from tools.tracebench.summary import (
    compare,
    identity_gate,
    print_block,
    print_comparison,
    print_rows,
    score_word,
    summarize,
)


STYLES = ("suetterlin", "kurrent", "offenbacher")
# The set the frozen development split lives in. The ten dev words are Abb.-19
# words; on any other set the split is undefined rather than empty, and saying
# so beats silently scoring a different population.
DEV_SET = "words"
# Below this a confirmation run is theatre rather than a test (§14).
MIN_CONFIRM_WORDS = 5


def find_fixture_root(fixtures: Path, style: str, which: str) -> Path:
    """The fixture root whose manifest declares `set == which` (wordbench's rule).

    The directory name is not the discriminator — a word set freezes into
    `<source_id>` and its pairs into `<source_id>-pairs` — so the manifest's own
    `set` field decides, exactly as `tools/wordbench/run.py` and
    `tools/wordlab/cases.py` do it.
    """
    style_root = fixtures / style
    for manifest_path in sorted(style_root.glob(f"*/{MANIFEST_FILE}")):
        if json.loads(manifest_path.read_text()).get("set", "words") == which:
            return manifest_path.parent
    raise SystemExit(f"no {which!r} fixtures under {style_root} — run tools/wordbench/export_fixtures first")


def assert_dev_set_intact(reference: Reference) -> None:
    """§14's startup assertion: the ruler must still have all ten dev words.

    Hard failure, naming the ids and — where the artifact says so — the reason
    they dropped out. A missing dev word does not shrink the bench, it silently
    changes which population the headline describes.
    """
    stale = set(reference.excluded.get(EXCLUDED_FRAME_STALE, []))
    available = set(reference.authored_ids())
    missing = sorted(i for i in TRACEBENCH_DEV_IDS if i not in available)
    if not missing:
        return
    reasons = ", ".join(f"{i} ({'frame_stale' if i in stale else 'not authored / absent'})" for i in missing)
    raise SystemExit(
        f"the ruler lost a word: {len(missing)} of {len(TRACEBENCH_DEV_IDS)} development ids are not usable "
        f"authored rows in {reference.root / 'word_instances.json'} — {reasons}. "
        "Re-export the word traces (`--only word-instances`) before reading any number."
    )


def select_split(reference: Reference, split: str, words: str | None) -> tuple[list[str], list[str]]:
    """`(specimen ids in manifest order, warnings to print)` for one run.

    `--words` is applied ON TOP of the split, and says so: a hand-picked
    selection is a debugging aid, never a pre-registered result.
    """
    authored = reference.authored_ids()
    warnings: list[str] = []
    if split == "dev":
        ids = [i for i in authored if i in TRACEBENCH_DEV_IDS]
    elif split == "confirm":
        ids = [i for i in authored if i not in TRACEBENCH_DEV_IDS]
        if len(ids) < MIN_CONFIRM_WORDS:
            raise SystemExit(
                f"--split confirm has {len(ids)} authored words outside the development set "
                f"(minimum {MIN_CONFIRM_WORDS}) — a confirmation on {len(ids)} words is theatre, "
                "trace more words in the word editor first"
            )
    else:
        ids = list(authored)
        warnings.append(
            "warning: --split all mixes the development words into the number — a combined result is NOT a "
            "held-out number and must never be quoted as a confirmation"
        )
    if words:
        wanted = {w.strip() for w in words.split(",") if w.strip()}
        ids = [i for i in ids if i in wanted or reference.entries[i].word in wanted]
        warnings.append(
            f"warning: --words restricts the run to {len(ids)} hand-picked words — not a pre-registered split"
        )
    return ids, warnings


def build_provider(args: argparse.Namespace) -> tuple[Provider, str]:
    """`(provider, label)` for `--candidate` — the label travels into every row."""
    if args.mark_refit and args.candidate != "chain":
        raise SystemExit(
            "--mark-refit changes how the CHAIN candidate is built and does nothing for --candidate "
            f"{args.candidate} — a stored row and a file are read as they are"
        )
    if args.candidate == "file":
        if not args.candidate_file:
            raise SystemExit("--candidate file needs --candidate-file <path>")
        return file_provider(args.candidate_file), args.label or args.candidate_file.name
    if args.candidate == "chain":
        provider = chain_provider(
            style=args.style, which=args.which, fixtures_root=args.fixtures, mark_refit=args.mark_refit
        )
        # A1 is a VARIANT of the baseline, so it may not answer to the baseline's
        # name: an unlabelled run is called `chain+marks`, and a report cannot be
        # mistaken for the frozen `chain` number it has to be compared against.
        return provider, args.label or ("chain+marks" if args.mark_refit else "chain")
    if args.candidate == "authored":
        return authored_provider, args.label or "authored"
    return traced_provider, args.label or "traced"


def _score_job(payload: tuple[ReferenceEntry, Candidate, str, str, float]) -> dict[str, Any]:
    """One word's scoring — module level so `--jobs` can pickle it."""
    entry, candidate, label, split, step = payload
    return score_word(entry, candidate, label=label, split=split, resample_step=step)


def score_all(
    reference: Reference,
    candidates: dict[str, Candidate],
    ids: Sequence[str],
    *,
    label: str,
    split: str,
    resample_step: float,
    jobs: int = 1,
) -> list[dict[str, Any]]:
    """Every selected word scored, in the input (= manifest) order.

    `ProcessPoolExecutor.map` yields in input order, so `--jobs` changes the
    runtime and nothing else — a bench whose row order depended on scheduling
    could not be diffed against yesterday's report.
    """
    payloads = [
        (
            reference.entries[i],
            candidates.get(i, Candidate([], {}, None, STATUS_SKIPPED, "the provider named no candidate")),
            label,
            split,
            resample_step,
        )
        for i in ids
    ]
    if jobs > 1 and len(payloads) > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(pool.map(_score_job, payloads))
    return [_score_job(p) for p in payloads]


def write_csv(rows: Sequence[dict], path: Path) -> None:
    """The rows as a flat CSV — first row's columns first, later extras appended."""
    if not rows:
        return
    fields: list[str] = []
    for row in rows:
        fields.extend(k for k in row if k not in fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracebench", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--style", default="suetterlin", choices=STYLES)
    parser.add_argument("--set", dest="which", default="words", help="fixture set (words | pairs | a custom set name)")
    parser.add_argument(
        "--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR, help="fixture root (default: the frozen set)"
    )
    parser.add_argument(
        "--split",
        default="dev",
        choices=("dev", "confirm", "all"),
        help="dev = the ten frozen development words; confirm = every OTHER authored word (the held-out "
        "reserve, refused under five); all = both, which is not a held-out number",
    )
    parser.add_argument("--words", help="comma-separated id/word filter applied on top of the split")
    parser.add_argument("--candidate", default="chain", choices=PROVIDER_NAMES)
    parser.add_argument("--candidate-file", type=Path, help="candidate JSON for --candidate file")
    parser.add_argument(
        "--mark-refit",
        action="store_true",
        help="measure A1 (tintenfolger.md §7.3): refit the marks (i-dot, umlaut, u-bow) onto the ink the "
        "body did not claim after the chain solve. --candidate chain only; the run is labelled chain+marks "
        "because it is a variant of the baseline, not the baseline",
    )
    parser.add_argument("--label", help="name of this candidate in the rows (default: the provider's name)")
    parser.add_argument("--jobs", type=int, default=1, help="parallel scoring workers (order-preserving)")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--csv", type=Path, help="write the per-word rows here")
    parser.add_argument("--compare", type=Path, help="previous --json report to pair against")
    parser.add_argument(
        "--resample-step",
        type=float,
        default=RESAMPLE_STEP_UNITS,
        help=f"arc-length resampling step in x-heights (default {RESAMPLE_STEP_UNITS}; the documented sweep "
        "of §14 is 0.02/0.03/0.05 and a non-default step is its own measurement)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    started = time.perf_counter()

    root = find_fixture_root(args.fixtures, args.style, args.which)
    try:
        reference = load_reference(root)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from None

    # The dev split is defined on the word plates. On another set it is not
    # empty but UNDEFINED, so the assertion is scoped rather than faked.
    if args.which == DEV_SET:
        assert_dev_set_intact(reference)
    elif args.split in ("dev", "confirm"):
        raise SystemExit(
            f"--split {args.split} is defined on the {DEV_SET!r} set only (the frozen development ids are "
            f"Abb.-19 words); run --set {DEV_SET} or --split all"
        )

    ids, warnings = select_split(reference, args.split, args.words)
    for line in warnings:
        print(line)
    if not ids:
        raise SystemExit(f"no words selected (split {args.split!r}, set {args.which!r}) — nothing to score")

    provider, label = build_provider(args)
    print(
        f"tracebench: {len(ids)} words · set {args.which} · split {args.split} · candidate {label} · root {root.name}"
    )
    candidates = provider(reference, ids)
    rows = score_all(
        reference,
        candidates,
        ids,
        label=label,
        split=args.split,
        resample_step=args.resample_step,
        jobs=max(1, args.jobs),
    )

    # The ductus target beside every row (the owner's standing test: a hand
    # count outside the target is a finding, a candidate count an invention).
    # Report-only: no scored number reads these fields, and a fixture root
    # without composition data degrades to a warning.
    soll, soll_warnings = ductus_soll(ids, which=args.which, style=args.style, fixtures_root=args.fixtures)
    for row in rows:
        entry = soll.get(str(row.get("id")))
        if entry is not None:
            row.update(soll_row_fields(entry))
    for line in soll_warnings:
        print(f"  {line}")

    print_rows(rows)
    summary = summarize(rows, excluded=reference.excluded_counts())
    print_block(summary, label=label, split=args.split)
    if soll:
        cross_pairs = [
            (r["cross_ref"], r["soll_cross"])
            for r in rows
            if r.get("soll_cross") is not None and r.get("cross_ref") is not None
        ]
        zone_pairs = [
            (r["retrace_ref"], r["soll_zones"])
            for r in rows
            if r.get("soll_zones") is not None and r.get("retrace_ref") is not None
        ]
        if cross_pairs:
            print(
                f"soll_cross_agree: {sum(1 for a, b in cross_pairs if a == b)}/{len(cross_pairs)} (Hand == Komposition)"
            )
        else:
            print("soll_cross_agree: n/a (no scored row carries a target)")
        if zone_pairs:
            print(
                f"soll_zones_agree: {sum(1 for a, b in zone_pairs if a == b)}/{len(zone_pairs)} (Hand == Komposition)"
            )
        else:
            print("soll_zones_agree: n/a (no scored row carries a target)")
    print(f"resample_step:   {args.resample_step}")
    print(f"runtime_s:       {time.perf_counter() - started:.1f}")

    result = {
        "style": args.style,
        "set": args.which,
        "split": args.split,
        "candidate": label,
        "resample_step": args.resample_step,
        "hand_id": reference.hand_id,
        "summary": summary,
        "rows": rows,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    if args.csv:
        write_csv(rows, args.csv)
    if args.compare:
        old = json.loads(args.compare.read_text())
        print_comparison(compare(old.get("rows", []), rows), against=str(args.compare))

    # The identity gate LAST, so its verdict is the final line of the run: with
    # a FAIL nothing above it may be read (§14 Kill-Kriterien).
    if args.candidate == "authored":
        failures = identity_gate(rows)
        print(f"identity gate:   {'PASS' if not failures else 'FAIL'}")
        for line in failures[:20]:
            print(f"  {line}")
        if failures:
            raise SystemExit(
                f"identity gate FAILED on {len(failures)} checks — the RULER is broken, "
                "no candidate number is read until it is fixed"
            )


if __name__ == "__main__":
    main()
