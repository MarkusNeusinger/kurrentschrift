// Sidebar — navigation + a letter grid. Letters are grouped (lowercase /
// uppercase / combinations); the initial/medial/final position is hidden until
// a letter is selected, then offered as a toggle in the panel at the bottom.
// One click on a letter activates it (and a sensible default position) and
// makes its bboxes visible on the chart.
//
// The sidebar is pure selection/navigation: Einrichten · Diagnose · Sperren all
// act on the active glyph and live in ONE place — the chart toolbar. Picking a
// letter (or a position for a split letter) here just sets the active glyph the
// toolbar then operates on.

import GridViewIcon from '@mui/icons-material/GridView';
import HomeIcon from '@mui/icons-material/Home';
import JoinInnerIcon from '@mui/icons-material/JoinInner';
import LockIcon from '@mui/icons-material/Lock';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';
import {
  Box,
  Button,
  ButtonBase,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { glyphKeyFor, isLetterSplit, LETTERS, LETTER_BY_KEY, POSITIONS } from '@/domain/glyphs';
import type { Letter, LetterGroup, Position } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { de, POSITION_LABEL, styleLabel } from '@/locales/admin';

const GROUP_LABELS: Record<LetterGroup, string> = {
  lower: de.admin.sidebar.groupLower,
  upper: de.admin.sidebar.groupUpper,
  comb: de.admin.sidebar.groupComb,
  digit: de.admin.sidebar.groupDigit,
  punct: de.admin.sidebar.groupPunct,
};
const GROUP_ORDER: LetterGroup[] = ['lower', 'upper', 'comb', 'digit', 'punct'];

export function GlyphSidebar({ onNavigate }: { onNavigate?: () => void } = {}) {
  const { source, sourceId, sources, switchSource, bboxesByKey, glyphsByKey, activeGlyph, visibleGlyphs, toggleVisible, setOnlyVisible, setActiveGlyph } =
    useAdmin();
  const navigate = useNavigate();
  const [openBase, setOpenBase] = useState<string | null>(null);

  // On mobile the sidebar lives in a Drawer; navigating away should close it.
  const go = (path: string) => {
    navigate(path);
    onNavigate?.();
  };

  // Keep the open letter in sync when the active glyph changes elsewhere (e.g.
  // when the editor route sets it on load).
  useEffect(() => {
    if (activeGlyph && LETTER_BY_KEY[activeGlyph]) setOpenBase(LETTER_BY_KEY[activeGlyph].base);
  }, [activeGlyph]);

  if (!source) return null;

  const hasBbox = (key: string) => key in bboxesByKey;
  const hasCanon = (key: string) => glyphsByKey[key]?.has_data === true;
  const isLocked = (key: string) => bboxesByKey[key]?.locked === true;

  const activatePosition = (letter: Letter, pos: Position) => {
    const key = glyphKeyFor(letter, pos);
    setActiveGlyph(key);
    if (!visibleGlyphs.has(key)) toggleVisible(key);
  };

  const selectLetter = (letter: Letter) => {
    setOpenBase(letter.base);
    // Prefer a position that already has data, then one with a bbox, else medial.
    const pos =
      POSITIONS.find((p) => hasCanon(glyphKeyFor(letter, p))) ??
      POSITIONS.find((p) => hasBbox(glyphKeyFor(letter, p))) ??
      'medial';
    activatePosition(letter, pos);
    // On mobile, a unified letter has nothing left to choose — close the drawer
    // so the chart toolbar (the action hub) is reachable for the active glyph.
    // A split letter keeps the drawer open so its position can be picked first;
    // the position rows close it on tap. onNavigate is a no-op on desktop.
    if (!isLetterSplit(glyphKeyFor(letter, 'medial'), bboxesByKey)) onNavigate?.();
  };

  const openLetter = openBase ? (LETTERS.find((l) => l.base === openBase) ?? null) : null;
  const keysWithBbox = Object.keys(bboxesByKey);

  return (
    <Box sx={{ borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* Navigation — get back out of the admin area / over to the overview. */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, px: 1, py: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Tooltip title={de.admin.sidebar.toHome}>
          <IconButton size="small" onClick={() => go('/')}>
            <HomeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Typography
          variant="subtitle2"
          sx={{ flex: 1, cursor: 'pointer', fontWeight: 600 }}
          onClick={() => go('/')}
        >
          {de.common.brand.name}
        </Typography>
        <Tooltip title={de.admin.sidebar.compareOverview}>
          <IconButton size="small" aria-label={de.admin.sidebar.compareOverview} onClick={() => go('/admin/vergleich')}>
            <ViewColumnIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={de.admin.sidebar.pairsOverview}>
          <IconButton size="small" aria-label={de.admin.sidebar.pairsOverview} onClick={() => go('/admin/paare')}>
            <JoinInnerIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={de.admin.sidebar.chartOverview}>
          <IconButton size="small" onClick={() => go('/admin/chart')}>
            <GridViewIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Box sx={{ p: 2, pb: 0.5 }}>
        <TextField
          select
          fullWidth
          size="small"
          variant="standard"
          label={de.admin.sidebar.sourceLabel}
          value={sourceId}
          onChange={(e) => switchSource(e.target.value)}
        >
          {sources.map((s) => (
            <MenuItem key={s.id} value={s.id}>
              {styleLabel(s.style_id)}
            </MenuItem>
          ))}
        </TextField>
        <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>
          {source.style_ratio.join(':')} · slant {source.slant_deg}°
        </Typography>
      </Box>
      <Box sx={{ px: 2, py: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
          {de.admin.sidebar.overlays}
        </Typography>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible(keysWithBbox)}>
          {de.admin.sidebar.all}
        </Button>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible([])}>
          {de.admin.sidebar.none}
        </Button>
      </Box>
      <Divider />

      {/* Letter grid — every letter, status dot in the corner. `scrollbarGutter:
          stable` always reserves the scrollbar's width, so selecting a letter
          (which adds the panel below and can push the grid into overflow) never
          shifts the flex-wrap grid from a scrollbar popping in. */}
      <Box sx={{ flex: 1, overflowY: 'auto', scrollbarGutter: 'stable', px: 2, py: 1 }}>
        {GROUP_ORDER.map((group) => {
          const letters = LETTERS.filter((l) => l.group === group);
          if (letters.length === 0) return null;
          return (
            <Box key={group} sx={{ mb: 2 }}>
              <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                {GROUP_LABELS[group]}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                {letters.map((letter) => {
                  const canon = POSITIONS.some((p) => hasCanon(glyphKeyFor(letter, p)));
                  const bbox = POSITIONS.some((p) => hasBbox(glyphKeyFor(letter, p)));
                  const locked = POSITIONS.some((p) => isLocked(glyphKeyFor(letter, p)));
                  const split = isLetterSplit(glyphKeyFor(letter, 'medial'), bboxesByKey);
                  const isOpen = openBase === letter.base;
                  return (
                    <Tooltip
                      key={letter.base}
                      title={`${letter.glyph}${letter.note ? ` · ${letter.note}` : ''}${
                        canon ? de.admin.sidebar.statusCanonical : bbox ? de.admin.sidebar.statusBbox : de.admin.sidebar.statusEmpty
                      }${locked ? de.admin.sidebar.statusLocked : ''}${split ? de.admin.sidebar.statusSplit : ''}`}
                    >
                      <ButtonBase
                        onClick={() => selectLetter(letter)}
                        sx={{
                          position: 'relative',
                          width: 34,
                          height: 34,
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: isOpen ? 'primary.main' : 'divider',
                          bgcolor: isOpen ? 'action.selected' : 'transparent',
                          fontFamily: 'Georgia, "Times New Roman", serif',
                          fontSize: letter.glyph.length > 1 ? 14 : 19,
                          lineHeight: 1,
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
                        {/* Split marker (top-left, distinct from the status dot):
                            this letter is authored per-position (aufgetrennt). */}
                        {split && (
                          <Box
                            sx={{
                              position: 'absolute',
                              top: 1,
                              left: 2,
                              fontSize: 9,
                              lineHeight: 1,
                              fontWeight: 700,
                              color: 'info.main',
                            }}
                          >
                            ⫶
                          </Box>
                        )}
                        {locked && (
                          <LockIcon
                            sx={{ position: 'absolute', bottom: 1, right: 1, fontSize: 10, color: 'success.main' }}
                          />
                        )}
                      </ButtonBase>
                    </Tooltip>
                  );
                })}
              </Box>
            </Box>
          );
        })}
      </Box>

      {/* Letter panel — shown once a letter is selected. Pure selection: it sets
          the active glyph the chart toolbar acts on (Einrichten · Diagnose ·
          Sperren all live there). A unified letter (the default) hides position
          entirely; a split letter (aufgetrennt) lists its three positions so
          each can be picked on its own. */}
      {openLetter &&
        (() => {
          const letter = openLetter;
          const split = isLetterSplit(glyphKeyFor(letter, 'medial'), bboxesByKey);
          return (
            <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 1 }}>
                <Typography sx={{ fontFamily: 'Georgia, serif', fontSize: 22, lineHeight: 1 }}>{letter.glyph}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {split ? de.admin.sidebar.splitCaption : de.admin.sidebar.unifiedCaption}
                  {letter.note ? ` · ${letter.note}` : ''}
                </Typography>
              </Box>

              {split && (
                <Stack spacing={0.5} sx={{ mb: 1 }}>
                  {POSITIONS.map((p) => {
                    const key = glyphKeyFor(letter, p);
                    const canon = hasCanon(key);
                    const bbox = hasBbox(key);
                    const locked = isLocked(key);
                    const selected = activeGlyph === key;
                    return (
                      <ButtonBase
                        key={p}
                        onClick={() => {
                          activatePosition(letter, p);
                          // Mobile: position picked → close the drawer so the
                          // toolbar is reachable (no-op on desktop).
                          onNavigate?.();
                        }}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          justifyContent: 'flex-start',
                          border: '1px solid',
                          borderColor: selected ? 'primary.main' : 'divider',
                          bgcolor: selected ? 'action.selected' : 'transparent',
                          borderRadius: 1,
                          px: 1,
                          py: 0.5,
                          '&:hover': { borderColor: 'primary.light', bgcolor: 'action.hover' },
                        }}
                      >
                        <Box
                          sx={{
                            width: 6,
                            height: 6,
                            borderRadius: '50%',
                            bgcolor: canon ? 'success.main' : bbox ? 'warning.main' : 'transparent',
                            border: canon || bbox ? 'none' : '1px solid',
                            borderColor: 'divider',
                          }}
                        />
                        <Typography variant="caption" sx={{ flex: 1, textAlign: 'left' }}>
                          {POSITION_LABEL[p]}
                          {locked ? ' 🔒' : ''}
                        </Typography>
                      </ButtonBase>
                    );
                  })}
                </Stack>
              )}

              {/* Where the actions are. The toolbar's buttons gate themselves on
                  bbox/lock; the sidebar only flags the two cases that block them. */}
              {activeGlyph && !hasBbox(activeGlyph) ? (
                <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
                  {de.admin.sidebar.noBboxHint}
                </Typography>
              ) : activeGlyph && isLocked(activeGlyph) ? (
                <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
                  {de.admin.sidebar.lockedHint}
                </Typography>
              ) : (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {de.admin.sidebar.actionsHint}
                </Typography>
              )}
            </Box>
          );
        })()}
    </Box>
  );
}
