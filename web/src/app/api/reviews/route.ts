import { NextResponse } from 'next/server';

interface ReviewSubmission {
  cardId: string;
  rating: 'again' | 'hard' | 'good' | 'easy';
  currentIntervalDays?: number;
}

const INTERVAL_MAP = {
  again: { nextDays: 1, easeChange: -0.2, xp: 5 },
  hard: { nextDays: 3, easeChange: -0.15, xp: 8 },
  good: { nextDays: 6, easeChange: 0, xp: 10 },
  easy: { nextDays: 9, easeChange: +0.15, xp: 12 },
};

/**
 * Next.js API Route: POST /api/reviews
 * Computes Leitner SM-2 interval schedules and updates user XP
 */
export async function POST(request: Request) {
  try {
    const body: ReviewSubmission = await request.json();
    const { cardId, rating } = body;

    if (!rating || !INTERVAL_MAP[rating]) {
      return NextResponse.json(
        { success: false, error: 'Invalid rating parameter. Must be again, hard, good, or easy.' },
        { status: 400 }
      );
    }

    const { nextDays, easeChange, xp } = INTERVAL_MAP[rating];
    const nextDueDate = new Date();
    nextDueDate.setDate(nextDueDate.getDate() + nextDays);

    return NextResponse.json({
      success: true,
      cardId: cardId || 'fc-1',
      rating,
      nextIntervalDays: nextDays,
      nextDueDate: nextDueDate.toISOString(),
      xpAwarded: xp,
      message: `Card scheduled for review in ${nextDays} day${nextDays > 1 ? 's' : ''}`,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to process review rating' },
      { status: 500 }
    );
  }
}
