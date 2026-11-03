import React from 'react';
import { WebDashboard } from '../../components/web/WebDashboard';
import { useRouter } from '../../lib/router';
import { DeckItem, WeakTopic } from '../../types';

interface DashboardPageProps {
  decks: DeckItem[];
  weakTopics: WeakTopic[];
  isEmptyState?: boolean;
  isLoadingSkeleton?: boolean;
}

/**
 * Next.js Page Route: /dashboard
 */
export default function DashboardPage({
  decks,
  weakTopics,
  isEmptyState = false,
  isLoadingSkeleton = false,
}: DashboardPageProps) {
  const router = useRouter();

  return (
    <WebDashboard
      decks={decks}
      weakTopics={weakTopics}
      isEmptyState={isEmptyState}
      isLoadingSkeleton={isLoadingSkeleton}
      onDeckClick={(deckId) => router.push(`/decks/${deckId}`)}
      onStartReview={() => router.push('/review/deck-1')}
      onTakeQuiz={() => router.push('/quiz/deck-1')}
      onNewDeckClick={() => router.push('/upload')}
    />
  );
}
