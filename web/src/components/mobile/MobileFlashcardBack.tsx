import React from 'react';
import { Card } from '../common/Card';
import { Flashcard } from '../../types';
import { X, ExternalLink, RotateCw } from 'lucide-react';

interface MobileFlashcardBackProps {
  flashcard: Flashcard;
  cardNumber?: number;
  totalCards?: number;
  onRate: (rating: 'again' | 'hard' | 'good' | 'easy') => void;
  onFlipToFront: () => void;
  onClose: () => void;
}

export const MobileFlashcardBack: React.FC<MobileFlashcardBackProps> = ({
  flashcard,
  cardNumber = 5,
  totalCards = 12,
  onRate,
  onFlipToFront,
  onClose,
}) => {
  // Function to highlight keyword in Jasmine (#FFD972)
  const renderAnswerWithHighlight = (answerText: string, keyword: string) => {
    if (!keyword) return answerText;
    const parts = answerText.split(new RegExp(`(${keyword})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === keyword.toLowerCase() ? (
        <span
          key={index}
          className="px-1.5 py-0.5 rounded font-semibold"
          style={{
            backgroundColor: '#FFD972',
            color: '#1A281F',
          }}
        >
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  return (
    <div className="flex-1 p-5 flex flex-col justify-between bg-[#F3FAF8]">
      {/* Top Bar */}
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
            Card {cardNumber} of {totalCards}
          </span>

          <button
            type="button"
            onClick={onFlipToFront}
            className="p-1.5 rounded-lg text-xs text-[#635255] hover:text-[#1A281F] flex items-center gap-1 cursor-pointer"
          >
            <RotateCw className="w-3 h-3" />
            <span>Flip</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div
          className="w-full h-1.5 rounded-full overflow-hidden"
          style={{ backgroundColor: '#C7EAE4' }}
        >
          <div
            className="h-full rounded-full"
            style={{
              width: `${(cardNumber / totalCards) * 100}%`,
              backgroundColor: '#1A281F',
            }}
          />
        </div>
      </div>

      {/* Back Card: Question small, Answer large, Source link */}
      <div
        className="my-auto rounded-[24px] p-6 border bg-white shadow-sm flex flex-col justify-between min-h-[420px]"
        style={{
          borderColor: '#B8D3D1',
          borderWidth: '1.5px',
        }}
      >
        {/* Question in Small Text */}
        <div className="space-y-1 pb-3 border-b border-[#B8D3D1]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#635255]">
            Question
          </span>
          <p className="text-xs font-medium text-[#635255] line-clamp-2">
            {flashcard.question}
          </p>
        </div>

        {/* Answer in Large Font */}
        <div className="my-auto py-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#1A281F] block mb-2">
            Answer
          </span>
          <p className="text-base md:text-lg font-medium text-[#1A281F] leading-relaxed">
            {renderAnswerWithHighlight(flashcard.answer, flashcard.highlightedKeyword)}
          </p>
        </div>

        {/* Source link */}
        <div className="pt-3 border-t border-[#B8D3D1] flex items-center justify-between text-[11px] text-[#635255]">
          <span className="flex items-center gap-1 truncate font-medium">
            <span>Source:</span>
            <strong className="text-[#1A281F] truncate">{flashcard.sourceRef}</strong>
          </span>
          <span className="shrink-0">p. {flashcard.pageNumber}</span>
        </div>
      </div>

      {/* Four Rating Buttons in One Row */}
      <div className="pt-2">
        <div className="grid grid-cols-4 gap-2">
          {/* Again: Powder Blush */}
          <button
            type="button"
            onClick={() => onRate('again')}
            className="min-h-[48px] py-2 px-1 rounded-xl text-center border flex flex-col items-center justify-center cursor-pointer active:scale-95"
            style={{
              backgroundColor: '#FCBCB8',
              borderColor: '#EFA7A7',
              borderWidth: '1.5px',
            }}
          >
            <span className="text-xs font-bold text-[#1A281F]">Again</span>
            <span className="text-[10px] font-medium text-[#635255]">1d</span>
          </button>

          {/* Hard: Jasmine */}
          <button
            type="button"
            onClick={() => onRate('hard')}
            className="min-h-[48px] py-2 px-1 rounded-xl text-center border flex flex-col items-center justify-center cursor-pointer active:scale-95"
            style={{
              backgroundColor: '#FFD972',
              borderColor: '#B8D3D1',
              borderWidth: '1.5px',
            }}
          >
            <span className="text-xs font-bold text-[#1A281F]">Hard</span>
            <span className="text-[10px] font-medium text-[#635255]">3d</span>
          </button>

          {/* Good: Celadon (Emphasized) */}
          <button
            type="button"
            onClick={() => onRate('good')}
            className="min-h-[48px] py-2 px-1 rounded-xl text-center border-2 flex flex-col items-center justify-center cursor-pointer active:scale-95"
            style={{
              backgroundColor: '#A7E8BD',
              borderColor: '#1A281F',
            }}
          >
            <span className="text-xs font-bold text-[#1A281F]">Good</span>
            <span className="text-[10px] font-bold text-[#1A281F]">6d</span>
          </button>

          {/* Easy: Pale Sky */}
          <button
            type="button"
            onClick={() => onRate('easy')}
            className="min-h-[48px] py-2 px-1 rounded-xl text-center border flex flex-col items-center justify-center cursor-pointer active:scale-95"
            style={{
              backgroundColor: '#C0E8F9',
              borderColor: '#B8D3D1',
              borderWidth: '1.5px',
            }}
          >
            <span className="text-xs font-bold text-[#1A281F]">Easy</span>
            <span className="text-[10px] font-medium text-[#635255]">9d</span>
          </button>
        </div>
      </div>
    </div>
  );
};
