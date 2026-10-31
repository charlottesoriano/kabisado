import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { MOCK_QUIZ_RESULTS } from '../../data/mockData';
import {
  RotateCcw,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Layers,
} from 'lucide-react';

interface WebQuizResultsProps {
  onReviewMissedAsFlashcards: () => void;
  onRetakeQuiz: () => void;
  onBackToDeck: () => void;
}

export const WebQuizResults: React.FC<WebQuizResultsProps> = ({
  onReviewMissedAsFlashcards,
  onRetakeQuiz,
  onBackToDeck,
}) => {
  const { score, total, percentage, previousPercentage, missedQuestions } = MOCK_QUIZ_RESULTS;

  // SVG circular score ring geometry
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (circumference * percentage) / 100;

  return (
    <div className="max-w-[840px] mx-auto px-6 py-10 space-y-8">
      {/* Top Banner / Summary Card */}
      <Card className="p-8 text-center flex flex-col items-center">
        {/* Score Ring (2px line, Celadon & Evergreen) */}
        <div className="relative w-36 h-36 flex items-center justify-center mb-4">
          <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 128 128">
            {/* Track in Frozen Water (#C7EAE4) */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              stroke="#C7EAE4"
              strokeWidth="10"
              fill="transparent"
            />
            {/* Progress in Evergreen (#1A281F) */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              stroke="#1A281F"
              strokeWidth="10"
              strokeLinecap="round"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-heading text-3xl font-bold tracking-tight text-[#1A281F] tabular-nums">
              {score}/{total}
            </span>
            <span className="text-xs font-semibold text-[#635255]">
              {percentage}%
            </span>
          </div>
        </div>

        <h1 className="font-heading text-2xl font-bold tracking-tight text-[#1A281F]">
          Quiz completed! Good job.
        </h1>

        {/* "Up from 60%" pill/indicator */}
        <div className="mt-2 flex items-center gap-1.5">
          <span
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold"
            style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
          >
            <TrendingUp className="w-3.5 h-3.5" strokeWidth={2.5} />
            <span>Up from {previousPercentage}% on last attempt</span>
          </span>
        </div>

        <p className="mt-3 text-sm text-[#635255] max-w-md">
          You mastered 7 concepts and have 3 questions to reinforce with active spaced repetition.
        </p>

        {/* Action Buttons: Review missed as flashcards / Retake / Back */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Button
            variant="primary"
            size="md"
            onClick={onReviewMissedAsFlashcards}
            icon={<Layers className="w-4 h-4" />}
          >
            Review missed as flashcards
          </Button>

          <Button
            variant="outline"
            size="md"
            onClick={onRetakeQuiz}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Retake quiz
          </Button>

          <Button
            variant="ghost"
            size="md"
            onClick={onBackToDeck}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to deck
          </Button>
        </div>
      </Card>

      {/* List of Missed Questions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-lg font-bold tracking-tight text-[#1A281F]">
            Review Missed Questions ({missedQuestions.length})
          </h2>
          <span className="text-xs text-[#635255]">
            Targeted for Leitner Box 1
          </span>
        </div>

        <div className="space-y-3">
          {missedQuestions.map((q, index) => (
            <Card key={q.id} className="p-5 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span
                  className="px-2 py-0.5 rounded text-[11px] font-semibold"
                  style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                >
                  {q.topic}
                </span>
                <span className="text-[#635255]">Question #{index + 1}</span>
              </div>

              <h3 className="font-heading text-base font-bold text-[#1A281F] leading-snug">
                {q.question}
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {/* Your answer (Powder Blush #FCBCB8 with deep border) */}
                <div
                  className="p-3 rounded-xl border space-y-1"
                  style={{
                    backgroundColor: '#FCBCB8',
                    borderColor: '#EFA7A7',
                  }}
                >
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#1A281F]">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Your answer:</span>
                  </div>
                  <p className="text-xs font-semibold text-[#1A281F]">
                    {q.userAnswer}
                  </p>
                </div>

                {/* Correct answer (Celadon #A7E8BD with Evergreen border) */}
                <div
                  className="p-3 rounded-xl border space-y-1"
                  style={{
                    backgroundColor: '#A7E8BD',
                    borderColor: '#1A281F',
                  }}
                >
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#1A281F]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Correct answer:</span>
                  </div>
                  <p className="text-xs font-semibold text-[#1A281F]">
                    {q.correctAnswer}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
