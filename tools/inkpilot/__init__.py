"""The ink pilot — ride the skeleton mid-ink, ask the ductus like a map.

Display name in German docs and on the duel page: "Lotse" (owner idea
2026-08-16, proposals/tintenfolger.md §7.8). The route inverts the chain
fit's economy: geometry comes ENTIRELY from the measured skeleton (the
prior-free control proved that path lies mid-ink better than anything
else, AIoU 0.833), while ORDER, branch choice at junctions, retraces and
mark assignment come ENTIRELY from the ductus prior — the composed word
acts as the map the pilot consults wherever the waterway forks. No #278
breach: there is no free tracer here, the prior decides the route.

Measurement layer only: no DB, no API, no `core/` change, no rendering.
Candidates go to `tools/tracebench` in the same file-provider frame the
other routes use.
"""
