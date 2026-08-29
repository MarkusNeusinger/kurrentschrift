"""The Lesart endpoints: the generation-switched load behind the admin gate,
the public read that answers a bucket of real words, never the list."""

from __future__ import annotations

from tests.api_harness import Harness


WORDS = [["Mühme", False], ["Nuhme", False], ["Mühle", True], ["Muhme", False], ["lesen", False], ["lefen", False]]
BUILD = {"source": "test build", "sha256": "a" * 64}


async def _load(api: Harness, words=WORDS, build=BUILD) -> int:
    opened = await api.client.request(
        "POST", "/lesarten/dictionary/generations", json_body=build, headers=api.admin_headers()
    )
    assert opened.status == 201, opened.body
    gen = opened.json()["generation"]
    added = await api.client.request(
        "POST", f"/lesarten/dictionary/generations/{gen}/forms", json_body={"words": words}, headers=api.admin_headers()
    )
    assert added.status == 200, added.body
    committed = await api.client.request(
        "POST", f"/lesarten/dictionary/generations/{gen}/commit", json_body=build, headers=api.admin_headers()
    )
    assert committed.status == 200, committed.body
    return gen


async def test_empty_until_loaded(api: Harness):
    res = await api.client.request("GET", "/lesarten", params={"text": "Muhme"})
    assert res.status == 200
    assert res.json() == {"text": "Muhme", "readings": [], "dictionary": None}
    assert res.headers["cache-control"].startswith("public")


async def test_load_then_read_real_words_only(api: Harness):
    await _load(api)
    res = await api.client.request("GET", "/lesarten", params={"text": "Muhme"})
    body = res.json()
    words = [r["word"] for r in body["readings"]]
    assert words == ["Mühme", "Nuhme"]  # the guess itself is not a reading; Mühle differs by two classes
    assert body["readings"][0]["swaps"] == [{"index": 1, "from": "u", "to": "ü"}]
    assert body["dictionary"]["forms"] == 6 and body["dictionary"]["source"] == "test build"
    # The long ſ trap: a typed s is read as f and back.
    res = await api.client.request("GET", "/lesarten", params={"text": "lesen"})
    assert [r["word"] for r in res.json()["readings"]] == ["lefen"]


async def test_same_build_is_refused_and_a_new_build_replaces_the_old(api: Harness):
    gen = await _load(api)
    again = await api.client.request(
        "POST", "/lesarten/dictionary/generations", json_body=BUILD, headers=api.admin_headers()
    )
    assert again.status == 409
    new_build = {"source": "second build", "sha256": "b" * 64}
    gen2 = await _load(api, words=[["Mühle", True]], build=new_build)
    assert gen2 > gen
    res = await api.client.request("GET", "/lesarten", params={"text": "Muhme"})
    assert res.json()["readings"] == []  # the old generation is gone
    meta = await api.client.request("GET", "/lesarten/dictionary")
    assert meta.json()["forms"] == 1 and meta.json()["source"] == "second build"


async def test_load_is_admin_gated_and_validates(api: Harness):
    res = await api.client.request("POST", "/lesarten/dictionary/generations", json_body=BUILD)
    assert res.status == 401
    gen = await _load(api)
    bad = await api.client.request(
        "POST",
        f"/lesarten/dictionary/generations/{gen + 1}/forms",
        json_body={"words": [["zwei Wörter", False]]},
        headers=api.admin_headers(),
    )
    assert bad.status == 400
    live = await api.client.request("DELETE", f"/lesarten/dictionary/generations/{gen}", headers=api.admin_headers())
    assert live.status == 409  # the live generation cannot be dropped
    stale = await api.client.request(
        "POST",
        f"/lesarten/dictionary/generations/{gen}/forms",
        json_body={"words": [["neu", False]]},
        headers=api.admin_headers(),
    )
    assert stale.status == 409  # nor appended to


async def test_text_is_bounded(api: Harness):
    res = await api.client.request("GET", "/lesarten", params={"text": "x" * 33})
    assert res.status == 422
    blank = await api.client.request("GET", "/lesarten", params={"text": "   "})
    assert blank.status == 422


async def test_an_abandoned_load_is_dropped_by_the_next_begin(api: Harness):
    gen = await _load(api)
    opened = await api.client.request(
        "POST",
        "/lesarten/dictionary/generations",
        json_body={"source": "x", "sha256": "c" * 64},
        headers=api.admin_headers(),
    )
    abandoned = opened.json()["generation"]
    await api.client.request(
        "POST",
        f"/lesarten/dictionary/generations/{abandoned}/forms",
        json_body={"words": [["Nuhme", False], ["Mühme", False]]},
        headers=api.admin_headers(),
    )
    # No commit — the next begin must sweep the abandoned rows and reuse the number.
    again = await api.client.request(
        "POST",
        "/lesarten/dictionary/generations",
        json_body={"source": "y", "sha256": "d" * 64},
        headers=api.admin_headers(),
    )
    assert again.json()["generation"] == gen + 1 == abandoned
    stale = await api.client.request(
        "POST",
        f"/lesarten/dictionary/generations/{abandoned}/commit",
        json_body={"source": "y", "sha256": "d" * 64},
        headers=api.admin_headers(),
    )
    assert stale.status == 409  # swept: nothing to commit
    live = await api.client.request("GET", "/lesarten", params={"text": "Muhme"})
    assert [r["word"] for r in live.json()["readings"]] == ["Mühme", "Nuhme"]  # the live generation is untouched
