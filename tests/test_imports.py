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

import ast
import importlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED = ("core", "api", "alembic")


@pytest.mark.parametrize(
    "module",
    [
        "core.database",
        "core.database.repositories",
        "core.database.models",
        "api.schemas",
        "api.rendering",
        "api.routers.templates",
        "api.routers.write",
        "api.main",
    ],
)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)


def _imports_tools(path: Path) -> list[str]:
    """Every `import tools…` in one file, including the ones inside functions."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits += [a.name for a in node.names if a.name == "tools" or a.name.startswith("tools.")]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            name = node.module or ""
            if name == "tools" or name.startswith("tools."):
                hits.append(name)
    return hits


@pytest.mark.parametrize("package", SHIPPED)
def test_shipped_code_never_imports_tools(package: str) -> None:
    """`api/Dockerfile` ships core/ + api/ + alembic/ — and NOT tools/.

    So an import of `tools…` from any of them is a ModuleNotFoundError in
    production even though every local run and the whole test suite are green:
    the dev tree has `tools/` on the path. That is not hypothetical — a lazy
    `from tools.eigenhand.corpus import …` inside a width helper made every
    Bogen the deployed API tried to print answer 500, and the failure was
    invisible until someone pressed the button in prod (2026-08-25).

    A deferred import inside a function is caught here too: hiding it from
    module load only moves the crash to the first request that needs it.
    """
    offenders = {
        str(path.relative_to(REPO_ROOT)): names
        for path in sorted((REPO_ROOT / package).rglob("*.py"))
        if (names := _imports_tools(path))
    }
    assert not offenders, f"shipped code imports tools/, which the API image does not contain: {offenders}"
