"""The reading-cost gate: what a session has to load before it starts working.

Why. On 2026-09-04 the mandatory reading list of `CLAUDE.md` cost 110 997
tokens — the glossary alone 56 401 — before a session had read one line about
the actual task. #521 and #524 brought it to 53 865 by moving the campaign
journal out of the metric doc, cutting the index to a map and putting a short
glossary on the list. Nothing stops that from growing back: every doc grows by
one paragraph at a time, and the list is edited by whoever adds a doc. So the
cost gets a number and the number gets a gate, in the shape `tools/changelog`
and `tools/docs_register` already use.

Three rules, all read off the committed files:

1. **The mandatory list stays inside its budget**, and so does every reading
   path named in `CLAUDE.md`. The list is not duplicated here — it is PARSED
   out of `CLAUDE.md`, so adding a doc to it raises the measured sum and this
   gate is what notices. Three paths end in „and the one you need" — a route
   page, a journal entry, a tool's section — and those halves are budgeted at
   their WORST case (`WIDEST`), because an unbudgeted half is an unbounded
   path however small the fixed half stays.
2. **A large `lebend` doc carries a fresh Stand block.** Over
   `STAND_BLOCK_MIN_TOKENS` a status blockquote is not enough: the head has to
   be a Stand block (at least `STAND_BLOCK_MIN_LINES` lines) and its date at
   most `STAND_BLOCK_MAX_AGE_DAYS` old. A doc that says „this is the current
   state" and has not been looked at in a month is the failure this catches —
   the reader trusts the summary instead of the file.

   This is the one rule that fires on the CALENDAR rather than on a change, and
   that is deliberate: what goes stale is the doc's claim about the CODE, and
   the code moves without the doc being touched. The price is that a month
   after the last pass the gate asks for a re-read, on whatever PR happens to
   be open. The alternative — comparing the block's date against the file's own
   last commit — was considered and dropped: it fires on every typo fix and
   stays silent exactly when the code moved and the doc did not, which is the
   case worth catching. If the cadence turns out wrong, the honest fix is this
   constant with a reason, never a bumped date without a re-read.
3. **The map has one row per file.** `docs/index.md` promises exactly one row
   per `.md` under `docs/`; a row that disappears makes a doc invisible, a row
   that stays behind sends a reader at a file that is gone. Both are cheap to
   check and impossible to notice by reading.
4. **Every jump lands.** The whole design is jump tables — the map, the
   registers, the Stand blocks that answer with an anchor instead of prose —
   so a dead link or a dead `#anchor` does not cost a click, it makes the cheap
   path a lie and sends the reader back to loading the file. Every relative
   markdown link in the repo is resolved, and every `#fragment` against the
   headings of the file it points into, GitHub's slug rules included.

**On counting tokens without a tokenizer.** This module ships its own proxy
instead of depending on `tiktoken`, for two reasons: the CI job runs
`uv run --no-project` like the register gate, so a dependency would mean
syncing extras; and `tiktoken.get_encoding` DOWNLOADS its BPE table on first
use, which would put a network fetch into every run of a gate whose whole job
is to be boring. The proxy is deterministic and offline: word-ish pieces, with
long alphabetic runs split every four characters the way BPE splits German
compounds, times a calibration factor.

The budgets below are set in PROXY units from the measured value plus 10 %, so
the gate compares like with like and the proxy's systematic offset cancels.
Cross-checked once against `tiktoken` `o200k_base` on 2026-09-04: the mandatory
list +0.6 %, the frontend path +2.3 %, the Werkbank path +0.4 %, the journal
−7.7 % (dense tables and numbers), the English agent files +14 %. That is the
accuracy this gate needs — it watches GROWTH, not an absolute budget.
"""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_MD = Path("CLAUDE.md")
INDEX = Path("docs/index.md")
DOCS = Path("docs")

# The two markers that bracket the mandatory list inside `CLAUDE.md`.
LIST_HEADING = "## Read these before substantive work"
LIST_END = "**Reading paths per track**"

# --- the proxy ---------------------------------------------------------------

# One piece per word, number or punctuation mark; an alphabetic run of more than
# four characters counts as several, which is what a BPE does to a German
# compound. `Übergangsraum` is not one token, and pretending it is would make
# every German doc look cheaper than it reads.
_PIECE = re.compile(r"[A-Za-zÄÖÜäöüßÀ-ÿ]+|\d+|[^\sA-Za-zÄÖÜäöüßÀ-ÿ\d]")
# Calibrated 2026-09-04 against tiktoken o200k_base over the 57 docs above
# 2 000 characters: the sum of proxy pieces times this factor equals the sum of
# real tokens. Re-derive it only together with the budgets.
_CALIBRATION = 0.85


def proxy_tokens(text: str) -> int:
    """A deterministic, dependency-free stand-in for a tokenizer's count."""
    pieces = 0
    for piece in _PIECE.findall(text):
        pieces += max(1, (len(piece) + 3) // 4) if piece.isalpha() else 1
    return round(pieces * _CALIBRATION)


# --- what is measured --------------------------------------------------------


@dataclass(frozen=True)
class Piece:
    """One thing a reading path asks a session to read.

    `selector` is `whole`, `stand` (the status blockquote under the H1),
    `register` (a journal's head down to its first entry) or a `## ` heading
    prefix such as `## 5. `.
    """

    path: Path
    selector: str


def _piece(path: str, selector: str = "whole") -> Piece:
    return Piece(path=Path(path), selector=selector)


# The reading paths of `CLAUDE.md` § „Reading paths per track", as sections
# rather than prose. Kept here and not parsed: the table's cells name sections
# in English prose („Stand block + §2 (frozen references)"), and a parser for
# that would fail silently the first time someone rewords a cell. The pin that
# keeps the two in step is `tests/test_docs_budget.py`, which requires every
# file named here to appear in that table.
PATHS: dict[str, tuple[Piece, ...]] = {
    "mess-runde": (
        _piece("docs/reference/messjournal.md", "register"),
        _piece("docs/reference/qualitaetsmetrik.md", "stand"),
        _piece("docs/reference/qualitaetsmetrik.md", "## 2. "),
        _piece("docs/proposals/tintenfolger.md", "stand"),
        _piece("docs/proposals/tintenfolger.md", "### 7.11"),
        _piece("docs/reference/verfahren.md"),
    ),
    "glyph-optimierung": (
        _piece("docs/reference/qualitaetsmetrik.md", "stand"),
        _piece("docs/reference/qualitaetsmetrik.md", "## 1. "),
        _piece("docs/reference/qualitaetsmetrik.md", "## 2. "),
        _piece("docs/reference/qualitaetsmetrik.md", "## 3. "),
        _piece("docs/reference/qualitaetsmetrik.md", "## 5. "),
    ),
    "komposition": (
        _piece("docs/concepts/architektur.md", "stand"),
        _piece("docs/concepts/architektur.md", "## 3. "),
        _piece("docs/concepts/architektur.md", "## 4. "),
        _piece("docs/concepts/architektur.md", "## 5. "),
        _piece("docs/concepts/architektur.md", "## 6. "),
        _piece("docs/reference/write-api.md"),
    ),
    "frontend": (
        _piece("docs/concepts/design-system.md"),
        _piece("docs/reference/frontend-stack.md", "stand"),
        _piece("docs/reference/frontend-stack.md", "## 2. "),
    ),
    "werkbank": (
        _piece("docs/proposals/optimierungs-werkbank.md", "## 3. "),
        _piece("docs/proposals/optimierungs-werkbank.md", "## 5. "),
        _piece("docs/reference/frontend-stack.md", "## 2. "),
    ),
    "werkzeug": (_piece("docs/reference/werkzeuge.md", "stand"),),
    "doku": (_piece("docs/index.md"), _piece("docs/dokument-status.md")),
}


# Three of the reading paths end in „and the one you need": the route's own
# `verfahren-*.md`, the journal entry a round cites, the section of the tool
# being changed. Which one is not knowable here — but the WORST one is, and a
# path whose variable half is unbudgeted is not a bounded path. Each of these
# is measured as the largest candidate and budgeted like everything else, so
# the gate's „every reading path inside its budget" is true of the whole read.
def widest_route(root: Path) -> int:
    """The largest duel-route page — the variable half of the Mess-Runde path."""
    pages = sorted((root / DOCS / "reference").glob("verfahren-*.md"))
    if not pages:
        raise BudgetError("no docs/reference/verfahren-*.md pages — the duel routes moved?")
    return max(proxy_tokens(page.read_text(encoding="utf-8")) for page in pages)


def widest_journal_entry(root: Path) -> int:
    """The largest `###` entry of the journal — the entry a round jumps to.

    The two index headings are excluded: the register and the headline ledger
    are already counted whole, in the `register` piece of the same path.
    """
    lines = _read(root, Path("docs/reference/messjournal.md")).split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("### ")]
    if not starts:
        raise BudgetError("docs/reference/messjournal.md carries no `###` entries")
    sizes = [
        proxy_tokens("\n".join(lines[a:b]))
        for a, b in zip(starts, starts[1:] + [len(lines)], strict=True)
        if not lines[a].startswith(("### Register", "### Headline"))
    ]
    return max(sizes)


def widest_tool_section(root: Path) -> int:
    """The largest section of `werkzeuge.md` — the one tool a change is about."""
    lines = _read(root, Path("docs/reference/werkzeuge.md")).split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        raise BudgetError("docs/reference/werkzeuge.md carries no `## ` sections")
    return max(proxy_tokens("\n".join(lines[a:b])) for a, b in zip(starts, starts[1:] + [len(lines)], strict=True))


WIDEST = {
    "mess-runde-route": widest_route,
    "mess-runde-eintrag": widest_journal_entry,
    "werkzeug-abschnitt": widest_tool_section,
}

# Measured 2026-09-04 plus 10 %. A budget is not a target: the headroom is
# there so that a paragraph does not fail a PR, and a rewrite does.
#
# `mess-runde` raised the same day, deliberately and for one reason: its
# growing piece is the §14 REGISTER, which carries exactly one row per journal
# entry. Six rounds were booked on 2026-09-04, and a register that may not grow
# by a row per round is an index that cannot index — the headroom would have to
# be bought by deleting rows, which is the one thing the register forbids
# ("ein Eintrag wird nie gelöscht oder umsortiert"). Re-measured with those
# rows in and given the same 10 % headroom as every other path. What this does
# NOT license is prose: if the Stand blocks or §7.11 grow, that is the rewrite
# the gate is for.
BUDGETS: dict[str, int] = {
    "mandatory": 60_852,
    "mess-runde": 18_644,
    "mess-runde-route": 6_177,
    "mess-runde-eintrag": 4_503,
    "glyph-optimierung": 8_504,
    "komposition": 9_680,
    "frontend": 14_437,
    "werkbank": 5_166,
    "werkzeug": 713,
    "werkzeug-abschnitt": 4_073,
    "doku": 7_937,
}

# --- Stand blocks ------------------------------------------------------------

STAND_BLOCK_MIN_TOKENS = 10_000
STAND_BLOCK_MIN_LINES = 12
# The upper bound matters as much as the lower one: a Stand block is read
# INSTEAD of the file, so one that grows into an essay is a second copy of the
# doc — the thing this whole package removed.
STAND_BLOCK_MAX_LINES = 40
STAND_BLOCK_MAX_AGE_DAYS = 30

# Only `lebend` docs owe a fresh date: they are the ones claiming to describe
# the current state. A `bindend` decision or an `umgesetzt-historisch` protocol
# is as true as the day it was written, and bumping its date would be noise.
FRESH_STATUS = "lebend"

_STATUS = re.compile(r"\*\*Status \((?P<date>\d{4}-\d{2}-\d{2})\): (?P<word>[\w-]+)")


class BudgetError(ValueError):
    """A file the gate needs is missing or malformed."""


def _read(root: Path, path: Path) -> str:
    return (root / path).read_text(encoding="utf-8")


def mandatory_docs(root: Path = REPO_ROOT) -> list[Path]:
    """The docs `CLAUDE.md` calls mandatory, read out of `CLAUDE.md` itself.

    Parsed rather than duplicated so that the list and its budget cannot drift:
    adding a bullet raises the measured sum, which is exactly the moment the
    author should see a number.
    """
    text = _read(root, CLAUDE_MD)
    try:
        start = text.index(LIST_HEADING)
        end = text.index(LIST_END, start)
    except ValueError as exc:  # pragma: no cover - a renamed heading
        raise BudgetError(
            f"{CLAUDE_MD}: cannot find the mandatory list between '{LIST_HEADING}' and '{LIST_END}'"
        ) from exc
    section_text = text[start:end]
    found: list[Path] = []
    # The list opens with „Start at `docs/index.md`" — a pointer, not a bullet,
    # and just as mandatory as the bullets under it.
    for match in re.findall(r"Start at `(docs/[\w./-]+\.md)`", section_text):
        found.append(Path(match))
    for line in section_text.split("\n"):
        if not line.startswith("- `docs/"):
            continue
        # Only the SUBJECT of the bullet counts — everything before the em dash
        # that opens its description. A description regularly names further
        # docs („the FULL vocabulary stays `glossar.md`"), and counting those
        # would put a doc on the list that the list explicitly takes off it.
        subject = line.split(" — ", 1)[0]
        for match in re.findall(r"`(docs/[\w./-]+\.md)`", subject):
            path = Path(match)
            if path not in found:
                found.append(path)
    if not found:
        raise BudgetError(f"{CLAUDE_MD}: the mandatory list names no docs — did its bullet shape change?")
    return found


def stand_block(text: str) -> list[str]:
    """The status blockquote directly under the H1, as its lines."""
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith(">")), None)
    if start is None or start > 4:
        return []
    end = next((i for i in range(start, len(lines)) if not lines[i].startswith(">")), len(lines))
    return lines[start:end]


def section(text: str, prefix: str) -> str:
    """The section whose heading starts with `prefix`, ending at the next heading of its level."""
    level = prefix[: len(prefix) - len(prefix.lstrip("#"))] + " "
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith(prefix)), None)
    if start is None:
        raise BudgetError(f"no section starting with {prefix!r}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith(level)), len(lines))
    return "\n".join(lines[start:end])


def register_head(text: str) -> str:
    """A journal's head: everything down to its first entry after the index tables."""
    lines = text.split("\n")
    end = next((i for i, line in enumerate(lines) if re.match(r"^### (?!Register|Headline)", line)), len(lines))
    return "\n".join(lines[:end])


def piece_text(root: Path, piece: Piece) -> str:
    text = _read(root, piece.path)
    if piece.selector == "whole":
        return text
    if piece.selector == "stand":
        return "\n".join(stand_block(text))
    if piece.selector == "register":
        return register_head(text)
    return section(text, piece.selector)


def cost(root: Path, pieces: tuple[Piece, ...]) -> int:
    return sum(proxy_tokens(piece_text(root, piece)) for piece in pieces)


def measure(root: Path = REPO_ROOT) -> dict[str, int]:
    """Every budgeted quantity, in proxy tokens."""
    out = {"mandatory": sum(proxy_tokens(_read(root, doc)) for doc in mandatory_docs(root))}
    for name, pieces in PATHS.items():
        out[name] = cost(root, pieces)
    for name, widest in WIDEST.items():
        out[name] = widest(root)
    return out


# --- the three rules ---------------------------------------------------------


def check_budgets(root: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    measured = measure(root)
    for name, value in measured.items():
        budget = BUDGETS.get(name)
        if budget is None:
            problems.append(f"reading path '{name}' has no budget in tools/docs_budget BUDGETS")
        elif value > budget:
            problems.append(
                f"'{name}' costs {value} proxy tokens, over its budget of {budget} "
                f"(+{value - budget}). Either move the growth out of the read path, or raise the "
                "budget deliberately in tools/docs_budget and say why in the PR"
            )
    for name in BUDGETS:
        if name not in measured:
            problems.append(f"budget '{name}' measures nothing — a reading path was renamed or removed")
    return problems


def check_stand_blocks(root: Path = REPO_ROOT, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    problems: list[str] = []
    for path in sorted((root / DOCS).rglob("*.md")):
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        if proxy_tokens(text) < STAND_BLOCK_MIN_TOKENS:
            continue
        block = stand_block(text)
        match = _STATUS.search("\n".join(block))
        if match is None:
            problems.append(f"{rel}: over {STAND_BLOCK_MIN_TOKENS} tokens and carries no dated status blockquote")
            continue
        if match.group("word") != FRESH_STATUS:
            continue
        if len(block) < STAND_BLOCK_MIN_LINES:
            problems.append(
                f"{rel}: {len(block)} status lines — a `{FRESH_STATUS}` doc this large owes a Stand block "
                f"of at least {STAND_BLOCK_MIN_LINES} (what holds · what is open · where the detail lives)"
            )
        elif len(block) > STAND_BLOCK_MAX_LINES:
            problems.append(
                f"{rel}: {len(block)} status lines, over the {STAND_BLOCK_MAX_LINES}-line cap — a Stand block "
                "is read instead of the file, so past that length it becomes a second copy of it. Move the "
                "detail into a section and leave the anchor"
            )
        age = (today - dt.date.fromisoformat(match.group("date"))).days
        if age > STAND_BLOCK_MAX_AGE_DAYS:
            problems.append(
                f"{rel}: the Stand block is dated {match.group('date')}, {age} days ago. A `{FRESH_STATUS}` doc "
                "claims to describe the current state — re-read it against the code and date it again "
                "(bumping the date alone is the one thing that makes this check worthless)"
            )
    return problems


def map_rows(root: Path = REPO_ROOT) -> list[str]:
    """The doc each row of `docs/index.md` points at, in order."""
    rows: list[str] = []
    for line in _read(root, INDEX).split("\n"):
        if not line.startswith("| ["):
            continue
        first_cell = line.strip("|").split("|")[0]
        rows += re.findall(r"\]\(([^)#]+\.md)\)", first_cell)
    return rows


def check_map(root: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    listed = map_rows(root)
    on_disk = {str(p.relative_to(root / DOCS)) for p in (root / DOCS).rglob("*.md")}
    seen: dict[str, int] = {}
    for row in listed:
        seen[row] = seen.get(row, 0) + 1
    for row, count in sorted(seen.items()):
        if count > 1:
            problems.append(f"{INDEX}: '{row}' has {count} rows — the map carries exactly one per file")
    for missing in sorted(on_disk - set(listed)):
        problems.append(f"{INDEX}: no row for docs/{missing} — a doc nobody can find from the map is invisible")
    for stale in sorted(set(listed) - on_disk):
        problems.append(f"{INDEX}: a row points at docs/{stale}, which does not exist")
    return problems


# --- the fourth rule: every jump lands ---------------------------------------

# Directories that are not documentation: dependencies, build output and the
# committed prerender snapshots (generated HTML, not prose).
_SKIP_DIRS = {"node_modules", ".git", "dist", "coverage", ".venv", "prerender"}
# `[text](target)`, with the `!` of an image excluded and an optional title.
_MD_LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
_ABSOLUTE = ("http://", "https://", "mailto:", "tel:")


def github_slug(text: str) -> str:
    """The anchor GitHub gives a heading — the same rule `tools/docs_register` uses."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("*", "")
    out: list[str] = []
    for ch in text.strip().lower():
        if ch == " ":
            out.append("-")
        elif ch in "-_":
            out.append(ch)
        elif unicodedata.category(ch)[0] in ("L", "N", "M"):
            out.append(ch)
    return "".join(out)


def anchors_of(text: str) -> set[str]:
    """Every `#fragment` a markdown file offers, duplicates numbered as GitHub does.

    Fenced code blocks are skipped: a `# comment` inside one is a comment, not a
    heading, and counting it would invent anchors that do not exist.
    """
    seen: dict[str, int] = {}
    out: set[str] = set()
    in_code = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.startswith("#"):
            continue
        slug = github_slug(line.lstrip("#").strip())
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        out.add(slug if not n else f"{slug}-{n}")
    return out


def check_links(root: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    anchors: dict[Path, set[str]] = {}
    for path in sorted(root.rglob("*.md")):
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)
        for match in _MD_LINK.finditer(text):
            target = match.group("target")
            if target.startswith(_ABSOLUTE):
                continue
            line = text[: match.start()].count("\n") + 1
            file_part, _, fragment = target.partition("#")
            dest = path if not file_part else (path.parent / file_part).resolve()
            if not dest.exists():
                problems.append(f"{rel}:{line}: link to a file that does not exist: {target}")
                continue
            if not fragment or dest.suffix != ".md":
                continue
            if dest not in anchors:
                anchors[dest] = anchors_of(dest.read_text(encoding="utf-8"))
            if fragment not in anchors[dest]:
                problems.append(f"{rel}:{line}: dead anchor: {target}")
    return problems


def check_all(*, root: Path = REPO_ROOT, today: dt.date | None = None) -> list[str]:
    return check_budgets(root) + check_stand_blocks(root, today) + check_map(root) + check_links(root)
