"""The §14 register gate: an entry without its index line does not ship.

Why. `docs/reference/qualitaetsmetrik.md` §14 is the campaign journal — 74 dated
sections, ~47 000 words, and the one home of the numbers. Three registers were
built on top of it so a reader can find the current state without reading all of
it: the entry table and the headline ledger at the head of §14, and the four
`verfahren-*.md` ledgers. Each of them carries a "same PR" duty in its own prose,
and the audit of 2026-09-02 found all three lagging — the process pages by two
adoptions and six to twelve days, the headline history only ever in running text,
and one headline pair whose fixture root nobody could name. A duty that only
exists in prose decays exactly this way, so it gets a gate, in the shape the
changelog fragments already use (`tools/changelog`).

Three rules, all read off the committed files:

1. **Every §14 entry has a register row.** One `###` heading under `## 14.` (the
   two index headings excepted) ⇒ exactly one row in the entry table whose link
   resolves to that heading's anchor. Rows may not point at headings that do not
   exist, and no heading may be claimed twice.
2. **Every headline ledger row cites a number the journal already carries**, and
   the newest row is the pair in the document's status blockquote. The ledger is
   an index, not a second home for the numbers — a value that appears nowhere
   else in the file is a number invented in a table.
3. **Every duel-route entry reaches its process page.** A register row on Kette ·
   Lotse · InkSight · Nullprobe needs its date in that page's ledger; a row on
   "alle Routen" needs it on all four.

Standard library only, so CI runs it without syncing the project's extras.
"""

from __future__ import annotations

import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
JOURNAL = Path("docs/reference/qualitaetsmetrik.md")
SECTION_HEADING = "## 14. "

# The two headings that ARE the registers; they index the section and are not
# entries of it.
INDEX_HEADINGS = (
    "Register der Einträge (Index, keine Zahl-Heimat)",
    "Headline-Ledger (die Wordbench-Zahlen und ihre Wurzeln)",
)

# Route name in the register ⇒ the process page that owns its ledger.
ROUTE_PAGES = {
    "Kette": Path("docs/reference/verfahren-kette.md"),
    "Lotse": Path("docs/reference/verfahren-lotse.md"),
    "InkSight": Path("docs/reference/verfahren-inksight.md"),
    "Nullprobe": Path("docs/reference/verfahren-nullprobe.md"),
}
ALL_ROUTES = "alle Routen"

# `aug14`, `sep02` — the journal's own date tag, also the Datum column everywhere.
# All twelve months, not just the ones the campaign has run through so far: the
# route-page rule matches on this tag, so a month the pattern does not know
# would silently stop enforcing it — no error, just a gate that waves everything
# through. The campaign started in `jun` and the first January would have found
# that out the hard way. The abbreviations are GERMAN, which the docs settle
# themselves by writing `okt`/`nov`/`dez` rather than oct/nov/dec; `mär` is
# accepted beside `mrz` because both spellings are current in German.
_DATE_TAG = re.compile(r"\b((?:jan|feb|mrz|mär|apr|mai|jun|jul|aug|sep|okt|nov|dez)\d{2})\b")
_LINK = re.compile(r"\[(?P<text>[^\]]*)\]\(#(?P<anchor>[^)]+)\)")
# German decimals as the docs write them: 0,109255 — three digits or more, so a
# stray "1,5 xh" cannot pass for a headline.
_LOSS = re.compile(r"\b0,\d{4,}\b")


class RegisterError(ValueError):
    """A register is malformed in a way that stops the check from running."""


def github_slug(text: str) -> str:
    """The anchor GitHub gives a heading: lowercase, punctuation dropped, spaces to hyphens.

    Kept in step with the link checker of the 2026-09-02 audit: letters, marks and
    numbers survive (so `①` and `λ` stay in the anchor), `-`/`_` survive, everything
    else falls away. Inline code spans and links are unwrapped first — GitHub slugs
    the RENDERED text, not the markdown.
    """
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


@dataclass(frozen=True)
class Entry:
    """One `###` section of §14."""

    title: str
    anchor: str
    line: int


@dataclass(frozen=True)
class Row:
    """One row of a markdown table, as its stripped cells."""

    cells: tuple[str, ...]
    line: int


def _read(root: Path, path: Path) -> str:
    return (root / path).read_text(encoding="utf-8")


def journal_section(text: str) -> tuple[list[str], int]:
    """The lines of §14 and the file offset they start at (0-based).

    §14 ends where the next `## ` begins, the way a section normally does. For
    a while this window ran to the end of the file instead: four `sep02` rounds
    had appended their sections after the `## 15.` heading — appending at the
    file end is what a round does — and widening the window was the way to
    index them without moving anyone's text. The author decided on 2026-09-03
    that §14 should be closed again, so the sections moved in front of §15 and
    the window is a section again. A round that appends at the file end now has
    to place its section — and because a truncating window would simply IGNORE
    a misplaced entry rather than complain about it, `stray_entries` looks at
    the tail and `check_register` reports what it finds.
    """
    lines = text.split("\n")
    start, end = _journal_bounds(lines)
    return lines[start:end], start


def _journal_bounds(lines: list[str]) -> tuple[int, int]:
    """Where §14 starts and where the next `## ` section takes over."""
    start = next((i for i, line in enumerate(lines) if line.startswith(SECTION_HEADING)), None)
    if start is None:
        raise RegisterError(f"{JOURNAL}: no '{SECTION_HEADING.strip()}' heading — the journal moved?")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def stray_entries(text: str) -> list[Entry]:
    """Journal entries that landed AFTER §14 — the append-at-the-file-end slip.

    A round writes its section at the end of the file, which is how five `sep02`
    entries ended up behind the `## 15.` heading. What identifies one is the
    journal's own date tag in the heading (`aug14`, `sep02`), so a later section's
    ordinary `###` subheading is not mistaken for a misplaced entry. Anchors are
    not computed here — the finding is "this belongs inside §14", not "index it
    where it fell".
    """
    lines = text.split("\n")
    _, end = _journal_bounds(lines)
    return [
        Entry(title=line[4:].strip(), anchor="", line=i + 1)
        for i, line in enumerate(lines)
        if i >= end and line.startswith("### ") and _DATE_TAG.search(line)
    ]


def entries(text: str) -> list[Entry]:
    """Every `###` heading of §14 except the two index headings, with its anchor.

    Anchors are assigned the way GitHub does it: a repeated slug gets `-1`, `-2`
    …, and the counter runs over the WHOLE file, not just this section.
    """
    lines = text.split("\n")
    section, offset = journal_section(text)
    seen: dict[str, int] = {}
    for line in lines[:offset]:
        if line.startswith("#"):
            slug = github_slug(line.lstrip("#").strip())
            seen[slug] = seen.get(slug, 0) + 1
    found: list[Entry] = []
    for i, line in enumerate(section):
        if not line.startswith("### "):
            continue
        title = line[4:].strip()
        slug = github_slug(title)
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        anchor = slug if not n else f"{slug}-{n}"
        if title in INDEX_HEADINGS:
            continue
        found.append(Entry(title=title, anchor=anchor, line=offset + i + 1))
    return found


def table_after(section: list[str], offset: int, heading: str) -> list[Row]:
    """The first markdown table under `heading`, without its header and separator."""
    try:
        start = next(i for i, line in enumerate(section) if line.strip() == f"### {heading}")
    except StopIteration as exc:
        raise RegisterError(f"{JOURNAL} §14: the heading '### {heading}' is gone") from exc
    rows: list[Row] = []
    in_table = False
    for i in range(start + 1, len(section)):
        line = section[i]
        if line.startswith("### "):
            break
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        if set(stripped) <= set("|-: "):  # the separator row
            in_table = True
            continue
        if not in_table:  # the header row
            in_table = True
            continue
        cells = tuple(c.strip() for c in stripped.strip("|").split("|"))
        rows.append(Row(cells=cells, line=offset + i + 1))
    if not rows:
        raise RegisterError(f"{JOURNAL} §14: '{heading}' carries no table rows")
    return rows


def register_rows(text: str) -> list[Row]:
    section, offset = journal_section(text)
    return table_after(section, offset, INDEX_HEADINGS[0])


def ledger_rows(text: str) -> list[Row]:
    section, offset = journal_section(text)
    return table_after(section, offset, INDEX_HEADINGS[1])


def status_headline(text: str) -> tuple[str, str] | None:
    """The `Wörter x · Paare y` pair from the document's status blockquote."""
    head = "\n".join(text.split("\n")[:20])
    match = re.search(r"Wörter\s+(0,\d+)\s*·\s*Paare\s+(0,\d+)", head)
    return (match.group(1), match.group(2)) if match else None


def ledger_dates(page_text: str) -> set[str]:
    """Every date tag in the first column of a process page's ledger tables."""
    dates: set[str] = set()
    for line in page_text.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        first = stripped.strip("|").split("|")[0]
        dates.update(_DATE_TAG.findall(first))
    return dates


# --- the three rules ---------------------------------------------------------


def check_register(text: str) -> list[str]:
    problems: list[str] = []
    known = {entry.anchor: entry for entry in entries(text)}
    claimed: dict[str, int] = {}
    for row in register_rows(text):
        if len(row.cells) != 5:
            problems.append(f"{JOURNAL}:{row.line}: register row has {len(row.cells)} columns, expected 5")
            continue
        link = _LINK.search(row.cells[2])
        if link is None:
            problems.append(f"{JOURNAL}:{row.line}: register row's Arm cell carries no anchor link: {row.cells[2]}")
            continue
        anchor = link.group("anchor")
        if anchor not in known:
            problems.append(f"{JOURNAL}:{row.line}: register row points at #{anchor}, which is no §14 heading")
            continue
        if anchor in claimed:
            problems.append(f"{JOURNAL}:{row.line}: #{anchor} already has a register row at line {claimed[anchor]}")
            continue
        claimed[anchor] = row.line
    for anchor, entry in known.items():
        if anchor not in claimed:
            problems.append(
                f"{JOURNAL}:{entry.line}: §14 entry '{entry.title}' has no register row — "
                f"add one to '{INDEX_HEADINGS[0]}' in this PR (link target: #{anchor})"
            )
    for stray in stray_entries(text):
        problems.append(
            f"{JOURNAL}:{stray.line}: '{stray.title}' reads as a journal entry but sits AFTER §14 — "
            "a round appends at the end of the file, and §14 is a closed section: move it in front of "
            "the next `## ` heading, then give it its register row"
        )
    return problems


def check_ledger(text: str) -> list[str]:
    problems: list[str] = []
    rows = ledger_rows(text)
    table_lines = {row.line for row in rows}
    elsewhere = {
        value
        for i, line in enumerate(text.split("\n"), start=1)
        if i not in table_lines
        for value in _LOSS.findall(line)
    }
    for row in rows:
        if len(row.cells) != 6:
            problems.append(f"{JOURNAL}:{row.line}: ledger row has {len(row.cells)} columns, expected 6")
            continue
        for label, cell in (("Wörter", row.cells[3]), ("Paare", row.cells[4])):
            value = _LOSS.search(cell)
            if value is None:
                problems.append(f"{JOURNAL}:{row.line}: ledger row's {label} cell carries no headline value: {cell!r}")
            elif value.group(0) not in elsewhere:
                problems.append(
                    f"{JOURNAL}:{row.line}: ledger cites {label} {value.group(0)}, which appears nowhere else in "
                    "the journal — the ledger indexes numbers, it does not mint them"
                )
    headline = status_headline(text)
    if headline is None:
        problems.append(f"{JOURNAL}: the status blockquote names no 'Wörter … · Paare …' headline")
    elif rows and len(rows[-1].cells) == 6:
        newest = (_LOSS.search(rows[-1].cells[3]), _LOSS.search(rows[-1].cells[4]))
        if all(newest) and tuple(m.group(0) for m in newest) != headline:  # type: ignore[union-attr]
            problems.append(
                f"{JOURNAL}:{rows[-1].line}: the newest ledger row "
                f"({newest[0].group(0)} / {newest[1].group(0)}) is not the status blockquote's headline "  # type: ignore[union-attr]
                f"({headline[0]} / {headline[1]}) — a run that moves the headline adds its row"
            )
    return problems


def check_verfahren(text: str, *, root: Path = REPO_ROOT) -> list[str]:
    problems: list[str] = []
    dates = {name: ledger_dates(_read(root, page)) for name, page in ROUTE_PAGES.items()}
    for row in register_rows(text):
        if len(row.cells) != 5:
            continue  # already reported by check_register
        row_dates = set(_DATE_TAG.findall(row.cells[0]))
        route_cell = row.cells[1].strip()
        wanted = (
            list(ROUTE_PAGES) if route_cell == ALL_ROUTES else [r for r in route_cell.split("/") if r in ROUTE_PAGES]
        )
        for route in wanted:
            if row_dates and not (row_dates & dates[route]):
                problems.append(
                    f"{JOURNAL}:{row.line}: {route} entry of {'/'.join(sorted(row_dates))} has no ledger row in "
                    f"{ROUTE_PAGES[route]} — the process page is the route's register (verfahren.md)"
                )
    return problems


def check_all(*, root: Path = REPO_ROOT) -> list[str]:
    text = _read(root, JOURNAL)
    return check_register(text) + check_ledger(text) + check_verfahren(text, root=root)


# --- what a PR added (message only; the rules above are the gate) -------------


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def added_entries(base: str, *, root: Path = REPO_ROOT) -> list[str]:
    """Titles of §14 entries this branch adds against `base` — for the summary line.

    Approximate on purpose: it reads added `###` lines out of the diff, so a
    section moved within the file counts as added. The rules above are the gate;
    this only names what the author should check twice.
    """
    diff = _git(root, "diff", "--unified=0", f"{base}...HEAD", "--", str(JOURNAL))
    titles = [line[5:].strip() for line in diff.split("\n") if line.startswith("+### ")]
    return [title for title in titles if title not in INDEX_HEADINGS]
