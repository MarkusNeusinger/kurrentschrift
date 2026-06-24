// SchriftkundeView — public primer page (/schriftkunde): a deliberately compact,
// fully-sourced overview of the German cursive scripts and the three
// Ausgangsschriften the project starts from (Kurrent · Sütterlin · Offenbacher).
//
// Same "paper & ink" identity as every public page (via PublicLayout, tokens
// from styles/paper); all German prose + every source link live in
// app/src/locales/de/schriftkunde.ts, this component is layout only. Section
// titles use the shared <CategoryHeading> (the viridian Kurrent initial on a
// hairline writing-line, identical to /impressum).
//
// Visualisation, one honest specimen per variant:
//   · Kurrent     — set in the GLKurrent show-script font (a period Kurrent face).
//   · Sütterlin   — written live by the synthesis engine (<WrittenWord>) from the
//                   project's own seeded 1922 Vorlage, with a Sütterlin-font
//                   fallback (Zinken HJZ 1911) so a cold API never leaves an
//                   empty box. In that font the plain 's' already is the long ſ
//                   (its round End-s sits on '#'), so the fallback word "lesen"
//                   renders the correct medial long-s without needing U+017F.
//   · Offenbacher — a marked excerpt from Koch's own public-domain 1928 plate
//                   (the genuine historical hand, not a synthesised glyph).

import { useCallback, useState, type ReactNode } from 'react';
import { Box, Link, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';

import offenbacherSpecimen from '@/assets/specimens/offenbacher-koch-1928.jpg';
import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { Prose } from '@/components/Prose';
import { WrittenWord } from '@/components/WrittenWord';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { display, garamond, paper, script, suetterlin } from '@/styles/paper';

const t = de.schriftkunde;

// --- shared text styles (mirrors ImpressumView) -----------------------------
// Body prose inherits size/family from the theme `body1` variant (19px Garamond);
// only colour and the slightly looser leading are set here.
const prose = {
  color: paper.inkSoft,
  lineHeight: 1.7,
} as const;

// In-prose links: sepia with a hairline underline, viridian on hover.
const proseLink = {
  color: paper.sepia,
  textDecorationColor: `${paper.sepia}80`,
  transition: 'color .2s',
  '&:hover': { color: paper.viridian, textDecorationColor: paper.viridian },
} as const;

type SourceRef = { label: string; href: string };
type TermItem = { term: string; desc: string };

// A "Quellen: a · b" line — the per-section / per-card citation row. `sx` is the
// proper MUI SxProps and merged via the array form, so callers may pass any
// valid sx shape (object / array / theme callback) without losing styles.
function SourceLine({ sources, sx }: { sources: readonly SourceRef[]; sx?: SxProps<Theme> }) {
  return (
    <Typography
      variant="caption"
      component="p"
      sx={[{ color: paper.sepia, mt: 1 }, ...(Array.isArray(sx) ? sx : [sx])]}
    >
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

// A section: CategoryHeading (viridian Kurrent initial) + optional lead line.
function Section({ heading, lead, children }: { heading: string; lead?: string; children: ReactNode }) {
  return (
    <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
      <CategoryHeading>{heading}</CategoryHeading>
      {lead && <Typography sx={{ ...prose, mb: 1.75, maxWidth: '64ch' }}>{lead}</Typography>}
      {children}
    </Box>
  );
}

// Three term/desc cells on hairlines — the Grundbegriffe + Federn grid.
function TripletGrid({ items }: { items: readonly TermItem[] }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, borderTop: `1px solid ${paper.line}` }}>
      {items.map((c, i) => (
        <Box
          key={c.term}
          sx={{
            px: { xs: 0, sm: 2.5 },
            py: { xs: 2, sm: 2.5 },
            borderTop: { xs: i > 0 ? `1px solid ${paper.line}` : 'none', sm: 'none' },
            borderLeft: { sm: i > 0 ? `1px solid ${paper.line}` : 'none' },
          }}
        >
          <Typography variant="h6" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 0.75 }}>{c.term}</Typography>
          <Typography variant="body2" sx={prose}>{c.desc}</Typography>
        </Box>
      ))}
    </Box>
  );
}

// Term/desc rows on hairlines — Tinte, Buchstaben, Zahlen. Term in the sepia
// margin (sm+), desc in the reading column; both stack on xs.
function DefinitionRows({ items }: { items: readonly TermItem[] }) {
  return (
    <Box sx={{ borderBottom: `1px solid ${paper.line}` }}>
      {items.map((it) => (
        <Box
          key={it.term}
          sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0.25, sm: 2.5 }, py: 1.1, borderTop: `1px solid ${paper.line}` }}
        >
          <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, minWidth: { sm: 196 }, flexShrink: 0, pt: { sm: 0.15 } }}>
            {it.term}
          </Typography>
          <Typography variant="body2" sx={prose}>{it.desc}</Typography>
        </Box>
      ))}
    </Box>
  );
}

// Show-script font specimen style, reused by the Kurrent card and the Sütterlin
// fallback (the GLKurrent face stands in when the engine can't render).
const fontSpecimenSx = { fontFamily: script, fontSize: 'clamp(2.4rem, 6vw, 3.2rem)', color: paper.ink, lineHeight: 1 } as const;
// Sütterlin cold-start fallback: the bundled Zinken HJZ 1911 face (a genuine
// Sütterlin school hand), distinct from the Kurrent show-script above.
const suetterlinFontSx = { fontFamily: suetterlin, fontSize: 'clamp(2.2rem, 5.5vw, 3rem)', color: paper.ink, lineHeight: 1 } as const;
// Fixed-height specimen box so the three cards line up.
const specimenBoxSx = {
  mt: 1.75,
  minHeight: 104,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderTop: `1px solid ${paper.line}`,
  borderBottom: `1px solid ${paper.line}`,
  py: 1.5,
} as const;
const specimenCaptionSx = { fontFamily: garamond, fontStyle: 'italic', fontSize: '0.76rem', color: paper.sepia, mt: 0.75, textAlign: 'center' } as const;

// One variant's specimen box + caption (see file header). The Sütterlin block is
// stateful: the engine writes the word live, and on a cold/unreachable API
// (nothing rendered or an error) it falls back to the show-script font — and the
// caption switches with it, so it never claims "live geschrieben … Synthese-
// Engine" while the static font fallback is on screen.
function SpecimenBlock({ id }: { id: string }) {
  const [fallback, setFallback] = useState(false);
  const onResolved = useCallback(({ rendered }: { rendered: number }) => {
    if (rendered === 0) setFallback(true);
  }, []);
  const onError = useCallback(() => setFallback(true), []);

  let content: ReactNode;
  let caption: string | null = null;

  if (id === 'kurrent') {
    content = <Box sx={fontSpecimenSx}>{t.variants[0].name}</Box>;
    caption = t.specimen.kurrentCaption;
  } else if (id === 'suetterlin') {
    content = fallback ? (
      <Box sx={suetterlinFontSx}>{t.specimen.suetterlinWordFallback}</Box>
    ) : (
      <WrittenWord
        text={t.specimen.suetterlinWord}
        height={84}
        durationMs={2400}
        maxWidth={260}
        showReplay
        onResolved={onResolved}
        onError={onError}
      />
    );
    caption = fallback ? t.specimen.suetterlinCaptionFallback : t.specimen.suetterlinCaption;
  } else {
    // offenbacher — a marked excerpt from Koch's own public-domain 1928 plate
    // (lowercase a–i). `multiply` drops the scan's white ground onto the paper.
    content = (
      <Box
        component="img"
        src={offenbacherSpecimen}
        alt={t.specimen.offenbacherAlt}
        loading="lazy"
        sx={{ maxWidth: '100%', height: 'auto', display: 'block', mixBlendMode: 'multiply' }}
      />
    );
    caption = t.specimen.offenbacherCaption;
  }

  return (
    <>
      <Box sx={specimenBoxSx}>{content}</Box>
      {caption && <Typography sx={specimenCaptionSx}>{caption}</Typography>}
    </>
  );
}

export function SchriftkundeView() {
  return (
    <PublicLayout footer>
      <PageContainer sx={{ pt: { xs: 4, md: 6 } }}>
        {/* shared page header — eyebrow (area) + Playfair title + intro */}
        <PageHeader eyebrow={t.eyebrow} title={t.title}>
          <Typography sx={{ ...prose, color: paper.ink }}>{t.intro}</Typography>
          <Typography sx={{ ...prose, mt: 1.5 }}>{t.lead}</Typography>
        </PageHeader>

        {/* --- Grundbegriffe --- */}
        <Section heading={t.conceptsHeading}>
          <TripletGrid items={t.concepts} />
          <SourceLine sources={t.conceptsSources} />
        </Section>

        {/* --- Die drei Schriften --- */}
        <Section heading={t.variantsHeading}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5 }}>
            {t.variants.map((v) => (
              <Box
                key={v.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  border: `1px solid ${paper.line}`,
                  borderRadius: '3px',
                  bgcolor: paper.hi,
                  p: { xs: 2.25, md: 2.5 },
                }}
              >
                <Typography variant="h4" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, lineHeight: 1.1 }}>
                  {v.name}
                </Typography>
                <Typography variant="caption" component="p" sx={{ fontStyle: 'italic', color: paper.sepia, mt: 0.25 }}>
                  {v.period}
                </Typography>

                {/* specimen box + caption — caption is state-aware for Sütterlin */}
                <SpecimenBlock id={v.id} />

                <Typography variant="body2" sx={{ ...prose, mt: 1.75 }}>{v.essence}</Typography>

                {/* Steckbrief — key/value rows on hairlines */}
                <Box sx={{ mt: 1.75 }}>
                  {v.facts.map((f) => (
                    <Box key={f.k} sx={{ display: 'flex', gap: 1.5, py: 0.6, borderTop: `1px solid ${paper.line}` }}>
                      <Typography variant="caption" sx={{ ...prose, color: paper.sepia, minWidth: 84, flexShrink: 0 }}>
                        {f.k}
                      </Typography>
                      <Typography variant="caption" sx={{ ...prose, color: paper.ink }}>{f.v}</Typography>
                    </Box>
                  ))}
                </Box>

                {'note' in v && v.note && (
                  <Typography variant="caption" component="p" sx={{ fontStyle: 'italic', color: paper.sepia, mt: 1 }}>
                    {v.note}
                  </Typography>
                )}

                <Box sx={{ flexGrow: 1 }} />
                <SourceLine sources={v.sources} sx={{ mt: 1.5 }} />
              </Box>
            ))}
          </Box>
        </Section>

        {/* --- Einordnung & Abgrenzung --- */}
        <Section heading={t.classifyHeading} lead={t.classifyLead}>
          <DefinitionRows items={t.classify} />
          <SourceLine sources={t.classifySources} />
        </Section>

        {/* --- Wo wurde so geschrieben --- */}
        <Section heading={t.geographyHeading} lead={t.geographyLead}>
          <DefinitionRows items={t.geography} />
          <SourceLine sources={t.geographySources} />
        </Section>

        {/* --- Warum wir heute nicht mehr so schreiben --- */}
        <Section heading={t.endHeading}>
          <Prose align="left">
            {t.endParagraphs.map((p, i) => (
              <Typography key={i} sx={{ ...prose, mt: i === 0 ? 0 : 1.25 }}>
                {p}
              </Typography>
            ))}
          </Prose>
          <SourceLine sources={t.endSources} />
        </Section>

        {/* --- Federn & Striche --- */}
        <Section heading={t.federnHeading} lead={t.federnLead}>
          <TripletGrid items={t.federn} />
          <SourceLine sources={t.federnSources} />
        </Section>

        {/* --- Tinte & Papier --- */}
        <Section heading={t.materialHeading} lead={t.materialLead}>
          <DefinitionRows items={t.material} />
          <SourceLine sources={t.materialSources} />
        </Section>

        {/* --- Buchstaben-Besonderheiten --- */}
        <Section heading={t.lettersHeading} lead={t.lettersLead}>
          <DefinitionRows items={t.letters} />
          <SourceLine sources={t.lettersSources} />
        </Section>

        {/* --- Zahlen & Zeichen --- */}
        <Section heading={t.signsHeading} lead={t.signsLead}>
          <DefinitionRows items={t.signs} />
          <SourceLine sources={t.signsSources} />
        </Section>

        {/* --- Chronologie --- */}
        <Section heading={t.timelineHeading}>
          {t.timeline.map((row) => (
            <Box
              key={row.year}
              sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0, sm: 2 }, py: 0.9, borderBottom: `1px solid ${paper.line}` }}
            >
              <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.viridian, minWidth: { sm: 110 }, flexShrink: 0 }}>
                {row.year}
              </Typography>
              <Typography variant="body2" sx={prose}>{row.text}</Typography>
            </Box>
          ))}
          <Typography variant="body2" sx={{ ...prose, mt: 1.5, fontStyle: 'italic', maxWidth: '62ch' }}>
            {t.timelineNote}
          </Typography>
          <SourceLine sources={t.timelineSources} />
        </Section>

        {/* --- Quellen — scholarly/archive sources first, Wikipedia as overview --- */}
        <Section heading={t.sourcesHeading}>
          <Typography variant="body2" sx={{ ...prose, maxWidth: '62ch' }}>{t.sourcesIntro}</Typography>
          {[
            { label: t.sourcesScholarlyHeading, items: t.sourcesScholarly as readonly SourceRef[] },
            { label: t.sourcesWikipediaHeading, items: t.sourcesWikipedia as readonly SourceRef[] },
          ].map((group) => (
            <Box key={group.label} sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.sepia }}>
                {group.label}
              </Typography>
              <Box component="ul" sx={{ mt: 0.75, mb: 0, pl: 3 }}>
                {group.items.map((s) => (
                  <Typography key={s.href} variant="body2" component="li" sx={{ ...prose, mb: 0.4 }}>
                    <Link href={s.href} target="_blank" rel="noopener noreferrer" sx={proseLink}>
                      {s.label}
                    </Link>
                  </Typography>
                ))}
              </Box>
            </Box>
          ))}
          <Typography variant="body2" sx={{ ...prose, mt: 1.5, fontStyle: 'italic' }}>{t.sourcesRepo}</Typography>
        </Section>

        {/* --- Weiterlernen (Süß-Empfehlung) --- */}
        <Section heading={t.recommendation.heading}>
          <Box sx={{ borderLeft: `2px solid ${paper.viridian}`, pl: 2, py: 0.25 }}>
            <Typography sx={{ ...prose, maxWidth: '62ch' }}>
              {t.recommendation.before}
              <Link href={t.recommendation.href} target="_blank" rel="noopener noreferrer" sx={proseLink}>
                {t.recommendation.linkLabel}
              </Link>
              {t.recommendation.after}
            </Typography>
          </Box>
          <Typography sx={{ ...prose, mt: 1.5, maxWidth: '62ch' }}>
            {t.recommendation.practiceIntro}
          </Typography>
          <Box component="ul" sx={{ mt: 0.75, mb: 0, pl: 3 }}>
            {t.recommendation.practiceLinks.map((s) => (
              <Typography key={s.href} variant="body2" component="li" sx={{ ...prose, mb: 0.4 }}>
                <Link href={s.href} target="_blank" rel="noopener noreferrer" sx={proseLink}>
                  {s.label}
                </Link>
              </Typography>
            ))}
          </Box>
        </Section>
      </PageContainer>
    </PublicLayout>
  );
}
