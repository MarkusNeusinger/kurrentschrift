"""The k0-protocol evaluation: candidates scored reference-free over ALL words.

The 63-word half of the campaign's standing measurement pair (the other half
is the dev-19 file-provider scoring of `tools.tracebench.run`): per word the
candidate-side structure counts against the COMPOSITION soll (`ductus_soll` —
since K0-S the one soll pipeline the structure guard shares), the soll
distance |cross − soll| + |zones − soll|, and `aiou` against the frozen ink
mask. With two candidate files the report pairs them: totals, per-word
soll-distance movement, the aiou losers against the standing −0.003 gate, and
the byte-identity classes (rows whose strokes are byte-equal between the two
files) that every identity and construction-prediction gate reads.

Until `aug21` every round re-wrote this as a scratchpad script (`kc-eval`,
`ke-k0-eval`, …) that died with its container; this module is the standing
form. Reads fixtures and candidate files only — no DB, no network, no solve.

    uv run python -m tools.tracebench.k0eval base-cand.json
    uv run python -m tools.tracebench.k0eval base-cand.json arm-cand.json --json out.json
"""

from __future__ import annotations

import argparse
import json
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


def eval_candidate(
    path: Path, reference: Reference, soll_rows: dict[str, tuple[SollRow, ...]], ids: list[str]
) -> dict[str, dict[str, object]]:
    """Per word: candidate counts, soll distance, aiou, and the byte identity key."""
    cands = file_provider(str(path))(reference, ids)
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
            "strokes_key": json.dumps(cand.strokes),
        }
    return rows


def _total(rows: dict[str, dict[str, object]]) -> int:
    return sum(int(r["soll_dist"]) for r in rows.values() if r["status"] == "ok")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracebench.k0eval", description=__doc__)
    parser.add_argument("base", type=Path, help="tracebench file-provider candidate JSON (the paired base)")
    parser.add_argument("candidate", type=Path, nargs="?", help="second candidate to pair against the base")
    parser.add_argument("--json", type=Path, help="write the full per-word report here")
    args = parser.parse_args()

    root = find_fixture_root(DEFAULT_FIXTURES_DIR, STYLE, WHICH)
    reference = load_reference(root)
    soll_rows, warnings = ductus_soll(reference.order, which=WHICH, style=STYLE, fixtures_root=DEFAULT_FIXTURES_DIR)
    for warning in warnings:
        print(f"WARN {warning}")
    ids = [i for i in reference.order if i in soll_rows]
    print(f"{len(ids)} words in the k0 scoring set")

    base = eval_candidate(args.base, reference, soll_rows, ids)
    print(f"== {args.base.name}: total soll distance {_total(base)}")
    if args.candidate is None:
        unscored = 0
        for sid in ids:
            row = base[sid]
            if row["status"] != "ok":
                unscored += 1
                continue
            print(
                f"  {sid:14s} cross {row['cross']}/{row['soll_cross']} zones {row['zones']}/{row['soll_zones']} "
                f"dist {row['soll_dist']} aiou {row['aiou']:.4f}"
            )
        if unscored:
            print(f"  ({unscored} words not in the candidate file)")
        if args.json:
            args.json.write_text(json.dumps({args.base.name: base}, indent=1, default=str))
            print(f"wrote {args.json}")
        return

    cand = eval_candidate(args.candidate, reference, soll_rows, ids)
    print(f"== {args.candidate.name}: total soll distance {_total(cand)}")
    better = worse = same = 0
    identical: list[str] = []
    moved: list[str] = []
    losers: list[tuple[str, float]] = []
    moved_deltas: list[float] = []
    unscored = 0
    for sid in ids:
        a, b = base[sid], cand[sid]
        if a["status"] != "ok" or b["status"] != "ok":
            if a["status"] != b["status"]:
                print(f"  {sid:14s} base={a['status']} cand={b['status']}")
            else:
                unscored += 1
            continue
        same_bytes = a["strokes_key"] == b["strokes_key"]
        (identical if same_bytes else moved).append(sid)
        d_soll = int(b["soll_dist"]) - int(a["soll_dist"])
        better += d_soll < 0
        worse += d_soll > 0
        same += d_soll == 0
        d_aiou = float(b["aiou"]) - float(a["aiou"])
        if not same_bytes:
            moved_deltas.append(d_aiou)
        if d_aiou < AIOU_LOSER_GATE:
            losers.append((sid, round(d_aiou, 4)))
        if d_soll or not same_bytes:
            print(
                f"  {sid:14s} dist {a['soll_dist']} -> {b['soll_dist']}  "
                f"aiou {a['aiou']:.4f} -> {b['aiou']:.4f} ({d_aiou:+.4f})  "
                f"{'identical' if same_bytes else 'moved'}"
            )
    if unscored:
        print(f"  ({unscored} words in neither candidate file)")
    print(f"\nsoll distance total: {_total(base)} -> {_total(cand)} ({better} better / {same} same / {worse} worse)")
    if moved_deltas:
        ordered = sorted(moved_deltas)
        median = (
            ordered[len(ordered) // 2]
            if len(ordered) % 2
            else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2
        )
        print(
            f"aiou over the {len(moved)} moved words: min {min(moved_deltas):+.4f} "
            f"median {median:+.4f} max {max(moved_deltas):+.4f}"
        )
    print(f"aiou losers (below {AIOU_LOSER_GATE}): {len(losers)}{' -> ' + str(losers) if losers else ''}")
    print(f"byte-identical rows: {len(identical)}/{len(identical) + len(moved)}; moved: {sorted(moved)}")
    if args.json:
        args.json.write_text(json.dumps({args.base.name: base, args.candidate.name: cand}, indent=1, default=str))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
