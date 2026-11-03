import { NextResponse } from 'next/server';
import { MOCK_DECKS } from '../../../data/mockData';
import { DeckItem } from '../../../types';

// In-memory deck storage for simulated runtime persistence
let currentDecks: DeckItem[] = [...MOCK_DECKS];

/**
 * Next.js API Route: GET /api/decks
 * Returns list of all study decks and reviewers
 */
export async function GET() {
  return NextResponse.json({
    success: true,
    data: currentDecks,
    total: currentDecks.length,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Next.js API Route: POST /api/decks
 * Creates a new deck from uploaded lecture notes or PDF
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, subject, notes, source } = body;

    const newDeck: DeckItem = {
      id: `deck-${Date.now()}`,
      title: title || 'Biology 101 · Cellular Respiration',
      subject: subject || 'Biology',
      source: source || 'Uploaded notes PDF (Campbell Biology Ch. 9)',
      totalPages: 12,
      totalCards: 18,
      dueCards: 18,
      masteryPercentage: 0,
      status: 'ready',
      lastStudied: 'Just now',
    };

    currentDecks = [newDeck, ...currentDecks];

    return NextResponse.json(
      {
        success: true,
        message: 'Reviewer created successfully',
        deck: newDeck,
      },
      { status: 201 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to process deck creation request',
      },
      { status: 400 }
    );
  }
}
