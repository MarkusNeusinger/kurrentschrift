"""The Bestandsbericht's two natures: offline by default, `--faellig` over the API.

`report` is a reading tool over the LOCAL Kartei, and it stays that way — with
one deliberate exception. The due list is „what has not reached the server
yet", so reading it locally would always look done: the weight file is on disk,
every strip image is on disk. `--faellig` therefore asks the server and prints
what `core.eigenhand.faellig` decided there.

Both halves of that are pinned here, because both are easy to lose: the mode
prints the SERVER's commands in the SERVER's order (no local re-derivation),
and every other mode still makes no HTTP call at all.
"""

from __future__ import annotations

import pytest

from tools.eigenhand import report as report_mod


HAND = "test-suetterlin"
BASE = "http://localhost:8000"


@pytest.fixture
def dataroot(tmp_path, monkeypatch):
    """An empty local data root — the offline modes read from here, not from $HOME."""
    monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
    return tmp_path / "own-hand"


@pytest.fixture
def no_http(monkeypatch):
    """Every way out of this process, closed — the client's opener included."""

    def refuse(*args, **kwargs):
        raise AssertionError("report made an HTTP call")

    monkeypatch.setattr(report_mod, "request_json", refuse)
    monkeypatch.setattr("tools.eigenhand.apiclient._OPENER.open", refuse)


def _faked(monkeypatch, payload: dict) -> list[tuple[str, str, str]]:
    """Record every admin call and answer it with `payload`."""
    calls: list[tuple[str, str, str]] = []

    def fake(method: str, url: str, token: str, body=None, allow_404: bool = False):
        calls.append((method, url, token))
        return payload

    monkeypatch.setattr(report_mod, "request_json", fake)
    return calls


class TestFaellig:
    def test_it_prints_the_servers_commands_in_the_servers_order(self, monkeypatch, capsys):
        monkeypatch.setenv("ADMIN_TOKEN", "t0ken")
        payload = {
            "faellig": [
                {"id": "universe_push", "befehl": "uv run python -m tools.eigenhand.universe --push", "params": {}},
                {
                    "id": "bogen_pull",
                    "befehl": f"uv run python -m tools.eigenhand.pull --hand {HAND} --sheet B0003",
                    "params": {"hand": HAND, "sheet": "B0003", "offen": 2},
                },
            ]
        }
        calls = _faked(monkeypatch, payload)

        assert report_mod.main(["--hand", HAND, "--faellig", "--api", BASE]) == 0

        assert calls == [("GET", f"{BASE}/eigenhand/bestand/{HAND}", "t0ken")]
        printed = capsys.readouterr().out
        lines = [line.strip() for line in printed.splitlines() if line.strip()]
        # The order is the server's, and nothing is re-derived here: the command
        # strings are the ones `core.eigenhand.faellig` built.
        assert lines[1:] == [row["befehl"] for row in payload["faellig"]]
        assert HAND in lines[0]

    def test_a_hand_with_nothing_due_says_so_rather_than_printing_nothing(self, monkeypatch, capsys):
        monkeypatch.setenv("ADMIN_TOKEN", "t0ken")
        _faked(monkeypatch, {"faellig": []})
        assert report_mod.main(["--hand", HAND, "--faellig", "--api", BASE]) == 0
        assert "nichts fällig" in capsys.readouterr().out

    def test_an_api_without_the_field_is_an_error_rather_than_an_all_clear(self, monkeypatch):
        """During a deploy window the tool can outrun the API — and „nichts
        fällig" would then be a confident wrong answer about a hand it could
        not read."""
        monkeypatch.setenv("ADMIN_TOKEN", "t0ken")
        _faked(monkeypatch, {"hand": HAND, "queue": []})
        with pytest.raises(SystemExit, match="due list"):
            report_mod.main(["--hand", HAND, "--faellig", "--api", BASE])

    def test_the_token_is_refused_in_the_clear_and_demanded_when_missing(self, monkeypatch):
        monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        _faked(monkeypatch, {"faellig": []})
        # Both refusals come from the shared client, which is the point: the
        # mode gains no second copy of the token or scheme rules.
        with pytest.raises(SystemExit, match="https"):
            report_mod.main(["--hand", HAND, "--faellig", "--api", "http://example.invalid"])
        with pytest.raises(SystemExit, match="admin token"):
            report_mod.main(["--hand", HAND, "--faellig", "--api", BASE])


class TestOffline:
    def test_without_faellig_the_tool_makes_no_http_call(self, dataroot, no_http, capsys):
        """The reading tool stays a reading tool — `--befund` over the local Kartei."""
        assert report_mod.main(["--hand", HAND, "--befund"]) == 0
        assert "Streifen-Befund" in capsys.readouterr().out
