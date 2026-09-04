"""`python -m tools.docs_budget` — the reading-cost gate.

    uv run python -m tools.docs_budget check    # the three rules (the CI gate)
    uv run python -m tools.docs_budget report   # the table, for setting a budget

Checks only; nothing here writes a file, touches a remote or reads a database.
The rules and the reason they exist are in `__init__`'s docstring.
"""

from __future__ import annotations

import argparse
import os
import sys

from tools.docs_budget import BUDGETS, BudgetError, check_all, measure


def _fail(message: str) -> None:
    # GitHub turns the `::error::` line into an annotation on the PR's checks tab.
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    print(f"{prefix}{message}", file=sys.stderr)


def cmd_check(_: argparse.Namespace) -> int:
    try:
        problems = check_all()
    except BudgetError as exc:
        _fail(str(exc))
        return 1
    if problems:
        for problem in problems:
            _fail(problem)
        return 1
    measured = measure()
    head = measured["mandatory"]
    print(
        f"mandatory reading list {head} proxy tokens (budget {BUDGETS['mandatory']}); "
        "every reading path inside its budget, every large lebend doc freshly dated, "
        "the map one row per file, every jump lands"
    )
    return 0


def cmd_report(_: argparse.Namespace) -> int:
    try:
        measured = measure()
    except BudgetError as exc:
        _fail(str(exc))
        return 1
    width = max(len(name) for name in measured)
    print(f"{'what':<{width}}  {'proxy':>7}  {'budget':>7}  headroom")
    for name, value in measured.items():
        budget = BUDGETS.get(name, 0)
        print(f"{name:<{width}}  {value:>7}  {budget:>7}  {budget - value:+8d}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.docs_budget", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="budgets, Stand blocks and the map — the CI gate")
    check.set_defaults(func=cmd_check)
    report = sub.add_parser("report", help="what each reading path costs today")
    report.set_defaults(func=cmd_report)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
