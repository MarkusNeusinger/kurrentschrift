"""Measure `import api.main` INSIDE the built API image and print the numbers.

Piped into the image's own interpreter by the CI job „Image (build + container
smoke)":

    docker run --rm -i -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 \
      kurrentschrift-api:ci /app/.venv/bin/python - < .github/scripts/importtime_report.py

It lives here and travels over stdin rather than living in `tools/`, because
the API image deliberately does not ship `tools/` (CLAUDE.md's never-import
invariant) — and because a measurement has no business inside the artefact it
measures.

**Output only: this never fails a build.** Import time on a shared GitHub
runner swings by more than any threshold worth setting would allow, so a gate
here would be noise with a veto. What it is good for is the number a later
round quotes, taken in the real image — same layers, same interpreter patch
level, same precompiled bytecode — which is the one thing the two local rounds
of 2026-09-04/05 could not do (`docs/notes/serve-image-importtime-2026-09-05.md`
§„Grenzen dieser Runde").

Three things get printed:

* the total, as the minimum of N fresh interpreters (a minimum, not a mean: on
  a loaded machine the mean measures the machine, the minimum measures the
  import);
* the ten most expensive modules by SELF time — only self time is additive,
  the cumulative column counts every nested import again;
* the SERVE-vs-BOTH split, using the module sets that
  `docs/notes/serve-image-importgraph-2026-09-04.md` §(c) fixed verbatim, so
  the difference stays comparable across rounds. Change a set here and the
  comparison with those two rounds is gone.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time


RUNS = 5

# Verbatim from `serve-image-importgraph-2026-09-04.md` §(c) — the import cache
# makes the exact module list and its order material to the difference, which is
# why that note wrote them down instead of describing them.
BARE = "pass"
SERVE = (
    "import fastapi, jwt, httpx, orjson, PIL.Image; "
    "import core.database, core.template, core.widths, core.compose, core.shaping, core.rounding"
)
BOTH = SERVE + (
    "; import core.pipeline, core.fit, core.chart, core.extract, core.quality, "
    "core.quality_suetterlin, core.suetterlin, core.word_metric, core.laufform, core.aggregate"
)
MAIN = "import api.main"

SETS = (("BARE", BARE), ("SERVE", SERVE), ("BOTH", BOTH), ("MAIN", MAIN))

# `-X importtime` writes `import time: self | cumulative | nested.module.name`,
# the leading blanks of the third column encoding the import depth. Only the
# self time is additive — the cumulative column counts every nested import again.
IMPORTTIME_LINE = re.compile(r"^import time:\s*(\d+)\s*\|\s*\d+\s*\|\s*(\S+)")


def _child_env() -> dict[str, str]:
    """BLAS pinned for every child, per the CLAUDE.md measurement guardrail."""
    env = dict(os.environ)
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    return env


def min_wall_ms(statement: str, runs: int = RUNS) -> float:
    """Wall clock of a fresh interpreter running `statement`, minimum of `runs`."""
    best = float("inf")
    env = _child_env()
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run([sys.executable, "-c", statement], check=True, env=env)
        best = min(best, (time.perf_counter() - start) * 1000)
    return best


def self_times() -> tuple[list[tuple[int, str]], int]:
    """Per-module self time (µs) of one `-X importtime` run, and their sum."""
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", MAIN], check=True, env=_child_env(), capture_output=True, text=True
    )
    rows = []
    for line in proc.stderr.splitlines():
        match = IMPORTTIME_LINE.match(line)
        if match:
            rows.append((int(match.group(1)), match.group(2)))
    return sorted(rows, reverse=True), sum(self_us for self_us, _ in rows)


def main() -> int:
    print(f"python {sys.version.split()[0]} · {sys.executable} · minimum of {RUNS} fresh interpreters")
    print("BLAS pinned (OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1). Numbers only — nothing here gates.\n")

    measured = {name: min_wall_ms(statement) for name, statement in SETS}

    print("(a) total")
    print(f"    import api.main   {measured['MAIN']:7.1f} ms wall clock, interpreter start included")
    print(
        f"    bare interpreter  {measured['BARE']:7.1f} ms  → the import itself ≈ {measured['MAIN'] - measured['BARE']:.1f} ms\n"
    )

    rows, total_self_us = self_times()
    print(f"(b) the ten most expensive modules by SELF time ({total_self_us / 1000:.1f} ms over {len(rows)} modules)")
    for self_us, module in rows[:10]:
        print(f"    {self_us / 1000:7.1f} ms  {module}")
    print()

    trace_half = measured["BOTH"] - measured["SERVE"]
    print("(c) SERVE vs BOTH — the trace half's share of the import")
    print(f"    SERVE (serve half)          {measured['SERVE']:7.1f} ms")
    print(f"    BOTH  (SERVE + trace half)  {measured['BOTH']:7.1f} ms")
    share = 100 * trace_half / measured["MAIN"] if measured["MAIN"] else 0.0
    print(f"    BOTH - SERVE                {trace_half:7.1f} ms  = {share:.1f} % of import api.main")
    print("\n    Module sets verbatim from docs/notes/serve-image-importgraph-2026-09-04.md §(c);")
    print("    local comparison values in docs/notes/serve-image-importtime-2026-09-05.md.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    # Broad on purpose: a measurement must never fail a build. A renamed module
    # in one of the sets should cost the reader a number, not the PR its check.
    except Exception as exc:
        print(f"importtime report skipped: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(0) from None
