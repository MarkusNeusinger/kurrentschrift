"""fitview — before/after comparison page for the stranded-anchor repair.

Re-runs the LIVE chain fit on exactly the occurrences the owner judged in the
humanbench rounds (default: every screen whose categories include ``A``, the
single-outlier verdict) and renders, per occurrence, a side-by-side of the
letter's anchor polyline over the specimen crop — "before" is the fit as-is,
"after" is the same fit with `tools.pairlab.anchors.repair_stranded_anchors`
applied to the letter's anchors. One self-contained HTML file, PNG panels
embedded as data URIs.

    uv run python -m tools.fitview [--round all] [--category A] [--out temp/fitview] [--limit N]

Measurement/diagnostics only: no DB, no API, no writes to `core/`, nothing that
renders for production. The panel frame (pad, zoom) mirrors the humanbench
round builds so the view matches what the owner judged.
"""
