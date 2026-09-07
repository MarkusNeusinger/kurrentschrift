### Changed

- **The running-form harvest now seeds from the chart, so it is a fixed
  point.** `tools.laufform.harvest` defaults to `--chain-seed chart`: the
  chain solve starts on a composition built WITHOUT the running-form rows, so
  the harvest no longer reads the rows it is about to replace. Under the old
  default that feedback did not settle — three iterations moved the worst row
  0.0582 → 0.0627 → 0.0627 xh and carried the accepted occurrence set
  235 → 232 → 239 with them, which made every re-harvest card blurred by the
  order of magnitude the arms measure in. Seeded from the chart the second
  pass reproduces the first map byte for byte, occurrences included. Author's
  decision A38 of 2026-09-07; the measured cost side is in
  `messjournal.md` §14 „Laufform LF16". `--chain-seed composed` stays
  reachable and reproduces every round before `sep06`, and the trace bench and
  the follower keep their own `composed` default — their `chain` candidate is
  the frozen base every measured arm is graded against, and a base that slides
  under the route makes every stored delta unreadable.
