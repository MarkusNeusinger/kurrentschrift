// The Lupe — the one way to look at a strip larger than the shared zoom shows
// it, without changing what the surface behind it is set to.

import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Slider,
  Stack,
  Typography,
} from '@mui/material';
import { useState } from 'react';

import { de } from '@/locales/admin';
import { LUPE_ZOOMS } from '@/sections/admin/eigenhand/stripZoom';
import { paper } from '@/styles/paper';

export type LupeTarget = {
  url: string;
  title: string;
  heightPx: number;
};

/** The Lupe: one image at any magnification, panned by scrolling. */
export function Lupe({ target, onClose }: { target: LupeTarget | null; onClose: () => void }) {
  const t = de.admin.eigenhand;
  const [zoom, setZoom] = useState(2);
  return (
    <Dialog open={target !== null} onClose={onClose} fullWidth maxWidth="xl">
      {target && (
        <>
          <DialogTitle sx={{ pb: 0 }}>{target.title}</DialogTitle>
          <DialogContent>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center', my: 1 }}>
              <Typography variant="caption" sx={{ color: paper.inkSoft, whiteSpace: 'nowrap' }}>
                {t.stripZoom} {zoom}×
              </Typography>
              <Slider
                size="small"
                min={LUPE_ZOOMS.min}
                max={LUPE_ZOOMS.max}
                step={LUPE_ZOOMS.step}
                value={zoom}
                onChange={(_e, value) => setZoom(Array.isArray(value) ? value[0] : value)}
                sx={{ maxWidth: '20rem' }}
                aria-label={t.stripZoom}
              />
            </Stack>
            <Box sx={{ overflow: 'auto', maxHeight: '75vh', bgcolor: paper.hi, borderRadius: 1 }}>
              <Box
                component="img"
                src={target.url}
                alt={target.title}
                sx={{ display: 'block', maxWidth: 'none', height: `${target.heightPx * zoom}px` }}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>{t.stripLupeClose}</Button>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
}
