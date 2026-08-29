// useWorksheetText — the browser half of the Übungstext: every model line is
// composed server-side (`/write/word` through the shared render cache — the
// Federprobe's own path), debounced so a line being typed is not requested
// letter by letter. Answers are kept by their text, so a line's composition
// can never be shown under a line that has changed since; lib/uebungstext.ts
// does the placing.

import { useEffect, useMemo, useRef, useState } from 'react';

import { CONFIG } from '@/global-config';
import { fetchRenderWord, type ComposedWordOut } from '@/lib/api';
import { textLines, type TextLine } from '@/lib/uebungstext';

const DEBOUNCE_MS = 450;

export interface WorksheetText {
  lines: TextLine[];
  /** Some line has no answer yet. */
  loading: boolean;
  /** Lines whose composition failed (the API unreachable); retried on the next edit. */
  failed: string[];
}

export function useWorksheetText(text: string, sourceId: string = CONFIG.sourceId): WorksheetText {
  const [answers, setAnswers] = useState<Map<string, ComposedWordOut | 'error'>>(() => new Map());
  // Lines already asked for — a failure is removed again so the next edit retries it.
  const requested = useRef(new Set<string>());
  const wanted = useMemo(() => textLines(text), [text]);

  useEffect(() => {
    const todo = wanted.filter((line) => !requested.current.has(line));
    if (!todo.length) return;
    const timer = setTimeout(() => {
      for (const line of todo) {
        requested.current.add(line);
        fetchRenderWord(sourceId, line).then(
          (c) => setAnswers((m) => new Map(m).set(line, c)),
          () => {
            requested.current.delete(line);
            setAnswers((m) => new Map(m).set(line, 'error'));
          },
        );
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [wanted, sourceId]);

  return useMemo(() => {
    const lines = wanted.map((line): TextLine => {
      const a = answers.get(line);
      return { text: line, composed: a && a !== 'error' ? a : null };
    });
    return {
      lines,
      loading: wanted.some((line) => !answers.has(line)),
      failed: wanted.filter((line) => answers.get(line) === 'error'),
    };
  }, [wanted, answers]);
}
