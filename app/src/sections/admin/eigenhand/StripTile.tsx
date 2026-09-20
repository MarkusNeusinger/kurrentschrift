// One stored Fassung in the strip list: its verdict sheet, its pixels once
// they are asked for, the word cuts of its row, and the Fleckenpinsel.

import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useState } from 'react';

import type { EigenhandFleck, EigenhandStrip } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { BefundChips } from '@/sections/admin/eigenhand/BefundChips';
import { FleckenEditor, MIN_ERASE_ZOOM } from '@/sections/admin/eigenhand/FleckenEditor';
import type { LupeTarget } from '@/sections/admin/eigenhand/Lupe';
import { PfadCaption } from '@/sections/admin/eigenhand/PfadCaption';
import { PfadLayer } from '@/sections/admin/eigenhand/PfadLayer';
import { PfadRohzahlenChips } from '@/sections/admin/eigenhand/PfadRohzahlenChips';
import { StripImage } from '@/sections/admin/eigenhand/StripImage';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { bahnKarte } from '@/sections/admin/eigenhand/uebergabe';
import { Uebergabekarte } from '@/sections/admin/eigenhand/Uebergabekarte';
import { useStripImage } from '@/sections/admin/eigenhand/useStripImage';
import { useStripPfade } from '@/sections/admin/eigenhand/useStripPfade';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

/** One stored Fassung: its metadata, and — once asked for — its pixels. */
export function StripTile({
  hand,
  row,
  zoom,
  ohneLineatur,
  pfade: wantPfade,
  onLupe,
  onZoom,
  onFlecken,
}: {
  hand: string;
  row: EigenhandStrip;
  zoom: Zoom;
  ohneLineatur: boolean;
  pfade: boolean;
  onLupe: (target: LupeTarget) => void;
  onZoom: (level: Zoom) => void;
  onFlecken: (strip: string, fassung: string, circles: EigenhandFleck[]) => void;
}) {
  const t = de.admin.eigenhand;
  // `open` says whether pixels are wanted at all; `shown` which cut. The box
  // INDEX identifies the cut, not the word text: a row may carry the same
  // word twice (the plan does — `ja!`, `„wohl“`), and addressing it by text
  // would serve the first box under every later chip and light them all.
  const [open, setOpen] = useState(false);
  const [shown, setShown] = useState<number | null>(null);
  // The eraser works on the WHOLE strip: the mask's millimetres are the
  // strip's own, and a word cut would put them against another origin.
  const [erasing, setErasing] = useState(false);
  const [roh, setRoh] = useState(false);
  const [reload, setReload] = useState(0);
  const { url, loading, error } = useStripImage(
    hand,
    row.strip,
    row.fassung,
    erasing ? null : shown,
    open,
    // „roh" promises the FILED bytes, so it has to switch the ruling view off
    // too — a raw strip still run through `without_rulings` is a derived image
    // like any other, and the promise would be false (Copilot review, PR #568).
    ohneLineatur && !roh,
    roh,
    reload,
  );
  // The paths are asked for only while the layer is on and the tile is open —
  // and never at all while the brush is out, where the picture is the raw
  // strip and a path over it would only be in the way.
  const showPfade = wantPfade && open && !erasing;
  const pfade = useStripPfade(hand, row.strip, row.fassung, showPfade);
  const title = `${row.strip} · ${row.fassung}${shown === null ? '' : ` · ${row.words[shown] ?? ''}`}`;
  const flecken = row.flecken ?? [];
  // A word cut needs its own frame; the box rectangle comes from the listing.
  const cut = shown === null ? null : (row.boxes[shown]?.rect_px ?? null);
  const drawn = (pfade.pfade ?? []).filter((p) => shown === null || p.box_index === shown);
  // A word cut without a box rectangle cannot carry an overlay at all — an old
  // Bogen has no cut geometry to place one against. That is a state of its
  // own: without it a stored path for exactly this word would be silently
  // suppressed and the tile would look as if the layer had not worked (review
  // of PR #598). CropTile has always said it out loud; so does this one now.
  const placeable = shown === null || cut !== null;

  const startErasing = () => {
    setShown(null);
    setOpen(true);
    // The brush has to be aimable: at ¼ the smallest one is under a display
    // pixel across. The zoom is lifted rather than the brush grown — a brush
    // size is a millimetre fact about the paper.
    if (zoom < MIN_ERASE_ZOOM) onZoom(MIN_ERASE_ZOOM);
    setErasing(true);
  };

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1.5, mb: 1.5 }}>
      <Stack direction="row" spacing={1.5} sx={{ flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
        <Typography variant="subtitle2" sx={{ color: paper.ink }}>
          {row.strip} · {row.fassung}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.stripMeta, {
            sheet: row.sheet,
            row: row.row_index,
            width: row.width_px,
            height: row.height_px,
            dpi: Math.round(row.dpi),
          })}
        </Typography>
        {loading && <CircularProgress size={14} />}
        {/* The mask count is a chip of this Fassung like the Befund's are, so
            what it means rides in the row's ONE hint instead of opening a
            second (§9.4) — the head row explains one subject: this Fassung. */}
        {flecken.length > 0 && !erasing && (
          <Chip size="small" variant="outlined" label={fmt(t.fleckenChip, { count: flecken.length })} />
        )}
        <BefundChips
          befund={row.befund}
          extra={
            flecken.length > 0 && !erasing ? (
              <Typography variant="body2">
                {`${t.fleckenChipTitle}: ${t.fleckenChipHint}`}
              </Typography>
            ) : undefined
          }
        />
        <Box sx={{ flexGrow: 1 }} />
        {/* No tooltip on „Flecken radieren": its content was an INSTRUCTION for
            the whole erasing mode (how the brush works, and that the stored
            strip stays byte-for-byte), not a name for the button — and a MUI
            tooltip needs a 700 ms long-press on the tablet this is operated on.
            It stands as the mode's own caption inside `FleckenEditor` (V25). */}
        {!erasing && (
          <Button size="small" onClick={startErasing} sx={{ minHeight: TOUCH_TARGET }}>
            {t.fleckenStart}
          </Button>
        )}
        {open ? (
          <Button size="small" onClick={() => setOpen(false)} disabled={erasing} sx={{ minHeight: TOUCH_TARGET }}>
            {t.stripHide}
          </Button>
        ) : (
          <Button size="small" variant="outlined" onClick={() => setOpen(true)} sx={{ minHeight: TOUCH_TARGET }}>
            {t.stripShow}
          </Button>
        )}
      </Stack>

      {open && erasing && (
        <FleckenEditor
          // Keyed by the Fassung alone: the editor takes the stored list when
          // the mode opens and owns it from there, so a save must not remount
          // it out from under its own confirmation.
          key={`${row.strip}/${row.fassung}`}
          hand={hand}
          strip={row.strip}
          fassung={row.fassung}
          url={url}
          widthPx={row.width_px}
          heightPx={row.height_px}
          dpi={row.dpi}
          zoom={zoom}
          initial={flecken}
          roh={roh}
          onRoh={setRoh}
          onClose={() => {
            setErasing(false);
            setRoh(false);
          }}
          onSaved={(circles) => {
            onFlecken(row.strip, row.fassung, circles);
            // The URL has not changed but the served pixels have.
            setReload((n) => n + 1);
          }}
        />
      )}

      {open && !erasing && (
        <>
          {url && (
            <Box sx={{ mt: 1 }}>
              <StripImage
                url={url}
                alt={title}
                heightPx={row.height_px}
                zoom={zoom}
                onLupe={onLupe}
                overlay={
                  drawn.length > 0 && placeable ? (
                    <PfadLayer
                      pfade={drawn}
                      widthPx={cut ? cut[2] - cut[0] : row.width_px}
                      heightPx={cut ? cut[3] - cut[1] : row.height_px}
                      zoom={zoom}
                      originX={cut ? cut[0] : 0}
                      originY={cut ? cut[1] : 0}
                      showIndex={shown !== null}
                    />
                  ) : undefined
                }
              />
            </Box>
          )}
          {showPfade && (
            <>
              {pfade.loading && <CircularProgress size={12} sx={{ mt: 1 }} />}
              {drawn.length > 0 && placeable && <PfadCaption pfade={drawn} flecken={row.flecken} />}
              {/* NOT gated by `placeable`: the numbers were measured on the
                  strip and need no cut geometry, while the overlay does. A box
                  from a Bogen printed before the cut rectangles existed can
                  show its reading even though its path cannot be drawn — the
                  „kein Kasten-Rechteck" line below says why the picture is
                  missing, and hiding the numbers with it would suppress a fact
                  the follower did measure. Only the whole strip needs the box
                  prefix: a selected cut is already named by the filled chip in
                  the selector below. */}
              {drawn.length > 0 && <PfadRohzahlenChips pfade={drawn} showBox={shown === null} />}
              {/* The empty answers are DIFFERENT and each is said out loud:
                  `null` is „nobody has followed this Fassung", an empty result
                  is „followed, nothing came back", a row with paths but none
                  for the word currently shown is a third — and a word cut
                  without a box rectangle is a fourth, where even a stored path
                  cannot be placed. A silent picture would make all four look
                  alike. */}
              {/* „Nobody has followed this Fassung" is the one of the four
                  that has a local STEP behind it, so it is the one that gets a
                  card instead of a sentence — with the real strip and Fassung
                  in the command, where the old running text had „…". The card
                  is built here rather than server-side because Phase 1 has no
                  read that says hand-wide which Fassung carries a Bahn (the
                  listing defers `pfade`); in the open Fassung the answer is
                  already loaded. */}
              {!pfade.loading &&
                !pfade.error &&
                (!placeable || drawn.length === 0) &&
                (!placeable ? (
                  <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.inkSoft }}>
                    {t.pfadNoBox}
                  </Typography>
                ) : pfade.pfade === null ? (
                  <Box sx={{ mt: 0.5 }}>
                    <Uebergabekarte karte={bahnKarte(hand, row.strip, row.fassung)} />
                  </Box>
                ) : (
                  <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.inkSoft }}>
                    {pfade.pfade.length === 0 ? t.pfadEmpty : t.pfadNotInBox}
                  </Typography>
                ))}
              {pfade.error && (
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: 'warning.main' }}>
                  {t.pfadError} {pfade.error.sentence}
                </Typography>
              )}
            </>
          )}
          <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', rowGap: 0.5 }}>
            <Chip
              size="small"
              label={t.stripWhole}
              variant={shown === null ? 'filled' : 'outlined'}
              onClick={() => setShown(null)}
            />
            {row.words.map((candidate, index) => (
              <Chip
                key={`${candidate}-${index}`}
                size="small"
                label={candidate}
                variant={shown === index ? 'filled' : 'outlined'}
                onClick={() => setShown(index)}
              />
            ))}
          </Stack>
        </>
      )}

      {error && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          <ErrorText error={error} prefix={t.stripImagesError} />
        </Alert>
      )}
    </Box>
  );
}
