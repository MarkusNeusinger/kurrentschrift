"""`python -m tools.docs_register` — the §14 register gate.

    uv run python -m tools.docs_register check                      # the three rules
    uv run python -m tools.docs_register check --base origin/main   # …and name what this branch adds (the CI gate)

Checks only; nothing here writes a file, touches a remote or reads a database.
The rules and the reason they exist are in `__init__`'s docstring.
"""

from __future__ import annotations

import argparse
import os
import sys

from tools.docs_register import RegisterError, added_entries, check_all


def _fail(message: str) -> None:
    # GitHub turns the `::error::` line into an annotation on the PR's checks tab.
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    print(f"{prefix}{message}", file=sys.stderr)


def cmd_check(args: argparse.Namespace) -> int:
    try:
        problems = check_all()
    except RegisterError as exc:
        _fail(str(exc))
        return 1
    if args.base:
        added = added_entries(args.base)
        print(
            f"this branch adds {len(added)} §14 entr{'y' if len(added) == 1 else 'ies'}"
            + ("".join(f"\n  + {title}" for title in added) if added else "")
        )
    if problems:
        for problem in problems:
            _fail(problem)
        return 1
    print("§14 register, headline ledger and the four process ledgers agree")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.docs_register", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="every §14 entry indexed, every headline ledgered, every route page current")
    check.add_argument("--base", help="branch point to report the added entries against (e.g. origin/main)")
    check.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
