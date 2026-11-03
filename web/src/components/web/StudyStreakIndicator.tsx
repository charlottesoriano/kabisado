import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Flame, Check, Shield, Trophy, ChevronRight, Info } from 'lucide-react';

export interface DayStreakStatus {
  dayLabel: string; // 'M', 'T', 'W', 'T', 'F', 'S', 'S'
  fullDay: string; // 'Mon', 'Tue', etc.
  dateNumber: number;
  completed: boolean;
  isToday: boolean;
}

interface StudyStreakIndicatorProps {
  consecutiveDays?: number;
  longestStreak?: number;
  reviewedToday?: boolean;
  history?: DayStreakStatus[];
  onOpenDetails?: () => void;
  className?: string;
  variant?: 'card' | 'compact';
}

const DEFAULT_WEEK_HISTORY: DayStreakStatus[] = [
  { dayLabel: 'M', fullDay: 'Mon', dateNumber: 26, completed: true, isToday: false },
  { dayLabel: 'T', fullDay: 'Tue', dateNumber: 27, completed: true, isToday: false },
  { dayLabel: 'W', fullDay: 'Wed', dateNumber: 28, completed: true, isToday: false },
  { dayLabel: 'T', fullDay: 'Thu', dateNumber: 29, completed: true, isToday: false },
  { dayLabel: 'F', fullDay: 'Fri', dateNumber: 30, completed: true, isToday: false },
  { dayLabel: 'S', fullDay: 'Sat', dateNumber: 31, completed: true, isToday: false },
  { dayLabel: 'S', fullDay: 'Sun', dateNumber: 1, completed: true, isToday: true },
];

export const StudyStreakIndicator: React.FC<StudyStreakIndicatorProps> = ({
  consecutiveDays = 14,
  longestStreak = 21,
  reviewedToday = true,
  history = DEFAULT_WEEK_HISTORY,
  onOpenDetails,
  className = '',
  variant = 'card',
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (variant === 'compact') {
    return (
      <div
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border select-none transition-all ${className}`}
        style={{
          backgroundColor: '#FFFFFF',
          borderColor: '#B8D3D1',
        }}
      >
        <div
          className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
          style={{
            backgroundColor: '#FFD972',
            color: '#1A281F',
          }}
          aria-label="Fire streak icon"
        >
          <Flame className="w-3.5 h-3.5" strokeWidth={2} />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="font-heading font-bold text-sm text-[#1A281F] tabular-nums">
            {consecutiveDays}
          </span>
          <span className="text-xs text-[#635255] font-medium">day streak</span>
        </div>
      </div>
    );
  }

  return (
    <Card
      className={`p-5 flex flex-col justify-between transition-all hover:border-[#1A281F] ${className}`}
      style={{
        backgroundColor: '#FFFFFF',
        borderColor: '#B8D3D1',
      }}
    >
      {/* Top Header: Fire Icon Badge + Main Text */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3.5">
          {/* Small Fire Icon container with 2px stroke line icon */}
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-transform select-none"
            style={{
              backgroundColor: reviewedToday ? '#FFD972' : '#C7EAE4',
              color: '#1A281F',
              border: '1px solid #B8D3D1',
            }}
            aria-hidden="true"
          >
            <Flame className="w-6 h-6" strokeWidth={2} />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <p className="text-xs font-semibold text-[#635255]">
                Study streak
              </p>
              {reviewedToday ? (
                <span
                  className="px-1.5 py-0.2 rounded text-[10px] font-bold tracking-tight inline-flex items-center gap-0.5"
                  style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
                >
                  <Check className="w-2.5 h-2.5" strokeWidth={2.5} />
                  Active today
                </span>
              ) : (
                <span
                  className="px-1.5 py-0.2 rounded text-[10px] font-bold tracking-tight"
                  style={{ backgroundColor: '#FCBCB8', color: '#1A281F' }}
                >
                  Review pending
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="font-heading text-2xl font-bold tracking-tight text-[#1A281F] tabular-nums">
                {consecutiveDays} days
              </span>
              <span className="text-xs text-[#635255] font-medium">
                in a row
              </span>
            </div>
          </div>
        </div>

        {/* Info toggle / helper button */}
        <button
          type="button"
          onClick={() => setShowTooltip(!showTooltip)}
          className="p-1 text-[#635255] hover:text-[#1A281F] transition-colors rounded-md cursor-pointer"
          title="Streak details & milestones"
          aria-label="View streak details"
        >
          <Info className="w-4 h-4" strokeWidth={2} />
        </button>
      </div>

      {/* 7-Day Mini Streak Calendar Strip */}
      <div className="mt-4 pt-3 border-t border-[#B8D3D1]">
        <div className="flex items-center justify-between text-[11px] text-[#635255] mb-2 font-medium">
          <span>Past 7 days</span>
          <span className="text-[#1A281F] font-semibold">
            {reviewedToday ? 'Daily session completed' : 'Complete today’s deck review'}
          </span>
        </div>

        {/* Strip of days */}
        <div className="grid grid-cols-7 gap-1.5 select-none">
          {history.map((day, idx) => (
            <div
              key={idx}
              className={`flex flex-col items-center py-1.5 rounded-lg border text-center transition-all ${
                day.isToday ? 'ring-1 ring-[#1A281F]' : ''
              }`}
              style={{
                backgroundColor: day.completed ? '#F3FAF8' : '#FFFFFF',
                borderColor: day.completed ? '#A7E8BD' : '#B8D3D1',
              }}
              title={`${day.fullDay} (${day.dateNumber}): ${day.completed ? 'Review session completed' : 'No review session'}`}
            >
              <span className="text-[10px] font-medium text-[#635255] leading-none mb-1">
                {day.dayLabel}
              </span>
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px]"
                style={{
                  backgroundColor: day.completed ? '#A7E8BD' : '#FFFFFF',
                  color: '#1A281F',
                  border: day.completed ? '1px solid #1A281F' : '1px dashed #B8D3D1',
                }}
              >
                {day.completed ? (
                  <Check className="w-3 h-3 text-[#1A281F]" strokeWidth={2.5} />
                ) : (
                  <span className="text-[#635255]">{day.dateNumber}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Info: Personal Best & Milestone */}
      <div className="mt-3 pt-2.5 border-t border-[#B8D3D1] flex items-center justify-between text-[11px] text-[#635255]">
        <div className="flex items-center gap-1.5">
          <Trophy className="w-3.5 h-3.5 text-[#1A281F]" strokeWidth={2} />
          <span>
            Best: <strong className="text-[#1A281F] font-semibold">{longestStreak} days</strong>
          </span>
        </div>

        <div className="flex items-center gap-1 text-[11px] font-medium text-[#1A281F]">
          <Shield className="w-3 h-3 text-[#1A281F]" strokeWidth={2} />
          <span>1 freeze protected</span>
        </div>
      </div>

      {/* Expanded Tooltip / Milestone card when toggled */}
      {showTooltip && (
        <div
          className="mt-3 p-3 rounded-xl border text-xs leading-relaxed space-y-1.5 animate-fadeIn"
          style={{
            backgroundColor: '#F3FAF8',
            borderColor: '#B8D3D1',
          }}
        >
          <div className="flex items-center justify-between font-semibold text-[#1A281F]">
            <span>How Study Streaks Work:</span>
            <span
              className="px-1.5 py-0.2 rounded text-[10px] font-bold"
              style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
            >
              14-Day Club
            </span>
          </div>
          <p className="text-[#635255] text-[11px]">
            Review at least 10 cards or complete 1 quiz/problem set each calendar day to maintain your streak. Reviews are time-stamped in Philippine Standard Time (PST).
          </p>
        </div>
      )}
    </Card>
  );
};
