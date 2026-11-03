import React, { useState } from 'react';
import { Card } from '../common/Card';
import {
  GraduationCap,
  Award,
  Sparkles,
  ChevronRight,
  TrendingUp,
  Info,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';

export interface AcademicRankTier {
  level: number;
  title: string;
  minXp: number;
  perk: string;
}

export const ACADEMIC_RANKS: AcademicRankTier[] = [
  { level: 1, title: 'Freshman Scholar', minXp: 0, perk: 'Basic spaced repetition' },
  { level: 3, title: 'Honor Roll', minXp: 800, perk: 'Custom deck tags & search' },
  { level: 5, title: 'College Scholar', minXp: 1600, perk: 'Targeted weakest topic drills' },
  { level: 7, title: "Dean's Lister", minXp: 2400, perk: 'Priority PDF equation parser' },
  { level: 9, title: 'Magna Track', minXp: 3400, perk: 'Advanced SM-2 interval tuning' },
  { level: 11, title: 'Summa Fellow', minXp: 5000, perk: 'Comprehensive exam simulators' },
];

interface StudyLevelProgressProps {
  currentLevel?: number;
  currentRankTitle?: string;
  currentXp?: number;
  nextLevelXp?: number;
  levelStartXp?: number;
  todayXpGained?: number;
  onViewRanks?: () => void;
  className?: string;
}

export const StudyLevelProgress: React.FC<StudyLevelProgressProps> = ({
  currentLevel = 7,
  currentRankTitle = "Dean's Lister",
  currentXp = 2450,
  nextLevelXp = 3000,
  levelStartXp = 2000,
  todayXpGained = 180,
  onViewRanks,
  className = '',
}) => {
  const [showRanksGuide, setShowRanksGuide] = useState(false);

  // Compute progress through current level
  const range = nextLevelXp - levelStartXp;
  const progressInLevel = Math.max(0, currentXp - levelStartXp);
  const percentage = Math.min(100, Math.round((progressInLevel / range) * 100));
  const xpNeeded = nextLevelXp - currentXp;

  return (
    <Card
      className={`p-6 space-y-5 transition-all hover:border-[#1A281F] ${className}`}
      style={{
        backgroundColor: '#FFFFFF',
        borderColor: '#B8D3D1',
      }}
    >
      {/* Header: Academic Rank & Level Insignia */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          {/* Insignia Icon: 2px line stroke icon in Celadon container */}
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border select-none"
            style={{
              backgroundColor: '#A7E8BD',
              color: '#1A281F',
              borderColor: '#1A281F',
            }}
            aria-hidden="true"
          >
            <GraduationCap className="w-6 h-6" strokeWidth={2} />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <span
                className="px-2 py-0.5 rounded text-[11px] font-bold tracking-tight"
                style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
              >
                Level {currentLevel}
              </span>
              <span className="text-xs text-[#635255] font-medium">Academic Rank</span>
            </div>

            <h3 className="font-heading text-lg font-bold tracking-tight text-[#1A281F] mt-0.5 leading-tight">
              {currentRankTitle}
            </h3>
          </div>
        </div>

        {/* Info button */}
        <button
          type="button"
          onClick={() => setShowRanksGuide(!showRanksGuide)}
          className="p-1 rounded-md text-[#635255] hover:text-[#1A281F] transition-colors cursor-pointer"
          title="View XP ranks & earning guide"
          aria-label="View study level details"
        >
          <Info className="w-4 h-4" strokeWidth={2} />
        </button>
      </div>

      {/* Experience Points Counter & Progress */}
      <div className="space-y-2">
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1.5">
            <span className="font-heading text-2xl font-bold tracking-tight text-[#1A281F] tabular-nums">
              {currentXp.toLocaleString()}
            </span>
            <span className="text-xs text-[#635255] font-medium">
              / {nextLevelXp.toLocaleString()} XP
            </span>
          </div>

          <span
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            <TrendingUp className="w-3 h-3" strokeWidth={2.5} />
            +{todayXpGained} XP today
          </span>
        </div>

        {/* Visual Progress Bar: Evergreen fill on Frozen Water track */}
        <div
          className="w-full h-2.5 rounded-full overflow-hidden select-none"
          style={{ backgroundColor: '#C7EAE4' }}
        >
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${percentage}%`,
              backgroundColor: '#1A281F',
            }}
          />
        </div>

        {/* Subtitle helper */}
        <div className="flex items-center justify-between text-[11px] text-[#635255] pt-0.5">
          <span>{percentage}% through Level {currentLevel}</span>
          <span className="font-medium text-[#1A281F]">
            {xpNeeded} XP to Level {currentLevel + 1}
          </span>
        </div>
      </div>

      {/* Review XP Sources Quick Matrix */}
      <div
        className="p-3.5 rounded-xl border space-y-2"
        style={{
          backgroundColor: '#F3FAF8',
          borderColor: '#B8D3D1',
        }}
      >
        <span className="text-[11px] font-bold text-[#1A281F] uppercase tracking-wide block">
          Earn XP from Daily Reviews:
        </span>

        <div className="grid grid-cols-3 gap-2 text-center select-none">
          <div className="p-2 rounded-lg bg-white border border-[#B8D3D1]">
            <p className="text-[10px] text-[#635255]">Flashcard</p>
            <p className="text-xs font-bold text-[#1A281F] mt-0.5">+10 XP</p>
          </div>
          <div className="p-2 rounded-lg bg-white border border-[#B8D3D1]">
            <p className="text-[10px] text-[#635255]">Quiz Answer</p>
            <p className="text-xs font-bold text-[#1A281F] mt-0.5">+25 XP</p>
          </div>
          <div className="p-2 rounded-lg bg-white border border-[#B8D3D1]">
            <p className="text-[10px] text-[#635255]">STEM Problem</p>
            <p className="text-xs font-bold text-[#1A281F] mt-0.5">+50 XP</p>
          </div>
        </div>
      </div>

      {/* Collapsible Academic Rank Ladder Guide */}
      {showRanksGuide && (
        <div
          className="pt-3 border-t border-[#B8D3D1] space-y-2.5 animate-fadeIn"
        >
          <div className="flex items-center justify-between text-xs font-bold text-[#1A281F]">
            <span>Academic Honor Progression</span>
            <span className="text-[#635255] font-normal text-[11px]">Next: Level 8</span>
          </div>

          <div className="space-y-1.5 text-xs">
            {ACADEMIC_RANKS.map((rank) => {
              const isCurrent = rank.level === currentLevel;
              const isPassed = rank.level < currentLevel;

              return (
                <div
                  key={rank.level}
                  className={`p-2 rounded-lg border flex items-center justify-between gap-2 transition-all ${
                    isCurrent ? 'ring-1 ring-[#1A281F] font-semibold' : ''
                  }`}
                  style={{
                    backgroundColor: isCurrent ? '#FFFFFF' : isPassed ? '#F3FAF8' : '#FFFFFF',
                    borderColor: isCurrent ? '#1A281F' : '#B8D3D1',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 border"
                      style={{
                        backgroundColor: isCurrent ? '#A7E8BD' : isPassed ? '#1A281F' : '#FFFFFF',
                        color: isPassed ? '#FFFFFF' : '#1A281F',
                        borderColor: '#1A281F',
                      }}
                    >
                      {isPassed ? '✓' : rank.level}
                    </span>
                    <span className="text-[#1A281F] text-xs">
                      {rank.title}
                    </span>
                  </div>

                  <span className="text-[11px] text-[#635255] tabular-nums">
                    {rank.minXp} XP
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
};
