// The Auftragskorb (optimierungs-werkbank.md §5): the filed work_items of the
// active source. Open items are the round's queue a working session reads at
// start; done ones stay behind a toggle with their resolution, so the archive
// says which stage was diagnosed and what changed. Deliberately a card at the
// top of the right column, not the mockup's floating panel — a fixed overlay
// would cover the very words the admin is judging.

import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import { Alert, Box, Collapse, FormControlLabel, IconButton, Switch, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { deleteWorkItem, listWorkItems } from '@/lib/api';
import type { WorkItemOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';

// "Buchstabe a" / "Übergang d→a" / "Wort einen" — the level plus its target.
function workItemLabel(item: WorkItemOut): string {
  const t = de.admin.werkbank;
  if (item.kind === 'letter') return `${t.kindLetter} ${item.glyph_key ?? '?'}`;
  if (item.kind === 'pair') return `${t.kindPair} ${item.left_key ?? '?'}→${item.right_key ?? '?'}`;
  return `${t.kindWord} ${item.word ?? item.specimen_id ?? '?'}`;
}

function ItemRow({ item, onDelete }: { item: WorkItemOut; onDelete: () => void }) {
  const t = de.admin.werkbank;
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
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            {item.note}
          </Typography>
        )}
        {item.status === 'done' && item.resolution && (
          <Typography variant="caption" color="success.main" sx={{ display: 'block' }}>
            {item.resolution}
          </Typography>
        )}
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
  const [expanded, setExpanded] = useState(true);
  const [showDone, setShowDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(false);
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

  const open = (items ?? []).filter((i) => i.status === 'open');
  const done = (items ?? []).filter((i) => i.status === 'done');
  const visible = showDone ? [...open, ...done] : open;

  // Single click, no confirm: deleting a MISFILING is cheap and this is the
  // admin's own basket (a worked item is closed with `done` instead).
  const remove = (id: number) => {
    setItems((prev) => (prev ?? []).filter((i) => i.id !== id));
    deleteWorkItem(sourceId, id).catch(() => setError(true));
  };

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 2, bgcolor: 'background.paper', p: 1.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          {`⚑ ${t.korbTitle} (${fmt(t.korbOpenCount, { count: open.length })})`}
        </Typography>
        <IconButton size="small" aria-label={t.korbTitle} onClick={() => setExpanded((v) => !v)}>
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        {error ? (
          <Alert severity="warning" sx={{ mt: 1 }}>
            {t.korbLoadError}
          </Alert>
        ) : visible.length === 0 ? (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {t.korbEmpty}
          </Typography>
        ) : (
          <Box sx={{ mt: 1 }}>
            {visible.map((item) => (
              <ItemRow key={item.id} item={item} onDelete={() => remove(item.id)} />
            ))}
          </Box>
        )}
        {done.length > 0 && (
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
