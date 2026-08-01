// The Auftragskorb (optimierungs-werkbank.md §5): the filed work_items of the
// active source, grouped by where they stand in the handling protocol. Open
// items are the round's queue a working session reads at start; an acked one
// carries the session's restatement — what it understood the task to be and
// whether it could reproduce it — written BEFORE it changes anything, so a
// misunderstanding surfaces early and can be rejected here with one click.
// Returned items sit on top: those need the author, not the algorithm. Done
// ones stay behind a toggle with their diagnosed stage and resolution, which
// is what makes the archive worth keeping. Deliberately a card at the top of
// the right column, not the mockup's floating panel — a fixed overlay would
// cover the very words the admin is judging.

import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  FormControlLabel,
  IconButton,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';

import { deleteWorkItem, listWorkItems, patchWorkItem } from '@/lib/api';
import type { WorkItemOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';

// "Buchstabe a" / "Übergang d→a" / "Wort einen" — the level plus its target.
function workItemLabel(item: WorkItemOut): string {
  const t = de.admin.werkbank;
  if (item.kind === 'letter') return `${t.kindLetter} ${item.glyph_key ?? '?'}`;
  if (item.kind === 'pair') return `${t.kindPair} ${item.left_key ?? '?'}→${item.right_key ?? '?'}`;
  return `${t.kindWord} ${item.word ?? item.specimen_id ?? '?'}`;
}

function ItemRow({
  item,
  onDelete,
  onReject,
}: {
  item: WorkItemOut;
  onDelete: () => void;
  onReject: (correction: string) => void;
}) {
  const t = de.admin.werkbank;
  const [rejecting, setRejecting] = useState(false);
  const [correction, setCorrection] = useState('');

  return (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, py: 0.5, borderTop: 1, borderColor: 'divider' }}>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {workItemLabel(item)}
          {item.specimen_id && (
            <Typography component="span" variant="caption" color="text.secondary">
              {` · ${item.specimen_id}`}
            </Typography>
          )}
        </Typography>
        {item.note && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', whiteSpace: 'pre-line' }}>
            {item.note}
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

export function KorbPanel({ sourceId, refreshKey }: { sourceId: string; refreshKey: number }) {
  const t = de.admin.werkbank;
  const [items, setItems] = useState<WorkItemOut[] | null>(null);
  const [error, setError] = useState(false);
  const [writeError, setWriteError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [showDone, setShowDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(false);
    setWriteError(null);
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
  const mutate = (
    item: WorkItemOut,
    apply: (row: WorkItemOut) => WorkItemOut,
    call: () => Promise<unknown>,
    message: string,
  ) => {
    setWriteError(null);
    setItems((prev) => (prev ?? []).map((i) => (i.id === item.id ? apply(i) : i)));
    call().catch(() => {
      restore(item);
      setWriteError(message);
    });
  };

  // Single click, no confirm: deleting a MISFILING is cheap and this is the
  // admin's own basket (a worked item is closed with `done` instead).
  const remove = (item: WorkItemOut) => {
    setWriteError(null);
    setItems((prev) => (prev ?? []).filter((i) => i.id !== item.id));
    deleteWorkItem(sourceId, item.id).catch(() => {
      restore(item);
      setWriteError(t.korbDeleteError);
    });
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
                  {g.rows.map((item) => (
                    <ItemRow
                      key={item.id}
                      item={item}
                      onDelete={() => remove(item)}
                      onReject={(correction) => reject(item, correction)}
                    />
                  ))}
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
    </Box>
  );
}
