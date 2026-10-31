import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { QuizQuestionItem } from '../../types';
import {
  X,
  CheckCircle2,
  XCircle,
  Sparkles,
  Info,
  ArrowRight,
  ChevronUp,
} from 'lucide-react';

interface MobileQuizAnsweredProps {
  quizItem: QuizQuestionItem;
  questionIndex?: number;
  totalQuestions?: number;
  onNextQuestion: () => void;
  onClose: () => void;
}

export const MobileQuizAnswered: React.FC<MobileQuizAnsweredProps> = ({
  quizItem,
  questionIndex = 3,
  totalQuestions = 10,
  onNextQuestion,
  onClose,
}) => {
  const [showDetailedExplanation, setShowDetailedExplanation] = useState(false);

  return (
    <div className="flex-1 flex flex-col justify-between bg-[#F3FAF8] relative overflow-hidden">
      {/* Top Header */}
      <div className="p-5 pb-0">
        <div className="flex items-center justify-between mb-3">
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl bg-white border text-[#1A281F] cursor-pointer"
            style={{ borderColor: '#B8D3D1' }}
          >
            <X className="w-4 h-4" strokeWidth={2} />
          </button>

          <span className="font-heading text-xs font-bold text-[#1A281F]">
            Question {questionIndex} of {totalQuestions}
          </span>

          <span className="text-xs text-[#635255] font-semibold">
            Bio 101
          </span>
        </div>

        {/* 10-Segment Progress Bar */}
        <div className="grid grid-cols-10 gap-1 h-2">
          {Array.from({ length: totalQuestions }).map((_, i) => {
            let color = '#C7EAE4';
            if (i < questionIndex - 1) color = '#A7E8BD'; // correct
            if (i === questionIndex - 1) color = '#FCBCB8'; // wrong
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

      {/* Main Content: Question and Options */}
      <div className="p-5 space-y-3.5 pb-24 overflow-y-auto">
        <div className="rounded-[20px] p-4 border bg-white shadow-xs" style={{ borderColor: '#B8D3D1' }}>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#635255]">
            Single Best Answer
          </span>
          <h2 className="font-heading text-sm font-bold text-[#1A281F] mt-1 leading-snug">
            {quizItem.question}
          </h2>
        </div>

        {/* Option list with correct/wrong states */}
        <div className="space-y-2">
          {quizItem.options.map((opt) => {
            const isUserWrongAnswer = opt.id === quizItem.userSelectedOptionId && opt.id !== quizItem.correctOptionId;
            const isCorrectOption = opt.id === quizItem.correctOptionId;

            let bgColor = '#FFFFFF';
            let borderColor = '#B8D3D1';
            let badge = null;

            if (isUserWrongAnswer) {
              bgColor = '#FCBCB8';
              borderColor = '#CE7B91';
              badge = (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1 shrink-0"
                  style={{ backgroundColor: '#FFFFFF', color: '#1A281F', borderColor: '#CE7B91' }}
                >
                  <XCircle className="w-3 h-3 text-[#1A281F]" />
                  <span>Your answer</span>
                </span>
              );
            } else if (isCorrectOption) {
              bgColor = '#A7E8BD';
              borderColor = '#1A281F';
              badge = (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1 shrink-0"
                  style={{ backgroundColor: '#1A281F', color: '#FFFFFF', borderColor: '#1A281F' }}
                >
                  <CheckCircle2 className="w-3 h-3 text-white" />
                  <span>Correct</span>
                </span>
              );
            }

            return (
              <div
                key={opt.id}
                className="p-3 rounded-xl border flex items-center justify-between gap-2.5 transition-all"
                style={{
                  backgroundColor: bgColor,
                  borderColor: borderColor,
                  borderWidth: isCorrectOption || isUserWrongAnswer ? '1.5px' : '1px',
                }}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span
                    className="w-6 h-6 rounded-md flex items-center justify-center font-bold text-[11px] shrink-0 border"
                    style={{
                      backgroundColor: isCorrectOption ? '#1A281F' : '#FFFFFF',
                      color: isCorrectOption ? '#FFFFFF' : '#1A281F',
                      borderColor: '#1A281F',
                    }}
                  >
                    {opt.label}
                  </span>
                  <span className="text-xs font-semibold text-[#1A281F] leading-tight">
                    {opt.text}
                  </span>
                </div>
                {badge}
              </div>
            );
          })}
        </div>
      </div>

      {/* Native Bottom Sheet: "Not quite", explanation, Explain my mistake and Next question */}
      <div
        className="rounded-t-[28px] border-t-2 bg-white p-5 shadow-lg space-y-3.5 z-40 transition-all"
        style={{
          borderColor: '#B8D3D1',
        }}
      >
        {/* Grab Handle */}
        <div className="w-10 h-1 bg-[#B8D3D1] rounded-full mx-auto -mt-1 mb-2" />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className="px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1"
              style={{
                backgroundColor: '#FCBCB8',
                borderColor: '#EFA7A7',
                color: '#1A281F',
              }}
            >
              <XCircle className="w-3.5 h-3.5 text-[#1A281F]" />
              <span>Not quite</span>
            </span>
            <span className="text-xs font-medium text-[#635255]">
              Correct: Option D
            </span>
          </div>

          {/* Explain my mistake button: Pale Sky (#C0E8F9) with Evergreen text */}
          <button
            type="button"
            onClick={() => setShowDetailedExplanation(!showDetailedExplanation)}
            className="px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 cursor-pointer transition-all active:scale-95 border"
            style={{
              backgroundColor: '#C0E8F9',
              borderColor: '#B8D3D1',
              color: '#1A281F',
            }}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Explain mistake</span>
          </button>
        </div>

        <p className="text-xs text-[#1A281F] leading-relaxed">
          {quizItem.explanation}
        </p>

        {showDetailedExplanation && (
          <div
            className="p-3 rounded-xl border text-xs leading-relaxed space-y-1"
            style={{ backgroundColor: '#F3FAF8', borderColor: '#FFD972' }}
          >
            <p className="font-bold text-[#1A281F]">Why C was tempting:</p>
            <p className="text-[#635255]">
              {quizItem.detailedMistakeExplanation}
            </p>
          </div>
        )}

        <div className="pt-1">
          <Button
            variant="primary"
            size="lg"
            fullWidth
            onClick={onNextQuestion}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Next question
          </Button>
        </div>
      </div>
    </div>
  );
};
