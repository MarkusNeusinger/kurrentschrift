"""The Open-Graph card (`app/public/og.png`), composed from the engine's own writing.

Why a tool and not a hand-made image. The card is the first thing anyone sees of
this project — it is what a link preview shows in a chat, a feed or a search
result — and until 2026-08-30 it showed the brand word set in the GL-GermanCursive
SHOW FONT. That contradicted the page it advertises: the landing hero writes
"Kurrentſchrift" with the synthesis engine and falls back to that font only when
the backend fails (`app/src/sections/landing/HeroWritten.tsx`). The card now takes
the same route the hero takes — `GET /sources/{id}/write/word.svg` — so the
preview shows the product, not a specimen of somebody else's typeface. And because
a re-traced template changes that writing, the card has to be re-buildable on
command instead of living on as a binary nobody can regenerate.

What is site-true here, and where its source of truth lives:

* the word — `/write/word.svg` for `Kurrentſchrift` on `PUBLIC_SOURCE_ID`, the
  very call `<WrittenWord>` makes; lineature off, as the hero renders it;
* the viridian swash — the hero's `Flourish` path and geometry, verbatim;
* the corner mark — the header `Wordmark` (`app/src/components/HeaderBar`),
  minus its leading dot (owner, 2026-08-30: the swash and the ".ink" already
  carry the accent, a third viridian spot is one too many);
* the palette — `app/src/styles/paper.ts`.

Those four are MIRRORED here, not imported: this is Python and they are TypeScript.
The constants below name their counterpart so a drift is findable; the card is
rebuilt and eyeballed when either side moves, which is the same discipline the
`shaping.py`/`shaping.ts` twins live under, minus the fixture (a picture has no
byte-equality worth pinning).

The composed geometry is fetched at build time and never committed: the authored
ductus is the reserved dataset (`docs/reference/quellen-und-rechte.md` §5). What
lands in the repo is the 1200x630 raster of one word — the published share image
itself, deliberate product surface like the `/write` payloads it came from.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = REPO_ROOT / "app/public/fonts"
CARD_PATH = REPO_ROOT / "app/public/og.png"

# The public "as written" Vorlage — `app/src/lib/seo/prerender.ts::PUBLIC_SOURCE_ID`.
PUBLIC_SOURCE_ID = "suetterlin-1922"
PUBLIC_API = "https://api.kurrentschrift.ink"

# The brand word, long-ſ at the syllable start — `de.landing.hero.word`.
BRAND_WORD = "Kurrentſchrift"

# The lead is the landing page's own H1 (`de.landing.hero.title`): whoever clicks
# the preview lands on exactly this sentence. It is also the shortest line on
# offer, which is what decides a card that is mostly seen as a thumbnail.
LEAD_HTML = "Alte Briefe wieder lesen &mdash;<br>und selbst zur Feder greifen."
LEAD_SIZE_PX = 52

CARD_W, CARD_H = 1200, 630

# app/src/styles/paper.ts
PAPER_HI = "#f1e8d4"
PAPER_LO = "#dccdad"  # the card's own gradient end, a touch above paper.lo
INK = "#241a10"
SEPIA = "#5e4726"
VIRIDIAN = "#40826d"

# The ink the renderer fills the silhouettes with (`api/glyph_svg.py`) — needed
# only to recolour, which the card does not do any more.
ENGINE_INK = "#2b2419"

# HeroWritten.tsx::Flourish — the signature swash under the word, verbatim: the
# path, its 1000x60 viewBox stretched with preserveAspectRatio="none", and the
# placement (left -1%, width 102%, bottom -8%, height 14%) that was tuned so the
# swash grazes the deepest descenders (ſ, f) instead of striking through them.
FLOURISH_D = "M8 42 C220 8 520 10 742 30 C840 38 922 36 992 20"
FLOURISH_STROKE = 7

# Wide enough to carry the word at reading weight, narrow enough to leave the
# 160px side air that makes the centred stack look placed rather than stretched.
# Same number as the hero's own cap, HeroWritten.tsx::HERO_MAX_W.
WORD_W = 880

_FONTS = (
    ("EB Garamond", "eb-garamond-latin-400-normal.woff2", 400, "normal"),
    ("EB Garamond", "eb-garamond-latin-ext-400-normal.woff2", 400, "normal"),
    ("Playfair Display", "playfair-display-latin-600-normal.woff2", 600, "normal"),
    ("Playfair Display", "playfair-display-latin-600-italic.woff2", 600, "italic"),
)


def word_svg_url(api: str = PUBLIC_API, source_id: str = PUBLIC_SOURCE_ID, text: str = BRAND_WORD) -> str:
    """The public render call the hero makes, as a URL."""
    from urllib.parse import quote

    return f"{api.rstrip('/')}/sources/{source_id}/write/word.svg?text={quote(text)}"


def font_faces() -> str:
    """The card's four faces inlined as data URIs.

    The screenshot runs against a `file://` page with no network, and a card that
    silently fell back to a system serif would still render — just wrong, and
    only noticed after publishing. Embedding removes that failure mode.
    """
    faces = []
    for family, file, weight, style in _FONTS:
        b64 = base64.b64encode((FONT_DIR / file).read_bytes()).decode()
        faces.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:{style};"
            f"font-display:block;src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )
    return "".join(faces)


def prepare_word(svg: str) -> str:
    """The `/write/word.svg` response as the card embeds it.

    Three edits, all of them things the hero does too: the lineature comes off
    (`showLineature={false}`), the XML prolog and `<title>` go (the card carries
    its own alt text in the meta tags), and the fixed pixel size gives way to the
    viewBox so CSS can scale the word to the card.
    """
    svg = re.sub(r'<g class="guides">.*?</g>', "", svg, flags=re.S)
    svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<title>.*?</title>", "", svg, flags=re.S)
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)
    if "<path" not in svg:
        raise ValueError("the word SVG carries no paths — nothing was written")
    return svg.strip()


def build_html(word_svg: str) -> str:
    """The card as a self-contained `file://` page, ready to screenshot at 1200x630.

    Centred throughout, the way the live hero stacks (word, then copy, then the
    mark). The card was left-aligned while its lead ran two full lines; with the
    short H1 as the lead, a left stack leaves the whole lower right of the frame
    empty and the mark alone in it.
    """
    return f"""<!doctype html>
<meta charset="utf-8">
<title>og-card</title>
<style>
{font_faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{CARD_W}px;height:{CARD_H}px}}
body{{background:linear-gradient(135deg,{PAPER_HI} 0%,{PAPER_LO} 100%);
  font-family:'EB Garamond',Georgia,serif;color:{SEPIA};padding:0 96px;
  display:flex;flex-direction:column;align-items:center;text-align:center}}

/* the written word and its swash are one block: the flourish is positioned
   against the word's own box, exactly as in the hero */
.word{{position:relative;width:{WORD_W}px;margin-top:100px}}
.word > svg{{display:block;width:100%;height:auto;overflow:visible}}
.flourish{{position:absolute;left:-1%;width:102%;bottom:-8%;height:14%;overflow:visible}}
.flourish path{{fill:none;stroke:{VIRIDIAN};stroke-width:{FLOURISH_STROKE};stroke-linecap:round}}

.lead{{margin-top:76px;font-size:{LEAD_SIZE_PX}px;line-height:1.28;color:{SEPIA}}}

.wordmark{{margin-top:58px;font-family:'Playfair Display',Georgia,serif;font-weight:600;
  font-size:34px;letter-spacing:0.02em;color:{INK};white-space:nowrap}}
.wordmark .tld{{color:{VIRIDIAN};font-style:italic}}
</style>
<div class="word">{word_svg}
  <svg class="flourish" viewBox="0 0 1000 60" preserveAspectRatio="none" aria-hidden="true"><path d="{FLOURISH_D}"/></svg>
</div>
<p class="lead">{LEAD_HTML}</p>
<div class="wordmark">kurrentschrift<span class="tld">.ink</span></div>
"""
