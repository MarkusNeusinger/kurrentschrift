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
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { createWorkItem, deleteWorkItem, listWorkItems, patchWorkItem } from '@/lib/api';
import type { WorkItemOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { joinsUrl, lettersUrl, wordsUrl } from '@/sections/admin/shell/focus';

// "Buchstabe a" / "Übergang d→a" / "Wort einen" — the level plus its target.
// A note has no target: its first line IS the headline, so a basket of notes
// reads as what was noticed instead of a column of the word "Notiz".
function workItemLabel(item: WorkItemOut): string {
  const t = de.admin.werkbank;
  if (item.kind === 'letter') return `${t.kindLetter} ${item.glyph_key ?? '?'}`;
  if (item.kind === 'pair') return `${t.kindPair} ${item.left_key ?? '?'}→${item.right_key ?? '?'}`;
  // No `?? specimen_id` here: the row already appends the specimen id after the
  // label, so a word item filed by its specimen alone printed the id twice.
  if (item.kind === 'word') return `${t.kindWord} ${item.word ?? '?'}`;
  return item.note.split('\n')[0].trim() || t.kindNote;
}

// What is left of the note once the label took its share — everything for the
// three targeted kinds, the lines after the first for a note.
function workItemBody(item: WorkItemOut): string {
  if (item.kind !== 'note') return item.note;
  return item.note.split('\n').slice(1).join('\n').trim();
}

// Where a filed task points. Without it the basket is a dead end: it names the
// thing that is wrong and offers no way to it — while the three views are one
// link away for exactly these keys. Null only when the row carries no usable
// target — a word item filed by specimen id alone, or a general note, which
// points at nothing in the workbench by definition.
function workItemUrl(item: WorkItemOut): string | null {
  if (item.kind === 'letter') return item.glyph_key ? lettersUrl(item.glyph_key) : null;
  if (item.kind === 'pair') return item.left_key && item.right_key ? joinsUrl(item.left_key, item.right_key) : null;
  if (item.kind === 'word') return item.word ? wordsUrl(item.word, item.specimen_id) : null;
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
        <Typography
          variant="body2"
          sx={{
            fontWeight: 600,
            ...(onOpen && {
              cursor: 'pointer',
              color: 'primary.main',
              '&:hover': { textDecoration: 'underline' },
            }),
          }}
          {...(onOpen && { role: 'link', tabIndex: 0, onClick: onOpen })}
          onKeyDown={(e) => {
            if (!onOpen || (e.key !== 'Enter' && e.key !== ' ')) return;
            e.preventDefault();
            onOpen();
          }}
        >
          {workItemLabel(item)}
          {item.specimen_id && (
            <Typography component="span" variant="caption" color="text.secondary">
              {` · ${item.specimen_id}`}
            </Typography>
          )}
        </Typography>
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
                <Button size="small" variant="contained" onClick={() => onReject(correction.trim())}>
                  {t.korbRejectSubmit}
                </Button>
                <Button size="small" onClick={() => setRejecting(false)}>
                  {t.cancel}
                </Button>
              </Box>
            </Box>
          ) : (
            <Button size="small" sx={{ mt: 0.25, px: 0.5 }} onClick={() => setRejecting(true)}>
              {t.korbReject}
            </Button>
          ))}

        {item.created_at && (
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
            {new Date(item.created_at).toLocaleString('de-DE')}
          </Typography>
        )}
      </Box>
      <IconButton size="small" aria-label={t.korbDelete} onClick={onDelete}>
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
  const t = de.admin.werkbank;
  const [items, setItems] = useState<WorkItemOut[] | null>(null);
  const [error, setError] = useState(false);
  const [writeError, setWriteError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [showDone, setShowDone] = useState(false);
  // The row whose deletion is being confirmed (see `remove`).
  const [confirming, setConfirming] = useState<WorkItemOut | null>(null);
  // The target-less quick note (see `addNote`).
  const [adding, setAdding] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(false);
    setWriteError(null);
    // A question about a row of the previous list must not outlive it.
    setConfirming(null);
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
  const groups: { key: string; heading: string | null; rows: WorkItemOut[] }[] = [
    { key: 'returned', heading: t.korbReturned, rows: rows.filter((i) => i.status === 'returned') },
    { key: 'open', heading: null, rows: rows.filter((i) => i.status === 'open') },
    { key: 'ack', heading: t.korbInProgress, rows: rows.filter((i) => i.status === 'ack') },
    { key: 'done', heading: t.korbDoneHeading, rows: showDone ? rows.filter((i) => i.status === 'done') : [] },
  ];
  const openCount = rows.filter((i) => i.status === 'open' || i.status === 'returned').length;
  const doneCount = rows.filter((i) => i.status === 'done').length;
  const visibleCount = groups.reduce((n, g) => n + g.rows.length, 0);

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
        <IconButton size="small" aria-label={t.korbTitle} onClick={() => setExpanded((v) => !v)}>
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
              <Button size="small" variant="contained" onClick={addNote} disabled={savingNote || !noteText.trim()}>
                {t.korbAddSubmit}
              </Button>
              <Button
                size="small"
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
          <Button size="small" startIcon={<AddIcon fontSize="small" />} sx={{ mt: 0.5 }} onClick={() => setAdding(true)}>
            {t.korbAddNote}
          </Button>
        )}
        {writeError && (
          <Alert severity="warning" sx={{ mt: 1 }} onClose={() => setWriteError(null)}>
            {writeError}
          </Alert>
        )}
        {error ? (
          <Alert severity="warning" sx={{ mt: 1 }}>
            {t.korbLoadError}
          </Alert>
        ) : visibleCount === 0 ? (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {t.korbEmpty}
          </Typography>
        ) : (
          <Box sx={{ mt: 1 }}>
            {groups
              .filter((g) => g.rows.length > 0)
              .map((g) => (
                <Box key={g.key}>
                  {g.heading && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      {g.heading}
                    </Typography>
                  )}
                  {g.rows.map((item) => {
                    const url = workItemUrl(item);
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
            control={<Switch size="small" checked={showDone} onChange={(e) => setShowDone(e.target.checked)} />}
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
          <Button onClick={() => setConfirming(null)}>{t.cancel}</Button>
          <Button color="error" variant="contained" onClick={() => confirming && remove(confirming)}>
            {t.korbDeleteConfirmSubmit}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
