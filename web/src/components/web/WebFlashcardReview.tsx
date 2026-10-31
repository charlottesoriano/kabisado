import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { RatingButtons } from '../common/RatingButtons';
import { Flashcard } from '../../types';
import { X, ExternalLink, RotateCw, Sparkles, Check, Bookmark } from 'lucide-react';

interface WebFlashcardReviewProps {
  flashcard: Flashcard;
  cardNumber?: number;
  totalCards?: number;
  onClose: () => void;
  onRate: (rating: 'again' | 'hard' | 'good' | 'easy') => void;
}

export const WebFlashcardReview: React.FC<WebFlashcardReviewProps> = ({
  flashcard,
  cardNumber = 5,
  totalCards = 12,
  onClose,
  onRate,
}) => {
  const [isFlipped, setIsFlipped] = useState(true); // default true to show the exact answered/revealed focus mode state with Jasmine highlight
  const [selectedRating, setSelectedRating] = useState<'again' | 'hard' | 'good' | 'easy' | null>('good');

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === ' ') {
        e.preventDefault();
        setIsFlipped((prev) => !prev);
      } else if (e.key === '1') {
        setSelectedRating('again');
        onRate('again');
      } else if (e.key === '2') {
        setSelectedRating('hard');
        onRate('hard');
      } else if (e.key === '3') {
        setSelectedRating('good');
        onRate('good');
      } else if (e.key === '4') {
        setSelectedRating('easy');
        onRate('easy');
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onRate, onClose]);

  const progressPercent = Math.round((cardNumber / totalCards) * 100);

  // Function to highlight keyword in Jasmine (#FFD972)
  const renderAnswerWithHighlight = (answerText: string, keyword: string) => {
    if (!keyword) return answerText;
    const parts = answerText.split(new RegExp(`(${keyword})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === keyword.toLowerCase() ? (
        <span
          key={index}
          className="px-1.5 py-0.5 rounded font-semibold transition-colors"
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
    <div
      className="min-h-screen py-8 px-6 flex flex-col justify-between"
      style={{ backgroundColor: '#F3FAF8' }}
    >
      {/* Top Bar: Close button, Progress bar, "Card 5 of 12" */}
      <div className="max-w-[800px] w-full mx-auto">
        <div className="flex items-center justify-between gap-4 mb-3">
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl border bg-white hover:bg-[#F3FAF8] transition-colors cursor-pointer text-[#1A281F]"
            style={{ borderColor: '#B8D3D1' }}
            title="Close review (Esc)"
          >
            <X className="w-5 h-5" strokeWidth={2} />
          </button>

          {/* Card Count */}
          <span className="font-heading text-sm font-bold text-[#1A281F] tabular-nums">
            Card {cardNumber} of {totalCards}
          </span>

          {/* Quick topic indicator */}
          <span
            className="px-3 py-1 rounded-full text-xs font-semibold"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            {flashcard.topic}
          </span>
        </div>

        {/* Progress Bar: Evergreen (#1A281F) fill on Frozen Water (#C7EAE4) track */}
        <div
          className="w-full h-2 rounded-full overflow-hidden"
          style={{ backgroundColor: '#C7EAE4' }}
        >
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${progressPercent}%`,
              backgroundColor: '#1A281F',
            }}
          />
        </div>
      </div>

      {/* Center: Large Card (20-24px radius, tidy desk feel) */}
      <div className="max-w-[800px] w-full mx-auto my-8">
        <div
          onClick={() => setIsFlipped(!isFlipped)}
          className="rounded-[24px] p-8 md:p-12 border bg-white cursor-pointer transition-all hover:shadow-xs relative"
          style={{
            borderColor: '#B8D3D1',
            borderWidth: '1.5px',
          }}
        >
          {/* Question Section */}
          <div className="space-y-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#635255]">
              Question
            </span>
            <h2 className="font-heading text-2xl md:text-3xl font-bold tracking-tight text-[#1A281F] leading-snug">
              {flashcard.question}
            </h2>
          </div>

          {/* Subtle Divider */}
          <div className="my-8 h-[1px]" style={{ backgroundColor: '#B8D3D1' }} />

          {/* Answer Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#635255]">
                Answer
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsFlipped(!isFlipped);
                }}
                className="text-xs text-[#635255] hover:text-[#1A281F] flex items-center gap-1 font-medium"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Flip (Space)</span>
              </button>
            </div>

            <p className="text-base md:text-lg text-[#1A281F] leading-relaxed">
              {renderAnswerWithHighlight(flashcard.answer, flashcard.highlightedKeyword)}
            </p>
          </div>

          {/* Source Link */}
          <div className="mt-8 pt-4 border-t border-[#B8D3D1] flex items-center justify-between text-xs">
            <span className="text-[#635255] font-medium flex items-center gap-1.5">
              <span>Source:</span>
              <strong className="text-[#1A281F] font-semibold">{flashcard.sourceRef}</strong>
            </span>
            <span className="text-xs text-[#635255]">
              Topic: {flashcard.topic}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom: Four Rating Buttons + Keyboard Shortcuts */}
      <div className="max-w-[800px] w-full mx-auto">
        <RatingButtons
          selectedRating={selectedRating}
          onRate={(rating) => {
            setSelectedRating(rating);
            onRate(rating);
          }}
        />
      </div>
    </div>
  );
};
