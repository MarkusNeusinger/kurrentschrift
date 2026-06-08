// Sidebar — navigation + a letter grid. Letters are grouped (lowercase /
// uppercase / combinations); the initial/medial/final position is hidden until
// a letter is selected, then offered as a toggle in the panel at the bottom.
// One click on a letter activates it (and a sensible default position) and
// makes its bboxes visible on the chart.

import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import GridViewIcon from '@mui/icons-material/GridView';
import HomeIcon from '@mui/icons-material/Home';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Box,
  Button,
  ButtonBase,
  Divider,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { glyphKeyFor, LETTERS, LETTER_BY_KEY, POSITIONS } from '../constants';
import type { Letter, LetterGroup, Position } from '../constants';
import { useAdmin } from '../state';

const GROUP_LABELS: Record<LetterGroup, string> = {
  lower: 'Kleinbuchstaben',
  upper: 'Großbuchstaben',
  comb: 'Kombinationen',
};
const GROUP_ORDER: LetterGroup[] = ['lower', 'upper', 'comb'];

export function GlyphSidebar({ onNavigate }: { onNavigate?: () => void } = {}) {
  const { source, bboxesByKey, glyphsByKey, activeGlyph, visibleGlyphs, toggleVisible, setOnlyVisible, setActiveGlyph, openWizard, openDiagnose } =
    useAdmin();
  const navigate = useNavigate();
  const [openBase, setOpenBase] = useState<string | null>(null);

  // On mobile the sidebar lives in a Drawer; navigating away should close it.
  const go = (path: string) => {
    navigate(path);
    onNavigate?.();
  };

  // The wizard / diagnose modals are mounted in AppLayout; opening one also
  // closes the mobile drawer so the full width is free.
  const launchWizard = () => {
    if (!activeGlyph) return;
    openWizard(activeGlyph);
    onNavigate?.();
  };
  const launchDiagnose = () => {
    if (!activeGlyph) return;
    openDiagnose(activeGlyph);
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
  };

  const openLetter = openBase ? (LETTERS.find((l) => l.base === openBase) ?? null) : null;
  const activePos: Position | null =
    openLetter && activeGlyph
      ? (POSITIONS.find((p) => glyphKeyFor(openLetter, p) === activeGlyph) ?? null)
      : null;
  const keysWithBbox = Object.keys(bboxesByKey);

  return (
    <Box sx={{ borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* Navigation — get back out of the admin area / over to the overview. */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, px: 1, py: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Tooltip title="Zur Startseite">
          <IconButton size="small" onClick={() => go('/')}>
            <HomeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Typography
          variant="subtitle2"
          sx={{ flex: 1, cursor: 'pointer', fontWeight: 600 }}
          onClick={() => go('/')}
        >
          kurrentschrift
        </Typography>
        <Tooltip title="Chart-Übersicht">
          <IconButton size="small" onClick={() => go('/admin/chart')}>
            <GridViewIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Box sx={{ p: 2, pb: 0.5 }}>
        <Typography variant="overline" color="text.secondary">
          {source.title}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
          {source.style_ratio.join(':')} · slant {source.slant_deg}°
        </Typography>
      </Box>
      <Box sx={{ px: 2, py: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
          Overlays
        </Typography>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible(keysWithBbox)}>
          alle
        </Button>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible([])}>
          keine
        </Button>
      </Box>
      <Divider />

      {/* Letter grid — every letter, status dot in the corner. */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 2, py: 1 }}>
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
                  const isOpen = openBase === letter.base;
                  return (
                    <Tooltip
                      key={letter.base}
                      title={`${letter.glyph}${letter.note ? ` · ${letter.note}` : ''}${
                        canon ? ' · Canonical vorhanden' : bbox ? ' · Bbox gesetzt' : ' · leer'
                      }${locked ? ' · gesperrt (fertig)' : ''}`}
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

      {/* Position panel — only shown once a letter is selected. */}
      {openLetter && (
        <Box sx={{ borderTop: 1, borderColor: 'divider', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 1 }}>
            <Typography sx={{ fontFamily: 'Georgia, serif', fontSize: 22, lineHeight: 1 }}>{openLetter.glyph}</Typography>
            <Typography variant="caption" color="text.secondary">
              Position {openLetter.note ? `· ${openLetter.note}` : ''}
            </Typography>
          </Box>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={activePos}
            onChange={(_e, p: Position | null) => p && activatePosition(openLetter, p)}
            fullWidth
          >
            {POSITIONS.map((p) => {
              const key = glyphKeyFor(openLetter, p);
              const canon = hasCanon(key);
              const bbox = hasBbox(key);
              return (
                <ToggleButton key={p} value={p} sx={{ textTransform: 'none', flexDirection: 'column', gap: 0.25, py: 0.5 }}>
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
                  <Typography variant="caption">{p}</Typography>
                </ToggleButton>
              );
            })}
          </ToggleButtonGroup>
          <Button
            fullWidth
            size="small"
            variant="contained"
            startIcon={<AutoFixHighIcon />}
            disabled={!activeGlyph || !hasBbox(activeGlyph) || isLocked(activeGlyph)}
            onClick={launchWizard}
            sx={{ mt: 1.5 }}
          >
            Einrichten
          </Button>
          {activeGlyph && hasCanon(activeGlyph) && (
            <Button
              fullWidth
              size="small"
              variant="outlined"
              startIcon={<VisibilityIcon />}
              onClick={launchDiagnose}
              sx={{ mt: 1 }}
            >
              Diagnose
            </Button>
          )}
          {activeGlyph && !hasBbox(activeGlyph) && (
            <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1 }}>
              Noch keine Bbox — im Modus „Bbox“ ein Rechteck auf der Vorlage ziehen.
            </Typography>
          )}
          {activeGlyph && hasBbox(activeGlyph) && isLocked(activeGlyph) && (
            <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1 }}>
              🔒 Gesperrt (fertig) — oben in der Leiste entsperren, um zu bearbeiten.
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
}
