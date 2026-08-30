"""Unit tests for the Open-Graph card builder.

The card is composed once and then only ever LOOKED at, so the parts that are
easy to break silently get pinned here: the surgery on the `/write/word.svg`
response, and the page's self-containment (no network reference may survive into
a `file://` screenshot — a card that quietly fell back to a system serif still
renders, just wrong, and nobody sees it before it is published).

Nothing here calls the API or a browser; both belong to `__main__`.
"""

from __future__ import annotations

import pytest

from tools import ogcard
from tools.ogcard.__main__ import newest_by_revision


WORD_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.79 -2.224 18.805 3.439" width="875" height="160"'
    ' role="img" aria-label="Kurrentſchrift"><title>Kurrentſchrift — Sütterlin</title>'
    '<g class="guides"><line x1="-1.79" x2="17.015" y1="1" y2="1" stroke="#c9bda3"/></g>'
    '<g class="ink"><path d="M0 0 L1 1" fill="#2b2419" fill-rule="evenodd"/>'
    '<path d="M1 1 L2 0" fill="none" stroke="#2b2419" stroke-width="0.145"/></g></svg>'
)


def test_prepare_word_drops_the_lineature_prolog_and_fixed_size():
    out = ogcard.prepare_word(WORD_SVG)

    # the hero renders the word with showLineature={false}
    assert 'class="guides"' not in out
    assert "<line" not in out
    # the card carries its own alt text in the meta tags
    assert "<?xml" not in out
    assert "<title>" not in out
    # the viewBox scales the word to the card; a fixed px size would not
    assert 'width="875"' not in out and 'height="160"' not in out
    assert 'viewBox="-1.79 -2.224 18.805 3.439"' in out
    # the writing itself survives untouched, ink colour included
    assert out.count("<path") == 2
    assert ogcard.ENGINE_INK in out


def test_prepare_word_rejects_a_wordless_svg():
    """A 404 body or an empty composition must stop the build, not become a blank card."""
    with pytest.raises(ValueError, match="no paths"):
        ogcard.prepare_word('<svg xmlns="http://www.w3.org/2000/svg"></svg>')


def test_build_html_is_self_contained_and_card_sized():
    html = ogcard.build_html(ogcard.prepare_word(WORD_SVG))

    assert f"width:{ogcard.CARD_W}px;height:{ogcard.CARD_H}px" in html
    # every face inlined — no http(s) reference of any kind may remain
    assert html.count("@font-face") == 4
    assert "src:url(data:font/woff2;base64," in html
    # the SVG namespace is an identifier, not a fetch — everything else that
    # looks like a URL would be one, and would be missing in the screenshot
    fetchable = html.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http://" not in fetchable and "https://" not in fetchable


def test_build_html_quotes_the_site_identity():
    html = ogcard.build_html(ogcard.prepare_word(WORD_SVG))

    # the hero's swash, verbatim
    assert ogcard.FLOURISH_D in html
    assert f"stroke:{ogcard.VIRIDIAN}" in html
    # the header wordmark, minus its dot (the swash and the ".ink" carry the accent)
    assert '<div class="wordmark">kurrentschrift<span class="tld">.ink</span></div>' in html
    assert "border-radius:50%" not in html
    # the landing page's own H1 as the lead
    assert ogcard.LEAD_HTML in html


def test_newest_by_revision_counts_rather_than_spells():
    """Playwright's revisions passed 1000, where a text sort picks the stale browser."""
    paths = [
        "/opt/pw-browsers/chromium_headless_shell-999/chrome-linux/headless_shell",
        "/opt/pw-browsers/chromium_headless_shell-1148/chrome-linux/headless_shell",
        "/opt/pw-browsers/chromium_headless_shell-1187/chrome-linux/headless_shell",
    ]

    assert newest_by_revision(paths) == paths[2]
    assert newest_by_revision(list(reversed(paths))) == paths[2]
    # an unusual layout stays usable, it just never outranks a numbered one
    assert newest_by_revision(["/custom/headless_shell"]) == "/custom/headless_shell"
    assert newest_by_revision(["/custom/headless_shell", paths[0]]) == paths[0]
    assert newest_by_revision([]) is None


def test_word_svg_url_is_the_public_render_route():
    url = ogcard.word_svg_url()

    assert url.startswith(f"{ogcard.PUBLIC_API}/sources/{ogcard.PUBLIC_SOURCE_ID}/write/word.svg?text=")
    # the long ſ has to survive as UTF-8 percent-encoding, or the word shapes wrong
    assert url.endswith("Kurrent%C5%BFchrift")
