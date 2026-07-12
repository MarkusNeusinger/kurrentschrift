// Public live-writing page (/federprobe): type any word or sentence and watch
// the synthesised Sütterlin ductus write it stroke by stroke, with the
// generated connecting strokes (Übergänge) between the letters. The whole thesis
// of the project — arbitrary text from a per-glyph ductus prior, not a font —
// made tangible. Shaping + geometry live server-side (core/shaping.py +
// core/compose.py, fetched via GET /write/word), rendering in
// components/WrittenWord; this file is the UI shell only.

import { useEffect, useMemo, useState } from 'react';
import { Chip, Paper, Stack, TextField, Typography } from '@mui/material';

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
  const [input, setInput] = useState<string>(de.scribe.examples[0]);
  const [text, setText] = useState<string>(de.scribe.examples[0]);
  const [missing, setMissing] = useState<string[]>([]);

  // Debounce so each keystroke doesn't kick off a fresh compose/fetch storm; the
  // glyph cache covers repeats, but the debounce keeps the write-in from
  // restarting mid-word while typing.
  useEffect(() => {
    const trimmed = input.trim();
    const id = setTimeout(() => setText(trimmed), DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [input]);

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
          slotProps={{ htmlInput: { maxLength: MAX_LEN, autoCapitalize: 'off', spellCheck: false } }}
          sx={{ mb: 1.5 }}
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
          {text ? (
            <WrittenWord
              key={text}
              text={text}
              height={170}
              durationMs={Math.min(5200, 700 + text.replace(/\s/g, '').length * 320)}
              maxWidth={840}
              showReplay
              onResolved={({ missing: m }) => setMissing(m)}
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

        <Typography variant="caption" component="p" sx={{ color: paper.sepiaFaint, fontStyle: 'italic', mt: 3 }}>
          {de.scribe.disclaimer}
        </Typography>
      </PageContainer>
    </PublicLayout>
  );
}
