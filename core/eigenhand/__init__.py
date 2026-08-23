"""Eigenhand compute — the pure half of the own-hand capture chain.

The capture chain has two halves. The PHYSICAL half stays local under
``tools/eigenhand``: scans, crops, the Siebung page, the gitignored data root.
The half in here is pure compute over committed inputs — the frozen strip plan,
the page geometry, the PDF writer, the coverage bookkeeping and the Bestand —
and it lives in ``core`` because the API serves it: which strips a hand already
holds (and how often) is DB state, so the Bestand and the Bogen printer must
run on the server too, not only in the author's terminal (owner, 2026-08-23).

Nothing here reads the reserved dataset. The modules take a plan and a
Kartei-shaped dict and hand back numbers, mm and PDF bytes; where that dict
comes from — ``kartei.json`` locally, the ``eigenhand_*`` tables on the server
— is the caller's business. One compute path, two persistences.
"""
