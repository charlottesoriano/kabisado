import React from 'react';
import { WebFlashcardReview } from '../../../components/web/WebFlashcardReview';
import { useRouter, useParams } from '../../../lib/router';
import { Flashcard } from '../../../types';

interface ReviewPageProps {
  flashcards: Flashcard[];
}

/**
 * Next.js Dynamic Page Route: /review/[id] (Focus Mode)
 */
export default function ReviewPage({ flashcards }: ReviewPageProps) {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  return (
    <WebFlashcardReview
      flashcard={flashcards[0]}
      cardNumber={5}
      totalCards={12}
      onClose={() => router.push(`/decks/${deckId}`)}
      onRate={(rating) => {
        // rating handled
      }}
    />
  );
}
