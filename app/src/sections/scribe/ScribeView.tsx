// Public live-writing page (/federprobe): type any word or sentence and watch
// the synthesised Sütterlin ductus write it stroke by stroke, with the
// generated connecting strokes (Übergänge) between the letters. The whole thesis
// of the project — arbitrary text from a per-glyph ductus prior, not a font —
// made tangible. Shaping + geometry live server-side (core/shaping.py +
// core/compose.py, fetched via GET /sources/{id}/write/word), rendering in
// components/WrittenWord; this file is the UI shell only.

import { useEffect, useMemo, useRef, useState } from 'react';
import { Button, Chip, Paper, Stack, TextField, Typography } from '@mui/material';
import { useSearchParams } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { WrittenWord } from '@/components/WrittenWord';
import { knownGlyph } from '@/domain/glyphs';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de, fmt } from '@/locales';
import { garamond, paper } from '@/styles/paper';

const MAX_LEN = 48;
const DEBOUNCE_MS = 450;

// Map an unrenderable glyph_key back to a human letter for the "not curated yet"
// note (e.g. `s-medial` → ſ, `qu-initial` → qu).
function lettersFromKeys(keys: string[]): string {
  const seen = new Set<string>();
  for (const k of keys) {
    const g = knownGlyph(k);
    if (g) seen.add(g.glyph);
  }
  return [...seen].join(' · ');
}

export function ScribeView() {
  // The page title / SEO meta is set by the route mount (ScribePage → usePageMeta).
  // A shared link (?text=…) seeds the field; otherwise the first example does.
  const [searchParams, setSearchParams] = useSearchParams();
  const paramText = searchParams.get('text')?.slice(0, MAX_LEN) ?? '';
  const defaultText = de.scribe.examples[0];
  const [input, setInput] = useState<string>(paramText || defaultText);
  const [text, setText] = useState<string>((paramText || defaultText).trim());
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
  useEffect(() => setComposeError(false), [text]);

  // State → URL: mirror the debounced text into ?text= so the page is
  // shareable. `replace` keeps typing from flooding the history; the default
  // example stays a clean URL. Records what it wrote so the URL→state effect
  // above can ignore the resulting searchParams change.
  useEffect(() => {
    const url = text && text !== defaultText ? text : '';
    lastWrittenParam.current = url;
    setSearchParams(url ? { text: url } : {}, { replace: true });
    // setSearchParams' identity is not stable across navigations — depending on
    // it would re-run (and re-navigate) after every sync.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, defaultText]);

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

  return (
    <PublicLayout footer minHeight="100vh">
      <PageContainer width="text" sx={{ pt: { xs: 4, md: 7 } }}>
        <PageHeader eyebrow={de.common.nav.write} title={de.scribe.heading}>
          <Typography sx={{ color: paper.inkSoft }}>{de.scribe.lead}</Typography>
        </PageHeader>

        <TextField
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, MAX_LEN))}
          label={de.scribe.inputLabel}
          placeholder={de.scribe.inputPlaceholder}
          helperText={`${input.length}/${MAX_LEN}`}
          slotProps={{
            htmlInput: { maxLength: MAX_LEN, autoCapitalize: 'off', spellCheck: false },
            formHelperText: { sx: { textAlign: 'right', mr: 0 } },
          }}
          sx={{ mb: 1 }}
        />

        <Stack direction="row" sx={{ flexWrap: 'wrap', alignItems: 'center', gap: 1, mb: 3 }}>
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
              sx={{ fontFamily: garamond, borderColor: paper.line, color: paper.ink }}
            />
          ))}
          {/* Share the written text — copies the ?text= deep link, label flips
              briefly to the viridian confirmation. */}
          <Button
            size="small"
            onClick={copyLink}
            sx={{ ml: 'auto', fontFamily: garamond, color: copied ? paper.viridian : paper.sepia, minWidth: 0 }}
          >
            {copied ? de.scribe.copied : de.scribe.copyLink}
          </Button>
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
          {text && composeError ? (
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
              height={170}
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
          <Typography variant="caption" component="p" sx={{ color: paper.sepia, mt: 1.5 }}>
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
