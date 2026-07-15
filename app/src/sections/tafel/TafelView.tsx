// TafelView — the public writing-chart page (`/tafel`, German "Schreibtafel").
// Shows the three German Ausgangsschriften (Kurrent · Sütterlin · Offenbacher)
// one below the other, each with whatever the DB holds today (see useGrundtafeln):
//   - written  — Original/Geschrieben toggle. "Geschrieben" is the WrittenSheet:
//     the locked, traced letters written on a ruled practice sheet (in the
//     chart's own rows); clicking one re-writes it in place.
//   - original — only the Original scan + an honest "noch nicht nachgeschrieben".
//   - pending  — a placeholder (no chart source seeded yet).
//
// Unlike the quiz this page does NOT ride the pinned AdminProvider (one source):
// useGrundtafeln fetches all chart sources read-only and groups them by style.

import { Box, Chip, Link, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { useLocation } from 'react-router-dom';

import { BootStatus } from '@/components/BootStatus';
import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { WrittenSheet } from '@/sections/tafel/WrittenSheet';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { chartUrl } from '@/lib/api';
import type { SourceOut } from '@/lib/api';
import { de } from '@/locales';
import { garamond, paper } from '@/styles/paper';
import { useGrundtafeln, type Grundtafel } from '@/sections/tafel/useGrundtafeln';

type View = 'original' | 'written';

// Friendly German labels for the short license codes stored on a source; the raw
// code is the fallback for anything not mapped here.
const LICENSE_LABELS: Record<string, string> = {
  PD: 'Gemeinfrei (Public Domain)',
  CC0: 'CC0 (gemeinfrei)',
};

// The provenance of one chart source (title, attribution, license, link), shown
// under each script that has a scan.
function SourceProvenance({ source }: { source: SourceOut }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, bgcolor: paper.hi }}>
      <Stack spacing={1}>
        {/* h3: sits under the per-script CategoryHeading <h2> */}
        <Typography component="h3" variant="h6" sx={{ fontFamily: garamond, fontWeight: 400, fontStyle: 'italic' }}>
          {de.tafel.source.heading}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {source.title}
        </Typography>
        {source.attribution && (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {source.attribution}
          </Typography>
        )}
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {de.tafel.source.licenseLabel}: {LICENSE_LABELS[source.license] ?? source.license}
        </Typography>
        {source.origin_url && (
          <Link
            href={source.origin_url}
            target="_blank"
            rel="noopener noreferrer"
            variant="body2"
            sx={{ color: paper.viridianText, alignSelf: 'flex-start' }}
          >
            {de.tafel.source.originLink}
          </Link>
        )}
      </Stack>
    </Paper>
  );
}

// The Original chart scan. A plain click/tap toggles zoom to 1:1 pixels (toward
// the tapped point) — on a phone the alphabet rows are tiny, so this makes them
// legible without leaving the page. While zoomed, press-and-drag pans the sheet
// with mouse OR finger (pointer events); a clean tap zooms back out. A 6px move
// threshold separates a pan (hold + drag) from a tap (click).
function OriginalScan({ source }: { source: SourceOut }) {
  const [zoomed, setZoomed] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  // The tapped point as a fraction of the image, kept so the effect can centre
  // it once the larger (zoomed) image has laid out.
  const focus = useRef<{ fx: number; fy: number }>({ fx: 0.5, fy: 0.5 });
  // Drag bookkeeping. `moved` distinguishes a pan from a tap so a tap still
  // toggles the zoom while a drag only pans.
  const drag = useRef({ active: false, moved: false, x: 0, y: 0, left: 0, top: 0 });

  const onPointerDown = (e: ReactPointerEvent<HTMLDivElement>) => {
    // Only react to the primary button / first contact: a tap toggles the zoom,
    // so a right- or middle-click and secondary touch points must be ignored.
    if (e.button !== 0 || !e.isPrimary) return;
    const box = boxRef.current;
    const img = imgRef.current;
    if (!box) return;
    drag.current = { active: true, moved: false, x: e.clientX, y: e.clientY, left: box.scrollLeft, top: box.scrollTop };
    // Compute the zoom focus only once the image has laid out — a zero
    // offsetWidth/Height would make the focus fraction Infinity/NaN.
    if (!zoomed && img && img.offsetWidth > 0 && img.offsetHeight > 0) {
      const r = box.getBoundingClientRect();
      focus.current = {
        fx: (box.scrollLeft + e.clientX - r.left) / img.offsetWidth,
        fy: (box.scrollTop + e.clientY - r.top) / img.offsetHeight,
      };
    }
    // capture only while zoomed so a press-drag keeps panning past the edges;
    // unzoomed we leave the pointer free so a page scroll can still cancel it.
    // (capture can throw for a stale pointer id — never let that break the drag.)
    if (zoomed) {
      try {
        box.setPointerCapture(e.pointerId);
      } catch {
        /* pointer already released */
      }
    }
  };

  const onPointerMove = (e: ReactPointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d.active) return;
    const dx = e.clientX - d.x;
    const dy = e.clientY - d.y;
    if (Math.abs(dx) > 6 || Math.abs(dy) > 6) d.moved = true;
    if (zoomed && boxRef.current) {
      boxRef.current.scrollLeft = d.left - dx;
      boxRef.current.scrollTop = d.top - dy;
    }
  };

  const endPointer = (e: ReactPointerEvent<HTMLDivElement>, tap: boolean) => {
    const d = drag.current;
    try {
      boxRef.current?.releasePointerCapture(e.pointerId);
    } catch {
      /* nothing captured */
    }
    if (!d.active) return;
    d.active = false;
    // a clean tap (no drag) toggles zoom; a drag (pan, or an aborted page
    // scroll) leaves the zoom state alone
    if (tap && !d.moved) setZoomed((z) => !z);
  };

  // After the zoom toggles, place the tapped point near the centre of the box.
  useEffect(() => {
    const box = boxRef.current;
    const img = imgRef.current;
    if (!box || !img) return;
    if (zoomed) {
      box.scrollLeft = focus.current.fx * img.offsetWidth - box.clientWidth / 2;
      box.scrollTop = focus.current.fy * img.offsetHeight - box.clientHeight / 2;
    } else {
      box.scrollTo({ top: 0, left: 0 });
    }
  }, [zoomed]);

  return (
    <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fff' }}>
      <Box
        ref={boxRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={(e) => endPointer(e, true)}
        onPointerCancel={(e) => endPointer(e, false)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setZoomed((z) => !z);
          }
        }}
        role="button"
        tabIndex={0}
        // The zoom-in / grab cursor signals the affordance on hover, so no
        // visible hint caption is needed — the aria-label keeps it accessible.
        aria-label={zoomed ? de.tafel.zoomOut : de.tafel.zoomIn}
        sx={{
          overflow: zoomed ? 'auto' : 'hidden',
          maxHeight: zoomed ? '78vh' : 'none',
          cursor: zoomed ? 'grab' : 'zoom-in',
          '&:active': { cursor: zoomed ? 'grabbing' : 'zoom-in' },
          lineHeight: 0,
          // while zoomed we pan ourselves, so stop the browser from scrolling
          touchAction: zoomed ? 'none' : 'auto',
        }}
      >
        <Box
          component="img"
          ref={imgRef}
          src={chartUrl(source.id)}
          alt={de.tafel.originalAlt}
          draggable={false}
          sx={{
            display: 'block',
            width: zoomed ? 'auto' : '100%',
            maxWidth: zoomed ? 'none' : '100%',
            height: 'auto',
            userSelect: 'none',
          }}
        />
      </Box>
    </Paper>
  );
}

// One script's section: heading + Feder/state caption, then the body by state.
function GrundtafelSection({ tafel }: { tafel: Grundtafel }) {
  // Original is the default everywhere; the written grid is one toggle away.
  const [view, setView] = useState<View>('original');
  const feder = de.tafel.feder[tafel.styleId];

  return (
    // `id` makes the section a deep-link target (landing links to /tafel#<styleId>);
    // the scroll offset is applied in JS (TafelView), measuring the live header.
    <Stack component="section" id={tafel.styleId} spacing={2} aria-label={tafel.name}>
      <Box>
        <CategoryHeading>{tafel.name}</CategoryHeading>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          {feder ? (
            <Typography variant="body2" sx={{ color: paper.inkSoft }}>
              {feder}
            </Typography>
          ) : null}
          <Chip
            size="small"
            label={de.tafel.state[tafel.state]}
            variant="outlined"
            sx={{
              color: tafel.state === 'written' ? paper.viridianText : paper.inkSoft,
              borderColor: tafel.state === 'written' ? paper.viridian : paper.line,
              bgcolor: 'transparent',
            }}
          />
        </Box>
      </Box>

      {tafel.state === 'written' && tafel.source ? (
        <>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={view}
            onChange={(_, v: View | null) => v && setView(v)}
            aria-label={de.tafel.viewToggleAria}
            sx={{ alignSelf: 'flex-start' }}
          >
            <ToggleButton value="original">{de.tafel.viewOriginal}</ToggleButton>
            <ToggleButton value="written">{de.tafel.viewWritten}</ToggleButton>
          </ToggleButtonGroup>
          {view === 'written' ? (
            <WrittenSheet rows={tafel.rows} ratio={tafel.source.style_ratio} />
          ) : (
            <OriginalScan source={tafel.source} />
          )}
          <SourceProvenance source={tafel.source} />
        </>
      ) : tafel.state === 'original' && tafel.source ? (
        <>
          <OriginalScan source={tafel.source} />
          <SourceProvenance source={tafel.source} />
        </>
      ) : (
        <Paper
          variant="outlined"
          sx={{ p: { xs: 3, sm: 5 }, bgcolor: paper.hi, textAlign: 'center', borderStyle: 'dashed' }}
        >
          <Typography sx={{ color: paper.inkSoft, maxWidth: '50ch', mx: 'auto' }}>{de.tafel.pendingNote}</Typography>
        </Paper>
      )}
    </Stack>
  );
}

export function TafelView() {
  const { tafeln, loadError, waking } = useGrundtafeln();
  const { hash } = useLocation();

  // Deep-link from the landing's script cards (/tafel#<styleId>): once the
  // sections exist, scroll the requested one clear of the sticky header (the
  // root ScrollToTop already reset us to the top). Two moving parts make a
  // single scroll unreliable: the PublicHeader wraps to two rows on mobile (so
  // its height isn't constant — #126), and the original scans load async and
  // reflow the sections above the target after the first scroll. So measure the
  // live header height, and re-align on every reflow (ResizeObserver) until the
  // user scrolls or ~1.5s passes — never fighting the user's own scrolling.
  useEffect(() => {
    if (!tafeln || !hash) return;
    const id = hash.slice(1);
    let settle: ReturnType<typeof setTimeout> | undefined;
    const scrollToSection = () => {
      const el = document.getElementById(id);
      if (!el) return;
      const header = document.querySelector('header');
      const offset = (header?.getBoundingClientRect().height ?? 0) + 16;
      window.scrollTo({ top: Math.max(0, el.getBoundingClientRect().top + window.scrollY - offset) });
    };
    const stop = () => {
      ro.disconnect();
      if (settle) clearTimeout(settle);
      if (cap) clearTimeout(cap);
      window.removeEventListener('wheel', stop);
      window.removeEventListener('touchmove', stop);
      window.removeEventListener('keydown', stop);
    };
    // Re-align on every reflow, but stop once the page has held still for 400ms
    // (the last scan/font has loaded) — a fixed delay under-aligns the lower
    // sections when an upper scan loads late. A 4s cap + user-scroll both abort.
    const onReflow = () => {
      scrollToSection();
      if (settle) clearTimeout(settle);
      settle = setTimeout(stop, 400);
    };
    const ro = new ResizeObserver(onReflow);
    scrollToSection();
    ro.observe(document.body);
    window.addEventListener('wheel', stop, { passive: true });
    window.addEventListener('touchmove', stop, { passive: true });
    window.addEventListener('keydown', stop);
    const cap = setTimeout(stop, 4000);
    return stop;
  }, [tafeln, hash]);

  // Boot/error states render inside PublicLayout so the header nav and footer
  // stay usable during a cold start instead of vanishing with the page.
  if (loadError) {
    return (
      <PublicLayout footer>
        <BootStatus
          variant="error"
          title={de.common.boot.sourceUnreachable}
          message={loadError}
          onRetry={() => window.location.reload()}
          retryLabel={de.common.boot.retry}
        />
      </PublicLayout>
    );
  }

  if (!tafeln) {
    return (
      <PublicLayout footer>
        <BootStatus
          variant="loading"
          message={waking ? de.common.boot.sourceColdStart : de.common.boot.loadingTemplate}
        />
      </PublicLayout>
    );
  }

  return (
    <PublicLayout footer>
      <PageContainer width="text" sx={{ pt: { xs: 4, sm: 6 } }}>
        <PageHeader eyebrow={de.common.nav.read} title={de.tafel.title}>
          <Typography sx={{ color: paper.inkSoft }}>{de.tafel.intro}</Typography>
          <Typography sx={{ color: paper.inkSoft, mt: 1.5 }}>{de.tafel.note}</Typography>
        </PageHeader>
        <Stack spacing={{ xs: 5, sm: 7 }}>
          {tafeln.map((t) => (
            <GrundtafelSection key={t.styleId} tafel={t} />
          ))}
        </Stack>
      </PageContainer>
    </PublicLayout>
  );
}
