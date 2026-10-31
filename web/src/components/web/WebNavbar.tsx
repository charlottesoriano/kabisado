import React from 'react';
import { Logo } from '../common/Logo';
import { WebScreen } from '../../types';
import { Plus, Sparkles, BookOpen } from 'lucide-react';

interface WebNavbarProps {
  currentScreen: WebScreen;
  onNavigate: (screen: WebScreen) => void;
  onNewDeckClick: () => void;
}

export const WebNavbar: React.FC<WebNavbarProps> = ({
  currentScreen,
  onNavigate,
  onNewDeckClick,
}) => {
  return (
    <header
      className="sticky top-[49px] z-40 w-full border-b transition-colors"
      style={{
        backgroundColor: '#FFFFFF',
        borderColor: '#B8D3D1',
      }}
    >
      <div className="max-w-[1280px] mx-auto px-6 h-16 flex items-center justify-between gap-8">
        {/* Zone 1: Brand Wordmark */}
        <div
          onClick={() => onNavigate('dashboard')}
          className="cursor-pointer"
        >
          <Logo size="md" showSubtitle subtitle="Reviewer" />
        </div>

        {/* Zone 2: Navigation Links (Single line, text with subtle hover) */}
        <nav className="flex items-center gap-7 text-sm font-medium">
          <button
            type="button"
            onClick={() => onNavigate('dashboard')}
            className={`whitespace-nowrap transition-colors cursor-pointer py-1 border-b-2 ${
              currentScreen === 'dashboard'
                ? 'border-[#1A281F] text-[#1A281F] font-semibold'
                : 'border-transparent text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            Dashboard
          </button>
          <button
            type="button"
            onClick={() => onNavigate('deck')}
            className={`whitespace-nowrap transition-colors cursor-pointer py-1 border-b-2 ${
              currentScreen === 'deck'
                ? 'border-[#1A281F] text-[#1A281F] font-semibold'
                : 'border-transparent text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            Decks
          </button>
          <button
            type="button"
            onClick={() => onNavigate('upload')}
            className={`whitespace-nowrap transition-colors cursor-pointer py-1 border-b-2 ${
              currentScreen === 'upload'
                ? 'border-[#1A281F] text-[#1A281F] font-semibold'
                : 'border-transparent text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            Upload
          </button>
        </nav>

        {/* Zone 3: 1 Primary Action + User Avatar */}
        <div className="flex items-center gap-3.5 shrink-0">
          <button
            type="button"
            onClick={onNewDeckClick}
            className="min-h-[40px] px-4 py-2 rounded-xl text-[14px] font-semibold transition-all cursor-pointer flex items-center gap-2 text-white active:scale-95"
            style={{ backgroundColor: '#1A281F' }}
          >
            <Plus className="w-4 h-4" strokeWidth={2} />
            <span>New deck</span>
          </button>

          {/* User Avatar with Initials */}
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs select-none border"
            style={{
              backgroundColor: '#C7EAE4',
              color: '#1A281F',
              borderColor: '#B8D3D1',
            }}
            title="Miguel Ramos (DLSU-Manila)"
          >
            MR
          </div>
        </div>
      </div>
    </header>
  );
};
