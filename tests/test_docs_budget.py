"""Unit tests for the reading-cost gate.

The gate exists because the mandatory reading list grew to 110 997 tokens one
paragraph at a time and nobody noticed until it was measured (2026-09-04). Each
rule is pinned here against a synthetic docs tree — a budget blown, a Stand
block too short or too old, a map row missing or doubled, a dead anchor — plus
one run against the repository's real files, which is the call the CI job makes.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from tools import docs_budget as db


CLAUDE = """# CLAUDE.md

## Read these before substantive work

Start at `docs/index.md`.

- `docs/concepts/vision.md` — the vision, and it also names `docs/reference/glossar.md` in passing
- `docs/reference/kurzglossar.md` + `docs/reference/datenablage.md` — two subjects in one bullet

**Reading paths per track** (a table follows):

| Track | Read | tokens |
|---|---|---|
| Frontend | `design-system.md` | 1k |
"""

INDEX = """# Dokumentation

> **Status (2026-09-04): lebend.** Die Karte.

| Doc | Wofür |
|---|---|
| [concepts/vision.md](concepts/vision.md) | Die Vision |
| [reference/kurzglossar.md](reference/kurzglossar.md) | Die Kurzfassung |
| [reference/glossar.md](reference/glossar.md) | Das volle Glossar |
| [reference/datenablage.md](reference/datenablage.md) | Der `/data`-Baum |
| [index.md](index.md) | Diese Karte |
"""

SMALL = "# Titel\n\n> **Status (2026-09-04): lebend.** Klein genug.\n\nProsa.\n"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A throwaway tree with a CLAUDE.md, a map and four small docs."""
    (tmp_path / "docs" / "concepts").mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text(CLAUDE, encoding="utf-8")
    (tmp_path / "docs" / "index.md").write_text(INDEX, encoding="utf-8")
    for rel in ("concepts/vision.md", "reference/kurzglossar.md", "reference/glossar.md", "reference/datenablage.md"):
        (tmp_path / "docs" / rel).write_text(SMALL, encoding="utf-8")
    return tmp_path


def _big(status: str = "lebend", date: str = "2026-09-04", stand_lines: int = 20) -> str:
    """A doc over the Stand-block threshold, with a head of the requested length."""
    head = "\n".join(f"> Zeile {i} des Stand-Blocks mit genug Text, damit sie zählt." for i in range(stand_lines - 1))
    body = "\n".join(f"Absatz {i}: " + "Übergangsraum Schwellzug Laufform Kettenfit Duktus. " * 12 for i in range(200))
    return f"# Groß\n\n> **Status ({date}): {status}.** Der Kopf.\n{head}\n\n{body}\n"


# --- rule 1: the budgets -----------------------------------------------------


def test_the_mandatory_list_is_read_out_of_claude_md(repo: Path) -> None:
    # Not duplicated in the module: adding a bullet must move the measured sum.
    assert db.mandatory_docs(repo) == [
        Path("docs/index.md"),
        Path("docs/concepts/vision.md"),
        Path("docs/reference/kurzglossar.md"),
        Path("docs/reference/datenablage.md"),
    ]


def test_a_doc_named_only_in_a_bullets_description_is_not_on_the_list(repo: Path) -> None:
    # `glossar.md` appears inside the vision bullet's text. Counting it would put
    # 57 000 tokens back on a list that deliberately took them off.
    assert Path("docs/reference/glossar.md") not in db.mandatory_docs(repo)


def test_a_blown_budget_fails(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "PATHS", {})
    monkeypatch.setattr(db, "BUDGETS", {"mandatory": 10})
    problems = db.check_budgets(repo)
    assert any("over its budget" in p for p in problems)


def test_a_budget_without_a_path_is_reported(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A renamed path would otherwise stop being measured in silence — the budget
    # would stay green while nothing behind it is counted.
    monkeypatch.setattr(db, "PATHS", {})
    monkeypatch.setattr(db, "BUDGETS", {"mandatory": 10_000, "weg": 1})
    assert any("measures nothing" in p for p in db.check_budgets(repo))


def test_the_proxy_is_deterministic_and_scales_with_length() -> None:
    text = "Übergangsraum und Schwellzug, zweimal gezählt."
    assert db.proxy_tokens(text) == db.proxy_tokens(text)
    assert db.proxy_tokens(text * 3) > db.proxy_tokens(text)


def test_the_proxy_splits_german_compounds() -> None:
    # A 13-letter compound is not one token, and a proxy that said so would make
    # every German doc look cheaper than it reads.
    assert db.proxy_tokens("Übergangsraum") > db.proxy_tokens("Raum")


# --- rule 2: Stand blocks ----------------------------------------------------


def test_a_large_lebend_doc_owes_a_stand_block(repo: Path) -> None:
    (repo / "docs" / "reference" / "gross.md").write_text(_big(stand_lines=3), encoding="utf-8")
    assert any("owes a Stand block" in p for p in db.check_stand_blocks(repo))


def test_a_stale_stand_block_fails(repo: Path) -> None:
    (repo / "docs" / "reference" / "gross.md").write_text(_big(date="2026-07-01"), encoding="utf-8")
    problems = db.check_stand_blocks(repo, today=dt.date(2026, 9, 4))
    assert any("days ago" in p for p in problems)


def test_a_fresh_stand_block_passes(repo: Path) -> None:
    (repo / "docs" / "reference" / "gross.md").write_text(_big(), encoding="utf-8")
    assert db.check_stand_blocks(repo, today=dt.date(2026, 9, 4)) == []


def test_only_lebend_docs_owe_a_fresh_date(repo: Path) -> None:
    # A `bindend` decision is as true as the day it was written; demanding a
    # monthly date bump on it would train everyone to bump dates without reading.
    (repo / "docs" / "reference" / "gross.md").write_text(_big(status="bindend", date="2026-01-01"), encoding="utf-8")
    assert db.check_stand_blocks(repo, today=dt.date(2026, 9, 4)) == []


def test_a_small_doc_owes_nothing(repo: Path) -> None:
    assert db.check_stand_blocks(repo, today=dt.date(2026, 9, 4)) == []


# --- rule 3: the map ---------------------------------------------------------


def test_a_doc_without_a_map_row_fails(repo: Path) -> None:
    (repo / "docs" / "reference" / "neu.md").write_text(SMALL, encoding="utf-8")
    assert any("no row for docs/reference/neu.md" in p for p in db.check_map(repo))


def test_a_map_row_for_a_deleted_doc_fails(repo: Path) -> None:
    (repo / "docs" / "reference" / "glossar.md").unlink()
    assert any("does not exist" in p for p in db.check_map(repo))


def test_a_doubled_map_row_fails(repo: Path) -> None:
    index = (repo / "docs" / "index.md").read_text(encoding="utf-8")
    (repo / "docs" / "index.md").write_text(
        index + "| [reference/glossar.md](reference/glossar.md) | noch einmal |\n", encoding="utf-8"
    )
    assert any("has 2 rows" in p for p in db.check_map(repo))


def test_the_synthetic_map_agrees(repo: Path) -> None:
    assert db.check_map(repo) == []


# --- rule 4: every jump lands ------------------------------------------------


def test_a_link_to_a_missing_file_fails(repo: Path) -> None:
    (repo / "docs" / "reference" / "glossar.md").write_text(SMALL + "\nSiehe [nirgends](weg.md).\n", encoding="utf-8")
    assert any("does not exist" in p for p in db.check_links(repo))


def test_a_dead_anchor_fails(repo: Path) -> None:
    (repo / "docs" / "reference" / "glossar.md").write_text(
        SMALL + "\nSiehe [dorthin](kurzglossar.md#gibt-es-nicht).\n", encoding="utf-8"
    )
    assert any("dead anchor" in p for p in db.check_links(repo))


def test_a_live_anchor_passes(repo: Path) -> None:
    (repo / "docs" / "reference" / "kurzglossar.md").write_text(SMALL + "\n## Ein Abschnitt\n", encoding="utf-8")
    (repo / "docs" / "reference" / "glossar.md").write_text(
        SMALL + "\nSiehe [dorthin](kurzglossar.md#ein-abschnitt).\n", encoding="utf-8"
    )
    assert db.check_links(repo) == []


def test_a_heading_inside_a_fenced_block_is_no_anchor() -> None:
    # `# comment` in a shell example is a comment; counting it would invent an
    # anchor and let a genuinely dead link pass.
    text = "# Titel\n\n```bash\n# nur ein Kommentar\n```\n\n## Echt\n"
    assert db.anchors_of(text) == {"titel", "echt"}


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [
        ("Kill-Kriterien", "kill-kriterien"),
        ("Was gemessen wird — und in welchem Rahmen", "was-gemessen-wird--und-in-welchem-rahmen"),
        ("§5 Werkbank und Prozess", "5-werkbank-und-prozess"),
    ],
)
def test_the_slug_matches_githubs_rule(heading: str, anchor: str) -> None:
    assert db.github_slug(heading) == anchor


# --- the repository itself ---------------------------------------------------


def test_the_repository_itself_passes() -> None:
    assert db.check_all() == []


def test_every_path_doc_is_named_in_the_reading_path_table() -> None:
    """The table in `CLAUDE.md` and `PATHS` describe the same reading paths.

    `PATHS` is data and the table is prose, so they cannot be generated from one
    another; what can be pinned is that no file is measured which the table
    never mentions, and vice versa.
    """
    text = (db.REPO_ROOT / db.CLAUDE_MD).read_text(encoding="utf-8")
    start = text.index(db.LIST_END)
    table = text[start : text.index("**Read situatively**", start)]
    for pieces in db.PATHS.values():
        for piece in pieces:
            assert piece.path.name in table, f"{piece.path.name} is measured but named in no reading path"
