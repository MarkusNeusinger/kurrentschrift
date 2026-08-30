"""Fetch the igerman98/frami dictionary (de_DE_frami .dic/.aff + README) here.

The bytes stay gitignored (`/data/corpora/**`; GPL server data — see
SOURCE.md); only this script and SOURCE.md are committed. Downloads go over
plain HTTPS (urllib, house style: no requests dependency) from a PINNED commit
of the LibreOffice dictionaries repo and are verified against the SHA256 pins
below — a changed upstream file fails loudly instead of silently shifting the
vocabulary.

    uv run python data/corpora/igerman98/fetch_igerman98.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
COMMIT = "32b006a2c22a4ac7e8ed3f03346f7b3d85a970a4"
BASE = f"https://raw.githubusercontent.com/LibreOffice/dictionaries/{COMMIT}/de"

# (filename, url, sha256) — pins recorded in SOURCE.md; update both together.
FILES: tuple[tuple[str, str, str], ...] = (
    ("de_DE_frami.dic", f"{BASE}/de_DE_frami.dic", "4ca3c958b0e5545910999bc246f668840bf8ede3df8e5e6790d05edd5a586c38"),
    ("de_DE_frami.aff", f"{BASE}/de_DE_frami.aff", "646bf3333ac69c23e9d794533ee5241d6f755c359e8fe10a648f87613743d594"),
    (
        "README_de_DE_frami.txt",
        f"{BASE}/README_de_DE_frami.txt",
        "c141f4f79c428b7348b5012836f4ad3db4d124f288f15effc22696dc876512ae",
    ),
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
            "fetch_igerman98.py AND SOURCE.md if the change is intended"
        )
    target.write_bytes(data)
    print(f"{name}: {len(data):,} bytes, checksum ok")


def main() -> int:
    for name, url, sha256 in FILES:
        fetch_one(name, url, sha256)
    return 0


if __name__ == "__main__":
    sys.exit(main())
