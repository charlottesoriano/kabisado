import React from 'react';
import { WebQuiz } from '../../../components/web/WebQuiz';
import { useRouter, useParams } from '../../../lib/router';
import { MOCK_QUIZ_QUESTION } from '../../../data/mockData';

/**
 * Next.js Dynamic Page Route: /quiz/[id]
 */
export default function QuizPage() {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  return (
    <WebQuiz
      quizItem={MOCK_QUIZ_QUESTION}
      questionIndex={3}
      totalQuestions={10}
      onNextQuestion={() => router.push(`/quiz/${deckId}/results`)}
      onFinishQuiz={() => router.push(`/quiz/${deckId}/results`)}
    />
  );
}
