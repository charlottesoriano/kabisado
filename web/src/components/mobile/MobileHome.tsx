import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { DeckItem } from '../../types';
import { MobileTabBar, MobileTab } from './MobileTabBar';
import {
  Clock,
  Flame,
  Award,
  ChevronRight,
  Play,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';

interface MobileHomeProps {
  decks: DeckItem[];
  activeTab: MobileTab;
  onTabChange: (tab: MobileTab) => void;
  onDeckClick: (deckId: string) => void;
  onStartReview: () => void;
  onOpenDeckPage: () => void;
}

export const MobileHome: React.FC<MobileHomeProps> = ({
  decks,
  activeTab,
  onTabChange,
  onDeckClick,
  onStartReview,
  onOpenDeckPage,
}) => {
  return (
    <div className="flex-1 flex flex-col justify-between">
      {/* Content Area */}
      <div className="p-5 space-y-5">
        {/* 1. Greeting and Avatar */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-[#635255]">
              Maligayang pag-aaral,
            </p>
            <h1 className="font-heading text-xl font-bold tracking-tight text-[#1A281F]">
              Miguel Ramos
            </h1>
          </div>

          <div
            className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs border"
            style={{
              backgroundColor: '#C7EAE4',
              color: '#1A281F',
              borderColor: '#B8D3D1',
            }}
          >
            MR
          </div>
        </div>

        {/* 2. Evergreen "Due today: 24 cards" Hero Card with Jasmine "Start review" button */}
        <div
          className="rounded-[22px] p-5 text-white space-y-3.5 shadow-sm border"
          style={{
            backgroundColor: '#1A281F',
            borderColor: '#1A281F',
          }}
        >
          <div className="flex items-center justify-between">
            <span
              className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
              style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
            >
              Daily Spaced Repetition
            </span>
            <span className="text-xs text-[#C7EAE4] font-medium">
              ~12 mins
            </span>
          </div>

          <div>
            <h2 className="font-heading text-2xl font-bold tracking-tight text-white leading-tight">
              Due today: 24 cards
            </h2>
            <p className="text-xs text-[#C7EAE4] mt-0.5">
              Cellular Respiration, Kinematics &amp; Hist 4
            </p>
          </div>

          {/* Jasmine "Start review" Button (#FFD972 background, #1A281F text) */}
          <Button
            variant="jasmine"
            size="md"
            fullWidth
            onClick={onStartReview}
            icon={<Play className="w-4 h-4 fill-[#1A281F]" />}
          >
            Start review
          </Button>
        </div>

        {/* 3. Two Small Stat Tiles */}
        <div className="grid grid-cols-2 gap-3">
          {/* Stat 1: 86% Accuracy */}
          <Card className="p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-[#635255] font-medium">Quiz Accuracy</span>
              <Award className="w-4 h-4 text-[#1A281F]" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-heading text-xl font-bold text-[#1A281F] tabular-nums">
                86%
              </span>
              <span className="text-[10px] text-[#1A281F] font-semibold">+4%</span>
            </div>
          </Card>

          {/* Stat 2: 14 Day Streak */}
          <Card className="p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-[#635255] font-medium">Study Streak</span>
              <Flame className="w-4 h-4 text-[#1A281F]" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-heading text-xl font-bold text-[#1A281F] tabular-nums">
                14d
              </span>
              <span className="text-[10px] text-[#635255]">streak</span>
            </div>
          </Card>
        </div>

        {/* 4. Deck List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-base font-bold text-[#1A281F]">
              Your Reviewers ({decks.length})
            </h3>
            <span
              onClick={onOpenDeckPage}
              className="text-xs font-semibold text-[#1A281F] cursor-pointer"
            >
              View all
            </span>
          </div>

          <div className="space-y-2.5">
            {decks.map((deck) => {
              const isGenerating = deck.status === 'generating';

              return (
                <div
                  key={deck.id}
                  onClick={() => !isGenerating && onDeckClick(deck.id)}
                  className="p-3.5 rounded-2xl border bg-white flex items-center justify-between gap-3 active:scale-[0.99] transition-transform cursor-pointer"
                  style={{ borderColor: '#B8D3D1' }}
                >
                  <div className="min-w-0 space-y-1 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="px-2 py-0.2 rounded text-[10px] font-semibold"
                        style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                      >
                        {deck.subject}
                      </span>
                      {isGenerating && (
                        <span className="text-[10px] font-bold text-[#1A281F]">
                          Generating ({deck.generatingProgress}%)
                        </span>
                      )}
                    </div>

                    <h4 className="font-heading text-sm font-bold text-[#1A281F] truncate">
                      {deck.title}
                    </h4>

                    <div className="flex items-center gap-2 text-[11px] text-[#635255]">
                      <span>{deck.totalCards} cards</span>
                      <span>·</span>
                      <span>{deck.masteryPercentage}% mastery</span>
                    </div>
                  </div>

                  {/* Right: Badge or progress */}
                  <div className="shrink-0 flex items-center gap-1.5">
                    {deck.dueCards > 0 ? (
                      <span
                        className="px-2 py-0.5 rounded-full text-[11px] font-bold"
                        style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
                      >
                        {deck.dueCards} due
                      </span>
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-[#A7E8BD]" />
                    )}
                    <ChevronRight className="w-4 h-4 text-[#635255]" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 5. Bottom Tab Bar (Home, Decks, Upload, Progress) */}
      <MobileTabBar activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
};
