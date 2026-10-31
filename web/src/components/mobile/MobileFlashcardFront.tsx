import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Flashcard } from '../../types';
import { X, RotateCw, Sparkles, Layers } from 'lucide-react';

interface MobileFlashcardFrontProps {
  flashcard: Flashcard;
  cardNumber?: number;
  totalCards?: number;
  onFlipToBack: () => void;
  onClose: () => void;
}

export const MobileFlashcardFront: React.FC<MobileFlashcardFrontProps> = ({
  flashcard,
  cardNumber = 5,
  totalCards = 12,
  onFlipToBack,
  onClose,
}) => {
  return (
    <div className="flex-1 p-5 flex flex-col justify-between bg-[#F3FAF8]">
      {/* Top Bar: Close & Counter */}
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

          <span
            className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            {flashcard.topic}
          </span>
        </div>

        {/* 1-line Progress Bar */}
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

      {/* Stacked Card Look (with layered cards underneath) */}
      <div className="relative my-auto w-full py-4">
        {/* Under-layer 2 */}
        <div
          className="absolute inset-x-5 -top-2 h-full rounded-[24px] border opacity-40 -rotate-1 pointer-events-none"
          style={{ backgroundColor: '#FFFFFF', borderColor: '#B8D3D1' }}
        />
        {/* Under-layer 1 */}
        <div
          className="absolute inset-x-2 -top-1 h-full rounded-[24px] border opacity-70 rotate-1 pointer-events-none"
          style={{ backgroundColor: '#FFFFFF', borderColor: '#B8D3D1' }}
        />

        {/* Front Active Card */}
        <div
          onClick={onFlipToBack}
          className="relative rounded-[24px] p-7 border bg-white shadow-sm flex flex-col justify-between min-h-[380px] cursor-pointer active:scale-[0.99] transition-transform text-center"
          style={{
            borderColor: '#B8D3D1',
            borderWidth: '1.5px',
          }}
        >
          <div className="flex items-center justify-center gap-1.5 text-xs text-[#635255]">
            <Layers className="w-3.5 h-3.5 text-[#1A281F]" />
            <span>Active Recall Question</span>
          </div>

          {/* Centered Question in Space Grotesk */}
          <div className="my-auto px-2">
            <h2 className="font-heading text-xl md:text-2xl font-bold tracking-tight text-[#1A281F] leading-snug">
              {flashcard.question}
            </h2>
          </div>

          <div className="flex flex-col items-center gap-1">
            <span className="text-xs text-[#635255] font-medium flex items-center gap-1.5">
              <RotateCw className="w-3.5 h-3.5" />
              <span>Tap the card to flip</span>
            </span>
          </div>
        </div>
      </div>

      {/* Large Touch Target "Show answer" Button */}
      <div className="pt-2">
        <Button
          variant="primary"
          size="lg"
          fullWidth
          onClick={onFlipToBack}
          icon={<RotateCw className="w-4 h-4" />}
        >
          Show answer
        </Button>
      </div>
    </div>
  );
};
