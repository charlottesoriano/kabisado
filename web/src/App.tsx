import React, { useState } from 'react';
import { PlatformMode, WebScreen, MobileScreen, DeckItem, Flashcard } from './types';
import {
  MOCK_DECKS,
  MOCK_FLASHCARDS,
  MOCK_WEAK_TOPICS,
  MOCK_QUIZ_QUESTION,
  MOCK_PROBLEM,
  MOCK_CODING_PROBLEM,
} from './data/mockData';

// Common Components
import { PlatformSwitcher } from './components/common/PlatformSwitcher';

// Web Components
import { WebNavbar } from './components/web/WebNavbar';
import { WebSignIn } from './components/web/WebSignIn';
import { WebDashboard } from './components/web/WebDashboard';
import { WebUpload } from './components/web/WebUpload';
import { WebDeckPage } from './components/web/WebDeckPage';
import { WebFlashcardReview } from './components/web/WebFlashcardReview';
import { WebQuiz } from './components/web/WebQuiz';
import { WebQuizResults } from './components/web/WebQuizResults';
import { WebProblemPractice } from './components/web/WebProblemPractice';
import { WebCodingProblem } from './components/web/WebCodingProblem';

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

export default function App() {
  // Platform & Navigation State
  const [platform, setPlatform] = useState<PlatformMode>('web');
  const [webScreen, setWebScreen] = useState<WebScreen>('dashboard');
  const [mobileScreen, setMobileScreen] = useState<MobileScreen>('home');
  const [webViewportWidth, setWebViewportWidth] = useState<'full' | '1280' | '768' | '375'>('1280');
  const [mobileTab, setMobileTab] = useState<MobileTab>('home');

  // App Data State
  const [decks, setDecks] = useState<DeckItem[]>(MOCK_DECKS);
  const [flashcards, setFlashcards] = useState<Flashcard[]>(MOCK_FLASHCARDS);
  const [selectedDeckId, setSelectedDeckId] = useState<string>('deck-1');

  // Simulated Special States
  const [isEmptyState, setIsEmptyState] = useState(false);
  const [isFailedUploadState, setIsFailedUploadState] = useState(false);
  const [isLoadingSkeleton, setIsLoadingSkeleton] = useState(false);
  const [isMobileOffline, setIsMobileOffline] = useState(false);

  const currentDeck = decks.find((d) => d.id === selectedDeckId) || decks[0];

  // Handlers for Web transitions
  const handleWebNewDeck = () => {
    setWebScreen('upload');
  };

  const handleWebGenerateSuccess = (title: string) => {
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
    setSelectedDeckId(newDeck.id);
    setWebScreen('deck');
  };

  const handleMobileTabChange = (tab: MobileTab) => {
    setMobileTab(tab);
    if (tab === 'home') setMobileScreen('home');
    if (tab === 'decks') setMobileScreen('home');
    if (tab === 'upload') {
      // In mobile, switch to front or practice
      setMobileScreen('home');
    }
  };

  // Viewport container width class for Web mode preview
  const getViewportContainerClass = () => {
    switch (webViewportWidth) {
      case '1280':
        return 'max-w-[1280px] mx-auto border-x shadow-xs';
      case '768':
        return 'max-w-[768px] mx-auto border-x shadow-xs';
      case '375':
        return 'max-w-[375px] mx-auto border-x shadow-xs';
      default:
        return 'w-full';
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F3FAF8] text-[#1A281F]">
      {/* Top Banner / Platform & Screen Switcher */}
      <PlatformSwitcher
        platform={platform}
        onPlatformChange={setPlatform}
        webScreen={webScreen}
        onWebScreenChange={setWebScreen}
        mobileScreen={mobileScreen}
        onMobileScreenChange={setMobileScreen}
        webViewportWidth={webViewportWidth}
        onWebViewportWidthChange={setWebViewportWidth}
        isEmptyState={isEmptyState}
        onToggleEmptyState={() => setIsEmptyState(!isEmptyState)}
        isFailedUploadState={isFailedUploadState}
        onToggleFailedUploadState={() => {
          setIsFailedUploadState(!isFailedUploadState);
          if (platform === 'web') setWebScreen('upload');
        }}
        isLoadingSkeleton={isLoadingSkeleton}
        onToggleLoadingSkeleton={() => setIsLoadingSkeleton(!isLoadingSkeleton)}
        isMobileOffline={isMobileOffline}
        onToggleMobileOffline={() => setIsMobileOffline(!isMobileOffline)}
      />

      {/* Main Content Render */}
      {platform === 'web' ? (
        <div className="flex-1 flex flex-col">
          {/* Web Navigation bar (shown on standard pages, omitted on focus modes and auth) */}
          {webScreen !== 'signin' && webScreen !== 'flashcard' && (
            <WebNavbar
              currentScreen={webScreen}
              onNavigate={(s) => setWebScreen(s)}
              onNewDeckClick={handleWebNewDeck}
            />
          )}

          {/* Viewport Width Constraint Wrapper */}
          <main
            className={`flex-1 transition-all ${getViewportContainerClass()}`}
            style={{
              backgroundColor: '#F3FAF8',
              borderColor: '#B8D3D1',
            }}
          >
            {webScreen === 'signin' && (
              <WebSignIn
                onSignInSuccess={() => setWebScreen('dashboard')}
              />
            )}

            {webScreen === 'dashboard' && (
              <WebDashboard
                decks={decks}
                weakTopics={MOCK_WEAK_TOPICS}
                isEmptyState={isEmptyState}
                isLoadingSkeleton={isLoadingSkeleton}
                onDeckClick={(id) => {
                  setSelectedDeckId(id);
                  setWebScreen('deck');
                }}
                onStartReview={() => setWebScreen('flashcard')}
                onTakeQuiz={() => setWebScreen('quiz')}
                onNewDeckClick={handleWebNewDeck}
              />
            )}

            {webScreen === 'upload' && (
              <WebUpload
                isFailedUploadState={isFailedUploadState}
                onRetryUpload={() => setIsFailedUploadState(false)}
                onGenerateSuccess={handleWebGenerateSuccess}
                onCancel={() => setWebScreen('dashboard')}
              />
            )}

            {webScreen === 'deck' && (
              <WebDeckPage
                deck={currentDeck}
                flashcards={flashcards}
                onStartReview={() => setWebScreen('flashcard')}
                onStartQuiz={() => setWebScreen('quiz')}
                onPracticeProblems={() => setWebScreen('problem')}
                onCodingProblemClick={() => setWebScreen('coding')}
              />
            )}

            {webScreen === 'flashcard' && (
              <WebFlashcardReview
                flashcard={flashcards[0]}
                cardNumber={5}
                totalCards={12}
                onClose={() => setWebScreen('deck')}
                onRate={() => {
                  // user can click rating buttons
                }}
              />
            )}

            {webScreen === 'quiz' && (
              <WebQuiz
                quizItem={MOCK_QUIZ_QUESTION}
                questionIndex={3}
                totalQuestions={10}
                onNextQuestion={() => setWebScreen('quiz-results')}
                onFinishQuiz={() => setWebScreen('quiz-results')}
              />
            )}

            {webScreen === 'quiz-results' && (
              <WebQuizResults
                onReviewMissedAsFlashcards={() => setWebScreen('flashcard')}
                onRetakeQuiz={() => setWebScreen('quiz')}
                onBackToDeck={() => setWebScreen('deck')}
              />
            )}

            {webScreen === 'problem' && (
              <WebProblemPractice
                problem={MOCK_PROBLEM}
                onNextProblem={() => setWebScreen('coding')}
                onTrySimilar={() => {
                  // toggle similar
                }}
              />
            )}

            {webScreen === 'coding' && (
              <WebCodingProblem
                codingProblem={MOCK_CODING_PROBLEM}
                onNextProblem={() => setWebScreen('dashboard')}
                onTrySimilar={() => {
                  // toggle similar
                }}
              />
            )}
          </main>
        </div>
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
                onDeckClick={(id) => {
                  setSelectedDeckId(id);
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
