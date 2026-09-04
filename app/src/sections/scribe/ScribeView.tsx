// Public live-writing page (/federprobe): type any word or sentence and watch
// the synthesised Sütterlin ductus write it stroke by stroke, with the
// generated connecting strokes (Übergänge) between the letters. The whole thesis
// of the project — arbitrary text from a per-glyph ductus prior, not a font —
// made tangible. Shaping + geometry live server-side (core/shaping.py +
// core/compose.py, fetched via GET /sources/{id}/write/word), rendering in
// components/WrittenWord; this file is the UI shell only.

import { useEffect, useMemo, useRef, useState } from 'react';
import { Button, Chip, Paper, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useSearchParams } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { WrittenWord } from '@/components/WrittenWord';
import { lettersFromKeys } from '@/domain/glyphs';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { MAX_COMPOSE_CHARS, tooLongRun } from '@/lib/lineWrap';
import { de, fmt } from '@/locales';
import {
  DEFAULT_SCRIBE_SIZE,
  SCRIBE_SIZE_PX,
  initialScribeSize,
  parseScribeSize,
  readStoredScribeSize,
  storeScribeSize,
  type ScribeSize,
} from '@/sections/scribe/size';
import { hitArea } from '@/styles/hitArea';
import { garamond, paper } from '@/styles/paper';

// A postcard, not a word (owner decision 2026-09-04): eight written lines of
// sixty characters — the practice sheet's own line length (`MAX_LINE_LEN`,
// lib/uebungstext.ts), because a written line is a written line whether it goes
// to a printer or to the screen. A typed newline spends one of these 480
// characters like any other character does, so the counter under the field
// stays the honest length of what will be written.
//
// The cap is NOT the API's (which takes 160 per request): every LINE is its own
// composition request, and lib/lineWrap keeps a line at 60 characters, so no
// request ever comes near it. What used to hold this number down was
// legibility — 48 characters on a phone wrote an x-height of ~8 px — and that
// job now belongs to the Tintenboden and the line wrap.
const MAX_LEN = 480;
const DEBOUNCE_MS = 450;

export function ScribeView() {
  // The page title / SEO meta is set by the route mount (ScribePage → usePageMeta).
  // A shared link (?text=…) seeds the field; otherwise the first example does.
  const [searchParams, setSearchParams] = useSearchParams();
  const paramText = searchParams.get('text')?.slice(0, MAX_LEN) ?? '';
  // `?size=` beats the remembered choice, so a shared link reproduces the look
  // its sender saw rather than the recipient's last setting.
  const paramSize = searchParams.get('size') ?? '';
  const defaultText = de.scribe.examples[0];
  const [input, setInput] = useState<string>(paramText || defaultText);
  const [text, setText] = useState<string>((paramText || defaultText).trim());
  const [size, setSize] = useState<ScribeSize>(() => initialScribeSize(paramSize, readStoredScribeSize()));
  // The ?text= value this component itself last wrote (mirror effect below).
  // Lets the URL→state effect tell our own replaceState apart from an external
  // navigation (another shared link, back/forward) — React Router does NOT
  // remount on search-param changes, so the ref-free version never re-seeded.
  const lastWrittenParam = useRef(paramText);

  // URL → state: an externally navigated ?text= (deep link while mounted,
  // history traversal) re-seeds the field; our own mirror writes are ignored.
  useEffect(() => {
    if (paramText === lastWrittenParam.current) return;
    lastWrittenParam.current = paramText;
    const next = paramText || defaultText;
    setInput(next);
    setText(next.trim());
  }, [paramText, defaultText]);

  // URL → state for the size, adjusted DURING RENDER rather than in an effect
  // (React's "adjusting state when a prop changes", the pattern WrittenWord
  // already uses): the size needs no ref guard, because our own mirror only
  // ever writes back the size we are already showing and setting it again is a
  // no-op. A link WITHOUT `?size=` — or with a value that names no step —
  // leaves the reader's own choice alone instead of resetting it.
  const [sizeParamSeen, setSizeParamSeen] = useState(paramSize);
  if (sizeParamSeen !== paramSize) {
    setSizeParamSeen(paramSize);
    const named = parseScribeSize(paramSize);
    if (named) setSize(named);
  }
  const [missing, setMissing] = useState<string[]>([]);
  // Compose fetch failed (after the cold-start retries) — offer a retry instead
  // of a spinner forever; the nonce remounts WrittenWord to kick a fresh fetch.
  const [composeError, setComposeError] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);
  const [copied, setCopied] = useState(false);
  const copyTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Debounce so each keystroke doesn't kick off a fresh compose/fetch storm; the
  // glyph cache covers repeats, but the debounce keeps the write-in from
  // restarting mid-word while typing.
  useEffect(() => {
    const trimmed = input.trim();
    const id = setTimeout(() => setText(trimmed), DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [input]);

  // A new text starts a fresh compose — clear a stale error from the last one.
  // Done during render, not in an effect (react-hooks/set-state-in-effect): the
  // error line would otherwise survive one commit into the new text, which is
  // exactly the frame in which the retry button was already gone.
  const [errorFor, setErrorFor] = useState(text);
  if (errorFor !== text) {
    setErrorFor(text);
    setComposeError(false);
  }

  // State → URL: mirror the debounced text and the chosen size into the query
  // so the page is shareable exactly as it looks. `replace` keeps typing from
  // flooding the history; the default example and the default size stay a clean
  // URL. Records what it wrote so the URL→state effects above can ignore the
  // resulting searchParams change. A newline in the text is carried as `%0A` —
  // it is part of the writing, so it belongs in the link.
  useEffect(() => {
    const urlText = text && text !== defaultText ? text : '';
    const urlSize = size === DEFAULT_SCRIBE_SIZE ? '' : size;
    lastWrittenParam.current = urlText;
    setSearchParams(
      { ...(urlText ? { text: urlText } : {}), ...(urlSize ? { size: urlSize } : {}) },
      { replace: true },
    );
    // setSearchParams' identity is not stable across navigations — depending on
    // it would re-run (and re-navigate) after every sync.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, size, defaultText]);

  const chooseSize = (next: ScribeSize) => {
    setSize(next);
    storeScribeSize(next);
  };

  useEffect(() => () => clearTimeout(copyTimer.current), []);

  const copyLink = () => {
    navigator.clipboard
      ?.writeText(window.location.href)
      .then(() => {
        setCopied(true);
        clearTimeout(copyTimer.current);
        copyTimer.current = setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {
        /* clipboard unavailable (permissions/insecure context) — stay quiet */
      });
  };

  const missingLetters = useMemo(() => lettersFromKeys(missing), [missing]);
  // The one input no line plan can rescue: a run without a space, longer than
  // one composition request may carry.
  const unwritable = useMemo(() => tooLongRun(text), [text]);

  return (
    <PublicLayout footer minHeight="100vh">
      <PageContainer width="text" sx={{ pt: { xs: 4, md: 7 } }}>
        <PageHeader eyebrow={de.common.nav.write} title={de.scribe.heading}>
          <Typography sx={{ color: paper.inkSoft }}>{de.scribe.lead}</Typography>
          {/* The explanatory paragraph a first-time visitor — and a crawler —
              owes: what this page is and how far it reaches (same slot as the
              hubs' `about`, HubView). */}
          <Typography sx={{ color: paper.inkSoft, mt: 1.5 }}>{de.scribe.about}</Typography>
        </PageHeader>

        {/* Multiline since 2026-09-04: Enter starts a new line and that break is
            written as a break (lib/lineWrap `planParagraphs`), so the field has
            to be a textarea and must not submit on Enter — there is no form to
            submit to, the debounce below is the only trigger. */}
        <TextField
          // Named, so the browser stops reporting an unnamed form field (a
          // DevTools issue on this page since before it was a textarea) and
          // can offer the reader their own earlier text back.
          id="federprobe-text"
          name="federprobe-text"
          fullWidth
          multiline
          minRows={3}
          maxRows={9}
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, MAX_LEN))}
          label={de.scribe.inputLabel}
          placeholder={de.scribe.inputPlaceholder}
          helperText={
            <>
              <span>{de.scribe.inputHint}</span>
              <span>{`${input.length}/${MAX_LEN}`}</span>
            </>
          }
          slotProps={{
            htmlInput: { maxLength: MAX_LEN, autoCapitalize: 'off', spellCheck: false },
            formHelperText: {
              component: 'span',
              sx: { display: 'flex', justifyContent: 'space-between', gap: 2, mr: 0 },
            },
          }}
          sx={{ mb: 1 }}
        />

        {/* The chips are 28px tall and carry an invisible 44px target (§9.3), so
            the ROW pitch has to clear 44 or a wrapped row's target overlaps the
            row above it and steals its taps — measured: at rowGap 1.5 the chip
            „das" lost its lower edge to the row below. 28 + 16 = 44 exactly. */}
        <Stack direction="row" sx={{ flexWrap: 'wrap', alignItems: 'center', columnGap: 1.5, rowGap: 2, mb: 2 }}>
          <Typography component="span" variant="body2" sx={{ color: paper.inkSoft }}>
            {de.scribe.examplesLabel}
          </Typography>
          {de.scribe.examples.map((ex) => (
            <Chip
              key={ex}
              label={ex}
              size="small"
              variant="outlined"
              onClick={() => setInput(ex)}
              sx={[hitArea(), { fontFamily: garamond, borderColor: paper.line, color: paper.ink }]}
            />
          ))}
          {/* Share the written text — copies the ?text= deep link, label flips
              briefly to the viridian confirmation. */}
          <Button
            size="small"
            onClick={copyLink}
            sx={[hitArea(), { ml: 'auto', fontFamily: garamond, color: copied ? paper.viridianText : paper.sepia, minWidth: 0 }]}
          >
            {copied ? de.scribe.copied : de.scribe.copyLink}
          </Button>
        </Stack>

        {/* Schriftgröße instead of a zoom (owner decision 2026-09-04): the step
            sets the x-height the text is WRITTEN at, so a bigger step wraps into
            more lines rather than magnifying a picture. Browser zoom stays
            available on top of it — index.html sets no `user-scalable=no`.
            ToggleButtons carry a real 44 px height under `sm` from the theme
            (design-system.md §9.3), so the row needs no invisible hit area. */}
        <Stack direction="row" sx={{ flexWrap: 'wrap', alignItems: 'center', columnGap: 1.5, rowGap: 1.5, mb: 3 }}>
          <Typography component="span" variant="body2" sx={{ color: paper.inkSoft }}>
            {de.scribe.sizeLabel}
          </Typography>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={size}
            onChange={(_, next: ScribeSize | null) => next && chooseSize(next)}
            aria-label={de.scribe.sizeAria}
          >
            {(Object.keys(SCRIBE_SIZE_PX) as ScribeSize[]).map((step) => (
              <ToggleButton key={step} value={step} sx={{ fontFamily: garamond }}>
                {de.scribe.sizes[step]}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>

        <Paper
          elevation={0}
          sx={{
            p: { xs: 2, md: 4 },
            minHeight: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            // White work surface: this Paper frames the live-written word
            // (WrittenWord renders transparent), so it follows the Tafel
            // written-glyph cards' neutral #fff, not the paper.hi card tone (§5).
            bgcolor: '#fff',
            border: `1px solid ${paper.line}`,
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          {/* A run without a space that no line can carry is REPORTED, not
              written and not cut — the practice sheet's own rule for a row its
              ruling is too narrow for. Checked before the composition is asked
              for, so the 480-character field cannot hand the composer a text it
              answers with a 422 and land the reader in the server-error card
              for something the input did. */}
          {text && unwritable ? (
            <Typography sx={{ color: paper.sepia, textAlign: 'center', px: 2 }}>
              {fmt(de.scribe.tooLongRun, { chars: unwritable.length, max: MAX_COMPOSE_CHARS })}
            </Typography>
          ) : text && composeError ? (
            <Stack spacing={1.5} sx={{ alignItems: 'center', textAlign: 'center', px: 2 }}>
              <Typography sx={{ color: paper.inkSoft }}>{de.scribe.loadError}</Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setComposeError(false);
                  setRetryNonce((n) => n + 1);
                }}
              >
                {de.scribe.retry}
              </Button>
            </Stack>
          ) : text ? (
            <WrittenWord
              key={`${text}#${retryNonce}`}
              text={text}
              // `height` is only the room the card holds while the composition
              // is on its way — the SIZE comes from the chosen step.
              height={170}
              targetXHeightPx={SCRIBE_SIZE_PX[size]}
              durationMs={Math.min(5200, 700 + text.replace(/\s/g, '').length * 320)}
              maxWidth={840}
              showReplay
              onResolved={({ missing: m }) => setMissing(m)}
              onError={() => setComposeError(true)}
            />
          ) : (
            <Typography sx={{ color: paper.inkSoft, fontStyle: 'italic' }}>{de.scribe.emptyHint}</Typography>
          )}
        </Paper>

        {missingLetters && (
          <Typography variant="body2" component="p" sx={{ color: paper.sepia, mt: 1.5 }}>
            {fmt(de.scribe.missingNote, { letters: missingLetters })}
          </Typography>
        )}

        <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 3 }}>
          {de.scribe.disclaimer}
        </Typography>
      </PageContainer>
    </PublicLayout>
  );
}
