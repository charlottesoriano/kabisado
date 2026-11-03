import React from 'react';
import DashboardPage from './dashboard/page';
import { DeckItem, WeakTopic } from '../types';

interface RootPageProps {
  decks: DeckItem[];
  weakTopics: WeakTopic[];
  isEmptyState?: boolean;
  isLoadingSkeleton?: boolean;
}

/**
 * Next.js Page Route: /
 * Defaults to Dashboard view in Kabisado
 */
export default function RootPage(props: RootPageProps) {
  return <DashboardPage {...props} />;
}
