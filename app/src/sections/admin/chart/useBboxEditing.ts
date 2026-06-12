// Bbox editing state for the chart editor: drawing a new bbox (drag), moving/
// resizing an existing one (edit grips), the putBbox commits, the lock toggle
// with its unified-letter fan-out, delete, the Escape cancel and the snackbar.
// ChartView keeps the single pointer-routing layer and calls into the
// start/update/commit primitives returned here.

import { useCallback, useEffect, useState } from 'react';

import { deleteBbox, deleteGlyph, putBbox } from '@/lib/api';
import { bboxInFromOut } from '@/lib/bbox';
import { isLetterSplit, knownGlyph, siblingKeys } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { de, fmt } from '@/locales';
import { applyHandle, editedBbox, hitHandle } from './bboxGeometry';
import {
  GRIP_HIT,
  MIN_BOX,
  NEW_BBOX_BASELINE_RATIO,
  NEW_BBOX_MIDBAND_RATIO,
  NEW_BBOX_N_ANCHORS,
} from './chartConstants';
import type { Mode } from './chartConstants';
import type { EditHandle, Rect } from './bboxGeometry';
import type { BboxIn } from '@/lib/api';

export interface DragState {
  mode: 'bbox';
  startX: number;
  startY: number;
  curX: number;
  curY: number;
}

// In-flight move/resize. We keep the original rect so each move recomputes
// from a fixed origin, and a live `cur` rect for the preview.
export interface EditState {
  handle: EditHandle;
  startX: number;
  startY: number;
  orig: Rect;
  cur: Rect;
}

interface UseBboxEditingArgs {
  width: number;
  height: number;
  zoom: number;
  mode: Mode;
  pointToImage: (clientX: number, clientY: number) => { x: number; y: number };
}

export function useBboxEditing({ width, height, zoom, mode, pointToImage }: UseBboxEditingArgs) {
  const { sourceId, bboxesByKey, glyphsByKey, activeGlyph, upsertBbox, removeBbox, removeGlyph } = useAdmin();
  const [drag, setDrag] = useState<DragState | null>(null);
  const [edit, setEdit] = useState<EditState | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  // Pointer-down in bbox/edit mode. True when an edit or draw drag actually
  // started (the caller then captures the pointer); the guard branches only
  // surface a snackbar hint.
  const startEditOrDraw = useCallback(
    (e: React.PointerEvent<HTMLDivElement>): boolean => {
      if (!activeGlyph) {
        setSnack(de.admin.snack.pickGlyphFirst);
        return false;
      }
      // A locked (finished) glyph is protected: no move/resize/exclude/redraw.
      if (bboxesByKey[activeGlyph]?.locked) {
        setSnack(fmt(de.admin.snack.lockedNoEdit, { glyph: activeGlyph }));
        return false;
      }
      const { x, y } = pointToImage(e.clientX, e.clientY);
      if (mode === 'edit') {
        const current = bboxesByKey[activeGlyph];
        if (!current) {
          setSnack(fmt(de.admin.snack.noBboxDrawFirst, { glyph: activeGlyph }));
          return false;
        }
        const handle = hitHandle(current, x, y, GRIP_HIT / zoom);
        if (!handle) {
          setSnack(de.admin.snack.editHandleHint);
          return false;
        }
        const r: Rect = { x0: current.x0, y0: current.y0, x1: current.x1, y1: current.y1 };
        setEdit({ handle, startX: x, startY: y, orig: r, cur: r });
      } else {
        setDrag({ mode: 'bbox', startX: x, startY: y, curX: x, curY: y });
      }
      return true;
    },
    [mode, activeGlyph, bboxesByKey, pointToImage, zoom],
  );

  // Pointer-move tail of the routing: live-update the edit preview, else the
  // draw rubber band.
  const updateEditOrDraw = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (edit) {
        const { x, y } = pointToImage(e.clientX, e.clientY);
        const cur = applyHandle(edit.handle, edit.orig, x - edit.startX, y - edit.startY, width, height);
        setEdit({ ...edit, cur });
        return;
      }
      if (!drag) return;
      const { x, y } = pointToImage(e.clientX, e.clientY);
      setDrag({ ...drag, curX: x, curY: y });
    },
    [drag, edit, pointToImage, width, height],
  );

  // Pointer-up tail of the routing: commit a finished move/resize, else a
  // finished draw (a fresh bbox with seeded guide defaults).
  const commitEditOrDraw = useCallback(async () => {
    if (edit) {
      const ed = edit;
      setEdit(null);
      const current = activeGlyph ? bboxesByKey[activeGlyph] : null;
      if (!activeGlyph || !current) return;
      const unchanged =
        Math.round(ed.cur.x0) === current.x0 &&
        Math.round(ed.cur.y0) === current.y0 &&
        Math.round(ed.cur.x1) === current.x1 &&
        Math.round(ed.cur.y1) === current.y1;
      if (unchanged) return;
      try {
        const saved = await putBbox(sourceId, activeGlyph, editedBbox(current, ed.handle, ed.cur));
        upsertBbox(activeGlyph, saved);
        setSnack(fmt(ed.handle === 'move' ? de.admin.snack.boxMoved : de.admin.snack.boxResized, { glyph: activeGlyph }));
      } catch (err) {
        setSnack(`${de.admin.snack.saveFailed} ${err}`);
      }
      return;
    }
    if (!drag || !activeGlyph) {
      setDrag(null);
      return;
    }
    const x0 = Math.min(drag.startX, drag.curX);
    const y0 = Math.min(drag.startY, drag.curY);
    const x1 = Math.max(drag.startX, drag.curX);
    const y1 = Math.max(drag.startY, drag.curY);
    if (x1 - x0 < MIN_BOX || y1 - y0 < MIN_BOX) {
      setDrag(null);
      return;
    }
    const current = bboxesByKey[activeGlyph];
    // New (rough) bbox: seed midband/baseline at sensible defaults — the wizard
    // refines them. Midband at top third, baseline at ~70% so the calibration
    // handles are visible immediately. A fresh draw resets the eraser strokes.
    const h = y1 - y0;
    const next: BboxIn = {
      x0,
      y0,
      x1,
      y1,
      mask_strokes: [],
      baseline_y: current?.baseline_y ?? Math.round(y0 + h * NEW_BBOX_BASELINE_RATIO),
      midband_y: current?.midband_y ?? Math.round(y0 + h * NEW_BBOX_MIDBAND_RATIO),
      n_anchors: current?.n_anchors ?? NEW_BBOX_N_ANCHORS,
    };
    setDrag(null);
    try {
      const saved = await putBbox(sourceId, activeGlyph, next);
      upsertBbox(activeGlyph, saved);
      setSnack(fmt(de.admin.snack.bboxSaved, { glyph: activeGlyph }));
    } catch (err) {
      setSnack(`${de.admin.snack.saveFailed} ${err}`);
    }
  }, [drag, edit, sourceId, activeGlyph, bboxesByKey, upsertBbox]);

  // A starting pinch drops a draw drag (but keeps a live edit, matching the
  // previous routing).
  const cancelDraw = useCallback(() => setDrag(null), []);

  // pointercancel: drop both interactions.
  const cancelInteraction = useCallback(() => {
    setDrag(null);
    setEdit(null);
  }, []);

  // Toggle the "done" lock. For a UNIFIED letter (the default) lock fans out
  // across the three positions so they stay one unit — else the sidebar lock
  // icon (`some position locked`) and the quiz keep firing on the siblings left
  // behind. For a SPLIT letter the positions are independent, so we lock only
  // the active position. The split decision routes through isLetterSplit (the
  // one shared `.some` helper). Either way we flip the aggregate of the affected
  // keys and keep each one's own geometry — positions without a bbox are skipped.
  const toggleLock = useCallback(async () => {
    if (!activeGlyph) return;
    const scopeKeys = isLetterSplit(activeGlyph, bboxesByKey) ? [activeGlyph] : siblingKeys(activeGlyph);
    const keys = scopeKeys.filter((k) => k in bboxesByKey);
    if (keys.length === 0) {
      setSnack(fmt(de.admin.snack.noBboxYet, { glyph: activeGlyph }));
      return;
    }
    const nextLocked = !keys.some((k) => bboxesByKey[k]?.locked === true);
    try {
      for (const k of keys) {
        const saved = await putBbox(sourceId, k, { ...bboxInFromOut(bboxesByKey[k]), locked: nextLocked });
        upsertBbox(k, saved);
      }
      const name = knownGlyph(activeGlyph)?.glyph ?? activeGlyph;
      const scope = keys.length > 1 ? de.admin.snack.scopeAllPositions : '';
      setSnack(fmt(nextLocked ? de.admin.snack.locked : de.admin.snack.unlocked, { name, scope }));
    } catch (err) {
      setSnack(`${de.admin.snack.saveFailed} ${err}`);
    }
  }, [sourceId, activeGlyph, bboxesByKey, upsertBbox]);

  const deleteActive = useCallback(async () => {
    if (!activeGlyph || !(activeGlyph in bboxesByKey)) return;
    const hasGlyph = glyphsByKey[activeGlyph]?.has_data === true;
    const ok = window.confirm(
      `${fmt(de.admin.snack.deleteConfirm, { glyph: activeGlyph })}${hasGlyph ? de.admin.snack.deleteConfirmCanonical : ''}`,
    );
    if (!ok) return;
    try {
      if (hasGlyph) {
        await deleteGlyph(sourceId, activeGlyph);
        removeGlyph(activeGlyph);
      }
      await deleteBbox(sourceId, activeGlyph);
      removeBbox(activeGlyph);
      setSnack(fmt(de.admin.snack.deleted, { glyph: activeGlyph }));
    } catch (err) {
      setSnack(`${de.admin.snack.deleteFailed} ${err}`);
    }
  }, [sourceId, activeGlyph, bboxesByKey, glyphsByKey, removeBbox, removeGlyph]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setDrag(null);
        setEdit(null);
      }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  return {
    drag,
    edit,
    snack,
    setSnack,
    startEditOrDraw,
    updateEditOrDraw,
    commitEditOrDraw,
    cancelDraw,
    cancelInteraction,
    toggleLock,
    deleteActive,
  };
}
