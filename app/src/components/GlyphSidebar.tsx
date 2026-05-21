// Sidebar — one click activates + shows. Iterates over the KNOWN_GLYPHS list
// (the v1 MVP target set), looking up bboxes and traced-canonical status
// from the admin state.

import CircleIcon from '@mui/icons-material/Circle';
import EditIcon from '@mui/icons-material/Edit';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import {
  Box,
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Tooltip,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { KNOWN_GLYPHS } from '../constants';
import { useAdmin } from '../state';

export function GlyphSidebar() {
  const { source, bboxesByKey, glyphsByKey, activeGlyph, visibleGlyphs, toggleVisible, setOnlyVisible, setActiveGlyph } =
    useAdmin();
  const navigate = useNavigate();

  if (!source) return null;
  const keysWithBbox = KNOWN_GLYPHS.filter((g) => g.key in bboxesByKey).map((g) => g.key);

  const activateGlyph = (k: string) => {
    setActiveGlyph(k);
    if (!visibleGlyphs.has(k)) toggleVisible(k);
  };

  return (
    <Box sx={{ borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Box sx={{ p: 2, pb: 0.5 }}>
        <Typography variant="overline" color="text.secondary">
          {source.title}
        </Typography>
        <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
          {source.style_ratio.join(':')} · slant {source.slant_deg}°
        </Typography>
      </Box>
      <Box sx={{ px: 2, py: 1, display: 'flex', gap: 1 }}>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible(keysWithBbox)}>
          alle
        </Button>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible([])}>
          keine
        </Button>
      </Box>
      <Divider />
      <List dense sx={{ flex: 1, overflowY: 'auto', py: 0 }}>
        {KNOWN_GLYPHS.map((kg) => {
          const k = kg.key;
          const hasBbox = k in bboxesByKey;
          const hasCanon = glyphsByKey[k]?.has_data === true;
          const visible = visibleGlyphs.has(k);
          const isActive = activeGlyph === k;
          return (
            <ListItem
              key={k}
              disablePadding
              secondaryAction={
                <Tooltip title="Editor öffnen">
                  <span>
                    <IconButton
                      size="small"
                      edge="end"
                      onClick={() => {
                        activateGlyph(k);
                        navigate(`/edit/${encodeURIComponent(k)}`);
                      }}
                      disabled={!hasBbox}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
              }
              sx={{
                bgcolor: isActive ? 'action.selected' : 'transparent',
                borderLeft: '3px solid',
                borderLeftColor: isActive ? 'primary.main' : 'transparent',
              }}
            >
              <ListItemButton onClick={() => activateGlyph(k)} sx={{ py: 0.5 }}>
                <Box sx={{ width: 26, display: 'flex', alignItems: 'center', color: visible ? 'secondary.main' : 'text.disabled' }}>
                  {visible ? <VisibilityIcon fontSize="small" /> : <VisibilityOffIcon fontSize="small" />}
                </Box>
                <Box
                  sx={{
                    width: 22,
                    display: 'flex',
                    alignItems: 'center',
                    color: hasCanon ? 'success.main' : hasBbox ? 'text.secondary' : 'text.disabled',
                  }}
                >
                  {hasCanon ? (
                    <TaskAltIcon fontSize="small" />
                  ) : hasBbox ? (
                    <CircleIcon sx={{ fontSize: 10 }} />
                  ) : (
                    <RadioButtonUncheckedIcon fontSize="small" />
                  )}
                </Box>
                <ListItemText
                  primary={kg.label}
                  secondary={k}
                  slotProps={{
                    primary: {
                      sx: {
                        fontFamily: 'ui-monospace, Menlo, monospace',
                        fontSize: 13,
                        color: hasBbox ? 'text.primary' : 'text.disabled',
                      },
                    },
                    secondary: { sx: { fontSize: 10, fontFamily: 'ui-monospace, Menlo, monospace' } },
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
}
