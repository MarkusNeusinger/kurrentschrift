// Lesart page (/lesen/vergleichen) — the reading aid for a person with an old
// letter on the desk: type what you believe a word says, the engine writes
// it in Sütterlin, and beside it the readings that would look the same on
// the page (lib/lesarten.ts — one confusable letter swapped each), so the
// eye can compare against the original instead of against memory. Below,
// the classic confusable pairs written side by side with the feature that
// tells them apart (SpecimenStrip). Vision goal 5's didactic half, without
// HTR: the person does the reading, the engine supplies the candidates.
//
// Same "paper & ink" identity as every public page; copy in
// locales/de/vergleichen.ts, this file is layout and state only.

import { useEffect, useMemo, useRef, useState } from 'react';
import { Box, Button, ButtonBase, Chip, CircularProgress, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { anyWritable, SpecimenStrip, useSpecimenPayloads } from '@/components/SpecimenStrip';
import { WrittenWord } from '@/components/WrittenWord';
import { knownGlyph } from '@/domain/glyphs';
import { useInView } from '@/hooks/useInView';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { getLesarten, type LesartDictionaryOut, type LesartenOut, type LesartReadingOut } from '@/lib/api';
import { de, fmt } from '@/locales';
import { paths } from '@/routes/paths';
import { SECTION_IDS } from '@/sections/schriftkunde/sections';
import { display, garamond, paper } from '@/styles/paper';

const t = de.vergleichen;

// A word or a short phrase — the Lesarten grid is one swap per card, and a
// long text would only bury the swap.
const MAX_LEN = 32;
const DEBOUNCE_MS = 450;

const prose = { color: paper.inkSoft, lineHeight: 1.7 } as const;
const proseLink = {
  color: paper.sepia,
  textDecorationColor: `${paper.sepia}80`,
  transition: 'color .2s',
  '&:hover': { color: paper.viridianText, textDecorationColor: paper.viridian },
} as const;

// Map an unrenderable glyph_key back to a human letter for the "not traced
// yet" note (e.g. `longs` → ſ) — the Federprobe's helper, same purpose.
function lettersFromKeys(keys: string[]): string {
  const seen = new Set<string>();
  for (const k of keys) {
    const g = knownGlyph(k);
    if (g) seen.add(g.glyph);
  }
  return [...seen].join(' · ');
}

// The Antiqua rendering of a reading with every swapped letter marked.
function MarkedReading({ text, indices }: { text: string; indices: readonly number[] }) {
  const marked = new Set(indices);
  return (
    <Typography component="span" sx={{ fontFamily: garamond, fontSize: '1.15rem', color: paper.ink }}>
      {[...text].map((ch, i) =>
        marked.has(i) ? (
          <Box key={i} component="span" sx={{ color: paper.viridianText, fontWeight: 700, textDecoration: 'underline', textDecorationColor: paper.viridian }}>
            {ch}
          </Box>
        ) : (
          ch
        ),
      )}
    </Typography>
  );
}

export function VergleichenView() {
  // A shared link (?text=…) seeds the field; otherwise the first example does.
  // The URL mirrors the debounced text (replace, so typing never floods the
  // history); the default example stays a clean URL.
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultText = t.examples[0];
  const seed = (searchParams.get('text') ?? '').slice(0, MAX_LEN) || defaultText;
  const [input, setInput] = useState<string>(seed);
  const [text, setText] = useState<string>(seed.trim());
  const [missing, setMissing] = useState<string[]>([]);
  const [composeError, setComposeError] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  // The readings come from the API (real words only). The answer is kept
  // together with the text it answers, so "loading" is simply "no answer for
  // the current text yet" — no state to reset when the text changes.
  const [answer, setAnswer] = useState<LesartenOut | null>(null);
  const [failedText, setFailedText] = useState<string | null>(null);

  // Debounced: a new text starts a fresh compose and a fresh reading lookup,
  // so a stale error, the last word's "missing letters" note and its readings
  // are cleared with it.
  useEffect(() => {
    const trimmed = input.trim();
    const id = setTimeout(() => {
      setText(trimmed);
      setComposeError(false);
      setMissing([]);
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [input]);

  useEffect(() => {
    const url = text && text !== defaultText ? text : '';
    setSearchParams(url ? { text: url } : {}, { replace: true });
    // setSearchParams' identity is not stable across navigations — depending
    // on it would re-run (and re-navigate) after every sync.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, defaultText]);

  useEffect(() => {
    if (!text) return undefined;
    let cancelled = false;
    getLesarten(text)
      .then((out) => {
        if (!cancelled) setAnswer(out);
      })
      .catch(() => {
        if (!cancelled) setFailedText(text);
      });
    return () => {
      cancelled = true;
    };
  }, [text]);
  const readings: LesartReadingOut[] | null = answer && answer.text === text ? answer.readings : null;
  const dictionary: LesartDictionaryOut | null | undefined = answer?.dictionary;
  const readingsError = failedText === text && readings === null;
  const missingLetters = useMemo(() => lettersFromKeys(missing), [missing]);

  // The confusable pairs: one batch for all their glyphs, fetched when the
  // section comes near; every strip mounts its cells in view.
  const pairKeys = useMemo(() => t.pairs.flatMap((p) => p.specimens.map((s) => s.key)), []);
  const [pairsRef, pairsNear] = useInView<HTMLDivElement>('300px');
  const payloads = useSpecimenPayloads(pairKeys, pairsNear);
  const showPairsNote = t.pairs.some((p) => anyWritable(p.specimens, payloads));

  const takeOver = (reading: string) => {
    setInput(reading);
    inputRef.current?.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <PublicLayout footer>
      <PageContainer width="text" sx={{ pt: { xs: 4, md: 7 } }}>
        <PageHeader eyebrow={de.common.nav.read} title={t.heading}>
          <Typography sx={prose}>{t.lead}</Typography>
        </PageHeader>

        {/* --- Deine Lesart: the guess, written --- */}
        <Box component="section">
          <CategoryHeading>{t.guessHeading}</CategoryHeading>
          <TextField
            fullWidth
            inputRef={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, MAX_LEN))}
            label={t.inputLabel}
            placeholder={t.inputPlaceholder}
            helperText={`${input.length}/${MAX_LEN}`}
            slotProps={{
              htmlInput: { maxLength: MAX_LEN, autoCapitalize: 'off', spellCheck: false },
              formHelperText: { sx: { textAlign: 'right', mr: 0 } },
            }}
            sx={{ mb: 1 }}
          />
          <Stack direction="row" sx={{ flexWrap: 'wrap', alignItems: 'center', gap: 1, mb: 2.5 }}>
            <Typography component="span" variant="body2" sx={{ color: paper.inkSoft }}>
              {t.examplesLabel}
            </Typography>
            {t.examples.map((ex) => (
              <Chip
                key={ex}
                label={ex}
                size="small"
                variant="outlined"
                onClick={() => setInput(ex)}
                sx={{ fontFamily: garamond, borderColor: paper.line, color: paper.ink }}
              />
            ))}
          </Stack>

          <Paper
            elevation={0}
            sx={{
              p: { xs: 2, md: 3 },
              minHeight: 180,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              // White work surface framing the written word, like the Federprobe (§5).
              bgcolor: '#fff',
              border: `1px solid ${paper.line}`,
              borderRadius: 1,
              overflow: 'hidden',
            }}
          >
            {text && composeError ? (
              <Stack spacing={1.5} sx={{ alignItems: 'center', textAlign: 'center', px: 2 }}>
                <Typography sx={{ color: paper.inkSoft }}>{t.loadError}</Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    setComposeError(false);
                    setRetryNonce((n) => n + 1);
                  }}
                >
                  {t.retry}
                </Button>
              </Stack>
            ) : text ? (
              <WrittenWord
                key={`${text}#${retryNonce}`}
                text={text}
                height={150}
                durationMs={Math.min(4200, 700 + text.replace(/\s/g, '').length * 320)}
                maxWidth={760}
                showReplay
                onResolved={({ missing: m }) => setMissing(m)}
                onError={() => setComposeError(true)}
              />
            ) : (
              <Typography sx={{ color: paper.inkSoft, fontStyle: 'italic' }}>{t.emptyHint}</Typography>
            )}
          </Paper>
          <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 0.75 }}>
            {missing.length > 0 && missingLetters ? fmt(t.missingNote, { letters: missingLetters }) : t.writtenCaption}
          </Typography>
        </Box>

        {/* --- Lesarten: the real words that differ from the guess by look-alikes only --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <CategoryHeading>{t.lesartenHeading}</CategoryHeading>
          <Typography sx={{ ...prose, mb: 2, maxWidth: '64ch' }}>{t.lesartenIntro}</Typography>
          {!text ? null : readingsError ? (
            <Typography sx={{ ...prose, fontStyle: 'italic' }}>{t.lesartenError}</Typography>
          ) : readings === null ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, color: paper.inkSoft }}>
              <CircularProgress size={18} aria-hidden />
              <Typography sx={prose}>{t.lesartenLoading}</Typography>
            </Box>
          ) : readings.length === 0 ? (
            <Typography sx={{ ...prose, fontStyle: 'italic' }}>{t.noLesarten}</Typography>
          ) : (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
              {readings.map((r) => (
                <ButtonBase
                  key={r.word}
                  onClick={() => takeOver(r.word)}
                  aria-label={`${r.word} — ${t.takeOver}`}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'stretch',
                    textAlign: 'left',
                    border: `1px solid ${paper.line}`,
                    borderRadius: '3px',
                    bgcolor: paper.hi,
                    p: 1.5,
                    transition: 'border-color .2s, transform .2s',
                    '&:hover, &:focus-visible': { borderColor: paper.viridian, transform: 'translateY(-2px)' },
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'center', minHeight: 96 }}>
                    <WrittenWord text={r.word} height={96} maxWidth={320} animate={false} ariaLabel={r.word} />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 1, mt: 0.75 }}>
                    <MarkedReading text={r.word} indices={r.swaps.map((s) => s.index)} />
                    <Typography variant="caption" sx={{ color: paper.sepia, fontStyle: 'italic', textAlign: 'right' }}>
                      {r.swaps.map((s) => fmt(t.swapNote, { from: s.from, to: s.to })).join(' · ')}
                      {r.bank ? ` · ${t.bankMark}` : ''}
                    </Typography>
                  </Box>
                </ButtonBase>
              ))}
            </Box>
          )}
          {dictionary !== undefined && (
            <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 1.5, maxWidth: '64ch' }}>
              {dictionary ? fmt(t.dictionaryNote, { forms: dictionary.forms.toLocaleString('de-DE') }) : t.dictionaryMissing}
            </Typography>
          )}
        </Box>

        {/* --- Die klassischen Verwechsler: pairs side by side --- */}
        <Box component="section" ref={pairsRef} sx={{ mt: { xs: 5, md: 6 } }}>
          <CategoryHeading>{t.pairsHeading}</CategoryHeading>
          <Typography sx={{ ...prose, maxWidth: '64ch' }}>{t.pairsIntro}</Typography>
          {showPairsNote && (
            <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 0.75, mb: 1.5, maxWidth: '64ch' }}>
              {t.pairsNote}
            </Typography>
          )}
          <Box sx={{ borderBottom: `1px solid ${paper.line}` }}>
            {t.pairs.map((pair) => (
              <Box
                key={pair.term}
                sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 1, sm: 2.5 }, py: 1.5, borderTop: `1px solid ${paper.line}`, alignItems: { sm: 'center' } }}
              >
                <SpecimenStrip specimens={pair.specimens} payloads={payloads} height={96} sx={{ alignSelf: { xs: 'flex-start', sm: 'center' }, minWidth: 140, justifyContent: 'center' }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink }}>
                    {pair.term}
                  </Typography>
                  <Typography variant="body2" sx={prose}>
                    {pair.desc}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>

        {/* --- Weiter --- */}
        <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
          <CategoryHeading>{t.moreHeading}</CategoryHeading>
          <Box component="ul" sx={{ m: 0, pl: 3 }}>
            <Typography component="li" sx={{ ...prose, mb: 0.5 }}>
              <Link component={RouterLink} to={`${paths.schriftkunde}#${SECTION_IDS.decipher}`} sx={proseLink}>
                {t.moreDecipher}
              </Link>
            </Typography>
            <Typography component="li" sx={prose}>
              <Link component={RouterLink} to={paths.quiz} sx={proseLink}>
                {t.moreQuiz}
              </Link>
            </Typography>
          </Box>
          <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 3, maxWidth: '64ch' }}>
            {t.disclaimer}
          </Typography>
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
