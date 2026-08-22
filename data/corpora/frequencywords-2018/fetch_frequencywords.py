"""Fetch the FrequencyWords 2018 lists (de/en 50k) into this directory.

The list bytes stay gitignored (`/data/corpora/**`, consult-only source —
see SOURCE.md); only this script and SOURCE.md are committed. Downloads go
over plain HTTPS (urllib, house style: no requests dependency) and are
verified against the SHA256 pins below — a changed upstream file fails
loudly instead of silently shifting the Übergangsraum weights.

    uv run python data/corpora/frequencywords-2018/fetch_frequencywords.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018"

# (filename, url, sha256) — pins recorded in SOURCE.md; update both together.
FILES: tuple[tuple[str, str, str], ...] = (
    ("de_50k.txt", f"{BASE}/de/de_50k.txt", "d9e50546fd7e8b6fe6542a2b33c51d1331092b2a3916ec09f80d97856068705b"),
    ("en_50k.txt", f"{BASE}/en/en_50k.txt", "5351ff405b1126ef555791dd4d9798a48e3e9a501a9fc481a9da957752cfb458"),
)


def fetch_one(name: str, url: str, sha256: str) -> None:
    target = HERE / name
    if target.exists():
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest == sha256:
            print(f"{name}: already present, checksum ok")
            return
        raise SystemExit(f"{name}: exists but checksum differs from the pin — refusing to overwrite; delete it first")
    print(f"fetching {url}")
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 — pinned https URL
        data = resp.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != sha256:
        raise SystemExit(
            f"{name}: checksum mismatch (got {digest}) — upstream changed; re-pin in "
            "fetch_frequencywords.py AND SOURCE.md if the change is intended"
        )
    target.write_bytes(data)
    print(f"{name}: {len(data):,} bytes, checksum ok")


def main() -> int:
    for name, url, sha256 in FILES:
        fetch_one(name, url, sha256)
    return 0


if __name__ == "__main__":
    sys.exit(main())
