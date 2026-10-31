import React from 'react';

interface RatingButtonsProps {
  onRate?: (rating: 'again' | 'hard' | 'good' | 'easy') => void;
  selectedRating?: 'again' | 'hard' | 'good' | 'easy' | null;
  compact?: boolean;
}

export const RatingButtons: React.FC<RatingButtonsProps> = ({
  onRate,
  selectedRating,
  compact = false,
}) => {
  return (
    <div className="w-full">
      <div className={`grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3`}>
        {/* 1. Again: Powder Blush (#FCBCB8) with Powder Blush deep (#EFA7A7) border */}
        <button
          type="button"
          onClick={() => onRate?.('again')}
          className={`min-h-[48px] px-3.5 py-2.5 rounded-xl text-center transition-all cursor-pointer flex flex-col items-center justify-center border ${
            selectedRating === 'again' ? 'ring-2 ring-[#1A281F]' : 'hover:brightness-95 active:scale-[0.98]'
          }`}
          style={{
            backgroundColor: '#FCBCB8',
            borderColor: '#EFA7A7',
            borderWidth: '1.5px',
          }}
        >
          <span className="text-[14px] font-semibold tracking-tight" style={{ color: '#1A281F' }}>
            Again
          </span>
          <span className="text-[12px] font-medium mt-0.5" style={{ color: '#635255' }}>
            1 day
          </span>
        </button>

        {/* 2. Hard: Jasmine (#FFD972) with subtle Light Blue or Evergreen border */}
        <button
          type="button"
          onClick={() => onRate?.('hard')}
          className={`min-h-[48px] px-3.5 py-2.5 rounded-xl text-center transition-all cursor-pointer flex flex-col items-center justify-center border ${
            selectedRating === 'hard' ? 'ring-2 ring-[#1A281F]' : 'hover:brightness-95 active:scale-[0.98]'
          }`}
          style={{
            backgroundColor: '#FFD972',
            borderColor: '#B8D3D1',
            borderWidth: '1.5px',
          }}
        >
          <span className="text-[14px] font-semibold tracking-tight" style={{ color: '#1A281F' }}>
            Hard
          </span>
          <span className="text-[12px] font-medium mt-0.5" style={{ color: '#635255' }}>
            3 days
          </span>
        </button>

        {/* 3. Good: Celadon (#A7E8BD), emphasized with subtle Evergreen border */}
        <button
          type="button"
          onClick={() => onRate?.('good')}
          className={`min-h-[48px] px-3.5 py-2.5 rounded-xl text-center transition-all cursor-pointer flex flex-col items-center justify-center border-2 ${
            selectedRating === 'good' ? 'ring-2 ring-[#1A281F]' : 'hover:brightness-95 active:scale-[0.98]'
          }`}
          style={{
            backgroundColor: '#A7E8BD',
            borderColor: '#1A281F',
          }}
        >
          <div className="flex items-center gap-1.5">
            <span className="text-[14px] font-bold tracking-tight" style={{ color: '#1A281F' }}>
              Good
            </span>
            <span
              className="text-[10px] px-1.5 py-0.2 rounded-full font-semibold uppercase tracking-wider"
              style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
            >
              Optimal
            </span>
          </div>
          <span className="text-[12px] font-semibold mt-0.5" style={{ color: '#1A281F' }}>
            6 days
          </span>
        </button>

        {/* 4. Easy: Pale Sky (#C0E8F9) */}
        <button
          type="button"
          onClick={() => onRate?.('easy')}
          className={`min-h-[48px] px-3.5 py-2.5 rounded-xl text-center transition-all cursor-pointer flex flex-col items-center justify-center border ${
            selectedRating === 'easy' ? 'ring-2 ring-[#1A281F]' : 'hover:brightness-95 active:scale-[0.98]'
          }`}
          style={{
            backgroundColor: '#C0E8F9',
            borderColor: '#B8D3D1',
            borderWidth: '1.5px',
          }}
        >
          <span className="text-[14px] font-semibold tracking-tight" style={{ color: '#1A281F' }}>
            Easy
          </span>
          <span className="text-[12px] font-medium mt-0.5" style={{ color: '#635255' }}>
            9 days
          </span>
        </button>
      </div>

      {!compact && (
        <p className="text-center text-[13px] mt-3.5 font-medium select-none" style={{ color: '#635255' }}>
          Keyboard shortcuts: <span className="underline">1</span> for Again ·{' '}
          <span className="underline">2</span> for Hard · <span className="underline">3</span> for Good ·{' '}
          <span className="underline">4</span> for Easy · <span className="underline">Space</span> to flip
        </p>
      )}
    </div>
  );
};
