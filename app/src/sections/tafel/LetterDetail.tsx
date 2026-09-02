// LetterDetail — one written letter of the Schreibtafel in detail (/tafel?g=
// <key>, opened by tapping a letter on the sheet; vision goal 3, „Buchstaben
// in Aktion"): the stroke order as numbered starts on the finished form with
// a stepper that shows the letter after stroke n, the Ansatz and Auslauf
// (entry/exit of the Übergang), the live write-in at two tempi, the
// documented look-alikes written beside it (SpecimenStrip) and a jump into
// the Federprobe to see the letter inside a word. Data: the same render
// payload the sheet draws (renderCache — a cache hit); copy in
// locales/de/tafel.ts `detail`.

import { Box, Button, ButtonBase, IconButton, Link, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import { SpecimenStrip, useSpecimenPayloads } from '@/components/SpecimenStrip';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { CONFIG } from '@/global-config';
import { knownGlyph } from '@/domain/glyphs';
import { fetchRenderGlyph, type GlyphRenderData } from '@/lib/api';
import { GLYPH_WRITE_MS } from '@/lib/strokeTiming';
import { ringsToPathD, type Ring } from '@/lib/svg';
import { de, fmt } from '@/locales';
import { paths } from '@/routes/paths';
import { WORD_BANK } from '@/sections/quiz/wordBank';
import { exampleWord, lookalikeKeys, strokeCount, strokeStarts } from '@/sections/tafel/letterDetail';
import { hitArea } from '@/styles/hitArea';
import { display, garamond, paper } from '@/styles/paper';

const t = de.tafel.detail;

// The slow tempo: three times the glyph's normal write-in, so a stroke's
// direction can be followed by eye.
const SLOW_FACTOR = 3;
const INK = paper.ink;
const GUIDE = paper.line;

// Static stroke-order view: every stroke's silhouette (the first `upto` filled,
// the rest as a hairline outline of what is still to come), numbered markers
// at the stroke starts, hollow markers at the Ansatz and Auslauf. Same
// template frame as WrittenGlyph (baseline 0, y up → negated for SVG).
function StrokeOrderGlyph({ data, upto, height }: { data: GlyphRenderData; upto: number; height: number }) {
  const geom = useMemo(() => {
    const tpl = data.template_guides;
    const xs = data.anchors_template.map((a) => a[0]);
    const minX = (xs.length ? Math.min(0, ...xs) : 0) - 0.5;
    const vbW = (xs.length ? Math.max(0.5, ...xs) : 0.5) + 0.5 - minX;
    const vbY = -tpl.ascender - 0.3;
    const vbH = tpl.ascender - tpl.descender + 0.6;
    const strokes: Ring[][] = data.outline_paths?.length
      ? (data.outline_paths as Ring[][])
      : (data.outline_polygons ?? []).filter((p) => p.length > 2).map((p) => [p as Ring]);
    return { tpl, minX, vbW, vbY, vbH, strokes, starts: strokeStarts(data) };
  }, [data]);
  const { tpl, minX, vbW, vbY, vbH, strokes, starts } = geom;
  const width = (height * vbW) / vbH;
  const r = 0.14; // marker radius, template units
  return (
    <svg width={width} height={height} viewBox={`${minX} ${vbY} ${vbW} ${vbH}`} role="img" aria-label={t.strokeOrderAria} style={{ display: 'block', maxWidth: '100%' }}>
      <line x1={minX} x2={minX + vbW} y1={-tpl.baseline} y2={-tpl.baseline} stroke={GUIDE} strokeWidth={0.012} />
      <line x1={minX} x2={minX + vbW} y1={-tpl.midband} y2={-tpl.midband} stroke={GUIDE} strokeWidth={0.012} strokeDasharray="0.06 0.05" />
      {strokes.map((rings, i) =>
        i < upto ? (
          <path key={i} d={ringsToPathD(rings, true)} fillRule="evenodd" fill={INK} />
        ) : (
          <path key={i} d={ringsToPathD(rings, true)} fillRule="evenodd" fill="none" stroke={paper.sepiaFaint} strokeWidth={0.015} strokeDasharray="0.04 0.03" />
        ),
      )}
      {/* Ansatz / Auslauf: where the Übergang from the previous letter lands
          and where the stroke to the next one leaves. */}
      {data.entry && <circle cx={data.entry.xy[0]} cy={-data.entry.xy[1]} r={r * 0.6} fill={paper.hi} stroke={paper.viridian} strokeWidth={0.03} />}
      {data.exit_pt && <circle cx={data.exit_pt.xy[0]} cy={-data.exit_pt.xy[1]} r={r * 0.6} fill={paper.hi} stroke={paper.viridian} strokeWidth={0.03} />}
      {/* Numbered stroke starts, in writing order. */}
      {starts.map(([x, y], i) => (
        <g key={i} opacity={i < upto ? 1 : 0.45}>
          <circle cx={x} cy={-y} r={r} fill={paper.viridian} />
          <text x={x} y={-y} fontSize={r * 1.3} fontFamily="Helvetica, Arial, sans-serif" fontWeight={700} fill="#fff" textAnchor="middle" dominantBaseline="central">
            {i + 1}
          </text>
        </g>
      ))}
    </svg>
  );
}

interface Props {
  /** The written letter's glyph_key (the `?g=` value). */
  glyphKey: string;
  /** Its display character (from the sheet's slot). */
  glyph: string;
  onClose: () => void;
}

// Mounted with `key={glyphKey}` by the caller, so a new letter starts with
// fresh state (no resets inside the fetch effect).
export function LetterDetail({ glyphKey, glyph, onClose }: Props) {
  const [data, setData] = useState<GlyphRenderData | null | undefined>(undefined);
  const [tempo, setTempo] = useState<'normal' | 'slow'>('normal');
  const [upto, setUpto] = useState<number | null>(null); // null = all strokes

  useEffect(() => {
    let cancelled = false;
    fetchRenderGlyph(CONFIG.sourceId, glyphKey)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      });
    return () => {
      cancelled = true;
    };
  }, [glyphKey]);

  const lookalikes = useMemo(() => lookalikeKeys(glyphKey), [glyphKey]);
  const specimens = useMemo(
    () => lookalikes.map((k) => ({ key: k, label: knownGlyph(k)?.glyph ?? k })),
    [lookalikes],
  );
  const lookalikeKeysMemo = useMemo(() => specimens.map((s) => s.key), [specimens]);
  const payloads = useSpecimenPayloads(lookalikeKeysMemo, true);
  const example = useMemo(() => exampleWord(glyphKey, WORD_BANK), [glyphKey]);
  const name = knownGlyph(glyphKey)?.label ?? glyph;
  const count = data ? strokeCount(data) : 0;
  const shown = upto ?? count;

  return (
    <Box
      component="section"
      id="buchstabe"
      aria-label={`${t.heading}: ${name}`}
      sx={{ border: `1px solid ${paper.line}`, borderRadius: '3px', bgcolor: paper.hi, p: { xs: 2, sm: 3 }, scrollMarginTop: { xs: 100, md: 84 } }}
    >
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, mb: 1.5 }}>
        <Typography component="span" sx={{ fontFamily: garamond, fontSize: '2.2rem', lineHeight: 1, color: paper.ink }}>
          {glyph}
        </Typography>
        <Typography variant="h5" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, flexGrow: 1 }}>
          {t.heading}: {name}
        </Typography>
        <IconButton size="small" onClick={onClose} aria-label={t.close} sx={[hitArea(), { color: paper.sepia }]}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {data === null ? (
        <Typography sx={{ color: paper.inkSoft }}>{t.unavailable}</Typography>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: { xs: 3, md: 4 } }}>
          {/* Zug um Zug — the live write-in at two tempi. */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1 }}>
              {t.animated}
            </Typography>
            <Box sx={{ minHeight: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#fff', border: `1px solid ${paper.line}`, borderRadius: '3px', p: 1 }}>
              {data && (
                <WrittenGlyph
                  key={`${glyphKey}-${tempo}`}
                  glyphKey={glyphKey}
                  data={data}
                  height={220}
                  durationMs={tempo === 'slow' ? GLYPH_WRITE_MS * SLOW_FACTOR : GLYPH_WRITE_MS}
                />
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 1 }}>
              <Typography variant="caption" sx={{ color: paper.sepia }}>
                {t.tempoLabel}
              </Typography>
              <ToggleButtonGroup size="small" exclusive value={tempo} onChange={(_, v: 'normal' | 'slow' | null) => v && setTempo(v)} aria-label={t.tempoLabel}>
                <ToggleButton value="normal">{t.tempoNormal}</ToggleButton>
                <ToggleButton value="slow">{t.tempoSlow}</ToggleButton>
              </ToggleButtonGroup>
            </Box>
          </Box>

          {/* Strichfolge — numbered starts, the stepper, Ansatz/Auslauf. */}
          <Box>
            <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1 }}>
              {t.strokeOrder}
            </Typography>
            <Box sx={{ minHeight: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#fff', border: `1px solid ${paper.line}`, borderRadius: '3px', p: 1 }}>
              {/* Full payload: the strokes past `upto` render as the hairline
                  of what is still to come, so the stepper shows the way. */}
              {data && <StrokeOrderGlyph data={data} upto={shown} height={220} />}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1.5, mt: 1 }}>
              {count > 1 ? (
                <>
                  <ButtonBase onClick={() => setUpto((u) => Math.max(1, (u ?? count) - 1))} aria-label={t.stepPrev} sx={{ px: 1, borderRadius: '3px', color: paper.sepia, fontFamily: garamond }}>
                    ‹
                  </ButtonBase>
                  <Typography variant="caption" sx={{ color: paper.sepia }}>
                    {fmt(t.step, { n: shown, total: count })}
                  </Typography>
                  <ButtonBase onClick={() => setUpto((u) => Math.min(count, (u ?? count) + 1))} aria-label={t.stepNext} sx={{ px: 1, borderRadius: '3px', color: paper.sepia, fontFamily: garamond }}>
                    ›
                  </ButtonBase>
                  {upto !== null && upto < count && (
                    <Button size="small" onClick={() => setUpto(null)} sx={{ fontFamily: garamond, color: paper.viridianText, minWidth: 0 }}>
                      {t.stepAll}
                    </Button>
                  )}
                </>
              ) : (
                <Typography variant="caption" sx={{ color: paper.sepia }}>
                  {count === 1 ? t.singleStroke : ''}
                </Typography>
              )}
              <Typography variant="caption" sx={{ color: paper.sepia, ml: 'auto' }}>
                {t.markers}
              </Typography>
            </Box>
          </Box>
        </Box>
      )}

      {/* Verwechsler + im Wort sehen */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: { xs: 2, sm: 3 }, mt: 3 }}>
        {specimens.length > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink }}>
              {t.lookalikes}
            </Typography>
            <SpecimenStrip specimens={specimens} payloads={payloads} height={72} sx={{ bgcolor: '#fff' }} />
          </Box>
        )}
        {example && (
          <Link component={RouterLink} to={`${paths.scribe}?text=${encodeURIComponent(example.word)}`} variant="body2" sx={{ color: paper.viridianText, ml: { sm: 'auto' } }}>
            {fmt(example.historic ? t.inWordHistoric : t.inWord, { word: example.word })} →
          </Link>
        )}
      </Box>
    </Box>
  );
}
