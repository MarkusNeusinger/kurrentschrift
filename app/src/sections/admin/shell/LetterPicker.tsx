// The letter grid — no longer a permanent sidebar, but the picker behind the
// current letter's chip. The user's brief was explicit: the letters do not need
// to sit there all the time. So the Buchstaben view shows WHICH letter is under
// inspection, and the grid opens on demand, over the work instead of beside it.
//
// The status dots are unchanged from the old sidebar (green = canonical,
// orange = bbox only, lock = finished), because that reading is what makes the
// grid a progress overview as well as a picker.

import LockIcon from '@mui/icons-material/Lock';
import { Box, ButtonBase, Popover, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { LETTERS, glyphKeyFor } from '@/domain/glyphs';
import type { Letter, LetterGroup } from '@/domain/glyphs';
import { de } from '@/locales/admin';

const GROUP_LABELS: Record<LetterGroup, string> = {
  lower: de.admin.sidebar.groupLower,
  upper: de.admin.sidebar.groupUpper,
  comb: de.admin.sidebar.groupComb,
  digit: de.admin.sidebar.groupDigit,
  punct: de.admin.sidebar.groupPunct,
};
const GROUP_ORDER: LetterGroup[] = ['lower', 'upper', 'comb', 'digit', 'punct'];

export interface LetterGridProps {
  activeKey?: string | null;
  onPick: (glyphKey: string) => void;
  // Letters the caller cannot use (e.g. a lowercase letter on the LEFT of a
  // pair would be fine, but a capital on the right never is): rendered
  // disabled rather than hidden, so the grid keeps its familiar shape.
  isDisabled?: (letter: Letter) => boolean;
}

// The bare grid — used inside the popover and, where a view wants it open
// permanently (the Übergänge left/right pickers), inline.
export function LetterGrid({ activeKey, onPick, isDisabled }: LetterGridProps) {
  const { bboxesByKey, glyphsByKey } = useAdmin();
  const t = de.admin.sidebar;

  return (
    <Box sx={{ p: 1.5, maxWidth: 360 }}>
      {GROUP_ORDER.map((group) => {
        const letters = LETTERS.filter((l) => l.group === group);
        if (letters.length === 0) return null;
        return (
          <Box key={group} sx={{ mb: 1.5 }}>
            <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              {GROUP_LABELS[group]}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
              {letters.map((letter) => {
                const key = glyphKeyFor(letter);
                const canon = glyphsByKey[key]?.has_data === true;
                const bbox = key in bboxesByKey;
                const locked = bboxesByKey[key]?.locked === true;
                const active = activeKey === key;
                const disabled = isDisabled?.(letter) ?? false;
                return (
                  <Tooltip
                    key={letter.base}
                    title={`${letter.glyph}${letter.note ? ` · ${letter.note}` : ''}${
                      canon ? t.statusCanonical : bbox ? t.statusBbox : t.statusEmpty
                    }${locked ? t.statusLocked : ''}`}
                  >
                    {/* A disabled ButtonBase swallows the tooltip's events — the
                        span keeps the hint readable either way. */}
                    <span>
                      <ButtonBase
                        onClick={() => onPick(key)}
                        disabled={disabled}
                        sx={{
                          position: 'relative',
                          width: 34,
                          height: 34,
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: active ? 'primary.main' : 'divider',
                          bgcolor: active ? 'action.selected' : 'transparent',
                          fontFamily: 'Georgia, "Times New Roman", serif',
                          fontSize: letter.glyph.length > 1 ? 14 : 19,
                          lineHeight: 1,
                          opacity: disabled ? 0.35 : 1,
                          color: canon || bbox ? 'text.primary' : 'text.disabled',
                          '&:hover': { borderColor: 'primary.light', bgcolor: 'action.hover' },
                        }}
                      >
                        {letter.glyph}
                        {(canon || bbox) && (
                          <Box
                            sx={{
                              position: 'absolute',
                              top: 2,
                              right: 2,
                              width: 7,
                              height: 7,
                              borderRadius: '50%',
                              bgcolor: canon ? 'success.main' : 'warning.main',
                            }}
                          />
                        )}
                        {locked && (
                          <LockIcon
                            sx={{ position: 'absolute', bottom: 1, right: 1, fontSize: 10, color: 'success.main' }}
                          />
                        )}
                      </ButtonBase>
                    </span>
                  </Tooltip>
                );
              })}
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}

// The grid behind a trigger element (a chip, a button showing the current
// letter). Picking closes the popover — one decision per opening.
export function LetterPicker({
  activeKey,
  onPick,
  isDisabled,
  children,
}: LetterGridProps & { children: (open: (e: React.MouseEvent<HTMLElement>) => void) => React.ReactNode }) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  return (
    <>
      {children((e) => setAnchor(e.currentTarget))}
      <Popover
        open={Boolean(anchor)}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <LetterGrid
          activeKey={activeKey}
          isDisabled={isDisabled}
          onPick={(key) => {
            setAnchor(null);
            onPick(key);
          }}
        />
      </Popover>
    </>
  );
}
