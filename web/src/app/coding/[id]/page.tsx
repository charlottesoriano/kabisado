import React from 'react';
import { WebCodingProblem } from '../../../components/web/WebCodingProblem';
import { useRouter, useParams } from '../../../lib/router';
import { MOCK_CODING_PROBLEM } from '../../../data/mockData';

/**
 * Next.js Dynamic Page Route: /coding/[id]
 */
export default function CodingProblemPage() {
  const router = useRouter();
  const params = useParams();
  const deckId = params.id || 'deck-1';

  return (
    <WebCodingProblem
      codingProblem={MOCK_CODING_PROBLEM}
      onNextProblem={() => router.push('/dashboard')}
      onTrySimilar={() => {}}
    />
  );
}
