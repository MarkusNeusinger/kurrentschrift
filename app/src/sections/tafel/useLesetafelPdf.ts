// useLesetafelPdf — the browser half of the printable Lesetafel: gather what
// the Schreibtafel already knows (useGrundtafeln's three scripts), fetch the
// written letters' render payloads in one batch (renderCache — the page has
// most of them already), rasterise the original plates to JPEG through a
// canvas (the Loth and Sütterlin charts are served as SVG, Koch's as JPEG; a
// hand-rolled PDF embeds baseline JPEG only), compose with lib/lesetafel.ts
// and hand the file to the browser's download.

import { useCallback, useState } from 'react';

import { CONFIG } from '@/global-config';
import { chartUrl, fetchRenderGlyphs } from '@/lib/api';
import { lesetafelPdf, type LesetafelSheet, type PlateImage, type WrittenLetter } from '@/lib/lesetafel';
import { de } from '@/locales';
import type { Grundtafel } from '@/sections/tafel/useGrundtafeln';

// Long side of a rasterised plate in pixels: ~260 dpi on an A4 content box,
// sharp on paper without a multi-megabyte file.
const PLATE_LONG_SIDE_PX = 2200;
const JPEG_QUALITY = 0.85;

export type LesetafelState = 'idle' | 'building' | 'error';

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    // The API allows the site's origin (CORS), so the canvas stays untainted
    // and can be read back as JPEG.
    //
    // This attribute alone is not enough, and that is why TafelView's DISPLAY
    // image carries it too: a browser keys its HTTP cache by CORS mode. The
    // page shows the same plate URL, so whichever request goes first files the
    // entry — and a no-CORS entry answered to this CORS-mode load carries no
    // Access-Control-Allow-Origin, which the browser then blocks. Live on
    // 2026-09-02 that killed the button on every visit that had let the plate
    // load first (website audit, finding 2); if it ever comes back, check that
    // the <img> in TafelView still has crossOrigin="anonymous".
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`plate failed to load: ${url}`));
    img.src = url;
  });
}

async function plateJpeg(url: string): Promise<PlateImage> {
  const img = await loadImage(url);
  const natW = img.naturalWidth || img.width;
  const natH = img.naturalHeight || img.height;
  if (!natW || !natH) throw new Error('plate has no size');
  const scale = PLATE_LONG_SIDE_PX / Math.max(natW, natH);
  const width = Math.round(natW * scale);
  const height = Math.round(natH * scale);
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('no 2d context');
  // An SVG plate may be transparent — paper white behind it, like the screen.
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(img, 0, 0, width, height);
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
  if (!blob) throw new Error('jpeg encoding failed');
  return { jpeg: new Uint8Array(await blob.arrayBuffer()), width, height };
}

async function sheetsOf(tafeln: Grundtafel[]): Promise<LesetafelSheet[]> {
  const sheets: LesetafelSheet[] = [];
  for (const t of tafeln) {
    if (!t.source) continue; // pending: nothing to print yet
    const base = {
      name: t.name,
      feder: de.tafel.feder[t.styleId] ?? '',
      title: t.source.title,
      attribution: t.source.attribution ?? t.source.license,
    };
    if (t.state === 'written') {
      const slots = t.rows.flat().filter((s) => s.key !== null);
      const keys = slots.map((s) => s.key as string);
      const payloads = await fetchRenderGlyphs(CONFIG.sourceId, keys);
      const letters: WrittenLetter[] = [];
      for (const s of slots) {
        const data = payloads.get(s.key as string);
        if (data) letters.push({ glyph: s.glyph, data });
      }
      sheets.push({ ...base, kind: 'written', ratio: t.source.style_ratio, letters });
    } else {
      sheets.push({ ...base, kind: 'plate', image: await plateJpeg(chartUrl(t.source.id)) });
    }
  }
  return sheets;
}

function download(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Defer revocation so it can't race the download start on slower devices.
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export function useLesetafelPdf(tafeln: Grundtafel[] | null): { state: LesetafelState; build: () => void } {
  const [state, setState] = useState<LesetafelState>('idle');
  const build = useCallback(() => {
    if (!tafeln || state === 'building') return;
    setState('building');
    const t = de.tafel.pdf;
    sheetsOf(tafeln)
      .then((sheets) => {
        download(
          lesetafelPdf(sheets, {
            heading: t.heading,
            writtenLine: t.writtenLine,
            plateLine: t.plateLine,
            footer: t.footer,
            longS: t.longS,
          }),
          t.filename,
        );
        setState('idle');
      })
      .catch((e: unknown) => {
        console.error('lesetafel build failed', e);
        setState('error');
      });
  }, [tafeln, state]);
  return { state, build };
}
