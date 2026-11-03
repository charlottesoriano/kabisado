import { NextResponse } from 'next/server';

/**
 * Next.js API Route: GET /api/streak
 * Returns user consecutive study streak, freeze shields, and activity history
 */
export async function GET() {
  return NextResponse.json({
    success: true,
    data: {
      consecutiveDays: 14,
      longestStreak: 21,
      reviewedToday: true,
      freezeShieldsAvailable: 1,
      currentAcademicRank: "Dean's Lister",
      level: 7,
      totalXp: 2450,
      nextLevelXp: 3000,
    },
    timezone: 'Asia/Manila (PST)',
    timestamp: new Date().toISOString(),
  });
}
