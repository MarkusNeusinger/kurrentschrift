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
//                   (its round End-s sits on '#'), so the fallback word
//                   "sütterlin" renders its initial long-s without needing U+017F.
//   · Offenbacher — a marked excerpt from Koch's own public-domain 1928 plate
//                   (the genuine historical hand, not a synthesised glyph).
//
// Navigation: every <section> carries a stable id (sections/schriftkunde/
// sections.ts) and a jump list under the page header links them — the page
// has fourteen sections. The Buchstaben-Besonderheiten rows carry a specimen
// strip each: the letters the row talks about, written live by the engine
// from the public Sütterlin source (WrittenGlyph), labelled with their Antiqua
// letter — design-system §9's "marked specimen on its own surface".

import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Box, ButtonBase, Link, Typography } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import type { SxProps, Theme } from '@mui/material/styles';
import offenbacherSpecimen from '@/assets/specimens/offenbacher-koch-1928-excerpt.jpg';
import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { PaperCardCta, PaperCardLink } from '@/components/PaperCardLink';
import { Prose } from '@/components/Prose';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { WrittenWord } from '@/components/WrittenWord';
import { CONFIG } from '@/global-config';
import { useInView } from '@/hooks/useInView';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { fetchRenderGlyphs, type GlyphRenderData } from '@/lib/api';
import { de } from '@/locales';
import { schriftkunde } from '@/locales/de/schriftkunde';
import { paths } from '@/routes/paths';
import { SCHRIFTKUNDE_SECTIONS, SECTION_IDS, type SectionId } from '@/sections/schriftkunde/sections';
import { TRY_TARGETS } from '@/sections/schriftkunde/tryTargets';
import { display, garamond, paper, script, suetterlin } from '@/styles/paper';

// Imported directly, not via the `de` barrel: this route chunk is the only
// consumer, and the direct import keeps the namespace (~7 kB gz measured on
// the eager locales chunk) out of the eager public bundle (see
// locales/index.ts).
const t = schriftkunde;

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
  '&:hover': { color: paper.viridianText, textDecorationColor: paper.viridian },
} as const;

type SourceRef = { label: string; href: string };
type TermItem = { term: string; desc: string };
// A letter row's specimens: the public source's glyph_key + the Antiqua label.
type Specimen = { readonly key: string; readonly label: string };
type LetterItem = TermItem & { readonly specimens?: readonly Specimen[] };

// Fragment targets sit under the sticky PublicHeader; the scroll margin keeps
// a jumped-to heading clear of it (jump list, /schriftkunde#… URLs). Measured
// header: ~82 px on phones (the nav wraps to a second line), ~67 px from md.
const anchorSx = { scrollMarginTop: { xs: 100, md: 84 } } as const;

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
// `id` is the fragment target the jump list and the prerender share.
function Section({ id, heading, lead, children }: { id: SectionId; heading: string; lead?: string; children: ReactNode }) {
  return (
    <Box component="section" id={id} sx={{ mt: { xs: 5, md: 6 }, ...anchorSx }}>
      <CategoryHeading>{heading}</CategoryHeading>
      {lead && <Typography sx={{ ...prose, mb: 1.75, maxWidth: '64ch' }}>{lead}</Typography>}
      {children}
    </Box>
  );
}

// "Auf dieser Seite" — the jump list under the page header, one link per
// section in page order. Plain fragment anchors on purpose (not RouterLink):
// the browser scrolls and sets the hash itself, the pathname stays, so the
// router's ScrollToTop does not fire.
function SectionNav() {
  return (
    <Box component="nav" aria-label={t.tocLabel} sx={{ mt: 3, pt: 1.5, borderTop: `1px solid ${paper.line}` }}>
      <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mb: 0.5 }}>
        {t.tocLabel}
      </Typography>
      <Box component="ol" sx={{ listStyle: 'none', m: 0, p: 0, display: 'flex', flexWrap: 'wrap', rowGap: 0.25 }}>
        {SCHRIFTKUNDE_SECTIONS.map((s, i) => (
          <Box component="li" key={s.id} sx={{ display: 'inline' }}>
            <Link href={`#${s.id}`} variant="body2" sx={proseLink}>
              {s.heading}
            </Link>
            {/* trailing separator, so a wrapped line ends on the dot rather than starting with one */}
            {i < SCHRIFTKUNDE_SECTIONS.length - 1 && (
              <Box component="span" aria-hidden sx={{ mx: 0.75, color: paper.sepia }}>
                ·
              </Box>
            )}
          </Box>
        ))}
      </Box>
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
          <Typography variant="h6" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 0.75 }}>{c.term}</Typography>
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

// --- Buchstaben-Besonderheiten with specimen strips -------------------------

const SPECIMEN_H = 84;

// The section's render payloads by glyph_key: `null` while the batch is in
// flight; a glyph maps to null when the source has no canonical for it, and
// every key is absent when the engine could not be reached.
type Payloads = ReadonlyMap<string, GlyphRenderData | null>;

// One written form with its Antiqua label. The payload arrives from the
// section's batch (WrittenGlyph's `data` — no fetch of its own); a click
// writes it again (remount; only the reveal restarts).
function SpecimenCell({ glyphKey, label, data }: { glyphKey: string; label: string; data: GlyphRenderData }) {
  const [run, setRun] = useState(0);
  return (
    <ButtonBase
      onClick={() => setRun((r) => r + 1)}
      aria-label={`${label} — ${de.common.writtenGlyph.replay}`}
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5, px: 0.5, borderRadius: '3px' }}
    >
      <Box sx={{ height: SPECIMEN_H, display: 'flex', alignItems: 'center' }}>
        <WrittenGlyph key={run} glyphKey={glyphKey} data={data} height={SPECIMEN_H} surfaceBg="transparent" showReplay={false} />
      </Box>
      <Typography variant="caption" component="span" aria-hidden sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.sepia, lineHeight: 1 }}>
        {label}
      </Typography>
    </ButtonBase>
  );
}

// The specimen strip of one row on its own hairline surface (design-system
// §9). Its cells mount only near the viewport, so the write-in plays when the
// reader arrives rather than at page load below the fold. While the batch is
// in flight the frame holds the space; once it has answered and none of the
// row's glyphs can be written (no canonical, engine unreachable) the strip
// goes entirely — no empty frame, no error box inside public prose.
function SpecimenStrip({ specimens, payloads }: { specimens: readonly Specimen[]; payloads: Payloads | null }) {
  const [ref, inView] = useInView<HTMLDivElement>('120px');
  const forms = specimens.map((s) => ({ ...s, data: payloads?.get(s.key) ?? null }));
  if (payloads && forms.every((f) => !f.data)) return null;
  return (
    <Box
      ref={ref}
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: 1,
        px: 1.25,
        py: 0.75,
        minHeight: SPECIMEN_H + 30,
        border: `1px solid ${paper.line}`,
        borderRadius: '3px',
        bgcolor: paper.hi,
        flexShrink: 0,
        alignSelf: { xs: 'flex-start', md: 'center' },
      }}
    >
      {inView &&
        forms.map((f, i) => f.data && <SpecimenCell key={`${f.key}-${i}`} glyphKey={f.key} label={f.label} data={f.data} />)}
    </Box>
  );
}

// The Buchstaben-Besonderheiten rows: DefinitionRows' layout plus a specimen
// strip beside the description where the row names one. ONE batch request
// (renderCache) fetches every specimen of the section as soon as it comes
// near; the cells render from that payload map. The caption that calls the
// strips "live geschrieben" stays only while a strip can show something — it
// never describes what is not on screen.
function LetterRows({ items }: { items: readonly LetterItem[] }) {
  const keys = useMemo(() => [...new Set(items.flatMap((it) => (it.specimens ?? []).map((s) => s.key)))], [items]);
  const [ref, near] = useInView<HTMLDivElement>('400px');
  const [payloads, setPayloads] = useState<Payloads | null>(null);
  useEffect(() => {
    if (!near) return undefined;
    let cancelled = false;
    fetchRenderGlyphs(CONFIG.sourceId, keys)
      .then((m) => {
        if (!cancelled) setPayloads(m);
      })
      .catch(() => {
        if (!cancelled) setPayloads(new Map()); // unreachable engine: the strips withdraw
      });
    return () => {
      cancelled = true;
    };
  }, [near, keys]);
  const showNote = !payloads || items.some((it) => it.specimens?.some((s) => payloads.get(s.key)));
  return (
    <>
      {showNote && (
        <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: -0.75, mb: 1.5, maxWidth: '64ch' }}>
          {t.lettersSpecimenNote}
        </Typography>
      )}
      <Box ref={ref} sx={{ borderBottom: `1px solid ${paper.line}` }}>
        {items.map((it) => (
          <Box
            key={it.term}
            sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0.25, sm: 2.5 }, py: 1.1, borderTop: `1px solid ${paper.line}` }}
          >
            <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, minWidth: { sm: 196 }, flexShrink: 0, pt: { sm: 0.15 } }}>
              {it.term}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: { xs: 1, md: 2.5 }, flexGrow: 1, alignItems: { md: 'center' } }}>
              <Typography variant="body2" sx={{ ...prose, flexGrow: 1 }}>
                {it.desc}
              </Typography>
              {it.specimens?.length ? <SpecimenStrip specimens={it.specimens} payloads={payloads} /> : null}
            </Box>
          </Box>
        ))}
      </Box>
    </>
  );
}

// Show-script font specimen style for the Kurrent card only (the GLKurrent face).
// The Sütterlin fallback has its own face — see suetterlinFontSx (Zinken HJZ 1911).
const fontSpecimenSx = { fontFamily: script, fontSize: 'clamp(3.5rem, 9vw, 4.8rem)', color: paper.ink, lineHeight: 1 } as const;
// Sütterlin cold-start fallback: the bundled Zinken HJZ 1911 face (a genuine
// Sütterlin school hand), distinct from the Kurrent show-script above.
const suetterlinFontSx = { fontFamily: suetterlin, fontSize: 'clamp(2.5rem, 6.5vw, 3.5rem)', color: paper.ink, lineHeight: 1 } as const;
// Minimum-height specimen box so the three cards line up; each specimen is sized
// to fill it generously (the script is the card's hero). It's a min-height, not a
// hard height — the box may grow if a specimen ever exceeds it, but none does.
const specimenBoxSx = {
  mt: 1.75,
  minHeight: 132,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderTop: `1px solid ${paper.line}`,
  borderBottom: `1px solid ${paper.line}`,
  py: 1.75,
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
  // No `= null` seed: every branch below assigns it, so the initialiser would be
  // dead (`no-useless-assignment`, error in ESLint 10's recommended set).
  let caption: string;

  if (id === 'kurrent') {
    content = <Box sx={fontSpecimenSx}>{t.variants[0].name}</Box>;
    caption = t.specimen.kurrentCaption;
  } else if (id === 'suetterlin') {
    content = fallback ? (
      <Box sx={suetterlinFontSx}>{t.specimen.suetterlinWordFallback}</Box>
    ) : (
      <WrittenWord
        text={t.specimen.suetterlinWord}
        height={104}
        durationMs={2400}
        maxWidth={300}
        showReplay
        onResolved={onResolved}
        onError={onError}
      />
    );
    caption = fallback ? t.specimen.suetterlinCaptionFallback : t.specimen.suetterlinCaption;
  } else {
    // offenbacher — a tight, centred excerpt from Koch's own public-domain 1928
    // plate (lowercase a–f). The tighter crop lets the letters render large and
    // fill the box like the other two cards; `multiply` drops the scan's white
    // ground onto the paper.
    content = (
      <Box
        component="img"
        src={offenbacherSpecimen}
        alt={t.specimen.offenbacherAlt}
        loading="lazy"
        sx={{ width: '100%', height: 'auto', display: 'block', mixBlendMode: 'multiply' }}
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
  // A /schriftkunde#… URL: the router's ScrollToTop has run for the pathname
  // and the browser's own fragment jump predates this lazy chunk — so scroll
  // to the section once the page is on screen (and again on a hash change).
  const { hash } = useLocation();
  useEffect(() => {
    const id = hash.slice(1);
    if (id) document.getElementById(id)?.scrollIntoView();
  }, [hash]);

  return (
    <PublicLayout footer>
      <PageContainer sx={{ pt: { xs: 4, md: 6 } }}>
        {/* shared page header — eyebrow (area) + Playfair title + intro */}
        <PageHeader eyebrow={t.eyebrow} title={t.title}>
          <Typography sx={{ ...prose, color: paper.ink }}>{t.intro}</Typography>
          <Typography sx={{ ...prose, mt: 1.5 }}>{t.lead}</Typography>
        </PageHeader>

        <SectionNav />

        {/* --- Grundbegriffe --- */}
        <Section id={SECTION_IDS.concepts} heading={t.conceptsHeading}>
          <TripletGrid items={t.concepts} />
          <SourceLine sources={t.conceptsSources} />
        </Section>

        {/* --- the three script variants ("Die drei Schriften") --- */}
        <Section id={SECTION_IDS.variants} heading={t.variantsHeading}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5 }}>
            {t.variants.map((v) => (
              // id: the Kennwerte JSON-LD in the prerender links each script as
              // /schriftkunde#<id> — the card is that target.
              <Box
                key={v.id}
                id={v.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  border: `1px solid ${paper.line}`,
                  borderRadius: '3px',
                  bgcolor: paper.hi,
                  p: { xs: 2.25, md: 2.5 },
                  ...anchorSx,
                }}
              >
                <Typography variant="h4" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, lineHeight: 1.1 }}>
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

        {/* --- classification ("Einordnung & Abgrenzung") --- */}
        <Section id={SECTION_IDS.classify} heading={t.classifyHeading} lead={t.classifyLead}>
          <DefinitionRows items={t.classify} />
          <SourceLine sources={t.classifySources} />
        </Section>

        {/* --- geography ("Wo wurde so geschrieben") --- */}
        <Section id={SECTION_IDS.geography} heading={t.geographyHeading} lead={t.geographyLead}>
          <DefinitionRows items={t.geography} />
          <SourceLine sources={t.geographySources} />
        </Section>

        {/* --- why we no longer write this way ("Warum wir heute nicht mehr so schreiben") --- */}
        <Section id={SECTION_IDS.end} heading={t.endHeading}>
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
        <Section id={SECTION_IDS.federn} heading={t.federnHeading} lead={t.federnLead}>
          <TripletGrid items={t.federn} />
          <SourceLine sources={t.federnSources} />
        </Section>

        {/* --- Tinte & Papier --- */}
        <Section id={SECTION_IDS.material} heading={t.materialHeading} lead={t.materialLead}>
          <DefinitionRows items={t.material} />
          <SourceLine sources={t.materialSources} />
        </Section>

        {/* --- Buchstaben-Besonderheiten — rows with live-written specimen strips --- */}
        <Section id={SECTION_IDS.letters} heading={t.lettersHeading} lead={t.lettersLead}>
          <LetterRows items={t.letters} />
          <SourceLine sources={t.lettersSources} />
        </Section>

        {/* --- Einen alten Brief entziffern ---
            Practical method steps (no historical claims → no SourceLine); the
            closing line points into the project's own Tafel. */}
        <Section id={SECTION_IDS.decipher} heading={t.decipherHeading} lead={t.decipherLead}>
          <DefinitionRows items={t.decipher} />
          <Typography variant="body2" sx={{ ...prose, mt: 1.5, maxWidth: '62ch' }}>
            {t.decipherTafel.before}
            <Link component={RouterLink} to={paths.tafel} sx={proseLink}>
              {t.decipherTafel.linkLabel}
            </Link>
            {t.decipherTafel.after}
          </Typography>
        </Section>

        {/* --- Zahlen & Zeichen --- */}
        <Section id={SECTION_IDS.signs} heading={t.signsHeading} lead={t.signsLead}>
          <DefinitionRows items={t.signs} />
          <SourceLine sources={t.signsSources} />
        </Section>

        {/* --- Chronologie --- */}
        <Section id={SECTION_IDS.timeline} heading={t.timelineHeading}>
          {t.timeline.map((row) => (
            <Box
              key={row.year}
              sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0, sm: 2 }, py: 0.9, borderBottom: `1px solid ${paper.line}` }}
            >
              <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.viridianText, minWidth: { sm: 110 }, flexShrink: 0 }}>
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
        <Section id={SECTION_IDS.sources} heading={t.sourcesHeading}>
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
        <Section id={SECTION_IDS.recommendation} heading={t.recommendation.heading}>
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

        {/* --- closing cross-links into the live tools ("Jetzt ausprobieren") ---
            The page must not dead-end in the source list: three cards lead into
            the quiz, the Schreibtafel and the Federprobe — same card pattern as
            the area hubs (sections/hub/HubView). */}
        <Section id={SECTION_IDS.try} heading={t.tryHeading} lead={t.tryLead}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
              gap: { xs: 2.5, md: 3 },
            }}
          >
            {t.tryCards.map((card) => (
              <PaperCardLink key={card.id} to={TRY_TARGETS[card.id]} sx={{ p: { xs: 3, md: 3.5 } }}>
                {/* h3: the cards sit under this Section's CategoryHeading <h2> */}
                <Typography variant="h5" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1 }}>
                  {card.title}
                </Typography>
                <Typography variant="body2" sx={{ color: paper.inkSoft, flexGrow: 1 }}>
                  {card.body}
                </Typography>
                <PaperCardCta>{card.cta}&nbsp;→</PaperCardCta>
              </PaperCardLink>
            ))}
          </Box>
        </Section>
      </PageContainer>
    </PublicLayout>
  );
}
