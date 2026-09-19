// The Auftragskorb (optimierungs-werkbank.md §5): the filed work_items of the
// active source, grouped by where they stand in the handling protocol. Open
// items are the round's queue a working session reads at start; an acked one
// carries the session's restatement — what it understood the task to be and
// whether it could reproduce it — written BEFORE it changes anything, so a
// misunderstanding surfaces early and can be rejected here with one click.
// Returned items sit on top: those need the author, not the algorithm. Done
// ones stay behind a toggle with their diagnosed stage and resolution, which
// is what makes the archive worth keeping — and is why the bin icon asks
// before it deletes rather than emptying that record on one tap.
//
// Since the redesign the panel lives in the shell's Korb drawer rather than on
// one page: the basket belongs to the whole workbench, and a drawer keeps it
// off the words the admin is judging while it is closed.

import AddIcon from '@mui/icons-material/Add';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import {
  Alert,
  Box,
  Button,
  ButtonBase,
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  MenuItem,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { createWorkItem, deleteWorkItem, listWorkItems, patchWorkItem } from '@/lib/api';
import type { WorkItemKind, WorkItemOut, WorkItemStage, WorkItemStatus } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { joinsUrl, lettersUrl, wordsUrl } from '@/sections/admin/shell/focus';
import {
  groupKorb,
  isKorbFilterAll,
  korbArchiveHides,
  korbArchiveVisible,
  KORB_FILTER_ALL,
  KORB_FILTER_STAGES,
  KORB_GROUP_ORDER,
  type KorbFilter,
} from '@/sections/admin/shell/korbFilter';
import { TOUCH_TARGET } from '@/styles/hitArea';

// The heading above each status group — `open` is the unmarked queue and
// carries none. These are sentences („Zurückgegeben — braucht deine Hand"),
// which is why the filter menu has its own short words instead.
const GROUP_HEADINGS: Record<WorkItemStatus, string | null> = {
  returned: de.admin.werkbank.korbReturned,
  open: null,
  ack: de.admin.werkbank.korbInProgress,
  done: de.admin.werkbank.korbDoneHeading,
};

const STATUS_LABELS: Record<WorkItemStatus, string> = de.admin.werkbank.korbStatusShort;
const STAGE_LABELS: Record<WorkItemStage, string> = de.admin.werkbank.korbStage;
const KIND_LABELS: Record<WorkItemKind, string> = {
  letter: de.admin.werkbank.kindLetter,
  pair: de.admin.werkbank.kindPair,
  word: de.admin.werkbank.kindWord,
  landmark: de.admin.werkbank.kindLandmark,
  note: de.admin.werkbank.kindNote,
};
// Safe as `Object.keys`: the map above is a fresh object literal, so TypeScript
// checks it for excess members too. The Stufen come from `KORB_FILTER_STAGES`
// instead — that record is the LOCALE's, which excess-property checking does
// not reach.
const FILTER_KINDS = Object.keys(KIND_LABELS) as WorkItemKind[];

// Every select wears the §9.3 touch floor on its closed field; the options get
// it from the theme's `MuiMenuItem`.
const FILTER_FIELD_SX = { '& .MuiOutlinedInput-root': { minHeight: TOUCH_TARGET } } as const;

// MUI's `small` button is 30.75 px and its default 36.5 — both under the §9.3
// floor. The drawer's buttons sit in tight rows, so they GROW rather than wear
// an invisible overlay that would reach into the neighbour.
const BUTTON_TARGET = { minHeight: TOUCH_TARGET } as const;

// "Buchstabe a" / "Übergang d→a" / "Wort einen" — the level plus its target.
// A note has no target: its first line IS the headline, so a basket of notes
// reads as what was noticed instead of a column of the word "Notiz". A
// landmark's headline is likewise its own first line — the lens wrote it, and
// it already names which marker on which letter (§8).
function workItemLabel(item: WorkItemOut): string {
  const t = de.admin.werkbank;
  if (item.kind === 'letter') return `${t.kindLetter} ${item.glyph_key ?? '?'}`;
  if (item.kind === 'pair') return `${t.kindPair} ${item.left_key ?? '?'}→${item.right_key ?? '?'}`;
  // No `?? specimen_id` here: the row already appends the specimen id after the
  // label, so a word item filed by its specimen alone printed the id twice.
  if (item.kind === 'word') return `${t.kindWord} ${item.word ?? '?'}`;
  const firstLine = item.note.split('\n')[0].trim();
  if (item.kind === 'landmark') return firstLine || `${t.kindLandmark} ${item.glyph_key ?? '?'}`;
  return firstLine || t.kindNote;
}

// What is left of the note once the label took its share — everything for the
// three targeted kinds, the lines after the first for a note or a landmark.
function workItemBody(item: WorkItemOut): string {
  if (item.kind !== 'note' && item.kind !== 'landmark') return item.note;
  return item.note.split('\n').slice(1).join('\n').trim();
}

// Where a filed task points. Without it the basket is a dead end: it names the
// thing that is wrong and offers no way to it — while the three views are one
// link away for exactly these keys. Null only when the row carries no usable
// target — a word item filed by specimen id alone, or a general note, which
// points at nothing in the workbench by definition.
//
// `hand` is the ACTIVE hand, appended to every link the basket offers: a task
// names its subject and the scope is the other half of the premise (Q2 a).
// Phase 1 has no hand ON the row — `work_items.hand_id` is Phase 3 (V7) — so
// this is honestly „the hand this session is on", which is also the hand the
// row was filed under in the session that filed it.
function workItemUrl(item: WorkItemOut, hand: string | null): string | null {
  // A landmark points at its letter: the lens lives in that view, and the
  // note's first line says which marker to open it on.
  if (item.kind === 'letter' || item.kind === 'landmark') {
    return item.glyph_key ? lettersUrl(item.glyph_key, hand) : null;
  }
  if (item.kind === 'pair') {
    return item.left_key && item.right_key ? joinsUrl(item.left_key, item.right_key, hand) : null;
  }
  if (item.kind === 'word') return item.word ? wordsUrl(item.word, item.specimen_id, hand) : null;
  return null;
}

function ItemRow({
  item,
  onDelete,
  onReject,
  onOpen,
}: {
  item: WorkItemOut;
  onDelete: () => void;
  onReject: (correction: string) => void;
  // Navigate to the task's subject; absent when the row names no reachable one.
  onOpen?: () => void;
}) {
  const t = de.admin.werkbank;
  const [rejecting, setRejecting] = useState(false);
  const [correction, setCorrection] = useState('');

  return (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, py: 0.5, borderTop: 1, borderColor: 'divider' }}>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {/* The one opener of a basket row. It was a `<p role="link">` with a
            hand-rolled `tabIndex` and a hand-rolled Enter/Space handler: a tab
            stop that showed NOTHING when reached, because `MuiTypography` has
            no focus-visible rule and the ring lives on `ButtonBase`. A
            `ButtonBase` is the same three lines with the ring, the native key
            handling and the right role (§9.1, V24 „jeder Öffner"). */}
        {onOpen ? (
          <ButtonBase
            onClick={onOpen}
            sx={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              // The row is dense and the label is the whole first line, so it
              // grows to the floor instead of wearing an overlay that would
              // reach into the neighbouring row (§9.3).
              minHeight: TOUCH_TARGET,
              px: 0.5,
              borderRadius: 1,
              '&:hover .korb-row-label': { textDecoration: 'underline' },
            }}
          >
            {/* `component="span"`: `body2` maps to `<p>`, and a `<button>` takes
                phrasing content only — React does not warn, but the markup is
                invalid and the nested caption below is already a `span`. */}
            <Typography
              className="korb-row-label"
              variant="body2"
              component="span"
              sx={{ display: 'block', fontWeight: 600, color: 'primary.main' }}
            >
              {workItemLabel(item)}
              {item.specimen_id && (
                <Typography component="span" variant="caption" color="text.secondary">
                  {` · ${item.specimen_id}`}
                </Typography>
              )}
            </Typography>
          </ButtonBase>
        ) : (
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {workItemLabel(item)}
            {item.specimen_id && (
              <Typography component="span" variant="caption" color="text.secondary">
                {` · ${item.specimen_id}`}
              </Typography>
            )}
          </Typography>
        )}
        {workItemBody(item) && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', whiteSpace: 'pre-line' }}>
            {workItemBody(item)}
          </Typography>
        )}

        {/* The session's restatement — the point of the whole protocol: read it
            before it has spent a round on the wrong problem. */}
        {item.understanding && (
          <Box sx={{ mt: 0.5, pl: 1, borderLeft: 2, borderColor: 'divider' }}>
            <Typography variant="caption" sx={{ display: 'block', fontStyle: 'italic' }}>
              {`${t.korbUnderstanding} ${item.understanding}`}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.25 }}>
              {item.reproduced && (
                <Chip
                  size="small"
                  variant="outlined"
                  color={item.reproduced === 'no' ? 'warning' : 'default'}
                  label={t.korbReproduced[item.reproduced]}
                />
              )}
              {item.stage && <Chip size="small" variant="outlined" label={t.korbStage[item.stage]} />}
            </Box>
          </Box>
        )}

        {item.resolution && (
          <Typography
            variant="caption"
            color={item.status === 'returned' ? 'warning.main' : 'success.main'}
            sx={{ display: 'block', mt: 0.25 }}
          >
            {item.resolution}
          </Typography>
        )}

        {item.status === 'ack' &&
          (rejecting ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 0.5 }}>
              <TextField
                multiline
                minRows={2}
                size="small"
                label={t.korbRejectLabel}
                value={correction}
                onChange={(e) => setCorrection(e.target.value)}
              />
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="contained" sx={BUTTON_TARGET} onClick={() => onReject(correction.trim())}>
                  {t.korbRejectSubmit}
                </Button>
                <Button size="small" sx={BUTTON_TARGET} onClick={() => setRejecting(false)}>
                  {t.cancel}
                </Button>
              </Box>
            </Box>
          ) : (
            <Button size="small" sx={{ mt: 0.25, px: 0.5, minHeight: TOUCH_TARGET }} onClick={() => setRejecting(true)}>
              {t.korbReject}
            </Button>
          ))}

        {item.created_at && (
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
            {new Date(item.created_at).toLocaleString('de-DE')}
          </Typography>
        )}
      </Box>
      {/* Grown, not overlaid: the rows stack tightly, so an invisible 44er
          would reach into the bin of the row above (§9.3). */}
      <IconButton size="small" aria-label={t.korbDelete} onClick={onDelete} sx={{ width: TOUCH_TARGET, height: TOUCH_TARGET }}>
        <DeleteOutlinedIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}

export function KorbPanel({
  sourceId,
  refreshKey,
  onChanged,
  onNavigate,
}: {
  sourceId: string;
  refreshKey: number;
  // A mutation the panel applied optimistically — the shell re-reads the open
  // count from it rather than tracking the same rows twice.
  onChanged?: () => void;
  // Called just before following a task's link, so the drawer holding the
  // panel can close itself.
  onNavigate?: () => void;
}) {
  const navigate = useNavigate();
  const { handId } = useAdmin();
  const t = de.admin.werkbank;
  const [items, setItems] = useState<WorkItemOut[] | null>(null);
  const [error, setError] = useState(false);
  const [writeError, setWriteError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [showDone, setShowDone] = useState(false);
  // Triage filter over the rows already loaded — see `korbFilter.ts` for why it
  // is client-side. Component state only: the drawer is not a route, and a
  // filter kept in the URL or in localStorage would silently narrow a basket
  // the author opens days later.
  const [filter, setFilter] = useState<KorbFilter>(KORB_FILTER_ALL);
  // The row whose deletion is being confirmed (see `remove`).
  const [confirming, setConfirming] = useState<WorkItemOut | null>(null);
  // The target-less quick note (see `addNote`).
  const [adding, setAdding] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  // Clear what belonged to the previous list DURING RENDER instead of in the
  // effect below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs.
  // `items` deliberately stays: the old rows are held until the fresh ones
  // arrive, so a refresh does not blink the panel empty.
  const loadKey = `${sourceId} ${refreshKey}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setError(false);
    setWriteError(null);
    // A question about a row of the previous list must not outlive it.
    setConfirming(null);
  }

  useEffect(() => {
    let cancelled = false;
    listWorkItems(sourceId, undefined, { retries: 2 })
      .then((rows) => {
        if (!cancelled) setItems(rows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, refreshKey]);

  const rows = items ?? [];
  // Handed back first (those wait on the author), then the queue, then what a
  // session is currently working on; the archive only on request.
  const groups = groupKorb(rows, filter, showDone);
  // These two read the UNFILTERED rows on purpose: the title's „n offen" and —
  // through `onChanged` — the shell's header badge count the BASKET, never the
  // current view. A filter that changed the badge would make the workbench
  // claim work was finished by hiding it.
  const openCount = rows.filter((i) => i.status === 'open' || i.status === 'returned').length;
  const doneCount = rows.filter((i) => i.status === 'done').length;
  const visibleCount = groups.reduce((n, g) => n + g.rows.length, 0);
  // Three distinct silences, so an empty list never lies about why it is empty:
  // an untouched basket, a filter that matches nothing, and rows that are only
  // hidden behind the „erledigte anzeigen" switch. The last sentence is EARNED,
  // not assumed — `korbArchiveHides` asks whether turning the switch on would
  // actually bring a row back, because the bare existence of a `done` row says
  // nothing under a filter that excludes the archive anyway.
  const emptyText =
    rows.length === 0
      ? t.korbEmpty
      : isKorbFilterAll(filter)
        ? t.korbNoMatchDone
        : korbArchiveHides(rows, filter, showDone)
          ? `${t.korbNoMatch} ${t.korbNoMatchDone}`
          : t.korbNoMatch;

  // Undo ONE row's optimistic change — restoring a whole snapshot would revive
  // rows a concurrent delete already removed, or discard a reject that landed
  // in the meantime. A row the failed call had removed is re-inserted in id
  // order, which is the server's own ordering (oldest first).
  const restore = (row: WorkItemOut) =>
    setItems((prev) => {
      const rows = prev ?? [];
      return rows.some((i) => i.id === row.id)
        ? rows.map((i) => (i.id === row.id ? row : i))
        : [...rows, row].sort((a, b) => a.id - b.id);
    });

  // Optimistic write: the basket is the admin's own, and a failed call must not
  // leave the list claiming something the server never stored.
  //
  // `onChanged` is reported only AFTER the server confirmed. It bumps the
  // shell's `refreshKey`, and this panel re-reads on that key — announcing the
  // change up front therefore started a re-read that RACED the write and
  // usually won, so the server's pre-write rows came back and undid the
  // optimistic change on screen (a deleted item reappeared and sat there until
  // the next reload). On failure the row is restored locally and nothing is
  // announced: the server state never moved.
  const mutate = (
    item: WorkItemOut,
    apply: (row: WorkItemOut) => WorkItemOut,
    call: () => Promise<unknown>,
    message: string,
  ) => {
    setWriteError(null);
    setItems((prev) => (prev ?? []).map((i) => (i.id === item.id ? apply(i) : i)));
    call()
      .then(() => onChanged?.())
      .catch(() => {
        restore(item);
        setWriteError(message);
      });
  };

  // Deleting is a hard DELETE with no undo anywhere in the basket, so the bin
  // icon only asks — `confirming` holds the row the question is about. An
  // erledigter Auftrag is the case that made this necessary: its protocol
  // (restatement · diagnosed stage · resolution) is the archive of symptom →
  // diagnosis → change the whole §5 protocol exists to accumulate, and one
  // stray tap on a phone used to be enough to lose it.
  const remove = (item: WorkItemOut) => {
    setConfirming(null);
    setWriteError(null);
    setItems((prev) => (prev ?? []).filter((i) => i.id !== item.id));
    deleteWorkItem(sourceId, item.id)
      .then(() => onChanged?.())
      .catch(() => {
        restore(item);
        setWriteError(t.korbDeleteError);
      });
  };

  // A general Kleinigkeit — an admin-UI wrinkle, a wording slip — filed with
  // nothing but its text. It points at no letter, join or word, so it is
  // reachable only here: the ⚑ affordance always marks something specific,
  // while this is the note the admin would otherwise lose because opening a
  // GitHub issue for it is out of proportion. The stored row is inserted
  // directly (the server hands it back with its id) so the basket shows it
  // before the confirming re-read arrives.
  const addNote = () => {
    const text = noteText.trim();
    if (!text || savingNote) return;
    setSavingNote(true);
    setWriteError(null);
    createWorkItem(sourceId, { kind: 'note', note: text })
      .then((row) => {
        setItems((prev) => [...(prev ?? []), row]);
        setNoteText('');
        setAdding(false);
        onChanged?.();
      })
      .catch(() => setWriteError(t.korbAddError))
      .finally(() => setSavingNote(false));
  };

  // "Missverstanden": the item goes back into the queue with the correction
  // appended to the note. The restatement itself stays on the row — a rejected
  // reading is part of the record, and the next session should see it.
  const reject = (item: WorkItemOut, correction: string) => {
    const note = correction ? `${item.note}\n\n${t.korbCorrectionPrefix} ${correction}`.trim() : item.note;
    mutate(
      item,
      (row) => ({ ...row, status: 'open', note, closed_at: null }),
      () => patchWorkItem(sourceId, item.id, { status: 'open', note }),
      t.korbRejectError,
    );
  };

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 2, bgcolor: 'background.paper', p: 1.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          {`⚑ ${t.korbTitle} (${fmt(t.korbOpenCount, { count: openCount })})`}
        </Typography>
        {/* The name says what the button DOES, not what it sits next to (it
            was „Auftragskorb", which is the heading right beside it), and
            aria-expanded reports the state the chevron shows visually. */}
        <IconButton
          size="small"
          aria-label={expanded ? de.admin.shell.closeKorb : de.admin.shell.openKorb}
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
          sx={{ width: TOUCH_TARGET, height: TOUCH_TARGET }}
        >
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        {adding ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 1 }}>
            <TextField
              multiline
              minRows={2}
              size="small"
              label={t.korbNoteLabel}
              placeholder={t.korbNotePlaceholder}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              // ⌘/Strg+Enter files it without reaching for the button — this is
              // the surface used one-handed on a phone.
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  addNote();
                }
              }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                variant="contained"
                sx={BUTTON_TARGET}
                onClick={addNote}
                disabled={savingNote || !noteText.trim()}
              >
                {t.korbAddSubmit}
              </Button>
              <Button
                size="small"
                sx={BUTTON_TARGET}
                onClick={() => {
                  setAdding(false);
                  setNoteText('');
                }}
              >
                {t.cancel}
              </Button>
            </Box>
          </Box>
        ) : (
          <Button
            size="small"
            startIcon={<AddIcon fontSize="small" />}
            sx={{ ...BUTTON_TARGET, mt: 0.5 }}
            onClick={() => setAdding(true)}
          >
            {t.korbAddNote}
          </Button>
        )}
        {writeError && (
          <Alert severity="warning" sx={{ mt: 1 }} onClose={() => setWriteError(null)}>
            {writeError}
          </Alert>
        )}
        {/* Only once there is something to narrow — an untouched basket stays
            the single sentence it is today. „Stufe" sits on its own row: its
            words are the longest and a truncated diagnosis is unreadable. */}
        {rows.length > 0 && (
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
            <TextField
              select
              size="small"
              label={t.korbFilterStatus}
              value={filter.status}
              onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value as KorbFilter['status'] }))}
              sx={FILTER_FIELD_SX}
            >
              <MenuItem value="all">{t.korbFilterAll}</MenuItem>
              {KORB_GROUP_ORDER.map((status) => (
                <MenuItem key={status} value={status}>
                  {STATUS_LABELS[status]}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label={t.korbFilterKind}
              value={filter.kind}
              onChange={(e) => setFilter((f) => ({ ...f, kind: e.target.value as KorbFilter['kind'] }))}
              sx={FILTER_FIELD_SX}
            >
              <MenuItem value="all">{t.korbFilterAll}</MenuItem>
              {FILTER_KINDS.map((kind) => (
                <MenuItem key={kind} value={kind}>
                  {KIND_LABELS[kind]}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              size="small"
              label={t.korbFilterStage}
              value={filter.stage}
              onChange={(e) => setFilter((f) => ({ ...f, stage: e.target.value as KorbFilter['stage'] }))}
              sx={{ ...FILTER_FIELD_SX, gridColumn: '1 / -1' }}
            >
              <MenuItem value="all">{t.korbFilterAll}</MenuItem>
              {KORB_FILTER_STAGES.map((stage) => (
                <MenuItem key={stage} value={stage}>
                  {STAGE_LABELS[stage]}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        )}
        {error ? (
          <Alert severity="warning" sx={{ mt: 1 }}>
            {t.korbLoadError}
          </Alert>
        ) : visibleCount === 0 ? (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {emptyText}
          </Typography>
        ) : (
          <Box sx={{ mt: 1 }}>
            {groups.map((g) => (
              <Box key={g.key}>
                {GROUP_HEADINGS[g.key] && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {GROUP_HEADINGS[g.key]}
                  </Typography>
                )}
                {g.rows.map((item) => {
                  const url = workItemUrl(item, handId);
                  return (
                    <ItemRow
                      key={item.id}
                      item={item}
                      onDelete={() => setConfirming(item)}
                      onReject={(correction) => reject(item, correction)}
                      onOpen={
                        url
                          ? () => {
                              onNavigate?.();
                              navigate(url);
                            }
                          : undefined
                      }
                    />
                  );
                })}
              </Box>
            ))}
          </Box>
        )}
        {doneCount > 0 && (
          <FormControlLabel
            sx={{ mt: 0.5 }}
            control={
              <Switch
                size="small"
                // Picking status „Erledigt" already asked for the archive, so
                // the switch reports it as on instead of contradicting the
                // list below it, and stops being a second answer to the same
                // question until the filter lets go again.
                checked={korbArchiveVisible(filter, showDone)}
                disabled={filter.status === 'done'}
                onChange={(e) => setShowDone(e.target.checked)}
              />
            }
            label={<Typography variant="caption">{t.korbShowDone}</Typography>}
          />
        )}
      </Collapse>

      <Dialog open={confirming !== null} onClose={() => setConfirming(null)} maxWidth="xs" fullWidth>
        <DialogTitle>{t.korbDeleteConfirmTitle}</DialogTitle>
        <DialogContent>
          {confirming && (
            <>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {workItemLabel(confirming)}
                {confirming.specimen_id && (
                  <Typography component="span" variant="caption" color="text.secondary">
                    {` · ${confirming.specimen_id}`}
                  </Typography>
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {t.korbDeleteConfirmBody}
              </Typography>
              {confirming.status === 'done' && (
                <Alert severity="warning" sx={{ mt: 1.5 }}>
                  {t.korbDeleteConfirmArchive}
                </Alert>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button sx={BUTTON_TARGET} onClick={() => setConfirming(null)}>
            {t.cancel}
          </Button>
          <Button
            color="error"
            variant="contained"
            sx={BUTTON_TARGET}
            onClick={() => confirming && remove(confirming)}
          >
            {t.korbDeleteConfirmSubmit}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
