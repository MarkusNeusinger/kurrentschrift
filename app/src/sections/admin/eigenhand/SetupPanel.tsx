// The hand's standing setup — nib, ink, paper, capture device.
//
// Ink, paper and nib are photometric parameters of a whole campaign, not
// details of one import: change them mid-campaign and the corpus splits into
// cohorts that cannot be compared on stroke width or darkness. Typed once
// here, they become the default `ingest` reads back; what a session actually
// used is recorded again on every Fassung, so a real change shows as a visible
// break in the data instead of something to reconstruct.
//
// This is deliberately a plain overwrite, not a new cohort row: the panel
// answers „what do I reach for now".

import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { getEigenhandSetup, putEigenhandSetup } from '@/lib/api';
import type { EigenhandSetup } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de, fmt } from '@/locales/admin';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

type Draft = { label: string; feder: string; tinte: string; papier: string; geraet: string; note: string };

const EMPTY: Draft = { label: '', feder: '', tinte: '', papier: '', geraet: 'scanner', note: '' };

const toDraft = (setup: EigenhandSetup | null): Draft =>
  setup
    ? {
        label: setup.label ?? '',
        feder: setup.feder ?? '',
        tinte: setup.tinte ?? '',
        papier: setup.papier ?? '',
        geraet: setup.geraet ?? 'scanner',
        note: setup.note ?? '',
      }
    : EMPTY;

export function SetupPanel({ hand }: { hand: string }) {
  const t = de.admin.eigenhand;
  const [setup, setSetup] = useState<EigenhandSetup | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiErrorText | null>(null);

  // `loaded` gates the form on the hand it belongs to. Without it a failed or
  // in-flight load left the PREVIOUS hand's values on screen under the new
  // hand's name — and one click on „Setup sichern" would have written them
  // into that hand's record, or blanked it with nulls.
  const [loaded, setLoaded] = useState<string | null>(null);

  // Emptying the form for the next hand happens DURING RENDER — React's
  // "adjusting state when a prop changes" (react-hooks/set-state-in-effect) —
  // so the previous hand's values never reach the screen under the new name,
  // not even for the frame between the render and the effect below.
  const [shownFor, setShownFor] = useState(hand);
  if (shownFor !== hand) {
    setShownFor(hand);
    setError(null);
    setLoaded(null);
    setSetup(null);
    setDraft(EMPTY);
  }

  useEffect(() => {
    let cancelled = false;
    getEigenhandSetup(hand)
      .then((data) => {
        if (cancelled) return;
        setSetup(data);
        setDraft(toDraft(data));
        setLoaded(hand);
      })
      .catch((err: unknown) => !cancelled && setError(apiErrorText(err)));
    return () => {
      cancelled = true;
    };
  }, [hand]);

  const save = () => {
    setSaving(true);
    setError(null);
    // Every field travels on every save: the API replaces the record, so
    // sending only what changed would blank the rest.
    putEigenhandSetup(hand, {
      label: draft.label || null,
      feder: draft.feder || null,
      tinte: draft.tinte || null,
      papier: draft.papier || null,
      geraet: draft.geraet || null,
      note: draft.note || null,
    })
      .then((data) => setSetup(data))
      .catch((err: unknown) => setError(apiErrorText(err)))
      .finally(() => setSaving(false));
  };

  const field = (key: keyof Draft, label: string, width: string) => (
    <TextField
      size="small"
      label={label}
      value={draft[key]}
      onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
      sx={{ width }}
    />
  );

  return (
    <Panel title={t.setupTitle} caption={t.setupIntro}>
      {loaded === hand && !setup && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t.setupNone}
        </Alert>
      )}
      <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', rowGap: 2, alignItems: 'center' }}>
        {field('feder', t.setupFeder, '16rem')}
        {field('tinte', t.setupTinte, '16rem')}
        {field('papier', t.setupPapier, '18rem')}
        <TextField
          select
          size="small"
          label={t.setupGeraet}
          value={draft.geraet}
          onChange={(e) => setDraft({ ...draft, geraet: e.target.value })}
          sx={{ width: '11rem' }}
        >
          <MenuItem value="scanner">scanner</MenuItem>
          <MenuItem value="kamera">kamera</MenuItem>
        </TextField>
        {field('label', t.setupLabel, '14rem')}
        {field('note', t.setupNote, '20rem')}
        <Button variant="outlined" onClick={save} disabled={saving || loaded !== hand}>
          {saving ? t.setupSaving : t.setupSave}
        </Button>
      </Stack>

      {error && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <ErrorText error={error} prefix={t.setupError} />
        </Alert>
      )}

      {setup?.updated_at && (
        <Typography variant="caption" sx={{ display: 'block', mt: 1.5, color: paper.inkSoft }}>
          {fmt(t.setupSaved, { stand: setup.updated_at.slice(0, 16).replace('T', ' ') })}
        </Typography>
      )}
      <Box sx={{ mt: 0.5 }}>
        <TerminalCommand lead={t.setupLocal} command={fmt(t.setupLocalCommand, { hand })} />
      </Box>
    </Panel>
  );
}
