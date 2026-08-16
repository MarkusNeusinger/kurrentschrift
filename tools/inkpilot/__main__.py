"""CLI: pilot the fixture words and write a tracebench candidate file.

    uv run python -m tools.inkpilot [ids ...] [--all] [--set words]
        [--out temp/inkpilot.json]

Measurement only: reads the frozen fixtures, writes one candidate JSON.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from tools.inkpilot.pilot import candidate_row, pilot_word, write_candidates
from tools.wordlab.cases import iter_fixture_word_cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="fixture case ids; default with --all: the whole set")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--out", type=Path, default=Path("temp/inkpilot.json"))
    args = parser.parse_args(argv)
    if not args.ids and not args.all:
        parser.error("name case ids or pass --all — otherwise the run writes an empty candidate file")

    wanted = set(args.ids)
    rows = []
    for case in iter_fixture_word_cases(which=args.which, style=args.style):
        if not case.scorable or case.skel is None:
            continue
        if not args.all and case.id not in wanted:
            continue
        t0 = time.perf_counter()
        try:
            strokes, detail = pilot_word(case)
        except Exception as exc:  # pragma: no cover - survey tool
            print(f"  {case.id:14} FAILED {exc!r}", file=sys.stderr, flush=True)
            continue
        rows.append(candidate_row(case, strokes, detail))
        print(
            f"  {case.id:14} ok  strokes {len(strokes):2d}  nodes {detail['nodes']:3d} "
            f"edges {detail['edges']:3d}  {time.perf_counter() - t0:6.1f}s",
            flush=True,
        )
    write_candidates(rows, args.out, label="inkpilot")
    print(f"wrote {args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
