"""The k0-protocol evaluation: candidates scored reference-free over ALL words.

The 63-word half of the campaign's standing measurement pair (the other half
is the dev-19 file-provider scoring of `tools.tracebench.run`): per word the
candidate-side structure counts against the COMPOSITION soll (`ductus_soll` —
since K0-S the one soll pipeline the structure guard shares), the soll
distance |cross − soll| + |zones − soll|, and `aiou` against the frozen ink
mask. With two candidate files the report pairs them: totals, per-word
soll-distance movement, the aiou losers against the standing −0.003 gate, and
the stroke-identity classes (rows whose parsed strokes are structurally equal
between the two files) that every identity and construction-prediction gate
reads. The `--json` report carries everything except the strokes themselves —
they serve only the in-process identity check.

Until `aug21` every round re-wrote this as a scratchpad script (`kc-eval`,
`ke-k0-eval`, …) that died with its container; this module is the standing
form. Reads fixtures and candidate files only — no DB, no network, no solve.

    uv run python -m tools.tracebench.k0eval base-cand.json
    uv run python -m tools.tracebench.k0eval base-cand.json arm-cand.json --json out.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.tracebench.candidates import file_provider
from tools.tracebench.counters import crossing_points, structure_zones
from tools.tracebench.metric import aiou
from tools.tracebench.reference import DEFAULT_FIXTURES_DIR, Reference, load_reference
from tools.tracebench.run import find_fixture_root
from tools.tracebench.soll import SollRow, ductus_soll


STYLE = "suetterlin"
WHICH = "words"
# The standing per-word aiou gate of the §14 chain arms (K-C onward): a word
# below this delta is a loser, anything above is measurement noise.
AIOU_LOSER_GATE = -0.003

# The follower weights that define a candidate's STACK — which guard it ran
# under, where its soll came from, whether the ink mask was on. Two files that
# differ here are not a base and its arm; they are two different instruments,
# and every paired number below is then a comparison between instruments, not
# between candidates. That mistake was made twice in two days (the L-U
# "Kette" row on aug25 and the v5 measurement on aug26 both paired the
# UNGUARDED follower against a guarded arm — 36 "aiou losers" that were the
# base's structure destruction, not the arm's cost), which is why the pairing
# now reads the flags off both files and says so before the first number.
STACK_FLAGS = (
    "structure_guard",
    "structure_guard_soll",
    "structure_guard_ratchet",
    "structure_guard_zone_units",
    "soll_source",
    "ink_evidence",
)


def guard_stack(path: Path) -> dict[str, object]:
    """The stack a candidate file was produced under, read off its first row's weights.

    Empty when the file carries no follower meta (a stored `traced` row, an
    InkSight or routeg candidate) — those are not follower stacks, and the
    caller prints them as such rather than as "unguarded".
    """
    payload = json.loads(path.read_text())
    for entry in payload.get("rows") or []:
        weights = (entry.get("meta") or {}).get("weights")
        if weights:
            return {flag: weights.get(flag) for flag in STACK_FLAGS}
    return {}


def guard_outcome(meta: dict | None) -> str:
    """What the structure guard did to ONE word, from the follower's round records.

    `revert-init` — round 1 rejected, the word keeps the chain init and was
    never followed; `revert-r<n>` — a later round rejected, the word keeps round
    n; `zonal` — a round was accepted only after the K0-Z zonal re-solve pinned
    anchors; `halved` — accepted after `max_delta` was halved; `clean` — every
    round accepted at its first attempt; `unguarded` — the rounds carry no
    guard records at all. These are the tiers the aug26 autopsy sorted the
    aiou losses into (§14 „Kette v5"); the column exists so that sorting is
    read off the file instead of re-derived by hand.
    """
    rounds = [record for run in (meta or {}).get("rounds") or [] for record in run]
    if not rounds:
        return "no-rounds"
    if not any("structure_rejected" in record for record in rounds):
        return "unguarded"
    for record in rounds:
        if record.get("structure_rejected"):
            number = int(record.get("round") or 0)
            return "revert-init" if number <= 1 else f"revert-r{number - 1}"
    if any((record.get("structure_zonal") or {}).get("pinned") for record in rounds):
        return "zonal"
    if any(record.get("structure_retries") for record in rounds):
        return "halved"
    return "clean"


def _row_meta(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text())
    return {entry.get("specimen_id"): entry.get("meta") or {} for entry in payload.get("rows") or []}


def eval_candidate(
    path: Path, reference: Reference, soll_rows: dict[str, tuple[SollRow, ...]], ids: list[str]
) -> dict[str, dict[str, object]]:
    """Per word: candidate counts, soll distance, aiou, and the strokes for identity."""
    cands = file_provider(str(path))(reference, ids)
    metas = _row_meta(path)
    rows: dict[str, dict[str, object]] = {}
    for sid in ids:
        cand = cands.get(sid)
        entry = reference.entries[sid]
        if cand is None or not cand.ok:
            rows[sid] = {"status": "missing" if cand is None else cand.status}
            continue
        strokes = entry.frame.trace_to_bench(cand.strokes, cand.registration_px, cand.xh_px)
        n_cross = int(len(crossing_points(strokes)))
        n_zones = int(len(structure_zones(strokes).retrace_mids))
        comp = soll_rows[sid][1]
        rows[sid] = {
            "status": "ok",
            "cross": n_cross,
            "zones": n_zones,
            "soll_cross": comp.crossings,
            "soll_zones": comp.zones,
            "soll_dist": abs(n_cross - comp.crossings) + abs(n_zones - comp.zones),
            "aiou": aiou([entry.frame.bench_to_crop_px(s) for s in strokes], entry.ink_mask()).value,
            "guard": guard_outcome(metas.get(sid)),
            "strokes": cand.strokes,
        }
    return rows


def _total(rows: dict[str, dict[str, object]]) -> int:
    return sum(int(r["soll_dist"]) for r in rows.values() if r["status"] == "ok")


def pair_rows(
    base: dict[str, dict[str, object]], cand: dict[str, dict[str, object]], ids: list[str]
) -> dict[str, object]:
    """The paired classification every §14 gate reads — pure, printing stays in main.

    Returns per class the word lists: soll-distance movement (better/same/
    worse), stroke identity (identical/moved, compared on the parsed strokes),
    the aiou losers below the standing gate, the aiou deltas of the moved
    words, plus the rows scored on neither side (unscored, a per-status
    Counter) and those failing on one side only (mismatched).
    """
    out: dict[str, object] = {
        "better": [],
        "same": [],
        "worse": [],
        "identical": [],
        "moved": [],
        "losers": [],
        "moved_deltas": [],
        "unscored": Counter(),
        "mismatched": [],
    }
    for sid in ids:
        a, b = base[sid], cand[sid]
        if a["status"] != "ok" or b["status"] != "ok":
            if a["status"] != b["status"]:
                out["mismatched"].append(sid)
            else:
                out["unscored"][str(a["status"])] += 1
            continue
        same_strokes = a["strokes"] == b["strokes"]
        out["identical" if same_strokes else "moved"].append(sid)
        d_soll = int(b["soll_dist"]) - int(a["soll_dist"])
        out["better" if d_soll < 0 else "worse" if d_soll > 0 else "same"].append(sid)
        d_aiou = float(b["aiou"]) - float(a["aiou"])
        if not same_strokes:
            out["moved_deltas"].append(d_aiou)
        if d_aiou < AIOU_LOSER_GATE:
            out["losers"].append((sid, round(d_aiou, 4)))
    return out


def report_rows(rows: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """The JSON-report view of the rows: the strokes serve only the in-process
    identity check and would multiply the report's size, so they stay out."""
    return {sid: {k: v for k, v in r.items() if k != "strokes"} for sid, r in rows.items()}


def scoring_ids(order: list[str], soll_rows: dict[str, tuple[SollRow, ...]]) -> list[str]:
    """The words with a composition soll, in reference order — empty is a hard
    error: the soll distance is the core metric, so a run without soll targets
    would be a meaningless evaluation that LOOKS like a quiet one."""
    ids = [i for i in order if i in soll_rows]
    if not ids:
        raise SystemExit("no words with a composition soll — ductus_soll returned nothing; refusing to score")
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench.k0eval", description=__doc__)
    parser.add_argument("base", type=Path, help="tracebench file-provider candidate JSON (the paired base)")
    parser.add_argument("candidate", type=Path, nargs="?", help="second candidate to pair against the base")
    parser.add_argument("--json", type=Path, help="write the full per-word report here")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help="fixture root the reference AND the composition soll are read from (default: the frozen set). "
        "A candidate solved on a patched root (a Laufform candidate map, §14 LF3b-W) is scored against "
        "THAT root's soll — the soll moves with the map, so the frozen root's would be the wrong ruler.",
    )
    args = parser.parse_args()

    root = find_fixture_root(args.fixtures, STYLE, WHICH)
    reference = load_reference(root)
    soll_rows, warnings = ductus_soll(reference.order, which=WHICH, style=STYLE, fixtures_root=args.fixtures)
    for warning in warnings:
        print(f"WARN {warning}")
    ids = scoring_ids(reference.order, soll_rows)
    print(f"{len(ids)} words in the k0 scoring set")

    base_stack = guard_stack(args.base)
    print(f"stack {args.base.name}: {base_stack or 'no follower meta'}")
    stack_warning = ""
    if args.candidate is not None:
        cand_stack = guard_stack(args.candidate)
        print(f"stack {args.candidate.name}: {cand_stack or 'no follower meta'}")
        if base_stack and cand_stack and base_stack != cand_stack:
            differing = sorted(flag for flag in STACK_FLAGS if base_stack.get(flag) != cand_stack.get(flag))
            stack_warning = (
                f"WARN stacks differ on {', '.join(differing)} — check these against the pre-registration: "
                "a §14 gate reads only when every differing flag IS the knob under test. Anything else here "
                "means the pairing compares instruments, not candidates (werkzeuge.md, Mess-Liturgie)."
            )
            print(stack_warning)

    base = eval_candidate(args.base, reference, soll_rows, ids)
    print(f"== {args.base.name}: total soll distance {_total(base)}")
    if args.candidate is None:
        unscored: Counter[str] = Counter()
        for sid in ids:
            row = base[sid]
            if row["status"] != "ok":
                unscored[str(row["status"])] += 1
                continue
            print(
                f"  {sid:14s} cross {row['cross']}/{row['soll_cross']} zones {row['zones']}/{row['soll_zones']} "
                f"dist {row['soll_dist']} aiou {row['aiou']:.4f}"
            )
        if unscored:
            detail = ", ".join(f"{status} {n}" for status, n in sorted(unscored.items()))
            print(f"  ({sum(unscored.values())} words unscored: {detail})")
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps({args.base.name: report_rows(base)}, indent=1))
            print(f"wrote {args.json}")
        return

    cand = eval_candidate(args.candidate, reference, soll_rows, ids)
    print(f"== {args.candidate.name}: total soll distance {_total(cand)}")
    pairing = pair_rows(base, cand, ids)
    mismatched = set(pairing["mismatched"])
    identical = set(pairing["identical"])
    for sid in ids:
        a, b = base[sid], cand[sid]
        if sid in mismatched:
            print(f"  {sid:14s} base={a['status']} cand={b['status']}")
            continue
        if a["status"] != "ok" or b["status"] != "ok":
            continue
        d_soll = int(b["soll_dist"]) - int(a["soll_dist"])
        d_aiou = float(b["aiou"]) - float(a["aiou"])
        if d_soll or sid not in identical:
            print(
                f"  {sid:14s} dist {a['soll_dist']} -> {b['soll_dist']}  "
                f"aiou {a['aiou']:.4f} -> {b['aiou']:.4f} ({d_aiou:+.4f})  "
                f"{'identical' if sid in identical else 'moved'}  guard {a.get('guard')} -> {b.get('guard')}"
            )
    unscored = pairing["unscored"]
    if unscored:
        detail = ", ".join(f"{status} {n}" for status, n in sorted(unscored.items()))
        print(f"  ({sum(unscored.values())} words unscored on both sides: {detail})")
    print(
        f"\nsoll distance total: {_total(base)} -> {_total(cand)} "
        f"({len(pairing['better'])} better / {len(pairing['same'])} same / {len(pairing['worse'])} worse)"
    )
    moved_deltas = pairing["moved_deltas"]
    if moved_deltas:
        ordered = sorted(moved_deltas)
        median = (
            ordered[len(ordered) // 2]
            if len(ordered) % 2
            else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2
        )
        print(
            f"aiou over the {len(pairing['moved'])} moved words: min {min(moved_deltas):+.4f} "
            f"median {median:+.4f} max {max(moved_deltas):+.4f}"
        )
    losers = pairing["losers"]
    print(f"aiou losers (below {AIOU_LOSER_GATE}): {len(losers)}{' -> ' + str(losers) if losers else ''}")
    print(
        f"stroke-identical rows: {len(identical)}/{len(identical) + len(pairing['moved'])}; "
        f"moved: {sorted(pairing['moved'])}"
    )
    # The guard's per-word outcome, tallied on the arm — the tiers of the
    # aug26 autopsy, read off the file: how many words the guard never touched,
    # how many it bent, how many it reverted to the init and never followed.
    outcomes = Counter(str(cand[sid].get("guard")) for sid in ids if cand[sid]["status"] == "ok")
    print(f"guard outcomes on {args.candidate.name}: " + ", ".join(f"{k} {n}" for k, n in sorted(outcomes.items())))
    if stack_warning:
        # Last, next to the verdict lines, so it is the thing the eye lands on.
        print(stack_warning)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "stacks": {args.base.name: base_stack, args.candidate.name: cand_stack},
                    "stack_mismatch": bool(stack_warning),
                    args.base.name: report_rows(base),
                    args.candidate.name: report_rows(cand),
                },
                indent=1,
            )
        )
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
