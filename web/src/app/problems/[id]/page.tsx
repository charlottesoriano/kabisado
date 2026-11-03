import React from 'react';
import { WebProblemPractice } from '../../../components/web/WebProblemPractice';
import { useRouter, useParams } from '../../../lib/router';
import { MOCK_PROBLEM } from '../../../data/mockData';

/**
 * Next.js Dynamic Page Route: /problems/[id]
 */
export default function ProblemPracticePage() {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  return (
    <WebProblemPractice
      problem={MOCK_PROBLEM}
      onNextProblem={() => router.push(`/coding/${deckId}`)}
      onTrySimilar={() => {}}
    />
  );
}
