"""The §14 register gate: an entry without its index line does not ship.

Why. `docs/reference/messjournal.md` §14 is the campaign journal — 81 dated
sections, ~47 000 words, and the one home of the numbers. Three registers were
built on top of it so a reader can find the current state without reading all of
it: the entry table and the headline ledger at the head of §14, and the four
`verfahren-*.md` ledgers. Each of them carries a "same PR" duty in its own prose,
and the audit of 2026-09-02 found all three lagging — the process pages by two
adoptions and six to twelve days, the headline history only ever in running text,
and one headline pair whose fixture root nobody could name. A duty that only
exists in prose decays exactly this way, so it gets a gate, in the shape the
changelog fragments already use (`tools/changelog`).

The journal moved out of `qualitaetsmetrik.md` on 2026-09-04 — same section,
same headings, same anchors, its own file — so the metric rules can be read
without the 7 366 lines of journal behind them. The section KEEPS the number
14: its entries are cited as „§14 «Titel»“ roughly 350 times, so the number is
a citation key, not a position. Three things follow for this module. The
journal is read from `JOURNAL`; the headline pair comes from the status
blockquote of `METRIC`, still the one place the current headlines are stated;
and an entry may also stand in `ARCHIVE_PAGE`, the second file that takes an
arm once it is finished — a register row reaches it by naming the file in
front of the `#` fragment.

Three rules, all read off the committed files:

1. **Every §14 entry has a register row.** One `###` heading under `## 14.` or
   in the archive page (the two index headings excepted) ⇒ exactly one row in
   the entry table whose link resolves to that heading's anchor. Rows may not
   point at headings that do not exist, and no heading may be claimed twice.
2. **Every headline ledger row cites a number the journal already carries**, and
   the newest row is the pair in `METRIC`'s status blockquote. The ledger is
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
JOURNAL = Path("docs/reference/messjournal.md")
# The metric rules, and the one place the current headlines are stated.
METRIC = Path("docs/reference/qualitaetsmetrik.md")
# Where an entry goes once its arm is finished. It stays an entry — same
# heading, same anchor, same register row, only the row's link gains the file
# name in front of the `#`.
ARCHIVE_PAGE = Path("docs/reference/messjournal-archiv.md")
SECTION_HEADING = "## 14. "

# The two headings that ARE the registers; they index the section and are not
# entries of it.
INDEX_HEADINGS = (
    "Register der Einträge (Index, keine Zahl-Heimat)",
    "Headline-Ledger (die Wordbench-Zahlen und ihre Wurzeln)",
)

# `###` headings of the journal file that are neither a §14 entry nor an
# archived one — an allowlist, and empty on purpose: there is no such heading
# today. It is a declaration rather than a shape test because shape cannot
# decide the question. Before the move, the file carried 26 dated `###` headings
# outside §14 (`Re-Baseline jul05`, `Nachtrag aug26` …), so "has a date tag"
# would have flagged a legitimate subsection the day someone wrote one, while a
# journal entry that fell out of §14 looks like any other heading. Defaulting to
# "report it" makes the append-at-the-file-end slip loud and costs a legitimate
# subheading one reviewed line here.
POST_JOURNAL_SUBHEADINGS: tuple[str, ...] = ()

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
# A register row links either into this file (`#anchor`) or into the archive
# page (`messjournal-archiv.md#anchor`) — the file part is what says which.
_LINK = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<file>[^)#]*)#(?P<anchor>[^)]+)\)")
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
    the window is a section again. Since the 2026-09-04 move §14 is the only
    section of its own file, so a round that appends at the file end is placing
    it correctly and the slip cannot recur — but the window stays a section and
    `stray_entries` keeps looking at the tail, because the day someone opens a
    second `## ` section here the old hole would be back, and a truncating
    window does not reject a misplaced entry, it simply cannot see one.
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
    """`###` headings behind §14 that nobody declared — the append-at-the-end slip.

    A round writes its section at the end of the file, which is how five `sep02`
    entries ended up behind the `## 15.` heading. Nothing in a heading says
    whether it was meant for the journal, so this does not guess: everything
    behind §14 is reported unless it stands in `POST_JOURNAL_SUBHEADINGS`.
    Anchors are not computed — the finding is "this belongs inside §14", not
    "index it where it fell".
    """
    lines = text.split("\n")
    _, end = _journal_bounds(lines)
    return [
        Entry(title=line[4:].strip(), anchor="", line=i + 1)
        for i, line in enumerate(lines)
        if i >= end and line.startswith("### ") and line[4:].strip() not in POST_JOURNAL_SUBHEADINGS
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


def archive_entries(text: str) -> list[Entry]:
    """Every `###` heading of the archive page, with its anchor.

    The archive is a page rather than a trailing section on purpose: §14 is then
    the only section of the journal, so appending a round at the file end is
    RIGHT again and the `sep02` misplacement cannot recur. The price is that the
    register row of an archived entry has to name the file — one word per move.
    """
    seen: dict[str, int] = {}
    found: list[Entry] = []
    for i, line in enumerate(text.split("\n")):
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        slug = github_slug(title)
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        if line.startswith("### "):
            found.append(Entry(title=title, anchor=slug if not n else f"{slug}-{n}", line=i + 1))
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
    """The `Wörter x · Paare y` pair from `METRIC`'s status blockquote.

    The headlines stay in the metric document even though the ledger moved with
    the journal: that blockquote is where `qualitaetsmetrik.md` promises them at
    exactly ONE place, and splitting the promise would be the defect this gate
    exists against.
    """
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


def check_register(text: str, archive_text: str) -> list[str]:
    problems: list[str] = []
    archive_name = ARCHIVE_PAGE.name
    # Keyed by (file, anchor) so an archived entry and a journal entry can never
    # be confused for one another, however similar their titles.
    known = {("", entry.anchor): entry for entry in entries(text)}
    known.update({(archive_name, entry.anchor): entry for entry in archive_entries(archive_text)})
    claimed: dict[tuple[str, str], int] = {}
    for row in register_rows(text):
        if len(row.cells) != 5:
            problems.append(f"{JOURNAL}:{row.line}: register row has {len(row.cells)} columns, expected 5")
            continue
        link = _LINK.search(row.cells[2])
        if link is None:
            problems.append(f"{JOURNAL}:{row.line}: register row's Arm cell carries no anchor link: {row.cells[2]}")
            continue
        target = (link.group("file"), link.group("anchor"))
        if target[0] not in ("", archive_name):
            problems.append(
                f"{JOURNAL}:{row.line}: register row links into '{target[0]}' — a row reaches this file "
                f"or '{archive_name}', nothing else"
            )
            continue
        if target not in known:
            problems.append(
                f"{JOURNAL}:{row.line}: register row points at {target[0]}#{target[1]}, which is no §14 heading"
            )
            continue
        if target in claimed:
            problems.append(f"{JOURNAL}:{row.line}: #{target[1]} already has a register row at line {claimed[target]}")
            continue
        claimed[target] = row.line
    for target, entry in known.items():
        if target not in claimed:
            page = ARCHIVE_PAGE if target[0] else JOURNAL
            problems.append(
                f"{page}:{entry.line}: §14 entry '{entry.title}' has no register row — "
                f"add one to '{INDEX_HEADINGS[0]}' in this PR (link target: {target[0]}#{target[1]})"
            )
    for stray in stray_entries(text):
        problems.append(
            f"{JOURNAL}:{stray.line}: '{stray.title}' sits AFTER §14 — §14 is a closed section and the "
            f"only one in this file: move it inside, or into '{archive_name}' if its arm is finished, and "
            "give it its register row. If it is no journal entry at all, declare it in "
            "tools/docs_register POST_JOURNAL_SUBHEADINGS"
        )
    return problems


def check_ledger(text: str, metric_text: str) -> list[str]:
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
    headline = status_headline(metric_text)
    if headline is None:
        problems.append(f"{METRIC}: the status blockquote names no 'Wörter … · Paare …' headline")
    elif rows and len(rows[-1].cells) == 6:
        newest = (_LOSS.search(rows[-1].cells[3]), _LOSS.search(rows[-1].cells[4]))
        if all(newest) and tuple(m.group(0) for m in newest) != headline:  # type: ignore[union-attr]
            problems.append(
                f"{JOURNAL}:{rows[-1].line}: the newest ledger row "
                f"({newest[0].group(0)} / {newest[1].group(0)}) is not the headline of {METRIC}'s status "  # type: ignore[union-attr]
                f"blockquote ({headline[0]} / {headline[1]}) — a run that moves the headline adds its row"
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
    return (
        check_register(text, _read(root, ARCHIVE_PAGE))
        + check_ledger(text, _read(root, METRIC))
        + check_verfahren(text, root=root)
    )


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
