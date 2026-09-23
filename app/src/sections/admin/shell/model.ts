// Shared vocabulary of the admin workbench: what can be marked as an Auftrag or
// put under a lens, how an occurrence box lands inside a specimen crop, and the
// colours the overlays draw with. Kept out of the component files so
// react-refresh only ever sees components there.
//
// This used to live under sections/admin/werkbank — it moved up into the shell
// when the three views (Buchstaben · Übergänge · Wörter) all became places
// where an element is inspected and complained about.

import type {
  InstanceOut,
  LandmarkKind,
  PenaltyCategoryKey,
  SpecimenKind,
  WordInstanceOut,
  WordSampleOut,
  WorkItemIn,
} from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { layer, liftConnector, paper, pigment, strokeStyle } from '@/styles/paper';

import { keysOfText } from './focus';

// One DETECTED structure of a letter, as the Landmarken-Linse hands it to the
// Korb (optimierungs-werkbank.md §8). `spot` is the fifth case and the only
// one without an index: a place where the author expects a marker and none
// stands, which is the complaint the layer most needs to be able to receive.
//
// The position is OPTIONAL, and that is the honest shape rather than a
// convenience: an unmatched catalogue Kringel has no detected location by
// definition, and a missing marker reported from the keyboard has none either.
// Required coordinates forced those callers to invent `(0, 0)`, which the note
// then filed as if the origin had been measured.
export interface LandmarkRef {
  kind: LandmarkKind | 'spot';
  index: number | null;
  x?: number;
  y?: number;
  numbers: Record<string, number | string | boolean | null>;
}

// One located deduction of the Abzugs-Linse (optimierungs-werkbank.md §9), as
// the lens hands it to the Korb: WHICH site of WHICH category, its part of the
// category's number and the raw numbers behind it. Always the chart row
// (variant 0) — the lens measures nothing else. `x`/`y` are crop pixels and
// null for the part without a place.
export type PenaltyRef = {
  category: PenaltyCategoryKey;
  index: number;
  kind: string;
  value: number;
  categoryValue: number;
  exact: boolean;
  pointsEst: number;
  x: number | null;
  y: number | null;
  numbers: Record<string, number | string | boolean | null>;
};

// The levels the doctrine knows (optimierungs-werkbank.md §5): a letter, a
// join, or the whole word — plus `landmark`, the generated structure layer of
// ONE letter (§8), and `penalty`, one deduction of the Abzugs-Linse (§9).
// `word` is the only one without a glyph key.
//
// `penalty` is a target, not a Korb kind: it files as a plain `letter` item
// (author decision 2026-09-23), because a complaint about where the ruler
// subtracts lands on the authored ductus or its derivation — a quarrel with
// the ruler itself is a proposal plus a re-baseline, never a Korb fix. It is
// its own variant here only so the filing dialog can skip the letter pre-sort
// question (the lens already shows the letter on its own, so the answer would
// always be „yes" and route every flag to the wizard) and preview the head.
export type WerkbankTarget =
  | { kind: 'letter'; glyphKey: string }
  | { kind: 'pair'; leftKey: string; rightKey: string }
  | { kind: 'word'; word: string }
  | { kind: 'landmark'; glyphKey: string; variant: number; landmark: LandmarkRef }
  | { kind: 'penalty'; glyphKey: string; penalty: PenaltyRef };

// Where the element was SEEN — the namespace and the id, exactly the pair the
// work-item API demands together (an id without its kind may point at nothing).
// Two of the three namespaces are plates; `strip` is a written word box of the
// own hand (`S0041/F02#2`, V7), which is why the type is the wire's own
// `SpecimenKind` rather than a second list beside it.
export interface SpecimenRef {
  id: string;
  kind: SpecimenKind;
  word: string;
}

export interface Mark {
  target: WerkbankTarget;
  // Absent when the complaint is about a FREELY TYPED combination or word that
  // has no specimen at all: the admin must be able to type any letter pair or
  // word, see how the engine writes it and file that it looks wrong, even where
  // the plates never wrote it. The API takes the reference as optional — it
  // only insists that id and kind travel together.
  specimen?: SpecimenRef;
}

// A lens selection is a mark whose target has a lens — the word, landmark and
// penalty levels have none (all three are filed, not inspected: a word
// complaint is about the whole picture, a landmark or a deduction is already
// being looked at when it is marked).
export type Selection = Mark & {
  target: Exclude<WerkbankTarget, { kind: 'word' } | { kind: 'landmark' } | { kind: 'penalty' }>;
};

export const pairKeyOf = (leftKey: string, rightKey: string): string => `${leftKey}→${rightKey}`;

// "Buchstabe a" / "Übergang d→a" / "Wort einen" / "Landmarke Kringel #1 · d" /
// "Buchstabe a · Abzug Ecken #1" — the level plus its target, as the filing
// dialog shows it back to the admin. A deduction says „Buchstabe" first
// because that is the kind it files as.
export function targetLabel(target: WerkbankTarget): string {
  const t = de.admin.werkbank;
  if (target.kind === 'letter') return `${t.kindLetter} ${target.glyphKey}`;
  if (target.kind === 'pair') return `${t.kindPair} ${pairKeyOf(target.leftKey, target.rightKey)}`;
  if (target.kind === 'landmark') {
    return `${t.kindLandmark} ${landmarkLabel(target.landmark)} · ${target.glyphKey}`;
  }
  if (target.kind === 'penalty') {
    return `${t.kindLetter} ${target.glyphKey} · ${t.penaltyHead} ${penaltyLabel(target.penalty)}`;
  }
  return `${t.kindWord} ${target.word}`;
}

// "Ecken #1" — a deduction site as the lens names it: the category's German
// label and the site's index, which is the handle the payload uses.
export const penaltyLabel = (ref: Pick<PenaltyRef, 'category' | 'index'>): string =>
  `${de.wizard.optimize.cat[ref.category]} #${ref.index}`;

// Four places, the precision the category numbers are shown and apportioned at.
const fourPlaces = (value: number): string => value.toFixed(4);

// The head of a deduction complaint — WRITTEN BY THE LENS, so a working session
// can reproduce it from the row alone. The same two-line shape as the
// landmark head: line 1 is the IDENTITY (`Abzug:` then the site, the machine
// token `<category>#<index>` in brackets, the letter, the row, and the site's
// part of its category's number), line 2 the measured `key value` pairs.
// Because a deduction files as a LETTER item, the Korb headline stays
// „Buchstabe x" and this head opens the body.
export function penaltyNoteHead(target: Extract<WerkbankTarget, { kind: 'penalty' }>): string {
  const { penalty: ref, glyphKey } = target;
  const t = de.admin.letters.penalties;
  const identity = [
    `${de.admin.werkbank.penaltyHead}: ${penaltyLabel(ref)} (${ref.category}#${ref.index})`,
    glyphKey,
    landmarkRowLabel(0),
    fmt(t.ofCategory, { value: fourPlaces(ref.value), total: fourPlaces(ref.categoryValue) }),
  ].join(' · ');
  // An unlocated site says so in words rather than leaving the reader to wonder
  // whether the position was forgotten.
  const position =
    ref.x !== null && ref.y !== null ? [`x ${ref.x} px`, `y ${ref.y} px`] : [t.noPlace];
  const details = [
    ref.exact ? t.exactTerm : t.exactShare,
    fmt(t.pointsShort, { points: ref.pointsEst.toFixed(2) }),
    `kind ${ref.kind}`,
    ...position,
    ...Object.entries(ref.numbers)
      .filter(([, value]) => value !== null && value !== undefined)
      .map(([key, value]) => `${key} ${value}`),
  ].join(' · ');
  return `${identity}\n${details}`;
}

// Identity of one drawn marker within its row — what the overlay keys on and
// what „selected" compares against.
export const landmarkKey = (landmark: { kind: string; index: number }): string =>
  `${landmark.kind}#${landmark.index}`;

// "Kringel #1" / "Stelle ohne Marke" — the marker as the overlay names it.
export function landmarkLabel(ref: LandmarkRef): string {
  const name = de.admin.letters.landmarkKind[ref.kind];
  return ref.index === null ? name : `${name} #${ref.index}`;
}

// Which stored row the landmark was read on.
export const landmarkRowLabel = (variant: number): string =>
  variant === 0 ? de.admin.letters.landmarksRowChart : de.admin.letters.landmarksRowLaufform;

// The head of a landmark work item — WRITTEN BY THE LENS, so a working session
// can reproduce the complaint from the row alone (optimierungs-werkbank.md §8).
// Deliberately plain text rather than a column: the landmark layer is DERIVED
// from the glyph_key's row, so a second key column would be a second name for
// the same thing, and a schema change for a string the human also has to read
// is the wrong trade.
//
// TWO lines, and the split is what makes the Korb readable: line 1 is the
// IDENTITY (`Landmarke:` then the German name, the machine token
// `<kind>#<index>` in brackets, the letter, the row) and becomes the row's
// headline; line 2 carries the measured `key value` pairs. It reads as a
// sentence AND greps as data.
export function landmarkNoteHead(target: Extract<WerkbankTarget, { kind: 'landmark' }>): string {
  const { landmark: ref, variant, glyphKey } = target;
  const token = ref.index === null ? ref.kind : `${ref.kind}#${ref.index}`;
  const identity = [
    `${de.admin.werkbank.kindLandmark}: ${landmarkLabel(ref)} (${token})`,
    glyphKey,
    landmarkRowLabel(variant),
  ].join(' · ');
  const position =
    ref.x !== undefined && ref.y !== undefined ? [`x ${ref.x.toFixed(4)}`, `y ${ref.y.toFixed(4)}`] : [];
  const numbers = [
    ...position,
    ...Object.entries(ref.numbers)
      .filter(([, value]) => value !== null && value !== undefined)
      .map(([key, value]) => `${key} ${value}`),
  ].join(' · ');
  // A landmark without a position and without numbers has nothing for the
  // second line — the identity alone is then the whole head, rather than a
  // blank line pretending something was measured.
  return numbers ? `${identity}\n${numbers}` : identity;
}

// Identity of one mark — the filing dialog is remounted under this key so its
// pre-sort/note state always starts fresh instead of being reset by an effect.
// A landmark carries its position: two „Stelle ohne Marke" complaints on the
// same letter have the same label and are not the same mark.
export const markKey = (mark: Mark): string => {
  const ref = mark.target.kind === 'landmark' ? mark.target.landmark : null;
  const where = ref && ref.x !== undefined && ref.y !== undefined ? `@${ref.x},${ref.y}` : '';
  return `${targetLabel(mark.target)}${where}:${mark.specimen?.id ?? '-'}`;
};

// Stable per-card DOM id, so a lens thumbnail can scroll its word into view.
export const cardElementId = (specimenId: string): string => `werkbank-card-${specimenId}`;

export function scrollToCard(specimenId: string): void {
  document.getElementById(cardElementId(specimenId))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Worst-first ranking of a stored word trace: unfitted letters dominate, the
// mean fit RMSE breaks ties.
export function rmseMean(row: WordInstanceOut): number | null {
  const values = Object.values(row.measurements.geo_rmse_px_by_slot ?? {});
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function badness(row: WordInstanceOut): number {
  return (row.measurements.unfitted_slots?.length ?? 0) * 10 + (rmseMean(row) ?? 0);
}

// Where a specimen stands in the manual tracing pass — the one question the
// word overview's status filter answers. Three states, and only three:
//   `authored`   — a hand-drawn trace is stored for it, the work is done;
//   `incomplete` — the sidecar flags the specimen's own ink as clipped, so the
//                  work can never be done (a cut-off i-dot, a last letter
//                  running off the plate). Not a to-do, and not a failure;
//   `open`       — everything else: still to trace.
// `authored` wins over `incomplete` deliberately: where a flagged specimen was
// traced anyway, the stored line is the truth about it, not the flag.
export type TraceStatus = 'authored' | 'open' | 'incomplete';

export function traceStatusOf(sample: WordSampleOut, traced: WordInstanceOut | null | undefined): TraceStatus {
  if (traced?.provenance === 'authored') return 'authored';
  return sample.incomplete ? 'incomplete' : 'open';
}

// The overview's filter over that status — `all` plus the three states.
export type TraceFilter = 'all' | TraceStatus;

// One piece of evidence for a word text in the word DETAIL: a Wortprobe of the
// plate, and the stored trace of it where one exists.
//
// The sample is the subject and the trace is an attribute of it, not the other
// way round — that inversion is the whole point. The detail used to build its
// list from the stored `word_instances`, so a Wortprobe that had never been
// traced was invisible there although the overview listed it with its crop:
// the one place where the missing work is done showed nothing exactly where
// there was work to do.
export type WordEvidence = { sample: WordSampleOut; row: WordInstanceOut | null };

// Every Wortprobe of one word text, worst first, each with its stored trace.
//
// WHICH specimens count as a Wortprobe of the text: the plate's `word` samples,
// plus any specimen of another kind that already carries a stored trace of it.
// The Abb.-20 pair drills are the other kind, and they have their own home in
// the Übergänge view — surfacing an untraced drill here as if the plate wrote
// the two-letter text as a WORD would put drill crops under „in", „of" or „du".
// A drill that HAS been traced stays reachable, because the drill card's „im
// Wort ansehen" deep-links exactly here and the trace-only list it replaces
// showed it.
//
// Order, unchanged from that list: the specimen named in the URL leads (so a
// deep link lands on it), then the worst measured fit — an untraced sample has
// nothing measured and therefore ranks last rather than pretending to a perfect
// fit of zero badness.
export function wordEvidenceOf(
  samples: WordSampleOut[],
  rows: WordInstanceOut[],
  text: string,
  specimenId: string | null,
): WordEvidence[] {
  const needle = text.trim().toLowerCase();
  if (!needle) return [];
  // Sidecar ids are unique across kinds — `sampleById` in the workbench keys on
  // the bare id for the same reason.
  const rowById = new Map(rows.map((row) => [row.specimen_id, row]));
  return samples
    .filter((sample) => sample.word.toLowerCase() === needle)
    .map((sample) => ({ sample, row: rowById.get(sample.id) ?? null }))
    .filter(({ sample, row }) => sample.kind === 'word' || row !== null)
    .sort((a, b) => {
      if (a.sample.id === specimenId) return -1;
      if (b.sample.id === specimenId) return 1;
      return (b.row ? badness(b.row) : -1) - (a.row ? badness(a.row) : -1);
    });
}

// The evidence that belongs to the PLATE's own hand — everything the detail is
// allowed to count.
//
// A sample carrying a `sample_set` tag comes from another writer's plate (the
// Abb.-22 Schülerschrift). It may stand in the detail as context, but it is
// „Kontext, nie Vorbild": excluded from this hand's statistics AND from its
// head counts (Vorgabe V4 of the Admin-Redesign). Truthiness, not != null, so
// an empty tag does not make a sample foreign — the same test the overview's
// mode filter makes.
export const ownHandEvidence = (evidence: WordEvidence[]): WordEvidence[] =>
  evidence.filter((e) => !e.sample.sample_set);

// Whether the word editor may be opened on this piece of evidence. Two kinds
// of sample are context rather than work, and both refusals are doctrine:
//
// * a FOREIGN writer's sample (Abb. 22) — a Bahn drawn over it would be stored
//   under the PLATE's hand and become ground truth for statistics and training
//   under the wrong writer („Kontext, nie Vorbild", V4);
// * an untraced sample whose own ink is CLIPPED — „sie lässt sich nicht von
//   Hand nachfahren und ist darum weder Arbeit noch Versäumnis" (glossar
//   „Unvollständige Wortprobe"): the i-dot is missing, the last letter runs off
//   the plate, so the hand has nothing to follow.
//
// A clipped specimen that ALREADY carries a row keeps its entry: that row
// exists and may be re-drawn, and `traceStatusOf` then reads the resulting hand
// line as the truth about the specimen rather than the flag. The card says why
// either way — the „Unvollständig" chip carries the sidecar's own reason.
export const canTraceByHand = ({ sample, row }: WordEvidence): boolean =>
  !sample.sample_set && !(sample.incomplete && !row);

// A Wortprobe with no stored trace, in the shape the word editor already takes.
//
// EDITOR-ONLY, never a display row: the spine card gets `row = null` for such a
// sample and says „Offen". The seed exists so the tested write flow is CALLED
// rather than rebuilt — the dialog keeps its props, its save body and its
// suites, and the first authored trace for a specimen is simply an upsert the
// server has always accepted (`PUT …/word-instances` keys on kind + specimen).
//
// The registration is the sidecar's own lineature, so the editor's frame gate
// reads it as current and opens without a spurious „Rahmen veraltet". `slots`
// is the shaper's own list, the Python twin of which the harvest stores, so a
// later re-harvest of the same specimen finds the labels it would have written.
export function seedWordInstance(sample: WordSampleOut): WordInstanceOut {
  return {
    kind: sample.kind,
    specimen_id: sample.id,
    word: sample.word,
    slots: keysOfText(sample.word),
    strokes: [],
    // What the save writes regardless — a seeded row can only ever become a
    // hand trace, since the only way to store it is to draw it.
    provenance: 'authored',
    // No sibling row to inherit from: the dialog resolves the hand from its
    // `fallbackHandId` and keeps saving disabled, with a reason, when none does.
    hand_id: null,
    measurements: {
      registration_px: { tx: 0, ty: 0, baseline_row: sample.baseline_y },
      xh_px: sample.baseline_y - sample.midband_y,
    },
    updated_at: null,
  };
}

export const matchesTraceFilter = (filter: TraceFilter, status: TraceStatus): boolean =>
  filter === 'all' || filter === status;

export interface CropBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

// Occurrence boxes are PAGE pixels of the plate, the crop starts at the word
// sample's rect origin — subtracting it puts the box in the crop's own frame
// (the SVG viewBox the spine card draws in). `rect` may be missing when a
// browser/CDN still serves the pre-`rect` word-samples schema (the endpoint's
// stale-while-revalidate spans days) — then there is no valid crop frame and
// the caller skips the interactive layer instead of drawing at page coords.
export function cropBoxOf(inst: InstanceOut, rect: number[] | undefined): CropBox | null {
  if (!rect || rect.length < 2) return null;
  return { x: inst.x0 - rect[0], y: inst.y0 - rect[1], w: inst.x1 - inst.x0, h: inst.y1 - inst.y0 };
}

// The crop box of a JOIN occurrence — the union of the two letters it runs
// between. A `pair_instance` stores its geometry in the glyph_pairs frame
// (template units relative to the left glyph's exit) and therefore carries no
// pixel box of its own; but it names the specimen and the LEFT glyph's slot
// (`tools/pairlab/harvest.py::_adjacent_joined` walks adjacent slot pairs), and
// the letter occurrences of the same plate carry exactly those slots as boxes.
// So the join's pixels are found rather than stored.
//
// Both letters must be present AND carry the expected glyph key: a slot index
// that lands on a different letter means the two harvests disagree about the
// word's slotting, and showing the wrong ink is worse than showing none.
export function joinCropBoxOf(
  occ: { left_key: string; right_key: string; slot: number },
  letters: InstanceOut[] | undefined,
  rect: number[] | undefined,
): CropBox | null {
  const at = (slot: number, key: string) =>
    (letters ?? []).find((i) => i.measurements.slot === slot && i.glyph_key === key);
  const left = at(occ.slot, occ.left_key);
  const right = at(occ.slot + 1, occ.right_key);
  if (!left || !right) return null;
  const a = cropBoxOf(left, rect);
  const b = cropBoxOf(right, rect);
  if (!a || !b) return null;
  const x = Math.min(a.x, b.x);
  const y = Math.min(a.y, b.y);
  return { x, y, w: Math.max(a.x + a.w, b.x + b.w) - x, h: Math.max(a.y + a.h, b.y + b.h) - y };
}

// Where a word's units sit in its specimen crop. The stored trace AND the
// engine's composition of the same word live in the identical frame (baseline
// = 0, 1 unit = x-height), so ONE map serves both: px = (u·xh + tx,
// baselineRow − v·xh).
//
// This is the row's own MEASURED registration, and it matters: the overlay used
// to pin the composition to the crop's left edge instead, which put it a median
// 8.9 px (~0.3 xh) left of the ink over the 63 Sütterlin word rows — every
// composition read worse than it is. On the measured registration that median
// drops to 1.1 px; what remains is the real width difference, which is the
// thing worth seeing. The left-edge pin survives only as the fallback for a
// sample with no traced row (`row` null) — there is nothing measured to use.
export interface TraceFrame {
  xh: number;
  tx: number;
  baselineRow: number;
}

export function traceFrameOf(
  row: WordInstanceOut | null | undefined,
  sample: { baseline_y: number; midband_y: number },
): TraceFrame {
  const fallback = { xh: sample.baseline_y - sample.midband_y, tx: 0, baselineRow: sample.baseline_y };
  if (!row) return fallback;
  const reg = row.measurements.registration_px;
  return {
    xh: row.measurements.xh_px ?? fallback.xh,
    tx: reg?.tx ?? fallback.tx,
    baselineRow: (reg?.baseline_row ?? fallback.baselineRow) + (reg?.ty ?? 0),
  };
}

// SVG transform for a TraceFrame — y flipped, since units grow upwards.
export const traceMatrix = (f: TraceFrame): string => `matrix(${f.xh} 0 0 ${-f.xh} ${f.tx} ${f.baselineRow})`;

// The request body for one filed task. specimen_kind + specimen_id always go
// together — the API 422s on a half-given reference — and are simply absent for
// a freely typed target that was never seen on a plate.
export function workItemBodyOf(mark: Mark, note: string): WorkItemIn {
  const base = mark.specimen
    ? { note, specimen_kind: mark.specimen.kind, specimen_id: mark.specimen.id }
    : { note };
  if (mark.target.kind === 'letter') return { ...base, kind: 'letter', glyph_key: mark.target.glyphKey };
  if (mark.target.kind === 'pair') {
    return { ...base, kind: 'pair', left_key: mark.target.leftKey, right_key: mark.target.rightKey };
  }
  if (mark.target.kind === 'landmark') {
    // The generated line first, the author's own words under it — the API
    // insists on text for exactly this reason (an item that does not say WHICH
    // landmark is unworkable).
    const head = landmarkNoteHead(mark.target);
    return { ...base, kind: 'landmark', glyph_key: mark.target.glyphKey, note: note ? `${head}\n\n${note}` : head };
  }
  if (mark.target.kind === 'penalty') {
    // A plain LETTER item — no kind or stage of its own (author decision
    // 2026-09-23) — whose note opens with the lens's head, so the row still
    // says which deduction of which letter, with which numbers.
    const head = penaltyNoteHead(mark.target);
    return { ...base, kind: 'letter', glyph_key: mark.target.glyphKey, note: note ? `${head}\n\n${note}` : head };
  }
  return { ...base, kind: 'word', word: mark.target.word };
}

// Overlay palette — what each mark on a work surface MEANS, resolved onto the
// palette's own Ebenen-Token (`styles/paper.ts`). The hues used to live here as
// literals, which is how the trace green reached 2.71:1 on the white sketches
// and how it ended up meeting the engine red in a pair no reader with a
// red-green deficiency can separate; the token file carries the contrast and
// colour-vision rules now, and this map only names the jobs.
export const WERKBANK_COLORS = {
  // ONE pen-path colour for both grounds. There used to be a second, brighter
  // token for the line drawn ON TOP of plate ink, because the dark green
  // vanished exactly where it mattered — `layer.trace` clears both (4.62:1 on
  // white, 3.70:1 on the ink), so the two collapse back into one.
  trace: layer.trace,
  box: paper.line, // dashed letter box, recessive
  accent: paper.sepia, // joins + hover
  // An ACTIVE state, not a role and not a reading: viridian is the app's one
  // accent for exactly that (design-system §2). It ships ahead of its consumer
  // — the Werkbank's selection highlight is a Phase-1 surface — so that the
  // Zinnober it used to hold is free for the engine layer.
  selected: paper.viridian,
  // What is written TODAY, against a median that would replace it: the warning
  // family's own hue, DOTTED. It shares the Pfad layer's hex, and can, because
  // no surface draws a Pfad and a Laufform reference at once — but it must not
  // also borrow the Engine's 4:3 dash, which §2 teaches as that layer's own
  // signature. Like the Absetzer it is a non-layer mark: no legend entry of its
  // own, so it takes the free stroke style rather than a taught one.
  current: pigment.ochre,
  engine: layer.engine, // what the engine itself writes — overlay AND its own face
  // The Pfad layer: the SAME line, read as a movement. The ramp runs from the
  // line's own colour — `trace` above, or whatever the caller passes as
  // `color` — to `pathLast` for the final stretch, so the writing ORDER is
  // legible without a legend and a path still looks like the trace it is. Only
  // the far end needs a token of its own; a separate „first" token was carried
  // here for a while, read by nothing, and agreed with the line colour by
  // coincidence rather than by construction (review of PR #598).
  pathLast: layer.path,
  lift: liftConnector.color,
} as const;

// The stroke style of the two marks that are NOT layers, so colour and stroke
// travel together for them the way `layer`/`layerDash` does for a layer. Both
// are dotted: the taught 4:3 dash belongs to the engine layer and a mark
// without a legend entry may not borrow a signature a legend teaches.
export const WERKBANK_DASH = {
  current: strokeStyle.dotted,
  lift: liftConnector.stroke,
} as const;
