// Pair matrix (redesign R1) — every two-letter combination of one chosen
// letter, server-composed via /write/word (single glyphs + generated Übergang),
// capitals only on the left. A read-only QA surface: an unnatural join shows up
// here directly instead of hiding inside a longer word. Cells fetch lazily
// (IntersectionObserver) through WrittenWord's shared render cache, so a full
// row of ~60 combinations doesn't fire at once on mount.

import { Alert, Box, ButtonBase, Chip, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { glyphKeyFor, LETTERS } from '@/domain/glyphs';
import type { Letter } from '@/domain/glyphs';
import { shapeText } from '@/domain/shaping';
import { useInView } from '@/hooks/useInView';
import { getPairs } from '@/lib/api';
import type { GlyphPairOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { garamond } from '@/styles/paper';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';

const CELL_H = 88; // px — big enough to judge a join, small enough for a grid

// The shaped glyph_keys behind a two-letter cell — null when the pair folds
// into a closed-set ligature (one slot: ch, ck, …), which has no join to edit.
function pairKeysOf(text: string): [string, string] | null {
  const keyed = shapeText(text).filter((s) => s.key);
  if (keyed.length !== 2) return null;
  return [keyed[0].key!, keyed[1].key!];
}

function PairCell({
  text,
  sourceId,
  row,
  onEdit,
}: {
  text: string;
  sourceId: string;
  row?: GlyphPairOut;
  onEdit?: () => void;
}) {
  const [ref, inView] = useInView<HTMLDivElement>();
  return (
    <Box
      ref={ref}
      component={onEdit ? ButtonBase : Box}
      onClick={onEdit}
      sx={{
        position: 'relative',
        border: 1,
        borderColor: row ? (row.approved ? 'success.main' : 'warning.main') : 'divider',
        borderRadius: 1,
        bgcolor: '#fff',
        p: 0.5,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0.25,
        minWidth: 96,
        cursor: onEdit ? 'pointer' : 'default',
      }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: garamond }}>
        {text}
      </Typography>
      {row && (
        <Chip
          size="small"
          color={row.approved ? 'success' : 'warning'}
          label={row.approved ? de.admin.pairs.badgeApproved : de.admin.pairs.badgeDraft}
          sx={{ position: 'absolute', top: 2, right: 2, height: 18, fontSize: 10 }}
        />
      )}
      <Box sx={{ height: CELL_H, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {inView && <WrittenWord text={text} sourceId={sourceId} height={CELL_H} animate={false} showLineature />}
      </Box>
    </Box>
  );
}

function CellGrid({
  pairs,
  sourceId,
  rowsByKeys,
  onEdit,
}: {
  pairs: string[];
  sourceId: string;
  rowsByKeys: Map<string, GlyphPairOut>;
  onEdit: (text: string, left: string, right: string) => void;
}) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      {pairs.map((p) => {
        const keys = pairKeysOf(p);
        return (
          <PairCell
            key={p}
            text={p}
            sourceId={sourceId}
            row={keys ? rowsByKeys.get(`${keys[0]}|${keys[1]}`) : undefined}
            onEdit={keys ? () => onEdit(p, keys[0], keys[1]) : undefined}
          />
        );
      })}
    </Box>
  );
}

export function PairMatrix() {
  const { source, sourceId, glyphsByKey } = useAdmin();
  const authored = useMemo(() => {
    const hasCanon = (letter: Letter) => glyphsByKey[glyphKeyFor(letter)]?.has_data === true;
    return {
      lower: LETTERS.filter((l) => l.group === 'lower' && hasCanon(l)),
      upper: LETTERS.filter((l) => l.group === 'upper' && hasCanon(l)),
    };
  }, [glyphsByKey]);
  const pickable = useMemo(() => [...authored.lower, ...authored.upper], [authored]);
  const [picked, setPicked] = useState<string | null>(null);
  const letter = pickable.find((l) => l.glyph === picked) ?? pickable[0];

  // Existing overrides (incl. unapproved drafts — the admin fetch carries the
  // auth headers) for the badges + the editor's starting state.
  const [rowsByKeys, setRowsByKeys] = useState<Map<string, GlyphPairOut>>(new Map());
  const refreshPairs = useCallback(() => {
    getPairs(sourceId, { all: true }, { retries: 1 })
      .then((rows) => setRowsByKeys(new Map(rows.map((r) => [`${r.left_key}|${r.right_key}`, r]))))
      .catch(() => setRowsByKeys(new Map()));
  }, [sourceId]);
  useEffect(refreshPairs, [refreshPairs]);

  const [editing, setEditing] = useState<{ text: string; left: string; right: string } | null>(null);

  if (!source) return null;

  // Right side of a pair is always lowercase; the left side may also be a
  // capital — so a lowercase letter gets both directions, a capital only the
  // "as first letter" row.
  const asFirst = letter ? authored.lower.map((r) => letter.glyph + r.glyph) : [];
  const asSecond =
    letter && letter.group === 'lower'
      ? [...authored.lower, ...authored.upper].filter((l) => l.glyph !== letter.glyph).map((l) => l.glyph + letter.glyph)
      : [];

  return (
    <Box sx={{ overflowY: 'auto', height: '100%', p: { xs: 2, md: 3 } }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6">{de.admin.pairs.title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
          {de.admin.pairs.intro}
        </Typography>
      </Box>

      {pickable.length === 0 ? (
        <Alert severity="info">{de.admin.pairs.empty}</Alert>
      ) : (
        <>
          <Box sx={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              {de.admin.pairs.pickLetter}
            </Typography>
            {pickable.map((l) => (
              <ButtonBase
                key={l.glyph}
                onClick={() => setPicked(l.glyph)}
                sx={{
                  fontFamily: garamond,
                  fontSize: 20,
                  lineHeight: 1,
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor: letter?.glyph === l.glyph ? 'primary.main' : 'divider',
                  bgcolor: letter?.glyph === l.glyph ? 'action.selected' : 'transparent',
                }}
              >
                {l.glyph}
              </ButtonBase>
            ))}
          </Box>

          {letter && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {fmt(de.admin.pairs.asFirst, { glyph: letter.glyph })}
                </Typography>
                <CellGrid
                  pairs={asFirst}
                  sourceId={sourceId}
                  rowsByKeys={rowsByKeys}
                  onEdit={(text, left, right) => setEditing({ text, left, right })}
                />
              </Box>
              {asSecond.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {fmt(de.admin.pairs.asSecond, { glyph: letter.glyph })}
                  </Typography>
                  <CellGrid
                    pairs={asSecond}
                    sourceId={sourceId}
                    rowsByKeys={rowsByKeys}
                    onEdit={(text, left, right) => setEditing({ text, left, right })}
                  />
                </Box>
              )}
            </Box>
          )}
        </>
      )}
      {editing && (
        <PairEditorDialog
          open
          onClose={() => setEditing(null)}
          pairText={editing.text}
          leftKey={editing.left}
          rightKey={editing.right}
          sourceId={sourceId}
          onChanged={refreshPairs}
        />
      )}
    </Box>
  );
}
