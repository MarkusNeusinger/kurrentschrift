// LehrbuchView — public primer page (/lehrbuch): a deliberately compact,
// fully-sourced overview of the German cursive scripts and the three
// Ausgangsschriften the project starts from (Kurrent · Sütterlin · Offenbacher).
//
// Same "paper & ink" identity as every public page (via PublicLayout, tokens
// from styles/paper); all German prose + every source link live in
// app/src/locales/de/lehrbuch.ts, this component is layout only.
//
// Visualisation, one honest specimen per variant:
//   · Kurrent     — set in the GLKurrent show-script font (a period Kurrent face).
//   · Sütterlin   — written live by the synthesis engine (<WrittenWord>) from the
//                   project's own seeded 1922 Vorlage, with a font fallback so a
//                   cold API never leaves an empty box.
//   · Offenbacher — no Vorlage in the repo yet; the public-domain primary source
//                   (Koch 1928) is named instead of faking a glyph.

import { useCallback, useState } from 'react';
import { Box, Container, Link, Typography } from '@mui/material';

import { WrittenWord } from '@/components/WrittenWord';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { display, garamond, letterpress, paper, script } from '@/styles/paper';

const t = de.lehrbuch;

// --- shared text styles (mirrors ImpressumView) -----------------------------
const prose = {
  fontFamily: garamond,
  color: paper.inkSoft,
  fontSize: '1.02rem',
  lineHeight: 1.7,
} as const;

// Small eyebrow/section label.
const overline = {
  fontFamily: garamond,
  textTransform: 'uppercase',
  letterSpacing: '0.12em',
  fontSize: '0.8rem',
  color: paper.sepia,
} as const;

// In-prose links: sepia with a hairline underline, viridian on hover.
const proseLink = {
  color: paper.sepia,
  textDecorationColor: `${paper.sepia}80`,
  transition: 'color .2s',
  '&:hover': { color: paper.viridian, textDecorationColor: paper.viridian },
} as const;

type SourceRef = { label: string; href: string };

// A "Quellen: a · b" line — the per-section / per-card citation row.
function SourceLine({ sources, sx }: { sources: readonly SourceRef[]; sx?: object }) {
  return (
    <Typography sx={{ fontFamily: garamond, fontSize: '0.82rem', color: paper.sepia, mt: 1, ...sx }}>
      {t.sourcesLabel}{' '}
      {sources.map((s, i) => (
        <Box component="span" key={s.href}>
          {i > 0 && <Box component="span" sx={{ mx: 0.5 }}>·</Box>}
          <Link href={s.href} target="_blank" rel="noopener noreferrer" sx={proseLink}>
            {s.label}
          </Link>
        </Box>
      ))}
    </Typography>
  );
}

// Sütterlin specimen — the engine writes the word live; on a cold/unreachable
// API (nothing rendered or an error) it falls back to the show-script font so
// the card is never an empty hole. The caption follows the active mode.
function SuetterlinSpecimen({ word }: { word: string }) {
  const [fallback, setFallback] = useState(false);
  const onResolved = useCallback(({ rendered }: { rendered: number }) => {
    if (rendered === 0) setFallback(true);
  }, []);
  const onError = useCallback(() => setFallback(true), []);

  if (fallback) {
    return (
      <Box sx={{ fontFamily: script, fontSize: 'clamp(2.4rem, 6vw, 3.2rem)', color: paper.ink, lineHeight: 1 }}>
        {word}
      </Box>
    );
  }
  return (
    <WrittenWord
      text={word}
      height={84}
      durationMs={2400}
      maxWidth={260}
      showReplay
      onResolved={onResolved}
      onError={onError}
    />
  );
}

// One variant's specimen, chosen by id (see file header).
function VariantSpecimen({ id }: { id: string }) {
  if (id === 'kurrent') {
    return (
      <Box sx={{ fontFamily: script, fontSize: 'clamp(2.4rem, 6vw, 3.2rem)', color: paper.ink, lineHeight: 1 }}>
        {t.variants[0].name}
      </Box>
    );
  }
  if (id === 'suetterlin') {
    return <SuetterlinSpecimen word={t.specimen.suetterlinWord} />;
  }
  // offenbacher — no glyph; name the public-domain source instead of faking one.
  return (
    <Typography
      sx={{
        fontFamily: garamond,
        fontStyle: 'italic',
        fontSize: '0.86rem',
        color: paper.sepia,
        textAlign: 'center',
        lineHeight: 1.5,
        px: 1,
      }}
    >
      {t.specimen.offenbacherPending}
    </Typography>
  );
}

function specimenCaption(id: string): string | null {
  if (id === 'kurrent') return t.specimen.kurrentCaption;
  if (id === 'suetterlin') return t.specimen.suetterlinCaption;
  return null;
}

export function LehrbuchView() {
  return (
    <PublicLayout footer>
      <Container
        maxWidth="md"
        sx={{ position: 'relative', zIndex: 1, px: { xs: 2.5, sm: 4, md: 6 }, pt: { xs: 4, md: 6 }, pb: { xs: 6, md: 9 } }}
      >
        {/* --- header --- */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.7rem', mb: '1rem', ...overline }}>
          <Box component="span" sx={{ width: 42, height: '1px', bgcolor: paper.sepia }} />
          {t.eyebrow}
        </Box>
        <Typography
          component="h1"
          sx={{ fontFamily: display, fontWeight: 600, fontSize: { xs: '2rem', md: '2.6rem' }, color: paper.ink, textShadow: letterpress, lineHeight: 1.1 }}
        >
          {t.title}
        </Typography>
        <Typography sx={{ ...prose, mt: 2, maxWidth: '60ch' }}>{t.lead}</Typography>

        {/* --- Grundbegriffe --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <Typography sx={{ ...overline, display: 'block', mb: 2 }}>{t.conceptsHeading}</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, borderTop: `1px solid ${paper.line}` }}>
            {t.concepts.map((c, i) => (
              <Box
                key={c.term}
                sx={{
                  px: { xs: 0, sm: 2.5 },
                  py: { xs: 2, sm: 2.5 },
                  borderTop: { xs: i > 0 ? `1px solid ${paper.line}` : 'none', sm: 'none' },
                  borderLeft: { sm: i > 0 ? `1px solid ${paper.line}` : 'none' },
                }}
              >
                <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.15rem', color: paper.ink, mb: 0.75 }}>
                  {c.term}
                </Typography>
                <Typography sx={{ ...prose, fontSize: '0.96rem' }}>{c.desc}</Typography>
              </Box>
            ))}
          </Box>
          <SourceLine sources={t.conceptsSources} />
        </Box>

        {/* --- Die drei Varianten --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <Typography sx={{ ...overline, display: 'block', mb: 2 }}>{t.variantsHeading}</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5 }}>
            {t.variants.map((v) => {
              const caption = specimenCaption(v.id);
              return (
                <Box
                  key={v.id}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    border: `1px solid ${paper.line}`,
                    borderRadius: '3px',
                    bgcolor: 'rgba(255,255,255,0.18)',
                    p: { xs: 2.25, md: 2.5 },
                  }}
                >
                  <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.5rem', color: paper.ink, lineHeight: 1.1 }}>
                    {v.name}
                  </Typography>
                  <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '0.86rem', color: paper.sepia, mt: 0.25 }}>
                    {v.period}
                  </Typography>

                  {/* specimen — fixed-height so the three cards line up */}
                  <Box
                    sx={{
                      mt: 1.75,
                      minHeight: 104,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderTop: `1px solid ${paper.line}`,
                      borderBottom: `1px solid ${paper.line}`,
                      py: 1.5,
                    }}
                  >
                    <VariantSpecimen id={v.id} />
                  </Box>
                  {caption && (
                    <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '0.76rem', color: paper.sepia, mt: 0.75, textAlign: 'center' }}>
                      {caption}
                    </Typography>
                  )}

                  <Typography sx={{ ...prose, fontSize: '0.95rem', mt: 1.75 }}>{v.essence}</Typography>

                  {/* Steckbrief — key/value rows on hairlines */}
                  <Box sx={{ mt: 1.75 }}>
                    {v.facts.map((f) => (
                      <Box key={f.k} sx={{ display: 'flex', gap: 1.5, py: 0.6, borderTop: `1px solid ${paper.line}` }}>
                        <Typography sx={{ ...prose, fontSize: '0.86rem', color: paper.sepia, minWidth: 84, flexShrink: 0 }}>
                          {f.k}
                        </Typography>
                        <Typography sx={{ ...prose, fontSize: '0.86rem', color: paper.ink }}>{f.v}</Typography>
                      </Box>
                    ))}
                  </Box>

                  {'note' in v && v.note && (
                    <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '0.8rem', color: paper.sepia, mt: 1 }}>
                      {v.note}
                    </Typography>
                  )}

                  <Box sx={{ flexGrow: 1 }} />
                  <SourceLine sources={v.sources} sx={{ mt: 1.5 }} />
                </Box>
              );
            })}
          </Box>
        </Box>

        {/* --- Kurz-Chronologie --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <Typography sx={{ ...overline, display: 'block', mb: 2 }}>{t.timelineHeading}</Typography>
          {t.timeline.map((row) => (
            <Box
              key={row.year}
              sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0, sm: 2 }, py: 0.9, borderBottom: `1px solid ${paper.line}` }}
            >
              <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.05rem', color: paper.viridian, minWidth: { sm: 110 } }}>
                {row.year}
              </Typography>
              <Typography sx={{ ...prose, fontSize: '0.96rem' }}>{row.text}</Typography>
            </Box>
          ))}
          <SourceLine sources={t.timelineSources} />
        </Box>

        {/* --- Quellen --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <Typography sx={{ ...overline, display: 'block', mb: 1.5 }}>{t.sourcesHeading}</Typography>
          <Typography sx={{ ...prose, fontSize: '0.96rem', maxWidth: '60ch' }}>{t.sourcesIntro}</Typography>
          <Box component="ul" sx={{ mt: 1.5, mb: 0, pl: 3 }}>
            {t.sources.map((s) => (
              <Typography key={s.href} component="li" sx={{ ...prose, fontSize: '0.92rem', mb: 0.4 }}>
                <Link href={s.href} target="_blank" rel="noopener noreferrer" sx={proseLink}>
                  {s.label}
                </Link>
              </Typography>
            ))}
          </Box>
          <Typography sx={{ ...prose, fontSize: '0.9rem', mt: 1.5, fontStyle: 'italic' }}>{t.sourcesBiblio}</Typography>
          <Typography sx={{ ...prose, fontSize: '0.9rem', mt: 0.75, fontStyle: 'italic' }}>{t.sourcesRepo}</Typography>
        </Box>
      </Container>
    </PublicLayout>
  );
}
