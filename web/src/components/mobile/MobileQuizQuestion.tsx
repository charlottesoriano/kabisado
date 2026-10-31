import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { QuizQuestionItem } from '../../types';
import { X, CheckCircle2 } from 'lucide-react';

interface MobileQuizQuestionProps {
  quizItem: QuizQuestionItem;
  questionIndex?: number;
  totalQuestions?: number;
  onCheckAnswer: () => void;
  onClose: () => void;
}

export const MobileQuizQuestion: React.FC<MobileQuizQuestionProps> = ({
  quizItem,
  questionIndex = 3,
  totalQuestions = 10,
  onCheckAnswer,
  onClose,
}) => {
  const [selectedOptionId, setSelectedOptionId] = useState<string>('opt-c');

  return (
    <div className="flex-1 p-5 flex flex-col justify-between bg-[#F3FAF8]">
      {/* Top Header */}
      <div>
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

        {/* 10-Segment Progress Bar Colored Per Answer */}
        <div className="grid grid-cols-10 gap-1 h-2">
          {Array.from({ length: totalQuestions }).map((_, i) => {
            let color = '#C7EAE4'; // Frozen Water track
            if (i < questionIndex - 1) color = '#A7E8BD'; // previously correct
            if (i === questionIndex - 1) color = '#1A281F'; // active
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
      <div className="my-auto space-y-4">
        <div className="rounded-[22px] p-5 border bg-white shadow-sm" style={{ borderColor: '#B8D3D1' }}>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#635255]">
            Single Best Answer
          </span>
          <h2 className="font-heading text-base font-bold text-[#1A281F] mt-1 leading-snug">
            {quizItem.question}
          </h2>
        </div>

        {/* Large Option Buttons (touch targets >= 48px) */}
        <div className="space-y-2.5">
          {quizItem.options.map((opt) => {
            const isSelected = selectedOptionId === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => setSelectedOptionId(opt.id)}
                className={`w-full min-h-[52px] p-3.5 rounded-xl border text-left flex items-center gap-3 transition-all cursor-pointer active:scale-[0.99] ${
                  isSelected ? 'border-2' : ''
                }`}
                style={{
                  backgroundColor: isSelected ? '#F3FAF8' : '#FFFFFF',
                  borderColor: isSelected ? '#1A281F' : '#B8D3D1',
                }}
              >
                <span
                  className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 border"
                  style={{
                    backgroundColor: isSelected ? '#1A281F' : '#FFFFFF',
                    color: isSelected ? '#FFFFFF' : '#1A281F',
                    borderColor: '#1A281F',
                  }}
                >
                  {opt.label}
                </span>
                <span className="text-xs font-semibold text-[#1A281F] flex-1">
                  {opt.text}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Check Answer Button */}
      <div className="pt-2">
        <Button
          variant="primary"
          size="lg"
          fullWidth
          onClick={onCheckAnswer}
          icon={<CheckCircle2 className="w-4 h-4" />}
        >
          Check answer
        </Button>
      </div>
    </div>
  );
};
