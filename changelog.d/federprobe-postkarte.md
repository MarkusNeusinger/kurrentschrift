### Added

- **The Federprobe takes a postcard, and a typed break is written as a
  break.** The field grows from 48 characters to 480 — eight written lines
  of sixty, the practice sheet's own line length — and becomes multiline:
  Enter starts a new line, and that line boundary survives into the writing.
  The planner splits on the typed breaks first and wraps each paragraph as
  before, so a hard break is always a break while an over-long typed line
  still wraps; one blank row renders as one paragraph gap (several collapse
  into it, leading and trailing ones are dropped). No newline ever reaches
  the API — the composer reads one as an ordinary space and would write the
  break as a gap mid-line — and the wrap planner keeps 60 characters as the
  hard cap per composition request. The counter under the field says
  `n/480`, newlines included, and the share link carries them as `%0A`. The
  one input no line plan can rescue — a run of 160+ characters without a
  space, which breaks at nothing and which the composer refuses — is
  reported and named instead of written or cut, the way the practice sheet
  reports a row its ruling is too narrow for.
- **A Schriftgröße switch instead of a zoom: klein · mittel · groß.** A step
  sets the x-height the text is WRITTEN at — 20 · 28 · 40 px per template
  unit — so the pen writes larger rather than a finished picture being
  magnified, and a larger step honestly wraps into more lines. The ladder is
  anchored on the ink floor of 14 px and rises in √2 steps above it, which
  puts `klein` exactly where a full desktop line already wrote (measured
  20.8 px per unit at 1440 px) and makes `mittel`, the default, visibly
  larger. Where the frame cannot carry a step, the longest word — which is
  never hyphenated — caps it, and the floor still holds: on a 360 px phone
  all three steps meet at ~14 px. The choice is remembered per reader and
  rides on the share link as `?size=`, the URL winning over the stored
  preference so a shared link reproduces the sender's view. Browser pinch
  zoom is untouched, which is why no zoom of our own was built.

### Changed

- **The compose rate limit counts characters, not requests.** One token of
  the narrow bucket buys one full-length composition (160 characters) and a
  shorter text costs proportionally less, down to an eighth. The configured
  numbers are unchanged — 60 per minute, burst 20 — but they no longer read
  as "60 requests", because what the 2026-09-01 audit measured scales with
  the text: the same line costs the same whether it arrives whole or in four
  pieces. Metering per request made that untrue in the one direction that
  matters, and the postcard showed it — a 480-character text wraps into up
  to ~57 written lines, each its own composition because each line is its
  own continuous pen stroke, and one page view spent more than the whole
  burst. It now spends 3 to 7 tokens of 20 — 3 at the small step, ~7 at the
  large one, whose short lines pay the eighth-token floor rather than their
  length. A full-length request still costs exactly one token, and the wide
  bucket still bounds the request count.
