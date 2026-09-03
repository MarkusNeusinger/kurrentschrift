### Changed

- **The Schreibtafel's narrow cells are a decided exception to the 44px touch
  rule, not an open question.** Fourteen of the sheet's 62 cells — i, l, ſ, t, z,
  the capitals I, J, O, Ö, P, S, T, Z and the digit 0 — stay under the floor in
  width, because a cell is as wide as its letter's ink plus half a gap
  (`cellW = glyphW + gap`), which is what makes the row read as a written line
  rather than a type case. The author decided to leave them (audit finding 21):
  the cells are not a primary target, the same letter is reachable at full size
  through the letter detail, and both remedies cost more than they buy — an
  invisible hit area would reach into the neighbouring letter and steal its tap,
  and widening reflows the very lookup grid the page exists for. §9.3 now records
  which cells, why they are narrow, why that is accepted, and the condition that
  ends the exception: the next time the sheet is re-laid out, the 44px width is
  part of that design rather than something to buy back afterwards (#514).
