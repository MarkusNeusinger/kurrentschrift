---
name: work-basket
description: Work off the Werkbank's Auftragskorb (the work_items basket) — read the open tasks, reproduce each complaint, restate it back into the row, triage it along the stage doctrine, fix the RULE rather than one spot, measure the effect and close the item with the diagnosed stage. Use when asked to work off the Korb, handle work items, process filed optimization tasks, or start an optimization round.
---

# Work off the Auftragskorb

The admin marks a bad letter, join or word in `/admin/werkbank` and files
it as a `work_items` row instead of sending a screenshot. This skill is
the other half: how a session picks those up and gives back something
that is still worth reading in a year.

**Read first, every time:** `docs/proposals/optimierungs-werkbank.md`
§3–§5. §3 says who is allowed to supply what, §4 sorts symptoms to
stages, §5 is the protocol below. The doctrine there wins over anything
summarized here.

The one rule everything else serves: **a complaint is a chance to fix a
RULE.** A manual patch repairs one spot; a rule repairs every word that
will ever use it. Overrides are the deliberate last resort, and closing
an item without saying which stage you diagnosed throws away the only
lasting product of the round.

## 0 · Getting at the basket

The queue is source-free — you do NOT need to know a `source_id` to read
your tasks:

```bash
curl -fsS -H "X-Admin-Token: $ADMIN_TOKEN" \
  "https://api.kurrentschrift.ink/work-items?status=open"
```

- **Host matters.** Only `api.kurrentschrift.ink` works. The apex
  `kurrentschrift.ink/api/*` sits behind Cloudflare Access and 302s
  before the header is ever seen (CLAUDE.md, `admin-token-two-values`).
- **Token.** `printenv ADMIN_TOKEN >/dev/null && echo set` — never print
  the value. Locally it comes from `.env`; in a cloud session it is an
  environment variable and the deployed API is the only admin path.
- **Reading the 404s.** `{"detail":"Not Found"}` (capital N) is FastAPI
  on an unknown PATH — wrong route or wrong host. `{"detail":"source 'x'
  not found"}` is a wrong `source_id`. They are different problems.
- Sources, when you do need one: `GET /sources`. The public site and the
  admin default is `suetterlin-1922` (`app/src/global-config.ts`).

Each row carries its own `source_id`, `kind`, target keys, the specimen
it was seen in and the admin's `note`. Work them oldest first.

## 1 · Reproduce before you believe

Never restate a complaint you have not looked at. Depending on the level:

- **word** — `GET /sources/{src}/word-samples/{specimen_id}/score`
  (admin-gated, uncached): the frozen wordbench ruler on the same
  composition `/write/word` serves, with per-letter/per-join attribution.
  `python -m tools.wordlab <id> [--set pairs] [--live]` draws it over the
  specimen with penalty callouts.
- **pair** — `python -m tools.pairlab <left> [<right>,…]` dissects the
  join against its real occurrences and separates connector shape from
  placement error.
- **letter** — the Werkbank letter lens (chart form vs. every stored
  occurrence, worst residual first); `python -m tools.glyphlab <key>
  --live --stages` for the derivation.

Write down what you actually measured. `reproduced` is `yes`, `partly`
or `no` — and `no` is a legitimate outcome, not a failure to try.

## 2 · Restate it into the row (before changing anything)

```bash
curl -fsS -X PATCH -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"ack","reproduced":"yes","understanding":"Das n in „wenn\" wirkt zu flach, nicht der Übergang davor. Nachgeprüft an wenn-19-2: Score 0.19, davon 0.11 auf dem zweiten n-Bogen. Verdacht zuerst auf der Laufform — solo stimmt das n."}' \
  "https://api.kurrentschrift.ink/work-items/<id>"
```

Three sentences, in your own words: what you take the complaint to be ·
what you saw when you checked · which stage you suspect first. Do NOT
open with „Verstanden als:" — the Korb already labels the field, and the
prefix would render twice. This is
not paperwork — the admin reads it in the Korb and can reject it with one
click if you understood the wrong thing, which is far cheaper than a
wasted round. **Do not wait for that.** Ack and keep working.

## 3 · Triage in this order (§3/§5)

1. **Tafel-Duktus** wrong (the letter is wrong on its own)? → the
   author's own ground truth. Do NOT redraw it: hand the item back
   (`status: "returned"`, §6 below).
2. **Laufform / Fit** — the letter is right on the chart but wrong in
   words. Aggregates, `apply-laufform`, the fit.
3. **Klassenregel** — a whole join TYPE misbehaves. Fix the grammar in
   `core/compose.py`; one rule lifts many pairs.
4. **Komposition** — placement, spacing, rhythm, baseline.
5. **Paar-Override** — only when the plate shows a genuinely
   idiosyncratic form that no rule should generalize. An override
   without a documented rule check is a doctrine violation.

## 4 · Measure the effect

The bench is the guard, and it is FROZEN during the loop — edit the
composer, never the ruler:

```bash
uv run python -m tools.wordbench.run --style suetterlin --set all
```

Compare against the baseline in `docs/reference/qualitaetsmetrik.md` §6.
A change that does not move the number needs a visual argument
(wordlab/pairlab before-after) or it does not ship.

## 5 · Close it

```bash
curl -fsS -X PATCH -H "X-Admin-Token: $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"done","stage":"laufform","resolution":"Stufe, Änderung, PR #NNN, Wörter 0.1240→0.1214"}' \
  "https://api.kurrentschrift.ink/work-items/<id>"
```

`stage` is one of `chart_ductus` · `laufform` · `join_rule` ·
`composition` · `pair_override` · `word_trace` · `not_reproducible`.
The API returns **422 naming the missing field** if the protocol is
incomplete — that is the reminder, not an obstacle to route around.

Two things it will refuse, both on purpose: acking and closing in ONE
call (the restatement is only worth writing if it stood there while it
could still be corrected), and writing a protocol field on a PATCH
without a `status` (it would slip past the ack gate). Step 2 and step 5
are two calls, always.

`resolution` names the stage, the change, the PR and the measurement.
The PR description names `Korb #<id>` in return, so the archive is
findable from both ends.

## 6 · Handing an item back

If the triage lands on a ground-truth gap — the chart ductus is wrong,
or the auto-fit cannot work without a manual trace — the item is not
yours to close:

```bash
-d '{"status":"returned","stage":"chart_ductus","resolution":"Rückgabe an Autor: n im Wizard neu nachfahren — der zweite Abstrich setzt zu früh an."}'
```

Name the concrete manual step (which glyph in the wizard, which word to
re-trace). The row stays visible at the top of the Korb.

## Gotchas

- **Never author ground truth for the admin.** Chart ductus and word
  re-traces are the human's contribution (§3). Guessing one and calling
  it fixed corrupts the very data the statistics learn from.
- **Manual contributions never enter the frozen metric references.** The
  measuring stick stays the plate (`qualitaetsmetrik.md`).
- **One source per round.** Statistics are per hand; do not mix sources
  in one diagnosis.
- **A wrong complaint is still a finding.** `reproduced: "no"` plus
  `stage: "not_reproducible"` and a resolution explaining what you did
  see is a complete, honest closure.
- The admin may reject a restatement while you work: the row goes back
  to `open` with a `Korrektur:` in the note. Re-read the row before you
  close it.
