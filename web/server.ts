import express, { Request, Response } from 'express';
import { createServer as createViteServer } from 'vite';
import { MOCK_DECKS, MOCK_FLASHCARDS, MOCK_QUIZ_QUESTION, MOCK_PROBLEM } from './src/data/mockData';

const PORT = 3000;
const app = express();

app.use(express.json());

// In-memory persistent store
let decksStore = [...MOCK_DECKS];

// Next.js API Routes Proxy & Dispatchers

// GET /api/decks
app.get('/api/decks', (req: Request, res: Response) => {
  res.json({
    success: true,
    data: decksStore,
    total: decksStore.length,
    timestamp: new Date().toISOString(),
  });
});

// POST /api/decks
app.post('/api/decks', (req: Request, res: Response) => {
  const { title, subject, source } = req.body || {};
  const newDeck = {
    id: `deck-${Date.now()}`,
    title: title || 'Biology 101 · Cellular Respiration',
    subject: subject || 'Biology',
    source: source || 'Uploaded notes PDF (Generated just now)',
    totalPages: 12,
    totalCards: 18,
    dueCards: 18,
    masteryPercentage: 0,
    status: 'ready' as const,
    lastStudied: 'Just now',
  };
  decksStore = [newDeck, ...decksStore];
  res.status(201).json({
    success: true,
    message: 'Deck created successfully',
    deck: newDeck,
  });
});

// POST /api/generate
app.post('/api/generate', (req: Request, res: Response) => {
  const { title } = req.body || {};
  res.json({
    success: true,
    deckTitle: title || 'Biology 101 · Cellular Respiration',
    generatedCount: {
      flashcards: MOCK_FLASHCARDS.length,
      quizzes: 12,
      problemSets: 6,
    },
    flashcards: MOCK_FLASHCARDS,
    quizSample: MOCK_QUIZ_QUESTION,
    problemSample: MOCK_PROBLEM,
    timestamp: new Date().toISOString(),
  });
});

// POST /api/reviews
app.post('/api/reviews', (req: Request, res: Response) => {
  const { cardId, rating } = req.body || {};
  const intervals: Record<string, number> = {
    again: 1,
    hard: 3,
    good: 6,
    easy: 9,
  };
  const days = intervals[rating as string] || 1;
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + days);

  res.json({
    success: true,
    cardId: cardId || 'fc-1',
    rating,
    nextIntervalDays: days,
    nextDueDate: dueDate.toISOString(),
    message: `Scheduled in ${days} day${days > 1 ? 's' : ''}`,
  });
});

// POST /api/quiz
app.post('/api/quiz', (req: Request, res: Response) => {
  const { questionId, selectedOptionId } = req.body || {};
  const isCorrect = selectedOptionId === MOCK_QUIZ_QUESTION.correctOptionId;
  res.json({
    success: true,
    questionId: questionId || MOCK_QUIZ_QUESTION.id,
    selectedOptionId,
    correctOptionId: MOCK_QUIZ_QUESTION.correctOptionId,
    isCorrect,
    explanation: MOCK_QUIZ_QUESTION.explanation,
    misconceptionDiagnostic: !isCorrect ? MOCK_QUIZ_QUESTION.detailedMistakeExplanation : null,
  });
});

// GET /api/streak
app.get('/api/streak', (req: Request, res: Response) => {
  res.json({
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
});

async function startServer() {
  // Mount Vite middlewares in development
  const vite = await createViteServer({
    server: { middlewareMode: true },
    appType: 'spa',
  });

  app.use(vite.middlewares);

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Kabisado Next.js full-stack server running on http://localhost:${PORT}`);
  });
}

startServer();
