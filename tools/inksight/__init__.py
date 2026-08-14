"""InkSight (route B of the Tintenfolger duel) — measurement-only pipeline.

Three stages, split so no dependency crosses: `prepare.py` and `to_candidate.py`
run in the REPO environment, `run_inksight.py` runs in the isolated
TensorFlow venv (`tools/inksight/.venv`). Only `tokens.py` and the affine
helpers of `prepare.py` are shared, and neither imports TensorFlow.

Nothing here writes to the DB or feeds rendering: derendered geometry is
measurement material for `tools/tracebench`, never a ductus source.
"""
