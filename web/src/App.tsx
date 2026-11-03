import React, { useState, useEffect } from 'react';
import { PlatformMode, WebScreen, MobileScreen, DeckItem, Flashcard } from './types';
import {
  MOCK_DECKS,
  MOCK_FLASHCARDS,
  MOCK_WEAK_TOPICS,
  MOCK_QUIZ_QUESTION,
  MOCK_PROBLEM,
  MOCK_CODING_PROBLEM,
} from './data/mockData';

// Next.js Router & Layout
import { NextRouterProvider, useRouter, usePathname, useParams } from './lib/router';
import RootLayout from './app/layout';

// Next.js Page Route Components
import DashboardPage from './app/dashboard/page';
import UploadPage from './app/upload/page';
import DeckDetailPage from './app/decks/[id]/page';
import ReviewPage from './app/review/[id]/page';
import QuizPage from './app/quiz/[id]/page';
import QuizResultsPage from './app/quiz/[id]/results/page';
import ProblemPracticePage from './app/problems/[id]/page';
import CodingProblemPage from './app/coding/[id]/page';
import SignInPage from './app/sign-in/page';

// Common Components
import { PlatformSwitcher } from './components/common/PlatformSwitcher';

// Mobile Components
import { MobileFrame } from './components/mobile/MobileFrame';
import { MobileSignIn } from './components/mobile/MobileSignIn';
import { MobileHome } from './components/mobile/MobileHome';
import { MobileFlashcardFront } from './components/mobile/MobileFlashcardFront';
import { MobileFlashcardBack } from './components/mobile/MobileFlashcardBack';
import { MobileQuizQuestion } from './components/mobile/MobileQuizQuestion';
import { MobileQuizAnswered } from './components/mobile/MobileQuizAnswered';
import { MobileProblemPractice } from './components/mobile/MobileProblemPractice';
import { MobileTab } from './components/mobile/MobileTabBar';

// Helper to map pathname to WebScreen for PlatformSwitcher dropdown sync
const getWebScreenFromPath = (path: string): WebScreen => {
  if (path === '/sign-in') return 'signin';
  if (path === '/upload') return 'upload';
  if (path.startsWith('/review/')) return 'flashcard';
  if (path.endsWith('/results')) return 'quiz-results';
  if (path.startsWith('/quiz/')) return 'quiz';
  if (path.startsWith('/problems/')) return 'problem';
  if (path.startsWith('/coding/')) return 'coding';
  if (path.startsWith('/decks/')) return 'deck';
  return 'dashboard';
};

// Helper to map WebScreen to Next.js route path
const getRouteFromWebScreen = (screen: WebScreen): string => {
  switch (screen) {
    case 'signin':
      return '/sign-in';
    case 'dashboard':
      return '/dashboard';
    case 'upload':
      return '/upload';
    case 'deck':
      return '/decks/deck-1';
    case 'flashcard':
      return '/review/deck-1';
    case 'quiz':
      return '/quiz/deck-1';
    case 'quiz-results':
      return '/quiz/deck-1/results';
    case 'problem':
      return '/problems/prob-101';
    case 'coding':
      return '/coding/code-101';
    default:
      return '/dashboard';
  }
};

function AppContent() {
  const router = useRouter();
  const pathname = usePathname();

  // Platform & Viewport Mode
  const [platform, setPlatform] = useState<PlatformMode>('web');
  const [mobileScreen, setMobileScreen] = useState<MobileScreen>('home');
  const [webViewportWidth, setWebViewportWidth] = useState<'full' | '1280' | '768' | '375'>('1280');
  const [mobileTab, setMobileTab] = useState<MobileTab>('home');

  // App Data State
  const [decks, setDecks] = useState<DeckItem[]>(MOCK_DECKS);
  const [flashcards] = useState<Flashcard[]>(MOCK_FLASHCARDS);

  // Special UI simulation states
  const [isEmptyState, setIsEmptyState] = useState(false);
  const [isFailedUploadState, setIsFailedUploadState] = useState(false);
  const [isLoadingSkeleton, setIsLoadingSkeleton] = useState(false);
  const [isMobileOffline, setIsMobileOffline] = useState(false);

  const currentWebScreen = getWebScreenFromPath(pathname);

  const handleWebScreenSelect = (screen: WebScreen) => {
    const route = getRouteFromWebScreen(screen);
    router.push(route);
  };

  const handleMobileTabChange = (tab: MobileTab) => {
    setMobileTab(tab);
    if (tab === 'home' || tab === 'decks') setMobileScreen('home');
    if (tab === 'upload') setMobileScreen('home');
  };

  const handleGenerateSuccess = (title: string) => {
    const newDeck: DeckItem = {
      id: `deck-${Date.now()}`,
      title: title || 'New Reviewer',
      subject: 'Custom Notes',
      source: 'Uploaded notes PDF (Generated just now)',
      totalPages: 12,
      totalCards: 14,
      dueCards: 14,
      masteryPercentage: 0,
      status: 'ready',
    };
    setDecks([newDeck, ...decks]);
    router.push(`/decks/${newDeck.id}`);
  };

  // Next.js Route Page Matcher following page routing rules
  const renderNextJsPage = () => {
    if (pathname === '/sign-in') {
      return <SignInPage />;
    }

    if (pathname === '/upload') {
      return (
        <UploadPage
          isFailedUploadState={isFailedUploadState}
          onRetryUpload={() => setIsFailedUploadState(false)}
          onGenerateSuccess={handleGenerateSuccess}
        />
      );
    }

    if (pathname.startsWith('/review/')) {
      return <ReviewPage flashcards={flashcards} />;
    }

    if (pathname.endsWith('/results')) {
      return <QuizResultsPage />;
    }

    if (pathname.startsWith('/quiz/')) {
      return <QuizPage />;
    }

    if (pathname.startsWith('/problems/')) {
      return <ProblemPracticePage />;
    }

    if (pathname.startsWith('/coding/')) {
      return <CodingProblemPage />;
    }

    if (pathname.startsWith('/decks/')) {
      return <DeckDetailPage decks={decks} flashcards={flashcards} />;
    }

    // Default to /dashboard
    return (
      <DashboardPage
        decks={decks}
        weakTopics={MOCK_WEAK_TOPICS}
        isEmptyState={isEmptyState}
        isLoadingSkeleton={isLoadingSkeleton}
      />
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F3FAF8] text-[#1A281F]">
      {/* Top Banner / Platform & Next.js Route Switcher */}
      <PlatformSwitcher
        platform={platform}
        onPlatformChange={setPlatform}
        webScreen={currentWebScreen}
        onWebScreenChange={handleWebScreenSelect}
        mobileScreen={mobileScreen}
        onMobileScreenChange={setMobileScreen}
        webViewportWidth={webViewportWidth}
        onWebViewportWidthChange={setWebViewportWidth}
        isEmptyState={isEmptyState}
        onToggleEmptyState={() => setIsEmptyState(!isEmptyState)}
        isFailedUploadState={isFailedUploadState}
        onToggleFailedUploadState={() => {
          setIsFailedUploadState(!isFailedUploadState);
          if (platform === 'web') router.push('/upload');
        }}
        isLoadingSkeleton={isLoadingSkeleton}
        onToggleLoadingSkeleton={() => setIsLoadingSkeleton(!isLoadingSkeleton)}
        isMobileOffline={isMobileOffline}
        onToggleMobileOffline={() => setIsMobileOffline(!isMobileOffline)}
        currentRoute={pathname}
      />

      {/* Main Content Render */}
      {platform === 'web' ? (
        /* Next.js RootLayout with current page */
        <RootLayout webViewportWidth={webViewportWidth}>
          {renderNextJsPage()}
        </RootLayout>
      ) : (
        /* Mobile App (390x844 frame feel) */
        <div className="flex-1 flex items-center justify-center bg-[#1A281F]/5 p-2">
          <MobileFrame isOffline={isMobileOffline}>
            {mobileScreen === 'signin' && (
              <MobileSignIn
                onSignInSuccess={() => setMobileScreen('home')}
              />
            )}

            {mobileScreen === 'home' && (
              <MobileHome
                decks={decks}
                activeTab={mobileTab}
                onTabChange={handleMobileTabChange}
                onDeckClick={() => {
                  setMobileScreen('flashcard-front');
                }}
                onStartReview={() => setMobileScreen('flashcard-front')}
                onOpenDeckPage={() => setMobileScreen('flashcard-front')}
              />
            )}

            {mobileScreen === 'flashcard-front' && (
              <MobileFlashcardFront
                flashcard={flashcards[0]}
                cardNumber={5}
                totalCards={12}
                onFlipToBack={() => setMobileScreen('flashcard-back')}
                onClose={() => setMobileScreen('home')}
              />
            )}

            {mobileScreen === 'flashcard-back' && (
              <MobileFlashcardBack
                flashcard={flashcards[0]}
                cardNumber={5}
                totalCards={12}
                onRate={() => setMobileScreen('flashcard-front')}
                onFlipToFront={() => setMobileScreen('flashcard-front')}
                onClose={() => setMobileScreen('home')}
              />
            )}

            {mobileScreen === 'quiz-question' && (
              <MobileQuizQuestion
                quizItem={MOCK_QUIZ_QUESTION}
                questionIndex={3}
                totalQuestions={10}
                onCheckAnswer={() => setMobileScreen('quiz-answered')}
                onClose={() => setMobileScreen('home')}
              />
            )}

            {mobileScreen === 'quiz-answered' && (
              <MobileQuizAnswered
                quizItem={MOCK_QUIZ_QUESTION}
                questionIndex={3}
                totalQuestions={10}
                onNextQuestion={() => setMobileScreen('problem')}
                onClose={() => setMobileScreen('home')}
              />
            )}

            {mobileScreen === 'problem' && (
              <MobileProblemPractice
                problem={MOCK_PROBLEM}
                onNextProblem={() => setMobileScreen('home')}
                onTrySimilar={() => {}}
                onClose={() => setMobileScreen('home')}
              />
            )}
          </MobileFrame>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <NextRouterProvider>
      <AppContent />
    </NextRouterProvider>
  );
}
