"""Tests for the candidate side (`tools.tracebench.candidates`).

Three properties carry the module:

* a candidate that could not be STORED is never praised — the wire bounds are
  checked here and pinned against `api.schemas.WordInstanceItem`, the only other
  place they exist;
* a provider failure is a ROW, never an exception, because one unauthored letter
  must not take a bench run down; and
* the `chain` candidate runs the HARVEST's own code path. That last one is
  proved on the harvest suite's synthetic ink: the strokes the provider hands
  the bench are byte-for-byte the ones the harvest would store.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from tests.test_tracebench_reference import row, write_root
from tools.tracebench.candidates import (
    CANDIDATE_FRAME,
    MAX_ABS_COORD,
    MAX_STROKE_POINTS,
    MAX_WORD_STROKES,
    Candidate,
    authored_provider,
    candidate_from_wire,
    chain_provider,
    file_provider,
    traced_provider,
    wire_violation,
)
from tools.tracebench.reference import load_reference


STROKE = [[0.1, 0.1], [0.6, 0.9], [1.2, 0.2]]
REGISTRATION = {"tx": 4.0, "ty": 0.0, "baseline_row": 70}


# ------------------------------------------------------------- the wire bounds


@pytest.mark.parametrize(
    ("strokes", "fragment"),
    [
        ([], "no strokes"),
        ([[[0.0, 0.0]]], "points"),
        ([[[0.0, 0.0], [1.0, MAX_ABS_COORD + 1.0]]], "range"),
        ([[[0.0, 0.0], [1.0, "x"]]], "non-numeric"),
        ([[[0.0, 0.0], [1.0, 2.0, 3.0]]], "[x, y] pair"),
        ([STROKE] * (MAX_WORD_STROKES + 1), "cap"),
        ([[[0.0, 0.0]] * (MAX_STROKE_POINTS + 1)], "points"),
    ],
)
def test_a_candidate_that_could_not_be_stored_fails_with_a_reason(strokes: list, fragment: str) -> None:
    assert fragment in wire_violation(strokes)
    candidate = candidate_from_wire(strokes, REGISTRATION, 30.0)
    assert candidate.status == "failed" and fragment in candidate.detail
    assert not candidate.ok


def test_the_bounds_are_the_ones_the_write_endpoint_enforces() -> None:
    """The caps are re-declared, so they are pinned against their only twin.

    `api.schemas.WordInstanceItem` is what a stored row must pass; a bench that
    accepted a wider trace would grade something the product could never keep.
    """
    from pydantic import ValidationError  # noqa: PLC0415

    from api.schemas import WordInstanceItem  # noqa: PLC0415

    def stored(strokes: list) -> None:
        WordInstanceItem(specimen_id="die", word="die", slots=["d"], strokes=strokes)

    stored([STROKE])  # the shape the bench calls clean is storable
    assert wire_violation([STROKE]) == ""
    for strokes in ([[[0.0, 0.0]]], [[[0.0, 0.0], [1.0, MAX_ABS_COORD + 1.0]]], [STROKE] * (MAX_WORD_STROKES + 1)):
        assert wire_violation(strokes)
        with pytest.raises(ValidationError):
            stored(strokes)


@pytest.mark.parametrize("xh", [None, 0.0, -12.0, "eleven"])
def test_a_candidate_without_a_usable_pixel_scale_fails(xh) -> None:
    assert candidate_from_wire([STROKE], REGISTRATION, xh).status == "failed"


def test_a_candidate_without_a_baseline_row_fails() -> None:
    candidate = candidate_from_wire([STROKE], {"tx": 1.0}, 30.0)
    assert candidate.status == "failed" and "baseline_row" in candidate.detail


def test_a_candidate_is_immutable() -> None:
    """It crosses a process boundary with `--jobs`; nothing may adjust it on the way."""
    candidate = candidate_from_wire([STROKE], REGISTRATION, 30.0)
    assert candidate.ok
    with pytest.raises(dataclasses.FrozenInstanceError):
        candidate.status = "ok"  # type: ignore[misc]


# ---------------------------------------------------------- the stored rows


def test_the_authored_and_traced_providers_read_their_own_provenance(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die"), row("mit", "traced")], order=["die", "mit"]))
    ids = ["die", "mit"]
    authored = authored_provider(reference, ids)
    traced = traced_provider(reference, ids)
    assert authored["die"].ok and authored["mit"].status == "skipped"
    assert traced["mit"].ok and traced["die"].status == "skipped"
    # …and the identity input is the stored row verbatim
    assert authored["die"].strokes == reference.entries["die"].row.strokes


def test_an_unknown_specimen_is_a_skipped_row_not_a_crash(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    out = authored_provider(reference, ["die", "nirgends"])
    assert out["nirgends"].status == "skipped" and "no scoreable row" in out["nirgends"].detail


# ------------------------------------------------------------- the file route


def _candidate_file(path: Path, **payload) -> Path:
    path.write_text(json.dumps({"frame": CANDIDATE_FRAME, **payload}))
    return path


def test_the_file_provider_reads_a_stored_shaped_row(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    path = _candidate_file(
        tmp_path / "cand.json",
        label="follow-v1",
        rows=[
            {
                "specimen_id": "die",
                "strokes": [STROKE],
                "measurements": {"registration_px": REGISTRATION, "xh_px": 30.0},
            }
        ],
    )
    candidate = file_provider(path)(reference, ["die"])["die"]
    assert candidate.ok and candidate.strokes == [STROKE]
    assert candidate.meta["label"] == "follow-v1"


def test_the_file_provider_also_takes_the_flat_row_shape(tmp_path: Path) -> None:
    """A generator that never had a `measurements` block to fill."""
    reference = load_reference(write_root(tmp_path, [row("die")]))
    path = _candidate_file(
        tmp_path / "cand.json",
        rows=[{"specimen_id": "die", "strokes": [STROKE], "registration_px": REGISTRATION, "xh_px": 30.0}],
    )
    assert file_provider(path)(reference, ["die"])["die"].ok


def test_the_frame_literal_is_mandatory(tmp_path: Path) -> None:
    """§2.4's refusal: a trace in an unstated frame is not measured, it is refused.

    Crop pixels or a model's own 224-grid would otherwise be read as a
    catastrophic tracing error — a wrong number instead of an honest stop.
    """
    reference = load_reference(write_root(tmp_path, [row("die")]))
    for payload in ({"rows": []}, {"frame": "crop_px", "rows": []}):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(payload))
        with pytest.raises(SystemExit, match="frame"):
            file_provider(path)(reference, ["die"])


def test_an_unknown_id_in_the_file_is_reported_not_raised(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    path = _candidate_file(
        tmp_path / "cand.json",
        rows=[
            {"specimen_id": "die", "strokes": [STROKE], "registration_px": REGISTRATION, "xh_px": 30.0},
            {"specimen_id": "gibtsnicht", "strokes": [STROKE], "registration_px": REGISTRATION, "xh_px": 30.0},
            {"strokes": [STROKE]},
        ],
    )
    out = file_provider(path)(reference, ["die"])
    printed = capsys.readouterr().out
    assert out["die"].ok
    assert "gibtsnicht" in printed and "without a specimen_id" in printed


def test_a_word_the_file_does_not_carry_is_skipped_by_name(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die"), row("mit")], order=["die", "mit"]))
    path = _candidate_file(
        tmp_path / "cand.json",
        rows=[{"specimen_id": "die", "strokes": [STROKE], "registration_px": REGISTRATION, "xh_px": 30.0}],
    )
    out = file_provider(path)(reference, ["die", "mit"])
    assert out["mit"].status == "skipped" and "cand.json" in out["mit"].detail


def test_a_malformed_candidate_file_stops_the_run_by_name(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    path = tmp_path / "broken.json"
    path.write_text("{not json")
    with pytest.raises(SystemExit, match="broken.json"):
        file_provider(path)(reference, ["die"])


# ------------------------------------------------------------ the chain route


def test_the_chain_provider_returns_what_the_harvest_would_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The chain candidate IS the harvest's own path — byte for byte.

    The synthetic specimen of `tests/test_laufform_harvest.py` (rasterised ink
    of a known shape, real grid windows, real `fit_word_chain`) is run twice:
    once through `harvest_case`, which is what writes `word_instances`, and once
    through the provider. A baseline that is a reimplementation stops being the
    baseline the moment the two drift, so the equality is asserted rather than
    assumed.
    """
    from tests.test_laufform_harvest import _synthetic_word  # noqa: PLC0415
    from tools.laufform import harvest as harvest_mod  # noqa: PLC0415
    from tools.laufform.harvest import HarvestOptions, harvest_case  # noqa: PLC0415
    from tools.tracebench import candidates as candidates_mod  # noqa: PLC0415

    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    stored = harvest_case(case, HarvestOptions(path="chain", rmse_max=2.5)).word_record

    reference = load_reference(write_root(tmp_path, [row(case.id)]))
    provider = chain_provider(fixtures_root=tmp_path)
    # The fixture loader and the composition are the only things stubbed: the
    # solve, the assembly and the record builder are the harvest's own.
    monkeypatch.setattr(candidates_mod, "_chain_cases", lambda *a, **kw: {case.id: case})
    monkeypatch.setattr(candidates_mod, "_chain_derive", lambda c: result)
    candidate = provider(reference, [case.id])[case.id]

    assert candidate.ok, candidate.detail
    assert candidate.strokes == stored["strokes"]
    assert candidate.registration_px == stored["measurements"]["registration_px"]
    assert candidate.xh_px == stored["measurements"]["xh_px"]
    assert candidate.meta["fit_path"] == "chain"
    assert candidate.meta["traced_slots"] == stored["measurements"]["traced_slots"]


def test_a_word_without_a_fixture_case_is_a_skipped_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.tracebench import candidates as candidates_mod  # noqa: PLC0415

    reference = load_reference(write_root(tmp_path, [row("die")]))
    provider = chain_provider(fixtures_root=tmp_path)
    monkeypatch.setattr(candidates_mod, "_chain_cases", lambda *a, **kw: {})
    assert provider(reference, ["die"])["die"].status == "skipped"


def test_a_solver_crash_is_one_row_not_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tools.tracebench import candidates as candidates_mod  # noqa: PLC0415

    reference = load_reference(write_root(tmp_path, [row("die")]))
    provider = chain_provider(fixtures_root=tmp_path)

    class _Case:
        id = "die"
        scorable = True

    def _boom(_case):
        raise RuntimeError("the optimiser gave up")

    monkeypatch.setattr(candidates_mod, "_chain_cases", lambda *a, **kw: {"die": _Case()})
    monkeypatch.setattr(candidates_mod, "_chain_derive", _boom)
    candidate = provider(reference, ["die"])["die"]
    assert candidate.status == "failed" and "the optimiser gave up" in candidate.detail


def test_a_provider_answers_for_every_id_it_was_asked_about(tmp_path: Path) -> None:
    """The scorer indexes by id — a provider that skips a key silently would
    turn a missing candidate into a missing ROW."""
    reference = load_reference(write_root(tmp_path, [row("die"), row("mit")], order=["die", "mit"]))
    ids = ["die", "mit"]
    for out in (authored_provider(reference, ids), traced_provider(reference, ids)):
        assert set(out) == set(ids)
        assert all(isinstance(c, Candidate) for c in out.values())


def test_a_candidate_owns_its_geometry():
    # Review finding: an aliased caller list mutated after construction must
    # not change what gets measured.
    strokes = [[[0.1, 0.2], [0.3, 0.4]]]
    candidate = candidate_from_wire(strokes, {"tx": 0, "ty": 0, "baseline_row": 60}, 30.0)
    strokes[0][0][0] = 99.0
    assert candidate.strokes[0][0][0] == 0.1
