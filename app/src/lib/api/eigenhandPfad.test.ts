// The two wrappers around the per-box Bahn write — the first place in this
// client where a response HEADER is part of the contract.
//
// What is worth pinning here is not the URL but the token's round trip: the
// read has to hand it out, the write has to send it back as `If-Match`, and the
// write's own answer has to carry the NEXT one. Drop any of the three and the
// editor still looks like it works — right up to the save that silently lands
// on a list a follower run replaced, which is the failure this route exists to
// make impossible.

import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import { getEigenhandPfadeWithEtag, patchEigenhandPfad } from '@/lib/api/endpoints';
import type { EigenhandPfad } from '@/lib/api/types';

const LIST = { hand: 'mn-suetterlin', strip: 'S0001', fassung: 'F01', format: 2, pfade: [], boxes: [] };

const answer = (etag: string | null, body: unknown = LIST): Response =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: etag ? { 'Content-Type': 'application/json', ETag: etag } : { 'Content-Type': 'application/json' },
  });

/** A box as the editor hands it over — everything but the provenance. */
const drawn = (): Omit<EigenhandPfad, 'verfahren'> => ({
  box_index: 3,
  word: 'lesen',
  status: null,
  grund: null,
  detail: null,
  strokes: [
    [
      [0, 0],
      [1, 1],
    ],
  ],
  letter_spans: null,
  registration_px: { tx: 40, ty: 0, baseline_row: 240 },
  xh_px: 120,
  konfiguration: {},
  meta: {},
  erzeugt_am: '2026-09-20',
  flecken_n: 0,
});

describe('the per-box Bahn write', () => {
  let fetchMock: Mock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  it('hands the read token out beside the list', async () => {
    fetchMock.mockResolvedValue(answer('"abc"'));

    const read = await getEigenhandPfadeWithEtag('mn-suetterlin', 'S0001', 'F01');

    expect(read.etag).toBe('"abc"');
    expect(read.list.format).toBe(2);
  });

  it('says so when an intermediary dropped the header', async () => {
    // Null rather than an empty string: a save then has nothing to send, and
    // the caller has to re-read instead of writing blind.
    fetchMock.mockResolvedValue(answer(null));

    expect((await getEigenhandPfadeWithEtag('mn-suetterlin', 'S0001', 'F01')).etag).toBeNull();
  });

  it('sends the token back as If-Match and stamps the provenance itself', async () => {
    fetchMock.mockResolvedValue(answer('"second"'));

    const saved = await patchEigenhandPfad('mn-suetterlin', 'S0001', 'F01', 3, drawn(), '"first"', 2);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/eigenhand\/strips\/mn-suetterlin\/S0001\/F01\/pfade\/3$/);
    expect(init.method).toBe('PATCH');
    expect((init.headers as Record<string, string>)['If-Match']).toBe('"first"');
    // `verfahren` is never a parameter — the route stamps `authored`, and the
    // wrapper sends exactly that so a caller cannot ask for anything else.
    expect(JSON.parse(init.body as string)).toMatchObject({
      format: 2,
      pfad: { box_index: 3, verfahren: 'authored' },
    });
    // The answer carries the token the NEXT save needs, so „Speichern & weiter"
    // never has to re-read between two boxes.
    expect(saved.etag).toBe('"second"');
  });

  it('raises the server refusal a stale token earns', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: 'the stored paths have moved on since this was read' }), {
        status: 412,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(patchEigenhandPfad('mn-suetterlin', 'S0001', 'F01', 3, drawn(), '"stale"', 2)).rejects.toMatchObject({
      status: 412,
    });
  });
});
