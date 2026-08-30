"""`python -m tools.ogcard` — rebuild the Open-Graph card from the engine's writing.

    uv run python -m tools.ogcard                       # fetch, render, write app/public/og.png
    uv run python -m tools.ogcard --api http://localhost:8000
    uv run python -m tools.ogcard --svg word.svg        # a word SVG you already have
    uv run python -m tools.ogcard --html-only page.html # the composed page, no browser

Reads one PUBLIC endpoint (`/write/word.svg`) and writes one file in the working
tree. No database, no admin token, no remote.

The renderer is a headless Chromium — the one Playwright already installs for
`/verify-frontend`; nothing is downloaded here. Point `OGCARD_CHROME` at a binary
to override the search. Prefer the `headless_shell` build: `chrome` in its new
headless mode sizes the WINDOW, not the viewport, and leaves a white band below
the page. The rendered card is checked for exactly that before it is written.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from glob import glob
from pathlib import Path

from tools.ogcard import CARD_H, CARD_PATH, CARD_W, build_html, prepare_word, word_svg_url


# Playwright's install roots, cloud first (`/verify-frontend` §"in the cloud").
# `headless_shell` leads in each: it is the build whose --window-size IS the
# viewport, which is what a fixed-size card needs.
CHROME_GLOBS = (
    "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell",
    "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell",
    "~/.cache/ms-playwright/chromium-*/chrome-linux/chrome",
)


def find_chrome() -> Path:
    if override := (os.environ.get("OGCARD_CHROME") or os.environ.get("CHROME_BIN")):
        path = Path(override).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"OGCARD_CHROME points at nothing: {path}")
        return path
    for pattern in CHROME_GLOBS:
        # newest revision first, so a stale install does not win
        if found := sorted(glob(os.path.expanduser(pattern)), reverse=True):
            return Path(found[0])
    raise FileNotFoundError(
        "no headless Chromium found. Install one with Playwright (see /verify-frontend) "
        "or set OGCARD_CHROME=/path/to/headless_shell"
    )


def fetch_word_svg(url: str, timeout: int = 60) -> str:
    # Cloudflare's browser-integrity check answers urllib's default agent with
    # 1010; a named agent is also simply the polite thing at our own edge.
    request = urllib.request.Request(url, headers={"User-Agent": "kurrentschrift-ogcard/1.0 (tools/ogcard)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        # 404 is the renderer's honest answer when nothing of the word is traced
        # yet — worth saying plainly, since it means the card cannot be built.
        raise SystemExit(f"{url}\n  → HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"{url}\n  → {e.reason}") from e


def shoot(chrome: Path, html: str, out: Path) -> None:
    """Screenshot the composed page at exactly the card size."""
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(html, encoding="utf-8")
        out.parent.mkdir(parents=True, exist_ok=True)
        done = subprocess.run(
            [
                str(chrome),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={CARD_W},{CARD_H}",
                f"--screenshot={out}",
                page.as_uri(),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if done.returncode != 0 or not out.exists():
        raise SystemExit(f"{chrome} failed ({done.returncode}):\n{done.stderr[-2000:]}")


def verify(out: Path) -> None:
    """The card is the right size and the paper reaches all four corners.

    Both failures are silent otherwise: a browser that sizes the window instead
    of the viewport writes a correctly-sized PNG with a white band along the
    bottom, and it looks fine in a file listing.
    """
    from PIL import Image

    with Image.open(out) as im:
        card = im.convert("RGB")
        if card.size != (CARD_W, CARD_H):
            raise SystemExit(f"{out}: {card.size[0]}x{card.size[1]}, expected {CARD_W}x{CARD_H}")
        corners = [(0, 0), (CARD_W - 1, 0), (0, CARD_H - 1), (CARD_W - 1, CARD_H - 1)]
        white = [c for c in corners if min(card.getpixel(c)) > 250]
        if white:
            raise SystemExit(
                f"{out}: the paper does not reach {len(white)} corner(s) — this browser sizes the window, "
                "not the viewport. Use a `headless_shell` build (OGCARD_CHROME=…)."
            )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m tools.ogcard", description=__doc__)
    p.add_argument("--api", default=None, help="API base URL (default: the public API)")
    p.add_argument("--svg", type=Path, help="use this word SVG instead of calling the API")
    p.add_argument("--out", type=Path, default=CARD_PATH, help=f"output PNG (default: {CARD_PATH})")
    p.add_argument("--html-only", type=Path, metavar="FILE", help="write the composed page and stop")
    args = p.parse_args(argv)

    if args.svg:
        raw, origin = args.svg.read_text(encoding="utf-8"), str(args.svg)
    else:
        origin = word_svg_url(args.api) if args.api else word_svg_url()
        raw = fetch_word_svg(origin)

    html = build_html(prepare_word(raw))

    if args.html_only:
        args.html_only.write_text(html, encoding="utf-8")
        print(f"{args.html_only}  ← {origin}")
        return 0

    chrome = find_chrome()
    shoot(chrome, html, args.out)
    verify(args.out)
    print(f"{args.out}  {args.out.stat().st_size // 1024} KiB  ← {origin}\n  rendered by {chrome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
