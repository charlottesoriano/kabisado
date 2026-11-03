import React from 'react';
import { WebQuizResults } from '../../../../components/web/WebQuizResults';
import { useRouter, useParams } from '../../../../lib/router';

/**
 * Next.js Nested Page Route: /quiz/[id]/results
 */
export default function QuizResultsPage() {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  return (
    <WebQuizResults
      onReviewMissedAsFlashcards={() => router.push(`/review/${deckId}`)}
      onRetakeQuiz={() => router.push(`/quiz/${deckId}`)}
      onBackToDeck={() => router.push(`/decks/${deckId}`)}
    />
  );
}
