"""The one source of the running app version.

`pyproject.toml`'s `version` field — what `tools.changelog release` bumps —
read once at import. The project is an uv WORKSPACE, not an installed
distribution, so `importlib.metadata` has no record of it (that is where this
differs from anyplot's twin, which reads the installed dist): the file ships in
the image next to `api/`, so it is read from disk. Keeping a second hardcoded
string here is exactly what drifted before — it sat at 0.2.0 for epochs.

`/health` serves the value so the deploy's pre-traffic smoke can assert that
the candidate revision runs the version this build's checkout carries
(`api/cloudbuild.yaml`) — the check that would have caught a stale image.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path


logger = logging.getLogger(__name__)


def _project_version() -> str:
    try:
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        return str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):  # pragma: no cover — packaging error, not runtime
        # A cosmetic version must never keep the API from starting, but a
        # missing/unparsable pyproject in the image is a packaging bug —
        # scream in the logs instead of failing silently.
        logger.exception("could not read project.version from pyproject.toml — check the image contents")
        return "0.0.0"


APP_VERSION = _project_version()
