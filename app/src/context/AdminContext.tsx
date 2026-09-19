// Shared admin state — active source, source metadata, bboxes-by-key,
// traced-glyph-status.
//
// The list of known glyph_keys is in `domain/glyphs.ts` (the MVP target set), so
// the sidebar can show all expected glyphs even before any bboxes exist. The
// DB only stores rows for glyphs that have actually been bbox'd or traced.
//
// The active source is admin-only runtime state (persisted per browser); the
// public pages stay pinned to CONFIG.sourceId. Switching remounts the whole
// per-source subtree via the React key below, so bboxes, glyph status,
// visibility, viewport and open modals reset without hand-written cleanup.
//
// The own HAND is the second scope, and it deliberately lives one level higher
// than all of that: the remount would wipe it on every Vorlage switch, and two
// Vorlagen of one script are supposed to share their hands (admin-redesign.md
// Q25 a). So the outer provider owns the choice and the candidates, and the
// inner one only resolves them against the Vorlage's script — V19 in
// `shell/handScope.ts`, never a branch here.

import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { AdminCtx, type AdminState } from '@/context/adminState';
import { CONFIG } from '@/global-config';
import { ApiError, getBboxes, getEigenhandHands, getEigenhandSetups, getGlyphs, getSource, getSources } from '@/lib/api';
import { de } from '@/locales';
import {
  handCandidates,
  handStyle,
  handsOfStyle,
  resolveHand,
  type HandCandidate,
} from '@/sections/admin/shell/handScope';
import type { BboxOut, GlyphSummary, SourceOut } from '@/lib/api';

const SOURCE_STORAGE_KEY = 'kurrentschrift.admin.sourceId';
// Per SCRIPT, not one id: with several Vorlagen per script the last hand of
// each is what makes a switch land where the author left off (V19).
const HAND_STORAGE_KEY = 'kurrentschrift.admin.handByStyle';

// What the outer provider knows about hands, handed to the source-scoped one
// so it can resolve the active hand against the Vorlage it just loaded.
type HandScope = {
  chosen: string | null;
  lastByStyle: Record<string, string>;
  candidates: HandCandidate[];
  setHand: (id: string) => void;
};

const readHandByStyle = (): Record<string, string> => {
  try {
    const raw = localStorage.getItem(HAND_STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    if (!parsed || typeof parsed !== 'object') return {};
    // Only string→string survives. The entry is hand-editable in the dev
    // tools, and one bad value must not throw on every resolve.
    return Object.fromEntries(
      Object.entries(parsed as Record<string, unknown>).filter(([, v]) => typeof v === 'string'),
    ) as Record<string, string>;
  } catch {
    return {};
  }
};

// The running form is stored as this template variant (core/database
// LAUFFORM_VARIANT).
const LAUFFORM_VARIANT = 100;

export function AdminProvider({
  children,
  pinnedSourceId,
}: {
  children: ReactNode;
  // Pin the provider to one source and ignore the persisted admin selection —
  // for public mounts (the quiz) that must always show the site-wide source.
  pinnedSourceId?: string;
}) {
  const [sourceId, setSourceId] = useState<string>(() => {
    if (pinnedSourceId) return pinnedSourceId;
    try {
      const stored = localStorage.getItem(SOURCE_STORAGE_KEY);
      // A persisted id that is no longer offered would strand the admin on a
      // Vorlage with no card to switch away from — the picker is the only way
      // out. Fall back to the build default instead (same reasoning as the
      // 404 recovery below, one step earlier).
      if (stored && !CONFIG.hiddenSourceIds.includes(stored)) return stored;
      return CONFIG.sourceId;
    } catch {
      return CONFIG.sourceId;
    }
  });

  const switchSource = useCallback(
    (id: string) => {
      if (pinnedSourceId) return;
      try {
        localStorage.setItem(SOURCE_STORAGE_KEY, id);
      } catch {
        /* private mode — the switch still holds for this session */
      }
      setSourceId(id);
    },
    [pinnedSourceId],
  );

  // The hand this session picked. It is only a CANDIDATE for the active hand:
  // `resolveHand` drops it again as soon as the Vorlage's script changes, and
  // picks it back up on the way back — which is the whole reason it may not
  // live under the remount.
  const [chosenHand, setChosenHand] = useState<string | null>(null);
  const [lastByStyle, setLastByStyle] = useState<Record<string, string>>(readHandByStyle);
  const [candidates, setCandidates] = useState<HandCandidate[]>([]);

  useEffect(() => {
    // A pinned mount is a public one (the quiz): it carries no admin token, so
    // the two gated reads would buy nothing but a pair of 401s.
    if (pinnedSourceId) return;
    let cancelled = false;
    // Both reads together, because neither alone knows every hand: /hands is
    // built from sheets ∪ Fassungen, /setups carries the ones that only have a
    // typed setup so far (handScope.ts).
    Promise.all([getEigenhandHands({ retries: 2 }), getEigenhandSetups({ retries: 2 })])
      .then(([hands, setups]) => {
        if (!cancelled) setCandidates(handCandidates(hands.hands, setups.setups, hands.styles));
      })
      .catch(() => {
        // Quiet, like the Korb badge: both routes are admin-gated and may 401,
        // and the honest answer is then an empty Hand field — not an error
        // banner over a workbench that otherwise works.
      });
    return () => {
      cancelled = true;
    };
  }, [pinnedSourceId]);

  const setHand = useCallback(
    (id: string) => {
      setChosenHand(id);
      const style = handStyle(candidates, id);
      // An id no read knows has no script to file it under; it stays this
      // session's pick and is simply not remembered.
      if (!style) return;
      const next = { ...lastByStyle, [style]: id };
      setLastByStyle(next);
      try {
        localStorage.setItem(HAND_STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* private mode — the pick still holds for this session */
      }
    },
    [candidates, lastByStyle],
  );

  const hand = useMemo<HandScope>(
    () => ({ chosen: chosenHand, lastByStyle, candidates, setHand }),
    [chosenHand, lastByStyle, candidates, setHand],
  );

  return (
    <SourceScopedProvider key={sourceId} sourceId={sourceId} switchSource={switchSource} hand={hand}>
      {children}
    </SourceScopedProvider>
  );
}

function SourceScopedProvider({
  sourceId,
  switchSource,
  hand,
  children,
}: {
  sourceId: string;
  switchSource: (id: string) => void;
  hand: HandScope;
  children: ReactNode;
}) {
  const [source, setSource] = useState<SourceOut | null>(null);
  const [sources, setSources] = useState<SourceOut[]>([]);
  const [bboxesByKey, setBboxesByKey] = useState<Record<string, BboxOut>>({});
  const [glyphsByKey, setGlyphsByKey] = useState<Record<string, GlyphSummary>>({});
  const [laufformKeys, setLaufformKeys] = useState<Set<string>>(() => new Set());
  const [loadError, setLoadError] = useState<string | null>(null);
  const [waking, setWaking] = useState<boolean>(false);
  const [activeGlyph, setActiveGlyph] = useState<string | null>(null);
  const [visibleGlyphs, setVisibleGlyphs] = useState<Set<string>>(new Set());
  const [cropCacheBust, setCropCacheBust] = useState<number>(0);
  const [wizardGlyph, setWizardGlyph] = useState<string | null>(null);
  const [diagnoseGlyph, setDiagnoseGlyph] = useState<string | null>(null);

  // Both derivations of ONE template read, kept together so they can never
  // describe different moments.
  const applyGlyphRows = useCallback((glyphs: GlyphSummary[]) => {
    // The per-key map is LOSSY — the read returns every variant of the style
    // ordered by (glyph_key, variant), so a letter's variant-100 row overwrites
    // its variant-0 row here. Harmless as long as only `has_data` is read from
    // it (every consumer today), but `.variant` and `.advance` on this map
    // belong to whichever row happened to come last. Anything that needs a
    // specific variant reads the ARRAY, as the Laufform set below does.
    const gm: Record<string, GlyphSummary> = {};
    for (const g of glyphs) gm[g.glyph_key] = g;
    setGlyphsByKey(gm);
    setLaufformKeys(
      new Set(glyphs.filter((g) => g.variant === LAUFFORM_VARIANT && g.has_data).map((g) => g.glyph_key)),
    );
  }, []);

  // `laufformKeys` is a SNAPSHOT of the boot read, and an apply writes exactly
  // the rows it is derived from — so the one action that can invalidate it has
  // to re-read it. Without this the work list keeps the „ohne Laufform" chip
  // and keeps the letter in that filter until the source is remounted, which
  // is the old card wall's behaviour inverted: it probed per render and could
  // not go stale, a list reads a set and can.
  const refreshGlyphs = useCallback(async () => {
    try {
      applyGlyphRows(await getGlyphs(sourceId, { retries: 1 }));
    } catch {
      // A failed refresh leaves the previous answer standing: it is one read
      // behind, which is better than an empty alphabet.
    }
  }, [sourceId, applyGlyphRows]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Cloud Run cold start: retry the boot load with backoff (~47s budget)
      // and flag `waking` on the first retry so the UI can say "API startet…".
      const onRetry = () => {
        if (!cancelled) setWaking(true);
      };
      const retry = { retries: 8, onRetry };
      try {
        const [s, allSources, bboxes, glyphs] = await Promise.all([
          getSource(sourceId, retry),
          getSources(retry),
          getBboxes(sourceId, retry),
          getGlyphs(sourceId, retry),
        ]);
        if (cancelled) return;
        setWaking(false);
        setSource(s);
        // The ONE narrowing of the source list: chart sources only, minus the
        // ones the workbench does not currently offer (CONFIG.hiddenSourceIds
        // — a presentation choice, nothing is deleted server-side).
        setSources(
          allSources.filter((x) => x.kind === 'chart' && !CONFIG.hiddenSourceIds.includes(x.id)),
        );
        const bm: Record<string, BboxOut> = {};
        for (const b of bboxes) bm[b.glyph_key] = b;
        setBboxesByKey(bm);
        // The per-key map is LOSSY — the read returns every variant of the
        // style ordered by (glyph_key, variant), so a letter's variant-100 row
        // overwrites its variant-0 row here. Harmless as long as only
        // `has_data` is read from it (every consumer today), but `.variant` and
        // `.advance` on this map belong to whichever row happened to come last.
        // Anything that needs a specific variant reads the ARRAY, as the
        // Laufform set below does.
        applyGlyphRows(glyphs);
        setVisibleGlyphs(new Set(bboxes.map((b) => b.glyph_key)));
      } catch (e) {
        if (cancelled) return;
        setWaking(false);
        // A stale persisted source id (renamed/removed in the DB) must not
        // brick the admin — fall back to the build default instead.
        if (e instanceof ApiError && e.status === 404 && sourceId !== CONFIG.sourceId) {
          switchSource(CONFIG.sourceId);
          return;
        }
        // Fixed German copy for the user (this state renders on the public
        // /quiz too); the raw exception goes to the console for diagnosis.
        console.error('source boot load failed', e);
        setLoadError(de.common.boot.sourceUnreachableDetail);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sourceId, switchSource, applyGlyphRows]);

  const toggleVisible = useCallback((key: string) => {
    setVisibleGlyphs((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const setOnlyVisible = useCallback((keys: string[]) => {
    setVisibleGlyphs(new Set(keys));
  }, []);

  const upsertBbox = useCallback((key: string, bbox: BboxOut) => {
    setBboxesByKey((prev) => ({ ...prev, [key]: bbox }));
    setCropCacheBust(Date.now());
    setVisibleGlyphs((prev) => {
      if (prev.has(key)) return prev;
      const next = new Set(prev);
      next.add(key);
      return next;
    });
  }, []);

  const removeBbox = useCallback((key: string) => {
    setBboxesByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const markGlyphTraced = useCallback((key: string, summary: GlyphSummary) => {
    setGlyphsByKey((prev) => ({ ...prev, [key]: summary }));
    // A trace/resample changes the canonical, so every diagnostic-derived
    // render (Diagnose stages, WrittenGlyph cache) must refetch — the crop
    // bytes are unchanged, but the bust doubles as the "canonical version".
    setCropCacheBust(Date.now());
  }, []);

  const removeGlyph = useCallback((key: string) => {
    setGlyphsByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const refreshCrop = useCallback(() => setCropCacheBust(Date.now()), []);

  // The one place the two scopes meet: the Vorlage's script decides which hand
  // may be active at all (V19). Derived rather than stored, so a candidate list
  // that arrives after the first paint — or a Vorlage switch — needs no effect
  // and can never leave a foreign-script hand standing.
  const styleId = source?.style_id ?? null;
  const handId = useMemo(
    () => resolveHand(hand.chosen, styleId, hand.candidates, hand.lastByStyle),
    [hand.chosen, hand.candidates, hand.lastByStyle, styleId],
  );
  const handChoices = useMemo(() => handsOfStyle(hand.candidates, styleId), [hand.candidates, styleId]);

  // Opening either modal also activates the glyph, so the sidebar/chart stay in
  // sync with whatever is being authored or inspected.
  const openWizard = useCallback((key: string) => {
    setActiveGlyph(key);
    setWizardGlyph(key);
  }, []);
  const closeWizard = useCallback(() => setWizardGlyph(null), []);
  const openDiagnose = useCallback((key: string) => {
    setActiveGlyph(key);
    setDiagnoseGlyph(key);
  }, []);
  const closeDiagnose = useCallback(() => setDiagnoseGlyph(null), []);

  const value = useMemo<AdminState>(
    () => ({
      sourceId,
      source,
      sources,
      switchSource,
      handId,
      handChoices,
      setHand: hand.setHand,
      bboxesByKey,
      glyphsByKey,
      laufformKeys,
      refreshGlyphs,
      loadError,
      waking,
      activeGlyph,
      visibleGlyphs,
      cropCacheBust,
      setActiveGlyph,
      toggleVisible,
      setOnlyVisible,
      upsertBbox,
      removeBbox,
      markGlyphTraced,
      removeGlyph,
      refreshCrop,
      wizardGlyph,
      openWizard,
      closeWizard,
      diagnoseGlyph,
      openDiagnose,
      closeDiagnose,
    }),
    [
      sourceId,
      source,
      sources,
      switchSource,
      handId,
      handChoices,
      hand.setHand,
      bboxesByKey,
      glyphsByKey,
      laufformKeys,
      refreshGlyphs,
      loadError,
      waking,
      activeGlyph,
      visibleGlyphs,
      cropCacheBust,
      toggleVisible,
      setOnlyVisible,
      upsertBbox,
      removeBbox,
      markGlyphTraced,
      removeGlyph,
      refreshCrop,
      wizardGlyph,
      openWizard,
      closeWizard,
      diagnoseGlyph,
      openDiagnose,
      closeDiagnose,
    ],
  );

  return <AdminCtx.Provider value={value}>{children}</AdminCtx.Provider>;
}
