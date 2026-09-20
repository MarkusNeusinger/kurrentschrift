"""The one way the local chain talks to the admin API — over a fake opener.

Everything else in the suite stubs `request_json` / `request_json_with_etag`
out at the module seam, which is right for testing what a TOOL does with an
answer and says nothing about the layer underneath. This file tests that layer
itself, and only what a stub cannot pin because it is what the stub imitates:
the `If-Match` header actually reaching the request, the `ETag` actually being
read off the response, and a refusal arriving as a refusal rather than as a
value some caller then merges.

No network: `_OPENER.open` is replaced, so nothing here can leave the machine
even if the URL were a real one.
"""

from __future__ import annotations

import email.message
import io
import json
import urllib.error
import urllib.request

import pytest

from tools.eigenhand.apiclient import StaleRead, request_answer, request_bytes, request_json, request_json_with_etag


URL = "https://example.invalid/eigenhand/strips/mn-suetterlin/S0001/F01/pfade"
TAG = '"3f1c"'


def _as_message(headers: dict[str, str]) -> email.message.Message:
    """Headers the way `http.client` hands them over — looked up case-blind.

    A plain `dict` would make these tests pin one SPELLING of `ETag` rather
    than the client finding the header at all: HTTP/2 lowercases every field
    name, and a regression to `res.headers["ETag"]` would sail through a fake
    that answers only to that key (found in review, this PR).
    """
    message = email.message.Message()
    for name, value in headers.items():
        message[name] = value
    return message


class _Response:
    """What `urllib` hands back: the bytes, and the headers they came with."""

    def __init__(self, body: bytes, headers: email.message.Message) -> None:
        self._body = body
        self.headers = headers

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


class _FakeOpener:
    """Answers every call with one canned response, and records the requests."""

    def __init__(self, body: bytes = b"{}", headers: dict[str, str] | None = None, error: int | None = None) -> None:
        self.body = body
        self.headers = _as_message(headers or {})
        self.error = error
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float | None = None) -> _Response:
        self.requests.append(request)
        if self.error is not None:
            raise urllib.error.HTTPError(
                request.full_url, self.error, "refused", email.message.Message(), io.BytesIO(self.body)
            )
        return _Response(self.body, self.headers)

    @property
    def sent(self) -> urllib.request.Request:
        assert len(self.requests) == 1, f"{len(self.requests)} requests, expected exactly one"
        return self.requests[0]


@pytest.fixture
def opener(monkeypatch):
    def install(**kwargs) -> _FakeOpener:
        fake = _FakeOpener(**kwargs)
        monkeypatch.setattr("tools.eigenhand.apiclient._OPENER.open", fake)
        return fake

    return install


class TestTheAnswersToken:
    """The read half of a guarded write: the tag travels beside the body."""

    def test_the_answers_etag_comes_back_beside_the_body(self, opener):
        opener(body=b'{"pfade": []}', headers={"ETag": TAG})
        answer = request_answer("GET", URL, "t")
        assert answer is not None
        assert (json.loads(answer.body), answer.etag) == ({"pfade": []}, TAG)

    def test_the_tag_is_found_whatever_case_it_arrives_in(self, opener):
        # HTTP/2 lowercases every field name, and Cloudflare sits between this
        # tool and the API. A tag the client cannot find is a write the server
        # refuses with 428 — the right failure for a missing token, and a
        # baffling one when the token was there all along.
        opener(body=b'{"pfade": []}', headers={"etag": TAG})
        assert request_json_with_etag("GET", URL, "t") == ({"pfade": []}, TAG)

    def test_an_answer_without_a_tag_says_so_rather_than_inventing_one(self, opener):
        # A `None` here is what makes the write fail loudly at the server
        # (428). A client that filled the gap in — from the payload, or with
        # `*` — would be stating this machine's opinion of what is stored.
        opener(body=b'{"pfade": []}')
        assert request_json_with_etag("GET", URL, "t") == ({"pfade": []}, None)

    def test_the_parsed_read_hands_back_both_halves(self, opener):
        opener(body=b'{"format": 2, "pfade": []}', headers={"ETag": TAG})
        body, etag = request_json_with_etag("GET", URL, "t")
        assert (body, etag) == ({"format": 2, "pfade": []}, TAG)

    def test_an_empty_body_reads_as_an_empty_document(self, opener):
        # A 204-shaped answer is not a parse error: `sync` reads the echo of
        # its own push and would otherwise die on the one route that answers
        # with nothing.
        opener(body=b"")
        assert request_json("PUT", URL, "t", {"pfade": []}) == {}


class TestTheWritesCondition:
    """The write half: what the caller passed is what goes on the wire."""

    def test_if_match_travels_verbatim(self, opener):
        fake = opener()
        request_json("PUT", URL, "t", {"pfade": []}, if_match=TAG)
        assert fake.sent.get_header("If-match") == TAG

    def test_a_weakened_validator_is_not_repaired_on_the_way_out(self, opener):
        # Cloudflare weakens a strong tag when it re-encodes an answer. The
        # server accepts the weak form of the same digest; a client that
        # "fixed" it would be asserting a stronger claim than it was handed.
        fake = opener()
        request_json("PUT", URL, "t", {"pfade": []}, if_match=f"W/{TAG}")
        assert fake.sent.get_header("If-match") == f"W/{TAG}"

    def test_a_call_that_names_no_list_sends_no_condition(self, opener):
        # Not `*`, not an empty string: the header is absent, which is what
        # earns the 428 on a guarded route instead of a write that looks safe.
        fake = opener()
        request_json("GET", URL, "t")
        assert fake.sent.get_header("If-match") is None

    def test_the_admin_token_and_the_name_ride_along(self, opener):
        fake = opener()
        request_bytes("GET", URL, "secret")
        assert fake.sent.get_header("X-admin-token") == "secret"
        assert fake.sent.get_header("User-agent", "").startswith("kurrentschrift-eigenhand")


class TestARefusalArrivesAsOne:
    """No refusal ever reaches a caller as a value it can merge."""

    def test_a_stale_read_is_its_own_refusal(self, opener):
        # The type is what lets the two guarded pushes add „run this again"
        # without matching on the server's prose.
        opener(body=b'{"detail": "the stored paths have moved on since this was read"}', error=412)
        with pytest.raises(StaleRead, match="moved on since this was read"):
            request_json("PUT", URL, "t", {"pfade": []}, if_match=TAG)

    def test_a_stale_read_still_stops_a_caller_that_never_heard_of_it(self, opener):
        # `StaleRead` is a `SystemExit`, so `setup`, `universe` and every other
        # push end exactly as loudly as they did before it existed.
        opener(error=412)
        with pytest.raises(SystemExit):
            request_json("PUT", URL, "t", {"pfade": []}, if_match=TAG)

    def test_nothing_is_sent_twice(self, opener):
        # A retry would re-send the same merge against the list that is there
        # now — the lost update the token just refused, with one extra step.
        fake = opener(error=412)
        with pytest.raises(StaleRead):
            request_json("PUT", URL, "t", {"pfade": []}, if_match=TAG)
        assert len(fake.requests) == 1

    def test_a_missing_precondition_is_loud_but_not_stale(self, opener):
        # 428 says the client sent no token at all, which no re-run fixes: it
        # is a bug here or an intermediary stripping the header, and giving it
        # the operator's „try again" would send them round in circles.
        opener(body=b'{"detail": "this write lands on a stored list"}', error=428)
        with pytest.raises(SystemExit) as refused:
            request_json("PUT", URL, "t", {"pfade": []})
        assert not isinstance(refused.value, StaleRead)
        assert "428" in str(refused.value)

    def test_allow_404_swallows_only_the_404(self, opener):
        # „Absence is an answer" is about a hand with no standing setup, never
        # about a write the server refused. A 412 read as `None` would let a
        # restore report the boxes it never stored as restored.
        opener(error=412)
        with pytest.raises(StaleRead):
            request_json("PUT", URL, "t", {"pfade": []}, allow_404=True, if_match=TAG)

    def test_an_absent_row_is_an_answer_only_where_the_caller_says_so(self, opener):
        opener(error=404)
        assert request_json("GET", URL, "t", allow_404=True) is None
        opener(error=404)
        with pytest.raises(SystemExit, match="404"):
            request_json("GET", URL, "t")

    def test_the_servers_own_words_reach_the_terminal(self, opener):
        # The API's `detail` says what to fix and in which order; this layer
        # relays it rather than replacing it with a status line.
        opener(body=b'{"detail": "deploy the matching API before pushing"}', error=409)
        with pytest.raises(SystemExit, match="deploy the matching API before pushing"):
            request_json("PUT", URL, "t", {"pfade": []})
