"""Import-smoke for the DB + API modules.

The rest of the suite is deliberately DB/HTTP-free (verify-core), so it never
imports the repository or router modules. A module-level error there — e.g. an
annotation that fails to evaluate at import time (`-> list[...]` where a method
named `list` shadows the builtin) — then sails through pytest AND ruff and only
crashes when something actually imports it: the API process, or the alembic
migrate job in the deploy pipeline (which is exactly how PR #93 broke the
deploy). These cheap imports close that gap. They define classes / the FastAPI
app only — no DB connection or env is needed at import time.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "core.database",
        "core.database.repositories",
        "core.database.models",
        "api.schemas",
        "api.routers.templates",
        "api.main",
    ],
)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)
