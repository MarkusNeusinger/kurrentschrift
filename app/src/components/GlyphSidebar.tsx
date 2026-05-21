// Sidebar — one click per row does the obvious thing:
//   - Click the row: activate this glyph (also makes it visible if it
//     wasn't yet). The active glyph is what bbox/exclude drags on the
//     chart target, and what the editor page opens.
//   - Click the edit icon on the right: same as row click + navigate
//     to the editor page.
//   - Bulk visibility: the "alle / keine" buttons at the top.
//
// Status column shows two pieces of info:
//   - whether this glyph is currently visible on the chart (filled vs
//     hollow circle on the left)
//   - whether the canonical has been traced (check vs hollow circle)

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
import { useAdmin } from '../state';

export function GlyphSidebar() {
  const {
    bboxes,
    activeGlyph,
    visibleGlyphs,
    canonStatus,
    toggleVisible,
    setOnlyVisible,
    setActiveGlyph,
  } = useAdmin();
  const navigate = useNavigate();

  if (!bboxes) return null;
  const keys = Object.keys(bboxes.bboxes);
  const visibleCount = visibleGlyphs.size;
  const setKeys = keys.filter((k) => bboxes.bboxes[k] !== null);

  const activateGlyph = (k: string) => {
    setActiveGlyph(k);
    if (!visibleGlyphs.has(k)) toggleVisible(k);
  };

  return (
    <Box sx={{ borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Box sx={{ p: 2, pb: 1 }}>
        <Typography variant="overline" color="text.secondary">
          Glyphen ({visibleCount}/{keys.length})
        </Typography>
      </Box>
      <Box sx={{ px: 2, pb: 1, display: 'flex', gap: 1 }}>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible(setKeys)}>alle</Button>
        <Button size="small" variant="outlined" onClick={() => setOnlyVisible([])}>keine</Button>
      </Box>
      <Divider />
      <List dense sx={{ flex: 1, overflowY: 'auto', py: 0 }}>
        {keys.map((k) => {
          const bbox = bboxes.bboxes[k];
          const hasBbox = bbox !== null;
          const hasCanon = canonStatus[k] === true;
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
                {/* visibility indicator */}
                <Box
                  sx={{
                    width: 26,
                    display: 'flex',
                    alignItems: 'center',
                    color: visible ? 'secondary.main' : 'text.disabled',
                  }}
                >
                  {visible ? <VisibilityIcon fontSize="small" /> : <VisibilityOffIcon fontSize="small" />}
                </Box>
                {/* canonical status */}
                <Box
                  sx={{
                    width: 22,
                    display: 'flex',
                    alignItems: 'center',
                    color: hasCanon ? 'success.main' : hasBbox ? 'text.secondary' : 'text.disabled',
                  }}
                >
                  {hasCanon ? <TaskAltIcon fontSize="small" /> : hasBbox ? <CircleIcon sx={{ fontSize: 10 }} /> : <RadioButtonUncheckedIcon fontSize="small" />}
                </Box>
                <ListItemText
                  primary={k}
                  slotProps={{
                    primary: {
                      sx: {
                        fontFamily: 'ui-monospace, Menlo, monospace',
                        fontSize: 13,
                        color: hasBbox ? 'text.primary' : 'text.disabled',
                      },
                    },
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
