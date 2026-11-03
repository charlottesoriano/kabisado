import { NextResponse } from 'next/server';
import { MOCK_FLASHCARDS, MOCK_QUIZ_QUESTION, MOCK_PROBLEM } from '../../../data/mockData';

/**
 * Next.js API Route: POST /api/generate
 * Extracts active recall flashcards, quizzes, and auto-graded STEM problem sets
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, text, generationType = 'all' } = body;

    // Simulated parsing and extraction logic
    const generatedFlashcards = MOCK_FLASHCARDS.map((card, i) => ({
      ...card,
      id: `gen-fc-${Date.now()}-${i}`,
    }));

    const responsePayload = {
      success: true,
      deckTitle: title || 'Biology 101 · Cellular Respiration',
      generatedCount: {
        flashcards: generatedFlashcards.length,
        quizzes: 12,
        problemSets: 6,
      },
      flashcards: generatedFlashcards,
      quizSample: MOCK_QUIZ_QUESTION,
      problemSample: MOCK_PROBLEM,
      metadata: {
        parser: 'Kabisado STEM Equation & Active Recall Pipeline',
        spacedRepetitionModel: 'Leitner SM-2',
        timestamp: new Date().toISOString(),
      },
    };

    return NextResponse.json(responsePayload, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Unable to parse provided study notes',
      },
      { status: 500 }
    );
  }
}
