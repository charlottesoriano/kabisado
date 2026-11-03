import { NextResponse } from 'next/server';
import { MOCK_QUIZ_QUESTION } from '../../../data/mockData';

/**
 * Next.js API Route: POST /api/quiz
 * Grades selected quiz option and provides misconception diagnostic
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { questionId, selectedOptionId } = body;

    const isCorrect = selectedOptionId === MOCK_QUIZ_QUESTION.correctOptionId;

    return NextResponse.json({
      success: true,
      questionId: questionId || MOCK_QUIZ_QUESTION.id,
      selectedOptionId,
      correctOptionId: MOCK_QUIZ_QUESTION.correctOptionId,
      isCorrect,
      explanation: MOCK_QUIZ_QUESTION.explanation,
      misconceptionDiagnostic: !isCorrect ? MOCK_QUIZ_QUESTION.detailedMistakeExplanation : null,
      sourceRef: MOCK_QUIZ_QUESTION.sourceRef,
      pageNumber: MOCK_QUIZ_QUESTION.pageNumber,
      xpAwarded: isCorrect ? 25 : 5,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to evaluate quiz answer' },
      { status: 500 }
    );
  }
}
