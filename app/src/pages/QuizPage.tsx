// Thin route mount for `/quiz` — the actual drill lives in sections/quiz.

import { QuizView } from '@/sections/quiz/QuizView';

// Default export for React.lazy route splitting (routes/sections).
export default function QuizPage() {
  return <QuizView />;
}
