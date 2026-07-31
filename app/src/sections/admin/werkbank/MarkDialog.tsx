// Filing one Auftrag (optimierungs-werkbank.md §4/§5). For a LETTER the dialog
// asks the one pre-sort question the doctrine puts on the human — "does the
// letter look wrong on its own too?": yes means the chart ductus is the
// problem, which is the author's own ground truth and belongs in the wizard,
// not in the basket; no means it only breaks inside words, which is algorithm
// territory (Laufform / fit / join grammar / placement) and gets filed. Every
// other triage step stays the working session's duty, not the admin's.

import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';

import { createWorkItem } from '@/lib/api';
import { de } from '@/locales/admin';

import { targetLabel, workItemBodyOf, type Mark } from './model';

interface Props {
  mark: Mark;
  sourceId: string;
  onClose: () => void;
  onFiled: () => void;
  // "Yes, it is wrong on its own" — straight into the wizard, nothing filed.
  onOpenWizard: (glyphKey: string) => void;
}

export function MarkDialog({ mark, sourceId, onClose, onFiled, onOpenWizard }: Props) {
  const t = de.admin.werkbank;
  // Only the letter level has the pre-sort question; pair and word marks are
  // always complaints about generated output and go straight to the note.
  const [presorted, setPresorted] = useState(mark.target.kind !== 'letter');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);

  const submit = () => {
    setSaving(true);
    setError(false);
    createWorkItem(sourceId, workItemBodyOf(mark, note.trim()))
      .then(() => {
        onFiled();
        onClose();
      })
      .catch(() => {
        setSaving(false);
        setError(true);
      });
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t.dialogTitle}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, pt: 0.5 }}>
          <Typography variant="body2">
            <strong>{`${t.dialogTarget}: `}</strong>
            {targetLabel(mark.target)}
            <Typography component="span" variant="caption" color="text.secondary">
              {` · ${t.dialogSeenIn} ${mark.specimen.word} (${mark.specimen.id})`}
            </Typography>
          </Typography>

          {!presorted && mark.target.kind === 'letter' ? (
            <>
              <Typography variant="body2">{t.presortQuestion}</Typography>
              <Typography variant="caption" color="text.secondary">
                {t.presortHint}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  onClick={() => {
                    onOpenWizard(mark.target.kind === 'letter' ? mark.target.glyphKey : '');
                    onClose();
                  }}
                >
                  {t.presortYes}
                </Button>
                <Button variant="contained" onClick={() => setPresorted(true)}>
                  {t.presortNo}
                </Button>
              </Box>
            </>
          ) : (
            <>
              <TextField
                multiline
                minRows={2}
                size="small"
                label={t.noteLabel}
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              {error && <Alert severity="error">{t.submitFailed}</Alert>}
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t.cancel}</Button>
        {presorted && (
          <Button variant="contained" onClick={submit} disabled={saving}>
            {t.submit}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

