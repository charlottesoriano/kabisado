import React from 'react';
import { WebDeckPage } from '../../../components/web/WebDeckPage';
import { useRouter, useParams } from '../../../lib/router';
import { DeckItem, Flashcard } from '../../../types';

interface DeckDetailPageProps {
  decks: DeckItem[];
  flashcards: Flashcard[];
}

/**
 * Next.js Dynamic Page Route: /decks/[id]
 */
export default function DeckDetailPage({
  decks,
  flashcards,
}: DeckDetailPageProps) {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  const deck = decks.find((d) => d.id === deckId) || decks[0];

  return (
    <WebDeckPage
      deck={deck}
      flashcards={flashcards}
      onStartReview={() => router.push(`/review/${deck.id}`)}
      onStartQuiz={() => router.push(`/quiz/${deck.id}`)}
      onPracticeProblems={() => router.push(`/problems/${deck.id}`)}
      onCodingProblemClick={() => router.push(`/coding/${deck.id}`)}
    />
  );
}
