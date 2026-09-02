"""The agent instructions must keep pointing at things that exist.

`CLAUDE.md` and `.github/copilot-instructions.md` both open with the claim
that they stay in sync, and both are read as binding shorthand — CLAUDE.md is
loaded into every Claude Code session, copilot-instructions.md into every
Copilot review. Until now nothing checked either claim, and the drift was
real: a `Pre-commit hooks: none configured yet` line survived nine months
after the hooks landed, table and router lists fell behind their migrations,
and a §-renumbering in a design doc would have broken both files silently.

Three cheap pins, none of which needs the DB or the network:

1. every backtick-quoted repo path in the four agent-facing files resolves;
2. every `file.md` §N reference resolves to a `## N.` heading in that file;
3. the rules that are supposed to be mirrored are present on BOTH sides.

(3) is deliberately a keyword pin, not a text diff: the two files address
different audiences and paraphrase each other, so requiring byte equality
would force false uniformity. What it does catch is a rule silently living
in only one of them — the failure mode the 2026-09-02 audit found five times
over.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
COPILOT_MD = REPO_ROOT / ".github" / "copilot-instructions.md"

AGENT_FILES = [
    CLAUDE_MD,
    COPILOT_MD,
    REPO_ROOT / ".claude" / "commands" / "prime.md",
    REPO_ROOT / ".claude" / "commands" / "start.md",
]

_BACKTICKED = re.compile(r"`([^`\n]+)`")

# A backticked span is only treated as a path when it looks like one and
# carries no shell/placeholder syntax. Everything else in backticks is a
# command, an identifier, a header name or a value.
_PATH_SHAPED = re.compile(r"^[\w./@-]+$")
_FILE_SUFFIXES = {
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".cff",
    ".txt",
    ".lock",
    ".gz",
    ".conf",
    ".js",
    ".mjs",
    ".html",
}

# §-references name their file either as a backticked path or by bare
# basename ("architektur.md §8"); both forms are resolved against docs/. The
# gap is kept tiny on purpose — a wider one starts matching a § that belongs
# to a different document mentioned earlier in the same sentence.
_SECTION_REF = re.compile(r"([\w-]+\.md)`?\s?§\s?(\d+)")

# Paths the guides name deliberately although they are absent: a gitignored
# local file, one named precisely to say it does not exist, and the two
# commit-class-3 directories that the licensing rules define ahead of the
# first file that will live in them.
_KNOWN_ABSENT = {"app/.env", "app/src/constants.ts", "/data/derived/from-cc-by/", "/data/derived/from-nc-sa/"}


def _looks_like_path(token: str) -> bool:
    """Only multi-segment paths are checked.

    A bare basename (`compose.py`, `SOURCE.md`) is prose shorthand in these
    files, not a location claim — pinning those would force every mention to
    carry a full path and make the guides harder to read, which is the
    opposite of the point.
    """
    if not _PATH_SHAPED.match(token) or token.startswith(("http", "@")):
        return False
    if token in _KNOWN_ABSENT:
        return False
    # The guides write repo-root paths with a leading slash (`/data/sources/`)
    # and sub-paths bare (`core/shaping.py`); normalise both to
    # repo-relative, then require at least two segments so that a bare
    # directory mentioned inside a sentence about its parent (`database/`
    # under core/) is not read as a top-level claim.
    normalised = token.strip("/")
    if "/" not in normalised:
        return False
    return token.endswith("/") or Path(token).suffix in _FILE_SUFFIXES


def _candidate_paths(text: str) -> set[str]:
    return {tok for tok in _BACKTICKED.findall(text) if _looks_like_path(tok)}


def _flat(text: str) -> str:
    """Lowercased with runs of whitespace collapsed.

    Both guides hard-wrap their prose, so a rule's phrase is regularly split
    across two lines; matching the raw text would report a rule as missing
    purely because of where the line broke.
    """
    return re.sub(r"\s+", " ", text).lower()


@pytest.mark.parametrize("path", AGENT_FILES, ids=lambda p: p.name)
def test_agent_file_exists(path: Path) -> None:
    assert path.is_file(), f"{path} is referenced as an agent instruction file"


@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda p: p.name)
def test_backticked_paths_resolve(agent_file: Path) -> None:
    """Every backticked repo path in the agent instructions exists.

    A path that has moved makes the instruction actively misleading — the
    agent follows it, finds nothing, and improvises.
    """
    missing = sorted(
        token
        for token in _candidate_paths(agent_file.read_text(encoding="utf-8"))
        if not (REPO_ROOT / token.strip("/")).exists()
    )
    assert not missing, f"{agent_file.name} points at paths that do not exist: {missing}"


@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda p: p.name)
def test_section_references_resolve(agent_file: Path) -> None:
    """Every `<doc>.md §N` reference hits a `## N.` heading in that doc.

    Renumbering a design doc otherwise breaks both agent files silently.
    """
    text = agent_file.read_text(encoding="utf-8")
    docs = {p.name: p for p in (REPO_ROOT / "docs").rglob("*.md")}

    broken: list[str] = []
    for doc_name, number in _SECTION_REF.findall(text):
        doc = docs.get(doc_name)
        if doc is None:
            continue  # not a docs/ file; the path pin covers its existence
        headings = re.findall(r"^##+ (\d+)\.", doc.read_text(encoding="utf-8"), re.M)
        if number not in headings:
            broken.append(f"{doc_name} §{number}")

    assert not broken, f"{agent_file.name} cites sections that do not exist: {broken}"


# Rules that must reach BOTH audiences. Each entry is a human-readable name
# plus the keywords that identify the rule in either file's own wording; a
# rule counts as present when every keyword appears (case-insensitively).
MIRRORED_RULES = {
    "never commit on main": ["never commit on `main`"],
    "changelog fragment per PR": ["changelog.d/", "changelog (fragment)"],
    "new terms go in the glossary": ["glossar.md"],
    "closing keyword for issues": ["fixes #n"],
    "sibling-repo transfer": ["anyplot", "same round"],
    "use asymmetric findings": ["asymmetric finding"],
    "author authors in the prod admin": ["prod admin"],
    "prod-touching needs confirmation": ["cloud sql ddl"],
    "never echo secrets": ["never echo secret"],
    "archive snapshots are create-only": ["create freely, never destroy"],
    "no heredoc/sed edits to tracked files": ["--no-verify"],
    "perfect result over fast one": ["the perfect result"],
    "rejected measures name rescue paths": ["rescue path"],
    "pin BLAS threads": ["openblas_num_threads"],
    "no AI disclosure on the site": ["ki-gestützt entwickelt"],
    "legibility over period": ["legibility over period"],
    "copyleft word lists are server data": ["lesart_forms", "igerman98"],
    "never merge a PR yourself": ["never merge a pr yourself"],
    "core PRs quote bench numbers": ["bench numbers"],
    "no state-management framework": ["redux"],
    "do not silently diverge": ["silently diverge"],
    "codecov is a reviewer": ["codecov"],
}


@pytest.mark.parametrize("rule", sorted(MIRRORED_RULES), ids=lambda r: r.replace(" ", "-"))
def test_rule_is_mirrored_in_both_guides(rule: str) -> None:
    """A rule the repo relies on must not live in only one of the two guides.

    CLAUDE.md never reaches Copilot, and copilot-instructions.md never reaches
    a Claude session; a rule in one file only is a rule half the agents never
    see.
    """
    keywords = MIRRORED_RULES[rule]
    claude = _flat(CLAUDE_MD.read_text(encoding="utf-8"))
    copilot = _flat(COPILOT_MD.read_text(encoding="utf-8"))

    missing_in = [
        name
        for name, text in (("CLAUDE.md", claude), ("copilot-instructions.md", copilot))
        if not all(keyword.lower() in text for keyword in keywords)
    ]
    assert not missing_in, f"rule {rule!r} is missing from: {', '.join(missing_in)}"
