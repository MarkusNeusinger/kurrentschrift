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
  // Answers and requests are keyed by source AND line, so a source switch
  // never shows a composition from the other Vorlage; a failed request is
  // forgotten again so the next edit retries it.
  const [answers, setAnswers] = useState<Map<string, ComposedWordOut | 'error'>>(() => new Map());
  const requested = useRef(new Set<string>());
  const wanted = useMemo(() => textLines(text), [text]);
  const keyOf = (line: string) => `${sourceId}\n${line}`;

  useEffect(() => {
    // One request per distinct line, however often it is typed — two rows
    // holding the same words share one composition.
    const todo = [...new Set(wanted.map((l) => l.text))].filter((line) => !requested.current.has(keyOf(line)));
    if (!todo.length) return;
    const timer = setTimeout(() => {
      for (const line of todo) {
        const key = keyOf(line);
        requested.current.add(key);
        fetchRenderWord(sourceId, line).then(
          (c) => setAnswers((m) => new Map(m).set(key, c)),
          () => {
            requested.current.delete(key);
            setAnswers((m) => new Map(m).set(key, 'error'));
          },
        );
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // keyOf is a plain closure over sourceId, which is in the list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wanted, sourceId]);

  return useMemo(() => {
    const lines = wanted.map((line): TextLine => {
      const a = answers.get(keyOf(line.text));
      return { ...line, composed: a && a !== 'error' ? a : null };
    });
    return {
      lines,
      loading: wanted.some((line) => !answers.has(keyOf(line.text))),
      failed: wanted.filter((line) => answers.get(keyOf(line.text)) === 'error').map((line) => line.text),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wanted, answers, sourceId]);
}
