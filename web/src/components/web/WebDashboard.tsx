import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { DeckItem, WeakTopic } from '../../types';
import {
  Clock,
  Flame,
  Award,
  Layers,
  Sparkles,
  ChevronRight,
  UploadCloud,
  Play,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

interface WebDashboardProps {
  decks: DeckItem[];
  weakTopics: WeakTopic[];
  isEmptyState?: boolean;
  isLoadingSkeleton?: boolean;
  onDeckClick: (deckId: string) => void;
  onStartReview: () => void;
  onTakeQuiz: () => void;
  onNewDeckClick: () => void;
}

export const WebDashboard: React.FC<WebDashboardProps> = ({
  decks,
  weakTopics,
  isEmptyState = false,
  isLoadingSkeleton = false,
  onDeckClick,
  onStartReview,
  onTakeQuiz,
  onNewDeckClick,
}) => {
  if (isLoadingSkeleton) {
    return (
      <div className="max-w-[1280px] mx-auto px-6 py-8 animate-pulse space-y-8">
        {/* Skeleton Hero */}
        <div className="h-44 rounded-[16px] bg-[#B8D3D1]/40 border border-[#B8D3D1]" />
        {/* Skeleton Stat Tiles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="h-28 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
          <div className="h-28 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
          <div className="h-28 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
        </div>
        {/* Skeleton Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-4">
            <div className="h-24 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
            <div className="h-24 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
            <div className="h-24 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
          </div>
          <div className="lg:col-span-4 h-80 rounded-[16px] bg-[#B8D3D1]/30 border border-[#B8D3D1]" />
        </div>
      </div>
    );
  }

  if (isEmptyState) {
    return (
      <div className="max-w-[1280px] mx-auto px-6 py-12">
        <Card className="p-12 text-center max-w-2xl mx-auto flex flex-col items-center">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            <UploadCloud className="w-8 h-8" strokeWidth={2} />
          </div>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-[#1A281F]">
            Upload your notes
          </h2>
          <p className="mt-2 text-[15px] leading-relaxed text-[#635255] max-w-md">
            You don't have any study reviewers yet. Upload your PDF slides or lecture notes, and Kabisado will automatically extract flashcards, quizzes, and problem sets.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <Button
              variant="primary"
              size="lg"
              onClick={onNewDeckClick}
              icon={<UploadCloud className="w-5 h-5" />}
            >
              Upload PDF or Notes
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8 space-y-8">
      {/* 1. Hero Card */}
      <Card
        className="p-7 md:p-8 relative overflow-hidden"
        style={{
          backgroundColor: '#FFFFFF',
          borderColor: '#B8D3D1',
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
              >
                <Clock className="w-3.5 h-3.5" strokeWidth={2} />
                Daily Review Batch
              </span>
              <span className="text-xs text-[#635255] font-medium">
                Optimized by Leitner SM-2
              </span>
            </div>
            <h1 className="font-heading text-3xl md:text-4xl font-bold tracking-tight text-[#1A281F]">
              24 cards due today
            </h1>
            <p className="text-[15px] text-[#635255]">
              Across 3 decks · about 12 minutes
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Button
              variant="primary"
              size="lg"
              onClick={onStartReview}
              icon={<Play className="w-4 h-4 fill-white" />}
            >
              Start review
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={onTakeQuiz}
              icon={<Award className="w-4 h-4" />}
            >
              Take a quiz
            </Button>
          </div>
        </div>
      </Card>

      {/* 2. Three Stat Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Tile 1: Due Today */}
        <Card className="p-5 flex items-center gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
          >
            <Clock className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <p className="text-xs font-medium text-[#635255]">Due today</p>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="font-heading text-2xl font-bold tracking-tight text-[#1A281F] tabular-nums">
                24
              </span>
              <span className="text-xs text-[#635255]">cards scheduled</span>
            </div>
          </div>
        </Card>

        {/* Tile 2: Quiz Accuracy */}
        <Card className="p-5 flex items-center gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
          >
            <Award className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <p className="text-xs font-medium text-[#635255]">Quiz accuracy (last 7 days)</p>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="font-heading text-2xl font-bold tracking-tight text-[#1A281F] tabular-nums">
                86%
              </span>
              <span className="text-xs font-semibold text-[#1A281F]">
                +4% vs last week
              </span>
            </div>
          </div>
        </Card>

        {/* Tile 3: Study Streak */}
        <Card className="p-5 flex items-center gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            <Flame className="w-6 h-6" strokeWidth={2} />
          </div>
          <div>
            <p className="text-xs font-medium text-[#635255]">Study streak</p>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="font-heading text-2xl font-bold tracking-tight text-[#1A281F] tabular-nums">
                14 days
              </span>
              <span className="text-xs text-[#635255]">Keep it up!</span>
            </div>
          </div>
        </Card>
      </div>

      {/* 3. Main Grid: Deck List (8 cols) + Weakest Topics Side Panel (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Deck List */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl font-bold tracking-tight text-[#1A281F]">
              Your Reviewers ({decks.length})
            </h2>
            <button
              type="button"
              onClick={onNewDeckClick}
              className="text-xs font-semibold text-[#1A281F] hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>Upload notes</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {decks.map((deck) => {
              const isGenerating = deck.status === 'generating';

              return (
                <div
                  key={deck.id}
                  onClick={() => !isGenerating && onDeckClick(deck.id)}
                  className={`p-5 rounded-[16px] border bg-white transition-all ${
                    isGenerating
                      ? 'cursor-wait opacity-95'
                      : 'cursor-pointer hover:border-[#1A281F] hover:shadow-xs active:scale-[0.99]'
                  }`}
                  style={{
                    borderColor: '#B8D3D1',
                  }}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className="px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide uppercase"
                          style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                        >
                          {deck.subject}
                        </span>
                        {isGenerating ? (
                          <span
                            className="text-xs font-semibold flex items-center gap-1"
                            style={{ color: '#1A281F' }}
                          >
                            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#CE7B91' }} />
                            Generating reviewer ({deck.generatingProgress}%)
                          </span>
                        ) : (
                          <span className="text-xs text-[#635255]">
                            {deck.totalCards} cards · {deck.totalPages} pages
                          </span>
                        )}
                      </div>

                      <h3 className="font-heading text-lg font-bold tracking-tight text-[#1A281F]">
                        {deck.title}
                      </h3>
                      <p className="text-xs text-[#635255] line-clamp-1">
                        {deck.source}
                      </p>
                    </div>

                    {/* Right side: Mastery Bar & Due Badge or Generating progress */}
                    <div className="flex sm:flex-col items-end justify-between sm:justify-center gap-2 shrink-0">
                      {isGenerating ? (
                        <div className="w-36 space-y-1 text-right">
                          <span className="text-[11px] font-medium text-[#635255]">
                            Parsing formulas &amp; diagrams
                          </span>
                          {/* Progress bar with Old Rose (#CE7B91) fill */}
                          <div
                            className="w-full h-2 rounded-full overflow-hidden"
                            style={{ backgroundColor: '#C7EAE4' }}
                          >
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${deck.generatingProgress}%`,
                                backgroundColor: '#CE7B91',
                              }}
                            />
                          </div>
                        </div>
                      ) : (
                        <>
                          {deck.dueCards > 0 ? (
                            <span
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold"
                              style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
                            >
                              <Clock className="w-3 h-3" strokeWidth={2.5} />
                              {deck.dueCards} due
                            </span>
                          ) : (
                            <span
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
                              style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              All caught up
                            </span>
                          )}

                          {/* Mastery progress */}
                          <div className="w-32 space-y-1 text-right">
                            <div className="flex items-center justify-between text-[11px] text-[#635255] tabular-nums">
                              <span>Mastery</span>
                              <span className="font-semibold text-[#1A281F]">{deck.masteryPercentage}%</span>
                            </div>
                            <div
                              className="w-full h-1.5 rounded-full overflow-hidden"
                              style={{ backgroundColor: '#C7EAE4' }}
                            >
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${deck.masteryPercentage}%`,
                                  backgroundColor: '#1A281F',
                                }}
                              />
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Weakest Topics Side Panel */}
        <div className="lg:col-span-4">
          <Card className="p-6 space-y-5">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="font-heading text-lg font-bold tracking-tight text-[#1A281F]">
                  Weakest topics
                </h3>
                <span className="text-xs text-[#635255]">Needs attention</span>
              </div>
              <p className="text-xs text-[#635255] mt-1">
                Kabisado identifies concepts where you miss quiz options or rate "Again".
              </p>
            </div>

            <div className="space-y-4">
              {weakTopics.map((topic) => (
                <div key={topic.id} className="space-y-1.5 pb-3 border-b border-[#B8D3D1] last:border-b-0 last:pb-0">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-[#1A281F] leading-snug">
                      {topic.name}
                    </span>
                    <span className="text-xs font-bold text-[#1A281F] tabular-nums shrink-0">
                      {topic.accuracy}%
                    </span>
                  </div>

                  {/* Accuracy Bar using Old Rose (#CE7B91) for weakest topic bar */}
                  <div
                    className="w-full h-2 rounded-full overflow-hidden"
                    style={{ backgroundColor: '#C7EAE4' }}
                  >
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${topic.accuracy}%`,
                        backgroundColor: '#CE7B91',
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#635255]">
                    <span>{topic.deckName}</span>
                    <span>{topic.dueCount} cards due</span>
                  </div>
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              fullWidth
              onClick={onStartReview}
            >
              Drill weakest topics
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};
