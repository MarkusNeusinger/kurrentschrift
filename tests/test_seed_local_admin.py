"""The guards of the throwaway seeder `/verify-frontend` uses.

The script itself lives under `.claude/skills/verify-frontend/` — it is a skill
asset, not a package module (`tools/` is the measurement layer and writes no
DB). Its guards are nevertheless safety-critical: they are what stands between
`uv run python seed-local-admin.py` and a `PUT /eigenhand/setups/<hand>` into
the shared Cloud SQL database, which `api/routers/eigenhand.py` documents as a
plain overwrite. They are also pure or cheaply faked, so they belong in the
suite rather than in a manual gate run that nobody repeats.

Loaded by path because `.claude` cannot be a package name.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest


SEEDER_PATH = Path(__file__).resolve().parents[1] / ".claude/skills/verify-frontend/seed-local-admin.py"


def _load_seeder():
    spec = importlib.util.spec_from_file_location("seed_local_admin", SEEDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


seeder = _load_seeder()


class FakeApi:
    """Stands in for `AdminApi`: answers the hand list, records every write."""

    def __init__(self, hands: list[str]) -> None:
        self.hands = hands
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, path))
        if method == "GET" and path == "/eigenhand/hands":
            return {"hands": self.hands, "styles": ["kurrent", "suetterlin", "offenbacher"]}
        raise AssertionError(f"unexpected {method} {path} — the guard should have stopped first")


@pytest.fixture
def run_main(monkeypatch):
    """Run `main(argv)` with a token exported and the API faked out."""

    def run(
        argv: list[str], hands: list[str] | None = None, token: str | None = "local-throwaway-token"
    ) -> tuple[int | None, str, FakeApi]:
        api = FakeApi(list(hands or []))
        if token is None:
            monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        else:
            monkeypatch.setenv("ADMIN_TOKEN", token)
        monkeypatch.setattr(seeder, "AdminApi", lambda base, token: (seeder.checked_base(base), api)[1])
        # `seed()` is the only thing past the guards; a test that reaches it has
        # already proved what it wanted to, so let it say so loudly.
        monkeypatch.setattr(seeder, "seed", lambda *a, **k: api.calls.append(("SEED", "reached")))
        try:
            return seeder.main(argv), "", api
        except SystemExit as exit_:
            return None, str(exit_), api

    return run


@pytest.mark.parametrize("base", ["http://localhost:8000", "http://127.0.0.1:8000", "http://[::1]:8000"])
def test_checked_base_accepts_loopback(base: str) -> None:
    assert seeder.checked_base(base) == base


@pytest.mark.parametrize(
    "base",
    [
        "https://api.kurrentschrift.ink",
        "https://kurrentschrift.ink/api",
        "http://10.0.0.5:8000",
        "http://localhost.evil.example",
    ],
)
def test_checked_base_refuses_anything_else(base: str) -> None:
    with pytest.raises(SystemExit, match="not loopback"):
        seeder.checked_base(base)


def test_checked_base_refuses_a_non_url() -> None:
    with pytest.raises(SystemExit, match="not an http"):
        seeder.checked_base("/var/tmp/pg-kurrent")


def test_checked_base_strips_a_trailing_slash() -> None:
    assert seeder.checked_base("http://localhost:8000/") == "http://localhost:8000"


def test_default_hand_is_reserved_and_legal() -> None:
    # A default outside the reserved namespace would make every plain run refuse
    # itself; one that is not a legal hand id would 422 at the first write.
    assert seeder.DEFAULT_HAND.startswith(seeder.RESERVED_HAND_PREFIX)
    assert seeder.is_hand_id(seeder.DEFAULT_HAND)


@pytest.mark.parametrize("hand", ["mn-suetterlin", "mn-kurrent", "suetterlin", "wegwerf-gotisch"])
def test_a_hand_outside_the_reserved_namespace_is_refused(run_main, hand: str) -> None:
    # Without this the foreign-hand guard is bypassable: naming the author's own
    # hand re-labels it as „this run's own" and lets --reseed overwrite it.
    code, message, api = run_main(["--hand", hand, "--reseed"], hands=[hand])
    assert code is None
    assert "not a throwaway hand" in message
    assert api.calls == []


@pytest.mark.parametrize("fassung", ["f2", "F1", "", "F0a", "01"])
def test_a_malformed_fassung_is_refused_before_any_request(run_main, fassung: str) -> None:
    code, message, api = run_main(["--fassung", fassung])
    assert code is None
    assert "not a Fassung id" in message
    assert api.calls == []


def test_a_foreign_hand_stops_the_run_even_with_reseed(run_main) -> None:
    # The signature of the shared database: a hand this run did not write. No
    # flag may talk past it.
    code, message, api = run_main(["--reseed"], hands=["mn-suetterlin"])
    assert code is None
    assert "that this run did not write" in message
    assert api.calls == [("GET", "/eigenhand/hands")]


def test_the_seeders_own_hand_needs_reseed(run_main) -> None:
    code, message, _ = run_main([], hands=[seeder.DEFAULT_HAND])
    assert code is None
    assert "--reseed" in message


def test_reseed_on_the_seeders_own_hand_proceeds(run_main) -> None:
    code, message, api = run_main(["--reseed", "--fassung", "F02"], hands=[seeder.DEFAULT_HAND])
    assert code == 0, message
    assert ("SEED", "reached") in api.calls


def test_an_empty_hand_list_proceeds(run_main) -> None:
    code, message, api = run_main([], hands=[])
    assert code == 0, message
    assert ("SEED", "reached") in api.calls


def test_a_remote_api_is_refused_before_the_hand_list(run_main) -> None:
    code, message, api = run_main(["--api", "https://api.kurrentschrift.ink"], hands=[])
    assert code is None
    assert "not loopback" in message
    assert api.calls == []


def test_a_missing_token_stops_the_run(run_main) -> None:
    # Without the token every admin route answers 503, so the run would fail
    # halfway through and leave a half-seeded Bogen behind.
    code, message, api = run_main([], hands=[], token=None)
    assert code is None
    assert "ADMIN_TOKEN" in message
    assert api.calls == []


def test_the_sensor_spread_carries_the_two_values_a_pipe_reader_gets_wrong() -> None:
    # The whole point of the invented numbers: a reader that writes `x || "—"`
    # turns the best box into „not measured" and a missing sensor into 0.
    assert any(entry["ink_unvisited_share"] == 0.0 for entry in seeder.TINTENPFAD_SPREAD)
    assert any(entry["hairpins"] is None for entry in seeder.TINTENPFAD_SPREAD)
