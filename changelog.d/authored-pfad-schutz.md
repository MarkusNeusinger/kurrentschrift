### Fixed

- **A hand-drawn Streifen-Pfad could be deleted by a follower run.** The write
  path is a FULL replacement, so once the author draws a pen path himself, a
  later `tools.eigenhand.pfad` run took it away in two ways — by answering the
  box with a followed path, and by simply leaving the box out. No hand-drawn
  path exists yet — the rule ships before the first one can be lost, because it
  cannot be retrofitted afterwards. Now a stored box
  whose `verfahren` is `authored` is ground truth: `PUT
  /eigenhand/strips/{hand}/{strip}/{fassung}/pfade` refuses the WHOLE push with
  409 before anything is committed. Whole and not per box, unlike the plate
  twin `PUT /word-instances`, because this answer has no `skipped` channel and
  a silent skip would leave the operator believing the run had been stored as
  followed. Authored over authored passes — that is the author correcting his
  own trace, and it is what keeps a drawing surface possible later.
- **`tools.eigenhand.pfad` merges around a hand-drawn path instead of
  provoking the refusal.** A whole-row re-follow would otherwise fail over the
  one word the author drew himself, so the run keeps that box's stored path and
  drops its own result for it, saying so on the way. `--replace-authored` (the
  query parameter `?replace_authored=true`) is the only way to hand a drawing
  over, and deliberately not a button in the workbench: no browser code sends
  that parameter, so giving up hand work stays an explicit act at the keyboard.
