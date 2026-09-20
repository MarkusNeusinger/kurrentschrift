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

import { useAdmin } from '@/context/adminState';
import { LETTERS, glyphKeyFor } from '@/domain/glyphs';
import type { Letter, LetterGroup } from '@/domain/glyphs';
import { de } from '@/locales/admin';
import { TOUCH_TARGET } from '@/styles/hitArea';

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
    // Wider on a real screen than it was: 44 px cells 6 px apart need 50 px of
    // track each, and at the old 360 the alphabet fell to six per row and the
    // popover grew a scrollbar. 420 keeps seven and fits every desktop and
    // tablet; a phone keeps the narrow box, where six per row is right anyway.
    <Box sx={{ p: 1.5, maxWidth: { xs: 320, sm: 420 } }}>
      {GROUP_ORDER.map((group) => {
        const letters = LETTERS.filter((l) => l.group === group);
        if (letters.length === 0) return null;
        return (
          <Box key={group} sx={{ mb: 1.5 }}>
            <Typography variant="overline" color="textSecondary" sx={{ display: 'block', mb: 0.5 }}>
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
                // The cell's whole state in words. The dot is a COLOUR (green =
                // canonical, orange = bbox only) and the tooltip was its only
                // wording — so for a colour-blind or keyboard reader the grid
                // said nothing. As the button's accessible name it is read out
                // on focus and on tap, and the tooltip stays for the mouse
                // (design-system.md §9, §9.4).
                const status = `${letter.glyph}${letter.note ? ` · ${letter.note}` : ''}${
                  canon ? t.statusCanonical : bbox ? t.statusBbox : t.statusEmpty
                }${locked ? t.statusLocked : ''}`;
                return (
                  <Tooltip key={letter.base} title={status}>
                    {/* A disabled ButtonBase swallows the tooltip's events — the
                        span keeps the hint readable either way. */}
                    <span>
                      <ButtonBase
                        onClick={() => onPick(key)}
                        aria-label={status}
                        disabled={disabled}
                        sx={{
                          position: 'relative',
                          // The grid's cells tile 6 px apart, so they GROW to
                          // the floor rather than wearing overlays that would
                          // steal each other's taps (§9.3). They escaped the
                          // route sweep because the popover is closed while a
                          // route is measured — found by hand, 2026-09-19.
                          width: TOUCH_TARGET,
                          height: TOUCH_TARGET,
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
                          // Two states, two CHANNELS. The dot used to differ in
                          // hue alone — green = canonical, orange = nur Bbox —
                          // which a deuteranope cannot separate at 7 px, and it
                          // was §9.4's one open case. Now the canonical dot is
                          // FILLED and the bbox-only one a hollow ring of the
                          // same size, so shape carries the state and the
                          // colour only reinforces it. Grown to 8 px: a 1.5 px
                          // ring inside 7 px left a hole of 4 px.
                          <Box
                            sx={{
                              position: 'absolute',
                              top: 2,
                              right: 2,
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              boxSizing: 'border-box',
                              border: canon ? 'none' : '1.5px solid',
                              borderColor: 'warning.main',
                              bgcolor: canon ? 'success.main' : 'transparent',
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
