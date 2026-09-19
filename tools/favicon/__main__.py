"""`python -m tools.favicon` — rebuild the site icons from the engine's written K.

    uv run python -m tools.favicon                       # fetch, fit, write app/public/
    uv run python -m tools.favicon --api http://localhost:8000
    uv run python -m tools.favicon --svg K.svg           # a glyph SVG you already have

Reads one PUBLIC endpoint (`/write/glyphs/K.svg`) — the only network call, and
the reason `--svg` exists for an offline run — and writes three files in the
working tree: `favicon.svg`, `favicon.ico` (16/32/48) and `apple-touch-icon.png`
(180). No database, no admin token, no browser: Pillow draws the rasters.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

from tools.favicon import PUBLIC_DIR, build_svg, fit, glyph_svg_url, ico_bytes, outline_strokes, touch_icon


def fetch_glyph_svg(url: str, timeout: int = 60) -> str:
    # Cloudflare's browser-integrity check answers urllib's default agent with
    # 1010 — the same reason `tools/ogcard` names itself.
    request = urllib.request.Request(url, headers={"User-Agent": "kurrentschrift-favicon/1.0 (tools/favicon)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{url}\n  → HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"{url}\n  → {e.reason}") from e


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m tools.favicon", description=__doc__)
    p.add_argument("--api", default=None, help="API base URL (default: the public API)")
    p.add_argument("--svg", type=Path, help="use this glyph SVG instead of calling the API")
    p.add_argument("--out", type=Path, default=PUBLIC_DIR, help=f"output directory (default: {PUBLIC_DIR})")
    args = p.parse_args(argv)

    if args.svg:
        raw, origin = args.svg.read_text(encoding="utf-8"), str(args.svg)
    else:
        origin = glyph_svg_url(args.api) if args.api else glyph_svg_url()
        raw = fetch_glyph_svg(origin)

    fitted = fit(outline_strokes(raw))

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "favicon.svg").write_text(build_svg(fitted), encoding="utf-8")
    (args.out / "favicon.ico").write_bytes(ico_bytes(fitted))
    touch_icon(fitted).save(args.out / "apple-touch-icon.png", optimize=True)

    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png"):
        print(f"{args.out / name}  {(args.out / name).stat().st_size} B")
    print(f"  ← {origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
