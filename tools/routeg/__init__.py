"""Route G of the Tintenfolger duel — the prior-free geometric CONTROL.

Recovers a writing order from the ink alone: skeleton → segment graph →
traversal, with no ductus prior, no template and no learning anywhere. Its role
is not "competitor" but control — the difference between it and the chain fit on
the same ten words is the first measured number for what the ductus prior
actually buys (`docs/proposals/tintenfolger.md` §4b, `architektur.md` §2).

Three stages, so nothing foreign has to cross into the repo environment:
`prepare.py` (fixture entries → binary ink images), stage 2 (the recovery
itself), `to_candidate.py` (crop pixels → the stored `word_instances` frame).

Nothing here writes to the DB or feeds rendering: recovered geometry is
measurement material for `tools/tracebench`, never a ductus source.
"""
