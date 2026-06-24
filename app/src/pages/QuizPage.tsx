// Thin route mount for `/quiz` — the actual drill lives in sections/quiz.

import { usePageMeta } from '@/hooks/usePageMeta';
import { de } from '@/locales';
import { QuizView } from '@/sections/quiz/QuizView';

// Default export for React.lazy route splitting (routes/sections).
export default function QuizPage() {
  usePageMeta(de.seo.quiz);
  return <QuizView />;
}
