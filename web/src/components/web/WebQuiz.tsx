import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { QuizQuestionItem } from '../../types';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  Flag,
  ArrowRight,
  ExternalLink,
  Sparkles,
  Info,
} from 'lucide-react';

interface WebQuizProps {
  quizItem: QuizQuestionItem;
  questionIndex?: number;
  totalQuestions?: number;
  onNextQuestion: () => void;
  onFinishQuiz: () => void;
}

export const WebQuiz: React.FC<WebQuizProps> = ({
  quizItem,
  questionIndex = 3,
  totalQuestions = 10,
  onNextQuestion,
  onFinishQuiz,
}) => {
  const [showDetailedExplanation, setShowDetailedExplanation] = useState(false);
  const [reported, setReported] = useState(false);

  return (
    <div className="max-w-[840px] mx-auto px-6 py-8 space-y-6">
      {/* Quiz Progress Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-[#635255]">
            Question {questionIndex} of {totalQuestions}
          </span>
          <span className="text-[#1A281F]">
            Cellular Respiration Quiz
          </span>
        </div>

        {/* 10-segment styled progress bar */}
        <div className="grid grid-cols-10 gap-1.5 h-2">
          {Array.from({ length: totalQuestions }).map((_, i) => {
            let color = '#C7EAE4'; // default Frozen Water
            if (i < questionIndex - 1) color = '#A7E8BD'; // previously correct
            if (i === questionIndex - 1) color = '#FCBCB8'; // current answered (missed)
            return (
              <div
                key={i}
                className="h-full rounded-full transition-all"
                style={{ backgroundColor: color }}
              />
            );
          })}
        </div>
      </div>

      {/* Question Card */}
      <Card className="p-7 md:p-8 space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#635255]">
            Multiple Choice Question
          </span>
          <h2 className="font-heading text-xl md:text-2xl font-bold tracking-tight text-[#1A281F] mt-2 leading-snug">
            {quizItem.question}
          </h2>
        </div>

        {/* Options A-D with exact Answered States */}
        <div className="space-y-3">
          {quizItem.options.map((opt) => {
            const isUserWrongAnswer = opt.id === quizItem.userSelectedOptionId && opt.id !== quizItem.correctOptionId;
            const isCorrectOption = opt.id === quizItem.correctOptionId;
            const isNeutral = !isUserWrongAnswer && !isCorrectOption;

            let bgColor = '#FFFFFF';
            let borderColor = '#B8D3D1';
            let labelBadge = null;

            if (isUserWrongAnswer) {
              // The chosen wrong option is Powder Blush (#FCBCB8) with an Old Rose (#CE7B91) border, labelled "Your answer"
              bgColor = '#FCBCB8';
              borderColor = '#CE7B91';
              labelBadge = (
                <span
                  className="px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 border shrink-0"
                  style={{
                    backgroundColor: '#FFFFFF',
                    color: '#1A281F',
                    borderColor: '#CE7B91',
                  }}
                >
                  <XCircle className="w-3.5 h-3.5 text-[#1A281F]" strokeWidth={2} />
                  <span>Your answer</span>
                </span>
              );
            } else if (isCorrectOption) {
              // The correct option is Celadon (#A7E8BD) with an Evergreen (#1A281F) border, labelled "Correct"
              bgColor = '#A7E8BD';
              borderColor = '#1A281F';
              labelBadge = (
                <span
                  className="px-2 py-0.5 rounded text-[11px] font-bold flex items-center gap-1 border shrink-0"
                  style={{
                    backgroundColor: '#1A281F',
                    color: '#FFFFFF',
                    borderColor: '#1A281F',
                  }}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-white" strokeWidth={2} />
                  <span>Correct</span>
                </span>
              );
            }

            return (
              <div
                key={opt.id}
                className="p-4 rounded-xl border flex items-center justify-between gap-4 transition-all"
                style={{
                  backgroundColor: bgColor,
                  borderColor: borderColor,
                  borderWidth: isCorrectOption || isUserWrongAnswer ? '1.5px' : '1px',
                }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 border"
                    style={{
                      backgroundColor: isCorrectOption ? '#1A281F' : '#FFFFFF',
                      color: isCorrectOption ? '#FFFFFF' : '#1A281F',
                      borderColor: '#1A281F',
                    }}
                  >
                    {opt.label}
                  </span>
                  <span className="text-sm font-semibold text-[#1A281F]">
                    {opt.text}
                  </span>
                </div>

                {labelBadge}
              </div>
            );
          })}
        </div>

        {/* Explanation Card */}
        <div
          className="p-5 rounded-xl border space-y-4"
          style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#1A281F] flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" strokeWidth={2} />
                Explanation
              </span>
              <p className="text-xs leading-relaxed text-[#1A281F]">
                {quizItem.explanation}
              </p>
            </div>

            {/* "Explain my mistake" button in Pale Sky (#C0E8F9) with Evergreen text */}
            <Button
              variant="pale-sky"
              size="sm"
              onClick={() => setShowDetailedExplanation(!showDetailedExplanation)}
              icon={<Sparkles className="w-3.5 h-3.5" />}
            >
              {showDetailedExplanation ? 'Hide mistake analysis' : 'Explain my mistake'}
            </Button>
          </div>

          {/* AI Diagnostic breakdown of why the chosen answer was tempting */}
          {showDetailedExplanation && (
            <div
              className="p-4 rounded-lg border text-xs leading-relaxed space-y-2 mt-3"
              style={{
                backgroundColor: '#FFFFFF',
                borderColor: '#FFD972',
              }}
            >
              <div className="font-bold text-[#1A281F] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#1A281F]" />
                <span>Misconception Diagnostic:</span>
              </div>
              <p className="text-[#1A281F]">
                {quizItem.detailedMistakeExplanation}
              </p>
              <p className="text-[#635255] font-medium pt-1">
                Study tip: Remember that Krebs produces raw electron currency (NADH/FADH₂), but the mitochondrion's oxidative phosphorylation ATP-synthase engine "cashes them in" for ~28 ATP.
              </p>
            </div>
          )}

          {/* Source Link */}
          <div className="pt-3 border-t border-[#B8D3D1] flex items-center justify-between text-xs text-[#635255]">
            <a
              href="#source"
              onClick={(e) => e.preventDefault()}
              className="flex items-center gap-1 hover:text-[#1A281F] hover:underline font-medium"
            >
              <span>{quizItem.sourceRef}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>Page {quizItem.pageNumber}</span>
          </div>
        </div>

        {/* Action Row: Report question & Next question */}
        <div className="pt-2 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => setReported(true)}
            className="text-xs text-[#635255] hover:text-[#1A281F] flex items-center gap-1.5 font-medium cursor-pointer"
          >
            <Flag className="w-3.5 h-3.5" />
            <span>{reported ? 'Reported to review team' : 'Report question'}</span>
          </button>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="md"
              onClick={onFinishQuiz}
            >
              View Results (7/10)
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={onNextQuestion}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              Next question
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
