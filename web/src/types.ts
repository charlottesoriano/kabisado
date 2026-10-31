export type WebScreen =
  | 'signin'
  | 'dashboard'
  | 'upload'
  | 'deck'
  | 'flashcard'
  | 'quiz'
  | 'quiz-results'
  | 'problem'
  | 'coding';

export type MobileScreen =
  | 'signin'
  | 'home'
  | 'flashcard-front'
  | 'flashcard-back'
  | 'quiz-question'
  | 'quiz-answered'
  | 'problem';

export type PlatformMode = 'web' | 'mobile';

export interface DeckItem {
  id: string;
  title: string;
  subject: string;
  source: string;
  totalPages: number;
  totalCards: number;
  dueCards: number;
  masteryPercentage: number;
  status: 'ready' | 'generating' | 'empty';
  generatingProgress?: number;
  lastStudied?: string;
}

export interface Flashcard {
  id: string;
  deckId: string;
  topic: string;
  question: string;
  answer: string;
  highlightedKeyword: string;
  sourceRef: string;
  pageNumber: number;
  isFlagged?: boolean;
}

export interface QuizOption {
  id: string;
  label: string; // "A", "B", "C", "D"
  text: string;
}

export interface QuizQuestionItem {
  id: string;
  question: string;
  options: QuizOption[];
  correctOptionId: string;
  userSelectedOptionId?: string;
  explanation: string;
  sourceRef: string;
  pageNumber: number;
  detailedMistakeExplanation?: string;
}

export interface SolutionStep {
  stepNumber: number;
  title: string;
  explanation: string;
  formula?: string;
}

export interface ProblemItemData {
  id: string;
  title: string;
  subject: string;
  questionHtml: string;
  rawQuestion: string;
  highlightedValues: string[];
  unit: string;
  correctAnswer: string;
  userAnswer?: string;
  userUnit?: string;
  statusText: string;
  mistakeFeedback: string;
  hints: string[];
  usedHintsCount: number;
  workedSolution: SolutionStep[];
}

export interface CodingProblemData {
  id: string;
  title: string;
  language: string;
  task: string;
  codeSnippet: string;
  expectedOutput: string;
  userOutput: string;
  explanation: string;
}

export interface WeakTopic {
  id: string;
  name: string;
  deckName: string;
  accuracy: number;
  dueCount: number;
}
