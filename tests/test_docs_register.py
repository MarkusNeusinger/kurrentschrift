"""Unit tests for the §14 register gate.

The gate exists because three "same PR" duties written in prose all decayed at
once (audit 2026-09-02), so every rule is pinned here against a synthetic
journal — a missing register row, a dangling anchor, a headline invented in the
ledger, a route whose process page never heard of it — plus one run against the
repository's real files, which is the call the CI job makes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import docs_register as dr


JOURNAL = """# Titel

> **Status (2026-09-02): lebend.** Aktuelle Headlines:
> Wörter 0,109255 · Paare 0,148433 (Re-Baseline `sep01`).

## 13. Etwas anderes

### Ein Abschnitt davor

## 14. Tintenfolger-Bench (`tracebench`)

Vorspann.

### Register der Einträge (Index, keine Zahl-Heimat)

| Datum | Route | Arm (Link → Abschnitt) | Typ · Verdikt | Befund in einer Zeile |
|---|---|---|---|---|
| aug14 | Kette | [Baseline](#baseline-aug14--der-freeze-akt) | gemessen | dtw 0,062 med |
| aug20 | Lotse | [v0.17](#lotse-v017-aug20--das-reservierungs-veto) | gemessen · adoptiert | zähler-identisch |

### Headline-Ledger (die Wordbench-Zahlen und ihre Wurzeln)

| Datum | PR | Wurzel / Re-Baseline | Wörter | Paare | Beleg |
|---|---|---|---|---|---|
| sep01 | #472 | Re-Baseline | 0,109255 | 0,148433 | §15 |

### Baseline `aug14` — der Freeze-Akt

Kette dtw 0,062 med.

### Lotse v0.17 `aug20` — das Reservierungs-Veto

Zähler-identisch.

## 15. Danach

Wörter 0,109255 · Paare 0,148433 im Fließtext.
"""

KETTE = """# Verfahrensseite Kette

| Datum | Arm | Verdikt |
|---|---|---|
| aug14 | Baseline | eingefroren |
"""

LOTSE = """# Verfahrensseite Lotse

| Datum | Version | Verdikt |
|---|---|---|
| aug20 | v0.17 | adoptiert |
"""

INKSIGHT = "# InkSight\n\n| Datum | Stufe |\n|---|---|\n| aug15 | T0 |\n"
NULLPROBE = "# Nullprobe\n\n| Datum | Messung |\n|---|---|\n| aug14 | Kontrolllauf |\n"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A throwaway tree with just the five files the gate reads."""
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    _write(tmp_path, dr.JOURNAL, JOURNAL)
    _write(tmp_path, dr.ROUTE_PAGES["Kette"], KETTE)
    _write(tmp_path, dr.ROUTE_PAGES["Lotse"], LOTSE)
    _write(tmp_path, dr.ROUTE_PAGES["InkSight"], INKSIGHT)
    _write(tmp_path, dr.ROUTE_PAGES["Nullprobe"], NULLPROBE)
    return tmp_path


def _write(root: Path, path: Path, text: str) -> None:
    (root / path).write_text(text, encoding="utf-8")


def test_the_synthetic_journal_passes_every_rule(repo: Path) -> None:
    assert dr.check_all(root=repo) == []


def test_the_two_index_headings_are_not_themselves_entries(repo: Path) -> None:
    titles = [entry.title for entry in dr.entries(JOURNAL)]
    assert titles == ["Baseline `aug14` — der Freeze-Akt", "Lotse v0.17 `aug20` — das Reservierungs-Veto"]


def test_a_section_before_14_is_not_an_entry(repo: Path) -> None:
    assert all("davor" not in entry.title for entry in dr.entries(JOURNAL))


def test_an_entry_without_a_register_row_fails(repo: Path) -> None:
    # The new section must land INSIDE §14, so splice it in before §15.
    text = JOURNAL.replace("## 15. Danach", "### Kette K-Z `sep02` — ein neuer Arm\n\nGemessen.\n\n## 15. Danach")
    _write(repo, dr.JOURNAL, text)
    problems = dr.check_all(root=repo)
    assert any("has no register row" in p for p in problems)


def test_a_register_row_pointing_nowhere_fails(repo: Path) -> None:
    text = JOURNAL.replace("#lotse-v017-aug20--das-reservierungs-veto", "#gibt-es-nicht")
    _write(repo, dr.JOURNAL, text)
    problems = dr.check_all(root=repo)
    assert any("which is no §14 heading" in p for p in problems)
    assert any("has no register row" in p for p in problems)


def test_a_headline_the_journal_never_names_fails(repo: Path) -> None:
    text = JOURNAL.replace(
        "| sep01 | #472 | Re-Baseline | 0,109255 | 0,148433 | §15 |",
        "| sep01 | #472 | Re-Baseline | 0,109255 | 0,148433 | §15 |\n"
        "| sep02 | #999 | frei erfunden | 0,101010 | 0,202020 | — |",
    )
    _write(repo, dr.JOURNAL, text)
    problems = dr.check_all(root=repo)
    assert any("appears nowhere else in the journal" in p for p in problems)


def test_the_newest_ledger_row_must_be_the_status_headline(repo: Path) -> None:
    text = JOURNAL.replace("> Wörter 0,109255 · Paare 0,148433", "> Wörter 0,106400 · Paare 0,146580")
    _write(repo, dr.JOURNAL, text)
    problems = dr.check_all(root=repo)
    assert any("is not the status blockquote's headline" in p for p in problems)


def test_a_route_entry_missing_from_its_process_page_fails(repo: Path) -> None:
    _write(repo, dr.ROUTE_PAGES["Lotse"], LOTSE.replace("| aug20 |", "| aug19 |"))
    problems = dr.check_all(root=repo)
    assert any("has no ledger row in docs/reference/verfahren-lotse.md" in p for p in problems)


def test_alle_routen_needs_the_date_on_every_page(repo: Path) -> None:
    text = JOURNAL.replace(
        "| aug14 | Kette | [Baseline](#baseline-aug14--der-freeze-akt) | gemessen | dtw 0,062 med |",
        "| aug14 | alle Routen | [Baseline](#baseline-aug14--der-freeze-akt) | gemessen | dtw 0,062 med |",
    )
    _write(repo, dr.JOURNAL, text)
    problems = dr.check_all(root=repo)
    # InkSight's synthetic ledger knows aug15 only.
    assert any("verfahren-inksight.md" in p for p in problems)
    assert not any("verfahren-nullprobe.md" in p for p in problems)


def test_a_missing_register_heading_is_reported_not_raised(repo: Path) -> None:
    _write(repo, dr.JOURNAL, JOURNAL.replace("### Register der Einträge (Index, keine Zahl-Heimat)", "### Weg"))
    with pytest.raises(dr.RegisterError):
        dr.check_all(root=repo)


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [
        ("Kill-Kriterien", "kill-kriterien"),
        ("Was gemessen wird — und in welchem Rahmen", "was-gemessen-wird--und-in-welchem-rahmen"),
        (
            "Arm ⑥b `aug14` — Vorregistrierung: Klassenbewusste Korrespondenz",
            "arm-⑥b-aug14--vorregistrierung-klassenbewusste-korrespondenz",
        ),
    ],
)
def test_the_slug_matches_githubs_rule(heading: str, anchor: str) -> None:
    assert dr.github_slug(heading) == anchor


def test_a_repeated_heading_gets_githubs_numeric_suffix() -> None:
    text = JOURNAL.replace(
        "### Lotse v0.17 `aug20` — das Reservierungs-Veto\n\nZähler-identisch.",
        "### Baseline `aug14` — der Freeze-Akt\n\nZweimal derselbe Titel.",
    )
    assert [entry.anchor for entry in dr.entries(text)] == [
        "baseline-aug14--der-freeze-akt",
        "baseline-aug14--der-freeze-akt-1",
    ]


def test_the_repository_itself_passes() -> None:
    assert dr.check_all() == []
